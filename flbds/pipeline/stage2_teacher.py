"""Stage 2: Mechanism Card Drafting using Qwen2.5-72B-Instruct-FP8 and Schema Guided Decoding."""

import argparse
import json
import time
import yaml
from pathlib import Path
import torch
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams
from flbds.schema import MechanismCard


def build_teacher_prompt(doc: dict) -> str:
    doc_id = doc["doc_id"]
    domain = doc["domain"]
    title = doc.get("title", "")
    citation = doc.get("citation", "")
    lic = doc.get("license", "Unknown")
    text = doc["text"]

    system_prompt = (
        "You are an expert physical scientist and knowledge engineer extracting SAPPhIRE Mechanism Cards.\n"
        "Domain scope: Thermal, fluid, and porous-media physical mechanisms.\n"
        "You must extract a strictly valid MechanismCard matching the provided JSON schema.\n\n"
        "MANDATORY EVIDENCE GROUNDING RULES:\n"
        "1. Every item in 'evidence' MUST have 'text_span' as an EXACT VERBATIM SUBSTRING from <DOCUMENT_TEXT>.\n"
        "2. 'char_start' must be the exact 0-based character start offset of 'text_span' in <DOCUMENT_TEXT>.\n"
        "3. 'char_end' must be the exact 0-based character end offset (char_start + len(text_span)).\n"
        "4. verification condition: document_text[char_start:char_end] == text_span must be strictly true.\n"
        "5. 'source_doc_id' must equal the document's doc_id.\n\n"
        "RULES FOR PHYSICAL CAUSAL CHAIN:\n"
        "- Action: functional verb (regulate, insulate, store, dissipate, wick, evaporate) and object.\n"
        "- StateChange: state_variable (e.g. temperature, saturation, pressure) and direction/values.\n"
        "- Phenomenon: physical behavior or macroscopic process.\n"
        "- Effect: canonical physical law (e.g. fourier_conduction, darcy_flow, latent_heat_evaporation).\n"
        "- Tier: must be 'silver'.\n"
        "- Unsupported fields: Any field not explicitly stated in the text must be left empty and named in 'unsupported_fields'."
    )

    user_prompt = (
        f"<DOCUMENT_METADATA>\n"
        f"Doc ID: {doc_id}\n"
        f"Domain: {domain}\n"
        f"Title: {title}\n"
        f"Citation: {citation}\n"
        f"License: {lic}\n"
        f"</DOCUMENT_METADATA>\n\n"
        f"<DOCUMENT_TEXT>\n"
        f"{text}\n"
        f"</DOCUMENT_TEXT>\n\n"
        f"Extract the primary physical mechanism card from <DOCUMENT_TEXT>."
    )

    return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"


def run_teacher(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
    model_dir: str,
    max_docs: int | None = None,
    temperature: float = 0.2,
    seed: int = 42,
) -> dict:
    t_start = time.perf_counter()
    docs = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
                if max_docs and len(docs) >= max_docs:
                    break

    input_count = len(docs)
    print(f"[Stage 2 Teacher] Loaded {input_count} documents from {input_path}", flush=True)

    prompts = [build_teacher_prompt(d) for d in docs]

    print(f"[Stage 2 Teacher] Initializing vLLM with 72B FP8 model: {model_dir}...", flush=True)
    t_model_load = time.perf_counter()
    llm = LLM(
        model=model_dir,
        max_model_len=8192,
        gpu_memory_utilization=0.90,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t_model_load
    print(f"[Stage 2 Teacher] Model loaded in {load_time:.2f} s. Drafting cards with schema guided decoding...", flush=True)

    schema = MechanismCard.model_json_schema()
    sampling_params = SamplingParams(
        temperature=temperature,
        seed=seed,
        max_tokens=1500,
        structured_outputs=StructuredOutputsParams(json=schema),
    )

    t_gen_start = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params)
    gen_time = time.perf_counter() - t_gen_start

    total_prompt_tokens = sum(len(o.prompt_token_ids) for o in outputs)
    total_output_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    decode_tok_s = total_output_tokens / max(0.001, gen_time)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_cards = 0
    schema_failures = 0
    drop_reasons = {}

    with open(output_path, "w") as fout:
        for doc, out in zip(docs, outputs):
            raw_json = out.outputs[0].text.strip()
            try:
                parsed = json.loads(raw_json)
                # Ensure license and tier match document metadata
                if not parsed.get("license"):
                    parsed["license"] = doc.get("license", "Unknown")
                parsed["tier"] = "silver"
                card = MechanismCard.model_validate(parsed)
                record = {
                    "doc_id": doc["doc_id"],
                    "domain": doc["domain"],
                    "title": doc.get("title", ""),
                    "citation": doc.get("citation", ""),
                    "license": doc.get("license", "Unknown"),
                    "text": doc["text"],
                    "card": card.model_dump(),
                }
                fout.write(json.dumps(record) + "\n")
                valid_cards += 1
            except Exception as e:
                schema_failures += 1
                reason = f"schema_validation_failure: {str(e)[:60]}"
                drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

    elapsed = time.perf_counter() - t_start
    gpu_hours = round(elapsed / 3600.0, 5)

    summary = {
        "stage": 2,
        "stage_name": "72B Teacher Drafting",
        "model": Path(model_dir).name,
        "input_count": input_count,
        "output_count": valid_cards,
        "dropped_count": schema_failures,
        "drop_reasons": drop_reasons,
        "prompt_tokens": total_prompt_tokens,
        "output_tokens": total_output_tokens,
        "decode_tokens_per_sec": round(decode_tok_s, 1),
        "elapsed_seconds": round(elapsed, 2),
        "gpu_hours": gpu_hours,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[Stage 2 Teacher] Complete: {valid_cards}/{input_count} valid MechanismCards drafted. Logged -> {summary_path}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 2 teacher drafting.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/stage_1_output.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/stage_2_output.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_2_summary.json")
    parser.add_argument("--config", default="configs/models.yaml")
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)["teacher"]

    run_teacher(
        input_path=Path(args.input),
        output_path=Path(args.output),
        summary_path=Path(args.summary),
        model_dir=cfg["local_dir"],
        max_docs=args.max_docs,
        temperature=args.temperature,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
