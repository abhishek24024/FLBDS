import json
from pathlib import Path
from flbds.schema.problem_card import ProblemCard
from flbds.schema.ground_truth_eval import GroundTruthEval

with open('/home/abhishek24024/flbds_data/audit8/b0_t07_exposed_seeds1to5.json') as f:
    valid_data = json.load(f)

# Group valid runs by case
valid_by_case = {}
for r in valid_data['results']:
    cid = r['case_id']
    if cid not in valid_by_case:
        valid_by_case[cid] = []
    valid_by_case[cid].append(r)

dev_dir = Path('/home/abhishek24024/flbds/flbds/benchmark/dev')

cases = sorted([d.name for d in dev_dir.iterdir() if d.is_dir() and d.name.startswith('DEV-')])

# Defined evaluator limits per case
# Check what each case's evaluator actually enforces:
evaluator_limits = {
    "DEV-M1-S1": [
        ("thickness_max_m", 0.05, "flbds/physics/tpl02_pcm.py", "eval_tpl02 (thickness_cap_m)"),
        ("max_mass_kg_m2", 45.0, "flbds/physics/tpl02_pcm.py", "eval_tpl02 (mass_cap_kg_m2)"),
        ("required_energy_J_m2", 4.0e6, "flbds/benchmark/dev/DEV-M1-S1/problem_card.json", "required_function.flux_or_load"),
        ("superheat_limit_K", 10.0, "flbds/schema/templates.py", "TPL02Params default / eval_tpl02"),
    ],
    "DEV-M1-S2": [
        ("thickness_max_m", 0.05, "flbds/physics/tpl02_pcm.py", "eval_tpl02 (thickness_cap_m)"),
        ("max_mass_kg_m2", 45.0, "flbds/physics/tpl02_pcm.py", "eval_tpl02 (mass_cap_kg_m2)"),
        ("required_energy_J_m2", 5.76e6, "flbds/benchmark/dev/DEV-M1-S2/problem_card.json", "required_function.flux_or_load"),
        ("superheat_limit_K", 10.0, "flbds/schema/templates.py", "TPL02Params default / eval_tpl02"),
    ],
    "DEV-M1-S3": [
        ("thickness_max_m", 0.04, "flbds/physics/tpl02_pcm.py", "eval_tpl02 (thickness_cap_m)"),
        ("max_mass_kg_m2", 45.0, "flbds/physics/tpl02_pcm.py", "eval_tpl02 (mass_cap_kg_m2)"),
        ("required_energy_J_m2", 3.5e6, "flbds/benchmark/dev/DEV-M1-S3/problem_card.json", "required_function.flux_or_load"),
        ("superheat_limit_K", 10.0, "flbds/schema/templates.py", "TPL02Params default / eval_tpl02"),
    ],
    "DEV-M2-S1": [
        ("required_duty_W", 500.0, "flbds/benchmark/dev/DEV-M2-S1/problem_card.json", "required_function.flux_or_load"),
        ("max_pressure_drop_Pa", 500.0, "flbds/benchmark/dev/DEV-M2-S1/problem_card.json", "hard_constraints.max_pressure_drop_Pa"),
        ("max_envelope_height_m", 1.0, "flbds/physics/tpl08_countercurrent.py", "eval_tpl08 (length_cap_m)"),
    ],
    "DEV-M2-S2": [
        ("required_duty_W", 2000.0, "flbds/benchmark/dev/DEV-M2-S2/problem_card.json", "required_function.flux_or_load"),
        ("max_pressure_drop_Pa", 800.0, "flbds/benchmark/dev/DEV-M2-S2/problem_card.json", "hard_constraints.max_pressure_drop_Pa"),
        ("max_envelope_height_m", 1.0, "flbds/physics/tpl08_countercurrent.py", "eval_tpl08 (length_cap_m)"),
    ],
    "DEV-M2-S3": [
        ("required_duty_W", 800.0, "flbds/benchmark/dev/DEV-M2-S3/problem_card.json", "required_function.flux_or_load"),
        ("max_pressure_drop_Pa", 250.0, "flbds/benchmark/dev/DEV-M2-S3/problem_card.json", "hard_constraints.max_pressure_drop_Pa"),
        ("max_envelope_height_m", 1.0, "flbds/physics/tpl08_countercurrent.py", "eval_tpl08 (length_cap_m)"),
    ],
    "DEV-M3-S1": [
        ("max_inner_leakage_W_m2", 40.0, "flbds/benchmark/dev/DEV-M3-S1/problem_card.json", "constraints[0].bound"),
        ("required_net_cooling_W_m2", 0.0, "flbds/physics/tpl09_radiative.py", "eval_tpl09 target"),
        ("max_thickness_m", 0.05, "flbds/physics/tpl09_radiative.py", "eval_tpl09 thickness_cap_m"),
        ("max_mass_kg_m2", 20.0, "flbds/physics/tpl09_radiative.py", "eval_tpl09 mass_cap_kg_m2"),
    ],
    "DEV-M3-S2": [
        ("max_inner_leakage_W_m2", 50.0, "flbds/benchmark/dev/DEV-M3-S2/problem_card.json", "constraints[0].bound"),
        ("required_net_cooling_W_m2", 0.0, "flbds/physics/tpl09_radiative.py", "eval_tpl09 target"),
        ("max_thickness_m", 0.05, "flbds/physics/tpl09_radiative.py", "eval_tpl09 thickness_cap_m"),
        ("max_mass_kg_m2", 20.0, "flbds/physics/tpl09_radiative.py", "eval_tpl09 mass_cap_kg_m2"),
    ],
    "DEV-M3-S3": [
        ("max_inner_leakage_W_m2", 20.0, "flbds/benchmark/dev/DEV-M3-S3/problem_card.json", "constraints[0].bound"),
        ("required_net_cooling_W_m2", 0.0, "flbds/physics/tpl09_radiative.py", "eval_tpl09 target"),
        ("max_thickness_m", 0.05, "flbds/physics/tpl09_radiative.py", "eval_tpl09 thickness_cap_m"),
        ("max_mass_kg_m2", 20.0, "flbds/physics/tpl09_radiative.py", "eval_tpl09 mass_cap_kg_m2"),
    ],
    "DEV-M4-S1": [
        ("required_flux_mol_m2_s", 0.005, "flbds/benchmark/dev/DEV-M4-S1/problem_card.json", "required_function.flux_or_load"),
        ("min_pore_diameter_m", 2e-8, "flbds/benchmark/dev/DEV-M4-S1/problem_card.json", "hard_constraints.min_pore_diameter_m"),
        ("breakthrough_head_m", 2.5, "flbds/benchmark/dev/DEV-M4-S1/problem_card.json", "specific_constraints[0].bound"),
    ],
    "DEV-M4-S2": [
        ("required_flux_mol_m2_s", 0.008, "flbds/benchmark/dev/DEV-M4-S2/problem_card.json", "required_function.flux_or_load"),
        ("min_pore_diameter_m", 2.5e-8, "flbds/benchmark/dev/DEV-M4-S2/problem_card.json", "hard_constraints.min_pore_diameter_m"),
        ("breakthrough_head_m", 80.0, "flbds/benchmark/dev/DEV-M4-S2/problem_card.json", "specific_constraints[0].bound"),
    ],
    "DEV-M4-S3": [
        ("required_flux_mol_m2_s", 0.006, "flbds/benchmark/dev/DEV-M4-S3/problem_card.json", "required_function.flux_or_load"),
        ("min_pore_diameter_m", 3.5e-8, "flbds/benchmark/dev/DEV-M4-S3/problem_card.json", "hard_constraints.min_pore_diameter_m"),
        ("breakthrough_head_m", 6.0, "flbds/benchmark/dev/DEV-M4-S3/problem_card.json", "specific_constraints[0].bound"),
    ],
}

