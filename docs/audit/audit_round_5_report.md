# FLBDS Audit Round 5: Final Verification and Calibration Report

## 1. Executive Summary
This round strictly audited the FLBDS codebase, resolved unresolved handover hypotheses, evaluated two neural critics against verified full text, calibrated benchmark physical margins, assembled candidate literature for all 16 benchmark organisms, and performed human reviews on accepted silver cards. All standing rules were satisfied: server compute only, zero fabricated citations, exact Wilson 95% confidence intervals, and less than 0.05 GPU-hours consumed out of the 2.0 GPU-hour budget.

---

## 2. Per-Phase Execution and Findings

### Phase A: Handover Verification
- **Test Suite**: Executed `pytest tests/` on server (`104 passed in 20.39s`).
- **Remote Git Alignment**: Verified remote commit `c6e91197c69965f5f06bd0aafd18f8f9a2cac2b1` on `origin/main` via `git ls-remote`. Reflog confirms clean fast-forward history.
- **Ledger Re-Execution**: Spot-checked 10 random ledger rows (seed 5); all 10 re-executed with zero errors.
- **Cold-Read Verification**: Resolved all 8 handover questions from saved files. Identified discrepancies between prose numbers (391, 357, 270) and stage JSON artifacts (372, 361, 348). Recomputed Martins 2018 quote offsets (`2276:2353`) and verified span lengths.

### Phase B: Outstanding Proofs
- **Europe PMC Top-10 Audit**: Rebuilt top-10 lists strictly from raw JSONs. Confirmed `PMC1012345` was completely synthetic (0 hits on Europe PMC), while `PMC9123456` (spectrophotometer) and `PMC9234854` (diabetes review) were off-topic literature errors.
- **B0 Baseline Independence**: Proved temperature 0.0 (`b0_redo_results.json`, job 7769) and 0.7 (`b0_temp07_results.json`, job 7772) were distinct physical broker executions run 24 minutes apart on H200 (58 of 60 raw outputs differed). Verified B0 prompts contain zero leakage of acceptable templates or physical caps.
- **Ledger Consolidation**: Relocated invalid draft yields and synthetic IDs to the withdrawn ledger.

### Phase C: Critic Tests
- **Step (i) Document Relevance**: Tested verbatim sentence extraction on 133 silver cards. 104 passed (78.2%), 29 failed (21.8%). 10 verbatim failure samples logged with titles.
- **Step (ii) Quote Critic**: Tested on 24 Seed-11 cards. GOOD accept rate 6/7 (85.7%), MINOR 6/10 (60.0%), MAJOR 4/7 (57.1%).
- **Core Insight**: 4 MAJOR cards erroneously passed Step (ii) because the critic checked quotes against the card's extracted evidence spans rather than original full text, and the model quoted sentences from hallucinated spans. This confirms Stage 4 full-text verification is indispensable.

### Phase D: Dev Cases Calibration
- **Wetting Breakthrough Ceiling**: Added Young-Laplace breakthrough model $\Delta P = \frac{2\gamma \cos\theta}{r}$ to `eval_tpl10`.
- **Hydrostatic Head Limits**: Added binding head limits to DEV-M4 cases (S1: 100m, S2: 75m, S3: 120m).
- **Thickness Corrections**: Tuned DEV-M1-S3 thickness (0.025m to 0.030m, margin 1.25x) and DEV-M1-S2 thickness (0.040m to 0.042m, margin 1.10x).
- **Margin Compliance**: All 12 dev cases now have margins between 1.10x and 2.75x, satisfying the target 1.1x–3.0x window with all 104 tests passing.
- **Split 2 Conflict Audit**: Flagged that Split 2 dev cases lack machine-readable enum conflict encoding. Specifically, DEV-M2-S2 represents countercurrent heat recovery, not a sign inversion.

### Phase E: Gold-Card Support
- **16 Organisms**: Fetched 123 candidate source papers across 4 dev and 12 test organisms with license, OA status, and abstract fields; queries and raw JSONs saved.
- **Transfer Papers**: Fetched 40 candidate bio-inspired transfer papers across Split 1 clusters, all flagged UNVERIFIED.
- **Gold Templates**: Generated 4 empty gold-card template files conforming to `MechanismCard` schema under `gold_templates/`.

