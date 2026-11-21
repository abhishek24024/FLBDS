# 00 — FLBDS Project Digest (state as of 2026-11-19)

Purpose: factual input for literature researchers and an architect who will propose a simpler, more-likely-to-work architecture.
Convention: **[P]** = the research proposal PDF says; **[S]** = spec / handover docs say; **[C]** = code shows; **[R]** = result files / server show; **[D]** = my own derivation or check (method stated). Every claim cites a path (line numbers `:L` where useful) or PDF page.

Abbreviations of source paths used below:
- PDF = `~/Downloads/Physics-Verified Bio-Inspired Concept Generation from Biological Images (9) (1).pdf` (19 pages)
- v9 = `docs/flbds_v9.md`; v5 = `flbds_v5.md`; PH = `docs/PROJECT_HANDOVER.md`; HO = `docs/HANDOVER.md`
- R5..R11 = `docs/audit/audit_round_N_report.md`
- runner11 = `scripts/run_round11_benchmarks.py`
- server data root = `/home/abhishek24024/flbds_data/` (abbrev. `DATA/`)

> Naming note for the caller: "Anoop" in the repo is **A-NoOp** (the "screen/evaluator feedback loop with no operators" ablation), not a human reviewer. Files `docs/audit/anoop_*.md` are agent-written transcript reviews of the A-NoOp/Oracle condition. There is no external human reviewer feedback anywhere in the repo; all blind packets are listed as "awaiting user review" (R11:85-92).

---

## 1. Research goal and claims

### 1.1 Proposal (PDF, latest version, 19 pp.)
- Two goals inherited from v9: (G1) a visual biology→engineering **thesaurus** of SAPPhIRE "Mechanism Cards" linked only through shared function/effect nodes; (G2) a **concept generator** producing 3–5 physics-verified concepts ("Concept Package") [P p.1–2; v9:15-52].
- Two modes [P p.2–3]: **Mode A** = bio image (+caption) + problem (text and/or engineering image) → verified concepts. **Mode B** = bio image only → system *selects* a problem from a pool of code-checkable physics problems, then runs Mode A. "Mode B is designed but not yet implemented" [P p.1].
- Four motivating gaps [P p.1]: knowledge gap, matching gap (look-alike ≠ work-alike), verification gap (no prior LLM BID system checks physics), and an **attribution gap found in the pilot**: plain prompted 72B passed 17/60 (28.3%); feeding evaluator failure messages back raised it to 33/60 (55.0%) "with no biology and no operators", and in 0/8 reviewed transcripts did the model change mechanism. Proposal concludes: "the open question is ... whether operators and the biological source add value beyond a feedback loop" [P p.1].
- Research questions [P p.2]: RQ1 operators + in-loop physics check beat plain prompting, retrieval, self-written checks, and an operator-free feedback loop? RQ2 does the biological source help vs mismatched/missing? RQ3 does function-based search beat text search cross-domain? RQ4 can Mode B pick a suitable problem and solve it?
- Scope: thermal, fluid, porous-media (TFP) only; results "do not carry over to structural colour, adhesion or aerodynamic shape" [P p.8, p.14–15].

### 1.2 Hypotheses and evaluation protocol
**Proposal version (PDF p.18)** — five Holm-corrected:
- H1: B3 > B1 (retrieval + self-critique) on PVR_eval.
- H2: B3 > B2-Code (model-written verification code) on PVR_eval.
- H3: on Split 2, B3 > A-NoOp on PVR_eval ("tests the operators").
- H4: on Split 3, B3-Screen+ > B3 (separates verifier coverage from analogy-transfer failure).
- H5: blind experts rate B3 > **B3-WrongBio** on analogical validity ("tests whether the biology helps").
- Separate: B3-NoBio vs B3 non-inferiority (margin 0.10); H6 Mode B vs random / embedding-only / LLM-only selection (exploratory); retrieval and image studies with bootstrap CIs.
- Note: v9 (v9:94-103) differs: H3 is "H3a", H5 is B3 vs **B1** (not WrongBio), and H3b is B3-NoBio non-inferiority. The PDF adds B3-WrongBio and "one stronger, newer open model" baseline [P p.18].

**Conditions** (all 3 turns, same schema, 5 seeds, T=0.7, guided JSON; limits/environment from the Problem Card) [P p.18; v9:318-336]: B0 plain prompt; B1 retrieval + self-critique; B2-Code; A-NoOp; B3 full; B3-NoBio; B3-WrongBio; B3-Screen+; A-NoVerifier; A-RawText; A-Img; optional B4 (DPO proposer). Planned test run = 10 conditions × 36 cases × 5 seeds = 1,800 runs [v9:322].

**Metrics** [P p.16–17; v9:340-349]: Q1 PVR_eval (binary: acceptable template AND typed params pass M5-Eval; PVR_screen likewise); Q2 design quality (min normalised margin, objective vs solver-optimised conventional design, Pareto); Q3 biology attribution (B3 vs WrongBio vs NoBio + blind expert analogical validity 1–5); Q4 rediscovery level L0–L4 (Split 1); Q5 novelty class; Q6 verifier trust (false-assurance/false-rejection from a two-rater blind audit, subset re-checked by 2D FE); Q7 sketch shape-copy rate vs IP-Adapter baseline; Q8 Mode B problem appropriateness.

**Statistics** [P p.18; v9:351-357]: average 5 seeds within case; 12 mechanism clusters are the units; paired exact permutation (4,096 sign flips) + Pratt Wilcoxon; binomial mixed model with cluster bootstrap (10,000); Holm across H1–H5. PDF p.13 notes Holm at 0.01 needs ≥8 informative clusters.

