# FLBDS — Functional & Logical Biomimetic Design System (v3.0)

A multimodal, neuro-symbolic **visual biology-to-engineering thesaurus** and
**dual-image analogical design compiler**.

Given a biological source image (`Image_Bio`) and an engineering baseline image
(`Image_Eng`), FLBDS grounds the functional parts of both, retrieves the causal
mechanism behind the biological strategy, aligns the two mechanisms under
Structure-Mapping Theory, audits the physical scaling laws that a direct
geometric transfer would violate, resolves the resulting TRIZ contradiction,
and emits three artefacts:

1. a structure-locked render (`Image_Out`, keep-out zone bit-identical),
2. a primitive-preserving vector schematic (SVG / LaTeX TikZ),
3. an executable, watertight CAD program (CadQuery / STEP).

Everything is organised around the **7-construct SAPPhIRE model of causality**
(State change, Action, Part, Phenomenon, Input, oRgan, Effect) stored in a
multimodal causal property graph `G_MCKG`.

---

## Status

| Phase | Scope | State |
|---|---|---|
| 0 | Foundations, config, CI-ready test harness | **done** ✅ |
| 1 | SAPPhIRE ontology, TRIZ spine, physical-laws catalog, graph store | **done** ✅ |
| 2 | Deterministic SAPPhIRE extraction + HyDE-CoT corrective RAG | **done** ✅ |
| 3 | Multimodal thesaurus + hybrid GraphRAG retrieval | **done** ✅ |
| 4 | Dual-image perception (VLM grounding, affordance masks, `T_Bio`) | **done** ✅ |
| 5 | DeepGAR alignment, Buckingham Π audit, TRIZ resolution | **done** ✅ |
| 6 | Synthesis: image / SVG-TikZ / CAD | **done** ✅ |
| 7 | API, UI, evaluation protocol, packaging | **done** ✅ |

See [`docs/PHASES.md`](docs/PHASES.md) for deliverable-level detail and the
acceptance criteria of each phase, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the module map.

## Quickstart

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

flbds doctor                 # environment + data integrity report
flbds triz lookup 14 21      # contradiction lookup -> inventive principles
flbds graph build            # build the property graph from seed data
flbds api                    # serve the HTTP API
pytest                       # unit tests
```

GPU work on the lab server runs through the broker:

```bash
gpurun python -c "import torch; print(torch.cuda.is_available())"
```

## Repository layout

```
flbds/
  ontology/     SAPPhIRE constructs, graph models, validation (abductive guardrail)
  knowledge/    TRIZ 39x39 spine, physical-laws catalog, lexical rules
  graph/        property-graph store (SQLite now, Neo4j adapter), vector index
  extraction/   deterministic rule engine, HyDE-CoT corrective RAG
  perception/   VLM grounding, affordance masks, oRgan tensor field
  reasoning/    order-embedding alignment, Buckingham Pi audit, TRIZ solver
  synthesis/    image / SVG / TikZ / CadQuery back-ends
  eval/         metrics and benchmark harness
  api/          FastAPI service + demo UI
  data/         vendored *seed* knowledge only (no corpora, no weights)
docs/           architecture, phase plan, evaluation protocol
scripts/        operational scripts (ingest, build, evaluate)
tests/          pytest suite
```

## Data policy

Committed: ontology definitions, TRIZ/physics-laws reference tables, curated seed
graphs, schema, tests.
**Never committed:** raw corpora (AskNature, IDEA-INSPIRE, USPTO/EPO dumps),
generated databases (`*.sqlite`, Neo4j stores), model weights (`*.safetensors`,
`*.pt`), and per-run artefacts. Those live in `data/raw/` and `runs/`, both
git-ignored.

## Attribution

* TRIZ parameters, principles, separation operators and the 39x39 contradiction
  matrix are vendored from the [MATRIZ TRIZ Knowledge Base](https://wiki.matriz.org)
  (CC-BY, attribution required) via the MIT-licensed
  [`pytriz`](https://github.com/mmysior/pytriz) resource files.
* SAPPhIRE model of causality: Chakrabarti et al.; extraction methodology:
  Majumder et al. (HyDE-CoT RAG), Bhattacharya et al. (dependency-rule
  extraction), Srinivasan & Chakrabarti (physical-laws catalog).
