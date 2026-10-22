"""FastAPI Service and Interactive Demonstration Server for FLBDS v3.0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from flbds.config import get_settings
from flbds.graph.store import GraphStore
from flbds.ontology.models import SapphireGraph
from flbds.perception.affordance import AffordanceSegmenter
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


def get_store() -> GraphStore:
    global _STORE
    if _STORE is None:
        settings = get_settings()
        _STORE = GraphStore(str(settings.paths.graph_db))
        # Preload seeds if store is empty
        if len(_STORE.list_graphs()) < 10 and SEEDS_DIR.exists():
            for sf in SEEDS_DIR.glob("*.json"):
                g = SapphireGraph.from_json(sf)
                _STORE.save_graph(g)
    return _STORE


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


@app.get("/api/thesaurus/graphs")
def list_graphs(domain: str | None = None) -> list[dict[str, Any]]:
    store = get_store()
    graphs = store.list_graphs(domain=domain)
    return [{"id": g.id, "title": g.title, "domain": g.domain, "description": g.description} for g in graphs]


@app.get("/api/thesaurus/graph/{graph_id}")
def get_graph(graph_id: str) -> dict[str, Any]:
    store = get_store()
    try:
        g = store.get_graph(graph_id)
        return g.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")


@app.get("/api/thesaurus/search")
def search_thesaurus(q: str = Query(..., description="Query query text"), domain: str = "biological") -> list[dict[str, Any]]:
    store = get_store()
    rag = HybridGraphRAG(store)
    matches = rag.search_thesaurus(query_text=q, target_domain=domain, top_k=5)
    return [
        {
            "id": m.graph_id,
            "title": m.title,
            "score": m.score,
            "vector_sim": m.vector_sim,
            "causal_completeness": m.causal_completeness,
            "shared_effects": m.shared_effects,
        }
        for m in matches
    ]



def _create_case_images(case: str, masks: Any, out_img: Any) -> dict[str, str]:
    import base64, io
    from PIL import Image, ImageDraw

    # 1. Biological image
    img_bio = Image.new("RGB", (260, 260), color=(15, 30, 20))
    d_bio = ImageDraw.Draw(img_bio)
    for i in range(12):
        for j in range(12):
            d_bio.ellipse([10 + i * 20, 10 + j * 20, 22 + i * 20, 22 + j * 20], fill=(40, 160, 90), outline=(20, 80, 40))
    d_bio.text((15, 12), f"Biological Source: {case.title()}", fill=(220, 255, 230))

    # 2. Engineering Baseline with Keep-out overlay
    img_eng = Image.new("RGB", (260, 260), color=(140, 150, 160))
    d_eng = ImageDraw.Draw(img_eng)
    d_eng.rectangle([20, 20, 240, 240], fill=(160, 170, 180), outline=(40, 50, 60), width=2)
    # Mounting flanges (keepout) in red
    d_eng.rectangle([20, 20, 240, 60], fill=(220, 180, 180), outline=(180, 40, 40), width=2)
    d_eng.text((30, 35), "KEEP-OUT DATUM FLANGE", fill=(160, 20, 20))
    # Modifiable zone in light blue
    d_eng.rectangle([40, 80, 220, 220], fill=(180, 200, 220), outline=(20, 100, 180), width=2)
    d_eng.text((50, 140), "MODIFIABLE CORE (M_Eng)", fill=(20, 60, 120))

    def _to_b64(im):
        b = io.BytesIO()
        im.save(b, format="PNG")
        return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("utf-8")

    return {
        "bio_image": _to_b64(img_bio),
        "eng_baseline": _to_b64(img_eng),
        "synthesized_render": _to_b64(out_img.resize((260, 260))),
    }

CASE_MAP = {
    "lotus": ("bio_lotus-self-cleaning.json", "eng_superhydrophobic-facade.json"),
    "shark": ("bio_shark-denticles.json", "eng_riblet-fuselage-film.json"),
    "gecko": ("bio_gecko-setae.json", "eng_dry-adhesive-gripper.json"),
    "kingfisher": ("bio_kingfisher-beak.json", "eng_shinkansen-nose.json"),
    "termite": ("bio_termite-mound.json", "eng_eastgate-centre.json"),
}


@app.post("/api/pipeline/run")
def run_pipeline(case: str = Query("lotus")) -> dict[str, Any]:
    if case not in CASE_MAP:
        case = "lotus"
    bio_file, eng_file = CASE_MAP[case]

    g_bio = SapphireGraph.from_json(SEEDS_DIR / bio_file)
    g_eng = SapphireGraph.from_json(SEEDS_DIR / eng_file)

    # Stage 3: DeepGAR Subgraph Alignment
    aligner = DeepGARAlignmentSolver()
    alignment = aligner.align(g_bio, g_eng)

    # Stage 4: Buckingham Pi Similitude Audit
    auditor = BuckinghamAuditor()
    eff_id = g_bio.effects[0].label if g_bio.effects else "fourier_conduction"
    audit = auditor.audit_effect(eff_id, {}, {}, length_scale_ratio=20.0)

    # Stage 5: Compiler-Verified TRIZ Contradiction Solver
    solver = TrizContradictionSolver()
    triz_res = solver.resolve(g_bio, g_eng, scale_audit=audit)

    # Stage 6: Multi-Track Synthesis
    from PIL import Image
    dummy_img = Image.new("RGB", (260, 260), color=(180, 180, 180))
    masks = AffordanceSegmenter().segment_masks(dummy_img)
    synth_out_img, keep_out_mse = MaskLockedImageSynthesizer().synthesize(dummy_img, masks)
    previews = _create_case_images(case, masks, synth_out_img)

    svg_str = SVGSchematicSynthesizer().synthesize(triz_res.modified_graph or g_eng)
    tikz_str = TikZSchematicSynthesizer().synthesize(triz_res.modified_graph or g_eng)

    cad_synth = CadQuerySynthesizer()
    cad_script = cad_synth.generate_script(triz_res.modified_graph or g_eng)
    cad_rep = cad_synth.execute_and_verify(cad_script)

    consistency = verify_tracks(
        keep_out_mse=keep_out_mse,
        svg_valid=SVGSchematicSynthesizer.validate_svg(svg_str),
        cad_report=cad_rep,
    )

    return {
        "case": case,
        "bio_graph": g_bio.to_dict(),
        "eng_graph": g_eng.to_dict(),
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
