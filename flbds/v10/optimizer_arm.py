"""flbds/v10/optimizer_arm.py
Bounded optimiser arm against the SCREEN (never the hidden eval).

Conditions:
    OPT      LLM chooses template + initial design -> optimise_from(design_init=llm_design)
    OPTONLY  no LLM, oracle family, random init     -> optimise_from(design_init=None)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import differential_evolution

from flbds.v10.families import Design, Env, Family, get_family


def optimise_from(
    design_init: Design | None,
    env: Env,
    family: Family | str,
    use: str = "screen",
    seed: int = 0,
    maxiter: int = 30,
    popsize: int = 10,
    polish: bool = True,
) -> tuple[Design, dict[str, Any]]:
    """Maximise the minimum normalised SCREEN margin with DE (+L-BFGS-B polish).

    If `design_init` is given it is clipped to bounds and inserted as the first member of the initial
    population (the remaining members are a seeded Latin hypercube). Returns (best_design, info).
    """
    if use != "screen":
        raise ValueError("optimiser arm may only use the screen (use='screen')")
    fam = get_family(family) if isinstance(family, str) else family
    n = len(fam.design_space)
    rng = np.random.default_rng(seed)
    n_pop = max(5, popsize * n)
    # Seeded Latin hypercube in the unit cube.
    init = np.empty((n_pop, n))
    for j in range(n):
        init[:, j] = (rng.permutation(n_pop) + rng.random(n_pop)) / n_pop
    if design_init is not None:
        clipped, _ = fam.clip_design(design_init)
        init[0] = fam.design_to_unit(clipped)
    n_evals = 0

    def obj(u: np.ndarray) -> float:
        nonlocal n_evals
        n_evals += 1
        try:
            return -fam.screen_min_margin(fam.design_from_unit(u), env)
        except Exception:  # noqa: BLE001
            return 10.0

    res = differential_evolution(
        obj,
        bounds=[(0.0, 1.0)] * n,
        maxiter=maxiter,
        init=init,
        seed=seed,
        polish=polish,
        tol=1e-8,
        updating="immediate",
        workers=1,
    )
    best = fam.design_from_unit(np.clip(res.x, 0.0, 1.0))
    passed, cons, _ = fam.screen(best, env)
    return best, {
        "screen_pass": passed,
        "screen_min_margin": float(min(c["margin_normalised"] for c in cons)),
        "n_screen_evals": n_evals,
        "seeded_with_llm_design": design_init is not None,
    }
