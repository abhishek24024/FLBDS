# FLBDS — from an organism photo to a physics-checked engineering design

FLBDS (Functional Bio-Inspired Design System) is a research pipeline for bio-inspired design. You give it a photo of an organism. It works out what the organism does and how, finds an engineering problem that mechanism could solve, and produces a design. Every design is checked against closed-form physics models and comes with a dimensioned blueprint.

Current version: **V11** (image-driven). Paper draft: [`docs/v11/paper/paper.pdf`](docs/v11/paper/paper.pdf).

## How it works

```
organism photo
   │
   ▼
1 PERCEIVE ─── BioCLIP 2 (zero-shot species ID) + Qwen3-VL-32B: structures, scale, candidate mechanisms
   │
   ▼
2 GROUND ───── mechanism cards with verbatim quotes from the literature
   │
   ▼
3 ANALOGISE ── physical-effect tag → physics card → problem library (with a scale / regime gate)
   │
   ▼
4 DESIGN ───── LLM chooses problem + physics card; differential evolution sets the numbers;
   │           the card checks every constraint and returns per-constraint margins
   ▼
5 BLUEPRINT ── JSON spec + parametric schematic (authoritative) + image render (illustrative)
   │
   ▼
6 EVALUATE ─── physics pass, rediscovery of the known application, BIO vs NO-BIO controls
```

The system runs in two modes:

- **Mode B (primary).** The system gets only the photo and chooses the problem itself.
- **Mode A.** An engineering problem is supplied along with the photo.

### Example: blue morpho butterfly (a real pilot run)

1. **Perceive.** Shown only the photo, the model identifies a *Morpho* butterfly. It proposes structural colour: the blue comes from nanostructured scales, not from pigment.
2. **Choose a problem.** It picks a fade-proof blue coating with no pigment: peak at 470 ± 10 nm, reflectance ≥ 0.5, total thickness ≤ 3 µm.
3. **Choose a physics card.** It picks the Bragg-reflector card, which is correct.
4. **LLM design.** The language model's own layer thicknesses put the reflection peak at about 330 nm, in the UV. Four repair turns did not fix it.
5. **Optimised design.** The optimiser's design (11 layer pairs, n = 1.92 / 2.16, layers about 57 nm) peaks within 4 nm of the target at 0.82 reflectance. Every constraint passes.

The full trace is in [`docs/v11/dataset_samples/pipeline_example_B06_morpho/`](docs/v11/dataset_samples/pipeline_example_B06_morpho/).

## Physics cards and problems

**Physics cards** ([`flbds/v11/cards/`](flbds/v11/cards/)). Each card is a cited, closed-form model with a design space, environment inputs and a `screen()` function that returns a margin for every constraint. There are 11:

| Domain | Cards |
|---|---|
| Thermal | phase-change storage, counter-current heat exchanger, radiative cooling |
| Structures | honeycomb sandwich panel, lattice truss |
| Fluids | riblet drag reduction |
| Adhesion | fibrillar (gecko-type) adhesive |
| Wetting | superhydrophobic surface |
| Optics | Bragg structural colour |
| Mass transfer | plastron membrane, fog-harvesting mesh |

**Problems** ([`flbds/v11/problems.py`](flbds/v11/problems.py)). There are 23 engineering problems. Each has numeric requirements taken from a standard, a product or a paper (for example ETSI, WHO PQS, ASHRAE, ASTM, IEC and ISO).

**Feasibility certificates.** Before a (problem, card) pair is used, [`flbds/v11/certify.py`](flbds/v11/certify.py) checks that a feasible design exists. The certificates are stored in [`flbds/v11/problem_feasibility.json`](flbds/v11/problem_feasibility.json).

## Results so far

The V11 numbers come from a pilot: 22 well-known organisms with 3 seeds each. Statistics use the organism as the unit, with paired sign-flip tests and bootstrap CIs.

