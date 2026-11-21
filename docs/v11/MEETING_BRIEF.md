# FLBDS V11 — meeting brief (20 Nov 2026)

The full draft is at `docs/v11/paper/paper.pdf` (32 pages). Data samples are in `docs/v11/dataset_samples/`.

## 1. What we are building

**Goal.** Start from a picture of an organism. Find an engineering problem the organism's mechanism can solve. Produce a design that passes physics checks, with a blueprint someone could build from.

```
 organism photo ─► 1 PERCEIVE ─► 2 GROUND ─► 3 ANALOGISE ─► 4 DESIGN + VERIFY ─► 5 BLUEPRINT ─► 6 EVALUATE
 (Mode B: alone;   BioCLIP 2 ID   mechanism   effect tag →    LLM picks problem    JSON + param.   physics, rediscovery,
  Mode A: + a      + Qwen3-VL     cards with  physics card →  + card; optimiser    SVG (authori-   image/name ablations,
  given problem)   structures,    verbatim    problem library sets numbers; card   tative) +       BIO vs NO-BIO, prior-
                   scales,        quotes      (scale/regime   screen() checks      render          art novelty
                   mechanisms                 gate)           every constraint     (illustrative)
```

The two tracks:

- **Biology track (stages 1–2).** What the organism does and how, at what scale, with literature evidence.
- **Engineering track.** A library of real problems with numeric requirements (23 now), plus physics cards (11 now). Each card is a closed-form, cited model across six domains.
  - Thermal: PCM, counter-current heat exchanger, radiative cooling.
  - Structures: honeycomb sandwich, lattice.
  - Fluids: riblet drag.
  - Adhesion: gecko-type fibrils.
  - Wetting: lotus-type surfaces.
  - Optics: Bragg structural colour.
  - Mass transfer: plastron, fog mesh.
- **Where they meet (stage 3).** The physical-effect tag of the biological mechanism selects physics cards. Each card lists the problems it can address.
- **Mode B (primary).** The system starts from the photo alone and chooses the problem itself.
- **Mode A.** Someone supplies the problem.

**Division of labour (decision D3).**

- The language model chooses what biology can decide: the mechanism, the problem and the card.
- An optimiser (differential evolution) sets the numbers.
- The card checks every constraint and returns margins.
- If the result fails, the system repairs it and checks again.

## 2. Worked example (a real pilot run, B06 blue morpho)

1. **Input.** One public-domain Commons photo, showing a display case of morpho and owl butterflies.
2. **Perceive.** The VLM identified "Morpho sp. and Caligo sp.". Among its proposed mechanisms was "structural colour via photonic crystals; the blue is from nanostructured scales, not pigment" (tag: optics).
3. **Analogise.** From the 23 problems, it chose P-OPT-02, a fade-proof blue coating with no pigment:
   - peak at 470 ± 10 nm
   - reflectance ≥ 0.5
   - total thickness ≤ 3 µm
   - every layer ≥ 30 nm

   It chose the Bragg-reflector card, which is the correct card. Its mapping: wing scales (~1 µm) → thin-film multilayer (0.1–1 µm).
4. **Design (LLM only).** 15 layer pairs, n = 1.5 / 2.0, 30–47 nm thick.
   - The card computes a reflection peak at about 330 nm, which is UV, not blue. That misses the target by 141 nm.
   - Four repair turns did not fix it.
5. **Design (optimiser).** n = 1.92 / 2.16, layers 57 nm, 11 pairs.
   - Peak error 4 nm, reflectance 0.82, 1.26 µm thick, stop band 35 nm.
   - **All constraints pass.**
6. **Blueprint.** JSON description, dimensioned schematic and illustrative render. The files are in `docs/v11/dataset_samples/pipeline_example_B06_morpho/`.

**Lesson.** Biology supplied the right idea. The optimiser supplied the right numbers.

## 3. The gap

| | Image input | Physics check | Design-image output | Evaluation |
|---|---|---|---|---|
| BioSpark (CHI 2025) | display only | no | no | 12 users |
| BioinspiredLLM, BIDARA, AskNatureGPT, Zhu–Luo | no | no | no | QA / ratings / case studies |
| Cephalo (2024) | yes | no | microstructure images | qualitative |
| Bioinspired123D (2026) | renders for a critic | geometry only | yes (Blender) | script benchmark |
| CADCodeVerify (ICLR 2025) | renders for self-check | geometry only | CAD | no biology |
| **FLBDS V11** | **organism photos (later micrographs)** | **closed-form physics, 6–7 domains** | **parametric schematic + render** | **fully automatic, with controls** |

