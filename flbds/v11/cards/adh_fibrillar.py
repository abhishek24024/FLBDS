"""ADH_FIBRILLAR: gecko-inspired fibrillar dry adhesive (contact splitting + JKR)."""

from __future__ import annotations

import math

from .base import ConstraintResult, Param, PhysicsCard, ge, le

INTERACTION_RANGE_M = 4.0e-10  # van der Waals range b for theoretical strength W/b
TILT = math.radians(45.0)
DAHLQUIST_PA = 1.0e5
AR_WINDOW = (1.0, 30.0)


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    a, L, phi, E = d["fibril_radius_m"], d["fibril_length_m"], d["packing_fraction"], d["fibril_modulus_Pa"]
    W = e["work_of_adhesion_J_m2"]
    f_jkr = 1.5 * math.pi * W * a  # JKR pull-off, hemispherical tip R = a
    sigma_split = phi * f_jkr / (math.pi * a**2)  # n = phi/(pi a^2) fibrils per area (Arzt 2003)
    sigma_th = phi * W / INTERACTION_RANGE_M  # flaw-tolerant upper bound (Gao & Yao 2004)
    sigma = min(sigma_split, sigma_th)
    pitch = a * math.sqrt(math.pi / phi)  # square packing
    gap = pitch - 2.0 * a
    # Lateral collapse (energy balance after Hui et al. 2002 / Glassmaker et al. 2004): bending two cantilevers
    # by gap/2 each costs 3 E I (g/2)^2 / L^3 * 2; side adhesion gains ~ W a L/2.  Stable if L <= L_c.
    l_crit = (3.0 * math.pi * E * a**3 * max(gap, 0.0) ** 2 / (4.0 * W)) ** 0.25
    # Effective array modulus of 45-deg tilted cantilevers (Autumn et al. 2006): E_eff = 3/4 phi E (a/L)^2 sin/cos^2
    e_eff = 0.75 * phi * E * (a / L) ** 2 * math.sin(TILT) / math.cos(TILT) ** 2
    rough = e["surface_roughness_amplitude_m"]
    p_pre = e_eff * rough / (L * math.sin(TILT))  # preload to conform over roughness amplitude
    p_cr = math.pi**2 * E * (math.pi * a**4 / 4.0) / (4.0 * L**2)  # Euler fixed-free
    p_buckle = phi * p_cr / (math.pi * a**2)
    cons = [
        ge("adhesion_pressure_Pa", sigma, e["required_adhesion_pressure_Pa"], "Pa"),
        le("fibril_length_vs_lateral_collapse_m", L, l_crit, "m"),
        le("preload_pressure_Pa", p_pre, e["max_preload_pressure_Pa"], "Pa"),
        le("preload_vs_buckling_pressure_Pa", p_pre, p_buckle, "Pa"),
        le("effective_array_modulus_Pa", e_eff, DAHLQUIST_PA, "Pa"),
        ge("fibril_diameter_min_feature_m", 2.0 * a, e["min_feature_m"], "m"),
        ge("fibril_length_vs_roughness_m", L * math.sin(TILT), 2.0 * rough, "m"),
    ]
    notes: list[str] = []
    ar = L / a
    if not (AR_WINDOW[0] <= ar <= AR_WINDOW[1]):
        notes.append(f"aspect ratio L/a = {ar:.1f} outside model window {AR_WINDOW}")
    if gap <= 0.0:
        notes.append("packing fraction too high: fibrils overlap (square packing limit pi/4)")
    return cons, notes, {"pull_off_per_fibril_N": f_jkr, "contact_splitting_pressure_Pa": sigma_split,
                         "theoretical_strength_cap_Pa": sigma_th, "fibril_pitch_m": pitch, "aspect_ratio": ar,
                         "lateral_collapse_length_m": l_crit, "effective_modulus_Pa": e_eff,
                         "preload_pressure_Pa": p_pre, "buckling_pressure_Pa": p_buckle}


CARD = PhysicsCard(
    id="ADH_FIBRILLAR",
    domain="adhesion",
    title="Fibrillar (gecko-type) dry adhesive pad",
    principle=(
        "Contact splitting: n = phi/(pi a^2) fibrils each with JKR pull-off F = 1.5 pi W a give adhesion pressure "
        "sigma = 1.5 phi W / a (rises as fibrils shrink), capped by theoretical strength phi W/b. Limits: lateral "
        "collapse of neighbouring fibrils (bending energy vs side adhesion, L <= (3 pi E a^3 g^2/4W)^(1/4)); "
        "Euler buckling under preload; array effective modulus E_eff = 0.75 phi E (a/L)^2 sin/cos^2 <= Dahlquist "
        "100 kPa for tack; preload E_eff*roughness/(L sin) <= allowable."
    ),
    bio_exemplars=["gecko setae and spatulae (Gekko gecko)", "beetle tarsal hairy pads (Chrysomelidae)",
                   "fly pulvilli setae", "jumping spider scopulae"],
    design_space=[
        Param("fibril_radius_m", 5.0e-8, 5.0e-5, "m", "fibril (and hemispherical tip) radius a"),
        Param("fibril_length_m", 1.0e-6, 2.0e-3, "m", "fibril length L"),
        Param("packing_fraction", 0.05, 0.7, "-", "areal fraction of fibril cross-sections phi"),
        Param("fibril_modulus_Pa", 1.0e6, 4.0e9, "Pa", "fibril material Young's modulus (PDMS ~2 MPa .. polyimide ~3 GPa)"),
    ],
    env_space=[
        Param("required_adhesion_pressure_Pa", 1.0e2, 5.0e5, "Pa", "required normal adhesion stress incl. safety"),
        Param("work_of_adhesion_J_m2", 0.005, 0.2, "J/m2", "work of adhesion fibril/substrate pair"),
        Param("max_preload_pressure_Pa", 10.0, 1.0e5, "Pa", "maximum allowable engagement preload"),
        Param("surface_roughness_amplitude_m", 1.0e-8, 1.0e-4, "m", "substrate roughness amplitude to conform to"),
        Param("min_feature_m", 1.0e-8, 1.0e-4, "m", "minimum manufacturable fibril diameter"),
    ],
    references=[
        "Arzt E., Gorb S., Spolenak R. (2003) From micro to nano contacts in biological attachment devices, PNAS 100:10603.",
        "Johnson K.L., Kendall K., Roberts A.D. (1971) Surface energy and the contact of elastic solids, Proc. R. Soc. A 324:301.",
        "Hui C.Y., Jagota A., Lin Y.Y., Kramer E.J. (2002) Constraints on microcontact printing imposed by stamp deformation, Langmuir 18:1394.",
        "Glassmaker N.J., Jagota A., Hui C.Y., Kim J. (2004) Design of biomimetic fibrillar interfaces: 1, J. R. Soc. Interface 1:23.",
        "Autumn K., Majidi C., Groff R.E., Dittmore A., Fearing R. (2006) Effective elastic modulus of isolated gecko setal arrays, J. Exp. Biol. 209:3558.",
        "Gao H., Yao H. (2004) Shape insensitive optimal adhesion of nanoscale fibrillar structures, PNAS 101:7851.",
    ],
    _screen=_screen,
)
