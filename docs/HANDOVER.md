# FLBDS Handover Guide for Incoming Agents

> [!IMPORTANT]
> **Comprehensive Master Project Handover**: For the exhaustive, full-depth project handover detailing all accomplishments across Rounds 1–11, technical architecture, verified vs. withdrawn ledgers, dual-tier physics solvers, M4 analogy engine, and the detailed roadmap for what is yet to do across Weeks 4–26 (Phases 1 through 6), see [`docs/PROJECT_HANDOVER.md`](PROJECT_HANDOVER.md).

**Repository**: `FLBDS` | **Current Commit**: `ac446c4 (Sun Nov 1 12:07:24 2026 +0530)`  
**Target Audience**: An autonomous AI agent with zero access to prior conversation transcripts.  
**System Authority**: [`docs/flbds_v9.md`](flbds_v9.md) (Solo BTech scope, 26-week plan, fixed physics and schemas).

---

## 1. Project in 10 Lines

1. **Goal**: Build a visual biology-to-engineering thesaurus and a two-image concept generator with verified physics verifiers.
2. **Authority**: [`docs/flbds_v9.md`](flbds_v9.md) governs all definitions, milestone scopes, benchmark splits, and schemas.
3. **Hardware & Compute**: 1 x NVIDIA H200 (141 GB HBM3e) on server `192.168.2.69`; strict 90.0 GPU-hours/week quota.
4. **Server-Only Data**: Large datasets, model weights, and heavy outputs stay on the server (`/home/abhishek24024/flbds_data`); git stores code, configs, tests, and documentation.
5. **No Fabrication**: Never invent citations, DOIs, abstracts, metrics, or gold labels. If a paper cannot be fetched via API, write UNVERIFIED.
6. **Silver is Never Gold**: Model-extracted silver cards are candidate hypotheses. Gold requires human verification against the source paper.
7. **Empirical Verification**: Nothing is done until executed with real output logged. Report exact exit codes and execution times.
8. **No Polling Loops**: Launch GPU jobs with `gpurun` / `nohup` and inspect results asynchronously; never execute tight sleep-poll loops.
9. **Quote Grounding**: Any quoted text or abstract must pass [`scripts/verify_quotes.py`](../scripts/verify_quotes.py) as an exact substring of a saved artifact.
10. **Human Review Protocol**: Work producing cards or data must include seeded random audits (read source first, 10-point rubric, blind evaluation packet).

---

## 2. Environment & Execution

- **Server Access**: Connect via SSH using credentials configured in `~/.ssh/bio_server` to `abhishek24024@192.168.2.69`. Refer to connection details in `ssh_details.md` by path only (never print or expose host keys or tokens).
- **Paths**:
  - Remote Repository: `/home/abhishek24024/flbds`
  - Heavy Storage: `/home/abhishek24024/flbds_data/`
  - Models (`Qwen2.5-72B-FP8`, `32B-FP8`, `7B-BF16`): `/home/abhishek24024/flbds_data/models/`
  - Corpus (`bio_pilot.jsonl`, `eng_pilot.jsonl`): `/home/abhishek24024/flbds_data/corpus/`
  - Review Packets: `/home/abhishek24024/flbds_data/review/`
- **Virtual Environment**: `/home/abhishek24024/flbds_env/bin/python3` (Python 3.12, PyTorch, vLLM, Pint, SymPy, Pydantic).
- **Running Tests**: `PYTHONPATH=. /home/abhishek24024/flbds_env/bin/pytest tests/`
- **GPU Broker (`gpurun`)**:
  - Submit jobs: `gpurun <command>` or `gpurun bash -c '...'`
  - Status & quota: `gpurun --status`
  - Broker ledger status: 90.0 weekly quota, 88.6 GPU-hours remaining (0.79 GPU-hours consumed across Round 11 jobs 7891, 7892, 7893, 7894).
- **Gitignore Rules**: Heavy safetensors, raw corpus JSONL, pilot checkpoint directories, and `flbds_data` symlinks are gitignored.

---

## 3. What Exists: Modules, Scripts, and Datasets

### Test Suite Status
Current execution of pytest on server:
```text
============================= 134 passed in 6.01s =============================
```

### Repository and Server Assets

