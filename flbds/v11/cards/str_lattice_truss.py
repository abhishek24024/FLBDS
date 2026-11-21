"""STR_LATTICE_TRUSS: strut-lattice-core sandwich beam (stretch- vs bending-dominated core)."""

from __future__ import annotations

import math

from ._sandwich import SANDWICH_ENV, SANDWICH_REFS, sandwich_checks, thin_face_note
from .base import ConstraintResult, Param, PhysicsCard, ge

# L-PBF AlSi10Mg strut material (core constants).
CORE_E_PA, CORE_RHO, CORE_SY_PA = 70.0e9, 2670.0, 230.0e6
OMEGA = math.radians(45.0)
CONNECTIVITY_STRETCH = 10.0  # Maxwell: Z>=12 rigid 3D truss (pyramidal/octet); Z~8 (BCC) bending-dominated


def core_properties(rho_rel: float, slenderness_r_over_l: float, stretch: bool) -> tuple[float, float, float]:
    """Return (E_c, G_c, tau_c).

    Stretch (pyramidal, Deshpande & Fleck 2001): E33 = E_s rho sin^4 w, G13 = E_s rho sin^2(2w)/8,
    tau = rho sigma_strut sin(2w)/(2 sqrt2), sigma_strut = min(sigma_ys, pi^2 E_s (r/l)^2) (built-in ends).
    Bending (Gibson & Ashby open cell): E = E_s rho^2, G = 3/8 E_s rho^2,
    tau = min(0.2 sigma_ys rho^1.5, 0.05 E_s rho^2) (plastic / elastic collapse).
    """
    if stretch:
        sig = min(CORE_SY_PA, math.pi**2 * CORE_E_PA * slenderness_r_over_l**2)
        return (CORE_E_PA * rho_rel * math.sin(OMEGA) ** 4, CORE_E_PA * rho_rel * math.sin(2 * OMEGA) ** 2 / 8.0,
                rho_rel * sig * math.sin(2 * OMEGA) / (2.0 * math.sqrt(2.0)))
    return (CORE_E_PA * rho_rel**2, 0.375 * CORE_E_PA * rho_rel**2,
            min(0.2 * CORE_SY_PA * rho_rel**1.5, 0.05 * CORE_E_PA * rho_rel**2))


def strut_r_over_l(rho_rel: float, stretch: bool) -> float:
    """Pyramidal: rho = 2 pi (r/l)^2/(cos^2 w sin w); BCC (cell a, strut l = sqrt3 a/2): rho = 4 sqrt3 pi (r/a)^2."""
    if stretch:
        return math.sqrt(rho_rel * math.cos(OMEGA) ** 2 * math.sin(OMEGA) / (2.0 * math.pi))
    r_over_a = math.sqrt(rho_rel / (4.0 * math.sqrt(3.0) * math.pi))
    return r_over_a / (math.sqrt(3.0) / 2.0)


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    t, c, rr, lstrut = d["face_thickness_m"], d["core_thickness_m"], d["core_relative_density"], d["strut_length_m"]
    stretch = d["nodal_connectivity"] >= CONNECTIVITY_STRETCH
    rl = strut_r_over_l(rr, stretch)
    ec, gc, tau = core_properties(rr, rl, stretch)
    cons, der = sandwich_checks(t, c, e, ec, gc, tau, CORE_RHO * rr * c, None)
    dia = 2.0 * rl * lstrut
    cons.append(ge("strut_diameter_m", dia, e["min_strut_diameter_m"], "m"))
    der.update(strut_diameter_m=dia, strut_slenderness_l_over_r=1.0 / rl, stretch_dominated=float(stretch))
    notes = thin_face_note(t, c)
    if rr > 0.3:
        notes.append(f"relative density {rr:.3f} > 0.3: slender-strut scaling invalid")
    layer_h = lstrut * math.sin(OMEGA) if stretch else 2.0 * lstrut / math.sqrt(3.0)
    if c < layer_h:
        notes.append(f"core thickness {c:.4g} m < one unit-cell height {layer_h:.4g} m")
    return cons, notes, der


CARD = PhysicsCard(
    id="STR_LATTICE_TRUSS",
    domain="structures",
    title="Truss-lattice-core sandwich panel (L-PBF AlSi10Mg core; pyramidal or BCC)",
    principle=(
        "Maxwell connectivity: Z>=12 nodes give stretch-dominated trusses (pyramidal/octet: E ~ rho* E_s, "
        "tau ~ rho* sigma_strut) whereas Z~8 (BCC) bend (E ~ rho*^2 E_s, tau ~ 0.2 rho*^1.5 sigma_ys). Strut "
        "Euler buckling sigma = pi^2 E_s (r/l)^2 caps the stretch-dominated strength. Core properties feed Allen "
        "sandwich-beam stiffness (bending + shear deflection), face yield, core shear and face wrinkling checks; "
        "strut diameter >= additive-manufacturing minimum."
    ),
    bio_exemplars=["bird bone trabeculae (graded strut lattice)", "Euplectella glass sponge skeleton",
                   "cuttlebone pillared chambers", "sea urchin stereom"],
    design_space=[
        Param("face_thickness_m", 1.0e-4, 5.0e-3, "m", "face sheet thickness t (each face)"),
        Param("core_thickness_m", 2.0e-3, 0.15, "m", "lattice core thickness c"),
        Param("core_relative_density", 0.01, 0.4, "-", "lattice relative density rho*"),
        Param("strut_length_m", 1.0e-3, 2.0e-2, "m", "strut length l"),
        Param("nodal_connectivity", 8.0, 12.0, "-", "struts per node Z (>=10 -> pyramidal/octet, else BCC)"),
    ],
    env_space=[*SANDWICH_ENV, Param("min_strut_diameter_m", 5.0e-5, 3.0e-3, "m", "minimum printable strut diameter")],
    references=SANDWICH_REFS + [
        "Deshpande V.S., Fleck N.A. (2001) Collapse of truss core sandwich beams in 3-point bending, Int. J. Solids Struct. 38:6275.",
        "Deshpande V.S., Ashby M.F., Fleck N.A. (2001) Foam topology: bending versus stretching dominated architectures, Acta Mater. 49:1035.",
        "Gibson L.J., Ashby M.F. (1997) Cellular Solids, 2nd ed., ch. 5 (open-cell scaling).",
    ],
    _screen=_screen,
)
