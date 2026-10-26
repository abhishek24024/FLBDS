# FLBDS Project Notes & Decision Register

## 1. Project Scope & Architecture Boundaries
* **Core Focus**: Scoped BTech project focusing on:
  1. Small pilot of Phase 1 (data factory) Mechanism Card extraction restricted to the **thermal, fluid, and porous-media** domain (thermoregulation, heat storage, evaporative cooling, wicking, porous insulation, phase change, sorption).
  2. The Lumped-Parameter Physics Verifier (M5).
  3. Transformation Operators T1 to T4 (M4: loop-closing, flow inversion, phase shift, mechanism substitution).
  4. Prompted LLM integration with no model training (no LoRA, DPO, or SFT; inference only).
* **Grounding & Integrity Rules**:
  * All citations, release dates, and numbers from `flbds_v5.md` are unverified claims until checked.
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
  * User quota (`abhishek24024`): 28.7 GB (29,369 MB) used out of 900 GB soft quota / 1024 GB hard limit (~871.3 GB free quota).
* **Software Toolchain**:
  * OS / Python: Ubuntu / Python 3.12.3 (`/usr/bin/python3`).
  * CUDA Driver & Compiler: CUDA 13.3 (`/usr/local/cuda-13.3/bin/nvcc`, V13.3.33).
  * Existing Models on Server:
    * `Bio_Analogy_Gen/models/sam_vit_h_4b8939.pth` (2.5 GB)
    * `cae/best.pt`, `cae_design/best.pt`, `cae_design_aux/best.pt` (~164 MB each)
    * **No LLM weights** (70B, 30B, 8B) currently exist on the server.
  * vLLM Status: **Not installed** globally or in user directories.
* **Outbound Internet Connectivity Test**:
  * `huggingface.co`: Reachable (HTTP/2 200).
  * `ftp.ncbi.nlm.nih.gov`: Reachable via HTTPS (`https://ftp.ncbi.nlm.nih.gov` HTTP/1.1 200 OK).
  * PMC AWS S3 mirror (`https://pmc-oa-opendata.s3.amazonaws.com`): Reachable (HTTP/1.1 200 OK).
  * `patentsview.org`: Reachable, redirecting (HTTP/2 301) to `https://data.uspto.gov/support/transition-guide/patentsview`.
  * `bulkdata.uspto.gov`: Failed DNS resolution (endpoint has transitioned to `data.uspto.gov`, which is reachable and returned HTTP/2 200).
* **Virtual Environment Setup**:
  * Dedicated venv created at `/home/abhishek24024/flbds_env`.
  * Core libraries installed and verified: `pydantic 2.14.1`, `pytest 9.1.1`, `pint 0.26.2`, `sympy 1.14.0`, `scipy 1.18.1`, `numpy 2.5.4`.

## 3. Remote Git History Status (Rule 7)
* Remote repository: `git@github.com:abhishek24024/FLBDS.git`
* Default branch: `main`
* Current remote HEAD: `5cf1d7b` ("chore: clear all files from repository", 86 files deleted, tree empty).
* Cloned on server into `/home/abhishek24024/FLBDS`, with symlink `/home/abhishek24024/flbds`.
* Local repository initialized and linked to origin/main.
* `.gitignore` configured to prevent committing credentials (`ssh_details.md`), venvs, and datasets/weights (`flbds_data/`).

## 4. Compute Budget & GPU-Hour Accounting
* **Server Weekly Allotment**: 90.0 H200-hours / week (reset weekly by server broker `gpurun`).
* **Pilot Budget Cap**: The entire pilot (~1,000 documents: ~500 bio, ~500 eng) must use strictly **well under 20.0 H200-hours**.
* **Budget Guardrails**:
  1. If any stage approaches or exceeds **80%** of its pre-run estimate, execution must **STOP** immediately and report.
  2. No scaling beyond the pilot without explicit user approval and a measured throughput calibration table.
  3. Spare weekly hours are NOT a justification to scale up; human quality review of the pilot cards comes first.
* **Weekly Consumption Log (Current Week: Starting 2026-10-26)**:
  * Weekly Allotment: 90.00 h
  * Current Broker Status: Remaining 90.00 h

| Date | Step / Task Description | Target Model / Job | Duration (s) | GPU-Hours | Cumulative Week Total | Remaining Weekly Quota |
|---|---|---|---|---|---|---|
| 2026-10-26 | Step 0: Recon & NVML probe | N/A (broker ping) | ~2 s | < 0.001 h | ~0.001 h | 90.00 h |
| 2026-10-26 | Step 3: Harvest pilot corpus | CPU Network I/O | ~180 s | 0.000 h | ~0.001 h | 90.00 h |

