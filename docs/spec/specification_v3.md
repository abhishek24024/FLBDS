## M aster Technical Specification: FLBDS v 3.0

T o give FLBDS v3.0 a complete understanding of biology, mechanics, physics, and engineering contraptions, the architecture separates data into two roles: (1) Knowledge Graph & Retrieval Corpora (populating the Neo4j Visual-SAPPhIRE Thesaurus at runtime) and (2) Foundation Model T raining Datasets (training the vision, schematic, and 3D CAD compilers)[cite: 22, 41, 44, 56].

Rather than training a single monolithic model from scratch on raw patents, FLBDS v3.0 combines five specialized database tiers covering biology, physics, engineering contraptions, visual af fordances, and 3D CAD[cite: 9, 22, 41, 44, 56]:

- AskNature & AskNatureNet (Biomimicry Institute / ZJU D3Lab): Serves as the gold-standard seed corpus of curated biological strategies, functional mechanisms, and organism imagery used to ground AskNatureGPT and initialize BioSpark .

- NCBI Taxonomy, IRMNG & Tree-of-Life + Full-Text Biological Literature: Because manually curated biomimetic databases only hold 1 0 to 1 0 entries, BioSpark couples the NCBI and IRMNG taxonomic hierarchies ( :Species -> :Genus -> :Order -> :Class - > :Phylum ) with peer-reviewed biological manuscripts and SEM micrographs to expand outward across sister taxa and convergent evolutionary lineages. 2 3

- IDEA-INSPIRE 4.0 Multimodal Database (IISc Bengaluru): Provides gold-standard multimodal entries (text, images, video, and kinematic simulations) of biological and engineered systems annotated with all 7 SAPPhIRE constructs for few-shot prompting and validation.

