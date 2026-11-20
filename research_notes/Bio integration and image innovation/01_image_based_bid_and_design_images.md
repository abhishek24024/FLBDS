# 01 — Image-based bio-inspired design (BID) and design-image generation: literature scan

Scope: 2020–Nov 2026, primary sources only (arXiv, journals, proceedings, official repos and model cards). Compiled 2026-11-20 under a hard time limit. Each claim is tagged **[PR]** (peer-reviewed) or **[pre]** (preprint). Numbers come from the cited page. "N/R" means not reported on the page that was read. Items marked *(unverified)* were not re-checked in this pass.

FLBDS target pipeline: biological image (± text) → VLM perception → analogy to an engineering problem (Mode A: given, Mode B: chosen) → design with closed-form physics checks → blueprint sketch + description, with fully automatic evaluation.

---

## Q1. Systems that take biological IMAGES as input for design ideation / BID

### Takeaway
No published system found takes **an organism image as the primary input** and runs it end-to-end through analogy, design, and a physics check. The image-capable systems are:
- **Cephalo**: a materials-micrograph VLM with no design verification.
- **Bioinspired3D/123D**: the VLM is a *critic* of rendered geometry, not a perceiver of organisms.
- **BioSpark**: uses GPT-4V only to *rank stock photos* for display.

The mainstream BID-LLM line is text-only: BioinspiredLLM, BIDARA, AskNatureGPT, Zhu–Luo GPT BID, and BARcode. That leaves FLBDS's "image → mechanism → physics-checked design" niche open, but there is no off-the-shelf baseline to compare against. FLBDS has to build its own baselines, e.g. a text-only ablation of the same pipeline.

