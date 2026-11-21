#!/usr/bin/env python3
"""Unified Round 10 Benchmark Runner:
Executes:
1. Condition B0 (3 turns: Proposal -> Self-Critique -> Guided JSON Refinement)
2. Condition Oracle (3 turns: Evaluator-tier feedback loop with PDE/numerical failure reasons)
3. Condition Screen-Only (3 turns: Screen-tier feedback loop with lumped capacity bounds only)

Evaluates on 12 dev cases, seeds 1 to 5 (N=60 per condition), T=0.7, guided JSON decoding.
Uses synchronized DEV-M1 flux (150 W/m2 for S1, 200 W/m2 for S2/S3) and card-dictated environments.
"""

import os
import sys
os.environ["PATH"] = "/home/abhishek24024/flbds_env/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, '/home/abhishek24024/flbds')

import argparse
import difflib
import json
import math
import time
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

def apply_specs_to_design(ref_design: TemplateParameters, cid: str):
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

def evaluate_design_m5_eval(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters, cid: str = ""):
    apply_specs_to_design(ref_design, cid)
    spec = DEV_SPECS.get(cid, {})

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

def evaluate_design_screen_only(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters, cid: str = ""):
    apply_specs_to_design(ref_design, cid)
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
        return False, "screen_failure", f"Screen check failed: {explanation}"

    return True, "pass", f"Screen capacity satisfied: {explanation}"

