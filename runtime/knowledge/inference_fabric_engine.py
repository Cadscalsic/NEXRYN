"""Inference Fabric Engine.

Inference Fabric is a lightweight reasoning layer above Knowledge Fabric. It
does not own meaning, store relationships, or create new facts. It traverses
existing Fabric relations to produce dynamic inference paths for downstream
mental model discovery.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


INFERENCE_GOALS = {
    "prediction",
    "planning",
    "transfer",
    "explanation",
    "generalization",
    "diagnosis",
    "mental_model_discovery",
}

RELATION_GOAL_WEIGHT = {
    "Predicts": {"prediction": 1.0, "planning": 0.75},
    "Transfers": {"transfer": 1.0, "planning": 0.7, "mental_model_discovery": 0.65},
    "Explains": {"explanation": 1.0, "diagnosis": 0.85, "mental_model_discovery": 0.7},
    "Generalizes": {"generalization": 1.0, "mental_model_discovery": 0.8, "transfer": 0.65},
    "Bridges": {"transfer": 0.8, "planning": 0.65, "mental_model_discovery": 0.75},
    "Supports": {"explanation": 0.65, "diagnosis": 0.6},
    "Depends On": {"planning": 0.55, "explanation": 0.5},
    "Influences": {"prediction": 0.75, "planning": 0.7},
    "Constrains": {"planning": 0.65, "diagnosis": 0.6},
    "Complements": {"transfer": 0.45, "mental_model_discovery": 0.45},
}


@dataclass(frozen=True)
class InferencePath:
    inference_path_id: str
    source_entity_id: str
    target_entity_id: str
    inference_goal: str
    entity_path: list[str] = field(default_factory=list)
    relation_path: list[str] = field(default_factory=list)
    relation_types: list[str] = field(default_factory=list)
    path_confidence: float = 0.0
    path_strength: float = 0.0
    path_depth: int = 0
    cross_domain_steps: int = 0
    dynamic: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class InferenceFabricEngine:
    """Build transient inference paths over an existing Knowledge Fabric."""

    system_name = "inference_fabric_engine"

    def build_report(
        self,
        *,
        knowledge_fabric_report: Mapping[str, Any],
        source_entity_id: str | None = None,
        target_entity_id: str | None = None,
        inference_goal: str = "mental_model_discovery",
        max_depth: int = 4,
        top_k: int = 10,
    ) -> dict[str, Any]:
        goal = _goal(inference_goal)
        relationships = [
            _relation_view(relation)
            for relation in _list(knowledge_fabric_report.get("Fabric Relationships"))
        ]
        entity_ids = _entity_ids(knowledge_fabric_report, relationships)
        graph = _adjacency(relationships)
        starts = [source_entity_id] if source_entity_id else sorted(entity_ids)
        paths = []
        for start in starts:
            if start not in entity_ids:
                continue
            paths.extend(_walk_paths(
                graph=graph,
                source=str(start),
                target=str(target_entity_id or ""),
                goal=goal,
                max_depth=max(1, int(max_depth or 1)),
            ))
        ranked = sorted(
            paths,
            key=lambda path: (path.path_confidence, path.path_strength, -path.path_depth),
            reverse=True,
        )[: max(1, int(top_k or 1))]
        return {
            "INFERENCE_FABRIC_REPORT": True,
            "system": self.system_name,
            "status": "OPERATIONAL",
            "inference_goal": goal,
            "source_entity_id": source_entity_id or "",
            "target_entity_id": target_entity_id or "",
            "Inference Paths": [path.as_dict() for path in ranked],
            "path_count": len(ranked),
            "candidate_path_count": len(paths),
            "Dynamic Path Statistics": {
                "max_depth": max_depth,
                "average_depth": _average(path.path_depth for path in ranked),
                "average_confidence": _average(path.path_confidence for path in ranked),
                "average_strength": _average(path.path_strength for path in ranked),
                "cross_domain_paths": sum(1 for path in ranked if path.cross_domain_steps > 0),
            },
            "Reasoning Coverage": {
                "reachable_entities": len({entity for path in ranked for entity in path.entity_path}),
                "available_entities": len(entity_ids),
                "coverage_ratio": round(
                    len({entity for path in ranked for entity in path.entity_path})
                    / max(len(entity_ids), 1),
                    4,
                ),
            },
            "Mental Model Preparation": {
                "ready": bool(ranked),
                "path_ids": [path.inference_path_id for path in ranked],
                "entity_paths": [path.entity_path for path in ranked],
                "relation_paths": [path.relation_path for path in ranked],
            },
            "Integration Contracts": {
                "creates_new_memory_system": False,
                "stores_relationships": False,
                "stores_semantic_meaning": False,
                "duplicates_knowledge_fabric": False,
                "creates_new_truth": False,
                "mutates_knowledge_fabric": False,
                "mutates_semantic_memory": False,
                "returns_dynamic_inference_paths": True,
                "returns_ids_for_later_hydration": True,
                "mental_models_consume_inference_paths": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def _walk_paths(
    *,
    graph: Mapping[str, list[dict[str, Any]]],
    source: str,
    target: str,
    goal: str,
    max_depth: int,
) -> list[InferencePath]:
    paths: list[InferencePath] = []
    queue = deque([(source, [source], [], [], [], [])])
    while queue:
        current, entity_path, relation_path, relation_types, confidences, strengths = queue.popleft()
        if len(relation_path) >= max_depth:
            continue
        for relation in graph.get(current, []):
            next_id = relation["target_entity_id"]
            if next_id in entity_path:
                continue
            next_entities = [*entity_path, next_id]
            next_relations = [*relation_path, relation["relation_id"]]
            next_types = [*relation_types, relation["relation_type"]]
            next_confidences = [*confidences, relation["relation_confidence"]]
            next_strengths = [*strengths, _goal_strength(relation, goal)]
            reaches_target = not target or next_id == target
            if reaches_target:
                paths.append(_inference_path(
                    source=source,
                    target=next_id,
                    goal=goal,
                    entity_path=next_entities,
                    relation_path=next_relations,
                    relation_types=next_types,
                    confidences=next_confidences,
                    strengths=next_strengths,
                    cross_domain_steps=sum(1 for rel_id in next_relations if _is_cross_domain_relation(graph, rel_id)),
                ))
            if not target or next_id != target:
                queue.append((next_id, next_entities, next_relations, next_types, next_confidences, next_strengths))
    return paths


def _inference_path(
    *,
    source: str,
    target: str,
    goal: str,
    entity_path: list[str],
    relation_path: list[str],
    relation_types: list[str],
    confidences: list[float],
    strengths: list[float],
    cross_domain_steps: int,
) -> InferencePath:
    confidence = _path_score(confidences)
    strength = _path_score(strengths)
    path_id = _path_id(source, target, goal, relation_path)
    return InferencePath(
        inference_path_id=path_id,
        source_entity_id=source,
        target_entity_id=target,
        inference_goal=goal,
        entity_path=entity_path,
        relation_path=relation_path,
        relation_types=relation_types,
        path_confidence=confidence,
        path_strength=strength,
        path_depth=len(relation_path),
        cross_domain_steps=cross_domain_steps,
    )


def _relation_view(value: Any) -> dict[str, Any]:
    relation = dict(value) if isinstance(value, Mapping) else {}
    scope = dict(relation.get("validity_scope") or {})
    return {
        "relation_id": str(relation.get("relation_id") or ""),
        "source_entity_id": str(relation.get("source_entity_id") or ""),
        "target_entity_id": str(relation.get("target_entity_id") or ""),
        "relation_type": str(relation.get("relation_type") or "Complements"),
        "relation_confidence": _number(relation.get("relation_confidence", 0.0)),
        "relation_strength": _number(relation.get("relation_strength", 0.0)),
        "cross_domain": bool(scope.get("cross_domain", False)),
    }


def _adjacency(relationships: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    graph: dict[str, list[dict[str, Any]]] = {}
    for relation in relationships:
        source = relation["source_entity_id"]
        target = relation["target_entity_id"]
        if source and target:
            graph.setdefault(source, []).append(relation)
            reverse = {
                **relation,
                "source_entity_id": target,
                "target_entity_id": source,
                "relation_id": f"{relation['relation_id']}:reverse",
            }
            graph.setdefault(target, []).append(reverse)
    for edges in graph.values():
        edges.sort(key=lambda rel: (rel["relation_confidence"], rel["relation_strength"]), reverse=True)
    return graph


def _entity_ids(
    report: Mapping[str, Any],
    relationships: list[dict[str, Any]],
) -> set[str]:
    ids = set()
    for relation in relationships:
        ids.add(relation["source_entity_id"])
        ids.add(relation["target_entity_id"])
    for entity in _list(report.get("Fabric Entities")):
        if isinstance(entity, Mapping):
            ids.update(str(item) for item in _list(entity.get("source_entity_ids")))
            ids.update(str(item) for item in _list(entity.get("target_entity_ids")))
    return {item for item in ids if item}


def _goal(value: str) -> str:
    normalized = str(value or "mental_model_discovery").strip().lower().replace(" ", "_")
    return normalized if normalized in INFERENCE_GOALS else "mental_model_discovery"


def _goal_strength(relation: Mapping[str, Any], goal: str) -> float:
    relation_type = str(relation.get("relation_type") or "")
    goal_weight = RELATION_GOAL_WEIGHT.get(relation_type, {}).get(goal, 0.35)
    return round(clamp(float(relation.get("relation_strength", 0.0)) * goal_weight), 4)


def _path_score(values: Iterable[Any]) -> float:
    items = [_number(value) for value in values]
    if not items:
        return 0.0
    score = 1.0
    for item in items:
        score *= max(item, 0.01)
    return round(clamp(score ** (1 / len(items))), 4)


def _is_cross_domain_relation(
    graph: Mapping[str, list[dict[str, Any]]],
    relation_id: str,
) -> bool:
    clean_id = relation_id.removesuffix(":reverse")
    for edges in graph.values():
        for relation in edges:
            if relation["relation_id"].removesuffix(":reverse") == clean_id:
                return bool(relation.get("cross_domain"))
    return False


def _path_id(source: str, target: str, goal: str, relation_path: list[str]) -> str:
    digest = hashlib.sha1(
        f"{source}:{target}:{goal}:{'|'.join(relation_path)}".encode("utf-8")
    ).hexdigest()[:16]
    return f"INF-PATH-{digest}"


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return round(clamp(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _average(values: Iterable[Any]) -> float:
    items = [_number(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


inference_fabric_engine = InferenceFabricEngine()


__all__ = [
    "InferenceFabricEngine",
    "InferencePath",
    "inference_fabric_engine",
]
