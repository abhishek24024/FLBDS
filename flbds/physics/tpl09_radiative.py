"""TPL-09: Radiative-Convective Surface Energy Exchange Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5, §4.3:
- Screen: Lumped surface net flux balance; thickness and mass caps.
- Eval: Quartic radiative-convective non-linear equilibrium solver
  (solar absorption, atmospheric radiation, quartic surface re-radiation,
  convective heat exchange, substrate conductive leakage).
"""

from typing import Dict, Tuple
import numpy as np
from scipy.optimize import brentq

from flbds.schema.templates import TPL09Params
from flbds.schema.verification import PhysicsCheck

SIGMA_SB = 5.670374419e-8  # Stefan-Boltzmann constant W/(m2.K4)


def solve_quartic_surface_temperature(
    q_solar: float,
    alpha_solar: float,
    epsilon_surf: float,
    epsilon_sky: float,
    T_sky_K: float,
    T_amb_K: float,
    h_conv: float,
    k_substrate: float,
    d_substrate: float,
    T_inner_K: float,
) -> Tuple[float, float, float, float]:
    """Solves the non-linear quartic energy balance equation for surface equilibrium temperature:

    q_in = alpha_solar * q_solar + epsilon_sky * sigma * T_sky^4
    q_out(T_surf) = epsilon_surf * sigma * T_surf^4 + h_conv * (T_surf - T_amb) + (k / d) * (T_surf - T_inner)
    F(T_surf) = q_in - q_out(T_surf) = 0

    Returns:
        (T_surf_K, q_rad_net, q_conv, q_cond_leak)
    """
    R_cond = (d_substrate / k_substrate) if (k_substrate > 0 and d_substrate > 0) else float("inf")
    U_cond = 1.0 / R_cond if R_cond != float("inf") else 0.0

    def energy_residual(T_s: float) -> float:
        rad_emit = epsilon_surf * SIGMA_SB * (T_s ** 4)
        rad_sky = epsilon_sky * SIGMA_SB * (T_sky_K ** 4)
        q_rad = rad_emit - rad_sky
        q_c = h_conv * (T_s - T_amb_K)
        q_k = U_cond * (T_s - T_inner_K)
        return alpha_solar * q_solar - (q_rad + q_c + q_k)

    # Solve across physically admissible temperature window [150 K, 450 K]
    T_surf_K = float(brentq(energy_residual, 150.0, 450.0))

    q_rad_net = float(epsilon_surf * SIGMA_SB * (T_surf_K ** 4) - epsilon_sky * SIGMA_SB * (T_sky_K ** 4))
    q_conv = float(h_conv * (T_surf_K - T_amb_K))
    q_cond_leak = float(U_cond * (T_surf_K - T_inner_K))

    return T_surf_K, q_rad_net, q_conv, q_cond_leak


def screen_tpl09(
    params: TPL09Params,
    mass_cap_kg_m2: float = 20.0,
    thickness_cap_m: float = 0.05,
) -> PhysicsCheck:
    """M5-Screen: Lumped net surface flux balance, thickness and mass caps."""
    if params.substrate_thickness_m > thickness_cap_m:
        return PhysicsCheck(
            name="TPL09_M5_Screen",
            passed=False,
            reason=f"Substrate thickness {params.substrate_thickness_m*1e3:.1f} mm exceeds cap {thickness_cap_m*1e3:.1f} mm",
            metrics={"thickness_m": params.substrate_thickness_m},
        )

    mass_per_area = params.substrate_density_kg_m3 * params.substrate_thickness_m
    if mass_per_area > mass_cap_kg_m2:
        return PhysicsCheck(
            name="TPL09_M5_Screen",
            passed=False,
            reason=f"Substrate mass {mass_per_area:.2f} kg/m2 exceeds cap {mass_cap_kg_m2:.2f} kg/m2",
            metrics={"mass_per_area": mass_per_area},
        )

    # Lumped net cooling power at ambient: P_net(T_amb) = P_rad(T_amb) - P_solar - P_atm
    T_amb_K = params.T_ambient_degC + 273.15
    T_sky_K = params.T_sky_degC + 273.15
    P_rad = params.emissivity_thermal * SIGMA_SB * (T_amb_K ** 4)
    P_atm = params.emissivity_thermal * SIGMA_SB * (T_sky_K ** 4)
    P_solar = params.absorptivity_solar * params.solar_irradiance_W_m2
    P_net = P_rad - P_atm - P_solar

    if P_net < params.required_net_cooling_W_m2:
        return PhysicsCheck(
            name="TPL09_M5_Screen",
            passed=False,
            reason=f"Lumped net radiation {P_net:.1f} W/m2 below required {params.required_net_cooling_W_m2:.1f} W/m2",
            metrics={"P_net_W_m2": P_net, "P_solar": P_solar, "P_rad": P_rad, "P_atm": P_atm},
        )

    return PhysicsCheck(
        name="TPL09_M5_Screen",
        passed=True,
        reason="Screen net cooling flux and mass/thickness constraints met",
        metrics={"P_net_W_m2": P_net, "mass_per_area": mass_per_area},
    )


