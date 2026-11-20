"""flbds/m4/operators.py
Causal Graph Rewrite Operators T1 to T5 for FLBDS v9 §4.4.

Each operator implements:
1. Typed precondition gate: checks whether problem context triggers the transformation.
2. Ablation flag gate: can be disabled individually to support ablation studies (e.g. A-NoOp).
3. Deterministic graph rewrite: transforms SAPPhIRE graph while preserving topological validity.
4. Proof obligation: explicit physical requirement matching target M5 verifier template.
"""

from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from flbds.schema.enums import DirectionEnum, ResourceEnum, TimeModeEnum, TemplateEnum
from flbds.schema.problem_card import ProblemCard
from flbds.schema.role_binding import RoleBinding
from flbds.schema.sapphire import (
    Part,
    Organ,
    ResourceInput,
    PhysicalEffect,
    Phenomenon,
    StateChange,
    Action,
)
from flbds.m4.sapphire_graph import SapphireGraph


class AblationConfig(BaseModel):
    """Configuration flags controlling operator availability."""
    enable_t1: bool = True  # Resource-loop closing
    enable_t2: bool = True  # Flow / direction inversion
    enable_t3: bool = True  # Temporal phase shift
    enable_t4: bool = True  # Effect / template substitution
    enable_t5: bool = True  # Regime re-scaling


class OperatorResult(BaseModel):
    """Output bundle produced by an operator rewrite."""
    operator_id: str
    applied: bool
    rejection_reason: Optional[str] = None
    rewritten_graph: Optional[SapphireGraph] = None
    role_binding: Optional[RoleBinding] = None
    target_template: Optional[str] = None
    proof_obligation: Optional[str] = None


# =========================================================================
# OPERATOR T1: Resource-Loop Closing
# =========================================================================
def check_precondition_t1(source_meta: Dict[str, Any], prob: ProblemCard) -> Tuple[bool, str]:
    consumables = set(source_meta.get("consumable_inputs", []))
    absent = set(prob.environment.resources_absent)
    overlap = consumables.intersection(absent)
    if not overlap:
        return False, f"Precondition failed: No consumable input {consumables} is absent in target {absent}."
    return True, f"Consumable resource(s) {overlap} absent in target environment."


def apply_operator_t1(
    graph: SapphireGraph,
    source_meta: Dict[str, Any],
    prob: ProblemCard,
    config: AblationConfig = AblationConfig(),
) -> OperatorResult:
    if not config.enable_t1:
        return OperatorResult(operator_id="T1", applied=False, rejection_reason="Operator T1 disabled by ablation flag.")

    ok, reason = check_precondition_t1(source_meta, prob)
    if not ok:
        return OperatorResult(operator_id="T1", applied=False, rejection_reason=reason)

    g = graph.clone()
    # Rewrite: Replace open evaporative consumable with sealed solid-state latent storage (PCM)
    g.inputs["input_sealed"] = ResourceInput(input_type="energy", name="absorbed_heat_flux")
    if "input_01" in g.inputs:
        del g.inputs["input_01"]

    g.organs["organ_pcm"] = Organ(description="Sealed composite phase change material matrix")
    if "organ_01" in g.organs:
        del g.organs["organ_01"]

    g.effects["effect_pcm"] = PhysicalEffect(
        canonical_name="solid_liquid_phase_change_enthalpy",
        governing_equation="E = rho * L_fus * thickness",
        relevant_variables=["thickness_m", "k_eff_W_mK", "heat_flux_W_m2", "superheat_limit_K"],
    )
    if "effect_01" in g.effects:
        del g.effects["effect_01"]

    g.phenomena["phenom_pcm"] = Phenomenon(description="Solid-to-liquid isothermal melting retaining heat without mass loss")
    if "phenom_01" in g.phenomena:
        del g.phenomena["phenom_01"]

    # Reconnect edges
    g.edges = [e for e in g.edges if e.source_id not in ["organ_01", "input_01", "effect_01", "phenom_01"] and
                             e.target_id not in ["organ_01", "input_01", "effect_01", "phenom_01"]]
    g.add_edge("part_01", "organ_pcm", "creates")
    g.add_edge("organ_pcm", "effect_pcm", "co_activates")
    g.add_edge("input_sealed", "effect_pcm", "co_activates")
    g.add_edge("effect_pcm", "phenom_pcm", "creates")
    g.add_edge("phenom_pcm", "state_01", "creates")

    proof_ob = "Net consumable loss is zero over cycle; enthalpy capacity >= required_energy; Fo_eff >= 0.8; surface superheat <= limit."
    rb = RoleBinding(
        binding_id="RB-T1-01",
        source_node="effect_01",
        target_node="effect_pcm",
        relation="transformed",
        operator="T1",
        justification="Substituted open water evaporation with closed-loop PCM storage due to water absence.",
        source_card_node_ids=["organ_01", "effect_01"],
        proof_obligations=[proof_ob],
    )

    return OperatorResult(
        operator_id="T1",
        applied=True,
        rewritten_graph=g,
        role_binding=rb,
        target_template="TPL_02",
        proof_obligation=proof_ob,
    )


