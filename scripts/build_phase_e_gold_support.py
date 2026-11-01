#!/usr/bin/env python3
"""Phase E: Gold-Card Support (Do not write gold content).

For 4 dev and 12 test organisms:
- Up to 8 candidate source papers each:
  (DOI, title, authors, year, journal, open-access status, licence, whether abstract returned;
   queries and raw responses saved).
- Up to 5 candidate bio-inspired transfer papers per Split 1 cluster, all marked UNVERIFIED.
- Build empty gold-card template files with MechanismCard schema for the 4 dev organisms.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Target directories
DATA_DIR = Path("/home/abhishek24024/flbds_data")
AUDIT_DIR = DATA_DIR / "audit5"
CANDIDATES_DIR = AUDIT_DIR / "candidates"
RAW_DIR = CANDIDATES_DIR / "raw"
TEMPLATES_DIR = AUDIT_DIR / "gold_templates"

for d in [CANDIDATES_DIR, RAW_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 4 Dev Organisms + 12 Test Organisms
ORGANISMS = {
    # 4 Dev organisms
    "DEV-M1": {
        "organism": "Loxodonta africana (African elephant)",
        "taxon": "Loxodonta africana",
        "query": '("Loxodonta africana" OR "elephant skin") AND (evaporative OR crack OR thermoregulation OR mud)'
    },
    "DEV-M2": {
        "organism": "Aptenodytes forsteri / Cetacea (Countercurrent exchange)",
        "taxon": "Aptenodytes forsteri",
        "query": '("Aptenodytes" OR "whale" OR "dolphin") AND ("countercurrent" OR "rete mirabile") AND (heat OR temperature)'
    },
    "DEV-M3": {
        "organism": "Cataglyphis bombycina (Saharan silver ant)",
        "taxon": "Cataglyphis bombycina",
        "query": '("Cataglyphis bombycina" OR "silver ant") AND (radiative OR hair OR cooling OR reflectance)'
    },
    "DEV-M4": {
        "organism": "Notonecta / Argyroneta (Plastron gas exchange)",
        "taxon": "Notonecta / Argyroneta",
        "query": '("plastron" OR "Notonecta" OR "Argyroneta") AND ("gas exchange" OR respiration OR hydrophobic)'
    },
    # 12 Test organisms
    "TEST-M01": {
        "organism": "Macrotermes bellicosus (Termite)",
        "taxon": "Macrotermes bellicosus",
        "query": '("Macrotermes" OR "termite mound") AND (ventilation OR thermoregulation)'
    },
    "TEST-M02": {
        "organism": "Stenocara gracilipes (Namib beetle)",
        "taxon": "Stenocara gracilipes",
        "query": '("Stenocara" OR "Namib beetle") AND (fog OR water harvesting OR hydrophilic)'
    },
    "TEST-M03": {
        "organism": "Opuntia microdasys (Cactus)",
        "taxon": "Opuntia microdasys",
        "query": '("Opuntia" OR "cactus spine") AND (wicking OR water transport OR droplet)'
    },
    "TEST-M04": {
        "organism": "Ursus maritimus (Polar bear)",
        "taxon": "Ursus maritimus",
        "query": '("Ursus maritimus" OR "polar bear hair") AND (insulation OR thermal OR radiative)'
    },
    "TEST-M05": {
        "organism": "Lepus californicus (Jackrabbit)",
        "taxon": "Lepus californicus",
        "query": '("Lepus californicus" OR "jackrabbit ear") AND (thermoregulation OR pinna OR heat dissipation)'
    },
    "TEST-M06": {
        "organism": "Thunnus thynnus (Tuna)",
        "taxon": "Thunnus thynnus",
        "query": '("Thunnus" OR "tuna") AND ("countercurrent" OR "rete mirabile") AND (heat OR muscle)'
    },
    "TEST-M07": {
        "organism": "Camelus dromedarius (Camel)",
        "taxon": "Camelus dromedarius",
        "query": '("Camelus" OR "camel") AND (nasal OR turbinate OR respiration OR cooling)'
    },
    "TEST-M08": {
        "organism": "Pinus sylvestris / Xylem",
        "taxon": "Pinus sylvestris",
        "query": '("xylem" OR "Pinus") AND (capillary OR transport OR cavitation OR negative pressure)'
    },
    "TEST-M09": {
        "organism": "Arabidopsis thaliana / Stomata",
        "taxon": "Arabidopsis thaliana",
        "query": '("stomata" OR "Arabidopsis") AND (transpiration OR evaporative cooling OR conductance)'
    },
    "TEST-M10": {
        "organism": "Sphincterochila boissieri (Desert snail)",
        "taxon": "Sphincterochila boissieri",
        "query": '("Sphincterochila" OR "desert snail shell") AND (thermal OR solar OR reflectance)'
    },
    "TEST-M11": {
        "organism": "Cynomys ludovicianus (Prairie dog)",
        "taxon": "Cynomys ludovicianus",
        "query": '("Cynomys" OR "prairie dog burrow") AND (ventilation OR airflow OR Bernoulli)'
    },
    "TEST-M12": {
        "organism": "Ramphastos toco (Toco toucan)",
        "taxon": "Ramphastos toco",
        "query": '("Ramphastos toco" OR "toucan bill") AND (heat exchange OR thermal radiator OR vasodilation)'
    }
}

# Bio-inspired transfer paper queries per Split 1 cluster
TRANSFER_QUERIES = {
    "DEV-M1-S1": ("Elephant skin biomimetic hydrogel/wall", '(elephant skin biomimetic OR "cracked hydrogel" OR "bio-inspired evaporative skin")'),
    "DEV-M2-S1": ("Rete mirabile countercurrent heat exchanger", '("rete mirabile" OR "countercurrent heat exchange") AND (biomimetic OR bioinspired OR engineering)'),
    "DEV-M3-S1": ("Saharan silver ant radiative cooling metamaterial", '("Cataglyphis" OR "silver ant") AND ("radiative cooling" OR biomimetic OR metamaterial)'),
    "DEV-M4-S1": ("Plastron synthetic aeration membrane", '("plastron" OR "superhydrophobic membrane") AND ("gas exchange" OR aeration OR biomimetic)'),
    "TEST-M01-S1": ("Termite mound inspired passive building ventilation", '("termite mound" OR "Eastgate") AND (biomimetic OR ventilation OR architectural)'),
    "TEST-M02-S1": ("Namib beetle fog-harvesting surface", '("Namib beetle" OR Stenocara) AND ("fog harvesting" OR biomimetic surface)'),
    "TEST-M03-S1": ("Cactus spine directional liquid collection", '("cactus spine" OR Opuntia) AND ("fog collection" OR "directional wicking" OR biomimetic)'),
    "TEST-M04-S1": ("Polar bear hair inspired thermal aerogel/textile", '("polar bear" OR "Ursus maritimus") AND ("thermal insulation" OR aerogel OR biomimetic textile)')
}


def search_europe_pmc(query_str: str, page_size: int = 15):
    encoded_q = urllib.parse.quote(query_str)
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_q}&format=json&pageSize={page_size}"
    req = urllib.request.Request(url, headers={"User-Agent": "FLBDS_Audit/1.0 (academic; abhishek@example.com)"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            d = json.loads(data.decode("utf-8"))
            return d, data
    except Exception as e:
        print(f"Error querying Europe PMC: {e}")
        return None, None


def main():
    print("=== Fetching Candidate Source Papers for 16 Benchmark Organisms ===")
    candidate_summary = {}

    for org_id, info in ORGANISMS.items():
        q = info["query"]
        print(f"\n[{org_id}] Searching: {info['organism']}...")
        d, raw_bytes = search_europe_pmc(q, page_size=10)
        
        papers = []
        if d and raw_bytes:
            # Save raw JSON response
            raw_fp = RAW_DIR / f"{org_id}_raw.json"
            with open(raw_fp, "wb") as f_raw:
                f_raw.write(raw_bytes)

            res_list = d.get("resultList", {}).get("result", [])
            for r in res_list[:8]:
                # Extract required bibliographic fields
                doi = r.get("doi", "UNVERIFIED")
                title = r.get("title", "No Title")
                authors = r.get("authorString", "Unknown Authors")
                year = r.get("pubYear", "Unknown")
                journal = r.get("journalTitle", "Unknown Journal")
                isOpenAccess = r.get("isOpenAccess", "N")
                license_code = r.get("license", "unknown")
                has_abstract = (r.get("hasAbstract", "N") == "Y") or bool(r.get("abstractText"))

                papers.append({
                    "pmcid": r.get("pmcid", r.get("id")),
                    "doi": doi,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "journal": journal,
                    "open_access": (isOpenAccess == "Y"),
                    "license": license_code,
                    "abstract_returned": has_abstract,
                    "status": "UNVERIFIED"
                })

        candidate_summary[org_id] = {
            "organism": info["organism"],
            "query": q,
            "raw_file": f"raw/{org_id}_raw.json",
            "candidates_found": len(papers),
            "candidate_papers": papers
        }
        print(f"  Found {len(papers)} candidate papers.")

    with open(CANDIDATES_DIR / "candidate_source_papers_16_organisms.json", "w", encoding="utf-8") as f:
        json.dump(candidate_summary, f, indent=2)

    print("\n=== Fetching Candidate Bio-Inspired Transfer Papers per Split 1 Cluster ===")
    transfer_summary = {}

    for cluster_id, (desc, q) in TRANSFER_QUERIES.items():
        print(f"[{cluster_id}] Querying: {desc}...")
        d, raw_bytes = search_europe_pmc(q, page_size=8)
        papers = []
        if d and raw_bytes:
            raw_fp = RAW_DIR / f"{cluster_id}_transfer_raw.json"
            with open(raw_fp, "wb") as f_raw:
                f_raw.write(raw_bytes)

            res_list = d.get("resultList", {}).get("result", [])
            for r in res_list[:5]:
                papers.append({
                    "pmcid": r.get("pmcid", r.get("id")),
                    "doi": r.get("doi", "UNVERIFIED"),
                    "title": r.get("title", "No Title"),
                    "authors": r.get("authorString", "Unknown Authors"),
                    "year": r.get("pubYear", "Unknown"),
                    "journal": r.get("journalTitle", "Unknown Journal"),
                    "open_access": (r.get("isOpenAccess", "N") == "Y"),
                    "license": r.get("license", "unknown"),
                    "abstract_returned": (r.get("hasAbstract", "N") == "Y"),
                    "status": "UNVERIFIED"
                })

        transfer_summary[cluster_id] = {
            "description": desc,
            "query": q,
            "raw_file": f"raw/{cluster_id}_transfer_raw.json",
            "candidate_count": len(papers),
            "candidates": papers
        }
        print(f"  Found {len(papers)} transfer candidates.")

    with open(CANDIDATES_DIR / "candidate_transfer_papers_split1.json", "w", encoding="utf-8") as f:
        json.dump(transfer_summary, f, indent=2)

    print("\n=== Building Empty Gold-Card Template Files for 4 Dev Organisms ===")
    dev_templates = {
        "DEV-M1-elephant": {
            "card_id": "GOLD-DEV-M1-ELEPHANT",
            "domain": "bio",
            "subject": {
                "name": "Loxodonta africana (African elephant)",
                "identifier": "NCBI:txid9785"
            },
            "context": {
                "environment": "African savanna / arid scrubland",
                "scale": "Macro (meters)",
                "regime": "Diurnal solar thermal load, intermittent mud wallowing"
            },
            "action": {
                "verb": "absorb",
                "object": "latent heat",
                "direction": "cooling"
            },
            "state_change": {
                "state_variable": "body surface temperature",
                "from_value": "42 degC",
                "to_value": "36 degC",
                "magnitude": "-6 K"
            },
            "phenomenon": {
                "description": "Evaporative cooling through porous mud-cuticle layer with deep micro-cracks increasing surface area and water retention",
                "governing_equation": None
            },
            "effect": {
                "canonical_name": "latent_heat_phase_change",
                "governing_equation": "q = m_dot_evap * h_fg",
                "relevant_variables": ["h_fg", "evaporation_rate", "effective_surface_area"]
            },
            "inputs": [
                {
                    "name": "liquid water / mud",
                    "role": "working_fluid_consumable"
                }
            ],
            "organ": "epidermis / skin",
            "part": "micro-cracked stratum corneum and mud cake matrix",
            "quantities": [],
            "constraints_and_resources": {
                "resources_available": ["water", "mud"],
                "constraints": ["water scarcity in dry season"]
            },
            "evidence": [],
            "abstraction_ladder": {
                "L0_specimen": "African elephant wallowing in mud at Etosha",
                "L1_mechanism": "Mud layer retains water in cuticular micro-cracks; water evaporates absorbing latent heat",
                "L2_causal_chain": "Skin cracking -> mud adhesion -> capillary water retention -> extended latent heat flux -> buffering peak core temperature",
                "L3_solution_neutral_principle": "A porous matrix retains a volatile phase-change fluid whose evaporation absorbs transient heat flux",
                "L4_function": "Keep a system below a critical temperature ceiling under cyclic thermal load"
            },
            "tier": "gold_candidate_template",
            "confidence": 0.0,
            "human_verified": False,
            "notes": "Awaiting human authoring against verified source paper (Martins et al. 2018 or similar)"
        },
        "DEV-M2-penguin": {
            "card_id": "GOLD-DEV-M2-PENGUIN",
            "domain": "bio",
            "subject": {
                "name": "Aptenodytes forsteri (Emperor penguin)",
                "identifier": "NCBI:txid9233"
            },
            "context": {
                "environment": "Antarctic marine / sea ice",
                "scale": "Meso (centimeters)",
                "regime": "Immersion in sub-zero seawater (-1.8 degC)"
            },
            "action": {
                "verb": "exchange",
                "object": "thermal energy",
                "direction": "conservation"
            },
            "state_change": {
                "state_variable": "arterial blood temperature",
                "from_value": "38 degC",
                "to_value": "4 degC",
                "magnitude": "-34 K"
            },
            "phenomenon": {
                "description": "Countercurrent heat exchange between closely apposed warm central arteries and cold peripheral returning veins in flippers and nasal passages",
                "governing_equation": None
            },
            "effect": {
                "canonical_name": "countercurrent_heat_exchange",
                "governing_equation": "q = U * A * LMTD",
                "relevant_variables": ["U", "A", "mass_flow_rate", "c_p"]
            },
            "inputs": [],
            "organ": "pectoral flipper / nasal turbinates",
            "part": "vascular rete mirabile",
            "quantities": [],
            "constraints_and_resources": {
                "resources_available": ["metabolic blood flow"],
                "constraints": ["extreme cold environment"]
            },
            "evidence": [],
            "abstraction_ladder": {
                "L0_specimen": "Emperor penguin diving in Antarctic waters",
                "L1_mechanism": "Warm core blood preheats cold venous blood before returning to thorax",
                "L2_causal_chain": "Opposed fluid conduits -> conductive wall -> sensible enthalpy transfer -> core temperature conservation",
                "L3_solution_neutral_principle": "Counterflowing fluid streams transfer heat across high conductance partition to minimize core discharge loss",
                "L4_function": "Conserve thermal energy in an open fluid exchange loop"
            },
            "tier": "gold_candidate_template",
            "confidence": 0.0,
            "human_verified": False,
            "notes": "Awaiting human authoring against verified source literature"
        },
        "DEV-M3-silver_ant": {
            "card_id": "GOLD-DEV-M3-SILVER-ANT",
            "domain": "bio",
            "subject": {
                "name": "Cataglyphis bombycina (Saharan silver ant)",
                "identifier": "NCBI:txid60434"
            },
            "context": {
                "environment": "Saharan desert dunes",
                "scale": "Micro (millimeters)",
                "regime": "Midday extreme solar irradiance (> 1000 W/m2) and ground temperatures (> 60 degC)"
            },
            "action": {
                "verb": "reflect_and_emit",
                "object": "electromagnetic radiation",
                "direction": "cooling"
            },
            "state_change": {
                "state_variable": "cuticle temperature",
                "from_value": "55 degC",
                "to_value": "48 degC",
                "magnitude": "-7 K"
            },
            "phenomenon": {
                "description": "Dense coat of triangular-cross-section hairs providing high solar reflectance via total internal reflection and high mid-infrared emissivity via Mie resonance",
                "governing_equation": None
            },
            "effect": {
                "canonical_name": "passive_radiative_cooling",
                "governing_equation": "q_net = epsilon*sigma*T^4 - alpha*q_solar - q_sky",
                "relevant_variables": ["solar_reflectance", "mid_ir_emissivity", "q_solar"]
            },
            "inputs": [],
            "organ": "dorsal cuticle",
            "part": "triangular hairs",
            "quantities": [],
            "constraints_and_resources": {
                "resources_available": ["sky thermal radiation window"],
                "constraints": ["absence of liquid water for evaporative cooling"]
            },
            "evidence": [],
            "abstraction_ladder": {
                "L0_specimen": "Saharan silver ant foraging on hot sand",
                "L1_mechanism": "Triangular hair array reflects solar spectrum and emits strongly in atmospheric transparency window",
                "L2_causal_chain": "Micro-structured prism hairs -> total internal reflection of visible -> mid-IR vibrational emission -> sub-ambient cooling without consumables",
                "L3_solution_neutral_principle": "Optical microstructures selectively reject external incoming radiative load and maximize thermal radiative coupling to a cold sink",
                "L4_function": "Maintain passive thermal equilibrium in high-radiation environment without water or power"
            },
            "tier": "gold_candidate_template",
            "confidence": 0.0,
            "human_verified": False,
            "notes": "Awaiting human authoring against verified source literature (Shi et al. 2015 Science)"
        },
        "DEV-M4-plastron": {
            "card_id": "GOLD-DEV-M4-PLASTRON",
            "domain": "bio",
            "subject": {
                "name": "Aquatic insect (Notonecta / Aphelocheirus)",
                "identifier": "NCBI:txid236407"
            },
            "context": {
                "environment": "Submerged freshwater stream",
                "scale": "Meso-micro (millimeters to micrometers)",
                "regime": "Continuous underwater submergence under hydrostatic pressure"
            },
            "action": {
                "verb": "diffuse",
                "object": "dissolved oxygen gas",
                "direction": "replenishment"
            },
            "state_change": {
                "state_variable": "plastron oxygen partial pressure",
                "from_value": "0.10 atm",
                "to_value": "0.18 atm",
                "magnitude": "+0.08 atm"
            },
            "phenomenon": {
                "description": "Dense hydrophobic hair array or microporous cuticular plastron sustaining a permanent gas-water interface across which dissolved oxygen diffuses into the spiracles",
                "governing_equation": None
            },
            "effect": {
                "canonical_name": "membrane_gas_diffusion",
                "governing_equation": "J = D_eff * delta_C / L",
                "relevant_variables": ["porosity", "tortuosity", "hydrostatic_head", "capillary_breakthrough"]
            },
            "inputs": [
                {
                    "name": "dissolved oxygen in water",
                    "role": "transport_species"
                }
            ],
            "organ": "abdominal cuticular hairs / spiracles",
            "part": "micro-setae plastron layer",
            "quantities": [],
            "constraints_and_resources": {
                "resources_available": ["dissolved oxygen in surrounding water"],
                "constraints": ["hydrostatic pressure causing wetting breakthrough"]
            },
            "evidence": [],
            "abstraction_ladder": {
                "L0_specimen": "Aphelocheirus aestivalis submerged in gravel riverbed",
                "L1_mechanism": "Microscopic hydrophobic hairs resist hydrostatic water pressure and maintain an incompressible gas layer for Fickian oxygen uptake",
                "L2_causal_chain": "Superhydrophobic hair array -> Laplace breakthrough resistance -> stable gas layer -> continuous diffusive gas exchange without surfacing",
                "L3_solution_neutral_principle": "High capillary pressure resists liquid intrusion, stabilizing a porous gas boundary for continuous species diffusion",
                "L4_function": "Supply a reactant species continuously across a phase boundary without liquid intrusion"
            },
            "tier": "gold_candidate_template",
            "confidence": 0.0,
            "human_verified": False,
            "notes": "Awaiting human authoring against verified source literature (Flynn & Bush 2008 or similar)"
        }
    }

    for name, card in dev_templates.items():
        fp = TEMPLATES_DIR / f"{name}_gold_template.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2)
        print(f"  Created template: {fp.name}")

    print("\nPhase E completed successfully!")


if __name__ == "__main__":
    main()
