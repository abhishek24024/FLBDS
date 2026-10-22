import numpy as np
from PIL import Image

from flbds.ontology.models import SapphireGraph
from flbds.perception.affordance import AffordanceSegmenter
from flbds.synthesis.cad_synthesis import CadQuerySynthesizer
from flbds.synthesis.consistency import verify_tracks
from flbds.synthesis.image_synthesis import MaskLockedImageSynthesizer
from flbds.synthesis.svg_synthesis import SVGSchematicSynthesizer
from flbds.synthesis.tikz_synthesis import TikZSchematicSynthesizer

def test_mask_locked_render_zero_drift():
    # Acceptance criteria: unmasked drift MSE = 0
    img = Image.new("RGB", (100, 100), color=(150, 150, 150))
    segmenter = AffordanceSegmenter()
    masks = segmenter.segment_masks(img)

    synthesizer = MaskLockedImageSynthesizer()
    out_img, mse = synthesizer.synthesize(img, masks)

    assert out_img.size == (100, 100)
    assert mse == 0.0, f"Expected 0.0 drift MSE, got {mse}"

def test_svg_schematic_synthesis_no_raster():
    # Acceptance criteria: SVG renders without raster fallback
    g = SapphireGraph.from_json("flbds/data/seeds/bio_lotus-self-cleaning.json")
    synthesizer = SVGSchematicSynthesizer()
    svg_str = synthesizer.synthesize(g)

    assert SVGSchematicSynthesizer.validate_svg(svg_str)
    assert "<svg" in svg_str
    assert "<image" not in svg_str  # Pure vector primitives

def test_tikz_schematic_synthesis():
    g = SapphireGraph.from_json("flbds/data/seeds/eng_eastgate-centre.json")
    synthesizer = TikZSchematicSynthesizer()
    tikz_str = synthesizer.synthesize(g)
    assert r"\begin{tikzpicture}" in tikz_str
    assert r"\end{tikzpicture}" in tikz_str

def test_cadquery_synthesis_and_watertightness():
    # Acceptance criteria: 100% of emitted scripts execute, DangEL = 0
    g = SapphireGraph.from_json("flbds/data/seeds/bio_shark-denticles.json")
    synthesizer = CadQuerySynthesizer()
    script = synthesizer.generate_script(g)
    assert "import cadquery as cq" in script

    report = synthesizer.execute_and_verify(script)
    assert report.script_valid
    assert report.is_watertight
    assert report.dangling_edge_length == 0.0

def test_track_consistency_auditor():
    cad_report = CadQuerySynthesizer().execute_and_verify("a = 1")
    rep = verify_tracks(keep_out_mse=0.0, svg_valid=True, cad_report=cad_report)
    assert rep.tracks_agree
    assert rep.image_render_verified
    assert rep.svg_schematic_verified
    assert rep.cad_model_verified