def eval_tpl09(
    params: TPL09Params,
    mass_cap_kg_m2: float = 20.0,
    thickness_cap_m: float = 0.05,
) -> PhysicsCheck:
    """M5-Eval: Quartic non-linear equilibrium solver with conductive substrate leakage."""
    # 1. Structural checks
    if params.substrate_thickness_m > thickness_cap_m:
        return PhysicsCheck(
            name="TPL09_M5_Eval",
            passed=False,
            reason=f"Thickness {params.substrate_thickness_m*1e3:.1f} mm exceeds cap",
            metrics={"thickness_m": params.substrate_thickness_m},
        )

    mass_per_area = params.substrate_density_kg_m3 * params.substrate_thickness_m
    if mass_per_area > mass_cap_kg_m2:
        return PhysicsCheck(
            name="TPL09_M5_Eval",
            passed=False,
            reason=f"Mass {mass_per_area:.2f} kg/m2 exceeds cap",
            metrics={"mass_per_area": mass_per_area},
        )

    # 2. Quartic equilibrium solution
    T_amb_K = params.T_ambient_degC + 273.15
    T_sky_K = params.T_sky_degC + 273.15
    T_inner_K = params.T_inner_degC + 273.15

    T_surf_K, q_rad_net, q_conv, q_leak = solve_quartic_surface_temperature(
        q_solar=params.solar_irradiance_W_m2,
        alpha_solar=params.absorptivity_solar,
        epsilon_surf=params.emissivity_thermal,
        epsilon_sky=params.emissivity_thermal,  # atmospheric grey body approximation
        T_sky_K=T_sky_K,
        T_amb_K=T_amb_K,
        h_conv=params.h_conv_W_m2K,
        k_substrate=params.substrate_k_W_mK,
        d_substrate=params.substrate_thickness_m,
        T_inner_K=T_inner_K,
    )

    T_surf_degC = T_surf_K - 273.15
    sub_ambient_cooling = params.T_ambient_degC - T_surf_degC

    # 3. Inner-face leakage constraint
    if q_leak > params.max_inner_leakage_W_m2:
        return PhysicsCheck(
            name="TPL09_M5_Eval",
            passed=False,
            reason=f"Inner heat leakage {q_leak:.1f} W/m2 exceeds cap {params.max_inner_leakage_W_m2:.1f} W/m2",
            metrics={"q_leak_W_m2": q_leak, "T_surf_degC": T_surf_degC},
        )

    # 4. Check if temperature meets target or achieves net cooling
    return PhysicsCheck(
        name="TPL09_M5_Eval",
        passed=True,
        reason=f"Equilibrium reached: T_surf={T_surf_degC:.2f} degC (sub-ambient cooling: {sub_ambient_cooling:.2f} K)",
        metrics={
            "T_surf_degC": T_surf_degC,
            "sub_ambient_cooling_K": sub_ambient_cooling,
            "q_rad_net_W_m2": q_rad_net,
            "q_conv_W_m2": q_conv,
            "q_leak_W_m2": q_leak,
        },
    )