No published system goes from an organism image, through a physics-checked design, to a design image.

Existing bio-inspired design systems that use LLMs have two further weaknesses:

- They are text-only.
- Each is evaluated by a handful of human raters.

## 4. Research questions (short form; full form in paper §6)

- **RQ1 Image value.** Does an image add information beyond the organism's name, where the model's memory is weak (less-famous organisms, micrographs)?
- **RQ2 Rediscovery.** From a photo alone, does the system recover the known mechanism and application?
- **RQ3 Biology vs no biology.** Are bio-sourced designs as feasible and as sound as no-biology designs, and farther from prior art?
- **RQ4 Choice.** On problems where only some mechanisms work, does a matched organism steer the system to a working mechanism more often than:
  - a mismatched organism,
  - no organism,
  - the same principle stated without biology?
- **RQ5 Design loop.** Do physics feedback, optimiser polish and the 3 × 7 compute allocation carry over to the new domains?
- **RQ6 Blueprint quality.** Are blueprints complete and self-consistent, and does the schematic match the description?

## 5. What has been tested so far

| Experiment | Result | Status |
|---|---|---|
| **V9 audit** | The old headline result ("feedback doubles pass rate") was an artefact. Answers leaked into prompts, and 5 of 12 cases passed with a blank design. | measured |
| **V10 design loop** (48 certified thermal instances, Qwen2.5-72B) | Feedback loop: +30.6 points over one shot (p = 3×10⁻⁵). 3 samples × 7 repairs: 70.8%, against 41.0% for 24 independent samples. A matched biology card made no difference (+2.8, p = 0.56), because each family had only one possible mechanism. | measured |
| **E1 perception** (22 famous organisms × 3 seeds) | Photo alone: identification 64%, against 100% from the name. Canonical application in top 5: 71% (photo), 100% (name). In 42% of misidentified photos, the image still led to the right application. | measured |
| **E1b BioCLIP 2** | Correct taxon ranked first for 19/22 photos, in the top 5 for 21/22 (closed list of 54 names). | measured |
| **E2 blueprints**, BIO vs NO-BIO (judged in both orders) | Soundness: equal. Implementability: BIO higher (+0.39, p = 0.003). Novelty: BIO lower (−0.51), because textbook biomimicry is already standard practice. Faithfulness to the biology: 4.3/5. | measured |
| **E3 end-to-end Mode B** (11 cards, 23 problems) | Physics pass: 24% (photo), 35% (name), 30% (no biology), no significant difference. Biology steered the choice to the organism's own mechanism in 41–57% of runs, against 33% without biology. The physics check caught a look-alike transfer: a lotus texture that fails under rain impact. | measured |
| **E3b optimiser polish** | Pass rate rose from 24% to 73% (photo) and from 30% to 73% (no biology). Bio-led designs now pass as often as no-biology designs. | measured |
| **Renders** (Qwen-Image) | 3 of 7 on target. The rest misread the photo or drew a look-alike. Decision: renders are illustrative only. | measured |

## 6. Decisions taken after the pilot (paper §9.1)

- **D1.** Less-famous organisms and micrographs become the primary benchmark.
- **D2.** Novelty is measured against prior art (patents and papers).
- **D3.** The LLM chooses; the optimiser sets the numbers.
- **D4.** A mechanism-card store is primary; a knowledge graph is tested only as a later ablation.
- **D5.** The parametric SVG schematic is the authoritative design image.
- **D6.** The image claim is reframed.
- **D7.** The venue is still open.

## 7. Next (to April 2027)

1. Make the cards and problems choice-sensitive, and audit the 7 new cards.
2. Put BioCLIP 2 in front of perception. Build 60–150 mechanism cards from PMC OA.
3. Run the RQ4 choice experiments on about 100 instances.
4. Build the parametric schematics and the prior-art index.
5. Scale up to about 100 organisms with several photos each, plus micrographs.
6. Write it up.
