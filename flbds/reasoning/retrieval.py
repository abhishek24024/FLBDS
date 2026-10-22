"""Hybrid GraphRAG retrieval objective J_GraphRAG for Aim 1.

J_GraphRAG = w_vec * S_vec + w_causal * E_causal + w_community * Sim(C_m) + w_phylo * D_phylo
Combines text ⊕ image vector similarity, causal path completeness, mechanism cluster membership,
and phylogenetic convergence rewards to return the best biological analogies for an engineering problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from flbds.graph.community import detect_mechanism_communities
from flbds.graph.store import GraphStore
from flbds.graph.taxonomy import TaxonomyGraph
from flbds.knowledge.embeddings import MultimodalEmbeddingAdapter
from flbds.ontology.constructs import Construct
from flbds.ontology.models import SapphireGraph


@dataclass
class RetrievalMatch:
    graph_id: str
    title: str
    domain: str
    score: float
    vector_sim: float
    causal_completeness: float
    community_score: float
    phylogenetic_reward: float
    shared_effects: list[str] = field(default_factory=list)
    graph: SapphireGraph | None = None


class HybridGraphRAG:
    """Retrieval engine for the Multimodal Visual-SAPPhIRE Thesaurus."""

    def __init__(
        self,
        store: GraphStore,
        embeddings: MultimodalEmbeddingAdapter | None = None,
        taxonomy: TaxonomyGraph | None = None,
        w_vec: float = 0.45,
        w_causal: float = 0.30,
        w_community: float = 0.15,
        w_phylo: float = 0.10,
    ) -> None:
        self.store = store
        self.embeddings = embeddings or MultimodalEmbeddingAdapter()
        self.taxonomy = taxonomy or TaxonomyGraph()
        self.w_vec = w_vec
        self.w_causal = w_causal
        self.w_community = w_community
        self.w_phylo = w_phylo

    def search_thesaurus(
        self,
        query_text: str,
        query_image: Any | None = None,
        target_domain: str = "biological",
        top_k: int = 5,
    ) -> list[RetrievalMatch]:
        """Execute hybrid Cypher-vector retrieval objective J_GraphRAG."""
        all_graphs = self.store.list_graphs()
        target_graphs = [g for g in all_graphs if g.domain == target_domain]
        if not target_graphs:
            return []

        # Vector embedding of query
        q_vec = self.embeddings.embed_text(query_text)
        if query_image is not None:
            img_vec = self.embeddings.embed_image(query_image)
            q_vec = 0.65 * q_vec + 0.35 * img_vec
            q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-9)

        # Mechanism communities
        communities = detect_mechanism_communities(all_graphs)

        matches: list[RetrievalMatch] = []
        for g in target_graphs:
            # 1. S_vec: similarity over Action and State change
            acts = g.nodes_of(Construct.ACTION)
            act_text = " ".join([a.label for a in acts])
            g_vec = self.embeddings.embed_text(f"{g.title} {g.description} {act_text}")
            s_vec = max(0.0, self.embeddings.cosine_similarity(q_vec, g_vec))

            # 2. E_causal: causal completeness (fraction of 7 constructs present and linked)
            cov = g.construct_coverage()
            causal_score = sum(cov.values()) / max(1, len(cov))

            # 3. Community score: check if Effect or Phenomenon words align with query
            eff_labels = [e.label.lower() for e in g.effects]
            comm_score = 0.5
            for eff in eff_labels:
                if any(w in query_text.lower() for w in eff.split()):
                    comm_score = 1.0
                    break

            # 4. Phylogenetic convergence reward
            taxon_name = g.source.get("taxon", g.title.split()[0])
            phylo_score = 0.5
            if taxon_name in self.taxonomy.tree:
                phylo_score = 0.85

            # Combined objective J_GraphRAG
            j_score = (
                self.w_vec * s_vec
                + self.w_causal * causal_score
                + self.w_community * comm_score
                + self.w_phylo * phylo_score
            )

            matches.append(
                RetrievalMatch(
                    graph_id=g.id,
                    title=g.title,
                    domain=g.domain,
                    score=round(j_score, 4),
                    vector_sim=round(s_vec, 4),
                    causal_completeness=round(causal_score, 4),
                    community_score=round(comm_score, 4),
                    phylogenetic_reward=round(phylo_score, 4),
                    shared_effects=[e.label for e in g.effects],
                    graph=g,
                )
            )

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:top_k]
