#!/usr/bin/env python3
"""E0 (CPU-only): rescore the stored Round-11 Qwen2.5-72B outputs with the V10-fixed scorer.

Fixes applied in the scorer (see git diff): DEV-M4-S1 head 10 m -> 2.5 m (card value),
cos(theta) sign fix in TPL-10 (latent: schema forces theta > 90 deg).

Also measures exposure to the two leakage channels and to schema-default reliance:
  * leak_template_list: a feedback prompt contained the hidden acceptable-template list
  * b3_gt_template:     B3 prompt took its target template from hidden ground truth (no operator fired)
  * default_reliance:   final design omitted >=1 designer field that the schema default-filled
"""

import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
from pydantic import TypeAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.problem_card import ProblemCard
from flbds.schema.templates import TemplateParameters
from scripts.run_round11_benchmarks import (
    DEV_CASES,
    DEV_SPECS,
    evaluate_design_m5_eval,
)

SRC = Path(
    sys.argv[1] if len(sys.argv) > 1 else "/home/abhishek24024/flbds_data/audit11"
)
OUT = Path(
    sys.argv[2] if len(sys.argv) > 2 else "/home/abhishek24024/flbds_data/v10_e0"
)
OUT.mkdir(parents=True, exist_ok=True)
FILES = {
    "B0": "b0_self_critique_results.json",
    "Screen": "screen_only_results.json",
    "Oracle": "oracle_feedback_results.json",
    "B3": "b3_dev_results.json",
}
adapter = TypeAdapter(TemplateParameters)
dev = Path(__file__).resolve().parents[1] / "flbds/benchmark/dev"
cases = {}
for cid in DEV_CASES:
    prob = ProblemCard.model_validate_json(
        (dev / cid / "problem_card.json").read_text()
    )
    gt = GroundTruthEval.model_validate_json(
        (dev / cid / "ground_truth_eval.json").read_text()
    )
    cases[cid] = (prob, gt)


def designer_fields_defaulted(pdict, obj):
    """Fields that the model omitted and the schema filled, excluding env fields overwritten by DEV_SPECS."""
    spec_keys = set().union(*[set(v) for v in DEV_SPECS.values()]) | {
        "pressure_drop_cap_Pa",
        "q_solar_W_m2",
        "h_conv_ambient_W_m2K",
    }
    fields = set(type(obj).model_fields) - {"template_id"}
    return sorted(f for f in fields if f not in pdict and f not in spec_keys)


rows = []
for cond, fn in FILES.items():
    data = json.loads((SRC / fn).read_text())["results"]
    for r in data:
        cid = r["case_id"]
        prob, gt = cases[cid]
        pd = r.get("final_parsed_json")
        new_pass, ftype, defaulted = False, "parse_or_schema_failure", []
        if isinstance(pd, dict):
            try:
                obj = adapter.validate_python(pd)
                defaulted = designer_fields_defaulted(pd, obj)
                new_pass, ftype, _ = evaluate_design_m5_eval(prob, gt, obj, cid)
            except Exception as exc:  # schema failure
                ftype = f"schema_failure: {str(exc)[:60]}"
        fb = r.get("feedback_history") or []
        leak = any(
            "not in acceptable" in (h.get("prompt", "") + h.get("previous_reason", ""))
            for h in fb
        )
        b3_gt = cond == "B3" and not r.get("applied_operator")
        rows.append(
            {
                "condition": cond,
                "case_id": cid,
                "seed": r["seed"],
                "orig_pass": bool(r["passed"]),
                "fixed_pass": bool(new_pass),
                "fixed_ftype": ftype,
                "leak_template_list": leak,
                "b3_gt_template": b3_gt,
                "default_reliance": bool(defaulted),
                "defaulted_fields": defaulted,
            }
        )

(OUT / "e0_rescore_rows.json").write_text(json.dumps(rows, indent=1))


def per_case(cond, key="fixed_pass", exclude_default=False):
    out = {}
    for cid in DEV_CASES:
        rr = [r for r in rows if r["condition"] == cond and r["case_id"] == cid]
        out[cid] = np.mean(
            [r[key] and not (exclude_default and r["default_reliance"]) for r in rr]
        )
    return out


def signflip(d):
    d = np.asarray(d, float)
    obs = abs(d.mean())
    n = len(d)
    cnt = 0
    for s in product([1, -1], repeat=n):
        cnt += abs((d * np.array(s)).mean()) >= obs - 1e-12
    return cnt / 2**n


def cluster_signflip(da):
    clusters = sorted({c[:6] for c in DEV_CASES})
    cm = np.array(
        [np.mean([da[c] for c in DEV_CASES if c.startswith(k)]) for k in clusters]
    )
    return signflip(cm), cm


summary = {}
for cond in FILES:
    rr = [r for r in rows if r["condition"] == cond]
    summary[cond] = {
        "n": len(rr),
        "orig_pass": sum(r["orig_pass"] for r in rr),
        "fixed_pass": sum(r["fixed_pass"] for r in rr),
        "fixed_pass_no_default_reliance": sum(
            r["fixed_pass"] and not r["default_reliance"] for r in rr
        ),
        "runs_with_leaked_template_list": sum(r["leak_template_list"] for r in rr),
        "passes_after_leak": sum(
            r["leak_template_list"] and r["fixed_pass"] for r in rr
        ),
        "b3_gt_template_runs": sum(r["b3_gt_template"] for r in rr),
        "default_reliance_runs": sum(r["default_reliance"] for r in rr),
        "per_case_fixed": per_case(cond),
    }
comp = {}
for a, b in [("Screen", "B0"), ("Oracle", "B0"), ("B3", "Screen")]:
    pa, pb = per_case(a), per_case(b)
    d = [pa[c] - pb[c] for c in DEV_CASES]
    p_case = signflip(d)
    p_cl, cm = cluster_signflip({c: pa[c] - pb[c] for c in DEV_CASES})
    pa2, pb2 = per_case(a, exclude_default=True), per_case(b, exclude_default=True)
    d2 = [pa2[c] - pb2[c] for c in DEV_CASES]
    comp[f"{a}-{b}"] = {
        "mean_diff": float(np.mean(d)),
        "p_signflip_cases(n=12)": p_case,
        "cluster_means": cm.tolist(),
        "p_signflip_clusters(n=4)": p_cl,
        "mean_diff_strict_no_defaults": float(np.mean(d2)),
        "p_signflip_cases_strict": signflip(d2),
    }
summary["comparisons"] = comp
(OUT / "e0_rescore_summary.json").write_text(
    json.dumps(summary, indent=2, default=float)
)
print(
    json.dumps(
        {
            k: {kk: vv for kk, vv in v.items() if kk != "per_case_fixed"}
            for k, v in summary.items()
            if k != "comparisons"
        },
        indent=1,
    )
)
print(json.dumps(comp, indent=1, default=float))
