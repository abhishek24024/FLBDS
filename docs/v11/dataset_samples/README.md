# FLBDS V11 — dataset samples (for supervisor review)

This folder holds a small, readable sample of every dataset the project uses, from both the biology side and the engineering side. It was copied from the GPU server (`hcd-dept-h200`, `~/flbds_data/`) and from the repository on 20 November 2026. The full inventory, with sizes and licences, is in [`../DATASETS.md`](../DATASETS.md).

## Biology side

| Folder | What it is | Sample | Full dataset | Licence |
|---|---|---|---|---|
| `bio_v11_gold_set/` | **The V11 gold set.** 24 textbook organism → engineering cases (organism, structure, mechanism, physical-effect tag, canonical application, physics card), used to test whether the system rediscovers known transfers from a photo. See `gold_set.md`. | All 24 cases + 6 of the 22 photos | 24 cases, 22 photos | Project-authored; photos CC BY / CC BY-SA / PD (see `photos/images_manifest.json`) |
| `bio_foundation_papers/` | **Foundation papers** behind the four V10 thermal families: elephant skin (Martins 2018), counter-current rete (Scholander 1955), Saharan silver ant (Shi 2015), plastron (Flynn & Bush 2008; Shirtcliffe 2006). `.md` = summary and mechanism notes; `.json` = OpenAlex metadata and abstract. | All 5 | 5 foundation + 10 audited PMC papers | Open-access metadata |
| `bio_corpus_pmc/` | **PMC biology corpus** (V9 `bio_pilot`). Full-text CC BY papers from PubMed Central about how organisms manage heat, water and light. It feeds the mechanism-card store. | 11 organism-focused papers (honey bee, Hoplia beetle, bat, cotton, leaf, lizard, insect refuge, biomimetic distillation, …) | 500 papers | CC BY (only CC BY picked here) |

**Caveat about `bio_corpus_pmc`.** The full 500-paper corpus is noisy. It was built from thermoregulation keywords, so many papers are clinical (sweat, newborn care) or about engineered materials. In V9, 51 of 53 "biology" cards extracted from it described engineered materials, not organisms. The samples here were hand-filtered to organism papers. V11 replaces this corpus with targeted PMC OA retrieval by taxon and function (DATASETS.md, B10–B11).

## Engineering side

| Folder | What it is | Sample | Full dataset | Licence |
|---|---|---|---|---|
| `eng_v11_problems_and_cards/problems.md` | **Problem library.** Real engineering problems, each with numeric requirements and the cards that could solve it. In Mode B the system picks a problem; in Mode A one is given. | All 23 | 23 (to grow to 30+) | Project-authored, each with a source |
| `eng_v11_problems_and_cards/physics_cards.md` | **Physics cards.** Closed-form, cited models that check a design: PCM storage, counter-current HX, radiative cooling, plastron, honeycomb sandwich, lattice, riblets, fibrillar adhesion, superhydrophobic wetting, Bragg structural colour, fog mesh. | All 11 | 11 | Project code |
| `eng_v11_problems_and_cards/problem_feasibility.json` | **Feasibility certificates.** For every (problem, plausible card) pair, the optimiser's best design and its minimum margin. These show which mechanisms can work for each problem. | All | 29 pairs (27 feasible) | Derived |
| `eng_corpus_patents/` | **USPTO patent corpus** (V9 `eng_pilot`). Full-text patents in CPC sections F (heating, cooling, heat exchange) and E (buildings, insulation). Planned use: prior-art novelty, i.e. how far a generated design is from its nearest existing patent. | 11 patents (evaporative coolers, PCM thermal buffers, counter-flow regenerator, heat pipe, heat-recovery ventilation, insulated roof, radiative-control glazing) | 500 patents (to scale to 10k–100k) | US patent text, public domain |

## One end-to-end example

`pipeline_example_B06_morpho/` follows one real pilot run from photo to verified design:

- `input_photo.jpg`: the only input (Wikimedia Commons, public domain).
- `trace.json`: every stage, recorded verbatim from the pilot.
  1. Perception: the VLM output.
  2. The chosen problem (P-OPT-02, a fade-proof blue coating) and card (Bragg reflector).
  3. The LLM's design and the four repair attempts, all failing.
     - The LLM's layers were 30–47 nm thick, which tunes the reflection to UV light.
  4. The optimiser-polished design, which passes every constraint.
  5. The LLM-only pilot blueprint.
- `illustrative_render.png`: the Qwen-Image concept render of the pilot blueprint. It is illustrative only; the authoritative image will be a parametric schematic drawn from the verified numbers.

All numbers are explained in the paper (§8.5, worked example): `docs/v11/paper/paper.pdf`.
