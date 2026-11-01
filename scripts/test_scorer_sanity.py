#!/usr/bin/env python3
"""Sanity check the M5 scorer on 12 reference designs and 12 perturbed designs."""

import json
from pathlib import Path
from pydantic import TypeAdapter

from flbds.schema.templates import TemplateParameters
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.problem_card import ProblemCard
from scripts.rescore_b0 import run_m5_eval

def main():
    dev_base = Path("/home/abhishek24024/flbds/flbds/benchmark/dev")
    case_ids = [
        "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
        "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
        "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
        "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
    ]

    adapter = TypeAdapter(TemplateParameters)

    print("=== SCORER SANITY CHECK ===")
    print("Testing 12 Solver Reference Designs (must all PASS):")
    ref_pass = 0
    for cid in case_ids:
        with open(dev_base / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(dev_base / cid / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        
        ref_path = dev_base / cid / "reference_design.json"
        with open(ref_path) as f:
            ref_dict = json.load(f)
        ref_design = adapter.validate_python(ref_dict)

        passed, ftype, reason = run_m5_eval(prob, gt, ref_design)
        status = "PASS" if passed else f"FAIL ({ftype}: {reason})"
        print(f"  {cid}: {status}")
        if passed:
            ref_pass += 1

    print(f"\nReference designs pass rate: {ref_pass}/12 ({ref_pass/12*100:.1f}%)\n")

    print("Testing 12 Perturbed Designs (must all FAIL):")
    pert_fail = 0
    for cid in case_ids:
        with open(dev_base / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(dev_base / cid / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        
        ref_path = dev_base / cid / "reference_design.json"
        with open(ref_path) as f:
            ref_dict = json.load(f)
        
        # Perturb dimensions and properties to make it physically infeasible
        # e.g., shrink critical dimensions or capacities by 1000x or degrade performance
        template_id = ref_dict.get("template_id")
        if template_id == "TPL_02":
            for key in ["thickness_m", "pcm_latent_heat_J_kg", "pcm_density_kg_m3"]:
                if key in ref_dict and isinstance(ref_dict[key], (int, float)):
                    ref_dict[key] *= 0.01
        elif template_id == "TPL_08":
            for key in ["exchange_area_m2", "heat_transfer_area_m2", "u_overall_W_m2K", "overall_U_W_m2K", "m_dot_hot_kg_s"]:
                if key in ref_dict and isinstance(ref_dict[key], (int, float)):
                    ref_dict[key] *= 0.001
        elif template_id == "TPL_09":
            ref_dict["surface_emissivity"] = 0.05
            ref_dict["emissivity_thermal"] = 0.05
            ref_dict["solar_absorptivity"] = 0.95
            ref_dict["absorptivity_solar"] = 0.95
        elif template_id == "TPL_10":
            ref_dict["membrane_thickness_m"] = 0.1  # 10 cm thick membrane
            ref_dict["porosity"] = 0.001
        elif template_id == "TPL_07":
            ref_dict["fin_height_m"] = 0.0001
            ref_dict["fin_thickness_m"] = 0.00001
        else:
            for key in ["thickness_m", "length_m", "area_m2", "total_mass_kg", "fin_length_m", "volume_m3"]:
                if key in ref_dict and isinstance(ref_dict[key], (int, float)):
                    ref_dict[key] *= 0.001

        perturbed = adapter.validate_python(ref_dict)
        passed, ftype, reason = run_m5_eval(prob, gt, perturbed)
        status = f"FAIL (correctly rejected: {ftype} - {reason[:60]}...)" if not passed else "UNEXPECTED PASS"
        print(f"  {cid}: {status}")
        if not passed:
            pert_fail += 1

    print(f"\nPerturbed designs rejection rate: {pert_fail}/12 ({pert_fail/12*100:.1f}% rejected)\n")

if __name__ == "__main__":
    main()
