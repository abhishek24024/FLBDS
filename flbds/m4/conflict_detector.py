"""flbds/m4/conflict_detector.py
Symbolic, Rule-Based Conflict Detector operating on ProblemCard enums and fields (FLBDS v9 §4.4).
"""

import re
from typing import Dict, List, Optional, Any
from flbds.schema.enums import DirectionEnum, ResourceEnum, TimeModeEnum
from flbds.schema.problem_card import ProblemCard
from flbds.m4.sapphire_graph import SapphireGraph


def detect_conflicts(
    source_fixture: Dict[str, Any],
    prob: ProblemCard,
    proposed_char_length: Optional[float] = None,
) -> List[str]:
    """Pure symbolic, rule-based conflict detector operating on ProblemCard enums and fields.

    Args:
        source_fixture: Biological mechanism dictionary or metadata (FIXTURE).
        prob: Target engineering ProblemCard.
        proposed_char_length: Optional proposed device characteristic length (m).

    Returns:
        List of conflict flags that fired: ['T1', 'T2', 'T3', 'T4', 'T5'].
    """
    flags = []

    # 1. Operator T1: Resource Absence
    source_consumables = set(source_fixture.get("consumable_inputs", []))
    problem_absent = set(prob.environment.resources_absent)
    if source_consumables.intersection(problem_absent):
        flags.append("T1")

    # 2. Operator T2: Flow / Direction Inversion
    source_dir = source_fixture.get("target_direction")
    target_dir = prob.required_function.target_direction
    if (source_dir == DirectionEnum.DECREASE and target_dir == DirectionEnum.INCREASE) or \
       (source_dir == DirectionEnum.INCREASE and target_dir == DirectionEnum.DECREASE):
        flags.append("T2")

    # 3. Operator T3: Temporal Phase Shift
    source_time = source_fixture.get("time_mode")
    target_time = prob.time_pattern.time_mode
    if source_time in [TimeModeEnum.STEADY, TimeModeEnum.CONTINUOUS] and \
       target_time in [TimeModeEnum.CYCLIC_DIURNAL, TimeModeEnum.PULSED]:
        flags.append("T3")

    # 4. Operator T4: Effect / Medium Substitution
    # Fires if source relies on an open liquid phase or effect blocked in target environment
    source_effects = source_fixture.get("effects", [])
    if any("evaporation" in e.lower() for e in source_effects) and "liquid_water" in problem_absent:
        flags.append("T4")

    # 5. Operator T5: Regime Re-scaling
    # Compares characteristic length or regime bounds
    source_max_L = source_fixture.get("regime_max_length_m", 0.005)
    target_L = proposed_char_length
    if target_L is None:
        target_L = getattr(prob.system, "characteristic_length_m", None)
    if target_L is None and prob.constraints:
        for c in prob.constraints:
            if any(k in c.variable.lower() for k in ["characteristic_length", "device_length", "macro_scale", "envelope_length"]):
                m = re.search(r"(\d+(?:\.\d+)?)", c.bound)
                if m:
                    target_L = float(m.group(1))
                    break
    if target_L is not None and target_L > (5.0 * source_max_L):
        flags.append("T5")

    return flags
