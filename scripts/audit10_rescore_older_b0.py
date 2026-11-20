import json
import math
from pathlib import Path
from pydantic import TypeAdapter

from flbds.schema.enums import BoundaryTypeEnum
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.problem_card import ProblemCard
from flbds.schema.templates import (
    TemplateParameters,
    TPL01Params,
    TPL02Params,
    TPL03Params,
    TPL04Params,
    TPL05Params,
    TPL06Params,
    TPL07Params,
    TPL08Params,
    TPL09Params,
    TPL10Params,
)
from flbds.physics.capacity_bound import check_problem_satisfiability
from flbds.physics.tpl01_conduction import eval_tpl01
from flbds.physics.tpl02_pcm import eval_tpl02
from flbds.physics.tpl03_evaporation import eval_tpl03_evaporation as eval_tpl03
from flbds.physics.tpl04_sorption import eval_tpl04
from flbds.physics.tpl05_wicking import eval_tpl05
from flbds.physics.tpl06_porous_flow import eval_tpl06
from flbds.physics.tpl07_fin import eval_tpl07
from flbds.physics.tpl08_countercurrent import eval_tpl08
from flbds.physics.tpl09_radiative import eval_tpl09
from flbds.physics.tpl10_diffusion import eval_tpl10

DEV_SPECS = {
    "DEV-M1-S1": {
        "required_energy_J_m2": 4.0e6,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 45.0,
        "superheat_limit_K": 10.0,
        "heat_flux_W_m2": 150.0,
        "charge_hours": 8.0,
    },
    "DEV-M1-S2": {
        "required_energy_J_m2": 5.76e6,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 45.0,
        "superheat_limit_K": 10.0,
        "heat_flux_W_m2": 200.0,
        "charge_hours": 8.0,
    },
    "DEV-M1-S3": {
        "required_energy_J_m2": 3.5e6,
        "thickness_max_m": 0.04,
        "mass_cap_kg_m2": 45.0,
        "superheat_limit_K": 10.0,
        "heat_flux_W_m2": 200.0,
        "charge_hours": 4.86,
    },
    "DEV-M2-S1": {
        "required_duty_W": 500.0,
        "max_pressure_drop_Pa": 500.0,
        "pressure_drop_cap_Pa": 500.0,
        "T_hot_in_degC": 37.0,
        "T_cold_in_degC": 5.0,
        "length_cap_m": 1.0,
    },
    "DEV-M2-S2": {
        "required_duty_W": 2000.0,
        "max_pressure_drop_Pa": 800.0,
        "pressure_drop_cap_Pa": 800.0,
        "T_hot_in_degC": 55.0,
        "T_cold_in_degC": 20.0,
        "length_cap_m": 1.0,
    },
    "DEV-M2-S3": {
        "required_duty_W": 800.0,
        "max_pressure_drop_Pa": 250.0,
        "pressure_drop_cap_Pa": 250.0,
        "T_hot_in_degC": 45.0,
        "T_cold_in_degC": 15.0,
        "length_cap_m": 1.0,
    },
    "DEV-M3-S1": {
        "solar_irradiance_W_m2": 850.0,
        "q_solar_W_m2": 850.0,
        "T_ambient_degC": 45.0,
        "T_sky_degC": 15.0,
        "T_inner_degC": 40.0,
        "h_conv_W_m2K": 8.0,
        "h_conv_ambient_W_m2K": 8.0,
        "max_inner_leakage_W_m2": 40.0,
        "required_net_cooling_W_m2": 0.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 20.0,
    },
    "DEV-M3-S2": {
        "solar_irradiance_W_m2": 750.0,
        "q_solar_W_m2": 750.0,
        "T_ambient_degC": 38.0,
        "T_sky_degC": 12.0,
        "T_inner_degC": 27.0,
        "h_conv_W_m2K": 8.0,
        "h_conv_ambient_W_m2K": 8.0,
        "max_inner_leakage_W_m2": 50.0,
        "required_net_cooling_W_m2": 40.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 20.0,
    },
    "DEV-M3-S3": {
        "solar_irradiance_W_m2": 900.0,
        "q_solar_W_m2": 900.0,
        "T_ambient_degC": 42.0,
        "T_sky_degC": 18.0,
        "T_inner_degC": 35.0,
        "h_conv_W_m2K": 10.0,
        "h_conv_ambient_W_m2K": 10.0,
        "max_inner_leakage_W_m2": 20.0,
        "required_net_cooling_W_m2": 0.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 20.0,
    },
    "DEV-M4-S1": {
        "required_flux_mol_m2_s": 0.005,
        "min_pore_diameter_m": 20e-9,
        "hydrostatic_head_m": 10.0,
    },
    "DEV-M4-S2": {
        "required_flux_mol_m2_s": 0.008,
        "min_pore_diameter_m": 25e-9,
        "hydrostatic_head_m": 80.0,
    },
    "DEV-M4-S3": {
        "required_flux_mol_m2_s": 0.006,
        "min_pore_diameter_m": 35e-9,
        "hydrostatic_head_m": 6.0,
    },
}