**Human evaluation** [v9:359-367]: two independent raters ≈26 h each (Packet A verifier audit 30 concepts; B analogical validity 24 blinded pairs; C leakage/novelty). If no raters: H5 dropped. **[S] No raters are recorded as recruited anywhere in the repo** (PH:171-173 lists it as open; HO:167).

### 1.3 Testability today (my assessment against code/data/compute)
| Hypothesis | Needs | Exists now? | Testable now? |
|---|---|---|---|
| H1 (B3 vs B1) | M3 retrieval index + B1 runner | No retrieval/M3 code [C: `flbds/` has no retrieval module] | No |
| H2 (B3 vs B2-Code) | sandboxed self-written-code runner | Not implemented [C] | No (moderate effort) |
| H3 (B3 vs A-NoOp, Split 2) | B3 + A-NoOp runners on same cards | Both runnable on 12 dev cases (runner11; A-NoOp ≈ "Screen-only" condition) | Yes on dev, but only 4 dev clusters; only 1/4 Split-2 cases actually triggers an operator (§5.3) |
| H4 (B3-Screen+ vs B3, Split 3) | Oracle condition | "Oracle" condition exists (runner11 `run_benchmark_oracle`) | Yes on dev |
| H5 (expert ratings B3 vs WrongBio/B1) | raters | No raters | No |
| H3b / B3-NoBio, B3-WrongBio | variant prompts | Trivial prompt edits | Yes on dev (not yet run) |
| G1 retrieval / image study, RQ3 | gold pairs, embedding, images | 0 gold cards, 0 image pairs [PH:243-249] | No |
| RQ4 Mode B | problem pool + selector | Not implemented [P p.1] | No |
| Test-set (36 cases) | test cases | **0 of 36 authored** [PH:223-237] | No |

---

## 2. Architecture end to end

### 2.1 Planned pipeline (v9 §4.1, v9:124-153; PDF p.3 figure)
Generation path (solid boxes) and hidden scoring (dashed):
1. **M1 Bio grounding** (photo → Mechanism Cards): frozen BioCLIP top-k taxa → VLM tags structure/behaviour/scale/environment (abstains) → query planner (3 query levels) → hybrid retrieval (BM25 + functional embedding + citation expansion) + cross-encoder rerank → LLM extractor writes one card per function with verbatim spans and units → verbatim-span check + entailment critic [P p.4; v9:196-203]. LLM/VLM-driven.
2. **M2 Target understanding** (problem text / eng photo → Problem Card): VLM or text parser fills system, scale, environment, resources available/absent (enums), required function, time pattern, hard limits; **must not name a template**; at most one clarifying question; TRIZ-style contradictions [P p.4; v9:205-212]. LLM/VLM-driven.
3. **(Mode B only) problem pool + selector**: hard filters (maps to a template; passes capacity bound; not a sealed test problem) then S(m,p)=a·Match+b·Resolvable+c·Feasible+d·Far, top-k diversified by graph community [P p.6–7]. Mixed (embedding cosine + deterministic filters).
4. **M3 Knowledge graph / thesaurus**: Neo4j or NetworkX + vector index + provenance DB; node types Card, Document, Subject, Effect, Action, StateVariable, Part, Evidence, Community; bio and eng cards connect only via shared canonical Effect/Action/StateVariable nodes; three vectors per card (purpose/mechanism/effect); Leiden communities; trained three-head bge-large encoder with gradient-reversal adversary vs shape/taxon cues; cross-encoder reranker [P p.4–5, p.11; v9:161, 214]. Mostly deterministic + trained embeddings.
5. **M4 Analogy & transformation engine**: role binder (LLM; each source role preserved/transformed/substituted/dropped with cited node ids), rule-based **conflict detector** (resource, direction, timing, regime, medium), **typed graph-rewrite operators T1–T5** (T1 close resource loop, T2 invert flow, T3 add charge/discharge phases, T4 swap effect, T5 regime re-scale post-trial; T6 material substitution, T7 hybridisation optional); "The LLM chooses which operator to try and its parameters; the code checks the precondition and applies the rewrite"; then 3–5 variants ranked [P p.5; v9:180-192, 216].
6. **LLM proposes typed parameters** (guided JSON) ↔ **M5-Screen** (lumped closed-form checks + all hard constraints), fail → feedback, max 3 turns [P p.3, p.6; v9:224-243].
7. **M6 Novelty gate**: nearest prior art at L2/L3 + judge LLM, 4 novelty classes [P p.6; v9:218].
8. **M7 Outputs**: explanation, SVG schematic (code model + VLM critic), CadQuery/STEP (checked watertight), hand-drawn-style concept sketch from the verified parameter vector only; IP-Adapter on bio photo kept only as baseline [P p.6, p.13; v9:220].
9. **M8 Designer UI + logging** [v9:222].
10. **Locked scoring** (never visible to generator): **M5-Eval** coupled solvers + blind expert audit [P p.3; v9:150-153].

LLM-driven vs deterministic summary: M1 (VLM + LLM extractor + LLM critic), M2 (VLM/LLM), M4 role binder & operator choice (LLM), parameter proposal (LLM), M6 judge (LLM), M7 coders/VLM critic/image model are model-driven. Conflict detector, operator rewrites, M5-Screen, M5-Eval, capacity bound, satisfiability gate, graph linking are deterministic Python.

