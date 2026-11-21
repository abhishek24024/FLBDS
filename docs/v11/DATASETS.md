# FLBDS V11 — datasets (biology side and engineering side)

Status key: **IN USE** (used in the 20 Nov 2026 pilot) · **HAVE** (on disk, not yet used in V11) · **PLANNED** · **EXCLUDED**.
Server paths are under `/home/abhishek24024/` on hcd-dept-h200.

## A. Biology side

| # | Dataset | What it is | Size | Licence | Role in V11 | Status |
|---|---|---|---|---|---|---|
| B1 | **V11 canonical organism set** (`flbds/v11/data/organisms.json`) | Hand-curated textbook cases of biology→engineering transfer: organism (common + scientific), key structure, mechanism, physical-effect tag, canonical engineering application, target physics card | 24 cases (19 with a physics card; 5 with no card yet: kingfisher, burdock, humpback whale, penguin, mussel) | Project-authored | Ground truth for **rediscovery**: can the system recover the known mechanism and application from an image? | IN USE |
| B2 | **Organism photos** (`flbds/v11/data/images/`, `images_manifest.json`) | One photo per case, the first CC/PD-licensed hit from a Wikimedia Commons search; unscreened (e.g. the lotus photo contains a frog; the termite photo shows a soldier, not the mound) | 22 images (gecko rate-limited, humpback had no licensed hit) | CC BY / CC BY-SA / CC0 / PD; author + page recorded per image | Input to the VLM in the IMG arms | IN USE |
| B3 | **Rediscovery table, extended** (`research_notes/Bio integration and image innovation/03_bioinspiration_validity_evidence.md`) | 28 canonical cases incl. 2 negative controls (claims with wrong biology), with claimed vs measured performance | 28 rows (some rows still need source checks) | Literature-derived | Expand B1 to ~60–100 cases; negative controls test whether the system repeats folk biomimicry | PLANNED |
| B4 | **iNaturalist research-grade photos** | Community photos with expert-verified species IDs | Millions; we would take 3–5 per organism | Per photo CC0 / CC BY / CC BY-NC (keep only CC0/CC BY) | Several photos per organism (different views, scales) to test robustness; replaces noisy single Commons hits | PLANNED |
| B5 | **Micrographs / SEM figures from open papers** | Figure images from PMC OA papers showing the functional microstructure (setae, denticles, wax tubules, Bragg lamellae) | ~1–3 per organism | Paper licence (CC BY only) | Tests whether microscale images add information that field photos cannot (structure, scale) | PLANNED |
| B6 | **BioCLIP 2** (`flbds_data/models/bioclip-2`) | Biology CLIP model trained on TreeOfLife-200M | 3.2 GB weights | MIT | Taxon identification and closed-list re-ranking before the VLM; reduces wrong-organism errors | HAVE (downloaded) |
| B7 | **PMC biology pilot corpus** (`flbds_data/corpus/bio_pilot.jsonl`) | 500 PMC CC BY biology papers | 500 docs | CC BY | Source of the V9 silver-card factory | HAVE (but 51/53 "biology" cards described engineered materials) |
| B8 | **Silver mechanism cards** (V9 Stages 1–6) | LLM-extracted cards with verbatim quotes and linked quantities | 133 cards | Derived from B7 + patents | Seed for the V11 mechanism-card store after re-filtering to real organisms | HAVE |
| B9 | **Foundation + audited papers** (`flbds_data/biological_papers/`) | Martins 2018 (elephant skin), Scholander 1955 (rete), Shi 2015 (silver ant), Flynn & Bush 2008 and Shirtcliffe 2006 (plastron), plus 10 audited PMC papers | 15 papers | Mixed (open access) | Gold evidence for the 4 V10 families' cards | HAVE |
| B10 | **Mechanism card store (V11)** | 60–150 cards: organism, structure (with scale), mechanism, physical-effect tag, verbatim evidence quotes, source | 60–150 | Derived from B11–B13 | Retrieval for Mode A/B ("retrieved" arm); replaces the knowledge graph | PLANNED |
| B11 | **PMC Open Access (commercial-use subset) via BioC API** | Full-text biology papers retrieved by taxon + function keywords | On demand | CC BY / CC0 (filter by licence field) | Mechanism evidence for B10 | PLANNED |
| B12 | **OpenAlex** | Scholarly metadata, abstracts (inverted index), citations | 250M+ works | CC0 | Literature search, novelty/prior-art lookups | PLANNED |
| B13 | **Wikidata + GBIF backbone taxonomy** | Taxon names, synonyms, common names, hierarchy | — | Wikidata CC0; GBIF CC BY 4.0 | Name normalisation; genus/family-level scoring of organism identification | PLANNED |
| — | AskNature | Curated biomimicry strategies | ~2,100 entries | Terms forbid data mining/redistribution | Only as a manual pointer to primary papers | **EXCLUDED** |
| — | S2ORC | Full-text corpus | 81M papers | Non-commercial | — | **EXCLUDED** |

