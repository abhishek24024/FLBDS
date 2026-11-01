#!/usr/bin/env python3
"""Extract 12 Bio and 12 Eng records sampled with seed 11 for rigorous review."""

import json
import random
from pathlib import Path

def main():
    path = Path("/home/abhishek24024/flbds_data/pilot/stage_6_output_clean.jsonl")
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))

    bio = [r for r in records if r.get("domain") == "bio" or "PMC" in r.get("doc_id", "")]
    eng = [r for r in records if r not in bio]

    bio.sort(key=lambda x: x["doc_id"])
    eng.sort(key=lambda x: x["doc_id"])

    random.seed(11)
    sampled_bio = random.sample(bio, 12)
    sampled_eng = random.sample(eng, 12)

    out = {
        "bio": sampled_bio,
        "eng": sampled_eng
    }

    out_path = Path("/home/abhishek24024/flbds_data/review/seed11_sampled_24.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Saved 24 sampled records to {out_path}")
    print("Bio doc_ids:", [r["doc_id"] for r in sampled_bio])
    print("Eng doc_ids:", [r["doc_id"] for r in sampled_eng])

if __name__ == "__main__":
    main()