| Experiment | Result |
|---|---|
| **V10 design loop** (48 certified thermal instances, Qwen2.5-72B) | A physics-feedback repair loop scored +30.6 points over a single attempt (p = 3×10⁻⁵, Holm-corrected). Spending compute on 3 samples × 7 repairs passed 70.8% of instances, against 41.0% for 24 independent samples. |
| **Species ID** (BioCLIP 2, zero-shot) | The correct species ranked first for 19/22 photos and in the top 5 for 21/22. |
| **Perception** (Qwen3-VL, photo only) | The organism's known application appeared in the model's top 5 for 71% of runs. |
| **End-to-end, Mode B** | Physics pass rate with the LLM loop alone was 24%. With optimiser polish it rose to 73%. Bio-led designs now pass as often as no-biology designs. |
| **Blueprints** (pairwise LLM judge, run in both orders) | BIO and NO-BIO designs were rated equally sound. BIO designs were rated more implementable (+0.39, p = 0.003). |

Two caveats:

- The pass rates are upper bounds until the newer cards pass their accuracy audit.
- The full write-up, including the limitations, is in the paper (§8–9).

## Repository layout

```
flbds/
  v11/            V11: physics cards, problem library, feasibility certifier, organism data
  v10/            V10: certified instance generator, LLM design loop, optimiser arm, statistics
  physics/        V10 thermal / fluid physics templates and the screening verifier
  m4/             SAPPhIRE causal graphs, typed graph-rewrite operators, conflict detector
  pipeline/       LLM extraction pipeline: relevance filter → card drafting (schema-constrained)
                  → agreement → verbatim evidence check → entailment critic → unit normalisation → dedup
  schema/         Pydantic schemas (mechanism card, problem card, role binding, verification report)
scripts/
  v11/            V11 experiments: perception, end-to-end Mode B, optimiser polish, judging, renders
  run_v10.py      V10 runner;  analyse_v10.py  paired analysis with Holm correction
docs/
  v11/            paper, results (JSONL), datasets, interfaces, meeting brief, dataset samples
  v10/            V10 paper and results (7B and 72B runs)
tests/            pytest suite
```

## Getting started

You need Python 3.10 or newer. The core package, the physics cards and the tests run on CPU.

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

Re-run the optimiser polish on the committed E3 results. This needs only a CPU and writes `docs/v11/results/e3b_summary.json`:

```bash
python scripts/v11/e3b_optimiser_polish.py docs/v11/results
```

Re-analyse the end-to-end pilot:

```bash
python scripts/v11/analyse_e3.py docs/v11/results
```

Re-certify problem feasibility:

```bash
python -m flbds.v11.certify
```

The GPU experiments in `scripts/v11/` and `scripts/run_v10.py` need:

- these packages, which are not in `pyproject.toml`: `torch`, `transformers`, `vllm`, `open_clip_torch`;
- local copies of the models: Qwen3-VL-32B-FP8, Qwen2.5-72B-Instruct, BioCLIP 2 and Qwen-Image.

Paths are passed as script arguments.

## Data

- [`docs/v11/DATASETS.md`](docs/v11/DATASETS.md) lists every dataset with its size and licence.
- [`docs/v11/dataset_samples/`](docs/v11/dataset_samples/) holds small readable samples: the gold organism set, PMC biology papers, USPTO patents, the problems and cards, and the morpho example.
- Large corpora and model weights are not in the repository.
- Photos are CC BY, CC BY-SA or public domain; the manifests give attribution.

## Project history

- **V9.** A literature-extraction pipeline plus SAPPhIRE graph operators for thermal and fluid design. An audit found the headline benchmark result was not reliable, because answers leaked into prompts. That led to V10.
- **V10.** A certified, leakage-free benchmark and a study of the design loop: physics feedback, optimiser polish and compute allocation. Paper: [`docs/v10/paper/paper.pdf`](docs/v10/paper/paper.pdf).
- **V11.** The current version: image-driven and biology-first, with six physics domains, Mode B, and parametric blueprints.

## Roadmap

- Benchmark on less-famous organisms and micrographs, where the model's memory of famous examples helps less.
- Build a mechanism-card store from PubMed Central open-access papers, with a knowledge graph tested as an ablation.
- Run choice-sensitive experiments that test whether the right organism steers the system to a mechanism that works.
- Measure novelty against prior art in patents and papers.
- Generate parametric schematics from the verified numbers.