### Cited findings
- **Cephalo** (Buehler, MIT): [arXiv:2405.19076](https://arxiv.org/abs/2405.19076) [pre], journal version listed as *Adv. Funct. Mater.* 2024 on the [HF card](https://huggingface.co/lamm-mit/cephalo) [PR].
  - Method and models: multimodal V-LLMs fine-tuned on image–caption pairs extracted from the PDFs of thousands of scientific papers plus science Wikipedia. Released 4B (Phi-3-Vision), 8B (Idefics-2, LLaVA-1.6-Mistral) and merged 10B/12B models, plus MoE 3×4B.
  - Demonstrations: pollen-inspired architected materials, and microstructures generated from a solar-eclipse photo.
  - Evaluation: **qualitative only**, with no quantitative benchmark in the [repo](https://github.com/lamm-mit/Cephalo).
  - Licence: code Apache-2.0; model licences are on the individual HF cards.
  - Training data: GPT-4o/Idefics-2-distilled image–text pairs. The dataset is not released under a name or size.
- **Bioinspired123D / Bioinspired3D** (Luu & Buehler, 11 Feb 2026): [arXiv:2603.29592](https://arxiv.org/abs/2603.29592) [pre].
  - Method: a compact LM fine-tuned to emit **parametric Blender Python** ("code-as-geometry"). It runs inside a graph-based agent with multimodal RAG and a **VLM critic** that inspects the rendered geometry and repairs the script.
  - Data: >4,000 bioinspired and geometric scripts (helical, cellular, tubular), quality-controlled by an automated LLM+Blender pipeline.
  - Result: "near fourfold" improvement over the non-fine-tuned base on a new script-generation benchmark. Absolute numbers N/R in the abstract.
  - Licence: paper CC BY-NC-ND. Code and data release N/R.
  - Relevance: closest analogue to FLBDS's "design-image output + automatic VLM check", but it has no physics check and its input is text cues, not organism images.
- **BioinspiredLLM** (Luu & Buehler): *Adv. Sci.* 11:2306724 (2024), [PMC10933662](https://pmc.ncbi.nlm.nih.gov/articles/PMC10933662) [PR], [arXiv:2309.08788](https://arxiv.org/abs/2309.08788).
  - Method: Llama-2-13B-chat fine-tuned on >1,000 peer-reviewed articles on structural biological materials, distilled into Q&A pairs, plus RAG.
  - Input: text only. A later Llama-3-8B variant is on [HF](https://huggingface.co/lamm-mit/BioinspiredLlama-3-8B).
  - Evaluation: knowledge-recall questions, not design quality.
- **BIDARA** (NASA PeTaL; Toukmaji & Tee): [AAAI Spring Symposium 2024](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210) [PR-symposium].
  - Method: a GPT-4/4o chatbot following the Biomimicry Institute's design spiral (define → biologize → discover → abstract → emulate), with RAG and ReAct agents.
  - Result: RAG increased the rated *feasibility* of solutions in both prompting and agent settings.
  - Input: text. Repo: [nasa-petal/bidara-deep-chat](https://www.github.com/nasa-petal/bidara-deep-chat).
- **BioSpark** (Kang, Lin, Martelaro, Kittur, Chen, Hong; Toyota Research Institute/CMU): CHI '25, DOI 10.1145/3706598.3714053 [PR]; [arXiv:2503.09838](https://arxiv.org/abs/2503.09838); earlier version at the NeurIPS'23 workshop, [arXiv:2312.11388](https://arxiv.org/abs/2312.11388).
  - Data: seed mechanisms come from AskNature.org. A 7-level "tree-of-life" hierarchy is expanded with GPT-4 to generate new species → mechanism triplets, then clustered with DBSCAN.
  - Images: retrieved from Google and Adobe Stock, then **GPT-4V ranks them for visual focus/value** and the top one is shown per species. Images are therefore *display*, not reasoning input.
  - Study: within-subjects, N=12 researchers, 2 design problems (wheelchair stairs, bike carrier), baseline = 5 AskNature URLs + ChatGPT. Ideas were rated by **one domain expert** on novelty, value and feasibility, combined by geometric mean.
  - Results: creative quality M=6.5 vs 4.5, p<.001. Ideas per participant 10.3 (SD 8.46) vs 5.5 (SD 2.91), paired t p=.04. More diverse biological sources: 8.2 vs 4.6.
- **AskNatureGPT**: *J. Eng. Design* 37(1), 2026, [doi:10.1080/09544828.2025.2481536](https://www.tandfonline.com/doi/full/10.1080/09544828.2025.2481536) [PR]. Fine-tuned GPT-3.5 on biological solution ↔ engineering problem ↔ innovation triples. Text only.
- **Zhu, Zhang & Luo, "BID concept generation using GPT"**: *J. Mech. Des.* 145(4):041409, 2023 [PR], [arXiv:2212.13196](https://arxiv.org/abs/2212.13196).
  - Method: three fine-tuned generators that differ by how loosely the problem space is represented. Case study: a lightweight flying car.
  - The companion preprint [arXiv:2204.09714](https://arxiv.org/abs/2204.09714) reports a fine-tuned "biomimicry-innovation evaluator" at 97.8% accuracy after 1 epoch (text classifier).
- **BARcode, "Imitation of Life: a search engine for BID"** (Emuna, …, Kittur, Shahaf): AAAI 2024 [PR], [arXiv:2312.12681](https://arxiv.org/abs/2312.12681).
  - Method: mines web text for bio-inspirations using NLU and data programming.
  - Evaluation: claims to **recover famous historical BID examples**, a usable ground-truth idea for Q4. Text only. Data and code are said to be released.
- **CNN patent-image retrieval for design-by-analogy** (Jiang, Luo et al.): *J. Mech. Des.* 143(6), 2021, DOI 10.1115/1.4049214 [PR], [arXiv:2003.08741](https://arxiv.org/abs/2003.08741).
  - Method: Dual-VGG features trained on visual material type plus the patent's IPC class, with cosine retrieval of near- and far-field stimuli.
  - Relevance: the only mature *image-based* analogy retrieval line found, but it uses patent drawings, not organisms.
- **GPT-4o literature mining of biomimetics**: *Sci. Rep.* 2025, ["Overlooked sources of inspiration"](https://www.nature.com/articles/s41598-025-11703-6) [PR]. Analysed 74,359 publications and extracted 31,776 biological models, which showed a strong bias toward a narrow set of animal taxa. Useful as a mechanism corpus and as a taxonomic-coverage reference. Text only.
- **Text-to-image for biomorphic design**: Christiansen, Rafsanjani & Jørgensen, *Front. Robot. AI* 2024, [doi:10.3389/frobt.2024.1472051](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1472051/pdf) [PR]. Text-to-image and image-to-image generation used to explore soft biomorphic robot design spaces. Qualitative.

### Gaps
1. No benchmark pairs **organism images with ground-truth mechanisms and the engineering designs derived from them**.
2. No study checks whether VLM-extracted mechanisms are physically right, for example with scale-dependent physics such as Re, Bond number, or JKR adhesion.
3. Buehler-lab systems report mostly qualitative case studies.
4. BioSpark's quality judgments rest on **one expert rater**.

---

## Q2. Generating design sketches / images / CAD with descriptions, and how they are evaluated automatically

### Takeaway
Code-as-geometry (CadQuery/Python, Blender scripts, TikZ, SVG) is the dominant route to *checkable* design outputs. It produces exact geometry that can be executed, measured, and rendered for a VLM to inspect. Automatic evaluation stacks:
- **geometry**: Chamfer distance, IoU, invalid/compile rate;
- **image–text alignment**: VQAScore beats CLIPScore on compositional prompts;
- **VLM-as-critic**: question-generation and answering over rendered views, as in CADCodeVerify.

For FLBDS, a blueprint as SVG or TikZ, *generated from the same parameter dict the physics checks use*, makes consistency checkable by construction.

### Cited findings
- **Text2CAD** (Khan et al.): NeurIPS 2024 spotlight [PR], [arXiv:2409.17106](https://arxiv.org/abs/2409.17106).
  - Data: annotated DeepCAD (~170K models) with ~660K text prompts from beginner to expert level.
  - Model: transformer that emits CAD construction sequences.
  - Metrics: F1 on line/arc/circle/extrusion primitives, Chamfer distance, invalidity ratio, and a GPT-4V visual comparison on 1,000 samples per complexity level, plus human preference.
- **CADCodeVerify**: "Generating CAD Code with VLMs for 3D Designs", ICLR 2025 [PR], [arXiv:2410.05340](https://arxiv.org/abs/2410.05340).
  - Method: the VLM renders the generated CadQuery object, generates verification questions, answers them, and feeds the answers back as corrections.
  - Benchmark: **CADPrompt**, 200 objects with NL prompts and expert Python code.
  - Results with GPT-4: −7.30% point-cloud distance and +5.5% compile rate vs prior work. The ICLR abstract reports +5.0% success rate.
  - Relevance: the template for FLBDS's "VLM checks the sketch against the spec" loop.
- **CAD-Recode**: [arXiv:2412.14042](https://arxiv.org/abs/2412.14042) [pre], ICCV 2025 version on [ORBilu](https://orbilu.uni.lu/bitstream/10993/67036/1/CADRecode_ICCV_2025.pdf) [PR]. Point cloud → CadQuery Python using a small LLM decoder and a point projector. Trained on **1M procedurally generated CAD sequences**. Evaluated on DeepCAD, Fusion360 and CC3D with CD, IoU and invalid ratio. Numbers N/R in the abstract.
- **Picard et al., "From Concept to Manufacturing: evaluating VLMs for engineering design"**: *Artif. Intell. Rev.* 58 (2025) [PR], [arXiv:2311.12668](https://arxiv.org/abs/2311.12668).
  - Scope: GPT-4V and LLaVA-1.6-34B on >1,000 queries covering sketch similarity, Pugh-chart selection, CAD generation, topology optimization, DfM and textbook problems.
  - Failure modes: complex engineering drawings, accurate CAD, **volume-fraction estimation**, and spotting floating material.
  - Relevance: a direct warning that VLMs should not judge quantitative geometry. Closed-form checks should do that.
- **Sketch2Prototype** (Edwards, Man, Ahmed): Proc. Design Society (DESIGN 2024) [PR], [arXiv:2405.12985](https://arxiv.org/abs/2405.12985). Sketch → text (GPT-4) → images (DALL-E 3) → 3D → fabricated prototype. Code on [GitHub](https://github.com/BrandonMan123/Sketch2Prototype). Evaluation compared diversity and manufacturability against direct sketch-to-3D and ControlNet baselines.
- **DeTikZify** (Belouadi, Ponzetto, Eger): NeurIPS 2024 spotlight [PR], [arXiv:2405.15306](https://arxiv.org/abs/2405.15306).
  - Method: sketch or figure → TikZ program, with MCTS refinement guided by self-assessed visual similarity.
  - Data: DaTikZv2 (>360K TikZ graphics), SketchFig, MetaFig.
  - Result: beats Claude 3 and GPT-4V in automatic and human evaluation. Models on [HF](https://huggingface.co/collections/nllg/detikzify).
  - Relevance: the most directly reusable "blueprint-style schematic" generator.
- **StarVector**: [arXiv:2312.11556](https://arxiv.org/abs/2312.11556) [pre; CVPR 2025 *(unverified)*]. Image/text → SVG code. Introduces SVG-Bench (10 datasets; image-to-SVG, text-to-SVG, diagrams) and **DinoScore**, arguing that pixel MSE is a poor metric for vector graphics.
- **SVGenius**: [arXiv:2506.03139](https://arxiv.org/abs/2506.03139) [pre]. 2,377 queries, 8 task categories, 18 metrics, 22 models. All models degrade with complexity, and reasoning-tuned models beat scaled-up ones.
- **VQAScore** (Lin et al.): ECCV 2024 [PR], [arXiv:2404.01291](https://arxiv.org/abs/2404.01291).
  - Method: score = P("Yes" | image, "Does this figure show '{text}'?").
  - Result: state of the art on 8 image–text alignment benchmarks, and better than CLIPScore, which acts as a "bag of words" on compositional prompts.
  - GenAI-Bench: 1,600 designer-written prompts, 1–5 Likert ratings, 3 annotators per pair.

### Gaps
1. No metric measures whether a *bio-inspired design sketch* is faithful to both the **mechanism** and the **engineering parameters**. VQAScore checks semantics, not dimensions.
2. CAD benchmarks (DeepCAD, CADPrompt) are mechanical parts with no biological analogy.
3. Raster diffusion sketches cannot be checked geometrically, so FLBDS should render from parameters (SVG/TikZ/CadQuery) and use a VLM only for semantic QA.

---

## Q3. What open VLMs reliably infer from organism images, and where they fail

### Takeaway
VLMs are fairly reliable at **coarse identification** (species MCQ ~80% for frontier models) and **presence/absence of salient traits**. They are unreliable at **localizing traits, counting, measuring and scale**, and they are easily misled by suggestive prompts. Design needs morphology plus scale plus function, and only morphology is reasonably safe. Scale must therefore come from text, a scale bar, or a lookup table (e.g. species → size database), never from VLM estimation.

### Cited findings
- **VLM4Bio**: NeurIPS 2024 Datasets & Benchmarks [PR], [arXiv:2408.16176](https://arxiv.org/abs/2408.16176), [code](https://github.com/imageomics/VLM4Bio).
  - Scale: 469K QA pairs over ~30K images. 12 VLMs tested zero-shot: GPT-4V, LLaVA-1.5 7B/13B, CogVLM, BLIP-FLAN-T5, MiniGPT-4, InstructBLIP; GPT-4o was added later.
  - Datasets:

    | Dataset | Images | Species | Traits | Source | Licence |
    |---|---|---|---|---|---|
    | Fish-10K | 10,347 | 495 | 10 | FishAIR/iDigBio | CC BY-NC |
    | Bird-10K | 11,092 | 188 | 28 | CUB-200-2011 | CC BY |
    | Butterfly-10K | 10,013 | 60 | – | Jiggins *Heliconius* collection | CC BY 4.0 |

    Fish-500 and Bird-500 carry bounding-box annotations. The VLM4Bio release itself is CC BY 4.0.
  - Results for GPT-4V:
    - species MCQ 82.6% on birds (chance 25%), but **open-ended species only 17.4%**;
    - trait identification 82.2% on fish;
    - **trait grounding 29.4% (fish) and 8.1% (birds)**, at or below chance;
    - trait referring 28–42%;
    - counting 16.4% open-ended and 44.8% MCQ.
  - Best overall average was 34.2%.
  - Prompting: CoT helped GPT-4o (fish 79 → 86; butterfly 56.4 → 74.6). Dense captions helped on birds (78.8 → 87.4) but **hurt on fish (34.4 → 18.8)**.
  - Hallucination: in the false-confidence test, LLaVA-1.5-7B agreed 99.8% of the time with a suggested wrong answer, at 25% accuracy.
- **BioCLIP 2**: NeurIPS 2025 [PR], [arXiv:2505.23883](https://arxiv.org/abs/2505.23883).
  - Data: TreeOfLife-200M, 214M images over 952K taxa.
  - Results: +18% species accuracy over BioCLIP. Emergent embedding structure clusters species by ecology and function, and keeps life stage and sex separable in orthogonal subspaces.
  - Relevance: a strong *retrieval/ID front-end*. Use it to identify the organism, then look up mechanisms in text corpora.
- **MicroVQA**: CVPR 2025 [PR], [arXiv:2503.13399](https://arxiv.org/abs/2503.13399), [data](https://huggingface.co/datasets/jmhb/microvqa), CC BY-SA 4.0.
  - Scale: 1,042 expert MCQs (12 experts, 31 organisms; brightfield, fluorescence and EM; tissue to atomic scale).
  - Best scores: o1 52.8%, Claude-3.5-Sonnet 51.7%, Gemini-1.5-Pro 51.1%, Qwen2-VL-7B 48.8%. Human baseline 50.3%, chance 22%.
  - **Image vs text**: on naively generated MCQs GPT-4o reached 93% *without needing the image*, because of language shortcuts. Only after the RefineBot rewrite do the questions require the image.
  - Error analysis (Claude-3.5): **perception 50%**, knowledge 30%, overgeneralization 13%.
  - Implication: many "multimodal" wins are text-only wins, so FLBDS must run a no-image ablation.
- **Picard et al. 2025** (see Q2): VLMs fail at volume-fraction and quantitative geometric estimation.
- **"Image beats text-only" evidence**:
  - **Edwards et al., "AI Judges in Design"** ([arXiv:2504.00938](https://arxiv.org/abs/2504.00938) [pre]; *J. Mech. Des.* 2026 version on the [MIT DeCoDE page](https://decode.mit.edu/assets/papers/2026_Edwards_judges_jmd.pdf)): the best judge used **text + image in-context examples with reasoning**, and it beat unimodal-prompt variants.
  - **MicroVQA** shows the converse: without debiasing, text alone is enough.
  - No BID study was found that isolates the image's contribution to design quality.

### Gaps
1. No benchmark tests **function/mechanism inference** from organism images (e.g. "what makes this surface superhydrophobic?"). VLM4Bio covers ID and traits only.
2. No benchmark tests **scale estimation** for organisms.
3. No study shows image > text-only for *design* outcomes. FLBDS could make that ablation a contribution.

---

## Q4. Automatic evaluation without human raters

### Takeaway
A single LLM judge of *novelty or feasibility* agrees with humans at about chance level on research ideas (≈51–53% pairwise, vs 56% human–human). It gets close to experts only on narrow, rubric-based visual criteria when given in-context examples, and even there expert–expert κ is only 0.26–0.59. Reliable automatic signals, in decreasing order:
1. **verifiable checks** (physics, geometry, compile);
2. **rediscovery of held-out known designs** (MOOSE-Chem-style contamination-controlled ground truth, BARcode recovering historical BID examples);
3. **embedding-based novelty and diversity** against corpora (patents, AskNature), with explicit thresholds;
4. **multi-family judge panels** (PoLL) for semantic QA only, reported with agreement statistics and with a human-free calibration set built from known designs.

### Cited findings
- **Si, Yang & Hashimoto, "Can LLMs generate novel research ideas?"**: ICLR 2025 [PR], [arXiv:2409.04109](https://arxiv.org/abs/2409.04109).
  - Human study: 100+ NLP researchers, 49 ideas per condition, ~300 reviews. AI ideas were judged more novel (p<.05) and slightly less feasible.
  - **LLM-judge agreement** with human top/bottom-25% splits: Claude-3.5 pairwise 53.3%, Claude-3.5 direct 51.7%, GPT-4o direct 50.0%, GPT-4o pairwise 45.0%, "AI Scientist" reviewer 43.3%. Humans agree with each other 56.1%; chance is 50%.
  - On ICLR accept/reject pairs Claude-3.5 reached 71.4%.
  - **Duplication**: of 4,000 seed ideas only 200 were unique (5%) at cosine > 0.8 with all-MiniLM-L6-v2. A ready-made automatic diversity metric.
- **Edwards, Tehranchi, Miller & Ahmed, "AI Judges in Design"**: [arXiv:2504.00938](https://arxiv.org/abs/2504.00938) [pre], JMD 2026 [PR].
  - Setup: VLM judges of early-stage design *sketches* on uniqueness, creativity, usefulness and drawing quality, compared with experts using a statistical-equivalence framework (TOST-style).
  - Data: **934 milk-frother sketches**, ~875 in the test set after removing 50 in-context examples. 2 expert raters and 3 trained novices.
  - Judges: GPT-4o (2024-08-06); the top judge adds o1 for reasoning. Equivalence test: TOST with a ±1.0 margin on a 6-point Likert scale.
  - **Experts agree with each other only moderately** (κ/ICC):

    | Metric | Expert vs expert | Best AI judge vs E1 | Best AI judge vs E2 |
    |---|---|---|---|
    | Uniqueness | 0.54 | 0.49 | 0.52 |
    | Creativity | 0.26 | 0.15 | 0.22 |
    | Usefulness | 0.59 | 0.35 | 0.19 |
    | Drawing quality | 0.33 | 0.31 | 0.29 |

    AI-judge figures are from run 1.
  - Results: the best configuration (text + image ICL + reasoning) reached **expert-level equivalence for uniqueness and drawing quality**, and matched or beat trained novices on all metrics. It equalled or exceeded most novices in 6/6 runs for uniqueness and creativity, and 5/6 for drawing quality and usefulness.
  - Not reached: expert-level equivalence on **usefulness (the feasibility-like criterion)** and creativity.
  - Implication: even a strong VLM judge is weakest on exactly the criterion FLBDS cares about, so physics checks must carry feasibility.
- **PoLL, "Replacing Judges with Juries"** (Verga et al., Cohere): [arXiv:2404.18796](https://arxiv.org/abs/2404.18796) [pre].
  - Setup: a panel of 3 smaller models from different families (Command R, Haiku, GPT-3.5) tested over 6 datasets.
  - Cohen's κ vs humans: NQ 0.763, TriviaQA 0.906, HotpotQA 0.867. A single GPT-4 judge scored 0.627, 0.841 and 0.830.
  - Less intra-model bias and more than 7× cheaper. Note this is QA correctness, not creativity.
- **MOOSE-Chem**: ICLR 2025 [PR], [arXiv:2410.07076](https://arxiv.org/abs/2410.07076), [code](https://github.com/ZonglinY/MOOSE-Chem).
  - Ground truth: **51 Nature/Science-level 2024 chemistry papers**, decomposed by PhD students into background, inspirations and hypothesis.
  - Setup: the LLM (training cutoff 2023) gets the background plus a corpus containing the true inspirations, and must **rediscover** the hypothesis. Many are recovered at high similarity.
  - Relevance: the template for FLBDS rediscovery evaluation. Hold out known bio-inspired products whose organism image is the input, and score recovery of mechanism and design parameters.
- **BARcode** (AAAI 2024, see Q1): evaluated partly by recovering famous historical BID examples, the same rediscovery logic.
- **BioSpark** (CHI '25): used a geometric mean of novelty × value × feasibility from 1 expert. The rubric is reusable for an LLM judge, but the human reliability baseline is weak.
- **Zhu–Luo** [arXiv:2204.09714](https://arxiv.org/abs/2204.09714): a fine-tuned GPT "BID-ness" classifier at 97.8% accuracy, a cheap automatic gate for "is this a genuine biological analogy?". Text, not peer-reviewed in that form.

### Gaps
1. No validated automatic **feasibility** judge exists for engineering concepts. FLBDS's closed-form physics checks *are* the feasibility judge, which is a selling point.
2. No public "known bio-inspired designs" rediscovery set **with images** (e.g. lotus → self-cleaning, gecko → dry adhesive, Morpho → structural colour, boxfish → car body, termite mound → ventilation, kingfisher → train nose). Building one with licensed images, from Wikimedia CC BY/CC0 or iNaturalist CC licences, is a contribution.
3. Embedding novelty against patents has no BID-specific validation. The candidate tool is **PaECTER** ([arXiv:2402.19411](https://arxiv.org/abs/2402.19411) [pre], Max Planck Institute for Innovation and Competition): BERT-for-Patents fine-tuned on examiner citation triplets from 300K EPO patent families (1985–2022). It beats BERT-for-Patents, E5, GTE and BGE on citation prediction, and is on HF. Use nearest-patent cosine as a "prior-art distance" signal, but it has not been calibrated against human novelty judgments.

---

## Q5. Closest related work: comparison

| # | Name | Year | Venue | Image input? | Physics check? | Design image output? | Evaluation |
|---|---|---|---|---|---|---|---|
| 1 | Cephalo ([2405.19076](https://arxiv.org/abs/2405.19076)) | 2024 | Adv. Funct. Mater. [PR] | **Yes** (micrographs, photos) | No | Yes (generated microstructure images) | Qualitative case studies |
| 2 | Bioinspired123D ([2603.29592](https://arxiv.org/abs/2603.29592)) | 2026 | arXiv [pre] | Only renders, for the VLM critic | No (geometry validity only) | **Yes** (Blender 3D) | New script benchmark; ~4× over base |
| 3 | BioSpark ([CHI'25](https://arxiv.org/abs/2503.09838)) | 2025 | CHI [PR] | Display only (GPT-4V ranks photos) | No | No | User study N=12; 1 expert rater |
| 4 | BioinspiredLLM ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10933662)) | 2024 | Adv. Sci. [PR] | No | No | No (text; paired with gen-AI images in demos) | Knowledge-recall QA |
| 5 | BIDARA ([AAAI-SS](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210)) | 2024 | AAAI Spring Symp. | No | No | No | Rated feasibility with/without RAG |
| 6 | AskNatureGPT ([JED](https://www.tandfonline.com/doi/full/10.1080/09544828.2025.2481536)) | 2026 | J. Eng. Design [PR] | No | No | No | Case studies / ratings |
| 7 | Zhu–Luo GPT BID ([2212.13196](https://arxiv.org/abs/2212.13196)) | 2023 | J. Mech. Des. [PR] | No | No | No | Case study (flying car) + classifier |
| 8 | BARcode ([2312.12681](https://arxiv.org/abs/2312.12681)) | 2024 | AAAI [PR] | No | No | No | Rediscovery of historical BID + expert usefulness |
| 9 | CADCodeVerify ([2410.05340](https://arxiv.org/abs/2410.05340)) | 2025 | ICLR [PR] | Renders, for VLM self-check | Geometric (point-cloud distance, compile) | **Yes** (CAD) | CADPrompt (200), PC distance, compile rate |
| 10 | Sketch2Prototype ([2405.12985](https://arxiv.org/abs/2405.12985)) | 2024 | DESIGN (Des. Soc.) [PR] | **Yes** (hand sketch) | No (manufacturability heuristics) | **Yes** (images → 3D → print) | Diversity / manufacturability vs baselines |
| 11 | Picard et al. VLMs for eng. design ([2311.12668](https://arxiv.org/abs/2311.12668)) | 2025 | AI Review [PR] | **Yes** | Tests VLM on topology opt./DfM | Partly (CAD) | >1,000 queries benchmark |
| 12 | Jiang–Luo patent-image retrieval ([2003.08741](https://arxiv.org/abs/2003.08741)) | 2021 | J. Mech. Des. [PR] | **Yes** (patent drawings) | No | No (retrieval) | Retrieval accuracy |
| — | **FLBDS (target)** | 2026 | — | **Yes (organism)** | **Yes (closed-form, multi-domain)** | **Yes (parametric blueprint)** | Automatic: physics + rediscovery + VLM-QA + no-image ablation |

Read-out: no row has all three of image input, physics check and design-image output. CADCodeVerify comes closest to the evaluation pattern, and Cephalo and Bioinspired123D are the closest bio-inspired neighbours.

---

## Datasets used by the cited works

| Dataset | Used by | Content | Size | Licence |
|---|---|---|---|---|
| VLM4Bio (Fish/Bird/Butterfly-10K, -500) | VLM4Bio | Organism images + trait QA | ~30K images, 469K QA | CC BY 4.0 (components: CC BY-NC fish, CC BY birds, CC BY 4.0 butterflies) |
| TreeOfLife-200M | BioCLIP 2 | Organism images with taxonomy | 214M images, 952K taxa | See [HF/imageomics](https://huggingface.co/imageomics) card (mixed source licences) *(unverified)* |
| MicroVQA | MicroVQA | Microscopy MCQs | 1,042 Q; 255 image sets | CC BY-SA 4.0 |
| CUB-200-2011 | VLM4Bio | Bird images | 11,788 images, 200 species *(unverified)* | Research use |
| Cephalo training pairs | Cephalo | Image–caption pairs from papers + Wikipedia | "Thousands of papers"; not released as a named set | N/R |
| Bioinspired3D scripts | Bioinspired123D | Blender Python bio-geometries | >4,000 scripts | N/R |
| BioinspiredLLM corpus | BioinspiredLLM | Biological-materials papers → Q&A | >1,000 articles | Not redistributed (copyrighted papers) |
| AskNature.org | BioSpark, AskNatureGPT, BIDARA (RAG) | Function-indexed biological strategies | ~1,800 strategies *(unverified)* | Biomimicry Institute terms; check before redistribution |
| BioSpark generated mechanisms | BioSpark | Species → mechanism triplets (GPT-4-expanded) | N/R in excerpt | N/R |
| PeTaL labelled corpus | NASA PeTaL / BIDARA | Biology papers labelled with function taxonomy | >1,400 articles ([blog](https://nasa-petal.github.io/blog/posts/engineering-elegance-from-nature)) | NASA open source (repo) |
| GPT-4o biomimetics mining | Sci. Rep. 2025 | Biological models in biomimetics literature | 74,359 papers → 31,776 models | Article CC BY |
| DeepCAD + Text2CAD annotations | Text2CAD | CAD sequences + text | ~170K models, ~660K prompts | DeepCAD MIT *(unverified)* |
| CADPrompt | CADCodeVerify | NL prompt + CadQuery code | 200 objects | See repo |
| CAD-Recode synthetic | CAD-Recode | Procedural CadQuery sequences | 1M | See repo |
| DaTikZv2 / SketchFig / MetaFig | DeTikZify | TikZ graphics, sketches | >360K TikZ | Mixed (arXiv sources) |
| SVG-Bench / SVGenius | StarVector / SVGenius | SVG tasks | 10 datasets / 2,377 queries | See repos |
| GenAI-Bench | VQAScore | Compositional prompts + human ratings | 1,600 prompts | See repo |
| MOOSE-Chem bench | MOOSE-Chem | 2024 chemistry papers decomposed | 51 papers | Repo |
| Si et al. ideas + reviews | Si et al. | NLP ideas + ~300 reviews | 49 ideas × 3 conditions | Repo ([NoviScl/AI-Researcher](https://github.com/NoviScl/AI-Researcher)) |
| Picard et al. VLM eng-design bench | Picard et al. | Engineering-design VQA | >1,000 queries | See MIT DeCoDE |

---

## Implications for FLBDS (short)
1. **Perception front-end**: use BioCLIP 2 for organism ID (strong), then text-corpus lookup for mechanisms and length scales. Keep VLM output to morphology and qualitative traits. Never let the VLM estimate scale, counts or volume fractions (VLM4Bio, Picard).
2. **Design image**: render SVG/TikZ/CadQuery from the *same parameter dict* the physics checks use, then run a CADCodeVerify-style VLM QA plus VQAScore for semantic consistency.
3. **Evaluation without humans**:
   - (a) physics pass rate;
   - (b) a rediscovery set of ~20–50 canonical BID cases with CC-licensed organism images and hidden target designs;
   - (c) a no-image ablation, because MicroVQA shows text shortcuts;
   - (d) Si-style dedup/diversity (MiniLM cosine > 0.8);
   - (e) a PoLL judge panel for semantic rubric items only, reported with κ against the rediscovery ground truth.
