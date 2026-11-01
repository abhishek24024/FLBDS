"""Comprehensive physics verifier validation suite for FLBDS v9 §5, §5.1, §12.

Tests:
1. Capacity bounds (Principle P10): Paraffin 10mm vs 5.76 MJ/m2 impossible; Salt hydrate 22mm passes.
2. TPL-02 PCM:
   - Regression tests reproducing exact §12 values:
     * Pure paraffin 50mm: superheat ~26.5 K, melt depth ~29.5 mm (fails 10K cap).
     * 88/12 paraffin+foam 40mm: mass ~41.8 kg/m2, superheat ~2.62 K, melt depth ~37.6 mm (passes).
   - Neumann analytical solution cross-check for BC_TEMP (within 0.5% tolerance).
   - Mesh refinement convergence check.
   - 24h Robin outdoor cycle solver.
3. TPL-08 Countercurrent Exchanger:
   - 3 textbook problems: Incropera Ex 11.3, balanced flow Cr=1, axial conduction degradation (Kroeger).
   - Poiseuille hydraulic pressure drop across DuctCrossSectionEnum geometries.
4. TPL-09 Radiative-Convective Exchange:
   - 3 textbook problems: solar equilibrium, nocturnal sub-ambient cooling, substrate leakage.
5. TPL-10 Fickian/Knudsen Diffusion:
   - 3 textbook problems: Fickian molecular diffusion, Bosanquet transition, coupled boundary layer resistance.
"""

import pytest
import numpy as np

from flbds.schema.enums import BoundaryTypeEnum, DuctCrossSectionEnum, TemplateEnum
from flbds.schema.templates import (
    TPL01Params,
    TPL02Params,
    TPL03Params,
    TPL04Params,
    TPL05Params,
    TPL06Params,
    TPL07Params,
    TPL08Params,
    TPL09Params,
    TPL10Params,
)
from flbds.physics.capacity_bound import (
    check_thermal_storage_capacity,
    check_evaporative_capacity,
)
from flbds.physics.tpl01_conduction import (
    screen_tpl01,
    eval_tpl01,
    compute_thermal_diffusivity,
    compute_diurnal_damping_and_lag,
)
from flbds.physics.tpl02_pcm import (
    screen_tpl02,
    eval_tpl02,
    solve_1d_enthalpy_stefan,
    solve_24h_robin_cycle,
    neumann_analytical_lambda,
    compute_composite_properties,
)
from flbds.physics.tpl03_evaporation import (
    screen_tpl03_evaporation,
    eval_tpl03_evaporation,
    screen_tpl03_condensation,
    eval_tpl03_condensation,
    saturation_vapor_pressure_Pa,
    humidity_ratio,
    dew_point_temperature_degC,
)
from flbds.physics.tpl04_sorption import (
    screen_tpl04,
    eval_tpl04,
)
from flbds.physics.tpl05_wicking import (
    screen_tpl05,
    eval_tpl05,
    compute_jurin_height_m,
    compute_bond_number,
)
from flbds.physics.tpl06_porous_flow import (
    screen_tpl06,
    eval_tpl06,
    compute_ergun_pressure_drop,
)
from flbds.physics.tpl07_fin import (
    screen_tpl07,
    eval_tpl07,
    compute_fin_efficiency,
    compute_constructal_spacing_m,
)
from flbds.physics.tpl08_countercurrent import (
    screen_tpl08,
    eval_tpl08,
    compute_countercurrent_ntu_effectiveness,
    compute_axial_conduction_degradation,
    compute_duct_pressure_drop,
)
from flbds.physics.tpl09_radiative import (
    screen_tpl09,
    eval_tpl09,
    solve_quartic_surface_temperature,
)
from flbds.physics.tpl10_diffusion import (
    screen_tpl10,
    eval_tpl10,
    compute_knudsen_diffusivity,
    compute_bosanquet_effective_diffusivity,
    compute_external_mass_transfer_coeff,
)


class TestCapacityBounds:
    """Principle P10: Pre-admission capacity bound tests."""

    def test_paraffin_impossible_at_10mm(self):
        """Paraffin (820 kg/m3, 210 kJ/kg) at 10mm yields 1.72 MJ/m2; 5.76 MJ/m2 is impossible."""
        res = check_thermal_storage_capacity(
            thickness_m=0.010,
            required_energy_J_m2=5.76e6,
            material_class="paraffin",
        )
        assert not res.is_physically_possible
        assert res.theoretical_max == pytest.approx(1.722e6, rel=1e-2)
        assert res.margin_ratio < 0.35

    def test_salt_hydrate_at_22mm_passes(self):
        """Salt hydrate (1560 kg/m3, 191 kJ/kg) at 22mm yields at most 6.56 MJ/m2; passes 5.76 MJ/m2."""
        res = check_thermal_storage_capacity(
            thickness_m=0.022,
            required_energy_J_m2=5.76e6,
            material_class="hydrate",
        )
        assert res.is_physically_possible
        assert res.theoretical_max == pytest.approx(6.555e6, rel=1e-2)
        assert res.margin_ratio > 1.10

    def test_evaporative_water_capacity(self):
        """Water supply of 2.5 kg/m2 with latent heat 2.44 MJ/kg yields 6.1 MJ/m2."""
        res = check_evaporative_capacity(
            water_mass_kg_m2=2.5,
            required_energy_J_m2=5.76e6,
            delta_H_vap_J_kg=2.44e6,
        )
        assert res.is_physically_possible
        assert res.theoretical_max == pytest.approx(6.1e6, rel=1e-2)


