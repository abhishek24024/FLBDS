#!/usr/bin/env python3
"""Baseline B0 evaluation harness on 12 Dev Cases across 5 seeds.

Rebuilt per FLBDS v9 §7.1 and Audit Round 2:
- Plain prompt to 72B model (Qwen2.5-72B-Instruct-FP8)
- 3-turn self-critique (Generation -> Critique -> Refined Schema Output)
- Typed parameter schema shown in Turn 3 prompt
- vLLM guided JSON decoding keyed to the TemplateParameters discriminated union
- Fixed '{' prefix bug (direct guided output extraction)
- 5 seeds per case (seeds 1 to 5, total 60 runs)
- Strict failure taxonomy: parse failures, schema failures, template-choice errors, physics failures, passes
- Wilson score intervals for all categories and splits
- Complete 3-turn conversation transcripts saved for qualitative review
"""

import os
import sys
os.environ["PATH"] = "/home/abhishek24024/flbds_env/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, '/home/abhishek24024/flbds')

import argparse
import json
import math
import re
import time
from pathlib import Path
from pydantic import TypeAdapter, ValidationError

from flbds.schema.enums import BoundaryTypeEnum, TemplateEnum
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

from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams


DEV_CASES = [
    "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
    "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
    "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
    "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
]

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

SCHEMA_SPEC = """
Available Physics Templates and Parameter Schemas (choose ONE):
- TPL_01: Cyclic sensible thermal storage (conduction, thermal mass)
  Required: template_id: "TPL_01", thickness_m (float), density_kg_m3 (float), specific_heat_J_kgK (float), thermal_conductivity_W_mK (float), required_energy_J_m2 (float)
  Optional: period_hours (float, default 24.0)

- TPL_02: 1D solid-liquid phase change thermal storage (Stefan PDE, latent heat)
  Required: template_id: "TPL_02", thickness_m (float), k_eff_W_mK (float)
  Optional: pcm_density_kg_m3 (float, default 820.0), pcm_latent_heat_J_kg (float, default 210000.0), pcm_specific_heat_J_kgK (float, default 2000.0), matrix_volume_fraction (float, default 0.0), matrix_density_kg_m3 (float, default 2700.0), matrix_specific_heat_J_kgK (float, default 900.0), melting_temp_degC (float, default 28.0), superheat_limit_K (float, default 10.0), heat_flux_W_m2 (float, default 200.0), charge_hours (float, default 8.0), required_energy_J_m2 (float, default 5760000.0)

- TPL_03: Evaporative cooling / condensation
  Required: template_id: "TPL_03"
  Optional: latent_heat_J_kg (float, default 2400000.0), evaporation_rate_kg_m2_s (float, default 0.0001), water_budget_kg_m2 (float, default 10.0), ambient_relative_humidity (float, default 0.4), air_velocity_m_s (float, default 1.0), characteristic_length_m (float, default 0.1)

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
  Required: template_id: "TPL_09", surface_emissivity (float, default 0.95), solar_absorptivity (float, default 0.05)
  Optional: h_conv_ambient_W_m2K (float, default 6.0), T_ambient_degC (float, default 35.0), T_sky_degC (float, default 15.0), solar_irradiance_W_m2 (float, default 800.0), substrate_thickness_m (float, default 0.02), substrate_k_W_mK (float, default 0.05), substrate_density_kg_m3 (float, default 50.0), T_inner_degC (float, default 22.0), max_inner_leakage_W_m2 (float, default 50.0), required_net_cooling_W_m2 (float, default 0.0)

- TPL_10: Submerged microporous membrane / plastron gas diffusion
  Required: template_id: "TPL_10", membrane_thickness_m (float), porosity (float), required_flux_mol_m2_s (float)
  Optional: pore_diameter_m (float, default 5e-8), min_pore_diameter_m (float, default 2e-8), tortuosity (float, default 2.0), molecular_diffusivity_m2_s (float, default 2e-5), molar_mass_kg_mol (float, default 0.032), temperature_degC (float, default 25.0), delta_concentration_mol_m3 (float, default 5.0)
"""


