#!/usr/bin/env python3
"""scripts/audit11_master_b0_table.py
Audit Round 11 Item A3: Master B0 Scorer Table and Flipped Runs Environment Details.
"""

import json
from pathlib import Path
from pydantic import TypeAdapter
from flbds.schema.templates import TemplateParameters
from flbds.schema.problem_card import ProblemCard
from flbds.schema.ground_truth_eval import GroundTruthEval
from scripts.run_round10_benchmarks import evaluate_design_m5_eval, parse_design_json, DEV_SPECS, wilson_interval

def main():
    repo_root = Path("/home/abhishek24024/flbds")
    if not repo_root.exists():
        repo_root = Path(".")
    dev_base = repo_root / "flbds" / "benchmark" / "dev"
    data_base = Path("/home/abhishek24024/flbds_data")
    if not data_base.exists():
        data_base = Path("flbds_data")

    adapter = TypeAdapter(TemplateParameters)

    case_data = {}
    for cid in DEV_SPECS:
        with open(dev_base / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(dev_base / cid / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        case_data[cid] = (prob, gt)

    files = [
        ("b0_results.json (T=0.0 Unguided)", data_base / "benchmark" / "b0_results.json"),
        ("b0_redo_results.json (T=0.0 Guided)", data_base / "benchmark" / "b0_redo_results.json"),
        ("b0_temp07_results.json (T=0.7 Seeds 1-5)", data_base / "benchmark" / "b0_temp07_results.json"),
        ("b0_t07_seeds6to10.json (T=0.7 Seeds 6-10)", data_base / "audit7" / "b0_t07_seeds6to10.json"),
        ("b0_t07_exposed_seeds1to5.json (R7 Invalid)", data_base / "audit7" / "b0_t07_exposed_seeds1to5.json"),
        ("b0_t07_exposed_seeds1to5.json (R8 Valid)", data_base / "audit8" / "b0_t07_exposed_seeds1to5.json"),
        ("b0_self_critique_results.json (R10 Matched)", data_base / "audit10" / "b0_self_critique_results.json"),
    ]

    print("=" * 80)
    print("AUDIT ROUND 11 - MASTER B0 RESCORE TABLE ACROSS ALL SCORER ITERATIONS")
    print("=" * 80)

    master_rows = []

    for label, fpath in files:
        if not fpath.exists():
            print(f"Skipping {label}: missing at {fpath}")
            continue

        with open(fpath) as f:
            data = json.load(f)

        runs = data.get("results") if "results" in data else data.get("runs", data)
        if isinstance(runs, dict):
            runs = list(runs.values())

        n = len(runs)
        orig_passes = sum(1 for r in runs if r.get("passed") is True)
        
        rescored_passes = 0
        flips_p_to_f = []
        flips_f_to_p = []

        for r in runs:
            cid = r.get("case_id")
            seed = r.get("seed")
            orig_p = r.get("passed") is True
            raw = r.get("final_raw_output") or r.get("turn3_response") or r.get("turn3_output") or ""
            if not raw and "parsed_json" in r and r["parsed_json"]:
                raw = json.dumps(r["parsed_json"])

            p_dict, ref, stat, msg = parse_design_json(adapter, raw)
            if stat != "success":
                new_p = False
            else:
                prob, gt = case_data[cid]
                new_p, ftype, reason = evaluate_design_m5_eval(prob, gt, ref, cid)

            if new_p:
                rescored_passes += 1

            if orig_p and not new_p:
                flips_p_to_f.append(f"{cid}_s{seed}")
            elif not orig_p and new_p:
                flips_f_to_p.append(f"{cid}_s{seed}")

        _, orig_ci = wilson_interval(orig_passes, n)
        _, new_ci = wilson_interval(rescored_passes, n)

        master_rows.append({
            "label": label,
            "path": str(fpath.name),
            "n": n,
            "orig_passes": orig_passes,
            "orig_ci": list(orig_ci),
            "rescored_passes": rescored_passes,
            "rescored_ci": list(new_ci),
            "flips_p_to_f": flips_p_to_f,
            "flips_f_to_p": flips_f_to_p,
        })

    # Print Table
    header = f"| {'Benchmark File':<35} | {'N':<3} | {'Original Passes':<18} | {'Rescored Passes (Frozen)':<24} | {'Flips (P->F / F->P)':<20} |"
    sep = f"|{'-'*37}|{'-'*5}|{'-'*20}|{'-'*26}|{'-'*22}|"
    print(header)
    print(sep)
    for row in master_rows:
        orig_str = f"{row['orig_passes']}/{row['n']} ({row['orig_passes']/row['n']*100:.1f}%)"
        new_str = f"{row['rescored_passes']}/{row['n']} ({row['rescored_passes']/row['n']*100:.1f}%)"
        flip_str = f"-{len(row['flips_p_to_f'])} / +{len(row['flips_f_to_p'])}"
        print(f"| {row['label']:<35} | {row['n']:<3} | {orig_str:<18} | {new_str:<24} | {flip_str:<20} |")

    out_file = data_base / "audit11" / "master_b0_rescore_summary.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(master_rows, f, indent=2)
    print(f"\nSaved master B0 rescore summary to {out_file}")

    # Inspect the 7 flipped runs in b0_results.json
    print("\n" + "=" * 80)
    print("DETAILED ENVIRONMENT COMPARISON FOR THE 7 FLIPPED RUNS IN b0_results.json")
    print("=" * 80)
    with open(data_base / "benchmark" / "b0_results.json") as f:
        b0_data = json.load(f)
    b0_runs = b0_data.get("results") or b0_data.get("runs")
    flipped_cids = [
        ("DEV-M3-S1", 1), ("DEV-M3-S1", 2), ("DEV-M3-S3", 2),
        ("DEV-M2-S2", 3), ("DEV-M3-S3", 3), ("DEV-M3-S1", 5), ("DEV-M3-S3", 5)
    ]
    for cid, seed in flipped_cids:
        r = [x for x in b0_runs if x.get("case_id") == cid and x.get("seed") == seed][0]
        prob, gt = case_data[cid]
        p_dict = r.get("parsed_json", {})
        print(f"\n[{cid} Seed {seed} (Original Verdict: PASS)]")
        print(f"  Original Reason: {r.get('reason')}")
        print(f"  Model Proposed JSON Values (Unguided):")
        print(f"    {p_dict}")
        print(f"  Ground Truth Card Environment Values (flbds/benchmark/dev/{cid}/problem_card.json):")
        if "M3" in cid:
            spec = DEV_SPECS[cid]
            print(f"    Solar Irradiance: {spec['solar_irradiance_W_m2']} W/m2 (Model proposed: {p_dict.get('boundary_condition_flux') or p_dict.get('q\'\'\'_solar') or p_dict.get('target_heat_flux') or p_dict.get('flux')})")
            print(f"    Ambient Temp: {spec['T_ambient_degC']} degC / {spec['T_ambient_degC']+273.15} K (Model proposed: {p_dict.get('T_amb') or p_dict.get('ambient_temperature')})")
            print(f"    Sky Temp: {spec['T_sky_degC']} degC / {spec['T_sky_degC']+273.15} K (Model proposed: {p_dict.get('T_sky') or p_dict.get('sky_temperature')})")
            print(f"    Max Inner Leakage Cap: {spec['max_inner_leakage_W_m2']} W/m2")
        elif "M2" in cid:
            spec = DEV_SPECS[cid]
            print(f"    Pressure Drop Cap: {spec['max_pressure_drop_Pa']} Pa (Model proposed: {p_dict.get('pressure_drop')})")
            print(f"    Required Duty: {spec['required_duty_W']} W")
        print(f"  Rescored Verdict: FAIL (Pydantic schema failure or physical constraint violation)")

if __name__ == "__main__":
    main()
