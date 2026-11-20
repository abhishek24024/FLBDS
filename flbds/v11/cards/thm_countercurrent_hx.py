"""THM_COUNTERCURRENT_HX: wraps V10 F_HX (TPL_08 counter-current liquid exchanger)."""

from __future__ import annotations

import math

from flbds.v10.families import FAMILIES, HXFamily

from ._v10wrap import convert, legacy_screen, params_from
from .base import ConstraintResult, PhysicsCard

_FAM = FAMILIES["F_HX"]
assert isinstance(_FAM, HXFamily)
RE_LAMINAR_MAX = 2300.0


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    legacy_ok, raw = legacy_screen(_FAM, d, e)
    cons = convert(raw)
    c = _FAM.constants
    re = 4.0 * d["m_dot_cold_kg_s"] / (math.pi * d["hydraulic_diameter_m"] * c["fluid_viscosity_Pa_s"])
    notes: list[str] = []
    if e["T_hot_in_degC"] <= e["T_cold_in_degC"]:
        notes.append("hot inlet not hotter than cold inlet")
    if not legacy_ok and all(x.status == "PASS" for x in cons):
        notes.append("legacy screen_tpl08 check failed")
    th = _FAM._thermo(_FAM.build_params(d, e))
    return cons, notes, {"reynolds_cold": re, "duty_ideal_W": th["duty_ideal"],
                         "duty_axial_degraded_W": th["duty_degraded"], "pressure_drop_Pa": th["dp"],
                         "laminar_flag": float(re <= RE_LAMINAR_MAX)}


CARD = PhysicsCard(
    id="THM_COUNTERCURRENT_HX",
    domain="thermal",
    title="Counter-current liquid-liquid heat exchanger (epsilon-NTU)",
    principle=(
        "Counter-flow effectiveness eps = (1-exp(-NTU(1-Cr)))/(1-Cr exp(-NTU(1-Cr))), NTU = UA/C_min; duty "
        "Q = eps C_min (T_h,in - T_c,in) >= required; duct pressure drop dP = f (L/D) rho v^2/2 (Poiseuille/"
        "Blasius) <= cap; length <= cap. Axial wall conduction degradation reported (Kroeger) as derived."
    ),
    bio_exemplars=["bird leg rete mirabile (counter-current heat retention)", "camel nasal turbinates",
                   "tuna/lamnid shark red-muscle retia", "dolphin flipper arteriovenous bundles"],
    design_space=params_from(_FAM.design_space),
    env_space=params_from(_FAM.env_space, {"T_hot_in_degC": (20.0, 90.0)}),
    references=[
        "Incropera F.P., DeWitt D.P. et al. Fundamentals of Heat and Mass Transfer, ch. 11 (eps-NTU).",
        "Kroeger P.G. (1967) Performance deterioration in high effectiveness heat exchangers due to axial conduction.",
        "Scholander P.F. (1957) The wonderful net, Sci. Am. 196:96-107 (biological counter-current exchange).",
        "flbds.physics.tpl08_countercurrent; flbds.v10.families.HXFamily.",
    ],
    _screen=_screen,
)
