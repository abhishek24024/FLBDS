"""TPL-10: Fickian and Knudsen Diffusion Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5, §4.3:
- Screen: Uncoupled porous diffusion flux >= required flux; Mass Fourier number Fo_m >= 1.0.
- Eval: Bosanquet transition (1/D_eff = (tau/eps) * (1/D_mol + 1/D_Kn)) plus
  external boundary-layer convective mass transfer resistance (1/k_c);
  pore fouling clearance check (d_pore >= d_pore_min).
"""

from typing import Dict, Tuple
import numpy as np

from flbds.schema.templates import TPL10Params
from flbds.schema.verification import PhysicsCheck

R_GAS = 8.314462618  # Universal gas constant J/(mol.K)


def compute_knudsen_diffusivity(
    pore_diameter_m: float,
    temperature_K: float,
    molar_mass_kg_mol: float,
) -> float:
    """Computes Knudsen diffusivity D_Kn = (d_pore / 3) * sqrt(8 * R * T / (pi * M)).

    Reference: Cussler, Diffusion: Mass Transfer in Fluid Systems; Bosanquet (1944).
    """
    if pore_diameter_m <= 0 or temperature_K <= 0 or molar_mass_kg_mol <= 0:
        return 0.0
    mean_speed = np.sqrt(8.0 * R_GAS * temperature_K / (np.pi * molar_mass_kg_mol))
    return float((pore_diameter_m / 3.0) * mean_speed)


def compute_bosanquet_effective_diffusivity(
    D_mol: float,
    D_kn: float,
    porosity: float,
    tortuosity: float,
) -> Tuple[float, float]:
    """Computes pore diffusivity D_p via Bosanquet formula and effective porous medium diffusivity D_eff:

    1 / D_p = 1 / D_mol + 1 / D_kn
    D_eff = (porosity / tortuosity) * D_p

    Returns:
        (D_p [m2/s], D_eff [m2/s])
    """
    if D_mol <= 0 or D_kn <= 0:
        return 0.0, 0.0
    inv_D_p = (1.0 / D_mol) + (1.0 / D_kn)
    D_p = 1.0 / inv_D_p
    factor = (porosity / tortuosity) if tortuosity > 0 else porosity
    D_eff = factor * D_p
    return float(D_p), float(D_eff)


def compute_external_mass_transfer_coeff(
    D_mol: float,
    L_char: float,
    velocity: float,
    kinematic_viscosity: float = 1.5e-5,  # m2/s (air default)
) -> float:
    """Computes external boundary layer mass transfer coefficient k_c via Sherwood correlation.

    Laminar flat plate: Sh = 0.664 * Re^(1/2) * Sc^(1/3)
    k_c = Sh * D_mol / L_char
    """
    if L_char <= 0 or D_mol <= 0:
        return 1.0
    Re = (velocity * L_char) / kinematic_viscosity if kinematic_viscosity > 0 else 100.0
    Sc = kinematic_viscosity / D_mol if D_mol > 0 else 1.0
    Sh = 0.664 * (Re ** 0.5) * (Sc ** (1.0 / 3.0))
    return float(Sh * D_mol / L_char)


