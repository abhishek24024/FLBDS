"""Shared fixtures. Everything runs offline: no model downloads, no network."""

from __future__ import annotations

import pytest

from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, Evidence, SapphireGraph


def _ev(source_id: str = "test:doc", locator: str = "paras 0001-0004") -> Evidence:
    return Evidence(source_id=source_id, source_type="paper", locator=locator)


@pytest.fixture
def lotus_graph() -> SapphireGraph:
    """A minimal but complete 7-construct graph (lotus self-cleaning)."""

    g = SapphireGraph(
        id="bio:lotus-self-cleaning",
        title="Lotus leaf self-cleaning",
        domain="biological",
        description="Hierarchical wax papillae + microtexture shed water and contaminants.",
    )
    nodes = [
        ConstructNode(
            id="I1",
            construct=Construct.INPUT,
            label="Incident water droplet + dust",
            attributes=[Attribute(name="surface tension", symbol="gamma", dimension="M T^-2", role="boundary")],
            evidence=[_ev()],
        ),
        ConstructNode(
            id="P1",
            construct=Construct.PART,
            label="Epicuticular wax crystals on papillae",
            evidence=[_ev()],
        ),
        ConstructNode(
            id="R1",
            construct=Construct.ORGAN,
            label="Hierarchical micro/nano roughness",
            attributes=[
                Attribute(name="contact angle", symbol="theta", value=162, unit="deg", dimension="", role="interface"),
                Attribute(name="papilla radius", symbol="r", value=5e-6, unit="m", dimension="L", role="interface"),
            ],
            evidence=[_ev()],
        ),
        ConstructNode(
            id="E1",
            construct=Construct.EFFECT,
            label="Young-Laplace capillary pressure",
            attributes=[
                Attribute(name="contact angle", symbol="theta", dimension=""),
                Attribute(name="papilla radius", symbol="r", dimension="L"),
                Attribute(name="surface tension", symbol="gamma", dimension="M T^-2"),
            ],
            evidence=[_ev()],
        ),
        ConstructNode(
            id="Ph1",
            construct=Construct.PHENOMENON,
            label="Cassie-Baxter droplet roll-off",
            evidence=[_ev()],
        ),
        ConstructNode(
            id="S1",
            construct=Construct.STATE_CHANGE,
            label="Contact angle hysteresis < 5 deg",
            attributes=[Attribute(name="hysteresis", symbol="dtheta", value=3, unit="deg", dimension="")],
            evidence=[_ev()],
        ),
        ConstructNode(
            id="A1",
            construct=Construct.ACTION,
            label="Remove particulate contamination passively",
            evidence=[_ev()],
        ),
    ]
    for n in nodes:
        g.add_node(n)
    for src, rel, dst in [
        ("P1", Relation.CREATES, "R1"),
        ("I1", Relation.ACTIVATES, "E1"),
        ("R1", Relation.ACTIVATES, "E1"),
        ("E1", Relation.CREATES, "Ph1"),
        ("Ph1", Relation.CREATES, "S1"),
        ("S1", Relation.INTERPRETED_AS, "A1"),
        ("S1", Relation.MODIFIES, "P1"),
    ]:
        g.add_edge(CausalEdge(source=src, target=dst, relation=rel, evidence=[_ev()]))
    return g
