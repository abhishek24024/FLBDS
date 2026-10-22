from flbds.ontology.models import SapphireGraph
from flbds.reasoning.buckingham import BuckinghamAuditor
from flbds.reasoning.triz_solver import TrizContradictionSolver

def test_triz_solver_resolution():
    solver = TrizContradictionSolver()
    g_bio = SapphireGraph.from_json("flbds/data/seeds/bio_termite-mound.json")
    g_eng = SapphireGraph.from_json("flbds/data/seeds/eng_eastgate-centre.json")

    # Force a scaling violation by scaling from 15cm termite flue to 8m building atrium
    auditor = BuckinghamAuditor()
    audit = auditor.audit_effect(
        "fourier_conduction",
        {"h": 25.0, "L_c": 0.004, "k_s": 1.2},
        {"h": 20.0, "L_c": 8.0, "k_s": 1.5},
        length_scale_ratio=53.3,
    )
    assert audit.has_violations

    resolution = solver.resolve(g_bio, g_eng, scale_audit=audit)
    assert resolution.type_check_passed
    assert resolution.physical_contradiction is not None
    assert "Separation" in resolution.separation_operator
    assert "TPMS" in resolution.topological_subdivision or "Voronoi" in resolution.topological_subdivision

    # Verify principles are valid canonical 1..40
    assert len(resolution.inventive_principles) > 0
    assert all(1 <= p.id <= 40 for p in resolution.inventive_principles)

    # Verify graph rewrite
    assert resolution.graph_rewrite_applied
    assert resolution.modified_graph is not None
    assert "Bio-Synthesized" in resolution.modified_graph.title
