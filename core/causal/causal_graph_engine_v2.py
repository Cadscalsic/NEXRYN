from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core.epistemic_models import clamp


DEFAULT_GRAPH_PATH = Path("memory") / "causal_graph.json"
NEGATION_PREFIXES = ("NOT ", "not:", "not_", "anti_")
CAUSAL_REPORT = "CAUSAL GRAPH REPORT"
CAUSAL_PATH_REPORT = "CAUSAL PATH REPORT"
COUNTERFACTUAL_REPORT = "COUNTERFACTUAL REPORT"
CAUSAL_CONFLICT_REPORT = "CAUSAL CONFLICT REPORT"
CAUSAL_ALIGNMENT_REPORT = "CAUSAL ALIGNMENT REPORT"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_identifier(value: Any, field_name: str) -> str:
    identifier = str(value or "").strip()
    if not identifier:
        raise ValueError(f"{field_name} must be a non-empty string")
    return identifier


def _normal_form(concept: str) -> str:
    value = str(concept or "").strip()
    lowered = value.lower()
    for prefix in NEGATION_PREFIXES:
        if lowered.startswith(prefix.lower()):
            return value[len(prefix):].strip().lower()
    return lowered


def _is_negated(concept: str) -> bool:
    lowered = str(concept or "").strip().lower()
    return any(lowered.startswith(prefix.lower()) for prefix in NEGATION_PREFIXES)


@dataclass
class CausalNode:
    """Persistent graph node representing a concept, truth, identity, or event."""

    node_id: str
    node_type: str = "concept"
    label: str = ""
    confidence: float = 0.5
    created_at: str = field(default_factory=_utc_timestamp)
    last_seen: str = field(default_factory=_utc_timestamp)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.node_id = _clean_identifier(self.node_id, "node_id")
        self.node_type = str(self.node_type or "concept").strip().lower()
        self.label = str(self.label or self.node_id).strip()
        self.confidence = clamp(self.confidence)
        self.metadata = dict(self.metadata or {})
        self.created_at = str(self.created_at or _utc_timestamp())
        self.last_seen = str(self.last_seen or _utc_timestamp())

    def merge(self, other: "CausalNode") -> "CausalNode":
        """Merge newer evidence into an existing node."""

        self.confidence = max(self.confidence, other.confidence)
        self.last_seen = other.last_seen or _utc_timestamp()
        self.metadata.update(other.metadata)
        return self

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CausalEdge:
    """Persistent directed cause-effect relationship with temporal support."""

    cause: str
    effect: str
    confidence: float = 0.5
    support_count: int = 1
    contradiction_count: int = 0
    last_observed: str = field(default_factory=_utc_timestamp)
    stability: float = 0.5
    relation_type: str = "causes"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.cause = _clean_identifier(self.cause, "cause")
        self.effect = _clean_identifier(self.effect, "effect")
        self.confidence = clamp(self.confidence)
        self.support_count = max(int(self.support_count or 0), 0)
        self.contradiction_count = max(int(self.contradiction_count or 0), 0)
        self.last_observed = str(self.last_observed or _utc_timestamp())
        self.stability = clamp(self.stability)
        self.relation_type = str(self.relation_type or "causes").strip()
        self.metadata = dict(self.metadata or {})

    @property
    def key(self) -> tuple[str, str]:
        return self.cause, self.effect

    def reinforce(self, amount: float = 0.04) -> "CausalEdge":
        """Strengthen the edge after a supporting observation."""

        self.support_count += 1
        learning_rate = clamp(amount, 0.0, 0.25)
        support_pressure = min(self.support_count, 20) / 20.0
        contradiction_penalty = min(self.contradiction_count, 20) / 40.0
        self.confidence = clamp(
            self.confidence
            + learning_rate * (1.0 - self.confidence)
            + support_pressure * 0.01
            - contradiction_penalty * 0.01
        )
        self.stability = clamp(self.stability + learning_rate * 0.75)
        self.last_observed = _utc_timestamp()
        return self

    def contradict(self, amount: float = 0.05) -> "CausalEdge":
        """Weaken the edge after contradictory evidence."""

        self.contradiction_count += 1
        pressure = clamp(amount, 0.0, 0.30)
        self.confidence = clamp(self.confidence - pressure)
        self.stability = clamp(self.stability - pressure * 0.75)
        self.last_observed = _utc_timestamp()
        return self

    def decay(self, rate: float = 0.02) -> "CausalEdge":
        """Apply bounded temporal decay when an edge is not observed."""

        decay_rate = clamp(rate, 0.0, 0.25)
        self.confidence = clamp(self.confidence * (1.0 - decay_rate))
        self.stability = clamp(self.stability * (1.0 - decay_rate * 0.75))
        return self

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CausalPath:
    """A directed multi-hop causal path and its propagated confidence."""

    nodes: list[str]
    edges: list[CausalEdge]

    @property
    def depth(self) -> int:
        return len(self.edges)

    @property
    def confidence(self) -> float:
        if not self.edges:
            return 0.0
        product = 1.0
        stability = 0.0
        support = 0
        for edge in self.edges:
            product *= max(edge.confidence, 0.0001)
            stability += edge.stability
            support += edge.support_count
        geometric_confidence = product ** (1.0 / len(self.edges))
        depth_penalty = 0.96 ** max(len(self.edges) - 1, 0)
        stability_factor = stability / len(self.edges)
        return clamp(
            geometric_confidence * 0.78
            + stability_factor * 0.17
            + min(support / (len(self.edges) * 12.0), 1.0) * 0.05
        ) if depth_penalty >= 1.0 else clamp(
            (
                geometric_confidence * 0.78
                + stability_factor * 0.17
                + min(support / (len(self.edges) * 12.0), 1.0) * 0.05
            )
            * depth_penalty
        )

    @property
    def support_count(self) -> int:
        if not self.edges:
            return 0
        return min(edge.support_count for edge in self.edges)

    @property
    def stability(self) -> float:
        if not self.edges:
            return 0.0
        return clamp(sum(edge.stability for edge in self.edges) / len(self.edges))

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": list(self.nodes),
            "edges": [edge.as_dict() for edge in self.edges],
            "depth": self.depth,
            "confidence": self.confidence,
            "support_count": self.support_count,
            "stability": self.stability,
        }


