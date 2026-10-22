"""Deterministic validation of a SAPPhIRE graph.

Two families of checks:

1. **Structural** — the graph must be a well-formed causal DAG whose edges obey
   the construct grammar. Catches hallucinated or mis-ordered relations.
2. **Abductive** — the guardrail from the specification:

       Activates(I, R -> e)  <=>  Variables(e) subset-of Attrs(I) | Attrs(R)

   If an Effect needs `theta` and `r` but no oRgan or Input supplies them, the
   claim is not physically grounded and is rejected (or flagged for a targeted
   GraphRAG follow-up, depending on strictness).

Everything here is pure Python: no model call, no randomness, same answer every
time. That is deliberate — the symbolic layer is what makes the system auditable.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from flbds.ontology.constructs import (
    ALLOWED_ENDPOINTS,
    CAUSAL_CHAIN,
    CHAIN_ORDER,
    Construct,
    Relation,
)
from flbds.ontology.models import CausalEdge, ConstructNode, SapphireGraph


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(dict):
    """A single finding. Behaves like a dict so it serialises to JSON directly."""

    def __init__(
        self,
        code: str,
        severity: Severity,
        message: str,
        node_ids: Iterable[str] = (),
        edge_keys: Iterable[str] = (),
    ) -> None:
        super().__init__(
            code=code,
            severity=severity.value,
            message=message,
            node_ids=list(node_ids),
            edge_keys=list(edge_keys),
        )

    @property
    def code(self) -> str:
        return self["code"]

    @property
    def severity(self) -> Severity:
        return Severity(self["severity"])

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"[{self[severity]}] {self[code]}: {self[message]}"


@dataclass(frozen=True)
class AbductiveCoverage:
    """Result of the variable-coverage check for one Effect."""

    effect_id: str
    declared: tuple[str, ...]
    covered: tuple[str, ...]
    missing: tuple[str, ...]
    supplying_nodes: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.missing


@dataclass
class ValidationReport:
    graph_id: str
    issues: list[ValidationIssue] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    abductive: list[AbductiveCoverage] = field(default_factory=list)

    # ------------------------------------------------------------- summaries
    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def codes(self) -> set[str]:
        return {i.code for i in self.issues}

    def to_dict(self) -> dict:
        return {
            "graph_id": self.graph_id,
            "ok": self.ok,
            "n_errors": len(self.errors),
            "n_warnings": len(self.warnings),
            "metrics": self.metrics,
            "issues": [dict(i) for i in self.issues],
            "abductive": [
                {
                    "effect_id": a.effect_id,
                    "declared": list(a.declared),
                    "covered": list(a.covered),
                    "missing": list(a.missing),
                    "complete": a.complete,
                }
                for a in self.abductive
            ],
        }

    def summary(self) -> str:  # pragma: no cover - cosmetic
        status = "PASS" if self.ok else "FAIL"
        return (
            f"{status} {self.graph_id}: {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s), "
            f"construct coverage {self.metrics.get('construct_coverage', 0):.0%}, "
            f"grounding {self.metrics.get('grounding_ratio', 0):.0%}"
        )


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------


def validate_graph(
    graph: SapphireGraph,
    *,
    strict_abductive: bool = True,
    require_evidence: bool = True,
    min_confidence: float = 0.0,
) -> ValidationReport:
    """Run every deterministic check and return a report (never raises)."""

    report = ValidationReport(graph_id=graph.id)
    nodes = graph.nodes
    by_id = {n.id: n for n in nodes}

    _check_duplicates(graph, report)
    _check_labels_and_confidence(graph, report, min_confidence)
    _check_edges(graph, by_id, report)
    _check_acyclicity(graph, by_id, report)
    _check_construct_coverage(graph, report)
    _check_chain_links(graph, by_id, report)
    _check_grounding(graph, report, require_evidence)
    _check_abductive(graph, by_id, report, strict_abductive)

    report.metrics.update(
        {
            "n_nodes": float(len(nodes)),
            "n_edges": float(len(graph.edges)),
            "n_causal_edges": float(len(graph.causal_edges())),
            "construct_coverage": _coverage(graph),
            "grounding_ratio": (
                sum(1 for n in nodes if n.grounded()) / len(nodes) if nodes else 0.0
            ),
        }
    )
    return report


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def _check_duplicates(graph: SapphireGraph, report: ValidationReport) -> None:
    seen: set[str] = set()
    dupes: list[str] = []
    for n in graph.nodes:
        if n.id in seen:
            dupes.append(n.id)
        seen.add(n.id)
    for nid in dupes:
        report.issues.append(
            ValidationIssue(
                "DUPLICATE_NODE_ID",
                Severity.ERROR,
                f"node id {nid} appears more than once",
                node_ids=[nid],
            )
        )

    seen_edges: set[str] = set()
    for e in graph.edges:
        if e.key in seen_edges:
            report.issues.append(
                ValidationIssue(
                    "DUPLICATE_EDGE",
                    Severity.ERROR,
                    f"edge {e.key} appears more than once",
                    [e.source, e.target],
                    [e.key],
                )
            )
        seen_edges.add(e.key)


def _check_labels_and_confidence(
    graph: SapphireGraph, report: ValidationReport, min_confidence: float
) -> None:
    for n in graph.nodes:
        if not n.label.strip():
            report.issues.append(
                ValidationIssue("EMPTY_LABEL", Severity.ERROR, "node has an empty label", [n.id])
            )
        if n.confidence < min_confidence:
            report.issues.append(
                ValidationIssue(
                    "LOW_CONFIDENCE",
                    Severity.WARNING,
                    f"confidence {n.confidence:.2f} below threshold {min_confidence:.2f}",
                    [n.id],
                )
            )


def _check_edges(
    graph: SapphireGraph, by_id: dict[str, ConstructNode], report: ValidationReport
) -> None:
    for e in graph.edges:
        missing = [x for x in (e.source, e.target) if x not in by_id]
        if missing:
            report.issues.append(
                ValidationIssue(
                    "DANGLING_EDGE", Severity.ERROR, f"edge points at unknown node(s) {missing}", [], [e.key]
                )
            )
            continue

        if e.source == e.target:
            report.issues.append(
                ValidationIssue(
                    "SELF_LOOP", Severity.ERROR, "an edge may not loop onto its own node", [e.source], [e.key]
                )
            )

        allowed = ALLOWED_ENDPOINTS.get(e.relation)
        if allowed is None:
            continue
        pair = (by_id[e.source].construct, by_id[e.target].construct)
        if pair not in allowed:
            report.issues.append(
                ValidationIssue(
                    "ILLEGAL_ENDPOINT",
                    Severity.ERROR,
                    f"relation {e.relation.value} cannot connect "
                    f"{pair[0].value} -> {pair[1].value}",
                    [e.source, e.target],
                    [e.key],
                )
            )


def _check_acyclicity(
    graph: SapphireGraph, by_id: dict[str, ConstructNode], report: ValidationReport
) -> None:
    adj: dict[str, list[str]] = defaultdict(list)
    for e in graph.causal_edges():
        # Feedback edges (MODIFIES) close the control loop over time;
        # the feedforward causal chain must remain a strict DAG.
        if e.relation is not Relation.MODIFIES and e.source in by_id and e.target in by_id:
            adj[e.source].append(e.target)

    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = defaultdict(int)
    stack: list[str] = []

    def dfs(u: str) -> bool:
        colour[u] = GREY
        stack.append(u)
        for v in adj[u]:
            if colour[v] == GREY:
                cycle = stack[stack.index(v) :] + [v]
                report.issues.append(
                    ValidationIssue(
                        "CAUSAL_CYCLE",
                        Severity.ERROR,
                        "causal chain forms a cycle: " + " -> ".join(cycle),
                        cycle,
                    )
                )
                return True
            if colour[v] == WHITE and dfs(v):
                return True
        stack.pop()
        colour[u] = BLACK
        return False

    for n in graph.nodes:
        if colour[n.id] == WHITE:
            if dfs(n.id):
                break


def _check_construct_coverage(graph: SapphireGraph, report: ValidationReport) -> None:
    present = {n.construct for n in graph.nodes}
    for c in CHAIN_ORDER:
        if c not in present:
            report.issues.append(
                ValidationIssue(
                    "MISSING_CONSTRUCT",
                    Severity.WARNING,
                    f"no {c.value} ({_construct_name(c)}) node — the causal chain is incomplete",
                )
            )


def _check_chain_links(
    graph: SapphireGraph, by_id: dict[str, ConstructNode], report: ValidationReport
) -> None:
    have: set[tuple[Construct, Relation, Construct]] = set()
    for e in graph.causal_edges():
        if e.source in by_id and e.target in by_id:
            have.add((by_id[e.source].construct, e.relation, by_id[e.target].construct))
    for src, rel, dst in CAUSAL_CHAIN:
        if (src, rel, dst) not in have:
            report.issues.append(
                ValidationIssue(
                    "MISSING_CHAIN_LINK",
                    Severity.WARNING,
                    f"missing link {src.value} --{rel.value}--> {dst.value}",
                )
            )


def _check_grounding(
    graph: SapphireGraph, report: ValidationReport, require_evidence: bool
) -> None:
    if not require_evidence:
        return
    for n in graph.nodes:
        if not n.grounded():
            report.issues.append(
                ValidationIssue(
                    "UNGROUNDED_CLAIM",
                    Severity.WARNING,
                    f"{n.construct.value} node {n.label} has no evidence pointer",
                    [n.id],
                )
            )
    for e in graph.causal_edges():
        if not e.evidence:
            report.issues.append(
                ValidationIssue(
                    "UNGROUNDED_CLAIM",
                    Severity.INFO,
                    f"edge {e.key} has no evidence pointer",
                    [e.source, e.target],
                    [e.key],
                )
            )


def _check_abductive(
    graph: SapphireGraph,
    by_id: dict[str, ConstructNode],
    report: ValidationReport,
    strict: bool,
) -> None:
    suppliers = [n for n in graph.nodes if n.construct in (Construct.INPUT, Construct.ORGAN, Construct.PART)]
    supplied: dict[str, list[str]] = defaultdict(list)
    for n in suppliers:
        for sym in n.attribute_symbols():
            supplied[sym].append(n.id)

    severity = Severity.ERROR if strict else Severity.WARNING
    for effect in graph.effects:
        declared = tuple(sorted(effect.attribute_symbols()))
        if not declared:
            report.issues.append(
                ValidationIssue(
                    "EFFECT_VARIABLES_UNSPECIFIED",
                    Severity.WARNING,
                    f"Effect {effect.label} declares no variables; abductive check is vacuous",
                    [effect.id],
                )
            )
            continue
        covered = tuple(d for d in declared if d in supplied)
        missing = tuple(d for d in declared if d not in supplied)
        nodes_involved = tuple(sorted({nid for d in covered for nid in supplied[d]}))
        report.abductive.append(
            AbductiveCoverage(
                effect_id=effect.id,
                declared=declared,
                covered=covered,
                missing=missing,
                supplying_nodes=nodes_involved,
            )
        )
        if missing:
            report.issues.append(
                ValidationIssue(
                    "ABDUCTIVE_VARIABLE_GAP",
                    severity,
                    f"Effect {effect.label} requires {list(missing)} but no Input/oRgan/Part "
                    "supplies them; issue a targeted GraphRAG follow-up",
                    [effect.id, *nodes_involved],
                )
            )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _coverage(graph: SapphireGraph) -> float:
    present = {n.construct for n in graph.nodes}
    return len(present & set(CHAIN_ORDER)) / len(CHAIN_ORDER)


def _construct_name(c: Construct) -> str:
    from flbds.ontology.constructs import CONSTRUCT_SPECS

    return CONSTRUCT_SPECS[c].name


def abductive_gap(graph: SapphireGraph) -> dict[str, tuple[str, ...]]:
    """Convenience: effect id -> missing variable symbols."""
    report = validate_graph(graph, strict_abductive=False)
    return {a.effect_id: a.missing for a in report.abductive if a.missing}
