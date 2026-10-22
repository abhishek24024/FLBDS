"""Hybrid GraphRAG retrieval objective J_GraphRAG for Aim 1.

J_GraphRAG = w_vec * S_vec + w_causal * E_causal + w_community * Sim(C_m) + w_phylo * D_phylo
Combines text ⊕ image vector similarity, causal path completeness, mechanism cluster membership,
and phylogenetic convergence rewards across the complete Visual-SAPPhIRE Thesaurus.
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
        # 1. Vector embedding of query
        q_vec = self.embeddings.embed_text(query_text)
        if query_image is not None:
            img_vec = self.embeddings.embed_image(query_image)
            q_vec = 0.65 * q_vec + 0.35 * img_vec
            q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-9)

        # 2. Fast candidate retrieval using vector index
        # Search candidate pool proportional to top_k
        candidate_pool_size = max(12, top_k * 2)
        vector_candidates = self.store.vector_search(q_vec, modality="text", top_k=candidate_pool_size)

        candidate_graphs: list[SapphireGraph] = []
        candidate_sims: dict[str, float] = {}

        if vector_candidates:
            for entity_id, cos_sim in vector_candidates:
                try:
                    g = self.store.get_graph(entity_id)
                    if g.domain == target_domain:
                        candidate_graphs.append(g)
                        candidate_sims[g.id] = cos_sim
                except KeyError:
                    continue

        # Fallback if no vector candidates matched the domain
        if not candidate_graphs:
            all_graphs = self.store.list_graphs(domain=target_domain)
            candidate_graphs = all_graphs[:candidate_pool_size]
            for g in candidate_graphs:
                g_vec = self.embeddings.embed_text(f"{g.title} {g.description}")
                candidate_sims[g.id] = max(0.0, self.embeddings.cosine_similarity(q_vec, g_vec))

        # Query taxon inference for phylogenetic reward
        query_taxon = self.taxonomy.resolve_taxon(query_text)

        matches: list[RetrievalMatch] = []
        for g in candidate_graphs:
            # 1. S_vec
            s_vec = candidate_sims.get(g.id, 0.0)

            # 2. E_causal: causal completeness across 7 constructs
            cov = g.construct_coverage()
            causal_score = sum(cov.values()) / max(1, len(cov))

            # 3. Community score: align governing Effect or Phenomenon keywords with query
            eff_labels = [e.label.lower() for e in g.effects]
            ph_labels = [ph.label.lower() for ph in g.nodes_of(Construct.PHENOMENON)]
            comm_score = 0.5
            q_tokens = set(query_text.lower().split())
            for lbl in eff_labels + ph_labels:
                if any(w in lbl for w in q_tokens if len(w) > 3):
                    comm_score = 1.0
                    break

            # 4. Phylogenetic convergence reward D_phylo
            graph_taxon = g.source.get("taxon") or self.taxonomy.resolve_taxon(g.title)
            phylo_score = self.taxonomy.phylogenetic_reward(query_taxon, graph_taxon)

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