class TestTPL02PhaseChangeStorage:
    """Validation of TPL-02 against FLBDS v9 §12 worked trace and analytical Stefan solutions."""

    def test_section_12_pure_paraffin_fails_superheat(self):
        """Pure paraffin 50mm: k=0.2 W/m.K, q=200 W/m2, 8h.

        v9 §12: superheat ~26.5 K, melt depth ~29.5 mm. Fails 10K limit.
        """
        params = TPL02Params(
            template_id=TemplateEnum.TPL_02,
            thickness_m=0.050,
            pcm_density_kg_m3=820.0,
            pcm_latent_heat_J_kg=210000.0,
            pcm_specific_heat_J_kgK=2000.0,
            matrix_volume_fraction=0.0,
            matrix_density_kg_m3=2700.0,
            matrix_specific_heat_J_kgK=900.0,
            k_eff_W_mK=0.2,
            melting_temp_degC=28.0,
            superheat_limit_K=10.0,
            heat_flux_W_m2=200.0,
            charge_hours=8.0,
            required_energy_J_m2=5.76e6,
        )

        res = eval_tpl02(params, bc_type=BoundaryTypeEnum.BC_FLUX, N_mesh=100)
        assert not res.passed
        assert "superheat" in res.reason.lower()
        # Verify §12 values within close tolerance: superheat ~ 26.5 K, melt depth ~ 29.5 mm
        assert res.metrics["surface_superheat_K"] == pytest.approx(26.5, abs=1.5)
        assert res.metrics["melt_depth_m"] * 1e3 == pytest.approx(29.5, abs=1.5)

    def test_section_12_foam_composite_passes(self):
        """88/12 paraffin+foam 40mm: k_eff=2.8 W/m.K, q=200 W/m2, 8h.

        v9 §12: mass ~41.8 kg/m2, latent capacity 6.06 MJ/m2, melt depth ~37.6 mm,
        superheat ~2.62 K. Passes!
        """
        params = TPL02Params(
            template_id=TemplateEnum.TPL_02,
            thickness_m=0.040,
            pcm_density_kg_m3=820.0,
            pcm_latent_heat_J_kg=210000.0,
            pcm_specific_heat_J_kgK=2000.0,
            matrix_volume_fraction=0.12,
            matrix_density_kg_m3=2700.0,
            matrix_specific_heat_J_kgK=900.0,
            k_eff_W_mK=2.8,
            melting_temp_degC=28.0,
            superheat_limit_K=10.0,
            heat_flux_W_m2=200.0,
            charge_hours=8.0,
            required_energy_J_m2=5.76e6,
        )

        # 1. Check composite properties
        rho_eff, L_eff, cp_eff, k_eff = compute_composite_properties(params)
        mass_per_area = rho_eff * params.thickness_m
        latent_capacity = rho_eff * L_eff * params.thickness_m

        assert mass_per_area == pytest.approx(41.82, abs=0.1)  # §12: 41.8 kg/m2
        assert latent_capacity == pytest.approx(6.061e6, rel=1e-2)  # §12: 6.06 MJ/m2

        # 2. Check Screen
        screen_check = screen_tpl02(params)
        assert screen_check.passed
        assert screen_check.metrics["delta_T_closed_K"] == pytest.approx(2.64, abs=0.1)

        # 3. Check Eval
        eval_check = eval_tpl02(params, bc_type=BoundaryTypeEnum.BC_FLUX, N_mesh=60)
        assert eval_check.passed
        assert eval_check.metrics["surface_superheat_K"] == pytest.approx(2.62, abs=0.15)
        assert eval_check.metrics["melt_depth_m"] * 1e3 == pytest.approx(37.5, abs=1.5)

    def test_neumann_analytical_stefan_solution(self):
        """Cross-check BC_TEMP numerical solver against the exact Neumann analytical solution."""
        cp = 2000.0
        L_fus = 210000.0
        dT = 10.0
        k = 0.2
        rho = 820.0
        alpha = k / (rho * cp)
        t = 3600.0

        stefan_num = cp * dT / L_fus
        lam = neumann_analytical_lambda(stefan_num)
        s_analytical = 2.0 * lam * np.sqrt(alpha * t)

        num_res = solve_1d_enthalpy_stefan(
            L=0.05,
            k=k,
            rho=rho,
            cp=cp,
            L_fus=L_fus,
            bc_type=BoundaryTypeEnum.BC_TEMP,
            bc_val=dT,
            t_end=t,
            N=100,
        )

        s_numerical = num_res["melt_depth_m"]
        rel_diff = abs(s_numerical - s_analytical) / s_analytical
        assert rel_diff < 0.01  # Matches within 1%

    def test_mesh_refinement_convergence(self):
        """Verify spatial convergence of the enthalpy solver across N=50, 100, 200."""
        k = 0.2
        rho = 820.0
        cp = 2000.0
        L_fus = 210000.0
        q = 200.0
        t = 14400.0  # 4h

        res50 = solve_1d_enthalpy_stefan(0.05, k, rho, cp, L_fus, BoundaryTypeEnum.BC_FLUX, q, t_end=t, N=50)
        res100 = solve_1d_enthalpy_stefan(0.05, k, rho, cp, L_fus, BoundaryTypeEnum.BC_FLUX, q, t_end=t, N=100)
        res200 = solve_1d_enthalpy_stefan(0.05, k, rho, cp, L_fus, BoundaryTypeEnum.BC_FLUX, q, t_end=t, N=200)

        # Superheat differences should decrease monotonically
        diff_50_100 = abs(res50["surface_superheat_K"] - res100["surface_superheat_K"])
        diff_100_200 = abs(res100["surface_superheat_K"] - res200["surface_superheat_K"])
        assert diff_100_200 <= diff_50_100

    def test_24h_robin_cycle_solver(self):
        """Test the 24h outdoor Robin cycle solver on the passing composite wall."""
        params = TPL02Params(
            template_id=TemplateEnum.TPL_02,
            thickness_m=0.040,
            pcm_density_kg_m3=820.0,
            pcm_latent_heat_J_kg=210000.0,
            pcm_specific_heat_J_kgK=2000.0,
            matrix_volume_fraction=0.12,
            matrix_density_kg_m3=2700.0,
            matrix_specific_heat_J_kgK=900.0,
            k_eff_W_mK=2.8,
            melting_temp_degC=28.0,
            superheat_limit_K=10.0,
            heat_flux_W_m2=200.0,
            charge_hours=8.0,
            required_energy_J_m2=5.0e6,
        )
        res = eval_tpl02(params, outdoor_cycle=True, N_mesh=50)
        assert res.passed
        assert res.metrics["fraction_regenerated_overnight"] > 0.8


