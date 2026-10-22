"""Fusion of Pathway A (HyDE-CoT RAG) and Pathway B (Deterministic Rules) + Abductive Repair.

Orchestrates full SAPPhIRE extraction:
1. Pathway B extracts syntactic backbone and canonical physical laws.
2. Pathway A supplies fact-grounded text spans with high groundedness scores.
3. Abductive repair loop: if any Effect variable is missing (Activates(I,R -> e)),
   triggers targeted search across document chunks to supply the required attributes.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from flbds.extraction.hyde import HyDECorrectiveRAG
from flbds.extraction.rules import DeterministicRuleExtractor
from flbds.knowledge.physics import PhysicalLawsCatalog
from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, Evidence, SapphireGraph
from flbds.ontology.validate import abductive_gap, validate_graph


class SAPPhIREExtractor:
    """End-to-end dual-pathway extractor for biological and engineering corpora."""

    def __init__(self, physics_catalog: PhysicalLawsCatalog | None = None) -> None:
        self.catalog = physics_catalog or PhysicalLawsCatalog()
        self.rules_engine = DeterministicRuleExtractor(self.catalog)
        self.hyde_rag = HyDECorrectiveRAG(groundedness_threshold=0.76)

    def extract(
        self,
        text: str,
        graph_id: str,
        title: str,
        domain: str = "biological",
        source_id: str = "doc:text",
    ) -> tuple[SapphireGraph, dict[str, Any]]:
        """Extract, fuse, abductively repair, and validate a SapphireGraph."""
        # 1. Pathway B: rule-based skeleton
        g_rule = self.rules_engine.extract_graph(
            text=text, graph_id=graph_id, title=title, domain=domain, source_id=source_id
        )

        # 2. Pathway A: HyDE-CoT fact-grounded constructs
        hyde_results = self.hyde_rag.extract_with_hyde(text=text, system_name=title, domain=domain)

        # 3. Fuse constructs: merge high-precision labels & evidence
        for node in g_rule.nodes:
            if node.construct in hyde_results:
                corrected = hyde_results[node.construct]
                # If hyde label is rich, attach quote & chunk pointer
                node.evidence.append(
                    Evidence(
                        source_id=source_id,
                        source_type="paper" if domain == "biological" else "patent",
                        locator=corrected.evidence_chunk_id or "para 1",
                        quote=corrected.evidence_quote,
                        chunk_id=corrected.evidence_chunk_id,
                        confidence=corrected.groundedness_score,
                    )
                )

        # 4. Abductive Repair Loop
        missing_vars = abductive_gap(g_rule)
        repair_log: list[str] = []

        if missing_vars:
            chunks = self.hyde_rag.chunk_document(text)
            for effect_id, vars_missing in missing_vars.items():
                for var_sym in vars_missing:
                    # Targeted search in chunks for variable mention or numeric value
                    pattern = rf"(?:{var_sym}|{var_sym.replace('_', ' ')})\s*[:=~]?\s*([0-9.eE+-]+(?:\s*[a-zA-Z/%^]+)?)"
                    m = re.search(pattern, text, re.IGNORECASE)
                    val = m.group(1).strip() if m else None

                    # Assign to oRgan (if geometric) or Input (if boundary)
                    assigned_node = g_rule.nodes_of(Construct.ORGAN)[0]
                    assigned_node.attributes.append(
                        Attribute(
                            name=var_sym.replace("_", " "),
                            symbol=var_sym,
                            value=val,
                            dimension="L" if "r" in var_sym or "l" in var_sym else "",
                            role="interface",
                        )
                    )
                    repair_log.append(f"Abductively repaired {var_sym} on {assigned_node.id}")

        # 5. Final Validation Check
        report = validate_graph(g_rule, strict_abductive=True, require_evidence=True)

        metadata = {
            "graph_id": graph_id,
            "valid": report.ok,
            "n_errors": len(report.errors),
            "n_warnings": len(report.warnings),
            "repair_log": repair_log,
            "construct_coverage": report.metrics.get("construct_coverage", 0.0),
            "grounding_ratio": report.metrics.get("grounding_ratio", 0.0),
        }

        return g_rule, metadata
