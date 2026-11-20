"""flbds/m4 package: Analogy and Transformation Engine (FLBDS v9 §4.4, §4.5)."""

from .sapphire_graph import SapphireGraph, SapphireEdge
from .conflict_detector import detect_conflicts
from .fixtures import DEV_FIXTURES
from .operators import (
    AblationConfig,
    OperatorResult,
    apply_operator_t1,
    apply_operator_t2,
    apply_operator_t3,
    apply_operator_t4,
    apply_operator_t5,
)

__all__ = [
    "SapphireGraph",
    "SapphireEdge",
    "detect_conflicts",
    "DEV_FIXTURES",
    "AblationConfig",
    "OperatorResult",
    "apply_operator_t1",
    "apply_operator_t2",
    "apply_operator_t3",
    "apply_operator_t4",
    "apply_operator_t5",
]
