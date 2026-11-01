#!/usr/bin/env python3
"""Execute full extraction pipeline on targeted organism harvest."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from flbds.pipeline.chunker import process_corpus
from flbds.pipeline.stage1_filter import run_filter
from flbds.pipeline.stage2_teacher import run_teacher
from flbds.pipeline.stage4_evidence import run_evidence_verification
from flbds.pipeline.stage5_critic import run_critic
from flbds.pipeline.stage6_quantities import run_quantities
from flbds.pipeline.stage7_dedup import run_dedup


def main():
    parser = argparse.ArgumentParser(description="Run pipeline on targeted harvest.")
    parser.add_argument("--harvest-dir", default="/home/abhishek24024/flbds_data/harvest")
    parser.add_argument("--models-dir", default="/home/abhishek24024/flbds_data/models")
    args = parser.parse_args()

    hdir = Path(args.harvest_dir)
    mdir = Path(args.models_dir)

    raw_input = hdir / "pmc_targeted_harvest.jsonl"
    chunked_corpus = hdir / "corpus_chunked.jsonl"
    s1_out = hdir / "stage_1_output.jsonl"
    s1_sum = hdir / "stage_1_summary.json"
    s2_out = hdir / "stage_2_output.jsonl"
    s2_sum = hdir / "stage_2_summary.json"
    s4_out = hdir / "stage_4_output.jsonl"
    s4_sum = hdir / "stage_4_summary.json"
    s5_out = hdir / "stage_5_output.jsonl"
    s5_sum = hdir / "stage_5_summary.json"
    s6_out = hdir / "stage_6_output.jsonl"
    s6_sum = hdir / "stage_6_summary.json"
    s7_out = hdir / "silver_cards.jsonl"
    s7_sum = hdir / "stage_7_summary.json"
    final_report = hdir / "organism_cards_summary.json"

    print("=========================================================")
    print("FLBDS: Processing Targeted Organism Harvest Through Pipeline")
    print(f"Harvest Directory: {hdir}")
    print("=========================================================")

    # Stage 0: Chunking
    print("\n--- Stage 0: Chunking Corpus ---")
    n_chunked = process_corpus(raw_input, chunked_corpus, max_chars=12000)
    print(f"Chunked {n_chunked} documents.")

    # Stage 1: 7B Relevance Filter
    print("\n--- Stage 1: 7B Relevance Filter ---")
    run_filter(
        input_corpus=chunked_corpus,
        output_path=s1_out,
        summary_path=s1_sum,
        model_dir=str(mdir / "Qwen2.5-7B-Instruct"),
    )

    # Stage 2: 72B Teacher Drafting
    print("\n--- Stage 2: 72B Teacher Drafting ---")
    run_teacher(
        input_path=s1_out,
        output_path=s2_out,
        summary_path=s2_sum,
        model_dir=str(mdir / "Qwen2.5-72B-Instruct-FP8"),
    )

    # Stage 4: Deterministic Evidence Verification (CPU)
    print("\n--- Stage 4: Evidence Verification (CPU) ---")
    run_evidence_verification(
        input_path=s2_out,
        output_path=s4_out,
        summary_path=s4_sum,
    )

    # Stage 5: 32B Entailment Critic with Field Pruning
    print("\n--- Stage 5: 32B Critic (Field Pruning) ---")
    run_critic(
        input_path=s4_out,
        output_path=s5_out,
        summary_path=s5_sum,
        model_dir=str(mdir / "Qwen2.5-32B-Instruct-FP8"),
    )

    # Stage 6: 7B + Pint Sanitized Quantities
    print("\n--- Stage 6: 7B + Pint Quantity Extraction ---")
    run_quantities(
        input_path=s5_out,
        output_path=s6_out,
        summary_path=s6_sum,
        model_dir=str(mdir / "Qwen2.5-7B-Instruct"),
    )

    # Stage 7: Near-Duplicate Removal (CPU)
    print("\n--- Stage 7: Near-Duplicate Removal ---")
    run_dedup(
        input_path=s6_out,
        output_path=s7_out,
        summary_path=s7_sum,
    )

    # Final Aggregation per Organism
    silver_cards = []
    with open(s7_out) as f:
        for line in f:
            if line.strip():
                silver_cards.append(json.loads(line))

    org_summary = {}
    lic_summary = {}
    for c in silver_cards:
        org = c.get("organism", "Unknown")
        lic = c.get("license", "Unknown")
        org_summary[org] = org_summary.get(org, 0) + 1
        lic_summary[lic] = lic_summary.get(lic, 0) + 1

    report = {
        "total_silver_cards": len(silver_cards),
        "cards_per_organism": org_summary,
        "license_breakdown": lic_summary,
        "silver_cards_file": str(s7_out),
    }

    with open(final_report, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=========================================================")
    print(f"HARVEST PIPELINE COMPLETE: {len(silver_cards)} Silver Cards Produced")
    print("Cards per Organism:")
    for o, cnt in sorted(org_summary.items(), key=lambda x: -x[1]):
        print(f"  {o:20s}: {cnt} silver cards")
    print("\nLicense Breakdown:")
    for l, cnt in lic_summary.items():
        print(f"  {l:20s}: {cnt}")
    print(f"Summary logged -> {final_report}")
    print("=========================================================")


if __name__ == "__main__":
    main()