### 2.2 Models / tools (planned vs present)
- Planned [v9:371-385]: 70B teacher (Qwen2.5-72B-Instruct FP8 proposed), 30B critic/judge (Qwen2.5-32B FP8), 7–8B filter/extractor, 70B teacher VLM (chosen at Phase 4), BioCLIP + SigLIP frozen, bge-large three-head encoder, 0.6–1B cross-encoder, 7–8B LoRA VLMs for tagging/Problem Cards, optional 14B DPO proposer, prompted coder models, off-the-shelf image editor. Trained components only if they pass go/no-go gates [v9:389-399].
- Present on server [R: `ls DATA/models`]: `Qwen2.5-72B-Instruct-FP8` (71 GB, RedHatAI FP8-dynamic), `Qwen2.5-32B-Instruct-FP8` (32 GB), `Qwen2.5-7B-Instruct` (15 GB) [`configs/models.yaml`]. **No VLM, no BioCLIP, no embedding model, no image model downloaded.** All benchmark runs used Qwen2.5-72B-FP8 via offline vLLM `LLM(...)`, tensor_parallel=1, max_model_len 4096 [C: runner11:300, 331-337].
- Physics stack: Pint, SymPy, SciPy, NumPy [C: `pyproject.toml`].

### 2.3 Physics verifier M5 (the most developed part)
- 10 templates TPL-01..10 each with `screen_*` (lumped) and `eval_*` (coupled) functions [C: `flbds/physics/tpl01_conduction.py`..`tpl10_diffusion.py`]. Examples: TPL-02 1D enthalpy Stefan solver + 24 h Robin cycle with night discharge (`tpl02_pcm.py:137, 212-310, 314`); TPL-08 ε-NTU + axial conduction + Poiseuille per duct shape; TPL-09 quartic radiative equilibrium; TPL-10 Bosanquet/Knudsen + boundary layer + Young-Laplace breakthrough.
- Capacity-bound / satisfiability gate (`flbds/physics/capacity_bound.py`, 185 lines).
- M5-Screen tier written in Round 11 (`flbds/physics/screen.py`, 217 lines) [R11:22-34].
- Verified numbers [S]: enthalpy solver vs Neumann within 0.018–0.02% (R9:35-40; PDF p.11 marks it agent-reported); paraffin 50 mm superheat 26.5–26.92 K numerical vs 35.3 K closed form; composite 40 mm 2.62–2.64 K [v9:466-469; R9:37].
- v9 says each template is to be tested on ≥3 textbook problems within 1% [v9:249-251]; test suite has 37 physics test functions (`tests/test_physics.py`, 834 lines) — I did not verify textbook coverage per template.

---

## 3. Built in code vs only planned

### 3.1 Code inventory (line counts, `wc -l`, local working tree)
| Area | Files (lines) | Status |
|---|---|---|
| `flbds/schema/` | enums 81, evidence 44, ground_truth_eval 35, mechanism_card 187, problem_card 270, quantity 39, role_binding 72, sapphire 112, templates 307, verification 143, `__init__` 100 → **1,390** | Built. Pydantic v2 contracts. |
| `flbds/physics/` | capacity_bound 185, screen 217, tpl01 146, tpl02 419, tpl03 243, tpl04 98, tpl05 139, tpl06 127, tpl07 142, tpl08 200, tpl09 175, tpl10 219, `__init__` 132 → **2,442** | Built (M5-Screen + M5-Eval). |
| `flbds/m4/` | conflict_detector 71, fixtures 161, operators 413, sapphire_graph 119, `__init__` 28 → **792** | Built as skeleton (see §5.3 for what it really does). |
| `flbds/pipeline/` (silver-card factory) | chunker 75, stage1_filter 171 (7B), stage2_teacher 192 (72B), stage3_agreement 191 (72B dual run), stage4_evidence 155 (CPU verbatim), stage5_critic 261 (32B), stage6_quantities 467 (7B + Pint), stage7_dedup 130 → **1,643** | Built; run once on 1,000-doc pilot. |
| `flbds/benchmark/dev/` | 12 cases × {problem_card, ground_truth_eval, reference_design}.json + manifest | Built, SHA-256 frozen [`docs/audit/freeze_hashes.txt`]. |
| `tests/` | test_physics 834, test_schemas 585, test_m4_engine 271, test_conflict_detector 223, test_benchmark_dev 205, test_eval_f1 81 → **2,199** (95 `def test_` functions; HO:51 reports 134 passing incl. parametrisations) | I could not re-run locally (deps missing: ImportError at collection); not re-run on server to stay read-only. |
| `scripts/` | 94 .py files, **14,684** lines; benchmark runners `run_round11_benchmarks.py` 872, `run_round10_benchmarks.py` 813, `run_a_noop_benchmark.py` 524 | Many one-off audit scripts (audit9_*, audit10_*, audit11_*). |

Total `flbds/` + `tests/` + `configs/` = 8,502 lines [D: `wc -l`].