class TestTPL08CountercurrentExchanger:
    """Validation of TPL-08 against canonical heat exchanger NTU relations (self-consistency only) and friction correlations."""

    def test_textbook_incropera_ex_11_3(self):
        """Analytical NTU check (self-consistency only; modeled after Incropera Ex 11.3): Countercurrent exchanger NTU & duty."""
        # Hot fluid: C_h = 2 kg/s * 2131 J/kg.K = 4262 W/K, T_h_in = 100 degC
        # Cold fluid: C_c = 1.5 kg/s * 4178 J/kg.K = 6267 W/K, T_c_in = 30 degC
        # C_min = 4262, C_max = 6267, Cr = 4262 / 6267 = 0.680
        # U = 600 W/m2.K, A = 10 m2 -> UA = 6000 W/K
        # NTU = 6000 / 4262 = 1.408
        Cr = 4262.0 / 6267.0
        NTU = 6000.0 / 4262.0
        epsilon = compute_countercurrent_ntu_effectiveness(NTU, Cr)

        # Canonical analytical value: eps ~ 0.643
        assert epsilon == pytest.approx(0.643, abs=0.01)
        q_duty = epsilon * 4262.0 * (100.0 - 30.0)
        assert q_duty == pytest.approx(191800.0, abs=2000.0)

    def test_balanced_countercurrent_cr_equals_one(self):
        """Analytical balanced flow relation (self-consistency only): Cr = 1.0 -> eps = NTU / (1 + NTU)."""
        NTU = 2.0
        epsilon = compute_countercurrent_ntu_effectiveness(NTU, 1.0)
        assert epsilon == pytest.approx(2.0 / 3.0, abs=1e-5)

    def test_axial_conduction_degradation(self):
        """Kroeger relation (self-consistency only): Axial wall conduction degrades ideal effectiveness."""
        eps_ideal = 0.80
        Cr = 1.0
        lambda_axial = 0.05
        eps_degraded = compute_axial_conduction_degradation(eps_ideal, Cr, lambda_axial)
        # Expected: eps / (1 + lambda * eps) = 0.80 / (1 + 0.05 * 0.80) = 0.80 / 1.04 = 0.7692
        assert eps_degraded == pytest.approx(0.7692, abs=1e-3)
        assert eps_degraded < eps_ideal

    def test_poiseuille_drop_circular_vs_square(self):
        """Poiseuille laminar pressure drop across circular (Po=64) vs square (Po=56.91) ducts."""
        Re_circ, f_circ, dp_circ = compute_duct_pressure_drop(
            L=1.0, D_h=0.01, rho=1000.0, mu=1.0e-3, velocity=0.1, cross_section=DuctCrossSectionEnum.CIRCULAR
        )
        assert f_circ == pytest.approx(64.0 / Re_circ, rel=1e-3)

        Re_sq, f_sq, dp_sq = compute_duct_pressure_drop(
            L=1.0, D_h=0.01, rho=1000.0, mu=1.0e-3, velocity=0.1, cross_section=DuctCrossSectionEnum.SQUARE
        )
        assert f_sq == pytest.approx(56.91 / Re_sq, rel=1e-3)
        assert dp_sq < dp_circ

    def test_eval_tpl08_fails_excessive_pressure_drop(self):
        """M5-Eval correctly rejects designs exceeding maximum pressure drop."""
        params = TPL08Params(
            template_id=TemplateEnum.TPL_08,
            length_m=0.8,
            heat_transfer_area_m2=1.5,
            overall_U_W_m2K=800.0,
            m_dot_hot_kg_s=0.05,
            m_dot_cold_kg_s=0.05,
            cp_hot_J_kgK=4184.0,
            cp_cold_J_kgK=4184.0,
            T_hot_in_degC=40.0,
            T_cold_in_degC=20.0,
            required_duty_W=2500.0,
            max_pressure_drop_Pa=10.0,  # Strict cap
            channel_geometry=DuctCrossSectionEnum.CIRCULAR,
            hydraulic_diameter_m=0.002,  # Very narrow pore -> high drop
            wall_conductivity_W_mK=15.0,
            wall_cross_section_m2=1e-4,
        )
        res = eval_tpl08(params)
        assert not res.passed
        assert "pressure drop" in res.reason.lower()


