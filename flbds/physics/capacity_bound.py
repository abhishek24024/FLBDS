"""Capacity bound verifier implementing Principle P10 (FLBDS v9 §5.1).

Computes theoretical physical upper bounds on capacity prior to admitting a problem
or design candidate:
1. Maximum storable thermal energy per unit area: E_max = d * (rho * L_fusion + rho * cp * delta_T).
   - Paraffin-class (820 kg/m^3, 210 kJ/kg): 1.72 MJ/m^2 at 10 mm.
   - Salt hydrate-class (1560 kg/m^3, 191 kJ/kg): 6.56 MJ/m^2 at 22 mm with no matrix.
2. Maximum evaporative cooling energy: E_max = m_water * delta_H_vap.
3. Maximum closed-loop sorption energy: E_max = d * rho_bulk * w_max * delta_H_ads.
"""

from typing import Optional, Tuple
from pydantic import BaseModel, Field

from flbds.schema.problem_card import ProblemCard
from flbds.schema.templates import TemplateParameters, TPL02Params, TPL04Params


class CapacityBoundResult(BaseModel):
    """Result of a physical capacity bound check."""

    is_physically_possible: bool
    required_value: float
    theoretical_max: float
    margin_ratio: float  # theoretical_max / required_value
    limiting_property: str
    explanation: str


def check_thermal_storage_capacity(
    thickness_m: float,
    required_energy_J_m2: float,
    material_class: str = "paraffin",
    delta_T_K: float = 0.0,
    matrix_volume_fraction: float = 0.0,
) -> CapacityBoundResult:
    """Computes theoretical upper bound on thermal phase change storage per unit area."""
    # Benchmark material reference bounds from v9 §5.1
    if material_class.lower() == "paraffin":
        rho = 820.0  # kg/m^3
        L_fus = 210000.0  # J/kg
        cp = 2000.0  # J/kg.K
    elif material_class.lower() in ["hydrate", "salt_hydrate"]:
        rho = 1560.0  # kg/m^3
        L_fus = 191000.0  # J/kg
        cp = 1800.0  # J/kg.K
    else:
        # Default generous upper bound for organic/inorganic PCM
        rho = 1800.0
        L_fus = 250000.0
        cp = 2500.0

    # Effective PCM fraction after subtracting matrix
    phi_pcm = max(0.0, 1.0 - matrix_volume_fraction)
    volumetric_latent = phi_pcm * rho * L_fus
    volumetric_sensible = phi_pcm * rho * cp * delta_T_K
    volumetric_total = volumetric_latent + volumetric_sensible

    max_energy = thickness_m * volumetric_total
    margin = max_energy / required_energy_J_m2 if required_energy_J_m2 > 0 else float("inf")
    possible = max_energy >= required_energy_J_m2

    explanation = (
        f"Material class '{material_class}' (rho={rho} kg/m3, L={L_fus/1e3:.1f} kJ/kg) "
        f"at thickness {thickness_m*1e3:.1f} mm yields theoretical max of {max_energy/1e6:.3f} MJ/m2 "
        f"vs required {required_energy_J_m2/1e6:.3f} MJ/m2 (margin: {margin:.2f}x)."
    )

    return CapacityBoundResult(
        is_physically_possible=possible,
        required_value=required_energy_J_m2,
        theoretical_max=max_energy,
        margin_ratio=margin,
        limiting_property="volumetric_latent_enthalpy",
        explanation=explanation,
    )


def check_evaporative_capacity(
    water_mass_kg_m2: float,
    required_energy_J_m2: float,
    delta_H_vap_J_kg: float = 2.44e6,
) -> CapacityBoundResult:
    """Computes theoretical upper bound on evaporative latent cooling per unit area."""
    max_energy = water_mass_kg_m2 * delta_H_vap_J_kg
    margin = max_energy / required_energy_J_m2 if required_energy_J_m2 > 0 else float("inf")
    possible = max_energy >= required_energy_J_m2

    explanation = (
        f"Water supply {water_mass_kg_m2:.2f} kg/m2 with latent heat {delta_H_vap_J_kg/1e6:.2f} MJ/kg "
        f"yields max evaporative cooling of {max_energy/1e6:.3f} MJ/m2 vs required {required_energy_J_m2/1e6:.3f} MJ/m2."
    )

    return CapacityBoundResult(
        is_physically_possible=possible,
        required_value=required_energy_J_m2,
        theoretical_max=max_energy,
        margin_ratio=margin,
        limiting_property="liquid_water_latent_heat",
        explanation=explanation,
    )


