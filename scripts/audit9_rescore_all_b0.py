import json
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
        "T_inner_degC": 30.0,
        "h_conv_W_m2K": 6.0,
        "h_conv_ambient_W_m2K": 6.0,
        "max_inner_leakage_W_m2": 50.0,
        "required_net_cooling_W_m2": 0.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 20.0,
    },
    "DEV-M3-S3": {
        "solar_irradiance_W_m2": 500.0,
        "q_solar_W_m2": 500.0,
        "T_ambient_degC": 32.0,
        "T_sky_degC": 10.0,
        "T_inner_degC": 20.0,
        "h_conv_W_m2K": 5.0,
        "h_conv_ambient_W_m2K": 5.0,
        "max_inner_leakage_W_m2": 20.0,
        "required_net_cooling_W_m2": 0.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 20.0,
    },
    "DEV-M4-S1": {
        "required_flux_mol_m2_s": 0.005,
        "min_pore_diameter_m": 20e-9,
        "hydrostatic_head_m": 2.5,
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

def run_m5_eval_fixed(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters, cid: str = ""):
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

    acceptable = [
        t.value if hasattr(t, "value") else str(t) for t in gt.acceptable_templates
    ]
    cand_template = (
        ref_design.template_id.value
        if hasattr(ref_design.template_id, "value")
        else str(ref_design.template_id)
    )
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
            return False, "template_choice_error", f"Unknown template type {type(ref_design)}"
    except Exception as exc:
        return False, "physics_failure", f"Solver exception: {exc}"

    if not res.passed:
        return False, "physics_failure", f"Physics check failed: {res.reason}"

    return True, "pass", res.reason

dev_base = Path("/home/abhishek24024/flbds/flbds/benchmark/dev")
case_data = {}
for cid in DEV_SPECS:
    cdir = dev_base / cid
    with open(cdir / "problem_card.json") as f:
        prob = ProblemCard.model_validate_json(f.read())
    with open(cdir / "ground_truth_eval.json") as f:
        gt = GroundTruthEval.model_validate_json(f.read())
    case_data[cid] = (prob, gt)

adapter = TypeAdapter(TemplateParameters)

files_to_rescore = [
    ("/home/abhishek24024/flbds_data/benchmark/b0_results.json", "b0_results.json (T=0.0)"),
    ("/home/abhishek24024/flbds_data/benchmark/b0_temp07_results.json", "b0_temp07_results.json (T=0.7 seeds 1-5)"),
    ("/home/abhishek24024/flbds_data/audit7/b0_t07_seeds6to10.json", "b0_t07_seeds6to10.json (T=0.7 seeds 6-10)"),
    ("/home/abhishek24024/flbds_data/audit7/b0_t07_exposed_seeds1to5.json", "audit7/b0_t07_exposed_seeds1to5.json (Invalid R7)"),
    ("/home/abhishek24024/flbds_data/audit8/b0_t07_exposed_seeds1to5.json", "audit8/b0_t07_exposed_seeds1to5.json (Valid R8)"),
]

all_rescore_reports = {}

for fpath, label in files_to_rescore:
    print(f"\n=======================================================")
    print(f"RESCORING FILE: {label}")
    print(f"Path: {fpath}")
    with open(fpath) as f:
        data = json.load(f)
    runs = data.get("results", data) if isinstance(data, dict) else data
    
    total = len(runs)
    orig_pass = sum(1 for r in runs if r.get("passed"))
    new_pass = 0
    flips_pass_to_fail = []
    flips_fail_to_pass = []
    
    for r in runs:
        cid = r.get("case_id")
        seed = r.get("seed")
        orig_verdict = r.get("passed", False)
        
        parsed = r.get("parsed_json")
        if not parsed:
            # Check raw output
            raw = r.get("raw_output", "")
            try:
                import re
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
            except Exception:
                parsed = None
                
        if not parsed:
            new_passed = False
            fail_type = "parse_failure"
            reason = "No valid JSON parsed"
        else:
            try:
                params_obj = adapter.validate_python(parsed)
                prob, gt = case_data[cid]
                new_passed, fail_type, reason = run_m5_eval_fixed(prob, gt, params_obj, cid=cid)
            except Exception as e:
                new_passed = False
                fail_type = "schema_error"
                reason = str(e)
                
        if new_passed:
            new_pass += 1
            
        if orig_verdict and not new_passed:
            flips_pass_to_fail.append({
                "case_id": cid,
                "seed": seed,
                "orig_reason": r.get("reason"),
                "new_reason": reason,
            })
        elif not orig_verdict and new_passed:
            flips_fail_to_pass.append({
                "case_id": cid,
                "seed": seed,
                "orig_reason": r.get("reason"),
                "new_reason": reason,
            })
            
    print(f"Total: {total} | Orig Passes: {orig_pass} ({orig_pass/total*100:.1f}%) | Rescored Passes: {new_pass} ({new_pass/total*100:.1f}%)")
    print(f"Flips Pass -> Fail: {len(flips_pass_to_fail)}")
    for flip in flips_pass_to_fail:
        print(f"  [FLIP P->F] {flip['case_id']} Seed {flip['seed']}: {flip['orig_reason']} --> {flip['new_reason']}")
    print(f"Flips Fail -> Pass: {len(flips_fail_to_pass)}")
    for flip in flips_fail_to_pass:
        print(f"  [FLIP F->P] {flip['case_id']} Seed {flip['seed']}: {flip['orig_reason']} --> {flip['new_reason']}")
        
    all_rescore_reports[Path(fpath).name] = {
        "file": fpath,
        "label": label,
        "total": total,
        "orig_passes": orig_pass,
        "rescored_passes": new_pass,
        "flips_pass_to_fail": flips_pass_to_fail,
        "flips_fail_to_pass": flips_fail_to_pass,
    }

out_report = Path("/home/abhishek24024/flbds_data/audit9/b0_rescore_environment_flips.json")
with open(out_report, "w") as f:
    json.dump(all_rescore_reports, f, indent=2)
print(f"\nSaved rescore report to {out_report}")
