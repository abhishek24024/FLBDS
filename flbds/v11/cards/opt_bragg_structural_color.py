"""OPT_BRAGG_STRUCTURAL_COLOR: two-material quarter-wave multilayer reflector."""

from __future__ import annotations

import math

from .base import ConstraintResult, Param, PhysicsCard, ge, le

QW_RATIO_WINDOW = (0.8, 1.25)


def peak_wavelength(n1: float, d1: float, n2: float, d2: float) -> float:
    """First-order Bragg peak, normal incidence: lambda = 2 (n1 d1 + n2 d2)."""
    return 2.0 * (n1 * d1 + n2 * d2)


def peak_reflectance(
    n_hi: float, n_lo: float, n_pairs: int, n0: float, ns: float
) -> float:
    """Quarter-wave stack (Macleod): R = ((1 - q)/(1 + q))^2, q = (ns/n0)(nH/nL)^(2N)."""
    q = (ns / n0) * (n_hi / n_lo) ** (2 * n_pairs)
    return ((1.0 - q) / (1.0 + q)) ** 2


def bandwidth(lam: float, n1: float, n2: float) -> float:
    """Stop-band full width: d_lambda = (4 lambda/pi) asin(|n1-n2|/(n1+n2))."""
    return 4.0 * lam / math.pi * math.asin(abs(n1 - n2) / (n1 + n2))


def _screen(
    d: dict[str, float], e: dict[str, float]
) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    n1, d1, n2, d2 = (
        d["n_layer1"],
        d["thickness_layer1_m"],
        d["n_layer2"],
        d["thickness_layer2_m"],
    )
    npairs = math.floor(d["n_pairs"])
    lam = peak_wavelength(n1, d1, n2, d2)
    rr = peak_reflectance(
        max(n1, n2), min(n1, n2), npairs, e["incident_index"], e["substrate_index"]
    )
    bw = bandwidth(lam, n1, n2)
    total = npairs * (d1 + d2)
    cons = [
        le(
            "peak_wavelength_error_m",
            abs(lam - e["target_wavelength_m"]),
            e["wavelength_tolerance_m"],
            "m",
        ),
        ge("peak_reflectance", rr, e["min_peak_reflectance"], "-"),
        le("total_thickness_m", total, e["max_total_thickness_m"], "m"),
        le("stopband_width_m", bw, e["max_bandwidth_m"], "m"),
        ge("min_layer_thickness_m", min(d1, d2), e["min_layer_thickness_m"], "m"),
    ]
    notes: list[str] = []
    ratio = (n1 * d1) / (n2 * d2)
    if not (QW_RATIO_WINDOW[0] <= ratio <= QW_RATIO_WINDOW[1]):
        notes.append(
            f"optical thickness ratio n1d1/n2d2 = {ratio:.2f} outside quarter-wave window {QW_RATIO_WINDOW}"
        )
    if abs(n1 - n2) < 0.02:
        notes.append("index contrast < 0.02: no usable stop band")
    return (
        cons,
        notes,
        {
            "peak_wavelength_m": lam,
            "peak_reflectance": rr,
            "bandwidth_m": bw,
            "total_thickness_m": total,
            "pairs": float(npairs),
            "optical_ratio": ratio,
        },
    )


CARD = PhysicsCard(
    id="OPT_BRAGG_STRUCTURAL_COLOR",
    domain="optics",
    title="Multilayer Bragg reflector for structural colour / spectral mirror",
    principle=(
        "N bilayers of indices n1, n2 and thicknesses d1, d2 reflect constructively at lambda = 2(n1 d1 + n2 d2) "
        "(normal incidence, first order). For quarter-wave layers the peak reflectance is "
        "R = ((1 - (ns/n0)(nH/nL)^2N)/(1 + (ns/n0)(nH/nL)^2N))^2 and the stop-band width is "
        "(4 lambda/pi) asin(|n1-n2|/(n1+n2)). Total thickness N(d1+d2)."
    ),
    bio_exemplars=[
        "Morpho butterfly wing-scale lamellae",
        "jewel beetle (Buprestidae) cuticle multilayer",
        "silver fish scales (guanine platelets)",
        "Pollia condensata fruit (helicoidal multilayer)",
    ],
    design_space=[
        Param(
            "n_layer1",
            1.3,
            2.6,
            "-",
            "refractive index of layer 1 (SiO2 1.46, TiO2 2.4, chitin 1.56)",
        ),
        Param("thickness_layer1_m", 2.0e-8, 5.0e-7, "m", "layer-1 thickness d1"),
        Param(
            "n_layer2",
            1.0,
            2.6,
            "-",
            "refractive index of layer 2 (air gaps 1.0 as in Morpho)",
        ),
        Param("thickness_layer2_m", 2.0e-8, 5.0e-7, "m", "layer-2 thickness d2"),
        Param("n_pairs", 1.0, 40.0, "-", "number of bilayers N (floored to integer)"),
    ],
    env_space=[
        Param(
            "target_wavelength_m",
            3.5e-7,
            2.5e-6,
            "m",
            "target reflection peak wavelength",
        ),
        Param("wavelength_tolerance_m", 2.0e-9, 1.0e-7, "m", "allowed |peak - target|"),
        Param("min_peak_reflectance", 0.1, 0.9999, "-", "required peak reflectance"),
        Param("max_total_thickness_m", 1.0e-7, 2.0e-5, "m", "maximum stack thickness"),
        Param(
            "max_bandwidth_m",
            1.0e-8,
            1.0e-6,
            "m",
            "maximum stop-band width (colour purity)",
        ),
        Param(
            "min_layer_thickness_m",
            5.0e-9,
            1.0e-7,
            "m",
            "minimum depositable layer thickness",
        ),
        Param("incident_index", 1.0, 1.6, "-", "incident medium index n0"),
        Param("substrate_index", 1.0, 4.0, "-", "substrate index ns"),
    ],
    references=[
        "Macleod H.A. (2010) Thin-Film Optical Filters, 4th ed., CRC (quarter-wave stack reflectance, stop band).",
        "Hecht E. Optics, 5th ed., sec. 9.7 (multilayer films).",
        ("Kinoshita S., Yoshioka S. (2005) Structural colors in nature: the role of regularity and irregularity, "
        "ChemPhysChem 6:1442."),
        "Vukusic P., Sambles J.R. (2003) Photonic structures in biology, Nature 424:852.",
    ],
    _screen=_screen,
)
