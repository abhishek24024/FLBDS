"""FLBDS Physics Verification Library (flbds.physics).

Implements M5-Screen (lumped parameters) and M5-Eval (coupled held-out numerical solvers)
per FLBDS v9 §5, §5.1, §12.
"""

from .capacity_bound import (
    CapacityBoundResult,
    check_thermal_storage_capacity,
    check_evaporative_capacity,
    check_problem_satisfiability,
)
from .tpl02_pcm import (
    screen_tpl02,
    eval_tpl02,
    solve_1d_enthalpy_stefan,
    solve_24h_robin_cycle,
    neumann_analytical_lambda,
    compute_composite_properties,
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
    # TPL-02
    "screen_tpl02",
    "eval_tpl02",
    "solve_1d_enthalpy_stefan",
    "solve_24h_robin_cycle",
    "neumann_analytical_lambda",
    "compute_composite_properties",
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
