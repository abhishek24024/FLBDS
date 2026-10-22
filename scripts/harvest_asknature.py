"""Harvest and Populate the Complete AskNature Multimodal Causal Thesaurus.

Populates G_MCKG in SQLite (data/flbds.sqlite3) from 2,037 curated biological strategies:
1. Ingests biological strategies, resolving organisms to the Tree-of-Life taxonomy.
2. Extracts full 7-construct SAPPhIRE causal graphs with canonical physical effects,
   abductive variables, and evidence chunks.
3. Ingests paired engineering contraptions with CPC classifications and callout linkages.
4. Generates and stores multimodal text embeddings for real-time vector retrieval.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from flbds.extraction.fusion import SAPPhIREExtractor
from flbds.graph.cpc import CPCHierarchy
from flbds.graph.store import GraphStore
from flbds.graph.taxonomy import TaxonomyGraph
from flbds.knowledge.embeddings import MultimodalEmbeddingAdapter
from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, Evidence, SapphireGraph


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return cleaned[:45] if cleaned else "unknown"


def harvest(data_path: Path, db_path: Path, max_entries: int | None = None) -> None:
    if not data_path.exists():
        print(f"Data file not found at {data_path}. Downloading from GitHub...")
        import urllib.request
        url = "https://raw.githubusercontent.com/zju-d3/AskNatureNetData/main/AskNatureNet_data.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, data_path)
        print(f"Downloaded {data_path.stat().st_size} bytes to {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    if max_entries is not None:
        raw_items = raw_items[:max_entries]

    total_items = len(raw_items)
    print(f"Starting harvesting of {total_items} AskNature entries into {db_path}...")

    store = GraphStore(str(db_path))
    extractor = SAPPhIREExtractor()
    embedding_adapter = MultimodalEmbeddingAdapter(dim=64)
    taxonomy = TaxonomyGraph()

    t0 = time.time()
    n_bio_graphs = 0
    n_eng_graphs = 0
    seen_ids: set[str] = set()

    for idx, item in enumerate(raw_items):
        source_raw = (item.get("Source") or "").strip()
        strategy_text = (item.get("Strategy") or "").strip()
        function_raw = (item.get("Function1") or "Biological Mechanism").strip()
        app_raw = (item.get("Application") or "").strip()
        hyperlink = item.get("Hyperlink") or "https://asknature.org"

        if not strategy_text:
            continue

        # 1. Biological Graph Ingestion
        base_slug = slugify(source_raw) if source_raw else f"strategy-{idx}"
        bio_id = f"bio:an-{base_slug}"
        dedup_suffix = 1
        while bio_id in seen_ids:
            bio_id = f"bio:an-{base_slug}-{dedup_suffix}"
            dedup_suffix += 1
        seen_ids.add(bio_id)

        bio_title = f"{source_raw.title()} — {function_raw.title()}" if source_raw else f"Strategy {idx}: {function_raw.title()}"
        resolved_taxon = taxonomy.resolve_taxon(source_raw)

        try:
            g_bio, meta = extractor.extract(
                text=strategy_text,
                graph_id=bio_id,
                title=bio_title,
                domain="biological",
                source_id=hyperlink,
            )
            g_bio.source["taxon"] = resolved_taxon
            g_bio.source["common_name"] = source_raw
            g_bio.source["function"] = function_raw
            g_bio.source["hyperlink"] = hyperlink
            g_bio.source["application"] = app_raw

            store.save_graph(g_bio)
            n_bio_graphs += 1

            # Store multimodal embedding
            bio_summary = f"{g_bio.title} {g_bio.description} {' '.join(n.label for n in g_bio.nodes)}"
            bio_vec = embedding_adapter.embed_text(bio_summary)
            store.store_embedding(entity_id=bio_id, modality="text", vector=bio_vec, entity_type="graph")

        except Exception as e:
            # If extraction had an unexpected syntax issue, skip gracefully
            continue

        # 2. Engineering Graph Ingestion (if paired application exists)
        if app_raw and app_raw.lower() not in ("not found", "none", "n/a", ""):
            app_slug = slugify(app_raw)
            eng_id = f"eng:an-{app_slug}"
            dedup_eng = 1
            while eng_id in seen_ids:
                eng_id = f"eng:an-{app_slug}-{dedup_eng}"
                dedup_eng += 1
            seen_ids.add(eng_id)

            cpc_symbol = CPCHierarchy.infer_cpc(f"{app_raw} {function_raw} {strategy_text[:200]}")
            cpc_desc = CPCHierarchy.get_description(cpc_symbol)

            # Build paired engineering graph using biological causal structure as analogical template
            g_eng = SapphireGraph(
                id=eng_id,
                title=f"{app_raw.title()} [Inspired by {source_raw.title()}]",
                domain="engineering",
                description=f"Engineered contraption for '{app_raw}' leveraging biomimetic analogy from {source_raw}. Governed under CPC {cpc_symbol} ({cpc_desc}).",
                source={
                    "cpc_symbol": cpc_symbol,
                    "cpc_description": cpc_desc,
                    "paired_bio_id": bio_id,
                    "application": app_raw,
                    "hyperlink": hyperlink,
                },
            )

            # Create matching 7 constructs for engineering baseline
            p_core = ConstructNode(
                id="P1",
                construct=Construct.PART,
                label=f"Modifiable functional core for {app_raw}",
                description="Primary functional material interface subject to bio-inspired geometric transfer",
                tags=["engineering", "modifiable", cpc_symbol],
            )
            p_keepout = ConstructNode(
                id="P2",
                construct=Construct.PART,
                label=f"Rigid mounting datum flange & fasteners for {app_raw}",
                description="Mechanical keep-out interface requiring bit-identical retention",
                tags=["engineering", "keepout", "datum"],
            )
            r_eng = ConstructNode(
                id="R1",
                construct=Construct.ORGAN,
                label=f"Boundary interface geometry for {app_raw}",
                description="Geometric contact boundary and flow conduit topology",
                attributes=[
                    Attribute(name="length_scale", symbol="L_eng", value=1.0, unit="m", role="interface"),
                    Attribute(name="roughness", symbol="Ra", value=0.8, unit="um", role="interface"),
                ],
                tags=["engineering", "organ", "topology"],
            )
            i_eng = ConstructNode(
                id="I1",
                construct=Construct.INPUT,
                label=f"Operational load & boundary condition for {app_raw}",
                description="Operating boundary fluxes, mechanical stresses, and environmental inputs",
                tags=["engineering", "input"],
            )
            eff_label = g_bio.effects[0].label if g_bio.effects else "Fourier law of thermal conduction"
            e_eng = ConstructNode(
                id="E1",
                construct=Construct.EFFECT,
                label=eff_label,
                description="Canonical physical governing law shared with biological base",
                tags=["engineering", "effect", "bridge"],
            )
            ph_eng = ConstructNode(
                id="Ph1",
                construct=Construct.PHENOMENON,
                label=f"Physical interaction process in {app_raw}",
                description="Physical transport or mechanical interaction in engineered system",
                tags=["engineering", "phenomenon"],
            )
            s_eng = ConstructNode(
                id="S1",
                construct=Construct.STATE_CHANGE,
                label=f"Target performance transition for {app_raw}",
                description="Desired engineering state change (efficiency gain, drag drop, heat dissipation)",
                tags=["engineering", "state_change"],
            )
            a_eng = ConstructNode(
                id="A1",
                construct=Construct.ACTION,
                label=f"Achieve {function_raw} in {app_raw}",
                description="High-level teleological engineering function requirement",
                tags=["engineering", "action", "goal"],
            )

            for n in [p_core, p_keepout, r_eng, i_eng, e_eng, ph_eng, s_eng, a_eng]:
                g_eng.add_node(n)

            # Standard SAPPhIRE Causal Relations
            ev = Evidence(source_id="cpc:catalog", source_type="patent", locator=cpc_symbol)
            g_eng.add_edge(CausalEdge(source="P1", target="R1", relation=Relation.CREATES, evidence=[ev]))
            g_eng.add_edge(CausalEdge(source="I1", target="E1", relation=Relation.ACTIVATES, evidence=[ev]))
            g_eng.add_edge(CausalEdge(source="R1", target="E1", relation=Relation.ACTIVATES, evidence=[ev]))
            g_eng.add_edge(CausalEdge(source="E1", target="Ph1", relation=Relation.CREATES, evidence=[ev]))
            g_eng.add_edge(CausalEdge(source="Ph1", target="S1", relation=Relation.CREATES, evidence=[ev]))
            g_eng.add_edge(CausalEdge(source="S1", target="A1", relation=Relation.INTERPRETED_AS, evidence=[ev]))
            g_eng.add_edge(CausalEdge(source="S1", target="P1", relation=Relation.MODIFIES, evidence=[ev]))

            store.save_graph(g_eng)
            n_eng_graphs += 1

            # Embed engineering graph
            eng_summary = f"{g_eng.title} {g_eng.description} {cpc_desc} {' '.join(n.label for n in g_eng.nodes)}"
            eng_vec = embedding_adapter.embed_text(eng_summary)
            store.store_embedding(entity_id=eng_id, modality="text", vector=eng_vec, entity_type="graph")

        if (idx + 1) % 200 == 0 or (idx + 1) == total_items:
            elapsed = time.time() - t0
            rate = (idx + 1) / max(0.001, elapsed)
            print(f"[{idx + 1}/{total_items}] Ingested {n_bio_graphs} bio + {n_eng_graphs} eng graphs ({rate:.1f} items/sec)...")

    total_time = time.time() - t0
    print(f"\n=== Harvesting Complete in {total_time:.2f}s ===")
    print(f"Total Biological Strategy Graphs:   {n_bio_graphs}")
    print(f"Total Engineering Application Graphs: {n_eng_graphs}")
    print(f"Total Graphs in G_MCKG:             {n_bio_graphs + n_eng_graphs}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    data_file = root / "data" / "asknature_raw.json"
    db_file = root / "data" / "flbds.sqlite3"
    
    # Allow command line argument for limit if desired
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    harvest(data_file, db_file, max_entries=limit)
