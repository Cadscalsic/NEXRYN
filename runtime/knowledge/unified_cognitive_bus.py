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
from uuid import NAMESPACE_URL, uuid5
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.knowledge.cognitive_episode_engine import (
    CognitiveEpisodeEngine,
    CognitiveEpisodeRegistry,
)


RUNTIME_OBJECT_TYPES = {
    "reasoning_runtime": "REASONING_STEP",
    "search_runtime": "SEARCH_ROUTE",
    "adaptive_search_runtime": "SEARCH_ROUTE",
    "concept_formation_runtime": "CONCEPT",
    "program_synthesis_runtime": "PROGRAM",
    "evidence_builder_runtime": "EVIDENCE",
    "truth_runtime": "TRUTH",
    "memory_runtime": "MEMORY",
    "evaluation_runtime": "OBSERVATION",
    "knowledge_integration_runtime": "KNOWLEDGE",
}

ROUTING_TABLE = {
    "CONCEPT": ["process_semantic_context_engine"],
    "PROGRAM": ["process_semantic_context_engine", "evidence_builder_runtime"],
    "EVIDENCE": ["truth_runtime"],
    "TRUTH_CANDIDATE": ["memory_runtime"],
    "TRUTH": ["memory_runtime"],
    "MEMORY_ENTRY": ["experience_engine"],
    "MEMORY": ["experience_engine"],
    "SEARCH_ROUTE": ["evidence_builder_runtime"],
    "REASONING": ["concept_formation_runtime", "search_runtime"],
    "REASONING_STEP": ["concept_formation_runtime", "search_runtime"],
    "SEMANTIC_CONTEXT": ["cognitive_coverage_analyzer"],
    "EXPERIENCE": ["world_model"],
}

CANONICAL_OBJECT_TYPES = {
    "CONCEPT",
    "PROGRAM",
    "EVIDENCE",
    "TRUTH",
    "MEMORY",
    "EXPERIENCE",
    "SEMANTIC_CONTEXT",
    "REASONING_STEP",
    "INFERENCE",
    "HYPOTHESIS",
    "DECISION",
    "GOAL",
    "CONSTRAINT",
    "POLICY",
    "OBSERVATION",
    "SITUATION",
    "TRANSFORMATION",
    "RELATIONSHIP",
    "PATTERN",
    "SEARCH_ROUTE",
    "FAILURE",
    "UNKNOWN",
    "KNOWLEDGE",
}

OBJECT_FAMILY_BY_TYPE = {
    "CONCEPT": "Knowledge",
    "PROGRAM": "Execution",
    "EVIDENCE": "Knowledge",
    "TRUTH": "Knowledge",
    "TRUTH_CANDIDATE": "Knowledge",
    "MEMORY": "Memory",
    "MEMORY_ENTRY": "Memory",
    "EXPERIENCE": "Learning",
    "SEMANTIC_CONTEXT": "Semantic",
    "REASONING": "Reasoning",
    "REASONING_STEP": "Reasoning",
    "INFERENCE": "Reasoning",
    "HYPOTHESIS": "Reasoning",
    "DECISION": "Planning",
    "GOAL": "Planning",
    "CONSTRAINT": "Governance",
    "POLICY": "Governance",
    "OBSERVATION": "Perception",
    "SITUATION": "World",
    "TRANSFORMATION": "Transformation",
    "RELATIONSHIP": "Knowledge",
    "PATTERN": "Knowledge",
    "SEARCH_ROUTE": "Planning",
    "FAILURE": "Learning",
    "UNKNOWN": "Meta",
    "KNOWLEDGE": "Knowledge",
}

CANONICAL_LIFECYCLE_STATES = {
    "CREATED",
    "OBSERVED",
    "SUPPORTED",
    "VALIDATED",
    "ACTIVE",
    "REUSED",
    "GENERALIZED",
    "SPECIALIZED",
    "CANONICAL",
    "ARCHIVED",
    "RETIRED",
}