| Path | Location | Purpose | Test Status |
| :--- | :--- | :--- | :--- |
| `flbds/schema/` | Git / Server | Pydantic data contracts (Cards, SAPPhIRE, Templates, Problem Cards) | 21 passed (`test_schemas.py`) |
| `flbds/physics/` | Git / Server | 10 analytical & ODE physics verifiers (`tpl01` to `tpl10`, capacity bounds) | 37 passed (`test_physics.py`) |
| `flbds/physics/screen.py` | Git / Server | Lumped algebraic M5-Screen verifier evaluating hard constraints | 5 messages verified |
| `flbds/m4/` | Git / Server | SAPPhIRE graph schema, rule-based conflict detector, T1-T5 operators, fixtures | 27 passed (`test_m4_engine.py`) |
| `flbds/benchmark/dev/`| Git / Server | 12 dev-case specifications (`DEV-M1` to `DEV-M4` across Splits 1-3) | 39 passed (`test_benchmark_dev.py`) |
| `tests/test_eval_f1.py`| Git / Server | Token-overlap F1 evaluator for schema and extraction agreement | 7 passed (`test_eval_f1.py`) |
| `scripts/run_round11_benchmarks.py`| Git / Server | Unified runner executing B0, Screen, Oracle, and B3 on frozen dev cases | Validated (N=60 per condition) |
| `scripts/verify_quotes.py` | Git / Server | Exact substring verifier asserting quotes against saved corpus/API files | Operational CLI tool |
| `scripts/relink_quantities_stage6.py` | Git / Server | Full-text quantity re-linking engine recovering un-grounded numbers | Operational CLI tool |
| `/home/.../flbds_data/corpus/` | Server | 1,000-doc pilot corpus (500 PMC CC BY papers, 500 USPTO patents) | Read-only input source |
| `/home/.../flbds_data/pilot/` | Server | Pilot pipeline outputs (`stage_1` to `stage_6`, `silver_cards.jsonl`) | 137 silver cards generated |
| `/home/.../flbds_data/review/`| Server | Audits, blind human packet (`human_packet.md`), verified 17 below-GOOD cards | Artifacts grounded |
| `/home/.../flbds_data/api_responses/` | Server | Saved raw JSON responses from Crossref, OpenAlex, and Europe PMC | Ground truth for citations |

---

## 4. Verified Ledger

Every entry below has been proven and verified against a concrete artifact:

| Claim | Artifact Path | Command to Re-Check |
| :--- | :--- | :--- |
| 104 tests pass with 1% relative numerical tolerance | `tests/test_physics.py`, `tests/test_benchmark_dev.py` | `PYTHONPATH=. pytest` |
| Infeasible dev cases fail satisfiability gates | `tests/test_benchmark_dev.py::TestDeliberatelyInfeasibleCases` | `PYTHONPATH=. pytest tests/test_benchmark_dev.py` |
| Circular Poiseuille Darcy friction law is dP = 32*mu*L*u / D^2 (Po = 64) | `flbds/physics/tpl08_countercurrent.py` | `PYTHONPATH=. pytest -k poiseuille` |
| Martins 2018 (DOI: `10.1038/s41467-018-06257-3`) title is *Locally-curved geometry generates bending cracks in the African elephant skin* | `api_responses/martins_2018_crossref.json` | `python3 scripts/verify_quotes.py --doc_id martins_2018_crossref --quote "Locally-curved geometry"` |
| B0 parse failure rate is 0.0% with guided decoding | `benchmark/b0_redo_results.json` | `jq .categories.parse_failure benchmark/b0_redo_results.json` |
| B0 unassisted physics pass rate is 23.3% (14/60, valid exposed limits run; 33.3% under card environment rescore) | `audit8/b0_t07_exposed_seeds1to5.json`, `audit9/b0_rescore_environment_flips.json` | `jq .total_passes flbds_data/audit8/b0_t07_exposed_seeds1to5.json` |
| 17 below-GOOD Seed 11 cards verified from corpus | `review/verified_17_below_good.json` | `PYTHONPATH=scripts python3 scripts/audit_17_below_good.py` |
| 239 quantities re-linked in document text (53.6%), only 20 nowhere (4.5%) | `pilot/stage_6_relinked_summary.json` | `cat pilot/stage_6_relinked_summary.json` |
| DEV-M4 diffusion flux margin is un-binding (27.5x - 50.0x) | `benchmark/dev_case_margins.json` | `cat benchmark/dev_case_margins.json` |
| DEV-M1-S3 latent capacity margin is tight (1.045x) | `benchmark/dev_case_margins.json` | `cat benchmark/dev_case_margins.json` |
| R3 vs R10 offset shift explained: `full_text` prefix length shift (`PMC8593863`: 133, `US-PAT-E-0478`: 798, `US-PAT-E-0427`: 813, `US-PAT-F-0220`: 566) | `scripts/audit11_check_offsets.py` | `python3 scripts/audit11_check_offsets.py` |
| Authoritative Oracle result is 33/60 (55.0% [42.5%, 66.9%]); R9 45/60 used un-budgeted 6-turn loop | `scripts/run_round11_benchmarks.py`, `flbds_data/audit11/oracle_feedback_results.json` | `cat flbds_data/audit11/oracle_feedback_results.json` |
| True lumped M5-Screen yields PVR_screen=36/60 (60.0%), PVR_eval=34/60 (56.7%), gap 3.3% | `flbds/physics/screen.py`, `flbds_data/audit11/screen_only_results.json` | `cat flbds_data/audit11/screen_only_results.json` |
| B3 Pipeline (M4 Operators + lumped Screen) achieves 30/60 passes (50.0% [37.7%, 62.3%]) with 100% template preservation | `flbds_data/audit11/b3_dev_results.json` | `cat flbds_data/audit11/b3_dev_results.json` |
| M4 engine unit tests pass (27/27) and full suite passes (134/134) in 6.01s | `tests/test_m4_engine.py` | `pytest tests/test_m4_engine.py` |

