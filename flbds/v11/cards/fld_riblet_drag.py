"""FLD_RIBLET_DRAG: streamwise riblets on a turbulent flat-plate boundary layer."""

from __future__ import annotations

import math

from .base import ConstraintResult, Param, PhysicsCard, ge

LG_OPT = 10.7  # Garcia-Mayoral & Jimenez (2011): optimum l_g+ = sqrt(A_g+) ~ 10.7 for all shapes
LG_ZERO = 17.7  # l_g+ at which DR crosses zero (s+ ~ 25 for h/s = 0.5 blades; Bechert 1997)
DR_MAX_PCT = 9.9  # Bechert et al. (1997) best blade riblets, h/s ~ 0.5
RE_TURB_MIN, RE_MODEL_MAX = 5.0e5, 1.0e9


def friction_velocity(u: float, nu: float, x: float) -> tuple[float, float, float]:
    """Local turbulent flat-plate skin friction Cf = 0.0592 Re_x^-0.2 (Schlichting); u_tau = U sqrt(Cf/2)."""
    re_x = u * x / nu
    cf = 0.0592 * re_x**-0.2
    return u * math.sqrt(cf / 2.0), cf, re_x


def drag_reduction_pct(s_plus: float, h_over_s: float) -> float:
    """Drag change (positive = reduction) vs s+ and blade aspect ratio h/s.

    l_g+ = sqrt(A_g)/s * s+ with groove area A_g ~ h s => l_g+ = sqrt(h/s) s+. Viscous regime: DR rises
    linearly-quadratically to DR_max at l_g+ = 10.7 and falls (breakdown) through zero at l_g+ ~ 17.7,
    then turns into drag increase (capped at -20 %). DR_max(h/s) = 9.9 % * (1 - ((h/s - 0.5)/0.6)^2), a fit
    to Bechert et al. 1997 blade data (approximate).
    """
    lg = math.sqrt(h_over_s) * s_plus
    peak = DR_MAX_PCT * max(0.0, 1.0 - ((h_over_s - 0.5) / 0.6) ** 2)
    if lg <= LG_OPT:
        x = lg / LG_OPT
        return peak * x * (2.0 - x)
    y = (lg - LG_OPT) / (LG_ZERO - LG_OPT)
    return max(-20.0, peak * (1.0 - y**2))


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    s, hs, cov = d["riblet_spacing_m"], d["height_to_spacing"], d["coverage_fraction"]
    u, nu = e["flow_velocity_m_s"], e["kinematic_viscosity_m2_s"]
    u_tau, cf, re_x = friction_velocity(u, nu, e["reference_length_m"])
    s_plus = s * u_tau / nu
    dr_local = drag_reduction_pct(s_plus, hs)
    dr = cov * dr_local
    cons = [
        ge("drag_reduction_pct", dr, e["target_drag_reduction_pct"], "%"),
        ge("riblet_spacing_min_feature_m", s, e["min_feature_m"], "m"),
    ]
    notes: list[str] = []
    if not (RE_TURB_MIN <= re_x <= RE_MODEL_MAX):
        notes.append(f"Re_x = {re_x:.3g} outside turbulent correlation window [{RE_TURB_MIN:.0e}, {RE_MODEL_MAX:.0e}]")
    if s_plus > 40.0:
        notes.append(f"s+ = {s_plus:.1f} > 40: beyond calibrated riblet range (roughness-like drag increase)")
    tau_w = 0.5 * cf * u**2  # per unit density
    return cons, notes, {"s_plus": s_plus, "l_g_plus": math.sqrt(hs) * s_plus, "u_tau_m_s": u_tau,
                         "Re_x": re_x, "skin_friction_coeff": cf, "local_drag_reduction_pct": dr_local,
                         "riblet_height_m": hs * s, "wall_shear_per_density_m2_s2": tau_w}


CARD = PhysicsCard(
    id="FLD_RIBLET_DRAG",
    domain="fluids",
    title="Streamwise riblet film for turbulent skin-friction reduction",
    principle=(
        "Riblets of spacing s reduce turbulent skin friction when s+ = s u_tau/nu is small (viscous regime, "
        "DR ~ m_s s+), with optimum near s+ ~ 15 (l_g+ = sqrt(A_g)/nu*u_tau ~ 10.7) and up to ~10 % reduction for "
        "thin blades (h/s ~ 0.5); beyond s+ ~ 25 Kelvin-Helmholtz rollers cause breakdown and drag increase. "
        "u_tau = U sqrt(Cf/2) with turbulent flat-plate Cf = 0.0592 Re_x^-0.2."
    ),
    bio_exemplars=["shark skin dermal denticles (Isurus oxyrinchus, Carcharhinus)", "sailfish/bird flight-feather grooves"],
    design_space=[
        Param("riblet_spacing_m", 5.0e-6, 2.0e-3, "m", "lateral riblet spacing s"),
        Param("height_to_spacing", 0.2, 1.0, "-", "riblet height / spacing h/s"),
        Param("coverage_fraction", 0.1, 1.0, "-", "fraction of wetted area covered by riblet film"),
    ],
    env_space=[
        Param("flow_velocity_m_s", 1.0, 300.0, "m/s", "free-stream velocity U"),
        Param("kinematic_viscosity_m2_s", 1.0e-6, 1.0e-4, "m2/s", "fluid kinematic viscosity nu"),
        Param("reference_length_m", 0.1, 300.0, "m", "streamwise distance from leading edge at design station"),
        Param("target_drag_reduction_pct", 0.5, 12.0, "%", "required skin-friction drag reduction"),
        Param("min_feature_m", 1.0e-6, 5.0e-4, "m", "minimum manufacturable riblet pitch"),
    ],
    references=[
        "Bechert D.W., Bruse M., Hage W., van der Hoeven J.G.T., Hoppe G. (1997) Experiments on drag-reducing surfaces and their optimization with an adjustable geometry, J. Fluid Mech. 338:59-87.",
        "Garcia-Mayoral R., Jimenez J. (2011) Drag reduction by riblets, Phil. Trans. R. Soc. A 369:1412-1427.",
        "Schlichting H., Gersten K. Boundary-Layer Theory (turbulent flat-plate Cf = 0.0592 Re_x^-0.2).",
        "Dean B., Bhushan B. (2010) Shark-skin surfaces for fluid-drag reduction in turbulent flow: a review, Phil. Trans. R. Soc. A 368:4775.",
    ],
    _screen=_screen,
)