class CausalGraph:
    """Persistent directed graph optimized for runtime causal reasoning."""

    def __init__(self) -> None:
        self.nodes: dict[str, CausalNode] = {}
        self.edges: dict[tuple[str, str], CausalEdge] = {}

    def add_node(
        self,
        node_id: str,
        node_type: str = "concept",
        label: str = "",
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> CausalNode:
        node = CausalNode(
            node_id=node_id,
            node_type=node_type,
            label=label or node_id,
            confidence=confidence,
            metadata=metadata or {},
            last_seen=_utc_timestamp(),
        )
        if node.node_id in self.nodes:
            return self.nodes[node.node_id].merge(node)
        self.nodes[node.node_id] = node
        return node

    def add_edge(
        self,
        cause: str,
        effect: str,
        confidence: float = 0.5,
        support_count: int = 1,
        contradiction_count: int = 0,
        stability: float | None = None,
        relation_type: str = "causes",
        metadata: dict[str, Any] | None = None,
        reinforce_existing: bool = True,
    ) -> CausalEdge:
        cause = _clean_identifier(cause, "cause")
        effect = _clean_identifier(effect, "effect")
        self.add_node(cause)
        self.add_node(effect)
        key = (cause, effect)
        if key in self.edges:
            edge = self.edges[key]
            edge.metadata.update(metadata or {})
            if confidence > edge.confidence:
                edge.confidence = clamp((edge.confidence + confidence) / 2.0)
            if reinforce_existing:
                edge.reinforce()
            return edge

        edge = CausalEdge(
            cause=cause,
            effect=effect,
            confidence=confidence,
            support_count=support_count,
            contradiction_count=contradiction_count,
            stability=confidence if stability is None else stability,
            relation_type=relation_type,
            metadata=metadata or {},
        )
        self.edges[key] = edge
        return edge

    def remove_edge(self, cause: str, effect: str) -> CausalEdge | None:
        return self.edges.pop((cause, effect), None)

    def update_edge_confidence(
        self,
        cause: str,
        effect: str,
        confidence: float | None = None,
        support_delta: int = 0,
        contradiction_delta: int = 0,
        stability: float | None = None,
    ) -> CausalEdge:
        edge = self.edges.get((cause, effect))
        if edge is None:
            edge = self.add_edge(cause, effect, confidence=confidence or 0.5)
        if confidence is not None:
            edge.confidence = clamp(confidence)
        edge.support_count = max(edge.support_count + int(support_delta), 0)
        edge.contradiction_count = max(
            edge.contradiction_count + int(contradiction_delta),
            0,
        )
        if stability is not None:
            edge.stability = clamp(stability)
        edge.last_observed = _utc_timestamp()
        return edge

    def adjacency(self) -> dict[str, list[CausalEdge]]:
        adjacent: dict[str, list[CausalEdge]] = defaultdict(list)
        for edge in self.edges.values():
            adjacent[edge.cause].append(edge)
        return adjacent

    def incoming(self) -> dict[str, list[CausalEdge]]:
        incoming: dict[str, list[CausalEdge]] = defaultdict(list)
        for edge in self.edges.values():
            incoming[edge.effect].append(edge)
        return incoming

    def find_causal_paths(
        self,
        cause: str | None,
        effect: str,
        max_depth: int = 5,
        minimum_confidence: float = 0.0,
    ) -> list[CausalPath]:
        effect = _clean_identifier(effect, "effect")
        max_depth = max(int(max_depth or 1), 1)
        starts = [cause] if cause else sorted(self.nodes)
        adjacent = self.adjacency()
        paths: list[CausalPath] = []

        for start in starts:
            if not start or start not in self.nodes:
                continue
            queue: deque[tuple[str, list[str], list[CausalEdge]]] = deque(
                [(start, [start], [])]
            )
            while queue:
                current, nodes, edges = queue.popleft()
                if len(edges) > max_depth:
                    continue
                if current == effect and edges:
                    path = CausalPath(nodes=nodes, edges=edges)
                    if path.confidence >= minimum_confidence:
                        paths.append(path)
                    continue
                for edge in adjacent.get(current, []):
                    if edge.effect in nodes:
                        continue
                    queue.append((edge.effect, [*nodes, edge.effect], [*edges, edge]))

        paths.sort(key=lambda item: (item.confidence, -item.depth), reverse=True)
        return paths

    def export_graph(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "generated_at": _utc_timestamp(),
            "nodes": [node.as_dict() for node in self.nodes.values()],
            "edges": [edge.as_dict() for edge in self.edges.values()],
        }

    @classmethod
    def import_graph(cls, payload: dict[str, Any]) -> "CausalGraph":
        graph = cls()
        for node_data in payload.get("nodes", []):
            node = CausalNode(**node_data)
            graph.nodes[node.node_id] = node
        for edge_data in payload.get("edges", []):
            edge = CausalEdge(**edge_data)
            graph.nodes.setdefault(edge.cause, CausalNode(edge.cause))
            graph.nodes.setdefault(edge.effect, CausalNode(edge.effect))
            graph.edges[edge.key] = edge
        return graph


class CausalInferenceEngine:
    """Finds and scores direct and multi-hop causal support."""

    def __init__(self, graph: CausalGraph) -> None:
        self.graph = graph

    def infer(
        self,
        cause: str | None,
        effect: str,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        paths = self.graph.find_causal_paths(cause, effect, max_depth=max_depth)
        best = paths[0] if paths else None
        return {
            "system": "causal_inference_engine",
            "cause": cause,
            "effect": effect,
            "causal_support": best is not None,
            "causal_confidence": best.confidence if best else 0.0,
            "best_path": best.as_dict() if best else {},
            "paths": [path.as_dict() for path in paths],
        }


class CounterfactualSimulator:
    """Simulates graph impact when a cause is removed or weakened."""

    def __init__(self, graph: CausalGraph) -> None:
        self.graph = graph

    def analyze(self, removed_cause: str, max_depth: int = 5) -> dict[str, Any]:
        removed_cause = _clean_identifier(removed_cause, "removed_cause")
        adjacent = self.graph.adjacency()
        impacted: dict[str, dict[str, Any]] = {}
        queue: deque[tuple[str, float, list[str]]] = deque(
            [(removed_cause, 1.0, [removed_cause])]
        )
        visited: set[str] = set()

        while queue:
            current, inherited_confidence, lineage = queue.popleft()
            if len(lineage) > max_depth + 1 or current in visited:
                continue
            visited.add(current)
            for edge in adjacent.get(current, []):
                impact = clamp(inherited_confidence * edge.confidence)
                previous = impacted.get(edge.effect, {})
                if impact > previous.get("impact_score", 0.0):
                    impacted[edge.effect] = {
                        "effect": edge.effect,
                        "impact_score": impact,
                        "prediction": (
                            "disappears"
                            if current == removed_cause and impact >= 0.65
                            else "weakens"
                        ),
                        "lineage": [*lineage, edge.effect],
                        "supporting_edge": edge.as_dict(),
                    }
                queue.append((edge.effect, impact, [*lineage, edge.effect]))

        impact_score = clamp(
            sum(item["impact_score"] for item in impacted.values())
            / max(len(impacted), 1)
        )
        return {
            "system": "counterfactual_simulator",
            "removed_cause": removed_cause,
            "counterfactual_impact_score": impact_score,
            "impacted_effects": list(impacted.values()),
            "causal_support_lost": [
                item["effect"]
                for item in impacted.values()
                if item["prediction"] == "disappears"
            ],
            "causal_support_weakened": [
                item["effect"]
                for item in impacted.values()
                if item["prediction"] == "weakens"
            ],
        }


class CausalConflictDetector:
    """Detects negation conflicts and declared ontology violations."""

    def __init__(
        self,
        graph: CausalGraph,
        ontology: dict[str, Any] | None = None,
    ) -> None:
        self.graph = graph
        self.ontology = dict(ontology or {})

    def detect(self) -> dict[str, Any]:
        by_cause: dict[str, list[CausalEdge]] = defaultdict(list)
        for edge in self.graph.edges.values():
            by_cause[edge.cause].append(edge)

        conflicts: list[dict[str, Any]] = []
        for cause, edges in by_cause.items():
            seen: dict[str, CausalEdge] = {}
            negated: dict[str, CausalEdge] = {}
            for edge in edges:
                normal = _normal_form(edge.effect)
                if _is_negated(edge.effect):
                    negated[normal] = edge
                else:
                    seen[normal] = edge
            for normal, positive_edge in seen.items():
                negative_edge = negated.get(normal)
                if negative_edge:
                    conflicts.append({
                        "type": "DIRECT_NEGATION",
                        "cause": cause,
                        "effect": positive_edge.effect,
                        "conflicting_effect": negative_edge.effect,
                        "severity": clamp(
                            (
                                positive_edge.confidence
                                + negative_edge.confidence
                            )
                            / 2.0
                        ),
                    })

        for edge in self.graph.edges.values():
            violation = self._ontology_violation(edge)
            if violation:
                conflicts.append(violation)

        conflict_pressure = clamp(
            sum(item["severity"] for item in conflicts)
            / max(len(self.graph.edges), 1)
        )
        return {
            "system": "causal_conflict_detector",
            "conflict_count": len(conflicts),
            "conflict_pressure": conflict_pressure,
            "causal_conflicts_detected": bool(conflicts),
            "conflicts": conflicts,
        }

    def _ontology_violation(self, edge: CausalEdge) -> dict[str, Any] | None:
        if edge.metadata.get("violates_ontology") is True:
            return {
                "type": "DECLARED_ONTOLOGY_VIOLATION",
                "cause": edge.cause,
                "effect": edge.effect,
                "severity": edge.confidence,
                "details": edge.metadata.get("ontology_reason", ""),
            }

        blocked = set(self.ontology.get("forbidden_effects", {}).get(edge.cause, []))
        if edge.effect in blocked:
            return {
                "type": "FORBIDDEN_EFFECT",
                "cause": edge.cause,
                "effect": edge.effect,
                "severity": edge.confidence,
                "details": "effect violates known ontology",
            }
        return None


class CausalGraphEngineV2:
    """Production runtime facade for persistent causal graph cognition."""

    def __init__(
        self,
        graph_path: str | Path = DEFAULT_GRAPH_PATH,
        ontology: dict[str, Any] | None = None,
        autosave: bool = True,
    ) -> None:
        self.graph_path = Path(graph_path)
        self.ontology = dict(ontology or {})
        self.autosave = bool(autosave)
        self.graph = CausalGraph()
        self.import_graph(self.graph_path, missing_ok=True)

    def add_node(
        self,
        node_id: str,
        node_type: str = "concept",
        label: str = "",
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> CausalNode:
        node = self.graph.add_node(
            node_id=node_id,
            node_type=node_type,
            label=label,
            confidence=confidence,
            metadata=metadata,
        )
        self._persist_if_needed()
        return node

    def add_edge(
        self,
        cause: str,
        effect: str,
        confidence: float = 0.5,
        support_count: int = 1,
        contradiction_count: int = 0,
        stability: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CausalEdge:
        edge = self.graph.add_edge(
            cause=cause,
            effect=effect,
            confidence=confidence,
            support_count=support_count,
            contradiction_count=contradiction_count,
            stability=stability,
            metadata=metadata,
        )
        self._persist_if_needed()
        return edge

    def remove_edge(self, cause: str, effect: str) -> CausalEdge | None:
        edge = self.graph.remove_edge(cause, effect)
        self._persist_if_needed()
        return edge

    def update_edge_confidence(
        self,
        cause: str,
        effect: str,
        confidence: float | None = None,
        support_delta: int = 0,
        contradiction_delta: int = 0,
        stability: float | None = None,
    ) -> CausalEdge:
        edge = self.graph.update_edge_confidence(
            cause=cause,
            effect=effect,
            confidence=confidence,
            support_delta=support_delta,
            contradiction_delta=contradiction_delta,
            stability=stability,
        )
        self._persist_if_needed()
        return edge

    def find_causal_paths(
        self,
        cause: str | None,
        effect: str,
        max_depth: int = 5,
        minimum_confidence: float = 0.0,
    ) -> dict[str, Any]:
        paths = self.graph.find_causal_paths(
            cause=cause,
            effect=effect,
            max_depth=max_depth,
            minimum_confidence=minimum_confidence,
        )
        return {
            "system": "causal_graph_engine_v2",
            "report_type": CAUSAL_PATH_REPORT,
            "cause": cause,
            "effect": effect,
            "path_count": len(paths),
            "best_path": paths[0].as_dict() if paths else {},
            "paths": [path.as_dict() for path in paths],
        }

    def validate_candidate(
        self,
        candidate: str | dict[str, Any],
        required_path: Iterable[str] | None = None,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        candidate_data = self._candidate_data(candidate)
        effect = candidate_data["effect"]
        cause = candidate_data.get("cause")
        expected_path = list(required_path or candidate_data.get("required_path") or [])

        if expected_path:
            path = self._path_from_required_nodes(expected_path)
            paths = [path] if path else []
        else:
            paths = self.graph.find_causal_paths(cause, effect, max_depth=max_depth)

        best = paths[0] if paths else None
        conflict_report = self.detect_conflicts()
        conflict_penalty = conflict_report["conflict_pressure"] * 0.20
        causal_confidence = best.confidence if best else 0.0
        path_completeness = 1.0 if best else 0.0
        alignment_score = clamp(
            causal_confidence * 0.72
            + path_completeness * 0.18
            + (1.0 - conflict_report["conflict_pressure"]) * 0.10
            - conflict_penalty
        )
        return {
            "system": "causal_graph_engine_v2",
            "report_type": CAUSAL_ALIGNMENT_REPORT,
            "candidate": candidate_data.get("candidate"),
            "cause": cause,
            "effect": effect,
            "alignment_score": alignment_score,
            "causal_support": best is not None,
            "causal_confidence": causal_confidence,
            "path_completeness": path_completeness,
            "causal_graph_alignment": alignment_score,
            "truth_governance_action": (
                "ALLOW_TRUTH_REVIEW"
                if alignment_score >= 0.85
                else "HOLD_FOR_CAUSAL_REVIEW"
            ),
            "best_path": best.as_dict() if best else {},
            "causal_conflict_report": conflict_report,
        }

    def counterfactual_analysis(
        self,
        removed_cause: str,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        report = CounterfactualSimulator(self.graph).analyze(
            removed_cause=removed_cause,
            max_depth=max_depth,
        )
        report["report_type"] = COUNTERFACTUAL_REPORT
        return report

    def detect_conflicts(self) -> dict[str, Any]:
        report = CausalConflictDetector(self.graph, self.ontology).detect()
        report["report_type"] = CAUSAL_CONFLICT_REPORT
        return report

    def reinforce_path(
        self,
        path: Iterable[str] | CausalPath,
        amount: float = 0.04,
    ) -> dict[str, Any]:
        edges = self._edges_from_path(path, create_missing=True)
        for edge in edges:
            edge.reinforce(amount=amount)
        self._persist_if_needed()
        return {
            "system": "causal_graph_engine_v2",
            "reinforced": True,
            "edge_count": len(edges),
            "path": [edge.as_dict() for edge in edges],
        }

    def decay_path(
        self,
        path: Iterable[str] | CausalPath | None = None,
        rate: float = 0.02,
    ) -> dict[str, Any]:
        edges = (
            self._edges_from_path(path, create_missing=False)
            if path is not None
            else list(self.graph.edges.values())
        )
        for edge in edges:
            edge.decay(rate=rate)
        self._persist_if_needed()
        return {
            "system": "causal_graph_engine_v2",
            "decayed": True,
            "edge_count": len(edges),
            "decay_rate": clamp(rate, 0.0, 0.25),
        }

    def generate_explanation(
        self,
        concept: str,
        cause: str | None = None,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        paths = self.graph.find_causal_paths(cause, concept, max_depth=max_depth)
        best = paths[0] if paths else None
        observed = best.support_count if best else 0
        why = []
        if best:
            for edge in best.edges:
                why.append(f"{edge.cause} -> {edge.effect}")
            why.append(f"observed in {observed} tasks")
        return {
            "system": "causal_graph_engine_v2",
            "concept": concept,
            "why": why,
            "causal_confidence": best.confidence if best else 0.0,
            "causal_support": best is not None,
            "explanation_path": best.nodes if best else [],
            "best_path": best.as_dict() if best else {},
        }

    def export_graph(self, destination: str | Path | None = None) -> dict[str, Any]:
        payload = self.graph.export_graph()
        if destination is not None:
            self._write_payload(Path(destination), payload)
        return {
            "system": "causal_graph_engine_v2",
            "report_type": CAUSAL_REPORT,
            "graph_path": str(destination or self.graph_path),
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "graph": payload,
        }

    def import_graph(
        self,
        source: str | Path | dict[str, Any],
        missing_ok: bool = False,
    ) -> dict[str, Any]:
        if isinstance(source, dict):
            payload = source
        else:
            path = Path(source)
            if not path.exists():
                if missing_ok:
                    return {
                        "system": "causal_graph_engine_v2",
                        "imported": False,
                        "reason": "graph file missing",
                    }
                raise FileNotFoundError(path)
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)

        self.graph = CausalGraph.import_graph(payload)
        return {
            "system": "causal_graph_engine_v2",
            "imported": True,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
        }

    def build_graph_from_observations(
        self,
        observations: Iterable[dict[str, Any]],
    ) -> dict[str, Any]:
        """Ingest runtime observations from context or truth engines."""

        added_edges = 0
        for observation in observations or []:
            cause = observation.get("cause") or observation.get("source")
            effect = observation.get("effect") or observation.get("concept")
            if not cause or not effect:
                continue
            self.add_edge(
                cause=cause,
                effect=effect,
                confidence=observation.get(
                    "causal_confidence",
                    observation.get("confidence", 0.6),
                ),
                metadata={"observation": observation},
            )
            added_edges += 1
        self._persist_if_needed()
        return {
            "system": "causal_graph_engine_v2",
            "added_edges": added_edges,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
        }

    def _candidate_data(self, candidate: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(candidate, dict):
            effect = (
                candidate.get("effect")
                or candidate.get("concept")
                or candidate.get("truth_candidate")
                or candidate.get("candidate")
            )
            data = dict(candidate)
            data["effect"] = _clean_identifier(effect, "candidate effect")
            data["candidate"] = data.get("candidate", data["effect"])
            data["cause"] = data.get("cause") or data.get("root_cause")
            return data
        effect = _clean_identifier(candidate, "candidate")
        return {"candidate": effect, "effect": effect, "cause": None}

    def _path_from_required_nodes(
        self,
        required_nodes: list[str],
    ) -> CausalPath | None:
        if len(required_nodes) < 2:
            return None
        edges: list[CausalEdge] = []
        for cause, effect in zip(required_nodes, required_nodes[1:]):
            edge = self.graph.edges.get((cause, effect))
            if edge is None:
                return None
            edges.append(edge)
        return CausalPath(nodes=required_nodes, edges=edges)

    def _edges_from_path(
        self,
        path: Iterable[str] | CausalPath | None,
        create_missing: bool,
    ) -> list[CausalEdge]:
        if path is None:
            return []
        if isinstance(path, CausalPath):
            return list(path.edges)
        nodes = list(path)
        if len(nodes) < 2:
            return []
        edges = []
        for cause, effect in zip(nodes, nodes[1:]):
            edge = self.graph.edges.get((cause, effect))
            if edge is None and create_missing:
                edge = self.graph.add_edge(cause, effect, confidence=0.55)
            if edge is not None:
                edges.append(edge)
        return edges

    def _persist_if_needed(self) -> None:
        if self.autosave:
            self._write_payload(self.graph_path, self.graph.export_graph())

    def _write_payload(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)


__all__ = [
    "CausalNode",
    "CausalEdge",
    "CausalGraph",
    "CausalPath",
    "CausalInferenceEngine",
    "CounterfactualSimulator",
    "CausalConflictDetector",
    "CausalGraphEngineV2",
]