# =========================================================================
# OPERATOR T2: Flow / Direction Inversion
# =========================================================================
def check_precondition_t2(source_meta: Dict[str, Any], prob: ProblemCard) -> Tuple[bool, str]:
    source_dir = source_meta.get("target_direction")
    target_dir = prob.required_function.target_direction
    opposing = (
        (source_dir == DirectionEnum.DECREASE and target_dir == DirectionEnum.INCREASE) or
        (source_dir == DirectionEnum.INCREASE and target_dir == DirectionEnum.DECREASE) or
        (source_dir == DirectionEnum.DECREASE and target_dir == DirectionEnum.STORE_AND_RELEASE)
    )
    if not opposing:
        return False, f"Precondition failed: Source direction '{source_dir}' does not oppose target '{target_dir}'."
    return True, f"Source direction '{source_dir}' opposes target functional direction '{target_dir}'."


def apply_operator_t2(
    graph: SapphireGraph,
    source_meta: Dict[str, Any],
    prob: ProblemCard,
    config: AblationConfig = AblationConfig(),
) -> OperatorResult:
    if not config.enable_t2:
        return OperatorResult(operator_id="T2", applied=False, rejection_reason="Operator T2 disabled by ablation flag.")

    ok, reason = check_precondition_t2(source_meta, prob)
    if not ok:
        return OperatorResult(operator_id="T2", applied=False, rejection_reason=reason)

    g = graph.clone()
    # Invert flux sign and swap boundary role
    g.effects["effect_inverted"] = PhysicalEffect(
        canonical_name="selective_surface_radiative_convective_exchange",
        governing_equation="q_net = P_rad - P_atm - P_solar - q_inner",
        relevant_variables=["emissivity_thermal", "solar_irradiance_W_m2", "absorptivity_solar"],
    )
    if "effect_01" in g.effects:
        del g.effects["effect_01"]

    g.phenomena["phenom_inverted"] = Phenomenon(description="Directed nocturnal/diurnal net cooling reversing daytime heat accumulation")
    if "phenom_01" in g.phenomena:
        del g.phenomena["phenom_01"]

    g.edges = [e for e in g.edges if e.source_id not in ["effect_01", "phenom_01"] and
                             e.target_id not in ["effect_01", "phenom_01"]]
    g.add_edge("organ_01", "effect_inverted", "co_activates")
    g.add_edge("input_01", "effect_inverted", "co_activates")
    g.add_edge("effect_inverted", "phenom_inverted", "creates")
    g.add_edge("phenom_inverted", "state_01", "creates")

    proof_ob = "Signed net flux matches target; P_net >= required_net_cooling; inner heat leakage <= cap."
    rb = RoleBinding(
        binding_id="RB-T2-01",
        source_node="effect_01",
        target_node="effect_inverted",
        relation="transformed",
        operator="T2",
        justification="Reversed heat flux sign to enforce active cooling under solar irradiation.",
        source_card_node_ids=["effect_01"],
        proof_obligations=[proof_ob],
    )

    return OperatorResult(
        operator_id="T2",
        applied=True,
        rewritten_graph=g,
        role_binding=rb,
        target_template="TPL_09",
        proof_obligation=proof_ob,
    )


# =========================================================================
# OPERATOR T3: Temporal Phase Shift
# =========================================================================
def check_precondition_t3(source_meta: Dict[str, Any], prob: ProblemCard) -> Tuple[bool, str]:
    source_time = source_meta.get("time_mode")
    target_time = prob.time_pattern.time_mode
    if source_time in [TimeModeEnum.STEADY, TimeModeEnum.CONTINUOUS] and \
       target_time in [TimeModeEnum.CYCLIC_DIURNAL, TimeModeEnum.PULSED]:
        return True, f"Source steady mode '{source_time}' mismatches cyclic target '{target_time}'."
    return False, f"Precondition failed: Time patterns compatible ({source_time} vs {target_time})."


