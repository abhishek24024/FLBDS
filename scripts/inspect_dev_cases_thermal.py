#!/usr/bin/env python3
"""Inspect all 12 Dev Cases for Thermal Engineering Review."""

import json
from pathlib import Path

def main():
    dev_base = Path("flbds/benchmark/dev")
    case_ids = [
        "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
        "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
        "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
        "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
    ]

    for cid in case_ids:
        cdir = dev_base / cid
        with open(cdir / "problem_card.json") as f:
            prob = json.load(f)
        with open(cdir / "ground_truth_eval.json") as f:
            gt = json.load(f)
        with open(cdir / "reference_design.json") as f:
            ref = json.load(f)

        print(f"=== {cid} ===")
        print("System:", prob["system"]["name"])
        print("Required Function:", prob["required_function"])
        print("Hard Constraints:", prob["hard_constraints"])
        print("Acceptable Templates:", gt["acceptable_templates"])
        print("Reference Design:", json.dumps(ref, indent=2))
        print("-" * 60)

if __name__ == "__main__":
    main()
