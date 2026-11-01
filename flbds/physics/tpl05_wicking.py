"""TPL-05: Capillary Wicking Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5:
- Screen: Jurin capillary rise height >= 1.5 * lift_height; Bond number Bo < 0.1.
- Eval: Washburn / Darcy mass supply rate at lift height covers required evaporation/replenishment flow;
  viscous pressure drop within capillary pressure limit; pore clearance above fouling limit.
"""

from typing import Dict, Tuple, Optional
import numpy as np

from flbds.schema.templates import TPL05Params
from flbds.schema.verification import PhysicsCheck

G_ACCEL = 9.80665  # Gravitational acceleration m/s^2


def compute_jurin_height_m(gamma: float, theta_rad: float, rho: float, r_pore: float) -> float:
    """Computes equilibrium Jurin capillary rise height h = (2 * gamma * cos(theta)) / (rho * g * r_pore)."""
    if rho <= 0 or r_pore <= 0:
        return 0.0
    return float((2.0 * gamma * np.cos(theta_rad)) / (rho * G_ACCEL * r_pore))


def compute_bond_number(rho: float, r_pore: float, gamma: float) -> float:
    """Computes Bond number Bo = (rho * g * r_pore^2) / gamma."""
    if gamma <= 0:
        return float("inf")
    return float((rho * G_ACCEL * (r_pore ** 2)) / gamma)


def screen_tpl05(
    params: TPL05Params,
) -> PhysicsCheck:
    """M5-Screen: Jurin height >= 1.5 * lift_height and Bond number < 0.1."""
    theta_rad = np.radians(params.contact_angle_deg)
    h_jurin = compute_jurin_height_m(params.surface_tension_N_m, theta_rad, params.fluid_density_kg_m3, params.pore_radius_m)
    bo = compute_bond_number(params.fluid_density_kg_m3, params.pore_radius_m, params.surface_tension_N_m)

    if h_jurin < 1.5 * params.lift_height_m:
        return PhysicsCheck(
            template_name="TPL05_M5_Screen",
            passed=False,
            reason=f"Jurin height {h_jurin:.3f} m below 1.5x required lift ({1.5*params.lift_height_m:.3f} m)",
            metrics={"h_jurin_m": h_jurin, "required_lift_m": params.lift_height_m, "Bo": bo},
        )

    if bo >= 0.1:
        return PhysicsCheck(
            template_name="TPL05_M5_Screen",
            passed=False,
            reason=f"Bond number Bo={bo:.4f} >= 0.1 (gravity dominates over capillary force)",
            metrics={"Bo": bo, "h_jurin_m": h_jurin},
        )

    return PhysicsCheck(
        template_name="TPL05_M5_Screen",
        passed=True,
        reason=f"Screen capillary lift verified (h_jurin={h_jurin:.3f} m, Bo={bo:.4e})",
        metrics={"h_jurin_m": h_jurin, "Bo": bo},
    )


def eval_tpl05(
    params: TPL05Params,
    min_pore_diameter_fouling_m: float = 5e-7,  # 500 nm particulate fouling ceiling
    min_pore_diameter_m: Optional[float] = None,
) -> PhysicsCheck:
    """M5-Eval: Coupled Darcy-Washburn fluid replenishment supply rate and fouling clearance."""
    if min_pore_diameter_m is not None:
        min_pore_diameter_fouling_m = min_pore_diameter_m
    # 1. Screen check
    screen_res = screen_tpl05(params)
    if not screen_res.passed:
        return PhysicsCheck(
            template_name="TPL05_M5_Eval",
            passed=False,
            reason=f"Screen check failed: {screen_res.reason}",
            metrics=screen_res.metrics,
        )

    # 2. Pore fouling clearance check
    pore_diam = 2.0 * params.pore_radius_m
    if pore_diam < min_pore_diameter_fouling_m:
        return PhysicsCheck(
            template_name="TPL05_M5_Eval",
            passed=False,
            reason=f"Pore diameter {pore_diam*1e9:.1f} nm below particulate fouling limit {min_pore_diameter_fouling_m*1e9:.1f} nm",
            metrics={"pore_diam_nm": pore_diam * 1e9, "fouling_limit_nm": min_pore_diameter_fouling_m * 1e9},
        )

    # 3. Darcy-Washburn mass flow supply rate against gravity
    # Net driving pressure head: delta_P_cap - delta_P_grav
    theta_rad = np.radians(params.contact_angle_deg)
    delta_p_cap = (2.0 * params.surface_tension_N_m * np.cos(theta_rad)) / params.pore_radius_m
    delta_p_grav = params.fluid_density_kg_m3 * G_ACCEL * params.lift_height_m

    net_driving_pressure = delta_p_cap - delta_p_grav
    if net_driving_pressure <= 0:
        return PhysicsCheck(
            template_name="TPL05_M5_Eval",
            passed=False,
            reason="Gravity head exceeds capillary driving pressure",
            metrics={"delta_p_cap": delta_p_cap, "delta_p_grav": delta_p_grav},
        )

    # Darcy supply velocity u = (K / mu) * (net_driving_pressure / lift_height)
    # Mass flux m_dot'' = rho * u
    u_darcy = (params.permeability_m2 / params.dynamic_viscosity_Pa_s) * (net_driving_pressure / params.lift_height_m)
    mass_flux_supply = params.fluid_density_kg_m3 * u_darcy

    if mass_flux_supply < params.required_mass_flux_kg_m2_s:
        return PhysicsCheck(
            template_name="TPL05_M5_Eval",
            passed=False,
            reason=(
                f"Darcy replenishment flux {mass_flux_supply*1e3:.3f} g/(m2.s) below "
                f"required {params.required_mass_flux_kg_m2_s*1e3:.3f} g/(m2.s) (viscous drag limitation)"
            ),
            metrics={
                "mass_flux_supply": mass_flux_supply,
                "required_flux": params.required_mass_flux_kg_m2_s,
                "delta_p_cap_Pa": delta_p_cap,
            },
        )

    return PhysicsCheck(
        template_name="TPL05_M5_Eval",
        passed=True,
        reason=(
            f"Coupled capillary wicking verified: supply rate {mass_flux_supply*1e3:.2f} g/(m2.s) covers "
            f"demand at {params.lift_height_m*1e3:.1f} mm lift"
        ),
        metrics={
            "mass_flux_supply_kg_m2_s": mass_flux_supply,
            "delta_p_cap_Pa": delta_p_cap,
            "net_pressure_Pa": net_driving_pressure,
        },
    )
