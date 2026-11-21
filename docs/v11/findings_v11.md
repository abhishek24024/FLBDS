# V11 pilot findings (20 Nov 2026, 09:26–09:40) — docs/v11/results/

Setup: 22 canonical organisms (B1 gold set; one unscreened Wikimedia Commons photo each), Qwen3-VL-32B-Instruct-FP8 generator (vLLM, T=0.7, 3 seeds), arms IMG (photo only) / NAME (name only) / IMG+NAME; judge = Qwen2.5-72B-Instruct-FP8 (different model, T=0). Unit of inference = organism (n=22); paired sign-flip tests, bootstrap 95% CIs.

## E1/E2 perception and rediscovery (judge vs gold mechanism + canonical application)
| metric | IMG | NAME | IMG+NAME |
|---|---|---|---|
| organism identified (genus/common name) | 0.636 | 1.000 | 0.985 |
| mechanism score (0–2) | 1.17 | 1.86 | 1.73 |
| canonical application ranked #1 | 0.515 | 0.788 | 0.803 |
| canonical application in top-5 | 0.712 | 1.000 | 0.970 |
| hallucination (false biological fact) | 0.045 | 0.000 | 0.000 |
| specificity (1–5) | 3.82 | 4.46 | 4.20 |
Paired: IMG−NAME organism −0.36 (p=0.004), mechanism −0.70 (p=0.0004), hit@1 −0.27 (p=0.012), hit@5 −0.29 (p=0.016). IMG+NAME−NAME: mechanism −0.14 (p=0.031), hit@1 +0.02 (p=1.0) — adding the photo to the name does not help on canonical organisms.
IMG conditional on identification: correct ID (42 runs) mechanism 1.57, hit@1 0.64, hit@5 0.88; wrong ID (24 runs) mechanism 0.46, hit@1 0.29, hit@5 0.42 — the photo alone still leads to the canonical application in 42% of misidentified runs (e.g. SEM of shark denticles, xylem micrograph).
Per-organism identification from photo: 0/3 for lotus (photo dominated by a frog), shark denticle SEM, Namib beetle, silver ant, termite soldier (gold = mound), springtail, xylem micrograph; jewel beetle 1/3; burdock 2/3; the rest 3/3.
Interpretation: on famous organisms the name already unlocks the model's memorised biomimicry; the image's value is bottlenecked by identification. Next: BioCLIP 2 identification stage; multiple and micro-scale images; less-famous organisms where memory is weak; negative controls.

## E2 blueprints: BIO vs NOBIO for the same application (pairwise, both orders; score −1..+1, + = BIO better)
| arm source | novelty | soundness | implementability | overall | bio-faithfulness (1–5) |
|---|---|---|---|---|---|
| IMG | −0.51 (p=0.0008) | −0.03 (p=0.50) | +0.39 (p=0.003) | −0.09 (p=0.039) | 4.30 |
| NAME | −0.48 (p=0.003) | −0.02 (p=0.75) | +0.38 (p=0.004) | −0.15 (p=0.056) | 4.65 |
| IMG+NAME | −0.55 (p=0.0002) | −0.05 (p=0.38) | +0.33 (p=0.009) | −0.19 (p=0.006) | 4.58 |
Judge order-consistency: soundness 0.90, novelty 0.70, overall 0.59, implementability 0.51 (implementability/overall are close to position noise).
Interpretation: bio-sourced blueprints are judged as sound and more implementable but LESS novel than unconstrained no-biology designs for the same application — the canonical applications are established practice, so "novel vs standard practice" penalises them. Novelty must be measured against prior art (patents/literature) and on less-famous organisms; RQ3 as framed is not yet supported.

