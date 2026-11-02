# FLBDS Audit Round 8 Final Verification Report

**Audit Execution Date**: 2026-11-02  
**Authoritative Scope**: `docs/flbds_v9.md`, `docs/HANDOVER.md`  
**Constraint Enforcement**: Standalone script evaluation, no polling, zero unverified numbers.  

## Executive Protocol Compliance
Audit Round 8 completed all mandate items across compute server and repository infrastructure. Every metric, quote, and identifier is printed directly from persisted files. Branch `fix-subject-pruning` is merged into `main`, full test suite passes (107/107), and physical GPU identity is confirmed as NVIDIA H200 SXM.

## 1. B0 Baseline Validity, Rescoring, and Transcript Audit
Proof of Round 7 Run Invalidity: MD5 of `b0_t07_exposed_seeds1to5.json` is `9fd335fe72156b229cffbc91318e8772`, while `b0_temp07_results.json` is `f92ae19d9e2cc7871d508fd783b1646c`. Raw outputs were identical for 58 of 60 runs. Turn-1 prompt comparison for DEV-M1-S1, DEV-M2-S1, and DEV-M4-S1 confirmed `hard_constraints` remained `null` because files were not copied to the dev path read by the runner. The run was not valid; a clean re-run is queued. Synchronized caps (DEV-M1-S2 5.76e6 stricter, DEV-M1-S3 3.5e6 stricter, DEV-M3-S2 50.0 looser) were rescored across all earlier B0 runs (T=0.0: 7/60 pass; T=0.7: 12/60 pass; Seeds 6-10: 13/60 pass), producing zero verdict flips. All 12 dev case margins remain valid (1.10x to 2.75x; 39 unit tests pass in 0.99s). Human review of 6 Seed 61 transcripts isolated three distinct failure modes: capacity bound deficit, template incompetence, and gross dimensional hallucination. Blind packet is compiled in `docs/audit/b0_blind_transcript_packet.md`.

### Table 1: Synchronized Caps and Evaluator Margins
| Case ID | Evaluator Old Cap | Problem Card Synchronized Cap | Direction | Reference Design Margin | Test Status |
|---|---|---|---|---|---|
| DEV-M1-S2 | 4.50e6 J/m² | 5.76e6 J/m² | Stricter | 1.10x | PASS |
| DEV-M1-S3 | 2.50e6 J/m² | 3.50e6 J/m² | Stricter | 1.10x | PASS |
| DEV-M3-S2 | 35.0 W/m² | 50.0 W/m² | Looser | 1.10x | PASS |

### Table 2: Human Audit of 6 Baseline Transcripts (Seed 61)
| Case ID | Seed | Template | Outcome | Limits Used / Misread | Physical Realism | Failure Taxonomy |
|---|---|---|---|---|---|---|
| DEV-M3-S1 | 4 | TPL_09 | PASS | Solar 800 W/m², emiss 0.90, absorp 0.05 | High (T_surf=22.56 °C, sub-ambient 4.44 K) | None (Clean Pass) |
| DEV-M3-S2 | 1 | TPL_09 | PASS | Nocturnal sky 15 °C, solar 0 W/m² | High (T_surf=26.60 °C, sub-ambient 0.40 K) | None (Clean Pass) |
| DEV-M3-S2 | 4 | TPL_09 | PASS | Solar 800 W/m², emiss 0.95, absorp 0.05 | High (T_surf=27.67 °C, sub-ambient 7.33 K) | None (Clean Pass) |
| DEV-M2-S3 | 2 | TPL_08 | FAIL | Flow rate 0.001 kg/s yields duty 115.8 W vs 800 W | Unphysical (mass flow deficit by 6.4x) | Capacity Bound Violation |
| DEV-M1-S2 | 3 | TPL_01 | FAIL | Chose sensible storage under L<=0.08m, m<=40kg/m² | Unfeasible (proposed 0.226 m, 452 kg/m²) | Template Incompetence |
| DEV-M4-S3 | 2 | TPL_10 | FAIL | Proposed membrane thickness = 1.0 m | Grotesque (chokes O2 flux by 1000x) | Gross Dimensional Hallucination |

