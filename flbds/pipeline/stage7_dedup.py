"""Stage 7: Near-Duplicate Removal for Mechanism Cards."""

import argparse
import json
import time
from pathlib import Path


def card_signature(card: dict) -> set[str]:
    """Create a token set representing the causal essence of a card."""
    parts = []
    sub = card.get("subject", {}).get("name", "")
    parts.append(sub.lower())

    act = card.get("action", {})
    parts.append(act.get("verb", "").lower())
    parts.append(act.get("object", "").lower())

    eff = card.get("effect", {})
    parts.append(eff.get("canonical_name", "").lower())

    ph = card.get("phenomenon", {})
    parts.extend(ph.get("description", "").lower().split())

    tokens = set()
    for p in parts:
        for w in p.replace("_", " ").split():
            if len(w) > 2:
                tokens.add(w)
    return tokens


def card_similarity(sig1: set[str], sig2: set[str]) -> float:
    if not sig1 or not sig2:
        return 0.0
    return len(sig1 & sig2) / len(sig1 | sig2)


def run_dedup(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
    sim_threshold: float = 0.80,
) -> dict:
    t_start = time.perf_counter()
    records = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    input_count = len(records)
    print(f"[Stage 7 Dedup] Running near-duplicate clustering on {input_count} cards (threshold={sim_threshold})...", flush=True)

    kept_records = []
    dropped_records = []
    domain_groups = {"bio": [], "eng": []}

    for rec in records:
        dom = rec.get("domain", "bio")
        domain_groups.setdefault(dom, []).append(rec)

    for dom, dom_recs in domain_groups.items():
        retained = []
        for rec in dom_recs:
            card = rec["card"]
            sig = card_signature(card)
            is_dup = False
            for prev_rec, prev_sig in retained:
                sim = card_similarity(sig, prev_sig)
                if sim >= sim_threshold:
                    is_dup = True
                    dropped_records.append({
                        "dropped_card_id": card.get("card_id"),
                        "matched_card_id": prev_rec["card"].get("card_id"),
                        "similarity": round(sim, 3),
                    })
                    break
            if not is_dup:
                retained.append((rec, sig))
                kept_records.append(rec)

    output_count = len(kept_records)
    dropped_count = len(dropped_records)
    elapsed = time.perf_counter() - t_start

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fout:
        for rec in kept_records:
            fout.write(json.dumps(rec) + "\n")

    summary = {
        "stage": 7,
        "stage_name": "Near-Duplicate Removal",
        "similarity_threshold": sim_threshold,
        "input_count": input_count,
        "output_count": output_count,
        "dropped_count": dropped_count,
        "drop_reasons": {"near_duplicate": dropped_count},
        "tokens_per_sec": 0.0,
        "elapsed_seconds": round(elapsed, 2),
        "gpu_hours": 0.0,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[Stage 7 Dedup] Complete: {output_count}/{input_count} unique silver cards retained ({dropped_count} duplicates removed). Logged -> {summary_path}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 7 near-duplicate removal.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/stage_6_output.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/silver_cards.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_7_summary.json")
    parser.add_argument("--threshold", type=float, default=0.80)
    args = parser.parse_args()

    run_dedup(
        input_path=Path(args.input),
        output_path=Path(args.output),
        summary_path=Path(args.summary),
        sim_threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
