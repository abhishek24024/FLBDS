"""flbds/v10/stats.py
Instance-level paired statistics (the instance is the unit of inference) + screen relaxation audit.
"""

from __future__ import annotations

import itertools
import re
import json
from pathlib import Path
from typing import Any

import numpy as np

from flbds.v10.families import FAMILIES, get_family


# ----------------------------------------------------------------------------- paired stats
def per_instance_pass(
    records: list[dict[str, Any]], key: str = "eval_pass"
) -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for r in records:
        acc.setdefault(r["instance_id"], []).append(float(bool(r[key])))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def sign_flip_pvalue(
    d: np.ndarray, n_mc: int = 100_000, seed: int = 0, exact_max_n: int = 20
) -> float:
    """Two-sided paired sign-flip permutation p-value for H0: mean(d) == 0.

    Exact enumeration over the non-zero differences when there are <= exact_max_n of them, else
    Monte-Carlo with the +1 correction.
    """
    d = np.asarray(d, dtype=float)
    d = d[d != 0.0]
    n = len(d)
    if n == 0:
        return 1.0
    obs = abs(d.sum())
    if n <= exact_max_n:
        signs = np.array(list(itertools.product([-1.0, 1.0], repeat=n)))
        stats = np.abs(signs @ d)
        return float(np.mean(stats >= obs - 1e-12))
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_mc, n))
    stats = np.abs(signs @ d)
    return float((np.sum(stats >= obs - 1e-12) + 1) / (n_mc + 1))


def bootstrap_ci(
    d: np.ndarray, n_boot: int = 10_000, seed: int = 0, alpha: float = 0.05
) -> tuple[float, float]:
    """Percentile bootstrap CI of the mean, resampling instances."""
    d = np.asarray(d, dtype=float)
    if len(d) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(
        np.quantile(means, 1 - alpha / 2)
    )


def holm(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values (same order as input)."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def paired_compare(
    recs_a: list[dict[str, Any]],
    recs_b: list[dict[str, Any]],
    name_a: str,
    name_b: str,
    key: str = "eval_pass",
    n_boot: int = 10_000,
    seed: int = 0,
) -> dict[str, Any]:
    pa, pb = per_instance_pass(recs_a, key), per_instance_pass(recs_b, key)
    common = sorted(set(pa) & set(pb))
    fam_of = {r["instance_id"]: r["family"] for r in recs_a}
    d = np.array([pa[i] - pb[i] for i in common])
    lo, hi = bootstrap_ci(d, n_boot=n_boot, seed=seed)
    out: dict[str, Any] = {
        "a": name_a,
        "b": name_b,
        "metric": key,
        "n_instances": len(common),
        "mean_a": float(np.mean([pa[i] for i in common])) if common else float("nan"),
        "mean_b": float(np.mean([pb[i] for i in common])) if common else float("nan"),
        "mean_diff": float(d.mean()) if len(d) else float("nan"),
        "sd_diff": float(d.std(ddof=1)) if len(d) > 1 else float("nan"),
        "ci95_bootstrap": [lo, hi],
        "p_sign_flip": sign_flip_pvalue(d, seed=seed),
        "per_family": {},
    }
    for fam in sorted({fam_of[i] for i in common}):
        ids = [i for i in common if fam_of[i] == fam]
        df = np.array([pa[i] - pb[i] for i in ids])
        flo, fhi = bootstrap_ci(df, n_boot=n_boot, seed=seed)
        out["per_family"][fam] = {
            "n": len(ids),
            "mean_a": float(np.mean([pa[i] for i in ids])),
            "mean_b": float(np.mean([pb[i] for i in ids])),
            "mean_diff": float(df.mean()),
            "ci95_bootstrap": [flo, fhi],
            "p_sign_flip": sign_flip_pvalue(df, seed=seed),
        }
    return out


