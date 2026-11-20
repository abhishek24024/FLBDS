"""Shared V11 card dataclasses and helpers (contract: docs/v11/INTERFACES.md section 1)."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

MARGIN_FLOOR = -10.0


class DesignSchemaError(ValueError):
    """Design dict is missing a field, has a non-finite value, or is out of bounds."""


class EnvSchemaError(ValueError):
    """Environment dict is missing a required field or has a non-finite value."""


@dataclass(frozen=True)
class Param:
    name: str
    lo: float
    hi: float
    unit: str
    desc: str


@dataclass
class ConstraintResult:
    name: str
    achieved: float
    limit: float
    sense: str
    unit: str
    margin: float
    status: str


@dataclass
class ScreenResult:
    passed: bool
    constraints: list[ConstraintResult]
    regime_ok: bool
    regime_notes: list[str]
    derived: dict[str, float]

    @property
    def min_margin(self) -> float:
        return min((c.margin for c in self.constraints), default=MARGIN_FLOOR)


def ge(name: str, achieved: float, limit: float, unit: str, scale: float | None = None) -> ConstraintResult:
    """achieved >= limit; margin (achieved-limit)/|limit| (or /scale if limit is 0)."""
    s = scale if scale is not None else abs(limit)
    m = (achieved - limit) / s if s > 0 else (0.0 if achieved >= limit else MARGIN_FLOOR)
    return _make(name, achieved, limit, ">=", unit, m)


def le(name: str, achieved: float, limit: float, unit: str, scale: float | None = None) -> ConstraintResult:
    """achieved <= limit; margin (limit-achieved)/|limit|."""
    s = scale if scale is not None else abs(limit)
    m = (limit - achieved) / s if s > 0 else (0.0 if achieved <= limit else MARGIN_FLOOR)
    return _make(name, achieved, limit, "<=", unit, m)


def _make(name: str, achieved: float, limit: float, sense: str, unit: str, m: float) -> ConstraintResult:
    if not math.isfinite(m):
        m = MARGIN_FLOOR
    m = float(max(MARGIN_FLOOR, min(10.0, m)))
    return ConstraintResult(name, float(achieved), float(limit), sense, unit, m, "PASS" if m >= 0 else "MISS")


def validate(values: dict[str, Any], space: list[Param], what: str, check_bounds: bool) -> dict[str, float]:
    """Return a float dict restricted to `space`; raise on missing / non-finite / out-of-bounds."""
    out: dict[str, float] = {}
    errs: list[str] = []
    for p in space:
        if p.name not in values:
            errs.append(f"missing {what} field {p.name!r}")
            continue
        try:
            v = float(values[p.name])
        except (TypeError, ValueError):
            errs.append(f"{what} field {p.name!r} not numeric: {values[p.name]!r}")
            continue
        if not math.isfinite(v):
            errs.append(f"{what} field {p.name!r} not finite")
        elif check_bounds and not (p.lo <= v <= p.hi):
            errs.append(f"{what} field {p.name!r}={v:.4g} outside [{p.lo:.4g}, {p.hi:.4g}] {p.unit}")
        out[p.name] = v
    if errs:
        exc = DesignSchemaError if what == "design" else EnvSchemaError
        raise exc("; ".join(errs))
    return out


ScreenFn = Callable[[dict[str, float], dict[str, float]], tuple[list[ConstraintResult], list[str], dict[str, float]]]


@dataclass(frozen=True)
class PhysicsCard:
    id: str
    domain: str
    title: str
    principle: str
    bio_exemplars: list[str]
    design_space: list[Param]
    env_space: list[Param]
    references: list[str]
    _screen: ScreenFn = field(repr=False, compare=False)

    def screen(self, design: dict, env: dict) -> ScreenResult:
        """Validate inputs (no defaults) and run the closed-form screen.

        `_screen` returns (constraints, regime_violation_notes, derived); an empty
        violation list means the validity window is satisfied.
        """
        d = validate(design, self.design_space, "design", check_bounds=True)
        e = validate(env, self.env_space, "env", check_bounds=False)
        cons, notes, derived = self._screen(d, e)
        regime_ok = not notes
        passed = regime_ok and all(c.status == "PASS" for c in cons)
        return ScreenResult(passed, cons, regime_ok, notes, {k: float(v) for k, v in derived.items()})
