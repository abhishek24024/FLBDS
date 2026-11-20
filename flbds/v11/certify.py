"""Certify every (problem, plausible card) pair by maximising the min constraint margin.

Run:  python -m flbds.v11.certify   -> writes flbds/v11/problem_feasibility.json
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import differential_evolution

from flbds.v11.cards import CARDS, PhysicsCard
from flbds.v11.cards.base import MARGIN_FLOOR, Param
from flbds.v11.problems import PROBLEMS, Problem

OUT_PATH = Path(__file__).with_name("problem_feasibility.json")
REGIME_PENALTY = 1.0
LOG_RATIO = 50.0


def _is_log(p: Param) -> bool:
    return p.lo > 0 and p.hi / p.lo >= LOG_RATIO


def from_unit(space: list[Param], u: np.ndarray) -> dict[str, float]:
    out: dict[str, float] = {}
    for p, x in zip(space, u, strict=True):
        x = float(min(1.0, max(0.0, x)))
        if _is_log(p):
            v = math.exp(math.log(p.lo) + x * (math.log(p.hi) - math.log(p.lo)))
        else:
            v = p.lo + x * (p.hi - p.lo)
        out[p.name] = float(min(p.hi, max(p.lo, v)))
    return out


def objective(
    card: PhysicsCard, design: dict[str, float], env: dict[str, float]
) -> float:
    """Min margin, minus a penalty if the validity regime is violated (higher is better)."""
    try:
        res = card.screen(design, env)
    except (ValueError, ZeroDivisionError, OverflowError):
        return MARGIN_FLOOR
    m = res.min_margin
    if not math.isfinite(m):
        return MARGIN_FLOOR
    return m if res.regime_ok else min(m, 0.0) - REGIME_PENALTY * len(res.regime_notes)


@dataclass
class CertResult:
    card_id: str
    feasible: bool
    min_margin: float
    regime_ok: bool
    regime_notes: list[str]
    best_design: dict[str, float]
    binding_constraint: str


def certify_pair(
    card: PhysicsCard, env: dict[str, float], seed: int = 0, maxiter: int = 120
) -> CertResult:
    space = card.design_space

    def f(u: np.ndarray) -> float:
        return -objective(card, from_unit(space, u), env)

    r = differential_evolution(
        f,
        [(0.0, 1.0)] * len(space),
        seed=seed,
        maxiter=maxiter,
        popsize=20,
        tol=1e-8,
        polish=False,
        init="sobol",
    )
    design = from_unit(space, r.x)
    res = card.screen(design, env)
    binding = (
        min(res.constraints, key=lambda c: c.margin).name if res.constraints else ""
    )
    return CertResult(
        card.id,
        res.passed,
        res.min_margin,
        res.regime_ok,
        res.regime_notes,
        design,
        binding,
    )


def certify_problem(prob: Problem, seed: int = 0) -> dict[str, Any]:
    results = [
        certify_pair(CARDS[cid], prob.env, seed=seed) for cid in prob.plausible_cards
    ]
    feas = [r.card_id for r in results if r.feasible]
    return {
        "problem_id": prob.id,
        "domain": prob.domain,
        "title": prob.title,
        "plausible_cards": prob.plausible_cards,
        "feasible_cards": feas,
        "choice_sensitive": len(prob.plausible_cards) >= 2,
        "discriminating": len(prob.plausible_cards) >= 2
        and 0 < len(feas) < len(prob.plausible_cards),
        "results": [r.__dict__ for r in results],
    }


def main() -> None:
    rows = [certify_problem(p) for p in PROBLEMS]
    summary = {
        "n_problems": len(rows),
        "n_choice_sensitive": sum(r["choice_sensitive"] for r in rows),
        "n_discriminating": sum(r["discriminating"] for r in rows),
        "n_without_feasible_card": sum(not r["feasible_cards"] for r in rows),
        "n_pairs": sum(len(r["results"]) for r in rows),
        "n_feasible_pairs": sum(len(r["feasible_cards"]) for r in rows),
    }
    OUT_PATH.write_text(json.dumps({"summary": summary, "problems": rows}, indent=1))
    for r in rows:
        tags = ", ".join(
            f"{x['card_id']}:{'OK' if x['feasible'] else 'X'}({x['min_margin']:+.2f},{x['binding_constraint']})"
            for x in r["results"]
        )
        print(f"{r['problem_id']:<10} {tags}")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
