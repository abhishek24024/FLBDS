#!/usr/bin/env python3
"""scripts/export_bio_papers.py
Extracts biological research papers from the pilot corpus (PMC open-access papers)
and benchmark API records, generating clean Markdown and JSON files with an index.
"""

import json
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent
    server_data_dir = Path("/home/abhishek24024/flbds_data") if Path("/home/abhishek24024/flbds_data").is_dir() else repo_root / "flbds_data"
    corpus_file = server_data_dir / "corpus" / "bio_pilot.jsonl"
    api_dir = server_data_dir / "api_responses"
    out_dir = server_data_dir / "biological_papers"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = []

    # 1. Benchmark Organism Foundation Papers
    benchmark_specs = [
        {
            "tag": "DEV-M1_elephant_skin_martins2018",
            "file": "martins_2018_openalex.json",
            "organism": "Loxodonta africana (African Elephant)",
            "mechanism": "Skin cracking & mud-wallowing for evaporation and thermal buffering",
            "benchmark_cluster": "DEV-M1",
        },
        {
            "tag": "DEV-M2_countercurrent_bundle_scholander1955",
            "file": "scholander_1955_openalex.json",
            "organism": "Aptenodytes forsteri / Cetaceans (Penguin / Whale extremity)",
            "mechanism": "Appendicular countercurrent vascular rete (artery surrounded by venous channels)",
            "benchmark_cluster": "DEV-M2",
        },
        {
            "tag": "DEV-M3_silver_ant_cooling_shi2015",
            "file": "shi_2015_openalex.json",
            "organism": "Cataglyphis bombycina (Saharan Silver Ant)",
            "mechanism": "Triangular cross-section hair arrays for solar reflection & mid-IR passive radiative cooling",
            "benchmark_cluster": "DEV-M3",
        },
        {
            "tag": "DEV-M4_underwater_plastron_flynn2008",
            "file": "flynn_bush_2008_openalex.json",
            "organism": "Aphelocheirus aestivalis (Plastron Insect)",
            "mechanism": "Hydrophobic micro-pore plastron gill for underwater diffusive gas exchange",
            "benchmark_cluster": "DEV-M4",
        },
        {
            "tag": "DEV-M4_superhydrophobic_plastron_shirtcliffe2006",
            "file": "shirtcliffe_2006_openalex.json",
            "organism": "Submerged Arthropods / Bio-inspired Plastron",
            "mechanism": "Capillary breakthrough pressure and Laplace retention in porous plastrons",
            "benchmark_cluster": "DEV-M4",
        },
    ]

    for b in benchmark_specs:
        p_path = api_dir / b["file"]
        if p_path.is_file():
            with open(p_path, "r", encoding="utf-8") as f:
                d = json.load(f)

            title = d.get("title", "Untitled")
            doi = d.get("doi", "N/A")
            year = d.get("publication_year", "N/A")
            venue = d.get("primary_location", {}).get("source", {}).get("display_name", "N/A")

            # Reconstruct OpenAlex inverted abstract
            abs_inv = d.get("abstract_inverted_index")
            abstract = ""
            if abs_inv:
                pos_list = []
                for word, indices in abs_inv.items():
                    for idx in indices:
                        pos_list.append((idx, word))
                pos_list.sort()
                abstract = " ".join(w for _, w in pos_list)
            else:
                abstract = "Full abstract available in DOI link."

            md_text = f"# {title}\n\n"
            md_text += f"- **Target Benchmark**: `{b['benchmark_cluster']}`\n"
            md_text += f"- **Biological Model**: *{b['organism']}*\n"
            md_text += f"- **Physical Mechanism**: {b['mechanism']}\n"
            md_text += f"- **Publication Year**: {year}\n"
            md_text += f"- **Journal / Venue**: {venue}\n"
            md_text += f"- **DOI**: [{doi}]({doi})\n\n"
            md_text += f"## Abstract\n\n{abstract}\n\n"
            md_text += f"## Benchmark Relevance\n\n"
            md_text += f"This foundation paper provides the authoritative biological ground truth for **{b['benchmark_cluster']}** in FLBDS v9.\n"
            md_text += f"See `{b['tag']}.json` for the complete API response metadata.\n"

            with open(out_dir / f"{b['tag']}.md", "w", encoding="utf-8") as f:
                f.write(md_text)

            with open(out_dir / f"{b['tag']}.json", "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)

            manifest.append({
                "id": b["tag"],
                "title": title,
                "category": f"Benchmark Foundation ({b['benchmark_cluster']})",
                "organism": b["organism"],
                "mechanism": b["mechanism"],
                "year_venue": f"{year} ({venue})",
                "doi": doi,
                "md_file": f"{b['tag']}.md",
                "json_file": f"{b['tag']}.json",
            })

    # 2. Pilot Corpus Full-Text Research Papers (PMC Open Access)
    target_pmc_ids = [
        ("PMC8531342", "Personal Perspiration & Conduction", "i-Cool textile coupling heat conduction and sweat transportation"),
        ("PMC8593863", "Wicking & Microfluidics", "Bicomponent cellulose fibrils and mineral wicking channels for fluid transport"),
        ("PMC13658535", "Insect Thermoregulation", "TRP channel activation and cholinergic signaling in American cockroach thermoregulation"),
        ("PMC13348343", "Janus Film Thermoregulation", "Adaptive and highly efficient thermoregulation based on multi-dimensional Janus film"),
        ("PMC13632099", "Ectotherm Behavioural Cooling", "Experimental evidence for behavioural cooling in response to thermal stress"),
        ("PMC13574850", "Coat-Mediated Thermoregulation", "Morphophysiological profiles and thermal regulation in dark-coated sheep"),
        ("PMC13508986", "Avian Heat Exchange", "Bioenergetic dynamics of convective and evaporative heat exchange in Japanese quail"),
        ("PMC13488905", "Evaporative Cooling in Arid Heat", "Perspiration vapor dynamics and human evaporative cooling limitations in arid climates"),
        ("PMC13547889", "Ectotherm Thermal Ecology", "Thermal ecology and basking/cooling thermoregulatory behavior in invasive turtles"),
        ("PMC13336401", "Passive Radiative Cooling", "Intrinsic coupling of radiative surface cooling and triboelectric response"),
    ]

    target_map = {pmc_id: (cat, mech) for pmc_id, cat, mech in target_pmc_ids}

    if corpus_file.is_file():
        with open(corpus_file, "r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                doc_id = d.get("doc_id")
                if doc_id in target_map:
                    cat, mech = target_map[doc_id]
                    title = d.get("title", "Untitled")
                    abstract = d.get("abstract", "")
                    text = d.get("text", "")
                    doi = d.get("doi", "N/A")
                    journal = d.get("journal", "PubMed Central")
                    license_str = d.get("license", "CC BY")

                    md_text = f"# {title}\n\n"
                    md_text += f"- **Document ID**: `{doc_id}`\n"
                    md_text += f"- **Category**: {cat}\n"
                    md_text += f"- **Biological Mechanism**: {mech}\n"
                    md_text += f"- **Journal**: {journal}\n"
                    md_text += f"- **DOI**: [{doi}](https://doi.org/{doi})\n"
                    md_text += f"- **License**: {license_str}\n\n"
                    md_text += f"## Abstract\n\n{abstract}\n\n"
                    md_text += f"## Full Article Text\n\n{text}\n"

                    with open(out_dir / f"{doc_id}.md", "w", encoding="utf-8") as f:
                        f.write(md_text)

                    with open(out_dir / f"{doc_id}.json", "w", encoding="utf-8") as f:
                        json.dump(d, f, indent=2)

                    manifest.append({
                        "id": doc_id,
                        "title": title,
                        "category": f"Corpus Paper ({cat})",
                        "organism": "Biological System / Biomimetic Mechanism",
                        "mechanism": mech,
                        "year_venue": journal,
                        "doi": doi,
                        "md_file": f"{doc_id}.md",
                        "json_file": f"{doc_id}.json",
                    })

    # Save manifest.json
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Save INDEX.md
    index_md = []
    index_md.append("# Biological Research Papers Archive")
    index_md.append("")
    index_md.append("Curated collection of biological research papers from the FLBDS corpus and benchmark foundation literature, including full text, abstracts, and physical mechanism annotations.")
    index_md.append("")
    index_md.append("| Paper ID | Target / Category | Organism & Mechanism | Publication Venue | Markdown Text |")
    index_md.append("| :--- | :--- | :--- | :--- | :--- |")
    for m in manifest:
        index_md.append(f"| `{m['id']}` | **{m['category']}** | *{m['organism']}*<br>{m['mechanism']} | {m['year_venue']} | [{m['id']}.md]({m['md_file']}) |")
    index_md.append("")

    with open(out_dir / "INDEX.md", "w", encoding="utf-8") as f:
        f.write("\n".join(index_md))

    print(f"Successfully generated {len(manifest)} biological papers and index in {out_dir}")

if __name__ == "__main__":
    main()
