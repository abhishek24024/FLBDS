# FLBDS Project Notes & Decision Register

## 1. Project Scope & Architecture Boundaries (v9.0 Realignment)
* **Authoritative Reference**: `docs/flbds_v9.md` (Version 9.0, 30 October 2026).
* **Hardware & Quota**: 1 × NVIDIA H200 (141 GB HBM3e), 90 H200-hours/week, 26-week solo BTech project scope.
* **Core Paradigm (Principle P4 Prompted-First)**:
  * Models are deployed in inference-only mode first (prompted VLMs, prompted 72B teacher, prompted 32B critic, prompted 7B extractor/filter, prompted coders for SVG/CAD).
  * Fine-tuning (LoRA SFT, offline DPO, contrastive InfoNCE) is restricted to explicit quantitative gates (e.g., 8B extractor must match teacher within 3 F1 points with >= 0.90 grounding; functional embedding must beat BM25/bge-large with <= 10% leakage).
* **Superseded Earlier Decisions**:
  * *Vision & Multimodal Input (M1/M2)*: Previously scoped out; now **IN SCOPE**. M1 (BioCLIP + VLM tagger + hybrid retrieval) and M2 (VLM Target Problem Card extraction) are evaluated under prompted baseline first.
  * *Thesaurus Graph & Multimodal Embeddings (M3)*: Previously scoped out; now **IN SCOPE** with 3-vector representation (purpose L4, mechanism L3, effect L2), canonical physical effects, and community detection.
  * *Transformation Operators*: Expanded from T1-T4 to full set **T1 to T5** (plus demonstrated T6 material substitution and optional T7 hybridization).
  * *Physics Verifier (M5)*: Dual-tier verification architecture **IN SCOPE** across all 10 templates (TPL-01 to TPL-10):
    * **M5-Screen**: Lumped-parameter closed-form checks guiding generator search.
    * **M5-Eval**: Coupled, held-out numerical solvers (e.g. 1D Stefan enthalpy method, 24h Robin boundary outdoor cycle, coupled boundary-layer mass transfer) evaluating candidate validity.
  * *Prior-Art Novelty Gate (M6)*: Now **IN SCOPE** (L2/L3 abstraction-level distance + judge model).
  * *Concept Package Outputs (M7)*: Now **IN SCOPE** (SVG schematic, CadQuery 3D solid/STEP/STL, concept image).
* **Grounding & Integrity Rules**:
  * All citations, release dates, and numbers from earlier drafts are unverified claims until checked.
  * No fabrication of data, gold labels, citations, or metrics.
  * Teacher-model output is strictly classified as "silver". Gold cards are human-authored.
  * Every milestone must conclude with executable, passing test suites.

## 2. Infrastructure & Server Baseline (Step 0 Reconnaissance)
* **Server Hostname**: `hcd-dept-h200` (IP: `192.168.2.69` via IIIT FortiClient VPN).
* **GPUs**:
  * 4 x NVIDIA H200 SXM (143,771 MiB / ~141 GB HBM3e each).
  * Direct NVML is restricted; access is managed via the broker (`gpurun`).
  * In a test job on GPU 2: 143,149 MiB free memory available.
* **Disk & Storage**:
  * Filesystem `/dev/sda2`: 21 TB total, 4.0 TB used, 16 TB available (21% system usage).
  * User quota (`abhishek24024`): 28.7 GB used out of 900 GB soft quota / 1024 GB hard limit (~871.3 GB free quota).
* **Software Toolchain**:
  * OS / Python: Ubuntu / Python 3.12.3 (`/usr/bin/python3`).
  * CUDA Driver & Compiler: CUDA 13.3 (`/usr/local/cuda-13.3/bin/nvcc`, V13.3.33).
  * vLLM Status: Installed in `flbds_env` (`vllm 0.32.0`).
