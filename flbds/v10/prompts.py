"""flbds/v10/prompts.py
Prompt construction for the V10 runner. Prompts are CHAT MESSAGES (list of {"role", "content"}); each
backend applies its tokenizer's chat template, so vLLM and HF transformers see identical conversations.

One call per turn (token-minimal): the model returns a single JSON object
    {"rationale": "<1-2 sentences>", "template_id": "TPL_XX", "design": {<fields of the chosen template>}}
If template_id is not the instance's family template the attempt is a template_choice_error and the
feedback says only that the chosen template's physics cannot deliver the required function.
No acceptable-template list, hidden-eval value or the instance's template id is ever rendered.
"""

from __future__ import annotations

import json
from typing import Any

from flbds.v10.families import FAMILIES, Family

Messages = list[dict[str, str]]

TEMPLATE_IDS = [f"TPL_{i:02d}" for i in range(1, 11)]

# Template descriptions copied from scripts/run_round11_benchmarks.py::AVAILABLE_TEMPLATES.
TEMPLATE_DESC = {
    "TPL_01": "Cyclic sensible thermal storage (conduction, Fourier number Fo in [0.25, 5.0], thermal mass)",
    "TPL_02": "1D solid-liquid phase change thermal storage (enthalpy Stefan PDE, cyclic Robin boundary)",
    "TPL_03": "Evaporative cooling / condensation (latent heat, water budget, boundary layer mass transfer)",
    "TPL_04": "Closed-loop thermochemical sorption storage (LDF kinetics, regeneration temperature)",
    "TPL_05": "Capillary wicking replenishment (Jurin height, Darcy-Washburn flux, pore radius)",
    "TPL_06": "Porous media fluid flow (Darcy / Ergun pressure drop, pumping COP)",
    "TPL_07": "Extended surface pin/straight fin convective dissipation (fin efficiency, Biot < 0.1)",
    "TPL_08": "Countercurrent heat exchange (effectiveness-NTU, pressure drop cap)",
    "TPL_09": "Radiative surface cooling (emissivity, solar reflectance, sky radiation)",
    "TPL_10": "Submerged microporous membrane / plastron gas diffusion (Fickian/Knudsen diffusion flux)",
}

# Design fields of the templates without a V10 family (from the round-11 SCHEMA_SPEC, design-side only).
OTHER_TEMPLATE_FIELDS = {
    "TPL_01": "thickness_m, density_kg_m3, specific_heat_J_kgK, thermal_conductivity_W_mK",
    "TPL_03": "evaporation_rate_kg_m2_s, water_budget_kg_m2, characteristic_length_m",
    "TPL_04": "bulk_density_kg_m3, sorption_density_J_kg, regeneration_temp_degC, ldf_time_constant_s",
    "TPL_05": "lift_height_m, pore_radius_m, permeability_m2, contact_angle_deg",
    "TPL_06": "bed_length_m, bed_porosity, mean_pore_diameter_m, superficial_velocity_m_s",
    "TPL_07": "fin_thickness_m, fin_spacing_m, fin_length_m, fin_conductivity_W_mK",
}

SYSTEM = "You are an expert thermal-fluid physics and engineering design engine."
TEMPLATE_ERROR_FEEDBACK = (
    "The chosen template's physics cannot deliver the required function."
)
FAMILY_ORDER = ["F_PCM", "F_HX", "F_RAD", "F_MEM"]
_TPL_TO_FAM = {f.template_id: f for f in FAMILIES.values()}


def template_catalogue() -> str:
    lines = [
        "Available physics templates and their design fields (SI units as in the field names):"
    ]
    for tid in TEMPLATE_IDS:
        lines.append(f"- {tid}: {TEMPLATE_DESC[tid]}")
        fam = _TPL_TO_FAM.get(tid)
        if fam is not None:
            fields = ", ".join(
                f"{p.name} [{p.lo:.4g}..{p.hi:.4g}]" for p in fam.design_space
            )
        else:
            fields = OTHER_TEMPLATE_FIELDS[tid]
        lines.append(f"    design fields: {fields}")
    return "\n".join(lines)


TEMPLATE_CATALOGUE = template_catalogue()


# ----------------------------------------------------------------------------- biology cards
def _fixture_card(cluster: str) -> str:
    from flbds.m4.fixtures import DEV_FIXTURES

    meta, g = DEV_FIXTURES[cluster]()
    part = g.parts["part_01"].description if "part_01" in g.parts else ""
    organ = g.organs["organ_01"].description if "organ_01" in g.organs else ""
    effect = (
        g.effects["effect_01"].canonical_name.replace("_", " ")
        if "effect_01" in g.effects
        else ""
    )
    phen = g.phenomena["phenom_01"].description if "phenom_01" in g.phenomena else ""
    act = g.actions["action_01"].description if "action_01" in g.actions else ""
    return (
        f"Organism: {meta['organism']}\n"
        f"Mechanism: {g.description}\n"
        f"Structure: {part}; {organ}\n"
        f"Physical effect: {effect}. {phen}\n"
        f"Biological function: {act}"
    )


_BIO_CACHE: dict[str, str] = {}


