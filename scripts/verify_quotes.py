#!/usr/bin/env python3
"""Quote Verifier for FLBDS Audit Reports.

Asserts that any quoted text (source excerpt, evidence span, or abstract sentence)
is an exact substring of the corpus record, harvest record, or saved raw API response on disk.
Prints: doc_id, record title, character offsets (start:end), and record SHA256.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_all_records(data_dir: Path):
    records = {}

    # 1. Corpus files
    corpus_dir = data_dir / "corpus"
    for fn in ["bio_pilot.jsonl", "eng_pilot.jsonl"]:
        fp = corpus_dir / fn
        if fp.exists():
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    doc_id = d.get("doc_id") or d.get("id") or d.get("pmcid") or d.get("patent_id")
                    if doc_id:
                        # Full searchable text is title + abstract + text
                        text_parts = [
                            d.get("title", ""),
                            d.get("abstract", ""),
                            d.get("text", "")
                        ]
                        full_text = "\n".join(p for p in text_parts if p)
                        sha = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
                        records[doc_id] = {
                            "title": d.get("title", "No Title"),
                            "text": full_text,
                            "sha256": sha,
                            "source_file": str(fp.name),
                        }

    # 2. Harvest files
    harvest_dir = data_dir / "harvest"
    if harvest_dir.exists():
        for fp in harvest_dir.glob("*.jsonl"):
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    doc_id = d.get("doc_id") or d.get("id") or d.get("pmcid")
                    if doc_id and doc_id not in records:
                        text_parts = [
                            d.get("title", ""),
                            d.get("abstract", ""),
                            d.get("text", "")
                        ]
                        full_text = "\n".join(p for p in text_parts if p)
                        sha = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
                        records[doc_id] = {
                            "title": d.get("title", "No Title"),
                            "text": full_text,
                            "sha256": sha,
                            "source_file": str(fp.name),
                        }

    # 3. Raw API responses
    api_dir = data_dir / "api_responses"
    if api_dir.exists():
        for fp in api_dir.glob("*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                    d = json.loads(content)
                doc_id = fp.stem
                sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
                # If it's a crossref/europepmc/openalex object, stringify or search raw
                records[doc_id] = {
                    "title": d.get("title", [fp.stem])[0] if isinstance(d.get("title"), list) else str(d.get("title", fp.stem)),
                    "text": content,
                    "sha256": sha,
                    "source_file": f"api_responses/{fp.name}",
                }
            except Exception:
                pass

    return records


def verify_quote(doc_id: str, quote: str, records: dict):
    clean_quote = quote.strip()
    if not clean_quote:
        return False, "Empty quote string provided."

    if doc_id not in records:
        return False, f"doc_id '{doc_id}' not found in any corpus, harvest, or API response."

    rec = records[doc_id]
    target_text = rec["text"]

    pos = target_text.find(clean_quote)
    if pos != -1:
        start_char = pos
        end_char = pos + len(clean_quote)
        return True, {
            "doc_id": doc_id,
            "title": rec["title"],
            "offsets": f"{start_char}:{end_char}",
            "sha256": rec["sha256"],
            "source_file": rec["source_file"],
            "quote_len": len(clean_quote)
        }
    
    # Try normalized whitespace if direct substring fails
    norm_quote = " ".join(clean_quote.split())
    # find where norm_quote matches
    import re
    pat = re.escape(norm_quote)
    pat = pat.replace(r"\ ", r"\s+")
    m = re.search(pat, target_text)
    if m:
        return True, {
            "doc_id": doc_id,
            "title": rec["title"],
            "offsets": f"{m.start()}:{m.end()}",
            "sha256": rec["sha256"],
            "source_file": rec["source_file"],
            "quote_len": len(clean_quote),
            "note": "matched_with_whitespace_normalization"
        }

    return False, f"Quote text ({len(clean_quote)} chars) is NOT a substring of {doc_id} text."


def main():
    parser = argparse.ArgumentParser(description="Verify exact substring quotes against corpus.")
    parser.add_argument("--data_dir", type=str, default="/home/abhishek24024/flbds_data", help="Path to flbds_data")
    parser.add_argument("--doc_id", type=str, required=True, help="Document ID or DOI slug")
    parser.add_argument("--quote", type=str, required=True, help="Exact quote to verify")
    args = parser.parse_args()

    records = load_all_records(Path(args.data_dir))
    passed, info = verify_quote(args.doc_id, args.quote, records)
    if passed:
        print("VERIFIED QUOTE:")
        print(f"  doc_id:      {info['doc_id']}")
        print(f"  title:       {info['title']}")
        print(f"  offsets:     {info['offsets']}")
        print(f"  sha256:      {info['sha256']}")
        print(f"  source_file: {info['source_file']}")
        sys.exit(0)
    else:
        print(f"FAILED VERIFICATION: {info}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
