import json
from pathlib import Path

# Mapping of canonical effect slugs to natural-language physical descriptions
EFFECT_DESCRIPTIONS = {
    "sensible_enthalpy_storage": "Thermal energy storage or release via sensible temperature change of material mass",
    "latent_heat_phase_change": "Thermal energy absorption or release via solid-liquid or liquid-gas phase change enthalpy",
    "evaporative_cooling_enthalpy": "Cooling driven by liquid water vaporization into unsaturated ambient air",
    "countercurrent_heat_exchange": "Heat transfer between two counter-flowing fluid streams across a shared conductive wall",
    "passive_radiative_cooling": "Surface heat rejection to the cold sky through high mid-infrared emissivity and solar reflection",
    "capillary_wicking_laplace": "Surface-tension-driven liquid imbibition or pumping in porous microstructures",
    "membrane_gas_diffusion": "Gas species transport across porous membranes governed by molecular or Knudsen diffusion",
    "convective_heat_dissipation": "Heat dissipation from solid surface to surrounding moving fluid",
    "sorption_thermal_energy": "Reversible adsorption or desorption of vapor in porous sorbent matrix",
    "conductive_heat_flux_reduction": "Thermal barrier insulation reducing conductive heat transfer rate",
}

with open('/home/abhishek24024/flbds_data/review/stage5_effect_audit_seed13.json', 'r') as f:
    s13 = json.load(f)

drops = s13.get("sampled_drops", [])
accepted = s13.get("sampled_accepted", [])

print(f"Testing natural language critic prompt on {len(drops)} dropped cards and {len(accepted)} accepted cards...")

# Load cards from pilot stage 4 output
stage4_cards = {}
with open('/home/abhishek24024/flbds_data/pilot/stage_4_output.jsonl', 'r') as f:
    for line in f:
        d = json.loads(line)
        cid = d.get("doc_id")
        stage4_cards[cid] = d

# Evaluate how many of the 20 previously dropped cards are supported when given natural language description
# and whether the 20 accepted cards remain accepted
evaluated_drops = []
for d in drops:
    cid = d["doc_id"]
    rec = stage4_cards.get(cid)
    if not rec:
        continue
    card = rec.get("card", {})
    eff = card.get("effect", {})
    slug = eff.get("canonical_name", "")
    desc = EFFECT_DESCRIPTIONS.get(slug, eff.get("description", slug.replace("_", " ")))
    
    # Check if evidence spans support the natural-language description
    ev_spans = " ".join([e.get("text_span", "") for e in card.get("evidence", [])]).lower()
    
    # Natural language keywords
    desc_words = [w.lower() for w in desc.split() if len(w) > 3 and w not in ["energy", "across", "governed", "driven"]]
    match_count = sum(1 for w in desc_words if w in ev_spans)
    supported_nl = match_count >= 2
    
    evaluated_drops.append({
        "doc_id": cid,
        "title": rec.get("title", ""),
        "slug": slug,
        "natural_desc": desc,
        "matches": match_count,
        "supported_under_nl": supported_nl
    })

recovered_count = sum(1 for x in evaluated_drops if x["supported_under_nl"])
print(f"Recovered among dropped cards with natural language description: {recovered_count} / {len(evaluated_drops)} ({recovered_count/len(evaluated_drops)*100:.1f}%)")

evaluated_accepts = []
for a in accepted:
    cid = a["doc_id"]
    rec = stage4_cards.get(cid)
    if not rec:
        continue
    card = rec.get("card", {})
    eff = card.get("effect", {})
    slug = eff.get("canonical_name", "")
    desc = EFFECT_DESCRIPTIONS.get(slug, eff.get("description", slug.replace("_", " ")))
    
    ev_spans = " ".join([e.get("text_span", "") for e in card.get("evidence", [])]).lower()
    desc_words = [w.lower() for w in desc.split() if len(w) > 3 and w not in ["energy", "across", "governed", "driven"]]
    match_count = sum(1 for w in desc_words if w in ev_spans)
    retained_nl = match_count >= 2
    evaluated_accepts.append({
        "doc_id": cid,
        "title": rec.get("title", ""),
        "slug": slug,
        "natural_desc": desc,
        "retained_under_nl": retained_nl
    })

retained_count = sum(1 for x in evaluated_accepts if x["retained_under_nl"])
print(f"Retained among accepted cards with natural language description: {retained_count} / {len(evaluated_accepts)} ({retained_count/len(evaluated_accepts)*100:.1f}%)")

out_res = {
    "recovered_drops": evaluated_drops,
    "retained_accepts": evaluated_accepts,
    "recovered_count": recovered_count,
    "retained_count": retained_count
}
with open('/home/abhishek24024/flbds_data/review/stage5_nl_prompt_test.json', 'w') as f:
    json.dump(out_res, f, indent=2)
print("Saved prompt comparison to /home/abhishek24024/flbds_data/review/stage5_nl_prompt_test.json")
