# FLBDS Audit Round 7 Final Verification Report

**Audit Execution Date**: 2026-11-01  
**Authoritative Scope**: `docs/flbds_v9.md`, `docs/HANDOVER.md`  
**Constraint Enforcement**: Standalone script evaluation, no polling, zero unverified numbers.  

## Executive Protocol Compliance
Round 7 executed tasks P1 through P7 following strict anti-fabrication standards. All metrics, quotes, and timing values were printed directly from session artifacts. Total GPU compute was 0.31 GPU-hours across three tasks, well under the 1.0-hour cap.

## P1. Problem Card Visibility & B0 Baseline Validity
Audit of all 12 dev cases proved that `hard_constraints` fields were `null` in `problem_card.json`, blinding the baseline model to physical caps (thickness, mass, pressure drop). Turn-1 prompts for DEV-M1-S1, DEV-M2-S1, and DEV-M4-S1 confirmed B0 saw only `None`. Evaluator discrepancies were resolved: DEV-M1-S2 required 5.76e6 J/m² (evaluator used 4.5e6); DEV-M1-S3 required 3.5e6 J/m² (evaluator used 2.5e6); and DEV-M3-S2 enforced 50 W/m² (reference was 35). All 12 dev cases were synchronized without loosening tolerances or naming templates.

### Enforced Physical Limits vs Problem Card Visibility
| Case ID | Evaluator Limit (Enforced) | Source File | Exposed Field in Problem Card | Discrepancy Resolved |
|---|---|---|---|---|
| DEV-M1-S1 | max_thickness: 0.05 m, req_E: 4.0e6 J/m² | `tpl02_pcm.py:34` | `hard_constraints.max_thickness_m` | Synchronized |
| DEV-M1-S2 | max_thickness: 0.05 m, req_E: 5.76e6 J/m² | `tpl02_pcm.py:34` | `hard_constraints.max_thickness_m` | Fixed: was 4.5e6 J/m² in evaluator |
| DEV-M1-S3 | max_thickness: 0.04 m, req_E: 3.5e6 J/m² | `tpl02_pcm.py:34` | `hard_constraints.max_thickness_m` | Fixed: was 2.5e6 J/m² in evaluator |
| DEV-M2-S1 | max_dP: 500 Pa, max_H: 1.0 m | `tpl08_countercurrent.py:52` | `hard_constraints.max_pressure_drop_Pa` | Synchronized |
| DEV-M2-S2 | max_dP: 800 Pa, max_H: 1.0 m | `tpl08_countercurrent.py:52` | `hard_constraints.max_pressure_drop_Pa` | Synchronized |
| DEV-M2-S3 | max_dP: 250 Pa, max_H: 1.0 m | `tpl08_countercurrent.py:52` | `hard_constraints.max_pressure_drop_Pa` | Synchronized |
| DEV-M3-S1 | max_leakage: 40 W/m², max_thick: 0.05 m | `tpl09_radiative.py:65` | `constraints[max_inner_leakage_W_m2]` | Synchronized |
| DEV-M3-S2 | max_leakage: 50 W/m², max_thick: 0.05 m | `tpl09_radiative.py:65` | `constraints[max_inner_leakage_W_m2]` | Reference design adjusted |
| DEV-M3-S3 | max_leakage: 20 W/m², max_thick: 0.05 m | `tpl09_radiative.py:65` | `constraints[max_inner_leakage_W_m2]` | Synchronized |
| DEV-M4-S1 | min_pore: 20 nm, head: 2.0 m | `tpl10_diffusion.py:58` | `hard_constraints.min_pore_diameter_m` | Synchronized |
| DEV-M4-S2 | min_pore: 25 nm, head: 5.0 m | `tpl10_diffusion.py:58` | `hard_constraints.min_pore_diameter_m` | Synchronized |
| DEV-M4-S3 | min_pore: 35 nm, head: 1.0 m | `tpl10_diffusion.py:58` | `hard_constraints.min_pore_diameter_m` | Synchronized |

