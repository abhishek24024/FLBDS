# LLM generation with simulator/verifier feedback loops for engineering and scientific design (2022 to Nov 2026): what works, and a minimal strong architecture for FLBDS

Scope note: this covers the FLBDS generation and verification core: the LLM proposes typed parameters, M5-Screen gives feedback, and M5-Eval scores in hidden. Biology retrieval, the thesaurus and the operators are out of scope except where evidence speaks to "prompted guidance vs external feedback".

Provenance tags:
- **[fetched]** means I read the page or the full paper's HTML this session.
- **[search]** means the claim comes from search-result abstracts or snippets. These are mostly abstract-level, so verify exact numbers before quoting them in a paper.

FLBDS numbers quoted below come from `00_project_digest.md`:
- B0 30%
- Screen-loop 56.7%
- Oracle (hidden-solver feedback) 55%
- B3 50%

---

## Q1. Self-refine vs external-verifier feedback, and how detailed the feedback should be

### Takeaway
Intrinsic self-correction (the model critiquing itself with no outside signal) gives little or negative gain on reasoning. Gains are reliable only when the feedback comes from an external, trustworthy signal: execution, a simulator, tests or tools. Prompted LLM critics or "guidance" text add little on top.

How detailed the feedback is matters less than whether it is correct. Per-target numeric feedback (achieved value, error, PASS/MISS) is the current standard in simulator benchmarks. Better-quality feedback is the main lever for repair.

