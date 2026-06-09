from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core.epistemic_models import clamp


DEFAULT_DEPENDENCY_GRAPH_PATH = Path("memory") / "dependency_graph.json"
DEPENDENCY_GRAPH_REPORT = "DEPENDENCY GRAPH REPORT"
DEPENDENCY_PATH_REPORT = "DEPENDENCY PATH REPORT"
DEPENDENCY_COHERENCE_REPORT = "DEPENDENCY COHERENCE REPORT"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identifier(value: Any, name: str) -> str:
    identifier = str(value or "").strip()
    if not identifier:
        raise ValueError(f"{name} must be a non-empty string")
    return identifier


@dataclass
class DependencyNode:
    """A concept, context, truth, or dependency factor in the graph."""

    node_id: str
    node_type: str = "concept"
    label: str = ""
    confidence: float = 0.5
    created_at: str = field(default_factory=_timestamp)
    last_seen: str = field(default_factory=_timestamp)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.node_id = _identifier(self.node_id, "node_id")
        self.node_type = str(self.node_type or "concept").strip().lower()
        self.label = str(self.label or self.node_id).strip()
        self.confidence = clamp(self.confidence)
        self.created_at = str(self.created_at or _timestamp())
        self.last_seen = str(self.last_seen or _timestamp())
        self.metadata = dict(self.metadata or {})

    def merge(self, other: "DependencyNode") -> "DependencyNode":
        self.confidence = max(self.confidence, other.confidence)
        self.last_seen = other.last_seen or _timestamp()
        self.metadata.update(other.metadata)
        return self

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyEdge:
    """Directed dependency relation with support, contradiction, and stability."""

    source: str
    target: str
    relation: str = "depends_on"
    confidence: float = 0.5
    support_count: int = 1
    contradiction_count: int = 0
    transfer_success_count: int = 0
    transfer_failure_count: int = 0
    stability: float = 0.5
    last_observed: str = field(default_factory=_timestamp)
    dependency_type: str = "observational_dependency"
    required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source = _identifier(self.source, "source")
        self.target = _identifier(self.target, "target")
        self.relation = str(self.relation or "depends_on").strip()
        self.confidence = clamp(self.confidence)
        self.support_count = max(int(self.support_count or 0), 0)
        self.contradiction_count = max(int(self.contradiction_count or 0), 0)
        self.transfer_success_count = max(
            int(self.transfer_success_count or 0),
            0,
        )
        self.transfer_failure_count = max(
            int(self.transfer_failure_count or 0),
            0,
        )
        self.stability = clamp(self.stability)
        self.last_observed = str(self.last_observed or _timestamp())
        self.dependency_type = str(
            self.dependency_type or "observational_dependency"
        ).strip()
        self.required = bool(self.required)
        self.metadata = dict(self.metadata or {})

    @property
    def key(self) -> tuple[str, str, str]:
        return self.source, self.target, self.relation

    @property
    def contradiction_risk(self) -> float:
        total = self.support_count + self.contradiction_count
        if total == 0:
            return 0.0
        return clamp(self.contradiction_count / total)

    @property
    def transfer_success_rate(self) -> float:
        total = self.transfer_success_count + self.transfer_failure_count
        if total == 0:
            return 0.5
        return clamp(self.transfer_success_count / total)

    @property
    def dependency_confidence(self) -> float:
        evidence_volume = clamp(
            (self.support_count + self.contradiction_count) / 5.0
        )
        support_ratio = (
            self.support_count
            / max(self.support_count + self.contradiction_count, 1)
        )
        required_weight = 0.82 if self.required else 0.70
        return clamp(
            (
                self.confidence
                + support_ratio
                + evidence_volume
                + self.stability
                + self.transfer_success_rate
                + (1.0 - self.contradiction_risk)
                + required_weight
            )
            / 7.0
        )

    def reinforce(
        self,
        confidence: float | None = None,
        transfer_success: bool | None = None,
    ) -> "DependencyEdge":
        self.support_count += 1
        if confidence is not None:
            self.confidence = clamp((self.confidence + clamp(confidence)) / 2.0)
        else:
            self.confidence = clamp(self.confidence + 0.04 * (1.0 - self.confidence))
        if transfer_success is True:
            self.transfer_success_count += 1
        elif transfer_success is False:
            self.transfer_failure_count += 1
        self.stability = clamp(self.stability + 0.035)
        self.last_observed = _timestamp()
        return self

    def contradict(self, confidence: float | None = None) -> "DependencyEdge":
        self.contradiction_count += 1
        if confidence is not None:
            self.confidence = clamp((self.confidence + clamp(confidence)) / 2.0)
        self.confidence = clamp(self.confidence - 0.05)
        self.stability = clamp(self.stability - 0.04)
        self.last_observed = _timestamp()
        return self

    def decay(self, rate: float = 0.015) -> "DependencyEdge":
        decay_rate = clamp(rate, 0.0, 0.25)
        self.confidence = clamp(self.confidence * (1.0 - decay_rate))
        self.stability = clamp(self.stability * (1.0 - decay_rate * 0.75))
        return self

    def as_dict(self) -> dict[str, Any]:
        report = asdict(self)
        report["contradiction_risk"] = self.contradiction_risk
        report["transfer_success_rate"] = self.transfer_success_rate
        report["dependency_confidence"] = self.dependency_confidence
        return report


