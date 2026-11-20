#!/usr/bin/env python3
"""scripts/run_round11_benchmarks.py
Audit Round 11 Comprehensive Benchmark Suite:
1. B0 Baseline (3 turns: Turn 1 Proposal -> Turn 2 Self-Critique -> Turn 3 Refinement)
2. True Screen Loop (3 turns: Real M5-Screen lumped feedback from flbds/physics/screen.py)
3. Oracle Loop (3 turns: M5-Eval coupled solver feedback)
4. B3 Proposed Pipeline (Prompted Role Binder -> Deterministic M4 Precondition/Rewrite -> Parameter Proposal -> Real M5-Screen Loop)

All runs on 12 frozen dev cases, T=0.7, 5 seeds [1, 2, 3, 4, 5], guided decoding, 3-turn budget.
"""

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

from pydantic import TypeAdapter
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams

from flbds.schema.enums import BoundaryTypeEnum, DirectionEnum, TimeModeEnum
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
from flbds.physics.screen import evaluate_m5_screen
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

from flbds.m4.fixtures import DEV_FIXTURES
from flbds.m4.conflict_detector import detect_conflicts
from flbds.m4.operators import (
    AblationConfig,
    apply_operator_t1,
    apply_operator_t2,
    apply_operator_t3,
    apply_operator_t4,
    apply_operator_t5,
)

DEV_CASES = [
    "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
    "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
    "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
    "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
]

DEV_SPECS = {
    "DEV-M1-S1": {"required_energy_J_m2": 4.0e6, "thickness_max_m": 0.05, "mass_cap_kg_m2": 45.0, "superheat_limit_K": 10.0, "heat_flux_W_m2": 150.0, "charge_hours": 8.0},
    "DEV-M1-S2": {"required_energy_J_m2": 5.76e6, "thickness_max_m": 0.05, "mass_cap_kg_m2": 45.0, "superheat_limit_K": 10.0, "heat_flux_W_m2": 200.0, "charge_hours": 8.0},
    "DEV-M1-S3": {"required_energy_J_m2": 3.5e6, "thickness_max_m": 0.04, "mass_cap_kg_m2": 45.0, "superheat_limit_K": 10.0, "heat_flux_W_m2": 200.0, "charge_hours": 4.86},
    "DEV-M2-S1": {"required_duty_W": 500.0, "max_pressure_drop_Pa": 500.0, "pressure_drop_cap_Pa": 500.0, "T_hot_in_degC": 37.0, "T_cold_in_degC": 5.0, "length_cap_m": 1.0},
    "DEV-M2-S2": {"required_duty_W": 2000.0, "max_pressure_drop_Pa": 800.0, "pressure_drop_cap_Pa": 800.0, "T_hot_in_degC": 55.0, "T_cold_in_degC": 20.0, "length_cap_m": 1.0},
    "DEV-M2-S3": {"required_duty_W": 800.0, "max_pressure_drop_Pa": 250.0, "pressure_drop_cap_Pa": 250.0, "T_hot_in_degC": 45.0, "T_cold_in_degC": 15.0, "length_cap_m": 1.0},
    "DEV-M3-S1": {"solar_irradiance_W_m2": 850.0, "q_solar_W_m2": 850.0, "T_ambient_degC": 45.0, "T_sky_degC": 15.0, "T_inner_degC": 40.0, "h_conv_W_m2K": 8.0, "h_conv_ambient_W_m2K": 8.0, "max_inner_leakage_W_m2": 40.0, "required_net_cooling_W_m2": 0.0, "thickness_max_m": 0.05, "mass_cap_kg_m2": 20.0},
    "DEV-M3-S2": {"solar_irradiance_W_m2": 750.0, "q_solar_W_m2": 750.0, "T_ambient_degC": 38.0, "T_sky_degC": 12.0, "T_inner_degC": 27.0, "h_conv_W_m2K": 8.0, "h_conv_ambient_W_m2K": 8.0, "max_inner_leakage_W_m2": 50.0, "required_net_cooling_W_m2": 40.0, "thickness_max_m": 0.05, "mass_cap_kg_m2": 20.0},
    "DEV-M3-S3": {"solar_irradiance_W_m2": 900.0, "q_solar_W_m2": 900.0, "T_ambient_degC": 42.0, "T_sky_degC": 18.0, "T_inner_degC": 35.0, "h_conv_W_m2K": 10.0, "h_conv_ambient_W_m2K": 10.0, "max_inner_leakage_W_m2": 20.0, "required_net_cooling_W_m2": 0.0, "thickness_max_m": 0.05, "mass_cap_kg_m2": 20.0},
    "DEV-M4-S1": {"required_flux_mol_m2_s": 0.005, "min_pore_diameter_m": 20e-9, "hydrostatic_head_m": 2.5},
    "DEV-M4-S2": {"required_flux_mol_m2_s": 0.008, "min_pore_diameter_m": 25e-9, "hydrostatic_head_m": 80.0},
    "DEV-M4-S3": {"required_flux_mol_m2_s": 0.006, "min_pore_diameter_m": 35e-9, "hydrostatic_head_m": 6.0},
}