def screen_tpl10(
    params: TPL10Params,
    t_process_s: float = 3600.0,
) -> PhysicsCheck:
    """M5-Screen: Uncoupled Fickian flux and mass Fourier number Fo_m >= 1.0."""
    T_K = params.temperature_degC + 273.15
    D_kn = compute_knudsen_diffusivity(params.pore_diameter_m, T_K, params.molar_mass_kg_mol)
    D_p, D_eff = compute_bosanquet_effective_diffusivity(
        params.molecular_diffusivity_m2_s,
        D_kn,
        params.porosity,
        params.tortuosity,
    )

    L = params.membrane_thickness_m
    if L <= 0:
        return PhysicsCheck(
            name="TPL10_M5_Screen",
            passed=False,
            reason="Membrane thickness must be positive",
            metrics={},
        )

    # Mass Fourier number: Fo_m = D_eff * t / L^2
    fo_m = (D_eff * t_process_s) / (L ** 2)
    if fo_m < 1.0:
        return PhysicsCheck(
            name="TPL10_M5_Screen",
            passed=False,
            reason=f"Mass Fourier number Fo_m={fo_m:.3f} below minimum 1.0",
            metrics={"Fo_m": fo_m, "D_eff": D_eff},
        )

    # Uncoupled flux: J = D_eff * delta_C / L
    J_screen = D_eff * params.delta_concentration_mol_m3 / L
    if J_screen < params.required_flux_mol_m2_s:
        return PhysicsCheck(
            name="TPL10_M5_Screen",
            passed=False,
            reason=f"Screen flux {J_screen:.3e} mol/(m2.s) below required {params.required_flux_mol_m2_s:.3e}",
            metrics={"J_screen": J_screen, "required_flux": params.required_flux_mol_m2_s},
        )

    return PhysicsCheck(
        name="TPL10_M5_Screen",
        passed=True,
        reason="Screen diffusion flux and mass Fourier number satisfied",
        metrics={"J_screen": J_screen, "Fo_m": fo_m, "D_eff": D_eff, "D_kn": D_kn},
    )


def eval_tpl10(
    params: TPL10Params,
    external_velocity_m_s: float = 1.0,
    char_length_m: float = 0.05,
) -> PhysicsCheck:
    """M5-Eval: Coupled Bosanquet diffusion + external boundary-layer resistance + fouling clearance."""
    # 1. Fouling clearance check
    if params.pore_diameter_m < params.min_pore_diameter_m:
        return PhysicsCheck(
            name="TPL10_M5_Eval",
            passed=False,
            reason=f"Pore diameter {params.pore_diameter_m*1e9:.1f} nm below minimum fouling limit {params.min_pore_diameter_m*1e9:.1f} nm",
            metrics={"pore_diameter_m": params.pore_diameter_m, "min_pore_diameter_m": params.min_pore_diameter_m},
        )

    T_K = params.temperature_degC + 273.15
    D_kn = compute_knudsen_diffusivity(params.pore_diameter_m, T_K, params.molar_mass_kg_mol)
    D_p, D_eff = compute_bosanquet_effective_diffusivity(
        params.molecular_diffusivity_m2_s,
        D_kn,
        params.porosity,
        params.tortuosity,
    )

    L = params.membrane_thickness_m
    # Pore resistance R_pore = L / D_eff
    R_pore = L / D_eff if D_eff > 0 else float("inf")

    # External boundary layer mass transfer resistance R_BL = 1 / k_c
    k_c = compute_external_mass_transfer_coeff(
        params.molecular_diffusivity_m2_s,
        char_length_m,
        external_velocity_m_s,
    )
    R_bl = 1.0 / k_c if k_c > 0 else 0.0

    R_total = R_pore + R_bl
    J_coupled = params.delta_concentration_mol_m3 / R_total if R_total > 0 else 0.0

    if J_coupled < params.required_flux_mol_m2_s:
        return PhysicsCheck(
            name="TPL10_M5_Eval",
            passed=False,
            reason=(
                f"Coupled flux {J_coupled:.3e} mol/(m2.s) below required {params.required_flux_mol_m2_s:.3e} "
                f"(R_pore={R_pore:.1f} s/m, R_bl={R_bl:.1f} s/m, D_kn={D_kn:.2e} m2/s)"
            ),
            metrics={"J_coupled": J_coupled, "R_pore": R_pore, "R_bl": R_bl, "k_c": k_c},
        )

    return PhysicsCheck(
        name="TPL10_M5_Eval",
        passed=True,
        reason="Coupled Bosanquet diffusion, boundary-layer resistance, and pore clearance satisfied",
        metrics={
            "J_coupled_mol_m2_s": J_coupled,
            "D_eff_m2_s": D_eff,
            "D_kn_m2_s": D_kn,
            "R_pore_s_m": R_pore,
            "R_bl_s_m": R_bl,
        },
    )
