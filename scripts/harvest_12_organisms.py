import urllib.request
import urllib.parse
import json
import os
from pathlib import Path

out_dir = Path("/home/abhishek24024/flbds_data/harvest/benchmark_organisms")
out_dir.mkdir(parents=True, exist_ok=True)

# 12 benchmark organisms (Latin binomial + mechanism term)
queries = {
    "TEST-M01_termite": ("Macrotermes bellicosus", "Macrotermes mound ventilation"),
    "TEST-M02_beetle": ("Stenocara gracilipes", "Stenocara fog condensation"),
    "TEST-M03_cactus": ("Opuntia microdasys", "Opuntia microdasys spine wicking"),
    "TEST-M04_polar_bear": ("Ursus maritimus", "Ursus maritimus hair insulation"),
    "TEST-M05_jackrabbit": ("Lepus californicus", "Lepus californicus ear thermoregulation"),
    "TEST-M06_tuna": ("Thunnus thynnus", "Thunnus countercurrent rete mirabile"),
    "TEST-M07_camel": ("Camelus dromedarius", "Camelus nasal turbinate heat recovery"),
    "TEST-M08_xylem": ("Pinus sylvestris", "xylem capillary transport cavitation"),
    "TEST-M09_stomata": ("Arabidopsis thaliana", "stomatal conductance transpiration cooling"),
    "TEST-M10_desert_snail": ("Sphincterochila boissieri", "Sphincterochila shell thermal reflectance"),
    "TEST-M11_prairie_dog": ("Cynomys ludovicianus", "Cynomys prairie dog burrow ventilation"),
    "TEST-M12_toucan": ("Ramphastos toco", "Ramphastos toco bill thermal radiator")
}

headers = {"User-Agent": "FLBDS_Audit/1.0 (mailto:abhishek@example.com)"}

summary = []

for tag, (organism, mech_term) in queries.items():
    # Construct Europe PMC query: OPEN_ACCESS:Y AND (LICENSE:"cc by" OR LICENSE:"cc0")
    # Clean query syntax
    query_str = f'"{organism}" AND ({mech_term}) AND (OPEN_ACCESS:Y) AND (LICENSE:"cc by" OR LICENSE:"cc0")'
    encoded_q = urllib.parse.quote(f'({mech_term}) AND (OPEN_ACCESS:Y) AND (LICENSE:"cc by" OR LICENSE:"cc0")')
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_q}&format=json&pageSize=20"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            d = json.loads(data.decode("utf-8"))
            hit_count = d.get("hitCount", 0)
            res_list = d.get("resultList", {}).get("result", [])
            
            # Save raw response
            raw_path = out_dir / f"{tag}_raw.json"
            with open(raw_path, "wb") as f_out:
                f_out.write(data)
                
            summary.append({
                "tag": tag,
                "organism": organism,
                "query": f'({mech_term}) AND (OPEN_ACCESS:Y) AND (LICENSE:"cc by" OR LICENSE:"cc0")',
                "hit_count": hit_count,
                "saved_file": str(raw_path.name),
                "num_results": len(res_list),
                "top_papers": [
                    {
                        "pmcid": r.get("pmcid", r.get("id")),
                        "title": r.get("title"),
                        "license": r.get("license", "unknown")
                    }
                    for r in res_list[:10]
                ]
            })
            print(f"[{tag}] Hits: {hit_count} | Retrieved: {len(res_list)}")
    except Exception as e:
        print(f"[{tag}] Error: {e}")
        summary.append({
            "tag": tag,
            "organism": organism,
            "query": f'({mech_term}) AND (OPEN_ACCESS:Y) AND (LICENSE:"cc by" OR LICENSE:"cc0")',
            "hit_count": 0,
            "error": str(e)
        })

summary_path = out_dir / "harvest_summary_12.json"
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"\nSaved all results to {summary_path}")
