# FLBDS V11 — module interfaces (contract shared by all builders)

V11 = biology-first, image-driven, physics-checked design. Package: `flbds/v11/`.
Pipeline: organism image (+ optional caption) → **Perceive** (VLM) → **Mechanism card** → **Analogy** (Mode B: pick problems from the library; Mode A: problem given) → **Design** (choose physics card + parameters, screen feedback, repair) → **Blueprint** (structured description + SVG sketch + optional rendered image).

## 1. Physics cards — `flbds/v11/cards/`

```python
@dataclass(frozen=True)
class Param:            # one design or environment variable
    name: str           # snake_case incl. SI unit suffix, e.g. "cell_size_m"
    lo: float; hi: float
    unit: str           # "m", "Pa", "W/m2", "-", ...
    desc: str

@dataclass
class ConstraintResult:
    name: str; achieved: float; limit: float
    sense: str          # ">=" or "<="
    unit: str
    margin: float       # signed normalised: (achieved-limit)/|limit| for ">=", (limit-achieved)/|limit| for "<="
    status: str         # "PASS" | "MISS"

@dataclass
class ScreenResult:
    passed: bool                    # all constraints PASS and regime_ok
    constraints: list[ConstraintResult]
    regime_ok: bool                 # model-validity window (dimensionless groups) satisfied
    regime_notes: list[str]         # e.g. "s+ = 34 outside riblet window [8, 22]"
    derived: dict[str, float]       # extra computed quantities for the blueprint (e.g. "drag_reduction_pct")

@dataclass(frozen=True)
class PhysicsCard:
    id: str                         # e.g. "STR_SANDWICH_HONEYCOMB"
    domain: str                     # thermal | fluids | structures | adhesion | wetting | optics | mass_transfer
    title: str
    principle: str                  # one-paragraph physics summary with governing equations in plain text
    bio_exemplars: list[str]        # organisms whose mechanism this card can express (for retrieval, NOT for scoring)
    design_space: list[Param]
    env_space: list[Param]          # environment/requirement variables supplied by a Problem
    references: list[str]           # textbook/paper sources of the equations
    def screen(self, design: dict, env: dict) -> ScreenResult: ...

CARDS: dict[str, PhysicsCard]       # registry in flbds/v11/cards/__init__.py
```
Rules: no defaults for design fields (missing/out-of-bounds ⇒ caller reports schema error); env always from the Problem; closed-form only (ms per call); every equation cited.

## 2. Problem library — `flbds/v11/problems.py`

```python
@dataclass(frozen=True)
class Problem:
    id: str                         # "P-STR-01"
    domain: str
    title: str                      # "Lightweight floor panel for a delivery drone"
    statement: str                  # engineering need in plain words (no biology, no card ids)
    env: dict[str, float]           # values for the env_space of each plausible card (superset)
    plausible_cards: list[str]      # >=1 card ids that could address it (choice-sensitive when >=2)
    source: str                     # where this real-world problem comes from (paper/standard/benchmark)

PROBLEMS: list[Problem]
```

## 3. Pipeline records — `flbds/v11/pipeline.py`
Perception JSON (VLM output): `{organism:{common, scientific, confidence}, structures:[{name, description, scale_m_estimate}], functions:[...], mechanisms:[{principle, physical_effect_tag, evidence_in_image}], design_relevant_features:[...]}`
Design JSON (LLM output): `{rationale, bio_mapping:[{bio_feature, engineering_feature}], card_id, design:{...}}`
Blueprint JSON: `{title, problem_id, card_id, bio_source, summary, bio_to_engineering_mapping:[...], geometry:[{part, dimension, value, unit}], materials:[...], manufacturing_steps:[...], verified_performance:[{metric, value, unit, limit, status}], limitations:[...], svg_sketch: "<svg ...>", render_prompt}`
