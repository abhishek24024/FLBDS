# Implementation plan — FLBDS v3.0

Eight phases. Each phase is independently runnable, has explicit acceptance
criteria, and leaves the previous phases green. Phases 0–1 are the foundation;
everything after that maps one-to-one onto the two project aims.

Aim 1 (Phases 2–3): the visual biology-to-engineering thesaurus.
Aim 2 (Phases 4–6): dual-image analogical engineering synthesis.

---

## Phase 0 — Foundations and reproducibility  ✅ done

**Goal:** a repository that a second person (or a reviewer) can clone and run.

| Deliverable | Where |
|---|---|
| Package layout, pinned deps, editable install | `pyproject.toml`, `flbds/` |
| Typed configuration with env overrides | `flbds/config.py`, `configs/default.yaml` |
| Structured logging, deterministic seeds | `flbds/logging.py` |
| Git policy: corpora/weights/DBs excluded | `.gitignore` |
| Test harness + CI-ready `pytest` config | `tests/`, `pyproject.toml` |
| `flbds doctor` self-check | `flbds/cli.py` |

**Acceptance:** `pip install -e ".[dev]" && pytest` passes on a clean checkout;
the repo contains zero binary artefacts > 1 MB.

---

## Phase 1 — Causal ontology and knowledge spine  ✅ done

**Goal:** the semantic substrate every later stage reads and writes.

| Deliverable | Where |
|---|---|
| 7 SAPPhIRE constructs + relational operators, with definitions, FBS alignment, transfer role | `flbds/ontology/constructs.py` |
| Typed node/edge/graph models with provenance and confidence | `flbds/ontology/models.py` |
| Causal-chain + endpoint legality + DAG acyclicity validation | `flbds/ontology/validate.py` |
| **Abductive variable guardrail** `Activates(I,R→e) ⇔ Variables(e) ⊆ Attrs(I) ∪ Attrs(R)` | `flbds/ontology/validate.py` |
| TRIZ spine: 39 parameters, 40 principles, 4 separation operators, 39×39 matrix, lexical parameter matcher | `flbds/knowledge/triz.py`, `flbds/data/triz/` |
| Physical-laws catalog with dimensioned variables and dimensionless groups | `flbds/knowledge/physics.py`, `flbds/data/physics/laws.json` |
| Dimension parser + Π-group nullspace + regime audit | `flbds/reasoning/buckingham.py` |
| Property-graph store (SQLite) + HNSW-ready vector index, Neo4j DDL mirror | `flbds/graph/` |
| Curated seed graphs (bio + eng) for retrieval/regression tests | `flbds/data/seeds/` |

**Acceptance**
* every seed graph validates with zero errors and at least one `Effect` whose
  variables are fully covered by `Input`/`oRgan` attributes;
* `TrizKnowledge.principles_for(14, 21)` returns the canonical principle set;
* `Re`, `Bi`, `Bo` and `Π_g` Π-groups reproduce their textbook length exponents
  (1, 1, 2, 1);
* graph round-trips through SQLite byte-for-byte in content.

---

## Phase 2 — Extraction: deterministic rules + HyDE-CoT corrective RAG  ✅ done

**Goal:** turn a patent specification or a biological paper into a validated
7-node SAPPhIRE graph, without letting an LLM invent constructs.

| Deliverable |
|---|
| Pathway B: deterministic rule engine — dependency parse → 5 intermediate categories (Interaction, Entity, State change, Condition, Physical law) → SAPPhIRE, with WordNet-style hypernym sets vendored as data |
| Pathway A: HyDE-CoT corrective RAG — hypothetical construct synthesis → dense retrieval over evidence chunks → fact-grounded revision, with a groundedness score `G(y│r)` and a rejection threshold |
| Fusion + provenance merge: every construct carries `evidence[]` (source id, locator, quote) |
| Abductive repair loop: missing effect variables trigger targeted GraphRAG follow-ups |
| `flbds ingest --domain bio|eng --file …` CLI writing into `G_MCKG` |

**Acceptance:** ≥ 0.75 construct-level F1 on a 30-document hand-labelled dev set;
100% of emitted graphs pass SHACL-style structural validation; every `Effect`
node has ≥ 1 supporting evidence span.

---

## Phase 3 — Visual thesaurus and hybrid GraphRAG retrieval  ✅ done

**Goal:** Aim 1 in production form — images and text in one index; causal paths
out.

| Deliverable |
|---|
| CLIP/SigLIP image encoder + text encoder, unified embedding table in the graph store |
| AskNature/IDEA-INSPIRE/patent-drawing ingestion adapters (streamed, resumable) |
| NCBI/IRMNG taxonomy loader and `:Species→:Genus→:Order→:Class→:Phylum` edges |
| CPC hierarchy loader + patent callout linking (`:FigureROI-[:DEPICTS_PART]->:Part`) |
| Leiden-style community detection → "mechanism active ingredient" clusters |
| Hybrid objective `J_GraphRAG = ω₁ΣS_vec + ω₂ΠE_causal + ω₃Sim(C_m) + ω₄D_phylo` with LCA-height phylogenetic reward |
| Backward causal traversal queries (Action → Part, lateral across Effect bridges) |

