"""flbds/m4/sapphire_graph.py
SAPPhIRE Causal Graph Structure for Functional Bio-Inspired Design (FLBDS v9 §1.1, §4.3).

Constructs (Chakrabarti et al.):
  - Part (P): Physical components or constituent elements
  - Organ (R): Structural properties and morphological conditions enabling the phenomenon
  - Input (I): Energy, material, or signal required to activate the physical effect
  - PhysicalEffect (E): Canonical physical law, effect, or governing equation
  - Phenomenon (P): Physical behavior or process
  - StateChange (S): Change of physical state property across time or boundary
  - Action (A): Higher-level function interpreted from the state change

Canonical Edges:
  1. (Part, Organ, "creates")
  2. (Organ, PhysicalEffect, "co_activates")
  3. (Input, PhysicalEffect, "co_activates")
  4. (PhysicalEffect, Phenomenon, "creates")
  5. (Phenomenon, StateChange, "creates")
  6. (StateChange, Action, "interpreted_as")
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from pydantic import BaseModel, Field

from flbds.schema.sapphire import (
    Part,
    Organ,
    ResourceInput,
    PhysicalEffect,
    Phenomenon,
    StateChange,
    Action,
)


class SapphireEdge(BaseModel):
    """A directed edge in the SAPPhIRE graph."""
    source_id: str
    target_id: str
    relation: str  # e.g. "creates", "co_activates", "interpreted_as"


class SapphireGraph(BaseModel):
    """Directed SAPPhIRE graph instance."""
    graph_id: str = Field(..., description="Unique graph identifier")
    description: str = Field(..., description="Natural language description of mechanism")

    # Canonical nodes
    parts: Dict[str, Part] = Field(default_factory=dict)
    organs: Dict[str, Organ] = Field(default_factory=dict)
    inputs: Dict[str, ResourceInput] = Field(default_factory=dict)
    effects: Dict[str, PhysicalEffect] = Field(default_factory=dict)
    phenomena: Dict[str, Phenomenon] = Field(default_factory=dict)
    state_changes: Dict[str, StateChange] = Field(default_factory=dict)
    actions: Dict[str, Action] = Field(default_factory=dict)

    # Edges
    edges: List[SapphireEdge] = Field(default_factory=list)

    def add_edge(self, source_id: str, target_id: str, relation: str):
        self.edges.append(SapphireEdge(source_id=source_id, target_id=target_id, relation=relation))

    def get_all_node_ids(self) -> Set[str]:
        node_ids = set()
        node_ids.update(self.parts.keys())
        node_ids.update(self.organs.keys())
        node_ids.update(self.inputs.keys())
        node_ids.update(self.effects.keys())
        node_ids.update(self.phenomena.keys())
        node_ids.update(self.state_changes.keys())
        node_ids.update(self.actions.keys())
        return node_ids

    def validate_topology(self) -> Tuple[bool, List[str]]:
        """Validates that graph satisfies SAPPhIRE topological rules:
        1. All edge endpoints exist.
        2. Graph contains at least one node of each canonical type (P, R, I, E, P, S, A).
        3. A connected causal path exists from Part/Input through Effect to Action.
        """
        errors = []
        node_ids = self.get_all_node_ids()

        # 1. Edge endpoint check
        for e in self.edges:
            if e.source_id not in node_ids:
                errors.append(f"Edge source '{e.source_id}' does not exist in graph nodes.")
            if e.target_id not in node_ids:
                errors.append(f"Edge target '{e.target_id}' does not exist in graph nodes.")

        # 2. Node presence check
        if not self.parts:
            errors.append("Graph missing 'Part' node.")
        if not self.organs:
            errors.append("Graph missing 'Organ' node.")
        if not self.inputs:
            errors.append("Graph missing 'Input' node.")
        if not self.effects:
            errors.append("Graph missing 'PhysicalEffect' node.")
        if not self.phenomena:
            errors.append("Graph missing 'Phenomenon' node.")
        if not self.state_changes:
            errors.append("Graph missing 'StateChange' node.")
        if not self.actions:
            errors.append("Graph missing 'Action' node.")

        # 3. Path connectivity check: Effect must have inbound and outbound edges
        effect_sources = {e.target_id for e in self.edges if e.target_id in self.effects}
        effect_targets = {e.source_id for e in self.edges if e.source_id in self.effects}
        if not effect_sources:
            errors.append("No edges connect into 'PhysicalEffect' nodes.")
        if not effect_targets:
            errors.append("No edges depart from 'PhysicalEffect' nodes.")

        is_valid = len(errors) == 0
        return is_valid, errors

    def clone(self) -> "SapphireGraph":
        """Deep clone of the graph."""
        return SapphireGraph.model_validate(self.model_dump())