def extract_json_block(text: str) -> str:
    """Extract JSON object from LLM output."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def wilson_interval(k: int, n: int, confidence: float = 0.95):
    """Compute Wilson score confidence interval."""
    if n == 0:
        return 0.0, (0.0, 0.0)
    p = k / n
    z = 1.959963984540054  # 95%
    denom = 1 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p)) / n + (z ** 2) / (4 * (n ** 2)))
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return p, (round(low, 4), round(high, 4))


def run_m5_eval(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters):
    """Run full M5-Eval scoring pipeline."""
    # 1. Template choice check
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

    # 2. Capacity bound check
    possible, explanation = check_problem_satisfiability(prob, ref_design.template_id, ref_design)
    if not possible:
        return False, "physics_failure", f"Capacity bound violated: {explanation}"

    # 3. Numerical template physics evaluation
    try:
        if isinstance(ref_design, TPL01Params):
            res = eval_tpl01(ref_design)
        elif isinstance(ref_design, TPL02Params):
            res = eval_tpl02(ref_design, bc_type=BoundaryTypeEnum.BC_FLUX)
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
            res = eval_tpl08(ref_design)
        elif isinstance(ref_design, TPL09Params):
            res = eval_tpl09(ref_design)
        elif isinstance(ref_design, TPL10Params):
            res = eval_tpl10(ref_design)
        else:
            return False, "template_choice_error", f"Unknown template type {type(ref_design)}"
    except Exception as exc:
        return False, "physics_failure", f"Solver exception: {exc}"

    if not res.passed:
        return False, "physics_failure", f"Physics check failed: {res.reason}"

    return True, "pass", res.reason


def main():
    parser = argparse.ArgumentParser(description="Run Baseline B0 harness.")
    default_dev = str(Path(__file__).resolve().parent.parent / "flbds" / "benchmark" / "dev")
    parser.add_argument("--model-dir", default="/home/abhishek24024/flbds_data/models/Qwen2.5-72B-Instruct-FP8")
    parser.add_argument("--dev-dir", default=default_dev)
    parser.add_argument("--output-json", default="/home/abhishek24024/flbds_data/benchmark/b0_redo_results.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    dev_base = Path(args.dev_dir).resolve()
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=========================================================")
    print("FLBDS Baseline B0 Redo Harness (v9 §7.1)")
    print(f"Model: {args.model_dir}")
    print(f"Dev Directory: {dev_base}")
    print(f"Seeds: {args.seeds}")
    print(f"Output: {out_path}")
    print("=========================================================")

    # Load all dev cases
    case_data = {}
    for cid in DEV_CASES:
        cdir = dev_base / cid
        with open(cdir / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(cdir / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        case_data[cid] = (prob, gt)
    print(f"Successfully loaded all {len(case_data)} dev cases.")

    # Initialize vLLM with schema adapter
    adapter = TypeAdapter(TemplateParameters)
    schema = adapter.json_schema()
    sop = StructuredOutputsParams(json=schema)

    t_start = time.perf_counter()
    llm = LLM(
        model=args.model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.90,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t_start
    print(f"Model loaded in {load_time:.2f} s.", flush=True)

    results = []
    total_prompt_tok = 0
    total_gen_tok = 0

    # Run across 5 seeds
    for seed in args.seeds:
        print(f"\n--- Running Seed {seed} across 12 Dev Cases ---", flush=True)
        sp_gen = SamplingParams(temperature=0.7, top_p=0.9, seed=seed, max_tokens=1024)
        sp_critic = SamplingParams(temperature=0.3, top_p=0.9, seed=seed, max_tokens=1024)
        sp_refine = SamplingParams(
            temperature=0.1,
            top_p=0.9,
            seed=seed,
            max_tokens=1024,
            structured_outputs=sop,
        )

        # Turn 1: Initial Proposals
        t1_prompts = []
        for cid in DEV_CASES:
            prob, _ = case_data[cid]
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem Specification:\n"
                f"Target System: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Environment: {prob.environment}\n"
                f"Time Pattern: {prob.time_pattern}\n"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json(indent=2)}\n"
                f"{AVAILABLE_TEMPLATES}\n\n"
                f"Task (Turn 1): Propose the best physics template (e.g. TPL_02, TPL_08, TPL_09, TPL_10) "
                f"and initial parameter values to satisfy all functional targets and hard constraints.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t1_prompts.append(p_text)

        t1_outs = llm.generate(t1_prompts, sp_gen)
        total_prompt_tok += sum(len(o.prompt_token_ids) for o in t1_outs)
        total_gen_tok += sum(len(o.outputs[0].token_ids) for o in t1_outs)

        # Turn 2: Self-Critique
        t2_prompts = []
        for cid, t1_out in zip(DEV_CASES, t1_outs):
            t1_ans = t1_out.outputs[0].text
            prob, _ = case_data[cid]
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Constraints: {prob.hard_constraints.model_dump_json()}\n"
                f"Proposed Initial Design:\n{t1_ans}\n\n"
                f"Task (Turn 2 - Critique): Critically analyze this proposed design against physical reality:\n"
                f"1. Is the template thermodynamically capable of the required duty (capacity bounds)?\n"
                f"2. Does it violate any envelope constraints (thickness, mass, pressure drop, temperature cap)?\n"
                f"3. Check for unrealistic fluid velocities, unachievable heat transfer coefficients, or material limits.\n"
                f"Identify all deficiencies and specify exact numerical adjustments required.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t2_prompts.append(p_text)

        t2_outs = llm.generate(t2_prompts, sp_critic)
        total_prompt_tok += sum(len(o.prompt_token_ids) for o in t2_outs)
        total_gen_tok += sum(len(o.outputs[0].token_ids) for o in t2_outs)

        # Turn 3: Refined Schema Output (Guided JSON Decoding)
        t3_prompts = []
        for cid, t1_out, t2_out in zip(DEV_CASES, t1_outs, t2_outs):
            prob, _ = case_data[cid]
            critique = t2_out.outputs[0].text
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                f"Critique and Corrections:\n{critique}\n\n"
                f"{SCHEMA_SPEC}\n\n"
                f"Task (Turn 3 - Refined Parameter Generation):\n"
                f"Incorporate the critique and output the final verified design parameters strictly as a valid JSON object matching the schema for your chosen template_id.\n"
                f"Output ONLY the JSON object conforming to the schema.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t3_prompts.append(p_text)

        t3_outs = llm.generate(t3_prompts, sp_refine)
        total_prompt_tok += sum(len(o.prompt_token_ids) for o in t3_outs)
        total_gen_tok += sum(len(o.outputs[0].token_ids) for o in t3_outs)

        # Evaluate each output with M5-Eval and record full transcripts
        for idx, (cid, t1_out, t2_out, t3_out) in enumerate(zip(DEV_CASES, t1_outs, t2_outs, t3_outs)):
            prob, gt = case_data[cid]
            t1_ans = t1_out.outputs[0].text
            t2_ans = t2_out.outputs[0].text
            t3_ans = t3_out.outputs[0].text
            json_str = extract_json_block(t3_ans)

            record = {
                "case_id": cid,
                "split": cid.split("-")[2],
                "seed": seed,
                "turn1_prompt": t1_prompts[idx],
                "turn1_response": t1_ans,
                "turn2_prompt": t2_prompts[idx],
                "turn2_response": t2_ans,
                "turn3_prompt": t3_prompts[idx],
                "turn3_response": t3_ans,
                "raw_output": t3_ans,
                "parsed_json": None,
                "passed": False,
                "failure_type": None,  # parse_failure, schema_failure, template_choice_error, physics_failure
                "reason": None,
            }

            # 1. Parse check
            try:
                parsed_dict = json.loads(json_str)
                record["parsed_json"] = parsed_dict
            except json.JSONDecodeError as jde:
                record["failure_type"] = "parse_failure"
                record["reason"] = f"JSON parse error: {jde}"
                status_str = "FAIL (parse_failure)"
                print(f"[{cid}] Seed {seed}: {status_str} -> {str(record['reason'])[:70]}", flush=True)
                results.append(record)
                continue

            # 2. Schema validation check
            try:
                ref_design = adapter.validate_python(parsed_dict)
            except ValidationError as ve:
                record["failure_type"] = "schema_failure"
                record["reason"] = f"Schema validation error: {ve}"
                status_str = "FAIL (schema_failure)"
                print(f"[{cid}] Seed {seed}: {status_str} -> {str(record['reason'])[:70]}", flush=True)
                results.append(record)
                continue

            # 3. M5-Eval physics & template check
            passed, fail_type, reason = run_m5_eval(prob, gt, ref_design)
            record["passed"] = passed
            if passed:
                record["failure_type"] = None
                record["reason"] = reason
                status_str = "PASS"
            else:
                record["failure_type"] = fail_type
                record["reason"] = reason
                status_str = f"FAIL ({fail_type})"

            print(f"[{cid}] Seed {seed}: {status_str} -> {str(record['reason'])[:70]}", flush=True)
            results.append(record)

    total_time = time.perf_counter() - t_start
    gpu_hours = round(total_time / 3600.0, 5)

    # Compute aggregate statistics and Wilson score intervals
    total_runs = len(results)
    categories = ["parse_failure", "schema_failure", "template_choice_error", "physics_failure", "pass"]
    cat_counts = {c: 0 for c in categories}
    for r in results:
        if r["passed"]:
            cat_counts["pass"] += 1
        else:
            cat_counts[r["failure_type"]] += 1

    cat_stats = {}
    for c in categories:
        cnt = cat_counts[c]
        p, (ci_low, ci_high) = wilson_interval(cnt, total_runs)
        cat_stats[c] = {
            "count": cnt,
            "rate": round(p, 4),
            "wilson_ci_95": [ci_low, ci_high],
        }

    # Per-split breakdown
    splits = ["S1", "S2", "S3"]
    split_stats = {}
    for sp in splits:
        sp_runs = [r for r in results if r["split"] == sp]
        n_sp = len(sp_runs)
        sp_pass = sum(1 for r in sp_runs if r["passed"])
        p_sp, (ci_l, ci_h) = wilson_interval(sp_pass, n_sp)
        sp_cats = {c: 0 for c in categories}
        for r in sp_runs:
            if r["passed"]:
                sp_cats["pass"] += 1
            else:
                sp_cats[r["failure_type"]] += 1
        split_stats[sp] = {
            "total": n_sp,
            "passed": sp_pass,
            "pass_rate": round(p_sp, 4),
            "pass_wilson_ci_95": [ci_l, ci_h],
            "categories": sp_cats,
        }

    summary = {
        "benchmark": "Baseline B0 Redo on 12 Dev Cases",
        "model": "Qwen2.5-72B-Instruct-FP8",
        "seeds": args.seeds,
        "total_runs": total_runs,
        "categories": cat_stats,
        "split_performance": split_stats,
        "total_prompt_tokens": total_prompt_tok,
        "total_gen_tokens": total_gen_tok,
        "elapsed_seconds": round(total_time, 2),
        "gpu_hours": gpu_hours,
        "results": results,
    }

    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=========================================================")
    print("BASELINE B0 REDO SUMMARY RESULTS (with 95% Wilson CIs)")
    print(f"Total Runs: {total_runs}")
    for c in categories:
        st = cat_stats[c]
        print(f"  {c:22s}: {st['count']:2d} ({st['rate']*100:5.1f}%)  95% CI: [{st['wilson_ci_95'][0]*100:.1f}%, {st['wilson_ci_95'][1]*100:.1f}%]")

    print("\nPer-Split Performance:")
    for sp, sstat in split_stats.items():
        print(f"  Split {sp}: {sstat['passed']}/{sstat['total']} ({sstat['pass_rate']*100:.1f}%) 95% CI: [{sstat['pass_wilson_ci_95'][0]*100:.1f}%, {sstat['pass_wilson_ci_95'][1]*100:.1f}%]")
    print(f"Elapsed: {total_time:.2f} s ({gpu_hours} GPU-hours)")
    print(f"Saved results -> {out_path}")
    print("=========================================================")


if __name__ == "__main__":
    main()
