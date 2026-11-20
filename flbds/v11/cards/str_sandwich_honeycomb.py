"""STR_SANDWICH_HONEYCOMB: hexagonal-honeycomb-core sandwich beam (Gibson-Ashby core + Allen beam)."""

from __future__ import annotations

import math

from ._sandwich import SANDWICH_ENV, SANDWICH_REFS, sandwich_checks, thin_face_note
from .base import ConstraintResult, Param, PhysicsCard, ge

# Aluminium 5052 foil (core material constants).
CORE_E_PA, CORE_G_PA, CORE_RHO, CORE_SY_PA = 70.0e9, 26.0e9, 2680.0, 215.0e6
FACE_NU = 0.3


def core_properties(rho_rel: float) -> tuple[float, float, float]:
    """Gibson & Ashby (1997) regular hexagonal honeycomb, out-of-plane.

    E3 = E_s rho_rel; G13 = (1/sqrt3)(t/l) G_s = 0.5 rho_rel G_s (rho_rel = (2/sqrt3) t/l);
    shear strength = min(plastic 0.5 rho_rel tau_ys, elastic wall buckling ~ E_s (t/l)^3).
    """
    t_over_l = rho_rel * math.sqrt(3.0) / 2.0
    ec = CORE_E_PA * rho_rel
    gc = 0.5 * rho_rel * CORE_G_PA
    tau_pl = 0.5 * rho_rel * CORE_SY_PA / math.sqrt(3.0)
    tau_el = CORE_E_PA * t_over_l**3
    return ec, gc, min(tau_pl, tau_el)


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    t, c, rr, s = d["face_thickness_m"], d["core_thickness_m"], d["core_relative_density"], d["cell_size_m"]
    ec, gc, tau = core_properties(rr)
    dimple = 2.0 * e["face_modulus_Pa"] / (1.0 - FACE_NU**2) * (2.0 * t / s) ** 2  # Norris intracell buckling
    cons, der = sandwich_checks(t, c, e, ec, gc, tau, CORE_RHO * rr * c, dimple)
    wall = rr * s / 2.0  # t_w for regular hexagon, s across flats
    cons.append(ge("cell_wall_thickness_m", wall, e["min_foil_thickness_m"], "m"))
    der["cell_wall_thickness_m"] = wall
    notes = thin_face_note(t, c)
    if not (0.005 <= rr <= 0.2):
        notes.append(f"relative density {rr:.3f} outside Gibson-Ashby thin-wall window [0.005, 0.2]")
    if c < 2.0 * s:
        notes.append(f"core thickness {c:.4g} m < 2 cell sizes: core not continuum-like")
    return cons, notes, der


CARD = PhysicsCard(
    id="STR_SANDWICH_HONEYCOMB",
    domain="structures",
    title="Honeycomb-core sandwich panel/beam (Al 5052 hexagonal core)",
    principle=(
        "Gibson-Ashby: honeycomb out-of-plane modulus E_c = E_s rho*, transverse shear modulus G_c = 0.5 rho* G_s, "
        "core shear strength ~0.5 rho* tau_ys (or wall buckling E_s (t/l)^3). Allen sandwich beam, 3-point bending: "
        "D = E_f b t d^2/2, S = G_c b d^2/c, delta = P L^3/(48D) + P L/(4S). Failure loads: face yield 4 sigma_f t d b/L, "
        "core shear 2 tau_c b d, face wrinkling sigma = 0.5 (E_f E_c G_c)^(1/3), intracell dimpling "
        "2E_f/(1-nu^2)(t/s)^2. Mass/area = 2 rho_f t + rho* rho_s c."
    ),
    bio_exemplars=["honeybee comb (hexagonal wax cells)", "bird skull/wing bone sandwich (diploe)",
                   "beetle elytra (trabecular sandwich)", "cuttlebone lamellar septa"],
    design_space=[
        Param("face_thickness_m", 1.0e-4, 5.0e-3, "m", "face sheet thickness t (each face)"),
        Param("core_thickness_m", 2.0e-3, 0.15, "m", "honeycomb core thickness c"),
        Param("core_relative_density", 0.003, 0.25, "-", "core density / cell-wall material density"),
        Param("cell_size_m", 1.5e-3, 2.5e-2, "m", "hexagon cell size across flats s"),
    ],
    env_space=[*SANDWICH_ENV, Param("min_foil_thickness_m", 1.0e-5, 5.0e-4, "m", "minimum available core foil gauge")],
    references=SANDWICH_REFS + [
        "Gibson L.J., Ashby M.F. (1997) Cellular Solids: Structure and Properties, 2nd ed., CUP, ch. 4.",
        "Hexcel (2016) HexWeb Honeycomb Sandwich Design Technology, publication AGU 075b (dimpling, Norris).",
    ],
    _screen=_screen,
)
