"""Core schemas and ontologies for FLBDS v9."""

from .enums import (
    BoundaryTypeEnum,
    DirectionEnum,
    DuctCrossSectionEnum,
    HazardEnum,
    ResourceEnum,
    TemplateEnum,
    TimeModeEnum,
)
from .evidence import EvidenceSpan
from .ground_truth_eval import GroundTruthEval
from .mechanism_card import AbstractionLadder, Context, MechanismCard, Subject
from .problem_card import (
    Constraint,
    Contradiction,
    EnvironmentSpec,
    HardConstraints,
    ProblemCard,
    RequiredFunction,
    SystemSpec,
    TimePattern,
)
from .quantity import Quantity, ureg
from .role_binding import RoleBinding
from .sapphire import (
    Action,
    Organ,
    Part,
    Phenomenon,
    PhysicalEffect,
    ResourceInput,
    StateChange,
)
from .templates import (
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
    TemplateParameters,
)
from .verification import AssertionResult, PhysicsCheck, VerificationReport

__all__ = [
    # Enums
    "ResourceEnum",
    "HazardEnum",
    "DirectionEnum",
    "TimeModeEnum",
    "BoundaryTypeEnum",
    "DuctCrossSectionEnum",
    "TemplateEnum",
    # Core Schemas
    "EvidenceSpan",
    "Quantity",
    "ureg",
    "StateChange",
    "Action",
    "Phenomenon",
    "PhysicalEffect",
    "ResourceInput",
    "Organ",
    "Part",
    "Subject",
    "Context",
    "AbstractionLadder",
    "MechanismCard",
    "SystemSpec",
    "EnvironmentSpec",
    "RequiredFunction",
    "TimePattern",
    "Constraint",
    "HardConstraints",
    "Contradiction",
    "ProblemCard",
    "RoleBinding",
    "GroundTruthEval",
    "AssertionResult",
    "PhysicsCheck",
    "VerificationReport",
    # Template parameter schemas
    "TPL01Params",
    "TPL02Params",
    "TPL03Params",
    "TPL04Params",
    "TPL05Params",
    "TPL06Params",
    "TPL07Params",
    "TPL08Params",
    "TPL09Params",
    "TPL10Params",
    "TemplateParameters",
]
