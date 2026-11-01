"""FLBDS Physics Verification Library (flbds.physics).

Implements M5-Screen (lumped parameters) and M5-Eval (coupled held-out numerical solvers)
for all ten physical mechanism templates (TPL-01 to TPL-10) per FLBDS v9 §5, §5.1, §12.
"""

from .capacity_bound import (
    CapacityBoundResult,
    check_thermal_storage_capacity,
    check_evaporative_capacity,
    check_problem_satisfiability,
)
from .tpl01_conduction import (
    screen_tpl01,
    eval_tpl01,
    compute_thermal_diffusivity,
    compute_diurnal_damping_and_lag,
)
from .tpl02_pcm import (
    screen_tpl02,
    eval_tpl02,
    solve_1d_enthalpy_stefan,
    solve_24h_robin_cycle,
    neumann_analytical_lambda,
    compute_composite_properties,
)
from .tpl03_evaporation import (
    screen_tpl03_evaporation,
    eval_tpl03_evaporation,
    eval_tpl03_condensation,
    saturation_vapor_pressure_Pa,
    humidity_ratio,
    dew_point_temperature_degC,
)
from .tpl04_sorption import (
    screen_tpl04,
    eval_tpl04,
)
from .tpl05_wicking import (
    screen_tpl05,
    eval_tpl05,
    compute_jurin_height_m,
    compute_bond_number,
)
from .tpl06_porous_flow import (
    screen_tpl06,
    eval_tpl06,
    compute_ergun_pressure_drop,
)
from .tpl07_fin import (
    screen_tpl07,
    eval_tpl07,
    compute_fin_efficiency,
)
from .tpl08_countercurrent import (
    screen_tpl08,
    eval_tpl08,
    compute_countercurrent_ntu_effectiveness,
    compute_axial_conduction_degradation,
    compute_duct_pressure_drop,
)
from .tpl09_radiative import (
    screen_tpl09,
    eval_tpl09,
    solve_quartic_surface_temperature,
)
from .tpl10_diffusion import (
    screen_tpl10,
    eval_tpl10,
    compute_knudsen_diffusivity,
    compute_bosanquet_effective_diffusivity,
    compute_external_mass_transfer_coeff,
)

__all__ = [
    # Capacity bound
    "CapacityBoundResult",
    "check_thermal_storage_capacity",
    "check_evaporative_capacity",
    "check_problem_satisfiability",
    # TPL-01
    "screen_tpl01",
    "eval_tpl01",
    "compute_thermal_diffusivity",
    "compute_diurnal_damping_and_lag",
    # TPL-02
    "screen_tpl02",
    "eval_tpl02",
    "solve_1d_enthalpy_stefan",
    "solve_24h_robin_cycle",
    "neumann_analytical_lambda",
    "compute_composite_properties",
    # TPL-03
    "screen_tpl03_evaporation",
    "eval_tpl03_evaporation",
    "eval_tpl03_condensation",
    "saturation_vapor_pressure_Pa",
    "humidity_ratio",
    "dew_point_temperature_degC",
    # TPL-04
    "screen_tpl04",
    "eval_tpl04",
    # TPL-05
    "screen_tpl05",
    "eval_tpl05",
    "compute_jurin_height_m",
    "compute_bond_number",
    # TPL-06
    "screen_tpl06",
    "eval_tpl06",
    "compute_ergun_pressure_drop",
    # TPL-07
    "screen_tpl07",
    "eval_tpl07",
    "compute_fin_efficiency",
    # TPL-08
    "screen_tpl08",
    "eval_tpl08",
    "compute_countercurrent_ntu_effectiveness",
    "compute_axial_conduction_degradation",
    "compute_duct_pressure_drop",
    # TPL-09
    "screen_tpl09",
    "eval_tpl09",
    "solve_quartic_surface_temperature",
    # TPL-10
    "screen_tpl10",
    "eval_tpl10",
    "compute_knudsen_diffusivity",
    "compute_bosanquet_effective_diffusivity",
    "compute_external_mass_transfer_coeff",
]