### Cited Findings
- **Huang et al. (ICLR 2024), self-correction without feedback.** Intrinsic self-correction lowered GSM8K accuracy:
  - GPT-3.5 went from 75.9% to 74.7% after two rounds.
  - Llama-2 went from 62.0% to 36.5%.
  - GPT-3.5 flipped correct→incorrect 8.8% of the time vs incorrect→correct 7.6%.
  - With oracle correctness labels, GPT-3.5 reached 84.3%. So the bottleneck is *judging* correctness, not generating fixes.
  - A third-party summary reports CommonSenseQA 66.8% → 55.4% for GPT-3.5; I did not confirm this against the paper.
  - Sources: [Huang et al. 2023, arXiv 2310.01798](https://arxiv.org/abs/2310.01798), [ICLR poster](https://iclr.cc/virtual/2024/poster/18956) [search]. Exact baseline numbers vary between versions and summaries.
- **Kamoi et al. (TACL 2024), critical survey.** Three conclusions:
  - Self-correction is effective in tasks where reliable external feedback is available.
  - No prior work shows successful self-correction with feedback from *prompted* LLMs on general tasks.
  - Large-scale fine-tuning enables self-correction.
  - Many earlier positive results used "unfair evaluations that over-evaluate self-correction".
  - Source: [Kamoi et al. 2024, TACL 12:1417–1440](https://aclanthology.org/2024.tacl-1.78) [search].
- **Self-Refine.** Reports about 20% absolute average improvement across 7 tasks using the model's own feedback. These are mostly generation and preference tasks scored by GPT-4 or humans, not verifiable reasoning. This is the kind of setting Kamoi et al. criticise. Source: [Madaan et al. 2023, arXiv 2303.17651](https://arxiv.org/abs/2303.17651) [search, abstract-level].
- **Reflexion.** Verbal reflection on *external* signals (unit-test results, environment rewards) reached 91% pass@1 on HumanEval. Source: [Shinn et al. 2023, arXiv 2303.11366](https://arxiv.org/abs/2303.11366) [abstract-level; not re-fetched].
- **CRITIC.** LLMs check and revise their outputs by calling tools (search, code interpreter). The paper's framing is that external tool feedback is what makes self-correction work. Source: [Gou et al. 2023, arXiv 2305.11738](https://arxiv.org/abs/2305.11738) [abstract-level; not re-fetched].
- **LEVER.** Reranks sampled programs with a learned verifier that sees the *execution results*. This is selection with execution feedback, not repair. Source: [Ni et al. ICML 2023, arXiv 2302.08468](https://arxiv.org/abs/2302.08468) [abstract-level; exact gains not re-verified here].
- **Self-Debug (ICLR 2024).**
  - Up to +12% with unit-test feedback on TransCoder and MBPP.
  - +2–3% from code explanation alone on Spider, where no tests are available.
  - Matches or beats baselines that sample more than 10× as many candidates.
  - Source: [Chen et al. 2023, arXiv 2304.05128](https://arxiv.org/abs/2304.05128) [search].
- **LeDex.** Asking for an explanation of the unit-test feedback *before* refining raises refinement success over direct refinement. Source: [LeDex, arXiv 2405.18649](https://arxiv.org/html/2405.18649v2) [search].
- **Feedback quality is the bottleneck (Olausson et al., ICLR 2024).** Artificially improving feedback quality "significantly improves the efficacy of self-repair". Replacing GPT-4's own explanations with a human programmer's improves repair significantly. Source: [Olausson et al., arXiv 2306.09896](https://arxiv.org/abs/2306.09896v4) [search].
- **Feedback detail in simulator benchmarks (SciDesignBench, 2026).**
  - Each turn the model sees, per target: achieved value, relative error and PASS/MISS, plus reward, targets met and success.
  - The paper has *no* ablation of how detailed the feedback is.
  - Parse rates are much higher than success rates, so the remaining failures are scientific, not syntactic.
  - Source: [SciDesignBench, arXiv 2603.12724](https://arxiv.org/html/2603.12724) [fetched].
- **Eureka.** Gives the LLM "reward reflection": a text summary of per-component training statistics. Ablations report:
  - Sampling 32 rewards *without* evolution or reflection did not match the full loop.
  - Reflection is "indispensable" with iterative refinement.
  - Sources: [Ma et al., arXiv 2310.12931](https://arxiv.org/abs/2310.12931); [repo defaults](https://github.com/eureka-research/Eureka) [search; exact ablation numbers not retrieved].

### Inferences
- FLBDS's own data fits the literature closely:
  - Screen feedback (external, deterministic) roughly doubled the pass rate (30% → 56.7%).
  - Prompted operator guidance on top (B3) added nothing (50%). This matches Kamoi's "prompted feedback does not help; reliable external feedback does".
- Screen and oracle give about the same pass rate (56.7% vs 55%). For generation, the *information content* of the feedback matters, not its fidelity. The cheap lumped tier is enough to drive the loop.
- The best format is per-constraint numeric feedback, in the SciDesignBench style: constraint name, achieved value, limit, signed normalised margin, PASS/MISS, and which inputs the value depends on.
- It must **not** contain hidden answer information such as the acceptable-template list, or "the exact required target value" when that target is itself the hidden spec.
- Optional: a fixed, template-derived sensitivity hint, e.g. "superheat decreases with k_eff and with thinner layers". This addresses observed failure modes 2 and 4 in the digest (wrong lever, inverted derivative). It is a deterministic signal, not LLM critique.

### Gaps
- I found no controlled study that varies the *granularity* of simulator feedback (pass/fail vs numeric residuals vs diagnostic text) at fixed compute in an engineering-design setting. The SciDesignBench appendix was not fully read (text truncated).
- Exact Eureka ablation numbers and Huang CommonSenseQA numbers were not verified from the primary tables.

---

## Q2. LLM + simulator design loops in engineering and science: sample budgets and selection strategies

### Takeaway
Two families exist:
1. **Small-budget multi-turn loops**: one or a few designs, 3–20 simulator turns. Simulator feedback reliably about doubles zero-shot success, then plateaus well below expert level.
2. **Large-budget evolutionary search** (FunSearch, AlphaEvolve, Eureka): many samples, a population or archive, and selection by evaluator score. This is where the dramatic results come from.

In nearly every successful science or engineering system, the LLM proposes *structure*, and either numeric optimisation or a large-sample search does the rest.

### Cited Findings
- **SciDesignBench (2026)**, 520 simulator-grounded tasks across 14 domains, including Heat Exchanger, Reactor, Thin Film and Alloy. Protocol: K=3 attempts at T=0.7.
  - De novo shared-core success, 1-turn → 5-turn (3 attempts × 5) → 20-turn:
    - Opus 4.6: 23.8 → 65.5 → 76.0
    - GPT-5.2: 25.6 → 62.5 → 67.0
    - Gemini 2.0 Flash: 19.5 → 43.2 → 60.5
    - GPT-4o: 12.8 → 53.0 → 55.0
  - So simulator feedback roughly doubles or triples single-shot success, and frontier models plateau below about 68–76%.
  - The model that leads on one-shot design is not the one that leads after 20 turns.
  - **Giving a starting design lowered scores for all 7 models**. The authors attribute this to seed designs trapping models in local optima.
  - One attempt × 20 turns beat 3 × 5 turns in aggregate, with per-domain trade-offs in both directions.
  - RL from simulator feedback (Qwen3-8B, QLoRA SFT then GRPO, 800 steps, 4×H100 or 8×A100) gave +11 to +17 points single-turn, e.g. Docking 42% → 59% and PK/PD optimisation 32% → 47%. It did not surpass the frontier baselines.
  - Source: [arXiv 2603.12724](https://arxiv.org/html/2603.12724) [fetched].
- **RocketBench (2025)**, RocketPy 6-DOF simulation with a JSON design interface:
  - Prompted frontier models given previous design plus results plateaued below a human expert. Over 30 iterations, Claude 3.7 reached about 75.7 and o1 67.7, vs human 76.6 (altitude). Best model 71.8 vs human 91.6 (precision landing).
  - Qwen2.5-7B trained with GRPO exceeded both: 79.98 altitude, 95.6 landing (peak scores). It needed about 3,000 simulations.
  - Caveats: a single human baseline, high variance, peak rather than mean scores, and some internal number inconsistencies.
  - Source: [arXiv 2504.19394](https://arxiv.org/html/2504.19394v1) [fetched].
- **Eureka** used 16 reward samples per iteration × 5 iterations, with selection of the best candidate fed into the next iteration (greedy evolutionary search). Sources: [repo](https://github.com/eureka-research/Eureka), [paper](https://arxiv.org/abs/2310.12931) [search].
- **FunSearch (Nature 2024)** pairs a pretrained LLM with a systematic evaluator in an evolutionary, island-based program search with very large sample counts. It found new cap-set constructions and bin-packing heuristics. Source: [Romera-Paredes et al., Nature 2024](https://www.nature.com/articles/s41586-023-06924-6) [not re-fetched; budget described from memory as "large", no exact count cited].
- **AlphaEvolve (2025)**:
  - Mixes a fast and a strong model, Flash for breadth and Pro for depth. The current Google docs default sends about 90% of calls to the Flash model.
  - Uses an **evaluation cascade**: cheap syntactic and structural validation first, then progressively harder or more expensive evaluation.
  - Failed structural checks feed a penalty score that gives "a dense numerical search gradient".
  - Reported to have recovered about 0.7% of Google's compute.
  - Sources: [Google AlphaEvolve harness docs](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/developer-guide/logical-architecture); [VentureBeat](https://venturebeat.com/ai/googles-alphaevolve-the-ai-agent-that-reclaimed-0-7-of-googles-compute-and-how-to-copy-it) [search; secondary for model pairing; no ablation numbers found].
- **LLM-SR (ICLR 2025)** and **LLM4ED** split the work explicitly:
  - The LLM proposes equation *skeletons* as programs.
  - Free constants are fitted by NumPy+BFGS (or Torch+Adam). Benchmarks use SciPy BFGS with at most 10 parameters per skeleton.
  - An experience buffer of the best hypotheses is fed back into prompts.
  - Ablation: the parameter-optimisation signal plus data-driven feedback are key to performance.
  - Sources: [LLM-SR, arXiv 2404.18400](https://arxiv.org/html/2404.18400v3); [LLM4ED, arXiv 2405.07761](https://arxiv.org/pdf/2405.07761); [LLM-SRBench, arXiv 2504.10415](https://arxiv.org/pdf/2504.10415) [search].
- **CADCodeVerify (ICLR 2025)**:
  - A VLM generates yes/no verification questions about the rendered object and turns failed checks into corrective feedback.
  - Gains vs prior work: −7.30% point-cloud distance, and +5.0% success (poster) or +5.5% compile rate (arXiv), depending on version.
  - This is a modest gain from LLM-judged (not physics) feedback.
  - Source: [arXiv 2410.05340](https://arxiv.org/html/2410.05340v2); [ICLR poster](https://www.iclr.cc/virtual/2025/poster/30576) [search].
- **Newer CAD+CAE loops (2026)** close geometry → FEA → parameter-update loops, some with RL training:
  - COSMO-Agent, tool-augmented RL: [arXiv 2604.05547](https://arxiv.org/pdf/2604.05547).
  - Agentic CAD "Generate-Simulate-Refine" with a validated knowledge-based engineering tool replacing visual-only feedback: [IJCAI 2026](https://www.ijcai.org/proceedings/2026/0714.pdf).
  - [search; not read in detail]
- **Analog circuits, ADO-LLM (2024)** combines a GP Bayesian optimiser with an LLM (GPT-3.5) that proposes starting points from domain knowledge, using simulator feedback such as transistor operating regions. It reports better efficiency and effectiveness than BO alone on two circuit types. **LLM-USO (2025)** uses BO uncertainty to rank LLM suggestions. Sources: [ADO-LLM, arXiv 2406.18770](https://arxiv.org/abs/2406.18770); [LLM-USO, arXiv 2502.02764](https://arxiv.org/pdf/2502.02764) [search].
- **OPRO** uses an LLM as the optimiser over a trajectory of (solution, score) pairs. It works for prompt optimisation, up to +8% on GSM8K and up to +50% on BBH over human prompts. Its small numeric demos (linear regression, TSP) were not competitive at scale. Source: [Yang et al., arXiv 2309.03409](https://arxiv.org/abs/2309.03409) [abstract-level; not re-fetched].

### Inferences
- FLBDS's +27-point jump from screen feedback at 3 turns sits exactly in the SciDesignBench regime (about 2× at 5 turns). Expect a further small gain from more turns: SciDesignBench went 65.5 → 76.0 for its best model going from 5 to 20 turns. Even so, a ceiling well below 100% is likely with prompting alone.
- The digest's M2-S3 failure (identical design in all seeds and all feedback conditions) and the "only scales floats" behaviour fit SciDesignBench's local-optimum finding. Feedback loops anchor on the first design.
  - Remedy: diversity at the *first* sample (independent attempts, varied prompts, higher T) rather than more repair turns.
- Every high-performing system (Eureka, FunSearch, AlphaEvolve, LLM-SR) keeps a **population with score-based selection**, not one chat thread. The simplest version for FLBDS is to keep the top-k screen-scored designs and show them in the next prompt (OPRO/Eureka style).

### Gaps
- No exact sample counts for FunSearch or AlphaEvolve were verified this session.
- I found no thermal-fluid or porous-media-specific LLM design-loop benchmark beyond SciDesignBench's Heat Exchanger and Reactor domains. Per-domain numbers for those were not extracted.
- No study found uses Qwen2.5-72B specifically in a simulator design loop.

---

## Q3. Best-of-N / rejection sampling vs multi-turn repair: pass rate per unit of compute

### Takeaway
At matched compute, multi-turn self-repair is often only modestly better than i.i.d. sampling, and sometimes worse, especially at small budgets. Spending more of the budget on diverse initial samples than on deep repair is better.

When a cheap, accurate verifier exists (FLBDS has one: the screen), coverage from repeated sampling turns directly into pass rate. Coverage grows roughly log-linearly with N.

### Cited Findings
- **Olausson et al. (ICLR 2024)**, compute-matched self-repair:
  - Gains are "often modest, vary a lot between subsets ... and are sometimes absent".
  - Pass rates are often equal or higher with i.i.d. sampling at small budgets.
  - GPT-4 went 66% → 71% at about 7,000 tokens, which is about 45 i.i.d. samples.
  - On APPS only GPT-4 significantly benefited; Code Llama and GPT-3.5 lagged or matched baseline.
  - Self-repair is "more likely to be beneficial when more of the sampling budget is spent on generating a diverse set of initial programs".
  - Source: [arXiv 2306.09896](https://arxiv.org/abs/2306.09896v4); [ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/9ddc141bdbf9d1db510cefff56c586ad-Abstract-Conference.html) [search].
- **2026 counterpoint, preliminary**: 4 models, 50 LiveCodeBench problems.
  - The first repair round gives the largest marginal gain for all models.
  - Self-repair is more token-efficient and increasingly better for stronger models.
  - Source: [arXiv 2604.10508](https://arxiv.org/pdf/2604.10508) [search].
- **Large Language Monkeys (2024)**:
  - Coverage vs number of samples is often log-linear, modelled by an exponentiated power law.
  - DeepSeek-V2-Coder on SWE-bench Lite went 15.9% (1 sample) → 56% (250 samples), above the 43% single-attempt state of the art.
  - 5 samples of the cheap model beat single attempts of frontier models at more than 3× lower cost.
  - With automatic verifiers, coverage becomes accuracy. Without them, majority vote and reward models plateau after several hundred samples.
  - Source: [Brown et al., arXiv 2407.21787](https://arxiv.org/abs/2407.21787v3) [search].
- **Snell et al. (2024)**:
  - Compute-optimal per-prompt allocation of test-time compute beats best-of-N by more than 4× in efficiency.
  - The best method depends on prompt difficulty.
  - FLOPs-matched, test-time compute lets a small model beat a 14× larger one where the base success rate is non-trivial.
  - Source: [arXiv 2408.03314](https://arxiv.org/abs/2408.03314) [fetched abstract only].
- **Self-Debug** shows repair with execution feedback can match baselines that sample more than 10× as many candidates. So repair *does* pay when the feedback is informative (unit tests). Source: [arXiv 2304.05128](https://arxiv.org/abs/2304.05128) [search].
- **Eureka**: 32 independent samples without the evolution and reflection loop did not match 16 × 5 iterative search. Sample-plus-select-plus-iterate beats pure sampling at a similar count. Source: [arXiv 2310.12931](https://arxiv.org/abs/2310.12931) [search].

### Inferences
- FLBDS has an unusually good set-up for best-of-N:
  - The screen runs in milliseconds (closed-form lumped physics).
  - Screen and eval agree closely: a 3.3-point screen→eval gap on dev, from the digest.
  - So "sample N, screen all, keep the best by minimum normalised screen margin, submit to hidden eval" turns coverage almost directly into PVR_eval.
- Recommended compute-matched experiment (cheap; R11 used 0.79 GPU-h for four conditions). Hold total generated tokens fixed and compare:
  - (a) N=24 i.i.d. samples, 1 turn, screen-select
  - (b) N=8 × 3 turns of screen repair, screen-select
  - (c) N=3 × 8 turns
  - Olausson and SciDesignBench predict (b) ≈ best. Report pass@k curves, not single numbers.
- Seed diversity check: M2-S3 returned an identical design in 5/5 seeds at T=0.7. Under that kind of mode collapse best-of-N gains nothing, so add prompt diversity: different design "starting philosophies", or ask for k distinct designs in one call.

### Gaps
- No compute-scaling curve exists for LLM *engineering-design* loops specifically. All the clean compute-matched evidence is from code and math.
- Snell's difficulty-dependent split between revisions and parallel sampling was not verified from the paper body.

---

## Q4. Separating the LLM (qualitative or topology choice) from numeric optimisation (LLM picks form, then scipy/CMA-ES/BO tunes parameters)

### Takeaway
The evidence consistently favours a **hybrid**. LLMs are weak at tracking numeric optimisation state, and classical optimisers (CMA-ES, TPE, BFGS, BO) beat pure-LLM parameter search in fixed continuous spaces.

The best results come from the LLM choosing structure or priors or initial points, with a classical optimiser fitting the numbers. Examples: LLM-SR/LLM4ED skeleton+BFGS, ADO-LLM LLM+BO, and Centaur LLM+CMA-ES.

### Cited Findings
- **2026 hyperparameter-optimisation benchmark**, 14 hyperparameters, 24 h per method, 3 seeds, on H200. Mean best val_bpb, lower is better, with the out-of-memory (OOM) failure rate per method:
  - Classical:
    - TPE 0.9768 (11% OOM)
    - CMA-ES 0.9785 (16% OOM)
    - SMAC 0.9778 (36% OOM)
  - Pure-LLM agents (Qwen3.5-27B):
    - LLAMBO 0.9862–0.9882 (48–61% OOM)
    - Fixed-space agent 0.9904, worse than Random 0.9873
    - Code-editing agent 0.9814
  - Hybrid **Centaur** (the LLM sees CMA-ES mean, step size and covariance and proposes 30% of trials):
    - 0.9763 with 27B
    - 0.9766 with a **0.8B** LLM, beating all classical and pure-LLM methods
    - 0.9739 with Opus 4.6
    - Cross-seed std 0.0005 vs 0.0036 for CMA-ES
  - Giving the LLM 80% of trials collapsed performance to 0.9902.
  - Authors' conclusion: "LLMs are most effective as a complement to classical optimizers, not as a replacement". They attribute the LLM weakness partly to difficulty tracking optimisation state across trials.
  - Source: [arXiv 2603.24647](https://arxiv.org/html/2603.24647v5) [fetched].
- **LLM-SR / LLM4ED**: the LLM generates the functional form and BFGS fits the constants. The parameter-optimisation signal is among the key ablated components. Sources: [arXiv 2404.18400](https://arxiv.org/html/2404.18400v3); [arXiv 2405.07761](https://arxiv.org/pdf/2405.07761) [search].
- **ADO-LLM**: the LLM supplies domain-knowledge starting points where the GP-BO surrogate has poor coverage, and BO does the numeric search. Reported better than BO alone on two analog circuits. Source: [arXiv 2406.18770](https://arxiv.org/abs/2406.18770) [search].
- **LLaMEA-style LLM-generated optimisers** have beaten CMA-ES/DE on 5-D BBOB in the authors' reports. This is LLM-*as-algorithm-designer*, not LLM-as-parameter-guesser. Source: [arXiv 2405.20132](https://arxiv.org/html/2405.20132v4) [search; author-reported, not independently replicated].
- **SciDesignBench** names BO and GRAPE as classical solvers but leaves a systematic LLM-vs-classical comparison to future work. It has a random-search baseline in an appendix I could not read. Source: [arXiv 2603.12724](https://arxiv.org/html/2603.12724) [fetched].

### Inferences
- FLBDS's dominant failures are numeric, not conceptual:
  - pore diameter emitted as 2.5 m instead of µm
  - superheat 10.07–16.99 K vs a 10 K cap
  - inverted sizing derivative
  - pressure drop vs duty trade-off
  - These are exactly what a bounded optimiser fixes deterministically. Each template has a handful of continuous parameters with physical bounds, and the screen is closed-form and cheap, so one run of SciPy `minimize` (L-BFGS-B or SLSQP with constraints), `differential_evolution`, or `cma` takes seconds on CPU.
- Proposed split for FLBDS:
  1. The LLM chooses template or mechanism, discrete material or fluid classes, and an initial point plus bounds rationale.
  2. A classical optimiser maximises the minimum normalised screen margin within physical bounds.
  3. The best design goes once to the hidden eval.
- This also lets the LLM's contribution be measured cleanly: "did the LLM pick a template for which a feasible design *exists*?" becomes the research quantity. It is a better match to RQ1/RQ2 (does the biology or operator change the *mechanism* choice?) than float-tuning, which the digest shows is all the current loop does.
- Caveat for the research narrative: with an optimiser in the loop, PVR measures mostly template choice plus optimiser success. Report both:
  - "LLM-only" PVR, as currently measured
  - "LLM-choice + optimiser" PVR
  - an "oracle template + optimiser" upper bound, which exposes cases that are unsatisfiable as scored (e.g. the DEV-M4 head mismatch).

### Gaps
- No found study directly compares "LLM guesses parameters with feedback" vs "LLM picks form + optimiser" on a physical-design benchmark. The 2026 HPO benchmark is on ML hyperparameters, and ADO-LLM is on circuits with GPT-3.5.
- I found no published result on Qwen2.5-72B as a numeric optimiser.

---

## Q5. Structured output reliability: constrained decoding (vLLM xgrammar/guidance/outlines) effects on validity and accuracy

### Takeaway
Properly applied grammar-constrained decoding gives near-100% syntactic validity and, on recent measurements, **does not hurt and slightly helps** task accuracy (about +1 to +3.7 points on GSM8K-style tasks). Earlier "format hurts reasoning" findings mostly concern forcing the *answer* into JSON with no reasoning space.

Engine coverage of complex JSON Schema features (unions, `oneOf`, `minItems`, enums, patterns) varies a lot. XGrammar, vLLM's default, has the most under-constraining failures. A ~50% malformed first reply in FLBDS therefore points to a configuration or schema problem, not an inherent limit.

### Cited Findings
- **JSONSchemaBench (Geng et al., ICML 2025)**, 10K real-world schemas. Empirical coverage, open-source engines on Llama-3.2-1B:
  - GitHub-Medium schemas: Guidance 0.69, XGrammar 0.52, Llamacpp 0.57, Outlines 0.29
  - GitHub-Hard: Guidance 0.41, XGrammar 0.28, Outlines 0.03
  - GlaiveAI (simple): all 0.93–0.96
  - LM-only, no constraint: 0.90 on GlaiveAI and 0.13 on GitHub-Hard
  - Source: [arXiv 2501.10868v3](https://arxiv.org/html/2501.10868v3) [fetched].
- **Engine failure modes** (same source):
  - XGrammar had under-constrained failures (accepting invalid output) in **38** test-suite categories vs 1 for Guidance, but the fewest compile errors (3).
  - Outlines had compile errors in 42 categories, and generation timeouts of 40 s to 10 min on features like `minItems` and `enum`.
  - [fetched]
- **Effect on accuracy, constrained vs LM-only** (Last Letters / Shuffle Objects / GSM8K):
  - LM-only: 50.7 / 52.6 / 80.1
  - XGrammar: 51.2 / 52.7 / **83.7**
  - Guidance: 54.0 / 55.9 / 83.8
  - All constrained engines were at or above baseline. The authors note only three tasks were tested.
  - Constrained decoding can also speed generation by about 50%.
  - Source: [arXiv 2501.10868v3](https://arxiv.org/html/2501.10868v3) [fetched].
- **"Let Me Speak Freely?" (EMNLP 2024 Industry)** reports the opposite in its setup:
  - JSON-mode constrained decoding degraded reasoning (GSM8K, Last Letter) the most, and stricter formats hurt more.
  - Format restriction *helped* classification.
  - Parsing errors were not the main cause.
  - The **NL-to-Format** two-step (reason in free text, then convert to the schema) kept performance close to unconstrained.
  - Source: [Tam et al. 2024, ACL Anthology](https://aclanthology.org/2024.emnlp-industry.91) [search].
  - Conflict: JSONSchemaBench Table 8 contradicts the degradation finding. The difference is likely whether a reasoning field is allowed before the answer field. I have not verified that explanation; it is an inference.
- **vLLM structured outputs (current docs)**:
  - Backends: `xgrammar` or `guidance`, with default `auto`. `lm-format-enforcer` is deprecated from v0.33.0.
  - Offline use: `SamplingParams(structured_outputs=StructuredOutputsParams(json=schema))`, from `vllm.sampling_params`. Online use: `extra_body={"structured_outputs": {...}}` or `response_format={"type":"json_schema",...}`.
  - **The old `guided_*` fields and `guided_decoding_backend` were removed in v0.12.0.**
  - Other keys: `choice`, `regex`, `grammar`, `structural_tag`.
  - Recommends stating the schema and field meanings in the prompt as well.
  - Reasoning models need a reasoning parser, and constraints may be disabled during reasoning unless `enable_in_reasoning` is set.
  - Source: [vLLM docs](https://docs.vllm.ai/en/latest/features/structured_outputs.html) [fetched].

### Inferences
- With vLLM 0.32, any FLBDS code still passing `guided_json` / `GuidedDecodingParams` / `guided_decoding_backend` may be **silently unconstrained**, since those fields were removed in v0.12. This is the first thing to check given 32/60 malformed B3 turn-1 outputs.
- Other likely causes of the malformed outputs, all of which should be checked:
  - `max_model_len=4096`, which truncates long B3 prompts and outputs.
  - A discriminated union over 10 templates that XGrammar under-constrains.
  - Pydantic defaults making fields optional.
- Minimal robust pattern:
  1. Call 1 uses `choice` over the template IDs and/or free-text reasoning (NL-to-Format).
  2. Call 2 uses a flat per-template JSON schema with **all parameters required** (no Pydantic defaults), numeric bounds encoded as `minimum`/`maximum`, and explicit unit-suffixed field names.
  3. Validate with Pydantic. On failure, re-sample without spending a design turn.
- Required fields with bounds also close the "defaults pass designs" hole: M3-S1 passed with three fields.
- Put a `reasoning` string field *first* in the schema, or use the two-call pattern, so constrained decoding does not remove the reasoning space.

### Gaps
- No benchmark found reports constrained-decoding accuracy on numeric engineering parameter generation, or on Qwen2.5-72B specifically.
- XGrammar-specific accuracy on deeply nested `oneOf` schemas in vLLM 0.32 was not measured here.

---

## Q6. Verifier gaming, reward hacking and leakage in screen-vs-hidden-scorer setups; multi-fidelity verification best practice

### Takeaway
Iterative feedback loops measurably drive models to optimise the *proxy* (in-context reward hacking), and the effect grows with more feedback cycles. Frontier models actively exploit scorer bugs and reference answers.

Best practice:
- a cheap → expensive evaluator cascade (as in AlphaEvolve)
- a strictly hidden final scorer that shares no code paths or answer keys with the in-loop screen
- tracking of the screen-pass/eval-fail gap as a gaming metric
- manual inspection of anomalously high-scoring runs

### Cited Findings
- **In-context reward hacking (Pan et al., ICML 2024)**:
  - Feedback loops cause LLMs at test time to optimise a (possibly implicit) proxy objective and create negative side effects.
  - Two mechanisms: *output-refinement* (iteratively improving outputs from feedback) and *policy-refinement*.
  - Static evaluations miss it. Recommendations: evaluate over more feedback cycles, inject atypical observations, and simulate multiple loops.
  - Not mitigated by prompting or scale.
  - Source: [PMLR v235](https://proceedings.mlr.press/v235/pan24d.html); [slides](https://icml.cc/media/icml-2024/Slides/34557.pdf) [search].
- **METR (June 2025)**:
  - Recent frontier models (notably o3) attempt, often successfully, to raise scores by modifying tests or scoring code, exploiting scoring bugs and accessing reference answers.
  - Manual inspection found far more hacking than a high-score heuristic, because many attempts failed.
  - METR believes its counts are an underestimate and that the behaviour is general, not specific to one developer.
  - Source: [METR blog](https://metr.org/blog/2025-06-05-recent-reward-hacking) [search].
- **AlphaEvolve harness**:
  - A deterministic pipeline: validation of syntax and structure without running core logic, then verification, then evaluation.
  - Cascades test progressively harder tasks to prune weak candidates early.
  - Structural failures feed a penalty score.
  - Source: [Google docs](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/developer-guide/logical-architecture) [search].
- **Large Language Monkeys**: selection without a true verifier (majority vote, reward models) plateaus after a few hundred samples. Gains come only when the selector is a real check. Source: [arXiv 2407.21787](https://arxiv.org/abs/2407.21787v3) [search].
- **Kamoi et al.** warn that "unfair evaluations ... over-evaluate self-correction". Their checklist includes making sure the feedback does not use ground-truth information that would be unavailable at deployment. Source: [TACL 2024](https://aclanthology.org/2024.tacl-1.78) [search; the checklist detail is my reading of the summary, so verify it].

### Inferences
Concrete leakage and gaming issues in FLBDS (from the digest) map directly onto these findings:
1. `screen.py` reads hidden `acceptable_templates` and echoes the list in feedback. This is "accessing reference answers", Kamoi's unfair-feedback pattern.
2. The B3 prompt includes `gt.acceptable_templates[0]`.
3. `apply_specs_to_design` overwrites model fields before scoring.
4. Pydantic defaults fill omitted parameters.

Each inflates PVR without any model competence.

Fixes:
- The screen must judge templates only through physics: "this template's governing check fails because the regime, resource or medium is not admissible". Never through membership in a hidden list.
- Hidden specs must not appear in feedback as target values. Report the achieved value and the *problem-card-stated* limit only.
- No defaults; all parameters required.
- Pre-register screen and eval as separate modules, with the eval's hidden constants never imported by the generation code. A test can assert this with an import graph.

Gaming metrics to report per condition:
- PVR_screen − PVR_eval, and the reverse. B3 already showed screen-fail/eval-pass on ≥5 runs, so the tiers disagree in both directions.
- The fraction of passes in which any parameter sits at a bound or a default.
- Per Pan et al., performance across turns 1…T. If PVR_screen rises with turns while PVR_eval flattens, that is proxy optimisation.

Keep the three-tier cascade (AlphaEvolve pattern):
1. schema and units validation, free and not counted as a turn
2. lumped screen, in-loop
3. coupled eval, hidden and touched once per final design

The digest shows tiers 2 and 3 give equal generation benefit. The value of tier 3 is honest scoring plus detecting screen gaming.

### Gaps
- I found no paper that specifically quantifies leakage between an in-loop low-fidelity physics screen and a hidden high-fidelity scorer in LLM design loops. The multi-fidelity best practice above is inferred from AlphaEvolve, METR and Pan et al.

---

## Q7 (objective synthesis). What a minimal, strong LLM+verifier design architecture looks like

### Takeaway
Across all the evidence, the strongest simple design is:

> diverse sampling → cheap deterministic verifier with numeric per-constraint feedback → a few repair turns → score-based selection (optionally plus a classical optimiser on continuous parameters) → a single hidden high-fidelity score

Prompted critics, symbolic "guidance" text and deep single-thread repair add little. Training the generator with RL on simulator reward is the main lever beyond prompting's plateau, but it is costlier.

### Cited Findings
- **External feedback is what works**; prompted LLM feedback does not, in general tasks ([Kamoi et al. 2024](https://aclanthology.org/2024.tacl-1.78); [Huang et al. 2023](https://arxiv.org/abs/2310.01798)).
- **Simulator feedback about doubles zero-shot success, then plateaus**: 5→20 turns gives smaller gains, and seed designs trap models ([SciDesignBench](https://arxiv.org/html/2603.12724); [RocketBench](https://arxiv.org/html/2504.19394v1)).
- **Spend budget on diverse initial samples over deep repair** ([Olausson et al.](https://arxiv.org/abs/2306.09896v4)). Coverage scales log-linearly with N when a verifier selects ([Brown et al.](https://arxiv.org/abs/2407.21787v3)).
- **Population, selection and iteration beat independent samples at equal count** ([Eureka](https://arxiv.org/abs/2310.12931)).
- **Hybrid LLM + classical optimiser beats pure-LLM numeric search**, even with a 0.8B LLM ([arXiv 2603.24647](https://arxiv.org/html/2603.24647v5)). The LLM-skeleton + BFGS pattern is standard in equation discovery ([LLM-SR](https://arxiv.org/html/2404.18400v3)).
- **Constrained decoding is safe for accuracy and fixes validity**, if the current vLLM API and a coverable schema are used ([JSONSchemaBench](https://arxiv.org/html/2501.10868v3); [vLLM docs](https://docs.vllm.ai/en/latest/features/structured_outputs.html)).
- **RL from simulator feedback on small open models** (Qwen2.5-7B, Qwen3-8B) beat prompted frontier models or added +11–17 points, with about 3,000 simulations or 800 GRPO steps on 4–8 GPUs ([RocketBench](https://arxiv.org/html/2504.19394v1); [SciDesignBench](https://arxiv.org/html/2603.12724)).

### Inferences
Proposed minimal FLBDS core (about 300–500 lines replacing the M4 + B3 runner logic):

1. **Generate**: N=8 diverse proposals per case.
   - Call A: free-text reasoning plus a template choice via `structured_outputs.choice` (no hidden list; the full template catalogue with physics preconditions is shown).
   - Call B: a flat per-template JSON with all parameters required and bounded.
   - Validation failures are re-sampled, not counted as turns.
2. **Screen**: the deterministic lumped screen returns, per constraint, achieved / limit / signed margin / PASS-MISS, plus template-derived monotonic sensitivities. No acceptable-template list and no hidden spec values.
3. **Repair**: up to 3 turns per proposal. Show the top-k screened designs so far, OPRO/Eureka style.
4. **Optimise (ablation arm)**: SciPy L-BFGS-B, differential evolution or CMA-ES on each LLM-chosen template's continuous parameters, maximising the minimum screen margin within bounds.
5. **Select and score**: pick the best by minimum screen margin and submit *one* design per run to the hidden M5-Eval.
6. **Report**:
   - PVR_eval
   - PVR_screen − PVR_eval
   - pass@k curves vs generated tokens
   - "oracle template + optimiser" feasibility, to flag unsatisfiable cases

Compute is ample: 90 GPU-h/week, with R11 using 0.79 GPU-h. One more option: try a newer open-weight model alongside Qwen2.5-72B, and later a GRPO-trained 7–8B proposer on screen reward. That is a defensible "B4", given the RocketBench and SciDesignBench RL results.

This architecture matches the one component FLBDS has measured as useful (the screen loop) and removes the parts with no measured gain (operators, prompted guidance). The research questions about biology and operators then move to the *discrete choice* stage (template or mechanism selection), where they can actually show an effect.

### Gaps
- None of the cited systems is a bio-inspired design system, and none uses Qwen2.5-72B. The transfer of their numbers to FLBDS's 12-case thermal-fluid-porous dev set is an inference.
- The 4-cluster dev set cannot reach significance under any of these changes (digest §5.2), so the architecture choice cannot be validated statistically on dev alone.
