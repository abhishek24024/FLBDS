"""flbds/v10/families.py
Four V10 problem families, one per dev cluster:

    F_PCM  TPL_02 phase-change storage           (DEV-M1)
    F_HX   TPL_08 countercurrent exchanger        (DEV-M2)
    F_RAD  TPL_09 radiative cooling               (DEV-M3)
    F_MEM  TPL_10 plastron membrane gas diffusion (DEV-M4)

Each family defines
    env_space     problem/environment parameters (sampled per instance, NEVER from model output)
    design_space  designer-controlled continuous parameters with physical bounds
    constants     documented family constants (fluid/species properties fixed by the family)
    build_params  -> TemplateParameters with EVERY pydantic field set explicitly
    hidden_eval   -> (passed, margins, reason)   uses the existing eval_tplXX exactly like
                     scripts/run_round11_benchmarks.py::evaluate_design_m5_eval (plus capacity bound)
    screen        -> (passed, constraints, reason) uses the existing screen_tplXX + the extra closed-form
                     checks evaluate_m5_screen applies; returns signed normalised per-constraint margins.

Margin convention (signed, normalised; >= 0 means satisfied):
    upper limit  m = (limit - achieved) / scale      scale = |limit| unless given
    lower limit  m = (achieved - required) / scale   scale = |required| unless given

Screen output never contains template ids, acceptable-template lists or hidden-eval values.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from flbds.physics.capacity_bound import check_thermal_storage_capacity
from flbds.physics.tpl02_pcm import (
    compute_composite_properties,
    eval_tpl02,
    screen_tpl02,
)
from flbds.physics.tpl08_countercurrent import (
    compute_axial_conduction_degradation,
    compute_countercurrent_ntu_effectiveness,
    compute_duct_pressure_drop,
    eval_tpl08,
    screen_tpl08,
)
from flbds.physics.tpl09_radiative import (
    SIGMA_SB,
    eval_tpl09,
    screen_tpl09,
    solve_quartic_surface_temperature,
)
from flbds.physics.tpl10_diffusion import (
    compute_bosanquet_effective_diffusivity,
    compute_external_mass_transfer_coeff,
    compute_knudsen_diffusivity,
    eval_tpl10,
    screen_tpl10,
)
from flbds.schema.enums import BoundaryTypeEnum, DuctCrossSectionEnum
from flbds.schema.templates import TPL02Params, TPL08Params, TPL09Params, TPL10Params

Design = dict[str, float]
Env = dict[str, float]
Constraint = dict[str, Any]

MARGIN_FLOOR = -10.0  # margin assigned when a solver raises / value is non-finite

# eval_tpl02's explicit enthalpy solver (N_mesh=100, 30000-step clamp, mesh floor N>=10) violates its own
# CFL condition -- and returns NaN / garbage that can still PASS -- exactly when the effective Fourier number
# Fo = alpha_eff * t_charge / d^2 exceeds 0.45 * 30000 / 10^2 = 135. V10 treats Fo <= 135 as a model-validity
# constraint in BOTH screen and hidden eval (checked before the solver runs). See tests/test_v10_families.py.
PCM_SOLVER_FO_MAX = 0.45 * 30000 / 10**2


@dataclass(frozen=True)
class ParamSpec:
    """A bounded continuous parameter. `log` => sampled/optimised log-uniformly."""

    name: str
    lo: float
    hi: float
    log: bool
    unit: str
    desc: str

    def from_unit(self, u: float) -> float:
        u = float(min(1.0, max(0.0, u)))
        if self.log:
            return float(
                math.exp(
                    math.log(self.lo) + u * (math.log(self.hi) - math.log(self.lo))
                )
            )
        return float(self.lo + u * (self.hi - self.lo))

    def to_unit(self, v: float) -> float:
        v = float(min(self.hi, max(self.lo, v)))
        if self.log:
            return (math.log(v) - math.log(self.lo)) / (
                math.log(self.hi) - math.log(self.lo)
            )
        return (v - self.lo) / (self.hi - self.lo)


def _upper(
    name: str, achieved: float, limit: float, unit: str, scale: float | None = None
) -> Constraint:
    s = scale if scale is not None else abs(limit)
    m = (limit - achieved) / s if s > 0 else 0.0
    return _con(name, achieved, limit, m, "max", unit)


def _lower(
    name: str, achieved: float, required: float, unit: str, scale: float | None = None
) -> Constraint:
    s = scale if scale is not None else abs(required)
    m = (achieved - required) / s if s > 0 else 0.0
    return _con(name, achieved, required, m, "min", unit)


def _con(
    name: str, achieved: float, limit: float, m: float, kind: str, unit: str
) -> Constraint:
    if not np.isfinite(m):
        m = MARGIN_FLOOR
    m = float(max(MARGIN_FLOOR, m))
    return {
        "name": name,
        "kind": kind,
        "unit": unit,
        "achieved": float(achieved) if np.isfinite(achieved) else None,
        "limit": float(limit),
        "margin_normalised": m,
        "status": "PASS" if m >= 0 else "MISS",
    }


@dataclass
class Family:
    """Base class; subclasses implement the physics-specific methods."""

    name: str
    template_id: str
    dev_cluster: str
    env_space: list[ParamSpec]
    design_space: list[ParamSpec]
    constants: dict[str, Any] = field(default_factory=dict)
    system_names: list[str] = field(default_factory=list)

    # ---- generic helpers -------------------------------------------------
    @property
    def design_names(self) -> list[str]:
        return [p.name for p in self.design_space]

    def random_design(self, rng: np.random.Generator) -> Design:
        return {p.name: p.from_unit(float(rng.random())) for p in self.design_space}

    def design_from_unit(self, u: np.ndarray) -> Design:
        return {p.name: p.from_unit(float(x)) for p, x in zip(self.design_space, u)}

    def design_to_unit(self, design: Design) -> np.ndarray:
        return np.array([p.to_unit(float(design[p.name])) for p in self.design_space])

    def clip_design(self, raw: dict[str, Any]) -> tuple[Design, list[str]]:
        """Keep only design fields, clip to bounds. Returns (design, names_clipped_or_missing)."""
        out: Design = {}
        touched: list[str] = []
        for p in self.design_space:
            v = raw.get(p.name)
            try:
                v = float(v)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                v = float("nan")
            if not np.isfinite(v):
                touched.append(p.name)
                v = math.sqrt(p.lo * p.hi) if p.log else 0.5 * (p.lo + p.hi)
            elif v < p.lo or v > p.hi:
                touched.append(p.name)
                v = min(p.hi, max(p.lo, v))
            out[p.name] = v
        return out, touched

    def sample_env(self, rng: np.random.Generator) -> Env:
        return {p.name: p.from_unit(float(rng.random())) for p in self.env_space}

    # ---- to implement ----------------------------------------------------
    def build_params(
        self, design: Design, env: Env
    ) -> Any:  # pragma: no cover - abstract
        raise NotImplementedError

    def screen(
        self, design: Design, env: Env
    ) -> tuple[bool, list[Constraint], str]:  # pragma: no cover
        raise NotImplementedError

    def hidden_eval_constraints(
        self, design: Design, env: Env
    ) -> tuple[bool, list[Constraint], str]:
        raise NotImplementedError  # pragma: no cover

    def cert_objective(self, design: Design, env: Env) -> float:
        """Min hidden-eval margin (override with a cheap surrogate for expensive evals)."""
        _, cons, _ = self.hidden_eval_constraints(design, env)
        return min(c["margin_normalised"] for c in cons) if cons else MARGIN_FLOOR

    def hidden_eval(
        self, design: Design, env: Env
    ) -> tuple[bool, dict[str, float], str]:
        passed, cons, reason = self.hidden_eval_constraints(design, env)
        return passed, {c["name"]: c["margin_normalised"] for c in cons}, reason

    def screen_min_margin(self, design: Design, env: Env) -> float:
        _, cons, _ = self.screen(design, env)
        return min(c["margin_normalised"] for c in cons) if cons else MARGIN_FLOOR

    def problem_statement(self, env: Env, system_name: str) -> str:  # pragma: no cover
        raise NotImplementedError

    def design_field_text(self) -> str:
        return "\n".join(
            f"- {p.name} [{p.unit}] in [{p.lo:.4g}, {p.hi:.4g}]: {p.desc}"
            for p in self.design_space
        )


# =============================================================================
# F_PCM : TPL_02
# =============================================================================
class PCMFamily(Family):
    def sample_env(self, rng: np.random.Generator) -> Env:
        q = float(rng.uniform(100.0, 250.0))
        hours = float(rng.uniform(4.0, 9.0))
        frac = float(rng.uniform(0.9, 1.0))
        return {
            "heat_flux_W_m2": q,
            "charge_hours": hours,
            "required_energy_J_m2": q * hours * 3600.0 * frac,
            "thickness_max_m": float(rng.uniform(0.035, 0.06)),
            "mass_cap_kg_m2": float(rng.uniform(30.0, 60.0)),
            "superheat_limit_K": float(rng.uniform(6.0, 15.0)),
        }

    def build_params(self, design: Design, env: Env) -> TPL02Params:
        return TPL02Params(
            template_id="TPL_02",
            thickness_m=design["thickness_m"],
            pcm_density_kg_m3=design["pcm_density_kg_m3"],
            pcm_latent_heat_J_kg=design["pcm_latent_heat_J_kg"],
            pcm_specific_heat_J_kgK=design["pcm_specific_heat_J_kgK"],
            matrix_volume_fraction=design["matrix_volume_fraction"],
            matrix_density_kg_m3=design["matrix_density_kg_m3"],
            matrix_specific_heat_J_kgK=design["matrix_specific_heat_J_kgK"],
            k_eff_W_mK=design["k_eff_W_mK"],
            melting_temp_degC=self.constants["melting_temp_degC"],
            superheat_limit_K=env["superheat_limit_K"],
            heat_flux_W_m2=env["heat_flux_W_m2"],
            charge_hours=env["charge_hours"],
            required_energy_J_m2=env["required_energy_J_m2"],
        )

    def _closed_forms(self, p: TPL02Params) -> dict[str, float]:
        rho, L, cp, k = compute_composite_properties(p)
        t = p.charge_hours * 3600.0
        x_melt = p.heat_flux_W_m2 * t / (rho * L)
        return {
            "mass": rho * p.thickness_m,
            "latent_capacity": rho * L * p.thickness_m,
            "fo": (k / (rho * cp)) * t / p.thickness_m**2,
            "dT_closed": p.heat_flux_W_m2 * x_melt / k,
            "x_melt": x_melt,
        }

    def screen(self, design: Design, env: Env) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        cf = self._closed_forms(p)
        cons = [
            _upper("areal_mass_kg_m2", cf["mass"], env["mass_cap_kg_m2"], "kg/m2"),
            _upper("thickness_m", p.thickness_m, env["thickness_max_m"], "m"),
            _lower(
                "latent_capacity_J_m2",
                cf["latent_capacity"],
                env["required_energy_J_m2"],
                "J/m2",
            ),
            _lower("effective_fourier_number", cf["fo"], 0.8, "-"),
            _upper(
                "closed_form_surface_superheat_K",
                cf["dT_closed"],
                env["superheat_limit_K"],
                "K",
            ),
            _upper(
                "eval_model_validity_fourier_number", cf["fo"], PCM_SOLVER_FO_MAX, "-"
            ),
        ]
        chk = screen_tpl02(
            p,
            mass_cap_kg_m2=env["mass_cap_kg_m2"],
            thickness_cap_m=env["thickness_max_m"],
        )
        passed = bool(chk.passed)
        if (
            passed and cf["dT_closed"] > env["superheat_limit_K"]
        ):  # evaluate_m5_screen card-limit check
            passed = False
        if cf["fo"] > PCM_SOLVER_FO_MAX:  # V10 validity regime (see PCM_SOLVER_FO_MAX)
            passed = False
        return passed, cons, _summary(passed, cons)

    def _capacity(self, design: Design, env: Env) -> Constraint:
        # Mirrors check_problem_satisfiability for TPL02 params: paraffin bound at min(card cap, thickness).
        res = check_thermal_storage_capacity(
            min(env["thickness_max_m"], design["thickness_m"]),
            env["required_energy_J_m2"],
            material_class="paraffin",
        )
        return _lower(
            "capacity_bound_J_m2",
            res.theoretical_max,
            env["required_energy_J_m2"],
            "J/m2",
        )

    def hidden_eval_constraints(
        self, design: Design, env: Env
    ) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        cf = self._closed_forms(p)
        cap = self._capacity(design, env)
        cons = [
            cap,
            _upper("areal_mass_kg_m2", cf["mass"], env["mass_cap_kg_m2"], "kg/m2"),
            _upper("thickness_m", p.thickness_m, env["thickness_max_m"], "m"),
            _upper(
                "eval_model_validity_fourier_number", cf["fo"], PCM_SOLVER_FO_MAX, "-"
            ),
        ]
        if cap["margin_normalised"] < 0:
            return False, cons, "Capacity bound violated"
        if cf["fo"] > PCM_SOLVER_FO_MAX:
            return (
                False,
                cons,
                f"invalid_regime: Fo_eff={cf['fo']:.1f} > {PCM_SOLVER_FO_MAX:.0f} (eval solver unstable)",
            )
        try:
            res = eval_tpl02(
                p,
                bc_type=BoundaryTypeEnum.BC_FLUX,
                thickness_cap_m=env["thickness_max_m"],
                mass_cap_kg_m2=env["mass_cap_kg_m2"],
            )
        except Exception as exc:  # noqa: BLE001 - mirror runner: solver exception = failure
            return False, cons, f"Solver exception: {exc}"
        if "surface_superheat_K" in res.metrics:
            cons.append(
                _upper(
                    "surface_superheat_K",
                    res.metrics["surface_superheat_K"],
                    env["superheat_limit_K"],
                    "K",
                )
            )
            cons.append(
                _upper(
                    "melt_depth_m",
                    res.metrics["melt_depth_m"],
                    p.thickness_m * 1.001,
                    "m",
                )
            )
        if not all(
            np.isfinite(v) for v in res.metrics.values() if isinstance(v, float)
        ):
            return False, cons, "invalid_regime: non-finite eval solver output"
        return bool(res.passed), cons, res.reason

    def cert_objective(self, design: Design, env: Env) -> float:
        """Cheap surrogate of the hidden eval (the 1-D Stefan solver costs ~0.15 s)."""
        p = self.build_params(design, env)
        cf = self._closed_forms(p)
        cons = [
            self._capacity(design, env),
            _upper("m", cf["mass"], env["mass_cap_kg_m2"], ""),
            _upper("t", p.thickness_m, env["thickness_max_m"], ""),
            _upper("dT", cf["dT_closed"], env["superheat_limit_K"], ""),
            _upper("x", cf["x_melt"], p.thickness_m, ""),
            _upper("fo", cf["fo"], PCM_SOLVER_FO_MAX, ""),
        ]
        return min(c["margin_normalised"] for c in cons)

    def problem_statement(self, env: Env, system_name: str) -> str:
        return (
            f"Target system: {system_name}\n"
            "Required function: passively buffer the interior against an intense daytime solar heat load by "
            "absorbing and storing the incident heat in a thin wall layer during the charging period, "
            "keeping the exposed surface temperature rise small, and releasing it later.\n"
            "Environment / operating conditions:\n"
            f"- absorbed heat flux on the exposed face: {env['heat_flux_W_m2']:.1f} W/m^2 (constant)\n"
            f"- charging duration: {env['charge_hours']:.2f} h\n"
            f"- energy that must be stored per unit area: {env['required_energy_J_m2'] / 1e6:.3f} MJ/m^2\n"
            "Hard constraints:\n"
            f"- layer thickness <= {env['thickness_max_m'] * 1e3:.1f} mm\n"
            f"- areal mass <= {env['mass_cap_kg_m2']:.1f} kg/m^2\n"
            f"- end-of-charge surface temperature rise above the storage transition temperature "
            f"<= {env['superheat_limit_K']:.1f} K\n"
        )


# =============================================================================
# F_HX : TPL_08
# =============================================================================
class HXFamily(Family):
    def sample_env(self, rng: np.random.Generator) -> Env:
        t_cold = float(rng.uniform(5.0, 25.0))
        dt_in = float(rng.uniform(15.0, 40.0))
        dp = float(math.exp(rng.uniform(math.log(150.0), math.log(1500.0))))
        return {
            "required_duty_W": float(
                math.exp(rng.uniform(math.log(250.0), math.log(4000.0)))
            ),
            "T_cold_in_degC": t_cold,
            "T_hot_in_degC": t_cold + dt_in,
            "max_pressure_drop_Pa": dp,
            "length_cap_m": float(rng.uniform(0.5, 1.5)),
        }

    def build_params(self, design: Design, env: Env) -> TPL08Params:
        c = self.constants
        dp = env["max_pressure_drop_Pa"]
        return TPL08Params(
            template_id="TPL_08",
            duct_type=c["duct_type"],
            mass_flow_rate_kg_s=None,  # explicit: per-stream flows below are authoritative
            m_dot_hot_kg_s=design["m_dot_hot_kg_s"],
            m_dot_cold_kg_s=design["m_dot_cold_kg_s"],
            c_p_J_kgK=c["cp_J_kgK"],
            cp_hot_J_kgK=c["cp_J_kgK"],
            cp_cold_J_kgK=c["cp_J_kgK"],
            u_overall_W_m2K=design["overall_U_W_m2K"],
            overall_U_W_m2K=design["overall_U_W_m2K"],
            exchange_area_m2=design["heat_transfer_area_m2"],
            heat_transfer_area_m2=design["heat_transfer_area_m2"],
            duct_length_m=design["length_m"],
            length_m=design["length_m"],
            hydraulic_diameter_m=design["hydraulic_diameter_m"],
            fluid_viscosity_Pa_s=c["fluid_viscosity_Pa_s"],
            fluid_density_kg_m3=c["fluid_density_kg_m3"],
            pressure_drop_cap_Pa=dp,
            max_pressure_drop_Pa=dp,
            T_hot_in_degC=env["T_hot_in_degC"],
            T_cold_in_degC=env["T_cold_in_degC"],
            required_duty_W=env["required_duty_W"],
            wall_conductivity_W_mK=design["wall_conductivity_W_mK"],
            wall_cross_section_m2=design["wall_cross_section_m2"],
        )

    @staticmethod
    def _thermo(p: TPL08Params) -> dict[str, float]:
        c_hot = p.m_dot_hot_kg_s * p.cp_hot_J_kgK
        c_cold = p.m_dot_cold_kg_s * p.cp_cold_J_kgK
        c_min, c_max = min(c_hot, c_cold), max(c_hot, c_cold)
        cr = c_min / c_max
        ntu = p.overall_U_W_m2K * p.heat_transfer_area_m2 / c_min
        eps = compute_countercurrent_ntu_effectiveness(ntu, cr)
        lam = p.wall_conductivity_W_mK * p.wall_cross_section_m2 / (p.length_m * c_min)
        eps_deg = compute_axial_conduction_degradation(eps, cr, lam)
        q_max = c_min * (p.T_hot_in_degC - p.T_cold_in_degC)
        if p.duct_type == DuctCrossSectionEnum.CIRCULAR:
            a_flow = math.pi * p.hydraulic_diameter_m**2 / 4.0
        else:
            a_flow = p.hydraulic_diameter_m**2
        v = p.m_dot_cold_kg_s / (p.fluid_density_kg_m3 * a_flow)
        _, _, dp = compute_duct_pressure_drop(
            L=p.length_m,
            D_h=p.hydraulic_diameter_m,
            rho=p.fluid_density_kg_m3,
            mu=p.fluid_viscosity_Pa_s,
            velocity=v,
            cross_section=p.duct_type,
        )
        return {"duty_ideal": eps * q_max, "duty_degraded": eps_deg * q_max, "dp": dp}

    def screen(self, design: Design, env: Env) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        th = self._thermo(p)
        cons = [
            _upper("length_m", p.length_m, env["length_cap_m"], "m"),
            _lower(
                "ideal_effectiveness_NTU_duty_W",
                th["duty_ideal"],
                env["required_duty_W"],
                "W",
            ),
            _upper(
                "closed_form_pressure_drop_Pa",
                th["dp"],
                env["max_pressure_drop_Pa"],
                "Pa",
            ),
        ]
        chk = screen_tpl08(p, length_cap_m=env["length_cap_m"])
        passed = bool(chk.passed) and th["dp"] <= env["max_pressure_drop_Pa"]
        return passed, cons, _summary(passed, cons)

    def hidden_eval_constraints(
        self, design: Design, env: Env
    ) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        th = self._thermo(p)
        cons = [
            _upper("length_m", p.length_m, env["length_cap_m"], "m"),
            _lower("degraded_duty_W", th["duty_degraded"], env["required_duty_W"], "W"),
            _upper("pressure_drop_Pa", th["dp"], env["max_pressure_drop_Pa"], "Pa"),
        ]
        # capacity bound (check_problem_satisfiability) is a no-op for TPL_08 params.
        try:
            res = eval_tpl08(p, length_cap_m=env["length_cap_m"])
        except Exception as exc:  # noqa: BLE001
            return False, cons, f"Solver exception: {exc}"
        return bool(res.passed), cons, res.reason

    def problem_statement(self, env: Env, system_name: str) -> str:
        return (
            f"Target system: {system_name}\n"
            "Required function: recover heat from a hot liquid supply loop into a cold liquid return loop "
            "(both streams water) inside a compact passive core, delivering the required thermal duty.\n"
            "Environment / operating conditions:\n"
            f"- hot stream inlet temperature: {env['T_hot_in_degC']:.1f} degC\n"
            f"- cold stream inlet temperature: {env['T_cold_in_degC']:.1f} degC\n"
            f"- required heat transfer duty: {env['required_duty_W']:.1f} W\n"
            "- working fluid: liquid water on both sides (cp 4184 J/(kg K), density 1000 kg/m^3, "
            "viscosity 1.0e-3 Pa s), circular channels\n"
            "Hard constraints:\n"
            f"- channel pressure drop <= {env['max_pressure_drop_Pa']:.1f} Pa\n"
            f"- core/channel length <= {env['length_cap_m']:.3f} m\n"
        )


# =============================================================================
# F_RAD : TPL_09
# =============================================================================
class RADFamily(Family):
    def sample_env(self, rng: np.random.Generator) -> Env:
        t_amb = float(rng.uniform(30.0, 47.0))
        h = float(rng.uniform(5.0, 12.0))
        s = float(rng.uniform(700.0, 1000.0))
        return {
            "solar_irradiance_W_m2": s,
            "T_ambient_degC": t_amb,
            "T_sky_degC": t_amb - float(rng.uniform(20.0, 35.0)),
            "T_inner_degC": t_amb - float(rng.uniform(3.0, 15.0)),
            "h_conv_W_m2K": h,
            "max_inner_leakage_W_m2": float(
                math.exp(rng.uniform(math.log(15.0), math.log(60.0)))
            ),
            "required_net_cooling_W_m2": float(rng.uniform(0.0, 60.0)),
            "thickness_max_m": float(rng.uniform(0.03, 0.06)),
            "mass_cap_kg_m2": float(rng.uniform(10.0, 30.0)),
        }

    def build_params(self, design: Design, env: Env) -> TPL09Params:
        e, a = design["surface_emissivity"], design["solar_absorptivity"]
        d, k = design["substrate_thickness_m"], design["substrate_k_W_mK"]
        return TPL09Params(
            template_id="TPL_09",
            surface_emissivity=e,
            emissivity_thermal=e,
            solar_absorptivity=a,
            absorptivity_solar=a,
            h_conv_ambient_W_m2K=env["h_conv_W_m2K"],
            h_conv_W_m2K=env["h_conv_W_m2K"],
            t_ambient_K=env["T_ambient_degC"] + 273.15,
            T_ambient_degC=env["T_ambient_degC"],
            t_sky_K=env["T_sky_degC"] + 273.15,
            T_sky_degC=env["T_sky_degC"],
            q_solar_W_m2=env["solar_irradiance_W_m2"],
            solar_irradiance_W_m2=env["solar_irradiance_W_m2"],
            thickness_m=d,
            substrate_thickness_m=d,
            thermal_conductivity_W_mK=k,
            substrate_k_W_mK=k,
            substrate_density_kg_m3=design["substrate_density_kg_m3"],
            T_inner_degC=env["T_inner_degC"],
            max_inner_leakage_W_m2=env["max_inner_leakage_W_m2"],
            required_net_cooling_W_m2=env["required_net_cooling_W_m2"],
        )

    def screen(self, design: Design, env: Env) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        t_amb, t_sky = p.T_ambient_degC + 273.15, p.T_sky_degC + 273.15
        p_net = (
            p.emissivity_thermal * SIGMA_SB * (t_amb**4 - t_sky**4)
            - p.absorptivity_solar * p.solar_irradiance_W_m2
        )
        cons = [
            _upper(
                "substrate_thickness_m",
                p.substrate_thickness_m,
                env["thickness_max_m"],
                "m",
            ),
            _upper(
                "areal_mass_kg_m2",
                p.substrate_density_kg_m3 * p.substrate_thickness_m,
                env["mass_cap_kg_m2"],
                "kg/m2",
            ),
            _lower(
                "lumped_net_radiative_cooling_W_m2",
                p_net,
                env["required_net_cooling_W_m2"],
                "W/m2",
                scale=max(
                    abs(env["required_net_cooling_W_m2"]),
                    self.constants["net_cooling_scale_W_m2"],
                ),
            ),
        ]
        chk = screen_tpl09(
            p,
            mass_cap_kg_m2=env["mass_cap_kg_m2"],
            thickness_cap_m=env["thickness_max_m"],
        )
        return bool(chk.passed), cons, _summary(bool(chk.passed), cons)

    def hidden_eval_constraints(
        self, design: Design, env: Env
    ) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        cons = [
            _upper(
                "substrate_thickness_m",
                p.substrate_thickness_m,
                env["thickness_max_m"],
                "m",
            ),
            _upper(
                "areal_mass_kg_m2",
                p.substrate_density_kg_m3 * p.substrate_thickness_m,
                env["mass_cap_kg_m2"],
                "kg/m2",
            ),
        ]
        try:
            _, _, _, q_leak = solve_quartic_surface_temperature(
                q_solar=p.solar_irradiance_W_m2,
                alpha_solar=p.absorptivity_solar,
                epsilon_surf=p.emissivity_thermal,
                epsilon_sky=p.emissivity_thermal,
                T_sky_K=p.T_sky_degC + 273.15,
                T_amb_K=p.T_ambient_degC + 273.15,
                h_conv=p.h_conv_W_m2K,
                k_substrate=p.substrate_k_W_mK,
                d_substrate=p.substrate_thickness_m,
                T_inner_K=p.T_inner_degC + 273.15,
            )
            cons.append(
                _upper(
                    "inner_leakage_W_m2", q_leak, env["max_inner_leakage_W_m2"], "W/m2"
                )
            )
        except Exception:  # noqa: BLE001
            cons.append(
                _con(
                    "inner_leakage_W_m2",
                    float("nan"),
                    env["max_inner_leakage_W_m2"],
                    MARGIN_FLOOR,
                    "max",
                    "W/m2",
                )
            )
        try:
            res = eval_tpl09(
                p,
                mass_cap_kg_m2=env["mass_cap_kg_m2"],
                thickness_cap_m=env["thickness_max_m"],
            )
        except Exception as exc:  # noqa: BLE001
            return False, cons, f"Solver exception: {exc}"
        return bool(res.passed), cons, res.reason

    def problem_statement(self, env: Env, system_name: str) -> str:
        return (
            f"Target system: {system_name}\n"
            "Required function: keep an enclosure roof skin cool under full sun without consuming power, "
            "shedding heat to the cold sky while limiting heat conducted into the interior.\n"
            "Environment / operating conditions:\n"
            f"- incident solar irradiance: {env['solar_irradiance_W_m2']:.1f} W/m^2\n"
            f"- ambient air temperature: {env['T_ambient_degC']:.1f} degC\n"
            f"- effective sky temperature: {env['T_sky_degC']:.1f} degC\n"
            f"- interior temperature: {env['T_inner_degC']:.1f} degC\n"
            f"- outdoor convective coefficient: {env['h_conv_W_m2K']:.1f} W/(m^2 K)\n"
            "Hard constraints:\n"
            f"- net cooling power at ambient temperature >= {env['required_net_cooling_W_m2']:.1f} W/m^2\n"
            f"- conductive heat leakage into the interior <= {env['max_inner_leakage_W_m2']:.1f} W/m^2\n"
            f"- panel/substrate thickness <= {env['thickness_max_m'] * 1e3:.1f} mm\n"
            f"- areal mass <= {env['mass_cap_kg_m2']:.1f} kg/m^2\n"
        )


# =============================================================================
# F_MEM : TPL_10
# =============================================================================
class MEMFamily(Family):
    def sample_env(self, rng: np.random.Generator) -> Env:
        lu = lambda lo, hi: float(math.exp(rng.uniform(math.log(lo), math.log(hi))))
        return {
            "required_flux_mol_m2_s": lu(0.0025, 0.016),
            "min_pore_diameter_m": lu(15e-9, 50e-9),
            "hydrostatic_head_m": lu(1.5, 120.0),
            "delta_concentration_mol_m3": float(rng.uniform(2.0, 8.0)),
        }

    def build_params(self, design: Design, env: Env) -> TPL10Params:
        c = self.constants
        d = design["pore_diameter_m"]
        return TPL10Params(
            template_id="TPL_10",
            membrane_thickness_m=design["membrane_thickness_m"],
            porosity=design["porosity"],
            mean_pore_radius_m=d / 2.0,
            pore_diameter_m=d,
            min_pore_diameter_m=env["min_pore_diameter_m"],
            hydrostatic_head_m=env["hydrostatic_head_m"],
            surface_tension_N_m=c["surface_tension_N_m"],
            contact_angle_deg=design["contact_angle_deg"],
            tortuosity=design["tortuosity"],
            species_diffusivity_m2_s=c["molecular_diffusivity_m2_s"],
            molecular_diffusivity_m2_s=c["molecular_diffusivity_m2_s"],
            molecular_mass_kg_mol=c["molar_mass_kg_mol"],
            molar_mass_kg_mol=c["molar_mass_kg_mol"],
            temperature_K=c["temperature_degC"] + 273.15,
            temperature_degC=c["temperature_degC"],
            delta_concentration_mol_m3=env["delta_concentration_mol_m3"],
            required_flux_mol_m2_s=env["required_flux_mol_m2_s"],
        )

    @staticmethod
    def _diff(p: TPL10Params) -> dict[str, float]:
        t_k = p.temperature_degC + 273.15
        d_kn = compute_knudsen_diffusivity(p.pore_diameter_m, t_k, p.molar_mass_kg_mol)
        _, d_eff = compute_bosanquet_effective_diffusivity(
            p.molecular_diffusivity_m2_s, d_kn, p.porosity, p.tortuosity
        )
        cos_t = max(0.0, -math.cos(math.radians(p.contact_angle_deg)))
        h_break = (4.0 * p.surface_tension_N_m * cos_t / p.pore_diameter_m) / (
            1000.0 * 9.81
        )
        L = p.membrane_thickness_m
        k_c = compute_external_mass_transfer_coeff(
            p.molecular_diffusivity_m2_s, 0.05, 1.0
        )
        r_tot = (L / d_eff if d_eff > 0 else float("inf")) + 1.0 / k_c
        return {
            "fo": d_eff * 3600.0 / L**2,
            "j_screen": d_eff * p.delta_concentration_mol_m3 / L,
            "j_coupled": p.delta_concentration_mol_m3 / r_tot,
            "h_break": h_break,
        }

    def screen(self, design: Design, env: Env) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        df = self._diff(p)
        cons = [
            _lower("mass_fourier_number", df["fo"], 1.0, "-"),
            _lower(
                "uncoupled_fickian_flux_mol_m2_s",
                df["j_screen"],
                env["required_flux_mol_m2_s"],
                "mol/(m2 s)",
            ),
            _lower(
                "pore_diameter_m", p.pore_diameter_m, env["min_pore_diameter_m"], "m"
            ),
            _lower(
                "capillary_breakthrough_head_m",
                df["h_break"],
                env["hydrostatic_head_m"],
                "m",
            ),
        ]
        chk = screen_tpl10(p)
        passed = (
            bool(chk.passed)
            and p.pore_diameter_m >= env["min_pore_diameter_m"]
            and env["hydrostatic_head_m"] <= df["h_break"]
        )
        return passed, cons, _summary(passed, cons)

    def hidden_eval_constraints(
        self, design: Design, env: Env
    ) -> tuple[bool, list[Constraint], str]:
        p = self.build_params(design, env)
        df = self._diff(p)
        cons = [
            _lower(
                "pore_diameter_m", p.pore_diameter_m, env["min_pore_diameter_m"], "m"
            ),
            _lower(
                "capillary_breakthrough_head_m",
                df["h_break"],
                env["hydrostatic_head_m"],
                "m",
            ),
            _lower(
                "coupled_flux_mol_m2_s",
                df["j_coupled"],
                env["required_flux_mol_m2_s"],
                "mol/(m2 s)",
            ),
        ]
        try:
            res = eval_tpl10(p, hydrostatic_head_m=env["hydrostatic_head_m"])
        except Exception as exc:  # noqa: BLE001
            return False, cons, f"Solver exception: {exc}"
        return bool(res.passed), cons, res.reason

    def problem_statement(self, env: Env, system_name: str) -> str:
        return (
            f"Target system: {system_name}\n"
            "Required function: passively supply oxygen to a submerged device by gas transport across a stable, "
            "non-flooding gas-liquid interface, without pumps.\n"
            "Environment / operating conditions:\n"
            "- species: oxygen (molar mass 0.032 kg/mol, molecular diffusivity in gas 2.0e-5 m^2/s), 25 degC\n"
            f"- concentration driving difference across the barrier: {env['delta_concentration_mol_m3']:.2f} mol/m^3\n"
            f"- operating hydrostatic water head: {env['hydrostatic_head_m']:.2f} m\n"
            "- external water-side flow ~1 m/s over a 50 mm characteristic length\n"
            "Hard constraints:\n"
            f"- delivered molar flux >= {env['required_flux_mol_m2_s']:.4g} mol/(m^2 s)\n"
            f"- pore diameter >= {env['min_pore_diameter_m'] * 1e9:.1f} nm (anti-fouling clearance)\n"
            "- the interface must not flood (no capillary breakthrough at the operating head)\n"
        )


def _summary(passed: bool, cons: list[Constraint]) -> str:
    if passed:
        return "All screen constraints satisfied."
    missed = [c["name"] for c in cons if c["margin_normalised"] < 0]
    return (
        "Screen constraints missed: " + ", ".join(missed)
        if missed
        else "Screen check failed."
    )


# =============================================================================
# Registry
# =============================================================================
def _build_registry() -> dict[str, Family]:
    pcm = PCMFamily(
        name="F_PCM",
        template_id="TPL_02",
        dev_cluster="DEV-M1",
        env_space=[
            ParamSpec(
                "heat_flux_W_m2",
                100.0,
                250.0,
                False,
                "W/m2",
                "absorbed constant heat flux",
            ),
            ParamSpec("charge_hours", 4.0, 9.0, False, "h", "charging duration"),
            ParamSpec(
                "required_energy_J_m2",
                0.0,
                0.0,
                False,
                "J/m2",
                "derived: q * t * U(0.9, 1.0)",
            ),
            ParamSpec("thickness_max_m", 0.035, 0.06, False, "m", "thickness cap"),
            ParamSpec("mass_cap_kg_m2", 30.0, 60.0, False, "kg/m2", "areal mass cap"),
            ParamSpec(
                "superheat_limit_K",
                6.0,
                15.0,
                False,
                "K",
                "end-of-charge surface superheat cap",
            ),
        ],
        design_space=[
            ParamSpec("thickness_m", 0.003, 0.08, True, "m", "storage layer thickness"),
            ParamSpec(
                "k_eff_W_mK",
                0.15,
                15.0,
                True,
                "W/(m K)",
                "effective thermal conductivity of the composite",
            ),
            ParamSpec(
                "matrix_volume_fraction",
                0.0,
                0.3,
                False,
                "-",
                "volume fraction of conductive matrix/foam",
            ),
            ParamSpec(
                "matrix_density_kg_m3",
                1500.0,
                9000.0,
                True,
                "kg/m3",
                "matrix material density",
            ),
            ParamSpec(
                "matrix_specific_heat_J_kgK",
                380.0,
                1000.0,
                False,
                "J/(kg K)",
                "matrix specific heat",
            ),
            ParamSpec(
                "pcm_density_kg_m3",
                750.0,
                1700.0,
                False,
                "kg/m3",
                "storage material density",
            ),
            ParamSpec(
                "pcm_latent_heat_J_kg",
                120000.0,
                260000.0,
                False,
                "J/kg",
                "storage material latent heat",
            ),
            ParamSpec(
                "pcm_specific_heat_J_kgK",
                1400.0,
                3000.0,
                False,
                "J/(kg K)",
                "storage material specific heat",
            ),
        ],
        constants={"melting_temp_degC": 28.0, "bc_type": "BC_FLUX"},
        system_names=[
            "Biomimetic Architectural Thermal Buffer Facade Panel",
            "Lightweight Rooftop Thermal Buffer Tile",
            "Desert Shelter Wall Heat-Load Damping Liner",
            "Modular Classroom Envelope Thermal Buffer Board",
        ],
    )
    hx = HXFamily(
        name="F_HX",
        template_id="TPL_08",
        dev_cluster="DEV-M2",
        env_space=[
            ParamSpec(
                "required_duty_W", 250.0, 4000.0, True, "W", "required heat duty"
            ),
            ParamSpec(
                "T_cold_in_degC", 5.0, 25.0, False, "degC", "cold inlet temperature"
            ),
            ParamSpec(
                "T_hot_in_degC",
                0.0,
                0.0,
                False,
                "degC",
                "derived: T_cold_in + U(15, 40)",
            ),
            ParamSpec(
                "max_pressure_drop_Pa", 150.0, 1500.0, True, "Pa", "pressure drop cap"
            ),
            ParamSpec("length_cap_m", 0.5, 1.5, False, "m", "length cap"),
        ],
        design_space=[
            ParamSpec(
                "m_dot_hot_kg_s", 0.002, 0.5, True, "kg/s", "hot stream mass flow rate"
            ),
            ParamSpec(
                "m_dot_cold_kg_s",
                0.002,
                0.5,
                True,
                "kg/s",
                "cold stream mass flow rate (per channel)",
            ),
            ParamSpec(
                "overall_U_W_m2K",
                50.0,
                5000.0,
                True,
                "W/(m2 K)",
                "overall heat transfer coefficient",
            ),
            ParamSpec(
                "heat_transfer_area_m2",
                0.01,
                5.0,
                True,
                "m2",
                "heat transfer surface area",
            ),
            ParamSpec("length_m", 0.05, 2.0, True, "m", "channel/core length"),
            ParamSpec(
                "hydraulic_diameter_m",
                0.0005,
                0.05,
                True,
                "m",
                "channel hydraulic diameter",
            ),
            ParamSpec(
                "wall_conductivity_W_mK",
                0.2,
                400.0,
                True,
                "W/(m K)",
                "wall material conductivity",
            ),
            ParamSpec(
                "wall_cross_section_m2",
                1e-6,
                1e-3,
                True,
                "m2",
                "wall axial-conduction cross-section",
            ),
        ],
        constants={
            "duct_type": "circular",
            "cp_J_kgK": 4184.0,
            "fluid_density_kg_m3": 1000.0,
            "fluid_viscosity_Pa_s": 1.0e-3,
        },
        system_names=[
            "Avionics Liquid-Liquid Coolant Heat Recovery Core",
            "Data-Centre Rack Liquid Loop Heat Recuperator",
            "Laboratory Chiller Return-Loop Heat Recovery Unit",
            "Marine Engine-Room Water-to-Water Heat Recuperator",
        ],
    )
    rad = RADFamily(
        name="F_RAD",
        template_id="TPL_09",
        dev_cluster="DEV-M3",
        env_space=[
            ParamSpec(
                "solar_irradiance_W_m2",
                700.0,
                1000.0,
                False,
                "W/m2",
                "solar irradiance",
            ),
            ParamSpec(
                "T_ambient_degC", 30.0, 47.0, False, "degC", "ambient temperature"
            ),
            ParamSpec(
                "T_sky_degC", 0.0, 0.0, False, "degC", "derived: T_amb - U(20, 35)"
            ),
            ParamSpec(
                "T_inner_degC", 0.0, 0.0, False, "degC", "derived: T_amb - U(3, 15)"
            ),
            ParamSpec(
                "h_conv_W_m2K",
                5.0,
                12.0,
                False,
                "W/(m2 K)",
                "outdoor convection coefficient",
            ),
            ParamSpec(
                "max_inner_leakage_W_m2", 15.0, 60.0, True, "W/m2", "inner leakage cap"
            ),
            ParamSpec(
                "required_net_cooling_W_m2",
                0.0,
                60.0,
                False,
                "W/m2",
                "required lumped net cooling",
            ),
            ParamSpec("thickness_max_m", 0.03, 0.06, False, "m", "thickness cap"),
            ParamSpec("mass_cap_kg_m2", 10.0, 30.0, False, "kg/m2", "areal mass cap"),
        ],
        design_space=[
            ParamSpec(
                "surface_emissivity",
                0.05,
                0.98,
                False,
                "-",
                "thermal-infrared emissivity of the outer surface",
            ),
            ParamSpec(
                "solar_absorptivity",
                0.02,
                0.95,
                False,
                "-",
                "solar absorptivity of the outer surface",
            ),
            ParamSpec(
                "substrate_thickness_m",
                0.001,
                0.08,
                True,
                "m",
                "substrate/insulation thickness",
            ),
            ParamSpec(
                "substrate_k_W_mK",
                0.02,
                2.0,
                True,
                "W/(m K)",
                "substrate thermal conductivity",
            ),
            ParamSpec(
                "substrate_density_kg_m3",
                15.0,
                2500.0,
                True,
                "kg/m3",
                "substrate density",
            ),
        ],
        constants={"net_cooling_scale_W_m2": 50.0},
        system_names=[
            "Telecom Cabinet Roof Radiator",
            "Desert Substation Enclosure Cool-Roof Skin",
            "Off-Grid Medicine Store Roof Panel",
            "Battery Container Passive Roof Radiator",
        ],
    )
    mem = MEMFamily(
        name="F_MEM",
        template_id="TPL_10",
        dev_cluster="DEV-M4",
        env_space=[
            ParamSpec(
                "required_flux_mol_m2_s",
                0.0025,
                0.016,
                True,
                "mol/(m2 s)",
                "required molar flux",
            ),
            ParamSpec(
                "min_pore_diameter_m",
                15e-9,
                50e-9,
                True,
                "m",
                "minimum pore diameter (fouling)",
            ),
            ParamSpec("hydrostatic_head_m", 1.5, 120.0, True, "m", "hydrostatic head"),
            ParamSpec(
                "delta_concentration_mol_m3",
                2.0,
                8.0,
                False,
                "mol/m3",
                "concentration driving difference",
            ),
        ],
        design_space=[
            ParamSpec(
                "membrane_thickness_m", 1e-6, 1e-3, True, "m", "membrane thickness"
            ),
            ParamSpec("porosity", 0.05, 0.9, False, "-", "membrane porosity"),
            ParamSpec("pore_diameter_m", 5e-9, 5e-6, True, "m", "mean pore diameter"),
            ParamSpec("tortuosity", 1.0, 5.0, False, "-", "pore tortuosity factor"),
            ParamSpec(
                "contact_angle_deg",
                91.0,
                160.0,
                False,
                "deg",
                "water contact angle of the pore walls",
            ),
        ],
        constants={
            "surface_tension_N_m": 0.072,
            "molecular_diffusivity_m2_s": 2.0e-5,
            "molar_mass_kg_mol": 0.032,
            "temperature_degC": 25.0,
            "external_velocity_m_s": 1.0,
            "char_length_m": 0.05,
        },
        system_names=[
            "Submerged Hydrophobic Microporous Membrane Aerator",
            "Underwater Sensor Passive Oxygen Gill",
            "Aquaculture Tank Passive Gas-Exchange Window",
            "Subsea Instrument Breathing Membrane Patch",
        ],
    )
    return {f.name: f for f in (pcm, hx, rad, mem)}


FAMILIES: dict[str, Family] = _build_registry()
TEMPLATE_TO_FAMILY: dict[str, str] = {f.template_id: f.name for f in FAMILIES.values()}


def get_family(name: str) -> Family:
    try:
        return FAMILIES[name]
    except KeyError as exc:
        raise KeyError(f"Unknown family {name!r}; known: {sorted(FAMILIES)}") from exc


Objective = Callable[[Design, Env], float]