**Acceptance:** recall@10 ≥ 0.80 on a 100-query visual benchmark; every returned
subgraph is causally connected; query latency < 300 ms at 10⁵ nodes.

---

## Phase 4 — Dual-image perception  ✅ done

**Goal:** `Image_Bio` and `Image_Eng` become structured, typed geometry.

| Deliverable |
|---|
| Native-resolution VLM wrapper (Qwen2.5-VL / Qwen3-VL) emitting boxes, points, JSON |
| Micro-feature grounding: attention-entropy box selection (ACS-style), recurrent latent visual search (ReLaViS-style), Hungarian IoU one-to-one filtering |
| Affordance-driven `M_Eng` (modifiable part mask) + `1 − M_Eng` keep-out mask |
| `T_Bio` oRgan tensor field: Canny/HED skeletons, surface-normal & curvature gradients, dimensionless ratios (porosity φ, hydraulic diameter ratio, branching angle) |
| Grounding quality benchmark (IoU on micro-organs, mIoU on affordance parts) |

**Acceptance:** micro-organ IoU ≥ 0.55; `M_Eng` mIoU ≥ 0.60 on the internal dev
set; keep-out mask provably disjoint from `M_Eng`.

---

## Phase 5 — Analogical reasoning, similitude and contradiction resolution  ✅ done

**Goal:** decide *what may transfer*, *what breaks*, and *how to fix it*.

| Deliverable |
|---|
| Order-embedding GNN encoder (partial order `h_u ≤ h_v` iff causal subgraph) |
| Constrained correspondence solver: `min_X ‖XA_TXᵀ − A_B‖² + λ₁order + λ₂systematicity − λ₃tiered-identity`, doubly sub-stochastic constraints, Sinkhorn projection |
| Gentner axiom checks reported per alignment (one-to-one, parallel connectivity, systematicity) |
| Buckingham Π regime auditor with `V_scale` violation metric and Gouy–Stodola exergy check |
| TRIZ resolver: physical contradiction → separation operators → technical contradiction → matrix lookup → graph rewrite `R_{p_k}(G_T)` |
| Optional kTRIZ type-check oracle; when the Kotlin toolchain is absent, a JSON-schema type guard enforces the same invariant |

**Acceptance:** alignment F1 ≥ 0.80 on the seeded benchmark; 100% of solutions
report Π-groups inside declared critical ranges or an explicit unresolved
violation; no principle outside the canonical 40 is ever emitted.

---

## Phase 6 — Synthesis: image, vector schematic, CAD  ✅ done

**Goal:** three artefact tracks from one locked design.

| Deliverable |
|---|
| 6A structure-locked render: mask-conditioned inpainting where `1 − M_Eng` is bit-identical (verified by MSE = 0), oRgan injection from `T_Bio` |
| 6B SVG: primitive-preserving vectorisation with `<rect>/<circle>/<line>/<path>` and text callouts; DinoScore-style ranking; TikZ emitter |
| 6C CAD: CadQuery program synthesis + execute-and-repair loop, STEP export, manifold/watertight check, DangEL metric |
| Track-consistency checker: schematic ↔ render ↔ CAD bounding boxes agree |

**Acceptance:** unmasked drift MSE = 0; SVG renders without raster fallback;
100% of emitted CadQuery scripts execute; ≥ 95% watertight solids on the
internal suite.

---

## Phase 7 — Service, UI and evaluation protocol  ✅ done

| Deliverable |
|---|
| FastAPI service (`/health`, `/thesaurus/search`, `/align`, `/synthesize`, `/jobs`) |
| Single-page demo UI: upload two images, see the 7-node graph, alignment, Π-audit, three artefacts |
| Evaluation harness implementing the five benchmark families of the specification |
| Reproducible experiment configs + report generator |

**Acceptance:** full pipeline runs end-to-end from the UI on a held-out pair in
< 60 s (GPU) and produces all three artefacts; evaluation report regenerates
from a single command.

---

## Honest scoping notes

The specification names 2024–2026 foundation models (FLUX.1-Fill-dev,
StarVector-8B, CAD-Coder, Qwen3-VL, Grounded-SAM 2, DeepGAR). Training those
from scratch is out of scope and unnecessary. The plan is:

1. **Reuse pretrained weights** where a permissive checkpoint exists and the
   lab GPU can hold it.
2. **Reimplement the architecture** (alignment solver, Π-audit, TRIZ oracle,
   order embeddings, mask-locked synthesis objective) so the method is ours and
   testable without a 20 GB download.
3. **Keep every model behind an adapter** (`flbds/*/backends.py`) with a
   deterministic reference implementation, so the pipeline is always runnable —
   on CPU, in CI, and before any weight is fetched.