---

## 5. Withdrawn & UNVERIFIED Ledger

The following historical claims or entries are withdrawn or marked UNVERIFIED:

| Item | Reason for Withdrawal / UNVERIFIED Status |
| :--- | :--- |
| **Round 10 Offset Discrepancy Claim** | **Withdrawn**. R3 and R10 offsets slice the exact same quote; position difference was solely due to slicing `full_text` (`title + '\n' + abstract + '\n' + text`) in `verify_quotes.py` vs `doc['text']` in R10. |
| **Round 9 45/60 Oracle Headline** | **Withdrawn**. R9 used a 6-turn loop (3 COT turns + 3 feedback turns) violating the authoritative 3-turn budget in v9 §7.1. Authoritative Oracle is 33/60 (55.0%). |
| **Unguided T=0.0 7/60 Headline** | **Withdrawn**. Unguided model hallucinated its own favorable environments ($q_{\text{solar}} = 20\text{ W/m}^2$, $\Delta P = 5000\text{ Pa}$) when defaults were not overridden. Under card-bound scorer, guided T=0.0 achieved 18/60. |
| **Round 2 Item 7 Card Excerpts & Verdicts** | **Withdrawn**. 11 IDs (`PMC9234854`, `PMC9502598`, etc.) were synthetic; excerpts for 6 real IDs (`PMC8531342`, `US-PAT-F-0321`, etc.) were fabricated. Re-audited cleanly in `verified_17_below_good.json`. |
| **"190 Hallucinated Quantities" Claim** | **Withdrawn**. The original sanitizer checked only the 200-char cited evidence spans. Full-text document search proved 239 of these exist directly in the paper text; only 20 are truly absent. |
| **Wang et al. (2022, ACS AMI)** | **UNVERIFIED**. Query `Wang elephant skin hydrogel ACS Applied Materials 2022` returned zero matches in Crossref and ACS. Transfer paper for DEV-M1 is missing. |
| **Song & Bhushan (2010, Phil Trans A)** | **UNVERIFIED**. Query `Song Bhushan counter-current heat exchange rete mirabile 2010` returned zero matches. Real 2010 paper covers shark-skin drag reduction, not rete mirabile. |
| **Zhai et al. (2021, Sol Energy Mater)** | **UNVERIFIED**. Query `Zhai ant-inspired daytime passive radiative cooling Solar Energy Materials 2021` returned zero matches. Transfer paper for DEV-M3 is missing. |
| **Scholander & Schevill (1955) Abstract** | **UNVERIFIED (Abstract Not Available)**. DOI `10.1152/jappl.1955.8.3.279` confirmed, but Crossref, OpenAlex, and Europe PMC return null abstract fields. |
| **PMC9234854 Duality** | **Withdrawn**. Document does not exist in corpus; appeared as both dropped and accepted due to drafting hallucination. |
| **Round 7 B0 "Exposed Limits" Re-Run** | **Withdrawn (Invalid Execution)**. Round 7 run was identical to earlier run (broker jobs 7769 and 7772 did not execute new prompts; md5 identical). Valid re-run executed in Round 8/9 (`audit8/b0_t07_exposed_seeds1to5.json`). |
| **Round 8 Card Reversals** | **Withdrawn**. Round 8 reversals for `PMC8593863`, `US-PAT-E-0478`, `US-PAT-E-0427`, and `US-PAT-F-0220` were agent opinion. Historical Round 3 MAJOR verdicts stand based on grounded flaws in pilot silver cards. |
| **22/27/1 Pooled Card Quality Table** | **Withdrawn**. Merged heterogeneous sample distributions without re-deriving card verdicts from corpus text. |

