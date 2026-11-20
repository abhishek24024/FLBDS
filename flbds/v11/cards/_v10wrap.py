"""Adapters that expose flbds.v10 families (TPL_02/08/09/10) through the V11 card contract."""

from __future__ import annotations

from typing import Any

from flbds.v10.families import Family, ParamSpec

from .base import MARGIN_FLOOR, ConstraintResult, Param, _make


def params_from(specs: list[ParamSpec], overrides: dict[str, tuple[float, float]] | None = None) -> list[Param]:
    """Convert V10 ParamSpecs to V11 Params (derived env specs carry [0,0] bounds -> overrides)."""
    out = []
    for s in specs:
        lo, hi = (overrides or {}).get(s.name, (s.lo, s.hi))
        out.append(Param(s.name, lo, hi, s.unit, s.desc))
    return out


def convert(cons: list[dict[str, Any]], drop: tuple[str, ...] = ()) -> list[ConstraintResult]:
    """V10 constraint dicts -> ConstraintResult (V10 margins are already signed-normalised)."""
    out = []
    for c in cons:
        if c["name"] in drop:
            continue
        ach = c["achieved"] if c["achieved"] is not None else float("nan")
        m = c["margin_normalised"] if c["margin_normalised"] is not None else MARGIN_FLOOR
        sense = ">=" if c["kind"] == "min" else "<="
        out.append(_make(c["name"], ach, c["limit"], sense, c["unit"], m))
    return out


def legacy_screen(fam: Family, d: dict[str, float], e: dict[str, float]) -> tuple[bool, list[dict[str, Any]]]:
    passed, cons, _ = fam.screen(d, e)
    return passed, cons
