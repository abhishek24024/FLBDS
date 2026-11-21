#!/usr/bin/env python3
"""Run B0 Baseline Re-run on affected dev cases (DEV-M1) with exposed superheat limit (FLBDS v9 §7.1)."""

import argparse
import json
import time
from pathlib import Path
from pydantic import TypeAdapter

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
from flbds.schema.enums import BoundaryTypeEnum
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

from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams

DEV_CASES = ["DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3"]

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
}

AVAILABLE_TEMPLATES = """
Available physics templates:
- TPL_01: Cyclic sensible thermal storage (conduction, Fourier number Fo in [0.25, 5.0], thermal mass)
- TPL_02: 1D solid-liquid phase change thermal storage (enthalpy Stefan PDE, cyclic Robin boundary)
- TPL_03: Evaporative cooling / condensation (latent heat, water budget, boundary layer mass transfer)
- TPL_04: Closed-loop thermochemical sorption storage (LDF kinetics, regeneration temperature)
- TPL_05: Capillary wicking replenishment (Jurin height, Darcy-Washburn flux, pore radius)
- TPL_06: Porous media fluid flow (Darcy / Ergun pressure drop, pumping COP)
- TPL_07: Extended surface pin/straight fin convective dissipation (fin efficiency, Biot < 0.1)
- TPL_08: Countercurrent heat exchange (effectiveness-NTU, pressure drop cap)
- TPL_09: Radiative surface cooling (emissivity, solar reflectance, sky radiation)
- TPL_10: Submerged microporous membrane / plastron gas diffusion (Fickian/Knudsen diffusion flux)
"""

TEMPLATE_SCHEMAS_PROMPT = """
Available Physics Templates and Parameter Schemas (choose ONE):
- TPL_01: Cyclic sensible thermal storage
  Required: template_id: "TPL_01", thickness_m (float), density_kg_m3 (float), specific_heat_J_kgK (float), thermal_conductivity_W_mK (float), required_energy_J_m2 (float)
  Optional: period_hours (float, default 24.0)

- TPL_02: 1D solid-liquid phase change thermal storage
  Required: template_id: "TPL_02", thickness_m (float), k_eff_W_mK (float)
  Optional: pcm_density_kg_m3 (float, default 820.0), pcm_latent_heat_J_kg (float, default 210000.0), pcm_specific_heat_J_kgK (float, default 2000.0), matrix_volume_fraction (float, default 0.0), matrix_density_kg_m3 (float, default 2700.0), matrix_specific_heat_J_kgK (float, default 900.0), melting_temp_degC (float, default 28.0), superheat_limit_K (float, default 10.0), heat_flux_W_m2 (float, default 200.0), charge_hours (float, default 8.0), required_energy_J_m2 (float, default 5760000.0)

- TPL_03: Evaporative cooling / condensation
  Optional: template_id: "TPL_03", latent_heat_J_kg (float, default 2400000.0), evaporation_rate_kg_m2_s (float, default 0.0001), water_budget_kg_m2 (float, default 10.0), ambient_relative_humidity (float, default 0.4), air_velocity_m_s (float, default 1.0), characteristic_length_m (float, default 1.0)

- TPL_04: Closed-loop thermochemical sorption storage
  Required: template_id: "TPL_04", bulk_density_kg_m3 (float), sorption_density_J_kg (float), regeneration_temp_degC (float), ldf_time_constant_s (float)
  Optional: charge_period_hours (float, default 8.0)
"""

