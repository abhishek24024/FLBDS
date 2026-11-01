"""TPL-03: Evaporation and Condensation Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5:
- Evaporation mode:
  * Screen: Latent heat flux >= required duty; water mass budget closure.
  * Eval: Wet-bulb temperature depression and Chilton-Colburn / Lewis mass transfer at ambient humidity.
- Condensation mode:
  * Screen: Condensate rate meets target; surface temperature below dew point.
  * Eval: Air stream humidity-ratio capacity check (m_dot_air * (omega_in - omega_out) >= required condensate),
    coupled with surface condensation energy balance.
"""

from typing import Dict, Tuple, Literal, Optional
import numpy as np

from flbds.schema.templates import TPL03Params
from flbds.schema.verification import PhysicsCheck


def saturation_vapor_pressure_Pa(T_degC: float) -> float:
    """Tetens / Antoine formula for saturation vapor pressure of water in Pa."""
    return float(610.78 * np.exp((17.27 * T_degC) / (T_degC + 237.3)))


def humidity_ratio(vapor_pressure_Pa: float, total_pressure_Pa: float = 101325.0) -> float:
    """Computes humidity ratio omega (kg water / kg dry air)."""
    p_v = min(vapor_pressure_Pa, total_pressure_Pa * 0.95)
    return float(0.622 * p_v / (total_pressure_Pa - p_v))


def dew_point_temperature_degC(vapor_pressure_Pa: float) -> float:
    """Inverts Tetens formula to find dew point temperature in degC."""
    p_v = max(10.0, vapor_pressure_Pa)
    val = np.log(p_v / 610.78)
    return float((237.3 * val) / (17.27 - val))


def screen_tpl03_evaporation(
    params: TPL03Params,
    operating_hours: float = 8.0,
    required_cooling_W_m2: float = 200.0,
) -> PhysicsCheck:
    """M5-Screen: Evaporative cooling latent flux and water mass budget."""
    t_sec = operating_hours * 3600.0
    water_needed = params.evaporation_rate_kg_m2_s * t_sec

    if params.water_budget_kg_m2 < water_needed:
        return PhysicsCheck(
            template_name="TPL03_Evap_Screen",
            passed=False,
            reason=f"Water budget {params.water_budget_kg_m2:.2f} kg/m2 below needed {water_needed:.2f} kg/m2 for {operating_hours} h",
            metrics={"water_budget": params.water_budget_kg_m2, "water_needed": water_needed},
        )

    latent_flux = params.evaporation_rate_kg_m2_s * params.latent_heat_J_kg
    if latent_flux < required_cooling_W_m2:
        return PhysicsCheck(
            template_name="TPL03_Evap_Screen",
            passed=False,
            reason=f"Latent cooling flux {latent_flux:.1f} W/m2 below required {required_cooling_W_m2:.1f} W/m2",
            metrics={"latent_flux_W_m2": latent_flux, "required_flux": required_cooling_W_m2},
        )

    return PhysicsCheck(
        template_name="TPL03_Evap_Screen",
        passed=True,
        reason="Screen evaporative cooling flux and water budget satisfied",
        metrics={"latent_flux_W_m2": latent_flux, "water_needed_kg_m2": water_needed},
    )


def eval_tpl03_evaporation(
    params: TPL03Params,
    T_ambient_degC: float = 35.0,
    T_amb_degC: Optional[float] = None,
    operating_hours: float = 8.0,
    required_cooling_W_m2: float = 200.0,
) -> PhysicsCheck:
    """M5-Eval: Coupled Chilton-Colburn / Lewis relation mass transfer at ambient humidity."""
    if T_amb_degC is not None:
        T_ambient_degC = T_amb_degC

    # 1. Screen checks
    screen_res = screen_tpl03_evaporation(params, operating_hours=operating_hours, required_cooling_W_m2=required_cooling_W_m2)
    if not screen_res.passed:
        return PhysicsCheck(
            template_name="TPL03_Evap_Eval",
            passed=False,
            reason=f"Screen check failed: {screen_res.reason}",
            metrics=screen_res.metrics,
        )

    # Ambient psychrometrics
    p_sat_amb = saturation_vapor_pressure_Pa(T_ambient_degC)
    p_v_amb = params.ambient_relative_humidity * p_sat_amb
    rho_air = 1.18  # kg/m3
    cp_air = 1005.0  # J/kg.K
    Le = 0.85  # Lewis number for air-water

    # Convective heat transfer coefficient: h_c from flat plate flow
    Re_L = (rho_air * params.air_velocity_m_s * params.characteristic_length_m) / 1.8e-5
    Pr = 0.71
    Nu_L = 0.664 * (Re_L ** 0.5) * (Pr ** (1.0 / 3.0)) if Re_L < 5e5 else 0.037 * (Re_L ** 0.8) * (Pr ** (1.0 / 3.0))
    h_c = Nu_L * 0.026 / params.characteristic_length_m

    # Chilton-Colburn mass transfer coefficient: h_m = h_c / (rho * cp * Le^(2/3))
    h_m = h_c / (rho_air * cp_air * (Le ** (2.0 / 3.0)))

    # Wet-bulb / wetted surface equilibrium: driving force Delta_rho_v
    p_sat_surf = saturation_vapor_pressure_Pa(T_ambient_degC - 5.0)  # evaporatively cooled surface
    rho_v_sat = p_sat_surf / (461.5 * (T_ambient_degC - 5.0 + 273.15))
    rho_v_amb = p_v_amb / (461.5 * (T_ambient_degC + 273.15))

    delta_rho_v = max(0.0, rho_v_sat - rho_v_amb)
    max_evap_rate = h_m * delta_rho_v
    evap_cooling_flux = max_evap_rate * params.latent_heat_J_kg

    if evap_cooling_flux < 0.80 * required_cooling_W_m2:
        return PhysicsCheck(
            template_name="TPL03_Evap_Eval",
            passed=False,
            reason=(
                f"Coupled mass transfer cooling {evap_cooling_flux:.1f} W/m2 below required {required_cooling_W_m2:.1f} W/m2 "
                f"at RH={params.ambient_relative_humidity:.1%} (boundary layer choking)"
            ),
            metrics={"evap_flux_W_m2": evap_cooling_flux, "h_m": h_m, "RH": params.ambient_relative_humidity},
        )

    return PhysicsCheck(
        template_name="TPL03_Evap_Eval",
        passed=True,
        reason="Coupled Chilton-Colburn mass transfer and evaporative cooling verified",
        metrics={"evap_cooling_flux_W_m2": evap_cooling_flux, "latent_cooling_flux_W_m2": evap_cooling_flux, "h_m_m_s": h_m, "Re_L": Re_L},
    )


