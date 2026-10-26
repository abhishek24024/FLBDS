"""Stage 1: Relevance Filter using Qwen2.5-7B-Instruct."""

import argparse
import json
import time
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
import torch
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams


class FilterResult(BaseModel):
    relevant: bool = Field(
        ...,
        description="True if the text describes a thermal, fluid, or porous-media mechanism; False otherwise"
    )
    mechanism_type: str = Field(
        ...,
        description="One of: thermoregulation, heat_storage, evaporative_cooling, wicking, porous_insulation, phase_change, sorption, or none"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    rationale: str = Field(..., description="One-sentence physical rationale")


def run_filter(
    input_corpus: Path,
    output_path: Path,
    summary_path: Path,
    model_dir: str,
    max_docs: int | None = None,
) -> dict:
    t_start = time.perf_counter()
    docs = []
    with open(input_corpus) as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
                if max_docs and len(docs) >= max_docs:
                    break

    input_count = len(docs)
    print(f"[Stage 1 Filter] Loaded {input_count} documents from {input_corpus}", flush=True)

    system_prompt = (
        "You are an expert physicist evaluating technical documents for physical mechanisms.\n"
        "Domain scope is strictly restricted to: thermal, fluid and porous-media mechanisms "
        "(thermoregulation, heat storage, evaporative cooling, wicking, porous insulation, phase change, sorption).\n"
        "Documents describing genetics, medicine/surgery, purely electrical circuits, or unrelated software without "
        "a physical thermal/fluid/porous mechanism must be marked relevant=false.\n"
        "Respond strictly with the required JSON object."
    )

    prompts = []
    for d in docs:
        excerpt = d["text"][:3000]
        user_prompt = (
            f"<DOCUMENT_METADATA>\n"
            f"Doc ID: {d['doc_id']}\n"
            f"Domain: {d['domain']}\n"
            f"Title: {d.get('title', '')}\n"
            f"</DOCUMENT_METADATA>\n\n"
            f"<DOCUMENT_TEXT>\n"
            f"{excerpt}\n"
            f"</DOCUMENT_TEXT>\n\n"
            f"Question: Does this document describe a physical mechanism in thermoregulation, heat storage, "
            f"evaporative cooling, wicking, porous insulation, phase change, or sorption?"
        )
        # Qwen chat formatting
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
        prompts.append(prompt)

    print(f"[Stage 1 Filter] Initializing vLLM with model: {model_dir}...", flush=True)
    t_model_load = time.perf_counter()
    llm = LLM(
        model=model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.85,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t_model_load
    print(f"[Stage 1 Filter] Model loaded in {load_time:.2f} s. Generating structured decisions...", flush=True)

    schema = FilterResult.model_json_schema()
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=150,
        structured_outputs=StructuredOutputsParams(json=schema),
    )

    t_gen_start = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params)
    gen_time = time.perf_counter() - t_gen_start

    total_prompt_tokens = sum(len(o.prompt_token_ids) for o in outputs)
    total_output_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    overall_tok_s = (total_prompt_tokens + total_output_tokens) / max(0.001, gen_time)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    drop_reasons = {}
    kept_count = 0
    dropped_count = 0

    with open(output_path, "w") as fout:
        for doc, out in zip(docs, outputs):
            raw_json = out.outputs[0].text.strip()
            try:
                parsed = json.loads(raw_json)
                decision = FilterResult.model_validate(parsed)
            except Exception as e:
                decision = FilterResult(relevant=False, mechanism_type="none", confidence=0.0, rationale=f"Parse error: {e}")

            if decision.relevant:
                doc["filter_decision"] = decision.model_dump()
                fout.write(json.dumps(doc) + "\n")
                kept_count += 1
            else:
                dropped_count += 1
                reason = f"irrelevant_{decision.mechanism_type}"
                drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

    elapsed = time.perf_counter() - t_start
    gpu_hours = round(elapsed / 3600.0, 5)

    summary = {
        "stage": 1,
        "stage_name": "7B Relevance Filter",
        "model": Path(model_dir).name,
        "input_count": input_count,
        "output_count": kept_count,
        "dropped_count": dropped_count,
        "drop_reasons": drop_reasons,
        "prompt_tokens": total_prompt_tokens,
        "output_tokens": total_output_tokens,
        "tokens_per_sec": round(overall_tok_s, 1),
        "elapsed_seconds": round(elapsed, 2),
        "gpu_hours": gpu_hours,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[Stage 1 Filter] Complete: {kept_count}/{input_count} passed ({dropped_count} dropped). Logged -> {summary_path}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 1 relevance filter.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/corpus_chunked.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/stage_1_output.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_1_summary.json")
    parser.add_argument("--config", default="configs/models.yaml")
    parser.add_argument("--max-docs", type=int, default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)["filter"]

    run_filter(
        input_corpus=Path(args.input),
        output_path=Path(args.output),
        summary_path=Path(args.summary),
        model_dir=cfg["local_dir"],
        max_docs=args.max_docs,
    )


if __name__ == "__main__":
    main()
