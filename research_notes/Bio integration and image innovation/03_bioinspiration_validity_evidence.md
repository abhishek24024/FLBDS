# 03 — Is biological inspiration a valid, productive source of engineering innovation? Evidence review

Compiled 2026-11-20 under a hard time limit. Web search hit a rate limit about halfway through, so some entries come from memory of the primary literature and were **not re-checked this session**. Every claim carries one of these tags:

- **[V]**: checked this session against the paper's abstract, full text, or an author-hosted copy.
- **[V-sec]**: checked this session, but only through a secondary page such as a press release or a citing paper.
- **[K]**: from memory of the primary paper, not checked this session. **Check the number before citing it.**

Status labels: **PR** = peer-reviewed journal, **PR-conf** = peer-reviewed conference, **PP** = preprint, **Grey** = interview, company or report.

---

## Q1. Controlled design studies: do biological analogies raise novelty, variety or quality?

### Takeaway
The controlled evidence leans positive, but it is **small, noisy and mostly about novelty**:

- Most studies find that biological stimuli raise **novelty and/or variety** compared with no stimulus or with engineered examples.
- Quality and feasibility gains are rarely significant, and feasibility can go down.
- Samples are small (N ≈ 12–61, often counted in teams).
- Effects depend on how the stimulus is presented and on the designers' biology knowledge.

The analogical-distance literature adds a caveat: "far" analogies, which biological ones usually are, raise novelty but can lower quantity and quality. One large field study (OpenIDEO) found that **nearer** sources predicted better ideas. **Defensible claim:** biology is a reliable source of *distant, non-fixating* stimuli. It is not a guaranteed quality booster.

