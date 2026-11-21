#!/usr/bin/env python3
"""Save Seed 31 15-Card Review Artifact for Audit 5."""

import json
from pathlib import Path

AUDIT5_DIR = Path("/home/abhishek24024/flbds_data/audit5")
AUDIT5_DIR.mkdir(parents=True, exist_ok=True)

RECORDS = [
    {
        "index": 1,
        "doc_id": "PMC11547354",
        "domain": "bio",
        "title": "Study on Phase Change Materials’ Heat Transfer Characteristics of Medium Temperature Solar Energy Collection System",
        "subject": None,
        "action": "store",
        "direction": "thermal energy",
        "effect": "latent_heat_storage",
        "quantities_count": 2,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Subject field is completely omitted (None) despite paper describing an engineered solar PCM collector.",
        "flaw_source_passage": "A medium-temperature solar energy collection system is investigated using blended phase change materials (PCMs) in a thermal storage tank.",
        "verified_substring": True
    },
    {
        "index": 2,
        "doc_id": "US-PAT-F-0295",
        "domain": "eng",
        "title": "A viscous fluid type heater including a heating chamber and a heat exchange chamber...",
        "subject": "Viscous Fluid Shearing and Heat Transfer",
        "action": "shear",
        "direction": "heating",
        "effect": "viscous_dissipation",
        "quantities_count": 0,
        "usefulness": 4,
        "verdict": "GOOD",
        "flaw_reason": None,
        "flaw_source_passage": None,
        "verified_substring": True
    },
    {
        "index": 3,
        "doc_id": "PMC12985825",
        "domain": "bio",
        "title": "Composite Adsorbent “1-Ethyl-3-methylimidazolium Acetate [EMIM] [Ac] into Mesoporous Silica Gel” for Adsorption Heat Storage",
        "subject": "Silica/[EMIM-Ac] Composite Adsorbent",
        "action": "adsorb",
        "direction": "water vapor uptake",
        "effect": "physical_adsorption_and_absorption",
        "quantities_count": 4,
        "usefulness": 5,
        "verdict": "GOOD",
        "flaw_reason": None,
        "flaw_source_passage": None,
        "verified_substring": True,
        "overlap_seed11_verdict": "GOOD"
    },
    {
        "index": 4,
        "doc_id": "US-PAT-F-0107",
        "domain": "eng",
        "title": "Provided, among other things, is a method of drying lumber comprising: igniting landfill gas...",
        "subject": None,
        "action": "ignite",
        "direction": "combustion gas generation",
        "effect": "heat_transfer_convection",
        "quantities_count": 1,
        "usefulness": 2,
        "verdict": "MINOR",
        "flaw_reason": "Action verb is chemical combustion ('ignite') rather than physical transport; subject field is omitted.",
        "flaw_source_passage": "igniting landfill gas to directly or indirectly create a heated gas or heat exchange medium; and directing the heated gas or heat exchange medium to the lumber drying kiln",
        "verified_substring": True
    },
    {
        "index": 5,
        "doc_id": "PMC13348343",
        "domain": "bio",
        "title": "Adaptive and Highly Efficient Thermoregulation Based on Multi‐Dimensional Janus Film",
        "subject": None,
        "action": "regulate",
        "direction": "temperature",
        "effect": "radiative_cooling_and_solar_heating",
        "quantities_count": 5,
        "usefulness": 4,
        "verdict": "MINOR",
        "flaw_reason": "Subject field is omitted (None) despite paper describing a multi-dimensional Janus radiative cooling film.",
        "flaw_source_passage": "Here, a multi-dimensional Janus film with reversible asymmetric radiation and thermal conduction is developed for adaptive thermoregulation.",
        "verified_substring": True
    },
    {
        "index": 6,
        "doc_id": "PMC11882818",
        "domain": "bio",
        "title": "Thermal and environmental analysis of Cucumis sativus drying in a hybrid greenhouse dryer",
        "subject": None,
        "action": "dry",
        "direction": "moisture removal",
        "effect": "convective_heat_and_mass_transfer",
        "quantities_count": 0,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Subject field omitted; mechanism describes agricultural crop drying rather than an organism thermal regulation adaptation.",
        "flaw_source_passage": "The experimental evaluation of drying Cucumis sativus in a mixed-mode greenhouse dryer under forced convection was conducted.",
        "verified_substring": True,
        "overlap_seed11_verdict": "MINOR"
    },
    {
        "index": 7,
        "doc_id": "PMC13336753",
        "domain": "bio",
        "title": "Breaking the Trade‐Off of Mechanical Robustness and Energy Storage Capacity in Phase Change Materials...",
        "subject": "Hard-Segment-Anchored/Side-Chain-Storage Polyurethane PCM",
        "action": "store",
        "direction": "latent heat",
        "effect": "latent_heat_storage",
        "quantities_count": 0,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Synthetic polyurethane polymer composite categorized under biological domain; lacks natural organism physiology.",
        "flaw_source_passage": "A molecular design strategy of hard-segment-anchored/side-chain-storage polyurethane solid-solid phase change materials is proposed.",
        "verified_substring": True,
        "overlap_seed11_verdict": "MINOR"
    },
    {
        "index": 8,
        "doc_id": "US-PAT-E-0402",
        "domain": "eng",
        "title": "A section of the wall has a plurality of interspaced structural members...",
        "subject": None,
        "action": "insulate",
        "direction": "heat flux reduction",
        "effect": "conductive_heat_flux_reduction",
        "quantities_count": 0,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Subject field omitted (None). Architectural wall framing insulation.",
        "flaw_source_passage": "A section of the wall has a plurality of interspaced structural members and an insulating batten disposed between adjacent members.",
        "verified_substring": True
    },
    {
        "index": 9,
        "doc_id": "PMC13363476",
        "domain": "bio",
        "title": "Comparative Analysis of Porous Alkali-Activated Composites Modified by Plant Biomass",
        "subject": "Alkali-Activated Composite with Plant Biomass",
        "action": "insulate",
        "direction": "conduction reduction",
        "effect": "thermal_insulation_porous_media",
        "quantities_count": 1,
        "usefulness": 4,
        "verdict": "GOOD",
        "flaw_reason": None,
        "flaw_source_passage": None,
        "verified_substring": True
    },
    {
        "index": 10,
        "doc_id": "PMC11820987",
        "domain": "bio",
        "title": "Bamboo–PCM: Comparative Analysis of Phase Change Material-Impregnated Bamboo...",
        "subject": "PCM-Impregnated Bamboo (Dendrocalamus giganteus)",
        "action": "store",
        "direction": "thermal energy",
        "effect": "latent_heat_accumulation",
        "quantities_count": 0,
        "usefulness": 4,
        "verdict": "GOOD",
        "flaw_reason": None,
        "flaw_source_passage": None,
        "verified_substring": True
    },
    {
        "index": 11,
        "doc_id": "PMC12155899",
        "domain": "bio",
        "title": "Geopolymer Concretes with Organic Phase Change Materials—Analysis of Thermal Properties and Microstructure",
        "subject": "Geopolymer Concrete with Organic PCMs",
        "action": "store",
        "direction": "thermal energy",
        "effect": "latent_heat_storage",
        "quantities_count": 0,
        "usefulness": 4,
        "verdict": "GOOD",
        "flaw_reason": None,
        "flaw_source_passage": None,
        "verified_substring": True
    },
    {
        "index": 12,
        "doc_id": "PMC13264069",
        "domain": "bio",
        "title": "Fabrication and thermal performance of ternary fatty acid/expanded graphite form–stable composite phase change materials",
        "subject": None,
        "action": "store",
        "direction": "latent heat",
        "effect": "latent_heat_storage",
        "quantities_count": 4,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Subject field omitted (None). High quality phase change enthalpy data otherwise verified.",
        "flaw_source_passage": "Form-stable composite phase change materials (CPCMs) were fabricated by vacuum impregnation of ternary fatty acid into expanded graphite.",
        "verified_substring": True
    },
    {
        "index": 13,
        "doc_id": "US-PAT-F-0251",
        "domain": "eng",
        "title": "An improved refrigeration evaporator having a first heat exchange element...",
        "subject": None,
        "action": "subcool",
        "direction": "liquid refrigerant",
        "effect": "heat_exchange",
        "quantities_count": 0,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Subject field omitted (None). Refrigeration cycle subcooling heat exchange.",
        "flaw_source_passage": "The evaporator comprises first heat transfer means for receiving the high pressure refrigerant liquid from the condensing unit and subcooling said liquid.",
        "verified_substring": True
    },
    {
        "index": 14,
        "doc_id": "US-PAT-F-0179",
        "domain": "eng",
        "title": "The invention relates to a refrigerant accumulator combined with a heat exchanger for a motor vehicle",
        "subject": None,
        "action": "regulate",
        "direction": "refrigerant flow",
        "effect": "pressure_difference_valve_operation",
        "quantities_count": 0,
        "usefulness": 3,
        "verdict": "MINOR",
        "flaw_reason": "Subject field omitted (None). Mechanical valve control for accumulator.",
        "flaw_source_passage": "The valve can open its passage either based on a pressure difference between the collector and the flow channel, or on the basis of a control signal.",
        "verified_substring": True
    },
    {
        "index": 15,
        "doc_id": "PMC9318119",
        "domain": "bio",
        "title": "Wicking in Porous Polymeric Membranes: Determination of an Effective Capillary Radius...",
        "subject": "Capillary-Driven Wicking in Porous Polymeric Membranes",
        "action": "wick",
        "direction": "liquid sample",
        "effect": "capillary_suction_pressure",
        "quantities_count": 0,
        "usefulness": 5,
        "verdict": "GOOD",
        "flaw_reason": None,
        "flaw_source_passage": None,
        "verified_substring": True,
        "overlap_seed11_verdict": "GOOD"
    }
]

out = {
    "seed": 31,
    "sample_size": 15,
    "counts": {
        "GOOD": 6,
        "MINOR": 9,
        "MAJOR": 0
    },
    "rates": {
        "GOOD": {"rate": 6/15, "wilson_95_ci": [0.198, 0.643]},
        "MINOR": {"rate": 9/15, "wilson_95_ci": [0.357, 0.802]},
        "MAJOR": {"rate": 0/15, "wilson_95_ci": [0.000, 0.204]}
    },
    "overlap_with_seed11": {
        "total_overlapping": 4,
        "agreement_count": 4,
        "agreement_rate": 1.0,
        "comparisons": [
            {"doc_id": "PMC12985825", "seed11": "GOOD", "seed31": "GOOD"},
            {"doc_id": "PMC11882818", "seed11": "MINOR", "seed31": "MINOR"},
            {"doc_id": "PMC13336753", "seed11": "MINOR", "seed31": "MINOR"},
            {"doc_id": "PMC9318119", "seed11": "GOOD", "seed31": "GOOD"}
        ]
    },
    "audited_cards": RECORDS
}

with open(AUDIT5_DIR / "seed31_human_review_15.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print("Saved seed31_human_review_15.json")
