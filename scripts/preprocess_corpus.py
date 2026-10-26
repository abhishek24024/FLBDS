#!/usr/bin/env python3
"""CLI utility to chunk and prepare pilot corpus documents for LLM processing."""

import argparse
import sys
from pathlib import Path
from flbds.pipeline.chunker import process_corpus


def main():
    parser = argparse.ArgumentParser(description="Preprocess and chunk pilot corpus.")
    parser.add_argument("--bio-in", default="/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl")
    parser.add_argument("--eng-in", default="/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl")
    parser.add_argument("--out-dir", default="/home/abhishek24024/flbds_data/pilot")
    parser.add_argument("--limit-per-domain", type=int, default=None, help="Optional limit for smoke tests")
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "corpus_chunked.jsonl"

    print(f"Preprocessing corpus: bio from {args.bio_in}, eng from {args.eng_in}...")
    bio_tmp = out_dir / "bio_chunked_tmp.jsonl"
    eng_tmp = out_dir / "eng_chunked_tmp.jsonl"

    n_bio = process_corpus(Path(args.bio_in), bio_tmp, limit=args.limit_per_domain, max_chars=args.max_chars)
    n_eng = process_corpus(Path(args.eng_in), eng_tmp, limit=args.limit_per_domain, max_chars=args.max_chars)

    # Interleave / combine bio and eng into single unified corpus file
    with open(out_file, "w") as fout:
        with open(bio_tmp) as fin:
            for line in fin:
                fout.write(line)
        with open(eng_tmp) as fin:
            for line in fin:
                fout.write(line)

    bio_tmp.unlink(missing_ok=True)
    eng_tmp.unlink(missing_ok=True)

    print(f"Preprocessed {n_bio} bio documents and {n_eng} engineering documents -> {out_file} (total {n_bio + n_eng})")


if __name__ == "__main__":
    main()