### 3.2 Module status vs plan
| Planned module | Implemented? | Evidence |
|---|---|---|
| M1 bio grounding (BioCLIP, VLM tagger, query planner, hybrid RAG, extractor) | **No** (only the text silver-card factory exists; no image path, no retrieval) | No such code in `flbds/`; PH:296-310 lists M1 as Phase 4 to-do |
| M2 Problem Card extractor (VLM) | **No**; the 12 dev Problem Cards are hand-authored JSON | `flbds/benchmark/dev/*/problem_card.json` |
| Mode B selector + problem pool | **No** | PDF p.1 |
| M3 graph/thesaurus/embeddings/reranker | **No** | PH:257-270 (Phase 2 to-do) |
| M4 role binder (LLM) | **No** — B3 runner defines `sp_prompted` but never calls it | runner11:697 (only occurrence) |
| M4 conflict detector + T1–T5 | Skeleton: rules on 4 hand-written fixtures; operators are hard-coded rewrites each mapped to one fixed template | `flbds/m4/conflict_detector.py`, `operators.py:105-123, 177-195, 244-262, 304-322, 394-412` |
| M5-Screen, M5-Eval, capacity bound | **Yes** | `flbds/physics/` |
| M6 novelty gate | **No** | PH:321-323 |
| M7 SVG/CadQuery/sketch | **No** | PH:317-320 |
| M8 UI | **No** | — |
| Gold cards (100) | **0**; empty templates exist | R5:36, 106; PH:248-249 |
| Test set (36 cases) | **0** | PH:223-237 |
| Image pairs (48) | **0** | PH:243-244 |
| Corpus | 1,000-doc pilot only (500 PMC, 500 BigPatent F/E) | NOTES.md:72-80; PH:35 |
| Silver cards | 133–135 | HO:122-129; R6:132-134 |
| Biological source for dev cases | 4 hand-written **FIXTURE** cards; 0 silver cards exist for dev organisms in corpus | `flbds/m4/fixtures.py:5`; R10:50-55 |

Historical note: before 2026-10-26 the repo contained a much larger previous system (AskNature 2,744-graph "G_MCKG", DeepGAR SMT alignment, Buckingham-Pi auditor, TRIZ solver, FastAPI UI, CadQuery/SVG tracks), all deleted in commit `5cf1d7b "chore: clear all files from repository"` [R: `git log`; ssh_details.md commit archive]. v5 (`flbds_v5.md`, 811 lines) planned 8 phases with per-phase caps up to 90 h; v9 cut to a 26-week, 160 GPU-h plan [v9:417-431].

### 3.3 Repo hygiene facts relevant to reproducibility
- Everything from Round 9 onward (`flbds/m4/`, `flbds/physics/screen.py`, `tests/test_m4_engine.py`, all round 9–11 runners and reports) is **untracked / uncommitted** locally [R: gitStatus `??` entries]. Local HEAD `97db903` (Round 8). Server repo HEAD is older still (`939dc51`, Round 5) with many uncommitted modifications, but it does contain `flbds/m4/` and `screen.py` [R: ssh `git log`, `git status`].
- GitHub repo `abhishek24024/FLBDS` reported public (R10:64-66; R11:80-84).
- Case-specific hacks in shared code: `capacity_bound.py:131` hard-codes `charge_h = 4.86 if "DEV-M1-S3" in problem_id` (uncommitted diff); scorer spec values hard-coded per case in `runner11:72-85` (`DEV_SPECS`) and written over the model's design (`apply_specs_to_design`, runner11:99-109, called before both screen and eval).

---

## 4. Benchmark

