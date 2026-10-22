"""BioSpark Tree-of-Life taxonomic hierarchy and phylogenetic distance.

Encodes: Species -> Genus -> Family -> Order -> Class -> Phylum -> Kingdom
Computes Lowest Common Ancestor (LCA) height and phylogenetic distance D_phylo
to reward evolutionary convergent solutions across disparate lineages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

TAXONOMIC_RANKS = ("species", "genus", "family", "order", "class", "phylum", "kingdom")


@dataclass
class TaxonNode:
    name: str
    rank: str
    parent: str | None = None


# Comprehensive multi-kingdom Tree-of-Life spanning Animalia, Plantae, Fungi, and Bacteria
TAXONOMY_TREE: dict[str, TaxonNode] = {
    # Roots
    "Biota": TaxonNode("Biota", "root", None),

    # Kingdom Animalia
    "Animalia": TaxonNode("Animalia", "kingdom", "Biota"),
    "Chordata": TaxonNode("Chordata", "phylum", "Animalia"),
    "Chondrichthyes": TaxonNode("Chondrichthyes", "class", "Chordata"),
    "Lamniformes": TaxonNode("Lamniformes", "order", "Chondrichthyes"),
    "Lamnidae": TaxonNode("Lamnidae", "family", "Lamniformes"),
    "Isurus": TaxonNode("Isurus", "genus", "Lamnidae"),
    "Isurus oxyrinchus": TaxonNode("Isurus oxyrinchus", "species", "Isurus"),  # Shortfin mako shark
    "Carcharhiniformes": TaxonNode("Carcharhiniformes", "order", "Chondrichthyes"),
    "Galeomorphi": TaxonNode("Galeomorphi", "subclass", "Chondrichthyes"),

    "Actinopterygii": TaxonNode("Actinopterygii", "class", "Chordata"),
    "Perciformes": TaxonNode("Perciformes", "order", "Actinopterygii"),
    "Scombridae": TaxonNode("Scombridae", "family", "Perciformes"),
    "Thunnus": TaxonNode("Thunnus", "genus", "Scombridae"),  # Tuna

    "Reptilia": TaxonNode("Reptilia", "class", "Chordata"),
    "Squamata": TaxonNode("Squamata", "order", "Reptilia"),
    "Gekkonidae": TaxonNode("Gekkonidae", "family", "Squamata"),
    "Gekko": TaxonNode("Gekko", "genus", "Gekkonidae"),
    "Gekko gecko": TaxonNode("Gekko gecko", "species", "Gekko"),  # Tokay gecko
    "Chamaeleonidae": TaxonNode("Chamaeleonidae", "family", "Squamata"),
    "Chamaeleo": TaxonNode("Chamaeleo", "genus", "Chamaeleonidae"),  # Chameleon

    "Aves": TaxonNode("Aves", "class", "Chordata"),
    "Coraciiformes": TaxonNode("Coraciiformes", "order", "Aves"),
    "Alcedinidae": TaxonNode("Alcedinidae", "family", "Coraciiformes"),
    "Alcedo": TaxonNode("Alcedo", "genus", "Alcedinidae"),
    "Alcedo atthis": TaxonNode("Alcedo atthis", "species", "Alcedo"),  # Common kingfisher
    "Strigiformes": TaxonNode("Strigiformes", "order", "Aves"),  # Owls (silent flight)
    "Tytonidae": TaxonNode("Tytonidae", "family", "Strigiformes"),
    "Sphenisciformes": TaxonNode("Sphenisciformes", "order", "Aves"),  # Penguins (hydrodynamics)

    "Mammalia": TaxonNode("Mammalia", "class", "Chordata"),
    "Cetacea": TaxonNode("Cetacea", "order", "Mammalia"),
    "Balaenopteridae": TaxonNode("Balaenopteridae", "family", "Cetacea"),
    "Megaptera": TaxonNode("Megaptera", "genus", "Balaenopteridae"),
    "Megaptera novaeangliae": TaxonNode("Megaptera novaeangliae", "species", "Megaptera"),  # Humpback whale
    "Chiroptera": TaxonNode("Chiroptera", "order", "Mammalia"),  # Bats (echolocation)
    "Primates": TaxonNode("Primates", "order", "Mammalia"),
    "Hominidae": TaxonNode("Hominidae", "family", "Primates"),
    "Homo": TaxonNode("Homo", "genus", "Hominidae"),

    "Arthropoda": TaxonNode("Arthropoda", "phylum", "Animalia"),
    "Insecta": TaxonNode("Insecta", "class", "Arthropoda"),
    "Blattodea": TaxonNode("Blattodea", "order", "Insecta"),
    "Termitidae": TaxonNode("Termitidae", "family", "Blattodea"),
    "Macrotermes": TaxonNode("Macrotermes", "genus", "Termitidae"),
    "Macrotermes bellicosus": TaxonNode("Macrotermes bellicosus", "species", "Macrotermes"),
    "Coleoptera": TaxonNode("Coleoptera", "order", "Insecta"),  # Beetles (Stenocara fog harvesting)
    "Tenebrionidae": TaxonNode("Tenebrionidae", "family", "Coleoptera"),
    "Stenocara": TaxonNode("Stenocara", "genus", "Tenebrionidae"),
    "Lepidoptera": TaxonNode("Lepidoptera", "order", "Insecta"),  # Butterflies (Morpho structural color)
    "Nymphalidae": TaxonNode("Nymphalidae", "family", "Lepidoptera"),
    "Morpho": TaxonNode("Morpho", "genus", "Nymphalidae"),
    "Hymenoptera": TaxonNode("Hymenoptera", "order", "Insecta"),  # Bees / Ants (honeycomb, adhesives)
    "Apidae": TaxonNode("Apidae", "family", "Hymenoptera"),
    "Apis": TaxonNode("Apis", "genus", "Apidae"),
    "Formicidae": TaxonNode("Formicidae", "family", "Hymenoptera"),
    "Odonata": TaxonNode("Odonata", "order", "Insecta"),  # Dragonflies (flight control)

    "Arachnida": TaxonNode("Arachnida", "class", "Arthropoda"),
    "Araneae": TaxonNode("Araneae", "order", "Arachnida"),  # Spiders (silk tensile strength)
    "Araneidae": TaxonNode("Araneidae", "family", "Araneae"),

    "Mollusca": TaxonNode("Mollusca", "phylum", "Animalia"),
    "Cephalopoda": TaxonNode("Cephalopoda", "class", "Mollusca"),
    "Octopoda": TaxonNode("Octopoda", "order", "Cephalopoda"),  # Octopus (suction, camouflage)
    "Bivalvia": TaxonNode("Bivalvia", "class", "Mollusca"),
    "Mytilida": TaxonNode("Mytilida", "order", "Bivalvia"),
    "Mytilidae": TaxonNode("Mytilidae", "family", "Mytilida"),
    "Mytilus": TaxonNode("Mytilus", "genus", "Mytilidae"),  # Blue mussel (catechol underwater adhesion)
    "Gastropoda": TaxonNode("Gastropoda", "class", "Mollusca"),  # Snails / Limpets

    "Cnidaria": TaxonNode("Cnidaria", "phylum", "Animalia"),
    "Anthozoa": TaxonNode("Anthozoa", "class", "Cnidaria"),  # Corals (calcium carbonate matrices, fluorescent proteins)
    "Discosoma": TaxonNode("Discosoma", "genus", "Anthozoa"),

    "Porifera": TaxonNode("Porifera", "phylum", "Animalia"),
    "Hexactinellida": TaxonNode("Hexactinellida", "class", "Porifera"),
    "Euplectella": TaxonNode("Euplectella", "genus", "Hexactinellida"),  # Venus flower basket (hierarchical glass fiber)

    "Echinodermata": TaxonNode("Echinodermata", "phylum", "Animalia"),
    "Echinoidea": TaxonNode("Echinoidea", "class", "Echinodermata"),  # Sea urchins (Aristotle's lantern rock drilling)

    # Kingdom Plantae
    "Plantae": TaxonNode("Plantae", "kingdom", "Biota"),
    "Tracheophyta": TaxonNode("Tracheophyta", "phylum", "Plantae"),
    "Magnoliopsida": TaxonNode("Magnoliopsida", "class", "Tracheophyta"),
    "Proteales": TaxonNode("Proteales", "order", "Magnoliopsida"),
    "Nelumbonaceae": TaxonNode("Nelumbonaceae", "family", "Proteales"),
    "Nelumbo": TaxonNode("Nelumbo", "genus", "Nelumbonaceae"),
    "Nelumbo nucifera": TaxonNode("Nelumbo nucifera", "species", "Nelumbo"),  # Sacred lotus
    "Nepenthales": TaxonNode("Nepenthales", "order", "Magnoliopsida"),
    "Nepenthaceae": TaxonNode("Nepenthaceae", "family", "Nepenthales"),
    "Nepenthes": TaxonNode("Nepenthes", "genus", "Nepenthaceae"),  # Pitcher plant (slippery lubricant surfaces)
    "Fabales": TaxonNode("Fabales", "order", "Magnoliopsida"),
    "Poales": TaxonNode("Poales", "order", "Magnoliopsida"),  # Grasses, Bamboo (high strength-to-weight tubular beams)
    "Caryophyllales": TaxonNode("Caryophyllales", "order", "Magnoliopsida"),
    "Cactaceae": TaxonNode("Cactaceae", "family", "Caryophyllales"),  # Cacti (spines, fog collecting)
    "Pinopsida": TaxonNode("Pinopsida", "class", "Tracheophyta"),  # Conifers (pinecones hygroscopic opening)
    "Pinales": TaxonNode("Pinales", "order", "Pinopsida"),
    "Pinaceae": TaxonNode("Pinaceae", "family", "Pinales"),
    "Pinus": TaxonNode("Pinus", "genus", "Pinaceae"),

    # Kingdom Fungi
    "Fungi": TaxonNode("Fungi", "kingdom", "Biota"),
    "Basidiomycota": TaxonNode("Basidiomycota", "phylum", "Fungi"),
    "Agaricomycetes": TaxonNode("Agaricomycetes", "class", "Basidiomycota"),  # Mushrooms, mycelium composites

    # Kingdom Bacteria
    "Bacteria": TaxonNode("Bacteria", "kingdom", "Biota"),
    "Pseudomonadota": TaxonNode("Pseudomonadota", "phylum", "Bacteria"),
    "Actinomycetota": TaxonNode("Actinomycetota", "phylum", "Bacteria"),
    "Bacillota": TaxonNode("Bacillota", "phylum", "Bacteria"),
}

# Organism / Keyword mapping to canonical taxon
KEYWORD_TO_TAXON: list[tuple[str, str]] = [
    (r"\b(?:shark|mako|denticle|selachimorpha)\b", "Isurus oxyrinchus"),
    (r"\b(?:gecko|setae|fibril|squamata)\b", "Gekko gecko"),
    (r"\b(?:lotus|nelumbo|superhydrophobic|self-cleaning)\b", "Nelumbo nucifera"),
    (r"\b(?:kingfisher|alcedo|beak|plunge)\b", "Alcedo atthis"),
    (r"\b(?:termite|macrotermes|mound|ventilation)\b", "Macrotermes bellicosus"),
    (r"\b(?:whale|humpback|megaptera|tubercle|flipper)\b", "Megaptera novaeangliae"),
    (r"\b(?:mussel|mytilus|catechol|byssus)\b", "Mytilus"),
    (r"\b(?:pitcher\s+plant|nepenthes|slippery)\b", "Nepenthes"),
    (r"\b(?:stenocara|namib|fog\s+beetle|beetle|elytra)\b", "Stenocara"),
    (r"\b(?:butterfly|morpho|wing\s+scale|structural\s+color)\b", "Morpho"),
    (r"\b(?:spider|silk|dragline|araneae)\b", "Araneae"),
    (r"\b(?:coral|discosoma|polyps|anthozoa)\b", "Discosoma"),
    (r"\b(?:sponge|euplectella|glass\s+sponge)\b", "Euplectella"),
    (r"\b(?:cactus|cacti|spine|areole)\b", "Cactaceae"),
    (r"\b(?:pine\s*cone|pinus|hygroscopic|conifer)\b", "Pinus"),
    (r"\b(?:bamboo|grass|poales|stem)\b", "Poales"),
    (r"\b(?:owl|feather|fringe|silent\s+flight)\b", "Strigiformes"),
    (r"\b(?:penguin|sphenisciformes|plumage)\b", "Sphenisciformes"),
    (r"\b(?:octopus|squid|cuttlefish|cephalopod)\b", "Cephalopoda"),
    (r"\b(?:bee|honeycomb|wasp|ant|formicidae)\b", "Hymenoptera"),
    (r"\b(?:dragonfly|odonata)\b", "Odonata"),
    (r"\b(?:tuna|fish|teleost|fin|schooling)\b", "Actinopterygii"),
    (r"\b(?:bat|echolocation|chiroptera)\b", "Chiroptera"),
    (r"\b(?:mycelium|fungus|fungi|mushroom)\b", "Basidiomycota"),
    (r"\b(?:bacteria|bacterium|microbe|bacillus|escherichia)\b", "Bacteria"),
    (r"\b(?:plant|leaf|flora|tree|stem|root|bark)\b", "Plantae"),
    (r"\b(?:insect|arthropod|bug)\b", "Insecta"),
    (r"\b(?:bird|avian|feather)\b", "Aves"),
    (r"\b(?:mammal|fur|hair)\b", "Mammalia"),
]


class TaxonomyGraph:
    """Tree-of-Life taxonomy and phylogenetic distance calculator."""

    def __init__(self, tree: dict[str, TaxonNode] | None = None) -> None:
        self.tree = tree or TAXONOMY_TREE

    def resolve_taxon(self, text: str) -> str:
        """Map an organism name, text query, or biological source to its nearest taxon."""
        clean = text.strip()
        # Direct tree lookup
        if clean in self.tree:
            return clean

        # Title/case variations
        for name in self.tree:
            if name.lower() == clean.lower():
                return name

        # Pattern / keyword matching
        for pattern, canonical_taxon in KEYWORD_TO_TAXON:
            if re.search(pattern, text, re.IGNORECASE):
                return canonical_taxon

        # Default fallback to Animalia
        return "Animalia"

    def lineage(self, taxon_name: str) -> list[str]:
        path = []
        curr = taxon_name
        # Resolve if needed
        if curr not in self.tree:
            curr = self.resolve_taxon(curr)

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
        return "Biota", len(lineage_a) + len(lineage_b)

    def phylogenetic_reward(self, taxon_a: str, taxon_b: str) -> float:
        """Reward evolutionary convergence across distantly related clades (0.0 to 1.0)."""
        _, dist = self.lowest_common_ancestor(taxon_a, taxon_b)
        # Larger distance indicates higher evolutionary convergence (scaled up to 10 hops)
        return min(1.0, round(dist / 10.0, 4))