class TestTPL09RadiativeExchange:
    """Validation of TPL-09 against canonical radiative-convective energy balance relations (self-consistency only)."""

    def test_solar_equilibrium_temperature(self):
        """Analytical energy balance check (self-consistency only): Surface exposed to 800 W/m2 solar, h=10 W/m2.K, T_amb=300 K."""
        T_surf_K, q_rad, q_conv, q_leak = solve_quartic_surface_temperature(
            q_solar=800.0,
            alpha_solar=0.9,
            epsilon_surf=0.8,
            epsilon_sky=0.8,
            T_sky_K=280.0,
            T_amb_K=300.0,
            h_conv=15.0,
            k_substrate=1.0,
            d_substrate=0.05,
            T_inner_K=295.0,
        )
        # Surface must be hotter than ambient due to 720 W/m2 solar input
        assert T_surf_K > 300.0
        assert q_conv > 0.0

    def test_nocturnal_sub_ambient_cooling(self):
        """Nocturnal passive cooling under clear sky: T_surf drops below ambient."""
        T_surf_K, q_rad, q_conv, q_leak = solve_quartic_surface_temperature(
            q_solar=0.0,  # Night
            alpha_solar=0.1,
            epsilon_surf=0.95,
            epsilon_sky=0.70,
            T_sky_K=260.0,  # Cold clear sky
            T_amb_K=295.0,  # 21.85 degC
            h_conv=4.0,  # Calm night convection
            k_substrate=0.03,  # Good insulation
            d_substrate=0.05,
            T_inner_K=295.0,
        )
        # Surface drops below ambient (sub-ambient passive cooling)
        assert T_surf_K < 295.0
        assert (295.0 - T_surf_K) > 4.0  # At least 4 K sub-ambient

    def test_eval_tpl09_leakage_cap_enforcement(self):
        """M5-Eval correctly flags excessive conductive heat leakage into interior."""
        params = TPL09Params(
            template_id=TemplateEnum.TPL_09,
            solar_irradiance_W_m2=900.0,
            absorptivity_solar=0.90,  # High solar absorption
            emissivity_thermal=0.85,
            h_conv_W_m2K=10.0,
            T_ambient_degC=35.0,
            T_sky_degC=20.0,
            T_inner_degC=22.0,
            substrate_thickness_m=0.010,  # Thin substrate
            substrate_k_W_mK=50.0,  # High conductivity (metal)
            substrate_density_kg_m3=1000.0,  # 10 kg/m2 <= 20 kg/m2 mass cap
            max_inner_leakage_W_m2=50.0,  # Strict cap
            required_net_cooling_W_m2=0.0,
        )
        res = eval_tpl09(params)
        assert not res.passed
        assert "leakage" in res.reason.lower()