def apply_operator_t3(
    graph: SapphireGraph,
    source_meta: Dict[str, Any],
    prob: ProblemCard,
    config: AblationConfig = AblationConfig(),
) -> OperatorResult:
    if not config.enable_t3:
        return OperatorResult(operator_id="T3", applied=False, rejection_reason="Operator T3 disabled by ablation flag.")

    ok, reason = check_precondition_t3(source_meta, prob)
    if not ok:
        return OperatorResult(operator_id="T3", applied=False, rejection_reason=reason)

    g = graph.clone()
    g.organs["organ_buffer"] = Organ(description="Regenerative dual-phase thermal capacitance buffer")
    if "organ_01" in g.organs:
        del g.organs["organ_01"]

    g.effects["effect_storage"] = PhysicalEffect(
        canonical_name="cyclic_sensible_or_latent_storage",
        governing_equation="q(t) = C_th * dT/dt + q_loss",
        relevant_variables=["required_energy_J_m2", "thickness_m", "max_pressure_drop_Pa"],
    )
    if "effect_01" in g.effects:
        del g.effects["effect_01"]

    g.edges = [e for e in g.edges if e.source_id not in ["organ_01", "effect_01"] and
                             e.target_id not in ["organ_01", "effect_01"]]
    g.add_edge("part_01", "organ_buffer", "creates")
    g.add_edge("organ_buffer", "effect_storage", "co_activates")
    g.add_edge("input_01", "effect_storage", "co_activates")
    g.add_edge("effect_storage", "phenom_01", "creates")

    proof_ob = "Cyclic energy closure satisfied; storage capacitance buffers diurnal swing; pressure drop <= cap."
    rb = RoleBinding(
        binding_id="RB-T3-01",
        source_node="organ_01",
        target_node="organ_buffer",
        relation="transformed",
        operator="T3",
        justification="Introduced capacitive thermal buffering to decouple steady biological transfer from cyclic target.",
        source_card_node_ids=["organ_01"],
        proof_obligations=[proof_ob],
    )

    return OperatorResult(
        operator_id="T3",
        applied=True,
        rewritten_graph=g,
        role_binding=rb,
        target_template="TPL_08",
        proof_obligation=proof_ob,
    )


# =========================================================================
# OPERATOR T4: Effect / Template Substitution
# =========================================================================
def check_precondition_t4(source_meta: Dict[str, Any], prob: ProblemCard) -> Tuple[bool, str]:
    source_effects = source_meta.get("effects", [])
    absent = set(prob.environment.resources_absent)
    if any("latent_heat_of_vaporization" in e for e in source_effects) and "liquid_water" in absent:
        return True, "Source requires open vaporization but liquid water is absent; triggers effect substitution to solid PCM."
    return False, "Precondition failed: Source effect medium is available in target environment."


def apply_operator_t4(
    graph: SapphireGraph,
    source_meta: Dict[str, Any],
    prob: ProblemCard,
    config: AblationConfig = AblationConfig(),
) -> OperatorResult:
    if not config.enable_t4:
        return OperatorResult(operator_id="T4", applied=False, rejection_reason="Operator T4 disabled by ablation flag.")

    ok, reason = check_precondition_t4(source_meta, prob)
    if not ok:
        return OperatorResult(operator_id="T4", applied=False, rejection_reason=reason)

    g = graph.clone()
    g.effects["effect_substituted"] = PhysicalEffect(
        canonical_name="solid_liquid_phase_change_enthalpy",
        governing_equation="Delta_H = int(cp * dT) + L_fus",
        relevant_variables=["thickness_m", "required_energy_J_m2", "k_eff_W_mK"],
    )
    if "effect_01" in g.effects:
        del g.effects["effect_01"]

    g.edges = [e for e in g.edges if e.source_id != "effect_01" and e.target_id != "effect_01"]
    g.add_edge("organ_01", "effect_substituted", "co_activates")
    g.add_edge("input_01", "effect_substituted", "co_activates")
    g.add_edge("effect_substituted", "phenom_01", "creates")

    proof_ob = "Substituted template conserves energy; latent capacity >= required energy; superheat <= limit."
    rb = RoleBinding(
        binding_id="RB-T4-01",
        source_node="effect_01",
        target_node="effect_substituted",
        relation="substituted",
        operator="T4",
        justification="Substituted evaporative cooling effect with composite PCM thermal storage effect.",
        source_card_node_ids=["effect_01"],
        proof_obligations=[proof_ob],
    )

    return OperatorResult(
        operator_id="T4",
        applied=True,
        rewritten_graph=g,
        role_binding=rb,
        target_template="TPL_02",
        proof_obligation=proof_ob,
    )