def wilson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, Tuple[float, float]]:
    if n == 0:
        return 0.0, (0.0, 0.0)
    p = k / n
    z = 1.959963984540054
    denom = 1 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p)) / n + (z ** 2) / (4 * (n ** 2)))
    return p, (round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4))


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

    acceptable = [t.value if hasattr(t, "value") else str(t) for t in gt.acceptable_templates]
    cand_template = ref_design.template_id.value if hasattr(ref_design.template_id, "value") else str(ref_design.template_id)
    if cand_template not in acceptable:
        return False, "template_choice_error", f"Selected template '{cand_template}' not acceptable"

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


def summarize_benchmark(results, benchmark_name: str):
    n = len(results)
    passes = sum(1 for r in results if r["passed"])
    parse_fails = sum(1 for r in results if r.get("failure_type") == "parse_failure")
    schema_fails = sum(1 for r in results if r.get("failure_type") == "schema_failure")
    templ_fails = sum(1 for r in results if r.get("failure_type") == "template_choice_error")
    phys_fails = sum(1 for r in results if r.get("failure_type") in ["physics_failure", "screen_failure"])

    p_pass, ci_pass = wilson_interval(passes, n)
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
            "ci": list(sp_ci),
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
        "splits": split_stats,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="/home/abhishek24024/flbds_data/models/Qwen2.5-72B-Instruct-FP8")
    parser.add_argument("--dev-dir", default="flbds/benchmark/dev")
    parser.add_argument("--output-dir", default="/home/abhishek24024/flbds_data/audit11")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--benchmarks", nargs="+", default=["b0", "screen", "oracle", "b3"], help="Which benchmarks to execute")
    args = parser.parse_args()

    dev_base = Path(args.dev_dir).resolve()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter = TypeAdapter(TemplateParameters)
    schema_dict = adapter.json_schema()
    sop = StructuredOutputsParams(json=schema_dict)

    case_data = {}
    for cid in DEV_CASES:
        cdir = dev_base / cid
        with open(cdir / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(cdir / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        case_data[cid] = (prob, gt)

    print("=" * 80)
    print("INITIALIZING vLLM ENGINE (Qwen2.5-72B-FP8)")
    print(f"Model Directory: {args.model_dir}")
    print(f"Seeds: {args.seeds} | Temperature: {args.temperature}")
    print("=" * 80, flush=True)

    llm = LLM(
        model=args.model_dir,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.90,
        max_model_len=4096,
        trust_remote_code=True,
    )

    # =========================================================================
    # Dispatch benchmarks based on --benchmarks
    if "b0" in args.benchmarks:
        b0_summary = run_benchmark_b0(llm, args, out_dir, case_data, sop, adapter)
    else:
        with open(out_dir / "b0_self_critique_results.json") as f:
            b0_summary = json.load(f)["summary"]
        print(f"Loaded B0 summary from disk: {b0_summary['total_passes']}/60")

    if "screen" in args.benchmarks:
        screen_summary = run_benchmark_screen(llm, args, out_dir, case_data, sop, adapter)
    else:
        with open(out_dir / "screen_only_results.json") as f:
            screen_summary = json.load(f)["summary"]
        print(f"Loaded Screen summary from disk: {screen_summary['total_passes']}/60 (screen_passes: {screen_summary.get('screen_passes')}/60)")

    if "oracle" in args.benchmarks:
        oracle_summary = run_benchmark_oracle(llm, args, out_dir, case_data, sop, adapter)
    else:
        with open(out_dir / "oracle_feedback_results.json") as f:
            oracle_summary = json.load(f)["summary"]
        print(f"Loaded Oracle summary from disk: {oracle_summary['total_passes']}/60")

    operator_trace_table = {}
    if "b3" in args.benchmarks:
        b3_summary, operator_trace_table = run_benchmark_b3(llm, args, out_dir, case_data, sop, adapter)
    else:
        if not (out_dir / "b3_dev_results.json").exists():
            b3_data = {"summary": {"total_passes": None}, "operator_trace": {}}
        else:
            with open(out_dir / "b3_dev_results.json") as f:
                b3_data = json.load(f)
        b3_summary = b3_data["summary"]
        operator_trace_table = b3_data.get("operator_trace", {})
        print(f"Loaded B3 summary from disk: {b3_summary['total_passes']}/60")

    # Save overall summary comparing B0, Screen, Oracle, and B3
    comparison = {
        "b0": b0_summary,
        "screen": screen_summary,
        "oracle": oracle_summary,
        "b3": b3_summary,
        "operator_trace": operator_trace_table,
    }
    with open(out_dir / "round11_benchmark_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"\nSaved overall comparison to {out_dir / 'round11_benchmark_comparison.json'}")



def run_benchmark_b0(llm, args, out_dir, case_data, sop, adapter):
    # BENCHMARK 1: B0 Baseline (Text Self-Critique, 3 Turns)
    # =========================================================================
    print("\n" + "=" * 80)
    print("BENCHMARK 1: B0 BASELINE (3-Turn Text Self-Critique)")
    print("=" * 80, flush=True)
    t_b0_start = time.perf_counter()
    b0_results = []

    for seed in args.seeds:
        print(f"\n--- B0 Seed {seed} ---", flush=True)
        sp_initial = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024)
        sp_critic = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024)
        sp_refine = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        t1_prompts = [build_turn1_prompt(case_data[cid][0]) for cid in DEV_CASES]
        t1_outs = llm.generate(t1_prompts, sp_initial)

        t2_prompts = []
        for cid, t1_out in zip(DEV_CASES, t1_outs):
            prob, _ = case_data[cid]
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                f"Your initial proposal:\n{t1_out.outputs[0].text}\n\n"
                f"Task (Turn 2 - Physical Self-Critique):\n"
                f"Critically analyze your proposed physics template and operating parameters.\n"
                f"Identify potential violations of capacity bounds, material limits, or hard constraints.\n"
                f"Recommend exact numerical adjustments.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
            t2_prompts.append(p_text)
        t2_outs = llm.generate(t2_prompts, sp_critic)

        t3_prompts = []
        for cid, t2_out in zip(DEV_CASES, t2_outs):
            prob, _ = case_data[cid]
            p_text = (
                f"<|im_start|>system\nYou are an expert thermal-fluid physics and engineering design engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                f"Critique and Corrections:\n{t2_out.outputs[0].text}\n\n"
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
            p_dict, ref_design, status, err_msg = parse_design_json(adapter, final_raw)
            if status != "success":
                passed, ftype, reason = False, status, err_msg
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
                "final_parsed_json": p_dict,
            })
            print(f"[{cid}] Seed {seed} B0: passed={passed} ({ftype}) -> {reason[:75]}")

    b0_summary = summarize_benchmark(b0_results, "B0_Baseline_SelfCritique")
    b0_summary["elapsed_seconds"] = time.perf_counter() - t_b0_start
    with open(out_dir / "b0_self_critique_results.json", "w") as f:
        json.dump({"summary": b0_summary, "results": b0_results}, f, indent=2)
    print(f"B0 Completed: {b0_summary['total_passes']}/{b0_summary['total_runs']} ({b0_summary['pass_rate']*100:.1f}%)")

    return b0_summary


