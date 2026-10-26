#!/usr/bin/env python3
"""Step 6: Sample 30 documents (15 bio, 15 eng) with fixed seed for human gold-card annotation."""

import argparse
import json
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Sample 30 candidate documents for gold card annotation.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/corpus_chunked.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/gold_candidates.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-bio", type=int, default=15)
    parser.add_argument("--n-eng", type=int, default=15)
    args = parser.parse_args()

    bio_docs = []
    eng_docs = []

    with open(args.input) as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                if d.get("domain") == "bio":
                    bio_docs.append(d)
                else:
                    eng_docs.append(d)

    random.seed(args.seed)
    sampled_bio = random.sample(bio_docs, min(args.n_bio, len(bio_docs)))
    sampled_eng = random.sample(eng_docs, min(args.n_eng, len(eng_docs)))

    candidates = []
    for idx, d in enumerate(sampled_bio + sampled_eng):
        candidates.append({
            "candidate_index": idx + 1,
            "doc_id": d["doc_id"],
            "domain": d["domain"],
            "title": d.get("title", ""),
            "citation": d.get("citation", ""),
            "license": d.get("license", "Unknown"),
            "text_length": len(d["text"]),
            "text_preview": d["text"][:500] + "...",
            "gold_card_template": {
                "card_id": f"GOLD-{d['domain'].upper()}-{d['doc_id']}",
                "domain": d["domain"],
                "subject": {"name": "", "identifier": ""},
                "context": {"environment": "", "scale": "", "regime": ""},
                "action": {"verb": "", "object": "", "description": ""},
                "state_change": {"state_variable": "", "from_value": "", "to_value": ""},
                "phenomenon": {"description": ""},
                "effect": {"canonical_name": "", "governing_equation": "", "relevant_variables": []},
                "quantities": [],
                "evidence": [],
                "license": d.get("license", "Unknown"),
                "confidence": 1.0,
                "tier": "gold",
                "unsupported_fields": [],
            }
        })

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(candidates, f, indent=2)

    print(f"Sampled {len(sampled_bio)} bio and {len(sampled_eng)} eng candidates (seed={args.seed}) -> {out_path}")


if __name__ == "__main__":
    main()
