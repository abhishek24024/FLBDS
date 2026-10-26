#!/usr/bin/env python3
"""Harvest a pilot corpus of ~500 biological PMC open-access papers on thermal/fluid mechanisms."""

import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


KEYWORDS = [
    "thermoregulation",
    "evaporative cooling",
    "wicking",
    "heat storage",
    "fur insulation",
    "countercurrent heat exchange",
    "thermal buffering",
    "porous skin",
    "transpiration cooling",
    "sweating physiology",
    "mud wallowing",
    "thermal boundary layer",
]

ALLOWED_LICENSES = {"CC BY", "CC0", "CC BY-SA", "CC BY 4.0", "CC BY 3.0", "CC BY 2.0"}


def search_pmc_ids(term: str, retmax: int = 150) -> list[str]:
    """Search NCBI E-utilities for open-access PMC IDs matching keyword."""
    query = f'("{term}"[Title/Abstract]) AND open access[filter]'
    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pmc&term={urllib.parse.quote(query)}&retmode=json&retmax={retmax}"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FLBDS-BTech/1.0 (academic; abhishek24024@iiitd.ac.in)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("esearchresult", {}).get("idlist", [])
    except Exception as exc:
        print(f"Warning: E-utilities search failed for '{term}': {exc}", file=sys.stderr)
        return []


def fetch_pmc_document(pmcid: str, max_text_chars: int = 50000) -> dict | None:
    """Fetch article metadata and text from PMC Open Access AWS S3 mirror."""
    json_url = f"https://pmc-oa-opendata.s3.amazonaws.com/PMC{pmcid}.1/PMC{pmcid}.1.json"
    req_json = urllib.request.Request(json_url, headers={"User-Agent": "FLBDS/1.0"})

    try:
        with urllib.request.urlopen(req_json, timeout=8) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    license_code = (meta.get("license_code") or "").strip()
    is_allowed = any(license_code.startswith(allowed) for allowed in ALLOWED_LICENSES)
    if not is_allowed:
        return None

    # Fetch text file
    txt_url = f"https://pmc-oa-opendata.s3.amazonaws.com/PMC{pmcid}.1/PMC{pmcid}.1.txt"
    req_txt = urllib.request.Request(txt_url, headers={"User-Agent": "FLBDS/1.0"})
    try:
        with urllib.request.urlopen(req_txt, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception:
        text = meta.get("title", "")

    if len(text) > max_text_chars:
        text = text[:max_text_chars]

    return {
        "doc_id": f"PMC{pmcid}",
        "domain": "bio",
        "title": meta.get("title", ""),
        "citation": meta.get("citation", ""),
        "doi": meta.get("doi"),
        "license": license_code,
        "text": text,
    }


def main():
    parser = argparse.ArgumentParser(description="Harvest PMC open-access biology papers.")
    parser.add_argument(
        "--output",
        type=str,
        default="/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl",
        help="Path to output JSONL file",
    )
    parser.add_argument(
        "--sample-output",
        type=str,
        default="data/sample/bio_sample.jsonl",
        help="Path to write sample 5 documents for git",
    )
    parser.add_argument("--target-count", type=int, default=500, help="Target document count")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path = Path(args.sample_output)
    sample_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting PMC harvesting. Target: {args.target_count} documents.", flush=True)
    seen_ids = set()
    collected = []
    license_counts = {}

    out_file = open(out_path, "w", encoding="utf-8")

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for kw in KEYWORDS:
                if len(collected) >= args.target_count:
                    break
                print(f"Searching keyword: '{kw}'...", flush=True)
                pmc_ids = search_pmc_ids(kw, retmax=120)
                new_ids = [pid for pid in pmc_ids if pid not in seen_ids]
                for pid in new_ids:
                    seen_ids.add(pid)

                print(f"  Found {len(new_ids)} new candidate IDs. Fetching from AWS S3 in parallel...", flush=True)

                future_to_pid = {executor.submit(fetch_pmc_document, pid): pid for pid in new_ids}
                for future in concurrent.futures.as_completed(future_to_pid):
                    if len(collected) >= args.target_count:
                        break
                    try:
                        doc = future.result()
                    except Exception:
                        continue

                    if doc:
                        collected.append(doc)
                        out_file.write(json.dumps(doc, ensure_ascii=False) + "\n")
                        out_file.flush()
                        lic = doc["license"]
                        license_counts[lic] = license_counts.get(lic, 0) + 1
                        if len(collected) % 50 == 0 or len(collected) == args.target_count:
                            print(f"  Progress: {len(collected)}/{args.target_count} documents collected.", flush=True)

                if len(collected) >= args.target_count:
                    break
    finally:
        out_file.close()

    print(f"Harvest complete. Total {len(collected)} documents written to {out_path}.", flush=True)

    # Write small sample for git
    with open(sample_path, "w", encoding="utf-8") as f:
        for doc in collected[:5]:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    file_size_mb = out_path.stat().st_size / (1024 * 1024)
    print("\n=== PMC Bio Pilot Summary ===")
    print(f"Total documents: {len(collected)}")
    print(f"Disk size: {file_size_mb:.2f} MB")
    print(f"Output file: {out_path}")
    print(f"Sample file (5 docs): {sample_path}")
    print("License breakdown:")
    for lic, cnt in sorted(license_counts.items(), key=lambda x: -x[1]):
        print(f"  {lic}: {cnt} ({cnt / len(collected) * 100:.1f}%)")


if __name__ == "__main__":
    main()
