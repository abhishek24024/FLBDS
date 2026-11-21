#!/usr/bin/env python3
"""Run A-NoOp Baseline: B0 prompt + 3-turn M5-Screen feedback loop (FLBDS v9 §7.1 and Audit Round 9 Item 10).

A-NoOp architecture:
- Initial 3-turn B0 prompt generates candidate JSON parameters.
- If candidate passes M5 evaluation -> Pass!
- If candidate fails -> up to 3 iterative refinement feedback turns returning the raw M5-Screen
  failed assertion text and numeric values to the model. NO operators (no T1, T2, etc.).
- Evaluates on 12 dev cases, seeds 1 to 5, at temperature 0.7, with guided decoding.
"""

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

DEV_CASES = [
    "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
    "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
    "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
    "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
]

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

- TPL_05: Capillary wicking replenishment
  Required: template_id: "TPL_05", lift_height_m (float), pore_radius_m (float), permeability_m2 (float), required_mass_flux_kg_m2_s (float)
  Optional: surface_tension_N_m (float, default 0.072), contact_angle_deg (float, default 10.0), dynamic_viscosity_Pa_s (float, default 0.001), fluid_density_kg_m3 (float, default 1000.0)

- TPL_06: Porous media fluid flow
  Required: template_id: "TPL_06", bed_length_m (float), bed_porosity (float), mean_pore_diameter_m (float), superficial_velocity_m_s (float), pressure_drop_cap_Pa (float)
  Optional: fluid_density_kg_m3 (float, default 1.2), fluid_viscosity_Pa_s (float, default 1.8e-5), min_pumping_cop (float, default 5.0)

- TPL_07: Extended surface pin/straight fin convective dissipation
  Required: template_id: "TPL_07", fin_thickness_m (float), fin_spacing_m (float), fin_length_m (float), fin_conductivity_W_mK (float), h_conv_W_m2K (float)
  Optional: fluid_thermal_diffusivity_m2_s (float, default 2.2e-5)

- TPL_08: Countercurrent heat exchange
  Required: template_id: "TPL_08", duct_type ("circular"|"square"|"rectangular_2to1"|"parallel_plates"), mass_flow_rate_kg_s (float), c_p_J_kgK (float), overall_U_W_m2K (float), exchange_area_m2 (float), duct_length_m (float), hydraulic_diameter_m (float), pressure_drop_cap_Pa (float), T_hot_in_degC (float), T_cold_in_degC (float), required_duty_W (float)
  Optional: fluid_viscosity_Pa_s (float, default 0.001), fluid_density_kg_m3 (float, default 1000.0)

- TPL_09: Radiative surface cooling
  Required: template_id: "TPL_09", surface_emissivity (float), solar_absorptivity (float), substrate_thickness_m (float), substrate_k_W_mK (float), substrate_density_kg_m3 (float)
  Optional: h_conv_ambient_W_m2K (float, default 8.0), T_ambient_degC (float, default 25.0), T_sky_degC (float, default 10.0), solar_irradiance_W_m2 (float, default 0.0), T_inner_degC (float, default 22.0), max_inner_leakage_W_m2 (float, default 50.0), required_net_cooling_W_m2 (float, default 0.0)

- TPL_10: Submerged microporous membrane / plastron gas diffusion
  Required: template_id: "TPL_10", membrane_thickness_m (float), porosity (float), required_flux_mol_m2_s (float)
  Optional: pore_diameter_m (float, default 5e-8), min_pore_diameter_m (float, default 2e-8), tortuosity (float, default 2.0), molecular_diffusivity_m2_s (float, default 2e-5), molar_mass_kg_mol (float, default 0.032), temperature_degC (float, default 25.0), delta_concentration_mol_m3 (float, default 5.0)
