#!/usr/bin/env python3
"""Harvest a pilot corpus of ~500 US engineering patents in thermal/fluid/insulation CPC classes."""

import argparse
import json
import re
from pathlib import Path
from datasets import load_dataset


PATENT_KEYWORDS = [
    r"\bheat\s+exchang",
    r"\bthermal\s+storag",
    r"\bphase\s+change\s+material",
    r"\bevaporat\w*\s+cool",
    r"\bheat\s+pipe",
    r"\bporous\s+(?:matrix|insulation|layer)",
    r"\bwick\w*\s+(?:structure|pumping|channel)",
    r"\bthermal\s+insulat",
    r"\bbuilding\s+envelope",
    r"\bsorption\s+(?:cooling|storage|material)",
    r"\blatent\s+heat",
    r"\bconvective\s+cooling",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PATENT_KEYWORDS]


def matches_thermal_fluid_domain(text: str) -> bool:
    """Check if the abstract or description matches thermal, fluid, or insulation criteria."""
    return any(p.search(text) for p in COMPILED_PATTERNS)


def main():
    parser = argparse.ArgumentParser(description="Harvest engineering patents from big_patent.")
    parser.add_argument(
        "--output",
        type=str,
        default="/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl",
        help="Path to output JSONL file",
    )
    parser.add_argument(
        "--sample-output",
        type=str,
        default="data/sample/eng_sample.jsonl",
        help="Path to write sample 5 documents for git",
    )
    parser.add_argument("--target-count", type=int, default=500, help="Target document count")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path = Path(args.sample_output)
    sample_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting patent harvesting. Target: {args.target_count} documents.", flush=True)
    collected = []
    category_counts = {}

    # Stream from subset 'f' (Mechanical/Heating/Heat Exchange) and 'e' (Fixed constructions/Building/Insulation)
    subsets = [("f", int(args.target_count * 0.7)), ("e", int(args.target_count * 0.3))]

    doc_counter = 0
    for subset_name, subset_target in subsets:
        print(f"\nStreaming subset '{subset_name}' (target: {subset_target})...", flush=True)
        ds = load_dataset(
            "NortheasternUniversity/big_patent",
            subset_name,
            split="train",
            streaming=True,
        )

        subset_collected = 0
        for i, item in enumerate(ds):
            abstract = item.get("abstract", "")
            description = item.get("description", "")

            # Check domain relevance in abstract first (faster) or description head
            combined_preview = abstract + " " + description[:2000]
            if matches_thermal_fluid_domain(combined_preview):
                doc_counter += 1
                doc_id = f"US-PAT-{subset_name.upper()}-{doc_counter:04d}"
                doc = {
                    "doc_id": doc_id,
                    "domain": "eng",
                    "cpc_category": subset_name.upper(),
                    "title": abstract[:100].strip(),
                    "abstract": abstract.strip(),
                    "text": description[:50000].strip(),
                    "license": "US Patent Public Domain",
                }
                collected.append(doc)
                subset_collected += 1
                category_counts[subset_name.upper()] = category_counts.get(subset_name.upper(), 0) + 1

                if len(collected) % 50 == 0 or len(collected) == args.target_count:
                    print(f"  Progress: {len(collected)}/{args.target_count} patents collected.", flush=True)

                if subset_collected >= subset_target or len(collected) >= args.target_count:
                    break

            if i > 0 and i % 2000 == 0:
                print(f"  Scanned {i} candidate records from subset '{subset_name}'...", flush=True)

        if len(collected) >= args.target_count:
            break

    print(f"\nWriting {len(collected)} patents to {out_path}...", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for doc in collected:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    # Write small sample for git
    with open(sample_path, "w", encoding="utf-8") as f:
        for doc in collected[:5]:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    file_size_mb = out_path.stat().st_size / (1024 * 1024)
    print("\n=== Engineering Patent Pilot Summary ===")
    print(f"Total patents: {len(collected)}")
    print(f"Disk size: {file_size_mb:.2f} MB")
    print(f"Output file: {out_path}")
    print(f"Sample file (5 docs): {sample_path}")
    print("Category breakdown:")
    for cat, cnt in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  CPC Section {cat}: {cnt} ({cnt / len(collected) * 100:.1f}%)")
    print("License: 100% US Patent Public Domain")


if __name__ == "__main__":
    main()
