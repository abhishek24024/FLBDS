"""FLBDS — Functional and Logical Biomimetic Design System (v3.0)."""

__version__ = "0.1.0"

from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import (
    Attribute,
    CausalEdge,
    ConstructNode,
    Evidence,
    SapphireGraph,
)
from flbds.ontology.validate import Severity, ValidationIssue, ValidationReport, validate_graph

__all__ = [
    "Construct",
    "Relation",
    "Attribute",
    "CausalEdge",
    "ConstructNode",
    "Evidence",
    "SapphireGraph",
    "Severity",
    "ValidationIssue",
    "ValidationReport",
    "validate_graph",
]
