# Cut FLBDS Down to Its Working Verifier Loop

FLBDS should become a much smaller system, V10. It keeps the one part that has measured value: an LLM proposes a design, a deterministic physics screen sends back per-constraint numeric feedback, and a hidden physics scorer that never sees the generator grades the result. The symbolic operator layer, the knowledge graph, the image front end and Mode B are either removed or postponed until an experiment shows they are worth building. The evidence for this is consistent across both the project and the literature. On the 12 dev cases, screen feedback roughly doubled Qwen2.5-72B's pass rate, from 18/60 (30.0%) to 34/60 (56.7%). Adding the M4 operators on top lowered it to 30/60. Meanwhile, published work agrees that only external, trustworthy feedback improves LLM outputs, and that prompted "guidance" does not ([Kamoi et al., TACL 2024](https://aclanthology.org/2024.tacl-1.78); [Huang et al., ICLR 2024](https://arxiv.org/abs/2310.01798)). There is a catch: every number produced so far is contaminated. The hidden list of acceptable templates leaks into both the B3 prompt and the screen's feedback. Schema defaults let near-empty designs pass. One dev cluster is scored against a spec that its own reference design fails. And four clusters cannot reach p<0.05 under any test. The first job is therefore repair, not new modules: fix the leaks, then replace the twelve hand-tuned cases with about 80 sealed, solver-certified parametric instances. After that, the project can run a preregistered sequence of six experiments that answers the real open question, which is whether biology changes the *choice of mechanism*, once an optimiser handles the floats. That sequence needs roughly 30–45 H200 GPU-hours, about half of one week's quota. The binding constraints are human effort and evaluation validity, not compute. The proposal's claims about operators, images, Mode B and general "physics verification" should be narrowed until that evidence exists.

## Only the physics feedback loop has earned its place

### What the project's own results show

The project's results are easier to read once you separate what was built from what was planned. What exists and works is:
- ten hand-written thermal, fluid and porous-media (TFP) templates, each with a lumped screen and a coupled evaluator (2,442 lines in `flbds/physics/`);
- 12 hand-authored dev cases (4 mechanism clusters × 3 splits);
- a loop in which the LLM proposes typed parameters and gets physics feedback.

The planned biology path does not exist. There is no image path, no retrieval, no gold cards, no test set and no Mode B (`00_project_digest.md` §3.2). The "biological source" in every B3 run is one of four hand-written fixture cards (`flbds/m4/fixtures.py:5`).

The Round 11 ledger, recomputed from the server's result JSONs, shows two things. First, any external feedback (lumped screen 34/60, coupled oracle 33/60) beats the self-critique baseline B0 (18/60), and that is the only gain whose 95% confidence interval separates, if only borderline (B0 upper 42.5% vs Screen lower 44.1%). Second, the full B3 condition (fixture card, conflict detector, operator guidance and screen loop) scored **30/60, below the same loop without operators**.

### The operator layer did not do what it was meant to do

The operator layer's mechanics explain the null result. Only operator T1 ever fired, on 2 of 12 cases. On those two cases B3 scored 6/10, against 9/10 for the plain screen loop. The rewritten graph that an operator produces is never shown to the model. T3 cannot fire on any dev case, because `time_mode` is null in all twelve Problem Cards. Nine of the twelve cases have a single acceptable template, so switching templates, which is what operators exist to cause, is impossible on most of the benchmark (`00_project_digest.md` §4.1, §5.3). Transcripts confirm the behaviour the operators were meant to break: in 0 of 8 reviewed transcripts did the model change mechanism under feedback. It only rescaled floats.

### Two conclusions that shape the rest of the design

The screen and the oracle produced almost the same pass rates (34 vs 33). For *guiding generation*, the cheap lumped tier is enough. The coupled tier earns its keep only as an honest, hidden scorer and as a detector of models gaming the screen.

The literature points the same way on every axis that matters here:

