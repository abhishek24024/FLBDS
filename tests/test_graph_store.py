import numpy as np
from flbds.graph.store import GraphStore

def test_graph_roundtrip(lotus_graph):
    store = GraphStore(":memory:")
    store.save_graph(lotus_graph)
    loaded = store.get_graph(lotus_graph.id)

    assert loaded.id == lotus_graph.id
    assert loaded.title == lotus_graph.title
    assert loaded.domain == lotus_graph.domain
    assert len(loaded.nodes) == len(lotus_graph.nodes)
    assert len(loaded.edges) == len(lotus_graph.edges)

def test_backward_causal_path(lotus_graph):
    store = GraphStore(":memory:")
    store.save_graph(lotus_graph)
    path = store.backward_causal_path(lotus_graph.id, "A1")
    assert len(path) == 7
    endpoints = {e.source for e in path} | {e.target for e in path}
    assert "P1" in endpoints
    assert "A1" in endpoints

def test_vector_search(lotus_graph):
    store = GraphStore(":memory:")
    store.save_graph(lotus_graph)
    store.store_embedding("A1", "text", np.array([1.0, 0.0], dtype=np.float32))
    store.store_embedding("P1", "text", np.array([0.0, 1.0], dtype=np.float32))

    res = store.vector_search(np.array([0.9, 0.1], dtype=np.float32), "text", top_k=1)
    assert len(res) == 1
    assert res[0][0] == "A1"