print("=== AUDIT ROUND 9: EXPOSURE TABLE ANALYSIS ===")
exposure_report = []

for cid in cases:
    runs = valid_by_case[cid]
    t1_prompt = runs[0]['turn1_prompt']
    t3_prompt = runs[0]['turn3_prompt']
    
    t1_lines = t1_prompt.splitlines()
    t3_lines = t3_prompt.splitlines()
    
    limits = evaluator_limits.get(cid, [])
    for lim_name, lim_val, src_file, note in limits:
        # Check Turn 1
        t1_found = []
        for idx, line in enumerate(t1_lines):
            # check if name or numeric value appears
            val_str = str(lim_val)
            if isinstance(lim_val, float) and lim_val.is_integer():
                val_str2 = f"{lim_val:.1f}"
            else:
                val_str2 = str(lim_val)
            if (lim_name in line or val_str in line or val_str2 in line) and "Hard Constraints" not in line and "null" not in line:
                t1_found.append((idx + 1, line.strip()))
            elif lim_name in line and "null" in line:
                pass # Explicitly null
                
        # Check Turn 3
        t3_found = []
        for idx, line in enumerate(t3_lines):
            val_str = str(lim_val)
            if (lim_name in line or val_str in line) and "null" not in line:
                t3_found.append((idx + 1, line.strip()))
                
        visible_t1 = len(t1_found) > 0
        visible_t3 = len(t3_found) > 0
        
        exposure_report.append({
            "case_id": cid,
            "limit_name": lim_name,
            "limit_value": lim_val,
            "source_file": src_file,
            "enforced_by": note,
            "visible_turn1": visible_t1,
            "visible_turn3": visible_t3,
            "turn1_lines": t1_found,
            "turn3_lines": t3_found[:2],
        })

for item in exposure_report:
    flag = "VISIBLE" if (item['visible_turn1'] or item['visible_turn3']) else "HIDDEN"
    print(f"[{flag}] {item['case_id']}: {item['limit_name']} = {item['limit_value']} ({item['enforced_by']})")
    if not item['visible_turn1']:
        print(f"    -> Never visible in Turn 1! (Turn 3 visible: {item['visible_turn3']})")
    else:
        print(f"    Turn 1 (L{item['turn1_lines'][0][0]}): {item['turn1_lines'][0][1]}")
