# 03 — Evaluation methodology for a small, leakage-free benchmark of verified engineering design generation (FLBDS redesign)

Scope note: written against `00_project_digest.md` (12 dev cases = 4 clusters × 3 splits, 5 seeds, T=0.7, binary PVR_eval; observed B0 30%, Screen-only 56.7%, B3 50%). Items marked **[D]** are my own derivations or a simulation I ran (scripts: `/private/tmp/claude-501/-Users-abhishektripathi--claude-spares-spare-64Z6Sm/7ef9597c-7102-4814-8f7a-3f81ae4b796d/scratchpad/power.py` for the empirical SDs and normal-approximation table, and `/private/tmp/claude-501/-Users-abhishektripathi--claude-spares-spare-64Z6Sm/7ef9597c-7102-4814-8f7a-3f81ae4b796d/scratchpad/power_sim.py` for the simulation; numpy/scipy, seed 0; the scratchpad is temporary). They are not literature claims.

## Q1. Statistical power for pass-rate comparisons with clustered data (cases × seeds): which tests, and how many cases are needed to detect 15–25 pt differences?

### Takeaway
The unit of inference has to be the independent problem instance (or the cluster, if instances share a mechanism), never the run. Seeds reduce noise within a case but do not add degrees of freedom. With paired per-case differences, finding a 20 pt gain between conditions that behave quite differently (like B0 vs a feedback loop) needs roughly 35–55 independent cases. Finding a 15 pt ablation between closely related loop variants needs roughly 13–20. Four clusters can never reach p<0.05, and at least 6 independent units are needed before an exact paired test can.

