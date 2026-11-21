# 02. Knowledge graphs and alternatives for heavier biology integration in FLBDS

*Research note, 2026-11-20. Scope: 2018 to Nov 2026, primary sources only. Tags: **[PR]** = peer-reviewed, **[PP]** = preprint or non-archival workshop. Numbers come from the papers. Where a number could not be checked in the primary text, the note says so.*

**Question.** What is the best way to make biological knowledge matter in an LLM-plus-physics-template design system? Options include knowledge graphs, structured retrieval, function/effect ontologies, LLM-built graphs, GraphRAG, multi-agent graph reasoning and embeddings. Each option is judged on **measured design outcomes**, not on how its architecture is described.

**FLBDS facts that constrain the answer** (from `docs/v10/findings_log.md`):
- With Qwen2.5-72B, matched vs mismatched biology card gave +2.8 pts [−4.2, +9.7], Holm p = 0.56.
- OPTONLY − OPT = +1.7 pts (p = 0.44). Once the template is fixed, an optimiser alone does as well as LLM + optimiser.
- The PCM "matched" card actually describes evaporation (elephant mud), not latent storage.

So the only place biology can causally change the outcome is **which physical mechanism/template is chosen**, or possibly where the optimiser starts. Currently, each family admits only one feasible template, so biology has nothing to decide.

---

## Q1. Knowledge graphs and ontologies for bio-inspired design: what was built, what improved, how it was measured

### Takeaway
No published bio-inspired-design knowledge graph has shown a **controlled improvement in design outcomes over the same LLM without the graph**.

- **Buehler-lab graphs** (1,000 papers, about 12k–33k nodes) are evaluated only by graph statistics, case studies and LLM self-scores (novelty 6–8/10 on five ideas). No ablation without the graph, no human rating, no experiments.
- **The strongest outcome evidence comes from small human-subject studies of structured, function-indexed biology representations.**
  - Idea-Inspire 4.0 (SAPPhIRE / multimodal cards): groups of 6 designers.
  - BioSpark (problem–mechanism–organism triplets): N = 12.
  - Both report large gains over plain text or AskNature baselines, but samples are tiny and the authors are among the raters.
- **Function/effect ontologies** (SAPPhIRE, SBF/DANE, Functional Basis/E2B thesaurus, PeTaL taxonomy, BioTRIZ) are valuable as **indexing schemas**. Their outcome evidence is mostly pre-2018 classroom data or none.

### Cited findings