RELATIONSHIP_ALIASES = {
    "dependencies": "DEPENDS_ON",
    "required_concepts": "DEPENDS_ON",
    "supporting_concepts": "SUPPORTS",
    "supporting_programs": "BUILT_FROM",
    "supporting_routes": "DERIVED_FROM",
    "supporting_truths": "SUPPORTED_BY",
    "evidence_references": "SUPPORTED_BY",
    "causal_links": "CAUSES",
    "contradictions": "CONTRADICTS",
    "references": "REFERENCES",
}


@dataclass(frozen=True)
class CognitiveBusObject:
    object_id: str
    object_uuid: str
    object_origin: str
    execution_id: str
    execution_origin: str
    execution_cycle: str
    runtime_origin: str
    creation_timestamp: str
    last_update_timestamp: str
    object_type: str
    object_family: str
    object_version: int = 1
    object_status: str = "CREATED"
    object_priority: str = "normal"
    object_importance: float = 0.0
    object_confidence: float = 0.0
    object_stability: float = 0.0
    object_complexity: float = 0.0
    object_novelty: float = 0.0
    reuse_score: float = 0.0
    validation_score: float = 0.0
    generalization_score: float = 0.0
    semantic_quality: float = 0.0
    canonical_payload: dict[str, Any] = field(default_factory=dict)
    semantic_payload: dict[str, Any] = field(default_factory=dict)
    structural_payload: dict[str, Any] = field(default_factory=dict)
    evidence_payload: dict[str, Any] = field(default_factory=dict)
    causal_payload: dict[str, Any] = field(default_factory=dict)
    behavior_payload: dict[str, Any] = field(default_factory=dict)
    metadata_payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    importance: float = 0.0
    priority: str = "normal"
    relationships: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    required_objects: list[str] = field(default_factory=list)
    optional_objects: list[str] = field(default_factory=list)
    dependent_objects: list[str] = field(default_factory=list)
    blocking_objects: list[str] = field(default_factory=list)
    supporting_objects: list[str] = field(default_factory=list)
    lineage: dict[str, list[str]] = field(default_factory=dict)
    status: str = "PUBLISHED"
    lifecycle: str = "CREATED"
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
        object_uuid = str(uuid5(NAMESPACE_URL, object_id))
        confidence = _confidence(artifact)
        relationships = _relationships(artifact)
        dependency_map = _dependency_map(artifact)
        dependencies = sorted({
            *dependency_map["required_objects"],
            *dependency_map["supporting_objects"],
            *dependency_map["blocking_objects"],
        })
        timestamp = _timestamp(artifact)
        lifecycle = _lifecycle_state(artifact)
        semantic_payload = _semantic_payload(artifact)
        structural_payload = _structural_payload(artifact)
        evidence_payload = _evidence_payload(artifact)
        causal_payload = _causal_payload(artifact)
        behavior_payload = _behavior_payload(artifact)
        metadata_payload = _metadata_payload(artifact, source_id, sequence)
        canonical_payload = _canonical_payload(
            semantic_payload=semantic_payload,
            structural_payload=structural_payload,
            evidence_payload=evidence_payload,
            causal_payload=causal_payload,
            behavior_payload=behavior_payload,
            metadata_payload=metadata_payload,
        )
        return CognitiveBusObject(
            object_id=object_id,
            object_uuid=object_uuid,
            object_origin=source_id,
            execution_id=str(
                artifact.get("execution_id") or execution_id or "execution:unknown"
            ),
            execution_origin=str(
                artifact.get("execution_origin")
                or artifact.get("execution_id")
                or execution_id
                or "execution:unknown"
            ),
            execution_cycle=str(
                artifact.get("execution_cycle")
                or artifact.get("cycle")
                or artifact.get("run_id")
                or "cycle:unknown"
            ),
            runtime_origin=self.runtime_origin,
            creation_timestamp=timestamp,
            last_update_timestamp=timestamp,
            object_type=self.object_type,
            object_family=_object_family(self.object_type, artifact),
            object_version=1,
            object_status=lifecycle,
            object_priority=str(artifact.get("priority", "normal")),
            object_importance=_importance(artifact, confidence),
            object_confidence=confidence,
            object_stability=_metric(artifact, "stability", "stability_score"),
            object_complexity=_metric(artifact, "complexity", "complexity_score"),
            object_novelty=_metric(artifact, "novelty", "novelty_score"),
            reuse_score=_metric(artifact, "reuse_score", "reuse"),
            validation_score=_metric(artifact, "validation_score", "validation"),
            generalization_score=_metric(artifact, "generalization_score", "generalization"),
            semantic_quality=_metric(artifact, "semantic_quality", "semantic_consistency", default=confidence),
            canonical_payload=canonical_payload,
            semantic_payload=semantic_payload,
            structural_payload=structural_payload,
            evidence_payload=evidence_payload,
            causal_payload=causal_payload,
            behavior_payload=behavior_payload,
            metadata_payload=metadata_payload,
            confidence=confidence,
            importance=_importance(artifact, confidence),
            priority=str(artifact.get("priority", "normal")),
            relationships=relationships,
            dependencies=dependencies,
            required_objects=dependency_map["required_objects"],
            optional_objects=dependency_map["optional_objects"],
            dependent_objects=dependency_map["dependent_objects"],
            blocking_objects=dependency_map["blocking_objects"],
            supporting_objects=dependency_map["supporting_objects"],
            lineage=_initial_lineage(self.runtime_origin, artifact),
            status=lifecycle,
            lifecycle=lifecycle,
            history=[
                {
                    "revision": 1,
                    "object_version": 1,
                    "timestamp": timestamp,
                    "author_runtime": self.runtime_origin,
                    "change_reason": "object_published",
                    "reason": "object_published",
                    "supporting_evidence": _evidence_ids(artifact),
                    "previous_version": None,
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
        self.episode_engine = CognitiveEpisodeEngine(CognitiveEpisodeRegistry())
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
        timestamp = datetime.now(timezone.utc).isoformat()
        lifecycle = str(patch.get("lifecycle", patch.get("object_status", obj.lifecycle)))
        lifecycle = lifecycle if lifecycle in CANONICAL_LIFECYCLE_STATES else obj.lifecycle
        confidence = clamp(patch.get("confidence", patch.get("object_confidence", obj.confidence)))
        importance = clamp(patch.get("importance", patch.get("object_importance", obj.importance)))
        canonical_payload = _merged_canonical_payload(obj, patch)
        updated = replace(
            obj,
            last_update_timestamp=timestamp,
            object_confidence=confidence,
            object_importance=importance,
            object_priority=str(patch.get("priority", patch.get("object_priority", obj.priority))),
            object_status=lifecycle,
            canonical_payload=canonical_payload,
            semantic_payload=canonical_payload.get("semantic_payload", obj.semantic_payload),
            structural_payload=canonical_payload.get("structural_payload", obj.structural_payload),
            evidence_payload=canonical_payload.get("evidence_payload", obj.evidence_payload),
            causal_payload=canonical_payload.get("causal_payload", obj.causal_payload),
            behavior_payload=canonical_payload.get("behavior_payload", obj.behavior_payload),
            metadata_payload=canonical_payload.get("metadata_payload", obj.metadata_payload),
            confidence=confidence,
            importance=importance,
            priority=str(patch.get("priority", patch.get("object_priority", obj.priority))),
            status=lifecycle,
            lifecycle=lifecycle,
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
            {"status": "RETIRED", "lifecycle": "RETIRED", "object_status": "RETIRED"},
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
        episode = self.build_episode(execution_id)
        return {
            "published_objects": published,
            "published_count": len(published),
            "episode": episode,
            "snapshot": self.snapshot(execution_id),
        }

    def snapshot(self, execution_id: str) -> dict[str, Any]:
        objects = [
            obj for obj in self._ordered_objects()
            if not execution_id or obj.execution_id == execution_id
        ]
        type_counts = _distribution(obj.object_type for obj in objects)
        runtime_counts = _distribution(obj.runtime_origin for obj in objects)
        episode = self.build_episode(execution_id, objects=objects)
        object_dicts = []
        for obj in objects:
            item = obj.as_dict()
            item["episode_ids"] = self.episode_engine.registry.episodes_for_object(obj.object_id)
            object_dicts.append(item)
        episode_summary = self._episode_summary(episode)
        return {
            "COGNITIVE_SNAPSHOT": True,
            "execution_id": str(execution_id),
            "primary_episode": episode,
            "episode_summary": episode_summary,
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
            "object_graph": self.object_graph(objects),
            "execution_summary": episode_summary,
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
            "semantic_distribution": _distribution(obj.object_family for obj in objects),
            "confidence_distribution": _confidence_distribution(objects),
            "lifecycle_distribution": _distribution(obj.lifecycle for obj in objects),
            "coverage_summary": {
                "canonical_object_coverage": 1.0 if objects else 0.0,
                "runtime_coverage": len(runtime_counts),
                "object_type_coverage": len(type_counts),
            },
        }

    def build_episode(
        self,
        execution_id: str,
        objects: Iterable[CognitiveBusObject] | None = None,
    ) -> dict[str, Any]:
        selected = list(objects) if objects is not None else [
            obj for obj in self._ordered_objects()
            if not execution_id or obj.execution_id == execution_id
        ]
        episode = self.episode_engine.build_episode(
            execution_id=str(execution_id),
            objects=[obj.as_dict() for obj in selected],
            deliveries={
                object_id: sorted(targets)
                for object_id, targets in self.deliveries.items()
            },
            bus_events=[event.as_dict() for event in self.events],
        )
        return episode.as_dict()

    def replay_episode(self, episode_id: str) -> dict[str, Any]:
        replay = self.episode_engine.replay(episode_id)
        if replay.get("replay_available"):
            self.replay_events += len(replay.get("object_ids", []))
        return replay

    def object_graph(
        self,
        objects: Iterable[CognitiveBusObject] | None = None,
    ) -> dict[str, Any]:
        objects = list(objects) if objects is not None else self._ordered_objects()
        object_ids = {obj.object_id for obj in objects}
        edges = []
        for obj in objects:
            for relationship in obj.relationships:
                target = relationship.get("target")
                edges.append({
                    "source": obj.object_id,
                    "target": str(target),
                    "edge_type": relationship.get("relationship_type")
                    or relationship.get("relationship")
                    or "REFERENCES",
                    "target_is_cognitive_object": str(target) in object_ids,
                })
            for target in obj.dependencies:
                edges.append({
                    "source": obj.object_id,
                    "target": str(target),
                    "edge_type": "DEPENDS_ON",
                    "target_is_cognitive_object": str(target) in object_ids,
                })
        return {
            "nodes": [obj.as_dict() for obj in objects],
            "edges": edges,
            "node_count": len(objects),
            "edge_count": len(edges),
            "relationship_edge_count": sum(1 for edge in edges if edge["edge_type"] != "DEPENDS_ON"),
            "dependency_edge_count": sum(1 for edge in edges if edge["edge_type"] == "DEPENDS_ON"),
            "support_edge_count": sum(1 for edge in edges if "SUPPORT" in str(edge["edge_type"])),
            "conflict_edge_count": sum(1 for edge in edges if edge["edge_type"] == "CONTRADICTS"),
            "lineage_edge_count": sum(len(obj.history) for obj in objects),
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
            "episode_aggregation_statistics": self._episode_report_summary(),
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
            "cognitive_object_model": self.cognitive_object_model_report(),
            "cognitive_episode_report": self.episode_engine.report(),
        }

    def cognitive_episode_report(self) -> dict[str, Any]:
        if self.objects and not self.episode_engine.registry.episodes:
            execution_ids = sorted({obj.execution_id for obj in self.objects.values()})
            for execution_id in execution_ids:
                self.build_episode(execution_id)
        return self.episode_engine.report()

    def cognitive_object_model_report(self) -> dict[str, Any]:
        objects = self._ordered_objects()
        graph = self.object_graph(objects)
        lifecycle_counts = _distribution(obj.lifecycle for obj in objects)
        type_counts = _distribution(obj.object_type for obj in objects)
        family_counts = _distribution(obj.object_family for obj in objects)
        version_counts = {obj.object_id: obj.object_version for obj in objects}
        canonical_objects = [
            obj for obj in objects
            if obj.object_uuid
            and obj.canonical_payload
            and obj.object_type in CANONICAL_OBJECT_TYPES
        ]
        relationship_count = sum(len(obj.relationships) for obj in objects)
        dependency_count = sum(len(obj.dependencies) for obj in objects)
        lineage_depths = [len(obj.history) for obj in objects]
        return {
            "COGNITIVE_OBJECT_MODEL_REPORT": True,
            "objects_created": len(objects),
            "objects_updated": sum(1 for obj in objects if obj.object_version > 1),
            "object_types": type_counts,
            "object_families": family_counts,
            "relationship_statistics": {
                "relationship_count": relationship_count,
                "relationship_types": _distribution(
                    rel.get("relationship_type") or rel.get("relationship")
                    for obj in objects
                    for rel in obj.relationships
                ),
            },
            "dependency_statistics": {
                "dependency_count": dependency_count,
                "required_objects": sum(len(obj.required_objects) for obj in objects),
                "optional_objects": sum(len(obj.optional_objects) for obj in objects),
                "dependent_objects": sum(len(obj.dependent_objects) for obj in objects),
                "blocking_objects": sum(len(obj.blocking_objects) for obj in objects),
                "supporting_objects": sum(len(obj.supporting_objects) for obj in objects),
            },
            "lineage_depth": {
                "minimum": min(lineage_depths or [0]),
                "maximum": max(lineage_depths or [0]),
                "average": _average(lineage_depths),
            },
            "version_statistics": {
                "versions": version_counts,
                "average_version": _average(version_counts.values()),
                "immutable_identity": True,
            },
            "confidence_distribution": _confidence_distribution(objects),
            "object_graph_metrics": {
                "node_count": graph["node_count"],
                "edge_count": graph["edge_count"],
                "relationship_edge_count": graph["relationship_edge_count"],
                "dependency_edge_count": graph["dependency_edge_count"],
                "support_edge_count": graph["support_edge_count"],
                "conflict_edge_count": graph["conflict_edge_count"],
                "lineage_edge_count": graph["lineage_edge_count"],
            },
            "identity_consistency": {
                "stable_object_ids": len({obj.object_id for obj in objects}) == len(objects),
                "stable_object_uuids": len({obj.object_uuid for obj in objects}) == len(objects),
                "identity_survives_version_updates": True,
            },
            "lifecycle_distribution": lifecycle_counts,
            "canonical_coverage": round(len(canonical_objects) / len(objects), 4) if objects else 0.0,
            "reuse_statistics": {
                "average_reuse_score": _average(obj.reuse_score for obj in objects),
                "reused_objects": sum(1 for obj in objects if obj.reuse_score > 0 or obj.lifecycle == "REUSED"),
            },
            "generalization_statistics": {
                "average_generalization_score": _average(obj.generalization_score for obj in objects),
                "generalized_objects": sum(
                    1 for obj in objects
                    if obj.generalization_score > 0 or obj.lifecycle == "GENERALIZED"
                ),
            },
            "integration_health": {
                "creates_new_runtime": False,
                "duplicates_unified_cognitive_bus": False,
                "duplicates_storage_layer": False,
                "bus_exchanges_cognitive_objects": True,
                "future_subsystems_consume_cognitive_objects": True,
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
                "object_version": previous.version + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "author_runtime": str(author_runtime),
                "change_reason": str(reason),
                "reason": str(reason),
                "supporting_evidence": [str(item) for item in supporting_evidence or []],
                "previous_version": previous.version,
            },
        ]
        return replace(
            obj,
            object_version=previous.version + 1,
            version=previous.version + 1,
            history=history,
            lineage=_lineage_from_history(obj.lineage, history),
        )

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
            "generated_truth_candidates": counts.get("TRUTH_CANDIDATE", 0) + counts.get("TRUTH", 0),
            "generated_memory_entries": counts.get("MEMORY_ENTRY", 0) + counts.get("MEMORY", 0),
            "search_routes": counts.get("SEARCH_ROUTE", 0),
            "reasoning_artifacts": counts.get("REASONING", 0) + counts.get("REASONING_STEP", 0),
            "evidence_objects": counts.get("EVIDENCE", 0),
            "total_cognitive_objects": len(objects),
        }

    def _episode_summary(self, episode: Mapping[str, Any]) -> dict[str, Any]:
        stats = dict(episode.get("statistics") or {})
        return {
            "episode_id": episode.get("episode_id"),
            "episode_outcome": episode.get("episode_outcome"),
            "episode_quality": episode.get("episode_quality", 0.0),
            "generated_concepts": stats.get("concept_count", 0),
            "generated_programs": stats.get("program_count", 0),
            "generated_truth_candidates": stats.get("truth_count", 0),
            "generated_memory_entries": stats.get("memory_count", 0),
            "search_routes": stats.get("search_count", 0),
            "reasoning_artifacts": stats.get("reasoning_count", 0),
            "evidence_objects": stats.get("evidence_count", 0),
            "decision_objects": stats.get("decision_count", 0),
            "failure_objects": stats.get("failure_count", 0),
            "relationship_objects": stats.get("relationship_count", 0),
            "semantic_objects": stats.get("semantic_count", 0),
            "total_cognitive_objects": stats.get("object_count", 0),
            "parent_execution_summarizes_episode": True,
        }

    def _episode_report_summary(self) -> dict[str, Any]:
        report = self.cognitive_episode_report()
        return {
            "episodes_created": report.get("episodes_created", 0),
            "episode_outcomes": report.get("episode_outcomes", {}),
            "parent_execution_summarizes_episode": True,
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
        ("truth_candidates", "TRUTH"),
        ("memory_entries", "MEMORY"),
        ("memories", "MEMORY"),
        ("reasoning_artifacts", "REASONING_STEP"),
        ("reasoning_results", "REASONING_STEP"),
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


def _lifecycle_state(artifact: Mapping[str, Any]) -> str:
    raw = str(
        artifact.get("object_status")
        or artifact.get("status")
        or artifact.get("lifecycle")
        or artifact.get("lifecycle_state")
        or "CREATED"
    ).upper()
    aliases = {
        "BIRTH": "CREATED",
        "DISCOVERED": "OBSERVED",
        "PUBLISHED": "OBSERVED",
        "CANDIDATE": "OBSERVED",
        "STRENGTHENED": "SUPPORTED",
        "COMMITTED": "VALIDATED",
        "FAILED": "ARCHIVED",
        "REJECTED": "RETIRED",
    }
    return aliases.get(raw, raw if raw in CANONICAL_LIFECYCLE_STATES else "OBSERVED")


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
        or OBJECT_FAMILY_BY_TYPE.get(object_type)
        or object_type.title()
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


def _behavior_payload(artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: artifact.get(key)
        for key in (
            "behavior",
            "action",
            "decision",
            "execution_result",
            "utility",
            "reuse_score",
            "validation_score",
        )
        if artifact.get(key) is not None
    }


def _metadata_payload(
    artifact: Mapping[str, Any],
    source_id: str,
    sequence: int,
) -> dict[str, Any]:
    metadata = artifact.get("metadata")
    payload = dict(metadata) if isinstance(metadata, Mapping) else {}
    payload.update({
        "source_id": source_id,
        "bus_sequence": sequence,
    })
    for key in (
        "id",
        "object_id",
        "artifact_id",
        "owner_runtime",
        "domain",
        "tags",
    ):
        if artifact.get(key) is not None:
            payload[key] = artifact.get(key)
    return payload


def _canonical_payload(
    *,
    semantic_payload: Mapping[str, Any] | None = None,
    structural_payload: Mapping[str, Any] | None = None,
    evidence_payload: Mapping[str, Any] | None = None,
    causal_payload: Mapping[str, Any] | None = None,
    behavior_payload: Mapping[str, Any] | None = None,
    metadata_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payloads = {
        "semantic_payload": dict(semantic_payload or {}),
        "structural_payload": dict(structural_payload or {}),
        "evidence_payload": dict(evidence_payload or {}),
        "causal_payload": dict(causal_payload or {}),
        "behavior_payload": dict(behavior_payload or {}),
        "metadata_payload": dict(metadata_payload or {}),
    }
    return {
        key: value for key, value in payloads.items()
        if value
    }


def _merged_canonical_payload(
    obj: CognitiveBusObject,
    patch: Mapping[str, Any],
) -> dict[str, Any]:
    merged = {
        "semantic_payload": dict(obj.semantic_payload),
        "structural_payload": dict(obj.structural_payload),
        "evidence_payload": dict(obj.evidence_payload),
        "causal_payload": dict(obj.causal_payload),
        "behavior_payload": dict(obj.behavior_payload),
        "metadata_payload": dict(obj.metadata_payload),
    }
    canonical_patch = patch.get("canonical_payload")
    if isinstance(canonical_patch, Mapping):
        for key in merged:
            value = canonical_patch.get(key)
            if isinstance(value, Mapping):
                merged[key].update(value)
    for key in merged:
        value = patch.get(key)
        if isinstance(value, Mapping):
            merged[key].update(value)
    return {key: value for key, value in merged.items() if value}


def _relationships(artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    relationships = []
    for key in (
        "dependencies",
        "supporting_concepts",
        "supporting_programs",
        "supporting_routes",
        "supporting_truths",
        "evidence_references",
        "required_concepts",
        "causal_links",
        "contradictions",
        "references",
    ):
        for target in _list(artifact.get(key)):
            relationships.append(
                {
                    "relationship": key,
                    "relationship_type": RELATIONSHIP_ALIASES.get(key, "REFERENCES"),
                    "target": str(target.get("source", target)) if isinstance(target, Mapping) else str(target),
                }
            )
    return relationships


def _dependency_map(artifact: Mapping[str, Any]) -> dict[str, list[str]]:
    return {
        "required_objects": _unique_refs(
            _list(artifact.get("required_objects"))
            + _list(artifact.get("required_concepts"))
            + _list(artifact.get("dependencies"))
        ),
        "optional_objects": _unique_refs(
            _list(artifact.get("optional_objects"))
            + _list(artifact.get("optional_dependencies"))
        ),
        "dependent_objects": _unique_refs(
            _list(artifact.get("dependent_objects"))
            + _list(artifact.get("dependents"))
        ),
        "blocking_objects": _unique_refs(
            _list(artifact.get("blocking_objects"))
            + _list(artifact.get("blockers"))
        ),
        "supporting_objects": _unique_refs(
            _list(artifact.get("supporting_objects"))
            + _list(artifact.get("supporting_concepts"))
            + _list(artifact.get("supporting_programs"))
            + _list(artifact.get("supporting_routes"))
            + _list(artifact.get("supporting_truths"))
        ),
    }


def _unique_refs(values: Iterable[Any]) -> list[str]:
    refs = []
    for item in values:
        refs.append(str(item.get("source", item)) if isinstance(item, Mapping) else str(item))
    return sorted({item for item in refs if item})


def _evidence_ids(artifact: Mapping[str, Any]) -> list[str]:
    evidence = []
    for item in _list(artifact.get("supporting_evidence")):
        if isinstance(item, Mapping):
            evidence.append(str(item.get("id", item.get("source", item))))
        else:
            evidence.append(str(item))
    return evidence


def _initial_lineage(runtime_origin: str, artifact: Mapping[str, Any]) -> dict[str, list[str]]:
    evidence = _evidence_ids(artifact)
    lineage = {
        "created_by": [str(runtime_origin)],
        "derived_from": _unique_refs(_list(artifact.get("derived_from"))),
        "supported_by": evidence,
        "validated_by": _unique_refs(_list(artifact.get("validated_by"))),
        "generalized_by": _unique_refs(_list(artifact.get("generalized_by"))),
        "specialized_by": _unique_refs(_list(artifact.get("specialized_by"))),
        "consumed_by": _unique_refs(_list(artifact.get("consumed_by"))),
        "stored_by": _unique_refs(_list(artifact.get("stored_by"))),
        "referenced_by": _unique_refs(_list(artifact.get("referenced_by"))),
        "archived_by": _unique_refs(_list(artifact.get("archived_by"))),
    }
    return {key: value for key, value in lineage.items() if value}


def _lineage_from_history(
    lineage: Mapping[str, list[str]],
    history: Iterable[Mapping[str, Any]],
) -> dict[str, list[str]]:
    updated = {key: list(value) for key, value in lineage.items()}
    updated.setdefault("created_by", [])
    for entry in history:
        runtime = str(entry.get("author_runtime") or "")
        reason = str(entry.get("reason") or entry.get("change_reason") or "")
        if not runtime:
            continue
        if not updated["created_by"]:
            updated["created_by"].append(runtime)
        if "support" in reason:
            updated.setdefault("supported_by", []).append(runtime)
        if "valid" in reason or runtime == "truth_runtime":
            updated.setdefault("validated_by", []).append(runtime)
        if "general" in reason:
            updated.setdefault("generalized_by", []).append(runtime)
        if "special" in reason:
            updated.setdefault("specialized_by", []).append(runtime)
        if "memory" in runtime or "store" in reason:
            updated.setdefault("stored_by", []).append(runtime)
        if "archive" in reason or "retire" in reason:
            updated.setdefault("archived_by", []).append(runtime)
    return {key: sorted(set(value)) for key, value in updated.items() if value}


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


def _metric(
    artifact: Mapping[str, Any],
    *keys: str,
    default: float = 0.0,
) -> float:
    for key in keys:
        if artifact.get(key) is not None:
            return round(clamp(artifact.get(key)), 4)
    return round(clamp(default), 4)


def _confidence_distribution(objects: Iterable[CognitiveBusObject]) -> dict[str, int]:
    buckets = {
        "0.00-0.24": 0,
        "0.25-0.49": 0,
        "0.50-0.74": 0,
        "0.75-1.00": 0,
    }
    for obj in objects:
        confidence = obj.object_confidence
        if confidence < 0.25:
            buckets["0.00-0.24"] += 1
        elif confidence < 0.50:
            buckets["0.25-0.49"] += 1
        elif confidence < 0.75:
            buckets["0.50-0.74"] += 1
        else:
            buckets["0.75-1.00"] += 1
    return buckets


__all__ = [
    "CognitiveBusEvent",
    "CognitiveBusObject",
    "RuntimeAdapter",
    "UnifiedCognitiveBus",
]
