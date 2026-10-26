"""Stage 3: Inter-sample Agreement Evaluation on 72B Teacher (second sample on ~300 docs)."""

import argparse
import json
import random
import time
import yaml
from pathlib import Path
from pydantic import BaseModel
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams
from flbds.schema import MechanismCard
from flbds.pipeline.stage2_teacher import build_teacher_prompt


def token_jaccard(str1: str, str2: str) -> float:
    """Compute token-level Jaccard similarity between two strings."""
    t1 = set(str1.lower().replace("_", " ").split())
    t2 = set(str2.lower().replace("_", " ").split())
    if not t1 or not t2:
        return 1.0 if t1 == t2 else 0.0
    return len(t1 & t2) / len(t1 | t2)


def compute_agreement(card1: dict, card2: dict) -> dict:
    """Compute field-level agreement between two independent drafts of a MechanismCard."""
    # Subject agreement
    s1 = card1.get("subject", {}).get("name", "")
    s2 = card2.get("subject", {}).get("name", "")
    sub_sim = token_jaccard(s1, s2)

    # Action verb agreement
    v1 = card1.get("action", {}).get("verb", "").strip().lower()
    v2 = card2.get("action", {}).get("verb", "").strip().lower()
    verb_match = 1.0 if v1 == v2 or (v1 in v2 or v2 in v1) else 0.0

    # State variable agreement
    sv1 = card1.get("state_change", {}).get("state_variable", "").strip().lower()
    sv2 = card2.get("state_change", {}).get("state_variable", "").strip().lower()
    sv_sim = token_jaccard(sv1, sv2)

    # Physical effect canonical name agreement
    eff1 = card1.get("effect", {}).get("canonical_name", "").strip().lower()
    eff2 = card2.get("effect", {}).get("canonical_name", "").strip().lower()
    eff_sim = token_jaccard(eff1, eff2)

    # Phenomenon agreement
    ph1 = card1.get("phenomenon", {}).get("description", "")
    ph2 = card2.get("phenomenon", {}).get("description", "")
    ph_sim = token_jaccard(ph1, ph2)

    avg_agreement = (sub_sim + verb_match + sv_sim + eff_sim + ph_sim) / 5.0

    return {
        "subject_similarity": round(sub_sim, 3),
        "action_verb_match": round(verb_match, 3),
        "state_variable_similarity": round(sv_sim, 3),
        "effect_similarity": round(eff_sim, 3),
        "phenomenon_similarity": round(ph_sim, 3),
        "mean_agreement": round(avg_agreement, 3),
    }


def run_agreement(
    stage2_output: Path,
    output_details: Path,
    summary_path: Path,
    model_dir: str,
    max_sample: int = 300,
    seed: int = 43,
) -> dict:
    t_start = time.perf_counter()
    cards1 = []
    with open(stage2_output) as f:
        for line in f:
            if line.strip():
                cards1.append(json.loads(line))

    if not cards1:
        print("[Stage 3 Agreement] No cards found from Stage 2. Skipping.", flush=True)
        return {"stage": 3, "status": "skipped_no_input"}

    # Subsample up to max_sample
    random.seed(seed)
    sampled = cards1 if len(cards1) <= max_sample else random.sample(cards1, max_sample)
    sample_size = len(sampled)
    print(f"[Stage 3 Agreement] Subsampled {sample_size} documents for second 72B agreement pass", flush=True)

    prompts = [build_teacher_prompt(d) for d in sampled]

    print(f"[Stage 3 Agreement] Initializing vLLM with 72B FP8 model: {model_dir}...", flush=True)
    t_load = time.perf_counter()
    llm = LLM(
        model=model_dir,
        max_model_len=8192,
        gpu_memory_utilization=0.90,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t_load
    print(f"[Stage 3 Agreement] Model loaded in {load_time:.2f} s. Running second sample pass...", flush=True)

    schema = MechanismCard.model_json_schema()
    sampling_params = SamplingParams(
        temperature=0.7,
        seed=seed,
        max_tokens=1500,
        structured_outputs=StructuredOutputsParams(json=schema),
    )

    t_gen = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params)
    gen_time = time.perf_counter() - t_gen

    total_prompt_tokens = sum(len(o.prompt_token_ids) for o in outputs)
    total_output_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    decode_tok_s = total_output_tokens / max(0.001, gen_time)

    agreements = []
    output_details.parent.mkdir(parents=True, exist_ok=True)
    with open(output_details, "w") as fout:
        for rec, out in zip(sampled, outputs):
            try:
                card2 = json.loads(out.outputs[0].text.strip())
                card1 = rec["card"]
                aggr = compute_agreement(card1, card2)
                aggr["doc_id"] = rec["doc_id"]
                agreements.append(aggr)
                fout.write(json.dumps(aggr) + "\n")
            except Exception as e:
                pass

    n_valid = len(agreements)
    avg_sub = sum(a["subject_similarity"] for a in agreements) / max(1, n_valid)
    avg_act = sum(a["action_verb_match"] for a in agreements) / max(1, n_valid)
    avg_sv = sum(a["state_variable_similarity"] for a in agreements) / max(1, n_valid)
    avg_eff = sum(a["effect_similarity"] for a in agreements) / max(1, n_valid)
    avg_ph = sum(a["phenomenon_similarity"] for a in agreements) / max(1, n_valid)
    overall_mean = sum(a["mean_agreement"] for a in agreements) / max(1, n_valid)

    elapsed = time.perf_counter() - t_start
    gpu_hours = round(elapsed / 3600.0, 5)

    summary = {
        "stage": 3,
        "stage_name": "72B Inter-sample Agreement",
        "sample_size": sample_size,
        "valid_evaluations": n_valid,
        "mean_subject_agreement": round(avg_sub, 3),
        "mean_action_agreement": round(avg_act, 3),
        "mean_state_variable_agreement": round(avg_sv, 3),
        "mean_effect_agreement": round(avg_eff, 3),
        "mean_phenomenon_agreement": round(avg_ph, 3),
        "overall_mean_agreement": round(overall_mean, 3),
        "prompt_tokens": total_prompt_tokens,
        "output_tokens": total_output_tokens,
        "decode_tokens_per_sec": round(decode_tok_s, 1),
        "elapsed_seconds": round(elapsed, 2),
        "gpu_hours": gpu_hours,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[Stage 3 Agreement] Complete: Mean agreement = {overall_mean:.1%}. Logged -> {summary_path}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 3 agreement evaluation.")
    parser.add_argument("--stage2-output", default="/home/abhishek24024/flbds_data/pilot/stage_2_output.jsonl")
    parser.add_argument("--output-details", default="/home/abhishek24024/flbds_data/pilot/stage_3_agreement_details.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_3_summary.json")
    parser.add_argument("--config", default="configs/models.yaml")
    parser.add_argument("--max-sample", type=int, default=300)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)["teacher"]

    run_agreement(
        stage2_output=Path(args.stage2_output),
        output_details=Path(args.output_details),
        summary_path=Path(args.summary),
        model_dir=cfg["local_dir"],
        max_sample=args.max_sample,
    )


if __name__ == "__main__":
    main()