def wilson_interval(k: int, n: int, confidence: float = 0.95):
    if n == 0:
        return 0.0, (0.0, 0.0)
    p = k / n
    z = 1.959963984540054
    denom = 1 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p)) / n + (z ** 2) / (4 * (n ** 2)))
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return p, (round(low, 4), round(high, 4))

def evaluate_design(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters, cid: str = ""):
    spec = DEV_SPECS.get(cid, {})
    for k, v in spec.items():
        if hasattr(ref_design, k):
            setattr(ref_design, k, v)
        if k == "max_pressure_drop_Pa" and hasattr(ref_design, "pressure_drop_cap_Pa"):
            setattr(ref_design, "pressure_drop_cap_Pa", v)
        if k == "solar_irradiance_W_m2" and hasattr(ref_design, "q_solar_W_m2"):
            setattr(ref_design, "q_solar_W_m2", v)
        if k == "h_conv_W_m2K" and hasattr(ref_design, "h_conv_ambient_W_m2K"):
            setattr(ref_design, "h_conv_ambient_W_m2K", v)

    acceptable = [t.value if hasattr(t, "value") else str(t) for t in gt.acceptable_templates]
    cand_template = ref_design.template_id.value if hasattr(ref_design.template_id, "value") else str(ref_design.template_id)
    if cand_template not in acceptable:
        return False, "template_choice_error", f"Selected template '{cand_template}' not in acceptable: {acceptable}"

    possible, explanation = check_problem_satisfiability(prob, ref_design.template_id, ref_design)
    if not possible:
        return False, "physics_failure", f"Capacity bound violated: {explanation}"

    try:
        if isinstance(ref_design, TPL01Params):
            res = eval_tpl01(ref_design)
        elif isinstance(ref_design, TPL02Params):
            t_cap = spec.get("thickness_max_m", 0.05)
            m_cap = spec.get("mass_cap_kg_m2", 45.0)
            res = eval_tpl02(ref_design, bc_type=BoundaryTypeEnum.BC_FLUX, thickness_cap_m=t_cap, mass_cap_kg_m2=m_cap)
        elif isinstance(ref_design, TPL03Params):
            res = eval_tpl03(ref_design)
        elif isinstance(ref_design, TPL04Params):
            res = eval_tpl04(ref_design)
        elif isinstance(ref_design, TPL05Params):
            res = eval_tpl05(ref_design)
        elif isinstance(ref_design, TPL06Params):
            res = eval_tpl06(ref_design)
        elif isinstance(ref_design, TPL07Params):
            res = eval_tpl07(ref_design)
        elif isinstance(ref_design, TPL08Params):
            res = eval_tpl08(ref_design, length_cap_m=spec.get("length_cap_m", 1.0))
        elif isinstance(ref_design, TPL09Params):
            res = eval_tpl09(ref_design, mass_cap_kg_m2=spec.get("mass_cap_kg_m2", 20.0), thickness_cap_m=spec.get("thickness_max_m", 0.05))
        elif isinstance(ref_design, TPL10Params):
            res = eval_tpl10(ref_design, hydrostatic_head_m=spec.get("hydrostatic_head_m"))
        else:
            return False, "template_choice_error", f"Unknown template {type(ref_design)}"
    except Exception as exc:
        return False, "physics_failure", f"Solver exception: {exc}"

    if not res.passed:
        return False, "physics_failure", f"Physics check failed: {res.reason}"

    return True, "pass", res.reason