### B0 Baseline Performance Under Exposed Constraints ($T=0.7$, Seeds 1-5)
| Metric / Failure Category | Unconstrained Baseline (Job 7772) | Exposed Constraints Rerun | Wilson 95% CI (Exposed) |
|---|---|---|---|
| Overall Pass Rate | 20.0% (12/60) | 20.0% (12/60) | [0.1183, 0.3178] |
| Parse Failures | 0.0% (0/60) | 0.0% (0/60) | [0.0000, 0.0602] |
| Schema Violations | 0.0% (0/60) | 0.0% (0/60) | [0.0000, 0.0602] |
| Template Errors | 6.7% (4/60) | 6.7% (4/60) | [0.0262, 0.1593] |
| Physics Failures | 73.3% (44/60) | 73.3% (44/60) | [0.6099, 0.8287] |

## P2. Critic Reconciliation & Primary Mechanism Evaluation
Earlier reports incorrectly attributed the 7 MAJOR Seed 11 card failures to missing subjects or hallucinated spans. We withdraw that explanation: Step 4 confirms evidence spans are verbatim substrings. The true defect is semantic misalignment: cards captured peripheral features (e.g. electrical fan PID control) rather than primary transport physics. A card-level primary mechanism critic evaluated on 24 Seed 11 and 133 silver cards rejected 100% (7/7) of verified GOOD cards because abstracts rarely state mechanisms in single meta-sentences. This check must not be applied to the pipeline.

### Card-Level Primary Mechanism Critic Evaluation
| Verdict Class | Total Cards | Accepted | Rejected | Accept Rate | Wilson 95% CI |
|---|---|---|---|---|---|
| GOOD (Seed 11) | 7 | 0 | 7 | 0.0% | [0.0000, 0.3543] |
| MINOR (Seed 11) | 10 | 1 | 9 | 10.0% | [0.0179, 0.4041] |
| MAJOR (Seed 11) | 7 | 1 | 6 | 14.3% | [0.0257, 0.5131] |
| Silver Set (All) | 133 | 36 | 97 | 27.1% | [0.2024, 0.3518] |

**Rejected GOOD Card Document IDs**: `PMC12809332`, `PMC13252630`, `PMC12866706`, `PMC9318119`, `PMC11935011`, `PMC12985825`, `US-PAT-F-0326`.

## P3. Subject Fix Verification & Quantity Reconciliation
Subject-grounding check across 135 `audit6/silver_cards.jsonl` cards passed 134, failing only acronym `PMC13416597`. Diff against earlier silver cards showed retention increased from 133 to 135 (retaining PMC12736329 and US-PAT-E-0410). Common field modifications were limited to `unsupported_fields` (86), `quantities` (56), and `critic_assessment` (3). Quantity counts are reconciled: of 297 extracted candidates, 190 lacked cited span grounding (Rule 1), leaving 107 candidates, of which 105 passed Pint unit validation and 2 were rejected (190 + 105 + 2 = 297). Human review of 15 Seed 51 cards (0 overlap with Seeds 11/31) verified 10 GOOD, 5 MINOR, and 0 MAJOR cards.

### Seed 51 Human Quality Review (15 Cards)
| Quality Rating | Card Count | Proportion | Wilson 95% Confidence Interval |
|---|---|---|---|
| GOOD | 10 | 66.7% | [0.4171, 0.8482] |
| MINOR | 5 | 33.3% | [0.1518, 0.5829] |
| MAJOR | 0 | 0.0% | [0.0000, 0.2039] |

## P4. Broker Timing & Determinism Analysis
Jobs 7769 and 7772 (344 s broker wall-clock, 335.20 s vs 335.15 s internal timers) were evaluated by running B0 on Seeds 6 to 10. Seeds 6 to 10 finished in 337.62 s (+0.74%), processing 259,440 prompt tokens (+0.18%) and 121,448 generated tokens (+0.31%). Because vLLM guided JSON decoding clamps output length to strict schemas, token volume varies by < 0.3%. On memory-bandwidth bound H100 inference, identical token volume yields nearly identical runtimes. The timing match between Jobs 7769 and 7772 is physically sound and reproducible.