"""

def run_m5_eval(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters, cid: str = ""):
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/abhishek24024/flbds_data/models/Qwen2.5-72B-Instruct-FP8")
    parser.add_argument("--output-json", default="/home/abhishek24024/flbds_data/audit9/a_noop_results.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-feedback-turns", type=int, default=3)
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

    all_run_records = []
    t_start = time.perf_counter()

    for seed in args.seeds:
        print(f"\n=======================================================")
        print(f"STARTING A-NoOp RUN FOR SEED {seed}")
        print(f"=======================================================")
        sp_text = SamplingParams(temperature=args.temperature, max_tokens=1024, seed=seed)
        sp_json = SamplingParams(temperature=args.temperature, max_tokens=1024, seed=seed, structured_outputs=sop)

        # 1. Turn 1: Proposal
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

        # 2. Turn 2: Critique
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

        # 3. Turn 3: Refined Generation
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

        # 4. Feedback Loop (Up to 3 feedback turns)
        for i, cid in enumerate(DEV_CASES):
            prob, gt = case_data[cid]
            t1_p = t1_prompts[i]
            t1_o = t1_outs[i].outputs[0].text
            t2_p = t2_prompts[i]
            t2_o = t2_outs[i].outputs[0].text
            t3_p = t3_prompts[i]
            t3_o = t3_outs[i].outputs[0].text

            history = [
                {"role": "user", "content": t1_p},
                {"role": "assistant", "content": t1_o},
                {"role": "user", "content": t2_p},
                {"role": "assistant", "content": t2_o},
                {"role": "user", "content": t3_p},
                {"role": "assistant", "content": t3_o},
            ]

            curr_raw = t3_o
            curr_parsed = None
            passed = False
            ftype = "parse_failure"
            reason = "unparsed"

            try:
                curr_parsed = json.loads(curr_raw)
                p_obj = adapter.validate_python(curr_parsed)
                passed, ftype, reason = run_m5_eval(prob, gt, p_obj, cid=cid)
            except Exception as e:
                curr_parsed = None
                passed, ftype, reason = False, "parse_or_schema_error", str(e)

            turn_count = 3
            feedback_history = []

            # Loop up to max_feedback_turns
            fb_turn = 0
            while not passed and fb_turn < args.max_feedback_turns:
                fb_turn += 1
                turn_count += 1

                # Construct M5-Screen feedback prompt (NO operators)
                fb_prompt = (
                    f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                    f"<|im_start|>user\n"
                    f"Engineering Problem: {prob.system.name}\n"
                    f"Required Function: {prob.required_function}\n"
                    f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                    f"Your previously proposed parameter JSON:\n{curr_raw}\n\n"
                    f"M5-Screen Physical Evaluation Result:\n"
                    f"VERDICT: FAIL\n"
                    f"FAILURE TYPE: {ftype}\n"
                    f"PHYSICAL REASON: {reason}\n\n"
                    f"Task (Turn {turn_count} - Feedback Refinement):\n"
                    f"The evaluator failed your parameters due to the exact physical discrepancy shown above.\n"
                    f"Adjust your sizing, material selection, or dimensions to satisfy all physical capacity bounds and hard constraints.\n"
                    f"Output strictly the revised JSON matching the template schema.<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )

                # Generate revised parameters
                out_fb = llm.generate([fb_prompt], sp_json)[0]
                curr_raw = out_fb.outputs[0].text

                try:
                    curr_parsed = json.loads(curr_raw)
                    p_obj = adapter.validate_python(curr_parsed)
                    new_passed, new_ftype, new_reason = run_m5_eval(prob, gt, p_obj, cid=cid)
                except Exception as e:
                    curr_parsed = None
                    new_passed, new_ftype, new_reason = False, "parse_or_schema_error", str(e)

                feedback_history.append({
                    "feedback_turn": fb_turn,
                    "total_turn": turn_count,
                    "feedback_prompt": fb_prompt,
                    "model_response": curr_raw,
                    "previous_reason": reason,
                    "new_passed": new_passed,
                    "new_failure_type": new_ftype,
                    "new_reason": new_reason,
                })

                passed = new_passed
                ftype = new_ftype
                reason = new_reason

            print(f"[{cid}] Seed {seed} Final: passed={passed} ({ftype}) after {fb_turn} feedback turns -> {reason}")

            all_run_records.append({
                "case_id": cid,
                "split": int(cid.split("-S")[1]),
                "seed": seed,
                "initial_turn3_raw": t3_o,
                "final_raw_output": curr_raw,
                "final_parsed_json": curr_parsed,
                "passed": passed,
                "failure_type": ftype,
                "reason": reason,
                "feedback_turns_used": fb_turn,
                "total_turns": turn_count,
                "feedback_history": feedback_history,
                "turn1_prompt": t1_p,
                "turn1_response": t1_o,
                "turn2_prompt": t2_p,
                "turn2_response": t2_o,
                "turn3_prompt": t3_p,
                "turn3_response": t3_o,
            })

    total_time = time.perf_counter() - t_start
    total_runs = len(all_run_records)
    total_passes = sum(1 for r in all_run_records if r["passed"])

    summary = {
        "benchmark": "A-NoOp",
        "total_runs": total_runs,
        "total_passes": total_passes,
        "pass_rate": total_passes / total_runs if total_runs else 0.0,
        "elapsed_seconds": total_time,
        "gpu_hours": total_time / 3600.0,
        "results": all_run_records,
    }

    out_p = Path(args.output_json)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=======================================================")
    print(f"A-NoOp BENCHMARK COMPLETED: {total_passes}/{total_runs} passes ({summary['pass_rate']*100:.1f}%)")
    print(f"Elapsed: {total_time:.2f} s ({summary['gpu_hours']:.4f} GPU-h)")
    print(f"Saved to: {out_p}")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