## E3 — end-to-end Mode B with physics checks (Qwen3-VL-32B, 22 organisms × 3 seeds = 66 runs/arm; ≤4 screen-repair turns; 11 physics cards, 23 real problems)
IMG/NAME arms start from that arm's perception and must choose a problem from the library + a physics card + a design grounded in the organism; NOBIO = same problem as the IMG run, no biology, free card choice.
| arm | final physics pass | first-attempt pass | regime ok | card plausible for problem | first card = organism's gold card | invented card ids | schema errors |
|---|---|---|---|---|---|---|---|
| IMG | 16/66 (24.2%, case-CI 10.6–39.4) | 21.2% | 74.2% | 86.4% | 40.7% | 9 | 2 |
| NAME | 23/66 (34.8%, 19.7–53.0) | 18.2% | 65.2% | 87.9% | 57.4% | 8 | 6 |
| NOBIO | 20/66 (30.3%, 15.2–45.5) | 13.6% | 62.1% | 86.4% | 33.3% | 9 | 5 |
Paired over 22 organisms: IMG−NOBIO −6.1 pts (p=0.63); IMG−NAME −10.6 (p=0.34); NAME−NOBIO +4.5 (p=0.74) — no significant differences.
Pass by problem domain (IMG / NAME / NOBIO): thermal 11/14 · 18/24 · 5/14; wetting 0/11 · 1/15 · 11/11; mass transfer 3/9 · 3/10 · 4/9; structures 1/13 · 0/4 · 0/13; optics 1/8 · 0/6 · 0/8; adhesion 0/11 · 0/6 · 0/11.
Observations: (1) Mode B spreads across 6 domains (IMG chose thermal 14, structures 13, adhesion 11, wetting 11, mass transfer 9, optics 8). (2) Biology leads to the organism's own mechanism more often (gold-card choice IMG 41%, NAME 57% vs 33% for NOBIO choosing freely for the same problem). (3) LLM-only repair rarely satisfies the new-domain cards (adhesion 0%, structures ≤8%, optics ≤13%): the certified problems have tight margins (+0.04–0.10) — the V10 optimiser-polish step is needed. (4) Wetting: NOBIO 11/11 vs IMG 0/11 on the same problems — bio-led designs copy lotus-scale texture that fails the impact-robustness check, a concrete instance of look-alike transfer caught by physics. (5) ~13% of runs invented physics-card names (e.g. THM_RADIATIVE_COOLING_WITH_PCM) → constrain card_id with structured-output choice.

## E3b — optimiser polish on the E3 runs (CPU, 12 s; differential evolution on the chosen card's design space against its screen, seeded with the LLM's final design; problem and card kept as chosen by the LLM)
| arm | LLM loop pass | after optimiser polish | runs with invalid (invented) card id |
|---|---|---|---|
| IMG | 16/66 (24%) | 48/66 (73%) | 9 |
| NAME | 23/66 (35%) | 54/66 (82%) | 8 |
| NOBIO | 20/66 (30%) | 48/66 (73%) | 9 |
By domain, IMG (LLM → polished / n): adhesion 0→3/11, mass transfer 3→9/9, optics 1→8/8, structures 1→10/13, thermal 11→11/14, wetting 0→7/11.
Among runs with valid ids, polish passes 48/57 (IMG), 54/58 (NAME), 48/57 (NOBIO). Remaining failures: invented card ids (fix: constrained choice) and the adhesion card (fibril collapse vs pull-off pressure window is narrow) and some thermal choices.
Conclusion: the V10 lesson transfers to new domains — the LLM should choose the biological mechanism, problem and card; a classical optimiser should set the numbers. With that split, bio-led concepts reach the same physics pass rate as no-bio concepts (73% vs 73%) while staying on the organism's mechanism.

## E1b — BioCLIP 2 closed-list identification (CPU, same 22 photos)
Candidates: the 24 gold taxa + 30 look-alike distractor taxa (54 names), prompt "a photo of <scientific name>". Top-1 19/22 (86%), top-5 21/22 (95%), vs. 64% open-ended identification by Qwen3-VL-32B from the photo. Caveat: a closed list is easier than open identification and contains the answer; in the pipeline BioCLIP proposes a top-5 that the VLM then re-ranks, and a confidence threshold triggers abstention. Supports adding the BioCLIP stage before VLM perception (the identification bottleneck found in E1).