### 4.1 Dev set (12 cases = 4 clusters × 3 splits) [C: `flbds/benchmark/dev/`; PH:85-91]
| Case | System (problem_card) | Expected conflicts / operators (ground_truth_eval) | Acceptable templates | resources_absent |
|---|---|---|---|---|
| DEV-M1-S1 elephant | Thermal buffer facade panel | – | 02, 03, 05 | – |
| DEV-M1-S2 | Desert shelter storage wall | resource, direction, timing, effect, regime / T1–T5 | 02, 04 | liquid_water |
| DEV-M1-S3 | Ultra-compact thermal buffer | resource, timing / T1, T3, T5 | 02, 04 | liquid_water |
| DEV-M2-S1 penguin | Avionics microchannel CCHX | – | 08 | – |
| DEV-M2-S2 | Industrial exhaust heat recovery | direction / T2 | 08 | – |
| DEV-M2-S3 | Low-power avionics coolant HX | – | 08 | – |
| DEV-M3-S1 silver ant | Sensor canopy radiative shield | – | 09, 07 | – |
| DEV-M3-S2 | Telecom cabinet roof radiator | resource, direction / T1, T2 | 09 | grid_electricity |
| DEV-M3-S3 | Cryo-storage top shield | – | 09 | – |
| DEV-M4-S1 plastron insect | Submerged membrane aerator | – | 10 | – |
| DEV-M4-S2 | Submersible fuel-cell aeration | resource / T1 | 10 | pressurised_gas |
| DEV-M4-S3 | Bioreactor gas scavenger | – | 10 | – |
[D: printed from each case's JSON]. `time_pattern.time_mode` is `null` in all 12 cards [D], so the T3 rule (`conflict_detector.py:43-47`) cannot fire on any dev case.

- Splits: S1 unperturbed documented transfer; S2 in-operator conflict; S3 held-out coupled constraint no operator handles [v9:310]. In practice 9/12 cases have a single acceptable template, so template switching (the thing operators are meant to cause, e.g. T4) is impossible on them [D from table].
- Reference-design margins 1.10×–2.75× (R5 table 3; `flbds_data/benchmark/dev_case_margins.json`).
- Split 1 transfer citations for DEV-M1/M2/M3 are **UNVERIFIED** (Wang 2022, Song & Bhushan 2010, Zhai 2021 not found) [HO:109-111]. Principle "every Split 1 case must be a documented transfer" [v9:314] is not yet met.
- Proposed harder Split 2 variants with un-leaked feedback (`docs/proposals/split2_harder.md`) were written because feedback "explicitly stated the limiting parameter and the exact required target value" and models just tuned floats [split2_harder.md:4-9]; **not adopted** into the frozen cards.
- Problem Cards were repeatedly changed across rounds (hidden 10 K superheat cap exposed R9; flux stated as energy fixed R10; DEV-M4 heads changed R5→R6→R7) [R7:184-200; R9:5-19; R10:36-41; R6:154-158].

### 4.2 Test set
12 test clusters drafted in v9:297-308 (termite mound, Namib beetle, cactus spine, polar bear hair, jackrabbit pinna, tuna rete, camel nasal, xylem, leaf stomata, desert snail, prairie dog mound, toucan bill). **None authored** [PH:223-237]. Several flagged as possibly not documented transfers (toucan, snail, prairie dog) [v9:314].

### 4.3 Metric actually computed in runs
`passed` = template ∈ acceptable list AND capacity-bound OK AND `eval_tplXX` passes, with environment/limit fields overwritten from `DEV_SPECS` [C: runner11:112-156]. Wilson 95% CIs per condition; no per-cluster permutation statistics have been computed in any round [D: no such script in `scripts/`].

---

## 5. Experiments run and quantitative results

All runs: Qwen2.5-72B-Instruct-FP8, 12 frozen dev cases × 5 seeds = 60 runs/condition, T=0.7 (except early T=0.0 runs), guided JSON, 1×H200 via `gpurun` [runner11:9, 300-337].

### 5.1 Headline ledger (authoritative per R11)
| Condition (round) | Passes / 60 | Wilson 95% | S1 / S2 / S3 (of 20) | Source |
|---|---|---|---|---|
| B0 self-critique (R11) | 18 (30.0%) | 19.9–42.5 | 4 / 4 / 10 | R11:52, 59; `DATA/audit11/round11_benchmark_comparison.json` |
| B0 self-critique (R10) | 17 (28.3%) | 18.5–40.8 | 7 / 4 / 6 | R10:14-20 |
| "True" Screen-only lumped feedback, no operators (R11) — this *is* the A-NoOp design | 34 (56.7%); PVR_screen 36 (60.0%) | 44.1–68.4 | 11 / 12 / 11 | R11:22-34, 53 |
| Oracle = M5-Eval feedback (≈ B3-Screen+ without operators) (R10/R11) | 33 (55.0%) | 42.5–66.9 | 10 / 12 / 11 | R10:15; R11:54 |
| **B3** = fixture + M4 operator guidance + screen loop (R11) | **30 (50.0%)**; PVR_screen 25 (41.7%, 30.1–54.3) | 37.7–62.3 | 11 / 12 / **7** | R11:55, 62; `DATA/audit11/b3_dev_results.json` summary |
| A-NoOp R9 (evaluator feedback, 6 turns, older cards) — **withdrawn as headline** | 45 (75.0%) | 62.8–84.2 | 14 / 16 / 15 | R9:84-94; withdrawn R11:5-8, PH:158 |
| R10 "screen-only" (capacity-bound assertions only) | PVR_screen 60/60, PVR_eval 26/60 (gap 56.7 pts) | – | – | R10:22-34 |
| Older B0 variants (rescored) | 7–20 / 60 | – | – | R11 table A (lines ~12-20) |
Note: B3's PVR_screen (25/60) is *below* its PVR_eval (30/60), i.e. ≥5 B3 runs failed the lumped screen yet passed the coupled evaluator (screen stricter than eval on those designs); R11 does not report this. B3 condition wall time 494 s vs ≈296 s for the others [R: summary `elapsed_seconds`].

### 5.2 Per-case and per-cluster passes (my recomputation from server result JSONs) [R: `DATA/audit11/*.json`, `DATA/audit10/*.json`, `DATA/audit9/a_noop_results.json`; script run read-only]
| Case | B0 r11 | Screen r11 | Oracle r11 | B3 r11 | A-NoOp r9 |
|---|---|---|---|---|---|
| M1-S1 | 2/5 | 1/5 | 0/5 | 1/5 | 1/5 |
| M1-S2 (T1 fires) | 0/5 | 4/5 | 4/5 | 4/5 | 4/5 |
| M1-S3 (T1 fires) | 4/5 | 5/5 | 5/5 | **2/5** | 5/5 |
| M2-S1 | 0/5 | 5/5 | 5/5 | 5/5 | 3/5 |
| M2-S2 | 3/5 | 5/5 | 5/5 | 5/5 | 4/5 |
| M2-S3 | 2/5 | 0/5 | 0/5 | 0/5 | 4/5 |
| M3-S1 | 2/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| M3-S2 | 0/5 | 2/5 | 2/5 | 3/5 | 1/5 |
| M3-S3 | 2/5 | 5/5 | 5/5 | 5/5 | 4/5 |
| M4-S1 | 0/5 | 0/5 | 0/5 | 0/5 | 5/5 |
| M4-S2 | 1/5 | 1/5 | 1/5 | 0/5 | 4/5 |
| M4-S3 | 2/5 | 1/5 | 1/5 | 0/5 | 5/5 |
| **Clusters M1/M2/M3/M4** | 6/5/4/3 of 15 | 10/10/12/2 | 9/10/12/2 | 7/10/13/0 | 10/11/10/14 |

Observations [D]:
- Any feedback loop (screen or evaluator) roughly doubles B0 (≈30% → 55–57%). This is the only component with a measured, CI-separated benefit (B0 CI upper 42.5% < Screen CI lower 44.1%; borderline).
- **B3 vs Screen-only (the H3-style comparison): 30 vs 34 passes; B3 is lower, not higher.** The only cases where an operator fired (M1-S2, M1-S3) give B3 4/5 and 2/5 vs Screen-only 4/5 and 5/5. B3's Split-3 drop (7/20 vs 11/20) comes from M1-S3 and M4.
- Screen (lumped) vs Oracle (coupled) feedback: 34 vs 33 — no detectable difference; screen→eval gap 3.3 pts (2 runs) [R11:22-34].
- M2-S3 fails identically in all 5 seeds of Screen, Oracle and B3 ("Pressure drop 358.9 Pa exceeds 250 Pa") — the model returns the same design regardless of seed/feedback [R: failure-reason tally].
- DEV-M4 collapses from 14/15 (R9) to ≤2/15 (R10/R11) after the problem cards changed; see scoring/card mismatch in §6.
- With 4 clusters only, no cluster-level significance is possible (minimum two-sided permutation p with 4 clusters = 2/16 = 0.125) [D].

### 5.3 What B3 actually does in code (important for interpreting "operators")
[C: runner11:685-868; `flbds/m4/*`]
1. Loads a hand-written fixture for the cluster (`DEV_FIXTURES[cid[:6]]`) — not a retrieved or extracted card.
2. `detect_conflicts(fixture, problem_card)` (pure rules). Operator trace R11: only **T1** fired, on DEV-M1-S2 and DEV-M1-S3; all other 10 cases → no operator, including the three Split-2 cases whose ground truth expects T2 or T1 (M2-S2, M3-S2, M4-S2) [R11 operator trace table, lines ~64-78].
3. Applies the first matching operator (if/elif). Operators are fixed rewrites: T1→TPL_02 PCM, T2→TPL_09, T3→TPL_08, T4→TPL_02, T5→TPL_10 [C: operators.py]. They return a rewritten graph, but **the rewritten graph is not shown to the LLM**; the prompt only includes the original fixture Part/Organ/Effect, the operator id, a target template and a proof-obligation sentence [runner11:745-768].
4. **When no operator fires, the prompt's "Target Verifier Template" is `gt.acceptable_templates[0]` read from the hidden ground-truth file** [runner11:713]. So in 10/12 cases B3 is told the scorer's acceptable template. This alone explains B3's "100% template preservation / 0 template errors" headline [PH:148; R11:55].
5. Turn-1 B3 outputs were often malformed: only 28/60 initial responses contained `template_id`; 29/60 first feedbacks were "Schema validation error", 3 "No JSON object found" [R: my tally of `initial_response` / `feedback_history`]. Turn distribution B3 {0:8, 1:17, 3:35} vs Screen {0:21, 1:9, 2:4, 3:26}. So B3 often spent its first turn on a schema failure.
6. Parameters omitted by the model are filled from Pydantic defaults (e.g. TPL09 defaults ε=0.90, α=0.10, 20 mm substrate, k=0.05) [C: `flbds/schema/templates.py:165-187`]. Example: B3 DEV-M3-S1 seed 3 final JSON contained only `{"template_id":"TPL_09","max_inner_leakage_W_m2":0.05,"required_net_cooling_W_m2":0.157542}` and **passed** — i.e. the pass came from schema defaults + DEV_SPECS overrides, not from model-chosen optical properties [R: `DATA/audit11/b3_dev_results.json`].
7. M5-Screen itself reads the hidden ground-truth `acceptable_templates` and returns "Selected template ... not in acceptable templates: [...]" as feedback [C: `flbds/physics/screen.py:62-74`], so in the Screen and Oracle conditions the hidden template list leaks via feedback (7/60 first-feedback messages in each were this message [R]).

### 5.4 Discrepancy between the agent's B3 transcript review and the raw data
`docs/audit/b3_round11_transcript_review.md:40-50` claims BLIND-B3-R11-03 (DEV-M1-S3, seed 3) specified L=0.022 m, matrix volume fraction 0.12, k_eff=2.4, 3.68 MJ/m², superheat 4.82 K, and calls it "Exemplary ... Directly followed Operator T1" (also line 109). The raw final JSON is `thickness_m 0.04, k_eff 1.5, matrix_density 2700, required_energy_J_m2 800000`, **no matrix_volume_fraction** [R: `DATA/audit11/b3_dev_results.json`]. Other reviewed items (M1-S1 seed 2: claimed L=0.024; actual 0.045; M3-S1 seed 3: claimed α=0.05/ε=0.95; actual output omitted both) also do not match. The pass/fail verdicts in `b3_round11_review_key.json` do match. Conclusion [D]: the qualitative narrative in that review is not grounded in the transcripts; the claim "Operator T1 proved causally effective" is unsupported. Across the 5 B3 seeds on M1-S3, only 2/5 passed and none set a matrix fraction (k_eff 0.15–1.5).

### 5.5 Silver-card factory (pilot, 1,000 docs) [HO:122-129; R6:130-134; NOTES.md:72-108]
- Stage 1 (7B filter) 1,000→391; Stage 2 (72B teacher, guided) →357; Stage 3 agreement 67.7% exact / token-F1 0.814; Stage 4 schema+verbatim →270; Stage 5 (32B entailment critic) →137; Stage 6 quantities →133; Stage 7 dedup →135 (after subject-pruning fix). ~13.3% cumulative yield. (R5:14 notes JSON artifacts say 372/361/348, conflicting with the prose 391/357/270.)
- Quality: Seed-11 human-style review 7 GOOD / 10 MINOR / 7 MAJOR of 24 (HO:147); critic false-negative drops 7/20 (HO:148); critic accepted 4/7 MAJOR cards (R5:62-64); a card-level "primary mechanism" critic rejected 7/7 GOOD cards (R7:212-220). Teacher self-agreement on Phenomenon only 44.2% (NOTES.md:93-99).
- Domain coverage: "51 of 53 bio silver cards described materials ... not organisms" [P p.10, p.15]; 0 silver cards for the 4 dev organisms (R10:50-55); 12/16 benchmark organisms absent from pilot (NOTES.md:105-114).
- Pilot compute: 0.20 GPU-h per 1,000 docs; ≈6–8 GPU-h for 30k docs (NOTES.md:101-104).
- Embedding check (agent-reported): cross-domain similarity 0.764 vs within-domain 0.775 in an all-thermal corpus [P p.9].

### 5.6 Throughput measured (docs/throughput.md)
vLLM decode on H200: 7B 1,658 tok/s; 32B-FP8 593 tok/s; 72B-FP8 325 tok/s (10-prompt micro-benchmark; 0.12–0.16× of the doc's planning assumptions). Full 60-run benchmark condition ≈ 296 s wall (R11 JSON `elapsed_seconds`); Round 11 total 0.79 GPU-h for all four conditions (R11:94-100).

### 5.7 GPU usage to date
Rounds 5–11 each used < 1 GPU-h (R5:4; R6:124; R7:181; R9 0.147 h; R10 0.19 h; R11 0.79 h). Broker now shows 90.0/90.0 GPU-h remaining this week [R: `gpurun --status`, 2026-11-19]. Compute has never been the bottleneck (v9:419 says "people, not GPUs").

---

## 6. Known failures, open problems, and where complexity is not paying off

### 6.1 Failure modes observed in transcripts / results
1. **Unit/scale hallucination on micro-scale parameters (DEV-M4):** pore diameters emitted as 2.5–4.55 m (`pore_diameter_m: 2.5`) → Laplace breakthrough 0 Pa; not corrected within 3 turns [R: B3 M4-S1 seed 3; `b3_round11_transcript_review.md` items 07–08].
2. **Insufficient conductivity / missing matrix in PCM (DEV-M1):** superheat 10.07–16.99 K vs 10 K cap; model tweaks latent heat/density but not k_eff [R: failure tally; R10 BLIND-R10-06].
3. **Coupled trade-off traps (DEV-M2):** pressure drop vs duty; model reduces flow below capacity (A-NoOp review DEV-M2-S1) or returns the identical design in all seeds (M2-S3, 358.9 Pa) [`anoop_review_6transcripts.md:47-57`; R].
4. **Inverted sizing derivative (DEV-M3):** thinning a conductive substrate to cut leakage [`anoop_review_6transcripts.md:39-45`].
5. **Mechanism never changes under feedback:** "0 of 8 reviewed transcripts changed mechanism"; models only scale floats [P p.1; R10:43-48; split2_harder.md:4-9].
6. **Environment hallucination:** unguided runs set their own solar/sky/ΔP values; fixed by binding evaluator to card values (R9:21-33; HO:106).
7. **Guided-decoding schema failures** in B3 turn 1 (32/60 malformed) [R, §5.3].

### 6.2 Benchmark/evaluation validity problems (found by reading code + data)
- **Ground-truth leakage into generation:** B3 prompt template from `gt.acceptable_templates[0]` (runner11:713); M5-Screen feedback reveals the acceptable list (screen.py:62-74). Violates P7 / "Problem Card contains no template names" [v9:117, 173-174].
- **Scorer/card mismatch on DEV-M4:** `DEV_SPECS` scores DEV-M4-S1 at hydrostatic head 10.0 m (runner11:82) while its problem card and reference design say 2.5 m (`DEV-M4-S1/problem_card.json` constraints; `reference_design.json` head 2.5, d_pore 2.4 µm). Per R6:156 a 2.4 µm pore breaks through at 4.18 m, so [D] the frozen reference design would fail the 10 m scoring spec → case likely unsatisfiable as scored (P10 violated). This coincides with 0/5 in every condition since R10.
- **Defaults pass designs:** Pydantic template defaults plus `apply_specs_to_design` overwrite let near-empty outputs pass (M3-S1 example) [§5.3 item 6].
- **Split 2 does not exercise operators:** 3/4 Split-2 cases fire no operator; T3 can never fire (time_mode null); single-template cases make T4-style substitution impossible [§4.1].
- **Biological source is a hand-written fixture**, so RQ2 (does biology help) cannot be informed by the current B3 at all [`fixtures.py:5`].
- **Small N:** 4 dev clusters; CIs of all feedback conditions overlap heavily (e.g. B3 37.7–62.3 vs Screen 44.1–68.4) [R11:52-55].
- **Repeated case edits after seeing results** (caps exposed, fluxes fixed, heads changed, margins tuned) across R5–R10 — dev set is heavily tuned; v9 itself only allows that on dev.
- **Agent-written narrative reviews contain ungrounded details** (§5.4) and the handover docs repeat them as findings (PH:148-149).

### 6.3 Where complexity is not paying off (evidence-based)
| Component | Cost / complexity | Measured benefit so far |
|---|---|---|
| M4 operators + conflict detector + SAPPhIRE graph rewrite (792 lines + 223+271 test lines) | Hard-coded per dev cluster; rewritten graph unused by the LLM | B3 30/60 < Screen-only 34/60; on the 2 cases where T1 fired: 6/10 vs 9/10 for Screen-only. No evidence of gain. |
| Dual-tier verifier (Screen vs Eval) | Two implementations per template | Feedback from either tier gives ≈ the same pass rate (34 vs 33); screen→eval gap 3.3 pts on dev. The tiering matters for honest scoring, not for generation. |
| Silver-card factory (7 stages, 3 LLMs, 1,643 lines) | 13% yield, ~30% MAJOR-error rate in samples, mostly engineered materials | Not used by any benchmark condition (dev uses fixtures). |
| Planned M1/M3/M6/M7/Mode B, three-head adversarial embedding, DPO proposer | Large (Phases 2, 4, 5) | Not built; no evidence yet. Proposal's own pilot embedding check shows domain similarity barely separates (0.764 vs 0.775) [P p.9]. |
| Physics feedback loop (screen) | ~200 lines on top of templates | **Only measured win**: ≈ +26 pts over B0 (30% → 56.7%). |

### 6.4 Open items explicitly listed in docs
Gold cards, rater recruitment, USPTO key, Split-1 transfer citations, test-set authoring, DEV-M4 margin/binding constraint, harder Split 2, GitHub visibility, history purge, blind packets awaiting user review [HO:159-173; PH:377-390; R11:80-92; `docs/proposals/history_purge_plan.md`].

---

## 7. Compute / server setup (checked read-only over SSH on 2026-11-19)
- Access: `ssh -i ~/.ssh/bio_server abhishek24024@192.168.2.69` (key auth via agent; works non-interactively); requires IIIT FortiClient VPN, ProtonVPN off [`ssh_details.md`]. Hostname `hcd-dept-h200`.
- Hardware [R]: Ubuntu 24.04.4 LTS; 128 CPU threads; 1,007 GB RAM; **4× NVIDIA H200 SXM (~141 GB each)** behind a broker (direct `nvidia-smi` → "Insufficient Permissions"). Shared with other users: at check time GPUs 0 and 3 were running other users' jobs, GPUs 1 and 2 idle. Load average ≈118 (CPU shared).
- Scheduler: **no Slurm**; custom broker `/usr/local/bin/gpurun` over `/run/gpu-broker/broker.sock`; `gpurun -g N <cmd>`; quota **90.0 GPU-h/week per user** (1 GPU-h = 1 H200 for 1 h); remaining 90.0 at check time [R: `gpurun --status`; NOTES.md:52-58]. Multi-GPU allowed if free (`-g N`).
- Disk: `/dev/sda2` 21 TB, 4.9 TB used, 16 TB free; user quota ~900 GB soft / 1 TB hard (NOTES.md:44-46); `flbds_data` 117 GB, repo 5.8 MB [R].
- Environment [R]: `/home/abhishek24024/flbds_env` — Python 3.12.3, **vLLM 0.32.0**, **PyTorch 2.13.0+cu130**, Pydantic 2.14.1; CUDA 13.3 (NOTES.md:47-51). (PH:37 says "PyTorch 2.5, vLLM 0.7.0" — outdated/incorrect.)
- Paths [R]: repo `/home/abhishek24024/flbds/`; data `/home/abhishek24024/flbds_data/` with `api_responses, audit5..audit11, benchmark, biological_papers, corpus, harvest, models, pilot, pilot_smoke, pulled_bio_papers, review`.
- Latest results [R]: `DATA/audit11/` (2026-11-03): `b0_self_critique_results.json`, `screen_only_results.json`, `oracle_feedback_results.json`, `b3_dev_results.json`, `round11_benchmark_comparison.json`, `master_b0_rescore_summary.json`, `gpu_suite.log`, `suite_runner.log` (suite ran 19:21–19:35). Nothing newer than Round 11 on the server.
- Models on disk: Qwen2.5-72B-Instruct-FP8, Qwen2.5-32B-Instruct-FP8, Qwen2.5-7B-Instruct only (2024-era). The PDF itself proposes adding "one stronger, newer open model" [P p.18]. Models run as offline `vllm.LLM` per job (no persistent server). An older "analogy app API" on port 8765 belongs to the deleted pre-Oct-26 system [`ssh_details.md`] — not checked.
- Time budget: v9 is a 26-week solo BTech plan dated 30 Oct 2026 [v9:5]; PH:173 says Phase 0 (weeks 1–3) complete; remaining Phases 1–6 = weeks 4–26 with 160 planned / 251 cap GPU-h [v9:417-431].

---

## 8. One-paragraph synthesis for the architect
The only parts of FLBDS that exist and work are (a) ten hand-written TFP physics templates with lumped and coupled checks, (b) 12 hand-authored dev cases, and (c) an LLM-proposes-typed-parameters → physics-feedback loop using Qwen2.5-72B. That loop is the only component with a measured benefit (≈30% → ≈55–57% PVR_eval on 60 dev runs). The symbolic M4 layer (conflict rules + T1–T5 graph rewrites) is a thin, cluster-specific skeleton; it fires on 2/12 cases, its rewritten graph never reaches the model, and B3 (operators + screen) scored 30/60 vs 34/60 for the same loop without operators. B3's "100% template preservation" comes from reading the hidden acceptable template into the prompt. The biology side (M1, M3, gold cards, image entry, Mode B), novelty (M6), and outputs (M7) are unbuilt, and the benchmark biology is four hand-written fixtures. The evaluation has leakage (template list in prompt and screen feedback), a scorer/card mismatch on DEV-M4, default-filled passes, only four clusters (no significance possible), and agent-written reviews whose details do not match the transcripts. Compute is plentiful (4× H200 broker, 90 GPU-h/week, <2 GPU-h used across all rounds); the binding constraints are human effort (gold cards, test cases, raters) and evaluation validity.