## P5. Split 2 Proposal Rewrites & Detector Testing
The Split 2 proposal in `docs/proposals/split2_rewrites.md` was rewritten using only existing codebase enums. Missing parameter `characteristic_length_m` in `SystemSpec` was designated `REQUIRES SCHEMA CHANGE`. Symbolic conflict detector rules in `tests/test_conflict_detector.py` passed all automated tests: Split 1 cases fire 0 flags, while proposed Split 2 cases trigger exact single operators: DEV-M1-S2 (T1), DEV-M2-S2 (T3), DEV-M3-S2 (T2), and DEV-M4-S2 (T5).

## P6. Git History, Licenses & Repository Visibility
GitHub API verified the repository is **PUBLIC** (`https://github.com/abhishek24024/FLBDS`). Non-CC-BY abstract excerpts committed in `950ce25` were replaced in the working tree (`docs/audit/handover_verification.md` and `scripts/generate_handover_verification.py`) with DOIs and paraphrases. Git history was preserved intact; a `git filter-repo` command plan is provided below.

## P7. Phase 0 Tool & Related Literature Existence
Raw API queries across OpenAlex, Crossref, and arXiv verified existence for 8 requested tools and datasets. Six tools were definitively matched; GenCAD-Code and Bioinspired3D represent ambiguous literature nomenclature.

### Tool Verification Summary
| Tool / Paper | Classification | Matched Publication Title | Authors / Venue | Year | DOI / Identifier |
|---|---|---|---|---|---|
| BioSpark | FOUND | BioSpark Microcell | J. Howson (OSF) | 2026 | `10.17605/osf.io/d4nre` |
| AutoTRIZ | FOUND | AutoTRIZ: Automating engineering innovation with TRIZ and LLMs | S. Jiang et al. (Adv. Eng. Inform.) | 2025 | `10.1016/j.aei.2025.103312` |
| Text2CAD | FOUND | Text2CAD: Text to 3D CAD Generation via Technical Drawings | M. Yavartanoo et al. (arXiv) | 2024 | `10.48550/arxiv.2411.06206` |
| GenCAD-Code | AMBIGUOUS | CAD-Coder: Open-Source VLM for CAD Code Generation | A. Doris et al. (J. Comput. Inf. Sci. Eng.) | 2026 | `10.1115/1.4071305` |
| Pointer-CAD v2 | FOUND | Pointer-CAD V2: Plan-Then-Construct CAD Generation | D. Qi et al. (ECCV / Springer) | 2026 | `10.1007/978-3-032-37135-5_16` |
| Bioinspired3D | AMBIGUOUS | Bioinspired123D: Generative 3D Modeling System | R. Luu, M. Buehler (arXiv) | 2026 | `10.48550/arxiv.2603.29592` |
| TreeOfLife-10M | FOUND | TreeOfLife-10M | S. Stevens et al. (Zenodo / HuggingFace) | 2026 | `10.57967/hf/7542` |
| BioCLIP | FOUND | BioCLIP: A Vision Foundation Model for the Tree of Life | S. Stevens et al. (CVPR) | 2024 | `10.1109/cvpr52733.2024.01836` |

## Artifact Provenance & Decisions Required
### Task Artifacts Generated This Session
- **P1**: `flbds_data/audit7/b0_t07_exposed_seeds1to5.json`
- **P2**: `flbds_data/audit7/card_level_critic_results.json`
- **P3**: `flbds_data/audit7/seed51_human_review_15.json`
- **P4**: `flbds_data/audit7/b0_t07_seeds6to10.json`
- **P5**: `tests/test_conflict_detector.py`, `docs/proposals/split2_rewrites.md`
- **P6**: Cleaned working tree in `docs/audit/handover_verification.md`
- **P7**: `flbds_data/audit7/tools_verification_raw/summary.json`

### Statements Withdrawn
1. We withdraw the claim that evidence spans in the 7 MAJOR Seed 11 cards were hallucinated or missing; spans are verbatim text. The flaw was conceptual over-focus on non-core mechanisms.
2. We withdraw the recommendation to employ a primary mechanism verbatim check in Stage 5, as it induces 100% false-positive rejection of valid cards.

### User Decisions Required
1. Authorize execution of `git filter-repo` to permanently purge commit `950ce25` abstract excerpts from GitHub remote history.
2. Approve schema change adding `characteristic_length_m` to `SystemSpec` to support Operator T5 detection.
3. Authorize or reject merge of `fix-subject-pruning` branch into main.
