# 05 — Fast, trustworthy physics verification for LLM-proposed designs (FLBDS M5 screen + hidden solver)

Scope: how to make FLBDS's physics layer (10 TFP templates, `flbds/physics/`, 2,442 lines) smaller and more reliable: dimensional analysis and regime checks, unit safety, contract/property testing, screen-vs-scorer design, cheap higher-fidelity tools, evidence on LLMs writing physics code, and whether an optimiser should replace LLM float tuning.
Conventions: [C] = observed in this repo's code (path given); web claims carry inline links. Search-engine summaries were used for some numbers; where a primary text was not opened this is noted.

### Codebase observations that frame the questions (all [C], read 2026-11-19)
- No unit library is used in the physics layer. Pint is listed in `pyproject.toml` but used only in `flbds/pipeline/stage6_quantities.py`; templates pass bare floats with suffix names (`pore_diameter_m`, `h_conv_W_m2K`) — `flbds/physics/*.py`, `flbds/schema/templates.py`.
- Silent defaults sit at two levels. (a) Schema: e.g. `TPL09Params` defaults `emissivity_thermal=0.90`, `absorptivity_solar=0.10`, `substrate_thickness_m=0.02`, `substrate_k_W_mK=0.05`, `h_conv_W_m2K=8.0`, `T_sky_degC=10` (`flbds/schema/templates.py:165-187`). (b) Screen: when the card has no cap, `max_thickness_m→0.05`, `max_mass_kg_m2→500`, TPL-07 envelope→0.1 m, TPL-08 length→1.0 m, and a TPL-08 fallback velocity of 0.1 (`flbds/physics/screen.py:77-84, 136, 140, 155`). This is the "blank outputs pass" mechanism.
- The screen reads hidden ground truth: `gt.acceptable_templates` is returned in feedback (`screen.py:62-74`). That is the "screen leaked acceptable templates" issue.
- Screen and eval share helpers, so their errors are correlated (common-mode). `compute_duct_pressure_drop` (TPL-08) and `compute_ergun_pressure_drop` (TPL-06) are imported into the screen and also called inside the eval (`tpl08_countercurrent.py:52,171`; `tpl06_porous_flow.py:14,49,88`).
- **Likely physics bug, same in both tiers (common-mode):** the TPL-10 Laplace breakthrough uses `cos_theta = abs(np.cos(theta))` (`screen.py` TPL-10 branch; `tpl10_diffusion.py:149`). A hydrophilic pore (θ < 90°) has no capillary barrier, because water wicks in. The abs() makes a hydrophilic membrane look as good as a hydrophobic one with the mirror angle. A regime/sign check (θ > 90° required for a gas plastron) would catch it.
- The screen is not a relaxation of the eval. In Round 11, B3 had PVR_screen 25/60 < PVR_eval 30/60, so at least 5 designs failed the screen but passed the scorer (digest §5.1). The TPL-08 screen also computes velocity from `m_dot_cold` only and uses `A = D_h²` for non-circular ducts (`screen.py:142-151`), an approximation that is not guaranteed to bound the eval.
- Only a few regime checks exist, hard-coded and per template: Fo∈[0.25,5] (TPL-01), Bi<0.1 (TPL-07), Re_pore≤10 (TPL-06), Re<2300 switch (TPL-08), Fo_m≥1 (TPL-10).
- Scoring-environment mismatch: the scorer's `DEV_SPECS` hard-codes DEV-M4-S1 head = 10 m vs the card's 2.5 m (digest §6.2). Root cause: environment values are duplicated in a runner dict instead of coming from the Problem Card.

---

## Q1. Dimensional analysis / Buckingham Pi / scaling laws as screening tools; regime-validity checks; use in bio-inspired design

### Takeaway
Dimensionless groups are the right currency for both screening (scaling bounds) and declaring each template's validity domain. Bio-inspired transfers fail exactly when the group that governs the biological effect changes regime at engineering scale: adhesion vs size, Bond and Weber for droplets, s+ for riblets, Stokes number for fog capture. Each FLBDS template should declare its governing groups and valid ranges, and the screen should refuse to score outside them.