def run_m5_eval(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters, cid: str = ""):
    spec = DEV_SPECS.get(cid, {})
    for k, v in spec.items():
        if hasattr(ref_design, k):
            setattr(ref_design, k, v)

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
        else:
            return False, "template_choice_error", f"Unknown template type {type(ref_design)}"
    except Exception as exc:
        return False, "physics_failure", f"Solver exception: {exc}"

    if not res.passed:
        return False, "physics_failure", f"Physics check failed: {res.reason}"

    return True, "pass", res.reason

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/abhishek24024/flbds_data/models/Qwen2.5-72B-Instruct-FP8")
    parser.add_argument("--output-json", default="/home/abhishek24024/flbds_data/audit9/b0_dev_m1_exposed_rerun.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()

    dev_base = Path("/home/abhishek24024/flbds/flbds/benchmark/dev")
    case_data = {}
    for cid in DEV_CASES:
        cdir = dev_base / cid
        with open(cdir / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(cdir / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        case_data[cid] = (prob, gt)

    adapter = TypeAdapter(TemplateParameters)
    schema = adapter.json_schema()
    sop = StructuredOutputsParams(json=schema)

    llm = LLM(
        model=args.model_dir,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.90,
        max_model_len=4096,
        trust_remote_code=True,
    )

    all_results = []
    for seed in args.seeds:
        sp_text = SamplingParams(temperature=args.temperature, max_tokens=1024, seed=seed)
        sp_json = SamplingParams(temperature=args.temperature, max_tokens=1024, seed=seed, structured_outputs=sop)

        # Turn 1
        t1_prompts = []
        for cid in DEV_CASES:
            prob, _ = case_data[cid]
            c_list = [c.model_dump() for c in prob.constraints] if prob.constraints else []
            c_str = f"Specific Constraints: {json.dumps(c_list)}\n" if c_list else ""
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem Specification:\n"
                f"Target System: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Environment: {prob.environment}\n"
                f"Time Pattern: {prob.time_pattern}\n"
                f"{c_str}"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json(indent=2)}\n"
                f"{AVAILABLE_TEMPLATES}\n\n"
                f"Task (Turn 1): Propose the best physics template (e.g. TPL_02, TPL_08, TPL_09, TPL_10) "
                f"and initial parameter values to satisfy all functional targets and hard constraints.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t1_prompts.append(p_text)
        t1_outs = llm.generate(t1_prompts, sp_text)

        # Turn 2
        t2_prompts = []
        for cid, t1_out in zip(DEV_CASES, t1_outs):
            t1_ans = t1_out.outputs[0].text
            prob, _ = case_data[cid]
            c_list = [c.model_dump() for c in prob.constraints] if prob.constraints else []
            c_str = f"Specific Constraints: {json.dumps(c_list)}\n" if c_list else ""
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"{c_str}"
                f"Constraints: {prob.hard_constraints.model_dump_json()}\n"
                f"Proposed Initial Design:\n{t1_ans}\n\n"
                f"Task (Turn 2 - Critique): Critically analyze this proposed design against physical reality:\n"
                f"1. Is the proposed template thermodynamically capable of the required flux/load under the stated boundary conditions (capacity bounds)?\n"
                f"2. Are the parameters within realistic material and geometric limits (thickness, mass, pressure drop, superheat)?\n"
                f"3. Provide concrete parameter adjustments needed to ensure feasibility.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t2_prompts.append(p_text)
        t2_outs = llm.generate(t2_prompts, sp_text)

        # Turn 3
        t3_prompts = []
        for cid, t1_out, t2_out in zip(DEV_CASES, t1_outs, t2_outs):
            t1_ans = t1_out.outputs[0].text
            t2_ans = t2_out.outputs[0].text
            prob, _ = case_data[cid]
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                f"Turn 1 Proposal:\n{t1_ans}\n\n"
                f"Turn 2 Engineering Critique:\n{t2_ans}\n\n"
                f"{TEMPLATE_SCHEMAS_PROMPT}\n\n"
                f"Task (Turn 3 - Refined Parameter Generation):\n"
                f"Incorporate the critique and output the final verified design parameters strictly as a valid JSON object matching the schema for your chosen template_id.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t3_prompts.append(p_text)
        t3_outs = llm.generate(t3_prompts, sp_json)

        # Evaluate
        for cid, t1_p, t1_o, t2_p, t2_o, t3_p, t3_o in zip(DEV_CASES, t1_prompts, t1_outs, t2_prompts, t2_outs, t3_prompts, t3_outs):
            prob, gt = case_data[cid]
            raw_json = t3_o.outputs[0].text
            try:
                parsed = json.loads(raw_json)
                params_obj = adapter.validate_python(parsed)
                passed, ftype, reason = run_m5_eval(prob, gt, params_obj, cid=cid)
            except Exception as exc:
                parsed = None
                passed, ftype, reason = False, "parse_or_schema_error", str(exc)

            all_results.append({
                "case_id": cid,
                "split": int(cid.split("-S")[1]),
                "seed": seed,
                "turn1_prompt": t1_p,
                "turn1_response": t1_o.outputs[0].text,
                "turn2_prompt": t2_p,
                "turn2_response": t2_o.outputs[0].text,
                "turn3_prompt": t3_p,
                "turn3_response": raw_json,
                "raw_output": raw_json,
                "parsed_json": parsed,
                "passed": passed,
                "failure_type": ftype,
                "reason": reason,
            })
            print(f"[{cid}] Seed {seed}: passed={passed} ({ftype}) -> {reason}")

    out_p = Path(args.output_json)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w") as f:
        json.dump({"total": len(all_results), "results": all_results}, f, indent=2)
    print(f"Saved results to {out_p}")

if __name__ == "__main__":
    main()
