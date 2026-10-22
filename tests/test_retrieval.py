from pathlib import Path
import numpy as np
from PIL import Image

from flbds.graph.cpc import CPCHierarchy
from flbds.graph.store import GraphStore
from flbds.graph.taxonomy import TaxonomyGraph
from flbds.knowledge.embeddings import MultimodalEmbeddingAdapter
from flbds.ontology.models import SapphireGraph
from flbds.reasoning.retrieval import HybridGraphRAG

def test_multimodal_embeddings():
    adapter = MultimodalEmbeddingAdapter(dim=64)
    v_text = adapter.embed_text("lotus leaf self-cleaning surface")
    assert v_text.shape == (64,)
    assert abs(np.linalg.norm(v_text) - 1.0) < 1e-5

    # Test image embedding with PIL synthetic image
    img = Image.new("RGB", (32, 32), color=(100, 150, 200))
    v_img = adapter.embed_image(img)
    assert v_img.shape == (64,)
    assert abs(np.linalg.norm(v_img) - 1.0) < 1e-5

def test_taxonomy_graph_and_lca():
    tax = TaxonomyGraph()
    # Isurus oxyrinchus (Mako shark) vs Gekko gecko (Gecko)
    lca, dist = tax.lowest_common_ancestor("Isurus oxyrinchus", "Gekko gecko")
    assert lca in ("Chordata", "Animalia")
    assert dist > 0

    reward = tax.phylogenetic_reward("Isurus oxyrinchus", "Alcedo atthis")
    assert 0.0 <= reward <= 1.0

def test_cpc_hierarchy():
    desc = CPCHierarchy.get_description("B64C")
    assert "Aircraft" in desc or "Aeroplanes" in desc

def test_hybrid_graphrag_retrieval():
    store = GraphStore(":memory:")
    # Seed with all 10 graphs
    seeds_dir = Path("flbds/data/seeds")
    for p in seeds_dir.glob("*.json"):
        g = SapphireGraph.from_json(p)
        store.save_graph(g)

    engine = HybridGraphRAG(store)
    # Search biological analogies for drag reduction
    matches = engine.search_thesaurus(
        query_text="hydrodynamic skin friction drag reduction riblets Navier-Stokes",
        target_domain="biological",
        top_k=3,
    )
    assert len(matches) > 0
    top_match = matches[0]
    assert "shark" in top_match.graph_id.lower()
    assert top_match.causal_completeness == 1.0
    assert top_match.score > 0.6