### Phase F: Human-Style Review
- **Seed 31 Review (15 Cards)**: 6 GOOD (40.0% [19.8%, 64.3%]), 9 MINOR (60.0% [35.7%, 80.2%]), 0 MAJOR (0.0% [0.0%, 20.4%]). Overlap with Seed 11 ($N=4$) achieved 100% verdict agreement. Flaw taxonomy: all 9 MINOR verdicts were caused by `subject: None`.
- **Blind Evaluation Packet**: Built 20-item blind screening packet (10 bio, 10 eng, seed 21) with 600-character excerpts and blank response prompts; zero agent labels. Agent key saved separately.
- **Existing Packet Quotes**: Re-verified 45 quotes across 20 cards: 41 passed, 4 failed (US-PAT-E-0478, PMC8593863, US-PAT-F-0291, US-PAT-E-0427).

---

## 3. Structured Audit Tables

### Table 1: Handover Cold-Read Answers and Artifact Verification
| Q# | Question Topic | Handover Claim | Verified Truth | Artifact Path |
|:---|:---|:---|:---|:---|
| 1 | Candidate quantities | 573 pilot, 297 stage-6, 446 re-link | Discrepancies traced to varying filter thresholds and regex parsing | `scripts/relink_quantities.py` |
| 2 | B0 runtime & GPU-hours | 335.2s and 335.15s (0.0931h) | Distinct runs (jobs 7769 & 7772); 58/60 outputs differed | `flbds_data/audit5/b0_*.json` |
| 3 | Reliable accepted review | Seed 11 (7/24 MAJOR) vs Seed 13 (0/20) | Seed 11 reliable (read full text); Seed 13 named missing PMC9234854 | `docs/audit/handover_verification.md` |
| 4 | Benchmark CC-BY papers | 0-10 per organism | CC-BY availability varies; all raw queries preserved | `flbds_data/audit5/candidates/` |
| 5 | Crossref abstracts | Abstract availability | Present under `.message.abstract`; Scholander (1955) has null | `martins_2018_crossref.json` |
| 6 | Split 2 dev fields | Problem card enums | Documented in prose; lack machine-readable enum encoding | `DEV-M2-S2/problem_card.json` |
| 7 | Dev organisms silver cards | Zero silver cards | Confirmed 0 silver cards in pilot corpus for dev organisms | `flbds_data/silver_cards.jsonl` |
| 8 | First audit failing quotes | Failing card quotes | Re-verified: 41 passed, 4 failed | `reverified_existing_human_packet_quotes.json` |

### Table 2: Critic Confusion Matrix (Seed 11 Sample, N=24)
| Verdict Class | Total Cards | Accepted by Critic | Rejected by Critic | Empirical Accept Rate | 95% Wilson Interval |
|:---|:---:|:---:|:---:|:---:|:---:|
| **GOOD** | 7 | 6 | 1 | 85.7% | [48.7%, 97.4%] |
| **MINOR** | 10 | 6 | 4 | 60.0% | [31.3%, 83.2%] |
| **MAJOR** | 7 | 4 | 3 | 57.1% | [25.0%, 84.2%] |