---

## 6. Measured Numbers with Artifacts

### A. Pilot Corpus Pipeline Yield (N = 1,000 input documents)
- **Stage 1 (7B Filter)**: 1,000 raw -> 391 passed (39.1%). Artifact: `pilot/stage_1_summary.json`.
- **Stage 2 (7B Extractor)**: 391 docs -> 357 candidate cards (91.3%). Artifact: `pilot/stage_2_summary.json`.
- **Stage 3 (Agreement)**: 67.7% exact match; token-overlap F1 = 0.814 (N=357). Artifact: `pilot/stage_3_summary.json`.
- **Stage 4 (Harmonizer)**: 357 cards -> 270 valid schema cards (75.6%). Artifact: `pilot/stage_4_summary.json`.
- **Stage 5 (32B Critic)**: 270 cards -> 137 clean retained cards (50.7%). Artifact: `pilot/stage_5_summary_clean.json`.
- **Stage 6 (Quantities)**: 137 cards -> 133 silver cards with validated quantities (97.1%). Artifact: `pilot/stage_6_summary_clean.json`.
- **Cumulative Yield**: 133 silver cards from 1,000 inputs (**13.3%**).

### B. Baseline B0 Performance (12 Dev Cases x 5 Seeds = 60 Runs)

| Metric | B0 Valid Exposed (T=0.7, N=60) | A-NoOp Feedback (T=0.7, N=60) | Artifact Path |
| :--- | :---: | :---: | :--- |
| **Parse Failures** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `audit8/b0_t07_exposed_seeds1to5.json` |
| **Schema Failures** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `audit8/b0_t07_exposed_seeds1to5.json` |
| **Template Errors** | **0 / 60 (0.0%)** [0.0%, 6.0%] | **0 / 60 (0.0%)** [0.0%, 6.0%] | `audit8/b0_t07_exposed_seeds1to5.json` |
| **Physics Failures**| **46 / 60 (76.7%)** [64.6%, 85.6%] | **15 / 60 (25.0%)** [15.8%, 37.2%] | `audit9/a_noop_results.json` |
| **Satisfiable Passes**| **14 / 60 (23.3%)** [14.4%, 35.4%] | **45 / 60 (75.0%)** [62.8%, 84.2%] | `audit9/a_noop_results.json` |
| Split 1 Pass Rate | 2 / 20 (10.0%) [2.8%, 30.1%] | 14 / 20 (70.0%) [48.1%, 85.5%] | `audit9/a_noop_results.json` |
| Split 2 Pass Rate | 7 / 20 (35.0%) [18.1%, 56.7%] | 16 / 20 (80.0%) [58.4%, 91.9%] | `audit9/a_noop_results.json` |
| Split 3 Pass Rate | 5 / 20 (25.0%) [11.2%, 46.9%] | 15 / 20 (75.0%) [53.1%, 88.8%] | `audit9/a_noop_results.json` |

*(Note: Under ground-truth card environment rescoring with fixed 10 K superheat caps, B0 baseline passes reach 20 / 60 (33.3%) [22.7%, 45.9%]; artifact: `audit9/b0_rescore_environment_flips.json`)*

### C. Audits & Grounding Measurements
- **Seed 11 Holistic Card Quality (N=24)**: 7 GOOD (29.2%), 10 MINOR (41.7%), 7 MAJOR (29.2%). Artifact: `review/agent_verdicts_seed11.json`.
- **Seed 13 Critic Effect Audit (N=40)**: 7 / 20 false negative drops (35.0%), 0 / 20 false positive accepts (0.0%). Artifact: `review/stage5_effect_audit_seed13.json`.
- **Quantity Full-Text Re-Linking (N=446)**: 187 in cited span (41.9%), 239 re-linked in document (53.6%), 20 absent (4.5%). Artifact: `pilot/stage_6_relinked_summary.json`.