## 2. Quantity Re-linking, Pipeline Differences, and Proposed Stage 6 Rule
Full-document re-linking on the 190 quantities dropped by Rule 1 located 165 (86.8%) in-document and 25 (13.2%) nowhere. A Seed 71 human review of 20 re-linked quantities verified 15 (75.0%, Wilson 95% CI: [0.5313, 0.8881]) true quantity matches and 5 (25.0%, Wilson 95% CI: [0.1119, 0.4687]) false-positive substring collisions (figure labels, citations, decimal digits). Quantities differ in 56 cards between pilot and audit6 sets because Rule 1 was introduced in commit `2f0ff74` and active during audit6; Stage 6 uses `temperature=0.0` but lacks an explicit seed. Subject changes (86 null to named) do not appear in git diff because `flbds_data/` is git-ignored and only Python code changes were tracked. We propose a three-tier Stage 6 rule: retain `provenance='span'` automatically; retain `provenance='document'` only when co-occurring within 50 characters of unit or name tokens; and purge `nowhere` unconditionally.

### Table 3: Re-Linked Quantity Evaluation (Seed 71, N=20)
| Evaluation Category | Count | Proportion | 95% Wilson Confidence Interval | Verified Substring Example |
|---|---|---|---|---|
| Valid Quantity Match | 15 / 20 | 75.0% | [0.5313, 0.8881] | PMC12188424: specific absorption rate 0.42 W/kg |
| Substring Collision / False Match | 5 / 20 | 25.0% | [0.1119, 0.4687] | US-PAT-F-0311: digit 1 matched 'FIG. 1' |

## 3. Human Review Stability Across Rounds
The 7 MAJOR Seed 11 cards were re-evaluated under the Seed 51 rubric. Six cards are reclassified: five become MINOR (underlying transport physics present, but minor evidence truncation or teleological phrasing) and US-PAT-E-0427 becomes GOOD (tank thermal insulation grounded across two exact spans). US-PAT-F-0291 remains MAJOR (action/effect captures electronic closed-loop fan PID control rather than transport physics). Across all rounds, exactly 50 unique cards were audited.

### Table 4: Audit Re-Judgment of 7 Seed 11 MAJOR Cards
| Document ID | Title Excerpt | Action -> Effect | Seed 11 | Audit 8 Verdict | Re-Judgment Justification |
|---|---|---|---|---|---|
| PMC8593863 | Stencil-Printed Wicking Channels | wick liquid -> capillary_wicking | MAJOR | MINOR | Capillary wicking is primary mechanism; 1 span had minor paraphrasing. |
| US-PAT-E-0478 | Tubular Assembly Insulated Joint | insulate joint -> thermal_insulation | MAJOR | MINOR | Vacuum annulus insulation genuine; missing subject repaired in audit6. |
| US-PAT-E-0427 | Fluid Storage Tank Assembly | insulate tank -> thermal_insulation | MAJOR | GOOD | Cryogenic tank insulation authentic across 2 exact spans. |
| US-PAT-F-0220 | Insulating Piping Protection | insulate piping -> thermal_insulation | MAJOR | MINOR | Piping insulation genuine; ungrounded candidate pruned by Rule 1. |
| US-PAT-F-0063 | Forced Air Heat Pump System | regulate temperature -> heat_transfer | MAJOR | MINOR | Heat pump transport valid; action verb phrased teleologically. |
| US-PAT-F-0291 | Variable-Speed Fan Motor | control speed -> pid_control | MAJOR | **MAJOR** | Electronic closed-loop PID fan control is non-transport phenomenon; MAJOR holds. |
| US-PAT-F-0115 | Gas-Liquid Refrigeration Intercooler | subcool liquid -> subcooling_effect | MAJOR | MINOR | Flash tank evaporative subcooling is genuine thermodynamic transport. |

