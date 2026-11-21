# LLM-based and computational bio-inspired design (BID) and analogy retrieval, 2022 to Nov 2026: what works empirically and what is simplest

Scope note: this covers the biology-to-engineering mapping stages (FLBDS M1 to M4). Status labels: **[PR]** peer-reviewed, **[PP]** preprint, **[WS]** workshop or symposium. Dates are publication or arXiv dates. Several primary sources (Taylor & Francis, ScienceDirect, PMC, MDPI, AAAI-SS) blocked automated fetching (403, CAPTCHA or bot wall), so for some papers only abstracts or search snippets were read. Those items are marked "abstract only".

## Q1. Which LLM-based BID systems exist, what did they measure, and which components demonstrably improved outcomes?

### Takeaway
The best-evidenced LLM BID system is BioSpark (CHI 2025). Its evidence is a user study of human designers against an "AskNature + ChatGPT" baseline, not an ablation of the system's own components. In that study the most-used and most-useful features were simple LLM "transfer" prompts ("Sparks") and a Q&A box. The clustering and structure features were rated least useful. Across the field, no paper shows that a structured intermediate representation or a knowledge graph beats a strong LLM prompted directly, measured on a verifiable engineering outcome. Retrieval (RAG) gives reported feasibility or grounding gains, but the papers report them mostly without numbers.

