"""Mechanism Active Ingredient Community Detection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from flbds.ontology.constructs import Construct
from flbds.ontology.models import SapphireGraph


def detect_mechanism_communities(graphs: list[SapphireGraph]) -> dict[str, list[str]]:
    """Partition graphs into mechanism active ingredient clusters C_m based on shared Effects and Phenomena."""
    clusters: dict[str, list[str]] = defaultdict(list)

    for g in graphs:
        # Key cluster by canonical governing Effect or Phenomenon
        effs = g.effects
        if effs:
            key = effs[0].label.strip().lower()
        else:
            ph = g.nodes_of(Construct.PHENOMENON)
            key = ph[0].label.strip().lower() if ph else "general_mechanism"
        clusters[key].append(g.id)

    return dict(clusters)