@dataclass
class DependencyPath:
    """A multi-hop dependency path from a concept to a supporting factor."""

    nodes: list[str]
    edges: list[DependencyEdge]

    @property
    def depth(self) -> int:
        return len(self.edges)

    @property
    def confidence(self) -> float:
        if not self.edges:
            return 0.0
        product = 1.0
        stability = 0.0
        for edge in self.edges:
            product *= max(edge.dependency_confidence, 0.0001)
            stability += edge.stability
        propagated = product ** (1.0 / len(self.edges))
        depth_penalty = 0.95 ** max(len(self.edges) - 1, 0)
        return clamp(
            (propagated * 0.82 + (stability / len(self.edges)) * 0.18)
            * depth_penalty
        )

    @property
    def support_count(self) -> int:
        if not self.edges:
            return 0
        return min(edge.support_count for edge in self.edges)

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": list(self.nodes),
            "edges": [edge.as_dict() for edge in self.edges],
            "depth": self.depth,
            "confidence": self.confidence,
            "support_count": self.support_count,
        }


class DependencyGraph:
    """Persistent directed graph for concept dependency coherence."""

    def __init__(self) -> None:
        self.nodes: dict[str, DependencyNode] = {}
        self.edges: dict[tuple[str, str, str], DependencyEdge] = {}

    def add_node(
        self,
        node_id: str,
        node_type: str = "concept",
        label: str = "",
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> DependencyNode:
        node = DependencyNode(
            node_id=node_id,
            node_type=node_type,
            label=label or node_id,
            confidence=confidence,
            metadata=metadata or {},
            last_seen=_timestamp(),
        )
        if node.node_id in self.nodes:
            return self.nodes[node.node_id].merge(node)
        self.nodes[node.node_id] = node
        return node

    def add_dependency(
        self,
        source: str,
        target: str,
        relation: str = "depends_on",
        confidence: float = 0.5,
        dependency_type: str = "observational_dependency",
        required: bool = True,
        supported: bool = True,
        transfer_success: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DependencyEdge:
        source = _identifier(source, "source")
        target = _identifier(target, "target")
        self.add_node(source, node_type="concept")
        self.add_node(target, node_type="dependency")
        key = (source, target, relation)
        if key in self.edges:
            edge = self.edges[key]
            edge.metadata.update(metadata or {})
            if supported:
                edge.reinforce(confidence=confidence, transfer_success=transfer_success)
            else:
                edge.contradict(confidence=confidence)
            return edge

        edge = DependencyEdge(
            source=source,
            target=target,
            relation=relation,
            confidence=confidence,
            support_count=1 if supported else 0,
            contradiction_count=0 if supported else 1,
            transfer_success_count=1 if transfer_success is True else 0,
            transfer_failure_count=1 if transfer_success is False else 0,
            stability=confidence,
            dependency_type=dependency_type,
            required=required,
            metadata=metadata or {},
        )
        self.edges[key] = edge
        return edge

    def remove_dependency(
        self,
        source: str,
        target: str,
        relation: str | None = None,
    ) -> list[DependencyEdge]:
        removed = []
        retained = {}
        for key, edge in self.edges.items():
            matches = (
                edge.source == source
                and edge.target == target
                and (relation is None or edge.relation == relation)
            )
            if matches:
                removed.append(edge)
            else:
                retained[key] = edge
        self.edges = retained
        return removed

    def adjacency(self) -> dict[str, list[DependencyEdge]]:
        adjacent: dict[str, list[DependencyEdge]] = defaultdict(list)
        for edge in self.edges.values():
            adjacent[edge.source].append(edge)
        return adjacent

    def incoming(self) -> dict[str, list[DependencyEdge]]:
        incoming: dict[str, list[DependencyEdge]] = defaultdict(list)
        for edge in self.edges.values():
            incoming[edge.target].append(edge)
        return incoming

    def dependencies_for(self, concept: str) -> list[DependencyEdge]:
        return [
            edge
            for edge in self.edges.values()
            if edge.source == concept
        ]

    def find_dependency_paths(
        self,
        source: str,
        target: str | None = None,
        max_depth: int = 4,
        minimum_confidence: float = 0.0,
    ) -> list[DependencyPath]:
        source = _identifier(source, "source")
        if source not in self.nodes:
            return []
        max_depth = max(int(max_depth or 1), 1)
        adjacent = self.adjacency()
        queue: deque[tuple[str, list[str], list[DependencyEdge]]] = deque(
            [(source, [source], [])]
        )
        paths: list[DependencyPath] = []

        while queue:
            current, nodes, edges = queue.popleft()
            if len(edges) > max_depth:
                continue
            if edges and (target is None or current == target):
                path = DependencyPath(nodes=nodes, edges=edges)
                if path.confidence >= minimum_confidence:
                    paths.append(path)
            for edge in adjacent.get(current, []):
                if edge.target in nodes:
                    continue
                queue.append((edge.target, [*nodes, edge.target], [*edges, edge]))

        paths.sort(key=lambda item: (item.confidence, -item.depth), reverse=True)
        return paths

    def export_graph(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "generated_at": _timestamp(),
            "nodes": [node.as_dict() for node in self.nodes.values()],
            "edges": [edge.as_dict() for edge in self.edges.values()],
        }

    @classmethod
    def import_graph(cls, payload: dict[str, Any]) -> "DependencyGraph":
        graph = cls()
        for node_data in payload.get("nodes", []):
            node = DependencyNode(**node_data)
            graph.nodes[node.node_id] = node
        for edge_data in payload.get("edges", []):
            clean_edge_data = dict(edge_data)
            clean_edge_data.pop("contradiction_risk", None)
            clean_edge_data.pop("transfer_success_rate", None)
            clean_edge_data.pop("dependency_confidence", None)
            edge = DependencyEdge(**clean_edge_data)
            graph.nodes.setdefault(edge.source, DependencyNode(edge.source))
            graph.nodes.setdefault(
                edge.target,
                DependencyNode(edge.target, node_type="dependency"),
            )
            graph.edges[edge.key] = edge
        return graph


class DependencyGraphEngine:
    """Runtime facade for persistent dependency discovery and coherence."""

    def __init__(
        self,
        graph_path: str | Path = DEFAULT_DEPENDENCY_GRAPH_PATH,
        autosave: bool = True,
    ) -> None:
        self.graph_path = Path(graph_path)
        self.autosave = bool(autosave)
        self.graph = DependencyGraph()
        self.import_graph(self.graph_path, missing_ok=True)

    def add_node(
        self,
        node_id: str,
        node_type: str = "concept",
        label: str = "",
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> DependencyNode:
        node = self.graph.add_node(
            node_id=node_id,
            node_type=node_type,
            label=label,
            confidence=confidence,
            metadata=metadata,
        )
        self._persist_if_needed()
        return node

    def add_dependency(
        self,
        source: str,
        target: str,
        relation: str = "depends_on",
        confidence: float = 0.5,
        dependency_type: str = "observational_dependency",
        required: bool = True,
        supported: bool = True,
        transfer_success: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DependencyEdge:
        edge = self.graph.add_dependency(
            source=source,
            target=target,
            relation=relation,
            confidence=confidence,
            dependency_type=dependency_type,
            required=required,
            supported=supported,
            transfer_success=transfer_success,
            metadata=metadata,
        )
        self._persist_if_needed()
        return edge

    def remove_dependency(
        self,
        source: str,
        target: str,
        relation: str | None = None,
    ) -> list[DependencyEdge]:
        removed = self.graph.remove_dependency(source, target, relation)
        self._persist_if_needed()
        return removed

    def update_dependency_confidence(
        self,
        source: str,
        target: str,
        relation: str = "depends_on",
        confidence: float | None = None,
        support_delta: int = 0,
        contradiction_delta: int = 0,
        stability: float | None = None,
    ) -> DependencyEdge:
        key = (source, target, relation)
        edge = self.graph.edges.get(key)
        if edge is None:
            edge = self.graph.add_dependency(
                source,
                target,
                relation=relation,
                confidence=confidence or 0.5,
            )
        if confidence is not None:
            edge.confidence = clamp(confidence)
        edge.support_count = max(edge.support_count + int(support_delta), 0)
        edge.contradiction_count = max(
            edge.contradiction_count + int(contradiction_delta),
            0,
        )
        if stability is not None:
            edge.stability = clamp(stability)
        edge.last_observed = _timestamp()
        self._persist_if_needed()
        return edge

    def ingest_dependencies(
        self,
        dependencies: Iterable[dict[str, Any]],
        default_source: str | None = None,
    ) -> dict[str, Any]:
        ingested = 0
        for dependency in list(dependencies or []):
            source = (
                dependency.get("source")
                or dependency.get("concept")
                or default_source
            )
            target = dependency.get("target") or dependency.get("dependency")
            if not source or not target:
                continue
            validation = dependency.get("validation", {})
            supported = dependency.get(
                "supported",
                validation.get("validated", True),
            )
            confidence = dependency.get(
                "confidence",
                dependency.get("score", validation.get("score", 0.6)),
            )
            self.graph.add_dependency(
                source=source,
                target=target,
                relation=dependency.get("relation", "depends_on"),
                confidence=confidence,
                dependency_type=dependency.get(
                    "dependency_type",
                    "observational_dependency",
                ),
                required=dependency.get("required", True),
                supported=bool(supported),
                transfer_success=dependency.get("transfer_success"),
                metadata={"dependency": dependency},
            )
            ingested += 1
        self._persist_if_needed()
        return {
            "system": "dependency_graph_engine",
            "ingested_dependencies": ingested,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
        }

    def find_dependency_paths(
        self,
        source: str,
        target: str | None = None,
        max_depth: int = 4,
        minimum_confidence: float = 0.0,
    ) -> dict[str, Any]:
        paths = self.graph.find_dependency_paths(
            source=source,
            target=target,
            max_depth=max_depth,
            minimum_confidence=minimum_confidence,
        )
        return {
            "system": "dependency_graph_engine",
            "report_type": DEPENDENCY_PATH_REPORT,
            "source": source,
            "target": target,
            "path_count": len(paths),
            "best_path": paths[0].as_dict() if paths else {},
            "paths": [path.as_dict() for path in paths],
        }

    def validate_dependency_coherence(
        self,
        concept: str,
        required_dependencies: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        concept = _identifier(concept, "concept")
        direct_edges = self.graph.dependencies_for(concept)
        required = set(required_dependencies or [])
        if not required:
            required = {
                edge.target
                for edge in direct_edges
                if edge.required
            }

        validated = [
            edge
            for edge in direct_edges
            if edge.dependency_confidence >= 0.78
            and edge.contradiction_risk < 0.25
        ]
        provisional = [
            edge
            for edge in direct_edges
            if edge not in validated
            and edge.dependency_confidence >= 0.55
            and edge.contradiction_risk < 0.45
        ]
        blocked = [
            edge
            for edge in direct_edges
            if edge.contradiction_risk >= 0.45
            or edge.dependency_confidence < 0.55
        ]
        observed_targets = {edge.target for edge in direct_edges}
        missing = sorted(required - observed_targets)
        path_bonus = self._path_bonus(concept)
        confidence_average = (
            sum(edge.dependency_confidence for edge in direct_edges)
            / max(len(direct_edges), 1)
        )
        validation_ratio = len(validated) / max(len(required or direct_edges), 1)
        contradiction_resistance = clamp(
            1.0
            - (
                sum(edge.contradiction_risk for edge in direct_edges)
                / max(len(direct_edges), 1)
            )
        )
        missing_penalty = clamp(len(missing) / max(len(required), 1)) * 0.18
        dependency_coherence = clamp(
            confidence_average * 0.44
            + validation_ratio * 0.26
            + contradiction_resistance * 0.20
            + path_bonus * 0.10
            - missing_penalty
        )
        status = (
            "DEPENDENCY_GRAPH_VALIDATED"
            if dependency_coherence >= 0.80 and not blocked and not missing
            else "DEPENDENCY_GRAPH_REVIEW_REQUIRED"
            if dependency_coherence >= 0.62
            else "DEPENDENCY_GRAPH_BLOCKED"
        )
        return {
            "system": "dependency_graph_engine",
            "report_type": DEPENDENCY_COHERENCE_REPORT,
            "concept": concept,
            "dependency_coherence": dependency_coherence,
            "dependency_confidence": confidence_average,
            "dependency_path_support": path_bonus,
            "validated_dependencies": [edge.as_dict() for edge in validated],
            "provisional_dependencies": [edge.as_dict() for edge in provisional],
            "blocked_dependencies": [edge.as_dict() for edge in blocked],
            "missing_dependencies": missing,
            "status": status,
            "recommended_action": (
                "USE_FOR_TRUTH_PROMOTION"
                if status == "DEPENDENCY_GRAPH_VALIDATED"
                else "COLLECT_DEPENDENCY_EVIDENCE"
            ),
            "why": self._why(
                direct_edges=direct_edges,
                validated=validated,
                missing=missing,
                dependency_coherence=dependency_coherence,
            ),
        }

    def reinforce_dependency_path(
        self,
        path: Iterable[str] | DependencyPath,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        edges = self._edges_from_path(path, create_missing=True)
        for edge in edges:
            edge.reinforce(confidence=confidence, transfer_success=True)
        self._persist_if_needed()
        return {
            "system": "dependency_graph_engine",
            "reinforced": True,
            "edge_count": len(edges),
            "edges": [edge.as_dict() for edge in edges],
        }

    def decay_dependency_graph(
        self,
        rate: float = 0.015,
        path: Iterable[str] | DependencyPath | None = None,
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
            "system": "dependency_graph_engine",
            "decayed": True,
            "edge_count": len(edges),
            "decay_rate": clamp(rate, 0.0, 0.25),
        }

    def generate_dependency_report(
        self,
        concept: str,
        required_dependencies: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        coherence = self.validate_dependency_coherence(
            concept,
            required_dependencies=required_dependencies,
        )
        paths = self.find_dependency_paths(concept)
        return {
            "system": "dependency_graph_engine",
            "report_type": DEPENDENCY_GRAPH_REPORT,
            "concept": concept,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "coherence": coherence,
            "paths": paths,
        }

    def export_graph(self, destination: str | Path | None = None) -> dict[str, Any]:
        payload = self.graph.export_graph()
        if destination is not None:
            self._write(Path(destination), payload)
        return {
            "system": "dependency_graph_engine",
            "report_type": DEPENDENCY_GRAPH_REPORT,
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
                        "system": "dependency_graph_engine",
                        "imported": False,
                        "reason": "graph file missing",
                    }
                raise FileNotFoundError(path)
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        self.graph = DependencyGraph.import_graph(payload)
        return {
            "system": "dependency_graph_engine",
            "imported": True,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
        }

    def _path_bonus(self, concept: str) -> float:
        paths = self.graph.find_dependency_paths(concept, max_depth=4)
        if not paths:
            return 0.0
        return clamp(sum(path.confidence for path in paths[:3]) / min(len(paths), 3))

    def _why(
        self,
        direct_edges: list[DependencyEdge],
        validated: list[DependencyEdge],
        missing: list[str],
        dependency_coherence: float,
    ) -> list[str]:
        why = [
            f"{len(validated)} dependency links validated",
            f"{len(direct_edges)} dependency links observed",
        ]
        if missing:
            why.append("missing dependencies: " + ", ".join(missing))
        if dependency_coherence >= 0.80:
            why.append("dependency coherence ready for promotion")
        else:
            why.append("dependency coherence requires more evidence")
        return why

    def _edges_from_path(
        self,
        path: Iterable[str] | DependencyPath,
        create_missing: bool,
    ) -> list[DependencyEdge]:
        if isinstance(path, DependencyPath):
            return list(path.edges)
        nodes = list(path or [])
        edges = []
        for source, target in zip(nodes, nodes[1:]):
            edge = self.graph.edges.get((source, target, "depends_on"))
            if edge is None and create_missing:
                edge = self.graph.add_dependency(source, target, confidence=0.60)
            if edge is not None:
                edges.append(edge)
        return edges

    def _persist_if_needed(self) -> None:
        if self.autosave:
            self._write(self.graph_path, self.graph.export_graph())

    def _write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)


__all__ = [
    "DependencyNode",
    "DependencyEdge",
    "DependencyPath",
    "DependencyGraph",
    "DependencyGraphEngine",
]