### Cited Findings
- **BioSpark [PR, CHI 2025; arXiv 2503.09838, Mar 2025]** (Kang, Lin, Martelaro, Kittur et al., CMU / Toyota Research Institute).
  - Pipeline: seed AskNature entries become (problem, mechanism, species) triplets. GPT-4 (gpt-4-turbo-preview) builds a 7-level tree-of-life taxonomy per species and expands sparse branches with new mechanisms. Mechanisms are clustered by "active ingredient" with recursive DBSCAN. Per saved mechanism the system generates "Sparks" (2 transfer suggestions), "Trade-offs" (pros/cons table) and "Q&A". GPT-4V ranks species photos. — [BioSpark arXiv HTML](https://arxiv.org/html/2503.09838v1)
  - Study: within-subjects, N=12, two problems, 20 min each. Baseline was AskNature pages + ChatGPT + a spreadsheet. — [BioSpark](https://arxiv.org/html/2503.09838v1)
  - Expert-rated quality (geometric mean of novelty, value, feasibility): 6.5 vs 4.5 (t=16.22, p<.0001). Novelty 7.1 vs 3.9; value 7.0 vs 3.8; **feasibility was lower with BioSpark, 5.7 vs 6.8**. — [BioSpark](https://arxiv.org/html/2503.09838v1)
  - Ideas 10.3 vs 5.5 (p=.04); unique species used 8.2 vs 4.6 (p=.007). — [BioSpark](https://arxiv.org/html/2503.09838v1)
  - Feature usefulness (out of 7): Stream 6.3, Sparks 5.9 (most used, 6.2 times on average), Q&A 5.8, Trade-offs 5.2, **Clustering 4.1** (several participants never noticed it). — [BioSpark](https://arxiv.org/html/2503.09838v1)
  - Feeding back the last 20 Sparks ("precedent-based diversification") made Sparks more diverse: mean cosine 0.24 with it vs 0.17 without, p<.0001, over 3,800 pairs. Note that the direction of this metric as reported by the summariser needs checking in the paper. — [BioSpark](https://arxiv.org/html/2503.09838v1)
  - The only accuracy check was on taxonomy: GPT-4 hierarchy accuracy was 94.4 to 100% per level against 90 Wikipedia taxonomies. No systematic check of whether the mechanisms were biologically true was found in the text that was read. — [BioSpark](https://arxiv.org/html/2503.09838v1)
  - The authors flag a risk that LLM support causes "fixation and direct use rather than creative adaptation" (text extracted from the PDF). — [BioSpark PDF](https://arxiv.org/pdf/2503.09838)
  - An earlier workshop version was BioSpark [WS, NeurIPS 2023 workshop; arXiv 2312.11388]. — [arXiv 2312.11388](https://arxiv.org/abs/2312.11388)
- **Zhu, Zhang & Luo, "BID concept generation using GPT" [PR, J. Mech. Design 145(4), Apr 2023; arXiv 2212.13196, Dec 2022].**
  - Method: GPT-3 was fine-tuned into 3 generator types (problem described as application, as benefits + application, or as challenge) plus 3 fine-tuned relevance-classifier "evaluators". It was applied to a lightweight flying car. — [arXiv abs](https://arxiv.org/abs/2212.13196); [venue confirmation](https://cs.paperswithcode.com/paper/biologically-inspired-design-concept)
  - Evaluator validation accuracy: 75.3% (benefits), 79.8% (challenge), 94.4% (biomimicry relevance). — [Zhu et al. PDF](https://arxiv.org/pdf/2212.13196)
  - Share of concepts passing both relevance evaluators: 80% / 50% / 62% by generator type. Over 50% of retrieved analogies were birds. The authors read this as attribute-similarity retrieval, i.e. superficial (flying car, so flying animals). — [Zhu et al. PDF](https://arxiv.org/pdf/2212.13196)
  - Stated limitations: the knowledge is "mostly common-sense" rather than technical; the model produces "infeasible numbers from the engineering perspective"; and retrieval is biased toward historically common AskNature sources. — [Zhu et al. PDF](https://arxiv.org/pdf/2212.13196)
- **AskNatureGPT [PR, J. Engineering Design, 2025, doi 10.1080/09544828.2025.2481536]** (abstract only). An LLM fine-tuned on AskNature generates and evaluates solution-driven BID concepts. It was evaluated by an ablation, machine metrics, a human study with 10 industrial-design graduate students, and a 3-task case study. No numbers were retrieved. — [T&F listing](https://www.tandfonline.com/doi/full/10.1080/09544828.2025.2481536); [search summary](https://www.tandfonline.com/doi/full/10.1080/09544828.2025.2481536?af=R)
- **Solution-driven BID with a fine-tuned generator + 2 evaluators [PR, DRS 2024]** (abstract only). — [DRS 2024 paper 281](https://dl.designresearchsociety.org/drs-conference-papers/drs2024/researchpapers/281)
- **BIDARA (NASA PeTaL / Glenn) [WS, AAAI Spring Symposium 2024]** (Toukmaji & Tee).
  - Adds RAG to BIDARA's ReAct-style agents to reduce hallucination. Reports that "incorporating RAG increases the feasibility of the design solutions in both prompting and agent settings". Sample sizes and numbers were not retrievable (bot wall). — [AAAI-SS 31210](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210)
  - BIDARA itself is a GPT-4o chatbot instructed to follow the Biomimicry Institute process (define, biologize, discover, abstract, emulate). — [NASA NTRS 20240008030](https://ntrs.nasa.gov/citations/20240008030); [PeTaL](https://redirect.github.com/nasa-petal)
- **RAG over AskNature for automotive design [PR, Biomimetics (MDPI) 10(9):626, 2025]** (snippet only). RAG over a 2,106-document AskNature corpus with a locally run Llama 3.1. It positions BioTRIZ and SAPPhIRE as systematic but expertise-heavy. — [MDPI](https://www.mdpi.com/2313-7673/10/9/626)
- **Stage-specific RAG for biomimicry knowledge translation [PR, 2025, PMC12467817]** (could not be read because of a CAPTCHA). — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12467817/)
- **Cui, Zheng et al., cross-domain knowledge-retrieval RAG for BID [PR, Advanced Engineering Informatics, 2025/2026]** (abstract only). A unified knowledge graph aligns the engineering and biological domains. Validation was a single wastewater-treatment case study. — [PolyU record](https://research.polyu.edu.hk/en/publications/an-llm-based-cross-domain-knowledge-retrieval-augmented-generatio/); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1474034625009103)
- **BARcode, "Imitation of Life" [PR, AAAI 2024; arXiv 2312.12681]** (Emuna et al., HUJI). Mines bio-inspirations from the web at scale using NLU + data programming because hand-curated BID datasets are "small". Claims it recovers famous historical BID examples. Data and code are released. No numbers were in the abstract. — [arXiv](https://arxiv.org/abs/2312.12681v1); [AAAI record](https://mlanthology.org/aaai/2024/emuna2024aaai-imitation)
- **BioinspiredLLM [PP arXiv 2309.08788 (Sep 2023); later Advanced Science per PMC10933662]** (Luu & Buehler). An open-source LLM fine-tuned on over 1,000 papers on biological and bio-inspired materials. The abstract gives no quantitative comparison to the base model. — [arXiv](https://arxiv.org/abs/2309.08788); [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10933662/)
- **LLM multi-agent biomimetic furniture design [PR, Eng. Appl. of AI, 2026]** (abstract only). A model fine-tuned on biomimetic data scored well on entity recognition but showed "notable deficits" in functional fidelity and lifecycle completeness. — [ACM listing](https://dl.acm.org/doi/abs/10.1016/j.engappai.2026.114818)

### Inferences
- Every component with a measured, CI-separated gain in this literature is either retrieval of real examples (AskNature RAG, BIDARA RAG) or a cheap LLM transfer prompt (BioSpark Sparks). The elaborate structure (clustering, taxonomies, graphs) is either unmeasured or rated least useful. This matches FLBDS's own result: the feedback loop helped and the operators did not.
- No surveyed BID system verifies physics. Zhu et al. explicitly name "infeasible numbers" as a failure, and BioSpark lowered feasibility (5.7 vs 6.8). FLBDS's physics-in-the-loop check is therefore the differentiator, and it is also the piece with evidence behind it.
- All the human-study systems measure ideation quality (novelty and similar ratings), not engineering pass rates. No published BID system reports a verifiable outcome like PVR, so FLBDS cannot borrow a "this component improves verified designs" result from the literature.

### Gaps
- DANE (Goel lab) and newer IDETC/ICED/DCC 2023 to 2026 LLM BID papers were not individually retrieved within the tool budget.
- Numbers for AskNatureGPT's ablation, the BIDARA RAG feasibility effect, the MDPI AskNature-RAG paper and the AEI KG-RAG paper could not be read (paywalls or bot walls).
- No retrieved paper ran an ablation of a BID pipeline's components against a downstream verified metric.

## Q2. Structured intermediate representations (SAPPhIRE, FBS, BioTRIZ, functional basis) and TRIZ guidance vs letting the LLM reason directly

### Takeaway
TRIZ-plus-LLM papers (TRIZ-GPT, AutoTRIZ, TRIZ Agents) are small case studies with **no plain-LLM baseline**. None shows that TRIZ guidance improves design outcomes. The one benchmark (TRIZBench, ACL Findings 2026) finds that LLMs detect contradictions more easily than they recover the correct trade-off pair, and that TRIZ structure helps *principle prediction*, which is a classification task, not design quality. SAPPhIRE is mainly used as an annotation schema. Its bottleneck is manual effort, which LLMs are now used to fill, but no paper shows SAPPhIRE improves the downstream designs.

### Cited Findings
- **TRIZ-GPT [PP arXiv 2408.05897, Aug 2024]** (Chen et al.). GPT-4 vs GPT-3.5 with few-shot prompts. Evaluated by keyword and semantic distribution against the original patented solutions on two small case collections. GPT-4 solutions were closer to the originals and covered more strategies. There was no no-TRIZ baseline. — [arXiv 2408.05897](https://arxiv.org/pdf/2408.05897); [abstract](https://arxiv.org/html/2408.05897v1)
- **AutoTRIZ [PP arXiv 2403.13002, Mar 2024, revised Mar 2025]** (Jiang & Luo).
  - 10 textbook cases, GPT-4 (1106), each run 100 times to measure entropy-based consistency. "7 out of 10 cases match or half-match the textbook's analysis within the top 3 detections." — [AutoTRIZ v2](https://arxiv.org/html/2403.13002v2)
  - There is no plain-LLM baseline. The authors state "there is no objective mechanism to evaluate the effectiveness of generated solutions". — [AutoTRIZ v2](https://arxiv.org/html/2403.13002v2)
- **TRIZ Agents [PR, ICAART 2025; arXiv 2506.18783]** (Szczepanik & Chudziak). LangGraph setup: a project-manager agent plus 7 worker agents. GPT-4o, with TRIZ tools (contradiction matrix, principles, RAG).
  - A single gantry-crane case, compared qualitatively to a published analysis. The agents missed 6 useful connections and 1 harmful one, and shared only one inventive principle with the original. — [TRIZ Agents](https://arxiv.org/html/2506.18783v1)
  - Each run cost 150k to 250k tokens. There was no single-agent or no-TRIZ baseline. The TRIZ specialist under-used the RAG tool. — [TRIZ Agents](https://arxiv.org/html/2506.18783v1)
- **TRIZBench [PR, Findings of ACL 2026]** (Wang & Uzzi; data from U.S. patents). Abstract only:
  - Contradiction detection is easier than recovering the correct trade-off pairs.
  - Principle prediction "benefits from explicitly exploiting TRIZ structure".
  - Semantic retrieval gives evidence-based justifications.
  - The authors note that prior TRIZ-LLM evaluations are small-scale case studies. Code is at github ellenzhuwang/trizbench.
  — [ACL Anthology](https://aclanthology.org/2026.findings-acl.1798/); [search summary](https://preview.aclanthology.org/ingest-acl/2026.findings-acl.1798/)
- **TRIZ-RAGNER [PP arXiv 2602.23656, Feb 2026].** Notes that "directly applying LLMs to TRIZ contradiction mining remains challenging due to hallucination risks and the lack of explicit structured grounding", and adds RAG. — [arXiv 2602.23656](https://arxiv.org/abs/2602.23656)
- **TRIZ enhanced through Environment-Based Design + LLM [PR, AI EDAM 2025]** (abstract only). — [Cambridge PDF](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/C3305E839793A17763076FF8BF510E08/S0890060425000083a.pdf/enhancing-triz-through-environment-based-design-methodology-supported-by-a-large-language-model.pdf)
- **SAPPhIRE + LLM (IISc).**
  - IDEA-INSPIRE 4.0 runs on a *manually* built database of 60 biological and 83 engineered SAPPhIRE models. The authors state that dependence on experts to write SAPPhIRE models restricts scaling.
  - Majumder, Bhattacharya & Chakrabarti built a RAG tool that generates SAPPhIRE constructs for artificial systems, with only a "preliminary evaluation" [PP arXiv 2406.19493, Jun 2024].
  — [arXiv 2406.19493](https://arxiv.org/abs/2406.19493)
  - A DCC/Design Society paper on detecting and splitting SAPPhIRE constructs for automatic analogy structuring. — [Design Society](https://designsociety.org/download-publication/39709/Detection+and+splitting+of+constructs+of+SAPPhIRE+model+to+support+automatic+structuring+of+analogies)
- **FBS inside LLMs.** Ma et al. (JCISE 2025) note in their background that "recent studies have begun integrating established design frameworks, such as the function–behavior–structure framework, into LLMs". This is a mention, not evidence that it helps. — [Ma et al. JCISE](https://codesign.berkeley.edu/pdfs/papers/ma-llmdiverse-jcise.pdf)

### Inferences
- There is no published evidence that TRIZ or BioTRIZ conflict guidance improves the *verified* quality of LLM designs. FLBDS's own null result for T1–T5 (B3 30/60 vs screen-only 34/60) agrees with that empty evidence base rather than contradicting a positive literature. Dropping deterministic operators carries little literature risk.
- If TRIZ is kept, the evidence-backed use is narrow: as a label or classifier (contradiction type → principle). There it measurably helps prediction tasks (TRIZBench). It should not be used as a graph-rewrite engine.
- A SAPPhIRE-style card is useful as a *schema for provenance and display*: it gives fields with verbatim spans. Nothing shows it is needed for transfer quality. A flat card (function, mechanism, physical effect, key quantities, source span) is a defensible simplification.

### Gaps
- No direct A/B was found of "SAPPhIRE/FBS-structured prompt" vs "free-text prompt" on an LLM BID task.
- The quantitative TRIZBench results (per-model accuracy) were not readable from the abstract page.
- No paper evaluating BioTRIZ with LLMs specifically was found.

## Q3. Retrieval approaches: embedding analogy retrieval, function-based search, physical-effect keyed retrieval. Which are simplest and effective? Are knowledge graphs worth it?

### Takeaway
The simplest pattern that works in the literature is plain dense or hybrid RAG over a curated corpus (AskNature, about 2,100 documents) with an off-the-shelf embedder and a local LLM. Knowledge-graph systems exist (Cui et al. AEI; FLBDS's earlier G_MCKG) but are validated only by single case studies. No paper was found that keys retrieval on physical effects with an LLM. Embedding retrieval without any functional abstraction tends toward surface similarity (birds for flying cars).

### Cited Findings
- RAG over 2,106 AskNature documents with a local Llama 3.1. — [MDPI Biomimetics 2025](https://www.mdpi.com/2313-7673/10/9/626)
- BIDARA: RAG increased feasibility in both the prompting and the agent setting. — [AAAI-SS 2024](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210)
- BioSpark gets inspiration "retrieval" from the LLM itself: GPT-4 expands an AskNature seed set across a tree of life. That doubled the number of unique species used vs AskNature + ChatGPT (8.2 vs 4.6). — [BioSpark](https://arxiv.org/html/2503.09838v1)
- Fine-tuned GPT-3 retrieval was dominated by attribute-similar sources (over 50% birds for a flying car) and biased toward historically common AskNature examples. — [Zhu et al.](https://arxiv.org/pdf/2212.13196)
- BARcode mines web-scale bio-inspiration with NLU + weak supervision, because curated datasets are small. — [Emuna et al. AAAI 2024](https://arxiv.org/abs/2312.12681v1)
- KG-based cross-domain RAG (unified bio/eng KG) was validated on one wastewater case. — [PolyU / AEI](https://research.polyu.edu.hk/en/publications/an-llm-based-cross-domain-knowledge-retrieval-augmented-generatio/)
- The AskNature database is organised by the Biomimicry Taxonomy, which is function-based. Function-keyed lookup therefore comes built in. — [Majumder et al.](https://arxiv.org/pdf/2406.19493)
- A search for LLM retrieval keyed on a physical-effects database (e.g. TRIZ effects catalogue) found no paper. — (negative search result; see [search context](https://www.mdpi.com/2313-7673/10/9/626))
- Background survey: "Data-Driven Design-by-Analogy: State of the Art and Future Directions" (Jiang, Hu, Wood, Luo) [PP arXiv 2106.01592 / J. Mech. Des. 2022]. — [arXiv 2106.01592](https://arxiv.org/pdf/2106.01592)

### Inferences
- For FLBDS, a minimal M3 would be: a flat card table with a few hundred to a few thousand cards. Each card holds a function label from the AskNature taxonomy and a physical-effect tag from a small enum aligned to the 10 TPL templates. Retrieval is BM25 + an off-the-shelf embedder (e.g. bge/e5) over "function + mechanism" text, with a hard filter on effect tag or template. This gives effect-keyed retrieval without a graph or a trained three-head encoder.
- The proposal's own pilot (cross-domain 0.764 vs within-domain 0.775 cosine; digest §5.5) plus the literature's surface-similarity finding suggest that embeddings alone will not separate "work-alike" from "look-alike". A symbolic effect-tag filter is the cheap fix, and it is what M3's "shared Effect node" amounts to.
- Knowledge graphs are not justified by any published downstream gain. A graph adds value only as a provenance and navigation layer for the thesaurus goal (G1), not for generation.

### Gaps
- No head-to-head was found of embedding vs function-taxonomy vs effect-keyed retrieval on a common BID benchmark.
- No public gold BID retrieval benchmark with relevance labels was confirmed in this search. BARcode's release may contain one and needs checking.

## Q4. Known failure modes (hallucinated biology, superficial analogies, fixation, citation fabrication) and mitigations

### Takeaway
The documented failures are:
- surface-similarity retrieval
- infeasible engineering numbers
- lower feasibility of LLM-inspired concepts
- low diversity or homogeneity of LLM ideas
- AI-induced fixation (in image-generation studies)
- hallucination, which is cited as the motivation for RAG but rarely quantified in BID

The mitigations with evidence are RAG grounding (feasibility up, unquantified), feeding prior outputs back to force diversity (BioSpark), and external verification. Only the last addresses numeric feasibility.

### Cited Findings
- Superficial analogies: over 50% birds for flying cars. — [Zhu et al. 2023](https://arxiv.org/pdf/2212.13196)
- Infeasible numbers from LLM generation; the authors suggest trained verifiers as the fix. — [Zhu et al. 2023](https://arxiv.org/pdf/2212.13196)
- Feasibility trade-off: BioSpark concepts were more novel but less feasible (5.7 vs 6.8). — [BioSpark](https://arxiv.org/html/2503.09838v1)
- Homogeneity: in Ma et al. [PR, ASME JCISE 25(2) 024501, Feb 2025], GPT-4 generated 4,000 solutions across 5 topics, 8 parameter settings and 8 prompt techniques. Human crowdsourced solutions "consistently have greater diversity scores". Temperature/top-p had no monotonic effect, with T=1, top-p=1 the most diverse. A logistic regression found a semantic divide between human and LLM solutions in some topics. — [Ma et al. JCISE](https://codesign.berkeley.edu/pdfs/papers/ma-llmdiverse-jcise.pdf)
- Fixation: Wadinambiarachchi et al. [PR, CHI 2024], N=60, between-subjects, AI image generator. The AI group showed higher fixation and lower fluency, variety and originality. A later review calls the AI-fixation literature contradictory. — [arXiv 2403.11164](https://arxiv.org/html/2403.11164v1); [UniMelb record](https://findanexpert.unimelb.edu.au/scholarlywork/1886850-the-effects-of-generative-ai-on-design-fixation-and-divergent-thinking); see also [Understanding Design Fixation in Generative AI, arXiv 2502.05870](https://arxiv.org/html/2502.05870v1)
- BioSpark's related-work section lists LLM problems as "inaccurate inferences and hallucinations, user fixation on the initial prompts". Its mitigations are taxonomy grounding and diversification by feeding back the previous 20 outputs. — [BioSpark PDF](https://arxiv.org/pdf/2503.09838)
- Hallucination as the stated motivation for RAG, in BIDARA (2024) and TRIZ-RAGNER (2026). — [BIDARA RAG](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210); [TRIZ-RAGNER](https://arxiv.org/abs/2602.23656)
- Fine-tuned biomimetic LLMs are weak on "functional fidelity". — [EAAI 2026](https://dl.acm.org/doi/abs/10.1016/j.engappai.2026.114818)
- Outside BID, simulation- or verifier-in-the-loop design is the common answer to infeasibility:
  - FEA-feedback VLM agents (an 84.3% "meaningful refinement" figure appeared only in a search snippet; unverified)
  - "Generate-Simulate-Refine" (IJCAI 2026)
  - EngDesign benchmark with simulation-based functional verification (NeurIPS 2025 D&B)
  — [IJCAI 2026](https://www.ijcai.org/proceedings/2026/0714.pdf); [EngDesign NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/file/664f777548205fb6e0cbb0965e8d2e16-Paper-Datasets_and_Benchmarks_Track.pdf); [arXiv 2509.16204](https://arxiv.org/html/2509.16204v2)

### Inferences
- FLBDS's observed failures map onto these published failure modes:
  - unit/scale hallucination (pores in metres)
  - "mechanism never changes under feedback", which is fixation on the first design and the homogeneity seen in Ma et al.
  - identical designs across seeds (M2-S3)
- Mitigations with support, usable in FLBDS:
  - (a) external physics check (already the best component)
  - (b) explicit diversification: show the model its previous K designs and require a different mechanism or template, in the style of BioSpark's precedent feedback
  - (c) retrieval-grounded biology with verbatim spans instead of LLM-recalled biology
  - (d) unit-typed fields with range validation (Pint ranges per field) to stop scale hallucination before the physics check
- Hallucinated biology is mostly unmeasured in BID papers. FLBDS's verbatim-span check is ahead of the literature on this point and is cheap to keep.

### Gaps
- No BID paper was found that quantifies the rate of hallucinated biology or fabricated citations in LLM output.
- The FEA-loop 84.3% figure came from a snippet and was not verified against its paper.

## Q5. Usable datasets and knowledge bases, and their licenses

### Takeaway
AskNature is the de facto corpus: about 2,100 documents, function-taxonomy organised, used by BioSpark, AskNatureGPT, MDPI RAG and Zhu et al. **Its reuse license could not be confirmed** (the terms page returned 403). Treat it as "terms unknown, ask the Biomimicry Institute" before redistributing derived cards. Some tooling has open releases: BARcode data/code (release stated), TRIZBench (GitHub) and NASA PeTaL/BIDARA repos.

### Cited Findings
- AskNature corpus of 2,106 documents used for RAG. — [MDPI 2025](https://www.mdpi.com/2313-7673/10/9/626)
- AskNature is organised by the function-based Biomimicry Taxonomy. — [Majumder et al.](https://arxiv.org/pdf/2406.19493)
- AskNature has been described as "free, open source" only on an old (2011) third-party page, which is not reliable for current terms. The asknature.org terms page was not reachable (HTTP 403). — [third-party page](https://humancoral-team.squarespace.com/res/2011/7/28/biomimicry-institute.html); [asknature.org](https://asknature.org/)
- BARcode authors state that they release data and code. — [arXiv 2312.12681](https://arxiv.org/abs/2312.12681v1)
- TRIZBench data and code are at GitHub ellenzhuwang/trizbench; it is grounded in U.S. patents and open technical sources. — [ACL Anthology](https://aclanthology.org/2026.findings-acl.1798/)
- NASA PeTaL (Periodic Table of Life) and BIDARA have public GitHub presence. — [PeTaL](https://redirect.github.com/nasa-petal); [BIDARA fork](https://www.github.com/Abil27/bidara)
- IDEA-INSPIRE 4.0: 60 biological + 83 engineering SAPPhIRE models, manually built. Availability not stated. — [arXiv 2406.19493](https://arxiv.org/abs/2406.19493)
- AutoTRIZ is CC BY-NC-ND 4.0 on arXiv (paper license, not the tool). — [arXiv v1](https://arxiv.org/html/2403.13002v1)
- A BSI document describes a biomimetics database combining TRIZ with problem- and function-oriented approaches. It is a paid standard. — [BSI](https://knowledge.bsigroup.com/products/biomimetics-integrating-problem-and-function-oriented-approaches-applying-the-triz-method)

### Inferences
- For a small team, the lowest-risk corpus is open-access papers (PMC OA subset with per-article CC licenses, as FLBDS's pilot already uses) plus AskNature used *only as a retrieval index and pointer*, without redistributing its text, until the license is confirmed.
- Matched to FLBDS's TFP scope, BioTRIZ and physical-effects catalogues are small enough to hand-encode as an enum (about 10 effects aligned to TPL-01..10). That avoids any dependency on licensed databases.

### Gaps
- AskNature license and terms of use: unconfirmed.
- BioTRIZ matrix (Vincent et al. 2006) license and availability: not researched within budget.
- Physical-effects databases (e.g. TRIZ effects catalogue, Koller/Roth catalogues, the "Effects" DB): no license info found.
- Compute fit: all surveyed systems used GPT-3/GPT-4/GPT-4o, except MDPI (local Llama 3.1) and BioinspiredLLM (open model). No paper reports BID results with Qwen2.5-72B-class open models. Transfer of the findings to open models is plausible, but no BID paper tests it.
