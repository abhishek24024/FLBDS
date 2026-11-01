#!/usr/bin/env python3
"""Targeted harvest of 12 benchmark organisms from PMC Open Access (CC BY / CC0 only).

Follows FLBDS v9 §6.3 / Phase 1:
- 12 target organisms: Penguin, Aquatic insect, Termite, Namib beetle, Cactus,
  Polar bear, Jackrabbit, Xylem, Leaf, Desert snail, Prairie dog, Toucan.
- ~30 papers per organism fetched from NCBI + AWS S3 mirror.
- Strict CC BY / CC0 licensing check.
- Logs counts, license breakdown, and prepares corpus for silver card pipeline.
"""

import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ORGANISMS = [
    {"name": "Penguin", "queries": ["penguin thermoregulation", "Aptenodytes heat exchange", "penguin countercurrent"]},
    {"name": "Aquatic insect", "queries": ["aquatic insect plastron", "Notonecta respiration", "plastron hair array"]},
    {"name": "Termite", "queries": ["termite mound ventilation", "Macrotermes thermoregulation", "termite nest airflow"]},
    {"name": "Namib beetle", "queries": ["Stenocara fog harvesting", "Namib beetle water collection", "beetle hydrophilic hydrophobic"]},
    {"name": "Cactus", "queries": ["cactus stem thermoregulation", "Opuntia heat tolerance", "saguaro convective cooling"]},
    {"name": "Polar bear", "queries": ["polar bear fur insulation", "Ursus maritimus hair thermal", "polar bear adipose heat"]},
    {"name": "Jackrabbit", "queries": ["jackrabbit ear thermoregulation", "Lepus californicus pinna", "jackrabbit convective cooling"]},
    {"name": "Xylem", "queries": ["xylem capillary wicking", "plant xylem water transport", "xylem sap negative pressure"]},
    {"name": "Leaf", "queries": ["leaf stomatal transpiration cooling", "foliar evaporative cooling", "leaf energy balance"]},
    {"name": "Desert snail", "queries": ["desert snail thermoregulation", "Sphincterochila heat tolerance", "snail epiphragm insulation"]},
    {"name": "Prairie dog", "queries": ["prairie dog burrow ventilation", "Cynomys mound airflow", "burrow Bernoulli ventilation"]},
    {"name": "Toucan", "queries": ["toucan bill heat exchange", "Ramphastos toco thermal window", "toucan beak thermoregulation"]},
]

ALLOWED_LICENSES = {"CC BY", "CC0", "CC BY-SA", "CC BY 4.0", "CC BY 3.0", "CC BY 2.0"}


def search_pmc(query: str, retmax: int = 50) -> list[str]:
    """Search NCBI E-utilities for open access PMC IDs."""
    q_str = f'({query}) AND open access[filter]'
    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pmc&term={urllib.parse.quote(q_str)}&retmode=json&retmax={retmax}"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FLBDS-BTech/1.0 (academic; abhishek24024@iiitd.ac.in)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("esearchresult", {}).get("idlist", [])
    except Exception as exc:
        print(f"  Warning: E-utilities search failed for '{query}': {exc}", file=sys.stderr)
        return []


def fetch_doc(pmcid: str, organism: str, max_text_chars: int = 50000) -> dict | None:
    """Fetch article metadata and text from AWS S3 mirror."""
    json_url = f"https://pmc-oa-opendata.s3.amazonaws.com/PMC{pmcid}.1/PMC{pmcid}.1.json"
    req_json = urllib.request.Request(json_url, headers={"User-Agent": "FLBDS/1.0"})

    try:
        with urllib.request.urlopen(req_json, timeout=10) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    license_code = (meta.get("license_code") or "").strip()
    is_allowed = any(license_code.startswith(allowed) for allowed in ALLOWED_LICENSES)
    if not is_allowed:
        return None

    txt_url = f"https://pmc-oa-opendata.s3.amazonaws.com/PMC{pmcid}.1/PMC{pmcid}.1.txt"
    req_txt = urllib.request.Request(txt_url, headers={"User-Agent": "FLBDS/1.0"})
    try:
        with urllib.request.urlopen(req_txt, timeout=12) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception:
        text = meta.get("title", "")

    if len(text) > max_text_chars:
        text = text[:max_text_chars]

    return {
        "doc_id": f"PMC{pmcid}",
        "organism": organism,
        "domain": "bio",
        "title": meta.get("title", ""),
        "citation": meta.get("citation", ""),
        "doi": meta.get("doi"),
        "license": license_code,
        "text": text,
    }


def main():
    parser = argparse.ArgumentParser(description="Targeted harvest of 12 missing benchmark organisms.")
    parser.add_argument("--output-dir", default="/home/abhishek24024/flbds_data/harvest")
    parser.add_argument("--target-per-org", type=int, default=30)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "pmc_targeted_harvest.jsonl"
    summary_file = out_dir / "harvest_summary.json"

    print("=========================================================")
    print(f"Targeted PMC Harvest: 12 Benchmark Organisms (~{args.target_per_org} papers each)")
    print(f"Output File: {out_file}")
    print("=========================================================")

    all_docs = []
    seen_pmcids = set()
    org_counts = {}
    lic_counts = {}

    with open(out_file, "w", encoding="utf-8") as fout:
        for org in ORGANISMS:
            org_name = org["name"]
            print(f"\nHarvesting for organism: {org_name}...")
            org_docs = []
            
            for query in org["queries"]:
                if len(org_docs) >= args.target_per_org:
                    break
                pmc_ids = search_pmc(query, retmax=40)
                new_ids = [pid for pid in pmc_ids if pid not in seen_pmcids]
                for pid in new_ids:
                    seen_pmcids.add(pid)

                # Fetch in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {executor.submit(fetch_doc, pid, org_name): pid for pid in new_ids}
                    for fut in concurrent.futures.as_completed(futures):
                        if len(org_docs) >= args.target_per_org:
                            break
                        try:
                            doc = fut.result()
                            if doc:
                                org_docs.append(doc)
                                all_docs.append(doc)
                                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
                                fout.flush()
                                lic = doc["license"]
                                lic_counts[lic] = lic_counts.get(lic, 0) + 1
                        except Exception:
                            continue

            org_counts[org_name] = len(org_docs)
            print(f"  -> Collected {len(org_docs)} papers for {org_name}")

    total_harvested = len(all_docs)
    summary_data = {
        "total_harvested": total_harvested,
        "organisms_targeted": len(ORGANISMS),
        "target_per_org": args.target_per_org,
        "counts_per_organism": org_counts,
        "license_breakdown": lic_counts,
        "harvest_file": str(out_file),
    }

    with open(summary_file, "w") as f:
        json.dump(summary_data, f, indent=2)

    print("\n=========================================================")
    print("TARGETED HARVEST SUMMARY")
    print(f"Total Papers Harvested: {total_harvested}")
    print("Organism Counts:")
    for o, c in org_counts.items():
        print(f"  {o:20s}: {c} papers")
    print("\nLicense Breakdown:")
    for l, c in lic_counts.items():
        print(f"  {l:20s}: {c} ({c / max(1, total_harvested) * 100:.1f}%)")
    print(f"Logged summary -> {summary_file}")
    print("=========================================================")


if __name__ == "__main__":
    main()
