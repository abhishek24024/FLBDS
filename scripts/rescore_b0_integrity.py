import json
from pathlib import Path
from pydantic import TypeAdapter

DEV_SPECS = {
    "DEV-M1-S1": {"required_energy_J_m2": 4.0e6, "thickness_max_m": 0.05},
    "DEV-M1-S2": {"required_energy_J_m2": 4.5e6, "thickness_max_m": 0.05},
    "DEV-M1-S3": {"required_energy_J_m2": 2.5e6, "thickness_max_m": 0.04},
    "DEV-M2-S1": {"required_duty_W": 500.0, "max_pressure_drop_Pa": 500.0, "pressure_drop_cap_Pa": 500.0},
    "DEV-M2-S2": {"required_duty_W": 2000.0, "max_pressure_drop_Pa": 800.0, "pressure_drop_cap_Pa": 800.0},
    "DEV-M2-S3": {"required_duty_W": 800.0, "max_pressure_drop_Pa": 250.0, "pressure_drop_cap_Pa": 250.0},
    "DEV-M3-S1": {"max_inner_leakage_W_m2": 40.0, "required_net_cooling_W_m2": 0.0},
    "DEV-M3-S2": {"max_inner_leakage_W_m2": 50.0, "required_net_cooling_W_m2": 0.0},
    "DEV-M3-S3": {"max_inner_leakage_W_m2": 20.0, "required_net_cooling_W_m2": 0.0},
    "DEV-M4-S1": {"required_flux_mol_m2_s": 0.005, "min_pore_diameter_m": 20e-9},
    "DEV-M4-S2": {"required_flux_mol_m2_s": 0.008, "min_pore_diameter_m": 25e-9},
    "DEV-M4-S3": {"required_flux_mol_m2_s": 0.006, "min_pore_diameter_m": 35e-9},
}

with open('/home/abhishek24024/flbds_data/benchmark/b0_redo_results.json', 'r') as f:
    b0_data = json.load(f)

runs = b0_data["results"]
print(f"Total runs to re-score: {len(runs)}")

passes_before = sum(1 for r in runs if r["passed"])
print(f"Passes before fixing scorer: {passes_before} / {len(runs)} ({passes_before/len(runs)*100:.1f}%)")

from flbds.schema.templates import TemplateParameters, TPL01Params, TPL02Params, TPL03Params, TPL04Params, TPL05Params, TPL06Params, TPL07Params, TPL08Params, TPL09Params, TPL10Params
from flbds.schema.problem_card import ProblemCard
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.physics.tpl01_conduction import eval_tpl01
from flbds.physics.tpl02_pcm import eval_tpl02
from flbds.physics.tpl03_evaporation import eval_tpl03_evaporation
from flbds.physics.tpl04_sorption import eval_tpl04
from flbds.physics.tpl05_wicking import eval_tpl05
from flbds.physics.tpl06_porous_flow import eval_tpl06
from flbds.physics.tpl07_fin import eval_tpl07
from flbds.physics.tpl08_countercurrent import eval_tpl08
from flbds.physics.tpl09_radiative import eval_tpl09
from flbds.physics.tpl10_diffusion import eval_tpl10
from flbds.physics.capacity_bound import check_problem_satisfiability
from flbds.schema.enums import BoundaryTypeEnum

adapter = TypeAdapter(TemplateParameters)

new_results = []
changed_runs = []

for r in runs:
    cid = r["case_id"]
    spec = DEV_SPECS.get(cid, {})
    parsed = r.get("parsed_json")
    if not parsed:
        new_results.append(r)
        continue
    
    dev_dir = Path("/home/abhishek24024/flbds/flbds/benchmark/dev") / cid
    with open(dev_dir / "ground_truth_eval.json") as f:
        gt = json.load(f)
    acceptable = gt.get("acceptable_templates", [])
    
    cand_tpl = parsed.get("template_id")
    if cand_tpl not in acceptable:
        r_copy = dict(r)
        r_copy["passed_after"] = False
        r_copy["failure_type_after"] = "template_choice_error"
        r_copy["reason_after"] = f"Template {cand_tpl} not in {acceptable}"
        new_results.append(r_copy)
        continue

    parsed_fixed = dict(parsed)
    for k, v in spec.items():
        if k in ["required_duty_W", "max_pressure_drop_Pa", "pressure_drop_cap_Pa"]:
            parsed_fixed[k] = v
            if k == "max_pressure_drop_Pa":
                parsed_fixed["pressure_drop_cap_Pa"] = v
        elif k in ["max_inner_leakage_W_m2", "required_net_cooling_W_m2"]:
            parsed_fixed[k] = v
        elif k in ["required_energy_J_m2"]:
            parsed_fixed[k] = v
        elif k in ["required_flux_mol_m2_s", "min_pore_diameter_m"]:
            parsed_fixed[k] = v

    try:
        ref_design = adapter.validate_python(parsed_fixed)
        with open(dev_dir / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
            
        possible, reason = check_problem_satisfiability(prob, ref_design.template_id, ref_design)
        if not possible:
            passed = False
            fail_type = "physics_failure"
            msg = f"Capacity bound violated: {reason}"
        else:
            if isinstance(ref_design, TPL01Params):
                res = eval_tpl01(ref_design)
            elif isinstance(ref_design, TPL02Params):
                res = eval_tpl02(ref_design, bc_type=BoundaryTypeEnum.BC_FLUX)
            elif isinstance(ref_design, TPL03Params):
                res = eval_tpl03_evaporation(ref_design)
            elif isinstance(ref_design, TPL04Params):
                res = eval_tpl04(ref_design)
            elif isinstance(ref_design, TPL05Params):
                res = eval_tpl05(ref_design)
            elif isinstance(ref_design, TPL06Params):
                res = eval_tpl06(ref_design)
            elif isinstance(ref_design, TPL07Params):
                res = eval_tpl07(ref_design)
            elif isinstance(ref_design, TPL08Params):
                res = eval_tpl08(ref_design)
            elif isinstance(ref_design, TPL09Params):
                res = eval_tpl09(ref_design)
            elif isinstance(ref_design, TPL10Params):
                res = eval_tpl10(ref_design)
            passed = res.passed
            fail_type = None if passed else "physics_failure"
            msg = res.reason
    except Exception as e:
        passed = False
        fail_type = "physics_failure"
        msg = f"Exception: {e}"

    r_copy = dict(r)
    r_copy["passed_after"] = passed
    r_copy["failure_type_after"] = fail_type
    r_copy["reason_after"] = msg
    new_results.append(r_copy)

    if r["passed"] != passed:
        changed_runs.append({
            "case_id": cid,
            "seed": r["seed"],
            "before": r["passed"],
            "after": passed,
            "reason_before": r.get("reason"),
            "reason_after": msg
        })

passes_after = sum(1 for r in new_results if r.get("passed_after", r["passed"]))
print(f"Passes after fixing scorer: {passes_after} / {len(new_results)} ({passes_after/len(new_results)*100:.1f}%)")
print(f"Number of runs whose verdict flipped: {len(changed_runs)}")
for c in changed_runs:
    print(f"  {c['case_id']} (seed {c['seed']}): Before={c['before']} -> After={c['after']} | {c['reason_after'][:80]}")

with open('/home/abhishek24024/flbds_data/benchmark/b0_rescored_integrity.json', 'w') as f:
    json.dump({"passes_before": passes_before, "passes_after": passes_after, "changed": changed_runs, "results": new_results}, f, indent=2)
print("Saved rescored results to /home/abhishek24024/flbds_data/benchmark/b0_rescored_integrity.json")
