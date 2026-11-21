"""V11 physics-card registry (contract: docs/v11/INTERFACES.md section 1)."""

from __future__ import annotations

from . import (
    adh_fibrillar,
    fld_riblet_drag,
    mt_fog_harvest_mesh,
    mt_plastron_membrane,
    opt_bragg_structural_color,
    str_lattice_truss,
    str_sandwich_honeycomb,
    thm_countercurrent_hx,
    thm_pcm_storage,
    thm_radiative_cooling,
    wet_superhydrophobic,
)
from .base import (
    ConstraintResult,
    DesignSchemaError,
    EnvSchemaError,
    Param,
    PhysicsCard,
    ScreenResult,
)

_MODULES = (
    thm_pcm_storage,
    thm_countercurrent_hx,
    thm_radiative_cooling,
    mt_plastron_membrane,
    str_sandwich_honeycomb,
    str_lattice_truss,
    fld_riblet_drag,
    adh_fibrillar,
    wet_superhydrophobic,
    opt_bragg_structural_color,
    mt_fog_harvest_mesh,
)
CARDS: dict[str, PhysicsCard] = {m.CARD.id: m.CARD for m in _MODULES}

__all__ = [
    "CARDS",
    "ConstraintResult",
    "DesignSchemaError",
    "EnvSchemaError",
    "Param",
    "PhysicsCard",
    "ScreenResult",
]
