"""Relational schema and Neo4j Cypher DDL generation for G_MCKG."""

from __future__ import annotations

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS graphs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    description TEXT,
    source_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT NOT NULL,
    graph_id TEXT NOT NULL,
    construct TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    confidence REAL DEFAULT 1.0,
    tags_json TEXT,
    meta_json TEXT,
    PRIMARY KEY (id, graph_id),
    FOREIGN KEY (graph_id) REFERENCES graphs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS edges (
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    graph_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    meta_json TEXT,
    PRIMARY KEY (source, target, graph_id, relation),
    FOREIGN KEY (graph_id) REFERENCES graphs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attributes (
    node_id TEXT NOT NULL,
    graph_id TEXT NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT,
    value_str TEXT,
    unit TEXT,
    dimension TEXT,
    role TEXT,
    PRIMARY KEY (node_id, graph_id, name),
    FOREIGN KEY (node_id, graph_id) REFERENCES nodes(id, graph_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- 'node' or 'edge'
    entity_id TEXT NOT NULL,
    graph_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    locator TEXT NOT NULL,
    quote TEXT,
    chunk_id TEXT,
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (graph_id) REFERENCES graphs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS embeddings (
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    modality TEXT NOT NULL, -- 'text' or 'image'
    vector BLOB NOT NULL,
    dim INTEGER NOT NULL,
    PRIMARY KEY (entity_type, entity_id, modality)
);

CREATE INDEX IF NOT EXISTS idx_nodes_construct ON nodes(construct);
CREATE INDEX IF NOT EXISTS idx_nodes_graph ON nodes(graph_id);
CREATE INDEX IF NOT EXISTS idx_edges_graph ON edges(graph_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source, graph_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target, graph_id);
CREATE INDEX IF NOT EXISTS idx_attrs_symbol ON attributes(symbol);
"""


def to_neo4j_cypher_ddl() -> str:
    """Emit Cypher DDL for constraints and indexes in Neo4j 5+."""
    return """
// G_MCKG Neo4j DDL Schema
CREATE CONSTRAINT node_uniq IF NOT EXISTS FOR (n:ConstructNode) REQUIRE (n.id, n.graph_id) IS UNIQUE;
CREATE CONSTRAINT graph_uniq IF NOT EXISTS FOR (g:SapphireGraph) REQUIRE g.id IS UNIQUE;
CREATE INDEX node_construct IF NOT EXISTS FOR (n:ConstructNode) ON (n.construct);
CREATE INDEX node_domain IF NOT EXISTS FOR (n:ConstructNode) ON (n.domain);
CREATE INDEX node_label IF NOT EXISTS FOR (n:ConstructNode) ON (n.label);
CREATE VECTOR INDEX node_embedding IF NOT EXISTS FOR (n:ConstructNode) ON (n.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
"""