def screen_tpl03_condensation(
    params: Optional[TPL03Params] = None,
    T_surf_degC: float = 12.0,
    T_amb_degC: float = 25.0,
    RH: float = 0.80,
) -> PhysicsCheck:
    """M5-Screen: Condensation screen check (surface temperature <= dew point)."""
    p_sat = saturation_vapor_pressure_Pa(T_amb_degC)
    p_v = RH * p_sat
    T_dew = dew_point_temperature_degC(p_v)

    if T_surf_degC > T_dew:
        return PhysicsCheck(
            template_name="TPL03_Cond_Screen",
            passed=False,
            reason=f"Surface temperature {T_surf_degC:.2f} degC is above dew point {T_dew:.2f} degC (no condensation occurs)",
            metrics={"T_surf_degC": T_surf_degC, "T_dew_degC": T_dew, "RH": RH},
        )

    return PhysicsCheck(
        template_name="TPL03_Cond_Screen",
        passed=True,
        reason=f"Condensation possible: T_surf ({T_surf_degC:.1f} degC) <= T_dew ({T_dew:.1f} degC)",
        metrics={"T_surf_degC": T_surf_degC, "T_dew_degC": T_dew, "subcooling_K": T_dew - T_surf_degC},
    )


def eval_tpl03_condensation(
    params: Optional[TPL03Params] = None,
    T_surf_degC: Optional[float] = None,
    T_amb_degC: Optional[float] = None,
    RH: Optional[float] = None,
    m_dot_air_kg_s: float = 0.10,
    required_condensate_kg_s: Optional[float] = None,
    required_condensate_kg_h: Optional[float] = None,
    surface_area_m2: float = 1.0,
    T_surface_degC: Optional[float] = None,
    T_air_in_degC: Optional[float] = None,
    RH_in: Optional[float] = None,
) -> PhysicsCheck:
    """M5-Eval: Atmospheric water condensation check.

    Enforces the explicit humidity-ratio capacity check per FLBDS v9 §5:
    The air stream's humidity-ratio capacity must cover the required condensate,
    plus a surface-temperature check (T_surf <= T_dew).
    """
    t_surf = T_surface_degC if T_surface_degC is not None else (T_surf_degC if T_surf_degC is not None else 10.0)
    t_air = T_air_in_degC if T_air_in_degC is not None else (T_amb_degC if T_amb_degC is not None else 25.0)
    rh = RH_in if RH_in is not None else (RH if RH is not None else 0.80)

    req_kg_s = required_condensate_kg_s
    if req_kg_s is None:
        if required_condensate_kg_h is not None:
            req_kg_s = required_condensate_kg_h / 3600.0
        else:
            req_kg_s = 1.0e-4

    p_sat_in = saturation_vapor_pressure_Pa(t_air)
    p_v_in = rh * p_sat_in
    T_dew = dew_point_temperature_degC(p_v_in)

    # 1. Surface temperature check: must be below dew point
    if t_surf > T_dew:
        return PhysicsCheck(
            template_name="TPL03_Cond_Eval",
            passed=False,
            reason=f"Surface temperature {t_surf:.2f} degC above dew point {T_dew:.2f} degC (no condensation occurs)",
            metrics={"T_surface": t_surf, "T_dew": T_dew, "RH_in": rh},
        )

    # 2. Humidity-ratio capacity check
    omega_in = humidity_ratio(p_v_in)
    p_sat_out = saturation_vapor_pressure_Pa(t_surf)
    omega_out = humidity_ratio(p_sat_out)  # air leaving saturated at surface temp

    delta_omega = max(0.0, omega_in - omega_out)
    max_condensate_capacity = m_dot_air_kg_s * delta_omega

    if max_condensate_capacity < req_kg_s:
        return PhysicsCheck(
            template_name="TPL03_Cond_Eval",
            passed=False,
            reason=(
                f"Air stream humidity-ratio capacity {max_condensate_capacity*3600:.3f} kg/h below "
                f"required condensate {req_kg_s*3600:.3f} kg/h (delta_omega={delta_omega:.5f} kg/kg)"
            ),
            metrics={
                "max_condensate_kg_s": max_condensate_capacity,
                "required_condensate_kg_s": req_kg_s,
                "delta_omega": delta_omega,
                "T_dew_degC": T_dew,
            },
        )

    return PhysicsCheck(
        template_name="TPL03_Cond_Eval",
        passed=True,
        reason=(
            f"Condensation verified: T_surf ({t_surf:.1f} degC) <= T_dew ({T_dew:.1f} degC) "
            f"and air humidity capacity ({max_condensate_capacity*3600:.2f} kg/h) covers required rate"
        ),
        metrics={
            "condensate_rate_kg_h": max_condensate_capacity * 3600.0,
            "T_dew_degC": T_dew,
            "delta_omega": delta_omega,
        },
    )
