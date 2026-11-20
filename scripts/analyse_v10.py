#!/usr/bin/env python3
"""scripts/analyse_v10.py
Paired instance-level analysis of V10 run outputs (<run-dir>/<COND>.jsonl).

    python scripts/analyse_v10.py --run-dir /home/abhishek24024/flbds_data/v10_run1 \
        --pairs L3:B0 BoN8:B0 OPT:L3 OPTONLY:OPT L3_BIOMATCH:L3_BIOMISMATCH \
        --confirmatory L3:B0 OPT:L3 L3_BIOMATCH:L3_BIOMISMATCH

Writes <run-dir>/analysis.md and analysis.json. Holm correction is applied across --confirmatory pairs only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from flbds.v10.runner import summarise, wilson
from flbds.v10.stats import holm, markdown_table, paired_compare


def load(run_dir: Path, cond: str) -> list[dict]:
    p = run_dir / f"{cond}.jsonl"
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--pairs", nargs="+", default=["L3:B0", "BoN8:B0", "OPT:L3", "OPTONLY:OPT", "L3_BIOMATCH:L3_BIOMISMATCH", "L3_BIOMATCH:L3"])
    ap.add_argument("--confirmatory", nargs="*", default=["L3:B0", "OPT:L3", "L3_BIOMATCH:L3_BIOMISMATCH"])
    ap.add_argument("--n-boot", type=int, default=10_000)
    args = ap.parse_args()
    run_dir = Path(args.run_dir)

    conds = sorted(
        {c for p in args.pairs for c in p.split(":")}
        | {p.stem for p in run_dir.glob("*.jsonl")}
    )
    data = {c: load(run_dir, c) for c in conds if (run_dir / f"{c}.jsonl").exists()}

    per_cond = {}
    for c, recs in data.items():
        s = summarise(recs, c)
        s.pop("per_family", None)
        per_cond[c] = s

    results = []
    for p in args.pairs:
        a, b = p.split(":")
        if a not in data or b not in data:
            print(f"[skip] {p}: missing condition output")
            continue
        r = paired_compare(data[a], data[b], a, b, n_boot=args.n_boot)
        r["pair"] = p
        r["margin_secondary"] = None
        results.append(r)
    conf = [r for r in results if r["pair"] in args.confirmatory]
    for r, adj in zip(conf, holm([r["p_sign_flip"] for r in conf])):
        r["p_holm"] = adj

    md = ["# V10 analysis", "", "## Per-condition pass rates (runs; Wilson 95% CI)", ""]
    md.append(
        "| condition | runs | eval pass | rate | Wilson CI | screen pass | S&!E | !S&E | tmpl err | tokens/run |"
    )
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    for c, s in per_cond.items():
        lo, hi = wilson(s["eval_passes"], s["n_runs"])
        md.append(
            f"| {c} | {s['n_runs']} | {s['eval_passes']} | {s['pass_rate']:.3f} | [{lo:.3f}, {hi:.3f}] | "
            f"{s['screen_passes']} | {s['screen_pass_eval_fail']} | {s['screen_fail_eval_pass']} | "
            f"{s['template_choice_errors']} | {s['tokens_mean_per_run']:.0f} |"
        )
    md += [
        "",
        "## Paired instance-level comparisons (per-instance pass fraction across seeds)",
        "",
    ]
    md.append(f"Confirmatory (Holm across these only): {', '.join(args.confirmatory)}")
    md.append("")
    md.append(markdown_table(results))
    (run_dir / "analysis.md").write_text("\n".join(md) + "\n")
    (run_dir / "analysis.json").write_text(
        json.dumps({"per_condition": per_cond, "pairs": results}, indent=2)
    )
    print("\n".join(md))


if __name__ == "__main__":
    main()