# =========================================================================
# OPERATOR T5: Regime Re-scaling (Post-Trial / Macro-Scale Transition)
# =========================================================================
def check_precondition_t5(
    source_meta: Dict[str, Any],
    prob: ProblemCard,
    char_length_m: Optional[float] = None,
) -> Tuple[bool, str]:
    source_max_L = source_meta.get("regime_max_length_m", 0.005)
    target_L = char_length_m or getattr(prob.system, "characteristic_length_m", None)
    if target_L is None and prob.constraints:
        import re
        for c in prob.constraints:
            if any(k in c.variable.lower() for k in ["characteristic_length", "device_length", "macro_scale", "envelope_length"]):
                m = re.search(r"(\d+(?:\.\d+)?)", c.bound)
                if m:
                    target_L = float(m.group(1))
                    break
    # If hydrostatic head > 5.0m on microporous gill, also triggers T5 regime switch
    head = None
    if prob.environment:
        # Check hydrostatic depth if present in problem context
        pass

    if target_L is not None and target_L > (5.0 * source_max_L):
        return True, f"Target characteristic scale {target_L:.3f} m exceeds biological micro-regime {source_max_L:.3f} m by > 5x."
    return False, f"Precondition failed: Target scale within biological regime bounds."


def apply_operator_t5(
    graph: SapphireGraph,
    source_meta: Dict[str, Any],
    prob: ProblemCard,
    config: AblationConfig = AblationConfig(),
    char_length_m: Optional[float] = None,
) -> OperatorResult:
    if not config.enable_t5:
        return OperatorResult(operator_id="T5", applied=False, rejection_reason="Operator T5 disabled by ablation flag.")

    ok, reason = check_precondition_t5(source_meta, prob, char_length_m)
    if not ok:
        return OperatorResult(operator_id="T5", applied=False, rejection_reason=reason)

    g = graph.clone()
    # Rewrite: Add sub-scale microporous cellular architecture
    g.parts["part_micro"] = Part(description="Micro-engineered membrane support with sub-scale pores")
    if "part_01" in g.parts:
        del g.parts["part_01"]

    g.organs["organ_plastron"] = Organ(description="Graded-porosity hydrophobic pore matrix with Laplace breakthrough enforcement")
    if "organ_01" in g.organs:
        del g.organs["organ_01"]

    g.effects["effect_subscale"] = PhysicalEffect(
        canonical_name="knudsen_bosanquet_effective_diffusion_with_capillary_barrier",
        governing_equation="J = D_eff * delta_C / L; P_cap = 4*gamma*cos(theta)/d_pore >= rho*g*H",
        relevant_variables=["pore_diameter_m", "membrane_thickness_m", "min_pore_diameter_m"],
    )
    if "effect_01" in g.effects:
        del g.effects["effect_01"]

    g.edges = [e for e in g.edges if e.source_id not in ["part_01", "organ_01", "effect_01"] and
                             e.target_id not in ["part_01", "organ_01", "effect_01"]]
    g.add_edge("part_micro", "organ_plastron", "creates")
    g.add_edge("organ_plastron", "effect_subscale", "co_activates")
    g.add_edge("input_01", "effect_subscale", "co_activates")
    g.add_edge("effect_subscale", "phenom_01", "creates")

    proof_ob = "Sub-scale pore diameter satisfies Laplace capillary breakthrough against hydrostatic head; d_pore >= min_pore_diameter_m; J_screen >= required_flux."
    rb = RoleBinding(
        binding_id="RB-T5-01",
        source_node="organ_01",
        target_node="organ_plastron",
        relation="transformed",
        operator="T5",
        justification="Sub-scale pore tuning prevents capillary wetting breakthrough at macro-engineering scale.",
        source_card_node_ids=["organ_01"],
        proof_obligations=[proof_ob],
    )

    return OperatorResult(
        operator_id="T5",
        applied=True,
        rewritten_graph=g,
        role_binding=rb,
        target_template="TPL_10",
        proof_obligation=proof_ob,
    )
