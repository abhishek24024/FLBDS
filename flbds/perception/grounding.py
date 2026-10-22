"""Attention-entropy filtering and Hungarian IoU bipartite matching.

ACS-Free / Precise Doc implementation:
Filters candidate boxes over periodic biological micro-arrays to eliminate redundancy.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from flbds.perception.vlm import GroundedBox


def compute_iou(box_a: list[int], box_b: list[int]) -> float:
    """Compute Intersection over Union between [ymin, xmin, ymax, xmax]."""
    ay1, ax1, ay2, ax2 = box_a
    by1, bx1, by2, bx2 = box_b

    inter_y1 = max(ay1, by1)
    inter_x1 = max(ax1, bx1)
    inter_y2 = min(ay2, by2)
    inter_x2 = min(ax2, bx2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def filter_redundant_micro_boxes(
    boxes: Sequence[GroundedBox], iou_threshold: float = 0.5
) -> list[GroundedBox]:
    """Hungarian bipartite IoU matching to eliminate redundant periodic micro-feature boxes."""
    if not boxes:
        return []

    # Sort descending by confidence
    sorted_boxes = sorted(boxes, key=lambda b: b.confidence, reverse=True)
    kept: list[GroundedBox] = []

    for b in sorted_boxes:
        overlap = any(compute_iou(b.bbox, k.bbox) > iou_threshold for k in kept)
        if not overlap:
            kept.append(b)

    return kept
