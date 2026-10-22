# Architecture

## The two roles of data

FLBDS separates *knowledge that is queried* from *models that are trained*.

```
                    ┌──────────────────────────────────────────────┐
                    │  G_MCKG  (multimodal causal property graph)  │
                    │  Neo4j today, SQLite reference implementation│
                    └──────────────────────────────────────────────┘
                        ▲                ▲                 ▲
        AskNature /     │   IDEA-INSPIRE │   USPTO/EPO     │  physical laws
        Tree-of-Life    │   multimodal   │   patents +     │  + TRIZ spine
                        │                │   drawings      │
                        └────────────────┴─────────────────┘
                                     │
                       hybrid GraphRAG (text ⊕ image ⊕ causal path)
                                     │
   Image_Bio ──► Stage 1 ──► T_Bio ──┤
   Image_Eng ──► Stage 1 ──► M_Eng ──┴──► Stage 3 alignment ──► Stage 4 Π-audit
                                                              ──► Stage 5 TRIZ
                                                              ──► Stage 6 synthesis
```

## Module map

| Module | Responsibility | Depends on |
|---|---|---|
| `ontology/constructs.py` | canonical vocabulary: 7 constructs, relations, causal chain | — |
| `ontology/models.py` | typed graph payloads, provenance, confidence | pydantic |
| `ontology/validate.py` | structural + abductive validation | models |
| `knowledge/triz.py` | 39 parameters / 40 principles / separations / matrix + lexical matcher | data/triz |
| `knowledge/physics.py` | physical laws, dimensioned variables, canonical Π-groups | data/physics |
| `reasoning/buckingham.py` | dimensional nullspace, Π-groups, regime violations | physics |
| `graph/store.py` | property graph + vector index (SQLite reference; Neo4j adapter) | models |
| `extraction/rules.py` | deterministic 5-category → SAPPhIRE mapping | ontology, knowledge |
| `extraction/hyde.py` | HyDE-CoT corrective RAG | graph, llm backend |
| `perception/*` | dual-image parsing, masks, `T_Bio` tensor field | vision backend |
| `reasoning/alignment.py` | order embeddings + constrained correspondence | ontology |
| `reasoning/triz_solver.py` | contradiction resolution + graph rewrite | triz, buckingham |
| `synthesis/*` | render / SVG / TikZ / CadQuery back-ends | perception, reasoning |
| `api/server.py` | HTTP surface | everything |
| `eval/*` | the five benchmark families | everything |

## Design rules

1. **Provenance is mandatory.** No node or edge enters the graph without an
   `Evidence` record. Anything ungrounded is rejected at write time.
2. **Symbolic beats stochastic on the critical path.** TRIZ lookups are table
   lookups; scaling checks are dimensional algebra; validation is deterministic.
   LLMs propose, the compiler disposes.
3. **Backends are swappable.** Every heavyweight model sits behind an adapter
   with a deterministic reference path, so tests never need a GPU.
4. **The graph is the contract.** Stages communicate through `SapphireGraph`
   objects, never through free-form text.

## Causality, precisely

```
P --creates--> R
(I AND R) --activates--> E --creates--> Ph --creates--> S --interpreted_as--> A
S --modifies--> P            # structural feedback
S_k  ==  I_{k+1}             # multi-state relay across subsystem boundaries
```

The oRgan `R` is the *dimensionless* geometric/topological boundary condition
created by the Parts — this is the invariant that survives transfer from a
biological specimen to an engineering artefact. `P` is the material substrate
that gets replaced. Keeping those two separate is what prevents the
"over-decoupling paradox" of collapsing structure into a single FBS node.

## Storage

| Datastore | Now | Later |
|---|---|---|
| Graph | SQLite (`flbds/graph/store.py`), full schema in `graph/schema.py` | Neo4j 5 + APOC, same schema, HNSW index |
| Vectors | float32 blobs in SQLite + NumPy cosine | FAISS HNSW / Neo4j vector index |
| Artefacts | `runs/<run_id>/` (git-ignored) | object store |
| Config | `configs/default.yaml` + `FLBDS_*` env | same |