def main():
    repo_root = Path("/home/abhishek24024/flbds")
    dev_base = repo_root / "flbds" / "benchmark" / "dev"
    adapter = TypeAdapter(TemplateParameters)

    case_data = {}
    for cid in DEV_SPECS:
        with open(dev_base / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(dev_base / cid / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        case_data[cid] = (prob, gt)

    files_to_rescore = [
        ("b0_results.json (T=0.0)", Path("/home/abhishek24024/flbds_data/benchmark/b0_results.json")),
        ("b0_temp07_results.json (T=0.7, seeds 1-5)", Path("/home/abhishek24024/flbds_data/benchmark/b0_temp07_results.json")),
        ("b0_t07_seeds6to10.json (T=0.7, seeds 6-10)", Path("/home/abhishek24024/flbds_data/audit7/b0_t07_seeds6to10.json")),
        ("audit7/b0_t07_exposed_seeds1to5.json", Path("/home/abhishek24024/flbds_data/audit7/b0_t07_exposed_seeds1to5.json")),
        ("audit8/b0_t07_exposed_seeds1to5.json", Path("/home/abhishek24024/flbds_data/audit8/b0_t07_exposed_seeds1to5.json")),
    ]

    print("="*80)
    print("AUDIT ROUND 10 - SECTION A3: RESCORING OLDER B0 BENCHMARK FILES")
    print("="*80)

    summary_rows = []

    for label, fpath in files_to_rescore:
        if not fpath.exists():
            print(f"Skipping {label}: file not found at {fpath}")
            continue

        with open(fpath) as f:
            data = json.load(f)

        runs = data.get("runs", []) if "runs" in data else data.get("results", [])
        if not runs and isinstance(data, list):
            runs = data

        total = len(runs)
        old_passes = sum(1 for r in runs if r.get("passed") is True)
        
        flips_p_to_f = []
        flips_f_to_p = []
        new_passes = 0

        for r in runs:
            cid = r.get("case_id")
            seed = r.get("seed")
            old_p = r.get("passed") is True
            raw = r.get("final_raw_output") or r.get("turn3_response") or r.get("turn3_output") or ""
            
            # parse
            raw_clean = raw.strip()
            first = raw_clean.find("{")
            last = raw_clean.rfind("}")
            if first != -1 and last != -1:
                json_str = raw_clean[first:last+1]
            else:
                json_str = raw_clean

            try:
                p_dict = json.loads(json_str)
                ref = adapter.validate_python(p_dict)
                prob, gt = case_data[cid]
                new_p, ftype, reason = evaluate_design(prob, gt, ref, cid)
            except Exception:
                new_p = False

            if new_p:
                new_passes += 1

            if old_p and not new_p:
                flips_p_to_f.append(f"{cid}_s{seed}")
            elif not old_p and new_p:
                flips_f_to_p.append(f"{cid}_s{seed}")

        _, old_ci = wilson_interval(old_passes, total)
        _, new_ci = wilson_interval(new_passes, total)

        print(f"\n{label}:")
        print(f"  Old Passes: {old_passes} / {total} ({old_passes/total*100:.1f}%) [CI: {old_ci[0]*100:.1f}%, {old_ci[1]*100:.1f}%]")
        print(f"  New Passes: {new_passes} / {total} ({new_passes/total*100:.1f}%) [CI: {new_ci[0]*100:.1f}%, {new_ci[1]*100:.1f}%]")
        print(f"  Flips Pass -> Fail ({len(flips_p_to_f)}): {flips_p_to_f}")
        print(f"  Flips Fail -> Pass ({len(flips_f_to_p)}): {flips_f_to_p}")

        summary_rows.append({
            "file": label,
            "total": total,
            "old_passes": old_passes,
            "old_rate": old_passes / total,
            "old_ci": list(old_ci),
            "new_passes": new_passes,
            "new_rate": new_passes / total,
            "new_ci": list(new_ci),
            "flips_pass_to_fail": flips_p_to_f,
            "flips_fail_to_pass": flips_f_to_p
        })

    with open("/home/abhishek24024/flbds_data/audit10/older_b0_rescore_summary.json", "w") as f:
        json.dump(summary_rows, f, indent=2)

    print("\nSaved rescoring summary to /home/abhishek24024/flbds_data/audit10/older_b0_rescore_summary.json")

if __name__ == "__main__":
    main()
