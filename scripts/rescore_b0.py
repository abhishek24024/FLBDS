#!/usr/bin/env python3
"""Rescore Baseline B0 outputs with robust JSON extraction and M5-Eval."""

import json
import re
from pathlib import Path
from pydantic import TypeAdapter, ValidationError

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
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.problem_card import ProblemCard
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


def extract_clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{{"):
        text = text[1:]
    
    # Try finding markdown code block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    
    # Try finding outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    
    return text


def run_m5_eval(prob: ProblemCard, gt: GroundTruthEval, ref_design: TemplateParameters):
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
        return False, "numerical_bound_violation", f"Capacity bound violated: {explanation}"

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
        return False, "unmodelled_coupling", f"Solver exception: {exc}"

    if not res.passed:
        reason_lower = res.reason.lower()
        if any(w in reason_lower for w in ["limit", "exceed", "cap", "biot", "delta_p", "thickness", "drop", "bound"]):
            return False, "numerical_bound_violation", f"Physics check failed: {res.reason}"
        else:
            return False, "unmodelled_coupling", f"Physics check failed: {res.reason}"

    return True, "passed", res.reason


def main():
    dev_base = Path("/home/abhishek24024/flbds/flbds/benchmark/dev")
    case_ids = [
        "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
        "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
        "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
        "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
    ]

    case_data = {}
    for cid in case_ids:
        with open(dev_base / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(dev_base / cid / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())
        case_data[cid] = (prob, gt)

    in_path = "/home/abhishek24024/flbds_data/benchmark/b0_results.json"
    with open(in_path) as f:
        data = json.load(f)

    adapter = TypeAdapter(TemplateParameters)

    rescored_results = []
    parsed_ok = 0

    for r in data["results"]:
        cid = r["case_id"]
        seed = r["seed"]
        prob, gt = case_data[cid]
        raw = r["raw_output"]
        clean_json = extract_clean_json(raw)

        rec = {
            "case_id": cid,
            "split": cid.split("-")[2],
            "seed": seed,
            "raw_output": raw,
            "parsed_json": None,
            "passed": False,
            "failure_type": None,
            "reason": None,
        }

        try:
            pj = json.loads(clean_json)
            rec["parsed_json"] = pj
            ref = adapter.validate_python(pj)
            passed, ftype, reason = run_m5_eval(prob, gt, ref)
            rec["passed"] = passed
            rec["failure_type"] = None if passed else ftype
            rec["reason"] = reason
            parsed_ok += 1
        except json.JSONDecodeError as jde:
            rec["failure_type"] = "json_parse_error"
            rec["reason"] = f"JSON decode error: {jde}"
        except ValidationError as ve:
            rec["failure_type"] = "numerical_bound_violation"
            rec["reason"] = f"Schema validation: {ve.errors()[0]['msg'] if ve.errors() else ve}"
        except Exception as e:
            rec["failure_type"] = "unmodelled_coupling"
            rec["reason"] = str(e)

        rescored_results.append(rec)

    total_runs = len(rescored_results)
    total_passed = sum(1 for r in rescored_results if r["passed"])
    overall_pass_rate = round(total_passed / max(1, total_runs), 3)

    splits = ["S1", "S2", "S3"]
    split_stats = {}
    for sp in splits:
        sp_runs = [r for r in rescored_results if r["split"] == sp]
        sp_pass = sum(1 for r in sp_runs if r["passed"])
        split_stats[sp] = {
            "total": len(sp_runs),
            "passed": sp_pass,
            "pass_rate": round(sp_pass / max(1, len(sp_runs)), 3),
        }

    failure_counts = {}
    for r in rescored_results:
        if not r["passed"]:
            ft = r["failure_type"]
            failure_counts[ft] = failure_counts.get(ft, 0) + 1

    summary = {
        "benchmark": "Baseline B0 on 12 Dev Cases",
        "model": data.get("model", "Qwen2.5-72B-Instruct-FP8"),
        "seeds": data.get("seeds", [1, 2, 3, 4, 5]),
        "total_runs": total_runs,
        "total_passed": total_passed,
        "overall_pass_rate": overall_pass_rate,
        "split_performance": split_stats,
        "failure_types": failure_counts,
        "total_prompt_tokens": data.get("total_prompt_tokens", 0),
        "total_gen_tokens": data.get("total_gen_tokens", 0),
        "elapsed_seconds": data.get("elapsed_seconds", 0),
        "gpu_hours": data.get("gpu_hours", 0),
        "results": rescored_results,
    }

    with open(in_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=========================================================")
    print("RESCORED BASELINE B0 SUMMARY RESULTS")
    print(f"Parsed Successfully: {parsed_ok}/{total_runs} ({parsed_ok/total_runs:.1%})")
    print(f"Overall Pass Rate: {total_passed}/{total_runs} ({overall_pass_rate:.1%})")
    for sp, sstat in split_stats.items():
        print(f"  Split {sp}: {sstat['passed']}/{sstat['total']} ({sstat['pass_rate']:.1%})")
    print("\nFailure Breakdown:")
    for ft, cnt in failure_counts.items():
        pct = (cnt / (total_runs - total_passed) * 100) if (total_runs - total_passed) > 0 else 0
        print(f"  {ft}: {cnt} ({pct:.1f}%)")
    print(f"Updated results saved -> {in_path}")
    print("=========================================================")


if __name__ == "__main__":
    main()
