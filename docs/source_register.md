# FLBDS Source Register (Phase 0 / Step 2 Verification)

*Status: Verified on-server on 2026-10-26*  
*Scope: Sources strictly used for the thermal, fluid, and porous-media BTech pilot project.*

---

## 1. PubMed Central Open Access (PMC OA) Subset (Biology Domain)

* **Claimed in `flbds_v5.md`**:
  * Free access to open-access biological papers; mechanism extraction on thermal/fluid functions; CC BY and CC0 licenses.
* **Verified Real URL & Endpoints**:
  * Primary Cloud Distribution: AWS Open Data S3 (`s3://pmc-oa-opendata/`, HTTPS: `https://pmc-oa-opendata.s3.amazonaws.com/`)
  * Documentation: `https://pmc.ncbi.nlm.nih.gov/tools/cloud/` and `https://registry.opendata.aws/ncbi-pmc`
  * API Search & Metadata: NCBI E-utilities (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`)
* **Date Checked**: 2026-10-26
* **Status**: **CONFIRMED (with infrastructure correction)**
* **Document Claim Verification**:
  * *Correction*: As of August 2026, NCBI has deprecated and removed legacy bulk download archives from its FTP server (`https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/` returns 404; see official notice in `ftp.ncbi.nlm.nih.gov/pub/pmc/readme.txt`).
  * *Operational Endpoint*: All full-text open-access records (JSON, XML, TXT, PDF) are now distributed via the AWS Open Data mirror at `https://pmc-oa-opendata.s3.amazonaws.com/`. Verified live on-server that individual article records (e.g. `PMC10000000.1.json`) are directly reachable over HTTPS without AWS credentials.
  * *Searchability*: NCBI E-utilities `esearch` is live and functional for querying thermal and fluid keywords (`thermoregulation`, `evaporative cooling`, `wicking`, `heat storage`, etc.).
* **Licence & Terms**:
  * Articles carry publisher-assigned licenses recorded in each article's JSON metadata (`license_code` field: `CC0`, `CC BY`, `CC BY-SA`, `CC BY-NC`, `CC BY-ND`).
  * For FLBDS pilot redistribution, filtering will strictly select **CC BY** and **CC0** articles.
  * Usage terms: Must acknowledge NLM/NCBI as source; cannot use PMC wordmark/logo to imply endorsement.

---

## 2. USPTO Patents / PatentsView (Engineering Domain)

* **Claimed in `flbds_v5.md`**:
  * PatentsView full text and CPC classes (F28, F24, E04) accessible via `patentsview.org` and USPTO bulk data at `bulkdata.uspto.gov`. Public domain data.
* **Verified Real URL & Endpoints**:
  * New Portal: USPTO Open Data Portal (ODP) at `https://data.uspto.gov`
  * Migration Guide: `https://data.uspto.gov/support/transition-guide/patentsview`
  * Granted Patents Disambiguated Tables (including CPC mappings): `https://data.uspto.gov/bulkdata/datasets/pvgpatdis`
  * Granted Patents Long Text Tables (Brief Summary, Claims, Detail Description): `https://data.uspto.gov/bulkdata/datasets/pvgpattxt`
* **Date Checked**: 2026-10-26
* **Status**: **CONFIRMED (with domain migration correction)**
* **Document Claim Verification**:
  * *Correction*: The legacy `patentsview.org` domain and `bulkdata.uspto.gov` DNS endpoints have transitioned to the USPTO Open Data Portal (`data.uspto.gov`). HTTP/2 301 redirects are in place from `patentsview.org` to `data.uspto.gov`.
  * *Bulk Access*: Bulk tables (`g_patent`, `g_cpc_current`, `g_brf_sum_text`) are hosted under `data.uspto.gov/bulkdata/`.
* **Licence & Terms**:
  * **Public Domain**: Works created by the US Federal Government and patent grants published by the USPTO are not subject to domestic copyright protection (17 U.S.C. § 105).
  * Terms: Freely reusable for academic and commercial purposes without royalty or license fees.

---

## 3. Candidate Open Model Weights (Inference Only)

* **Claimed in `flbds_v5.md`**:
  * ~70B-class instruct model in FP8 (~72 GB) as teacher.
  * ~30B-class instruct model in FP8 (~32 GB) as critic.
  * ~8B-class instruct model in BF16 (~16 GB) as filter and extractor.
  * Target hardware: 1 x NVIDIA H200 (141 GB HBM3e).
* **Verified Hugging Face Candidates**:
  1. **Teacher Model (~70B)**:
     * Candidate: `Qwen/Qwen2.5-72B-Instruct`
     * License: **Apache 2.0** (permissive, open)
     * Weights size: ~144 GB in BF16. When loaded with vLLM's native dynamic FP8 quantization (`--quantization fp8`), memory footprint is ~72 GB, leaving ~69 GB for KV cache. Alternatively, pre-quantized FP8 community weights (e.g. `RedHatAI/Qwen2.5-72B-Instruct-FP8-dynamic`) can be pulled directly.
  2. **Critic Model (~30B)**:
     * Candidate: `Qwen/Qwen2.5-32B-Instruct`
     * License: **Apache 2.0**
     * Weights size: ~64 GB in BF16; ~32 GB in FP8 via vLLM.
  3. **Filter & Quantity Extractor (~8B)**:
     * Candidate: `Qwen/Qwen2.5-7B-Instruct`
     * License: **Apache 2.0**
     * Weights size: ~15 GB in BF16.
* **Date Checked**: 2026-10-26
* **Status**: **CONFIRMED**
* **Notes on Other Models Checked**:
  * `neuralmagic/Qwen2.5-72B-Instruct-FP8`: Returned HTTP 401 Unauthorized (requires authorization or private repo).
  * `meta-llama/Llama-3.1-8B-Instruct`: Gated repository requiring user acceptance and a Hugging Face user token. The `Qwen2.5` family is completely ungated under Apache 2.0 and is recommended.

---

## 4. Verification Summary Matrix

| Source Identifier | Claim in `flbds_v5.md` | Verified Reality | Licence Confirmed | Status |
|---|---|---|---|---|
| **PMC OA Subset** | FTP / Bulk download | Legacy FTP removed (Aug 2026); AWS S3 Open Data mirror is live | CC BY / CC0 per document | **PASS (Redirected to AWS S3)** |
| **USPTO Patents** | `patentsview.org` | Migrated to USPTO Open Data Portal (`data.uspto.gov`) | US Public Domain | **PASS (Redirected to ODP)** |
| **70B Teacher** | 70B FP8 (~72 GB) | `Qwen/Qwen2.5-72B-Instruct` available; vLLM FP8 supported | Apache 2.0 | **PASS** |
| **30B Critic** | 30B FP8 (~32 GB) | `Qwen/Qwen2.5-32B-Instruct` available | Apache 2.0 | **PASS** |
| **8B Filter** | 8B BF16 (~16 GB) | `Qwen/Qwen2.5-7B-Instruct` available | Apache 2.0 | **PASS** |
