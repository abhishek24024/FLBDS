"""Tests for flbds.v10.stats."""

from __future__ import annotations

import numpy as np

from flbds.v10.stats import (
    bootstrap_ci,
    holm,
    paired_compare,
    per_instance_pass,
    sign_flip_pvalue,
)


def test_sign_flip_exact_small() -> None:
    # all 5 differences positive -> two-sided exact p = 2/2^5
    p = sign_flip_pvalue(np.array([0.2, 0.4, 0.1, 0.3, 0.5]))
    assert abs(p - 2 / 32) < 1e-12


def test_sign_flip_null_is_large() -> None:
    p = sign_flip_pvalue(np.array([0.2, -0.2, 0.1, -0.1, 0.0, 0.3, -0.3]))
    assert p > 0.9


def test_sign_flip_monte_carlo_strong_effect() -> None:
    rng = np.random.default_rng(0)
    d = rng.normal(0.3, 0.2, size=60)
    assert sign_flip_pvalue(d, n_mc=20000, seed=1) < 0.001


def test_bootstrap_ci_contains_true_mean() -> None:
    rng = np.random.default_rng(1)
    hits = 0
    for i in range(40):
        x = rng.normal(0.25, 0.3, size=64)
        lo, hi = bootstrap_ci(x, n_boot=2000, seed=i)
        hits += lo <= 0.25 <= hi
    assert hits >= 34  # ~95% nominal coverage


def test_holm() -> None:
    adj = holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])


def test_paired_compare_end_to_end() -> None:
    recs_a, recs_b = [], []
    for i in range(20):
        fam = "F_A" if i < 10 else "F_B"
        for s in (1, 2, 3):
            recs_a.append(
                {"instance_id": f"I{i}", "family": fam, "seed": s, "eval_pass": True}
            )
            recs_b.append(
                {
                    "instance_id": f"I{i}",
                    "family": fam,
                    "seed": s,
                    "eval_pass": (i + s) % 3 == 0,
                }
            )
    res = paired_compare(recs_a, recs_b, "A", "B", n_boot=2000)
    assert res["mean_diff"] > 0.5
    assert res["p_sign_flip"] < 0.001
    assert set(res["per_family"]) == {"F_A", "F_B"}
    pa = per_instance_pass(recs_a)
    assert pa["I0"] == 1.0