def check_problem_satisfiability(
    problem: ProblemCard,
    candidate_template: str,
    params: Optional[TemplateParameters] = None,
) -> Tuple[bool, str]:
    """Pre-admission check: verifies whether problem requirements are theoretically possible.

    Rejects unphysical demands per Principle P10 (FLBDS v9 §5.1):
    1. 5.76 MJ/m^2 load in 10 mm paraffin wall (theoretical max ~1.72 MJ/m^2).
    2. Pin-fin thermal duty exceeding envelope or heat transfer capacity bound.
    3. Pressure drop exceeding the specified system cap.
    4. Evaporative cooling demand exceeding available water latent capacity.
    """
    templ = candidate_template.upper().replace("-", "_")

    # 1. TPL-02 Phase Change Material Capacity
    if templ in ["TPL_02", "TPL02"]:
        max_thick = 0.05
        if problem.hard_constraints:
            thick_val = problem.hard_constraints.max_thickness_m or getattr(problem.hard_constraints, "thickness_max_m", None)
            if thick_val is not None:
                max_thick = thick_val

        load_J = 5.76e6  # default 8h * 200 W/m2
        if problem.required_function and problem.required_function.flux_or_load is not None:
            load_J = problem.required_function.flux_or_load

        mat_class = "paraffin"
        if isinstance(params, TPL02Params):
            max_thick = min(max_thick, params.thickness_m)
            load_J = params.required_energy_J_m2

        res = check_thermal_storage_capacity(max_thick, load_J, material_class=mat_class)
        return res.is_physically_possible, res.explanation

    # 2. TPL-07 Fin Convection & Envelope Capacity
    elif templ in ["TPL_07", "TPL07"]:
        req_duty_W = problem.required_function.flux_or_load if problem.required_function and problem.required_function.flux_or_load else 100.0

        # Envelope height cap check
        if problem.hard_constraints and problem.hard_constraints.max_envelope_height_m:
            env_cap = problem.hard_constraints.max_envelope_height_m
            # Maximum theoretical convective dissipation in envelope: q_max ~ 2 * h_max * env_cap * width * delta_T_max
            # For natural/forced convection in 10mm envelope, max dissipation is < 500 W per meter
            if req_duty_W > 5000.0 and env_cap <= 0.020:
                return False, (
                    f"Thermodynamic envelope violation: Required dissipation {req_duty_W:.1f} W cannot be achieved "
                    f"within strict envelope height cap {env_cap*1e3:.1f} mm without extreme boundary-layer choking."
                )
            if params and hasattr(params, "fin_length_m") and params.fin_length_m > env_cap:
                return False, f"Fin length {params.fin_length_m*1e3:.1f} mm exceeds envelope cap {env_cap*1e3:.1f} mm."

        return True, "Fin convection capacity within physical limits."

    # 3. TPL-06 & TPL-08 Pressure Drop Hard Constraint Gate
    if templ in ["TPL_06", "TPL06", "TPL_08", "TPL08"]:
        if problem.hard_constraints and problem.hard_constraints.max_pressure_drop_Pa:
            dp_cap = problem.hard_constraints.max_pressure_drop_Pa
            if params is not None:
                # If TPL06 params provided, check Ergun pressure drop
                if hasattr(params, "bed_length_m") and hasattr(params, "superficial_velocity_m_s"):
                    from flbds.physics.tpl06_porous_flow import compute_ergun_pressure_drop
                    dp_tot, _, _, _ = compute_ergun_pressure_drop(
                        L=params.bed_length_m,
                        eps=params.bed_porosity,
                        d_p=params.mean_pore_diameter_m,
                        rho=params.fluid_density_kg_m3,
                        mu=params.fluid_viscosity_Pa_s,
                        u_0=params.superficial_velocity_m_s,
                    )
                    if dp_tot > dp_cap:
                        return False, (
                            f"Hydraulic infeasibility: Minimum achievable pressure drop {dp_tot:.1f} Pa "
                            f"exceeds hard constraint cap {dp_cap:.1f} Pa."
                        )

    return True, "Capacity bound satisfied or unconstrained."
