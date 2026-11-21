"""MT_FOG_HARVEST_MESH: woven fog-collection mesh (Rivera 2011; Park et al. 2013)."""

from __future__ import annotations

import math

from .base import ConstraintResult, Param, PhysicsCard, ge, le

RHO_W, RHO_AIR, MU_AIR = 1000.0, 1.2, 1.8e-5
C0 = 1.18  # Rivera (2011) open-flow pressure coefficient
SC_WINDOW = (0.1, 0.9)
CLOG_OPENING_FACTOR = 20.0  # opening must exceed ~20 droplet diameters (coarse proxy for Park 2013 clogging)


def mesh_drag_coefficient(sc: float) -> float:
    """Woven-screen pressure-drop coefficient C_D = 1.3 SC + (SC/(1-SC))^2 (Idelchik; used by Park 2013)."""
    return 1.3 * sc + (sc / (1.0 - sc)) ** 2


def efficiencies(
    sc: float, r_fibre: float, d_drop: float, u: float
) -> tuple[float, float, float]:
    """Return (eta_aerodynamic, eta_deposition, Stokes number)."""
    cd = mesh_drag_coefficient(sc)
    eta_a = sc / (1.0 + math.sqrt(C0 / cd))
    st = RHO_W * d_drop**2 * u / (9.0 * MU_AIR * 2.0 * r_fibre)
    eta_d = st / (st + math.pi / 2.0)  # Langmuir-Blodgett impaction fit (Park 2013)
    return eta_a, eta_d, st


def _screen(
    d: dict[str, float], e: dict[str, float]
) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    rf, sc, area = d["fibre_radius_m"], d["shade_coefficient"], d["mesh_area_m2"]
    u = e["wind_speed_m_s"]
    eta_a, eta_d, st = efficiencies(sc, rf, e["droplet_diameter_m"], u)
    eta = eta_a * eta_d * e["drainage_efficiency"]
    yield_l_day = (
        eta
        * e["liquid_water_content_kg_m3"]
        * u
        * area
        * e["fog_hours_per_day"]
        * 3600.0
    )  # 1 kg = 1 L
    load = (
        0.5
        * RHO_AIR
        * mesh_drag_coefficient(sc)
        * e["design_wind_speed_m_s"] ** 2
        * area
    )
    opening = (
        2.0 * rf * (1.0 / math.sqrt(1.0 - sc) - 1.0)
    )  # square weave: 1-SC = (w/(w+2R))^2
    cons = [
        ge("water_yield_L_day", yield_l_day, e["target_yield_L_day"], "L/day"),
        le("mesh_area_m2", area, e["max_mesh_area_m2"], "m2"),
        le("design_wind_load_N", load, e["max_wind_load_N"], "N"),
        ge("fibre_radius_min_feature_m", rf, e["min_feature_m"], "m"),
    ]
    notes: list[str] = []
    if not (SC_WINDOW[0] <= sc <= SC_WINDOW[1]):
        notes.append(
            f"shade coefficient {sc:.2f} outside Rivera correlation window {SC_WINDOW}"
        )
    if opening < CLOG_OPENING_FACTOR * e["droplet_diameter_m"]:
        notes.append(
            f"mesh opening {opening * 1e6:.0f} um too small: clogging regime (Park et al. 2013)"
        )
    re_f = RHO_AIR * u * 2.0 * rf / MU_AIR
    return (
        cons,
        notes,
        {
            "eta_aerodynamic": eta_a,
            "eta_deposition": eta_d,
            "eta_total": eta,
            "stokes_number": st,
            "fibre_reynolds": re_f,
            "mesh_opening_m": opening,
            "yield_L_m2_day": yield_l_day / area,
            "design_wind_load_N": load,
        },
    )


CARD = PhysicsCard(
    id="MT_FOG_HARVEST_MESH",
    domain="mass_transfer",
    title="Fog-collection mesh (aerodynamic x deposition x drainage efficiency)",
    principle=(
        "Collection efficiency eta = eta_a * eta_d * eta_drain. Aerodynamic (Rivera 2011): "
        "eta_a = SC/(1 + sqrt(C0/C_D)), C_D = 1.3 SC + (SC/(1-SC))^2, C0 = 1.18. Deposition by inertial impaction "
        "on fibres: eta_d = St/(St + pi/2), St = rho_w d^2 U/(9 mu D_f). Yield = eta LWC U A t_fog >= target; "
        "storm wind load 0.5 rho C_D U_design^2 A <= frame capacity."
    ),
    bio_exemplars=[
        "Namib desert beetle (Onymacris unguicularis / Stenocara) elytra",
        "cactus spines (Opuntia microdasys)",
        "spider silk spindle knots (Uloborus walckenaerius)",
        "Namib dune grass (Stipagrostis sabulicola)",
    ],
    design_space=[
        Param("fibre_radius_m", 2.0e-5, 2.0e-3, "m", "mesh fibre radius R"),
        Param(
            "shade_coefficient",
            0.05,
            0.95,
            "-",
            "fraction of mesh area that is solid (SC)",
        ),
        Param("mesh_area_m2", 0.1, 200.0, "m2", "frontal collector area A"),
    ],
    env_space=[
        Param("wind_speed_m_s", 0.5, 15.0, "m/s", "mean fog-event wind speed U"),
        Param(
            "liquid_water_content_kg_m3",
            1.0e-5,
            1.0e-3,
            "kg/m3",
            "fog liquid water content LWC",
        ),
        Param("droplet_diameter_m", 3.0e-6, 4.0e-5, "m", "fog droplet diameter"),
        Param("fog_hours_per_day", 0.5, 24.0, "h", "mean fog duration per day"),
        Param(
            "drainage_efficiency",
            0.3,
            1.0,
            "-",
            "fraction of captured water drained (coating dependent)",
        ),
        Param("target_yield_L_day", 0.1, 5000.0, "L/day", "required daily water yield"),
        Param("max_mesh_area_m2", 0.1, 500.0, "m2", "maximum collector area"),
        Param(
            "design_wind_speed_m_s",
            5.0,
            50.0,
            "m/s",
            "structural design (storm) wind speed",
        ),
        Param("max_wind_load_N", 10.0, 1.0e6, "N", "frame/anchor load capacity"),
        Param("min_feature_m", 1.0e-5, 1.0e-3, "m", "minimum available fibre radius"),
    ],
    references=[
        "Rivera J. de D. (2011) Aerodynamic collection efficiency of fog water collectors, Atmos. Res. 102:335.",
        ("Park K.-C., Chhatre S.S., Srinivasan S., Cohen R.E., McKinley G.H. (2013) Optimal design of permeable "
        "fiber network structures for fog harvesting, Langmuir 29:13269."),
        "Langmuir I., Blodgett K.B. (1946) A mathematical investigation of water droplet trajectories, GE RL-225.",
        ("Schemenauer R.S., Cereceda P. (1994) A proposed standard fog collector for use in high-elevation "
        "regions, J. Appl. Meteorol. 33:1313."),
        "Parker A.R., Lawrence C.R. (2001) Water capture by a desert beetle, Nature 414:33.",
    ],
    _screen=_screen,
)
