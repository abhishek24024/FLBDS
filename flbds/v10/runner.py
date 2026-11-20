"""flbds/v10/runner.py
Batched V10 condition runner, independent of the LLM backend.

llm.generate(prompts: list[Messages], params: list[GenParams]) -> list[RequestOutput-like]
    each with .outputs[0].text and .outputs[0].token_ids   (see flbds/v10/gen.py, hf_backend.py)

One LLM call per turn (JSON with rationale + template_id + design). Every turn for ALL instances x seeds x
samples of a condition is issued as ONE llm.generate call (+ at most one batched free re-sample for parse
failures, which does not consume a repair turn). Each run (instance x seed) yields ONE final design scored
ONCE by the hidden eval. Selection across samples and turns uses only the screen.

Parsing is strict: missing / non-numeric / out-of-bounds design fields => schema_failure (no clamping).
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from flbds.v10 import prompts as P
from flbds.v10.families import get_family
from flbds.v10.gen import GenParams, derive_seed
from flbds.v10.optimizer_arm import optimise_from


@dataclass(frozen=True)
class Condition:
    name: str
    n_samples: int
    max_repairs: int
    bio: str = "none"  # none | match | mismatch
    optimiser: bool = False
    llm: bool = True


CONDITIONS: dict[str, Condition] = {
    c.name: c
    for c in [
        Condition("B0", 1, 0),
        Condition("L3", 1, 3),
        Condition("BoN8", 8, 0),
        Condition("V10", 8, 3),
        Condition("OPT", 1, 0, optimiser=True),
        Condition("OPTONLY", 0, 0, optimiser=True, llm=False),
        Condition("L3_BIOMATCH", 1, 3, bio="match"),
        Condition("L3_BIOMISMATCH", 1, 3, bio="mismatch"),
        Condition("A24x1", 24, 0),
        Condition("A8x3", 8, 2),
        Condition("A3x8", 3, 7),
    ]
}
DEFAULT_CONDITIONS = [
    "B0",
    "L3",
    "BoN8",
    "OPT",
    "OPTONLY",
    "L3_BIOMATCH",
    "L3_BIOMISMATCH",
]

LLM = Any


@dataclass(frozen=True)
class RunConfig:
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 350
    free_resample_on_parse_failure: bool = True
    opt_maxiter: int = 30
    opt_popsize: int = 10
    log: Callable[[str], None] | None = None


# ----------------------------------------------------------------------------- parsing
_TPL_RE = re.compile(r"TPL[\s_\-]?(\d{1,2})", re.IGNORECASE)


def normalise_template(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    m = _TPL_RE.search(v)
    if not m:
        return None
    tid = f"TPL_{int(m.group(1)):02d}"
    return tid if tid in P.TEMPLATE_IDS else None


def extract_json(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    for cand in (
        raw,
        raw[raw.find("{") : raw.rfind("}") + 1] if "{" in raw and "}" in raw else "",
    ):
        if not cand:
            continue
        try:
            obj = json.loads(cand)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict):
            return obj
    return None


def parse_response(text: str, inst: dict[str, Any]) -> dict[str, Any]:
    """-> {status, chosen_template, design, errors, rationale}. status in
    ok | template_choice_error | schema_failure | parse_failure."""
    obj = extract_json(text)
    if obj is None:
        return {
            "status": "parse_failure",
            "chosen_template": None,
            "design": None,
            "errors": ["no JSON object"],
        }
    chosen = normalise_template(obj.get("template_id"))
    rationale = str(obj.get("rationale", ""))[:500]
    if chosen is None:
        return {
            "status": "parse_failure",
            "chosen_template": None,
            "design": None,
            "errors": ["missing/invalid template_id"],
            "rationale": rationale,
        }
    if chosen != inst["template_id"]:
        return {
            "status": "template_choice_error",
            "chosen_template": chosen,
            "design": None,
            "errors": [],
            "rationale": rationale,
        }
    fam = get_family(inst["family"])
    src = obj.get("design") if isinstance(obj.get("design"), dict) else obj
    design: dict[str, float] = {}
    errors: list[str] = []
    for p in fam.design_space:
        v = src.get(p.name)
        try:
            if isinstance(v, bool):
                raise ValueError
            fv = float(v)  # numeric strings accepted
        except (TypeError, ValueError):
            errors.append(f"{p.name} missing or not a number")
            continue
        if not math.isfinite(fv):
            errors.append(f"{p.name} not finite")
        elif fv < p.lo or fv > p.hi:
            errors.append(f"{p.name}={fv:.4g} outside bounds [{p.lo:.4g}, {p.hi:.4g}]")
        else:
            design[p.name] = fv
    if errors:
        return {
            "status": "schema_failure",
            "chosen_template": chosen,
            "design": None,
            "errors": errors,
            "rationale": rationale,
        }
    return {
        "status": "ok",
        "chosen_template": chosen,
        "design": design,
        "errors": [],
        "rationale": rationale,
    }


def _out(o: Any) -> tuple[str, int]:
    c = o.outputs[0]
    return c.text, len(c.token_ids)


def screen_key(att: dict[str, Any]) -> tuple[int, float]:
    """Screen-only ranking: (screen_pass, min margin); non-scored attempts rank last."""
    if att["status"] != "ok":
        return (0, -1e9)
    return (int(att["screen_pass"]), float(att["screen_min_margin"]))


# ----------------------------------------------------------------------------- trajectories
@dataclass
class Traj:
    inst: dict[str, Any]
    seed: int
    sample: int
    bio_family: str | None
    history: list[dict[str, Any]] = field(default_factory=list)
    turns: list[dict[str, Any]] = field(default_factory=list)
    tokens: int = 0
    parse_failures: int = 0
    schema_failures: int = 0
    done: bool = False


def _score(inst: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    att = dict(parsed)
    if parsed["status"] == "ok":
        fam = get_family(inst["family"])
        passed, cons, reason = fam.screen(parsed["design"], inst["env"])
        att.update(
            screen_pass=passed,
            screen_constraints=cons,
            screen_min_margin=min(c["margin_normalised"] for c in cons),
            screen_reason=reason,
        )
    else:
        att.update(
            screen_pass=False,
            screen_constraints=[],
            screen_min_margin=None,
            screen_reason=parsed["status"],
        )
    return att


def _gp(cfg: RunConfig, key: tuple[int, ...]) -> GenParams:
    return GenParams(
        temperature=cfg.temperature,
        top_p=cfg.top_p,
        seed=derive_seed(key),
        max_tokens=cfg.max_tokens,
    )


def run_llm_trajectories(
    llm: LLM,
    instances: list[dict[str, Any]],
    seeds: list[int],
    cond: Condition,
    cfg: RunConfig,
) -> list[Traj]:
    trajs = [
        Traj(inst, seed, s, P.bio_family_for(inst["family"], cond.bio))
        for inst in instances
        for seed in seeds
        for s in range(cond.n_samples)
    ]
    for turn in range(cond.max_repairs + 1):
        active = [t for t in trajs if not t.done]
        if not active:
            break
        if cfg.log:
            cfg.log(f"  [{cond.name}] turn {turn}: {len(active)} active trajectories")
        msgs = [P.turn_messages(t.inst, t.bio_family, t.history) for t in active]
        outs = llm.generate(
            msgs, [_gp(cfg, (t.seed, t.sample, turn, 0)) for t in active]
        )
        parsed: list[dict[str, Any]] = []
        for t, m, o in zip(active, msgs, outs):
            text, n = _out(o)
            t.tokens += n
            t.turns.append(
                {"turn": turn, "prompt": m[-1]["content"], "responses": [text]}
            )
            parsed.append(parse_response(text, t.inst))
        # one free re-sample for unparseable outputs (does not consume a repair turn)
        redo = [i for i, p in enumerate(parsed) if p["status"] == "parse_failure"]
        if redo and cfg.free_resample_on_parse_failure:
            for i in redo:
                active[i].parse_failures += 1
            outs2 = llm.generate(
                [msgs[i] for i in redo],
                [_gp(cfg, (active[i].seed, active[i].sample, turn, 1)) for i in redo],
            )
            for i, o in zip(redo, outs2):
                text, n = _out(o)
                active[i].tokens += n
                active[i].turns[-1]["responses"].append(text)
                parsed[i] = parse_response(text, active[i].inst)
        for t, p in zip(active, parsed):
            if p["status"] == "parse_failure":
                t.parse_failures += 1
            if p["status"] == "schema_failure":
                t.schema_failures += 1
            att = _score(t.inst, p)
            t.history.append(att)
            t.turns[-1]["attempt"] = att
            if att["screen_pass"] or turn >= cond.max_repairs:
                t.done = True
    return trajs


# ----------------------------------------------------------------------------- scoring
def hidden_score(inst: dict[str, Any], att: dict[str, Any] | None) -> dict[str, Any]:
    """Score ONE final attempt with the hidden eval."""
    if att is None or att["status"] == "parse_failure":
        return {
            "eval_pass": False,
            "failure_type": "parse_failure",
            "eval_margins": {},
            "eval_reason": "unparseable",
        }
    if att["chosen_template"] != inst["template_id"]:
        return {
            "eval_pass": False,
            "failure_type": "template_choice_error",
            "eval_margins": {},
            "eval_reason": f"template {att['chosen_template']} cannot deliver the function",
        }
    if att["status"] != "ok" or att["design"] is None:
        return {
            "eval_pass": False,
            "failure_type": att["status"],
            "eval_margins": {},
            "eval_reason": att["status"],
        }
    fam = get_family(inst["family"])
    passed, margins, reason = fam.hidden_eval(att["design"], inst["env"])
    return {
        "eval_pass": passed,
        "failure_type": "pass" if passed else "physics_failure",
        "eval_margins": margins,
        "eval_min_margin": min(margins.values()) if margins else None,
        "eval_reason": reason,
    }


def _base_record(
    inst: dict[str, Any],
    seed: int,
    cond_name: str,
    att: dict[str, Any] | None,
    tokens: int,
    parse_failures: int,
    turns_used: int,
) -> dict[str, Any]:
    score = hidden_score(inst, att)
    return {
        "instance_id": inst["instance_id"],
        "family": inst["family"],
        "seed": seed,
        "condition": cond_name,
        "chosen_template": att["chosen_template"] if att else None,
        "final_design": att["design"] if att else None,
        "final_status": att["status"] if att else "none",
        "screen_pass": bool(att and att["screen_pass"]),
        "screen_min_margin": att["screen_min_margin"] if att else None,
        "screen_constraints": att["screen_constraints"] if att else [],
        "passed": score["eval_pass"],
        **score,
        "tokens_generated": tokens,
        "parse_failures": parse_failures,
        "turns_used": turns_used,
    }


def run_condition(
    llm: LLM | None,
    instances: list[dict[str, Any]],
    seeds: list[int],
    cond_name: str,
    cfg: RunConfig | None = None,
) -> list[dict[str, Any]]:
    cfg = cfg or RunConfig()
    cond = CONDITIONS[cond_name]
    records: list[dict[str, Any]] = []
    if not cond.llm:  # OPTONLY: oracle family, random init, screen-only optimisation
        for inst in instances:
            fam = get_family(inst["family"])
            for seed in seeds:
                design, info = optimise_from(
                    None,
                    inst["env"],
                    fam,
                    seed=seed,
                    maxiter=cfg.opt_maxiter,
                    popsize=cfg.opt_popsize,
                )
                att = _score(
                    inst,
                    {
                        "status": "ok",
                        "chosen_template": inst["template_id"],
                        "design": design,
                        "errors": [],
                    },
                )
                rec = _base_record(
                    inst, seed, cond_name, att, tokens=0, parse_failures=0, turns_used=0
                )
                rec["optimiser"] = info
                records.append(rec)
        return records

    trajs = run_llm_trajectories(llm, instances, seeds, cond, cfg)
    groups: dict[tuple[str, int], list[Traj]] = {}
    for t in trajs:
        groups.setdefault((t.inst["instance_id"], t.seed), []).append(t)
    for (_, seed), ts in groups.items():
        inst = ts[0].inst
        cands = [(max(t.history, key=screen_key), t) for t in ts if t.history]
        att, chosen_traj = (
            max(cands, key=lambda x: screen_key(x[0])) if cands else (None, ts[0])
        )
        opt_info = None
        if (
            cond.optimiser
            and att is not None
            and att["chosen_template"] == inst["template_id"]
        ):
            init = att["design"] if att["status"] == "ok" else None
            design, opt_info = optimise_from(
                init,
                inst["env"],
                get_family(inst["family"]),
                seed=seed,
                maxiter=cfg.opt_maxiter,
                popsize=cfg.opt_popsize,
            )
            opt_info["llm_initial_attempt"] = {
                k: att.get(k)
                for k in ("design", "status", "screen_pass", "screen_min_margin")
            }
            att = _score(
                inst,
                {
                    "status": "ok",
                    "chosen_template": inst["template_id"],
                    "design": design,
                    "errors": [],
                },
            )
        rec = _base_record(
            inst,
            seed,
            cond_name,
            att,
            tokens=sum(t.tokens for t in ts),
            parse_failures=sum(t.parse_failures for t in ts),
            turns_used=max(len(t.turns) for t in ts) - 1,
        )
        rec["schema_failures"] = sum(t.schema_failures for t in ts)
        rec["selected_sample"] = chosen_traj.sample
        rec["n_samples"] = len(ts)
        rec["bio_family"] = ts[0].bio_family
        rec["trajectories"] = [
            {
                "sample": t.sample,
                "tokens": t.tokens,
                "parse_failures": t.parse_failures,
                "turns": t.turns,
            }
            for t in ts
        ]
        if opt_info is not None:
            rec["optimiser"] = opt_info
        records.append(rec)
    return records


# ----------------------------------------------------------------------------- summary
def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = (z / d) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return max(0.0, c - h), min(1.0, c + h)


def summarise(records: list[dict[str, Any]], cond_name: str) -> dict[str, Any]:
    n = len(records)
    k = sum(r["eval_pass"] for r in records)
    ks = sum(r["screen_pass"] for r in records)
    fams: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        fams.setdefault(r["family"], []).append(r)
    return {
        "condition": cond_name,
        "n_runs": n,
        "eval_passes": k,
        "pass_rate": k / n if n else 0.0,
        "wilson_ci": list(wilson(k, n)),
        "screen_passes": ks,
        "screen_pass_rate": ks / n if n else 0.0,
        "screen_pass_eval_fail": sum(
            r["screen_pass"] and not r["eval_pass"] for r in records
        ),
        "screen_fail_eval_pass": sum(
            (not r["screen_pass"]) and r["eval_pass"] for r in records
        ),
        "template_choice_errors": sum(
            r["failure_type"] == "template_choice_error" for r in records
        ),
        "schema_failure_final": sum(
            r["failure_type"] == "schema_failure" for r in records
        ),
        "parse_failures_total": sum(r["parse_failures"] for r in records),
        "tokens_total": sum(r["tokens_generated"] for r in records),
        "tokens_mean_per_run": (sum(r["tokens_generated"] for r in records) / n)
        if n
        else 0.0,
        "per_family": {
            f: {"n": len(rs), "pass_rate": sum(r["eval_pass"] for r in rs) / len(rs)}
            for f, rs in sorted(fams.items())
        },
    }
