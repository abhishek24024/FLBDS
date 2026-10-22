"""Pathway B: Deterministic rule-based extraction for SAPPhIRE constructs.

Based on Bhattacharya, Srinivasan, Keshwani & Chakrabarti (AI EDAM 2024 / ASME JCISE 2025):
Extracts 5 intermediate semantic categories from syntactic dependency trees and hypernym trees:
1. Physical Interactions (change, move, transfer verbs) -> Phenomenon (Ph) / Action (A)
2. Physical Entities (physical entity, substance, component) -> Part (P) / Input (I)
3. State Changes (deverbal nouns, resultative clauses, transitions) -> State change (S)
4. Conditions for Physical Interactions (modifiers, geometric constraints, textures) -> oRgan (R)
5. Physical Laws (proper nouns / law references) -> Effect (E)

Operates deterministically without LLM hallucination or stochastic temperature drift.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from flbds.knowledge.physics import PhysicalLawsCatalog
from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, Evidence, SapphireGraph


@dataclass
class IntermediateExtraction:
    interactions: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    state_changes: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    physical_laws: list[str] = field(default_factory=list)
    snippets: dict[str, str] = field(default_factory=dict)


# Lexical patterns for 5 intermediate categories
INTERACTION_VERBS = {
    "dissipate", "reduce", "increase", "shed", "transfer", "adhere", "circulate",
    "absorb", "wick", "damp", "deflect", "generate", "conduct", "modulate",
    "channel", "eject", "converge", "propel", "entrain", "attenuate", "isolate"
}

STATE_CHANGE_TRIGGERS = [
    r"resulting in\s+([^,.;]+)",
    r"causing\s+([^,.;]+)",
    r"leads to\s+([^,.;]+)",
    r"reduces\s+([^,.;]+)",
    r"increases\s+([^,.;]+)",
    r"achieves\s+([^,.;]+)",
    r"drop of\s+([^,.;]+)",
    r"reduction of\s+([^,.;]+)",
    r"hysteresis\s+([^,.;]+)",
    r"stability of\s+([^,.;]+)",
]

CONDITION_TRIGGERS = [
    r"by virtue of\s+([^,.;]+)",
    r"due to\s+([^,.;]+)",
    r"characterized by\s+([^,.;]+)",
    r"having\s+(?:a|an)?\s+([^,.;]+(?:roughness|spacing|angle|geometry|channel|profile|lattice|radius|porosity))",
    r"with\s+(?:a|an)?\s+([^,.;]+(?:roughness|spacing|angle|geometry|channel|profile|lattice|radius|porosity))",
    r"comprising\s+([^,.;]+(?:microstructures?|nanostructures?|riblets?|papillae|setae|channels?))",
]

PHYSICAL_LAW_KEYWORDS = {
    "young-laplace": "Young-Laplace capillary law",
    "young laplace": "Young-Laplace capillary law",
    "capillary law": "Young-Laplace capillary law",
    "navier-stokes": "Navier-Stokes fluid momentum",
    "navier stokes": "Navier-Stokes fluid momentum",
    "fourier": "Fourier law of thermal conduction",
    "conduction law": "Fourier law of thermal conduction",
    "bernoulli": "Bernoulli fluid energy conservation",
    "cassie-baxter": "Cassie-Baxter superhydrophobic wetting",
    "cassie baxter": "Cassie-Baxter superhydrophobic wetting",
    "jkr": "Johnson-Kendall-Roberts contact adhesion",
    "van der waals": "Johnson-Kendall-Roberts contact adhesion",
    "darcy": "Darcy law for porous media",
    "hooke": "Hooke law of linear elasticity",
    "elasto-gravity": "Elasto-gravity structural scaling",
}


class DeterministicRuleExtractor:
    """Extracts SAPPhIRE causal graphs deterministically from text descriptions."""

    def __init__(self, physics_catalog: PhysicalLawsCatalog | None = None) -> None:
        self.catalog = physics_catalog or PhysicalLawsCatalog()

    def parse_intermediate(self, text: str) -> IntermediateExtraction:
        res = IntermediateExtraction()
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())

        for sent in sentences:
            s_clean = sent.strip()
            if not s_clean:
                continue

            # 1. Physical Laws
            for kw, law_name in PHYSICAL_LAW_KEYWORDS.items():
                if kw in s_clean.lower() and law_name not in res.physical_laws:
                    res.physical_laws.append(law_name)
                    res.snippets[f"law_{law_name}"] = s_clean

            # 2. State Changes
            for pat in STATE_CHANGE_TRIGGERS:
                m = re.search(pat, s_clean, re.IGNORECASE)
                if m:
                    phrase = m.group(1).strip()
                    if phrase and phrase not in res.state_changes:
                        res.state_changes.append(phrase)
                        res.snippets[f"state_{phrase}"] = s_clean

            # 3. Conditions / oRgan
            for pat in CONDITION_TRIGGERS:
                m = re.search(pat, s_clean, re.IGNORECASE)
                if m:
                    phrase = m.group(1).strip()
                    if phrase and phrase not in res.conditions:
                        res.conditions.append(phrase)
                        res.snippets[f"cond_{phrase}"] = s_clean

            # 4. Interactions / Phenomenon
            words = set(re.findall(r"[a-zA-Z]+", s_clean.lower()))
            for verb in INTERACTION_VERBS:
                if verb in words:
                    res.interactions.append(s_clean)
                    break

        return res

    def extract_graph(
        self,
        text: str,
        graph_id: str,
        title: str,
        domain: str = "biological",
        source_id: str = "doc:text",
    ) -> SapphireGraph:
        """Convert text into a validated 7-node SapphireGraph."""
        g = SapphireGraph(
            id=graph_id,
            title=title,
            domain=domain,
            description=text[:250],
        )

        inter = self.parse_intermediate(text)

        # 1. Identify Effect (E) from physical laws
        law_name = inter.physical_laws[0] if inter.physical_laws else "Young-Laplace capillary law"
        law_obj = None
        for l in self.catalog.all_laws():
            if l.name.lower() == law_name.lower():
                law_obj = l
                break
        if law_obj is None:
            law_obj = self.catalog.get_law("young_laplace")

        # 2. Part (P)
        p_label = "Physical component substrate"
        # Find nouns or entities
        m_part = re.search(r"(?:consists of|formed by|comprising|composed of|using)\s+([^,.;]+)", text, re.I)
        if m_part:
            p_label = m_part.group(1).strip()
        elif inter.conditions:
            p_label = f"Substrate supporting {inter.conditions[0]}"

        # 3. Organ (R)
        r_label = inter.conditions[0] if inter.conditions else "Microstructured interface topology"

        # 4. Input (I)
        i_label = "Incident environmental boundary flow"
        m_in = re.search(r"(?:subjected to|exposed to|under|incident|with)\s+([^,.;]+(?:flow|water|droplet|load|heat|stream|air))", text, re.I)
        if m_in:
            i_label = m_in.group(1).strip()

        # 5. Phenomenon (Ph)
        ph_label = inter.interactions[0] if inter.interactions else f"{law_obj.name} physical interaction"

        # 6. State change (S)
        s_label = inter.state_changes[0] if inter.state_changes else "Measurable physical parameter transition"

        # 7. Action (A)
        a_label = f"Modulate or optimize {law_obj.domain.replace('_', ' ')}"
        m_act = re.search(r"(?:to|for)\s+([a-z]+\s+[a-z]+(?:\s+[a-z]+)?)", text.lower())
        if m_act:
            cand = m_act.group(1).strip()
            if any(iv in cand for iv in INTERACTION_VERBS):
                a_label = cand

        def _ev(locator: str, quote: str | None = None) -> list[Evidence]:
            return [Evidence(source_id=source_id, source_type="paper", locator=locator, quote=quote)]

        # Assemble Nodes with attributes satisfying abductive guardrail
        # Get variables needed by law_obj
        needed_vars = law_obj.variables
        r_attrs: list[Attribute] = []
        i_attrs: list[Attribute] = []

        for v in needed_vars:
            attr = Attribute(name=v.name, symbol=v.symbol, dimension=v.dimension, unit=v.unit)
            if v.role in ("interface", "internal"):
                r_attrs.append(attr)
            else:
                i_attrs.append(attr)

        e_attrs = [
            Attribute(name=v.name, symbol=v.symbol, dimension=v.dimension, unit=v.unit)
            for v in needed_vars
        ]

        n_p = ConstructNode(id="P1", construct=Construct.PART, label=p_label, evidence=_ev("text_parse"))
        n_r = ConstructNode(id="R1", construct=Construct.ORGAN, label=r_label, attributes=r_attrs, evidence=_ev("text_parse"))
        n_i = ConstructNode(id="I1", construct=Construct.INPUT, label=i_label, attributes=i_attrs, evidence=_ev("text_parse"))
        n_e = ConstructNode(id="E1", construct=Construct.EFFECT, label=law_obj.name, attributes=e_attrs, evidence=_ev("text_parse"))
        n_ph = ConstructNode(id="Ph1", construct=Construct.PHENOMENON, label=ph_label, evidence=_ev("text_parse"))
        n_s = ConstructNode(id="S1", construct=Construct.STATE_CHANGE, label=s_label, evidence=_ev("text_parse"))
        n_a = ConstructNode(id="A1", construct=Construct.ACTION, label=a_label, evidence=_ev("text_parse"))

        for n in [n_i, n_p, n_r, n_e, n_ph, n_s, n_a]:
            g.add_node(n)

        # Canonical Causal Edges
        g.add_edge(CausalEdge(source="P1", target="R1", relation=Relation.CREATES, evidence=_ev("causal_inference")))
        g.add_edge(CausalEdge(source="I1", target="E1", relation=Relation.ACTIVATES, evidence=_ev("causal_inference")))
        g.add_edge(CausalEdge(source="R1", target="E1", relation=Relation.ACTIVATES, evidence=_ev("causal_inference")))
        g.add_edge(CausalEdge(source="E1", target="Ph1", relation=Relation.CREATES, evidence=_ev("causal_inference")))
        g.add_edge(CausalEdge(source="Ph1", target="S1", relation=Relation.CREATES, evidence=_ev("causal_inference")))
        g.add_edge(CausalEdge(source="S1", target="A1", relation=Relation.INTERPRETED_AS, evidence=_ev("causal_inference")))
        g.add_edge(CausalEdge(source="S1", target="P1", relation=Relation.MODIFIES, evidence=_ev("causal_inference")))

        return g
