"""Buckingham Pi dimensional similitude analysis, scaling auditor, and exergy check.

Implements Stage 4 of FLBDS:
- Parse SI dimensional exponents (M, L, T, K/Theta, I)
- Compute Buckingham Pi dimensionless nullspace groups D * alpha = 0
- Regime violation metric V_scale(E_B, R_B -> R_T)
- Second-law thermodynamic exergy check (Gouy-Stodola: E_d = T_0 * sigma_gen >= 0)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from scipy.linalg import null_space

from flbds.knowledge.physics import DimensionlessGroup, PhysicalLawsCatalog

FUNDAMENTAL_DIMENSIONS = ("M", "L", "T", "K", "I", "N", "J")
# Normalize Theta -> K
DIM_ALIASES = {"THETA": "K", "CD": "J", "MOL": "N", "A": "I"}


def parse_dimension(dim_str: str | None) -> dict[str, int]:
    """Parse an SI dimension string like 'M L^-1 T^-2' into {dim: exponent}."""
    if not dim_str:
        return {}
    out: dict[str, int] = {}
    tokens = dim_str.strip().split()
    for tok in tokens:
        m = re.match(r"^([a-zA-Z]+)(?:\^?(-?\d+))?$", tok)
        if not m:
            continue
        base = m.group(1).upper()
        base = DIM_ALIASES.get(base, base)
        exp = int(m.group(2)) if m.group(2) is not None else 1
        if base in FUNDAMENTAL_DIMENSIONS:
            out[base] = out.get(base, 0) + exp
    return out


def build_dimensional_matrix(variables: list[tuple[str, str]]) -> tuple[np.ndarray, list[str]]:
    """Build k x n matrix D from a list of (symbol, dimension_str).

    Returns:
        (D, non_zero_dimension_names)
    """
    parsed = [(sym, parse_dimension(dim)) for sym, dim in variables]
    active_dims = [
        d for d in FUNDAMENTAL_DIMENSIONS
        if any(d in p[1] for p in parsed)
    ]
    if not active_dims:
        return np.zeros((0, len(variables))), []

    D = np.zeros((len(active_dims), len(variables)), dtype=float)
    for j, (_, p_dims) in enumerate(parsed):
        for i, d in enumerate(active_dims):
            D[i, j] = p_dims.get(d, 0)
    return D, active_dims


def find_dimensionless_groups(variables: list[tuple[str, str]]) -> list[dict[str, float]]:
    """Compute nullspace basis vectors satisfying D * alpha = 0."""
    D, active_dims = build_dimensional_matrix(variables)
    n = len(variables)
    k = np.linalg.matrix_rank(D) if D.size > 0 else 0
    p = n - k
    if p <= 0:
        return []

    ns = null_space(D)  # shape (n, p)
    groups: list[dict[str, float]] = []

    for col_idx in range(ns.shape[1]):
        vec = ns[:, col_idx]
        # Normalize so largest magnitude is 1.0 or rational
        max_abs = np.max(np.abs(vec))
        if max_abs > 1e-9:
            vec = vec / max_abs
        group_dict = {}
        for (sym, _), val in zip(variables, vec):
            # Round very close to integers or simple fractions
            r_val = round(float(val), 3)
            if abs(r_val) > 1e-4:
                group_dict[sym] = r_val
        if group_dict:
            groups.append(group_dict)
    return groups


@dataclass
class GroupAuditResult:
    group_symbol: str
    group_name: str
    bio_value: float
    eng_value: float
    length_exponent: int
    critical_min: float
    critical_max: float
    in_critical_regime: bool
    scale_violation_score: float
    recommendation: str = ""


@dataclass
class ScaleAuditReport:
    effect_id: str
    length_scale_ratio: float
    v_scale_total: float
    has_violations: bool
    group_results: list[GroupAuditResult] = field(default_factory=list)
    exergy_valid: bool = True
    exergy_destruction_rate: float = 0.0
    ideality: float = 1.0

    def summary(self) -> str:
        status = "VIOLATION" if self.has_violations else "PASS"
        return (
            f"ScaleAudit[{status}] effect={self.effect_id} lambda_L={self.length_scale_ratio:.2e} "
            f"V_scale={self.v_scale_total:.3f} groups_audited={len(self.group_results)}"
        )


class BuckinghamAuditor:
    """Audits physical similitude and scaling across biological and engineering regimes."""

    def __init__(self, catalog: PhysicalLawsCatalog | None = None) -> None:
        self.catalog = catalog or PhysicalLawsCatalog()

    def audit_effect(
        self,
        effect_id: str,
        bio_values: dict[str, float],
        eng_values: dict[str, float],
        length_scale_ratio: float = 1.0,
    ) -> ScaleAuditReport:
        """Evaluate dimensionless Pi-groups and compute V_scale metric."""
        try:
            law = self.catalog.get_law(effect_id)
        except KeyError:
            return ScaleAuditReport(
                effect_id=effect_id,
                length_scale_ratio=length_scale_ratio,
                v_scale_total=0.0,
                has_violations=False,
            )

        group_results: list[GroupAuditResult] = []
        total_v_scale = 0.0

        for grp_sym in law.dimensionless_groups:
            try:
                grp = self.catalog.get_group(grp_sym)
            except KeyError:
                continue

            bio_val = self._evaluate_group_value(grp, bio_values)
            eng_val = self._evaluate_group_value(grp, eng_values)

            # If eng_val not directly provided, scale using length_exponent
            if eng_val is None and bio_val is not None and length_scale_ratio != 1.0:
                eng_val = bio_val * (length_scale_ratio ** grp.length_exponent)

            if bio_val is None or eng_val is None:
                continue

            # Determine critical limits
            crit_min = 0.0
            crit_max = grp.typical_limit
            # If both are below typical_limit, regime is preserved; if eng crosses typical_limit, it violates
            in_regime = (eng_val <= crit_max) if bio_val <= crit_max else (eng_val <= crit_max * 10)
            violation_score = 0.0
            recommendation = "Similitude preserved."

            if not in_regime:
                # V_scale = w_m * |log10(Pi_eng / Pi_bio)|
                ratio = max(1e-12, eng_val) / max(1e-12, bio_val)
                violation_score = abs(math.log10(ratio))
                total_v_scale += violation_score

                if grp.symbol == "Bi" and eng_val > crit_max:
                    recommendation = (
                        "Thermal trapping regime violation (Bi >> 0.1). Apply Separation in Scale / Space: "
                        "decouple macro panel size from conduction thickness via Voronoi/TPMS micro-scaffolds."
                    )
                elif grp.symbol == "Re" and eng_val > crit_max:
                    recommendation = (
                        "Turbulent boundary layer transition (Re > 2300). Apply riblet micro-grooves "
                        "(Separation in Surface Structure) to pin streamwise vortices."
                    )
                elif grp.symbol == "Bo" and eng_val > crit_max:
                    recommendation = (
                        "Gravity dominance over capillarity / adhesion (Bo > 1.0). Apply hierarchical "
                        "micro/nano-scale fibrillation to subdivide contact radius."
                    )
                elif grp.symbol == "Pi_g" and eng_val > crit_max:
                    recommendation = (
                        "Self-weight gravitational bending / buckling. Apply hollow cellular cross-section "
                        "or functionally graded density (TRIZ Principle 40: Composite Materials)."
                    )
                else:
                    recommendation = f"Scale violation for {grp.name}. Geometric parameter requires topological subdivision."

            group_results.append(
                GroupAuditResult(
                    group_symbol=grp.symbol,
                    group_name=grp.name,
                    bio_value=bio_val,
                    eng_value=eng_val,
                    length_exponent=grp.length_exponent,
                    critical_min=crit_min,
                    critical_max=crit_max,
                    in_critical_regime=in_regime,
                    scale_violation_score=round(violation_score, 4),
                    recommendation=recommendation,
                )
            )

        return ScaleAuditReport(
            effect_id=effect_id,
            length_scale_ratio=length_scale_ratio,
            v_scale_total=round(total_v_scale, 4),
            has_violations=any(not g.in_critical_regime for g in group_results),
            group_results=group_results,
        )

    def _evaluate_group_value(
        self, grp: DimensionlessGroup, values: dict[str, float]
    ) -> float | None:
        sym = grp.symbol
        # Direct lookup if present
        if sym in values:
            return float(values[sym])
        for k, v in values.items():
            if k.lower() == sym.lower():
                return float(v)

        # Standard evaluations
        if sym == "Re":
            # rho * v * L / mu
            rho = values.get("rho")
            v = values.get("v")
            L = values.get("L")
            mu = values.get("mu")
            if all(x is not None for x in (rho, v, L, mu)) and mu > 0:
                return float(rho * v * L / mu)
        elif sym == "Bi":
            # h * L_c / k_s
            h = values.get("h")
            L_c = values.get("L_c", values.get("L"))
            k_s = values.get("k_s", values.get("k"))
            if all(x is not None for x in (h, L_c, k_s)) and k_s > 0:
                return float(h * L_c / k_s)
        elif sym == "Bo":
            # delta_rho * g * L^2 / gamma
            drho = values.get("delta_rho", values.get("rho", 1000.0))
            g = values.get("g", 9.81)
            L = values.get("L", values.get("r"))
            gamma = values.get("gamma")
            if all(x is not None for x in (drho, g, L, gamma)) and gamma > 0:
                return float(drho * g * (L ** 2) / gamma)
        elif sym == "Pi_g":
            # rho * g * L / E
            rho = values.get("rho")
            g = values.get("g", 9.81)
            L = values.get("L")
            E = values.get("E")
            if all(x is not None for x in (rho, g, L, E)) and E > 0:
                return float(rho * g * L / E)
        return None

    def audit_exergy(
        self,
        t0: float,
        sigma_gen: float,
        action_utility: float,
        exergy_cost: float = 1.0,
        harmful_penalty: float = 0.0,
    ) -> tuple[bool, float, float]:
        """Evaluate Gouy-Stodola exergy destruction rate and TRIZ Ideality.

        Returns:
            (is_valid, exergy_destruction_rate, triz_ideality)
        """
        edot = t0 * sigma_gen
        is_valid = (edot >= -1e-9)  # 2nd Law: E_d >= 0
        denom = max(1e-6, exergy_cost + harmful_penalty)
        ideality = max(0.0, action_utility) / denom
        return is_valid, round(edot, 4), round(ideality, 4)