* **Virtual Environment Setup**:
  * Dedicated venv at `/home/abhishek24024/flbds_env`.
  * Verified libraries: `pydantic 2.14.1`, `pytest 9.1.1`, `pint 0.26.2`, `sympy 1.14.0`, `scipy 1.18.1`, `numpy 2.5.4`, `vllm 0.32.0`.

## 3. Remote Git History Status (Rule 7)
* Remote repository: `git@github.com:abhishek24024/FLBDS.git`
* Default branch: `main`
* Cloned on server into `/home/abhishek24024/flbds`.
* Local repository initialized and linked to origin/main.
* `.gitignore` configured to prevent committing credentials (`ssh_details.md`), venvs, and datasets/weights (`flbds_data/`).

## 4. Compute Budget, GPU Broker Rules & Accounting
* **Broker Mechanics (`gpurun`)**:
  * Broker binary: `/usr/local/bin/gpurun` communicating over UNIX socket `/run/gpu-broker/broker.sock`.
  * Default allocation: 1 GPU (`-g 1`), supports multi-GPU with `-g N` if available.
  * Quota accounting: 1 GPU-hour = 1 physical H200 GPU running for 1 wall-clock hour.
  * Server Weekly Allotment: 90.0 H200-hours / week (reset weekly).
* **Budget Guardrails**:
  1. Pilot budget cap: The entire pilot (~1,000 documents) strictly <= 20.0 H200-hours.
  2. If any stage approaches or exceeds **80%** of its pre-run estimate, execution must **STOP** immediately and report.
  3. No scaling beyond the pilot without explicit user approval and a measured throughput calibration table.
  4. Spare weekly hours are NOT a justification to scale up; human quality review of the pilot cards comes first.
* **Weekly Consumption Log (Week Starting 2026-10-26)**:
  * Weekly Allotment: 90.00 h
  * Cumulative Pilot Consumption: **0.318 H200-hours**
    - Step 0 Broker Recon & Calibration: ~0.05 h
    - Step 5 Smoke Test (40 docs): 0.0676 h
    - Step 5 Full Pilot (1,000 docs): 0.2004 h
  * Remaining Quota: **89.682 H200-hours**

## 5. Pilot Corpus & Extraction Audit Findings (Step A.3 Audit)
* **Corpus License Breakdown & Non-Commercial Reconcile**:
  * 500 PMC Biology Papers:
    - CC BY: 341 papers (68.2%)
    - CC0: 2 papers (0.4%)
    - Non-Commercial variants: 157 papers (31.4%: 112 CC BY-NC-ND, 43 CC BY-NC, 2 CC BY-NC-SA).
    - *Reconciliation*: Exactly matches the ~31% non-commercial figure noted in v9 §6.1. These non-commercial articles are retained for internal private research; only CC BY and CC0 articles will be distributed in open releases.
  * 500 Engineering Patents (BigPatent HF CPC sections F and E):
    - 500 documents (100.0% US Patent Public Domain).
  * Committed Git Samples (`data/sample/`):
    - `bio_sample.jsonl`: 5 papers, 100% CC BY.
    - `eng_sample.jsonl`: 5 patents, 100% Public Domain.
* **Stage 1 Filter Audit (30 Sampled Rejected Docs: 15 Bio, 15 Eng)**:
  * 27/30 (>90%) were legitimately off-domain: oncology therapies, clinical warming blankets, genetic syndromes, animal grooming ethology, mechanical pump bearings, fuel cell catalysts.
  * 2-3/30 (~7-10%) were borderline false rejections: tree xylem sapwood hydraulic conductance (bio) and ceramic tube heat exchanger geometry (eng).
  * Conclusion: Filter is high-precision with minimal false rejection of actionable thermodynamic mechanisms.
* **Stage 5 Causal Entailment Critic Audit (20 Sampled Dropped Cards)**:
  * 15/20 (75%) were legitimate rejections of teacher hallucinations: conflating comfortable hours percentage with enthalpy of vaporization; claiming positive cooling in failed experiments; attributing heat pipe performance to raw casing material.
  * 5/20 (25%) were overly strict rejections of complex phenomena: spontaneous evaporative freezing in high vacuum; laser-textured micro-groove radiative cooling.
  * Conclusion: Critic strictly preserves precision over recall, ensuring silver cards are causally grounded.
