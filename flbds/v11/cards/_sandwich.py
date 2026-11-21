"""Allen (1969) thin-face sandwich beam: 3-point bending, simply supported, central load P."""

from __future__ import annotations

from .base import ConstraintResult, Param, ge, le

SANDWICH_ENV: list[Param] = [
    Param("span_m", 0.05, 5.0, "m", "simply supported span L"),
    Param("width_m", 0.01, 2.0, "m", "beam/panel width b"),
    Param("design_load_N", 1.0, 1.0e5, "N", "central design load incl. safety factor"),
    Param("stiffness_min_N_m", 1.0e2, 1.0e8, "N/m", "required central bending stiffness P/delta"),
    Param("areal_mass_cap_kg_m2", 0.2, 50.0, "kg/m2", "maximum mass per unit panel area"),
    Param("thickness_cap_m", 0.003, 0.2, "m", "maximum total thickness 2t + c"),
    Param("face_modulus_Pa", 1.0e9, 2.5e11, "Pa", "face sheet Young's modulus (specified material)"),
    Param("face_strength_Pa", 5.0e7, 2.0e9, "Pa", "face sheet yield/failure strength"),
    Param("face_density_kg_m3", 1000.0, 8000.0, "kg/m3", "face sheet density"),
]


def sandwich_checks(
    t: float, c: float, e: dict[str, float], ec: float, gc: float, tau_c: float, core_areal_kg_m2: float,
    dimple_stress_Pa: float | None,
) -> tuple[list[ConstraintResult], dict[str, float]]:
    """Return constraints for stiffness, mass, thickness and failure modes (all closed form)."""
    L, b, P = e["span_m"], e["width_m"], e["design_load_N"]
    ef, sf = e["face_modulus_Pa"], e["face_strength_Pa"]
    dd = c + t
    D = ef * b * t * dd**2 / 2.0  # Allen eq. thin faces (faces' own bending neglected)
    S = gc * b * dd**2 / c  # transverse shear stiffness
    delta = P * L**3 / (48.0 * D) + P * L / (4.0 * S)
    k = P / delta
    mass = 2.0 * e["face_density_kg_m3"] * t + core_areal_kg_m2
    p_face = 4.0 * sf * t * dd * b / L  # face yield: sigma_f = M/(t d b), M = PL/4
    p_core = 2.0 * tau_c * b * dd  # core shear: tau = (P/2)/(b d)
    s_wr = 0.5 * (ef * ec * gc) ** (1.0 / 3.0)  # Hoff-Mautner wrinkling
    p_wr = 4.0 * s_wr * t * dd * b / L
    cons = [
        ge("bending_stiffness_N_m", k, e["stiffness_min_N_m"], "N/m"),
        le("areal_mass_kg_m2", mass, e["areal_mass_cap_kg_m2"], "kg/m2"),
        le("total_thickness_m", 2 * t + c, e["thickness_cap_m"], "m"),
        ge("face_yield_load_N", p_face, P, "N"),
        ge("core_shear_load_N", p_core, P, "N"),
        ge("face_wrinkling_load_N", p_wr, P, "N"),
    ]
    derived = {"flexural_rigidity_N_m2": D, "shear_stiffness_N": S, "deflection_m": delta, "stiffness_N_m": k,
               "areal_mass_kg_m2": mass, "core_modulus_Pa": ec, "core_shear_modulus_Pa": gc,
               "core_shear_strength_Pa": tau_c, "wrinkling_stress_Pa": s_wr,
               "shear_deflection_fraction": (P * L / (4.0 * S)) / delta}
    if dimple_stress_Pa is not None:
        cons.append(ge("intracell_dimpling_load_N", 4.0 * dimple_stress_Pa * t * dd * b / L, P, "N"))
        derived["dimpling_stress_Pa"] = dimple_stress_Pa
    return cons, derived


def thin_face_note(t: float, c: float) -> list[str]:
    ratio = (c + t) / t
    return [] if ratio >= 5.77 else [f"d/t = {ratio:.2f} < 5.77: thin-face (Allen) assumption invalid"]


SANDWICH_REFS = [
    "Allen H.G. (1969) Analysis and Design of Structural Sandwich Panels, Pergamon (D = E_f b t d^2/2, S = G_c b d^2/c).",
    "Zenkert D. (1995) An Introduction to Sandwich Construction, EMAS (failure modes, wrinkling 0.5(E_f E_c G_c)^(1/3)).",
    "Hoff N.J., Mautner S.E. (1945) The buckling of sandwich-type panels, J. Aeronaut. Sci. 12:285.",
]