def markdown_table(results: list[dict[str, Any]]) -> str:
    lines = [
        "| A | B | N | mean A | mean B | diff | 95% CI | p (sign-flip) | p (Holm) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['a']} | {r['b']} | {r['n_instances']} | {r['mean_a']:.3f} | {r['mean_b']:.3f} | "
            f"{r['mean_diff']:+.3f} | [{r['ci95_bootstrap'][0]:+.3f}, {r['ci95_bootstrap'][1]:+.3f}] | "
            f"{r['p_sign_flip']:.4g} | {r.get('p_holm', float('nan')):.4g} |"
        )
    lines.append("")
    lines.append("Per-family breakdown:")
    lines.append("| A vs B | family | n | mean A | mean B | diff | 95% CI | p |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in results:
        for fam, f in r["per_family"].items():
            lines.append(
                f"| {r['a']} vs {r['b']} | {fam} | {f['n']} | {f['mean_a']:.3f} | {f['mean_b']:.3f} | "
                f"{f['mean_diff']:+.3f} | [{f['ci95_bootstrap'][0]:+.3f}, {f['ci95_bootstrap'][1]:+.3f}] | "
                f"{f['p_sign_flip']:.4g} |"
            )
    return "\n".join(lines)


# ----------------------------------------------------------------------------- relaxation audit
def relaxation_audit(
    instances: list[dict[str, Any]],
    n_per_family: int = 2000,
    seed: int = 0,
    near_fraction: float = 0.5,
    near_sigma: float = 0.15,
) -> dict[str, Any]:
    """Screen => eval relaxation check.

    Per family, n_per_family designs spread over that family's instances: (1-near_fraction) uniform over the
    design space, near_fraction perturbed around the certified design (unit-cube Gaussian, sigma near_sigma)
    to populate the feasibility boundary. Counts:
        false_rejection  = screen FAIL & eval PASS   (screen too strict; should be 0 for a relaxation)
        false_assurance  = screen PASS & eval FAIL   (screen too loose)
    """
    rng = np.random.default_rng(seed)
    out: dict[str, Any] = {
        "n_per_family": n_per_family,
        "near_fraction": near_fraction,
        "families": {},
    }
    for fname in FAMILIES:
        fam = get_family(fname)
        insts = [i for i in instances if i["family"] == fname]
        if not insts:
            continue
        counts = {
            "uniform": np.zeros((2, 2), int),
            "near_certified": np.zeros((2, 2), int),
        }
        fr_examples: list[dict[str, Any]] = []
        fa_reasons: dict[str, int] = {}
        for k in range(n_per_family):
            inst = insts[k % len(insts)]
            near = rng.random() < near_fraction
            if near:
                u0 = fam.design_to_unit(inst["certified_design"])
                u = np.clip(u0 + rng.normal(0.0, near_sigma, size=len(u0)), 0.0, 1.0)
                design = fam.design_from_unit(u)
            else:
                design = fam.random_design(rng)
            s_pass, cons, _ = fam.screen(design, inst["env"])
            e_pass, margins, reason = fam.hidden_eval(design, inst["env"])
            counts["near_certified" if near else "uniform"][
                int(s_pass), int(e_pass)
            ] += 1
            if not s_pass and e_pass and len(fr_examples) < 5:
                fr_examples.append(
                    {
                        "instance_id": inst["instance_id"],
                        "design": design,
                        "screen_missed": [
                            c["name"] for c in cons if c["margin_normalised"] < 0
                        ],
                    }
                )
            if s_pass and not e_pass:
                key = re.sub(r"[-+]?[0-9][0-9.e+-]*", "#", reason)[:70]
                fa_reasons[key] = fa_reasons.get(key, 0) + 1
        fam_out: dict[str, Any] = {}
        tot = counts["uniform"] + counts["near_certified"]
        for name, c in list(counts.items()) + [("total", tot)]:
            fam_out[name] = {
                "n": int(c.sum()),
                "both_pass": int(c[1, 1]),
                "both_fail": int(c[0, 0]),
                "false_rejection_screen_fail_eval_pass": int(c[0, 1]),
                "false_assurance_screen_pass_eval_fail": int(c[1, 0]),
            }
        fam_out["false_rejection_examples"] = fr_examples
        fam_out["false_assurance_reasons"] = fa_reasons
        out["families"][fname] = fam_out
    return out


def main() -> None:  # pragma: no cover - CLI
    import argparse

    from flbds.v10.generator import load_instances

    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default="flbds/v10/instances_v10.json")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--out", default="flbds/v10/relaxation_audit.json")
    args = ap.parse_args()
    import time

    t0 = time.perf_counter()
    res = relaxation_audit(load_instances(args.instances), n_per_family=args.n)
    res["seconds"] = round(time.perf_counter() - t0, 1)
    Path(args.out).write_text(json.dumps(res, indent=2))
    for f, v in res["families"].items():
        print(f, json.dumps(v["total"]), v["false_assurance_reasons"])
    print(f"wrote {args.out} in {res['seconds']} s")


if __name__ == "__main__":  # pragma: no cover
    main()
