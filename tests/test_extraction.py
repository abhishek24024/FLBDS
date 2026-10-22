from flbds.extraction.rules import DeterministicRuleExtractor
from flbds.extraction.hyde import HyDECorrectiveRAG
from flbds.extraction.fusion import SAPPhIREExtractor
from flbds.ontology.constructs import Construct
from flbds.ontology.validate import validate_graph

SAMPLE_BIO_TEXT = """
The lotus leaf (Nelumbo nucifera) exhibits remarkable self-cleaning properties.
The surface consists of epicuticular wax crystals on convex papillae, having a hierarchical
roughness with contact angle theta = 162 deg and papilla radius r = 5 um.
When subjected to incident water droplet deposition with surface tension gamma = 0.072 N/m,
the interface activates the Young-Laplace capillary law. This creates Cassie-Baxter air-trapping
droplet roll-off, resulting in contact angle hysteresis reduction below 5 degrees.
This mechanism acts to shed particulate contamination passively.
"""

def test_deterministic_rule_extractor():
    extractor = DeterministicRuleExtractor()
    inter = extractor.parse_intermediate(SAMPLE_BIO_TEXT)
    assert len(inter.physical_laws) > 0
    assert "Young-Laplace capillary law" in inter.physical_laws
    assert len(inter.state_changes) > 0
    assert len(inter.conditions) > 0

    g = extractor.extract_graph(
        text=SAMPLE_BIO_TEXT,
        graph_id="bio:test-lotus",
        title="Lotus Self-Cleaning",
        domain="biological",
    )
    assert len(g.nodes) == 7
    assert len(g.edges) == 7
    rep = validate_graph(g, strict_abductive=True)
    assert rep.ok

def test_hyde_corrective_rag():
    rag = HyDECorrectiveRAG(groundedness_threshold=0.76)
    chunks = rag.chunk_document(SAMPLE_BIO_TEXT, chunk_size=50, overlap=10)
    assert len(chunks) >= 1

    retrieved = rag.retrieve_chunks("capillary surface tension droplet", chunks, top_k=2)
    assert len(retrieved) > 0

    score = rag.compute_groundedness("Young-Laplace capillary law water droplet", SAMPLE_BIO_TEXT)
    assert score >= 0.75

    res = rag.extract_with_hyde(SAMPLE_BIO_TEXT, system_name="Lotus", domain="biological")
    assert len(res) == 7
    assert all(c.groundedness_score >= 0.76 for c in res.values())

def test_end_to_end_extractor_and_abductive_repair():
    extractor = SAPPhIREExtractor()
    graph, meta = extractor.extract(
        text=SAMPLE_BIO_TEXT,
        graph_id="bio:fused-lotus",
        title="Fused Lotus",
        domain="biological",
    )
    assert meta["valid"]
    assert meta["n_errors"] == 0
    assert meta["construct_coverage"] == 1.0
    assert meta["grounding_ratio"] == 1.0
    assert len(graph.effects) == 1
    assert len(graph.nodes) == 7
