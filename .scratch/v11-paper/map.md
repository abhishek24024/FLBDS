# Wayfinder map: V11 paper — image-driven, biology-first, physics-checked design

Labels: wayfinder:map · Tracker: local markdown (`docs/agents/issue-tracker.md`)

## Destination

A submission-ready paper (ICED / DCC / ASME IDETC / Design Science / JMD class, target ~April 2027) showing, with automatic and reproducible evidence, that a pipeline from **organism images** to **physics-checked engineering blueprints** produces bio-inspired designs that work — and that the biology (and the image) causally contributes.

## Notes

- Domain: bio-inspired engineering design; LLM/VLM pipelines; closed-form physics verification.
- Skills every session should consult: `grilling` + `domain-modeling` (HITL tickets), `research` (AFK tickets), `prototype` (blueprint format), `experiment-rigor` (stats).
- Standing preferences (author, 20 Nov 2026): Mode B primary (image → system picks problems), Mode A supported; heavy bias toward biological inspiration; diversify domains beyond thermal-fluids; output = design sketch(es) + blueprint-like implementable description; solo researcher → **no human raters**; open-weight models on hcd-dept-h200 only (90 GPU-h/week; GPUs 2–3 currently need a reset).
- Key docs: `docs/v11/INTERFACES.md`, `docs/v11/DATASETS.md`, `docs/v11/paper/paper.pdf`, `docs/v10/findings_log.md`, `research_notes/Bio integration and image innovation/`.

## Decisions so far

- [Round-1 grilling (20 Nov)](../../docs/v11/DATASETS.md): claim = bio-inspiration improves/innovates designs, images add inferable information; Mode B primary; diversify domains; blueprint-style sketch + description outputs; no human raters; open models only; local tracker.
- Knowledge graph vs retrieval (research note 02): use a mechanism-card store with verbatim evidence + function/effect-keyed retrieval; a KG is an optional later ablation (no measured BID gains from KGs to date).
- Design loop (V10 results): 3 samples × up to 7 screen-repair turns; optimiser polish; screen must become a true relaxation.
- [V11 pilot results (20 Nov)](../../docs/v11/findings_v11.md): photo-only identification 64% (BioCLIP closed list 86%); name beats photo on famous organisms; bio blueprints more implementable but less novel than no-bio for canonical cases; end-to-end physics pass 24-35% LLM-only → 73-82% with optimiser polish; biology steers toward the organism's own mechanism.
- [Round-2 grilling (20 Nov), paper §9.1 Table 12b](../../docs/v11/paper/paper.html): D1 less-famous organisms + micrographs are the primary image benchmark, canonical 24 kept as contamination reference (revisit later); D2 novelty = prior-art distance primary, judge secondary (revisit later); D3 LLM chooses mechanism/problem/card, optimiser sets numbers (E3b 24%→73%); D4 mechanism-card store primary, KG only as later ablation; D5 per-card parametric SVG authoritative, render illustrative; D6 image claim reframed (entry point + structure→function cues; "image beats name" only where memory is weak, if data support it); D7 venue still open, presentation draft = docs/v11/paper/paper.pdf.

## Not yet specified

- How Mode B ranks candidate problems for a mechanism (fit score? physics feasibility? novelty vs prior art?) — depends on the problem library and judge results.
- Micrographs vs field photos vs multiple views: what image evidence the full study needs.
- CAD output (CadQuery) beyond SVG schematics; multi-organism combined designs.
- Learning components (e.g. GRPO-trained proposer) — only if the pipeline plateaus.

## Out of scope

- Human-rater studies (solo project) — replaced by automatic evaluation; revisit only if collaborators join.
- Physical fabrication/testing of designs.
