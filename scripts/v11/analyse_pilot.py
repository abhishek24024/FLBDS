#!/usr/bin/env python3
"""Analyse the V11 pilot (perception/rediscovery + blueprint pairwise). Unit of inference = organism (case);
paired sign-flip permutation tests across cases; bootstrap CIs over cases."""

import json
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np

d = Path(
    sys.argv[1] if len(sys.argv) > 1 else "/home/abhishek24024/flbds_data/v11/e1e2"
)
rng = np.random.default_rng(0)
ARMS = ["IMG", "NAME", "IMG+NAME"]


def signflip(x):
    x = np.asarray(x, float)
    if len(x) == 0 or np.allclose(x, 0):
        return 1.0
    obs = abs(x.mean())
    if len(x) <= 16:
        c = sum(
            abs((x * np.array(s)).mean()) >= obs - 1e-12
            for s in product([1, -1], repeat=len(x))
        )
        return c / 2 ** len(x)
    sims = np.abs((x * rng.choice([-1, 1], size=(100000, len(x)))).mean(1))
    return float((np.sum(sims >= obs - 1e-12) + 1) / (len(sims) + 1))


def boot(x):
    x = np.asarray(x, float)
    b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(5000)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


per = [json.loads(l) for l in open(d / "e1_perception.jsonl")]
raw = {(r["case"], r["arm"], r["seed"]): r for r in per}
j1 = [json.loads(l) for l in open(d / "j1_perception_judged.jsonl")]
res = {"n_cases": len({r["case"] for r in j1})}

metrics = {
    "parsed": lambda r: float(
        raw[(r["case"], r["arm"], r["seed"])]["parsed"] is not None
    ),
    "organism_correct": lambda r: float(
        (r["judge"] or {}).get("organism_correct", 0) or 0
    ),
    "mechanism_score": lambda r: float(
        (r["judge"] or {}).get("mechanism_score", 0) or 0
    ),
    "rediscovery_hit1": lambda r: float(
        ((r["judge"] or {}).get("rediscovery_rank") or 0) == 1
    ),
    "rediscovery_hit5": lambda r: float(
        ((r["judge"] or {}).get("rediscovery_rank") or 0) >= 1
    ),
    "hallucination": lambda r: float((r["judge"] or {}).get("hallucination", 0) or 0),
    "specificity": lambda r: float((r["judge"] or {}).get("specificity", 0) or 0),
    "n_structures": lambda r: float(
        len(
            
                (raw[(r["case"], r["arm"], r["seed"])]["parsed"] or {}).get(
                    "structures"
                )
                or []
            
        )
    ),
    "n_scaled_structures": lambda r: float(
        sum(
            1
            for s in (
                (raw[(r["case"], r["arm"], r["seed"])]["parsed"] or {}).get(
                    "structures"
                )
                or []
            )
            if isinstance(s, dict) and s.get("scale_m_estimate")
        )
    ),
}
case_means = {m: defaultdict(dict) for m in metrics}
for m, f in metrics.items():
    acc = defaultdict(list)
    for r in j1:
        acc[(r["case"], r["arm"])].append(f(r))
    for (c, a), v in acc.items():
        case_means[m][a][c] = float(np.mean(v))
table = {}
for m in metrics:
    table[m] = {}
    for a in ARMS:
        vals = list(case_means[m][a].values())
        table[m][a] = {"mean": float(np.mean(vals)), "ci": boot(vals)}
res["per_arm"] = table
comps = {}
for m in metrics:
    for a, b in [("IMG", "NAME"), ("IMG+NAME", "NAME"), ("IMG+NAME", "IMG")]:
        cs = sorted(set(case_means[m][a]) & set(case_means[m][b]))
        diff = [case_means[m][a][c] - case_means[m][b][c] for c in cs]
        comps[f"{m}:{a}-{b}"] = {
            "n": len(cs),
            "diff": float(np.mean(diff)),
            "ci": boot(diff),
            "p": signflip(diff),
        }
res["paired"] = comps

# per-case rediscovery (IMG arm) for the appendix
res["per_case_img"] = {
    c: {
        m: case_means[m]["IMG"].get(c)
        for m in ("organism_correct", "mechanism_score", "rediscovery_hit5")
    }
    for c in sorted(case_means["organism_correct"]["IMG"])
}

# blueprint pairwise
j2 = [json.loads(l) for l in open(d / "j2_pairwise_judged.jsonl")]
crit = ["novelty", "soundness", "implementability", "overall"]
pw = {a: {k: defaultdict(list) for k in crit} for a in ARMS}
consist = defaultdict(list)
faith = defaultdict(lambda: defaultdict(list))
for r in j2:
    A, B, F = r.get("bio_as_A") or {}, r.get("bio_as_B") or {}, r.get("faith") or {}
    for k in crit:
        s1 = {"A": 1, "B": -1}.get(A.get(k), 0)
        s2 = {"B": 1, "A": -1}.get(B.get(k), 0)
        pw[r["arm"]][k][r["case"]].append((s1 + s2) / 2)
        consist[k].append(float(s1 == s2))
    if F.get("bio_faithfulness") is not None:
        faith[r["arm"]][r["case"]].append(float(F["bio_faithfulness"]))
res["pairwise_bio_vs_nobio"] = {}
for a in ARMS:
    res["pairwise_bio_vs_nobio"][a] = {}
    for k in crit:
        x = [float(np.mean(v)) for v in pw[a][k].values()]
        if x:
            res["pairwise_bio_vs_nobio"][a][k] = {
                "mean_score(-1..1)": float(np.mean(x)),
                "ci": boot(x),
                "p": signflip(x),
                "n_cases": len(x),
            }
    fx = [float(np.mean(v)) for v in faith[a].values()]
    if fx:
        res["pairwise_bio_vs_nobio"][a]["bio_faithfulness_mean_1to5"] = {
            "mean": float(np.mean(fx)),
            "ci": boot(fx),
        }
res["judge_order_consistency"] = {k: float(np.mean(v)) for k, v in consist.items()}
(d / "pilot_analysis.json").write_text(json.dumps(res, indent=1))
print(
    json.dumps(
        {
            "per_arm": {
                m: {a: round(v[a]["mean"], 3) for a in ARMS} for m, v in table.items()
            }
        },
        indent=1,
    )
)
print(
    json.dumps(
        {
            k: v
            for k, v in comps.items()
            if v["p"] < 0.2 or "rediscovery" in k or "organism" in k
        },
        indent=1,
    )
)
print(json.dumps(res["pairwise_bio_vs_nobio"], indent=1))
print("consistency", res["judge_order_consistency"])