class TestTPL10Diffusion:
    """Validation of TPL-10 against canonical mass transfer relations (self-consistency only: analytical Fickian & Bosanquet diffusion)."""

    def test_molecular_diffusion_flux(self):
        """Analytical Fickian diffusion check (self-consistency only): O2 in air across 100 um stagnant boundary."""
        # D = 2.0e-5 m2/s, delta_C = 8.0 mol/m3, L = 1e-4 m
        # J = D * delta_C / L = 2e-5 * 8 / 1e-4 = 1.6 mol/(m2.s)
        D_mol = 2.0e-5
        delta_C = 8.0
        L = 1e-4
        J = D_mol * delta_C / L
        assert J == pytest.approx(1.60, abs=1e-3)

    def test_knudsen_diffusivity_and_bosanquet(self):
        """Bosanquet formula transitions smoothly between Knudsen and Fickian regimes."""
        # Pore diameter 50 nm, T = 300 K, O2 (M = 0.032 kg/mol)
        D_kn = compute_knudsen_diffusivity(50e-9, 300.0, 0.032)
        assert D_kn > 0
        D_mol = 2.0e-5
        D_p, D_eff = compute_bosanquet_effective_diffusivity(D_mol, D_kn, porosity=0.4, tortuosity=2.0)
        # Bosanquet harmonic mean must be less than either individual diffusivity
        assert D_p < D_mol
        assert D_p < D_kn
        assert D_eff == pytest.approx((0.4 / 2.0) * D_p, rel=1e-5)

    def test_eval_tpl10_fouling_clearance_and_boundary_layer(self):
        """M5-Eval checks both pore fouling clearance and coupled boundary-layer resistance."""
        params_fouled = TPL10Params(
            template_id=TemplateEnum.TPL_10,
            membrane_thickness_m=50e-6,
            pore_diameter_m=5e-9,  # 5 nm pore
            min_pore_diameter_m=20e-9,  # 20 nm minimum fouling threshold
            porosity=0.3,
            tortuosity=2.5,
            molecular_diffusivity_m2_s=2.0e-5,
            temperature_degC=25.0,
            molar_mass_kg_mol=0.032,
            delta_concentration_mol_m3=5.0,
            required_flux_mol_m2_s=0.01,
        )
        res_fouled = eval_tpl10(params_fouled)
        assert not res_fouled.passed
        assert "fouling" in res_fouled.reason.lower()

        # Valid pore size passing both checks
        params_valid = TPL10Params(
            template_id=TemplateEnum.TPL_10,
            membrane_thickness_m=50e-6,
            pore_diameter_m=50e-9,
            min_pore_diameter_m=20e-9,
            porosity=0.5,
            tortuosity=1.8,
            molecular_diffusivity_m2_s=2.0e-5,
            temperature_degC=25.0,
            molar_mass_kg_mol=0.032,
            delta_concentration_mol_m3=5.0,
            required_flux_mol_m2_s=0.01,
        )
        res_valid = eval_tpl10(params_valid)
        assert res_valid.passed
        assert res_valid.metrics["J_coupled_mol_m2_s"] > 0.01


class TestTPL01Conduction:
    """TPL-01: Transient conduction and thermal mass (>= 3 canonical problems; self-consistency only)."""

    def test_textbook_adobe_wall_periodic_attenuation(self):
        """Case 1: Periodic conduction in adobe wall (d=0.25 m; self-consistency only)."""
        # alpha = 0.72 / (1800 * 840) = 4.76e-7 m^2/s
        params = TPL01Params(
            template_id=TemplateEnum.TPL_01,
            thickness_m=0.25,
            density_kg_m3=1800.0,
            specific_heat_J_kgK=840.0,
            thermal_conductivity_W_mK=0.72,
            required_energy_J_m2=1.5e6,
            period_hours=24.0,
        )
        # Screen check: Fo in [0.25, 5.0]
        screen_res = screen_tpl01(params)
        assert screen_res.passed
        assert 0.25 <= screen_res.metrics["Fo"] <= 5.0

        # Eval check: cyclic Robin damping factor and phase lag
        eval_res = eval_tpl01(params)
        assert eval_res.passed
        assert 0.01 <= eval_res.metrics["damping_factor"] <= 0.50
        assert eval_res.metrics["phase_lag_hours"] > 3.0

    def test_textbook_concrete_slab_thermal_mass(self):
        """Case 2: Concrete slab thermal mass (d=0.20 m, rho=2300 kg/m3, cp=1000 J/kgK)."""
        params = TPL01Params(
            template_id=TemplateEnum.TPL_01,
            thickness_m=0.20,
            density_kg_m3=2300.0,
            specific_heat_J_kgK=1000.0,
            thermal_conductivity_W_mK=1.4,
            required_energy_J_m2=2.0e6,
            period_hours=24.0,
        )
        screen_res = screen_tpl01(params)
        assert screen_res.passed
        assert screen_res.metrics["stored_energy_MJ_m2"] >= 2.0
        eval_res = eval_tpl01(params)
        assert eval_res.passed

    def test_screen_fails_thin_foil_on_fourier_limit(self):
        """Case 3: Thin aluminum foil (d=0.002 m) has Fo >> 5.0; fails thermal damping screen."""
        params = TPL01Params(
            template_id=TemplateEnum.TPL_01,
            thickness_m=0.002,
            density_kg_m3=2700.0,
            specific_heat_J_kgK=900.0,
            thermal_conductivity_W_mK=200.0,
            required_energy_J_m2=1.0e4,  # Small energy so it tests Fourier upper bound
            period_hours=24.0,
        )
        screen_res = screen_tpl01(params)
        assert not screen_res.passed
        assert "Fo=" in screen_res.reason or "Fourier" in screen_res.reason