### Cited Findings
- Buckingham Pi is automated in Python by **BuckinghamPy** (Karam & Saad, SoftwareX 2021), which returns all possible sets of dimensionless groups from variables given in M, L, T dimensions; the authors note manual Pi analysis is "tedious and error-prone" — [GitHub saadgroup/BuckinghamPi](https://www.github.com/saadgroup/BuckinghamPi); [SoftwareX record](https://doaj.org/article/c60314e975dd43eaa37482ef8a255240). **PyDASA** is a newer PyPI library that adds unit conversion and sensitivity analysis — [PyPI pydasa](https://pypi.org/project/pydasa/).
- **Gecko/insect adhesion scaling:** across 225 climbing species spanning more than 7 orders of magnitude in body mass, pad area shows extreme positive allometry (about 200-fold increase in relative pad area from mites to geckos). Within closely related groups pads are almost isometric, but adhesive strength rises with size, "inconsistent with existing models". Extrapolating, a human would need about 40% of body surface as pads, so adhesion-based climbers larger than geckos are probably anatomically prohibited — [Labonte et al. 2016 PNAS, PMC4747726](https://pmc.ncbi.nlm.nih.gov/articles/PMC4747726). This is a scaling screen: a size-scaled adhesion transfer fails a force-per-weight bound.
- Autumn et al. (2000) measured single gecko setal adhesion directly — [Nature 35015073](https://www.nature.com/articles/35015073). This page was not opened this session, so per-seta force values are not quoted here.
- **Sharkskin/riblets:** the optimum spacing is s+ ≈ 10–20 wall units, depending on shape. Bechert et al. (1997) found an optimum near s+ ≈ 15, with peak drag reduction of about 7–10%. Above the optimum the viscous regime breaks down and drag reduction turns into drag *increase* — [García-Mayoral & Jiménez notes, UPM](https://torroja.dmt.upm.es/congresos/katnet09/pdf/Wednesday/Session%20Wed%202/RGM_JJ.pdf); [KIT study](https://publikationen.bibliothek.kit.edu/1000145506/148692997). DNS of herringbone riblets gave a maximum DR of 9.3% vs 9.9% in experiments at s+ = 17 — [arXiv 1703.10879](https://arxiv.org/pdf/1703.10879). Riblet benefit is defined only in wall units (s+ = s·u_τ/ν), so a geometry copied at fixed physical size from a shark is meaningless without the flow's u_τ.
- **Lotus effect / droplet impact:** no universal threshold exists. The critical Weber number for the Cassie→Wenzel transition depends on texture. Lotus leaves (micro-cones about 8 µm base, 10 µm high, 19.5 µm pitch) showed no transition up to We ≈ 22, taro up to We ≈ 15.9. Bouncing is reported from We ≈ 0.1, and splashing at We > 41 in one study — [PMC11223265 review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11223265); [arXiv 0901.4228](https://arxiv.org/pdf/0901.4228); [arXiv 1708.08582](https://arxiv.org/pdf/1708.08582).
- **Namib beetle fog harvesting:** droplets grow on hydrophilic bumps to a critical size, detach and roll to the mouth — [Parker & Lawrence 2001, Nature 414:33](https://link.springer.com/article/10.1038/35102108). Biomimetic models use Bond number Bo = ρgR²/γ (R = spherical-cap-equivalent radius). A Furmidge-style retention force balance is within 1% of Surface Evolver at small Bo — [arXiv 2203.04675 "Optimizing fog harvesting by biomimicry"](https://arxiv.org/pdf/2203.04675). Fog-capture efficiency on a small body is limited by droplet inertia (Stokes number). Shape and surface changes are claimed to raise harvesting by up to about 400% — [PMC10903646](https://pmc.ncbi.nlm.nih.gov/articles/PMC10903646).
- **Termite mound ventilation:** in *Odontotermes obesus*, ventilation is driven by diurnal temperature oscillation, not wind. Outer flutes heat faster than the central chimney by day, which sets up a convection cell that reverses at night. Low ambient wind (about 0–5 m/s) cannot drive significant bulk flow across the wall — [King, Ocko & Mahadevan 2015 PNAS 112:11589](https://dash.harvard.edu/bitstream/handle/1/23603185/MahadevanTermite2015.pdf?sequence=1); [arXiv 1703.08067](https://arxiv.org/abs/1703.08067). This matters for FLBDS: the popular "termite = wind-driven passive cooling" analogy is the wrong mechanism, and a regime check (thermal-buoyancy Rayleigh/Grashof vs wind-pressure scale) is what separates the two.
- **Kingfisher nose (Shinkansen 500):** the nose was shaped to reduce tunnel-boom pressure waves. Headline claims are "10% faster, 15% less power", but a detailed account reports 30% less air resistance and a *measured* 13% power reduction vs the 300 series at 270 km/h. Sources conflict on the energy figure — [Gigazine](https://gigazine.net/gsc_news/en/20171110-shinkansen-500-series-biomimetics); [Trellis](https://trellis.net/article/how-one-engineers-birdwatching-made-japans-bullet-train-better). The transfer works because both cases are governed by an impedance/area-change problem (bird entering water vs train entering tunnel). The density ratio is very different, so it is a shape heuristic, not a similarity match.
- Vogel's *Life in Moving Fluids* (Princeton UP) is the standard text organising biological fluid mechanics by Reynolds number and related groups — [Princeton UP](https://press.princeton.edu/books/paperback/9780691026169/life-in-moving-fluids). Not opened this session; no specific numbers quoted.

### Inferences
- Give each template a `validity` block of dimensionless groups with closed intervals, for example:
  - TPL-06: Re_p ≤ 10.
  - TPL-07: Bi < 0.1.
  - TPL-08: Re < 2300 laminar; axial-conduction parameter λ.
  - TPL-10: Kn and θ > 90°.
  - TPL-05: Bo ≪ 1.
  - TPL-01: Fo window.
  - TPL-02: Ste ≲ 0.1–0.2, for quasi-steady Neumann validity.
  - TPL-09: radiative vs convective ratio.
  
  Out-of-domain should be a third verdict, `invalid_regime` (≠ pass/fail), and the scorer should never count it as a pass. This turns the ad-hoc checks above into data and covers the TPL-10 θ<90° bug.
- Bio-transfer screening should check *the biology's* governing group against *the problem's*. If the dimensionless group that makes the organism work (s+, We, Bo, Stk, adhesion force/weight) falls outside the template's window at the problem's scale, then "look-alike ≠ work-alike" is detected deterministically. This is a cheap, defensible version of the conflict detector's "regime" rule (M4 T5) that does not need graph operators.
- Pi groups also cut search dimensionality for the optimiser in Q6: optimise over 2–4 groups, not 8–12 raw floats.

### Gaps
- Per-seta and whole-animal gecko force numbers (Autumn 2000) were not verified this session.
- No single published review compiles "dimensionless-group checks used in BID verification". Bio-inspired design tools (AskNature, DANE, SAPPhIRE) appear not to do this automatically, but I found no source stating so either way.

---

## Q2. Unit-safe computation and contract/property testing; verification vs validation (ASME V&V 10/20)

### Takeaway
Use units at the boundaries, not inside hot loops: parse and dimension-check every LLM-proposed and card-supplied value with Pint (or unyt), then strip to SI floats for the solver. Back each template with (i) code-verification tests (analytic/manufactured solutions, convergence order), (ii) Hypothesis property tests (conservation, monotonicity, limits, dimension invariance), and (iii) a separate, small validation set against literature/experiment. ASME V&V 20's E = S − D vs u_val framing gives an honest way to state each template's fidelity.

### Cited Findings
- Pint's own docs warn it "can impose a significant performance overhead on computationally-intensive problems" and give tuning advice — [Pint performance docs](https://pint.readthedocs.io/en/stable/advanced/performance.html).
- unyt (JOSS 2018) claims to be faster, with higher test coverage and fewer lines than Pint and astropy.units — [unyt JOSS paper](https://joss.theoj.org/papers/10.21105/joss.00809.pdf); [arXiv 1806.02417](https://arxiv.org/abs/1806.02417v3). A self-published comparison lists overhead vs NumPy of about 1.5–3× (unyt), 2–3× (astropy) and 2–5× (Pint), with no methodology stated, so treat as unverified — [dimtensor benchmarks](https://marcoloco23.github.io/dimtensor/performance/benchmarks). No independent head-to-head benchmark was found.
- LLM unit errors in benchmarks are a *minority* category: in CMPhysBench, unit errors are under 2% of errors, while math/logic errors are 20–30% — [CMPhysBench arXiv 2508.18124](https://arxiv.org/pdf/2508.18124). A small-model study finds that stronger models shift errors toward late-stage calculation and unit-consistency mistakes — [arXiv 2505.20707](https://arxiv.org/html/2505.20707v2). FLBDS's own data shows the costly form, a scale error that is dimensionally valid (pore diameter 2.5 m instead of µm), which unit checking alone does not catch (digest §6.1 item 1).
- **Metamorphic testing** is recommended for scientific software, which lacks test oracles. Relations between runs (symmetry, scaling, conservation) are checked instead of exact outputs — [Kanewala & Chen, IEEE CiSE 2018 (NSF PAR)](https://par.nsf.gov/servlets/purl/10085974). It applies along the whole verification→validation continuum — [Raunak & Olsen, NIST](https://www.nist.gov/publications/metamorphic-testing-continuum-verification-and-validation-simulation-models). Relations derived from tidal periodicity found a real defect in open-source tide-prediction software — [Luu et al., arXiv 2206.05457](https://arxiv.org/abs/2206.05457v1).
- **ASME V&V 20-2009** (CFD and heat transfer): comparison error E = S − D. The validation uncertainty u_val combines numerical (u_num), input (u_input) and experimental (u_D) uncertainty, propagated by Taylor series or Monte Carlo. The model error lies in E ± k·u_val — [Coleman V&V 20 slides](https://maretec.tecnico.ulisboa.pt/~maretec.daemon/html_files/CFD_workshops/html_files_2008/papers/COLEMAN.pdf); [ASME VVUQ standards list](https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty). V&V 10 is the solid-mechanics counterpart in the same ASME VVUQ series (same list). Sandia critiques note V&V 20 handles aleatory and sparse-data epistemic uncertainty less well — [OSTI 1783664](https://www.osti.gov/servlets/purl/1783664).
- Solution verification estimates discretisation error by grid refinement and observed convergence order (the Richardson/GCI family) — [Sandia, OSTI 1343249](https://www.osti.gov/servlets/purl/1343249).
- FLBDS already has one code-verification result: the enthalpy Stefan solver vs the Neumann analytic solution agrees to 0.018–0.02% (digest §2.3).

### Inferences (concrete Python contract)
- **Input contract.**
  - Each template declares `inputs: dict[name → (pint dimension, physical bounds, required: bool)]`.
  - The LLM emits `{"value": 2.4, "unit": "µm"}`. The parser does `ureg.Quantity(v, u).to(dim_si)` and raises `DimensionalityError` on a dimension mismatch.
  - Pydantic models use `extra="forbid"` and **no defaults for design variables**. Missing means a `schema_failure`, never a default.
  - Environment and limit values come only from the Problem Card. This removes the `DEV_SPECS` duplication, so the 10 m vs 2.5 m class of bug becomes impossible.
  - Plausibility bounds per variable (e.g. pore diameter 1 nm–1 mm) catch dimensionally valid scale errors like 2.5 m.
- **Core functions.** Pure SI-float functions (fast). Use `@ureg.wraps`/`@ureg.check` only on the public API.
- **Property tests (Hypothesis).** One test file per template, using `hypothesis.strategies.floats` within declared bounds:
  - (a) Dimension invariance: rescale all inputs to other unit systems and compare outputs.
  - (b) Conservation: energy balance closes, ε ≤ 1, q ≤ q_max = C_min·ΔT_max, T_surface between the sink and source temperatures.
  - (c) Monotonicity: superheat increases with flux and decreases with k_eff; ΔP increases with L; breakthrough pressure decreases with d_pore.
  - (d) Limiting cases: Bi→0 gives the lumped result; Ste→0 gives the Neumann solution; Kn→0 gives molecular diffusion; Kn→∞ gives Knudsen.
  - (e) Regime-sign checks (θ>90°).
  - (f) Determinism.
- **Verification ladder per template** (V&V 20-style statement in a metadata block):
  - Code verification: analytic or manufactured solution, plus observed convergence order for the numerical solvers (TPL-02, TPL-08 axial conduction).
  - Solution verification: mesh/timestep refinement, giving u_num.
  - Validation: at least 2 literature data points with E and u_val.
  - Report "validated range" ≠ "valid regime".
  - v9's "≥3 textbook problems within 1%" is code verification only, not validation.

### Gaps
- No published, independent Pint vs unyt vs astropy benchmark on current versions was found. Run `timeit` locally if this matters, though at FLBDS's call rate (tens of designs per run) it almost certainly does not.
- I found no published example combining Hypothesis with physics metamorphic relations, only the separate literatures.
- The full V&V 10/20 texts are paywalled and were not read; equations above come from secondary slides.

---

## Q3. Multi-fidelity verification: screen as a provable relaxation (no false negatives) and an independent scorer; agreement metrics

### Takeaway
A screen is safe to use for feedback only if it is a *necessary condition* of the scorer, i.e. screen_fail ⇒ eval_fail. Build it from bounds that hold regardless of detail: first-law and second-law limits, ε ≤ 1, best-case material or geometry. Then test the implication property-wise. Independence needs a separate implementation, not shared helpers. Measure fidelity agreement with a confusion matrix plus rank correlation, and report false-assurance and false-rejection rates.

### Cited Findings
- The multifidelity survey frames the low-fidelity model as giving speed-up "while the high-fidelity model is kept in the loop to establish accuracy and/or convergence guarantees". It classifies methods into adaptation, fusion and **filtering**; the FLBDS screen is a filter — [Peherstorfer, Willcox & Gunzburger, SIAM Review 2018 / arXiv 1806.10761](https://arxiv.org/pdf/1806.10761).
- Interruptible direct search screens points for infeasibility at low fidelity when "the infeasibility of each individual constraint can be detected at lower fidelities" — [GERAD G-2026-01 / arXiv 2601.06321](https://www.arxiv.org/pdf/2601.06321). It is the closest literature to "screen = cheap infeasibility detector". I did not confirm a formal no-false-negative guarantee in it.
- Probability-of-feasibility approaches in constrained multi-fidelity BO need a feasibility threshold that "cannot be chosen systematically and is sensitive to noisy data". In other words, probabilistic screens can wrongly reject feasible designs — [arXiv 2503.01126](https://arxiv.org/html/2503.01126v2).
- An industry harness study found about a 20-point gap between execution-based and field-level (physical) scoring on FoamBench. It recommends that benchmarks report execution success, benchmark success and physical validity separately — [arXiv 2609.03718](https://arxiv.org/html/2609.03718). This is the same issue as FLBDS PVR_screen vs PVR_eval.
- FLBDS empirics (digest §5.1–5.2): screen feedback gives 34/60, eval (Oracle) feedback 33/60, and the screen→eval gap is 3.3 pts. So a lumped screen is as good as the coupled solver *for guiding generation*. But B3's PVR_screen < PVR_eval shows the current screen is not a relaxation.

### Inferences (design recipe)
- **Screen = necessary conditions only**, each a theorem-like bound. Examples:
  - TPL-02: stored energy ≤ (ρL + ρc_pΔT)·thickness at the best k.
  - TPL-08: q ≤ C_min·ΔT_in; ΔP ≥ laminar f·Re lower bound.
  - TPL-09: net cooling ≤ εσ(T_s⁴ − T_sky⁴) with α=0.
  - TPL-10: head ≤ 4γ|cosθ|/d only if θ>90°, else fail.
  - Hard caps from the card.
  
  Any approximation that could be *stricter* than the eval (e.g. the TPL-08 A = D_h² shortcut) must move to the eval or be replaced by a bound. Template admissibility and ground-truth lists must not be in the screen.
- **Relaxation property test.** Sample designs with Hypothesis or a Sobol design over declared bounds, run both tiers, and assert `not screen.passed ⇒ not eval.passed`. Any counterexample is a screen bug. This turns "no false negatives" from a claim into a CI gate. Optionally, use interval arithmetic (e.g. `mpmath.iv`) on the closed-form bounds to handle parameter uncertainty conservatively.
- **Independence.** The eval must not import screen helpers (it currently shares `compute_duct_pressure_drop`/`compute_ergun_pressure_drop`). Better still, the hidden scorer is a different model class (1D/2D FE via scikit-fem, ε-NTU with a different correlation, CoolProp properties) or a second author's implementation. Shared code means shared bugs, as the TPL-10 abs(cos) bug sits in both tiers.
- **Agreement metrics to report per template:**
  - 2×2 confusion (screen vs eval) on a fixed design sample, giving false-assurance = P(screen pass ∧ eval fail) and false-rejection = P(screen fail ∧ eval pass). The latter must be 0 by construction.
  - Kendall τ or Spearman ρ between screen and eval margins.
  - Relative error of the key output (e.g. superheat 26.5 vs 35.3 K). The closed form is conservative in that case, which is acceptable.
  - Calibration of margins across the sample.
  - The same table vs a third-fidelity spot check (2D FE) on about 30 designs, which the proposal already plans as Q6.

### Gaps
- No source was found giving a general methodology for *certified* (provably conservative) lumped screens for heat and mass transfer design. Rigorous reduced-basis a-posteriori error bounds exist in the RB literature but were not searched this session.

---

## Q4. Open tools for slightly higher-fidelity checks callable from Python — speed vs complexity

### Takeaway
For FLBDS's 1D/2D TFP templates, the cheapest credible upgrade path is SciPy plus scikit-fem (pure Python, pip-install, BSD) for 1D/2D conduction, diffusion or Darcy, and CoolProp (low-level AbstractState) for fluid properties. FEniCSx, OpenFOAM/PyFoam, CalculiX and Modelica add install and run-time cost that this project's templates do not need. Use them only for a one-off independent validation subset (e.g. the planned 2D FE re-check), not in the generation loop.

### Cited Findings
- **scikit-fem:** pure interpreted Python on NumPy/SciPy, "easy and portable" installation. It focuses on assembly rather than the whole FEM workflow, is BSD-3, and claims "reasonable performance". Timings depend on element, quadrature and solver — [JOSS 10.21105/joss.02369](https://joss.theoj.org/papers/10.21105/joss.02369); [PyPI](https://pypi.python.org/pypi/scikit-fem).
- **CoolProp:** `PropsSI` (high-level) is the slow path. Docs advise reusing a single `AbstractState`; tabular backends only pay off through the low-level interface. The SVDSBTL backend reports under 200 ns/call single-phase and about 1–1.5 µs/call near saturation — [CoolProp tabular docs](https://coolprop.org/coolprop/Tabular.html); [SVDSBTL docs](https://coolprop.org/coolprop/SVDSBTL.html). A user reported 100 `HAPropsSI` humid-air calls taking 8.9 s — [coolprop-users thread](https://groups.google.com/g/coolprop-users/c/XY9L9bmj6Bg). This is relevant for TPL-03 evaporation/condensation: cache or tabulate it.
- **PyBaMM model hierarchy** is a template for "honest fidelity ladders". One docs run gives DFN 267 ms, SPMe 38 ms and SPM 21 ms. The first solve includes significant solver setup — [PyBaMM compare-lithium-ion](https://docs.pybamm.org/en/stable/source/examples/notebooks/models/compare-lithium-ion.html); [PyBaMM solvers notebook](https://docs.pybamm.org/en/stable/source/examples/notebooks/performance/03-pybamm-solvers.html). SPMe needs about 10% of DFN memory and is an ODE that allows larger time steps than the stiff DAE — [arXiv 1905.12553](https://arxiv.org/pdf/1905.12553). The pattern worth copying: one parameter set and one `Model` interface, several fidelities selectable by name, all tested against each other.
- **FEniCSx** works in LLM-agent pipelines (MechAgents and ALL-FEM generate FEniCS code; see Q5). The MCP-SIM benchmark (12 FEniCS tasks) is saturated at 100% for strong models — [arXiv 2609.03718](https://arxiv.org/html/2609.03718).
- **OpenFOAM** cases need several repair rounds even for frontier agents (see Q5). FoamBench is the only CAE suite with field-level NMSE ground truth — [arXiv 2609.03718](https://arxiv.org/html/2609.03718).

### Inferences
- Tool tiering for FLBDS:

  | Tier | Use | Tools | Cost |
  |---|---|---|---|
  | Screen | Generation loop | Closed-form bounds, NumPy | µs–ms |
  | Hidden eval | Scoring | SciPy ODE/BVP, 1D FV (existing TPL-02), scikit-fem 1D/2D, CoolProp low-level | ms–s |
  | Audit | ~30 designs (Q6 2D FE re-check) | FEniCSx or scikit-fem 2D/3D | One-off |
  | Out of scope | — | OpenFOAM/PyFoam, CalculiX, Modelica/OpenModelica (OMPython/FMPy), SimScale (cloud, commercial) | — |

  OpenFOAM, CalculiX and Modelica only make sense if a template needs real CFD or structural FE. TFP scope does not.
- Cantera (kinetics/thermo) is only relevant if a combustion or reacting template is added. It is not needed for TFP.

### Gaps
- No measured per-call timings for scikit-fem, FEniCSx, PyFoam/OpenFOAM, CalculiX, OpenModelica or Cantera were retrieved this session. Install footprint and speed claims for these remain qualitative. SimScale API pricing and latency were not checked.

---

## Q5. Prior work on LLMs writing or selecting physics models (2023–2026) and failure rates — should templates stay hand-written?

### Takeaway
LLM agents now get simulation code to *run* most of the time, but only after several execute-repair rounds. "Runs" overstates "physically correct" by about 20 points, and results on harder tool-specific tasks (FEABench/COMSOL) are about 20–33%. Consistency across repeated trials is much lower than best-of-k. For a research benchmark whose scorer must be trusted, templates and scorers should stay hand-written and verified. The LLM's role is selecting a template and proposing parameters, and possibly drafting new templates offline for human review.

### Cited Findings
- **MechAgents** (Ni & Buehler, 2023; Extreme Mechanics Letters): GPT-4 agent teams solve elasticity problems with FEniCS. In the paper's example, a two-agent team produced a script with incomplete geometry and a wrong weak form, while a larger team with a division of labour produced correct code — [arXiv 2311.08166](https://arxiv.org/abs/2311.08166v1).
- **ALL-FEM:** fine-tuned models in a multi-agent workflow with runtime feedback. The best (GPT-OSS-120B fine-tuned) reaches 71.79% code-level success on 39 FEniCS benchmarks (elasticity, plasticity, flow, FSI), above non-agentic GPT-5 Thinking — [arXiv 2603.21011](https://arxiv.org/html/2603.21011v1).
- **FEM-Bench:** the best model (Gemini 3 Pro) solved 30/33 FE-code tasks in at least 1 of 5 attempts, but only 26/33 in all 5. Joint test success was about 72–74% for GPT-5, Claude Opus 4.5 and Gemini 3 Pro — [arXiv 2512.20732](https://arxiv.org/html/2512.20732). An extension on 17 tasks reports 87.1% single-pass implementation success for the best model, but only 49.9% joint test success for the leading implementer. Pass@3 is 96.5% vs Pass^3 (all three succeed) 77.1% — [arXiv 2611.21176](https://arxiv.org/html/2611.21176v1). (Figures taken from search summaries; the 2611 paper was not opened.)
- **CAE harness study (2026):** a generic coding harness matches specialised agents. FoamBench success is 96.4% (Claude Opus 4.6), 92.5% (GPT-5.5) and 77.2% (Qwen3.5-Plus). FEABench (COMSOL, 15 tasks) is only 20–33% for every model and for the specialised system. Repair budget on FoamBench: R≤1 0.9%, R≤2 71.8%, R≤5 90.0%, R≤10 96.4%. Dominant failures are solver divergence or wrong fields, over-trusting tutorial settings, and missing hidden boundary conditions. There is about a 20-point gap between execution-based and field-level scoring. Tutorials (domain knowledge) were the main lever (80.9%→96.4%); scripted reflection added nothing (96.4% both). These are single runs with no CIs — [arXiv 2609.03718](https://arxiv.org/html/2609.03718).
- **Foam-Agent:** 88.2% on 110 OpenFOAM tasks (Claude 3.5 Sonnet) vs 55.5% for MetaOpenFOAM — [arXiv 2505.04997](https://arxiv.org/pdf/2505.04997). **ChatCFD** reports 82.1% vs MetaOpenFOAM 6.2% and Foam-Agent 42.3% on its own 205-case set. The benchmarks are not comparable, and the conflicting numbers show how definition-dependent "success" is — [arXiv 2506.02019](https://arxiv.org/html/2506.02019v2). CFDLLMBench's FoamBench defines success as *physically accurate* results — [CFDLLMBench via Foam-Agent v2, arXiv 2509.18178](https://arxiv.org/html/2509.18178v2).
- **PDE-Agents** reports 97.8% success over 1,369 production FE runs (85.4% first attempt). These are production-log figures, not a held-out benchmark — [arXiv 2606.07850](https://arxiv.org/html/2606.07850v2).
- **Physics reasoning benchmarks:** errors are dominated by wrong conditions or equations introduced in intermediate steps, and models have "limited capacity to detect or correct these mistakes" (PHYBench, per [PhysicsEval arXiv 2508.00079](https://arxiv.org/html/2508.00079v2)). In CMPhysBench, math/logic errors are 20–30% and unit errors under 2% — [arXiv 2508.18124](https://arxiv.org/pdf/2508.18124).
- FLBDS's own evidence (digest §5.3, §6.1): an agent-written transcript review contained parameter values that do not match the raw JSON (§5.4). With Qwen2.5-72B, 32/60 B3 first turns were malformed JSON. LLM-written *scorers* would bring the same reliability problem into the ground truth.

### Inferences
- Keep scorers hand-written, independently verified and frozen. An LLM-written scorer would make PVR_eval measure agreement between two LLM outputs, which breaks RQ1 (and H2 already uses "B2-Code, model-written verification code" as a *baseline*, so the project has already committed to this distinction).
- Decouple templates from operators and cases. A template is a reusable physics model with a declared validity domain; selection is done by the LLM (or a rule on the Problem Card's required function and regime), and the screen checks validity. This removes the 1:1 operator→template mapping (`flbds/m4/operators.py`).
- If more templates are needed (the test set has 12 new clusters), an LLM can *draft* a template offline from a textbook derivation. It is accepted only after it passes the Q2 contract: units, property tests, analytic cases, relaxation test vs its eval, and human sign-off. This matches the literature's "domain knowledge + execute/repair + human gate" pattern.

### Gaps
- No study was found that measures LLMs *selecting among pre-verified reduced-order models* (as opposed to writing code). This is FLBDS's actual setting and could itself be a minor contribution.
- Several 2026 figures (FEM-Bench extension, PDE-Agents) come from search summaries of preprints not fully read.

---

## Q6. Should parameter search be done by classical optimisers on the physics model rather than by the LLM? (brief)

### Takeaway
Yes for the continuous part. Let the LLM choose template, mechanism and variable ranges (discrete, knowledge-heavy). A classical constrained optimiser (SciPy SLSQP / differential evolution, Optuna, BoTorch) then finds a feasible parameter vector against the screen, and the hidden eval scores it. The evidence that LLMs beat well-tuned BO on continuous constrained design is weak; hybrids work best.

### Cited Findings
- On constrained multi-objective inverse design, the best LLM (WizardMath-7B) reaches GD 1.21 vs 15.03 for a BoTorch Ax baseline, but BoTorch qEHVI reaches GD 0.0, i.e. it hits the ceiling — [arXiv 2511.00070](https://arxiv.org/pdf/2511.00070).
- A NeurIPS 2025 systematic comparison finds LLMs fail at SMILES molecular optimisation but excel at small protein motifs through knowledge-driven hypotheses. It concludes hybrids are the way forward — [NeurIPS 2025 poster 125488](https://neurips.cc/virtual/2025/125488).
- LLAMBO (LLM inside BO) trades compute for sample efficiency — [arXiv 2402.03921](https://arxiv.org/pdf/2402.03921). A study of LLMs for HPO attributes early LLM advantage to the default seed rather than the model's proposals — [alphaXiv 2606.21641](https://www.alphaxiv.org/abs/2606.21641.md).
- FLBDS evidence (digest §5.2, §6.1): models "only scale floats" under feedback. DEV-M2-S3 returns the identical failing design (358.9 Pa > 250 Pa) in all seeds, and models invert sizing derivatives (DEV-M3). These are exactly the failures a gradient or bounded optimiser on a µs-cost screen avoids.

### Inferences
- With µs–ms screens, an optimiser can do 10³–10⁵ evaluations per design for free on CPU. This also gives a *solver-optimised conventional design* baseline (already planned as Q2 in the proposal) and an exact satisfiability check per case (replacing the hand-patched `capacity_bound.py:131` hack).
- The benchmark question shifts from "can the LLM tune floats" to "does the LLM (+biology) pick a mechanism and template whose optimised design is feasible and better". That is closer to RQ1/RQ2 and less confounded by float-tuning noise. Detailed comparison is covered by another researcher.

### Gaps
- No head-to-head study of LLM vs classical optimiser on lumped thermal/fluid design problems was found.
