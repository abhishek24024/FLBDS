from flbds.ontology.constructs import Construct, Relation, CAUSAL_CHAIN, CHAIN_ORDER
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, Evidence, SapphireGraph
from flbds.ontology.validate import validate_graph, Severity

def test_lotus_graph_validation(lotus_graph):
    report = validate_graph(lotus_graph, strict_abductive=True)
    assert report.ok
    assert len(report.errors) == 0
    assert report.metrics["construct_coverage"] == 1.0
    assert report.metrics["grounding_ratio"] == 1.0

def test_missing_construct_warning(lotus_graph):
    # Remove Action node
    lotus_graph.nodes = [n for n in lotus_graph.nodes if n.construct is not Construct.ACTION]
    lotus_graph.edges = [e for e in lotus_graph.edges if e.target != "A1"]
    report = validate_graph(lotus_graph, strict_abductive=False)
    assert any(i.code == "MISSING_CONSTRUCT" for i in report.warnings)

def test_abductive_variable_gap():
    g = SapphireGraph(id="test:abductive-gap", title="Test Gap", domain="biological")
    g.add_node(ConstructNode(id="I1", construct=Construct.INPUT, label="Input"))
    g.add_node(ConstructNode(id="P1", construct=Construct.PART, label="Part"))
    g.add_node(ConstructNode(id="R1", construct=Construct.ORGAN, label="Organ"))
    g.add_node(ConstructNode(
        id="E1",
        construct=Construct.EFFECT,
        label="Young-Laplace",
        attributes=[Attribute(name="surface tension", symbol="gamma", dimension="M T^-2")],
    ))
    g.add_node(ConstructNode(id="Ph1", construct=Construct.PHENOMENON, label="Phenomenon"))
    g.add_node(ConstructNode(id="S1", construct=Construct.STATE_CHANGE, label="State change"))
    g.add_node(ConstructNode(id="A1", construct=Construct.ACTION, label="Action"))

    g.add_edge(CausalEdge(source="P1", target="R1", relation=Relation.CREATES))
    g.add_edge(CausalEdge(source="I1", target="E1", relation=Relation.ACTIVATES))
    g.add_edge(CausalEdge(source="R1", target="E1", relation=Relation.ACTIVATES))
    g.add_edge(CausalEdge(source="E1", target="Ph1", relation=Relation.CREATES))
    g.add_edge(CausalEdge(source="Ph1", target="S1", relation=Relation.CREATES))
    g.add_edge(CausalEdge(source="S1", target="A1", relation=Relation.INTERPRETED_AS))

    report = validate_graph(g, strict_abductive=True, require_evidence=False)
    assert not report.ok
    assert any(i.code == "ABDUCTIVE_VARIABLE_GAP" for i in report.errors)
