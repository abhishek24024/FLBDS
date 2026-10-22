"""Multi-Track Consistency Auditor for Image, SVG, and CAD Blueprints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flbds.synthesis.cad_synthesis import CadExecutionReport


@dataclass
class ConsistencyReport:
    image_render_verified: bool
    svg_schematic_verified: bool
    cad_model_verified: bool
    keep_out_drift_mse: float
    dangling_edge_length: float
    tracks_agree: bool

    def summary(self) -> str:
        status = "CONSISTENT" if self.tracks_agree else "MISMATCH"
        return (
            f"Consistency[{status}] drift_MSE={self.keep_out_drift_mse:.6f} "
            f"DangEL={self.dangling_edge_length:.4f} tracks={{render: {self.image_render_verified}, "
            f"svg: {self.svg_schematic_verified}, cad: {self.cad_model_verified}}}"
        )


def verify_tracks(
    keep_out_mse: float,
    svg_valid: bool,
    cad_report: CadExecutionReport,
) -> ConsistencyReport:
    """Cross-verify the three synthesis tracks."""
    img_ok = (keep_out_mse == 0.0)
    cad_ok = (cad_report.script_valid and cad_report.is_watertight and cad_report.dangling_edge_length == 0.0)
    all_agree = img_ok and svg_valid and cad_ok

    return ConsistencyReport(
        image_render_verified=img_ok,
        svg_schematic_verified=svg_valid,
        cad_model_verified=cad_ok,
        keep_out_drift_mse=keep_out_mse,
        dangling_edge_length=cad_report.dangling_edge_length,
        tracks_agree=all_agree,
    )