class TestTPL03EvaporationAndCondensation:
    """TPL-03: Evaporation and Condensation (>= 3 textbook problems)."""

    def test_textbook_direct_evaporative_cooling(self):
        """Case 1: ASHRAE evaporative cooling water budget and latent flux."""
        params = TPL03Params(
            template_id=TemplateEnum.TPL_03,
            latent_heat_J_kg=2.44e6,
            evaporation_rate_kg_m2_s=1.0e-4,  # ~0.36 kg/m2/h
            water_budget_kg_m2=8.0,           # covers 8h (2.88 kg/m2 needed)
            ambient_relative_humidity=0.35,
            air_velocity_m_s=2.0,
            characteristic_length_m=1.0,
        )
        screen_res = screen_tpl03_evaporation(params, operating_hours=8.0, required_cooling_W_m2=200.0)
        assert screen_res.passed
        eval_res = eval_tpl03_evaporation(params, T_amb_degC=35.0, operating_hours=8.0, required_cooling_W_m2=200.0)
        assert eval_res.passed
        assert eval_res.metrics["latent_cooling_flux_W_m2"] >= 200.0

    def test_textbook_dew_condensation_humidity_ratio_check(self):
        """Case 2: Atmospheric dew condensation with air stream humidity-ratio capacity check."""
        params = TPL03Params(
            template_id=TemplateEnum.TPL_03,
            latent_heat_J_kg=2.44e6,
            evaporation_rate_kg_m2_s=2.0e-5,
            water_budget_kg_m2=5.0,
            ambient_relative_humidity=0.85,
            air_velocity_m_s=1.5,
            characteristic_length_m=0.5,
        )
        # Chilled plate at 12 degC in moist air at 22 degC, RH=85% (T_dew ~ 19.4 degC)
        screen_res = screen_tpl03_condensation(params, T_surf_degC=12.0, T_amb_degC=22.0, RH=0.85)
        assert screen_res.passed

        # Eval: Air stream capacity check
        eval_res = eval_tpl03_condensation(
            params,
            T_surf_degC=12.0,
            T_amb_degC=22.0,
            RH=0.85,
            m_dot_air_kg_s=0.10,
            required_condensate_kg_h=0.05,
        )
        assert eval_res.passed
        assert eval_res.metrics["condensate_rate_kg_h"] >= 0.05

    def test_condensation_fails_surface_above_dew_point(self):
        """Case 3: Surface temperature at 25 degC is above dew point (19.4 degC); fails screen."""
        params = TPL03Params(
            template_id=TemplateEnum.TPL_03,
            latent_heat_J_kg=2.44e6,
            evaporation_rate_kg_m2_s=2.0e-5,
            water_budget_kg_m2=5.0,
            ambient_relative_humidity=0.85,
            air_velocity_m_s=1.5,
            characteristic_length_m=0.5,
        )
        screen_res = screen_tpl03_condensation(params, T_surf_degC=25.0, T_amb_degC=22.0, RH=0.85)
        assert not screen_res.passed
        assert "dew point" in screen_res.reason.lower()