## 5. Decisions & Approvals Log
* [2026-10-26] Approved proceeding with Git connection on top of `5cf1d7b` on `main`.
* [2026-10-26] Approved proceeding with Step 1 (core Pydantic v2 schemas and unit tests).
* [2026-10-26] Step 1 Complete: Scaffolding deployed to `flbds/schema/` (`MechanismCard`, `ProblemCard`, `RoleBinding`, `VerificationReport`). All 15 unit tests passed on server (`pytest tests/test_schemas.py`). Pushed as commit `3843702`.
* [2026-10-26] Step 2 Complete: Source register verified live on server (`docs/source_register.md`). Identified migrations: PMC FTP -> AWS Open Data S3; PatentsView -> USPTO Open Data Portal (`data.uspto.gov`). Model candidates verified (Qwen2.5 72B/32B/7B under Apache 2.0). Pushed as commit `f07fb7e`.
* [2026-10-26] Server Directory Standardization: Standardized on `/home/abhishek24024/flbds` as the single real directory (removed symlink and renamed `FLBDS` to `flbds`).
* [2026-10-26] Step 3 Complete: Harvested 1,000 pilot documents server-side into `/home/abhishek24024/flbds_data/corpus/` (500 PMC bio articles, 22.38 MB; 500 US patents in CPC sections F and E, 12.67 MB). Reproducible scripts and 5-doc samples committed to git as commit `5bc5d2e`.
* [2026-10-26] Step 4 Model Research: Evaluated current state-of-the-art open instruct models across 8B, ~30B, and ~70B tiers on Hugging Face (October 2026 benchmark and licensing landscape). Reported gating, VRAM footprints, and vLLM FP8 support. Awaiting user approval before downloading any model weights.

* [2026-10-26] Step 4 Complete: Downloaded Qwen2.5-7B-Instruct (BF16, 15 GB), Qwen2.5-32B-Instruct-FP8-dynamic (32 GB), and Qwen2.5-72B-Instruct-FP8-dynamic (72 GB) to `/home/abhishek24024/flbds_data/models/`. Measured throughput on NVIDIA H200: 7B at 1,658 decode tok/s; 32B FP8 at 593.2 decode tok/s; 72B FP8 at 325.3 decode tok/s.
* [2026-10-26] BigPatent Provenance Clarification: Engineering corpus patents originate from Hugging Face `NortheasternUniversity/big_patent` (CPC sections F and E, filtered by thermal/fluid/insulation keywords, text up to ~2018), rather than direct USPTO bulk downloads, avoiding auth requirements.
* [2026-10-26] Bio Sample License Compliance: `data/sample/bio_sample.jsonl` replaced with strictly 5 CC BY / CC0 papers for GitHub repository compliance.

* [2026-10-26] Step 5 & Step 6 Autonomous Execution Complete:
  - Deployed master driver `scripts/run_pilot.sh` running Stages 0-7 resumably.
  - Smoke test executed on 40 docs (20 bio, 20 eng): 0.0676 GPU-hours.
  - Full pilot executed on 1,000 docs (500 bio, 500 eng): 0.2004 GPU-hours.
  - Stage 1 (7B Relevance Filter): 1,000 in -> 372 out, 628 dropped (46,841 tok/s, 0.0106 GPU-h).
  - Stage 2 (72B Teacher Drafting): 372 in -> 361 out, 11 dropped on schema validation (642.6 decode tok/s, 0.0925 GPU-h).
  - Stage 3 (72B Agreement Sample on 300 docs): Mean overall inter-sample agreement = 67.7% (subject: 67.1%, action verb: 80.5%, state variable: 82.3%, physical effect: 64.3%, phenomenon: 44.2%) across 298 valid pairs (648.3 decode tok/s, 0.0783 GPU-h).
  - Stage 4 (Deterministic Programmatic Evidence Verifier): 361 in -> 348 out, 13 dropped (0 valid spans). Evaluated 783 spans: 700 realigned to exact verbatim text, 83 hallucinated/unmatched spans dropped (CPU, 0.0 GPU-h).
  - Stage 5 (32B Causal Entailment Critic): 348 in -> 270 out, 78 dropped due to unentailed physical causal claims (3,012.9 decode tok/s, 0.0119 GPU-h).
  - Stage 6 (7B + Pint Quantity Extractor): 270 in -> 270 out. Extracted 573 quantities: 446 Pint-validated with SI units, 127 unparseable rejected (4,235.7 decode tok/s, 0.0071 GPU-h).
  - Stage 7 (Near-Duplicate Deduplication): 270 in -> 269 unique silver cards retained (1 duplicate removed, CPU, 0.0 GPU-h).
  - Step 6 Gold Annotation Tools: Sampled 30 documents (15 bio, 15 eng, seed=42) to `/home/abhishek24024/flbds_data/pilot/gold_candidates.json`. Built terminal side-by-side viewer `scripts/view_card.py` and field-level F1 evaluator `scripts/eval_f1.py` with 7 synthetic unit tests (`tests/test_eval_f1.py`).
  - Total Pilot GPU-Hours: 0.2004 h (Full) + 0.0676 h (Smoke) + ~0.05 h (Calibration) = ~0.318 GPU-hours total, well within the 20.0 h pilot cap and 90.0 h weekly quota.
