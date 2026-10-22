import numpy as np
from PIL import Image

from flbds.perception.affordance import AffordanceSegmenter
from flbds.perception.grounding import compute_iou, filter_redundant_micro_boxes
from flbds.perception.organ_tensor import OrganTensorExtractor
from flbds.perception.vlm import GroundedBox, VLMPerceptionAdapter

def test_vlm_adapter():
    adapter = VLMPerceptionAdapter(backend="reference")
    img = Image.new("RGB", (100, 100), color=(200, 200, 200))
    boxes_bio = adapter.parse_image_coordinates(img, "biological microstructures")
    assert len(boxes_bio) > 0
    assert all(b.attributes.get("role") == "organ" for b in boxes_bio)

    boxes_eng = adapter.parse_image_coordinates(img, "engineering housing")
    assert len(boxes_eng) == 2
    assert any("modifiable" in b.label for b in boxes_eng)

def test_iou_and_filtering():
    b1 = [0, 0, 50, 50]
    b2 = [0, 0, 50, 50]
    assert compute_iou(b1, b2) == 1.0

    b3 = [60, 60, 100, 100]
    assert compute_iou(b1, b3) == 0.0

    boxes = [
        GroundedBox(box_id="1", label="pore", bbox=[0, 0, 50, 50], confidence=0.9),
        GroundedBox(box_id="2", label="pore", bbox=[5, 5, 55, 55], confidence=0.8), # Redundant
        GroundedBox(box_id="3", label="pore", bbox=[60, 60, 100, 100], confidence=0.95),
    ]
    kept = filter_redundant_micro_boxes(boxes, iou_threshold=0.5)
    assert len(kept) == 2
    assert {k.box_id for k in kept} == {"1", "3"}

def test_affordance_masks_disjoint():
    segmenter = AffordanceSegmenter()
    img = Image.new("RGB", (120, 120), color=(180, 180, 180))
    masks = segmenter.segment_masks(img)

    assert masks.height == 120
    assert masks.width == 120
    assert masks.verify_disjoint()
    assert masks.modifiable_ratio > 0.0
    # Every pixel must be assigned to either M_Eng or Keep-Out
    assert np.all(masks.m_eng + masks.keep_out == 1)

def test_organ_tensor_extraction():
    extractor = OrganTensorExtractor()
    # Create image with textured pattern
    arr = np.zeros((64, 64), dtype=np.uint8)
    arr[20:44, 20:44] = 255
    img = Image.fromarray(arr, mode="L")

    tensor = extractor.extract_tensor_field(img)
    assert tensor.edge_skeleton.shape == (64, 64)
    assert tensor.normal_gradients.shape == (64, 64, 2)
    assert 0.0 <= tensor.porosity <= 1.0
    assert tensor.mean_gradient_magnitude > 0.0