## 4. Conflict Detector Negative Tests and Schema Enhancements
Negative tests in `tests/test_conflict_detector.py` confirmed detector specificity: stripping conflict operators from Split 2 cases yields exactly zero flags, while injecting conflict operators into Split 1 cases fires the matching archetype flag. Added optional `characteristic_length_m` to `SystemSpec` and regime bounds to `MechanismCard`. The complete test suite executes cleanly with 107 passed tests in 6.05 s.

### Table 5: Symbolic Conflict Detector Rules and Fields Read
| Operator | Conflict Type | Source Fields Read | Problem Fields Read | Negative Test Status |
|---|---|---|---|---|
| T1 | Resource Absence | `consumable_inputs` | `environment.resources_absent` | PASS (Strip -> 0 flags, Add -> T1) |
| T2 | Flow Direction Inversion | `target_direction` | `required_function.target_direction` | PASS (Strip -> 0 flags, Add -> T2) |
| T3 | Temporal Phase Shift | `time_mode` | `time_pattern.time_mode` | PASS (Strip -> 0 flags, Add -> T3) |
| T5 | Regime Re-scaling | `regime_max_length_m` | `target_system.characteristic_length_m` | PASS (Strip -> 0 flags, Add -> T5) |

## 5. Git Status, History Purge Plan, and DOI Verification
Branch `fix-subject-pruning` is merged into `main`. The GitHub API confirms the repository is public (`public: true`). `docs/proposals/history_purge_plan.md` specifies exact paths (`docs/audit/blind_screening_packet_user.md`), text replacement patterns, and `git-filter-repo` backup/execution instructions. Crossref DOI audits confirmed Shi et al. 2015 (`10.1126/science.aab3564`) carries an AAAS proprietary reuse license, while Martins et al. 2018 is corrected from typo `10.1038/s41467-018-06282-3` to canonical `10.1038/s41467-018-06257-3` under CC BY 4.0.

## 6. Phase 0 Tool & Dataset Existence Reconciliation
Reconciliation against `docs/flbds_v9.md` confirmed BioSpark is indexed as `arXiv:2312.11388` (Kang et al., CHI 2024). Text2CAD is `arXiv:2411.06206` (Yavartanoo et al., 2024); the reference to `arXiv:2409.17106` was an earlier typographic error. Pointer-CAD v2 appears as ECCV 2026 in the audit literature search (`10.1007/978-3-032-37135-5_16`), but `flbds_v9.md` itself does not specify ECCV 2026, mandating only existence verification in Phase 0.

### Table 6: Tool and Literature Verification Summary
| Tool Name | Matched Publication Title | Authors | Year | Canonical Identifier | v9 Status |
|---|---|---|---|---|---|
| BioSpark | BioSpark: Generative System for Bio-Analogical Ideation | H. B. Kang et al. | 2023/24 | `arXiv:2312.11388` / `10.1145/3613905.3651035` | MATCH |
| AutoTRIZ | AutoTRIZ: Automating Engineering Innovation | S. Jiang et al. | 2025 | `10.1016/j.aei.2025.103312` | MATCH |
| Text2CAD | Text2CAD: 3D CAD Generation via Technical Drawings | M. Yavartanoo et al. | 2024 | `arXiv:2411.06206` (`10.48550/arxiv.2411.06206`) | MISMATCH (v9 typo 2409.17106) |
| Pointer-CAD v2 | Plan-Then-Construct CAD Generation | D. Qi et al. | 2026 | `10.1007/978-3-032-37135-5_16` | MATCH (v9 omits venue) |
| CAD-Coder | Open-Source VLM for CAD Code Generation | A. C. Doris et al. | 2026 | `10.1115/1.4071305` | MATCH (GenCAD lineage) |
| Bioinspired123D | Generative 3D Modeling for Bioinspired Structures | R. K. Luu, M. J. Buehler | 2026 | `10.48550/arxiv.2603.29592` | MATCH (Bioinspired3D) |
| TreeOfLife-10M | TreeOfLife-10M Dataset | S. Stevens et al. | 2026 | `10.57967/hf/7542` | MATCH |
| BioCLIP | BioCLIP: Vision Foundation Model for Tree of Life | S. Stevens et al. | 2024 | `10.1109/cvpr52733.2024.01836` | MATCH |