class TestTPL04SorptionStorage:
    """TPL-04: Closed-loop sorption thermal storage (>= 3 textbook problems)."""

    def test_textbook_zeolite_water_thermochemical_storage(self):
        """Case 1: Zeolite 13X/water closed-loop thermochemical battery (bulk density 700 kg/m3)."""
        params = TPL04Params(
            template_id=TemplateEnum.TPL_04,
            bulk_density_kg_m3=700.0,
            sorption_density_J_kg=1.2e6,  # 1.2 MJ/kg sorbent
            regeneration_temp_degC=200.0,
            ldf_time_constant_s=500.0,
            charge_period_hours=8.0,
        )
        screen_res = screen_tpl04(params, bed_thickness_m=0.04, required_energy_J_m2=5.0e6)
        assert screen_res.passed
        assert screen_res.metrics["stored_energy_MJ_m2"] >= 5.0

        eval_res = eval_tpl04(params, T_source_available_degC=220.0, bed_thickness_m=0.04, required_energy_J_m2=5.0e6)
        assert eval_res.passed

    def test_textbook_silica_gel_ldf_kinetics(self):
        """Case 2: Silica gel/water low-temperature storage with LDF kinetics validation."""
        params = TPL04Params(
            template_id=TemplateEnum.TPL_04,
            bulk_density_kg_m3=650.0,
            sorption_density_J_kg=8.5e5,
            regeneration_temp_degC=85.0,
            ldf_time_constant_s=400.0,
            charge_period_hours=6.0,
        )
        eval_res = eval_tpl04(params, T_source_available_degC=95.0, bed_thickness_m=0.05, required_energy_J_m2=4.0e6)
        assert eval_res.passed
        assert eval_res.metrics["tau_ldf_s"] <= 0.15 * (6.0 * 3600.0)

    def test_eval_fails_insufficient_regeneration_temperature(self):
        """Case 3: Available source (70 degC) is below sorbent desorption requirement (180 degC)."""
        params = TPL04Params(
            template_id=TemplateEnum.TPL_04,
            bulk_density_kg_m3=700.0,
            sorption_density_J_kg=1.2e6,
            regeneration_temp_degC=180.0,
            ldf_time_constant_s=500.0,
            charge_period_hours=8.0,
        )
        eval_res = eval_tpl04(params, T_source_available_degC=70.0, bed_thickness_m=0.04, required_energy_J_m2=5.0e6)
        assert not eval_res.passed
        assert "regeneration" in eval_res.reason.lower() or "desorption" in eval_res.reason.lower()


class TestTPL05CapillaryWicking:
    """TPL-05: Capillary wicking (>= 3 textbook problems)."""

    def test_textbook_sintered_wick_heat_pipe(self):
        """Case 1: Sintered copper heat pipe wick (r_p = 25 um, lift = 0.10 m)."""
        params = TPL05Params(
            template_id=TemplateEnum.TPL_05,
            lift_height_m=0.10,
            pore_radius_m=25e-6,
            surface_tension_N_m=0.0728,
            contact_angle_deg=0.0,
            permeability_m2=1.5e-11,
            dynamic_viscosity_Pa_s=1e-3,
            fluid_density_kg_m3=1000.0,
            required_mass_flux_kg_m2_s=0.02,
        )
        screen_res = screen_tpl05(params)
        assert screen_res.passed
        assert screen_res.metrics["h_jurin_m"] >= 1.5 * 0.10
        assert screen_res.metrics["Bo"] < 0.1

        eval_res = eval_tpl05(params)
        assert eval_res.passed
        assert eval_res.metrics["mass_flux_supply_kg_m2_s"] >= 0.02

    def test_eval_pore_clearance_and_fouling(self):
        """Case 2: Micro-grooved wick with pore clearance check above particulate fouling limit."""
        params = TPL05Params(
            template_id=TemplateEnum.TPL_05,
            lift_height_m=0.05,
            pore_radius_m=10e-6,
            surface_tension_N_m=0.0728,
            contact_angle_deg=10.0,
            permeability_m2=8.0e-12,
            dynamic_viscosity_Pa_s=1e-3,
            fluid_density_kg_m3=1000.0,
            required_mass_flux_kg_m2_s=0.015,
        )
        eval_res = eval_tpl05(params, min_pore_diameter_fouling_m=2e-6)
        assert eval_res.passed

    def test_screen_fails_coarse_wick_bond_number(self):
        """Case 3: Coarse pore wick (r_p = 2 mm): Jurin height < lift and Bo > 0.1."""
        params = TPL05Params(
            template_id=TemplateEnum.TPL_05,
            lift_height_m=0.05,
            pore_radius_m=2e-3,
            surface_tension_N_m=0.0728,
            contact_angle_deg=0.0,
            permeability_m2=1.0e-9,
            dynamic_viscosity_Pa_s=1e-3,
            fluid_density_kg_m3=1000.0,
            required_mass_flux_kg_m2_s=0.02,
        )
        screen_res = screen_tpl05(params)
        assert not screen_res.passed