| System | How built | Size | What improved / how measured | Data / licence |
|---|---|---|---|---|
| **Graph reasoning**, Buehler 2024, *Mach. Learn.: Sci. Technol.* 5:035083 **[PR]** ([arXiv 2403.11996](https://arxiv.org/abs/2403.11996)) | LLM triple extraction from 1,000 papers on biological materials; node embeddings; path sampling between distant concepts | Global graph 12,319 nodes / 15,752 edges; giant component 11,878 / 15,396; 109 communities ([HTML v3](https://arxiv.org/html/2403.11996v3)) | Scale-free structure, community analysis, qualitative case studies (e.g. a mycelium composite "inspired by" a Kandinsky painting). **No quantitative novelty/feasibility evaluation and no baseline.** | Code: [lamm-mit/GraphReasoning](https://huggingface.co/lamm-mit/GraphReasoning) |
| **SciAgents**, Ghafarollahi & Buehler, *Adv. Mater.* 2025, DOI 10.1002/adma.202413523 **[PR]** ([arXiv 2409.05556](https://arxiv.org/abs/2409.05556)) | Ontologist / Scientist / Critic agents (AutoGen) walk paths in the graph above, expand hypotheses, check novelty via Semantic Scholar API | Graph 33,159 nodes / 48,753 edges, 92 communities, from about 1,000 papers ([HTML](https://arxiv.org/html/2409.05556v1), §4.1) | **Five** automated ideas self-scored by an LLM agent: novelty/feasibility 8/7, 8/7, 6/8, 7/8, 8/7 (Table 4). Shortest vs random path compared only qualitatively. No run without the graph, no human or experimental validation. Predicted gains such as "20–30 % heat-transfer increase" are model outputs. | Graph `bio-graph-1K` on HF; [README](https://raw.githubusercontent.com/lamm-mit/SciAgentsDiscovery/HEAD/README.md) states no licence; paper CC BY-NC-ND |
| **BioinspiredLLM**, Luu & Buehler, *Adv. Sci.* 2024 **[PR]** ([PMC10933662](https://pmc.ncbi.nlm.nih.gov/articles/PMC10933662/)) | Orca-2-13B fine-tuned on 1,034 papers on biological materials (not a graph) | n/a | 100-question multiple-choice recall exam: 82 % (about 90 % with step-by-step prompting). Beats base models. **RAG scored highest overall** (exact figure not given). Hypothesis generation only qualitative. | Llama-2 licence applies |
| **IDEA-INSPIRE 4.0 / SAPPhIRE**, Siddharth & Chakrabarti, *AI EDAM* 32(4) 2018 **[PR]** ([Cambridge](https://www.cambridge.org/core/product/D71ADA00167259963C38C3C373903112)) | Hand-built SAPPhIRE causal models (state-change, action, part, phenomenon, input, organ, effect) plus multimodal media | Manually curated, about 60 biological and 83 engineered systems (count as cited in [arXiv 2406.19493](https://arxiv.org/pdf/2406.19493)) | Versus a text+image representation. Understanding: 25 students (13/12), analysis scores about 40 % higher, concepts borrowed 4.63 vs 1.38. Design: **12 designers (6/6)**, novelty 4.33 vs 0.5, requirement satisfaction 7.0 vs 4.5. Very small N. | Database not openly released |
| **LLM + RAG for SAPPhIRE models**, Majumder, Bhattacharya, Chakrabarti, ICoRD 2025 **[PR, conference]** ([arXiv 2406.19493](https://arxiv.org/abs/2406.19493)) | RAG pipeline that drafts SAPPhIRE constructs (artificial systems only) | n/a | "Preliminary" factual-accuracy check. No design-outcome test. | n/a |
| **DANE** (SBF models), Goel et al., *Computer-Aided Design* 2012 **[PR, pre-window]** ([DILab](https://dilab.gatech.edu/publications/dane-fostering-creativity-in-and-through-biologically-inspired-design)) | Hand-built Structure–Behaviour–Function models | Tens of systems | Classroom deployment, "initial results indicate usefulness". Companion study: more function matches correlated with better final designs. No controlled effect size found. | Not openly licensed |
| **E2B thesaurus / Functional Basis**, Nagel, Stone, McAdams (IDETC 2010) **[PR, pre-window]**; E2BMO, McInerney et al., *Designs* 2018 **[PR]** ([PDF](https://agarner.expressions.syr.edu/wp-content/uploads/2022/03/McInerney-et-al-2018-Designs.pdf)) | Biology terms mapped to Functional Basis verbs/flows; E2BMO merges it with the BioMimetic Ontology | Hundreds of terms | Inter-translator agreement on "biologically meaningful keywords" ([Autodesk](https://research.autodesk.com/publications/biologically-meaningful-keywords-for-functional-terms-of-the-functional-basis)). No controlled outcome study found for 2018–2026. A 2025 *Biomimetics* review of nine taxonomies, thesauri and ontologies concludes none represents biomimetic knowledge adequately. | Published in papers |
| **BioTRIZ**, Vincent et al., *J. R. Soc. Interface* 3:471 (2006) **[PR, pre-window]** ([PMC1664643](https://pmc.ncbi.nlm.nih.gov/articles/PMC1664643)) | TRIZ contradiction matrix rebuilt from about 500 biological phenomena, with 6 operational fields | 6×6 matrix | Descriptive: only **12 %** similarity between biological and technical inventive principles; biology leans on information/structure, technology on energy. Not an outcome test, but it is the argument for why biology can change *which mechanism* is chosen. | Paper open |
| **PeTaL** (NASA) ontology and labelled corpus, *Designs* 3(3):43 (2019) **[PR]** ([MDPI](https://www.mdpi.com/2411-9660/3/3/43)) | Ontology: function, morphology, environment, state of matter, ecosystem. Labelled papers by Level I–III function. | ">1,400 peer-reviewed labelled articles" ([blog](https://nasa-petal.github.io/blog/posts/engineering-elegance-from-nature)) | No design-outcome evaluation found. Blog admits "low accuracy" from scarce labels (no number). | Code repos: PeTaL-db, PeTaL = Unlicense; bidara-web = GPL-3.0 ([org](https://github.com/nasa-petal)). **Licence and provenance of the labelled dataset: not found.** |
| **BIDARA** (NASA, RAG + ReAct agents), AAAI Spring Symp. 2024 **[PP / non-archival]** ([AAAI-SS](https://ojs.aaai.org/index.php/AAAI-SS/article/view/31210); [NTRS](https://ntrs.nasa.gov/citations/20240001144)) | GPT-based assistant over biomimicry literature | n/a | Abstract: RAG "increases the feasibility" of solutions in both prompting and agent settings. Metrics and N could not be retrieved (page blocked). | Repos listed above |
| **Cross-domain KG-RAG for bio-inspired design**, Cui, Zheng, Ren, Yan, *Adv. Eng. Inform.* 69:104017 (2026) **[PR]** ([PolyU](https://research.polyu.edu.hk/en/publications/an-llm-based-cross-domain-knowledge-retrieval-augmented-generatio/)) | Unified engineering–biology KG, sampling-based cross-domain reasoning, LLM generation with human feedback | Not stated in abstract | One wastewater case study, "enhanced creativity metrics and functional feasibility" vs conventional design. **No numbers in abstract and no LLM-only ablation visible.** | n/a |

### Gaps
- Nobody has ablated graph vs no graph with the same LLM on design outcomes. That includes SciAgents, Graph reasoning and the AEI 2026 KG-RAG paper.
- No extraction-precision audit of LLM-built biology graphs: what fraction of triples are correct and supported by the source.
- The human studies (Idea-Inspire, BioSpark) use N ≤ 12 per condition, author-involved raters and one or two problems.
- No study measures **physical feasibility by simulation**. Feasibility is always a rating. FLBDS's hidden solver would be the first objective endpoint in this literature.

---

## Q2. Alternatives: GraphRAG vs plain RAG, faceted/function search, effect databases, LLM-as-knowledge-base, verbatim-evidence cards

### Takeaway
1. **Faceted structured retrieval has the best measured gains for analogy retrieval relevance.** The useful facets are purpose/function and mechanism, sometimes plus a physical effect. Gains are large: precision@7 doubles, and inspiration quality is 50–60 % better in user studies.
2. **GraphRAG helps mainly on multi-hop or global "sense-making" questions.** Its headline wins shrink a lot once LLM-judge position and length bias are controlled. Plain RAG is equal or better for single-fact lookup, which is what "give me the mechanism for this function" is.
3. **LLM-as-knowledge-base generates more ideas and rates well, but needs verification.** Citation support is incomplete about 50 % of the time even for the best models. LLM-idea advantages collapse after execution.
4. **Physical-effect databases**: no measured LLM-era evaluation found. This is the biggest gap and the most relevant to FLBDS.

### Cited findings

**Faceted / structured retrieval (strongest evidence for relevance)**
- **BARcode** ("Imitation of Life"), Emuna et al., AAAI 2024 **[PR]** ([arXiv 2312.12681](https://arxiv.org/html/2312.12681v1)).
  - Corpus: 780,949 sentences from 27,640 Wikipedia species articles. A Snorkel filter keeps about 23.5k bio-strategy sentences.
  - Retrieval: SBERT, then NLI (DeBERTa), then an SVM ranker trained on 1,005 expert-labelled pairs.
  - Evaluation: 24 AskNature queries, 3 MTurk annotators per item (Fleiss κ 0.42–0.55).
  - **Strategy precision@7 0.718 vs 0.357 (Elasticsearch)**; @15 0.694 vs 0.295.
  - Recovered 4/5 famous biomimicry examples, ranked 8–14.
  - With 3 experts: about 33 % of relevant hits rated highly interesting, and about 21 % were already known to them.
- **Purpose–mechanism facets**, Hope et al., CHI 2022 **[PR]** ([arXiv 2102.09761](https://arxiv.org/abs/2102.09761)). Splitting ideas into purpose and mechanism facet embeddings beat strong baselines by **50–60 %** on search accuracy and inspiration quality in user studies. Per-metric N was not checked in the abstract.
- **BioSpark**, Kang et al., CHI 2025 **[PR]** ([arXiv 2503.09838](https://arxiv.org/html/2503.09838v1)).
  - Data: AskNature posts turned into problem–mechanism–organism triplets, then expanded by GPT-4 along a taxonomy tree. The taxonomy step was verified against 90 Wikipedia taxonomies (94–100 % per level); the generated mechanisms were not separately verified.
  - Study: within-subjects, **N = 12**, 20-min tasks, vs AskNature + ChatGPT.
  - Ideas: 10.3 vs 5.5 (p = .04). Unique species: 8.2 vs 4.6 (p = .007).
  - Quality: overall 6.5 vs 4.5 (LMM p < .0001). Novelty 7.1 vs 3.9, but **feasibility 5.7 vs 6.8 (lower with BioSpark)**.
  - Raters: a domain PhD student plus the first author.
- **Plain RAG over a biomimicry corpus**, Chen & Wang, *Biomimetics* 10(9):626, 2025 **[PR]** ([PMC12467817](https://pmc.ncbi.nlm.nih.gov/articles/PMC12467817/)).
  - Llama-3.1-8B; LLM-only vs RAG-Small (326 docs) vs RAG-Large (2,106 AskNature docs, MiniLM + FAISS top-5).
  - One automotive scenario, 30 student raters, 7-point scale.
  - RAG-Large beat LLM-only in most design-spiral stages (e.g. Discover 5.96 vs 4.64; ANOVA p < .001). But RAG-Small was *worse* than LLM-only on Biologize (4.64 vs 5.42).
  - Single-rater ICC 0.21. Internal inconsistencies in reported ICCs.
  - *Note: it scraped AskNature, which conflicts with AskNature's terms (see Q3).*

**GraphRAG vs RAG (general-domain evidence; no bio-design study found)**
- Edge et al., "From Local to Global" (Microsoft GraphRAG), 2024 **[PP]** ([HTML](https://arxiv.org/html/2404.16130v2)). Two corpora of about 1M and 1.7M tokens, 125 questions each, LLM judge. Win rates vs vector RAG: comprehensiveness 72–83 %, diversity 62–82 %. **Vector RAG was more direct in all comparisons.**
- Han et al., "RAG vs GraphRAG: a systematic evaluation" 2025 **[PP]** ([arXiv 2502.11371](https://arxiv.org/abs/2502.11371)). Same LLM and embeddings for both. RAG is better on single-hop/detail questions, GraphRAG on multi-hop. The two are complementary.
- GraphRAG-Bench, "When to use graphs in RAG", ICLR 2026 **[PR]** ([HTML v3](https://arxiv.org/html/2506.05690v3)). GPT-4o-mini.
  - Complex reasoning: HippoRAG2 53.4 vs RAG 42.9 (novel corpus) and 62.0 vs 58.6 (medical). MS-GraphRAG was *below* RAG on medical (47.0 vs 58.6).
  - Simple fact retrieval: RAG ≥ most graph methods (MS-GraphRAG 38.6 vs RAG 64.7 on medical).
  - Creative generation: graph methods raised faithfulness but **lowered evidence coverage**. Graph methods also cost substantially more tokens.
- "How significant are the real performance gains?" 2025 **[PP]** ([HTML](https://arxiv.org/html/2506.06331v1)). Using unbiased question generation and order-swapped judging, LightRAG vs NaiveRAG fell from a reported **66.7 % win to 39.1 %**. Ordering reversed. LightRAG compared with itself moved >30 points on answer-order swap alone.

**LLM-as-knowledge-base and verification**
- Gao et al., ALCE, EMNLP 2023 **[PR]** ([arXiv 2305.14627](https://arxiv.org/abs/2305.14627)): the best models lack complete citation support **about 50 %** of the time (ELI5).
- Si, Hashimoto, Yang, "Ideation–execution gap", ICLR 2026 **[PR]** ([HTML](https://arxiv.org/html/2506.20803v1)). 43 executors (19 human, 24 AI ideas), 58 reviewers.
  - At ideation, AI ideas were rated higher: novelty 5.78 vs 4.91 (p = .035).
  - After execution, AI ideas dropped by 1.05 (novelty) to 1.98 (overall); human ideas by 0.01 to 0.63. The gap difference is significant (p ≤ .025). Post-execution differences are not significant.
  - *Implication: rated novelty and feasibility of LLM-generated ideas, the metric used by SciAgents and AEI 2026, does not predict outcomes. FLBDS's solver-scored endpoint is the right one.*
- Northen & Wang, "Bioalignment" 2026 **[PP]** ([arXiv 2603.09154](https://arxiv.org/abs/2603.09154)). Across 10 LLMs and 50 prompts, most models systematically undervalue biological vs synthetic solutions. QLoRA on 6,636 PMC articles shifts this (Holm p < .001 Llama-3.2-3B, p < .01 Qwen2.5-3B). Relevant because FLBDS uses Qwen: a card may be discounted by the model's prior.
- MOOSE-Chem, Yang et al., ICLR 2025 **[PR]** ([arXiv 2410.07076](https://arxiv.org/abs/2410.07076)). Splitting ideation into *retrieving inspirations*, then *composing*, then *ranking* rediscovers held-out 2024 chemistry hypotheses (51-paper benchmark, corpus up to 3,000 papers). It supports explicit inspiration retrieval as a separate, scorable step.

**Function-based search and physical-effect databases**
- Classic function→effect "pointers to effects" and dynamic effect databases (TRIZ Future 2015, [Montecchi/Russo group](https://aisberg.unibg.it/bitstream/10446/116289/1/ETRIAjournal2016vol02.split-and-merged.pdf)) **[PR, pre-window]** were evaluated by retrieval examples, not outcomes.
- LLM-era TRIZ work is about contradictions and principles, not effects:
  - AutoTRIZ, 2024 **[PP]** ([arXiv 2403.13002](https://arxiv.org/html/2403.13002v2)).
  - A TRIZ-reasoning benchmark, Findings of ACL 2026 **[PR]** ([ACL Anthology](https://aclanthology.org/2026.findings-acl.1798/)).
- Siddharth & Luo, "RAG using engineering design knowledge" **[PP; v10]** ([arXiv 2307.06985](https://arxiv.org/abs/2307.06985)). Fine-tuned extractors reach up to 99.7 % token-classification accuracy on 375,084 examples. About 2.9M facts from 4,870 fan-system patents. RAG output quality was evaluated only qualitatively.
- Keshwani, Lenau, Ahmed-Kristensen, Chakrabarti, *J. Eng. Des.* 28 (2017) **[PR]** ([RCA](https://researchonline.rca.ac.uk/3743/)). Across four studies, concepts from biology cards ("biocards") had **higher mean novelty** than brainstorming, but **no significant difference in the share of high-novelty concepts**. Concepts sat at higher abstraction. The authors blame participants' limited biology knowledge.

### Gaps
- No study compares GraphRAG with faceted RAG on *analogy retrieval* specifically.
- No LLM-era study evaluates a function→physical-effect database. Yet that mapping is exactly what FLBDS's 10 templates implicitly are.
- No bio-inspired-design study uses a mismatched-biology control or an "engineering paraphrase of the same mechanism" control. Without these, "biology helped" cannot be separated from "a mechanism hint helped".
- Rated feasibility contradicts rated novelty (BioSpark feasibility was *lower*), and ratings do not survive execution.

---

## Q3. Open biological knowledge sources that can legally be used to build a graph or card store

### Takeaway
Use **CC0/CC BY sources plus per-article-licensed OA full text**:
- Wikidata (CC0) and OpenAlex (CC0) for identifiers and metadata.
- GBIF Backbone (CC BY 4.0) for taxonomy.
- The PMC OA **commercial-use-licensed** articles (CC0/BY/BY-SA/BY-ND plus author manuscripts) for verbatim mechanism evidence, retrieved only through the sanctioned bulk channels.

Avoid AskNature-derived material. That includes the existing 2,744-graph store, and probably BioSpark/Chen & Wang style corpora built from AskNature. Treat S2ORC and most iNaturalist/EOL media as non-commercial or per-record. BIOSCAN is legally fine but irrelevant: it holds insect images and DNA, not mechanisms.

### Cited findings

| Source | What it gives FLBDS | Licence / terms (primary page) |
|---|---|---|
| **PMC Open Access subset** | Full-text mechanism evidence (verbatim quotes) | Licence varies per article. Bulk retrieval only via the AWS bucket `pmc-oa-opendata`, OAI-PMH, E-utilities or BioC; "systematic retrieval … through any other automated process is prohibited" ([PMC OA page](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/)). The AWS bucket no longer splits comm/noncomm; filter on the per-article licence field. PMC treats **author manuscripts as available for commercial reuse regardless of licence** ([PMC AWS page](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)). |
| **OpenAlex** | Paper metadata, concepts/topics, DOIs, for building a candidate list | "Our data is CC0" ([openalex.org/about](https://openalex.org/about)) |
| **Wikidata** | Taxon IDs, organism–property statements, cross-IDs (GBIF, EOL, NCBI) | Structured data CC0; other namespaces CC BY-SA ([Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)) |
| **GBIF Backbone Taxonomy** | Canonical taxonomy for organism normalisation | CC BY 4.0 ([GBIF backbone README](https://hosted-datasets.gbif.org/datasets/backbone/README.html); [GBIF forum](https://discourse.gbif.org/t/linking-to-the-gbif-backbone-taxonomy-under-an-incompatible-license/4084)). Occurrence datasets are CC0 / CC BY / CC BY-NC per dataset ([GBIF terms](https://gbif.org/terms)). |
| **iNaturalist open data** | Images (for image-to-card linking), taxa table | Per-photo CC0 / CC BY / CC BY-NC ([repo](https://github.com/inaturalist/inaturalist-open-data)). Licence of the observation/taxa tables not stated there. Filter to CC0/CC BY. |
| **EOL / TraitBank** | Organism traits (body size, habitat, some physiology) | Per-record licences. EOL policy says data records without a licence have no reuse restriction and overview text is CC0 ([EOL licensing policy](https://media.eol.org/info/eol_licensing_policy)). Check the licence column per download. |
| **BIOSCAN-5M** (NeurIPS 2024 D&B **[PR]**) | 5M insect specimens with image, DNA barcode, taxonomy, size | CC BY 3.0 ([repo](https://github.com/bioscan-ml/BIOSCAN-5M)). No mechanism or function content, so low value here. |
| **NASA PeTaL** | Function taxonomy (Level I–III), labelled-paper idea, code | Code: Unlicense (PeTaL, PeTaL-db), GPL-3.0 (bidara-web) ([GitHub org](https://github.com/nasa-petal)). **Labelled dataset licence and provenance not found.** Use the *taxonomy* as a schema; do not ingest the labels until clarified. |
| **S2ORC** | Structured full text of about 8.1M OA papers | Official repo: **CC BY-NC 4.0, non-commercial only** ([allenai/s2orc](https://github.com/allenai/s2orc)). Some mirrors claim ODC-BY; treat that as unverified. |
| **BARcode** corpus/code | 23.5k Wikipedia-derived bio-strategy sentences + ranker | Paper CC BY-NC-ND. Repo licence not stated ([GitHub](https://github.com/emunatool/BARcode-BioInspired-Search)). The underlying Wikipedia text is CC BY-SA. |
| **Buehler `bio-graph-1K`** | 33k-node LLM-extracted biology-materials graph | No licence stated in [README](https://raw.githubusercontent.com/lamm-mit/SciAgentsDiscovery/HEAD/README.md). Derived from 1,000 papers of mixed copyright. Do not redistribute. |
| **AskNature** | Curated strategies | Project's prior finding: terms forbid data mining. The current terms page ([biomimicry.org/terms](https://biomimicry.org/terms/)) could not be retrieved here (HTTP 403); footer says "All Rights Reserved". **Exclude.** |

### Gaps
- The licences of the PeTaL labelled dataset and of the iNaturalist taxa table could not be confirmed.
- No open, licence-clean dataset links **organism → mechanism → physical effect → quantitative parameter range**. FLBDS would have to build it. That is also a publishable contribution.

---

## Q4. Recommendation for FLBDS: the smallest design that makes biology matter, and how to measure it

### Takeaway
**Do not build a large KG or GraphRAG stack now.** The evidence for graphs on design outcomes is null to weak. GraphRAG gains are multi-hop and judge-sensitive. FLBDS's failure was *problem design*, not retrieval.

Build three things instead:
1. **Choice-sensitive problem families**, where several templates are plausible but the environment makes only some feasible.
2. **A small curated mechanism-card store** (about 60–150 cards) with verbatim, licence-clean evidence, indexed by function → physical effect → FLBDS template. That index is the only "graph" needed: a bipartite card–effect–template table.
3. **A pre-registered five-arm causal test** whose primary endpoint is template-choice correctness against an optimiser-computed oracle.

Escalate to a graph only if measured retrieval recall@k on held-out problems needs multi-hop chains (organism → structure → effect → template).

### Cited findings that drive the design
- Faceted function/mechanism indexing is the only consistently measured win for analogy retrieval (BARcode, Hope 2022, BioSpark). Hence cards are indexed by function and physical effect, not by free-text similarity.
- Biology differs from engineering mostly in its *choice of mechanism*: 12 % principle overlap, and biology uses structure/information where technology uses energy (Vincent 2006). Hence biology should act on **template choice**, the step FLBDS currently makes trivial.
- Rated novelty/feasibility does not survive execution (Si et al. 2026), and LLM judges are order-biased (arXiv 2506.06331). Hence the endpoint is the hidden solver, not ratings.
- LLMs discount biological options (Bioalignment 2026), and citations are unsupported about 50 % of the time (ALCE). Hence cards carry verbatim quotes plus DOI, and the test includes a mismatched-card harm check.

### Concrete design

**1. Choice-sensitive families (the critical fix)**
- Pick a *function* with ≥3 admissible templates. Examples:
  - **"Keep a passive enclosure below T_max"**: TPL03 evaporation, TPL09 radiative, TPL02 PCM, TPL07 fin, TPL01 conduction.
  - **"Move/deliver a gas or vapour"**: TPL10 diffusion, TPL06 porous flow, TPL05 wicking.
- Sample environment parameters so the *feasible template set F(i)* varies across instances. Examples: water budget, sky view and humidity, duty cycle and ambient swing, allowed area.
- Compute F(i) offline by running **OPTONLY on every admissible template** for each instance. This is valid because OPTONLY ≈ OPT once the template is fixed (V10: +1.7 pts, p = 0.44). Keep the hidden eval as the judge.
- Acceptance criteria for a choice-sensitive family:
  - 1 ≤ |F(i)| ≤ k−1 for every instance.
  - No single template feasible in more than about 40 % of instances, so a "always pick X" prior fails.
  - A keyword heuristic and a "most-common-template" baseline both score ≤ 50 % on choice.
  - Report these trivial baselines first.
- Env values stay in engineering units in the problem card. **The biology card must not restate hidden constraints.** It supplies a mechanism exemplar plus its operating regime, e.g. "works when the sky is clear and humidity low". The model must map env → regime.

**2. Mechanism-card store (minimal)**
- Card schema:
  - organism (GBIF backbone key + Wikidata QID)
  - function (PeTaL Level-II / Functional-Basis verb)
  - physical effect
  - **target template ID**
  - operating regime as dimensionless groups or ranges
  - typical length scales
  - 1–3 **verbatim quotes** with DOI and article licence (PMC OA commercial-use subset only)
  - curator and date
- Construction:
  - Candidate papers: OpenAlex (CC0) query per function.
  - Text: PMC OA via AWS or OAI-PMH.
  - Draft: the LLM extracts a card.
  - Quote check: the quote must string-match the source.
  - Sign-off: a human (or second-model plus human spot-check) signs off the effect→template mapping.
- Audit and report extraction precision on a 30-card sample. Nobody in the literature reports this.
- Size: 5–15 cards per template is enough. With 10 templates, 60–150 cards.
- Fix the existing PCM card: it is evaporation, not latent storage.
- Retrieval: deterministic match on function, then rank by regime fit (or embedding over the card's mechanism field). Log recall@k against the oracle template.

**3. Measurement: five arms, paired per instance, same seeds**

| Arm | What the LLM sees | What it isolates |
|---|---|---|
| **NONE** | Problem card only | Baseline choice accuracy |
| **MATCH** | + card whose mechanism ∈ F(i) | Total effect of the biology card |
| **MISMATCH** | + plausible card whose template ∉ F(i) (same function, wrong regime) | Harm and blind-following. Whether the LLM checks regime vs env. |
| **ENG-PARAPHRASE** | + the same physical principle and regime written with **no organism** | Does *biology* add anything beyond the mechanism hint? (the key control the literature lacks) |
| **RETRIEVED** | + top-k cards from the store, unlabelled, model chooses | The realistic system. Combines retrieval quality and use. |

- **Primary endpoint**: template-choice correctness, choice ∈ F(i).
- **Secondary endpoints**:
  - End-to-end hidden-eval pass with the OPT downstream (choice → DE optimiser → hidden solver once).
  - Margin.
  - Tokens.
- **Confirmatory contrasts** (Holm): MATCH − NONE, MATCH − MISMATCH, MATCH − ENG-PARAPHRASE.
- **Interpretation**:
  - If MATCH ≈ ENG-PARAPHRASE > NONE, the value is the *mechanism knowledge*, and biology is one source of it. Honest, still publishable.
  - If MATCH > ENG-PARAPHRASE, biology-specific framing helps.
- **Power**: paired binary endpoint, McNemar. With discordance about 30 % and a 15-pt true difference, about **100 instances** gives 80 % power at α = .05 (two-sided). With 3 seeds, analyse at the instance level, sign-flip or cluster bootstrap.
- **Second causal path (optional)**: biology as a parameter prior. Seed OPT from card length scales vs random vs mismatched card. Measure screen calls to first feasible and the final pass rate. This tests whether biology helps where the LLM currently adds nothing.

### Gaps and risks
- If env → feasible-template mapping is easy for the 72B model, NONE will saturate. Tune families so NONE ≈ 40–60 % choice accuracy.
- Screen false assurance (49/144 OPT misses at 72B) caps end-to-end pass rates. Keep template choice as the primary endpoint so biology's effect is not masked by screen fidelity.
- Curated cards written by the same team that designs the problems risk circularity. Freeze cards before generating instances, and have someone not involved assign cards to "matched" status from F(i) alone.
- Image input (the project's "from biological images" framing) is not addressed here. The card store's GBIF/Wikidata keys and CC0/CC BY iNaturalist photos give a licence-clean path to image → card retrieval later.
