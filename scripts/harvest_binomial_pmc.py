#!/usr/bin/env python3
"""Item 5: Query Europe PMC with explicit CC BY or CC0 filter using Latin binomials."""

import json
import urllib.parse
import urllib.request
import time
from pathlib import Path

ORGANISM_QUERIES = [
    ("Cactus", "Opuntia microdasys spine wicking"),
    ("Penguin", "Aptenodytes forsteri countercurrent"),
    ("Termite", "Macrotermes bellicosus mound ventilation"),
    ("Namib beetle", "Stenocara gracilipes fog water"),
    ("Polar bear", "Ursus maritimus hair insulation"),
    ("Jackrabbit", "Lepus californicus pinna"),
    ("Camel", "Camelus dromedarius nasal cooling"),
    ("Tuna", "Thunnus thynnus rete mirabile"),
    ("Xylem", "xylem capillary transport cavitation"),
    ("Leaf", "stomatal evaporative cooling transpiration"),
    ("Desert snail", "Sphincterochila boissieri solar"),
    ("Prairie dog", "Cynomys ludovicianus burrow ventilation"),
]

def query_europe_pmc(query_str: str, max_results: int = 20) -> dict:
    # Explicit CC BY or CC0 filter
    license_filter = '(LICENSE:"cc by" OR LICENSE:"cc0" OR LICENSE:"cc-by")'
    full_query = f'{query_str} AND OPEN_ACCESS:Y AND {license_filter}'
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(full_query)}&format=json&pageSize={max_results}&resultType=core"
    
    req = urllib.request.Request(url, headers={"User-Agent": "FLBDS_Binomial_Audit/1.0 (mailto:abhishek24024@iiitd.ac.in)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            hit_count = data.get("hitCount", 0)
            items = data.get("resultList", {}).get("result", [])
            return {
                "status": "OK",
                "url": url,
                "hit_count": hit_count,
                "items": items
            }
    except Exception as e:
        return {"status": "ERROR", "url": url, "error": str(e), "hit_count": 0, "items": []}

def main():
    print("=== EUROPE PMC EXPLICIT CC BY / CC0 LATIN BINOMIAL HARVEST ===")
    summary = {}
    detailed_top3 = {}
    all_harvested = []

    for name, q in ORGANISM_QUERIES:
        res = query_europe_pmc(q, max_results=20)
        hits = res["hit_count"]
        items = res["items"]
        summary[name] = {
            "query": q,
            "hits": hits,
            "harvested_count": len(items),
            "status": res["status"]
        }
        print(f"[{name}] '{q}': {hits} hits, retrieved {len(items)}")

        # Store top 10 titles for Cactus, Penguin, and Termite
        if name in ["Cactus", "Penguin", "Termite"]:
            detailed_top3[name] = [
                {
                    "pmcid": it.get("pmcid", it.get("id")),
                    "title": it.get("title", "No title"),
                    "journal": it.get("journalTitle", ""),
                    "pubYear": it.get("pubYear", "")
                }
                for it in items[:10]
            ]

        for it in items:
            all_harvested.append({
                "organism": name,
                "query": q,
                "doc_id": it.get("pmcid", it.get("id")),
                "title": it.get("title", ""),
                "doi": it.get("doi", ""),
                "license": it.get("license", "CC BY / CC0"),
                "abstract": it.get("abstractText", ""),
                "journal": it.get("journalTitle", ""),
                "pubYear": it.get("pubYear", "")
            })
        time.sleep(0.5)

    out_dir = Path("/home/abhishek24024/flbds_data/harvest")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pmc_binomial_harvest.jsonl"
    with open(out_path, "w") as f:
        for p in all_harvested:
            f.write(json.dumps(p) + "\n")

    summary_path = out_dir / "binomial_harvest_summary.json"
    with open(summary_path, "w") as f:
        json.dump({
            "summary_per_organism": summary,
            "detailed_top10_three_organisms": detailed_top3
        }, f, indent=2)

    print(f"\nSaved {len(all_harvested)} papers to {out_path}")
    print(f"Saved summary to {summary_path}")

if __name__ == "__main__":
    main()