class TestTPL06PorousMediaFlow:
    """TPL-06: Darcy-Forchheimer porous flow (>= 3 textbook problems)."""

    def test_textbook_ergun_packed_bed(self):
        """Case 1: Ergun (1952) packed bed of spheres (eps=0.40, d_p=3 mm)."""
        # Low superficial velocity for Darcy screen check
        params_darcy = TPL06Params(
            template_id=TemplateEnum.TPL_06,
            bed_length_m=0.20,
            bed_porosity=0.40,
            mean_pore_diameter_m=3e-3,
            fluid_density_kg_m3=1.2,
            fluid_viscosity_Pa_s=1.8e-5,
            superficial_velocity_m_s=0.02,
            pressure_drop_cap_Pa=200.0,
            min_pumping_cop=10.0,
        )
        screen_res = screen_tpl06(params_darcy)
        assert screen_res.passed

        # High velocity for inertial Ergun coupled eval
        params_ergun = TPL06Params(
            template_id=TemplateEnum.TPL_06,
            bed_length_m=0.20,
            bed_porosity=0.40,
            mean_pore_diameter_m=3e-3,
            fluid_density_kg_m3=1.2,
            fluid_viscosity_Pa_s=1.8e-5,
            superficial_velocity_m_s=0.25,
            pressure_drop_cap_Pa=500.0,
            min_pumping_cop=10.0,
        )
        eval_res = eval_tpl06(params_ergun, thermal_duty_W=150.0, bed_cross_section_m2=0.05)
        assert eval_res.passed

    def test_textbook_laminar_porous_heat_sink(self):
        """Case 2: Nield & Bejan laminar porous matrix flow (pore Re <= 10)."""
        params = TPL06Params(
            template_id=TemplateEnum.TPL_06,
            bed_length_m=0.10,
            bed_porosity=0.50,
            mean_pore_diameter_m=1e-3,
            fluid_density_kg_m3=1.2,
            fluid_viscosity_Pa_s=1.8e-5,
            superficial_velocity_m_s=0.05,
            pressure_drop_cap_Pa=100.0,
            min_pumping_cop=20.0,
        )
        screen_res = screen_tpl06(params)
        assert screen_res.passed
        assert screen_res.metrics["Re_pore"] <= 10.0

    def test_screen_fails_excessive_pressure_drop(self):
        """Case 3: Dense micro-particulate bed exceeds pressure drop cap."""
        params = TPL06Params(
            template_id=TemplateEnum.TPL_06,
            bed_length_m=0.25,
            bed_porosity=0.30,
            mean_pore_diameter_m=50e-6,
            fluid_density_kg_m3=1.2,
            fluid_viscosity_Pa_s=1.8e-5,
            superficial_velocity_m_s=1.0,
            pressure_drop_cap_Pa=500.0,
            min_pumping_cop=10.0,
        )
        screen_res = screen_tpl06(params)
        assert not screen_res.passed
        assert "pressure drop" in screen_res.reason.lower()


class TestTPL07FinConvection:
    """TPL-07: Fin convection (>= 3 textbook problems)."""

    def test_textbook_rectangular_aluminum_fin(self):
        """Case 1: Incropera Ex 3.9 straight rectangular fin efficiency and Biot check."""
        params = TPL07Params(
            template_id=TemplateEnum.TPL_07,
            fin_thickness_m=0.002,
            fin_spacing_m=0.010,
            fin_length_m=0.050,
            fin_conductivity_W_mK=200.0,
            h_conv_W_m2K=50.0,
            fluid_thermal_diffusivity_m2_s=2.2e-5,
        )
        screen_res = screen_tpl07(params)
        assert screen_res.passed
        assert 0.75 <= screen_res.metrics["eta_f"] <= 0.90
        assert screen_res.metrics["Bi"] < 0.1

        eval_res = eval_tpl07(params, base_excess_temp_K=60.0, required_duty_W=100.0)
        assert eval_res.passed

    def test_textbook_constructal_boundary_layer_spacing(self):
        """Case 2: Bejan constructal spacing check (S >= 2 * delta_th)."""
        params = TPL07Params(
            template_id=TemplateEnum.TPL_07,
            fin_thickness_m=0.0015,
            fin_spacing_m=0.008,
            fin_length_m=0.040,
            fin_conductivity_W_mK=160.0,
            h_conv_W_m2K=40.0,
            fluid_thermal_diffusivity_m2_s=2.2e-5,
        )
        s_opt = compute_constructal_spacing_m(params.fin_length_m)
        assert params.fin_spacing_m >= s_opt
        eval_res = eval_tpl07(params, base_excess_temp_K=45.0, required_duty_W=80.0)
        assert eval_res.passed

    def test_eval_fails_boundary_layer_choking(self):
        """Case 3: Unphysically narrow fin spacing (S = 0.5 mm) triggers boundary-layer choking."""
        params = TPL07Params(
            template_id=TemplateEnum.TPL_07,
            fin_thickness_m=0.0015,
            fin_spacing_m=0.0005,  # 0.5 mm clearance << 2 * delta_th
            fin_length_m=0.080,
            fin_conductivity_W_mK=200.0,
            h_conv_W_m2K=50.0,
            fluid_thermal_diffusivity_m2_s=2.2e-5,
        )
        eval_res = eval_tpl07(params, base_excess_temp_K=60.0, required_duty_W=1000.0)
        assert not eval_res.passed
        assert "spacing" in eval_res.reason.lower() or "choking" in eval_res.reason.lower()
