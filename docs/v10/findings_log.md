# V10 findings log (2026-11-20, overnight run)

## Infrastructure
- 00:00 GPU 2 on hcd-dept-h200 reports MIG "GPU requires reset" with ~86 GB stuck; CUDA init fails for any native job that can see it. GPU 3 also fails cuInit natively (nvidia-smi healthy). GPUs 0/1 belong to other users. Docker Hub pulls fail (TLS). => No GPU available; experiments run on CPU with Qwen2.5-7B-Instruct (transformers, ~120 tok/s at batch 32).

## E0 — rescoring of the stored Round-11 Qwen2.5-72B runs with the fixed scorer (CPU only)
Source: docs/v10/e0_results/ (e0_rescore_summary.json, e0_nontrivial.json, blank_design_test.json)
- Fixes (DEV-M4-S1 head 10 m -> 2.5 m; cos θ sign) change no outcome: 18/34/33/30 of 60 for B0/Screen/Oracle/B3, unchanged.
- Leak exposure: 7/60 Screen runs and 7/60 Oracle runs saw the hidden acceptable-template list in feedback; 6 of each then passed. B3 took the template from hidden ground truth in 50/60 runs (no operator fired).
- Blank-design test: a design containing ONLY template_id (all other fields schema defaults, env from DEV_SPECS) passes the hidden scorer for 5/12 dev cases (DEV-M2-S1, M2-S2, M3-S1, M3-S2, M3-S3).
- On the 5 trivially-passable cases: B0 7/25, Screen 22/25, Oracle 22/25, B3 23/25.
- On the 7 non-trivial cases: B0 11/35, Screen 12/35, Oracle 11/35, B3 7/35. Screen−B0 = +2.9 pts (sign-flip p = 1.0, n = 7 cases).
- Conclusion: the Round-11 "feedback loop doubles pass rate" result is explained by template selection on cases a blank design already passes; there is no measured physical-design benefit on the 12 dev cases.

## V10 harness (built 00:00–00:45; flbds/v10/, scripts/run_v10.py, 45 tests pass)
- 4 families mirroring the dev clusters: F_PCM (TPL_02), F_HX (TPL_08, circular duct, water), F_RAD (TPL_09), F_MEM (TPL_10).
- Generator: env sampled around DEV_SPECS anchors (seed 20261119); each candidate certified satisfiable by differential evolution against the hidden scorer; instances rejected if >50% of 200 random designs pass ("too easy"). 48 instances (12/family), sha256 788426ff…, canary string, 40 s CPU.
  - Acceptance: PCM 12/12 (trivial-rate of kept 7%), HX 12/12 (9%), RAD 12/12 (6%), MEM 12/33 (21 rejected as too easy; kept trivial-rate 34%).
- No schema defaults: every design field required, explicit bounds; environment always from the instance, never from model output.
- Screen feedback: per-constraint achieved/limit/normalised margin/PASS-MISS; template errors get only "the chosen template's physics cannot deliver the required function".

## Relaxation audit (screen vs hidden scorer, 2,000 designs/family: half uniform, half near certified designs)
| family | both pass | both fail | screen-fail & eval-pass (false rejection) | screen-pass & eval-fail (false assurance) |
|---|---|---|---|---|
| PCM | 466 | 1415 | 7 | 112 |
| HX | 871 | 1126 | 0 | 3 |
| RAD | 698 | 1106 | 91 | 105 |
| MEM | 1144 | 849 | 0 | 7 |
- PCM: eval enforces a paraffin latent-capacity bound the screen lacks.
- RAD: the existing hidden eval for TPL_09 checks inner leakage but NOT the required net cooling; the screen checks cooling but not leakage => the two tiers test different constraints (neither is a relaxation of the other).
- New solver bug: the existing TPL_02 1-D enthalpy solver is numerically unstable for effective Fourier number α·t/d² > 135 and returns NaN/garbage that still PASSES; ~31% of random PCM designs hit this. Wrapped (Fo ≤ 135 "model validity" constraint in both tiers) in flbds/v10 only; flbds/physics not yet patched.
- Known residual leaks/limitations: catalogue shows numeric bounds only for the 4 benchmark templates (hints which templates are live); PCM "matched" biology card is the DEV-M1 fixture (elephant mud evaporation) which describes evaporation, not latent storage; HX dev names contain "Countercurrent".