### Cited Findings
- Miller (Anthropic), "Adding Error Bars to Evals" (arXiv 2411.00640, Nov 2024), makes five recommendations. (1) Use the CLT standard error. (2) Use clustered standard errors when questions come in related groups. (3) Reduce variance by resampling answers. (4) Compare models with question-level *paired* differences. (5) Use power analysis to decide whether an eval can detect the effect of interest. — [Miller 2024](https://arxiv.org/abs/2411.00640)
- On real Anthropic-model data, clustered SEs were 3.05× the naive SE on DROP, 1.10× on RACE-H and 1.88× on MGSM: "clustered standard errors can be over 3X larger than naive standard errors". Miller suggests reporting the cluster count alongside the question count. — [Miller 2024](https://arxiv.org/abs/2411.00640)
- Resampling (K answers per question, scored as the per-question mean) shrinks only the within-question term, Var(s_i)=σ²_i/K. In Miller's uniform-difficulty binary example, Var(μ̂|K)=Var(μ̂|K=1)·(1+2/K)/3. Going to K=2 cuts variance by 1/3, K=4 by 1/2, K=6 by 5/9, and the ceiling is 2/3. "Computing a pooled standard error across all KN answers will be inconsistent." — [Miller 2024](https://arxiv.org/abs/2411.00640)
- Miller warns against lowering temperature to cut variance ("Don't touch the thermostat!") unless the goal is to study the model at that temperature. — [Miller 2024](https://arxiv.org/abs/2411.00640)
- Pairing: Var(paired diff) = Var(unpaired) − 2Cov(x_A,x_B)/n. Paired differences are "a 'free' reduction in estimator variance", so report the paired SE and the cross-condition score correlation. A paired-and-clustered SE formula is given for grouped questions. — [Miller 2024](https://arxiv.org/abs/2411.00640)
- Sample-size formula (paired, K_A and K_B samples per question): n = (z_{α/2}+z_β)²(ω² + σ²_A/K_A + σ²_B/K_B)/δ², with ω² = Var(x_A)+Var(x_B)−2Cov(x_A,x_B). Worked example: ω²=1/9, δ=3 pts, α=0.05, power 80% gives n≈969, hence "new evals should contain at least 1,000 questions". Inverting the formula with n=198 and Corr=0.5, raising K from 1 to 10 cuts the MDE from 13.2% to 7.5%. Cluster-adjusted versions are in Miller's Appendix C. — [Miller 2024](https://arxiv.org/abs/2411.00640)
- Bowyer, Aitchison & Ivanova (ICML 2025 position paper) argue that CLT-based intervals "perform very poorly, usually dramatically underestimating uncertainty" for benchmarks below a few hundred datapoints. They recommend Wilson score intervals or Beta-Bernoulli Bayesian intervals and provide the `bayes_evals` library. — [Bowyer et al. 2025 (PMLR v267)](https://proceedings.mlr.press/v267/bowyer25a.html); [arXiv 2503.01747](https://arxiv.org/pdf/2503.01747)
- Card et al. (EMNLP 2020) conclude that underpowered experiments are common in NLP. On several GLUE tasks, most comparisons to state of the art are not adequately powered. A typical 2,000-sentence MT test set has about 75% power to detect 1 BLEU. "The most typical experimental design for human rating studies will be underpowered to detect small model differences." They supply simulation-based power-analysis notebooks, including a mixed-effects one for human evaluation. — [Card et al. 2020](https://web.stanford.edu/~jurafsky/pubs/2020.emnlp-main.745.pdf); [code](https://github.com/dallascard/NLP-power-analysis)
- Madaan et al. (2024) quantify seed variance and bootstrap CIs for benchmarks and note that variance is rarely reported even though it determines "whether differences in performance are meaningful". IRT-style methods from human testing "struggle to meaningfully reduce variance". — [Madaan et al. 2024](https://arxiv.org/abs/2406.10229)
- EngDesign (NeurIPS 2025 D&B) runs each task in 3 independent trials. It reports a "reasoning robustness" ratio: tasks where all 3 trials pass divided by tasks where at least one passes (o1 0.62, o3 0.61, Gemini-2.0-Flash 0.20). The main table shows only mean pass rates. — [EngDesign, arXiv 2509.16204](https://arxiv.org/html/2509.16204v2)

### Inferences
- **[D] Exact-test floor with few clusters.** An exact paired sign-flip permutation test on C independent units has a minimum two-sided p of 2/2^C. That gives C=4 → 0.125 (the digest's figure), C=5 → 0.0625, C=6 → 0.031 and C=8 → 0.0078. Holm at α=0.01 for the first of 5 hypotheses (0.01/5=0.002) needs C≥10 (2/1024≈0.002), and at α=0.05/5=0.01 it needs C≥8. This matches the proposal's own note that "≥8 informative clusters" are needed. Ties (zero differences) remove clusters, so the *informative* count is what matters.
- **[D] Variance inputs estimated from FLBDS R11 per-case data** (12 cases, K=5):
  - Screen − B0: mean per-case difference +0.267, SD 0.438, cross-condition per-case correlation r=0.29.
  - B3 − Screen: mean −0.067, SD 0.197, r=0.90.
  - Closely related conditions are therefore highly correlated, and pairing buys a lot.
- **[D] Normal-approximation sample sizes (Miller eq. 9 using the observed SD of per-case differences, which already includes the K=5 seed noise; α two-sided, 80% power):**

  | SD of per-case diff | δ=15 pt | δ=20 pt | δ=25 pt |
  |---|---|---|---|
  | 0.19 (similar conditions, e.g. B3 vs Screen) | 13 (α=.05) / 19 (α=.01) | 8 / 11 | 5 / 7 |
  | 0.30 (intermediate) | 32 / 47 | 18 / 27 | 12 / 17 |
  | 0.43 (dissimilar, e.g. B0 vs Screen) | 65 / 96 | 37 / 54 | 24 / 35 |

  These are the number of *independent* cases. If cases are nested in mechanism clusters with intra-cluster correlation ρ and m cases per cluster, multiply by the design effect 1+(m−1)ρ (standard survey-sampling result; I did not fetch a citation). For example, m=3 and ρ=0.5 doubles the requirement. The dev SDs are optimistic because dev cards were tuned.
- **[D] Simulation check.** Setup:
  - Logit random-intercept model: case SD τ=2.0 on the logit scale, case×condition interaction SD 0.8, baseline pass rate 30%, K=5 seeds per case and condition.
  - Test: paired one-sample t-test on per-unit mean differences, 4,000 reps per cell (script `power_sim.py` in the scratchpad).
  - Implied per-case difference SD ≈0.28 and cross-condition correlation 0.69, i.e. the "intermediate" row above.
  - "Clustered" means 3 cases per mechanism cluster with 50% of case variance shared, analysed at the cluster level.

  Power by number of cases N:

  | True mean gain | N=12 | 24 | 36 | 48 | 60 | 90 |
  |---|---|---|---|---|---|---|
  | 11 pt, independent, α=.05 / .01 | .23/.06 | .47/.22 | .65/.40 | .79/.54 | .87/.67 | .97/.89 |
  | 11 pt, clustered ×3, α=.05 / .01 | .14/.03 | .41/.14 | .59/.28 | .75/.46 | .84/.60 | .96/.86 |
  | 15 pt, independent | .37/.13 | .71/.43 | .87/.67 | .95/.84 | .99/.93 | 1.0/.99 |
  | 15 pt, clustered ×3 | .21/.04 | .60/.27 | .83/.54 | .92/.74 | .97/.87 | 1.0/.99 |
  | 19 pt, independent | .58/.25 | .91/.68 | .98/.91 | .99/.98 | 1.0/1.0 | 1.0/1.0 |
  | 19 pt, clustered ×3 | .32/.07 | .81/.44 | .96/.80 | .99/.94 | 1.0/.99 | 1.0/1.0 |

  Under these assumptions, 80% power for a ~15 pt gain needs N≈30–36 at α=.05 and N≈42–54 at α=.01 (Holm-level). A ~20 pt gain needs N≈20–24 at α=.05 and N≈30–36 at α=.01. The current 12-case dev set has 37% power for 15 pt even when cases are treated as independent, and 21% when they are clustered.
- **Recommended test stack, in order of priority:**
  1. *Primary:* paired exact sign-flip permutation test (or Pratt-Wilcoxon) on per-case mean pass-rate differences, with N = independent cases. If cases share a parent mechanism, aggregate to the cluster first.
  2. *Effect size + CI:* mean paired difference with a case-level (or cluster-level) bootstrap or Wilson/Beta intervals per Bowyer. Report the cross-condition correlation, as Miller advises.
  3. *Model-based secondary:* binomial GLMM `pass ~ condition + (1|case)`, adding `(1|cluster)` only if there are ≥ ~10 clusters (my judgement: variance components from 4 clusters are not identifiable in practice).
  4. *McNemar* is valid only for one paired binary outcome per independent unit, e.g. K=1 or a per-case "majority of seeds passed" indicator. Applying it to 60 run-pairs treats seeds as independent, which is exactly the pseudo-replication Miller warns about. Seed s of condition A and seed s of condition B are not naturally paired, so pairing belongs at the case level.
  5. *Cluster bootstrap* with fewer than ~10 clusters gives anti-conservative intervals. This is an econometrics result (wild cluster bootstrap literature) that I did not fetch, so treat it as unverified here.
- **Seeds:** with K=5 the within-case term is already small relative to between-case heterogeneity (per Miller's 2/K ≪ 1 heuristic with uniform difficulty). Going from 5 to 10 seeds buys far less than going from 12 to 36 cases. Keep T=0.7 fixed and do not lower T to reduce noise (Miller).
- **Practical target for FLBDS:**
  - About 40–60 independent, parametrically generated test instances for the headline comparison (B0 vs feedback loop, or the full system vs B0), at K=5.
  - At least 24–36 instances for any component ablation expected to be 15–20 pts.
  - Preregister one primary hypothesis so Holm does not eat the power.
  - With 4–5 hypotheses under Holm, plan for α_eff≈0.01 (the α=.01 column).

### Gaps
- I did not fetch Miller's Appendix C (cluster-adjusted sample-size formula) text beyond confirming that it exists. The design-effect multiplier above is a standard approximation and is not quoted from Miller.
- No source found that gives empirical intra-cluster correlations for engineering-design LLM benchmarks. They need to be estimated from FLBDS's own pilot.
- No fetched source on small-cluster bootstrap failure (e.g. Cameron, Gelbach & Miller 2008). This is listed as an inference only.

## Q2. Procedurally/parametrically generated instances to scale N; what engineering-design LLM benchmarks exist and how do they score?

### Takeaway
Credible design and science benchmarks use expert-authored seed problems with executable checkers and partial-credit rubrics. N is scaled either by decomposing problems or by templating parameters (GSM-Symbolic style). Templated instances expose large performance variance and contamination. For FLBDS, the cheapest route to N≈40–100 is to sample physical parameters per template inside documented regimes. A reference-design solver must certify each instance satisfiable before freezing it, and instances from one template must be treated as correlated.

### Cited Findings
- **EngDesign** (NeurIPS 2025 D&B):
  - Contents: 101 design tasks over 9 engineering domains (OS, computer architecture, control, mechanical, structure, digital HW, analog IC, robotics, signal processing) with 473 gradable items. 67 tasks are fully open-source ("EngDesign-Open") and 34 need MATLAB/Cadence.
  - Construction: graduate students and researchers authored tasks in a fixed format (description, rubric, evaluation code, reference solution). An o4-mini pre-test checked prompt sufficiency, a first-round review sorted tasks into Accept/Revise/Reject, and faculty experts reviewed a second round.
  - Scoring: each task has an executable pipeline returning pass/fail, a 0–100 rubric score and a log, using simulators such as SPICE and FEA.
  - Results: best overall pass rates are o3 34.38%, o4-mini-high 34.04% and GPT-4o 15.68%, and Analog IC is 0% for all models. Iterating with feedback, o3 reaches "almost a 60% pass rate after ten iterations" on a 71-task subset.
  - Failure modes: domain-knowledge errors 30.7–33.3% and constraint violations 25.2–36.0%.
  - The paper describes no contamination controls and no procedural variants. — [EngDesign](https://arxiv.org/html/2509.16204v2); [NeurIPS page](https://neurips.cc/virtual/2025/poster/121598)
- **DesignQA** (Doris et al., MIT; ASME JCISE 2025): 1,451 multimodal Q&A items built from the FSAE rule document and MIT Motorsports CAD and drawings. Models struggle with rule retrieval, CAD component recognition and drawing analysis. It is limited to one rule document. — [arXiv 2404.07917](https://arxiv.org/abs/2404.07917); [ASME JCISE](https://asmedigitalcollection.asme.org/computingengineering/article/25/2/021009/1210215/DesignQA-A-Multimodal-Benchmark-for-Evaluating)
- **SciCode** (NeurIPS 2024 D&B): 80 main problems decomposed into 338 subproblems with scientist-written gold solutions and test cases over 5 natural-science domains. Problems were chosen to avoid overlap with public data. The best model solved 4.6% of main problems in the realistic setting in the original paper and 7.7% in a later version. Decomposition multiplies gradable items, but subproblems are nested within main problems. — [SciCode](https://arxiv.org/abs/2407.13168v1); [project](https://scicode-bench.github.io)
- **GSM-Symbolic** (Mirzadeh et al., Apple, ICLR 2025) generates many instances from symbolic templates. LLMs "exhibit noticeable variance when responding to different instantiations of the same question". Performance drops relative to GSM8K, which the authors say may hint at contamination. Variance grows with clause count, and adding one irrelevant clause (GSM-NoOp) causes drops of up to 65%. — [arXiv 2410.05229](https://arxiv.org/html/2410.05229)
- A 2026 re-analysis ("The Importance of Being Statistically Earnest") argues that GSM-Symbolic's conclusions are statistically premature. Its sampled instances had a shifted distribution of larger integers than GSM-Base, so the parameter-sampling distribution itself confounded the comparison. — [arXiv 2605.28700](https://arxiv.org/html/2605.28700)
- **Conceptual design generation with LLMs** (Ma et al., Autodesk Research, 2023) compared LLM-generated and crowdsourced concepts on conceptual design problems. It is a precedent for concept-level (not parameter-level) evaluation. — [arXiv 2306.01779](https://arxiv.org/abs/2306.01779)
- **VLMs for engineering design review** (Picard et al., AI Review 2025) evaluates GPT-4V across concept-to-manufacturing tasks, including replicating a human-rater design-similarity study. — [Springer](https://link.springer.com/article/10.1007/s10462-025-11290-y)

### Inferences
- **Generator design for FLBDS:** for each of the 10 TPL templates, define a parameter-sampling spec (for example, PCM wall: required stored energy, ambient amplitude, superheat cap, thickness limit; HX: duty, ΔP cap, footprint). Use documented physical ranges, then:
  1. Draw instances by Latin hypercube or Sobol sampling.
  2. Solve each instance with a solver-optimised reference design (the digest already has eval functions) and keep it only if the best feasible design has margin within a target band, e.g. 1.05–1.5× (not trivially satisfiable, not impossible). This automates the "P10 satisfiable as scored" check that DEV-M4 failed.
  3. Stratify difficulty by the reference margin and by which constraint binds.
  4. Freeze the instances and hash them before any model sees them.
- The GSM-Symbolic critique implies the sampling distribution must be fixed *a priori* and shared across conditions, and difficulty strata must be reported. Instances generated from one template are correlated, so the template (or mechanism cluster) is the clustering unit for Q1's design-effect correction.
- **Mixed portfolio:** about 60–100 parametric instances (cheap, giving power for the loop/ablation comparisons), plus about 12 hand-authored "documented transfer" cases kept only for qualitative and rediscovery analysis (where N cannot be powered).
- Partial-credit margins (EngDesign-style 0–100 rubric, or FLBDS's normalised min-margin) should be a secondary continuous outcome. A continuous outcome has much higher power than binary pass rates at the same N (a general statistics fact, not sourced here).
- Like EngDesign, report pass@1 and an all-K-seeds-pass robustness ratio.

### Gaps
- I did not find a published *parametric generator* benchmark specific to thermal/fluid design. MechAgents and the "LLMs for engineering design" surveys did not surface in searches, and the EngDesign paper's last ~70k characters (appendix) were not read.
- No source gives the number of parametric instances per template needed to avoid template-level overfitting.

## Q3. Leakage and contamination controls (preregistration, frozen hashes, held-out splits, screen vs scorer separation, blinding)

### Takeaway
FLBDS's failures (hidden template in prompt, feedback revealing the acceptable list, cases edited after results) are the classic garden-of-forking-paths and test-leakage problems. The fix is procedural:
- a written preregistration with one primary hypothesis;
- a generator-produced test set, hashed and sealed before any run;
- an information-flow firewall enforced in code (the generator and screen may import only Problem-Card fields; the scorer alone reads the ground truth);
- schema "no-default" rules so empty fields fail.

### Cited Findings
- SciCode chose problems to avoid overlap with public datasets as its contamination control. — [SciCode](https://arxiv.org/abs/2407.13168v1)
- LiveBench (ICLR 2025, "contamination-limited") limits contamination by releasing new questions monthly with objective, automatically scored ground truth. Top models stayed below 65–70% accuracy. — [LiveBench](https://arxiv.org/abs/2406.19314v2); [GitHub](https://github.com/LiveBench/LiveBench)
- GSM-Symbolic's drop on freshly instantiated templates versus the original GSM8K items is interpreted as possible contamination of static items. Regenerating instances is therefore itself a contamination probe. — [GSM-Symbolic](https://arxiv.org/html/2410.05229)
- EngDesign pre-tests every prompt with an LLM for sufficiency and uses two-stage expert review before inclusion, but describes no contamination controls. — [EngDesign](https://arxiv.org/html/2509.16204v2)
- Madaan et al. note that benchmarks are now used to make training choices, so dev-set reuse inflates claims unless variance is quantified. — [Madaan et al. 2024](https://arxiv.org/abs/2406.10229)

### Inferences (concrete controls for a 1–2 person team)
1. **Preregistration (OSF or a dated, committed `PREREG.md` with git SHA):** primary hypothesis, primary metric, N, K, T, analysis script, exclusion rules and stopping rule. Write it *before* generating the test seed. Card et al.'s power-analysis notebooks and Miller's eq. 9 provide the N justification.
2. **Sealed test generation:** generate the test instances from a held-out RNG seed. Store only the SHA-256 manifest in the repo and keep the instance files off the public GitHub repo (the digest says the repo is public). Store a canary string in the files so leakage into future training data is detectable.
3. **Dev vs test roles:** dev cards may be edited freely. Any change to the generator, templates, scorer or prompts after the test seed is drawn requires a new preregistration version and a new test seed. Log every run, including discarded ones.
4. **Information-flow firewall in code:**
   - The scorer module is the only code allowed to read `ground_truth_eval.json`. Enforce this with an import-linter rule or a unit test that greps for ground-truth access outside `scorer/`.
   - Screen feedback must be computed from Problem-Card constraints only: no "acceptable templates" list and no exact target values. This is the leakage pattern flagged in `split2_harder.md`.
   - Add a leakage unit test: the prompt and feedback strings, run through a regex for template IDs or GT values, must find none.
5. **No silent defaults:** the scorer must reject any design missing a required decision variable (Pydantic `Field(...)` with no default for scored parameters), and log "defaulted fields" as a failure category. Scorer spec overrides (`DEV_SPECS`) must come from the frozen Problem Card, never from a second hard-coded table, and a test must assert card/scorer equality.
6. **Blinding:** human raters and any LLM judge see anonymised, condition-shuffled outputs with a hidden key held by a script. Analysts run the preregistered script once on the sealed test. Agent-written transcript "reviews" are not evidence: each claimed parameter must be machine-extracted from the raw JSON (the §5.4 discrepancy).
7. **Satisfiability certificate:** each frozen instance ships with a reference design that passes the *same* scorer call (a CI test), which would have caught DEV-M4.

### Gaps
- I found no fetched literature specifically on preregistration practice in ML benchmark papers, and did not fetch the canary-string convention (BIG-bench). These are presented as standard practice without a citation here.

## Q4. Evaluating creativity and novelty of design concepts (Shah metrics, CAT, LLM-as-judge reliability, patent-based novelty)

### Takeaway
Use objective set-level metrics (Shah novelty and variety over a coded attribute tree) for the bulk of the evaluation. Use a small expert CAT panel as the gold standard on a stratified subset. Use an LLM judge only after it is shown to agree with that panel on held-out items. The evidence says LLM judges reach moderate, metric-dependent agreement (often fine for novelty or uniqueness, weaker for usefulness/quality and feasibility) and must be calibrated per domain.

### Cited Findings
- Shah, Smith & Vargas-Hernandez (2003, *Design Studies*), "Metrics for measuring ideation effectiveness", define novelty, variety, quality and quantity. These remain among the most-used metrics for technical design ideation. — [Shah et al. 2003](https://www.researchgate.net/publication/222672623_Metrics_for_measuring_ideation_effectiveness); [Shah et al. 2000 (ASME)](https://www.researchgate.net/publication/245366249_Evaluation_of_Idea_Generation_Methods_for_Conceptual_Design_Effectiveness_Metrics_and_Design_of_Experiments)
- Edwards, Tehranchi, Miller & Ahmed, "AI Judges in Design" (arXiv 2504.00938, 2025), test VLM judges against experts on uniqueness, creativity, usefulness and drawing quality. The best judge (text+image in-context examples plus reasoning) reached "expert-level agreement for uniqueness and drawing quality". It matched or beat trained novices on all metrics, meeting or exceeding the majority of novices in 6/6 runs for uniqueness and creativity and 5/6 for usefulness and drawing quality. The paper also notes that Shah-style algorithmic novelty can miss subjective nuance. — [arXiv 2504.00938](https://arxiv.org/abs/2504.00938); [PDF](https://arxiv.org/pdf/2504.00938)
- Zhang, Han & Ahmed-Kristensen (ICED25, *Proc. Design Society* 5:1773–1782): 10 LLMs rated 78 design ideas (37 human, 41 GPT-4) for novelty and usefulness on 7-point scales against 2 experts with over 10 years' experience.
  - Expert agreement was Cronbach α=0.80 for novelty and 0.92 for usefulness.
  - A structured procedure (four yes/no sub-questions and a rule table) reduced inter-LLM SD from 0.970 to 0.822 for novelty and from 0.946 to 0.881 for usefulness.
  - No LLM–expert ICC or κ was reported, so the agreement claim is weak. — [Cambridge Core](https://www.cambridge.org/core/journals/proceedings-of-the-design-society/article/exploring-the-use-of-llms-to-evaluate-design-creativity/B7D16E2612A33C0A9DE1B1922E054639)
- A hackathon creativity study found the best LLM judges reached Cohen's κ≈0.59 with humans on novelty, while humans agreed only weakly with each other. The authors recommend human-AI collaboration. — [arXiv 2503.04290](https://arxiv.org/pdf/2503.04290)
- An LLM-judge CAT adaptation for poetry reports a correlation of about 0.38 with expert ratings. — [Sawicki et al., arXiv 2502.19064](https://arxiv.org/pdf/2502.19064v1)
- Advertising creativity: weak, inconsistent LLM–human correlations and judge-specific biases. Automated judges "cannot substitute" for humans. — [arXiv 2509.09702](https://arxiv.org/pdf/2509.09702v1)
- Scientific novelty: human–LLM agreement as low as 22%. — ["On the Limits of LLM-as-Judge for Scientific Novelty Assessment", arXiv 2606.12071](https://arxiv.org/pdf/2606.12071)
- Contrary evidence: with ChatGPT embedded as one member of a CAT panel, its scoring was internally consistent and comparable to expert judges across repeated runs. — [Addis et al. 2026](https://iris.uniroma1.it/retrieve/50a0314b-4b5e-4383-87d0-ca7faa1ec58b/Addis_Evaluating_2026.pdf)
- The CAT (Amabile) relies on independent expert judges. Reported inter-rater reliability is generally .80–.90 and rises with more judges.
  - Novice–expert correlation was .71 for short fiction, with novices far less consistent.
  - Kaufman et al. (2008) found novices had low reliability and did not match experts.
  - Silvia argues that CAT validity "is completely dependent on the use of expert judges".
  - Cseh & Jeffries' critical review still calls CAT a "gold standard". — [Kaufman/Baer CAT papers (Rider)](https://www.rider.edu/sites/default/files/2024-05/ExpertiseDomains%26CAT.pdf); [Cseh & Jeffries](https://knowledge.lancashire.ac.uk/id/eprint/28402/1/28402%20CsehJeffries_A%20scattered%20CAT%20A%20critical%20evaluation%20of%20the%20Consensual%20Assessment%20Technique%20for%20creativity%20research.pdf)

### Inferences
- **For FLBDS, novelty is secondary to PVR.** Recommended protocol:
  1. *Objective layer:* code every verified concept into a fixed attribute tree (template/effect, working medium, resource used, flow topology, operating mode). Compute Shah novelty (rarity of each attribute value within the pooled concept set across all conditions) and variety (genealogy-tree spread) automatically, which is cheap and reproducible.
  2. *Prior-art layer:* nearest-neighbour retrieval against patents and literature (for example, BigPatent F/E already in the corpus), with a fixed similarity threshold and manual check of the top-3 for a subset. Patent-based novelty checks were not covered by the sources I fetched.
  3. *Gold layer:* a 2–3 expert CAT panel rates a stratified, blinded subset (for example, 60 concepts) on novelty, usefulness and analogical validity.
  4. *LLM judge:* calibrate on half the gold subset and validate on the other half. Report ICC or Krippendorff α with each expert and with the expert mean. Only use the judge at scale if judge–expert agreement ≥ expert–expert agreement (the Edwards et al. "AI judge vs novice" framing). Otherwise report human ratings only.
- Use Zhang et al.'s decomposition into sub-questions plus a rule table for the judge prompt: it reduces judge variance, but validity still has to be shown against the experts.
- Never let the generator's own model family judge its outputs without validation (self-preference). This general LLM-judge caution was not fetched here.

### Gaps
- No fetched source reports LLM–expert agreement specifically for *physics-verified engineering concepts* or bio-inspired analogies. The closest are sketches (Edwards et al.) and text ideas (Zhang et al.).
- Numeric ICC values from Edwards et al. were not on the abstract page.
- No source fetched on patent-embedding novelty checks (e.g., PatentsView / USPTO-based novelty scores).

## Q5. Human evaluation protocols at small scale (number of raters, ICC / Krippendorff α)

### Takeaway
For a 1–2 person team, the realistic protocol is 2–3 qualified independent raters on a blinded, stratified subset (about 40–60 items). Raters should calibrate on dev items first. Report Krippendorff α (or ICC(2,k) for continuous scores) with a bootstrap CI, using α≥0.80 as reliable and 0.667–0.80 as tentative. Plan the human-rated comparison with a mixed-effects power simulation, because typical human-eval designs are underpowered.

### Cited Findings
- Krippendorff's decision bands: α ≥ 0.800 reliable; 0.667 ≤ α < 0.800 tentative conclusions only; below 0.667 discard. — [Wikipedia: Krippendorff's alpha](https://en.wikipedia.org/wiki/Krippendorff%27s_alpha)
- These cutoffs are often misapplied. Krippendorff and others advise that the criterion "is unlikely to suit all studies". — [Empathic Conversations, arXiv 2205.12698](https://arxiv.org/pdf/2205.12698)
- Two design experts rating 78 ideas reached Cronbach α=0.80 (novelty) and 0.92 (usefulness), then reconciled by discussion. That is a feasible small-scale benchmark for what 2 raters can achieve. — [Zhang et al., ICED25](https://www.cambridge.org/core/journals/proceedings-of-the-design-society/article/exploring-the-use-of-llms-to-evaluate-design-creativity/B7D16E2612A33C0A9DE1B1922E054639)
- CAT reliability is typically .80–.90 and increases with more judges. Studies with 1–3 expert judges cannot properly assess reliability, and novices are less reliable than experts. — [Kaufman/Baer (Rider)](https://www.rider.edu/sites/default/files/2024-05/ExpertiseDomains%26CAT.pdf)
- Card et al.: the most typical human-rating design is underpowered for small differences. They provide a mixed-effects simulation notebook (items × raters) for planning. — [Card et al. 2020](https://web.stanford.edu/~jurafsky/pubs/2020.emnlp-main.745.pdf); [code](https://github.com/dallascard/NLP-power-analysis)
- Edwards et al. show that 3 trained novices can serve as a comparison baseline against which an AI judge is tested for expert-equivalence. — [arXiv 2504.00938](https://arxiv.org/abs/2504.00938)

### Inferences
- **Protocol for FLBDS (about 10–15 rater-hours each):**
  - *Raters:* 2 thermal/fluids engineers plus 1 biology/BID-literate rater for analogical validity.
  - *Calibration:* 10 dev items, discussed and not scored.
  - *Scoring:* 48 test items stratified by condition (e.g. 12 each from B0, loop, full, WrongBio), blinded and randomised, rated independently on a 1–5 anchored rubric.
  - *Reliability:* compute Krippendorff α (interval) and ICC(2,k), each with a 1,000-sample item bootstrap CI.
  - *Analysis:* if α<0.667, report the dimension as unreliable and drop the hypothesis (the v9 contingency for H5). Run the condition test on item means with a paired or mixed model `rating ~ condition + (1|item) + (1|rater)`.
- The two-rater "Packet A" verifier audit (false assurance/rejection) is a binary agreement problem: report Cohen's κ and the rate at which the physics scorer and the humans disagree.
- If no external raters can be recruited, the honest fallback is to restrict claims to the machine-scored PVR and Shah metrics and to state that H5 is untested. Agent-written reviews must not be substituted for raters.

### Gaps
- I did not retrieve Koo & Li (2016) ICC interpretation bands (<0.5 poor, 0.5–0.75 moderate, 0.75–0.9 good, >0.9 excellent, as commonly cited) from a primary source. Verify before citing.
- No source gives a specific minimum rater count for engineering-concept rating. The "2–3 experts" figure is drawn from the CAT and design-study practice above.
