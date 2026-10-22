"""The canonical vocabulary of the SAPPhIRE model of causality.

Seven constructs, three relational operators, and two feedback forms. Every
downstream stage reads from this module, so the definitions here are the single
source of truth for the whole system.

Causal chain (Chakrabarti et al.):

    P --creates--> R
    (I AND R) --activates--> E --creates--> Ph --creates--> S --interpreted_as--> A
    S --modifies--> P                  (structural feedback)
    S_k == I_{k+1}                     (multi-state relay across subsystems)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Construct(str, Enum):
    """The seven SAPPhIRE constructs."""

    ACTION = "A"
    STATE_CHANGE = "S"
    PHENOMENON = "Ph"
    EFFECT = "E"
    ORGAN = "R"
    INPUT = "I"
    PART = "P"

    @property
    def symbol(self) -> str:
        return self.value


class Relation(str, Enum):
    """Relational operators of the causal graph."""

    CREATES = "creates"
    ACTIVATES = "activates"
    INTERPRETED_AS = "interpreted_as"
    MODIFIES = "modifies"
    # --- provenance / linking edges (not part of the causal chain) ---
    DEPICTS_PART = "depicts_part"
    ILLUSTRATES_ORGAN = "illustrates_organ"
    REALIZES = "realizes"  # biological strategy -> engineering solution

    @property
    def is_causal(self) -> bool:
        return self in _CAUSAL_RELATIONS


_CAUSAL_RELATIONS = frozenset(
    {Relation.CREATES, Relation.ACTIVATES, Relation.INTERPRETED_AS, Relation.MODIFIES}
)


@dataclass(frozen=True)
class ConstructSpec:
    construct: Construct
    name: str
    fbs_alignment: str
    transfer_role: str
    definition: str
    extraction_question: str
    examples: tuple[str, ...] = field(default_factory=tuple)


CONSTRUCT_SPECS: dict[Construct, ConstructSpec] = {
    Construct.ACTION: ConstructSpec(
        construct=Construct.ACTION,
        name="Action",
        fbs_alignment="Function (teleological)",
        transfer_role="SHARED BRIDGE NODE — the high-level verb-noun goal both "
        "domains must agree on before anything else transfers.",
        definition="The high-level goal the system achieves, stated as a "
        "verb-noun pair independent of the mechanism that realises it.",
        extraction_question="What is this system *for*? State it without naming parts.",
        examples=("dissipate thermal load", "adhere reversibly", "reduce drag"),
    ),
    Construct.STATE_CHANGE: ConstructSpec(
        construct=Construct.STATE_CHANGE,
        name="State change",
        fbs_alignment="Function / Behavior",
        transfer_role="OBSERVABLE OUTCOME — quantified so the transferred design "
        "can be compared against the baseline.",
        definition="A quantifiable transition of a physical state variable between "
        "t0 and t1 (e.g. temperature drop dT, drag coefficient reduction dCd).",
        extraction_question="Which measurable property changes, and by how much?",
        examples=("temperature drop dT = 12 K", "drag coefficient -8%", "contact angle < 5 deg"),
    ),
    Construct.PHENOMENON: ConstructSpec(
        construct=Construct.PHENOMENON,
        name="Phenomenon",
        fbs_alignment="Behavior (interaction)",
        transfer_role="MECHANISM CLASS — must be matched between source and target.",
        definition="The physical interaction that transforms material, energy or "
        "signal; the observable how that sits above the governing law.",
        extraction_question="What physical interaction is happening?",
        examples=("capillary wicking + evaporative phase change", "vortex shedding"),
    ),
    Construct.EFFECT: ConstructSpec(
        construct=Construct.EFFECT,
        name="Effect",
        fbs_alignment="Behavior (governing law)",
        transfer_role="SHARED CANONICAL BRIDGE — identical effects are the anchors "
        "of cross-domain alignment.",
        definition="The mathematical equation or physical law activated when the "
        "Input and the oRgan coexist (e.g. Young-Laplace, Biot-Savart).",
        extraction_question="Which physical law governs this interaction?",
        examples=("Young-Laplace capillary law", "Fourier conduction", "Euler buckling"),
    ),
    Construct.ORGAN: ConstructSpec(
        construct=Construct.ORGAN,
        name="oRgan",
        fbs_alignment="Structure (geometric context)",
        transfer_role="PRESERVED INVARIANT — dimensionless geometry, topology and "
        "boundary conditions that must survive the transfer.",
        definition="The dimensionless geometric/topological boundary conditions "
        "created by the Parts that are required to activate the Effect "
        "(e.g. porosity, riblet spacing s+, contact angle theta).",
        extraction_question="What geometry or topology makes the law apply here?",
        examples=("Voronoi channel porosity phi = 0.62", "riblet spacing s+ = 15"),
    ),
    Construct.INPUT: ConstructSpec(
        construct=Construct.INPUT,
        name="Input",
        fbs_alignment="Function (boundary flow)",
        transfer_role="BOUNDARY CONDITION — rescaled, not copied.",
        definition="Material, energy or signal crossing the system boundary "
        "(e.g. incident heat flux q, axial preload).",
        extraction_question="What crosses the system boundary?",
        examples=("solar heat flux q = 800 W/m2", "axial preload F = 2 kN"),
    ),
    Construct.PART: ConstructSpec(
        construct=Construct.PART,
        name="Part",
        fbs_alignment="Structure (physical entity)",
        transfer_role="MODIFIED / REPLACED SUBSTRATE — the material that changes "
        "domain; only its function is preserved.",
        definition="Physical components and assemblies (e.g. keratin/chitin vs. an "
        "aluminium fin array).",
        extraction_question="Which physical components realise this?",
        examples=("keratin scale array", "aluminium fin array", "bolted flange"),
    ),
}

RELATION_SPECS: dict[Relation, str] = {
    Relation.CREATES: "The source construct brings the target construct into existence.",
    Relation.ACTIVATES: "Input and oRgan jointly make the Effect applicable.",
    Relation.INTERPRETED_AS: "A state change is read as the achievement of an Action.",
    Relation.MODIFIES: "A state change feeds back onto a Part.",
    Relation.DEPICTS_PART: "A figure region of interest depicts a Part.",
    Relation.ILLUSTRATES_ORGAN: "A micrograph region of interest illustrates an oRgan.",
    Relation.REALIZES: "A biological strategy is realised by an engineering solution.",
}

#: Endpoint legality for the causal chain: (source, relation, target).
CAUSAL_CHAIN: tuple[tuple[Construct, Relation, Construct], ...] = (
    (Construct.PART, Relation.CREATES, Construct.ORGAN),
    (Construct.INPUT, Relation.ACTIVATES, Construct.EFFECT),
    (Construct.ORGAN, Relation.ACTIVATES, Construct.EFFECT),
    (Construct.EFFECT, Relation.CREATES, Construct.PHENOMENON),
    (Construct.PHENOMENON, Relation.CREATES, Construct.STATE_CHANGE),
    (Construct.STATE_CHANGE, Relation.INTERPRETED_AS, Construct.ACTION),
    (Construct.STATE_CHANGE, Relation.MODIFIES, Construct.PART),
)

ALLOWED_ENDPOINTS: dict[Relation, frozenset[tuple[Construct, Construct]]] = {}
for _src, _rel, _dst in CAUSAL_CHAIN:
    ALLOWED_ENDPOINTS.setdefault(_rel, frozenset())
    ALLOWED_ENDPOINTS[_rel] = ALLOWED_ENDPOINTS[_rel] | {(_src, _dst)}

#: Linking relations are construct-agnostic on the figure side.
ALLOWED_ENDPOINTS[Relation.DEPICTS_PART] = frozenset(
    {(c, Construct.PART) for c in (Construct.ORGAN, Construct.PART)}
)
ALLOWED_ENDPOINTS[Relation.ILLUSTRATES_ORGAN] = frozenset(
    {(c, Construct.ORGAN) for c in (Construct.ORGAN, Construct.PART)}
)
ALLOWED_ENDPOINTS[Relation.REALIZES] = frozenset(
    {
        (Construct.ACTION, Construct.ACTION),
        (Construct.ORGAN, Construct.PART),
        (Construct.PHENOMENON, Construct.PHENOMENON),
        (Construct.EFFECT, Construct.EFFECT),
    }
)

#: The order the chain is meant to be read in, for reporting.
CHAIN_ORDER: tuple[Construct, ...] = (
    Construct.INPUT,
    Construct.PART,
    Construct.ORGAN,
    Construct.EFFECT,
    Construct.PHENOMENON,
    Construct.STATE_CHANGE,
    Construct.ACTION,
)
