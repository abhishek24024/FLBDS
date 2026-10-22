"""FastAPI Service and Generalized Interactive Demonstration Server for FLBDS v3.0.

Provides:
1. Complete Visual-SAPPhIRE Thesaurus Search & Exploration (2,700+ biological & engineering graphs)
2. Generalized 6-Stage Analogical Design Compiler accepting arbitrary biological analogies,
   custom search queries, and custom image uploads.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw

from flbds.config import get_settings
from flbds.graph.cpc import CPCHierarchy
from flbds.graph.store import GraphStore
from flbds.graph.taxonomy import TaxonomyGraph
from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import Attribute, CausalEdge, ConstructNode, Evidence, SapphireGraph
from flbds.perception.affordance import AffordanceSegmenter
from flbds.perception.organ_tensor import OrganTensorExtractor
from flbds.reasoning.alignment import DeepGARAlignmentSolver
from flbds.reasoning.buckingham import BuckinghamAuditor
from flbds.reasoning.retrieval import HybridGraphRAG
from flbds.reasoning.triz_solver import TrizContradictionSolver
from flbds.synthesis.cad_synthesis import CadQuerySynthesizer
from flbds.synthesis.consistency import verify_tracks
from flbds.synthesis.image_synthesis import MaskLockedImageSynthesizer
from flbds.synthesis.svg_synthesis import SVGSchematicSynthesizer
from flbds.synthesis.tikz_synthesis import TikZSchematicSynthesizer

app = FastAPI(
    title="FLBDS v3.0 API",
    description="Multimodal Visual-SAPPhIRE Neuro-Symbolic Compiler for Bio-Inspired Engineering Design",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
SEEDS_DIR = Path(__file__).resolve().parent.parent / "data" / "seeds"

_STORE: GraphStore | None = None
_RAG: HybridGraphRAG | None = None


def get_store() -> GraphStore:
    global _STORE
    if _STORE is None:
        settings = get_settings()
        _STORE = GraphStore(str(settings.paths.graph_db))
    return _STORE


def get_rag() -> HybridGraphRAG:
    global _RAG
    if _RAG is None:
        _RAG = HybridGraphRAG(get_store())
    return _RAG


class PipelineRequest(BaseModel):
    query: str | None = Field(default=None, description="Free-form query or problem description")
    bio_id: str | None = Field(default=None, description="Explicit biological strategy graph ID")
    eng_id: str | None = Field(default=None, description="Explicit engineering target graph ID")
    case: str | None = Field(default=None, description="Legacy case slug (lotus, shark, gecko, etc.)")
    bio_image_b64: str | None = Field(default=None, description="Base64 encoded biological image")
    eng_image_b64: str | None = Field(default=None, description="Base64 encoded engineering baseline image")


@app.get("/health")
@app.get("/api/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "FLBDS v3.0",
        "aim_1": "Visual Biology-to-Engineering Thesaurus",
        "aim_2": "Dual-Image Analogical Design Compiler",
        "version": "3.0.0",
    }


@app.get("/api/thesaurus/stats")
def thesaurus_stats() -> dict[str, Any]:
    store = get_store()
    conn = store._get_conn()
    cur = conn.cursor()

    n_graphs = cur.execute("SELECT count(*) FROM graphs;").fetchone()[0]
    n_bio = cur.execute("SELECT count(*) FROM graphs WHERE domain = 'biological';").fetchone()[0]
    n_eng = cur.execute("SELECT count(*) FROM graphs WHERE domain = 'engineering';").fetchone()[0]
    n_nodes = cur.execute("SELECT count(*) FROM nodes;").fetchone()[0]
    n_edges = cur.execute("SELECT count(*) FROM edges;").fetchone()[0]
    n_attrs = cur.execute("SELECT count(*) FROM attributes;").fetchone()[0]
    n_ev = cur.execute("SELECT count(*) FROM evidence;").fetchone()[0]
    n_emb = cur.execute("SELECT count(*) FROM embeddings;").fetchone()[0]

    return {
        "total_graphs": n_graphs,
        "biological_graphs": n_bio,
        "engineering_graphs": n_eng,
        "total_nodes": n_nodes,
        "total_edges": n_edges,
        "total_attributes": n_attrs,
        "total_evidence": n_ev,
        "total_embeddings": n_emb,
    }


@app.get("/api/thesaurus/graphs")
def list_graphs(
    domain: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    store = get_store()
    conn = store._get_conn()
    cur = conn.cursor()

    query = "SELECT id, title, domain, description, source_json FROM graphs WHERE 1=1"
    params: list[Any] = []

    if domain:
        query += " AND domain = ?"
        params.append(domain)
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY id LIMIT ? OFFSET ?;"
    params.extend([limit, offset])

    rows = cur.execute(query, params).fetchall()
    import json
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "domain": r["domain"],
            "description": r["description"],
            "source": json.loads(r["source_json"] or "{}"),
        }
        for r in rows
    ]


@app.get("/api/thesaurus/graph/{graph_id}")
def get_graph(graph_id: str) -> dict[str, Any]:
    store = get_store()
    try:
        g = store.get_graph(graph_id)
        return g.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")


@app.get("/api/thesaurus/search")
def search_thesaurus(
    q: str = Query(..., description="Search query text"),
    domain: str = "biological",
    top_k: int = 10,
) -> list[dict[str, Any]]:
    rag = get_rag()
    matches = rag.search_thesaurus(query_text=q, target_domain=domain, top_k=top_k)
    return [
        {
            "id": m.graph_id,
            "title": m.title,
            "score": m.score,
            "vector_sim": m.vector_sim,
            "causal_completeness": m.causal_completeness,
            "community_score": m.community_score,
            "phylogenetic_reward": m.phylogenetic_reward,
            "shared_effects": m.shared_effects,
        }
        for m in matches
    ]


def _decode_or_create_image(img_b64: str | None, label: str, mode: str = "bio") -> Image.Image:
    if img_b64:
        try:
            if "," in img_b64:
                img_b64 = img_b64.split(",", 1)[1]
            raw = base64.b64decode(img_b64)
            return Image.open(io.BytesIO(raw)).convert("RGB").resize((260, 260))
        except Exception:
            pass

    # Synthesize illustrative domain image
    im = Image.new("RGB", (260, 260), color=(15, 25, 20) if mode == "bio" else (130, 140, 150))
    d = ImageDraw.Draw(im)

    if mode == "bio":
        # Microstructure pattern
        for i in range(12):
            for j in range(12):
                d.ellipse([10 + i * 20, 10 + j * 20, 22 + i * 20, 22 + j * 20], fill=(45, 170, 95), outline=(20, 90, 45))
        d.text((12, 12), f"Biological: {label[:24]}", fill=(220, 255, 230))
    else:
        # Engineering housing with keep-out datum
        d.rectangle([20, 20, 240, 240], fill=(160, 170, 180), outline=(40, 50, 60), width=2)
        d.rectangle([20, 20, 240, 60], fill=(210, 170, 170), outline=(180, 40, 40), width=2)
        d.text((30, 35), "KEEP-OUT DATUM FLANGE", fill=(160, 20, 20))
        d.rectangle([40, 80, 220, 220], fill=(175, 195, 220), outline=(20, 90, 180), width=2)
        d.text((50, 140), f"MODIFIABLE CORE (M_Eng)", fill=(20, 60, 120))
        d.text((15, 242), f"{label[:32]}", fill=(60, 70, 80))

    return im


def _image_to_b64(im: Image.Image) -> str:
    b = io.BytesIO()
    im.save(b, format="PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("utf-8")


LEGACY_CASE_MAP = {
    "lotus": ("bio_lotus-self-cleaning.json", "eng_superhydrophobic-facade.json"),
    "shark": ("bio_shark-denticles.json", "eng_riblet-fuselage-film.json"),
    "gecko": ("bio_gecko-setae.json", "eng_dry-adhesive-gripper.json"),
    "kingfisher": ("bio_kingfisher-beak.json", "eng_shinkansen-nose.json"),
    "termite": ("bio_termite-mound.json", "eng_eastgate-centre.json"),
}


@app.post("/api/pipeline/run")
def run_pipeline(
    req: PipelineRequest = Body(default=None),
    case: str | None = Query(default=None),
    query: str | None = Query(default=None),
) -> dict[str, Any]:
    store = get_store()
    rag = get_rag()

    # Determine biological graph
    g_bio: SapphireGraph | None = None
    g_eng: SapphireGraph | None = None

    req_query = (req.query if req else None) or query
    req_bio_id = req.bio_id if req else None
    req_eng_id = req.eng_id if req else None
    req_case = (req.case if req else None) or case

    if req_bio_id:
        try:
            g_bio = store.get_graph(req_bio_id)
        except KeyError:
            pass

    if g_bio is None and req_query:
        matches = rag.search_thesaurus(query_text=req_query, target_domain="biological", top_k=1)
        if matches and matches[0].graph:
            g_bio = matches[0].graph
        elif matches:
            g_bio = store.get_graph(matches[0].graph_id)

    if g_bio is None and req_case and req_case in LEGACY_CASE_MAP:
        bio_file, _ = LEGACY_CASE_MAP[req_case]
        if (SEEDS_DIR / bio_file).exists():
            g_bio = SapphireGraph.from_json(SEEDS_DIR / bio_file)

    if g_bio is None:
        # Default fallback to first biological graph in database
        bio_graphs = store.list_graphs(domain="biological")
        g_bio = bio_graphs[0] if bio_graphs else SapphireGraph(id="bio:default", title="Biological Base")

    # Determine engineering graph
    if req_eng_id:
        try:
            g_eng = store.get_graph(req_eng_id)
        except KeyError:
            pass

    if g_eng is None:
        # Check if paired engineering graph exists
        paired_app = g_bio.source.get("application", "")
        if paired_app:
            eng_matches = rag.search_thesaurus(query_text=paired_app, target_domain="engineering", top_k=1)
            if eng_matches and eng_matches[0].graph:
                g_eng = eng_matches[0].graph

    if g_eng is None and req_case and req_case in LEGACY_CASE_MAP:
        _, eng_file = LEGACY_CASE_MAP[req_case]
        if (SEEDS_DIR / eng_file).exists():
            g_eng = SapphireGraph.from_json(SEEDS_DIR / eng_file)

    if g_eng is None:
        eng_graphs = store.list_graphs(domain="engineering")
        g_eng = eng_graphs[0] if eng_graphs else SapphireGraph(id="eng:default", title="Engineering Target")

    # Stage 1: Dual-Image Perception & Affordance Parsing
    img_bio = _decode_or_create_image(req.bio_image_b64 if req else None, g_bio.title, mode="bio")
    img_eng = _decode_or_create_image(req.eng_image_b64 if req else None, g_eng.title, mode="eng")

    segmenter = AffordanceSegmenter()
    masks = segmenter.segment_masks(img_eng)
    organ_tensor = OrganTensorExtractor().extract_tensor_field(img_bio)

    # Stage 3: DeepGAR Continuous Order-Embedding Subgraph Alignment
    aligner = DeepGARAlignmentSolver()
    alignment = aligner.align(g_bio, g_eng)

    # Stage 4: Buckingham Pi Similitude & Scaling Audit
    auditor = BuckinghamAuditor()
    eff_name = g_bio.effects[0].label if g_bio.effects else "cassie_baxter"
    audit = auditor.audit_effect(eff_name, {}, {}, length_scale_ratio=15.0)

    # Stage 5: Compiler-Verified TRIZ Contradiction Solver
    solver = TrizContradictionSolver()
    triz_res = solver.resolve(g_bio, g_eng, scale_audit=audit)

    # Stage 6: Multi-Track Synthesis
    synth_out_img, keep_out_mse = MaskLockedImageSynthesizer().synthesize(img_eng, masks)

    target_graph = triz_res.modified_graph or g_eng
    svg_str = SVGSchematicSynthesizer().synthesize(target_graph)
    tikz_str = TikZSchematicSynthesizer().synthesize(target_graph)

    cad_synth = CadQuerySynthesizer()
    cad_script = cad_synth.generate_script(target_graph)
    cad_rep = cad_synth.execute_and_verify(cad_script)

    consistency = verify_tracks(
        keep_out_mse=keep_out_mse,
        svg_valid=SVGSchematicSynthesizer.validate_svg(svg_str),
        cad_report=cad_rep,
    )

    previews = {
        "bio_image": _image_to_b64(img_bio),
        "eng_baseline": _image_to_b64(img_eng),
        "synthesized_render": _image_to_b64(synth_out_img.resize((260, 260))),
    }

    return {
        "case": req_case or "custom",
        "bio_graph": g_bio.to_dict(),
        "eng_graph": g_eng.to_dict(),
        "perception": {
            "organ_tensor": organ_tensor.to_dict(),
            "affordance_masks": {
                "modifiable_core_pixels": int((masks.m_eng > 0).sum()),
                "keep_out_datum_pixels": int((masks.keep_out > 0).sum()),
                "strictly_disjoint": masks.verify_disjoint(),
            },
        },
        "alignment": {
            "alignment_f1": alignment.alignment_f1,
            "one_to_one": alignment.one_to_one_passed,
            "parallel_connectivity": alignment.parallel_connectivity_passed,
            "mappings_count": len(alignment.mappings),
        },
        "scaling_audit": {
            "effect_id": audit.effect_id,
            "length_scale_ratio": audit.length_scale_ratio,
            "has_violations": audit.has_violations,
            "v_scale_total": audit.v_scale_total,
        },
        "triz_resolution": {
            "physical_contradiction": triz_res.physical_contradiction,
            "separation_operator": triz_res.separation_operator,
            "topological_subdivision": triz_res.topological_subdivision,
            "inventive_principles": [{"id": p.id, "name": p.name} for p in triz_res.inventive_principles],
        },
        "synthesis": {
            "keep_out_drift_mse": keep_out_mse,
            "previews": previews,
            "dangling_edge_length": cad_rep.dangling_edge_length,
            "cad_script_valid": cad_rep.script_valid,
            "svg_schematic": svg_str,
            "tikz_code": tikz_str,
            "cad_script": cad_script,
            "consistency_verified": consistency.tracks_agree,
        },
    }


@app.get("/", response_class=HTMLResponse)
def index_page() -> str:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>FLBDS v3.0 API</h1><p>Demo UI index.html not found.</p>"