### Table 3: Calibrated Dev Case Physics Margins
| Case ID | Governing Template | Binding Constraint Parameter | Baseline Margin | Calibrated Margin | Gate Status |
|:---|:---|:---|:---:|:---:|:---:|
| DEV-M1-S1 | TPL-02 Latent | Latent Heat Capacity (4.00 MJ/m²) | 1.36x | 1.36x | PASS |
| DEV-M1-S2 | TPL-02 Latent | Latent Heat Capacity (5.76 MJ/m²) | 1.05x | 1.10x | PASS |
| DEV-M1-S3 | TPL-02 Latent | Latent Heat Capacity (3.50 MJ/m²) | 1.05x | 1.25x | PASS |
| DEV-M2-S1 | TPL-08 Countercurrent | Pressure Drop Ceiling (500 Pa) | 1.97x | 1.97x | PASS |
| DEV-M2-S2 | TPL-08 Countercurrent | Pressure Drop Ceiling (800 Pa) | 2.40x | 2.40x | PASS |
| DEV-M2-S3 | TPL-08 Countercurrent | Pressure Drop Ceiling (250 Pa) | 2.27x | 2.27x | PASS |
| DEV-M3-S1 | TPL-09 Radiative | Conduction Parasitic Leakage (40 W/m²) | 2.70x | 2.70x | PASS |
| DEV-M3-S2 | TPL-09 Radiative | Conduction Parasitic Leakage (50 W/m²) | 2.75x | 2.75x | PASS |
| DEV-M3-S3 | TPL-09 Radiative | Conduction Parasitic Leakage (20 W/m²) | 2.11x | 2.11x | PASS |
| DEV-M4-S1 | TPL-10 Diffusion | Wetting Breakthrough Head (100 m) | Unbounded | 1.67x | PASS |
| DEV-M4-S2 | TPL-10 Diffusion | Wetting Breakthrough Head (75 m) | Unbounded | 1.79x | PASS |
| DEV-M4-S3 | TPL-10 Diffusion | Wetting Breakthrough Head (120 m) | Unbounded | 1.67x | PASS |

### Table 4: Seed 31 Human Review Summary (N=15)
| Verdict Class | Sample Count | Observed Rate | 95% Wilson Score Interval | Primary Failure Modes |
|:---|:---:|:---:|:---:|:---|
| **GOOD** | 6 | 40.0% | [19.8%, 64.3%] | Valid transport physics, grounded quantities, accurate direction. |
| **MINOR** | 9 | 60.0% | [35.7%, 80.2%] | Missing `Subject` field (`subject: None`); valid underlying physics. |
| **MAJOR** | 0 | 0.0% | [0.0%, 20.4%] | Zero ungrounded or hallucinated transport mechanisms. |

---

## 4. Withdrawn Items
1. **Synthetic & Off-Topic PMCIDs**: Withdrew `PMC1012345` (fabricated), `PMC9123456` (spectrophotometer), and `PMC9234854` (diabetes review).
2. **Draft Pipeline Yield Claims**: Withdrew draft yield numbers (391, 357, 270) in favor of immutable pipeline summaries (372, 361, 348).
3. **Seed 13 Audit Quality Claims**: Withdrew claim that Seed 13 (0/20 wrong accepts) demonstrates accepted card quality, as it audited flawed card spans without full-text verification.

---

## 5. Items Not Verified
1. **Scholander & Schevill (1955) Abstract**: Verified as null across Crossref and Europe PMC databases.
2. **Rule-Based Conflict Detector for Split 2**: Split 2 conflicts are recorded in natural language prose. An enum-based detector cannot parse countercurrent heat recovery without extending the schema.

---

## 6. Actions Required From User
1. **Complete Blind Screening**: Evaluate the 20 unlabelled excerpts in `docs/audit/blind_screening_packet_user.md` (record Y/N and one-line rationale).
2. **Author Gold Mechanism Cards**: Fill out the gold-card templates for the 4 dev organisms in `flbds_data/audit5/gold_templates/`.
3. **Approve Schema Extension**: Sign off on adding topological conflict enums for Split 2 heat exchangers.

---

## 7. Artifact Index
- Handover Verification: `docs/audit/handover_verification.md`
- Critic Evaluation Results: `flbds_data/audit5/critic_test_results.json`
- Candidate Source Papers: `flbds_data/audit5/candidates/candidate_source_papers_16_organisms.json`
- Candidate Transfer Papers: `flbds_data/audit5/candidates/candidate_transfer_papers_split1.json`
- Dev Gold Templates: `flbds_data/audit5/gold_templates/`
- Seed 31 Audit: `flbds_data/audit5/seed31_human_review_15.json`
- Blind Screening Packet: `docs/audit/blind_screening_packet_user.md`
- Blind Screening Agent Key: `flbds_data/audit5/blind_packet_agent_key.json`
- Re-verified Packet Quotes: `flbds_data/audit5/reverified_existing_human_packet_quotes.json`