- SAPPhIRE Catalog of Physical Laws (Srinivasan & Chakrabarti, 2025/2026): A structured database of governing mathematical equations and physical principles (e.g., Y oung-Laplace capillary law, Biot-Savart electromagnetic law, Navier-Stokes vorticity equations, Hooke's law , van der Waals forces) that populates the canonical :Effect ( 𝑉 𝐸 ) bridge nodes in Neo4j and supplies variable definitions for the Abductive Causal Inversion check and Buckingham Π scaling auditor .

- Mechanistic Engineering Handbooks & Technical Reference Corpora: Used alongside patent specifications in the HyDE-CoT Corrective RAG pipeline (Majumder et

## T he Complete 5-Tier Database Stack for FLBDS v3.0

## T ier 1: Biological & Evolutionary Databases (Understanding Biology)

## T ier 2: Physics, Causality & TRIZ Databases (Understanding Mechanics & Physics)


- al., 2024/2025) to supply high-epistemic-density explanations of physical mechanisms, boosting SAPPhIRE extraction quality to 0.76–0.83.

- WordNet Lexical Ontology: Used by the deterministic spaCy + Propositional Rule extractor (Bhattacharya et al., ASME JCISE 2025) to trace verb and noun hypernym trees ( change.v.01 , move.v.02 , transfer.v.01 , physical_entity.n.01 , energy.n.01 ) without stochastic LLM drift.

- Canonical TRIZ 39 × 39 Matrix & kTRIZ 76 Standard Solutions: Combines the fixed 39 × 39 Contradiction Matrix ( Heinrich-The-Inventing-Machine in AutoTRIZ ) with the kTRIZ statically typed Kotlin specification encoding Altshuller's 39 parameters, 40 inventive principles, 4 physical separation operators, and all 76 Substance-Field (Su-Field) Standard Solutions.

## T ier 3: Patent & Contraption Databases (Understanding Existing E ngineering)

- USPTO & EPO Full-Text Patent Specifications + CPC Hierarchy + Patent Drawings: Ingests full patent descriptions and claims (bypassing vague abstracts) organized under the Cooperative Patent Classification ( 𝑉 𝐶𝑃𝐶 ) hierarchy to cover mechanical, structural, fluidic, thermal, and electromechanical contraptions. OCR and VLM parsers extract numbered reference callouts from patent drawings and link them via ( :FigureROI)-[:DEPICTS_PART]->(:Part) edges to the corresponding :Part and : Organ nodes in Neo4j.

- AGD20K (Affordance Grounding Dataset) & InstructPart Corpus: Trains and benchmarks AffordanceSAM (ACM MM 2026) and InstructPart (ACL 2025) to segment engineering components ( Image_Eng ) by physical interaction and mechanical function (e.g., separating a heat-dissipating fin zone from a load-bearing mounting flange) rather than visual texture.

- ScreenSpot-Pro & 3D CAD Functional Affordance Datasets: Used to benchmark fine-grained recurrent latent visual search ( ReLaViS ) on dense, repetitive micro-features and map operational af fordances onto 3D CAD meshes.

T o compile visual concepts into engineering blueprints and watertight 3D CAD solids, Stage 6 leverages pretrained models backed by six large-scale geometric datasets:

## T ier 4: Visual Affordance & Grounding Datasets (Training Stage 1 D ual-Image Perception)

## T ier 5: 2D Schematic & 3D Parametric CAD Datasets (Training Stage 6 S ynthesis)

| Dataset Name | Scale & Modalities | Role in FLBDS v3.0 (Stage |
| --- | --- | --- |
|   |   | 6) |


| SVG-Stack & | 2,000,000 paired raster | T rains StarVector-8B to |
| --- | --- | --- |
| SVG-Bench | images, text prompts, and | convert raster concepts into |
|   | SVG XML samples across 10 | primitive-preserving SVG |
|   | datasets (including | blueprints ( <rect> , <circle> , |
|   | S VG-Diagrams ). | < line> , <text> ) at a 0.959 |
|   |   | DinoScore. |
| T riGeoBench, | 1,000+ stratified (QA, RGB | Benchmarks and grounds |
| Diagram-MMU & | I mage, LaTeX TikZ) | two-stage VLM-to-TikZ |
| SciDiagBench | geometry triplets and scientific | cross-sectional schematic |
|   | schematic benchmarks. | synthesis and editing. |
| GenCAD-Code (MIT) | 163,000+ paired 3D CAD | Fine-tunes CAD-Coder |
|   | model images and executable | (ASME JMD 2026) to translate |
|   | CadQuery Python scripts . | visual engineering designs |
|   |   | into editable Python CAD |
|   |   | scripts with 100% syntax |
|   |   | validity . |
| Omni-CAD | ~450,000 4-modality instances | T rains CAD-MLLM for |
|   | (text, multi-view images, 3D | multimodal-conditioned CAD |
|   | point clouds, and CAD | synthesis and topological |
|   | command sequences). | Dangling Edge Length |
|   |   | ( DangEL ) evaluation. |


| DeepCAD, ABC | 100,000+ B-Rep CAD models, | T rains Pointer-CAD v1/v2 |
| --- | --- | --- |
| Dataset & Fusion 360 | sketch-and-extrude command | (GNN over B-Rep faces/edges |
| Gallery | histories, and vectorized | + continuous parameter |
|   | multi-view orthographic | regression) and |
|   | drawings. | Drawing2CAD (orthographic |
|   |   | SVG to 3D CAD). |
| Bioinspired123D & | 49,586 image-text-CAD triplets | Bridges organic bio-inspired |
| UniCAD | (UniCAD) + programmatic | internal lattices (TPMS, |
|   | bio-inspired structural/material | V oronoi stereom) with |
|   | code corpus | parametric 3D mechanical |
|   | (Bioinspired123D). | CAD scripts. |

## 3 . Practical Implementation Strategy: What You Actually N eed to Build vs. Reuse

Y ou do not need to train the vision, diffusion, SVG, or 3D CAD foundation models from scratch, as their open-source weights are already trained on AGD20K, SVG-Stack, GenCAD-Code, Omni-CAD, and DeepCAD .

Instead, your data engineering ef fort for FLBDS v3.0 focuses entirely on populating the Neo4j Multimodal Causal Property Graph ( 𝐺 𝑀𝐶𝐾𝐺 ) using four connected data streams[cite: 44, 56]:

- 1. Biological Stream: Seed with AskNature (~1,700 strategies) and IDEA-INSPIRE 4.0 , then use BioSpark 's Tree-of-Life expansion over NCBI Taxonomy + PubMed Central Open-Access biological papers (with SEM micrographs) to scale to tens of thousands of species.

2.

- 3. Engineering Contraption Stream: Ingest a targeted subset of USPTO PatentsView full-text specifications + patent drawings filtered by mechanical, structural, fluidic, and thermal CPC classes (e.g., CPC F16 Mechanical Engineering Elements, F28 Heat Exchange, B64 Aircraft, E04 Building) alongside open-access mechanical engineering handbooks.

4.

- 5. Physics & TRIZ Spine: Load the Srinivasan & Chakrabarti Physical Laws Catalog as canonical :Effect nodes in Neo4j, paired with the deterministic AutoTRIZ 39 × 39 Matrix and kTRIZ Kotlin DSL .

6.

- 7. Automated Extraction: Run the HyDE-CoT Corrective RAG + spaCy/WordNet 5-Category Rule Engine over the biological and patent streams to automatically


populate the 7 SAPPhIRE nodes and link the segmented micrograph/patent drawing ROIs.

8.

W ould you like me to add this Section 7: Training & Knowledge Graph Data Architecture directly into your Google Doc specification, or design the exact data-ingestion pipeline script for building the Neo4j graph from AskNature and USPT O PatentsView?

## A Mul timodal Visual-SAPPhIRE Neuro-Symbolic Compiler for Bio-Inspir ed Engineering Design

## 1 . Executive Summary & Core Project Objectives

Designers seek t o break away from traditional engineering fixation by leveraging biological analogies, y et they face two fundamental barriers: (1) an ontological and lexical chasm bet ween biological literature and patent disclosures, and (2) the inability of text-only syst ems to capture continuous multiscale spatial, geometric, and topological mechanisms. Con versely, unconstrained text-to-image diffusion models produce aesthetically

biomimetic r enders that violate mechanical assembly interfaces, break dimensional scaling laws, and output non-manif old surfaces unusable in CAD or FEA.

T o resolve this, the Functional and Logical Biomimetic Design System (FLBDS v3.0) est ablishes an end-to-end visual and neuro-symbolic engineering compiler built to satisfy t wo core project aims:

- Aim 1 (The Visual Biology-to-Engineering Thesaurus): A Multimodal Causal Pr operty Graph (G_MCKG) in Neo4j + HNSW vector indices that indexes biological micr ographs/imagery alongside engineering patent cross-sections/drawings, unified via the 7-construct SAPPhIRE Model of Causality (State change, Action, Par t, Phenomenon, Input, oRgan, Effect).

- Aim 2 (Dual-Image Analogical Engineering Synthesis): A 6-stage computational pipeline that ingest s both a biological source image ( Image_Bio ) and an existing engineer ing baseline image ( Image_Eng ), extracts modifiable engineering Parts ( M_Eng) and dimensionless biological oRgan topologies (T_Bio), aligns their causal ph ysics via DeepGAR subgraph isomorphism, resolves Buckingham Pi scaling violations via compiler -verified kTRIZ / AutoTRIZ , and synthesizes structure-locked visual r enders ( FLUX.1-Fill-dev + ControlNet++ / Ctrl-U ), vector schematics ( StarVector-8B / SVGThinker / TikZ ), and watertight 3D CAD solids ( CAD-Coder / P ointer-CAD v2 ).


## 2 . Architectural Evolution: Key Upgrades from FLBDS v1.0 to v3.0

|   |   | F LBDS v3.0 SOTA Component | Q uantitative & Architectural |
| --- | --- | --- | --- |
| S ubsystem Layer | L egacy FLBDS v1.0 Component | ( 2024–2026) | J ustification |
| Causal Ont ology Bridge | 3 -Node FBS | 7 -Node SAPPhIRE Model of | Split s Structure into Part (P) |
|   | ( Function-Behavior-Structure) | Causalit y + Abductive Variable | and oRgan (R), solving the |
|   |   | V erification | Ov er-Decoupling Paradox by |
|   |   |   | str ipping biological tissue (P) |
|   |   |   | while pr eserving dimensionless |
|   |   |   | geometr y (R). Splits Behavior |
|   |   |   | int o Input (I), Effect (E), |
|   |   |   | Phenomenon (Ph), and State |
|   |   |   | change (S). |
| Kno wledge Extraction | Zer o-shot LLM + Basic SVO | H yDE-CoT Corrective RAG + | Ungr ounded zero-shot LLMs |
|   | Pat ent Parsing | sp aCy/WordNet 5-Category | suf fer a 63.33% error rate |
|   |   | Pr opositional Rule Engine | ( 36.67% accuracy). HyDE-CoT |
|   |   |   | RA G achieves 0.76–0.83 RAG |
|   |   |   | qualit y score, while |
|   |   |   | det erministic dependency rules |
|   |   |   | eliminat e T=0 stochastic drift. |
| Visual P erception | Qw en3-VL + SnapPhysics + | Qw en2.5-VL / Qwen3-VL + | R eplaces robotic grasping |
| ( Dual-Image) | AFUN + T ARAD | A CS-Free + ReLaViS + | v oxel policies (TARAD) with |
|   |   | A ffordanceSAM / InstructPart | nativ e-resolution dual-image |
|   |   | + Gr ounded-SAM 2 | p arsing. ACS-Free boosts |
|   |   |   | micr o-feature ( oRgan ) |
|   |   |   | loc alization by +19%, and |
|   |   |   | R eLaViS adds +3.1 pp |
|   |   |   | gr ounding accuracy with only |
|   |   |   | + 3.5% FLOPs. |
| Analogic al Reasoning (SMT) | Heur istic SMT + CreativeFlow | DeepG AR (Continuous DAG | Enf orces all 3 Gentner SMT |
|   |   | Or der-Embeddings) | axioms (One-to-One, Parallel |
|   |   |   | Connectivit y, Systematicity) in |
|   |   |   | continuous or der-embedding |
|   |   |   | sp ace, achieving an 88.4% |
|   |   |   | F1-scor e (+15% average |
|   |   |   | impr ovement over SME, AMN, |
|   |   |   | and Neur oMatch). |
| Contr adiction & Scaling Solver | St andalone AutoTRIZ + Generic | Buckingham Pi Similitude | Aut omatically detects Reynolds |
|   | TRISM Agent | Audit or + AutoTRIZ + TRIZ | ( Re), Biot (Bi), Bond (Bo), and |


|   |   | F LBDS v3.0 SOTA Component | Q uantitative & Architectural |
| --- | --- | --- | --- |
| S ubsystem Layer | L egacy FLBDS v1.0 Component | ( 2024–2026) | J ustification |
|   |   | A gents + kTRIZ (Kotlin | Elast o-Gravity (Pi_g) scaling |
|   |   | Compiler Or acle) | violations when sc aling L_B to |
|   |   |   | L_ T, triggering Separation |
|   |   |   | Pr inciples and 39x39 matrix |
|   |   |   | lookups v erified by the kTRIZ |
|   |   |   | compiler (<1s execution, zero |
|   |   |   | hallucinat ed parameters). |
| Visual & C AD Back-End | La youtGPT + SceneComposer | FLUX. 1-Fill-dev + | Eliminat es unmasked |
|   |   | Contr olNet++ / Ctrl-U + | engineer ing datum drift via |
|   |   | St arVector-8B / SVGThinker + | mask ed rectified flow |
|   |   | C AD-Coder / Pointer-CAD v2 | ( CFG=30.0) and pixel-level |
|   |   |   | c ycle consistency (+13.4% |
|   |   |   | edge SSIM, +6.53% Ctrl-U |
|   |   |   | gain). Compiles output s into |
|   |   |   | SV G/TikZ (0.959 DinoScore) |
|   |   |   | and wat ertight B-Rep CAD |
|   |   |   | ( -56.9% infeasible CAD rate). |

## 3 . Pillar 1: The Multimodal Visual-SAPPhIRE Thesaurus (Addressing A im 1)

## 3 .1 Formalizing the Seven SAPPhIRE Constructs

Ev ery biological strategy and engineered patent system X is modeled as a directed causal graph o ver seven construct sets (P, R, I, E, Ph, S, A) governed by three relational operat ors—creation, activation, and interpretation:

- Causal Chain Equation: P --[creates]--> R, (I AND R) --[activates]--> E --[ creates]--> Ph --[creates]--> S --[interpreted_as]--> A

- Feedback & Multi-State Relay: A State change S_k either modifies structural component s (S_k --[modifies]--> P_k) or crosses a subsystem boundary to trigger a do wnstream subsystem (S_k = I_{k+1}).

|   |   |   | R ole in Dual-Image Biomimetic |
| --- | --- | --- | --- |
| C onstruct | S ymbol | F BS Alignment | T ransfer |
| A ction | A | F unction (Teleological) | High-le vel verb-noun goal (e.g., |
|   |   |   | "Dissip ate thermal load", |


|   |   |   | R ole in Dual-Image Biomimetic |
| --- | --- | --- | --- |
| C onstruct | S ymbol | F BS Alignment | T ransfer |
|   |   |   | " Adhere reversibly"). Shared |
|   |   |   | br idge node across domains. |
| St ate change | S | F unction / Behavior | Quantifiable transition in |
|   |   |   | ph ysical state variable between |
|   |   |   | t_ 0 and t_1 (e.g., Temperature |
|   |   |   | dr op ΔT, drag reduction ΔC_d). |
| Phenomenon | Ph | Beha vior (Interaction) | Ph ysical interaction |
|   |   |   | transf orming material, energy, |
|   |   |   | or signal ( e.g., Capillary wicking |
|   |   |   | + e vaporative phase change). |
| Ef fect | E | Beha vior (Governing Law) | Mathematic al equation or |
|   |   |   | ph ysical law activated when I |
|   |   |   | and R coe xist (e.g., |
|   |   |   | Y oung-Laplace law, Biot-Savart |
|   |   |   | law , Navier-Stokes vorticity |
|   |   |   | damping). Shar ed canonical |
|   |   |   | br idge node. |
| oR gan | R | Structur e (Geometric Context) | PRESER VED INVARIANT: |
|   |   |   | Dimensionless geometr ic, |
|   |   |   | t opological, and material |
|   |   |   | boundar y conditions created by |
|   |   |   | Par ts required to activate E |
|   |   |   | ( e.g., Voronoi channel porosity, |
|   |   |   | r iblet spacing s⁺, contact angle |
|   |   |   | θ). Visuall y extracted as tensor |
|   |   |   | field T _Bio. |
| Input | I | F unction (Boundary Flow) | Mat erial, energy, or signal |
|   |   |   | cr ossing the system boundary |
|   |   |   | ( e.g., Incident solar heat flux |
|   |   |   | q'' , axial preload force). |
| P art | P | Structur e (Physical Entity) | MODIFIED / REPLA CED |
|   |   |   | SUBS TRATE: Physical |
|   |   |   | component s and assemblies |
|   |   |   | ( e.g., biological keratin/chitin |
|   |   |   | vs. engineer ing aluminum fin |


|   |   | R ole in Dual-Image Biomimetic T ransfer |
| --- | --- | --- |
| C onstruct | S ymbol | F BS Alignment |
|   |   | ar ray). Visually segmented as binar y mask M_Part. |

## 3 .2 Hybrid Neuro-Symbolic SAPPhIRE Ingestion Pipeline

Empir ical research (Majumder et al., 2024; Bhattacharya et al., JCISE 2025) demonstrates that ungr ounded LLMs fail at SAPPhIRE extraction (36.67% accuracy) and struggle specific ally with oRgan (R) and Part (P) groundedness (0.50–0.80 vs. 0.80–1.00 for other nodes) bec ause oRgans are written implicitly as relational modifiers and the word "organ" in biology r efers to anatomical viscera. FLBDS v3.0 solves this by running a dual-pathway e xtractor:

## 1 . Pathway A — HyDE + CoT Corrective RAG (Majumder et al., arXiv:2406.19493 & 2 407.00396):

- Stage 1 (Hypothetical Construct Synthesis): Given system X and the SAPPhIRE ont ology definitions O_SAPPhIRE, zero/few-shot CoT prompting generat es ungrounded hypothetical constructs h_i = f_LLM(τ(X; O _SAPPhIRE))_i for i {1..7}.

- Stage 2 (Polysemy-Bypassing Dense Retrieval): Each hypothetical construct h_ i (containing concrete domain nouns/verbs rather than abstract ontology t ags) is concatenated with construct query q_i and embedded via encoder ϕ int o dense vector space to retrieve top-k high-epistemic-density chunks r_i fr om full-text patents or biological manuscripts: r_ i = arg top-k_{c D} [ ⟨ϕ(q_i ⊕ h_i), ϕ(c)⟩ / (||ϕ(q_i ⊕ h_i)||_2 · ||ϕ(c)||_2) ]

- Stage 3 (Fact-Grounded Corrective Generation): A corrective prompt t emplate ρ(X, q_i, h_i, r_i) revises h_i strictly against retrieved evidence r_i such that the RA G Groundedness score G(y_i | r_i) ≥ τ_g (achieving 0 .76–0.83 overall quality).

- 2 . Pathway B — Deterministic spaCy + WordNet + Propositional Rule Engine ( Bhattacharya et al., AI EDAM 2024; ASME JCISE 2025):

- Part A (Whole-Document Semantic Graph): Resolves coreferences across the entir e patent or biological paper.

- Part B (Two-Step Propositional Mapping): Extracts 5 intermediate c ategories from dependency trees T_dep = (V_w, E_dep) using WordNet h ypernyms before mapping to SAPPhIRE:

- i . Ph ysical Interactions (transitive verbs descending from change.v.01 , move.v.02 , transfer.v.01 ) → Mapped to Phenomenon (Ph) / Action (A) .


- i i. Ph ysical Entities ( nsubj , dobj , pobj descending from physical_entity.n.01 or energy.n.01 ) → Mapped to Part (P) (if int ernal/interface) or Input (I) (if crossing boundary).

- i ii. St ate Change due to Interactions (deverbal nouns, resultative adjectiv al complements acomp / oprd , passive clauses after "resulting in"/" causing") → Mapped to State change (S) .

- i v. Condition f or Physical Interactions (prepositional/clausal modifiers prep_due_to , advcl with "when"/"provided that"/"by virtue of", and pr operty attributes amod of interacting parts) → Mapped to oR gan (R) .

- v . Ph ysical Law (proper nouns collocated with "law", "principle", " effect", "equation") → Mapped to Effect (E) .

- 3 . Abductive Causal Inversion Guardrail & UNO-BID / SHACL Validation:

- Every extracted tuple must pass the formal abductive variable check: F or all e E, ph Ph: Activates(I, R → e) if and only if Variables(e) A ttributes(I) Attributes(R).

- Example: If Effect e = Young-Laplace Capillary Equation (ΔP = 2γ cos(θ) / r), the v erifier confirms that oRgan R explicitly defines contact angle θ and por e radius r, and Input I / Part P specifies surface tension γ. Missing v ariables trigger targeted GraphRAG follow-up queries. All outputs are v alidated against the UNO-BID OWL/SHACL schema.

## 3 .3 Neo4j Multimodal Causal Property Graph (G_MCKG) & Hybrid GraphRAG

- Graph Schema: G_MCKG = (V, E, A, I_vec), where vertex set V = V_Doc^Bio V _Taxon V_Doc^Pat V_CPC V_Fig V_{P,R,I,E,Ph,S,A}.

- Taxonomic Expansion (BioSpark Tree-of-Life): Encodes (:Species)-[:BELONGS_TO_GENUS]->(:Genus)-[:BELONGS_TO_ORDER] ->(:Order) , e xpanding AskNature gold-standard seeds across sister taxa and con vergent evolutionary lineages, grouped into Leiden modularity communities C _m ("Mechanism Active Ingredient" clusters).

- Patent Classification & Callout Linking: Encodes CPC hierarchies ( V_CPC ) and links OCR-e xtracted patent drawing reference numerals via (:FigureROI)-[:DEPICTS_PART]->(:Part) and biological micrograph masks via (:FigureROI)-[:ILLUSTRATES_ORGAN]->(:Organ) .

- Shared Cross-Domain Bridge Nodes: Biological and engineering subgraphs int ersect directly at canonical :Effect nodes (Srinivasan & Chakrabarti Ph ysical Laws Catalog) and normalized :Action / :StateChange nodes.

- Hybrid Cypher-Vector Retrieval Objective:

Giv en query Q_prob = (A_q, S_q, I_q, z_sketch):

- a . Dual-Modality Anchor Seeding: S_ vec(v, Q_prob) = α_txt · cos_sim(e_txt(v), e_txt(A_q ⊕ S_q)) + (1 - α_txt) · cos_sim(z_ vis(v), z_sketch)


- b . Backward Causal Path Traversal: Parameterized Cypher expands from :Action back to :Part and laterally across :Effect bridges.

- c . Community & Phylogenetic Ranking: J _GraphRAG(g_b | Q_prob) = ω_1 ∑_{v g_b} S_vec(v, Q_prob) + ω_2 ∏_{(u,v) E(g_b)} È_causal(u, v) + É_3 Sim(e(C_m), e(Q_prob)) + É_4 D _phylo(g_b) wher e D_phylo(g_b) rewards Lowest Common Ancestor (LCA) height h_LCA

- acr oss the Tree-of-Life to surface evolutionarily convergent mechanisms.

## 4 . Pillar 2: The 6-Stage End-to-End Computational Pipeline ( Addressing Aim 2)

## S tage 1: Dual-Image Functional & Topological Parsing ( Image_Bio + Image_Eng )

T ext-only systems suffer low recall on the SAPPhIRE oRgan construct because continuous

mul tiscale geometry is difficult to capture in prose. FLBDS v3.0 parses both images in p arallel using native-resolution VLMs and affordance segmentation:

- 1 . Native Dynamic Resolution Backbone (Qwen2.5-VL / Qwen3-VL): Maps arbitrary H × W images int o dynamic visual token sequences without downsampling dist ortion, emitting absolute pixel coordinates, point clicks ĉ = (x, y), and JSON bounding bo xes.

- 2 . Micro-Feature oRgan Grounding on Image_Bio (ACS-Free + ReLaViS + Precise Doc ):

- ACS-Free / ACS-Learned (2026): Probes localization-critical cr oss-attention heads via attention-entropy selection to filter candidate bo xes for micro-scale biological oRgans (pores, riblets, venation, Voronoi strut s), achieving up to +19% self-improvement on small-object localization without det ector retraining.

- ReLaViS (Recurrent Latent Visual Search, 2026): Formulates dense, r epetitive biological lattice/manifold localization as a multi-step recurrent lat ent trajectory (I, q) → S_1 → ... → S_T → ĉ within a single forward pass ( +3.1 pp accuracy on ScreenSpot-Pro at only +3.5% FLOPs).

- Hungarian Bipartite IoU Filtering (Precise Doc, 2026): Enforces one-to-one assignment (R = 0.8 · R_acc + 0.2 · R_IoU) to prevent redundant overlapping bo xes over periodic arrays.

- Output from Image_Bio : Grounded-SAM 2 isolates the specimen and e xtracts the normalized Topological oRgan Tensor Field ( T_Bio ) , compr ising Canny/HED edge skeletons, local surface normal/curvature gradient s, and dimensionless geometric ratios (porosity ϕ, hydraulic diamet er ratio, branching angle).

- 3 . Functional Part Mask Extraction on Image_Eng (AffordanceSAM + InstructPart + Gr ounded-SAM 2):


- Because standard semantic segmentation partitions by texture rather than mechanic al function (e.g., failing to separate a cantilevered load path, fluid impinging fin ar ray, and bolted mounting flange on a monolithic cast housing), AffordanceSAM (ACM MM 2026) and InstructPart (ACL 2025) segment Image_Eng based on task-conditioned SAPPhIRE Actions and Phenomena .

- Grounded-SAM 2 converts these functional regions into a watertight binary Modif iable Functional Part Mask ( M_Eng ∈ {0,1}^{H × W}) and a strictly lock ed Mechanical Keep-Out Mask ( 1 - M_Eng ) protecting bolt circles, mounting flanges, and datum int erfaces.

## S tage 2: Multimodal Thesaurus Retrieval & Problem/Solution SAPPhIRE Ins tantiation

- Using the visual embedding z_vis( T_Bio ) and functional tags from Image_Eng , the syst em queries G_MCKG via the Hybrid GraphRAG objective J_GraphRAG to inst antiate the full 7-node Biological Base DAG G_B = (V_B, E_B) and the b aseline Engineering Target DAG G_T = (V_T, E_T) .

- Integrates AskNatureGPT dual evaluators (feasibility, novelty, analogical fidelity) and BioSpark "Spark" / "Trade-off" failure analysis modules to surface secondary cont amination or operational hazards early.

## S tage 3: DeepGAR Subgraph Alignment (Structure Mapping Theory)

T o align G_B and G_T without combinatorial explosion while enforcing all three Gentner SMT axioms (One-to-One Correspondence, Parallel Connectivity, and Tiered Identicality / Syst ematicity), FLBDS v3.0 deploys DeepGAR (Ling et al., IEEE ICDM) :

- 1 . Continuous Order-Embedding Screening: A K-layer message-passing GNN maps e ach SAPPhIRE DAG node u and its K-hop causal descendants into ℝ₊ᵈ under the p artial order constraint h_u ≤ h_v iff G_u is a causal subgraph of G_v, minimizing asymmetr ic penalty D(h_u, h_v) = ||max{0, h_u - h_v}||_2^2. This filters candidate graphs in O( d) time.

- 2 . Constrained Node Correspondence Optimization: Solves for the doubly sub-st ochastic alignment matrix X [0,1]^{|V_B| × |V_T|} (where X 1 = 1 and Xᵀ 1 ≤ 1 ): min_X ||X A_T Xᵀ - A_B|| F^2 + λ_1 ||max{0, h {v_B} - X H_T}||_2^2 - λ_2 ||X d_ T||_2^2 - λ_3 Tr(X S_tierᵀ)

- Term 1 enforces Parallel Connectivity & Subgraph Isomorphism .

- Term 2 enforces Order-Embedding Subgraph Alignment .

- Term 3 (-λ_2 ||X d_T||_2^2) enforces SMT Systematicity (preferring deep c ausal chains over isolated surface attributes).

- Term 4 (-λ_3 Tr(X S_tierᵀ)) enforces Tiered Identicality over SAPPhIRE construct s, locking identical Effects (E_B ↔ E_T) and Phenomena (Ph_B


- ↔ Ph_ T) while projecting the biological oRgan (R_B) onto the target engineer ing Part (P_T) and oRgan (R_T).

- Benchmark Advantage: Achieves 88.4% F1-score (+15% average impr ovement over Rule SME [68.2%], AMN [74.5%], and NeuroMatch [ 76.8%]).

## S tage 4: Buckingham Pi Dimensional Similitude & Thermodynamic Verification

Dir ect geometric scaling of a biological mechanism from organism length scale L_B to engineer ing artifact length scale L_T (scaling factor λ_L = L_T / L_B) frequently crosses cr itical physical regime boundaries, deactivating Effect E_B:

- 1 . Buckingham Pi Nullspace Audit: For governing physical Effect E_B over n variables { q_1, ..., q_n} and k fundamental dimensions (M, L, T, Θ, I) with dimensional matrix D ^{k × n}, the verifier computes the p = n - k dimensionless groups  _m = ∏_{ j=1}^n q_j^{α_{mj}} where D · α_m = 0.

- 2 . Regime Violation Metric:

- V _scale(E_B, R_B → R_T) = ∑_{m=1}^{n-k} w_m · 𝕀(Π_m^{(T)} [Π_{m,min}^{crit}, Π_{m,max}^{cr it}]) · |log₁₀(Π_m^{(T)} / Π_m^{(B)})|

- Fluidic Regime (Reynolds Number Re = ρvL / μ ~ L¹): Checks laminar -to-turbulent transition (Re_crit ~ 2.3 × 10³) and viscous wall units (s⁺).

- Thermal Regime (Biot Number Bi = h L_c / k_s ~ L_c¹): Scaling biological skin (Bi_B < 0.1) to a monolithic 1m facade panel drives Bi_T >> 1, causing cor e thermal trapping unless characteristic length L_c = V / A_s is decoupled fr om macro length L_T.

- Capillary & Adhesion Regime (Bond Number Bo = Δρ g L² / γ ~ L²): Ensures sur face tension / van der Waals forces remain dominant over gravity (Bo_T < 1 ).

- Structural Shell Regime (Elasto-Gravity Number Π_g = ρ g L / E_mod ~ L¹): Audit s self-weight bending stress and buckling slenderness (L / t).

- 3 . Thermodynamic Second-Law & Ideality Check: Audits Gouy-Stodola exergy destruction rat e Ė_d = T_0 σ̇_gen ≥ 0 and evaluates TRIZ Ideality = ∑(ActionUtility) / [∑ (ExergyCost) + ∑(HarmfulStateChange)].

## S tage 5: Compiler-Verified Contradiction Resolution (AutoTRIZ + TRIZ Agents + k TRIZ)

Whene ver V_scale > 0 or transferring R_B into P_T triggers a mechanical trade-off, the conflict is r outed into a hybrid neuro-symbolic TRIZ solver:

- 1 . Physical Contradiction & Separation Operators (TRIZ Agents, arXiv:2506.18783): When a single geometr ic parameter θ_{P,i} must be simultaneously macro-scale to satisfy engineer ing Action A_T and micro-scale to keep Π_m^{(T)} within [ Π_min^{crit}, Π_max^{crit}]:


C _phys(θ_{P,i}): (θ_{P,i} ≥ θ_macro) AND (θ_{P,i} ≤ θ_micro)

The engine applies Separation in Scale (S_scale) and Separation in Space ( S_space) via a topological subdivision operator T_{TPMS/Voronoi}(P_T; N_cell, ϕ_por osity) (e.g., Functionally Graded Heterogeneous Triply Periodic Minimal Sur face [TPMS] scaffolds or hexagonal Voronoi stereom lattices). This decouples macr o bounding length L_T from local characteristic length L_c = V / A_s ~ N_cell^ {-1/3} L_T, restoring Bi_T < 0.1 and Bo_T < 1 while holding L_T fixed.

- 2 . Technical Contradiction Lookup (AutoTRIZ, arXiv:2403.13002v4): Maps impr oving feature f_imp and worsening feature V_scale to Altshuller's 39 p arameters (p_imp, p_wor) and executes a deterministic, non-LLM lookup over the c anonical 39x39 matrix: P_inv = M_{39x39}[p_imp, p_wor] {1..40}, injecting only the v erified 3–4 Inventive Principles as graph-rewrite operators R_{p_k}(G_T).

- 3 . Deterministic Symbolic Compiler Oracle (kTRIZ, Kotlin DSL + MCP Server, 2026): T o eliminate LLM parameter hallucination and prose ambiguity, all TRIZ formulations ( 39 parameters, 40 principles, physical separation polarities, and all 76 Standard Su -Field Solutions) are emitted as statically typed kTRIZ Kotlin code and checked b y the embedded Kotlin compiler (<1s runtime). Any invented parameter or invalid Su -Field triad fails compilation and forces immediate self-correction.

- 4 . Unified Master Optimization Objective: min_ {X, p_k, θ_P} L_DeepGAR(X; G_B, R_{p_k}(G_T)) + μ_1 ∑_{m=1}^{n-k} w_m |log₁₀(Π_m^ {(T)}(θ_P) / Π_m^{(B)})|² - μ_2 Ideality(P_T(θ_P), R_T(θ_P)) subject t o: Π_{m,min}^{crit} ≤ Π_m^{(T)}(θ_P) ≤ Π_{m,max}^{crit}, σ̇_gen(θ_P) ≥ 0, and T ypeCheck_kTRIZ(p_imp, p_wor, p_k) = True.

## S tage 6: Dual-Track Structure-Conditioned Visual, Schematic & 3D CAD S ynthesis

Inst ead of full-frame instruction editing (which corrupts unmasked bolt circles and datum edges) or r oom-layout bounding boxes (LayoutGPT), FLBDS v3.0 deploys a 3-track f abrication-aware generative back-end:

- 1 . Track 6A — Mask-Conditioned Rectified Flow & Pixel-Cycle-Consistent Image Synt hesis ( Image_Out ):

- Macro Boundary Lock (FLUX.1-Fill-dev): Ingests Image_Eng and the binary modifiable Par t mask M_Eng at high guidance (CFG ~ 30.0, denoising str ength 1.0 inside M_Eng ), mathematically guaranteeing zero pixel drift in the unmask ed keep-out zone 1 - M_Eng (preserving mounting flanges, bolt holes, and or thographic projection alignment).

- Decoupled Biological oRgan Injection (FLUX-Redux + ControlNet++ / Ctr l-U + SmartControl):

- Material/Porosity Distribution: Cropped biological microstructure p atches are encoded via FLUX-Redux / DEADiff to condition local structural distr ibution without transferring organic colors or b ackground clutter.


- Topological Edge & Depth Fidelity: The scaled biological oRgan t ensor field T_Bio (adjusted by Stage 5 TPMS/Voronoi parameters θ_P *) guides ControlNet++ (ECCV 2024) , which enforces single-st ep pixel-space cycle consistency L_total = L_train + λ · L( c_v, D(x_0')) ( +13.4% Line-Art Edge SSIM , +11.1% Mask mIoU , + 7.6% Depth RMSE reduction ).

- Uncertainty Calibration & Boundary Blending: Ctrl-U (ICLR 2025) do wn-weights high-variance reward gradients on novel bio-micr ostructures ( +6.53% consistency gain over ControlNet++ ), while SmartControl (2024) adaptively relaxes rough edge conflicts at the int erface between organic curved branching and rectilinear mechanic al walls.

- Preference Alignment: Optimized via Poly-DPO / VIPO (2026) (+6.87 GenEv al over Diffusion-DPO) and audited by a closed-loop VLM cr itic for strut connectivity and channel continuity.

- 2 . Track 6B — Primitive-Preserving 2D Vector Schematics & Annotated Blueprints ( SVG & LaTeX TikZ):

- StarVector-8B (CVPR 2025): Uses a SigLip-384 vision encoder + St arCoder2-7B LLM (16k context) with logit-biased decoding and CairoSVG + DinoScor e ranking to compile orthographic views directly into semantic SV G primitives ( <rect> , <circle> , <line> , <text> , <path> ), achieving a SO TA 0.959 DinoScore on SVG-Diagrams (vs. 0.882 for VTracer and 0.875 f or Potrace).

- SVGThinker (ACM MM 2025) & Two-Stage Diagram-MMU TikZ Synthesis ( 2026): Generates sequential step-by-step construction primitives t_i ~ P(x | I_ i, I_{i-1}, t_g, I_n) and compiles an intermediate verified text specification int o LaTeX TikZ cross-sectional blueprints labeled with SAPPhIRE physical flo w vectors ( Input arrows, Phenomenon gradients, Part material callouts, and dimensional t olerances).

- 3 . Track 6C — Programmatic & Topological B-Rep 3D CAD Compilation (STEP / CadQuer y):

- CAD-Coder (Doris et al., MIT / ASME JMD 2026) & Bioinspired123D ( 2026): Translates the synthesized visual and orthographic representations int o executable, human-editable CadQuery Python scripts with 100% synt ax validity and a 56.9% reduction in physically infeasible 3D CAD geometr y , paired with a Query2CAD interpreter-traceback self-repair loop.

- Pointer-CAD v2 (Qi et al., CVPR / ECCV 2026): For complex multi-step t opological modifications (such as shelling internal cavities or filleting bio-inspir ed strut junctions), a Graph Neural Network (GNN) encodes the e volving 3D Boundary Representation (B-Rep) graph (faces, loops, edges, v ertices) using a joint token + pointer network loss (L = L_token + α · L_ pointer) and Plan-Then-Construct continuous parameter regression . This eliminat es 8-bit staircase quantization artifacts and minimizes


non-manif old Dangling Edge Length (DangEL) (from CAD-MLLM), exporting wat ertight ISO 10303 STEP solids ready for automated multiphysics FEA /CFD screening (SimScale AI Agent) whose stress/thermal contours f eed back into Ctrl-U.

## 5 . Comprehensive Benchmark & Evaluation Protocol

T o validate FLBDS v3.0 for publication in top venues (ASME JMD, JCISE, CVPR, ACM CHI, or Design Science ), the system is evaluated across five standardized quantitative benchmar ks:

## 1 . Ontology & Causal Extraction Metrics:

- Construct-level Precision, Recall, F1, and RAG Groundedness Score G(y_i | r_ i) across all 7 SAPPhIRE constructs (specifically tracking the oRgan R and Part P groundedness lift from Abductive Variable Verification + Visual Gr ounding).

- 2 . Visual Grounding & Affordance Segmentation Metrics:

- Small-object localization IoU on micro-scale oRgans (evaluating ACS-Free + 19% lift and ReLaViS ScreenSpot-Pro accuracy) and functional Part mask mIoU on AGD20K (AffordanceSAM).

- 3 . Analogical Subgraph & Physical Similitude Metrics:

- Analogical Alignment F1-Score (DeepGAR 88.4% benchmark), Buckingham Pi Similitude P ass Rate (percentage of generated designs satisfying R e, Bi, Bo, Π_g critical regimes), and kTRIZ Compilation Pass R ate (100% type-safe contradiction resolution).

- 4 . Visual & Schematic Synthesis Metrics:

- Conditional consistency (Mask mIoU, Line-Art Edge SSIM, Depth RMSE), Unmask ed Datum Drift MSE (verifying zero pixel alteration in 1 - M_Eng ), DinoScor e on SVG-Bench / SVG-Diagrams (target ≥ 0.959), and compilation + t opological isomorphism on Diagram-MMU , TriGeoBench , and DiagramEval .

- 5 . 3D CAD & Multiphysics Manufacturability Metrics:

- CadQuery syntax validity (100%), 3D Solid Volumetric IoU, Dangling Edge Lengt h (DangEL → 0) for watertight manifold verification, surface enclosure e xtent, and FEA/CFD performance gain against the unmodified baseline Image_Eng .

## 6 . Consolidated Master Bibliography (2023–2026)

## A . SAPPhIRE Causality, Extraction & Biomimetic Thesauri

- 1 . Chakrabarti, A., et al. (2005 / 2023). SAPPhIRE Model of Causality & Extensions to Mul ti-State Mechanical Devices (MSMDs) . Majumder, A., Bhatt, A., & Chakrabarti, A. (2023).


- 2 . Srinivasan, V., et al. (2025/2026). Generate-Evaluate-Modify-Select of SAPPhIRE ( GoS) Framework & Physical Laws Catalog . ASTM Smart and Sustainable Manuf acturing Systems (doi:10.1520/SSMS20250030).

- 3 . Majumder, A., Bhattacharya, K., & Chakrabarti, A. (2024/2025). Development and Ev aluation of a Retrieval-Augmented Generation (HyDE-CoT RAG) Framework for SAPPhIRE Ex traction . arXiv:2406.19493 & arXiv:2407.00396 (Springer 2025, doi:10 .1007/978-981-96-5511-3_38).

- 4 . Bhattacharya, K., Srinivasan, V., Keshwani, S., & Chakrabarti, A. (2024/2025). Inf ormation Extraction for the SAPPhIRE Model of Causality Using Dependency P arsing, WordNet, and Propositional Rules . AI EDAM (2024, doi:10 .1017/S0890060424000118) & ASME JCISE (2025, Vol. 25(9), 091003, doi:10 .1115/1.4068637).

- 5 . Singh, H., & Chakrabarti, A. (2024). Problem SAPPhIRE: Evaluating Intrinsic Novelty of Design Pr oblems . arXiv:2410.18629.

- 6 . Kang, H., Lin, Y., Chen, J., Hong, M., Martelaro, N., & Kittur, A. (2024/2025). BioSpar k: An Interactive System for Biological-Analogical Mechanisms via T ree-of-Life Expansion . ACM CHI EA 2024 & ACM CHI 2025 (arXiv:2503.09838v1).

- 7 . Chen, L., Cai, Z., Cheang, C., Long, Y., Sun, L., Childs, P., & Zuo, H. (2024–2026). AskNatur eNet, BIDTrainer, and AskNatureGPT: Solution-Driven Bio-Inspired Design via Fine- Tuned Multi-LLM Evaluators . Advanced Engineering Informatics (2024), A CM CHI (2024), & Journal of Engineering Design (2025/2026, Vol. 37(1), doi:10 .1080/09544828.2025.2481536).

- 8 . Lin, Y., et al. (2024/2025). Inkspire: Supporting Design Exploration with Generative AI thr ough Analogical Sketching . ACM UIST 2024 & ACM CHI 2025.

- 9 . Rosa, F., et al. UNO-BID: Unified Ontology for Causal-Function Modeling in Biologicall y Inspired Design .

- B . Neuro-Symbolic Structure Mapping, Scaling Laws & Automated TRIZ

- 1 0. Ling, X., et al. (2023). DeepGAR: Deep Graph Learning for Analogical Reasoning via Continuous Or der-Embeddings . IEEE ICDM / arXiv:2211.10821.

- 1 1. Jiang, S., Luo, J., et al. (2024/2025). AutoTRIZ: An Artificial Ideation Tool for Aut omated TRIZ Reasoning with Search-Augmented Matrix Lookup . arXiv:2 403.13002v4.

- 1 2. TRIZ Agents: Multi-Agent Step Orchestration & Physical Contradiction Separation Pr inciples (2025). arXiv:2506.18783.

- 1 3. kTRIZ: Statically Typed Kotlin Domain-Specific Language & Compiler Oracle for TRIZ and 7 6 Standard Su-Field Solutions (2026). Apache-2.0 Open-Source Kotlin TRIZ Specific ation.

- 1 4. Bai, Z., Li, Y., Hao, J., & Zhang, X. (2026). Advanced BioTRIZ Method Based on Laws of T echnical System Evolution (LTE) and Main Parameters of Value (MPV) . Biomimetics (Jan 2026).


- 1 5. Perricone, V., Santulli, C., Rendina, F., & Langella, C. (2021–2025). Scaling Laws, Dimensional Similitude, and Ther modynamic Sustainability in Biomimetics . Biomimetics ( doi:10.3390/biomimetics6040056 & 7010024).

- 1 6. Shuangyu, et al. (2026). Functionally Graded Heterogeneous Triply Periodic Minimal Sur face (TPMS) Vertebral Porous Scaffolds . Biomimetics (Sept 2026).

- C . Dual-Image Functional Perception & Affordance Grounding

- 1 7. Bai, S., et al. (2025/2026). Qwen2.5-VL & Qwen3-VL: Native Dynamic Resolution Vision-Language Models f or Spatial Coordinate Grounding . arXiv:2502.13923.

- 1 8. ACS-Free & ACS-Learned: Self-Improving Small Object Grounding in LVLMs via A ttention-Entropy Selection (2026). arXiv:2606.01612v1.

- 1 9. ReLaViS: Recurrent Latent Visual Search for Fine-Grained Grounding (2026). arXiv:2610 .05185v1.

- 2 0. Precise Doc: Hungarian-Matched Dual IoU Optimization for Repetitive Element Gr ounding (2026). arXiv:2606.24118.

- 2 1. Jiang, et al. (2025/2026). AffordanceSAM: Segment Anything Once More in Af fordance Grounding . ACM Multimedia (ACM MM 2026) / arXiv:2504.15650.

- 2 2. InstructPart: Task-Oriented Part Segmentation with Instruction Reasoning (2025). A CL 2025 (2025.acl-long.1179).

- 2 3. Ravi, N., et al. / IDEA-Research (2024–2026). Grounded-SAM 2: Open-Vocabulary Det ection and Promptable Pixel Segmentation .

- 2 4. Zhang, et al. (2026). Probing and Bridging Geometry-Interaction Cues for Af fordance Reasoning in Vision . CVPR 2026.

## D . Structure-Conditioned Image Synthesis, Vector Schematics & 3D CAD C ompilation

- 2 5. Black Forest Labs & Flux Ecosystem (2024–2026). FLUX.1-Fill-dev, FLUX-Redux, & Mask ed Rectified Flow Transformers . arXiv:2507.09595v1.

- 2 6. Li, M., et al. (2024). ControlNet++: Improving Conditional Controls with Efficient Consist ency Feedback . ECCV 2024 / arXiv:2404.07987.

- 2 7. Zhang, G., Zheng, Z., et al. (2025). Ctrl-U: Robust Conditional Image Generation via Uncer tainty-Aware Reward Modeling . ICLR 2025 / arXiv:2410.11236v1.

- 2 8. SmartControl: Adaptive Rough-Condition Relaxation for ControlNet (2024); P oly-DPO & VIPO: Multi-Objective Preference Optimization (2026).

- 2 9. Rodriguez, J., et al. (2025). StarVector: Generating Scalable Vector Graphics Code fr om Images and Text . CVPR 2025 / arXiv:2312.11556v2.

- 3 0. SVGThinker: Instruction-Aligned and Reasoning-Driven Sequential Text-to-SVG Gener ation (2025). ACM MM 2025 / arXiv:2509.24299.

- 3 1. Diagram-MMU (arXiv:2608.12262), TriGeoBench (arXiv:2610.27626), SciDiagBench ( arXiv:2610.27841), & Two-Stage VLM-to-TikZ Reconstruction (arXiv:2603.07936) ( 2026).


- 3 2. Doris, A. C., et al. (2025/2026). CAD-Coder: An Open-Source Vision-Language Model f or Computer-Aided Design Code Generation . ASME Journal of Mechanical Design (March 2026, Vol. 148(7), 071702) / arXiv:2505.14646.

- 3 3. Bioinspired123D: Generative 3D Code-as-Geometry Modeling System for Bioinspir ed Structures (2026). arXiv:2603.29592v1.

- 3 4. Qi, et al. (2026). Pointer-CAD v1 & v2: Unifying B-Rep Graph States and Continuous-P arameter Plan-Then-Construct CAD Generation . CVPR 2026 & ECCV 2026 / arXiv:2603 .04337.

- 3 5. Xu, et al. (2024/2025). CAD-MLLM: Unifying Multimodality-Conditioned CAD Gener ation & Dangling Edge Length (DangEL) Topological Metric . arXiv:2 411.04954v3.

- 3 6. Qin, et al. (2025). Drawing2CAD: Sequence-to-Sequence Learning from Vectorized Mul ti-View Engineering Drawings . arXiv:2508.18733.

- 3 7. Lin, et al. / Chen, et al. (2026). UniCAD & Req2CAD: Unified Multimodal CAD Construction and R equirement-to-CAD Co-Creation . CVM 2026 / ACM CHI 2026.