### Cited findings
- **Wilson, Rosen, Nelson & Yen (2010), Design Studies 31(2):169–186** — [PR] [The effects of biological examples in idea generation](https://experts.nau.edu/en/publications/the-effects-of-biological-examples-in-idea-generation/) (doi:10.1016/j.destud.2009.10.003).
  - Three groups: no example, human-engineered example, biological example.
  - Biological examples **raised novelty without lowering variety**. Human-engineered examples **lowered variety**, which points to fixation [V-sec].
  - Chan et al. (2015) re-read it as showing *no novelty advantage of far over near* sources, only a variety penalty for near ones [V-sec].
  - The exact N was not retrieved because of the paywall. Check the full text.
- **Nelson, Wilson & Yen (2009), FIE conference** — [PR-conf] [A study of biologically-inspired design as a context for enhancing student innovation](https://experts.nau.edu/en/publications/a-study-of-biologically-inspired-design-as-a-context-for-enhancin/).
  - Students in a BID course scored **+80% mean novelty vs control (significant)**.
  - Variety was **+37%, not significant**, with a small N [V-sec].
- **Keshwani, Lenau, Ahmed-Kristensen & Chakrabarti (2017), J. Engineering Design 28:654–680** — [PR] [postprint](https://researchonline.rca.ac.uk/3743/1/2016JEDKESHWANIpost_print_version_Comparing_novelty_of_designs_from_biological_inspiration_with_those_from_brainstorming.pdf). [V] from the full text:
  - Design: 4 studies (India, Denmark ×2, Norway), **N = 61 participants in 16 teams**. Concepts: 66 from biocards and 114 from brainstorming.
  - Novelty was scored with SAPPhIRE-based metrics.
  - **Average novelty N[NCS] was higher with biocards** (Wilcoxon W = 30, p = 0.0512, treated as marginally significant).
  - **Proportion of high-novelty concepts: no significant difference** (W = 53).
  - Biocard concepts were ideated at higher abstraction (organ level) more often.
  - The authors blame participants' limited biology knowledge.
- **Sharma, Gururani & Sarkar (2023), AI EDAM 37:e14** — [PR] [Measuring ideation effectiveness in bioinspired design](https://www.cambridge.org/core/product/identifier/S0890060423000070/type/journal_article). [V] from the abstract and text:
  - Design: N = 12 (6 bio-aided with 26 biological analogies, 6 control).
  - **Variety was significant** (Mann–Whitney U = 49, p < 0.05).
  - Not significant: novelty (+7%, p = 0.70), quality (+8%, p = 0.28), quantity (2.5 vs 2.0 concepts, t = 1.16, p = 0.27).
  - The groups differed in experience (2.1 vs 4.5 years).
- **Kang et al., BioSpark (CHI 2025)** — [PR-conf; also PP [arXiv 2503.09838](https://arxiv.org/html/2503.09838v1)], doi:10.1145/3706598.3714053. [V]:
  - Design: within-subjects, **N = 12**, two 20-minute tasks. Baseline = AskNature + ChatGPT, so the comparison is tool vs tool, not biology vs no biology.
  - Expert-rated quality: 6.5 vs 4.5 (regression coefficient 2.04, p < .0001).
  - Novelty: 7.1 (SD 1.03) vs 3.9 (1.67). Value: 7.0 vs 3.8. **Feasibility was lower: 5.7 vs 6.8.**
  - Ideas: 10.3 vs 5.5 (p = .04). Unique species used: 8.2 vs 4.6 (p = .007).
  - Inter-rater ICC: 0.94 for novelty, 0.74 for feasibility.
  - No standardized effect sizes are reported. From the SDs, novelty d ≈ 2.3, which is implausibly large and probably inflated by a weak baseline and N = 12.
  - Precursor: [NeurIPS 2023 workshop, arXiv 2312.11388](https://arxiv.org/abs/2312.11388) [PP].
- **Zhu, Zhang & Luo (2022/23), GPT-3 bio-inspired concept generation** — [PP] [arXiv 2212.13196](https://arxiv.org/pdf/2212.13196). The authors say their evaluation by 10 engineers is too small for statistical significance [V-sec].
- **Analogical distance (not specific to biology):**
  - **Chan et al. (2011), J. Mech. Des. 133:081004** [PR] [K]. Far-field patent stimuli gave **more novel but fewer** ideas than near-field ones [V-sec]. Uncommon examples raised novelty.
  - **Fu, Chan, Cagan, Kotovsky, Schunn & Wood (2013), J. Mech. Des. 135:021007**, "The meaning of 'near' and 'far'" [PR]. Distance was computed from a Bayesian model of patent-text structure. Far stimuli gave lower quality and novelty than near ones, i.e. "too far" exists. A moderate distance looked best [V-sec, exact statistics not retrieved].
  - **Chan, Dow & Schunn (2015), Design Studies 36:31–58** [PR] ([preprint](https://joelchan.github.io/files/2014-desstudies-nearfar-manuscript.pdf)). In OpenIDEO data (>350 participants, 12 challenges, distance from LDA topic models), **conceptually nearer cited sources predicted shortlisting**. This directly contradicts the "far is better" view [V-sec].
- **Fixation:**
  - **Jansson & Smith (1991), Design Studies 12:3–11** [PR] [K]: examples induce fixation.
  - **Linsey et al. (2010), J. Mech. Des. 132:041003** [PR] [K]: engineering faculty fixated on a provided example.
  - **Toh & Miller (2014), J. Mech. Des.** [PR]: physical examples reduce novelty and variety [V-sec].
  - **Toh & Miller (2016), Research in Engineering Design**, "Choosing creativity" [PR]: risk aversion drives designers to select conventional concepts [V-sec].
  - Implication: a biological stimulus helps partly because it is *surface-dissimilar*, so it fixates less (Wilson 2010).
- **Process studies:**
  - **Helms, Vattam & Goel (2009), Design Studies 30(5):606–622** [PR] ([lab page](https://dilab.gatech.edu/publications/biologically-inspired-design-process-and-products)). It identifies two processes: *problem-driven* (start from the design problem) and *solution-based* (start from a biological case). It also catalogues recurrent errors [K]: fixating on a single biological solution, misapplied analogies, poor problem definition, and oversimplifying complex functions.
  - A 2021 **Design Science** meta-analysis of BID case studies ([link](https://www.cambridge.org/core/product/154F3753DF4E95D9DFE0E7344E3D4542/core-reader)) [PR] found that solution-based BID yields multifunctional designs more often [V-sec].
  - **Mak & Shu (2008), Res. Eng. Des. 19:21–28** [PR] [K]: designers fixate on surface features of biological text descriptions.

### Gaps
- No pre-registered RCT. No meta-analysis of biology-vs-control effect sizes. Most studies are N ≤ 61 and use student participants.
- Effect sizes are rarely reported. Novelty metrics differ across studies (SAPPhIRE, Shah–Vargas-Hernandez, expert Likert), so results cannot be pooled.
- No study isolates **"biological content" from "distant content"**. A matched-distance non-biological analogy control is missing in every study found here.
- LLM-era studies compare tools, not biology vs no biology, and test only 1–2 problems.

---

## Q2. Patent and innovation-output evidence

### Takeaway
The bibliometric and patent evidence shows **rapid growth in activity**, not superior impact:

- Papers grew from fewer than 100 a year (1990s) to several thousand a year (2000s).
- Patents grew along an S-curve.

No study found here compares forward citations or novelty of bio-inspired vs matched non-bio-inspired patents. This is a real gap that the proposal can fill. A targeted search for "bio-inspired patent forward citations vs controls" returned only proxies, such as science-linked patents getting more citations.

### Cited findings
- **Bonser & Vincent (2007), Proc. IMechE Part C 221(10):1177–1180**, doi:10.1243/09544062JMES522 — [PR] [Technology trajectories, innovation and the growth of biomimetics](https://researchportal.bath.ac.uk/en/publications/technology-trajectories-innovation-and-the-growth-of-biomimetics/).
  - Biomimetic patenting follows a **sigmoid growth curve**.
  - Analysed with TRIZ: inventiveness levels fall as a technology matures [V-sec from the abstract].
  - A later paper by Vincent's group cites it for a peak of **1,666 granted US patents in 2004**. The same paper shows that counts depend on the database: 6,199 EPO hits vs 5,786 PatentInspiration hits for the same terms [V-sec; check the primary].
- **Bonser (2006), J. Bionic Eng. 3:39–41**, "Patented biologically-inspired technological innovations: a twenty year view" [PR] [K]. Reports a faster rise in bio-inspired patents than in patents overall.
- **Lepora, Verschure & Prescott (2013), Bioinspir. Biomim. 8:013001** — [PR] [The state of the art in biomimetics](https://eprints.whiterose.ac.uk/id/eprint/155159/7/Lepora%202013%20BB%20State-of-the-Art%20preprint.pdf).
  - Bibliometric and network analysis of publications.
  - Growth from **<100 papers a year in the 1990s to several thousand a year in the 2000s** [V].
  - Topic clusters are dominated by robotics, materials and sensing.
- **Vincent, Bogatyreva, Bogatyrev, Bowyer & Pahl (2006), J. R. Soc. Interface 3:471–482**, "Biomimetics: its practice and theory" [PR] [K]. It maps biological and technological solutions onto TRIZ principles.
  - Biology solves problems mainly by information and structure; engineering mainly by energy and substance.
  - The two solution sets overlap only about 12%.
  - This is the strongest quantitative argument that biology is a **non-redundant** solution space.
- **Snell-Rood (2016), Nature 529:277–278**, "Bring biologists into biomimetics" [PR comment] [K]. Argues that few bio-inspired papers and patents involve biologists.
- **Fermanian Business & Economic Institute (2010)**, "Bioinspiration: an economic progress report" [Grey] [K]. Projected a large US GDP contribution by 2025. This is advocacy, not evidence; cite it only as the hype benchmark.

### Gaps
- No impact study with matched controls (same CPC class, year and assignee type).
- Patent sets defined by keyword, e.g. "biomimetic" or "inspired by", miss uncited bio-inspiration and include marketing claims.
- No study tracks bio-inspired patents to **commercial or performance outcomes**.
- **A study this project could run:** classify patents by citation to biological literature or by bio-terms in claims, then compare forward citations, CPC-combination novelty (Uzzi-style atypicality) and disruption (CD index) against propensity-matched controls.

---

## Q3. Canonical successes vs independently measured performance

### Takeaway
The canonical cases fall into three groups:

| Group | Cases | What the evidence shows |
|---|---|---|
| Independently measured, holds up | Riblets, gecko-type adhesives, lotus superhydrophobicity, tubercle stall delay | Peer-reviewed lab measurements support the effect, though only in a bounded regime |
| Anecdotal | Shinkansen, Eastgate | Company or architect figures only; no peer-reviewed measurement found |
| Biology misunderstood | Namib beetle, boxfish car, woodpecker shock absorber, termite ventilation model | The engineering artefact may still work, but the biological story behind it was wrong |

Velcro is a true case of biological origin, but its performance was never compared with burdock.

### Cited findings
- **Sharkskin and riblets.**
  - Bechert et al. (1997), **J. Fluid Mech.** [PR] ([abstract](https://cambridge.org/core/journals/journal-of-fluid-mechanics/article/abs/experiments-on-dragreducing-surfaces-and-their-optimization-with-an-adjustable-geometry/16FACE9E75678D170A4ECCC7990C8158)) reported a **record 9.9% skin-friction reduction** for optimized blade riblets in an oil channel [V]. Optimal spacing is s⁺ ≈ 10–20 [V-sec].
  - The effect is regime-bound. It disappears or reverses outside the optimal s⁺, which is a textbook regime check.
  - Oeffner & Lauder (2012), **J. Exp. Biol. 215:785** [PR] ([pdf](https://sites.harvard.edu/glauder/files/2022/03/Oeffner.Lauder.2012.pdf)): flexible real shark-skin foils swam **12.3% faster** than with denticles removed, and rigid skin showed no effect. **Speedo Fastskin FSII showed no consistent speed increase.** A riblet film gave **+7.2%** [V].
- **Gecko.**
  - Autumn et al. (2000), **Nature 405:681** [PR]: single-seta shear about **194 ± 25 µN (N = 28), ~10× whole-animal prediction** [V-sec].
  - Bartlett et al. (2012), **Adv. Mater. 24:1078** [PR] ([PubMed](https://www.pubmed.gov/22278804/)): "Geckskin" reached **2,950 N (29.5 N/cm²)** reversible force capacity. It works through a draping-fabric/tendon design rather than fibrils, so the biology that mattered was not the famous one [V].
- **Lotus.** Barthlott & Neinhuis (1997), **Planta 202:1–8** [PR]: Nelumbo adaxial contact angle **160.4 ± 0.7° (n = 20)**. Particles are removed by rolling drops [V-sec]. Facade products exist, but long-term field self-cleaning under abrasion and UV degrades [K].
- **Humpback tubercles.**
  - Miklosovic, Murray, Howle & Fish (2004), **Phys. Fluids 16:L39** [PR] ([pdf](https://math.wcupa.edu/sciences-mathematics/biology/fFish/documents/2004PF-Megaptera.pdf)): scale flipper model, NACA 0020 section. **Stall angle delayed by ~40%**, with higher maximum lift and lower post-stall drag [V].
  - The press-release "32% less drag" and "8% more lift" figures are condition-specific [V-sec].
  - Contested: Johari et al. (2007), **AIAA J. 45:2634** [PR] [K] found that on 2-D airfoils tubercles **reduce pre-stall lift** and soften stall rather than giving a free gain.
- **Kingfisher → Shinkansen 500-series.**
  - The only sources are an interview and company figures: "air pressure −30%, electricity −15%, speed +10%" (Nakatsu, 2005 interview) [Grey, V-sec].
  - A secondary account cites a **13% power reduction measured on a 270 km/h run** [Grey].
  - No peer-reviewed paper attributing the tunnel-boom mitigation to the bird analogy was found. Tunnel-boom physics depends mainly on nose length and the rate of change of cross-sectional area. **Status: plausible, but the analogy's causal role is unverified.**
- **Termites → Eastgate (Harare, 1996).**
  - The building was designed on a thermosiphon/stack model of mound ventilation.
  - King, Ocko & Mahadevan (2015), **PNAS 112:11589** [PR] ([pdf](https://dash.harvard.edu/bitstream/handle/1/23603185/MahadevanTermite2015.pdf?sequence=1)) measured mound airflow directly. Ventilation is **driven by diurnal temperature oscillations**: a convection cell that reverses between day and night [V].
  - J. S. Turner states the Eastgate design rested on a wrong conception of termite thermoregulation [V-sec, ASME article]. See Turner & Soar (2008), "Beyond biomimicry" [PR-conf] [K].
  - The building's energy claims (often "~10% of a conventional building's energy" and "10% lower build cost") come from the architect and engineers [Grey].
- **Namib beetle.**
  - Parker & Lawrence (2001), **Nature 414:33** [PR] [K]: hydrophilic bumps on a waxy hydrophobic background collect fog.
  - Nørgaard & Dacke (2010), **Front. Zool. 7:23** [PR] ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2918599)): differences in collection efficiency between beetles with very different elytra structures were **minor**. Behaviour (fog-basking) matters more than structure. The well-known fog-basking species lack the bumps [V].
  - Hamilton et al. re-identified the Parker & Lawrence beetle as *Physasterna cribripes*, a species that does not fog-bask [V-sec].
  - The engineered bumpy surfaces may still work, but the **biological attribution is contested**.
- **Boxfish → Mercedes-Benz Bionic concept car (2005).** Van Wassenbergh et al. (2015), **J. R. Soc. Interface 12:20141146** [PR] ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4305415)) combined flow-tank measurements and CFD. They found **consistently destabilizing** yaw moments, rejecting the self-stabilization theory, and a drag coefficient higher than assumed [V].
- **Woodpecker → shock-absorber designs.** Van Wassenbergh et al. (2022), **Curr. Biol. 32:3189** [PR]: high-speed video of three species shows the head acts as a **stiff hammer, not a shock absorber**. Brain deceleration of about 400 g stays below concussion thresholds [V-sec].
- **Morpho structural colour.** Vukusic et al. (1999), **Proc. R. Soc. B 266:1403** [PR] [K] quantified multilayer interference and diffraction in single scales. Potyrailo et al. (2007), **Nature Photonics 1:123** [PR] [K] used Morpho scales as selective vapour sensors.
- **Honeycomb and bone.** Hales (2001), **Discrete Comput. Geom. 25:1** [PR] [K] proved that the hexagonal partition minimizes perimeter, a purely mathematical result. Bone/tree "growth rule" optimization (Mattheck's CAO/SKO) is an algorithmic analogy [K]. Lattice performance should be credited to mechanics (Gibson–Ashby scaling), not to biology per se.

### Gaps
- Few independent field measurements of deployed products (Shinkansen, Eastgate, Lotusan, WhalePower fans).
- Company claims have not been checked against matched baselines with the same Reynolds number, load and climate.
- The pre-stall penalties and degradation over time are under-reported.

---

## Q4. Critiques and failure modes, and what they mean for evaluation

### Takeaway
There are five recurring failure modes:

1. **Superficial (surface-feature) analogy** (Mak & Shu 2008; Helms et al. 2009).
2. **Scale or regime mismatch**: riblets only work in a narrow s⁺ window, and tubercles help post-stall but hurt pre-stall.
3. **Wrong biology** (beetle, boxfish, termite, woodpecker).
4. **Fixation and risk-aversion** at selection time (Toh & Miller 2016).
5. **Hype, or retro-labelling** conventional engineering as "bio-inspired".

An automated pipeline should therefore score a bio-inspired idea **on physics, not provenance**. It needs:

- dimensionless-group and regime checks (Re, s⁺, Bond and capillary number, scale exponents);
- a mechanism-transfer check, i.e. is the same physical principle invoked in source and target;
- a biology-fidelity check against primary measurement papers.

### Cited findings
- Regime-bound effects: Bechert et al. 1997 (riblet s⁺ window) [V]; Johari et al. 2007 (tubercles pre-stall) [K]; Oeffner & Lauder 2012 (only flexible skin works) [V].
- Biological misreadings: Nørgaard & Dacke 2010 [V]; Van Wassenbergh et al. 2015 and 2022 [V]; King et al. 2015 [V].
- Human-process errors: Helms, Vattam & Goel 2009 [PR]; Mak & Shu 2008 [K].
- "Too far" analogies hurt: Fu et al. 2013 [V-sec]; Chan, Dow & Schunn 2015 [V-sec].
- Disciplinary gap: Snell-Rood 2016 [K]; Lepora et al. 2013 [V].
- Feasibility trade-off in LLM-assisted BID: BioSpark feasibility 5.7 vs 6.8 for the baseline [V].

### Gaps
- No published taxonomy maps failure modes to rates; how often is each one fatal?
- No benchmark of "bio-inspired claims" with physics-verified labels exists. The cases table below is a seed for one.

---

## Q5. Showing biology helps in an automated pipeline without human raters

### Takeaway
Combine three designs:

- **(a) Rediscovery:** can the system recover known organism→engineering pairs from the problem alone, with ground truth held out?
- **(b) Causal ablation:** matched biology vs mismatched biology vs a distance-matched non-biological analogy vs no analogy, scored by automatic metrics.
- **(c) Dose-response on analogical distance.**

All scoring should use physics verifiers and embedding-based novelty, not raters. This design follows the gaps above: no human study controls for *distance* separately from *biology*.

### Proposed designs (grounded in the cited literature)
1. **Rediscovery benchmark (ground truth = table below).**
   - Input: the engineering problem with the solution's domain terms masked, e.g. "reduce turbulent skin friction on a hull" with no mention of riblets or shark.
   - Metric: Recall@k of the correct organism *and* mechanism; mechanism-level match matters more than organism name.
   - Leakage controls: (i) use problems written after the model's cutoff, or paraphrase-perturbed problems; (ii) a contamination probe asking the model to name the case directly, and report results with and without contamination; (iii) counterfactual cases (e.g. boxfish stabilization) where a **correct** system should *reject* the folk analogy.
2. **Four-arm causal ablation per problem:**
   - (A) mechanism-matched biological analogy;
   - (B) mismatched biology: right domain, wrong function;
   - (C) non-biological analogy matched on embedding distance to (A), the arm missing from Wilson 2010 and Keshwani 2017;
   - (D) no analogy.
   Run ≥3 seeds per arm. Outcomes are below. Biology "helps" only if A > C at matched distance.
3. **Automatic outcomes (no raters):**
   - Novelty: embedding distance to a prior-art corpus of patents and papers before a cutoff date; CPC-combination atypicality.
   - Variety: number of clusters per problem (Shah-style variety via clustering).
   - Validity: pass rate on physics/regime checks, i.e. dimensionless groups inside the regime where the source mechanism is documented.
   - Optional: surrogate simulation, e.g. a panel method for a tubercle foil or Wenzel/Cassie prediction for wetting.
4. **Analogical-distance dose-response.** Bin stimuli by distance in topic or embedding space (as in Fu 2013 and Chan 2015) and test for an inverted-U in validity × novelty. This would replicate "too far" in silico.
5. **Retrospective patent test (from Q2).** For problems posed as of year T, check whether pipeline outputs anticipate patents granted after T. Compare bio-arm vs control-arm hit rates, using the date as a natural holdout.
6. **Statistics.** Treat problems as the unit of analysis; use mixed-effects models with problem as a random effect. Pre-register the primary metric (validity-weighted novelty). Report effect sizes with 95% CIs and ≥3 seeds.

### Gaps
- Embedding-based novelty has not been validated against expert novelty in BID specifically. A small calibration subset is advisable, even though the main pipeline uses no raters.
- Contamination of LLMs with canonical cases makes naive rediscovery uninformative. The counterfactual and post-cutoff controls are required.

---

## Citable sentences (with sources)
1. In a three-arm study, biological examples increased idea novelty without reducing variety, whereas human-engineered examples reduced variety (Wilson, Rosen, Nelson & Yen, 2010, *Design Studies* 31:169–186).
2. Across four studies (N = 61, 16 teams), concepts ideated with biological "biocards" had higher average novelty than brainstorming concepts (Wilcoxon W = 30, p = 0.051), but the proportion of highly novel concepts did not differ significantly (Keshwani et al., 2017, *J. Eng. Des.* 28:654–680).
3. In a within-subjects study (N = 12), an LLM-based biological-analogy tool roughly doubled the number of ideas (10.3 vs 5.5) and expert-rated novelty (7.1 vs 3.9) relative to an AskNature-plus-ChatGPT baseline, though feasibility ratings fell (5.7 vs 6.8) (Kang et al., BioSpark, CHI 2025).
4. Analogical distance trades novelty against quality: far-field stimuli yield more novel but fewer ideas (Chan et al., 2011, *J. Mech. Des.*), and in an OpenIDEO field dataset conceptually nearer sources predicted shortlisted concepts (Chan, Dow & Schunn, 2015, *Design Studies* 36:31–58).
5. Biomimetics publications grew from under 100 papers a year in the 1990s to several thousand a year in the 2000s (Lepora, Verschure & Prescott, 2013, *Bioinspir. Biomim.* 8:013001), and biomimetic patenting follows a sigmoid technology-growth trajectory (Bonser & Vincent, 2007, *Proc. IMechE C* 221:1177–1180).
6. Optimized riblet surfaces reduced turbulent skin friction by up to 9.9% in controlled experiments (Bechert et al., 1997, *J. Fluid Mech.*), but a commercial "sharkskin" swimsuit fabric produced no consistent swimming-speed gain (Oeffner & Lauder, 2012, *J. Exp. Biol.* 215:785–795).
7. Leading-edge tubercles modelled on humpback whale flippers delayed stall by about 40% in wind-tunnel tests (Miklosovic et al., 2004, *Phys. Fluids* 16:L39).
8. A gecko-inspired adhesive designed by scaling theory, not by copying fibrils, achieved reversible force capacities of 2,950 N (29.5 N/cm²) (Bartlett et al., 2012, *Adv. Mater.* 24:1078–1083).
9. Several iconic analogies rest on mistaken biology: boxfish carapaces are hydrodynamically destabilizing rather than self-stabilizing (Van Wassenbergh et al., 2015, *J. R. Soc. Interface* 12:20141146), and Namib darkling beetles' elytral structure contributes little to fog-collection efficiency compared with behaviour (Nørgaard & Dacke, 2010, *Front. Zool.* 7:23).
10. Termite mounds are ventilated by diurnal temperature oscillations rather than the steady stack effect assumed in popular accounts of the Eastgate Centre (King, Ocko & Mahadevan, 2015, *PNAS* 112:11589–11593).

---

## Canonical organism → engineering cases (ground-truth "rediscovery" set)

**Status column:**
- **Measured** = peer-reviewed measurement of the bio-derived artefact or mechanism.
- **Anecdotal** = interview or company figures only.
- **Contested** = the biology or the attribution has been disputed.
- **Neg** = a negative or counterfactual control; a good pipeline should flag or reject the folk analogy.

| # | Organism (common / scientific) | Structure | Mechanism / physical principle | Engineering application | Quantitative claim | Source | Status |
|---|---|---|---|---|---|---|---|
| 1 | Burdock / *Arctium lappa* | Hooked bracts on burrs | Mechanical interlock of hooks with loops/fibres | Hook-and-loop fastener (Velcro) | Patent: de Mestral, US 2,717,437 (1955); no quantitative bio-vs-product comparison | Patent [K] | Origin documented |
| 2 | Tokay gecko / *Gekko gecko* | Setae → spatulae; skin–tendon system | van der Waals contact splitting; load sharing via inextensible tendon | Dry reversible adhesives (Geckskin), climbing robots | Single seta ~194 µN (N = 28); Geckskin 2,950 N, 29.5 N/cm² | Autumn et al. 2000 *Nature* 405:681; Bartlett et al. 2012 *Adv. Mater.* 24:1078 [V] | Measured |
| 3 | Sacred lotus / *Nelumbo nucifera* | Hierarchical papillae + epicuticular wax | Cassie–Baxter superhydrophobicity; particle removal by rolling drops | Self-cleaning paints/glass (Lotusan) | Contact angle 160.4 ± 0.7° | Barthlott & Neinhuis 1997 *Planta* 202:1 [V-sec] | Measured (durability issues) |
| 4 | Sharks (various Carcharhinidae) | Ribbed placoid denticles | Streamwise riblets damp near-wall vortices at s⁺ ≈ 10–20 | Riblet films for aircraft and pipes | ≤9.9% skin-friction reduction; flexible skin +12.3% speed; FSII suit no effect | Bechert et al. 1997 *JFM*; Oeffner & Lauder 2012 *JEB* 215:785 [V] | Measured, regime-bound |
| 5 | Galápagos shark / *Carcharhinus galapagensis* | Denticle micro-topography | Topography-mediated reduction of microbial settlement | Sharklet antifouling/antibacterial surfaces | Reduced *S. aureus* biofilm colonization vs smooth PDMS | Chung et al. 2007 *Biointerphases* 2:89 [K] | Measured (lab) |
| 6 | Common kingfisher / *Alcedo atthis* | Long, wedge-shaped beak | Gradual cross-section change lowers pressure-wave steepness on entering a denser medium | Shinkansen 500-series nose (tunnel boom) | −30% air pressure, −15% electricity, +10% speed; 13% power cut measured at 270 km/h | Nakatsu interview 2005 [Grey, V-sec] | Anecdotal |
| 7 | Mound termites / *Macrotermes* spp., *Odontotermes obesus* | Mound with chimney + surface flutes | Diurnal thermal oscillation drives reversing convection | Passive ventilation (Eastgate Centre, Harare) | Mound: day/night flow reversal measured; building ~10% build-cost saving claimed | King, Ocko & Mahadevan 2015 *PNAS* 112:11589 [V]; ASME article [Grey] | Contested (design used the wrong model) |
| 8 | Namib darkling beetle / *Physasterna cribripes* (originally reported as *Stenocara* sp.) | Hydrophilic bumps on hydrophobic elytra | Patterned wettability nucleates and sheds droplets | Fog-harvesting surfaces | Collection efficiency differences across elytra types "minor" | Parker & Lawrence 2001 *Nature* 414:33 [K]; Nørgaard & Dacke 2010 *Front. Zool.* 7:23 [V] | Contested |
| 9 | Humpback whale / *Megaptera novaeangliae* | Leading-edge tubercles on flipper | Streamwise vortices keep flow attached after stall | Fans, turbine blades (WhalePower) | Stall angle +~40%; pre-stall lift penalty on 2-D foils | Miklosovic et al. 2004 *Phys. Fluids* 16:L39 [V]; Johari et al. 2007 *AIAA J.* 45:2634 [K] | Measured, regime-bound |
| 10 | Blue morpho / *Morpho* spp. (e.g. *M. rhetenor*) | Ridge-lamella multilayer scales | Thin-film interference + diffraction (structural colour) | Pigment-free colour fibres (Morphotex), vapour sensors | Quantified reflectance and angular spectra; vapour-selective response | Vukusic et al. 1999 *Proc. R. Soc. B* 266:1403; Potyrailo et al. 2007 *Nat. Photonics* 1:123 [K] | Measured |
| 11 | Moths (night-active Lepidoptera) | Sub-wavelength corneal nipple arrays | Graded refractive index suppresses reflection | Anti-reflection films, solar cells | Strong broadband reflectance reduction | Clapham & Hutley 1973 *Nature* 244:281 [K] | Measured |
| 12 | Blue mussel / *Mytilus edulis* | Byssal foot proteins rich in DOPA | Catechol/amine chemistry adheres wet | Polydopamine universal coatings, wet adhesives | Coating forms on virtually any substrate by dip-coating | Lee et al. 2007 *Science* 318:426 [K] | Measured |
| 13 | Orb-weaving spiders / *Araneus diadematus*; Darwin's bark spider *Caerostris darwini* | Dragline silk (β-sheet nanocrystals in amorphous matrix) | Hierarchical H-bonded crystals give strength + extensibility | Recombinant silk fibres, sutures | Toughness ~160 MJ/m³ (*A. diadematus*); ~350 MJ/m³ (*C. darwini*) | Gosline et al. 1999 *JEB* 202:3295; Agnarsson et al. 2010 *PLoS ONE* 5:e11234 [K] | Measured (bio); synthetic still falls short |
| 14 | Abalone / *Haliotis* spp. | Nacre "brick-and-mortar" aragonite tablets | Crack deflection, tablet sliding, organic bridges | Tough ceramic composites, bio-inspired glass | Work of fracture orders of magnitude above monolithic aragonite | Jackson, Vincent & Turner 1988 *Proc. R. Soc. B* 234:415 [K] | Measured |
| 15 | Yellow boxfish / *Ostracion cubicus* | Rigid keeled carapace | Claimed: self-stabilizing low-drag body. Measured: destabilizing moments aid manoeuvring | Mercedes-Benz Bionic concept car | Car Cd 0.19 claimed; fish drag higher than assumed | Van Wassenbergh et al. 2015 *J. R. Soc. Interface* 12:20141146 [V] | **Neg** (wrong biology) |
| 16 | Woodpeckers (Picidae) | Skull, hyoid, beak | Claimed: shock absorption. Measured: stiff hammer | Shock-absorbing helmets/packaging | ~400 g brain deceleration, below concussion threshold; no absorption observed | Van Wassenbergh et al. 2022 *Curr. Biol.* 32:3189 [V-sec] | **Neg** (wrong biology) |
| 17 | Barn owl / *Tyto alba* | Leading-edge comb, trailing-edge fringe, velvet | Porous/compliant serrated trailing edges scatter less sound | Low-noise fans, turbine blade serrations | Noise-scaling exponent change (U⁶ vs U⁵ for rigid edge) | Jaworski & Peake 2013 *JFM* 723:456 [K] | Measured (theory + experiment) |
| 18 | Firefly / *Photuris* sp. | Misfit-scale lantern cuticle | Index-matched sawtooth surface boosts light out-coupling | LED light-extraction overlayers | ~55% light-extraction gain claimed | Bay et al. 2013 *Opt. Express* 21:A179 [K] | Measured (lab) |
| 19 | Schooling fish (e.g. *Clupea*) | Vortex-street spacing in schools | Counter-rotating constructive wake interaction | Close-packed vertical-axis wind-turbine arrays | Field array ~21–47 W/m² vs ~2–3 W/m² for HAWT farms | Whittlesey, Liska & Dabiri 2010 *Bioinspir. Biomim.* 5:035005; Dabiri 2011 *J. Renew. Sust. Energy* 3:043104 [K] | Measured (small field array) |
| 20 | Sea cucumber / *Cucumaria frondosa* | Dermis with switchable collagen network | Chemically regulated stiffness via fibre–fibre coupling | Switchable-stiffness nanocomposites (neural probes) | ~40× modulus change on wetting | Capadona et al. 2008 *Science* 319:1370 [K] | Measured |
| 21 | Pitcher plant / *Nepenthes* spp. | Lubricated peristome | Liquid-infused slippery surface | SLIPS omniphobic/anti-ice coatings | Contact-angle hysteresis < 2.5° | Wong et al. 2011 *Nature* 477:443 [K] | Measured |
| 22 | Water fern / *Salvinia molesta* | "Eggbeater" hairs with hydrophilic tips | Pinned air layer (air retention under water) | Air-lubricated ship hulls | Long-term air retention under water; projected friction reduction | Barthlott et al. 2010 *Adv. Mater.* 22:2325 [K] | Measured (bio); hull claims projected |
| 23 | Lobsters / *Homarus* spp. | Square-channel reflecting eye | Grazing-incidence reflection focuses X-rays over a wide field | Lobster-eye X-ray optics (wide-field telescopes) | Wide field of view; flown in recent X-ray missions | Angel 1979 *Astrophys. J.* 233:364 [K] | Deployed |
| 24 | Pine cone / *Pinus* spp. | Bilayer scales with differing fibre orientation | Differential hygroscopic swelling (bilayer bending) | Humidity-driven actuators, adaptive facades | Curvature vs humidity follows the Timoshenko bilayer law | Reyssat & Mahadevan 2009 *J. R. Soc. Interface* 6:951 [K] | Measured |
| 25 | Venus flytrap / *Dionaea muscipula* | Doubly curved leaf lobes | Snap-through buckling instability | Fast snapping actuators, grippers | Closure ~100 ms via elastic instability | Forterre et al. 2005 *Nature* 433:421 [K] | Measured |
| 26 | Honeybee / *Apis mellifera* | Hexagonal comb | Hexagonal tiling minimizes perimeter per area | Honeycomb sandwich panels | Hexagon optimal (mathematical proof); panel performance follows Gibson–Ashby cellular-solid scaling | Hales 2001 *Discrete Comput. Geom.* 25:1 [K] | Math/mechanics (weak bio-causality) |
| 27 | Trees and trabecular bone | Load-adapted growth (Wolff/Mattheck) | Material added where stress is high and removed where low (uniform stress) | CAO/SKO shape and topology optimization, lattices | Notch-stress reduction in CAO-shaped parts | Mattheck & Burkhardt 1990 *J. Theor. Biol.* 143:99 [K] | Algorithmic analogy |
| 28 | Mosquito / *Aedes* spp. | Serrated, vibrating fascicles | Low-force insertion via serration and vibration | Low-pain microneedles | Reduced insertion force vs smooth needles | Izumi et al. 2011 *Sens. Actuators A* 165:115 [K] | Measured (lab) |

---

**Verification priority before submission:** rows marked [K]. Key figures are in rows 5, 13, 17–22 and 28; the Vincent et al. 2006 "~12% overlap" figure; and Wilson et al. 2010 N and statistics.
