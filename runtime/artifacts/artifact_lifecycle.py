"""Canonical cognitive artifact model and lifecycle engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CANONICAL_LIFECYCLE = (
    "CREATED",
    "NORMALIZED",
    "VALIDATED",
    "PUBLISHED",
    "DISCOVERED",
    "CONSUMED",
    "PROMOTED",
    "COMMITTED",
    "ARCHIVED",
)

PROMOTION_STAGES = (
    "CANDIDATE",
    "SUPPORTED",
    "VALIDATED",
    "TRUSTED",
    "COMMITTED",
    "PERSISTENT",
    "LONG_TERM_MEMORY",
)

ARTIFACT_TYPE_BY_STORE = {
    "concept_store": "CONCEPT",
    "program_store": "PROGRAM",
    "search_routes": "ROUTE",
    "evidence_store": "EVIDENCE",
    "knowledge_objects": "KNOWLEDGE",
    "truth_candidates": "TRUTH",
    "validated_truths": "TRUTH",
    "memory_entries": "MEMORY",
    "context_store": "CONTEXT",
    "dependency_graph": "DEPENDENCY",
}


@dataclass(frozen=True)
class CognitiveArtifact:
    artifact_id: str
    artifact_type: str
    artifact_version: int
    execution_id: str | None
    task_id: str | None
    owner_runtime: str
    origin_runtime: str
    creation_timestamp: str
    current_stage: str
    lifecycle_state: str
    confidence: float
    reliability: float
    priority: str
    evidence_references: tuple[str, ...] = ()
    context_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    concept_references: tuple[str, ...] = ()
    program_references: tuple[str, ...] = ()
    route_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    parent_artifact: str | None = None
    child_artifacts: tuple[str, ...] = ()
    lineage: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    validation_status: str = "PENDING"
    publication_status: str = "UNPUBLISHED"
    consumption_status: str = "UNCONSUMED"
    promotion_status: str = "UNPROMOTED"
    archive_status: str = "ACTIVE"
    promotion_stage: str = "CANDIDATE"
    promotion_score: float = 0.0
    persistence_status: str = "VOLATILE"
    cognitive_value: float = 0.0
    utility_score: float = 0.0
    evidence_density: float = 0.0
    reuse_count: int = 0
    generalization_score: float = 0.0
    novelty_score: float = 0.5
    compression_value: float = 0.0
    prediction_value: float = 0.0
    learning_contribution: float = 0.0
    health_score: float = 0.5
    health_state: str = "STABLE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConceptArtifact(CognitiveArtifact):
    pass


class ProgramArtifact(CognitiveArtifact):
    pass


class RouteArtifact(CognitiveArtifact):
    pass


class EvidenceArtifact(CognitiveArtifact):
    pass


class KnowledgeArtifact(CognitiveArtifact):
    pass


class TruthArtifact(CognitiveArtifact):
    pass


class MemoryArtifact(CognitiveArtifact):
    pass


class ContextArtifact(CognitiveArtifact):
    pass


class DependencyArtifact(CognitiveArtifact):
    pass


class ProcessArtifact(CognitiveArtifact):
    pass


ARTIFACT_CLASS_BY_TYPE = {
    "CONCEPT": ConceptArtifact,
    "PROGRAM": ProgramArtifact,
    "ROUTE": RouteArtifact,
    "EVIDENCE": EvidenceArtifact,
    "KNOWLEDGE": KnowledgeArtifact,
    "TRUTH": TruthArtifact,
    "MEMORY": MemoryArtifact,
    "CONTEXT": ContextArtifact,
    "DEPENDENCY": DependencyArtifact,
    "PROCESS": ProcessArtifact,
}


class ArtifactLifecycleError(ValueError):
    """Raised when an artifact lifecycle transition is invalid."""


class ArtifactLifecycleEngine:
    """Validate and record lifecycle for every cognitive artifact."""

    system_name = "artifact_lifecycle_engine"

    def __init__(
        self,
        registry: dict[str, dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
        validation_failures: list[dict[str, Any]] | None = None,
    ) -> None:
        self.registry = registry if registry is not None else {}
        self.events = events if events is not None else []
        self.validation_failures = (
            validation_failures if validation_failures is not None else []
        )

    def create_published(
        self,
        *,
        store_name: str,
        artifact: Mapping[str, Any],
        owner_runtime: str,
        origin_runtime: str,
        artifact_id: str | None = None,
    ) -> dict[str, Any]:
        artifact_type = ARTIFACT_TYPE_BY_STORE.get(store_name, "PROCESS")
        artifact_id = artifact_id or deterministic_artifact_id(
            artifact_type,
            artifact,
            execution_id=_optional_str(artifact.get("execution_id")),
        )
        existing = self.registry.get(artifact_id)
        if existing:
            if existing.get("owner_runtime") != owner_runtime:
                self._failure(
                    artifact_id,
                    "invalid_ownership",
                    f"{owner_runtime} cannot modify artifact owned by {existing.get('owner_runtime')}",
                )
            return dict(existing)

        created = self._artifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            artifact=artifact,
            owner_runtime=owner_runtime,
            origin_runtime=origin_runtime,
        )
        record = created.to_dict()
        self.registry[artifact_id] = record
        self._event(artifact_id, "CREATED", owner_runtime, "transition")
        for stage in ("NORMALIZED", "VALIDATED", "PUBLISHED"):
            self.transition(artifact_id, stage, runtime_id=owner_runtime)
        return dict(self.registry[artifact_id])

    def discover_and_consume(
        self,
        artifact_id: str,
        *,
        runtime_id: str,
    ) -> dict[str, Any] | None:
        if artifact_id not in self.registry:
            self._failure(artifact_id, "unknown_artifact", "artifact missing from registry")
            return None
        state = self.registry[artifact_id].get("lifecycle_state")
        if state == "PUBLISHED":
            self.transition(artifact_id, "DISCOVERED", runtime_id=runtime_id)
            self.transition(artifact_id, "CONSUMED", runtime_id=runtime_id)
        elif state == "DISCOVERED":
            self.transition(artifact_id, "CONSUMED", runtime_id=runtime_id)
        elif state in {"CONSUMED", "PROMOTED", "COMMITTED", "ARCHIVED"}:
            self._event(artifact_id, state, runtime_id, "already_consumed")
        else:
            self._failure(
                artifact_id,
                "consumption_before_publication",
                f"cannot consume artifact in {state}",
            )
        return dict(self.registry[artifact_id])

    def promote(self, artifact_id: str, *, runtime_id: str) -> dict[str, Any] | None:
        return self.transition(artifact_id, "PROMOTED", runtime_id=runtime_id)

    def commit(self, artifact_id: str, *, runtime_id: str) -> dict[str, Any] | None:
        return self.transition(artifact_id, "COMMITTED", runtime_id=runtime_id)

    def archive(self, artifact_id: str, *, runtime_id: str) -> dict[str, Any] | None:
        return self.transition(artifact_id, "ARCHIVED", runtime_id=runtime_id)

    def transition(
        self,
        artifact_id: str,
        target_state: str,
        *,
        runtime_id: str,
    ) -> dict[str, Any] | None:
        if target_state not in CANONICAL_LIFECYCLE:
            self._failure(artifact_id, "unknown_lifecycle_state", target_state)
            return None
        current = self.registry.get(artifact_id, {}).get("lifecycle_state")
        if current is None:
            if target_state != "CREATED":
                self._failure(artifact_id, "missing_creation", target_state)
                return None
        elif current == target_state:
            self._failure(artifact_id, "duplicate_transition", target_state)
            return None
        elif not self._can_transition(current, target_state):
            self._failure(
                artifact_id,
                "illegal_transition",
                f"{current} -> {target_state}",
            )
            return None

        record = self.registry[artifact_id]
        timestamp = _now()
        record["current_stage"] = target_state
        record["lifecycle_state"] = target_state
        record["updated_timestamp"] = timestamp
        if target_state == "VALIDATED":
            record["validation_status"] = "VALIDATED"
        if target_state == "PUBLISHED":
            record["publication_status"] = "PUBLISHED"
            record["immutable"] = True
        if target_state == "CONSUMED":
            record["consumption_status"] = "CONSUMED"
            record["consumption_time"] = timestamp
        if target_state == "PROMOTED":
            record["promotion_status"] = "PROMOTED"
            record["promotion_time"] = timestamp
        if target_state == "COMMITTED":
            record["commit_time"] = timestamp
        if target_state == "ARCHIVED":
            record["archive_status"] = "ARCHIVED"
            record["archive_time"] = timestamp
        self._event(artifact_id, target_state, runtime_id, "transition")
        return dict(record)

    def validate_registry(self) -> dict[str, Any]:
        failures = []
        for artifact_id, record in self.registry.items():
            owner = record.get("owner_runtime")
            if not owner:
                failures.append(self._validation_item(artifact_id, "missing_owner"))
            if not record.get("creation_timestamp"):
                failures.append(self._validation_item(artifact_id, "missing_creation_timestamp"))
            if record.get("lifecycle_state") not in CANONICAL_LIFECYCLE:
                failures.append(self._validation_item(artifact_id, "invalid_lifecycle_state"))
            for key in (
                "evidence_references",
                "context_references",
                "dependency_references",
                "concept_references",
                "program_references",
                "route_references",
                "knowledge_references",
            ):
                for reference in _as_tuple(record.get(key)):
                    if reference in self.registry:
                        continue
                    if key in {"concept_references", "program_references", "route_references"}:
                        failures.append(
                            self._validation_item(
                                artifact_id,
                                "broken_lineage",
                                {"reference": reference, "reference_field": key},
                            )
                        )
            lineage = _as_tuple(record.get("lineage"))
            if artifact_id in lineage:
                failures.append(self._validation_item(artifact_id, "circular_reference"))
        return {
            "valid": not failures and not self.validation_failures,
            "failure_count": len(failures) + len(self.validation_failures),
            "failures": (self.validation_failures + failures)[-200:],
        }

    def lineage_graph(self) -> dict[str, Any]:
        nodes = [
            {
                "id": artifact_id,
                "type": record.get("artifact_type"),
                "owner_runtime": record.get("owner_runtime"),
                "lifecycle_state": record.get("lifecycle_state"),
            }
            for artifact_id, record in self.registry.items()
        ]
        edges = []
        for artifact_id, record in self.registry.items():
            for key, relation in (
                ("parent_artifact", "parent"),
                ("lineage", "lineage"),
                ("evidence_references", "evidence"),
                ("context_references", "context"),
                ("dependency_references", "dependency"),
                ("concept_references", "concept"),
                ("program_references", "program"),
                ("route_references", "route"),
                ("knowledge_references", "knowledge"),
            ):
                values = (
                    [record.get(key)]
                    if key == "parent_artifact"
                    else _as_tuple(record.get(key))
                )
                for value in values:
                    if value:
                        edges.append({
                            "from": str(value),
                            "to": artifact_id,
                            "relation": relation,
                        })
        return {
            "nodes": nodes,
            "edges": _dedupe_edges(edges),
            "node_count": len(nodes),
            "edge_count": len(_dedupe_edges(edges)),
        }

    def build_report(self) -> dict[str, Any]:
        validation = self.validate_registry()
        states = {}
        types = {}
        for record in self.registry.values():
            states[record.get("lifecycle_state", "UNKNOWN")] = (
                states.get(record.get("lifecycle_state", "UNKNOWN"), 0) + 1
            )
            types[record.get("artifact_type", "UNKNOWN")] = (
                types.get(record.get("artifact_type", "UNKNOWN"), 0) + 1
            )
        return {
            "system": self.system_name,
            "COGNITIVE_ARTIFACT_LIFECYCLE_REPORT": True,
            "canonical_lifecycle": list(CANONICAL_LIFECYCLE),
            "artifact_count": len(self.registry),
            "artifact_types": types,
            "lifecycle_states": states,
            "ownership": {
                artifact_id: record.get("owner_runtime")
                for artifact_id, record in self.registry.items()
            },
            "immutable_published_artifacts": all(
                bool(record.get("immutable"))
                for record in self.registry.values()
                if CANONICAL_LIFECYCLE.index(record.get("lifecycle_state", "CREATED"))
                >= CANONICAL_LIFECYCLE.index("PUBLISHED")
            ),
            "lineage_graph": self.lineage_graph(),
            "validation": validation,
            "telemetry": list(self.events[-500:]),
            "generated_at": _now(),
        }

    def _artifact(
        self,
        *,
        artifact_id: str,
        artifact_type: str,
        artifact: Mapping[str, Any],
        owner_runtime: str,
        origin_runtime: str,
    ) -> CognitiveArtifact:
        artifact_class = ARTIFACT_CLASS_BY_TYPE.get(artifact_type, CognitiveArtifact)
        lineage = _references(
            artifact,
            "lineage",
            "parent_concepts",
            "supporting_evidence",
            "supporting_concepts",
            "supporting_programs",
            "supporting_routes",
            "dependencies",
        )
        return artifact_class(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            artifact_version=int(_number(artifact.get("artifact_version") or artifact.get("revision") or 1)),
            execution_id=_optional_str(artifact.get("execution_id")),
            task_id=_optional_str(artifact.get("task_id") or artifact.get("task")),
            owner_runtime=owner_runtime,
            origin_runtime=origin_runtime,
            creation_timestamp=str(artifact.get("creation_timestamp") or artifact.get("publication_time") or _now()),
            current_stage="CREATED",
            lifecycle_state="CREATED",
            confidence=_confidence(artifact),
            reliability=_clamp(artifact.get("reliability", artifact.get("confidence", 0.5))),
            priority=str(artifact.get("priority") or "normal"),
            evidence_references=_references(artifact, "evidence_references", "supporting_evidence", "evidence_ids"),
            context_references=_references(artifact, "context_references", "supporting_contexts", "context_ids"),
            dependency_references=_references(artifact, "dependency_references", "dependencies"),
            concept_references=_references(artifact, "concept_references", "supporting_concepts", "required_concepts"),
            program_references=_references(artifact, "program_references", "supporting_programs"),
            route_references=_references(artifact, "route_references", "supporting_routes"),
            knowledge_references=_references(artifact, "knowledge_references", "supporting_knowledge"),
            parent_artifact=_optional_str(artifact.get("parent_artifact") or artifact.get("parent") or artifact.get("parent_id")),
            child_artifacts=_references(artifact, "child_artifacts", "children"),
            lineage=lineage,
            metadata=_metadata(artifact),
            promotion_stage=str(artifact.get("promotion_stage") or "CANDIDATE"),
            promotion_score=_clamp(artifact.get("promotion_score", 0.0)),
            persistence_status=str(artifact.get("persistence_status") or "VOLATILE"),
            cognitive_value=_clamp(artifact.get("cognitive_value", 0.0)),
            utility_score=_clamp(artifact.get("utility_score", artifact.get("utility", 0.0))),
            evidence_density=_clamp(artifact.get("evidence_density", 0.0)),
            reuse_count=int(_number(artifact.get("reuse_count", 0))),
            generalization_score=_clamp(artifact.get("generalization_score", artifact.get("generalization", 0.0))),
            novelty_score=_clamp(artifact.get("novelty_score", artifact.get("novelty", 0.5))),
            compression_value=_clamp(artifact.get("compression_value", artifact.get("compression", 0.0))),
            prediction_value=_clamp(artifact.get("prediction_value", 0.0)),
            learning_contribution=_clamp(artifact.get("learning_contribution", 0.0)),
            health_score=_clamp(artifact.get("health_score", 0.5)),
            health_state=str(artifact.get("health_state") or "STABLE"),
        )

    def _can_transition(self, current: str, target: str) -> bool:
        current_index = CANONICAL_LIFECYCLE.index(current)
        target_index = CANONICAL_LIFECYCLE.index(target)
        return target_index == current_index + 1

    def _event(
        self,
        artifact_id: str,
        state: str,
        runtime_id: str,
        event_type: str,
    ) -> None:
        self.events.append({
            "artifact_id": artifact_id,
            "runtime_id": runtime_id,
            "event_type": event_type,
            "lifecycle_state": state,
            "timestamp": _now(),
        })

    def _failure(self, artifact_id: str, failure_type: str, detail: Any) -> None:
        self.validation_failures.append(
            self._validation_item(artifact_id, failure_type, detail)
        )

    def _validation_item(
        self,
        artifact_id: str,
        failure_type: str,
        detail: Any = None,
    ) -> dict[str, Any]:
        return {
            "artifact_id": artifact_id,
            "failure": failure_type,
            "detail": detail,
            "timestamp": _now(),
        }


class ArtifactPromotionEngine:
    """Deterministic promotion policy for canonical artifacts."""

    system_name = "artifact_promotion_engine"

    def __init__(
        self,
        lifecycle: ArtifactLifecycleEngine,
        promotion_events: list[dict[str, Any]] | None = None,
        promotion_failures: list[dict[str, Any]] | None = None,
    ) -> None:
        self.lifecycle = lifecycle
        self.promotion_events = promotion_events if promotion_events is not None else []
        self.promotion_failures = (
            promotion_failures if promotion_failures is not None else []
        )

    def evaluate(
        self,
        artifact_id: str,
        *,
        runtime_id: str = "artifact_governance",
        memory_policy: bool = True,
    ) -> dict[str, Any]:
        record = self.lifecycle.registry.get(artifact_id)
        if not record:
            return self._failure(artifact_id, "unknown_artifact", {})
        if record.get("promotion_stage") == "LONG_TERM_MEMORY":
            return self._failure(artifact_id, "duplicate_promotion", {})

        criteria = self._score(record, memory_policy=memory_policy)
        target_stage = self._target_stage(criteria["promotion_score"], record)
        current_stage = record.get("promotion_stage", "CANDIDATE")
        if PROMOTION_STAGES.index(target_stage) <= PROMOTION_STAGES.index(current_stage):
            return self._failure(artifact_id, "promotion_not_eligible", criteria)
        if not self._ownership_valid(record):
            return self._failure(artifact_id, "invalid_ownership", criteria)
        if (
            record.get("artifact_type") in {"TRUTH", "KNOWLEDGE", "MEMORY"}
            and criteria["evidence_count"] == 0
            and target_stage != "SUPPORTED"
        ):
            return self._failure(artifact_id, "promotion_without_evidence", criteria)

        self._advance_lifecycle_for_promotion(artifact_id, runtime_id)
        record = self.lifecycle.registry[artifact_id]
        promoted_stages = []
        for stage in PROMOTION_STAGES[
            PROMOTION_STAGES.index(current_stage) + 1:
            PROMOTION_STAGES.index(target_stage) + 1
        ]:
            timestamp = _now()
            event = {
                "artifact_id": artifact_id,
                "runtime_id": runtime_id,
                "promotion_stage": stage,
                "promotion_score": criteria["promotion_score"],
                "criteria": criteria,
                "timestamp": timestamp,
            }
            history = list(record.get("promotion_history", []))
            history.append(event)
            record["promotion_history"] = history
            record["promotion_stage"] = stage
            record["promotion_score"] = criteria["promotion_score"]
            record["promotion_time"] = timestamp
            if stage in {"SUPPORTED", "VALIDATED", "TRUSTED"}:
                record["promotion_status"] = stage
            if stage == "COMMITTED":
                self.lifecycle.commit(artifact_id, runtime_id=runtime_id)
                record["promotion_status"] = "COMMITTED"
            if stage == "PERSISTENT":
                record["persistence_status"] = "PERSISTENCE_READY"
            if stage == "LONG_TERM_MEMORY":
                record["persistence_status"] = "LONG_TERM_MEMORY"
            self.promotion_events.append(event)
            promoted_stages.append(stage)

        return {
            "artifact_id": artifact_id,
            "promoted": True,
            "promotion_stage": record.get("promotion_stage"),
            "promotion_score": criteria["promotion_score"],
            "promoted_stages": promoted_stages,
            "criteria": criteria,
        }

    def evaluate_all(self, *, runtime_id: str = "artifact_governance") -> dict[str, Any]:
        results = [
            self.evaluate(artifact_id, runtime_id=runtime_id)
            for artifact_id in list(self.lifecycle.registry)
        ]
        promoted = [item for item in results if item.get("promoted")]
        return {
            "system": self.system_name,
            "ARTIFACT_PROMOTION_REPORT": True,
            "evaluated": len(results),
            "promoted": len(promoted),
            "promotion_success_rate": round(len(promoted) / max(len(results), 1), 4),
            "promotion_failures": list(self.promotion_failures[-200:]),
            "results": results,
        }

    def _advance_lifecycle_for_promotion(self, artifact_id: str, runtime_id: str) -> None:
        state = self.lifecycle.registry[artifact_id].get("lifecycle_state")
        if state == "PUBLISHED":
            self.lifecycle.transition(artifact_id, "DISCOVERED", runtime_id=runtime_id)
            self.lifecycle.transition(artifact_id, "CONSUMED", runtime_id=runtime_id)
            self.lifecycle.transition(artifact_id, "PROMOTED", runtime_id=runtime_id)
        elif state == "DISCOVERED":
            self.lifecycle.transition(artifact_id, "CONSUMED", runtime_id=runtime_id)
            self.lifecycle.transition(artifact_id, "PROMOTED", runtime_id=runtime_id)
        elif state == "CONSUMED":
            self.lifecycle.transition(artifact_id, "PROMOTED", runtime_id=runtime_id)

    def _score(self, record: Mapping[str, Any], *, memory_policy: bool) -> dict[str, Any]:
        evidence_count = len(_as_tuple(record.get("evidence_references"))) + (
            1 if record.get("artifact_type") == "EVIDENCE" else 0
        )
        context_count = len(_as_tuple(record.get("context_references")))
        dependency_count = len(_as_tuple(record.get("dependency_references")))
        cross_runtime_agreement = len(set(_as_tuple(record.get("lineage")))) >= 2
        confidence = _clamp(record.get("confidence", 0.0))
        reliability = _clamp(record.get("reliability", 0.0))
        truth_validation = (
            record.get("artifact_type") == "TRUTH"
            and (
                record.get("validation_status") == "VALIDATED"
                or record.get("metadata", {}).get("validated") is True
            )
        )
        score = (
            confidence * 0.25
            + reliability * 0.2
            + min(evidence_count, 6) / 6 * 0.18
            + (0.12 if cross_runtime_agreement else 0.0)
            + min(context_count, 3) / 3 * 0.08
            + min(dependency_count, 3) / 3 * 0.07
            + (0.07 if truth_validation else 0.0)
            + (0.03 if memory_policy else 0.0)
        )
        return {
            "promotion_score": round(_clamp(score), 4),
            "evidence_count": evidence_count,
            "context_count": context_count,
            "dependency_count": dependency_count,
            "cross_runtime_agreement": cross_runtime_agreement,
            "confidence": confidence,
            "reliability": reliability,
            "truth_validation": bool(truth_validation),
            "memory_policy": memory_policy,
        }

    def _target_stage(self, score: float, record: Mapping[str, Any]) -> str:
        if score >= 0.88 and record.get("artifact_type") in {"TRUTH", "MEMORY"}:
            return "LONG_TERM_MEMORY"
        if score >= 0.82:
            return "PERSISTENT"
        if score >= 0.72:
            return "COMMITTED"
        if score >= 0.62:
            return "TRUSTED"
        if score >= 0.5:
            return "VALIDATED"
        if score >= 0.38:
            return "SUPPORTED"
        return "CANDIDATE"

    def _ownership_valid(self, record: Mapping[str, Any]) -> bool:
        expected = {
            "CONCEPT": "concept_formation_runtime",
            "PROGRAM": "program_synthesis_runtime",
            "EVIDENCE": "evidence_builder_runtime",
            "KNOWLEDGE": "knowledge_integration_runtime",
            "TRUTH": "truth_runtime",
            "MEMORY": "memory_runtime",
        }.get(str(record.get("artifact_type")))
        return expected is None or record.get("owner_runtime") == expected

    def _failure(self, artifact_id: str, failure: str, detail: Mapping[str, Any]) -> dict[str, Any]:
        item = {
            "artifact_id": artifact_id,
            "failure": failure,
            "detail": dict(detail),
            "timestamp": _now(),
        }
        self.promotion_failures.append(item)
        return {
            "artifact_id": artifact_id,
            "promoted": False,
            "failure": failure,
            "detail": dict(detail),
        }


class ArtifactPersistenceLayer:
    """Persist committed and stable artifacts with their cognitive history."""

    system_name = "artifact_persistence_layer"

    def __init__(
        self,
        registry: dict[str, dict[str, Any]],
        persistence_store: dict[str, dict[str, Any]] | None = None,
        persistence_events: list[dict[str, Any]] | None = None,
        path: str | Path | None = None,
    ) -> None:
        self.registry = registry
        self.persistence_store = persistence_store if persistence_store is not None else {}
        self.persistence_events = persistence_events if persistence_events is not None else []
        self.path = Path(path or "runtime_data/artifacts/committed_artifacts.json")

    def persist_eligible(self, *, runtime_id: str = "artifact_persistence_layer") -> dict[str, Any]:
        persisted = []
        failures = []
        for artifact_id, record in self.registry.items():
            eligible = (
                record.get("promotion_stage") in {"COMMITTED", "PERSISTENT", "LONG_TERM_MEMORY"}
                or record.get("lifecycle_state") == "COMMITTED"
            )
            if not eligible:
                continue
            if record.get("validation_status") != "VALIDATED":
                failures.append({
                    "artifact_id": artifact_id,
                    "failure": "persisted_without_validation_blocked",
                })
                continue
            snapshot = self._snapshot(record)
            self.persistence_store[artifact_id] = snapshot
            record["persistence_status"] = (
                "LONG_TERM_MEMORY"
                if record.get("promotion_stage") == "LONG_TERM_MEMORY"
                else "PERSISTENT"
            )
            record["persistence_time"] = snapshot["persistence_time"]
            self.persistence_events.append({
                "artifact_id": artifact_id,
                "runtime_id": runtime_id,
                "persistence_status": record["persistence_status"],
                "timestamp": snapshot["persistence_time"],
            })
            persisted.append(artifact_id)
        self._save()
        return {
            "system": self.system_name,
            "ARTIFACT_PERSISTENCE_REPORT": True,
            "persisted_count": len(persisted),
            "persisted_artifacts": persisted,
            "persistence_failures": failures,
            "persistence_store_size": len(self.persistence_store),
            "path": str(self.path),
        }

    def _snapshot(self, record: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "artifact_id": record.get("artifact_id"),
            "artifact_type": record.get("artifact_type"),
            "owner_runtime": record.get("owner_runtime"),
            "origin_runtime": record.get("origin_runtime"),
            "lifecycle_state": record.get("lifecycle_state"),
            "promotion_stage": record.get("promotion_stage"),
            "promotion_score": record.get("promotion_score"),
            "confidence": record.get("confidence"),
            "reliability": record.get("reliability"),
            "lineage": record.get("lineage", ()),
            "evidence_references": record.get("evidence_references", ()),
            "context_references": record.get("context_references", ()),
            "dependency_references": record.get("dependency_references", ()),
            "promotion_history": record.get("promotion_history", []),
            "validation_status": record.get("validation_status"),
            "creation_timestamp": record.get("creation_timestamp"),
            "publication_time": record.get("publication_time"),
            "promotion_time": record.get("promotion_time"),
            "persistence_time": _now(),
        }

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.persistence_store, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )
        except OSError:
            return


class ArtifactEconomyEngine:
    """Evolve artifacts as reusable cognitive assets."""

    system_name = "artifact_economy_engine"

    def __init__(
        self,
        registry: dict[str, dict[str, Any]],
        economy_events: list[dict[str, Any]] | None = None,
        reuse_events: list[dict[str, Any]] | None = None,
        relationships: list[dict[str, Any]] | None = None,
    ) -> None:
        self.registry = registry
        self.economy_events = economy_events if economy_events is not None else []
        self.reuse_events = reuse_events if reuse_events is not None else []
        self.relationships = relationships if relationships is not None else []

    def update_all(self, *, runtime_id: str = "artifact_economy_engine") -> dict[str, Any]:
        updated = []
        self._rebuild_relationships()
        for artifact_id in list(self.registry):
            updated.append(self.update_artifact(artifact_id, runtime_id=runtime_id))
        return {
            "system": self.system_name,
            "ARTIFACT_ECONOMY_REPORT": True,
            "updated_artifacts": len(updated),
            "average_cognitive_value": _average_number(
                item.get("cognitive_value", 0.0) for item in self.registry.values()
            ),
            "healthy_artifacts": sum(1 for item in self.registry.values() if item.get("health_state") == "HEALTHY"),
            "weak_artifacts": sum(1 for item in self.registry.values() if item.get("health_state") == "WEAK"),
            "conflicting_artifacts": sum(1 for item in self.registry.values() if item.get("health_state") == "CONFLICTING"),
            "archived_artifacts": sum(1 for item in self.registry.values() if item.get("health_state") == "ARCHIVED"),
            "relationship_graph": self.relationship_graph(),
            "events": list(self.economy_events[-200:]),
        }

    def update_artifact(self, artifact_id: str, *, runtime_id: str = "artifact_economy_engine") -> dict[str, Any]:
        record = self.registry[artifact_id]
        experience = self._experience(record)
        evidence_density = self._evidence_density(record)
        reuse_count = int(experience.get("times_reused", 0))
        success_count = int(experience.get("times_successful", 0))
        failure_count = int(experience.get("times_failed", 0))
        success_rate = success_count / max(success_count + failure_count, 1)
        utility = _clamp(
            record.get("utility_score", 0.0)
            or (
                _clamp(record.get("confidence", 0.0)) * 0.35
                + _clamp(record.get("reliability", 0.0)) * 0.25
                + success_rate * 0.25
                + min(reuse_count, 10) / 10 * 0.15
            )
        )
        generalization = _clamp(
            record.get("generalization_score", 0.0)
            or len(set(experience.get("generalization_domains", []))) / 8
        )
        compression = _clamp(
            record.get("compression_value", 0.0)
            or min(len(self._outgoing_relationships(artifact_id)), 8) / 8
        )
        prediction = _clamp(
            record.get("prediction_value", 0.0)
            or experience.get("prediction_accuracy", 0.0)
        )
        learning = _clamp(
            record.get("learning_contribution", 0.0)
            or (
                success_rate * 0.4
                + generalization * 0.25
                + evidence_density * 0.2
                + min(len(self._incoming_relationships(artifact_id)), 8) / 8 * 0.15
            )
        )
        novelty = _clamp(record.get("novelty_score", 0.5))
        aging_penalty = self._aging_penalty(record)
        cognitive_value = _clamp(
            utility * 0.24
            + evidence_density * 0.16
            + _clamp(record.get("reliability", 0.0)) * 0.16
            + generalization * 0.14
            + compression * 0.1
            + prediction * 0.1
            + learning * 0.08
            + novelty * 0.02
            - aging_penalty
        )
        health_score = _clamp(
            cognitive_value * 0.55
            + success_rate * 0.25
            + _clamp(record.get("promotion_score", 0.0)) * 0.2
            - min(failure_count, 5) * 0.04
        )
        health_state = self._health_state(record, health_score, failure_count)
        record.update({
            "artifact_experience": experience,
            "times_reused": reuse_count,
            "times_successful": success_count,
            "times_failed": failure_count,
            "prediction_accuracy": round(float(experience.get("prediction_accuracy", 0.0)), 4),
            "correction_count": int(experience.get("correction_count", 0)),
            "average_utility": round(utility, 4),
            "utility_score": round(utility, 4),
            "evidence_density": round(evidence_density, 4),
            "reuse_count": reuse_count,
            "generalization_score": round(generalization, 4),
            "novelty_score": round(novelty, 4),
            "compression_value": round(compression, 4),
            "prediction_value": round(prediction, 4),
            "learning_contribution": round(learning, 4),
            "cognitive_value": round(cognitive_value, 4),
            "health_score": round(health_score, 4),
            "health_state": health_state,
            "reuse_priority": round(_clamp(cognitive_value * 0.7 + health_score * 0.3), 4),
            "economy_updated_at": _now(),
        })
        self.economy_events.append({
            "artifact_id": artifact_id,
            "runtime_id": runtime_id,
            "event_type": "artifact_value_update",
            "cognitive_value": record["cognitive_value"],
            "health_state": health_state,
            "timestamp": record["economy_updated_at"],
        })
        return dict(record)

    def record_experience(
        self,
        artifact_id: str,
        *,
        success: bool,
        utility: float = 0.0,
        prediction_accuracy: float | None = None,
        domain: str | None = None,
        correction: bool = False,
        runtime_id: str = "artifact_experience",
    ) -> dict[str, Any]:
        if artifact_id not in self.registry:
            return {"artifact_id": artifact_id, "recorded": False, "reason": "unknown_artifact"}
        record = self.registry[artifact_id]
        experience = self._experience(record)
        experience["times_reused"] = int(experience.get("times_reused", 0)) + 1
        if success:
            experience["times_successful"] = int(experience.get("times_successful", 0)) + 1
        else:
            experience["times_failed"] = int(experience.get("times_failed", 0)) + 1
        if correction:
            experience["correction_count"] = int(experience.get("correction_count", 0)) + 1
        if prediction_accuracy is not None:
            prior = float(experience.get("prediction_accuracy", 0.0) or 0.0)
            observations = max(int(experience.get("times_reused", 1)), 1)
            experience["prediction_accuracy"] = round(
                ((prior * (observations - 1)) + _clamp(prediction_accuracy)) / observations,
                4,
            )
        if utility:
            values = list(experience.get("utility_history", []))
            values.append(_clamp(utility))
            experience["utility_history"] = values[-50:]
        if domain:
            domains = list(experience.get("execution_domains", []))
            if domain not in domains:
                domains.append(domain)
            experience["execution_domains"] = domains[-50:]
            generalization = list(experience.get("generalization_domains", []))
            if success and domain not in generalization:
                generalization.append(domain)
            experience["generalization_domains"] = generalization[-50:]
        history = list(record.get("historical_confidence", []))
        history.append(_clamp(record.get("confidence", 0.0)))
        record["historical_confidence"] = history[-50:]
        record["artifact_experience"] = experience
        self.update_artifact(artifact_id, runtime_id=runtime_id)
        self.reuse_events.append({
            "artifact_id": artifact_id,
            "runtime_id": runtime_id,
            "success": bool(success),
            "utility": _clamp(utility),
            "domain": domain,
            "timestamp": _now(),
        })
        return {"artifact_id": artifact_id, "recorded": True, "experience": dict(experience)}

    def recommend(
        self,
        *,
        query: Mapping[str, Any] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        query = query or {}
        candidates = []
        ignored = []
        rejected = []
        for artifact_id, record in self.registry.items():
            if record.get("health_state") in {"ARCHIVED", "DEPRECATED", "CONFLICTING"}:
                rejected.append({"artifact_id": artifact_id, "reason": record.get("health_state")})
                continue
            score = self._reuse_score(record, query)
            if score <= 0.1:
                ignored.append({"artifact_id": artifact_id, "reason": "low_reuse_score"})
                continue
            candidates.append({
                "artifact_id": artifact_id,
                "artifact_type": record.get("artifact_type"),
                "reuse_score": round(score, 4),
                "expected_usefulness": round(score * _clamp(record.get("health_score", 0.0)), 4),
                "health_state": record.get("health_state"),
                "cognitive_value": record.get("cognitive_value", 0.0),
                "supporting_evidence": list(_as_tuple(record.get("evidence_references"))),
                "promotion_history": record.get("promotion_history", []),
                "decision_lineage": list(_as_tuple(record.get("lineage"))),
            })
        ranked = sorted(candidates, key=lambda item: item["reuse_score"], reverse=True)[:limit]
        event = {
            "query": dict(query),
            "recommended": [item["artifact_id"] for item in ranked],
            "ignored_count": len(ignored),
            "rejected_count": len(rejected),
            "timestamp": _now(),
        }
        self.reuse_events.append(event)
        return {
            "system": "artifact_reuse_engine",
            "ARTIFACT_REUSE_REPORT": True,
            "recommended_artifacts": ranked,
            "artifacts_used": [item["artifact_id"] for item in ranked],
            "artifacts_ignored": ignored[:50],
            "artifacts_rejected": rejected[:50],
            "prevents_duplicate_reasoning": bool(ranked),
            "expected_usefulness": _average_number(item["expected_usefulness"] for item in ranked),
            "explainability": {
                "artifacts_used": [item["artifact_id"] for item in ranked],
                "supporting_evidence": {
                    item["artifact_id"]: item["supporting_evidence"]
                    for item in ranked
                },
                "promotion_history": {
                    item["artifact_id"]: item["promotion_history"]
                    for item in ranked
                },
                "decision_lineage": {
                    item["artifact_id"]: item["decision_lineage"]
                    for item in ranked
                },
            },
        }

    def relationship_graph(self) -> dict[str, Any]:
        nodes = [
            {
                "id": artifact_id,
                "type": record.get("artifact_type"),
                "health_state": record.get("health_state"),
                "cognitive_value": record.get("cognitive_value", 0.0),
            }
            for artifact_id, record in self.registry.items()
        ]
        edges = _dedupe_relation_edges(list(self.relationships))
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "relationship_types": sorted({edge["relation"] for edge in edges}),
        }

    def _rebuild_relationships(self) -> None:
        self.relationships.clear()
        for artifact_id, record in self.registry.items():
            for key, relation in (
                ("evidence_references", "supports"),
                ("dependency_references", "depends_on"),
                ("concept_references", "explains"),
                ("program_references", "extends"),
                ("route_references", "collaborates"),
                ("knowledge_references", "generalizes"),
                ("lineage", "supports"),
            ):
                for reference in _as_tuple(record.get(key)):
                    if reference:
                        self.relationships.append({
                            "source": str(reference),
                            "target": artifact_id,
                            "relation": relation,
                        })
            for other_id, other in self.registry.items():
                if artifact_id >= other_id:
                    continue
                if record.get("artifact_type") == other.get("artifact_type") == "TRUTH":
                    shared = set(_as_tuple(record.get("evidence_references"))) & set(_as_tuple(other.get("evidence_references")))
                    if shared:
                        relation = "contradicts" if abs(_clamp(record.get("confidence")) - _clamp(other.get("confidence"))) > 0.35 else "competes"
                        self.relationships.append({
                            "source": artifact_id,
                            "target": other_id,
                            "relation": relation,
                            "shared_evidence": sorted(shared),
                        })

    def _experience(self, record: Mapping[str, Any]) -> dict[str, Any]:
        existing = record.get("artifact_experience")
        if isinstance(existing, Mapping):
            return dict(existing)
        return {
            "times_reused": int(_number(record.get("reuse_count", 0))),
            "times_successful": 0,
            "times_failed": 0,
            "prediction_accuracy": _clamp(record.get("prediction_accuracy", 0.0)),
            "correction_count": 0,
            "promotion_count": len(record.get("promotion_history", [])),
            "utility_history": [],
            "execution_domains": [],
            "generalization_domains": [],
        }

    def _evidence_density(self, record: Mapping[str, Any]) -> float:
        evidence = len(_as_tuple(record.get("evidence_references")))
        lineage = len(_as_tuple(record.get("lineage")))
        if record.get("artifact_type") == "EVIDENCE":
            evidence += 1
        return _clamp((evidence + min(lineage, 6) / 2) / 8)

    def _aging_penalty(self, record: Mapping[str, Any]) -> float:
        if record.get("persistence_status") in {"PERSISTENT", "LONG_TERM_MEMORY"}:
            return 0.0
        if int(self._experience(record).get("times_reused", 0)) == 0:
            return 0.04
        if record.get("health_state") in {"WEAK", "DEPRECATED"}:
            return 0.06
        return 0.0

    def _health_state(self, record: Mapping[str, Any], health_score: float, failure_count: int) -> str:
        if record.get("archive_status") == "ARCHIVED":
            return "ARCHIVED"
        if failure_count >= 3 and health_score < 0.45:
            return "DEPRECATED"
        if self._has_conflict(record.get("artifact_id")):
            return "CONFLICTING"
        if health_score >= 0.72:
            return "HEALTHY"
        if health_score >= 0.5:
            return "STABLE"
        return "WEAK"

    def _has_conflict(self, artifact_id: str | None) -> bool:
        return any(
            edge.get("relation") in {"contradicts", "competes"}
            and artifact_id in {edge.get("source"), edge.get("target")}
            for edge in self.relationships
        )

    def _incoming_relationships(self, artifact_id: str) -> list[dict[str, Any]]:
        return [edge for edge in self.relationships if edge.get("target") == artifact_id]

    def _outgoing_relationships(self, artifact_id: str) -> list[dict[str, Any]]:
        return [edge for edge in self.relationships if edge.get("source") == artifact_id]

    def _reuse_score(self, record: Mapping[str, Any], query: Mapping[str, Any]) -> float:
        domain = query.get("domain") or query.get("task_type")
        experience = self._experience(record)
        domain_match = 0.0
        if domain and domain in set(experience.get("execution_domains", [])):
            domain_match = 0.15
        requested_type = query.get("artifact_type")
        type_match = 0.1 if requested_type and requested_type == record.get("artifact_type") else 0.0
        return _clamp(
            _clamp(record.get("reuse_priority", 0.0)) * 0.35
            + _clamp(record.get("cognitive_value", 0.0)) * 0.25
            + _clamp(record.get("health_score", 0.0)) * 0.2
            + min(int(experience.get("times_successful", 0)), 5) / 5 * 0.1
            + domain_match
            + type_match
        )


def deterministic_artifact_id(
    artifact_type: str,
    artifact: Mapping[str, Any],
    *,
    execution_id: str | None = None,
) -> str:
    stable_source = {
        "artifact_type": artifact_type,
        "source_id": artifact.get("id")
        or artifact.get("knowledge_id")
        or artifact.get("concept_id")
        or artifact.get("program_id")
        or artifact.get("route_id")
        or artifact.get("truth_id"),
        "execution_id": execution_id,
        "task_id": artifact.get("task_id") or artifact.get("task"),
        "signature": _metadata(artifact),
    }
    digest = hashlib.sha1(
        json.dumps(stable_source, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    return f"{artifact_type}:{digest}"


def _metadata(artifact: Mapping[str, Any]) -> dict[str, Any]:
    output = {}
    for index, (key, value) in enumerate(artifact.items()):
        if index >= 24:
            break
        if key in {
            "metadata",
            "summary",
            "lineage",
            "supporting_evidence",
            "supporting_concepts",
            "supporting_programs",
            "supporting_routes",
        }:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            output[str(key)] = value
        elif isinstance(value, list):
            output[str(key)] = {"count": len(value)}
        elif isinstance(value, Mapping):
            output[str(key)] = {"keys": sorted(str(k) for k in value.keys())[:8]}
        else:
            output[str(key)] = type(value).__name__
    return output


def _references(artifact: Mapping[str, Any], *keys: str) -> tuple[str, ...]:
    output = []
    for key in keys:
        output.extend(_strings(artifact.get(key)))
    return tuple(dict.fromkeys(item for item in output if item))


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        refs = []
        for key in ("id", "artifact_id", "source", "target", "knowledge_id"):
            if value.get(key):
                refs.append(str(value[key]))
        return refs
    if isinstance(value, (list, tuple, set)):
        refs = []
        for item in value:
            refs.extend(_strings(item))
        return refs
    return [str(value)]


def _as_tuple(value: Any) -> tuple[str, ...]:
    return tuple(_strings(value))


def _confidence(artifact: Mapping[str, Any]) -> float:
    for key in (
        "confidence",
        "current_confidence",
        "support_score",
        "evidence_score",
        "utility",
    ):
        if artifact.get(key) is not None:
            return _clamp(artifact.get(key))
    return 0.5


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return max(0.0, min(1.0, _number(value)))


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None and value != "" else None


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge["from"], edge["to"], edge["relation"])
        if marker in seen or edge["from"] == edge["to"]:
            continue
        seen.add(marker)
        output.append(edge)
    return output


def _dedupe_relation_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge.get("source"), edge.get("target"), edge.get("relation"))
        if marker in seen or edge.get("source") == edge.get("target"):
            continue
        seen.add(marker)
        output.append(dict(edge))
    return output


def _average_number(values: Any) -> float:
    collected = [float(value or 0.0) for value in values]
    return round(sum(collected) / max(len(collected), 1), 4) if collected else 0.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