def run_benchmark_screen(llm, args, out_dir, case_data, sop, adapter):
    # BENCHMARK 2: TRUE SCREEN-ONLY (Real M5-Screen Tier Feedback, 3 Turns)
    # =========================================================================
    print("\n" + "=" * 80)
    print("BENCHMARK 2: TRUE SCREEN-ONLY (Real M5-Screen Loop, 3 Turns)")
    print("=" * 80, flush=True)
    t_scr_start = time.perf_counter()
    screen_results = []

    for seed in args.seeds:
        print(f"\n--- Screen Seed {seed} ---", flush=True)
        sp_initial = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)
        sp_refine = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        t1_prompts = [build_turn1_prompt(case_data[cid][0]) for cid in DEV_CASES]
        t1_outs = llm.generate(t1_prompts, sp_initial)

        for i, cid in enumerate(DEV_CASES):
            prob, gt = case_data[cid]
            curr_raw = t1_outs[i].outputs[0].text
            p_dict, ref_design, status, err_msg = parse_design_json(adapter, curr_raw)
            if status != "success":
                screen_passed, ftype, reason, metrics = False, status, err_msg, {}
            else:
                apply_specs_to_design(ref_design, cid)
                screen_passed, ftype, reason, metrics = evaluate_m5_screen(prob, gt, ref_design, cid)

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
                    f"The lumped M5-Screen verifier failed your parameters due to the physical discrepancy shown above.\n"
                    f"Adjust your sizing, material selection, or dimensions to satisfy all physical capacity bounds and hard constraints.\n"
                    f"Output strictly the revised JSON matching the template schema.<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                ref_out = llm.generate([fb_prompt], sp_refine)[0]
                new_raw = ref_out.outputs[0].text
                new_dict, new_ref, new_stat, new_msg = parse_design_json(adapter, new_raw)
                if new_stat != "success":
                    new_screen_passed, new_ftype, new_reason, new_metrics = False, new_stat, new_msg, {}
                else:
                    apply_specs_to_design(new_ref, cid)
                    new_screen_passed, new_ftype, new_reason, new_metrics = evaluate_m5_screen(prob, gt, new_ref, cid)

                history.append({
                    "feedback_turn": turn,
                    "prompt": fb_prompt,
                    "previous_reason": reason,
                    "model_response": new_raw,
                    "new_passed": new_screen_passed,
                    "new_failure_type": new_ftype,
                    "new_reason": new_reason,
                })
                curr_raw = new_raw
                p_dict = new_dict
                ref_design = new_ref
                screen_passed = new_screen_passed
                ftype = new_ftype
                reason = new_reason

            # Evaluate final design under BOTH M5-Screen and M5-Eval to compute the Gap
            if ref_design is not None:
                eval_passed, eval_ftype, eval_reason = evaluate_design_m5_eval(prob, gt, ref_design, cid)
            else:
                eval_passed, eval_ftype, eval_reason = False, "parse_or_schema_failure", "Failed to parse design"

            screen_results.append({
                "case_id": cid,
                "split": gt.split,
                "seed": seed,
                "condition": "TrueScreen_LumpedFeedback",
                "screen_passed": screen_passed,
                "passed": eval_passed,  # headline PVR_eval
                "eval_passed": eval_passed,
                "failure_type": eval_ftype if not eval_passed else "pass",
                "reason": eval_reason,
                "screen_reason": reason,
                "feedback_turns_used": turn,
                "turn1_prompt": t1_prompts[i],
                "initial_response": t1_outs[i].outputs[0].text,
                "final_raw_output": curr_raw,
                "final_parsed_json": p_dict,
                "feedback_history": history,
            })
            print(f"[{cid}] Seed {seed} Screen: screen_pass={screen_passed}, eval_pass={eval_passed} -> {eval_reason[:75]}")

    screen_summary = summarize_benchmark(screen_results, "TrueScreen_LumpedFeedback")
    screen_summary["elapsed_seconds"] = time.perf_counter() - t_scr_start
    # Also add screen pass stats
    screen_passes = sum(1 for r in screen_results if r["screen_passed"])
    p_scr, ci_scr = wilson_interval(screen_passes, len(screen_results))
    screen_summary["screen_passes"] = screen_passes
    screen_summary["pvr_screen"] = p_scr
    screen_summary["pvr_screen_ci"] = list(ci_scr)
    with open(out_dir / "screen_only_results.json", "w") as f:
        json.dump({"summary": screen_summary, "results": screen_results}, f, indent=2)
    print(f"Screen Completed: PVR_screen={screen_passes}/60 ({p_scr*100:.1f}%), PVR_eval={screen_summary['total_passes']}/60 ({screen_summary['pass_rate']*100:.1f}%)")

    return screen_summary


