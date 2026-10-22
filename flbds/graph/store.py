"""SQLite property graph store with vector search and Neo4j Cypher export.

Reference implementation of G_MCKG datastore:
- Complete relational storage of SapphireGraph (nodes, edges, attributes, evidence)
- Vector embedding storage with fast in-memory cosine similarity search
- Backward causal path traversal (Action -> StateChange -> Phenomenon -> Effect -> oRgan/Part)
- Cypher query & graph export
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from flbds.graph.schema import SQLITE_SCHEMA, to_neo4j_cypher_ddl
from flbds.ontology.constructs import Construct, Relation
from flbds.ontology.models import (
    Attribute,
    CausalEdge,
    ConstructNode,
    Evidence,
    SapphireGraph,
)


class GraphStore:
    """Thread-safe SQLite property graph store for FLBDS."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript(SQLITE_SCHEMA)
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------- save_graph
    def save_graph(self, graph: SapphireGraph) -> None:
        """Persist graph and all connected constructs transactionally."""
        conn = self._get_conn()
        with conn:
            # 1. Upsert graphs
            conn.execute(
                """
                INSERT INTO graphs (id, title, domain, description, source_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    domain=excluded.domain,
                    description=excluded.description,
                    source_json=excluded.source_json;
                """,
                (
                    graph.id,
                    graph.title,
                    graph.domain,
                    graph.description,
                    json.dumps(graph.source),
                    graph.created_at.isoformat(),
                ),
            )

            # Clear existing components for graph
            conn.execute("DELETE FROM edges WHERE graph_id = ?;", (graph.id,))
            conn.execute("DELETE FROM attributes WHERE graph_id = ?;", (graph.id,))
            conn.execute("DELETE FROM evidence WHERE graph_id = ?;", (graph.id,))
            conn.execute("DELETE FROM nodes WHERE graph_id = ?;", (graph.id,))

            # 2. Insert nodes
            for n in graph.nodes:
                conn.execute(
                    """
                    INSERT INTO nodes (id, graph_id, construct, label, description, confidence, tags_json, meta_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        n.id,
                        graph.id,
                        n.construct.value,
                        n.label,
                        n.description,
                        n.confidence,
                        json.dumps(n.tags),
                        json.dumps(n.meta),
                    ),
                )
                # Attributes
                for a in n.attributes:
                    conn.execute(
                        """
                        INSERT INTO attributes (node_id, graph_id, name, symbol, value_str, unit, dimension, role)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            n.id,
                            graph.id,
                            a.name,
                            a.symbol,
                            str(a.value) if a.value is not None else None,
                            a.unit,
                            a.dimension,
                            a.role,
                        ),
                    )
                # Evidence
                for ev in n.evidence:
                    conn.execute(
                        """
                        INSERT INTO evidence (entity_type, entity_id, graph_id, source_id, source_type, locator, quote, chunk_id, confidence)
                        VALUES ('node', ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            n.id,
                            graph.id,
                            ev.source_id,
                            ev.source_type,
                            ev.locator,
                            ev.quote,
                            ev.chunk_id,
                            ev.confidence,
                        ),
                    )

            # 3. Insert edges
            for e in graph.edges:
                conn.execute(
                    """
                    INSERT INTO edges (source, target, graph_id, relation, confidence, meta_json)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        e.source,
                        e.target,
                        graph.id,
                        e.relation.value,
                        e.confidence,
                        json.dumps(e.meta),
                    ),
                )
                for ev in e.evidence:
                    conn.execute(
                        """
                        INSERT INTO evidence (entity_type, entity_id, graph_id, source_id, source_type, locator, quote, chunk_id, confidence)
                        VALUES ('edge', ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            e.key,
                            graph.id,
                            ev.source_id,
                            ev.source_type,
                            ev.locator,
                            ev.quote,
                            ev.chunk_id,
                            ev.confidence,
                        ),
                    )

    # -------------------------------------------------------------- get_graph
    def get_graph(self, graph_id: str) -> SapphireGraph:
        """Reconstitute a complete SapphireGraph from SQLite."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM graphs WHERE id = ?;", (graph_id,)).fetchone()
        if not row:
            raise KeyError(f"Graph id '{graph_id}' not found")

        # Load nodes
        nodes: list[ConstructNode] = []
        node_rows = conn.execute(
            "SELECT * FROM nodes WHERE graph_id = ? ORDER BY id;", (graph_id,)
        ).fetchall()

        for nr in node_rows:
            nid = nr["id"]
            # Load attributes
            attr_rows = conn.execute(
                "SELECT * FROM attributes WHERE node_id = ? AND graph_id = ?;", (nid, graph_id)
            ).fetchall()
            attrs = [
                Attribute(
                    name=ar["name"],
                    symbol=ar["symbol"],
                    value=ar["value_str"],
                    unit=ar["unit"],
                    dimension=ar["dimension"],
                    role=ar["role"],
                )
                for ar in attr_rows
            ]

            # Load evidence
            ev_rows = conn.execute(
                """
                SELECT * FROM evidence
                WHERE entity_type = 'node' AND entity_id = ? AND graph_id = ?;
                """,
                (nid, graph_id),
            ).fetchall()
            evs = [
                Evidence(
                    source_id=er["source_id"],
                    source_type=er["source_type"],
                    locator=er["locator"],
                    quote=er["quote"],
                    chunk_id=er["chunk_id"],
                    confidence=er["confidence"],
                )
                for er in ev_rows
            ]

            node = ConstructNode(
                id=nid,
                construct=Construct(nr["construct"]),
                label=nr["label"],
                description=nr["description"] or "",
                attributes=attrs,
                evidence=evs,
                confidence=nr["confidence"],
                tags=json.loads(nr["tags_json"] or "[]"),
                meta=json.loads(nr["meta_json"] or "{}"),
            )
            nodes.append(node)

        # Load edges
        edges: list[CausalEdge] = []
        edge_rows = conn.execute(
            "SELECT * FROM edges WHERE graph_id = ?;", (graph_id,)
        ).fetchall()

        for er in edge_rows:
            key = f"{er['source']}-[{er['relation']}]->{er['target']}"
            ev_rows = conn.execute(
                """
                SELECT * FROM evidence
                WHERE entity_type = 'edge' AND entity_id = ? AND graph_id = ?;
                """,
                (key, graph_id),
            ).fetchall()
            edge_evs = [
                Evidence(
                    source_id=rev["source_id"],
                    source_type=rev["source_type"],
                    locator=rev["locator"],
                    quote=rev["quote"],
                    chunk_id=rev["chunk_id"],
                    confidence=rev["confidence"],
                )
                for rev in ev_rows
            ]

            edge = CausalEdge(
                source=er["source"],
                target=er["target"],
                relation=Relation(er["relation"]),
                confidence=er["confidence"],
                evidence=edge_evs,
                meta=json.loads(er["meta_json"] or "{}"),
            )
            edges.append(edge)

        created_at = datetime.fromisoformat(row["created_at"])
        return SapphireGraph(
            id=row["id"],
            title=row["title"],
            domain=row["domain"],
            description=row["description"] or "",
            nodes=nodes,
            edges=edges,
            source=json.loads(row["source_json"] or "{}"),
            created_at=created_at,
        )

    def list_graphs(self, domain: str | None = None) -> list[SapphireGraph]:
        conn = self._get_conn()
        if domain:
            rows = conn.execute(
                "SELECT id FROM graphs WHERE domain = ? ORDER BY id;", (domain,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT id FROM graphs ORDER BY id;").fetchall()
        return [self.get_graph(r["id"]) for r in rows]

    def delete_graph(self, graph_id: str) -> bool:
        conn = self._get_conn()
        with conn:
            cur = conn.execute("DELETE FROM graphs WHERE id = ?;", (graph_id,))
            return cur.rowcount > 0

    # ------------------------------------------------------------- embeddings
    def store_embedding(
        self,
        entity_id: str,
        modality: str,
        vector: np.ndarray,
        entity_type: str = "node",
    ) -> None:
        conn = self._get_conn()
        vec_bytes = np.asarray(vector, dtype=np.float32).tobytes()
        with conn:
            conn.execute(
                """
                INSERT INTO embeddings (entity_type, entity_id, modality, vector, dim)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(entity_type, entity_id, modality) DO UPDATE SET
                    vector=excluded.vector,
                    dim=excluded.dim;
                """,
                (entity_type, entity_id, modality, vec_bytes, len(vector)),
            )

    def vector_search(
        self,
        query_vector: np.ndarray,
        modality: str = "text",
        top_k: int = 10,
        domain: str | None = None,
    ) -> list[tuple[str, float]]:
        """Search entities by cosine similarity against stored vector embeddings."""
        conn = self._get_conn()
        query_vec = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm < 1e-9:
            return []
        query_vec = query_vec / q_norm

        rows = conn.execute(
            "SELECT entity_id, vector, dim FROM embeddings WHERE modality = ?;", (modality,)
        ).fetchall()

        if not rows:
            return []
        ids = [r["entity_id"] for r in rows]
        mat = np.array([np.frombuffer(r["vector"], dtype=np.float32) for r in rows], dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms < 1e-9] = 1.0
        mat = mat / norms
        sims = mat @ query_vec

        if len(sims) <= top_k:
            top_idxs = np.argsort(-sims)
        else:
            top_idxs = np.argpartition(-sims, top_k)[:top_k]
            top_idxs = top_idxs[np.argsort(-sims[top_idxs])]

        return [(ids[i], float(sims[i])) for i in top_idxs]

    # ------------------------------------------------------ causal traversal
    def backward_causal_path(self, graph_id: str, start_node_id: str) -> list[CausalEdge]:
        """Traverse backwards along incoming causal edges (e.g. Action -> Part/oRgan)."""
        g = self.get_graph(graph_id)
        visited_nodes: set[str] = set()
        path_edges: list[CausalEdge] = []
        queue = [start_node_id]

        while queue:
            curr = queue.pop(0)
            if curr in visited_nodes:
                continue
            visited_nodes.add(curr)
            for inc in g.incoming(curr):
                if inc.relation.is_causal:
                    path_edges.append(inc)
                    queue.append(inc.source)
        return path_edges

    def export_cypher(self, graph_id: str | None = None) -> str:
        """Export graphs to Cypher statements for import into Neo4j."""
        graphs = [self.get_graph(graph_id)] if graph_id else self.list_graphs()
        lines: list[str] = [to_neo4j_cypher_ddl(), ""]
        for g in graphs:
            lines.append(f"// Graph: {g.title} ({g.id})")
            lines.append(
                f"MERGE (g:SapphireGraph {{id: '{g.id}'}}) "
                f"SET g.title = '{g.title.replace("'", "\\'")}', g.domain = '{g.domain}';"
            )
            for n in g.nodes:
                lbl = n.label.replace("'", "\\'")
                lines.append(
                    f"MERGE (n:ConstructNode {{id: '{n.id}', graph_id: '{g.id}'}}) "
                    f"SET n:{n.construct.name}, n.construct = '{n.construct.value}', n.label = '{lbl}';"
                )
            for e in g.edges:
                lines.append(
                    f"MATCH (src:ConstructNode {{id: '{e.source}', graph_id: '{g.id}'}}), "
                    f"(dst:ConstructNode {{id: '{e.target}', graph_id: '{g.id}'}}) "
                    f"MERGE (src)-[:{e.relation.name}]->(dst);"
                )
            lines.append("")
        return "\n".join(lines)
