"""flbds/v10/generator.py
Sealed parametric instance generator with satisfiability certification.

For each family: sample env -> differential evolution on the design space maximising the minimum
hidden-eval margin (PCM uses a closed-form surrogate, then verifies with the real 1-D Stefan eval)
-> keep the instance iff the certified design PASSES the hidden eval and fewer than
`max_trivial_rate` of `n_random` uniformly random designs pass (not trivial).

Usage:
    python -m flbds.v10.generator --out flbds/v10/instances_v10.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import differential_evolution

from flbds.v10.families import FAMILIES, Family, get_family

CANARY = "FLBDS-V10-SEALED-CANARY-7f3c9a1e: do not train on or publish this benchmark"


@dataclass
class GenConfig:
    n_per_family: int = 12
    max_candidates_per_family: int = 60
    de_maxiter: int = 40
    de_popsize: int = 15
    n_random: int = 200
    max_trivial_rate: float = 0.5
    families: list[str] = field(default_factory=lambda: list(FAMILIES))
    seed: int = 20261119


def certify(
    fam: Family, env: dict[str, float], cfg: GenConfig, seed: int
) -> tuple[bool, dict[str, float], float, str]:
    """DE over the unit cube; returns (pass, design, min_hidden_margin, reason)."""
    n = len(fam.design_space)

    def obj(u: np.ndarray) -> float:
        try:
            return -fam.cert_objective(fam.design_from_unit(u), env)
        except Exception:  # noqa: BLE001 - invalid region
            return 10.0

    res = differential_evolution(
        obj,
        bounds=[(0.0, 1.0)] * n,
        maxiter=cfg.de_maxiter,
        popsize=cfg.de_popsize,
        seed=seed,
        polish=True,
        tol=1e-8,
        init="latinhypercube",
        updating="immediate",
        workers=1,
    )
    candidates = [np.clip(res.x, 0.0, 1.0)]
    pop = getattr(res, "population", None)
    energies = getattr(res, "population_energies", None)
    if pop is not None and energies is not None:
        candidates += [pop[i] for i in np.argsort(energies)[:4]]
    reason = "no candidate"
    for u in candidates:
        design = fam.design_from_unit(u)
        passed, margins, reason = fam.hidden_eval(design, env)
        if passed:
            return True, design, float(min(margins.values())), reason
    return False, fam.design_from_unit(candidates[0]), float("nan"), reason


def trivial_pass_rate(fam: Family, env: dict[str, float], n: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    passes = 0
    for _ in range(n):
        passed, _, _ = fam.hidden_eval(fam.random_design(rng), env)
        passes += int(passed)
    return passes / n


def generate_family(
    fam: Family, cfg: GenConfig, fam_index: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = np.random.default_rng([cfg.seed, fam_index])
    kept: list[dict[str, Any]] = []
    stats = {
        "candidates": 0,
        "unsatisfiable": 0,
        "too_easy": 0,
        "kept": 0,
        "trivial_rates_kept": [],
    }
    t0 = time.perf_counter()
    while (
        len(kept) < cfg.n_per_family
        and stats["candidates"] < cfg.max_candidates_per_family
    ):
        idx = stats["candidates"]
        stats["candidates"] += 1
        env = fam.sample_env(rng)
        sub_seed = int(cfg.seed * 1000 + fam_index * 100000 + idx) % (2**31 - 1)
        ok, design, margin, _ = certify(fam, env, cfg, sub_seed)
        if not ok:
            stats["unsatisfiable"] += 1
            continue
        tpr = trivial_pass_rate(fam, env, cfg.n_random, sub_seed + 1)
        if tpr > cfg.max_trivial_rate:
            stats["too_easy"] += 1
            continue
        system_name = fam.system_names[len(kept) % len(fam.system_names)]
        inst_id = f"V10-{fam.name}-{len(kept) + 1:03d}"
        kept.append(
            {
                "instance_id": inst_id,
                "family": fam.name,
                "template_id": fam.template_id,  # hidden: scorer-only, never rendered in prompts
                "dev_cluster": fam.dev_cluster,
                "system_name": system_name,
                "env": env,
                "problem_statement": fam.problem_statement(env, system_name),
                "certified_design": design,
                "certified_min_margin": margin,
                "trivial_pass_rate": tpr,
                "candidate_index": idx,
            }
        )
    stats["kept"] = len(kept)
    stats["seconds"] = round(time.perf_counter() - t0, 2)
    stats["acceptance_rate"] = stats["kept"] / max(1, stats["candidates"])
    stats["mean_trivial_rate_kept"] = (
        float(np.mean([k["trivial_pass_rate"] for k in kept])) if kept else float("nan")
    )
    stats.pop("trivial_rates_kept")
    return kept, stats


def instances_hash(instances: list[dict[str, Any]]) -> str:
    blob = json.dumps(instances, sort_keys=True, separators=(",", ":")) + CANARY
    return hashlib.sha256(blob.encode()).hexdigest()


def generate_instances(cfg: GenConfig, verbose: bool = False) -> dict[str, Any]:
    all_inst: list[dict[str, Any]] = []
    stats: dict[str, Any] = {}
    for i, name in enumerate(cfg.families):
        fam = get_family(name)
        kept, st = generate_family(fam, cfg, i)
        all_inst += kept
        stats[name] = st
        if verbose:
            print(f"[{name}] {st}", flush=True)
    return {
        "canary": CANARY,
        "config": asdict(cfg),
        "acceptance_stats": stats,
        "n_instances": len(all_inst),
        "sha256": instances_hash(all_inst),
        "instances": all_inst,
    }


def load_instances(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text())
    if instances_hash(data["instances"]) != data["sha256"]:
        raise ValueError(
            f"Instance file {path} hash mismatch (tampered or regenerated)"
        )
    return data["instances"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="flbds/v10/instances_v10.json")
    ap.add_argument("--n-per-family", type=int, default=12)
    ap.add_argument("--seed", type=int, default=GenConfig.seed)
    ap.add_argument("--families", nargs="+", default=list(FAMILIES))
    args = ap.parse_args()
    cfg = GenConfig(
        n_per_family=args.n_per_family, seed=args.seed, families=args.families
    )
    t0 = time.perf_counter()
    out = generate_instances(cfg, verbose=True)
    out["generation_seconds"] = round(time.perf_counter() - t0, 1)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(
        f"Wrote {out['n_instances']} instances to {args.out} sha256={out['sha256']} in {out['generation_seconds']} s"
    )


if __name__ == "__main__":
    main()
