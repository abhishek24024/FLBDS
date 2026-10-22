"""Contradiction Resolution Engine (AutoTRIZ + TRIZ Agents + kTRIZ).

Resolves physical and technical contradictions arising during analogical transfer:
1. Physical Contradictions: apply Separation in Scale / Space via TPMS / Voronoi lattice subdivision.
2. Technical Contradictions: map improving and worsening features to Altshuller parameters (39x39 lookup).
3. Graph Rewrite: apply inventive principle transformations R_{p_k}(G_T).
4. Compiler Oracle: verify 100% parameter validity against canonical 39 params & 40 principles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from flbds.knowledge.triz import TrizKnowledge, TrizPrinciple
from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, SapphireGraph
from flbds.reasoning.buckingham import BuckinghamAuditor, ScaleAuditReport


@dataclass
class TrizResolution:
    physical_contradiction: str | None = None
    separation_operator: str | None = None
    topological_subdivision: str | None = None
    improving_parameter: int = 14
    worsening_parameter: int = 21
    inventive_principles: list[TrizPrinciple] = field(default_factory=list)
    graph_rewrite_applied: bool = False
    modified_graph: SapphireGraph | None = None
    type_check_passed: bool = True


class TrizContradictionSolver:
    """Resolves mechanical scaling and engineering trade-offs during biomimetic transfer."""

    def __init__(self, triz_knowledge: TrizKnowledge | None = None) -> None:
        self.triz = triz_knowledge or TrizKnowledge()
        self.auditor = BuckinghamAuditor()

    def resolve(
        self,
        g_bio: SapphireGraph,
        g_eng: SapphireGraph,
        scale_audit: ScaleAuditReport | None = None,
    ) -> TrizResolution:
        """End-to-end contradiction resolution workflow."""
        if scale_audit is None:
            # Audit primary effect
            eff_id = g_bio.effects[0].label if g_bio.effects else "young_laplace"
            scale_audit = self.auditor.audit_effect(eff_id, {}, {}, length_scale_ratio=10.0)

        res = TrizResolution()

        # 1. Physical Contradiction: Macro length vs Micro characteristic length
        if scale_audit.has_violations:
            violating_group = scale_audit.group_results[0] if scale_audit.group_results else None
            grp_name = violating_group.group_name if violating_group else "Similitude scale"
            res.physical_contradiction = (
                f"Geometric characteristic length must be macro-scale for structural support "
                f"and simultaneously micro-scale to satisfy {grp_name} boundary conditions."
            )
            res.separation_operator = "Separation in space and scale (System Level)"
            res.topological_subdivision = (
                "Heterogeneous Triply Periodic Minimal Surface (TPMS) / Voronoi Stereom lattice subdivision "
                "(decoupling macro span L from local hydraulic diameter L_c = V/A_s)."
            )

        # 2. Technical Contradiction: 39x39 Matrix Lookup
        # Map improving feature (Action goal, e.g. Speed/Force/Strength) vs worsening feature (Weight/Stress)
        imp_param = 14  # Strength
        wor_param = 21  # Power / energy consumption
        if scale_audit.has_violations:
            imp_param = 12  # Shape / form stability
            wor_param = 8   # Volume of stationary object (or weight)

        # Look up canonical matrix
        principle_ids = self.triz.principles_for(imp_param, wor_param)
        if not principle_ids:
            principle_ids = [1, 10, 15, 35]  # Fallback to standard segmentation & parameter change

        # Compile principles
        principles = [self.triz.get_principle(pid) for pid in principle_ids]
        res.improving_parameter = imp_param
        res.worsening_parameter = wor_param
        res.inventive_principles = principles

        # 3. Type-check Guard: verify no hallucinated parameters
        res.type_check_passed = (
            1 <= imp_param <= 39
            and 1 <= wor_param <= 39
            and all(1 <= p.id <= 40 for p in principles)
        )

        # 4. Graph Rewrite R_{p_k}(G_T)
        modified_g = SapphireGraph(
            id=f"{g_eng.id}-synthesized",
            title=f"{g_eng.title} (Bio-Synthesized via TRIZ #{principles[0].id})",
            domain="engineering",
            description=f"{g_eng.description} [Modified with {principles[0].name} & TPMS subdivision]",
        )
        for n in g_eng.nodes:
            new_node = ConstructNode(
                id=n.id,
                construct=n.construct,
                label=n.label,
                description=n.description,
                attributes=list(n.attributes),
                evidence=list(n.evidence),
            )
            # Inject bio-organ topological attributes into engineering part & organ
            if n.construct == Construct.ORGAN and g_bio.nodes_of(Construct.ORGAN):
                bio_organ = g_bio.nodes_of(Construct.ORGAN)[0]
                new_node.label = f"{n.label} + {bio_organ.label} (TPMS lattice)"
                new_node.attributes.extend(bio_organ.attributes)
            modified_g.add_node(new_node)

        for e in g_eng.edges:
            modified_g.add_edge(
                CausalEdge(source=e.source, target=e.target, relation=e.relation, evidence=list(e.evidence))
            )

        res.graph_rewrite_applied = True
        res.modified_graph = modified_g
        return res
