"""flbds/v10/dev_instances.py
The 12 frozen dev cases as V10 instances (env from DEV_SPECS), for comparison with Round <= 11 results.

DEV_SPECS is COPIED verbatim from scripts/run_round11_benchmarks.py (that module imports vLLM at import
time, so it cannot be imported on CPU-only hosts). Env keys not in DEV_SPECS use the template default the
round-11 runner relied on (F_MEM delta_concentration_mol_m3 = 5.0). No certified design is attached.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flbds.v10.families import FAMILIES

REPO = Path(__file__).resolve().parents[2]

DEV_SPECS: dict[str, dict[str, float]] = {
    "DEV-M1-S1": {"required_energy_J_m2": 4.0e6, "thickness_max_m": 0.05, "mass_cap_kg_m2": 45.0, "superheat_limit_K": 10.0, "heat_flux_W_m2": 150.0, "charge_hours": 8.0},
    "DEV-M1-S2": {"required_energy_J_m2": 5.76e6, "thickness_max_m": 0.05, "mass_cap_kg_m2": 45.0, "superheat_limit_K": 10.0, "heat_flux_W_m2": 200.0, "charge_hours": 8.0},
    "DEV-M1-S3": {"required_energy_J_m2": 3.5e6, "thickness_max_m": 0.04, "mass_cap_kg_m2": 45.0, "superheat_limit_K": 10.0, "heat_flux_W_m2": 200.0, "charge_hours": 4.86},
    "DEV-M2-S1": {"required_duty_W": 500.0, "max_pressure_drop_Pa": 500.0, "pressure_drop_cap_Pa": 500.0, "T_hot_in_degC": 37.0, "T_cold_in_degC": 5.0, "length_cap_m": 1.0},
    "DEV-M2-S2": {"required_duty_W": 2000.0, "max_pressure_drop_Pa": 800.0, "pressure_drop_cap_Pa": 800.0, "T_hot_in_degC": 55.0, "T_cold_in_degC": 20.0, "length_cap_m": 1.0},
    "DEV-M2-S3": {"required_duty_W": 800.0, "max_pressure_drop_Pa": 250.0, "pressure_drop_cap_Pa": 250.0, "T_hot_in_degC": 45.0, "T_cold_in_degC": 15.0, "length_cap_m": 1.0},
    "DEV-M3-S1": {"solar_irradiance_W_m2": 850.0, "q_solar_W_m2": 850.0, "T_ambient_degC": 45.0, "T_sky_degC": 15.0, "T_inner_degC": 40.0, "h_conv_W_m2K": 8.0, "h_conv_ambient_W_m2K": 8.0, "max_inner_leakage_W_m2": 40.0, "required_net_cooling_W_m2": 0.0, "thickness_max_m": 0.05, "mass_cap_kg_m2": 20.0},
    "DEV-M3-S2": {"solar_irradiance_W_m2": 750.0, "q_solar_W_m2": 750.0, "T_ambient_degC": 38.0, "T_sky_degC": 12.0, "T_inner_degC": 27.0, "h_conv_W_m2K": 8.0, "h_conv_ambient_W_m2K": 8.0, "max_inner_leakage_W_m2": 50.0, "required_net_cooling_W_m2": 40.0, "thickness_max_m": 0.05, "mass_cap_kg_m2": 20.0},
    "DEV-M3-S3": {"solar_irradiance_W_m2": 900.0, "q_solar_W_m2": 900.0, "T_ambient_degC": 42.0, "T_sky_degC": 18.0, "T_inner_degC": 35.0, "h_conv_W_m2K": 10.0, "h_conv_ambient_W_m2K": 10.0, "max_inner_leakage_W_m2": 20.0, "required_net_cooling_W_m2": 0.0, "thickness_max_m": 0.05, "mass_cap_kg_m2": 20.0},
    "DEV-M4-S1": {"required_flux_mol_m2_s": 0.005, "min_pore_diameter_m": 20e-9, "hydrostatic_head_m": 2.5},
    "DEV-M4-S2": {"required_flux_mol_m2_s": 0.008, "min_pore_diameter_m": 25e-9, "hydrostatic_head_m": 80.0},
    "DEV-M4-S3": {"required_flux_mol_m2_s": 0.006, "min_pore_diameter_m": 35e-9, "hydrostatic_head_m": 6.0},
}  # fmt: skip

CLUSTER_TO_FAMILY = {f.dev_cluster: name for name, f in FAMILIES.items()}
ENV_DEFAULTS = {"F_MEM": {"delta_concentration_mol_m3": 5.0}}


def _system_name(cid: str) -> str:
    p = REPO / "flbds/benchmark/dev" / cid / "problem_card.json"
    try:
        return json.loads(p.read_text())["system"]["name"]
    except Exception:  # noqa: BLE001
        return f"Dev case {cid}"


def build_dev_instances() -> list[dict[str, Any]]:
    out = []
    for cid, spec in DEV_SPECS.items():
        fname = CLUSTER_TO_FAMILY[cid[:6]]
        fam = FAMILIES[fname]
        env_keys = [p.name for p in fam.env_space]
        env = {
            **ENV_DEFAULTS.get(fname, {}),
            **{k: float(v) for k, v in spec.items() if k in env_keys},
        }
        missing = set(env_keys) - set(env)
        if missing:
            raise ValueError(f"{cid}: env keys missing {missing}")
        name = _system_name(cid)
        out.append(
            {
                "instance_id": cid,
                "family": fname,
                "template_id": fam.template_id,
                "dev_cluster": cid[:6],
                "system_name": name,
                "env": env,
                "problem_statement": fam.problem_statement(env, name),
                "certified_design": None,
                "certified_min_margin": None,
                "trivial_pass_rate": None,
            }
        )
    return out
