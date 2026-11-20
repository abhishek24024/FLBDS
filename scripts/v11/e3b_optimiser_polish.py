#!/usr/bin/env python3
"""E3b (CPU): optimiser polish on E3 runs. For each E3 run with a valid (problem, card) after the LLM loop, run
bounded differential evolution on the card's design space against the card screen (env from the problem), seeded with
the LLM's final design. Reports physics pass after polish per arm and domain. Mirrors the V10 OPT arm."""
import json, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from flbds.v11.cards import CARDS  # noqa: E402
from flbds.v11.problems import PROBLEMS  # noqa: E402

PROB = {p.id: p for p in PROBLEMS}
d = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs/v11/results")
rows = [json.loads(l) for l in open(d / "e3_modeb.jsonl")]
out = []
for r in rows:
    pid, cid = r["problem_id"], r["final_card"]
    rec = {k: r[k] for k in ("case", "arm", "seed", "problem_id", "final_card", "passed")}
    if pid not in PROB or cid not in CARDS:
        rec.update(polish_status="invalid_ids", polished_pass=False); out.append(rec); continue
    card, env = CARDS[cid], PROB[pid].env
    sp = card.design_space
    names = [p.name for p in sp]; lo = np.array([p.lo for p in sp]); hi = np.array([p.hi for p in sp])

    def f(x):
        try:
            res = card.screen(dict(zip(names, map(float, x))), env)
        except Exception as e:  # env mismatch => card cannot address this problem
            raise RuntimeError(str(e))
        return -(res.min_margin if res.regime_ok else min(res.min_margin, -0.01))

    seed = r.get("final_design", {}).get("design") or {}
    def _v(n, a, b):
        v = seed.get(n)
        try:
            v = float(v)
        except (TypeError, ValueError):
            return (a + b) / 2
        e = 1e-6 * (b - a)
        return float(np.clip(v, a + e, b - e)) if np.isfinite(v) else (a + b) / 2
    x0 = np.array([_v(n, a, b) for n, a, b in zip(names, lo, hi)])
    try:
        f(x0)
    except RuntimeError:
        rec.update(polish_status="card_problem_mismatch", polished_pass=False); out.append(rec); continue
    res = differential_evolution(f, list(zip(lo, hi)), x0=x0, maxiter=40, popsize=12, seed=1, polish=True, tol=1e-6)
    sr = card.screen(dict(zip(names, map(float, res.x))), env)
    rec.update(polish_status="ok", polished_pass=bool(sr.passed), polished_min_margin=float(sr.min_margin), regime_ok=bool(sr.regime_ok))
    out.append(rec)
(d / "e3b_polish.jsonl").write_text("\n".join(json.dumps(x) for x in out) + "\n")
summ = {}
for arm in ("IMG", "NAME", "NOBIO"):
    rs = [x for x in out if x["arm"] == arm]
    dom = defaultdict(lambda: [0, 0, 0])
    for x in rs:
        k = (x["problem_id"] or "?")[2:5]; dom[k][0] += x["passed"]; dom[k][1] += x["polished_pass"]; dom[k][2] += 1
    summ[arm] = {"llm_loop_pass": f"{sum(x['passed'] for x in rs)}/{len(rs)}", "after_polish": f"{sum(x['polished_pass'] for x in rs)}/{len(rs)}",
                 "status": {s: sum(1 for x in rs if x['polish_status'] == s) for s in ('ok', 'invalid_ids', 'card_problem_mismatch')},
                 "by_domain(llm, polished, n)": {k: tuple(v) for k, v in sorted(dom.items())}}
(d / "e3b_summary.json").write_text(json.dumps(summ, indent=1))
print(json.dumps(summ, indent=1))