def build_turn1_prompt(prob: ProblemCard):
    c_list = [c.model_dump() for c in prob.constraints] if prob.constraints else []
    c_str = f"Specific Constraints: {json.dumps(c_list)}\n" if c_list else ""
    return (
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

def parse_design_json(adapter: TypeAdapter, raw_text: str):
    raw = raw_text.strip()
    try:
        parsed_dict = json.loads(raw)
    except Exception:
        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last != -1 and last > first:
            try:
                parsed_dict = json.loads(raw[first : last + 1])
            except Exception:
                return None, None, "parse_failure", "Failed to parse model output into JSON"
        else:
            return None, None, "parse_failure", "No JSON object found in output"

    try:
        ref_design = adapter.validate_python(parsed_dict)
    except Exception as exc:
        return parsed_dict, None, "schema_failure", f"Schema validation error: {exc}"

    return parsed_dict, ref_design, "success", ""

def summarize_benchmark(results, benchmark_name: str):
    n = len(results)
    passes = sum(1 for r in results if r["passed"])
    parse_fails = sum(1 for r in results if r.get("failure_type") == "parse_failure")
    schema_fails = sum(1 for r in results if r.get("failure_type") == "schema_failure")
    templ_fails = sum(1 for r in results if r.get("failure_type") == "template_choice_error")
    phys_fails = sum(1 for r in results if r.get("failure_type") in ["physics_failure", "screen_failure"])

    p_pass, ci_pass = wilson_interval(passes, n)
    
    # Per split
    splits = {1: [], 2: [], 3: []}
    for r in results:
        splits[r["split"]].append(r)

    split_stats = {}
    for sp, items in splits.items():
        sp_n = len(items)
        sp_pass = sum(1 for r in items if r["passed"])
        _, sp_ci = wilson_interval(sp_pass, sp_n)
        split_stats[f"Split {sp}"] = {
            "total": sp_n,
            "passes": sp_pass,
            "pass_rate": sp_pass / sp_n if sp_n else 0.0,
            "ci": list(sp_ci)
        }

    return {
        "benchmark": benchmark_name,
        "total_runs": n,
        "total_passes": passes,
        "pass_rate": p_pass,
        "wilson_ci": list(ci_pass),
        "parse_failures": parse_fails,
        "schema_failures": schema_fails,
        "template_choice_errors": templ_fails,
        "physics_failures": phys_fails,
        "splits": split_stats
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/abhishek24024/flbds_data/models/Qwen2.5-72B-Instruct-FP8")
    parser.add_argument("--dev-dir", default="flbds/benchmark/dev")
    parser.add_argument("--output-dir", default="/home/abhishek24024/flbds_data/audit10")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    dev_base = Path(args.dev_dir).resolve()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print("FLBDS AUDIT ROUND 10 UNIFIED BENCHMARK RUNNER")
    print(f"Model: {args.model_dir}")
    print(f"Seeds: {args.seeds} (N={len(DEV_CASES)*len(args.seeds)} per benchmark)")
    print(f"Output Directory: {out_dir}")
    print("="*70)

    # Load dev cases
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

    print("Initializing vLLM LLM engine...", flush=True)
    t0 = time.perf_counter()
    llm = LLM(
        model=args.model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.88,
        trust_remote_code=True,
    )
    print(f"vLLM Engine initialized in {time.perf_counter() - t0:.2f} s.", flush=True)

    # =========================================================================
    # BENCHMARK 1: B0 Baseline (Text Self-Critique, 3 Turns)
    # =========================================================================
    print("\n" + "="*70)
    print("STARTING BENCHMARK 1: B0 BASELINE (3-Turn Self-Critique)")
    print("="*70, flush=True)
    b0_results = []
    t_b0_start = time.perf_counter()

    for seed in args.seeds:
        print(f"\n--- B0 Seed {seed} ---", flush=True)
        sp_gen = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024)
        sp_critic = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024)
        sp_refine = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        # Turn 1
        t1_prompts = [build_turn1_prompt(case_data[cid][0]) for cid in DEV_CASES]
        t1_outs = llm.generate(t1_prompts, sp_gen)

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

        # Turn 3: Refined Schema Output
        t3_prompts = []
        for cid, t2_out in zip(DEV_CASES, t2_outs):
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

        for i, cid in enumerate(DEV_CASES):
            prob, gt = case_data[cid]
            final_raw = t3_outs[i].outputs[0].text
            parsed_dict, ref_design, status, err_msg = parse_design_json(adapter, final_raw)
            if status != "success":
                passed = False
                ftype = status
                reason = err_msg
            else:
                passed, ftype, reason = evaluate_design_m5_eval(prob, gt, ref_design, cid)

            b0_results.append({
                "case_id": cid,
                "split": gt.split,
                "seed": seed,
                "condition": "B0_SelfCritique",
                "passed": passed,
                "failure_type": ftype,
                "reason": reason,
                "turn1_prompt": t1_prompts[i],
                "turn1_response": t1_outs[i].outputs[0].text,
                "turn2_prompt": t2_prompts[i],
                "turn2_response": t2_outs[i].outputs[0].text,
                "turn3_prompt": t3_prompts[i],
                "turn3_response": final_raw,
                "final_parsed_json": parsed_dict
            })
            print(f"[{cid}] Seed {seed} B0: passed={passed} ({ftype}) -> {reason[:75]}")

    b0_summary = summarize_benchmark(b0_results, "B0_Baseline_SelfCritique")
    b0_summary["elapsed_seconds"] = time.perf_counter() - t_b0_start
    with open(out_dir / "b0_self_critique_results.json", "w") as f:
        json.dump({"summary": b0_summary, "results": b0_results}, f, indent=2)
    print(f"B0 Completed: {b0_summary['total_passes']}/{b0_summary['total_runs']} ({b0_summary['pass_rate']*100:.1f}%)")

    # =========================================================================
    # BENCHMARK 2: ORACLE (Evaluator-Tier Feedback Loop, 3 Turns)
    # =========================================================================
    print("\n" + "="*70)
    print("STARTING BENCHMARK 2: ORACLE (Evaluator-Tier Feedback)")
    print("="*70, flush=True)
    oracle_results = []
    t_ora_start = time.perf_counter()

    for seed in args.seeds:
        print(f"\n--- Oracle Seed {seed} ---", flush=True)
        sp_initial = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)
        sp_refine = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        # Initial turn
        t1_prompts = [build_turn1_prompt(case_data[cid][0]) for cid in DEV_CASES]
        t1_outs = llm.generate(t1_prompts, sp_initial)

        for i, cid in enumerate(DEV_CASES):
            prob, gt = case_data[cid]
            curr_raw = t1_outs[i].outputs[0].text
            parsed_dict, ref_design, status, err_msg = parse_design_json(adapter, curr_raw)
            if status != "success":
                passed = False
                ftype = status
                reason = err_msg
            else:
                passed, ftype, reason = evaluate_design_m5_eval(prob, gt, ref_design, cid)

            history = []
            turn = 0
            while not passed and turn < 3:
                turn += 1
                fb_prompt = (
                    f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                    f"<|im_start|>user\n"
                    f"Engineering Problem: {prob.system.name}\n"
                    f"Required Function: {prob.required_function}\n"
                    f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                    f"Your previously proposed parameter JSON:\n{curr_raw}\n\n"
                    f"M5-Eval Physical Evaluation Result:\n"
                    f"VERDICT: FAIL\n"
                    f"FAILURE TYPE: {ftype}\n"
                    f"PHYSICAL REASON: {reason}\n\n"
                    f"Task (Turn {turn + 1} - Feedback Refinement):\n"
                    f"The evaluator failed your parameters due to the exact physical discrepancy shown above.\n"
                    f"Adjust your sizing, material selection, or dimensions to satisfy all physical capacity bounds and hard constraints.\n"
                    f"Output strictly the revised JSON matching the template schema.<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                ref_out = llm.generate([fb_prompt], sp_refine)[0]
                new_raw = ref_out.outputs[0].text
                p_dict, new_ref, p_stat, p_msg = parse_design_json(adapter, new_raw)
                if p_stat != "success":
                    new_passed = False
                    new_ftype = p_stat
                    new_reason = p_msg
                else:
                    new_passed, new_ftype, new_reason = evaluate_design_m5_eval(prob, gt, new_ref, cid)

                history.append({
                    "feedback_turn": turn,
                    "prompt": fb_prompt,
                    "previous_reason": reason,
                    "model_response": new_raw,
                    "new_passed": new_passed,
                    "new_failure_type": new_ftype,
                    "new_reason": new_reason
                })
                curr_raw = new_raw
                parsed_dict = p_dict
                passed = new_passed
                ftype = new_ftype
                reason = new_reason

            oracle_results.append({
                "case_id": cid,
                "split": gt.split,
                "seed": seed,
                "condition": "Oracle_EvaluatorFeedback",
                "passed": passed,
                "failure_type": ftype,
                "reason": reason,
                "feedback_turns_used": turn,
                "turn1_prompt": t1_prompts[i],
                "initial_response": t1_outs[i].outputs[0].text,
                "final_raw_output": curr_raw,
                "final_parsed_json": parsed_dict,
                "feedback_history": history
            })
            print(f"[{cid}] Seed {seed} Oracle: passed={passed} after {turn} turns -> {reason[:75]}")

    oracle_summary = summarize_benchmark(oracle_results, "Oracle_EvaluatorTier_Feedback")
    oracle_summary["elapsed_seconds"] = time.perf_counter() - t_ora_start
    with open(out_dir / "oracle_feedback_results.json", "w") as f:
        json.dump({"summary": oracle_summary, "results": oracle_results}, f, indent=2)
    print(f"Oracle Completed: {oracle_summary['total_passes']}/{oracle_summary['total_runs']} ({oracle_summary['pass_rate']*100:.1f}%)")

    # =========================================================================
    # BENCHMARK 3: SCREEN-ONLY (Lumped Screen-Tier Feedback Loop, 3 Turns)
    # =========================================================================
    print("\n" + "="*70)
    print("STARTING BENCHMARK 3: SCREEN-ONLY (Lumped M5-Screen Feedback)")
    print("="*70, flush=True)
    screen_results = []
    t_scr_start = time.perf_counter()

    for seed in args.seeds:
        print(f"\n--- Screen-Only Seed {seed} ---", flush=True)
        sp_initial = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)
        sp_refine = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        t1_prompts = [build_turn1_prompt(case_data[cid][0]) for cid in DEV_CASES]
        t1_outs = llm.generate(t1_prompts, sp_initial)

        for i, cid in enumerate(DEV_CASES):
            prob, gt = case_data[cid]
            curr_raw = t1_outs[i].outputs[0].text
            parsed_dict, ref_design, status, err_msg = parse_design_json(adapter, curr_raw)
            if status != "success":
                screen_passed = False
                ftype = status
                reason = err_msg
            else:
                screen_passed, ftype, reason = evaluate_design_screen_only(prob, gt, ref_design, cid)

            history = []
            turn = 0
            while not screen_passed and turn < 3:
                turn += 1
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
                    f"Task (Turn {turn + 1} - Feedback Refinement):\n"
                    f"The lumped capacity checker failed your parameters due to the physical discrepancy shown above.\n"
                    f"Adjust your sizing, material selection, or dimensions to satisfy all physical capacity bounds and hard constraints.\n"
                    f"Output strictly the revised JSON matching the template schema.<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                ref_out = llm.generate([fb_prompt], sp_refine)[0]
                new_raw = ref_out.outputs[0].text
                p_dict, new_ref, p_stat, p_msg = parse_design_json(adapter, new_raw)
                if p_stat != "success":
                    new_screen_passed = False
                    new_ftype = p_stat
                    new_reason = p_msg
                else:
                    new_screen_passed, new_ftype, new_reason = evaluate_design_screen_only(prob, gt, new_ref, cid)

                history.append({
                    "feedback_turn": turn,
                    "prompt": fb_prompt,
                    "previous_reason": reason,
                    "model_response": new_raw,
                    "new_passed": new_screen_passed,
                    "new_failure_type": new_ftype,
                    "new_reason": new_reason
                })
                curr_raw = new_raw
                parsed_dict = p_dict
                screen_passed = new_screen_passed
                ftype = new_ftype
                reason = new_reason

            # Evaluate final design under full M5-Eval to compute PVR_eval and gap
            _, final_ref, f_stat, f_msg = parse_design_json(adapter, curr_raw)
            if f_stat != "success":
                eval_passed = False
                eval_ftype = f_stat
                eval_reason = f_msg
            else:
                eval_passed, eval_ftype, eval_reason = evaluate_design_m5_eval(prob, gt, final_ref, cid)

            screen_results.append({
                "case_id": cid,
                "split": gt.split,
                "seed": seed,
                "condition": "ScreenOnly_Feedback",
                "screen_passed": screen_passed,
                "eval_passed": eval_passed,
                "passed": eval_passed,  # For standardized comparison
                "screen_failure_type": ftype,
                "screen_reason": reason,
                "eval_failure_type": eval_ftype,
                "eval_reason": eval_reason,
                "feedback_turns_used": turn,
                "turn1_prompt": t1_prompts[i],
                "initial_response": t1_outs[i].outputs[0].text,
                "final_raw_output": curr_raw,
                "final_parsed_json": parsed_dict,
                "feedback_history": history
            })
            print(f"[{cid}] Seed {seed} Screen-Only: screen_passed={screen_passed}, eval_passed={eval_passed} after {turn} turns")

    # Summarize Screen-Only metrics
    tot = len(screen_results)
    pvr_screen_cnt = sum(1 for r in screen_results if r["screen_passed"])
    pvr_eval_cnt = sum(1 for r in screen_results if r["eval_passed"])
    p_screen, ci_screen = wilson_interval(pvr_screen_cnt, tot)
    p_eval, ci_eval = wilson_interval(pvr_eval_cnt, tot)

    # Per-split Screen vs Eval
    sp_data = {}
    for sp in [1, 2, 3]:
        sp_items = [r for r in screen_results if r["split"] == sp]
        sp_tot = len(sp_items)
        sp_scr = sum(1 for r in sp_items if r["screen_passed"])
        sp_ev = sum(1 for r in sp_items if r["eval_passed"])
        sp_data[f"Split {sp}"] = {
            "total": sp_tot,
            "pvr_screen": sp_scr / sp_tot if sp_tot else 0.0,
            "pvr_screen_ci": list(wilson_interval(sp_scr, sp_tot)[1]),
            "pvr_eval": sp_ev / sp_tot if sp_tot else 0.0,
            "pvr_eval_ci": list(wilson_interval(sp_ev, sp_tot)[1]),
            "screen_to_eval_gap": (sp_scr - sp_ev) / sp_tot if sp_tot else 0.0
        }

    screen_summary = {
        "benchmark": "ScreenOnly_Lumped_Feedback",
        "total_runs": tot,
        "pvr_screen": p_screen,
        "pvr_screen_count": pvr_screen_cnt,
        "pvr_screen_ci": list(ci_screen),
        "pvr_eval": p_eval,
        "pvr_eval_count": pvr_eval_cnt,
        "pvr_eval_ci": list(ci_eval),
        "overall_screen_to_eval_gap": p_screen - p_eval,
        "splits": sp_data,
        "elapsed_seconds": time.perf_counter() - t_scr_start
    }

    with open(out_dir / "screen_only_results.json", "w") as f:
        json.dump({"summary": screen_summary, "results": screen_results}, f, indent=2)

    print(f"\nScreen-Only Completed: PVR_screen={p_screen*100:.1f}%, PVR_eval={p_eval*100:.1f}%, Gap={(p_screen-p_eval)*100:.1f}%")

    # =========================================================================
    # Compute Exact Prompt Diffs for 3 Cases (Section A2)
    # =========================================================================
    diff_cases = ["DEV-M1-S1", "DEV-M2-S1", "DEV-M3-S1"]
    diffs = {}
    for cid in diff_cases:
        b0_run = next(r for r in b0_results if r["case_id"] == cid and r["seed"] == 1)
        ora_run = next(r for r in oracle_results if r["case_id"] == cid and r["seed"] == 1)
        
        # Compare Turn 2 prompts
        t2_b0 = b0_run["turn2_prompt"]
        t2_ora = ora_run["feedback_history"][0]["prompt"] if ora_run["feedback_history"] else "(No feedback turn needed; passed Turn 1)"
        
        diff_lines = list(difflib.unified_diff(
            t2_b0.splitlines(),
            t2_ora.splitlines(),
            fromfile=f"B0_{cid}_Turn2",
            tofile=f"Oracle_{cid}_Turn2",
            lineterm=""
        ))
        diffs[cid] = "\n".join(diff_lines)

    with open(out_dir / "prompt_diffs_b0_vs_oracle.json", "w") as f:
        json.dump(diffs, f, indent=2)

    print("\nAll Round 10 GPU Benchmarks Finished Successfully!")

if __name__ == "__main__":
    main()