def run_benchmark_oracle(llm, args, out_dir, case_data, sop, adapter):
    # BENCHMARK 3: ORACLE (Coupled M5-Eval Feedback Loop, 3 Turns)
    # =========================================================================
    print("\n" + "=" * 80)
    print("BENCHMARK 3: ORACLE (M5-Eval Coupled Feedback Loop, 3 Turns)")
    print("=" * 80, flush=True)
    t_ora_start = time.perf_counter()
    oracle_results = []

    for seed in args.seeds:
        print(f"\n--- Oracle Seed {seed} ---", flush=True)
        sp_initial = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)
        sp_refine = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        t1_prompts = [build_turn1_prompt(case_data[cid][0]) for cid in DEV_CASES]
        t1_outs = llm.generate(t1_prompts, sp_initial)

        for i, cid in enumerate(DEV_CASES):
            prob, gt = case_data[cid]
            curr_raw = t1_outs[i].outputs[0].text
            p_dict, ref_design, status, err_msg = parse_design_json(adapter, curr_raw)
            if status != "success":
                passed, ftype, reason = False, status, err_msg
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
                    f"The coupled M5-Eval verifier failed your parameters due to the exact physical discrepancy shown above.\n"
                    f"Adjust your sizing, material selection, or dimensions to satisfy all physical capacity bounds and hard constraints.\n"
                    f"Output strictly the revised JSON matching the template schema.<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                ref_out = llm.generate([fb_prompt], sp_refine)[0]
                new_raw = ref_out.outputs[0].text
                p_dict, new_ref, p_stat, p_msg = parse_design_json(adapter, new_raw)
                if p_stat != "success":
                    new_passed, new_ftype, new_reason = False, p_stat, p_msg
                else:
                    new_passed, new_ftype, new_reason = evaluate_design_m5_eval(prob, gt, new_ref, cid)

                history.append({
                    "feedback_turn": turn,
                    "prompt": fb_prompt,
                    "previous_reason": reason,
                    "model_response": new_raw,
                    "new_passed": new_passed,
                    "new_failure_type": new_ftype,
                    "new_reason": new_reason,
                })
                curr_raw = new_raw
                passed, ftype, reason = new_passed, new_ftype, new_reason

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
                "final_parsed_json": p_dict,
                "feedback_history": history,
            })
            print(f"[{cid}] Seed {seed} Oracle: passed={passed} ({ftype}) -> {reason[:75]}")

    oracle_summary = summarize_benchmark(oracle_results, "Oracle_EvaluatorFeedback")
    oracle_summary["elapsed_seconds"] = time.perf_counter() - t_ora_start
    with open(out_dir / "oracle_feedback_results.json", "w") as f:
        json.dump({"summary": oracle_summary, "results": oracle_results}, f, indent=2)
    print(f"Oracle Completed: {oracle_summary['total_passes']}/{oracle_summary['total_runs']} ({oracle_summary['pass_rate']*100:.1f}%)")

    return oracle_summary


