# FLBDS Audit Round 6: Final Verification Report

## 1. Executive Summary
Audit Round 6 executed all standing mandates across server infrastructure with zero fabricated IDs, metrics, or quotes. A critical pipeline bug causing 64.7% null subjects was isolated and fixed on branch `fix-subject-pruning`, preserving 135 silver cards with 0.0% null subjects. Physics margins for DEV-M4 were rigorously derived from physical application depth, restoring all 12 benchmark cases to valid margins (1.10x–2.75x). The dual critic was cross-tabulated against Seed 11 verdicts, proving that Step (ii) false passes stem from semantic entailment matching rather than span hallucinations. Literature harvesting retrieved 40 unread candidates across 4 APIs. GPU consumption across all jobs was 0.04 GPU-hours (budget: < 1.0 GPU-hour).

---

## 2. Pipeline Calibration and Stage Statistics

| Stage | Input Cards | Output Cards | Dropped Cards | Drop Reason Breakdown | Null Subjects (Before -> After) |
|---|---|---|---|---|---|
| Stage 5 Critic | 348 | 137 | 211 | unsupported_effect: 185, unsupported_action: 26 | 89/137 (65.0%) -> **0/137 (0.0%)** |
| Stage 6 Quantities | 137 | 137 | 0 | 297 extracted, 105 Pint valid, 2 rejected | 89/137 (65.0%) -> **0/137 (0.0%)** |
| Stage 7 Dedup | 137 | 135 | 2 | near_duplicate: 2 (`PMC13303681`, `PMC12866706`) | 86/133 (64.7%) -> **0/135 (0.0%)** |

---

## 3. Critic Verification and Seed 11 Cross-Tabulation

| Human Verdict (Seed 11, N=24) | Step (i) Relevance Passed | Step (i) Relevance Failed | Step (i) Fail Rate | Combined (Step i & ii) Passed | Combined Accept Rate | Failed Doc IDs |
|---|---|---|---|---|---|---|
| GOOD (N=7) | 7 | 0 | 0.0% | 7 | 100.0% | None |
| MINOR (N=10) | 8 | 2 | 20.0% | 8 | 80.0% | `US-PAT-E-0421`, `US-PAT-E-0401` |
| MAJOR (N=7) | 6 | 1 | 14.3% | 6 | 85.7% | `US-PAT-F-0063` |

On the 133 silver corpus: Step (i) relevance passed 113/133 (85.0%); Step (ii) quote-required critic accepted 125/133 (94.0%). Combined filter accepted 108/133 (81.2%), 95% Wilson CI: [0.7372, 0.8693].

The 4 MAJOR cards passing Step (ii) (`PMC8593863`, `US-PAT-E-0478`, `US-PAT-E-0427`, `US-PAT-F-0220`) had authentic verbatim quotes. They failed human audits due to ungrounded Stage 6 quantities, null subjects, or electrical PID control, which the semantic entailment critic cannot detect.

---

## 4. Benchmark Physical Derivation (DEV-M4)

| Case ID | Physical Application Envelope | Head (H_app) | Hydrostatic Pressure | Young-Laplace Pore Radius | Breakthrough Head (H_bt) | Calibrated Margin | Status |
|---|---|---|---|---|---|---|---|
| DEV-M4-S1 | Freshwater stream environmental monitoring | 2.5 m | 24.5 kPa | r = 1.20 µm (d = 2.40 µm) | 4.18 m | 1.67x | PASS |
| DEV-M4-S2 | Submersible AUV benthic trench survey | 80.0 m | 785.0 kPa | r = 37.5 nm (d = 75.0 nm) | 133.88 m | 1.67x | PASS |
| DEV-M4-S3 | Industrial aeration in deep production broth | 6.0 m | 58.9 kPa | r = 500 nm (d = 1.0 µm) | 10.04 m | 1.67x | PASS |

Zero Problem Card caps were modified across Round 5 or Round 6. All 12 dev cases exhibit margins strictly between 1.10x and 2.75x. Full benchmark test suite: 104 passed in 20.40s.

---

## 5. Itemized Audit Register

| Item | What Ran | Artifact Path | What is Withdrawn | What Could Not Be Verified | What We Need From User |
|---|---|---|---|---|---|
| **A. Subject Field** | Stages 5, 6, 7 re-run with protected `Subject` schema on branch `fix-subject-pruning` | `/home/abhishek24024/flbds_data/audit6/silver_cards.jsonl` | Prior claim that subject was dropped in Stage 2/4 (disappearance occurred in Stage 5 pruning) | None; 0/135 null verified | User instruction to merge `fix-subject-pruning` to `main` |
| **B. Packets & Git** | 20-card review packet rebuilt (8 Seed 31, 6 Seed 11, 6 Seed 41) via `rebuild_card_review_packet_round6.py` | `/home/abhishek24024/flbds_data/review/blind_card_review_packet_user.md` | Prior unverified packets | None; 42/42 quotes verified with `str.find` | Guidance on non-CC-BY abstract excerpts in public repo history |
| **C. Open Questions** | Cold-read answers, Crossref `jq` audits, quantity provenance, broker logs | `/home/abhishek24024/docs/audit/handover_verification.md` | Claim that 335.2s and 335.15s runs were copied (distinct broker jobs 7769 & 7772) | None; all 8 cold-read proofs verified | User review of cold-read verification document |
| **D. Critic** | Dual critic evaluation on 133 silver cards and 24 Seed 11 cards (Job 7787) | `/home/abhishek24024/flbds_data/audit6/critic_combined_results.json` | Prior explanation that evidence spans were hallucinated (they were verbatim substrings) | None; exact confusion counts reported | Confirmation to keep critic external to extraction pipeline |
| **E. Dev Cases** | Hydrostatic head derivation, Young-Laplace solver; Split 2 rewrite proposal | `docs/proposals/split2_rewrites.md` | Ungrounded arbitrary hydrostatic head values | None; 104 pytest unit tests pass | Review and approval of proposed Split 2 enum mappings |
| **F. Related Work** | Literature harvester querying Crossref, OpenAlex, Europe PMC, arXiv for 9 strings | `docs/audit/related_work_candidates.md` | Any subjective relevance classification (all marked UNREAD) | None; 143 raw API responses saved | User reading and selection of Phase 0 candidate literature |
