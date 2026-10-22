"""BioSpark Tree-of-Life taxonomic hierarchy and phylogenetic distance.

Encodes: Species -> Genus -> Family -> Order -> Class -> Phylum -> Kingdom
Computes Lowest Common Ancestor (LCA) height and phylogenetic distance D_phylo
to reward evolutionary convergent solutions across disparate lineages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TAXONOMIC_RANKS = ("species", "genus", "family", "order", "class", "phylum", "kingdom")


@dataclass
class TaxonNode:
    name: str
    rank: str
    parent: str | None = None


# Seed Tree-of-Life for core biological analogies
TAXONOMY_TREE: dict[str, TaxonNode] = {
    # Kingdom Animalia
    "Animalia": TaxonNode("Animalia", "kingdom", None),
    "Chordata": TaxonNode("Chordata", "phylum", "Animalia"),
    "Chondrichthyes": TaxonNode("Chondrichthyes", "class", "Chordata"),
    "Lamniformes": TaxonNode("Lamniformes", "order", "Chondrichthyes"),
    "Lamnidae": TaxonNode("Lamnidae", "family", "Lamniformes"),
    "Isurus": TaxonNode("Isurus", "genus", "Lamnidae"),
    "Isurus oxyrinchus": TaxonNode("Isurus oxyrinchus", "species", "Isurus"), # Mako shark

    "Reptilia": TaxonNode("Reptilia", "class", "Chordata"),
    "Squamata": TaxonNode("Squamata", "order", "Reptilia"),
    "Gekkonidae": TaxonNode("Gekkonidae", "family", "Squamata"),
    "Gekko": TaxonNode("Gekko", "genus", "Gekkonidae"),
    "Gekko gecko": TaxonNode("Gekko gecko", "species", "Gekko"), # Tokay gecko

    "Aves": TaxonNode("Aves", "class", "Chordata"),
    "Coraciiformes": TaxonNode("Coraciiformes", "order", "Aves"),
    "Alcedinidae": TaxonNode("Alcedinidae", "family", "Coraciiformes"),
    "Alcedo": TaxonNode("Alcedo", "genus", "Alcedinidae"),
    "Alcedo atthis": TaxonNode("Alcedo atthis", "species", "Alcedo"), # Kingfisher

    "Arthropoda": TaxonNode("Arthropoda", "phylum", "Animalia"),
    "Insecta": TaxonNode("Insecta", "class", "Arthropoda"),
    "Blattodea": TaxonNode("Blattodea", "order", "Insecta"),
    "Termitidae": TaxonNode("Termitidae", "family", "Blattodea"),
    "Macrotermes": TaxonNode("Macrotermes", "genus", "Termitidae"),
    "Macrotermes bellicosus": TaxonNode("Macrotermes bellicosus", "species", "Macrotermes"),

    # Kingdom Plantae
    "Plantae": TaxonNode("Plantae", "kingdom", None),
    "Tracheophyta": TaxonNode("Tracheophyta", "phylum", "Plantae"),
    "Magnoliopsida": TaxonNode("Magnoliopsida", "class", "Tracheophyta"),
    "Proteales": TaxonNode("Proteales", "order", "Magnoliopsida"),
    "Nelumbonaceae": TaxonNode("Nelumbonaceae", "family", "Proteales"),
    "Nelumbo": TaxonNode("Nelumbo", "genus", "Nelumbonaceae"),
    "Nelumbo nucifera": TaxonNode("Nelumbo nucifera", "species", "Nelumbo"), # Sacred lotus
}


class TaxonomyGraph:
    """Tree-of-Life taxonomy and phylogenetic distance calculator."""

    def __init__(self, tree: dict[str, TaxonNode] | None = None) -> None:
        self.tree = tree or TAXONOMY_TREE

    def lineage(self, taxon_name: str) -> list[str]:
        path = []
        curr = taxon_name
        while curr and curr in self.tree:
            path.append(curr)
            curr = self.tree[curr].parent
        return path

    def lowest_common_ancestor(self, taxon_a: str, taxon_b: str) -> tuple[str | None, int]:
        """Compute LCA and tree height distance."""
        lineage_a = self.lineage(taxon_a)
        lineage_b = self.lineage(taxon_b)
        set_b = set(lineage_b)

        for depth_a, anc in enumerate(lineage_a):
            if anc in set_b:
                depth_b = lineage_b.index(anc)
                return anc, depth_a + depth_b
        return None, 10 # Root separation

    def phylogenetic_reward(self, taxon_a: str, taxon_b: str) -> float:
        """Reward evolutionary convergence across distantly related clades (0.0 to 1.0)."""
        _, dist = self.lowest_common_ancestor(taxon_a, taxon_b)
        # Larger distance indicates higher evolutionary convergence
        return min(1.0, dist / 8.0)