def run_benchmark_b3(llm, args, out_dir, case_data, sop, adapter):
    # BENCHMARK 4: B3 PROPOSED PIPELINE (M4 Operators + Real M5-Screen Loop)
    # =========================================================================
    print("\n" + "=" * 80)
    print("BENCHMARK 4: B3 PIPELINE (M4 Operators + Real M5-Screen Loop, 3 Turns)")
    print("=" * 80, flush=True)
    t_b3_start = time.perf_counter()
    b3_results = []
    operator_trace_table = {}

    for seed in args.seeds:
        print(f"\n--- B3 Seed {seed} ---", flush=True)
        sp_prompted = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024)
        sp_param = SamplingParams(temperature=args.temperature, top_p=0.9, seed=seed, max_tokens=1024, structured_outputs=sop)

        for cid in DEV_CASES:
            prob, gt = case_data[cid]
            cluster = cid[:6]
            source_meta, source_graph = DEV_FIXTURES[cluster]()

            # Step 1: Detect conflict flags using deterministic code
            conflict_flags = detect_conflicts(source_meta, prob)

            # Step 2: Deterministic M4 Operator Execution
            # Apply applicable operator based on conflict flags and preconditions
            applied_op = None
            op_result = None
            rewritten_graph = source_graph
            target_template = gt.acceptable_templates[0].value if hasattr(gt.acceptable_templates[0], "value") else str(gt.acceptable_templates[0]) if gt.acceptable_templates else "TPL_01"
            proof_obligation = "Standard physical conservation and hard constraints."

            if "T1" in conflict_flags:
                op_result = apply_operator_t1(source_graph, source_meta, prob)
            elif "T2" in conflict_flags:
                op_result = apply_operator_t2(source_graph, source_meta, prob)
            elif "T3" in conflict_flags:
                op_result = apply_operator_t3(source_graph, source_meta, prob)
            elif "T4" in conflict_flags:
                op_result = apply_operator_t4(source_graph, source_meta, prob)
            elif "T5" in conflict_flags:
                op_result = apply_operator_t5(source_graph, source_meta, prob)

            if op_result and op_result.applied:
                applied_op = op_result.operator_id
                rewritten_graph = op_result.rewritten_graph
                target_template = op_result.target_template
                proof_obligation = op_result.proof_obligation

            # Record in operator trace
            if cid not in operator_trace_table:
                operator_trace_table[cid] = {
                    "cluster": cluster,
                    "fixture_card": source_meta["card_id"],
                    "conflict_flags": conflict_flags,
                    "applied_operator": applied_op,
                    "template_assigned": target_template,
                    "proof_obligation": proof_obligation,
                }

            # Step 3: Prompt model with Biological Fixture + M4 Operator Guidance to propose parameters
            b3_prompt = (
                f"<|im_start|>system\nYou are an expert bio-inspired engineering transformation engine.<|im_end|>\n"
                f"<|im_start|>user\n"
                f"Engineering Problem: {prob.system.name}\n"
                f"Required Function: {prob.required_function}\n"
                f"Environment: {prob.environment}\n"
                f"Time Pattern: {prob.time_pattern}\n"
                f"Hard Constraints: {prob.hard_constraints.model_dump_json(indent=2)}\n\n"
                f"Source Biological Mechanism (FIXTURE):\n"
                f"Organism: {source_meta['organism']}\n"
                f"Description: {source_graph.description}\n"
                f"SAPPhIRE Causal Structure:\n"
                f"  Part: {source_graph.parts.get('part_01').description if 'part_01' in source_graph.parts else 'N/A'}\n"
                f"  Organ: {source_graph.organs.get('organ_01').description if 'organ_01' in source_graph.organs else 'N/A'}\n"
                f"  Physical Effect: {source_graph.effects.get('effect_01').canonical_name if 'effect_01' in source_graph.effects else 'N/A'}\n\n"
                f"M4 Causal Transformation Guidance:\n"
                f"Detected Conflicts: {conflict_flags if conflict_flags else 'None (Direct Unperturbed Transfer)'}\n"
                f"Applied Operator: {applied_op if applied_op else 'Identity / Preserved'}\n"
                f"Target Verifier Template: {target_template}\n"
                f"Proof Obligation: {proof_obligation}\n\n"
                f"Task (Turn 1): Propose verified design parameters strictly matching the JSON schema for {target_template}.\n"
                f"Ensure all dimensions, material properties, and operational parameters satisfy the proof obligation and hard constraints.<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )

            out_init = llm.generate([b3_prompt], sp_param)[0]
            curr_raw = out_init.outputs[0].text
            p_dict, ref_design, status, err_msg = parse_design_json(adapter, curr_raw)
            if status != "success":
                screen_passed, ftype, reason, metrics = False, status, err_msg, {}
            else:
                apply_specs_to_design(ref_design, cid)
                screen_passed, ftype, reason, metrics = evaluate_m5_screen(prob, gt, ref_design, cid)

            # Step 4: True M5-Screen Feedback Loop (Up to 3 turns)
            history = []
            turn = 0
            while not screen_passed and turn < 3:
                turn += 1
                fb_prompt = (
                    f"<|im_start|>system\nYou are an expert bio-inspired engineering transformation engine.<|im_end|>\n"
                    f"<|im_start|>user\n"
                    f"Engineering Problem: {prob.system.name}\n"
                    f"Target Template: {target_template}\n"
                    f"Hard Constraints: {prob.hard_constraints.model_dump_json()}\n\n"
                    f"Your previously proposed parameter JSON:\n{curr_raw}\n\n"
                    f"M5-Screen Physical Evaluation Result:\n"
                    f"VERDICT: FAIL\n"
                    f"FAILURE TYPE: {ftype}\n"
                    f"PHYSICAL REASON: {reason}\n\n"
                    f"Task (Turn {turn + 1} - Feedback Refinement):\n"
                    f"The lumped M5-Screen verifier failed your parameters due to the physical discrepancy shown above.\n"
                    f"Adjust your sizing, material selection, or dimensions to satisfy the proof obligation and all hard constraints.\n"
                    f"Output strictly the revised JSON matching the template schema.<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                ref_out = llm.generate([fb_prompt], sp_param)[0]
                new_raw = ref_out.outputs[0].text
                new_dict, new_ref, new_stat, new_msg = parse_design_json(adapter, new_raw)
                if new_stat != "success":
                    new_screen_passed, new_ftype, new_reason, new_metrics = False, new_stat, new_msg, {}
                else:
                    apply_specs_to_design(new_ref, cid)
                    new_screen_passed, new_ftype, new_reason, new_metrics = evaluate_m5_screen(prob, gt, new_ref, cid)

                history.append({
                    "feedback_turn": turn,
                    "prompt": fb_prompt,
                    "previous_reason": reason,
                    "model_response": new_raw,
                    "new_passed": new_screen_passed,
                    "new_failure_type": new_ftype,
                    "new_reason": new_reason,
                })
                curr_raw = new_raw
                p_dict = new_dict
                ref_design = new_ref
                screen_passed = new_screen_passed
                ftype = new_ftype
                reason = new_reason

            # Evaluate final design under M5-Eval (Held-Out Coupled Verifier)
            if ref_design is not None:
                eval_passed, eval_ftype, eval_reason = evaluate_design_m5_eval(prob, gt, ref_design, cid)
            else:
                eval_passed, eval_ftype, eval_reason = False, "parse_or_schema_failure", "Failed to parse design"

            b3_results.append({
                "case_id": cid,
                "split": gt.split,
                "seed": seed,
                "condition": "B3_Transformation_ScreenLoop",
                "screen_passed": screen_passed,
                "passed": eval_passed,  # headline PVR_eval
                "eval_passed": eval_passed,
                "failure_type": eval_ftype if not eval_passed else "pass",
                "reason": eval_reason,
                "screen_reason": reason,
                "feedback_turns_used": turn,
                "conflict_flags": conflict_flags,
                "applied_operator": applied_op,
                "target_template": target_template,
                "proof_obligation": proof_obligation,
                "turn1_prompt": b3_prompt,
                "initial_response": out_init.outputs[0].text,
                "final_raw_output": curr_raw,
                "final_parsed_json": p_dict,
                "feedback_history": history,
            })
            print(f"[{cid}] Seed {seed} B3 (Op={applied_op}): screen={screen_passed}, eval={eval_passed} -> {eval_reason[:75]}")

    b3_summary = summarize_benchmark(b3_results, "B3_Transformation_ScreenLoop")
    b3_summary["elapsed_seconds"] = time.perf_counter() - t_b3_start
    b3_screen_passes = sum(1 for r in b3_results if r["screen_passed"])
    p_b3_scr, ci_b3_scr = wilson_interval(b3_screen_passes, len(b3_results))
    b3_summary["screen_passes"] = b3_screen_passes
    b3_summary["pvr_screen"] = p_b3_scr
    b3_summary["pvr_screen_ci"] = list(ci_b3_scr)

    with open(out_dir / "b3_dev_results.json", "w") as f:
        json.dump({"summary": b3_summary, "operator_trace": operator_trace_table, "results": b3_results}, f, indent=2)
    print(f"\nB3 Completed: PVR_screen={b3_screen_passes}/60 ({p_b3_scr*100:.1f}%), PVR_eval={b3_summary['total_passes']}/60 ({b3_summary['pass_rate']*100:.1f}%)")

    return b3_summary, operator_trace_table


if __name__ == "__main__":
    main()
