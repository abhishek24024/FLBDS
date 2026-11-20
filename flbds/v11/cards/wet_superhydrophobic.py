"""WET_SUPERHYDROPHOBIC: square micropillar texture in the Cassie-Baxter state."""

from __future__ import annotations

import math

from .base import ConstraintResult, Param, PhysicsCard, ge

GAMMA_W, RHO_W = 0.072, 1000.0


def apparent_angles(phi_s: float, r: float, theta_y_deg: float) -> tuple[float, float]:
    """Cassie-Baxter cos t* = phi_s (cos t + 1) - 1; Wenzel cos t_W = r cos t (clipped)."""
    c = math.cos(math.radians(theta_y_deg))
    cb = math.degrees(math.acos(max(-1.0, min(1.0, phi_s * (c + 1.0) - 1.0))))
    wz = math.degrees(math.acos(max(-1.0, min(1.0, r * c))))
    return cb, wz


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    a, p, h, th = d["pillar_width_m"], d["pillar_pitch_m"], d["pillar_height_m"], d["intrinsic_contact_angle_deg"]
    notes: list[str] = []
    if a >= p:
        notes.append("pillar width >= pitch: no texture gaps")
        a = 0.999 * p
    phi_s = (a / p) ** 2
    r = 1.0 + 4.0 * a * h / p**2
    cb, wz = apparent_angles(phi_s, r, th)
    cos_t = math.cos(math.radians(th))
    p_break = -GAMMA_W * cos_t * 4.0 * a / (p**2 - a**2)  # Zheng et al. 2005 / Extrand 2004 (depinning)
    v = e["droplet_impact_speed_m_s"]
    p_dyn = 0.5 * RHO_W * v**2 + RHO_W * 9.81 * e["hydrostatic_head_m"]
    gap_diag = math.sqrt(2.0) * p - a
    sag = gap_diag**2 * p_dyn / (8.0 * GAMMA_W)  # meniscus sag (parabolic) at applied pressure
    cons = [
        ge("cassie_apparent_angle_deg", cb, e["target_apparent_angle_deg"], "deg"),
        ge("breakthrough_pressure_Pa", p_break, p_dyn, "Pa"),
        ge("pillar_height_vs_sag_m", h, sag, "m"),
        ge("pillar_width_min_feature_m", a, e["min_feature_m"], "m"),
        ge("solid_fraction_durability", phi_s, e["min_solid_fraction"], "-"),
    ]
    dd = e["droplet_diameter_m"]
    if dd < 10.0 * p:
        notes.append(f"droplet/pitch = {dd / p:.1f} < 10: Cassie-Baxter area averaging invalid")
    if th <= 90.0:
        notes.append(f"intrinsic angle {th:.0f} deg <= 90: no hydrophobic Laplace barrier (Cassie unsupported)")
    cos_c = (phi_s - 1.0) / (r - phi_s)
    we = RHO_W * v**2 * dd / GAMMA_W
    return cons, notes, {"solid_fraction": phi_s, "roughness_ratio": r, "wenzel_angle_deg": wz,
                         "impact_pressure_Pa": p_dyn, "sag_depth_m": sag, "weber_number": we,
                         "cassie_thermodynamically_stable": float(cos_t < cos_c)}


CARD = PhysicsCard(
    id="WET_SUPERHYDROPHOBIC",
    domain="wetting",
    title="Superhydrophobic micropillar texture (Cassie-Baxter, impalement-robust)",
    principle=(
        "Square pillars width a, pitch p, height h on a hydrophobic coating (Young angle theta): solid fraction "
        "phi = (a/p)^2, Cassie-Baxter cos theta* = phi(cos theta + 1) - 1, Wenzel cos theta_W = r cos theta, "
        "r = 1 + 4ah/p^2. Cassie robustness: depinning breakthrough pressure -gamma cos theta * 4a/(p^2 - a^2) and "
        "meniscus sag (sqrt2 p - a)^2 P/(8 gamma) <= h must resist the impact pressure 0.5 rho V^2 (+ rho g H)."
    ),
    bio_exemplars=["lotus leaf (Nelumbo nucifera) papillae", "springtail (Collembola) cuticle", "water strider legs",
                   "Salvinia leaf hairs", "rice leaf"],
    design_space=[
        Param("pillar_width_m", 1.0e-7, 1.0e-4, "m", "pillar side length a"),
        Param("pillar_pitch_m", 2.0e-7, 5.0e-4, "m", "pillar centre-to-centre pitch p"),
        Param("pillar_height_m", 1.0e-7, 2.0e-4, "m", "pillar height h"),
        Param("intrinsic_contact_angle_deg", 70.0, 125.0, "deg", "Young angle of the coating (fluoropolymer max ~120)"),
    ],
    env_space=[
        Param("target_apparent_angle_deg", 120.0, 175.0, "deg", "required apparent contact angle"),
        Param("droplet_impact_speed_m_s", 0.0, 10.0, "m/s", "droplet impact speed (rain terminal ~ 3-9 m/s)"),
        Param("droplet_diameter_m", 1.0e-4, 6.0e-3, "m", "typical droplet diameter"),
        Param("hydrostatic_head_m", 0.0, 10.0, "m", "static water head on the surface (0 if exposed to air)"),
        Param("min_feature_m", 5.0e-8, 5.0e-5, "m", "minimum manufacturable pillar width"),
        Param("min_solid_fraction", 0.0, 0.5, "-", "minimum solid fraction for abrasion durability"),
    ],
    references=[
        "Cassie A.B.D., Baxter S. (1944) Wettability of porous surfaces, Trans. Faraday Soc. 40:546.",
        "Wenzel R.N. (1936) Resistance of solid surfaces to wetting by water, Ind. Eng. Chem. 28:988.",
        "Bico J., Thiele U., Quere D. (2002) Wetting of textured surfaces, Colloids Surf. A 206:41.",
        "Zheng Q.-S., Yu Y., Zhao Z.-H. (2005) Effects of hydraulic pressure on the stability and transition of wetting modes of superhydrophobic surfaces, Langmuir 21:12207.",
        "Bartolo D. et al. (2006) Bouncing or sticky droplets: impalement transitions on superhydrophobic micropatterned surfaces, Europhys. Lett. 74:299.",
        "Barthlott W., Neinhuis C. (1997) Purity of the sacred lotus, Planta 202:1.",
    ],
    _screen=_screen,
)