* **Inter-Sample Agreement Metric (67.7% Mean Field Agreement)**:
  * Measures generation consistency of unconstrained Qwen2.5-72B teacher across 298 repeated runs at $T=0.7$ (seed 42 vs seed 43) across 5 core SAPPhIRE fields:
    - State Variable: 82.3% agreement
    - Action Verb: 80.5% agreement
    - Subject: 67.1% agreement
    - Physical Effect: 64.3% agreement
    - Phenomenon: 44.2% agreement
  * Reflects natural linguistic variation in free-form generation and motivates schema-constrained guided decoding.
* **Purged Quantity Units (127 Purged)**:
  * ~65-70% were Pint syntax and formatting failures: unescaped periods in percentage strings (`vol.%`, `wt.%`), unicode minus signs (`−` vs `-` in `J g−1`), and unparenthesized multi-division expressions (`g/m2/h`).
  * ~30-35% were genuine non-dimensional or non-physical tokens (`fold`, `times`, `relative ratio`).
* **Yield & Scaling to 8,000 Silver Mechanism Cards**:
  * Net yield: Bio = 118 cards / 500 docs = 0.236 cards/doc; Eng = 151 cards / 500 docs = 0.302 cards/doc. Overall = 0.269 cards/doc.
  * To obtain 8,000 silver cards: need ~29,740 documents (~16,950 bio, ~13,245 eng).
  * Compute requirement: At 0.2004 GPU-hours per 1,000 docs on H200, processing 30,000 docs requires **~6.0 to 8.0 H200-hours** (well within Phase 1 budget of 30 planned / 45 cap).
* **16 Benchmark Organism Representation in Pilot Bio Silver Cards (118 Cards)**:
  * **Present (4/16)**:
    1. Elephant (`DEV-M1`): 3 cards (thermoregulation, mud wallowing, ear vasodilation).
    2. Saharan silver ant (`DEV-M3`): 1 card (prismatic hair radiative cooling).
    3. Tuna (`TEST-M06`): 2 cards (countercurrent retia mirabilia).
    4. Camel (`TEST-M07`): 1 card (nasal turbinate moisture/heat sorption).
  * **Missing from Pilot (12/16)**:
    - Penguin (`DEV-M2`), Aquatic insect (`DEV-M4`), Termite (`TEST-M01`), Namib beetle (`TEST-M02`), Cactus (`TEST-M03`), Polar bear (`TEST-M04`), Jackrabbit (`TEST-M05`), Xylem (`TEST-M08`), Leaf (`TEST-M09`), Desert snail (`TEST-M10`), Prairie dog (`TEST-M11`), Toucan (`TEST-M12`).
  * *Resolution*: Targeted queries in Phase 1 corpus harvesting will acquire dedicated literature for all missing benchmark organisms.

## 6. Implementation & Verification Progress
* [2026-10-26] Step 1: Core Pydantic v2 schemas (`flbds/schema/`) passing 15 tests.
* [2026-10-26] Step 2: Source register verified live on server (`docs/source_register.md`).
* [2026-10-26] Step 3: Harvested 1,000-doc pilot corpus on server.
* [2026-10-26] Step 4: Installed vLLM, downloaded Qwen2.5 72B/32B/7B, calibrated throughput.
* [2026-10-26] Step 5 & 6: Autonomous pilot pipeline completed (269 silver cards produced, tools built).
* [2026-11-01] Step A.1: Updated NOTES.md to align with FLBDS v9.0 architecture.
* [2026-11-01] Step A.2: Extended Pydantic v2 schemas per v9 §4.3 (`enums.py`, `templates.py`, `ground_truth_eval.py`, `role_binding.py`, `mechanism_card.py`, `problem_card.py`). 28 tests passing on server.
