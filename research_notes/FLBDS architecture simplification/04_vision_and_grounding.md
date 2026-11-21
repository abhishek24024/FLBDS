# 04 — Vision and grounding for M1 (biological image → mechanism cards): feasibility with open models (2023–Nov 2026)

Scope: whether, and how simply, FLBDS stage M1 (photo → Mechanism Cards) can be built with open-weight models on 4×H200 / vLLM 0.32. Context from `00_project_digest.md`: M1 is unbuilt; no VLM, BioCLIP or embedder is on the server; the text silver-card pilot gave 135 cards, but 51 of the 53 biology cards described engineered materials, not organisms; the benchmark biology is 4 hand-written fixtures; 16 benchmark organisms are known in advance (4 dev, 12 test).

Research done 2026-11-19 (about 20 search/fetch calls). Benchmark numbers come from the primary papers or model cards unless noted.

---

## Q1. Organism identification: BioCLIP / BioCLIP 2 and VLMs, accuracy by taxonomic level

### Takeaway
BioCLIP 2 (open_clip, MIT licence) is the strongest open zero-shot species identifier: a 55.6% mean top-1 over 10 species benchmarks, 96.8% on PlantNet, 76.8% on Rare Species. General VLMs are much worse at naming species (Qwen2.5-VL-7B about 21% open-vocabulary zero-shot). Accuracy rises a lot at higher ranks (species about 40% → order about 80% for small VLMs). VLMs help as re-rankers of a specialist's top-k (+6.4 points), not as primary identifiers. Open-ended VLM identification invents nonexistent species names 5.9–9.6% of the time.