def bio_card(family: str) -> str:
    """Dev mechanism card (MC-BIO-DEV-M1..M4 fixtures in flbds/m4/fixtures.py) for a family."""
    if family not in _BIO_CACHE:
        _BIO_CACHE[family] = _fixture_card(FAMILIES[family].dev_cluster[:6])
    return _BIO_CACHE[family]


def bio_family_for(instance_family: str, mode: str) -> str | None:
    """mode: none | match | mismatch (deterministic rotation to the next family)."""
    if mode == "none":
        return None
    if mode == "match":
        return instance_family
    if mode == "mismatch":
        i = FAMILY_ORDER.index(instance_family)
        return FAMILY_ORDER[(i + 1) % len(FAMILY_ORDER)]
    raise ValueError(f"unknown bio mode {mode!r}")


# ----------------------------------------------------------------------------- JSON schema (vLLM option)
def design_json_schema(fam: Family, with_bounds: bool = True) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for p in fam.design_space:
        prop: dict[str, Any] = {"type": "number", "description": f"{p.desc} [{p.unit}]"}
        if with_bounds:
            prop["minimum"] = p.lo
            prop["maximum"] = p.hi
        props[p.name] = prop
    return {
        "type": "object",
        "properties": props,
        "required": [p.name for p in fam.design_space],
        "additionalProperties": False,
    }


# ----------------------------------------------------------------------------- feedback rendering
def screen_table(constraints: list[dict[str, Any]]) -> str:
    lines = [
        "| constraint | achieved | limit | normalised margin | status |",
        "|---|---|---|---|---|",
    ]
    for c in constraints:
        ach = "n/a" if c["achieved"] is None else f"{c['achieved']:.4g}"
        bound = "<=" if c["kind"] == "max" else ">="
        lines.append(
            f"| {c['name']} ({c['unit']}) | {ach} | {bound} {c['limit']:.4g} | "
            f"{c['margin_normalised']:+.3f} | {c['status']} |"
        )
    return "\n".join(lines)


def attempt_feedback(att: dict[str, Any]) -> str:
    """Render one attempt (design + screen result) for the feedback prompt."""
    head = f"Chosen template: {att['chosen_template']}\n"
    if att["status"] == "template_choice_error":
        return head + f"Screen verdict: FAIL. {TEMPLATE_ERROR_FEEDBACK}"
    if att["status"] == "schema_failure":
        return (
            head
            + "Screen verdict: FAIL. Invalid design fields: "
            + "; ".join(att.get("errors", []))
        )
    if att["status"] != "ok":
        return (
            head
            + "Screen verdict: FAIL. The response could not be parsed as the required JSON object."
        )
    verdict = "PASS" if att["screen_pass"] else "FAIL"
    return (
        head
        + f"Design: {json.dumps(_round(att['design']))}\n"
        + f"Screen verdict: {verdict} (min normalised margin {att['screen_min_margin']:+.3f})\n"
        + screen_table(att["screen_constraints"])
    )


def _round(d: dict[str, float]) -> dict[str, float]:
    return {k: float(f"{v:.4g}") for k, v in d.items()}


OUTPUT_INSTRUCTION = (
    "Respond with ONLY one JSON object, no other text:\n"
    '{"rationale": "<1-2 sentences>", "template_id": "TPL_XX", "design": {<every design field of the chosen '
    "template as a number in SI units, within the stated bounds>}}\n"
    "Environment/operating values and hard-constraint limits are fixed by the problem; do not include them."
)


def turn_messages(
    inst: dict[str, Any],
    bio_family: str | None,
    history: list[dict[str, Any]],
    top_k: int = 2,
) -> Messages:
    user = (
        "Engineering problem:\n"
        + inst["problem_statement"]
        + "\n"
        + TEMPLATE_CATALOGUE
        + "\n"
    )
    if bio_family is not None:
        user += (
            "\nBiological mechanism card (a biological system that may be relevant as inspiration):\n"
            + bio_card(bio_family)
            + "\n"
        )
    if not history:
        user += (
            "\nTask: choose the physics template that can deliver the required function under the hard "
            "constraints and propose design values that satisfy them.\n"
        )
    else:
        user += (
            "\nYour previous attempt and the screening verifier's result:\n"
            + attempt_feedback(history[-1])
            + "\n"
        )
        scored = [a for a in history if a["status"] == "ok"]
        best = sorted(scored, key=lambda a: -a["screen_min_margin"])[:top_k]
        if best:
            user += f"\nBest {len(best)} designs so far (by minimum screen margin):\n"
            for i, a in enumerate(best, 1):
                user += (
                    f"{i}. {a['chosen_template']} {json.dumps(_round(a['design']))} -> min margin "
                    f"{a['screen_min_margin']:+.3f}\n"
                )
        user += "\nTask: fix the failure (you may switch template) so that every screen constraint passes.\n"
    user += OUTPUT_INSTRUCTION
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def render_qwen(messages: Messages) -> str:
    """Fallback ChatML rendering (used only by tests / backends without a chat template)."""
    s = "".join(
        f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages
    )
    return s + "<|im_start|>assistant\n"
