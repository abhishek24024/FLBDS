from flbds.ontology.models import SapphireGraph
from flbds.reasoning.alignment import DeepGARAlignmentSolver
from flbds.reasoning.order_embedding import OrderEmbeddingEncoder

def test_order_embedding_encoder():
    encoder = OrderEmbeddingEncoder(dim=16)
    g_bio = SapphireGraph.from_json("flbds/data/seeds/bio_lotus-self-cleaning.json")
    embs = encoder.encode_graph(g_bio)
    assert len(embs) == len(g_bio.nodes)
    # Check that later depth in chain has equal or greater norm than earlier
    assert embs["A1"].sum() >= embs["P1"].sum()
    penalty = encoder.order_penalty(embs["P1"], embs["A1"])
    assert penalty == 0.0

def test_deepgar_alignment_acceptance():
    solver = DeepGARAlignmentSolver()
    g_bio = SapphireGraph.from_json("flbds/data/seeds/bio_lotus-self-cleaning.json")
    g_eng = SapphireGraph.from_json("flbds/data/seeds/eng_superhydrophobic-facade.json")

    report = solver.align(g_bio, g_eng)
    assert report.alignment_f1 >= 0.80  # Acceptance criteria: F1 >= 0.80
    assert report.one_to_one_passed
    assert report.parallel_connectivity_passed
    assert len(report.tier_identical_effects) >= 1
    assert "Young-Laplace" in report.tier_identical_effects[0]