- **External feedback is what works.** Kamoi et al.'s survey concludes that self-correction works "where reliable external feedback is available". They found no successful case of feedback from prompted LLMs on general tasks ([Kamoi et al.](https://aclanthology.org/2024.tacl-1.78)).
- **Simulator loops roughly double success, then plateau.** In SciDesignBench's 520 tasks, including heat exchangers and reactors, simulator feedback doubles to triples single-shot success. Frontier models plateau at about 67–76% after 20 turns, and giving the model a starting design *lowered* scores for all seven models ([SciDesignBench](https://arxiv.org/html/2603.12724)). FLBDS's jump from 30% to 57% at three turns sits squarely in that regime.
- **No BID system checks physics.** No LLM bio-inspired design (BID) system surveyed verifies physics. BioSpark, the best-evidenced one, raised expert-rated novelty but *lowered* feasibility, 5.7 vs 6.8 ([BioSpark, CHI 2025](https://arxiv.org/html/2503.09838v1)). Zhu et al. name "infeasible numbers" as a core failure of GPT-based BID ([Zhu et al., JMD 2023](https://arxiv.org/pdf/2212.13196)).
- **TRIZ structure has not been shown to improve design quality.** Published TRIZ-plus-LLM systems have no plain-LLM baseline ([AutoTRIZ](https://arxiv.org/html/2403.13002v2); [TRIZ Agents](https://arxiv.org/html/2506.18783v1)). The one benchmark, TRIZBench, finds that TRIZ structure helps *classification* of principles, not design quality ([TRIZBench, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.1798/)).

The physics verifier is both FLBDS's differentiator and the only component with evidence behind it. The architecture should be rebuilt around it.

## Twelve leaks and bugs invalidate every number so far

### The 56.7% may be inflated

Before any new experiment, the existing loop has to be made honest, because its headline 56.7% may be inflated. These are classic test-leakage and reward-hacking patterns. Pan et al. show that feedback loops drive models to optimise the proxy at test time ([Pan et al., ICML 2024](https://proceedings.mlr.press/v235/pan24d.html)). METR documents frontier models exploiting scorer bugs and reference answers ([METR 2025](https://metr.org/blog/2025-06-05-recent-reward-hacking)).

The table lists each defect with its location. Several of the locations were re-checked against the working tree while writing this report:
- the template leak at `run_round11_benchmarks.py:713`;
- `DEV_SPECS` at lines 72–85, including the 10.0 m head at line 82 against the card's "2.5 m";
- the `capacity_bound.py:131` hack;
- the `abs(np.cos(...))` at `tpl10_diffusion.py:149` and `screen.py:193`.

A quick Laplace calculation (γ=0.072 N/m, θ=110°) confirms that the DEV-M4-S1 reference pore of 2.4 µm breaks through at about 4.2 m of head. So the frozen case is unsatisfiable as scored.

| # | Defect | Location | Effect on results | Fix |
|---|---|---|---|---|
| 1 | B3 prompt's "Target Verifier Template" is read from hidden ground truth when no operator fires (10/12 cases) | `scripts/run_round11_benchmarks.py:713` | Explains B3's "100% template preservation" | Template must come from the model's own choice |
| 2 | Screen checks membership in `gt.acceptable_templates` and echoes the list as feedback | `flbds/physics/screen.py:21, 62-74` | 7/60 first feedbacks in Screen and Oracle leak the answer | Screen judges admissibility only through physics and regime checks; screen may not import `GroundTruthEval` |
| 3 | Scorer specs live in a second hard-coded table and overwrite model fields before both screen and eval | `run_round11_benchmarks.py:72-85`, `apply_specs_to_design` `:99-109` | Model-chosen values are silently replaced | Environment and limits come only from the frozen Problem Card; a test asserts card = scorer |
| 4 | DEV-M4-S1 is scored at a 10.0 m head; the card and reference design say 2.5 m | `run_round11_benchmarks.py:82` vs `flbds/benchmark/dev/DEV-M4-S1/problem_card.json` constraints | Case unsatisfiable as scored; M4 cluster collapsed from 14/15 to ≤2/15 | Satisfiability certificate: the reference design must pass the same scorer call in CI |
| 5 | Pydantic defaults fill omitted design variables (TPL-09 ε=0.90, α=0.10, substrate 20 mm, k=0.05) | `flbds/schema/templates.py:165-187` | A three-field B3 output on DEV-M3-S1 passed | No defaults on design variables; `extra="forbid"`; a missing field is a schema failure |
| 6 | Screen falls back to invented caps when the card is silent (thickness 0.05 m, mass 500 kg/m², TPL-07 envelope, TPL-08 length and velocity) | `flbds/physics/screen.py:77-84, 136, 140, 155` | The screen checks limits nobody stated | Missing limit = not checked, and logged; never a fabricated limit |
| 7 | Case-specific hack in shared code: `charge_h = 4.86 if "DEV-M1-S3" in problem_id` | `flbds/physics/capacity_bound.py:131` (also `DEV_SPECS` charge_hours) | Gate tuned to one case | Charge duration is a Problem Card field; replace the gate with an optimiser certificate |
| 8 | Laplace breakthrough uses `abs(cos θ)`, so hydrophilic pores look like hydrophobic ones | `flbds/physics/tpl10_diffusion.py:149`, `flbds/physics/screen.py:193` | Common-mode physics error in both tiers | Require θ>90°, else return `invalid_regime` |
| 9 | Screen and eval share helpers | `tpl08_countercurrent.py:52,171`; `tpl06_porous_flow.py:14,49,88` | Shared bugs, so tier agreement is not independent evidence | Hidden eval gets its own implementation |
| 10 | Screen is not a relaxation of the eval (TPL-08 uses only `m_dot_cold` and A = D_h²) | `flbds/physics/screen.py:142-151` | B3 PVR_screen 25/60 < PVR_eval 30/60, so the screen rejected eval-feasible designs | Rebuild the screen from necessary-condition bounds; property-test screen_fail ⇒ eval_fail |
| 11 | 32/60 B3 first turns were malformed ("Schema validation error" or "No JSON") | B3 prompt `run_round11_benchmarks.py:745-768` never shows field names (`SCHEMA_SPEC` used only at `:433`); decoder schema is a union over all templates (`:312-314`); `max_tokens=1024`, `max_model_len=4096` (`:335`) | B3 burned its first of 3 turns on format errors | Two-call decoding (below); re-sample validation failures without spending a turn |
| 12 | The agent-written B3 transcript review reports parameters absent from the raw JSON (claimed L=0.022 m, volume fraction 0.12; actual 0.04 m, no fraction) | `docs/audit/b3_round11_transcript_review.md:40-50, 109`; repeated in `docs/PROJECT_HANDOVER.md:148-149` | "Operator T1 proved causally effective" is unsupported | Retract; quote reviewed parameters only by machine extraction from raw outputs |

### Ruling out one suspected cause of the malformed outputs

One hypothesis from the literature notes can be ruled out. vLLM removed the old `guided_*` fields in v0.12 ([vLLM docs](https://docs.vllm.ai/en/latest/features/structured_outputs.html)). Round 11 already uses the current API: `StructuredOutputsParams(json=schema_dict)` at `run_round11_benchmarks.py:23, 313-314`. So the malformed outputs are not silently unconstrained decoding.

The likelier causes have different fixes:
- **The prompt never shows the schema.** B3 is told to match "the JSON schema for TPL_xx" but is never shown the fields.
- **The union schema is too complex for the grammar engine.** In JSONSchemaBench, XGrammar, vLLM's default backend, produced the most under-constraining failures on complex schemas (38 categories vs 1 for Guidance) ([JSONSchemaBench, ICML 2025](https://arxiv.org/html/2501.10868v3)).
- **Pydantic validation is stricter than the grammar.** Output can pass the grammar and still fail validation.

### Hygiene that must accompany the fixes

Commit and tag everything from Round 9 onward. It is all untracked locally, and the server's HEAD is at Round 5. Keep any sealed test material off the public GitHub repository.

## V10 keeps five modules and drops or defers the rest

### The pipeline

V10 makes one design move. It splits the LLM's job, choosing *which physical mechanism and template to use*, from the numeric job of *finding parameters that satisfy the physics*. The literature consistently finds that hybrids win: the LLM supplies structure or priors, and a classical optimiser fits the numbers.

- **Hyperparameter optimisation.** CMA-ES with an LLM proposing 30% of trials beat every classical and pure-LLM method, even with a 0.8B model. Giving the LLM 80% of trials collapsed performance ([Centaur HPO benchmark, 2026](https://arxiv.org/html/2603.24647v5)).
- **Equation discovery.** The LLM proposes skeletons and BFGS fits the constants ([LLM-SR, ICLR 2025](https://arxiv.org/html/2404.18400v3)).
- **Constrained inverse design.** A BoTorch baseline reached the ceiling where the best LLM did not ([arXiv 2511.00070](https://arxiv.org/pdf/2511.00070)).

FLBDS's dominant failures are the kind a bounded optimiser fixes deterministically:
- pores emitted in metres;
- superheat 0.07–7 K over the cap, with the model never touching k_eff;
- inverted sizing derivatives;
- an identical 358.9 Pa design returned in all five seeds of DEV-M2-S3.

Every screen is closed-form and runs in microseconds to milliseconds, so a SciPy differential-evolution plus SLSQP polish costs seconds on CPU.

The V10 generation path has six steps:

1. **Choose a template.** The LLM reasons in free text and then picks a template with `structured_outputs.choice` from the full catalogue. Each catalogue entry lists the template's physics preconditions and validity regime, never a hidden acceptable list. This follows the reason-then-format pattern that avoids the reasoning penalty of strict JSON ([Tam et al., EMNLP 2024](https://aclanthology.org/2024.emnlp-industry.91)).
2. **Fill a flat per-template JSON.** All fields are required, Pint-parsed `{value, unit}` pairs with physical bounds.
3. **Sample diversely.** The loop draws N=8 diverse proposals. Olausson et al. find repair pays most when budget goes to "a diverse set of initial programs" ([Olausson et al., ICLR 2024](https://arxiv.org/abs/2306.09896v4)), and verified coverage grows roughly log-linearly with samples ([Brown et al. 2024](https://arxiv.org/abs/2407.21787v3)).
4. **Screen.** The rewritten M5 screen returns, per constraint: achieved value, card-stated limit, signed normalised margin, PASS/MISS, plus fixed template-derived sensitivity signs (for example, "superheat falls with k_eff"). It may also return a third verdict, `invalid_regime`, when the design falls outside a template's declared validity window.
5. **Repair or optimise.** Up to three repair turns follow, with the top-k designs so far shown to the model, as in Eureka and OPRO ([Eureka](https://arxiv.org/abs/2310.12931)). Alternatively, in the optimiser arm, the continuous parameters are optimised against the screen.
6. **Score once.** The single best design by minimum screen margin goes once to the hidden M5-Eval.

This is the cheap-to-expensive evaluation cascade that AlphaEvolve formalises ([AlphaEvolve harness docs](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/developer-guide/logical-architecture)).

### What changes in the physics layer

The physics layer gets smaller and more trustworthy, not larger.

**Each template declares its validity regime.** Each template gets a `validity` block of dimensionless groups with closed intervals, for example:
- Bi<0.1 for TPL-07;
- Re_p≤10 for TPL-06;
- laminar Re for TPL-08;
- θ>90° and a Knudsen window for TPL-10;
- a Stefan-number window for TPL-02.

**The regime check replaces the operators' regime logic.** The same mechanism gives a deterministic version of the "look-alike ≠ work-alike" check the operators were meant to provide. When the dimensionless group that makes the organism work falls outside the template's window at the problem's scale, the transfer is flagged. Riblets work only near s+≈10–20 wall units and *increase* drag beyond it ([García-Mayoral & Jiménez](https://torroja.dmt.upm.es/congresos/katnet09/pdf/Wednesday/Session%20Wed%202/RGM_JJ.pdf)). Termite-mound ventilation is driven by diurnal thermal oscillation, not wind ([King, Ocko & Mahadevan, PNAS 2015](https://dash.harvard.edu/bitstream/handle/1/23603185/MahadevanTermite2015.pdf?sequence=1)). Pad-based adhesion does not scale beyond gecko size ([Labonte et al., PNAS 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4747726)). Each is a regime check, not a graph rewrite.

**The screen becomes a provable relaxation of the scorer.** It is built only from necessary-condition bounds (first-law limits, ε≤1, best-case material). A Hypothesis/Sobol property test asserts screen_fail ⇒ eval_fail over 10⁴ sampled designs per template. This turns the multifidelity "filtering" role into a CI gate ([Peherstorfer et al., SIAM Review 2018](https://arxiv.org/pdf/1806.10761)).

**Templates get metamorphic and property tests.** These check conservation, monotonicity, limiting cases, dimension invariance and sign, the standard remedy for scientific code without oracles ([Kanewala & Chen](https://par.nsf.gov/servlets/purl/10085974)).

**Templates and scorers stay hand-written.** LLM agents now get FE and CFD code to *run* after repair, but "runs" overstates "physically correct" by about 20 points ([CAE harness study, 2026](https://arxiv.org/html/2609.03718)). Repeated-trial consistency is also well below best-of-k ([FEM-Bench](https://arxiv.org/html/2512.20732)).

### Module-by-module decisions

| V9 module | V10 decision | Reason |
|---|---|---|
| G1 visual thesaurus | **Defer** | No downstream gain shown anywhere. A knowledge graph is justified only as a provenance and navigation layer. It is not on the critical path to any hypothesis. |
| M1 bio grounding (BioCLIP, VLM tagger, query planner, hybrid RAG, extractor, critic) | **Defer, then replace with a thin grounded path if H3 passes** | Unbuilt. The photo is not what limits performance. If built: BioCLIP 2 zero-shot over a *closed* candidate list with abstention, optional VLM re-rank, taxon-keyed PMC OA retrieval, and the existing extractor plus verbatim-span check plus a ChatExtract-style value verification turn. Never ask the VLM for the mechanism. |
| M2 Problem Card extractor (VLM/text parser) | **Replace** with the parametric instance generator | Cards are generated from sampled parameters and rendered to template-free text. A text-to-card parser is a Mode A demo feature only. |
| Mode B selector and problem pool | **Drop from this project's claims** | Not implemented, depends on M1 and M3, and RQ4 has no preliminary evidence. |
| M3 knowledge graph, three-head adversarial encoder, Leiden communities, reranker | **Drop for generation; simplify to a flat card table if retrieval is needed** | The proposal's own pilot found cross- and within-domain cosine barely separate (0.764 vs 0.775). A flat table with BM25 + Qwen3-Embedding-0.6B and a hard filter on a ~10-value physical-effect enum aligned to the templates gives effect-keyed retrieval without a graph. |
| M4 role binder (LLM) | **Drop** | Never called (`sp_prompted` defined but unused at runner11:697). |
| M4 conflict detector | **Simplify** into the screen's regime and dimensionless-group check | The deterministic part with a defensible physical basis survives. The rules tied to fixtures do not. |
| M4 operators T1–T5 (T6–T7) | **Drop** | Fixed per-cluster rewrites, each mapped to one template. The rewritten graph is never shown to the LLM. B3 30/60 < Screen 34/60. No literature support for TRIZ-style guidance improving verified designs. |
| LLM parameter proposer | **Keep, simplify** | Two-call decoding, all-required bounded schema, N diverse samples, top-k precedent feedback, re-sampling on validation failure. |
| Numeric optimiser (new) | **Add** | Handles the dominant numeric failure modes. Doubles as a satisfiability certificate and as the "solver-optimised conventional design" baseline. |
| M5-Screen | **Keep, rewrite** | Only component with measured gain. Must become a provable relaxation with no ground-truth access, no defaults, unit-checked inputs, a regime verdict and numeric per-constraint feedback. |
| M5-Eval | **Keep, harden** | Independent implementation, Problem-Card-only specs, abs(cos) fix, a verification metadata block in V&V 20 terms ([Coleman, ASME V&V 20](https://maretec.tecnico.ulisboa.pt/~maretec.daemon/html_files/CFD_workshops/html_files_2008/papers/COLEMAN.pdf)). scikit-fem only for a ~30-design audit tier ([scikit-fem](https://joss.theoj.org/papers/10.21105/joss.02369)). |
| Capacity-bound gate | **Replace** with an optimiser-based certificate | Removes the `capacity_bound.py:131` hack and computes each instance's feasible-template set from physics. |
| M6 novelty gate (LLM judge, four classes) | **Simplify** to Shah novelty and variety over a coded attribute tree; LLM judge only after calibration against experts | LLM-judge agreement is metric-dependent and weak for feasibility and scientific novelty ([Edwards et al. 2025](https://arxiv.org/abs/2504.00938); [arXiv 2606.12071](https://arxiv.org/pdf/2606.12071)). |
| M7 outputs (SVG, CadQuery/STEP, sketches, IP-Adapter baseline) | **Defer** | No hypothesis depends on them. Output a parameter table plus text explanation. |
| M8 designer UI | **Drop for now** | No research claim uses it. |
| Silver-card factory (7 stages, 3 LLMs) | **Freeze** | About 13% yield, about 30% MAJOR errors in samples, 51/53 bio cards about materials rather than organisms, unused by any benchmark condition. For experiments, replace with 16 hand-written gold cards from PMC primary papers. |
| B4 DPO proposer | **Replace with GRPO on screen reward, deferred** | RL from simulator reward on 7–8B Qwen models gave +11 to +17 points ([SciDesignBench](https://arxiv.org/html/2603.12724)) or beat prompted frontier models ([RocketBench](https://arxiv.org/html/2504.19394v1)). It is the main lever past prompting's plateau. |
| Human evaluation (three packets, ~26 h per rater) | **Narrow** | Packet A (binary verifier audit, Cohen's κ) is feasible. Analogical-validity ratings only if two qualified raters are recruited. Agent-written reviews never count as evidence. |

### The image front end, if it is ever built

If the H3 gate below passes, the image path should be deliberately narrow. On species identification the specialist encoder dominates:
- **BioCLIP 2** reaches 55.6% mean zero-shot top-1 over ten species benchmarks and is MIT-licensed ([BioCLIP 2](https://arxiv.org/html/2505.23883v2); [model card](https://huggingface.co/imageomics/bioclip-2)).
- **Qwen2.5-VL-7B** manages about 21% open-vocabulary. Its best use is re-ranking a specialist's top-5, which reached 65.6% ([arXiv 2512.15748](https://arxiv.org/html/2512.15748v1)).
- **Open-ended VLM answers** invent nonexistent species in 5.9–9.6% of responses ([arXiv 2609.11916](https://huggingface.co/papers/2609.11916.md)).
- **VLMs follow leading hints** almost blindly ([VLM4Bio](https://arxiv.org/html/2408.16176v1)).

So the VLM prompt must never contain the hypothesised taxon or mechanism.

The 51/53 materials-not-organisms failure is a corpus-selection problem, and taxon-keyed retrieval fixes it directly. Two further constraints apply:
- **AskNature cannot be bulk-mined.** Its terms forbid robots and data mining ([Biomimicry Institute terms](https://biomimicry.org/terms/)), so use it only manually, as a pointer to the primary papers.
- **Corpus licences must be recorded.** Draw the corpus from the PMC OA licence buckets and record each document's bucket ([PMC text-mining](https://pmc.ncbi.nlm.nih.gov/tools/textmining/)).

## A sealed parametric benchmark of ~80 certified instances replaces twelve tuned cases

### Why twelve cases cannot carry any claim

The dev set cannot support claims, however carefully it is fixed. Its cases were edited after results across Rounds 5–10. Three of its Split-1 transfer citations are unverified. And with four clusters, an exact paired permutation test has a minimum two-sided p of 2/2⁴ = 0.125.

Miller's evaluation guidance is unambiguous on three points ([Miller, "Adding Error Bars to Evals"](https://arxiv.org/abs/2411.00640)):
- **The independent problem is the unit of inference**, not the run.
- **Clustered standard errors can exceed naive ones by more than 3×.**
- **More questions beat more resamples.** Resampling only shrinks the within-question term.

Bowyer et al. add that CLT intervals badly underestimate uncertainty below a few hundred items. They recommend Wilson or Beta-Bernoulli intervals ([Bowyer et al., ICML 2025](https://arxiv.org/pdf/2503.01747)).

### How the generator works

The instance generator samples physical parameters per template inside documented regimes, in the style of GSM-Symbolic templating ([Mirzadeh et al., ICLR 2025](https://arxiv.org/html/2410.05229)). Examples of sampled parameters:
- for a PCM wall: required stored energy, flux, charge duration, superheat cap and thickness and mass caps;
- for a heat exchanger: duty, ΔP cap and length cap.

It draws parameter vectors by Sobol sampling and renders each one into a template-free Problem Card. A 2026 re-analysis showed that GSM-Symbolic's own sampling distribution confounded its comparison ([arXiv 2605.28700](https://arxiv.org/html/2605.28700)). FLBDS should therefore fix the sampling spec *before* drawing the test seed and report difficulty strata.

### How each instance is certified

Each candidate instance then goes through an automated satisfiability check:
1. A multi-start differential-evolution plus SLSQP optimiser runs against the **hidden eval** for every template whose physics preconditions plausibly apply.
2. The instance is kept only if the best feasible design has a minimum normalised margin within a target band, about 1.05–1.5×. That makes it neither trivial nor impossible.
3. The set of templates the optimiser could make feasible becomes the instance's ground-truth "feasible templates". This replaces the hand-authored `acceptable_templates`, so the list is now derived from physics rather than authored.
4. The certified reference design ships with the instance and must pass the same scorer call in CI. That one test would have caught DEV-M4.

One caveat: an optimiser that fails to find a feasible design does not prove infeasibility. Wherever possible, "infeasible template" labels should rest on closed-form bounds (first-law, ε≤1), and otherwise be reported as "not found feasible under budget B".

### Choice-sensitive instances

Instances should be deliberately stratified so that at least 48 of the 80 are **choice-sensitive**: at least one plausible template is certified feasible and at least one is not. Only there can biology or reasoning change the outcome once an optimiser handles the floats.

### Roles for the old cases

The 12 dev cases are frozen as a regression and development set. A small set of hand-authored documented-transfer cases (Split 1) is kept for qualitative rediscovery analysis only, where N can never be powered.

### How big the benchmark must be

Sample sizes come from note 03's derivations. They use Miller's paired formula with per-case standard deviations taken from the Round 11 data: SD 0.44 for dissimilar conditions like B0 vs Screen, SD 0.20 for close variants like B3 vs Screen with cross-condition r=0.90. A logit random-effects simulation checks them.

| Comparison type | SD of per-instance difference | δ=15 pt (α .05 / .01) | δ=20 pt | δ=25 pt |
|---|---|---|---|---|
| Close variants (e.g. Bio vs WrongBio, same loop) | ≈0.19 | 13 / 19 | 8 / 11 | 5 / 7 |
| Intermediate | ≈0.30 | 32 / 47 | 18 / 27 | 12 / 17 |
| Dissimilar (e.g. B0 vs loop) | ≈0.43 | 65 / 96 | 37 / 54 | 24 / 35 |

The simulation, with three cases per cluster and 50% shared variance, gives 80% power for a 15-point gain at N≈30–36 (α=.05) or N≈42–54 (α=.01). The current 12-case set has 21–37% power for that effect.

Instances from one template are correlated, so these counts must be inflated by the design effect 1+(m−1)ρ. With about 8 instances per template, **N=80 at K=5 seeds** covers the expected ~25-point primary effect at α=.01 for a template-level intra-class correlation of the paired differences up to about 0.2. It covers a 20-point effect only if that correlation is below about 0.07. The pilot (E1 below) estimates it, and the preregistration fixes final N by re-running the simulation, with a cap of 120. Generating more instances is cheap, and compute scales linearly. Keep T=0.7 and K=5: Miller warns against lowering temperature to cut variance, and more seeds buy far less than more instances.

### The statistics stack

The stack is fixed in advance:
1. **Primary test.** A paired exact sign-flip permutation test (or Pratt-Wilcoxon) on per-instance mean pass-rate differences.
2. **Robustness test.** A template-level permutation on 10 clusters. Its floor of 2/1024 clears Holm thresholds.
3. **Effect size.** The mean paired difference with a cluster bootstrap CI and Wilson per-condition intervals, plus the reported cross-condition correlation.
4. **Secondary model.** A binomial GLMM `pass ~ condition + (1|instance)`.
5. **Holm correction** across the three confirmatory hypotheses only.

McNemar on 60 run-pairs, as earlier rounds implicitly invited, is pseudo-replication.

Secondary outcomes:
- the continuous minimum normalised margin, which has more power than binary pass;
- EngDesign's all-K-seeds-pass robustness ratio ([EngDesign, NeurIPS 2025](https://arxiv.org/html/2509.16204v2));
- three gaming metrics: PVR_screen − PVR_eval in both directions, the fraction of passes with any parameter at a bound, and PVR by turn.

### Leakage controls enforced in code

Leakage control becomes structural rather than procedural:
- **Firewall.** An import-graph test lets only `scorer/` read `ground_truth_eval.json`.
- **Prompt scan.** A regex test scans every prompt and every feedback string for template IDs and hidden values.
- **Off-repo storage.** The test instances are generated from a held-out seed, SHA-256 hashed with a canary string, and stored off the public repo.
- **Preregistration.** A dated `PREREG.md` (git SHA, hypotheses, N, K, T, analysis script, exclusion and stopping rules) is committed *before* the test seed is drawn.
- **Re-seeding rule.** Any later change to the generator, templates, scorer or prompts requires a new preregistration version and a new seed.

## Two gates and six preregistered experiments fit in half a week's GPU quota

### Hypotheses mapped to experiments

The revised hypotheses move the research question from "do operators help" to two questions. Can a leakage-free verifier loop with an optimiser reliably produce verified TFP designs? And does the biological source change which mechanism gets chosen? The smallest effect size of interest is 10 points throughout.

| ID | Hypothesis (status) | Experiment | Data and code needed | Testable now? | Go / no-go |
|---|---|---|---|---|---|
| E0 | Regression: do the Round 11 effects survive the fixes? (descriptive) | Re-run B0, Screen loop and Oracle on the 12 dev cases × 5 seeds after fixes 1–11. B3 re-run only as a leak-free curiosity. | Existing runner plus fixes | **Yes, now** | If the Screen − B0 gap drops below 10 points after the fixes, the dev "doubling" was largely leakage. Investigate before building anything. |
| E1 | Pilot: generator works and variance is estimable (descriptive) | 20 pilot instances (not test) × 5 seeds × {B0, V10-core}. Estimate the per-instance difference SD and the template-level ICC; finalise N by simulation. | Generator, certificate, rewritten screen | Needs new components (generator, certificate) | Proceed if ≥95% of instances certify within the margin band and the screen relaxation test finds 0 false rejections in 10⁴ samples per template |
| H1 / E2 | V10-core (8 diverse samples × ≤3 screen-repair turns, screen-select) > B0 on PVR_eval (**primary, confirmatory**) | Sealed test, N≈80 × K=5 | E1 outputs, sealed test | After E1 | Go if Holm-adjusted p<0.01 *and* the CI lower bound is above +10 points. No-go means the headline claim fails; publish the negative result and stop expanding scope. |
| H2 / E3 | LLM chooses template, optimiser fits parameters > LLM-only V10-core at matched LLM tokens (**confirmatory**) | Same instances; arms: LLM-only, LLM-choice + DE/SLSQP, oracle-template + optimiser (CPU upper bound) | SciPy optimiser wrapper (~200 lines) | Optimiser arm needs new code; oracle bound runs on CPU | If the gain is ≥10 points, the optimiser becomes the default generator and the research quantity becomes template-choice correctness. If not, numeric tuning was not the bottleneck; keep LLM-only. |
| H3 / E5 | On choice-sensitive instances, a matched biological gold card raises the feasible-template-choice rate (and PVR_eval in the optimiser arm) vs a mechanism-mismatched WrongBio card; NoBio vs Bio tested for equivalence at ±10 points (**confirmatory; replaces proposal H5 and the NoBio test**) | ≥48 choice-sensitive instances × K=5 × {Bio, WrongBio, NoBio} | 16 hand-written gold cards from PMC primaries; WrongBio pairing table | Needs gold cards (human effort, no GPU) | Go (build M1's thin grounded path) only if Bio − WrongBio ≥ +10 points and is significant. If the CI excludes +10, narrow RQ2 to "biology supplies explanation and provenance, not performance", and do not build M1 for performance. |
| E4 | Compute allocation at matched tokens: 24×1 vs 8×3 vs 3×8, with pass@k-vs-tokens curves (secondary) | Same instances | Existing loop, batched | Yes once the test exists; can be piloted on dev now | Adopt the cheapest allocation within 5 points of the best. Literature predicts 8×3 ≥ the others ([Olausson](https://arxiv.org/abs/2306.09896v4); [SciDesignBench](https://arxiv.org/html/2603.12724)). |
| E6 | V10-core > B2-Code, where the model writes its own check code, sandboxed (secondary; proposal H2) | Same instances | Sandboxed executor | Moderate new code | Report only; supports the "external verifier, not self-written checks" claim |
| E7 | Replication of E2 and E3 key arms on one newer open Qwen-generation model (secondary) | Same instances | Model download and smoke test | Yes after download | Report only; tests whether conclusions are model-specific |

### Hypotheses dropped or deferred

- **Operators (proposal H3).** No longer confirmatory. The leak-free E0 B3 result is reported as an underpowered negative pilot.
- **Screen+ vs B3 (proposal H4).** Becomes the exploratory Oracle-vs-Screen contrast already in E0.
- **Retrieval baseline (proposal H1, B3 vs B1).** Deferred until retrieval exists. A flat BM25 table over the gold cards would make a cheap version possible after E5.
- **Mode B selection (H6) and RQ3 cross-domain retrieval.** Out of scope.
- **Precedent diversification.** Showing the model its prior designs and requiring a different template, inspired by BioSpark's precedent feedback and by the homogeneity of LLM concepts documented by [Ma et al.](https://codesign.berkeley.edu/pdfs/papers/ma-llmdiverse-jcise.pdf), is exploratory on mode-collapse instances only.

### Compute estimate

The compute estimate is anchored on measured Round 11 throughput: 0.79 GPU-hours for four 60-run conditions, about 296 s wall time per 3-turn condition on one H200 with Qwen2.5-72B-FP8, so about 5 s per run. The figures in the table assume today's unbatched runner. The feedback turns are issued one prompt at a time (`run_round11_benchmarks.py:526, 639, 770, 801`). Batching across instances and seeds should cut wall time several-fold, but that speed-up is unmeasured.

| Item | Runs or calls | Estimated GPU-h (unbatched) |
|---|---|---|
| E0 dev regression (3–4 conditions × 60 runs) | ~240 runs | ~1 |
| E1 pilot (20 × 5 × 2 conditions) | 200 runs | ~0.5–1 |
| E2 B0 + V10-core (80 × 5; V10-core ≈ 8× a single loop) | 400 + 400 runs | ~5 |
| E3 optimiser arms (LLM calls only for choice and initial point) | 400 runs | ~1.5 (CPU for optimisation) |
| E4 extra allocation arms (24×1, 3×8) | 800 runs | ~9 |
| E5 biology (≥48 × 5 × 3 cards, optimiser arm) | 720 runs | ~4.5 |
| E6 B2-Code | 400 runs | ~2 |
| E7 newer-model replication of E2 and E3 | ~1,200 runs | ~5–6 |
| **Total, with 1.5× contingency** | | **≈30–45 GPU-h** |

That is about half of one week's 90 GPU-h quota, and the project has used under 2 GPU-h across all rounds to date.

The deferred GRPO "B4" proposer is the only expensive item. SciDesignBench trained Qwen3-8B for 800 GRPO steps on 4×H100 or 8×A100, and RocketBench needed about 3,000 simulations. Neither reports wall time, so treat B4 as a multi-day 4-GPU job that could take one to two full weekly quotas. Schedule it only after H1–H3 are settled.

The CPU work is free in GPU terms but not trivial. It covers instance certification (multi-start optimisation × 10 templates × ~100 candidate instances) and the 10⁴-sample relaxation tests, and the server is shared at a load average around 118.

## Build order: harness first, biology last

### Phases

The v9 plan has about 22 of its 26 weeks left (Phase 0 ended around week 3; today is roughly week 4). V10 spends the first third making measurement trustworthy, because every later claim depends on it.

| Phase (weeks) | Build | Exit criterion |
|---|---|---|
| A (4–5) | Commit and tag Rounds 9–11; fixes 1–12; information-flow firewall and prompt-leak tests; delete `DEV_SPECS` in favour of card fields; two-call decoding with re-sampling; batched generation | E0 run and reported; all leak tests green |
| B (5–8) | Rewrite the screen as necessary-condition bounds with a `validity` block and `invalid_regime` verdict; Pint at input boundaries with plausibility bounds; Hypothesis property and metamorphic tests; separate the eval implementation; SciPy optimiser wrapper; parametric generator and satisfiability certificate | Relaxation test: 0 false rejections; E1 pilot passes; `PREREG.md` committed; test seed drawn and sealed |
| C (8–11) | Run E2, E3, E4, E6 once with the preregistered analysis script | H1 and H2 decided |
| D (6–12, parallel human track) | 16 gold cards hand-written from PMC OA primary papers (AskNature as pointer only); WrongBio pairing; ≥48 choice-sensitive instances confirmed | E5 run; H3 decided |
| E (12–20, conditional) | **Only if H3 = go:** thin M1 (BioCLIP 2 closed-list taxon with abstention → taxon-keyed PMC retrieval with Qwen3-Embedding-0.6B and reranker → existing extractor plus ChatExtract-style value verification), evaluated on ~48 photos of the 16 organisms and against the gold cards. **If H3 = no-go:** E7, B4 GRPO, or a deeper TFP template set instead. | M1 card precision measured on 50–100 hand-checked values before any end-to-end claim |
| F (20–26) | Verifier audit Packet A (two raters, κ) if raters exist; writing; release of the generator spec (not the sealed instances) | Paper claims limited to what H1–H3 decided |

### Retrieval and extraction choices, if Phase E runs

Two choices come from the literature:
- **Embedder.** Qwen3-Embedding runs natively in vLLM ([Qwen3 Embedding](https://arxiv.org/html/2506.05176v3)), which avoids training the planned three-head encoder.
- **Value extraction.** The best published LLM value-extraction pipeline reached about 91% precision and 84–88% recall with GPT-4 plus verification follow-ups ([ChatExtract, Nat. Commun. 2024](https://nature.com/articles/s41467-024-45914-8.pdf)). An open 72B model should be expected to do worse until measured.

## What the evidence does not support

### Claims to narrow

Several proposal claims need narrowing now, regardless of what the experiments show:

- **"Feedback without biology or operators raised the pass rate from 28% to 55%."** These numbers were produced while the screen leaked the acceptable-template list and defaults filled missing fields. They must be re-stated after E0.
- **"Physics-verified."** This should become "passes hand-written lumped and 1D/2D TFP checks within declared validity regimes". The proposal's "≥3 textbook problems within 1%" standard is code verification, not validation in the ASME V&V 20 sense, and no template has a validation data set.
- **"Operators" as a contribution.** This has no support from the project or the literature. Operators should leave the contribution list. The surviving idea is the deterministic dimensionless-group regime check, which is new to bio-inspired design tooling as far as the notes could find, but untested.
- **"From biological images."** The title promises something the system does not do. No image path exists, and the vision literature says a VLM should only label coarse descriptors and re-rank a specialist's taxa. Mechanism claims from pixels are unreliable: open models score about 47–50% on expert microscopy MCQs, and half of all errors are perception errors ([MicroVQA, CVPR 2025](https://arxiv.org/html/2503.13399v1)). Until E5 and Phase E succeed, the honest framing is text- or taxon-conditioned generation, with images as future work.
- **Mode B, the thesaurus, the novelty classes, the sketches and the "100% template preservation" figure.** Mode B and the thesaurus should be relabelled future work. The novelty classes and sketches have no evaluation behind them. The "100% template preservation" and "Operator T1 proved causally effective" statements should be retracted outright.
- **Scope beyond TFP.** None of this transfers beyond thermal, fluid and porous media, as the proposal already concedes.
- **Expert analogical-validity ratings.** These remain contingent on recruiting raters. None are recorded, and agent-written reviews have been shown not to match the raw transcripts.

### Uncertainties that remain even after V10

**The biology question may come back null.** In V10 that is a legitimate, publishable answer, because the design isolates it cleanly.

**The optimiser changes what PVR means.** With an optimiser in the loop, a high PVR largely measures template choice plus optimiser success. Results must therefore always be reported alongside the LLM-only arm and the oracle-template upper bound, or the system's contribution will be overstated.

**The design choices are inferred, not directly tested.** No published study compares LLM float-tuning against LLM-choice-plus-optimiser on lumped thermal design. None measures LLMs *selecting among pre-verified reduced-order models*, and none uses Qwen2.5-72B in a simulator loop. The V10 design choices are inferences from adjacent domains: code, hyperparameter optimisation, equation discovery and circuits.

**The steelman for keeping operators.** One could argue operators are the project's novelty, so they deserve another chance on a better benchmark. The rebuttal: they can only show an effect on choice-sensitive instances. E5's design already tests whether *any* structured mechanism information changes choice. If it does, an operator-style hint can be added as one more arm at near-zero cost. If it does not, operators have no route to an effect.

## Conclusion

FLBDS's problem was never a lack of architecture. Its problem was that measurement could not yet tell good components from bad, and every unmeasured module added more confounds. The most important change in V10 is not removing operators, the knowledge graph and Mode B. It is that the benchmark now defines its own ground truth from physics: an optimiser-certified feasible-template set replaces the authored acceptable list, so leaking the answer and building unsatisfiable cases both become structurally impossible.

That same move turns the project's central question into something testable for the first time. Once an optimiser handles the floats, the only thing left for the LLM, and for the biology, to contribute is the choice of mechanism. A clean positive on H3 would be a stronger and more novel result than the original proposal could have produced. A clean null is still publishable, and it costs only a few GPU-hours and sixteen hand-written cards to find out.