### Cited Findings
- **BioCLIP 2 setup:** ViT-L/14 initialised from CLIP (LAION-2B). Trained on TreeOfLife-200M (about 214M images, 952,257 taxa) for 30 epochs on 32 H100s for 10 days. Paper first submitted May 2025; v2 dated Oct 2025; NeurIPS 2025 poster. — [BioCLIP 2 arXiv 2505.23883v2](https://arxiv.org/html/2505.23883v2); [NeurIPS 2025](https://neurips.cc/virtual/2025/poster/115146)
- **Zero-shot species top-1, BioCLIP 2 vs BioCLIP vs SigLIP vs CLIP:**

  | Benchmark | BioCLIP 2 | BioCLIP | SigLIP | CLIP |
  |---|---|---|---|---|
  | Mean (10 benchmarks) | 55.6 | 37.6 | 39.5 | 25.5 |
  | NABirds | 74.9 | – | – | – |
  | Insects | 55.3 | – | – | – |
  | Insects 2 | 27.7 | – | – | – |
  | Camera Trap | 53.9 | – | – | – |
  | PlantNet | 96.8 | – | – | – |
  | Fungi | 83.8 | – | – | – |
  | Rare Species | 76.8 | – | – | – |
  | Plankton | 3.9 | – | – | – |
  | PlantVillage | 25.1 | – | – | – |

  Few-shot mean: 1-shot 64.1, 5-shot 78.3. — [BioCLIP 2 arXiv](https://arxiv.org/html/2505.23883v2). (The fetched table text was partly garbled; check against the PDF before quoting exact cells.)
- **BioCLIP 2 non-species tasks:** habitat/trait tasks (FishNet 39.8, NeWT 89.1, AwA2 69.5, Herbarium19 48.6, PlantDoc 40.4); mean 57.5 vs DINOv3 48.6 and CLIP 42.7. — [BioCLIP 2 arXiv](https://arxiv.org/html/2505.23883v2)
- **BioCLIP 2 model card:** MIT licence; loads with `open_clip.create_model_and_transforms('hf-hub:imageomics/bioclip-2')`. The long-tailed training data means "predictions … might be biased toward well-represented species". The model is not geo-tagged. The card reports no genus- or family-level accuracy. — [HF imageomics/bioclip-2](https://huggingface.co/imageomics/bioclip-2)
- **Edge-deployable VLM study (2026, 96 species):**
  - Models: Qwen3-VL 2B/4B/8B and Gemma 3 4B (4-bit) vs BioCLIP (300M).
  - Accuracy rises from about 37–44% at species level to about 77–80% at order level.
  - BioCLIP beat every VLM. On camera-trap crops it scored 71.0% vs 32.0% for the best VLM.
  - Camera-trap images cost VLMs 11.5–22.3 points vs clean iNaturalist photos.
  - Open-ended prompts produced nonexistent but plausible species names in 5.9–9.6% of responses; Gemma 3 was worst, and the rate fell as Qwen3-VL size grew.
  - — [HF papers 2609.11916](https://huggingface.co/papers/2609.11916.md)
- **"Surely LMMs (don't) excel in visual species recognition" (Dec 2025, 5 benchmarks):**
  - Qwen2.5-VL-7B zero-shot, open-vocabulary: 21.2% mean.
  - Chain-of-thought: 19.0%. Self-verification: 21.4%.
  - Supplying the candidate class names: 35.6%.
  - A 16-shot fine-tuned OpenCLIP ViT-B/32 expert: 59.2%.
  - **Post-hoc correction** (the LMM re-ranks the expert's top-5 with confidences and reference images): 65.6% (+6.4). Gains by benchmark: Aves 58.2→69.4, Insecta 63.8→70.5, Weeds 80.7→87.7, Fungi 29.9→31.1.
  - — [arXiv 2512.15748](https://arxiv.org/html/2512.15748v1)
- **VL-Taxon on iNat21-Animal (Qwen2.5-VL-7B):** baseline about 41.8% leaf and 19.9% hierarchical-consistency accuracy, rising to about 51.7 / 26.5 after SFT. The authors say the taxonomy-tuned 7B beats Qwen2.5-VL-72B by more than 10%. — [search summary of arXiv 2601.14610](https://arxiv.org/html/2601.14610) (not fetched in full)
- **FishNet++:** zero-shot Qwen2.5-VL reaches 6.2% on frequent and 0.2% on rare marine species. Fine-tuning raises frequent-species accuracy to 37.0%, still below BEiT's 43.4%. Fine-tuned predictions are taxonomically closer to the truth at higher ranks. — [FishNet++ arXiv 2509.25564](https://arxiv.org/html/2509.25564v1) (search snippet)
- **Neural Catalog / VR-RAG:** on iNaturalist-Birds, Qwen2.5-VL scored 16.8%, Qwen2-VL 12.0% and InternVL 4.2%. Naive retrieval-augmented prompting did not help (11.9%). — [arXiv 2505.05635](https://arxiv.org/html/2505.05635v1) (search snippet)
- **VLM4Bio (NeurIPS 2024 D&B; 469K QA pairs, 30K fish/bird/butterfly images):**
  - Open-ended species ID is close to zero (best: fish 1.01%, bird 17.40%, butterfly 9.94%).
  - Multiple-choice species ID with 4 options (25% chance): fish 40.2% best, butterfly 50.2% best, bird 82.6% (GPT-4V).
  - — [VLM4Bio arXiv 2408.16176](https://arxiv.org/html/2408.16176v1)

### Inferences
- For FLBDS the organism set is closed and small (16 benchmark organisms plus whatever the corpus covers). BioCLIP 2 zero-shot over a **restricted candidate list** (the organisms that have corpus/literature coverage) is far easier than open-world species ID. Abstaining below a similarity threshold is cheap. This needs about 1 GB of weights and runs on CPU or a fraction of one GPU (inferred: ViT-L/14 scale).
- Mechanism lookup is usually robust at **genus or family level**: gecko adhesion is shared across gekkonids, and plastron respiration across aquatic beetle and bug taxa. A top-k/rank-backoff design (species → genus → family) suits FLBDS better than species accuracy alone. This is an inference; I found no paper that measures it.
- The digest's 51/53 problem (cards about engineered materials) is a **corpus-selection** failure, not a vision failure. Retrieval keyed on taxon names fixes it more directly than better image models.

### Gaps
- I found no published genus- or family-level accuracy for BioCLIP 2. Only species-level results and the "hierarchical" training claim exist.
- I found no results for BioCLIP 2 on SEM or close-up microstructure images (setae, leaf papillae). Its training data is whole-organism photos (iNat/EOL/GBIF style), so such images are out of distribution.

---

## Q2. Open VLMs on scientific and biological image understanding

### Takeaway
On expert microscopy reasoning (MicroVQA, CVPR 2025) the best models score only about 50%, roughly the same as the human experts on that benchmark. Open models are close behind: Pixtral-Large 49.8, Qwen2-VL-72B 47.5, Qwen2-VL-7B 48.8. In the error analysis, 50% of errors were perception errors. VLMs identify traits well but **ground and localise** them poorly (VLM4Bio: about 29–35% vs 25% chance). VLMs also follow leading prompts (sycophancy). I found no benchmark for fine-grained biological microstructure in SEM images (setae, lotus papillae). The best current open generalists are Qwen3-VL (2B–235B, Apache-2.0) and InternVL3.5 (MMMU 77.7 at 241B-A28B; 73.4 at 8B).

### Cited Findings
- **MicroVQA (CVPR 2025; 1,042 expert-written MCQs across microscopy modalities):**

  | Model | Overall accuracy (%) |
  |---|---|
  | o1 | 52.8 |
  | Claude 3.5 Sonnet | 51.7 |
  | Human experts | 50.3 |
  | Pixtral-Large (open) | 49.8 |
  | Qwen2-VL-7B (open) | 48.8 |
  | Qwen2-VL-72B (open) | 47.5 |
  | VILA1.5-40B (open) | 47.5 |
  | Llama-3.2-90B-Vision (open) | 42.4 |
  | Llama-3.2-11B-Vision (open) | 30.3 |
  | Random | 22.0 |

  - Errors in 30 reviewed Claude 3.5 Sonnet chains: 50% perception, 30% knowledge, 13% over-generalisation, 7% text hallucination or reasoning.
  - Refining the questions ("RefineBot") cut accuracy for all models.
  - The authors note that open-ended prompting gave "very vague answers".
  - — [MicroVQA arXiv 2503.13399](https://arxiv.org/html/2503.13399v1); [CVPR 2025 paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Burgess_MicroVQA_A_Multimodal_Reasoning_Benchmark_for_Microscopy-Based_Scientific_Research_CVPR_2025_paper.pdf)
- **VLM4Bio trait tasks (chance 25% unless stated):**
  - Trait *identification* is good: fish 82.2% (GPT-4V, chance 50%); bird 90.0% (InstructBLIP-13B, chance 31%).
  - Trait *grounding* is near chance: fish 29.4%, bird 35.4%.
  - Trait *referring*: 39.2% and 42.3%.
  - False-confidence test (a leading hint in the prompt): LLaVA-1.5-7B agreed with the hint 93–99.8% of the time at about 25% accuracy. GPT-4V's accuracy dropped to 5.2% on butterflies.
  - None-of-the-above test: GPT-4o 4.6% on butterflies.
  - — [VLM4Bio arXiv](https://arxiv.org/html/2408.16176v1)
- **MaCBench (chemistry/materials, Nature-family 2025):** models do well at equipment identification and standardised data extraction. They show "fundamental limitations in spatial reasoning, cross-modal information synthesis and multi-step logical inference", and may perceive correctly yet fail to connect observations "in scientifically meaningful ways". — [MaCBench arXiv 2411.16955](https://www.arxiv.org/abs/2411.16955); [PMC12513823](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12513823/)
- **μ-Bench** (microscopy) is dominated by brightfield and fluorescence images, so electron-microscopy coverage is thin. MatCha (2025) covers materials characterisation in 21 tasks. — [μ-Bench arXiv 2407.01791](https://arxiv.org/html/2407.01791v1); [MatCha arXiv 2509.09307](https://web3.arxiv.org/pdf/2509.09307)
- **Qwen3-VL (tech report arXiv 2511.21631, Nov 2025):** dense 2B/4B/8B/32B and MoE 30B-A3B / 235B-A22B. The 235B-A22B-Thinking model beats Gemini-2.5-Pro, GPT-5 and Claude Opus 4.1 on HallusionBench by 3.0 / 1.0 / 6.3 points. Secondary coverage reports Qwen3-VL at 69.3 on MMMU-Pro vs GPT-5 at 78.4; model size not stated. — [Qwen3-VL report](https://arxiv.org/html/2511.21631v2); [The Decoder](https://the-decoder.com/qwen3-vl-can-scan-two-hour-videos-and-pinpoint-nearly-every-detail/)
- **Qwen3-VL-32B-Instruct model card:** 33B parameters in BF16; Apache-2.0; native 256K context (expandable to 1M); vLLM serving example provided. — [HF Qwen3-VL-32B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct)
- **InternVL3.5 (Aug 2025):** MMMU 77.7 (241B-A28B) and 73.4 (8B). The 241B model is reported within 3.9% (relative) of GPT-5 overall. A 38.4B variant exists. — [InternVL3.5 arXiv 2508.18265](https://arxiv.org/html/2508.18265v2); [HF InternVL3_5-38B](https://huggingface.co/OpenGVLab/InternVL3_5-38B)

### Inferences
- A VLM can reliably produce **coarse descriptors** of the image: organism class, visible organ, imaging modality (photo / SEM / micrograph), scale bar text, environment. It is unreliable for **mechanism claims from pixels** (e.g. "these setae are 200 nm spatulae giving van der Waals adhesion"). That is knowledge, not perception, and MicroVQA and VLM4Bio show both perception and grounding are weak. Mechanism text should come from retrieved literature, not the VLM.
- Leading-question sycophancy (VLM4Bio false-confidence test) means the VLM prompt must **not include the hypothesised taxon or mechanism**. Ask for neutral descriptors, then cross-check against BioCLIP.

### Gaps
- No public benchmark evaluates open VLMs on bio-inspired-design microstructure images (gecko setae, lotus papillae, butterfly scales in SEM). The accuracy of the "structure tagging" step is therefore unknown and would have to be measured on FLBDS's own images.
- I did not obtain absolute MMMU or MMMU-Pro (biology subset) numbers for Qwen3-VL 32B/235B, nor for Llama 4, Gemma 3 or Molmo. The tables were in figures or in unread parts of the pages.
- I found no measured hallucination rate for free-text "mechanism descriptions" from images.

---

## Q3. Grounded (image → taxon → curated literature) vs direct (image → VLM writes the mechanism)

### Takeaway
The evidence consistently favours using the VLM narrowly and grounding the mechanism in text:
- Specialist encoder plus VLM re-ranking beats VLM-direct identification by about 30–45 points.
- Open-ended VLM answers invent taxa.
- Retrieval-augmented biomimicry systems report more feasible, higher-quality outputs than LLM-only.

That last evidence is weak: the RAG studies use expert ratings or small student studies, not hallucination benchmarks. Naive retrieval does not automatically help (VR-RAG birds: 16.8% → 11.9%).

### Cited Findings
- **Expert model + LMM re-rank vs LMM alone:** 65.6% vs 21.2% (Qwen2.5-VL-7B) on 5 species benchmarks; the gain holds across every few-shot method and backbone tested. — [arXiv 2512.15748](https://arxiv.org/html/2512.15748v1)
- **Nonexistent species names:** 5.9–9.6% of open-ended VLM responses. — [HF papers 2609.11916](https://huggingface.co/papers/2609.11916.md)
- **BIDARA (NASA, AAAI Spring Symposium 2024):** RAG plus ReAct agents for biomimicry. Retrieval made generated design solutions more feasible in both prompting and agent settings; it is motivated by LLM hallucination in domain-specific regimes. — [AAAI-SS 31210](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210); [NTRS](https://ntrs.nasa.gov/citations/20240003594)
- **Chen & Wang (Biomimetics, Sep 2025):** RAG over a 2,106-document AskNature corpus with local Llama 3.1, tested with 30 design students. "RAG-Large" gave superior text quality in high-demand stages. The authors note AskNature's keyword-centric search and fragmented knowledge structure. — [MDPI Biomimetics 10(9):626](https://www.mdpi.com/2313-7673/10/9/626); [PMC12467817](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12467817/)
- **Majumder et al. (ICoRD 2025):** RAG tool that generates SAPPhIRE models of artificial systems, with a preliminary factual-accuracy evaluation. Extension to biosystems is planned. This is the closest prior work to FLBDS's SAPPhIRE cards. — [arXiv 2406.19493](https://arxiv.org/pdf/2406.19493)
- **Retrieval needs care:** naive RAG prompting lowered Qwen2.5-VL species accuracy on iNat-Birds from 16.8% to 11.9%. — [arXiv 2505.05635](https://arxiv.org/html/2505.05635v1)

### Inferences
- **Recommended shape:** image → BioCLIP 2 top-k taxa (restricted candidates, abstain) → optional VLM re-rank and neutral descriptor tags → taxon-keyed literature retrieval → LLM extraction with verbatim spans. This is the grounded path.
- Direct image → VLM → mechanism should be kept only as an **ablation baseline** (it maps naturally onto FLBDS's A-Img condition).
- In FLBDS's main experiments the photo is not what limits performance; the M5 feedback loop is the only measured win. So M1 could start as **caption or taxon text input**, with the image path as a thin front end that only needs to produce a taxon. RQ2 (does the biology help?) depends on card quality, not image recognition.

### Gaps
- I found no controlled study measuring the hallucination rate of grounded vs ungrounded mechanism descriptions for bio-inspired design. All BID RAG evidence uses expert ratings or feasibility scores.

---

## Q4. Literature retrieval and quantitative parameter extraction

### Takeaway
- **Full text:** PMC OA with per-article licence buckets, via the BioC API.
- **Embedding and reranking:** Qwen3-Embedding / Qwen3-Reranker (0.6B–8B, MTEB-multilingual 70.58 at 8B; vLLM support).
- **Number extraction:** the best published LLM extraction of numbers, ChatExtract (Nat. Commun. 2024), reaches about 91% precision and 84–88% recall with GPT-4 and verification follow-up prompts. Open 70B-class models would need to be measured; expect lower.

### Cited Findings
- **PMC OA access:** the Open Access Subset is split into a commercial-use bucket (CC0, CC BY, CC BY-SA, CC BY-ND), a non-commercial bucket (CC BY-NC variants) and an "other" bucket (no or custom licence). Approved bulk routes are Cloud Service, OAI-PMH, FTP, E-Utilities and BioC. The BioC API serves OA full text as XML/JSON, usually refreshed within 24 h. — [PMC FTP](https://pmc.ncbi.nlm.nih.gov/tools/ftp); [PMC text mining](https://pmc.ncbi.nlm.nih.gov/tools/textmining/); [PMC developers](https://pmc.ncbi.nlm.nih.gov/tools/developers); [BioC-PMC](https://ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC)
- **Qwen3 Embedding (arXiv 2506.05176, Jun 2025):**
  - Sizes 0.6B, 4B and 8B for both embedding and reranking.
  - 8B embedding: 70.58 on MTEB Multilingual (ranked #1 on 5 Jun 2025).
  - Reranker MTEB-R: 0.6B 65.80, 4B 69.76, 8B 69.02. Reranking was run over the top-100 candidates from the 0.6B embedder.
  - vLLM usage guides are provided (`LLM(..., task="embed")`).
  - — [Qwen3 Embedding arXiv](https://arxiv.org/html/2506.05176v3); [HF Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B); [Qwen blog](https://qwenlm.github.io/blog/qwen3-embedding)
- **Qwen3-VL-Embedding / Qwen3-VL-Reranker (Jan 2026):** multimodal retrieval models, which could embed images and text together. — [arXiv 2601.04720](https://arxiv.org/pdf/2601.04720)
- **ChatExtract (Polak & Morgan, Nat. Commun. 15:1569, 2024):**
  - Zero-shot pipeline: relevance screen, then extraction of Material/Value/Unit triplets, then follow-up verification questions.
  - Bulk modulus test: 90.8% precision, 87.7% recall.
  - Practical database of metallic-glass critical cooling rates: 91.6% precision, 83.6% recall.
  - Best with GPT-4; the 2023 preprint claimed higher numbers than the published version.
  - Sentences with several values are harder than single-valued ones.
  - — [Nat. Commun. PDF](https://nature.com/articles/s41467-024-45914-8.pdf); [arXiv 2303.05352](https://arxiv.org/html/2303.05352v3)

### Inferences
- FLBDS already has the pieces for "verbatim span + Pint units" (stage 4 and stage 6 of the silver factory). Adding a ChatExtract-style yes/no verification turn ("Is value X for property Y of organism Z stated in this sentence?") is a cheap, evidenced upgrade. Measure precision on 50–100 hand-checked values before trusting it.
- Retrieval should be **taxon-first**:
  1. Query PMC/Europe PMC with the taxon name plus a function keyword (e.g. "Gekkonidae setae adhesion").
  2. Restrict to the commercial or non-commercial OA bucket.
  3. Rank chunks with Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B/4B.

  A BM25 + embedding hybrid with a reranker is enough. The planned three-head adversarial encoder is not needed for M1.

### Gaps
- I did not verify OpenAlex or Semantic Scholar rate limits or API-key policies as of 2026. A Semantic Scholar API licence page exists ([S2 API licence](https://api.semanticscholar.org/license)) but I did not read it.
- I did not retrieve SPECTER2 benchmark numbers; I have no evidence that it beats Qwen3-Embedding on biology retrieval.
- I found no accuracy report specific to extracting **biological** morphometrics (seta length, contact angle, tissue modulus) with open LLMs.

---

## Q5. Datasets of bio-inspired mechanisms with images, and their licences

### Takeaway
AskNature is the canonical curated set of strategies (about 2,100 documents were used in the 2025 RAG study). Its Terms of Use **prohibit robots/spiders and data mining** and require authorisation to reproduce or redistribute content. It cannot be bulk-scraped into an FLBDS corpus without permission from the Biomimicry Institute. Image datasets for taxon ID are permissive: BioCLIP 2 is MIT; VLM4Bio is Apache-2.0.

### Cited Findings
- **Biomimicry Institute Terms of Use (last updated 9.19.24; covers asknature.org):**
  - Forbids using "any robot, spider, site search/retrieval application".
  - Forbids using automated processes to "data mine" or reproduce the site's taxonomy.
  - Users may not "copy, reproduce, republish, download … distribute, modify" Materials without the owner's authorisation; downloaded material may be used "solely for the Purpose".
  - No Creative Commons licence is stated.
  - — [biomimicry.org/terms](https://biomimicry.org/terms/); [AskNature ToS](https://asknature.org/terms-of-service-privacy-policy)
- **AskNature as corpus and gold source:** the 2025 RAG study used a 2,106-document AskNature database. BioSpark (CHI 2025) uses AskNature as a "gold standard" source of inspirations. — [MDPI Biomimetics 10(9):626](https://www.mdpi.com/2313-7673/10/9/626); search summary of BioSpark
- **VLM4Bio dataset:** Apache-2.0 on HF (imageomics/VLM4Bio). — [VLM4Bio](https://arxiv.org/html/2408.16176v1)
- **BioCLIP 2 model:** MIT licence. The model card does not state the TreeOfLife-200M licence. — [HF bioclip-2](https://huggingface.co/imageomics/bioclip-2)
- The digest notes the deleted pre-Oct-2026 system had an "AskNature 2,744-graph" — [00_project_digest.md §3.2](./00_project_digest.md)

### Inferences
- Use AskNature **manually, as a pointer index**: read a strategy page and follow its cited primary papers, which are usually in PMC or the journal literature. Then extract from those papers, not from AskNature text. This is legally safer and gives better provenance.
- If the old 2,744-item AskNature graph is still archived, check how it was obtained before reusing it.

### Gaps
- BIOSCAN-5M and TreeOfLife-200M licences were not verified (TreeOfLife-200M aggregates sources with mixed licences, per its own dataset card; unread).
- I found no open dataset pairing organism images with *quantitative* mechanism parameters. FLBDS's 16-organism gold set would have to be hand-built.

---

## Q6. vLLM support and GPU memory on H200

### Takeaway
All candidate VLM families have vLLM architectures: Qwen2.5-VL, Qwen3-VL (dense and MoE), InternVL3/3.5, Llama 4, Gemma 3, Molmo, Pixtral, GLM-4.5V and Kimi-VL. Qwen3-VL-32B (BF16, about 66 GB of weights) fits on one 141 GB H200. Qwen3-VL-30B-A3B is cheaper still. BioCLIP 2 runs through open_clip, not vLLM, and is tiny.

### Cited Findings
- vLLM's supported-models list includes:
  - `Qwen2_5_VLForConditionalGeneration` (up to 72B)
  - `Qwen3VLForConditionalGeneration`
  - `Qwen3VLMoeForConditionalGeneration` (Qwen3-VL-30B-A3B)
  - `InternVLChatModel` (InternVL3 / 3.5)
  - `Llama4ForConditionalGeneration` (Scout-17B-16E)
  - `Gemma3ForConditionalGeneration` (up to 27B)
  - `MolmoForCausalLM`
  - `PixtralForConditionalGeneration`
  - `Glm4vMoeForConditionalGeneration` (GLM-4.5V)
  - `KimiVLForConditionalGeneration`

  Models that can run both generation and pooling need `--runner pooling` for embedding use. — [vLLM supported models](https://docs.vllm.ai/en/latest/models/supported_models.html)
- **Qwen3-VL-32B-Instruct:** 33B parameters in BF16; Apache-2.0. — [HF model card](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct)
- **Qwen3-Embedding:** vLLM `task="embed"` path documented. — [HF Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)

### Inferences
- **Memory (derived, not measured):**
  - 33B × 2 bytes ≈ 66 GB of weights, leaving about 70 GB of a 141 GB H200 for KV cache and the vision encoder.
  - An FP8 copy would be about 33 GB.
  - Qwen3-Embedding-0.6B plus Reranker-0.6B together are about 2.5 GB in BF16.
  - So M1 can run on **one H200** next to nothing else, or one GPU in sequence with the 72B text model.
- vLLM 0.32 (the server version) is newer than every Qwen3-VL and InternVL3.5 release, so architecture support should exist (inferred from the docs being "latest"). Verify with a smoke test before committing.
- One generalist VLM is enough. Choose **Qwen3-VL-32B-Instruct** (or 8B for speed), because it matches the existing Qwen stack and its Apache-2.0 licence and has a reported hallucination advantage in the 235B report.

### Gaps
- Exact vLLM version thresholds for Qwen3-VL and InternVL3.5 are unconfirmed. Real memory and throughput on H200 with images are unmeasured.

---

## Recommended simplest robust M1 design (synthesis for the architect)

These are inferences drawn from the findings above.

1. **Input:** a photo plus an optional caption. If the caption names a taxon, skip vision.
2. **Taxon:** BioCLIP 2 zero-shot over a **closed candidate list**: the organisms with OA literature in the corpus, at species, genus and family names. Take the top-5 with scores and **abstain** below a calibrated threshold. Optionally let Qwen3-VL-8B/32B re-rank the top-5 (evidence: +6.4 points). Never ask the VLM for an open-ended species name.
3. **Descriptor tags (optional):** the VLM fills enums (organ, imaging modality, visible scale, environment) from a neutral prompt that does not mention the hypothesised taxon or mechanism. Tags are only used as retrieval filters, never as mechanism claims.
4. **Retrieval:** taxon name plus function keyword → PMC/Europe PMC OA (licence bucket recorded) → BM25 + Qwen3-Embedding-0.6B → Qwen3-Reranker. This **directly fixes the 51/53 materials-not-organisms failure**, because every retrieved document is selected by organism name.
5. **Extraction:** reuse the existing 72B extractor, verbatim-span check and Pint stage. Add one ChatExtract-style verification turn for each numeric value. Measure precision on a 50–100-value hand-checked set.
6. **Evaluation of M1 itself:**
   - (a) top-1/top-5 taxon accuracy on about 48 held-out photos of the 16 benchmark organisms;
   - (b) card precision against hand-written gold for those 16 organisms;
   - (c) the A-Img ablation (VLM writes the mechanism directly) as a contrast.
7. **Drop for now:** the three-head adversarial encoder, citation expansion and the 3-level query planner. None has evidence of being needed at a 16-organism scale.