## Main CPU run (Qwen2.5-7B-Instruct, HF transformers bf16, 96 threads, T=0.7, seeds 1–2, 48 instances)
Conditions: B0 (1 sample, no feedback), L3 (1 sample + ≤3 screen repairs), BoN8 (8 samples, best by screen), OPT (1 LLM sample → DE optimiser on screen seeded by it), OPTONLY (optimiser on screen, no LLM), L3_BIOMATCH, L3_BIOMISMATCH. One final design per run scored once by hidden eval.
Results (04:30; BoN8 still running; L3_BIOMISMATCH 48/96 runs at time of analysis) — docs/v10/results/analysis.md
| condition | eval pass / runs | rate [Wilson 95%] | screen-pass & eval-fail | template errors | tokens/run |
|---|---|---|---|---|---|
| B0 | 21/96 | 21.9% [14.8, 31.1] | 5 | 32 | 108 |
| L3 | 39/96 | 40.6% [31.3, 50.6] | 9 | 0 | 343 |
| L3_BIOMATCH | 37/96 | 38.5% [29.4, 48.5] | 9 | 1 | 372 |
| OPT | 61/96 | 63.5% [53.6, 72.5] | 9 | 26 | 110 |
| OPTONLY (no LLM) | 65/96 | 67.7% [57.8, 76.2] | 31 | 0 | 0 |
Paired instance-level (N=48; sign-flip; Holm over 3 confirmatory):
- L3 − B0 = +18.8 pts [+10.4, +29.2], Holm p = 0.0007  -> screen feedback helps on certified non-trivial instances (unlike the dev set).
- OPT − L3 = +22.9 pts [+7.3, +38.5], Holm p = 0.018    -> LLM template + optimiser beats LLM-only repair.
- OPTONLY − OPT = +4.2 pts [0.0, +9.4], p = 0.22        -> the LLM adds nothing over an optimiser that is told the template.
- L3_BIOMATCH − L3 = −2.1 pts [−9.4, +6.2], p = 0.79    -> no biology-card effect (7B).
Per family: HX 0% for every LLM-only condition (7B cannot size the exchanger) but 100% once the optimiser is used; PCM is hard for everyone (OPTONLY 12.5%, mostly screen-pass/eval-fail = screen not a relaxation); MEM easy (B0 67%).
OPTONLY passes the screen 96/96 but the hidden eval only 65/96: all 31 misses are screen false-assurance (PCM, RAD).