### D. Split 2 Physical Conflicts and Operators
- **DEV-M1-S2 (Desert Storage Wall)**: Resource Absence (liquid water absent) -> **T1 (Resource Substitution)** to solid PCM.
- **DEV-M2-S2 (Industrial Exhaust Exchanger)**: Sign Inversion (extracting heat from hot exhaust) -> **T2 (Sign / Direction Inversion)**.
- **DEV-M3-S2 (Diurnal Canopy Shield)**: Timing Conflict (daytime solar heat vs night sky sink) -> **T3 (Timing / Phase Delay)**.
- **DEV-M4-S2 (Submerged Scavenger)**: Regime Conflict (hydrostatic wetting transition) -> **T4 (Regime Switch / Pore Geometry Tuning)**.

---

## 7. Open Work (Priority Order)

1. **Audit Round 4 Deliverables**:
   - Resolve missing Split 1 transfer citations for DEV-M1, DEV-M2, and DEV-M3.
   - Address DEV-M4 un-binding flux margin (50x) by introducing Laplace capillary breakthrough pressure as the active binding constraint.
   - Adjust DEV-M1-S3 thickness envelope or latent density to increase headroom margin above 1.05x.
2. **Gold Card Authoring**: Solely the human researcher's responsibility. The user must review candidate silver cards and author true gold benchmark cards.
3. **Rater Recruitment & Study Protocol**: Design blind human study forms for rating expert engineering validity.
4. **USPTO Bulk Access Decision**: Decide whether to acquire USPTO bulk API key or continue streaming CC BY open patent archives.
5. **Architectural Decisions Reserved for User**:
   - Benchmark organism selection beyond the initial 12 candidates.
   - Setting final acceptance thresholds for Stage 5 Critic.
   - Authorization to scale up beyond the 1,000-document pilot corpus.

---

## 8. Known Pipeline Weaknesses

- **Bio Silver Cards Skew Toward Engineered Materials**: Because PMC thermal queries frequently return biomimetic polymers and composite materials, genuine organism physiology represents < 30% of the biological corpus.
- **Stage 1 Filter Keyword Bias**: The filter prompt relies heavily on mechanical engineering jargon, causing systematic drops of organism papers describing respiration, cuticular transpiration, or mound ventilation.
- **Critic Over-Rejection of Descriptive Language**: Stage 5 Critic penalizes papers that describe physical phenomena in natural prose rather than matching canonical enum slugs verbatim.
- **Evidence Span Narrowness**: Quantities are frequently extracted from Results sections while the cited evidence spans are drawn from Abstracts, causing false-positive un-grounded flags unless full-text re-linking is run.
- **Sparse Open-Access Coverage for Specific Species**: Specialized organisms (e.g. *Stenocara gracilipes*, *Sphincterochila boissieri*) have very few full-text CC BY papers indexed in Europe PMC.

---

## 9. First Tasks for the Incoming Agent

Before modifying code or running new pipelines, perform these verification steps:

1. **Re-Run Pytest**:
   ```bash
   ssh -i ~/.ssh/bio_server abhishek24024@192.168.2.69 "cd /home/abhishek24024/flbds && PYTHONPATH=. /home/abhishek24024/flbds_env/bin/pytest tests/"
   ```
   *Expected output*: Exactly 134 passed in ~6 seconds.
2. **Re-Run Quote Verifier on Verified Ledger**:
   ```bash
   ssh -i ~/.ssh/bio_server abhishek24024@192.168.2.69 "cd /home/abhishek24024/flbds && PYTHONPATH=scripts python3 scripts/audit_17_below_good.py"
   ```
   *Expected output*: 17 out of 17 below-GOOD cards verified against corpus.
3. **Spot-Check 5 Rows in the Verified Ledger**:
   Verify `b0_redo_results.json`, `b0_temp07_results.json`, `dev_case_margins.json`, `stage_6_relinked_summary.json`, and `martins_2018_crossref.json` against the artifact commands in Section 4.
4. **Report Discrepancies**: If any test fails, quote fails verification, or file is missing, halt and report the discrepancy to the user before proceeding.
