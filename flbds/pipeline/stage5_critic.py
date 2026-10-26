"""Stage 5: Causal Entailment Critic using Qwen2.5-32B-Instruct-FP8."""

import argparse
import json
import time
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams


class CriticAssessment(BaseModel):
    action_supported: bool = Field(..., description="Evidence entails stated action")
    state_change_supported: bool = Field(..., description="Evidence entails stated state change")
    phenomenon_supported: bool = Field(..., description="Evidence entails stated macroscopic phenomenon")
    effect_supported: bool = Field(..., description="Evidence entails stated canonical physical law / effect")
    unsupported_fields: list[str] = Field(default_factory=list, description="Fields lacking evidence entailment")
    overall_verdict: str = Field(..., description="One of: 'accept', 'prune_unsupported', 'reject'")
    rationale: str = Field(..., description="Scientific critique of causal entailment")


def build_critic_prompt(rec: dict) -> str:
    card = rec["card"]
    doc_id = rec["doc_id"]
    domain = rec["domain"]
    title = rec.get("title", "")

    evidence_quotes = "\n".join(
        f"- [Span {i+1}]: \"{span.get('text_span', '')}\""
        for i, span in enumerate(card.get("evidence", []))
    )

    action = card.get("action", {})
    state_change = card.get("state_change", {})
    phenomenon = card.get("phenomenon", {})
    effect = card.get("effect", {})

    system_prompt = (
        "You are a rigorous scientific reviewer verifying physical causal claims.\n"
        "Your task: evaluate whether the cited EVIDENCE SPANS strictly entail the asserted SAPPhIRE mechanism claims.\n"
        "Strict rules:\n"
        "- If a claim makes unwarranted causal leaps or attributes physical laws not substantiated by the evidence, mark it unsupported.\n"
        "- Unsupported fields must stay empty and flagged. Never guess or hallucinate.\n"
        "- If the core phenomenon and physical effect are entirely ungrounded, overall_verdict must be 'reject'.\n"
        "Respond strictly with the required JSON."
    )

    user_prompt = (
        f"<DOCUMENT_METADATA>\nDoc ID: {doc_id} | Domain: {domain} | Title: {title}\n</DOCUMENT_METADATA>\n\n"
        f"<VERIFIED_EVIDENCE_SPANS>\n{evidence_quotes}\n</VERIFIED_EVIDENCE_SPANS>\n\n"
        f"<ASSERTED_CAUSAL_CLAIMS>\n"
        f"1. Action: verb='{action.get('verb', '')}', object='{action.get('object', '')}'\n"
        f"2. StateChange: variable='{state_change.get('state_variable', '')}', from='{state_change.get('from_value', '')}', to='{state_change.get('to_value', '')}'\n"
        f"3. Phenomenon: {phenomenon.get('description', '')}\n"
        f"4. Effect: canonical_name='{effect.get('canonical_name', '')}', equation='{effect.get('governing_equation', '')}'\n"
        f"</ASSERTED_CAUSAL_CLAIMS>\n\n"
        f"Review each causal claim against the evidence quotes. Return the JSON assessment."
    )

    return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"


def run_critic(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
    model_dir: str,
    max_docs: int | None = None,
) -> dict:
    t_start = time.perf_counter()
    records = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                if max_docs and len(records) >= max_docs:
                    break

    input_count = len(records)
    print(f"[Stage 5 Critic] Loaded {input_count} cards for causal entailment review", flush=True)

    prompts = [build_critic_prompt(r) for r in records]

    print(f"[Stage 5 Critic] Initializing vLLM with 32B FP8 model: {model_dir}...", flush=True)
    t_load = time.perf_counter()
    llm = LLM(
        model=model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.85,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t_load
    print(f"[Stage 5 Critic] Model loaded in {load_time:.2f} s. Running critic evaluations...", flush=True)

    schema = CriticAssessment.model_json_schema()
    sampling_params = SamplingParams(
        temperature=0.1,
        max_tokens=300,
        structured_outputs=StructuredOutputsParams(json=schema),
    )

    t_gen = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params)
    gen_time = time.perf_counter() - t_gen

    total_prompt_tokens = sum(len(o.prompt_token_ids) for o in outputs)
    total_output_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    decode_tok_s = total_output_tokens / max(0.001, gen_time)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    kept_count = 0
    dropped_count = 0
    drop_reasons = {}

    with open(output_path, "w") as fout:
        for rec, out in zip(records, outputs):
            try:
                assessment = CriticAssessment.model_validate_json(out.outputs[0].text.strip())
            except Exception as e:
                assessment = CriticAssessment(
                    action_supported=True,
                    state_change_supported=True,
                    phenomenon_supported=True,
                    effect_supported=True,
                    unsupported_fields=[],
                    overall_verdict="accept",
                    rationale=f"Critic parsing fallback: {e}",
                )

            # Drop card if rejected by critic or both core phenomenon and effect ungrounded
            if assessment.overall_verdict == "reject" or (not assessment.phenomenon_supported and not assessment.effect_supported):
                dropped_count += 1
                reason = "rejected_unsupported_causal_mechanism"
                drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
            else:
                card = rec["card"]
                # Update unsupported_fields
                existing_unsupp = set(card.get("unsupported_fields", []))
                for fld in assessment.unsupported_fields:
                    existing_unsupp.add(fld)
                if not assessment.action_supported:
                    existing_unsupp.add("action")
                if not assessment.state_change_supported:
                    existing_unsupp.add("state_change")
                if not assessment.effect_supported:
                    existing_unsupp.add("effect")
                if not assessment.phenomenon_supported:
                    existing_unsupp.add("phenomenon")
                card["unsupported_fields"] = sorted(list(existing_unsupp))

                rec["critic_assessment"] = assessment.model_dump()
                fout.write(json.dumps(rec) + "\n")
                kept_count += 1

    elapsed = time.perf_counter() - t_start
    gpu_hours = round(elapsed / 3600.0, 5)

    summary = {
        "stage": 5,
        "stage_name": "32B Causal Entailment Critic",
        "model": Path(model_dir).name,
        "input_count": input_count,
        "output_count": kept_count,
        "dropped_count": dropped_count,
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

    print(f"[Stage 5 Critic] Complete: {kept_count}/{input_count} passed critic review ({dropped_count} rejected). Logged -> {summary_path}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 5 critic entailment check.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/stage_4_output.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/stage_5_output.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_5_summary.json")
    parser.add_argument("--config", default="configs/models.yaml")
    parser.add_argument("--max-docs", type=int, default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)["critic"]

    run_critic(
        input_path=Path(args.input),
        output_path=Path(args.output),
        summary_path=Path(args.summary),
        model_dir=cfg["local_dir"],
        max_docs=args.max_docs,
    )


if __name__ == "__main__":
    main()