## B. Engineering side

| # | Dataset | What it is | Size | Licence | Role in V11 | Status |
|---|---|---|---|---|---|---|
| E1 | **Physics templates, thermal-fluid** (`flbds/physics/`, wrapped in `flbds/v10/families.py`) | Hand-written, cited closed-form screens + coupled solvers: PCM storage, counter-current HX, radiative cooling, plastron membrane, evaporative cooling, wicking (+4 more) | 10 templates (~2,400 lines) | Project code | Physics check for thermal/fluid/mass-transfer designs | IN USE (V10); known bugs: PCM solver instability, radiative scorer ignores net cooling |
| E2 | **Physics cards, new domains** (`flbds/v11/cards/`) | Closed-form, cited models: honeycomb sandwich (Gibson–Ashby, Allen), lattice/truss, riblet drag (Bechert; García-Mayoral & Jiménez), fibrillar adhesion (JKR + contact splitting), superhydrophobic wetting (Cassie–Baxter + impact robustness), Bragg structural colour, fog-harvest mesh (Rivera; Park et al.) | 7 new + wrappers | Project code | Extends physics checks to structures, adhesion, wetting, optics, fog harvesting | PLANNED / being built |
| E3 | **V10 certified benchmark** (`flbds/v10/instances_v10.json`) | Generated problems in 4 thermal families, each certified satisfiable by an optimiser and rejected if too easy | 48 instances, sha256 `788426ff…`, canary string | Project-generated | Measures the design loop (feedback, optimiser, allocation) | IN USE (V10 results) |
| E4 | **V9 dev cases** (`flbds/benchmark/dev/`) | Hand-written problem cards, 4 clusters × 3 splits | 12 | Project-authored | Regression set only (5/12 were blank-passable) | HAVE |
| E5 | **V11 problem library** (`flbds/v11/problems.py`) | Real engineering problems (drone floor panel, pipeline drag, climbing-robot gripper, self-cleaning solar cover, pigment-free colour coating, arid fog collection, passive building cooling, …) with numeric requirements and ≥1 plausible card; ≥6 choice-sensitive | ~20–32 problems | Project-authored, each with a source | Mode B picks problems from here; Mode A supplies one; choice-sensitive problems test whether biology changes the mechanism chosen | PLANNED / being built |
| E6 | **Problem feasibility certificates** (`flbds/v11/problem_feasibility.json`) | For every (problem, plausible card), optimiser-found best design and min margin | per problem×card | Derived | Ground truth: which mechanisms can work for each problem | PLANNED |
| E7 | **USPTO engineering patent pilot** (`flbds_data/corpus/eng_pilot.jsonl`) | 500 patents | 500 | Public domain | Novelty check: nearest-neighbour similarity of generated designs to existing patents | HAVE |
| E8 | **Patent / prior-art index (scaled)** | USPTO full text (bulk, public domain) or Google Patents Public Data, embedded with an open text embedder (e.g. Qwen3-Embedding) | 10k–100k patents in target CPC classes | Public domain / CC BY 4.0 (Google public data) | Automatic novelty score without human raters | PLANNED |
| E9 | **Engineering design benchmarks (external)** | e.g. EngDesign (NeurIPS 2025, 101 tasks with executable checkers) | 101 tasks | See benchmark licence | Optional external check of the design loop on non-bio problems | PLANNED (optional) |

## C. Models used as instruments (not datasets, listed for reproducibility)
Qwen3-VL-32B-Instruct-FP8 (perception, analogy, blueprints; Apache-2.0) · Qwen2.5-72B-Instruct-FP8 (design loop, judge; Qwen licence) · Qwen2.5-7B-Instruct (CPU contrast) · Qwen-Image (concept-sketch renders; Apache-2.0) · BioCLIP 2 (MIT).
