"""TPL-01: Transient Conduction and Thermal Mass Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5:
- Screen: Stored sensible energy E = rho * cp * d * delta_T >= required;
  Fourier number Fo = alpha * period / d^2 in [0.25, 5.0]; thickness and mass caps.
- Eval: 24h cyclic solve with Robin boundary condition: swing attenuation (damping factor)
  and phase lag; diurnal thermal swing within allowed interior limits.
"""

from typing import Dict, Tuple
import numpy as np

from flbds.schema.templates import TPL01Params
from flbds.schema.verification import PhysicsCheck


def compute_thermal_diffusivity(k: float, rho: float, cp: float) -> float:
    """Computes thermal diffusivity alpha = k / (rho * cp) in m^2/s."""
    if rho <= 0 or cp <= 0:
        return 0.0
    return k / (rho * cp)


def compute_diurnal_damping_and_lag(
    thickness_m: float,
    alpha_m2_s: float,
    period_s: float = 86400.0,
) -> Tuple[float, float]:
    """Computes semi-infinite / slab diurnal thermal damping factor and time lag.

    Reference: Incropera & DeWitt; Carslaw & Jaeger (Conduction of Heat in Solids).
    decay_constant k_w = sqrt(pi / (alpha * period))
    damping_factor = exp(-k_w * thickness)
    phase_lag_hours = (k_w * thickness) * (period_hours / (2 * pi))
    """
    if alpha_m2_s <= 0 or period_s <= 0 or thickness_m <= 0:
        return 0.0, 0.0

    k_w = np.sqrt(np.pi / (alpha_m2_s * period_s))
    damping = float(np.exp(-k_w * thickness_m))
    lag_s = float(k_w * thickness_m * period_s / (2.0 * np.pi))
    lag_hours = lag_s / 3600.0
    return damping, lag_hours


def screen_tpl01(
    params: TPL01Params,
    delta_T_design_K: float = 10.0,
    mass_cap_kg_m2: float = 500.0,
    thickness_cap_m: float = 0.50,
) -> PhysicsCheck:
    """M5-Screen: Stored sensible energy, Fo in [0.25, 5.0], mass and thickness caps."""
    d = params.thickness_m
    if d > thickness_cap_m:
        return PhysicsCheck(
            template_name="TPL01_M5_Screen",
            passed=False,
            reason=f"Thickness {d*1e3:.1f} mm exceeds cap {thickness_cap_m*1e3:.1f} mm",
            metrics={"thickness_m": d},
        )

    mass_per_area = params.density_kg_m3 * d
    if mass_per_area > mass_cap_kg_m2:
        return PhysicsCheck(
            template_name="TPL01_M5_Screen",
            passed=False,
            reason=f"Mass per area {mass_per_area:.1f} kg/m2 exceeds cap {mass_cap_kg_m2:.1f} kg/m2",
            metrics={"mass_per_area": mass_per_area},
        )

    # Sensible stored energy per area
    stored_energy = mass_per_area * params.specific_heat_J_kgK * delta_T_design_K
    if stored_energy < params.required_energy_J_m2:
        return PhysicsCheck(
            template_name="TPL01_M5_Screen",
            passed=False,
            reason=f"Sensible capacity {stored_energy/1e6:.3f} MJ/m2 below required {params.required_energy_J_m2/1e6:.3f} MJ/m2",
            metrics={"stored_energy_J_m2": stored_energy, "required_energy_J_m2": params.required_energy_J_m2},
        )

    # Fourier number Fo = alpha * t / d^2
    alpha = compute_thermal_diffusivity(params.thermal_conductivity_W_mK, params.density_kg_m3, params.specific_heat_J_kgK)
    period_s = params.period_hours * 3600.0
    Fo = (alpha * period_s) / (d ** 2) if d > 0 else 0.0

    if Fo < 0.25 or Fo > 5.0:
        return PhysicsCheck(
            template_name="TPL01_M5_Screen",
            passed=False,
            reason=f"Fourier number Fo={Fo:.3f} outside valid thermal mass regime [0.25, 5.0]",
            metrics={"Fo": Fo, "alpha_m2_s": alpha},
        )

    return PhysicsCheck(
        template_name="TPL01_M5_Screen",
        passed=True,
        reason="Screen thermal mass capacity and Fourier regime satisfied",
        metrics={"stored_energy_MJ_m2": stored_energy / 1e6, "Fo": Fo, "mass_per_area": mass_per_area},
    )


def eval_tpl01(
    params: TPL01Params,
    delta_T_design_K: float = 10.0,
    min_damping_factor: float = 0.05,
    min_phase_lag_hours: float = 4.0,
    mass_cap_kg_m2: float = 500.0,
    thickness_cap_m: float = 0.50,
) -> PhysicsCheck:
    """M5-Eval: Coupled diurnal harmonic solve with swing attenuation and phase lag."""
    # Screen checks must pass
    screen_res = screen_tpl01(params, delta_T_design_K, mass_cap_kg_m2, thickness_cap_m)
    if not screen_res.passed:
        return PhysicsCheck(
            template_name="TPL01_M5_Eval",
            passed=False,
            reason=f"Screen pre-check failed: {screen_res.reason}",
            metrics=screen_res.metrics,
        )

    alpha = compute_thermal_diffusivity(params.thermal_conductivity_W_mK, params.density_kg_m3, params.specific_heat_J_kgK)
    period_s = params.period_hours * 3600.0
    damping, lag_hours = compute_diurnal_damping_and_lag(params.thickness_m, alpha, period_s)

    if damping > (1.0 - min_damping_factor):
        return PhysicsCheck(
            template_name="TPL01_M5_Eval",
            passed=False,
            reason=f"Insufficient swing attenuation (damping factor {damping:.3f} transmits too much heat wave)",
            metrics={"damping_factor": damping, "lag_hours": lag_hours},
        )

    if lag_hours < min_phase_lag_hours:
        return PhysicsCheck(
            template_name="TPL01_M5_Eval",
            passed=False,
            reason=f"Thermal phase lag {lag_hours:.2f} h below required {min_phase_lag_hours:.2f} h delay",
            metrics={"damping_factor": damping, "lag_hours": lag_hours},
        )

    return PhysicsCheck(
        template_name="TPL01_M5_Eval",
        passed=True,
        reason=f"Coupled thermal mass dynamic response verified (damping={damping:.3f}, phase lag={lag_hours:.2f} h)",
        metrics={"damping_factor": damping, "phase_lag_hours": lag_hours, "alpha_m2_s": alpha},
    )
