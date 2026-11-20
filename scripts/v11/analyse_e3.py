#!/usr/bin/env python3
"""Analyse E3 (Mode B end-to-end with physics checks). Unit = organism (case); paired sign-flip across cases."""

import json
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

import numpy as np

d = Path(
    sys.argv[1] if len(sys.argv) > 1 else "/home/abhishek24024/flbds_data/v11/e1e2"
)
rows = [json.loads(l) for l in open(d / "e3_modeb.jsonl")]
rng = np.random.default_rng(0)


def sf(x):
    x = np.asarray(x, float)
    if len(x) == 0 or np.allclose(x, 0):
        return 1.0
    o = abs(x.mean())
    if len(x) <= 16:
        return sum(
            abs((x * np.array(s)).mean()) >= o - 1e-12
            for s in product([1, -1], repeat=len(x))
        ) / 2 ** len(x)
    s = np.abs((x * rng.choice([-1, 1], size=(100000, len(x)))).mean(1))
    return float((np.sum(s >= o - 1e-12) + 1) / (len(s) + 1))


def boot(x):
    x = np.asarray(x, float)
    b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(5000)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


out = {}
by = defaultdict(lambda: defaultdict(list))
for r in rows:
    by[r["arm"]][r["case"]].append(r)
for arm, cases in by.items():
    rs = [r for v in cases.values() for r in v]
    pc = {c: np.mean([r["passed"] for r in v]) for c, v in cases.items()}
    gold = [r["first_card_is_gold"] for r in rs if r["first_card_is_gold"] is not None]
    out[arm] = {
        "runs": len(rs),
        "cases": len(cases),
        "pass_rate_runs": float(np.mean([r["passed"] for r in rs])),
        "pass_rate_case_mean": float(np.mean(list(pc.values()))),
        "ci": boot(list(pc.values())),
        "first_pass_rate": float(
            np.mean([bool(r["history"][0]["check"][0]) for r in rs])
        ),
        "regime_ok_rate": float(np.mean([r["regime_ok"] for r in rs])),
        "card_plausible_for_problem": float(
            np.mean([r["card_plausible_for_problem"] for r in rs])
        ),
        "first_card_is_gold_rate": float(np.mean(gold)) if gold else None,
        "mean_turns": float(np.mean([r["turns"] for r in rs])),
        "status": dict(Counter(r["status"] for r in rs)),
        "domains_chosen": dict(Counter((r["problem_id"] or "?")[2:5] for r in rs)),
        "cards_chosen": dict(Counter(r["final_card"] for r in rs)),
    }
comp = {}
for a, b in [("IMG", "NOBIO"), ("IMG", "NAME"), ("NAME", "NOBIO")]:
    cs = sorted(set(by[a]) & set(by[b]))
    diff = [
        np.mean([r["passed"] for r in by[a][c]])
        - np.mean([r["passed"] for r in by[b][c]])
        for c in cs
    ]
    if cs:
        comp[f"pass:{a}-{b}"] = {
            "n_cases": len(cs),
            "diff": float(np.mean(diff)),
            "ci": boot(diff),
            "p": sf(diff),
        }
out["paired"] = comp
(d / "e3_analysis.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps(out, indent=1, default=float))
