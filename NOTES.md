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

## 5. Decisions & Approvals Log
* [2026-10-26] Approved proceeding with Git connection on top of `5cf1d7b` on `main`.
* [2026-10-26] Approved proceeding with Step 1 (core Pydantic v2 schemas and unit tests).
