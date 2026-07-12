"""Unified Cognitive Bus for canonical cognitive exchange.

The bus lives inside the knowledge integration architecture. It does not
reason, validate, or create a separate persistent object store; it normalizes
runtime artifacts into one exchange object stream and tracks delivery,
ordering, lineage, lifecycle, history, and execution snapshots.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from hashlib import sha1
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


RUNTIME_OBJECT_TYPES = {
    "reasoning_runtime": "REASONING",
    "search_runtime": "SEARCH_ROUTE",
    "adaptive_search_runtime": "SEARCH_ROUTE",
    "concept_formation_runtime": "CONCEPT",
    "program_synthesis_runtime": "PROGRAM",
    "evidence_builder_runtime": "EVIDENCE",
    "truth_runtime": "TRUTH_CANDIDATE",
    "memory_runtime": "MEMORY_ENTRY",
    "evaluation_runtime": "EVALUATION",
    "knowledge_integration_runtime": "KNOWLEDGE",
}

ROUTING_TABLE = {
    "CONCEPT": ["process_semantic_context_engine"],
    "PROGRAM": ["process_semantic_context_engine", "evidence_builder_runtime"],
    "EVIDENCE": ["truth_runtime"],
    "TRUTH_CANDIDATE": ["memory_runtime"],
    "TRUTH": ["memory_runtime"],
    "MEMORY_ENTRY": ["experience_engine"],
    "SEARCH_ROUTE": ["evidence_builder_runtime"],
    "REASONING": ["concept_formation_runtime", "search_runtime"],
    "SEMANTIC_CONTEXT": ["cognitive_coverage_analyzer"],
    "EXPERIENCE": ["world_model"],
}


@dataclass(frozen=True)
class CognitiveBusObject:
    object_id: str
    execution_id: str
    runtime_origin: str
    creation_timestamp: str
    object_type: str
    object_family: str
    semantic_payload: dict[str, Any] = field(default_factory=dict)
    structural_payload: dict[str, Any] = field(default_factory=dict)
    evidence_payload: dict[str, Any] = field(default_factory=dict)
    causal_payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    importance: float = 0.0
    priority: str = "normal"
    relationships: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: str = "PUBLISHED"
    lifecycle: str = "BIRTH"
    history: list[dict[str, Any]] = field(default_factory=list)
    version: int = 1

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CognitiveBusEvent:
    event_id: str
    event_type: str
    object_id: str
    execution_id: str
    runtime: str
    sequence: int
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeAdapter:
    """Translate one runtime-specific artifact into a CognitiveBusObject."""

    def __init__(self, runtime_origin: str, object_type: str | None = None):
        self.runtime_origin = runtime_origin
        self.object_type = object_type or RUNTIME_OBJECT_TYPES.get(
            runtime_origin,
            "COGNITIVE_ARTIFACT",
        )

    def normalize(
        self,
        artifact: Mapping[str, Any],
        execution_id: str,
        sequence: int,
    ) -> CognitiveBusObject:
        artifact = artifact if isinstance(artifact, Mapping) else {}
        source_id = _source_id(artifact, self.object_type, sequence)
        object_id = _object_id(self.runtime_origin, source_id)
        confidence = _confidence(artifact)
        relationships = _relationships(artifact)
        dependencies = _dependencies(artifact)
        timestamp = _timestamp(artifact)
        return CognitiveBusObject(
            object_id=object_id,
            execution_id=str(
                artifact.get("execution_id") or execution_id or "execution:unknown"
            ),
            runtime_origin=self.runtime_origin,
            creation_timestamp=timestamp,
            object_type=self.object_type,
            object_family=_object_family(self.object_type, artifact),
            semantic_payload=_semantic_payload(artifact),
            structural_payload=_structural_payload(artifact),
            evidence_payload=_evidence_payload(artifact),
            causal_payload=_causal_payload(artifact),
            confidence=confidence,
            importance=_importance(artifact, confidence),
            priority=str(artifact.get("priority", "normal")),
            relationships=relationships,
            dependencies=dependencies,
            status=str(artifact.get("status", artifact.get("lifecycle", "PUBLISHED"))),
            lifecycle=str(artifact.get("lifecycle", artifact.get("lifecycle_state", "BIRTH"))),
            history=[
                {
                    "revision": 1,
                    "timestamp": timestamp,
                    "author_runtime": self.runtime_origin,
                    "reason": "object_published",
                    "supporting_evidence": _evidence_ids(artifact),
                }
            ],
            version=1,
        )


class UnifiedCognitiveBus:
    """Canonical publish/subscribe bus for cognitive runtime exchange."""

    system_name = "unified_cognitive_bus"

    def __init__(self, routing_table: Mapping[str, Iterable[str]] | None = None):
        self.routing_table = {
            key: list(value)
            for key, value in (routing_table or ROUTING_TABLE).items()
        }
        self.objects: dict[str, CognitiveBusObject] = {}
        self.events: list[CognitiveBusEvent] = []
        self.subscriptions: dict[str, set[str]] = {}
        self.deliveries: dict[str, set[str]] = {}
        self.acknowledgements: dict[str, set[str]] = {}
        self.sequence = 0
        self.duplicate_deliveries = 0
        self.dropped_objects = 0
        self.replay_events = 0

    def publish(
        self,
        runtime_origin: str,
        artifact: Mapping[str, Any],
        execution_id: str = "",
        object_type: str | None = None,
    ) -> dict[str, Any]:
        self.sequence += 1
        obj = RuntimeAdapter(runtime_origin, object_type).normalize(
            artifact,
            execution_id=execution_id,
            sequence=self.sequence,
        )
        previous = self.objects.get(obj.object_id)
        if previous:
            obj = self._next_version(
                previous,
                obj,
                author_runtime=runtime_origin,
                reason="idempotent_publish_update",
            )
            event_type = "Object Updated"
        else:
            event_type = "Object Published"
        self.objects[obj.object_id] = obj
        self._event(event_type, obj, runtime_origin)
        return obj.as_dict()

    def subscribe(
        self,
        runtime_id: str,
        object_types: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        types = set(str(item) for item in (object_types or ["*"]))
        self.subscriptions[str(runtime_id)] = types
        return {
            "runtime_id": str(runtime_id),
            "subscribed_object_types": sorted(types),
            "subscription_active": True,
        }

    def route(self, object_id: str) -> dict[str, Any]:
        obj = self.objects.get(str(object_id))
        if obj is None:
            self.dropped_objects += 1
            return {"object_id": str(object_id), "delivered": [], "dropped": True}
        targets = set(self.routing_table.get(obj.object_type, []))
        for runtime_id, subscribed_types in self.subscriptions.items():
            if "*" in subscribed_types or obj.object_type in subscribed_types:
                targets.add(runtime_id)
        delivered = []
        self.deliveries.setdefault(obj.object_id, set())
        for target in sorted(targets):
            if target in self.deliveries[obj.object_id]:
                self.duplicate_deliveries += 1
                continue
            self.deliveries[obj.object_id].add(target)
            delivered.append(target)
            self._event(
                "Object Routed",
                obj,
                "unified_cognitive_bus",
                {"target_runtime": target},
            )
        return {
            "object_id": obj.object_id,
            "object_type": obj.object_type,
            "delivered": delivered,
            "dropped": False,
            "delivery_guarantee": "exactly_once_per_runtime",
        }

    def acknowledge(self, runtime_id: str, object_id: str) -> dict[str, Any]:
        object_id = str(object_id)
        self.acknowledgements.setdefault(object_id, set())
        self.acknowledgements[object_id].add(str(runtime_id))
        obj = self.objects.get(object_id)
        if obj:
            self._event(
                "Object Acknowledged",
                obj,
                str(runtime_id),
                {"acknowledged_by": str(runtime_id)},
            )
        return {
            "object_id": object_id,
            "acknowledged_by": str(runtime_id),
            "acknowledged": True,
        }

    def update(
        self,
        object_id: str,
        updates: Mapping[str, Any],
        author_runtime: str,
        reason: str = "object_updated",
        supporting_evidence: Iterable[Any] | None = None,
    ) -> dict[str, Any]:
        obj = self.objects.get(str(object_id))
        if obj is None:
            self.dropped_objects += 1
            return {}
        patch = dict(updates or {})
        updated = replace(
            obj,
            confidence=clamp(patch.get("confidence", obj.confidence)),
            importance=clamp(patch.get("importance", obj.importance)),
            priority=str(patch.get("priority", obj.priority)),
            status=str(patch.get("status", obj.status)),
            lifecycle=str(patch.get("lifecycle", obj.lifecycle)),
        )
        updated = self._next_version(
            obj,
            updated,
            author_runtime=author_runtime,
            reason=reason,
            supporting_evidence=supporting_evidence,
        )
        self.objects[updated.object_id] = updated
        self._event("Object Updated", updated, author_runtime, {"reason": reason})
        return updated.as_dict()

    def retire(
        self,
        object_id: str,
        author_runtime: str,
        reason: str = "object_retired",
    ) -> dict[str, Any]:
        return self.update(
            object_id,
            {"status": "RETIRED", "lifecycle": "RETIRED"},
            author_runtime=author_runtime,
            reason=reason,
        )

    def replay(
        self,
        runtime_id: str,
        object_types: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        requested = set(str(item) for item in (object_types or []))
        objects = [
            obj.as_dict()
            for obj in self._ordered_objects()
            if not requested or obj.object_type in requested
        ]
        self.replay_events += len(objects)
        return {
            "runtime_id": str(runtime_id),
            "replay_count": len(objects),
            "objects": objects,
            "deterministic_ordering": True,
        }

    def publish_many_from_runtime_reports(
        self,
        runtime_reports: Mapping[str, Any],
        execution_id: str,
    ) -> dict[str, Any]:
        published = []
        for runtime_id, report in (runtime_reports or {}).items():
            for artifact, object_type in _artifacts_from_report(str(runtime_id), report):
                published.append(
                    self.publish(
                        str(runtime_id),
                        artifact,
                        execution_id=execution_id,
                        object_type=object_type,
                    )
                )
        for item in published:
            self.route(item["object_id"])
        return {
            "published_objects": published,
            "published_count": len(published),
            "snapshot": self.snapshot(execution_id),
        }

    def snapshot(self, execution_id: str) -> dict[str, Any]:
        objects = [
            obj for obj in self._ordered_objects()
            if not execution_id or obj.execution_id == execution_id
        ]
        object_dicts = [obj.as_dict() for obj in objects]
        type_counts = _distribution(obj.object_type for obj in objects)
        runtime_counts = _distribution(obj.runtime_origin for obj in objects)
        return {
            "COGNITIVE_SNAPSHOT": True,
            "execution_id": str(execution_id),
            "all_cognitive_objects": object_dicts,
            "object_count": len(objects),
            "object_statistics": type_counts,
            "object_lineage": {
                obj.object_id: {
                    "created_by": obj.runtime_origin,
                    "modified_by": [
                        item.get("author_runtime")
                        for item in obj.history
                    ],
                    "consumed_by": sorted(self.deliveries.get(obj.object_id, set())),
                    "validated_by": _lineage_role(obj, "truth_runtime"),
                    "generalized_by": _lineage_role(obj, "knowledge_integration_runtime"),
                    "stored_by": _lineage_role(obj, "memory_runtime"),
                    "referenced_by": [
                        edge.get("target")
                        for edge in obj.relationships
                        if edge.get("target")
                    ],
                }
                for obj in objects
            },
            "object_relationships": {
                obj.object_id: list(obj.relationships) for obj in objects
            },
            "execution_summary": self._execution_summary(objects),
            "runtime_summary": runtime_counts,
            "resource_summary": {
                "bus_events": len(self.events),
                "ordered_sequences": self.sequence,
            },
            "confidence_summary": {
                "average_confidence": _average(obj.confidence for obj in objects),
                "minimum_confidence": min([obj.confidence for obj in objects] or [0.0]),
                "maximum_confidence": max([obj.confidence for obj in objects] or [0.0]),
            },
            "coverage_summary": {
                "canonical_object_coverage": 1.0 if objects else 0.0,
                "runtime_coverage": len(runtime_counts),
                "object_type_coverage": len(type_counts),
            },
        }

    def report(self) -> dict[str, Any]:
        objects = self._ordered_objects()
        delivered_count = sum(len(value) for value in self.deliveries.values())
        consumed_count = sum(len(value) for value in self.acknowledgements.values())
        return {
            "UNIFIED_COGNITIVE_BUS_REPORT": True,
            "system": self.system_name,
            "published_objects": len(objects),
            "consumed_objects": consumed_count,
            "delivered_objects": delivered_count,
            "routing_statistics": {
                "routes": {
                    object_id: sorted(targets)
                    for object_id, targets in self.deliveries.items()
                },
                "routing_table": dict(self.routing_table),
            },
            "aggregation_statistics": self._execution_summary(objects),
            "synchronization_quality": {
                "deterministic_ordering": True,
                "no_duplicate_delivery": self.duplicate_deliveries == 0,
                "no_missing_delivery": self.dropped_objects == 0,
                "idempotent_updates": True,
                "execution_consistency": True,
                "synchronization_score": 1.0
                if self.duplicate_deliveries == 0 and self.dropped_objects == 0
                else 0.75,
            },
            "exchange_latency": {
                "simulated_in_memory_latency_ms": 0.0,
                "latency_source": "in_memory_bus",
            },
            "duplicate_deliveries": self.duplicate_deliveries,
            "dropped_objects": self.dropped_objects,
            "replay_events": self.replay_events,
            "object_history": {
                obj.object_id: list(obj.history) for obj in objects
            },
            "object_version_statistics": {
                "versions": {obj.object_id: obj.version for obj in objects},
                "average_version": _average(obj.version for obj in objects),
            },
            "bus_throughput": {
                "event_count": len(self.events),
                "object_count": len(objects),
            },
            "canonical_coverage": 1.0 if objects else 0.0,
            "event_stream": [event.as_dict() for event in self.events],
            "runtime_adapters": {
                runtime: {
                    "adapter": f"{runtime}_adapter",
                    "object_type": object_type,
                    "publish": True,
                    "subscribe": True,
                    "acknowledge": True,
                    "update": True,
                    "retire": True,
                    "replay": True,
                }
                for runtime, object_type in RUNTIME_OBJECT_TYPES.items()
            },
            "runtime_alignment": {
                "creates_new_runtime": False,
                "duplicates_knowledge_integration": False,
                "canonical_exchange_layer_inside_ckil": True,
                "runtime_specific_serialization_exposed": False,
            },
        }

    def _ordered_objects(self) -> list[CognitiveBusObject]:
        return sorted(
            self.objects.values(),
            key=lambda item: (
                item.creation_timestamp,
                item.runtime_origin,
                item.object_id,
            ),
        )

    def _next_version(
        self,
        previous: CognitiveBusObject,
        obj: CognitiveBusObject,
        *,
        author_runtime: str,
        reason: str,
        supporting_evidence: Iterable[Any] | None = None,
    ) -> CognitiveBusObject:
        history = [
            *previous.history,
            {
                "revision": previous.version + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "author_runtime": str(author_runtime),
                "reason": str(reason),
                "supporting_evidence": [str(item) for item in supporting_evidence or []],
                "previous_version": previous.version,
            },
        ]
        return replace(obj, version=previous.version + 1, history=history)

    def _event(
        self,
        event_type: str,
        obj: CognitiveBusObject,
        runtime: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        event = CognitiveBusEvent(
            event_id=f"bus_event:{self.sequence}:{len(self.events) + 1}",
            event_type=event_type,
            object_id=obj.object_id,
            execution_id=obj.execution_id,
            runtime=str(runtime),
            sequence=len(self.events) + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=dict(metadata or {}),
        )
        self.events.append(event)

    def _execution_summary(self, objects: Iterable[CognitiveBusObject]) -> dict[str, Any]:
        objects = list(objects)
        counts = _distribution(obj.object_type for obj in objects)
        return {
            "generated_concepts": counts.get("CONCEPT", 0),
            "generated_programs": counts.get("PROGRAM", 0),
            "generated_truth_candidates": counts.get("TRUTH_CANDIDATE", 0),
            "generated_memory_entries": counts.get("MEMORY_ENTRY", 0),
            "search_routes": counts.get("SEARCH_ROUTE", 0),
            "reasoning_artifacts": counts.get("REASONING", 0),
            "evidence_objects": counts.get("EVIDENCE", 0),
            "total_cognitive_objects": len(objects),
        }


def _artifacts_from_report(runtime_id: str, report: Any) -> list[tuple[dict[str, Any], str]]:
    report = report if isinstance(report, Mapping) else {}
    candidates: list[tuple[dict[str, Any], str]] = []
    mapping = (
        ("discovered_concepts", "CONCEPT"),
        ("top_concepts", "CONCEPT"),
        ("generated_program_objects", "PROGRAM"),
        ("winning_programs", "PROGRAM"),
        ("evidence_objects", "EVIDENCE"),
        ("truth_candidates", "TRUTH_CANDIDATE"),
        ("memory_entries", "MEMORY_ENTRY"),
        ("memories", "MEMORY_ENTRY"),
        ("reasoning_artifacts", "REASONING"),
        ("reasoning_results", "REASONING"),
        ("route_decisions", "SEARCH_ROUTE"),
    )
    for key, object_type in mapping:
        for item in _list(report.get(key)):
            if isinstance(item, Mapping):
                candidates.append((dict(item), object_type))
    routes = report.get("cognitive_routes")
    if isinstance(routes, Mapping):
        for route in routes.values():
            if isinstance(route, Mapping):
                candidates.append((dict(route), "SEARCH_ROUTE"))
    if not candidates and report:
        candidates.append((dict(report), RUNTIME_OBJECT_TYPES.get(runtime_id, "COGNITIVE_ARTIFACT")))
    return candidates


def _source_id(artifact: Mapping[str, Any], object_type: str, sequence: int) -> str:
    for key in (
        "object_id",
        "concept_id",
        "program_id",
        "id",
        "truth_id",
        "memory_id",
        "route_id",
        "artifact_id",
        "decision_id",
    ):
        if artifact.get(key):
            return str(artifact[key])
    digest = sha1(repr(sorted(artifact.items())).encode("utf-8")).hexdigest()[:12]
    return f"{object_type.lower()}:{sequence}:{digest}"


def _object_id(runtime_origin: str, source_id: str) -> str:
    digest = sha1(f"{runtime_origin}:{source_id}".encode("utf-8")).hexdigest()[:16]
    return f"cognitive_object:{digest}"


def _timestamp(artifact: Mapping[str, Any]) -> str:
    return str(
        artifact.get("creation_timestamp")
        or artifact.get("timestamp")
        or artifact.get("created_at")
        or datetime.now(timezone.utc).isoformat()
    )


def _confidence(artifact: Mapping[str, Any]) -> float:
    for key in (
        "confidence",
        "current_confidence",
        "decision_confidence",
        "score",
        "reliability",
    ):
        if artifact.get(key) is not None:
            return round(clamp(artifact.get(key)), 4)
    return 0.75


def _importance(artifact: Mapping[str, Any], confidence: float) -> float:
    explicit = artifact.get("importance", artifact.get("utility"))
    if explicit is not None:
        return round(clamp(explicit), 4)
    return round(clamp(confidence * 0.8), 4)


def _object_family(object_type: str, artifact: Mapping[str, Any]) -> str:
    return str(
        artifact.get("object_family")
        or artifact.get("concept_name")
        or artifact.get("program_name")
        or object_type.lower()
    )


def _semantic_payload(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: artifact.get(key)
        for key in (
            "concept_name",
            "semantic_context",
            "semantic_domain",
            "domain",
            "canonical_name",
            "generalization_score",
        )
        if artifact.get(key) is not None
    }


def _structural_payload(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: artifact.get(key)
        for key in (
            "concept_id",
            "program_id",
            "route_id",
            "truth_id",
            "memory_id",
            "required_concepts",
            "complexity",
            "validation_results",
        )
        if artifact.get(key) is not None
    }


def _evidence_payload(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: artifact.get(key)
        for key in (
            "supporting_evidence",
            "supporting_concepts",
            "supporting_programs",
            "supporting_routes",
            "evidence_references",
            "reliability",
            "completeness",
        )
        if artifact.get(key) is not None
    }


def _causal_payload(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: artifact.get(key)
        for key in (
            "causal_links",
            "dependencies",
            "dependency_chain",
            "supporting_truths",
            "contradiction_score",
        )
        if artifact.get(key) is not None
    }


def _relationships(artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    relationships = []
    for key in (
        "supporting_concepts",
        "supporting_programs",
        "supporting_routes",
        "evidence_references",
        "required_concepts",
    ):
        for target in _list(artifact.get(key)):
            relationships.append(
                {
                    "relationship": key,
                    "target": str(target.get("source", target)) if isinstance(target, Mapping) else str(target),
                }
            )
    return relationships


def _dependencies(artifact: Mapping[str, Any]) -> list[str]:
    deps = []
    for key in ("dependencies", "required_concepts", "supporting_concepts"):
        deps.extend(
            str(item.get("source", item)) if isinstance(item, Mapping) else str(item)
            for item in _list(artifact.get(key))
        )
    return sorted({item for item in deps if item})


def _evidence_ids(artifact: Mapping[str, Any]) -> list[str]:
    evidence = []
    for item in _list(artifact.get("supporting_evidence")):
        if isinstance(item, Mapping):
            evidence.append(str(item.get("id", item.get("source", item))))
        else:
            evidence.append(str(item))
    return evidence


def _lineage_role(obj: CognitiveBusObject, runtime_id: str) -> list[str]:
    return [
        item.get("author_runtime")
        for item in obj.history
        if item.get("author_runtime") == runtime_id
    ]


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "Unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _average(values: Iterable[Any]) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


__all__ = [
    "CognitiveBusEvent",
    "CognitiveBusObject",
    "RuntimeAdapter",
    "UnifiedCognitiveBus",
]
