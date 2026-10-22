"""Typed payloads for the multimodal causal property graph (G_MCKG).

Every node and edge carries provenance. A graph that cannot say *where* a claim
came from is not admissible evidence in a design study, so `Evidence` is a
first-class object rather than an optional annotation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from flbds.ontology.constructs import CHAIN_ORDER, Construct, Relation

SourceType = Literal[
    "patent",
    "paper",
    "asknature",
    "idea_inspire",
    "handbook",
    "image",
    "expert",
    "synthetic",
]

AttributeRole = Literal["boundary", "internal", "interface", "governing", "observed"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    """A pointer back into the corpus that justifies a claim."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    source_type: SourceType
    locator: str = Field(..., min_length=1, description="paragraph range, figure, bbox, ...")
    quote: str | None = None
    chunk_id: str | None = Field(
        default=None, description="retrieval chunk id, for HyDE-CoT groundedness scoring"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Attribute(BaseModel):
    """A named quantity, optionally dimensioned and symbolically addressable.

    `symbol` is what the abductive guardrail matches against: an Effect declares
    the variables it needs (theta, r, gamma) and the guardrail checks that the
    Input / oRgan / Part nodes actually supply them.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    symbol: str | None = None
    value: float | str | None = None
    unit: str | None = None
    dimension: str | None = Field(
        default=None,
        description="SI dimension string over M L T K I N J, e.g. M L^-1 T^-2; empty for dimensionless",
    )
    role: AttributeRole | None = None

    @field_validator("symbol")
    @classmethod
    def _normalise_symbol(cls, v: str | None) -> str | None:
        return v.strip() if v else None


import warnings

warnings.filterwarnings("ignore", message='.*Field name "construct" in "ConstructNode" shadows.*')

class ConstructNode(BaseModel):
    """One SAPPhIRE construct instance."""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    id: str = Field(..., min_length=1)
    construct: Construct
    label: str = Field(..., min_length=1)
    description: str = ""
    attributes: list[Attribute] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    def attribute_symbols(self) -> set[str]:
        """Lower-cased symbols (falling back to slugs of names)."""
        out: set[str] = set()
        for a in self.attributes:
            key = a.symbol or _slug(a.name)
            out.add(key.lower())
        return out

    def grounded(self) -> bool:
        return bool(self.evidence)


class CausalEdge(BaseModel):
    """A directed relation between two constructs (or provenance links)."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    relation: Relation
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.source}-[{self.relation.value}]->{self.target}"


class SapphireGraph(BaseModel):
    """A complete causal model of one biological strategy or engineered system."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    domain: Literal["biological", "engineering", "hybrid"]
    description: str = ""
    nodes: list[ConstructNode] = Field(default_factory=list)
    edges: list[CausalEdge] = Field(default_factory=list)
    source: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)

    # ---------------------------------------------------------------- accessors
    def node_map(self) -> dict[str, ConstructNode]:
        return {n.id: n for n in self.nodes}

    def get_node(self, node_id: str) -> ConstructNode:
        for n in self.nodes:
            if n.id == node_id:
                return n
        raise KeyError(node_id)

    def nodes_of(self, construct: Construct) -> list[ConstructNode]:
        return [n for n in self.nodes if n.construct is construct]

    @property
    def effects(self) -> list[ConstructNode]:
        return self.nodes_of(Construct.EFFECT)

    def outgoing(self, node_id: str, relation: Relation | None = None) -> list[CausalEdge]:
        return [
            e
            for e in self.edges
            if e.source == node_id and (relation is None or e.relation is relation)
        ]

    def incoming(self, node_id: str, relation: Relation | None = None) -> list[CausalEdge]:
        return [
            e
            for e in self.edges
            if e.target == node_id and (relation is None or e.relation is relation)
        ]

    def causal_edges(self) -> list[CausalEdge]:
        return [e for e in self.edges if e.relation.is_causal]

    # ------------------------------------------------------------------ mutate
    def add_node(self, node: ConstructNode) -> ConstructNode:
        if any(n.id == node.id for n in self.nodes):
            raise ValueError(f"duplicate node id: {node.id}")
        self.nodes.append(node)
        return node

    def add_edge(self, edge: CausalEdge) -> CausalEdge:
        ids = {n.id for n in self.nodes}
        if edge.source not in ids or edge.target not in ids:
            raise ValueError(f"dangling edge: {edge.key}")
        if any(e.key == edge.key for e in self.edges):
            raise ValueError(f"duplicate edge: {edge.key}")
        self.edges.append(edge)
        return edge

    # ------------------------------------------------------------- analytics
    def construct_coverage(self) -> dict[str, bool]:
        present = {n.construct.value for n in self.nodes}
        return {c.value: c.value in present for c in CHAIN_ORDER}

    def chain_edges(self) -> list[CausalEdge]:
        return self.causal_edges()

    def to_networkx(self):
        import networkx as nx

        g = nx.MultiDiGraph(id=self.id, title=self.title, domain=self.domain)
        for n in self.nodes:
            g.add_node(
                n.id,
                construct=n.construct.value,
                label=n.label,
                confidence=n.confidence,
                description=n.description,
            )
        for e in self.edges:
            g.add_edge(
                e.source,
                e.target,
                key=e.relation.value,
                relation=e.relation.value,
                confidence=e.confidence,
            )
        return g

    # ------------------------------------------------------------ (de)serialise
    def to_json(self, path: str | Path | None = None, indent: int | None = 2) -> str:
        payload = self.model_dump_json(indent=indent)
        if path is not None:
            Path(path).write_text(payload, encoding="utf-8")
        return payload

    @classmethod
    def from_json(cls, path: str | Path) -> "SapphireGraph":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.model_dump_json())

    def validate_graph(self, **kwargs):
        from flbds.ontology.validate import validate_graph

        return validate_graph(self, **kwargs)


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.strip().lower()).strip("_")