## Status at usage-limit cutoff (~00:35, 2026-11-20)
- CPU run in progress on server (runs unattended; resumable):
  log ~/flbds_data/v10_cpu_run1/run2.log, results ~/flbds_data/v10_cpu_run1/*.jsonl + summary_all.json
  order: B0 OPTONLY OPT L3 L3_BIOMATCH L3_BIOMISMATCH BoN8 (~4 min per 24 runs; full run ~5 h)
- To analyse and pull results:
  ssh -i ~/.ssh/bio_server abhishek24024@192.168.2.69 'cd ~/flbds_v10 && PYTHONPATH=. ~/flbds_env/bin/python3 scripts/analyse_v10.py --run-dir ~/flbds_data/v10_cpu_run1'
  rsync -az -e "ssh -i ~/.ssh/bio_server" abhishek24024@192.168.2.69:/home/abhishek24024/flbds_data/v10_cpu_run1/ docs/v10/results/
- Paper draft being written to docs/v10/paper/paper.html (+ make_figures.py, fig/); section 8.x has marker <!--RESULTS-CPU--> to fill.
  Render: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf=docs/v10/paper/paper.pdf file://$PWD/docs/v10/paper/paper.html

## 72B replication on GPU 1 (04:25–04:29; GPU 1 freed up; Qwen2.5-72B-Instruct-FP8, vLLM 0.32, 48 instances × 3 seeds) — docs/v10/results_72b/analysis.md
| condition | eval pass / runs | rate [Wilson 95%] | screen-pass & eval-fail | tokens/run |
|---|---|---|---|---|
| B0 | 35/144 | 24.3% [18.0, 31.9] | 3 | 135 |
| BoN8 | 55/144 | 38.2% [30.7, 46.3] | 7 | 1084 |
| L3 | 79/144 | 54.9% [46.7, 62.8] | 9 | 384 |
| L3_BIOMATCH | 75/144 | 52.1% [44.0, 60.1] | 9 | 372 |
| L3_BIOMISMATCH | 71/144 | 49.3% [41.3, 57.4] | 8 | 383 |
| OPT | 95/144 | 66.0% [57.9, 73.2] | 49 | 135 |
| OPTONLY (CPU run, 2 seeds) | 65/96 | 67.7% [57.8, 76.2] | 31 | 0 |
Paired (N=48 instances; Holm over L3:B0, OPT:L3, BIOMATCH:BIOMISMATCH):
- L3 − B0 = +30.6 pts [+20.8, +41.0], Holm p = 3e-5 (RAD +58 pts p=0.002, MEM +33, PCM +17, HX +14)
- BoN8 − B0 = +13.9 pts [+6.2, +22.2], p = 0.002 — but BoN8 < L3 at 2.8× the tokens: repair with margin feedback beats independent resampling here.
- OPT − L3 = +11.1 pts [−4.2, +26.4], Holm p = 0.37 (n.s. at 72B; significant at 7B: optimiser matters more for the weaker model)
- OPTONLY − OPT = +1.7 [−1.7, +5.6], p = 0.44 — LLM adds ≈0 over an optimiser given the template.
- BIOMATCH − BIOMISMATCH = +2.8 [−4.2, +9.7], Holm p = 0.56 — no biology-card effect.
- OPT passes the screen 144/144 but the hidden eval 95/144: all 49 misses are screen false-assurance => the ceiling is now set by screen fidelity, not the LLM.
Running next on GPU 1: dev-set rerun with V10 harness (B0, L3, OPT, OPTONLY × 5 seeds) and compute allocation (A24x1, A8x3, A3x8, V10=8×3) — output ~/flbds_data/v10_gpu72b_dev, ~/flbds_data/v10_gpu72b_alloc.

## 72B dev rerun with V10 harness (5 seeds, 60 runs/arm) — docs/v10/results_72b/dev/
B0 18/60 (30.0%), L3 39/60 (65.0%), OPT 41/60 (68.3%), OPTONLY 39/60 (65.0%); L3 − B0 = +35.0 pts [+18.3, +53.3], Holm p = 0.016 (N = 12 cases).
=> once blank designs cannot pass and nothing leaks, the loop's benefit is real on the dev cases too; the Round-11 number just did not measure it.

## 72B compute allocation (48 × 3 seeds) — docs/v10/results_72b/alloc/
A24x1 59/144 (41.0%, 3,258 tok/run); A8x3 96/144 (66.7%, 2,538); A3x8 102/144 (70.8%, 1,820); V10 8×3 102/144 (70.8%, 3,096).
A3x8 − A24x1 +29.9 pts p=5e-6; A3x8 − A8x3 +4.2 p=0.24; V10 − A3x8 0.0; A3x8 − L3 +16.0 p=0.0014. Depth beats breadth; default allocation should be 3×7.
7B L3_BIOMISMATCH final: 39/96 (40.6%); BIOMATCH − BIOMISMATCH = −2.1 pts, Holm p = 0.77. 7B BoN8 stopped unfinished (CPU too slow).
Paper: docs/v10/paper/paper.html + paper.pdf (28 pages).
