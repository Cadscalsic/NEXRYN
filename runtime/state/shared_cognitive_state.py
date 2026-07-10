"""Shared cognitive state and deterministic context propagation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from runtime.artifacts import (
    ArtifactEconomyEngine,
    ArtifactLifecycleEngine,
    ArtifactPersistenceLayer,
    ArtifactPromotionEngine,
)
from runtime.observability import cognitive_runtime_observability_engine


STATE_PATH = Path("runtime_data/shared_cognitive_state/latest.json")


@dataclass
class SharedCognitiveState:
    execution_context: dict[str, Any] = field(default_factory=dict)
    reasoning_context: dict[str, Any] = field(default_factory=dict)
    concept_store: dict[str, dict[str, Any]] = field(default_factory=dict)
    program_store: dict[str, dict[str, Any]] = field(default_factory=dict)
    search_routes: dict[str, dict[str, Any]] = field(default_factory=dict)
    evidence_store: dict[str, dict[str, Any]] = field(default_factory=dict)
    context_store: dict[str, dict[str, Any]] = field(default_factory=dict)
    dependency_graph: dict[str, dict[str, Any]] = field(default_factory=dict)
    truth_candidates: dict[str, dict[str, Any]] = field(default_factory=dict)
    validated_truths: dict[str, dict[str, Any]] = field(default_factory=dict)
    memory_entries: dict[str, dict[str, Any]] = field(default_factory=dict)
    knowledge_objects: dict[str, dict[str, Any]] = field(default_factory=dict)
    knowledge_graph: dict[str, Any] = field(default_factory=dict)
    world_model: dict[str, Any] = field(default_factory=dict)
    dna_state: dict[str, Any] = field(default_factory=dict)
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    runtime_metrics: dict[str, Any] = field(default_factory=dict)
    execution_profile: dict[str, Any] = field(default_factory=dict)
    ownership: dict[str, str] = field(default_factory=dict)
    artifact_registry: dict[str, dict[str, Any]] = field(default_factory=dict)
    artifact_lifecycle_events: list[dict[str, Any]] = field(default_factory=list)
    artifact_validation_failures: list[dict[str, Any]] = field(default_factory=list)
    artifact_promotion_events: list[dict[str, Any]] = field(default_factory=list)
    artifact_promotion_failures: list[dict[str, Any]] = field(default_factory=list)
    artifact_persistence_store: dict[str, dict[str, Any]] = field(default_factory=dict)
    artifact_persistence_events: list[dict[str, Any]] = field(default_factory=list)
    artifact_economy_events: list[dict[str, Any]] = field(default_factory=list)
    artifact_reuse_events: list[dict[str, Any]] = field(default_factory=list)
    artifact_relationships: list[dict[str, Any]] = field(default_factory=list)
    runtime_observability_snapshots: list[dict[str, Any]] = field(default_factory=list)
    runtime_observability_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    propagation_events: list[dict[str, Any]] = field(default_factory=list)
    consumption_events: list[dict[str, Any]] = field(default_factory=list)
    artifact_audit: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscriptions: dict[str, list[str]] = field(default_factory=dict)
    validation_warnings: list[dict[str, Any]] = field(default_factory=list)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    inherited_from_snapshot: str | None = None

    @classmethod
    def create(
        cls,
        execution_profile: Mapping[str, Any] | None = None,
        mode: str = "adaptive",
        inherit_latest: bool = False,
        path: str | Path | None = None,
    ) -> "SharedCognitiveState":
        state = cls.load(path=path) if inherit_latest else cls()
        inherited_counts = state.counts()
        state.execution_profile = dict(execution_profile or {})
        state.execution_metadata.update({
            "mode": mode,
            "cognitive_pipeline": (
                state.execution_profile.get("cognitive_pipeline")
                or state.execution_profile.get("pipeline_name")
                or "adaptive"
            ),
            "state_created_at": datetime.now(timezone.utc).isoformat(),
            "inherit_requested": bool(inherit_latest),
            "inherited_state": bool(state.inherited_from_snapshot),
            "inherited_counts_at_boot": inherited_counts,
        })
        if inherit_latest and not state.inherited_from_snapshot:
            state.validation_warnings.append({
                "runtime_id": "shared_cognitive_state",
                "warning": "inherit_requested_without_snapshot",
                "severity": "diagnostic",
            })
        if inherit_latest and inherited_counts.get("context_count", 0) == 0:
            state.validation_warnings.append({
                "runtime_id": "shared_cognitive_state",
                "warning": "inherited_context_count_zero",
                "severity": "critical" if state.inherited_from_snapshot else "diagnostic",
            })
        return state

    @classmethod
    def load(cls, path: str | Path | None = None) -> "SharedCognitiveState":
        source = Path(path or STATE_PATH)
        if not source.exists():
            return cls()
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(payload, dict):
            return cls()
        state = cls(
            execution_context=dict(payload.get("execution_context", {})),
            reasoning_context=dict(payload.get("reasoning_context", {})),
            concept_store=dict(payload.get("concept_store", {})),
            program_store=dict(payload.get("program_store", {})),
            search_routes=dict(payload.get("search_routes", {})),
            evidence_store=dict(payload.get("evidence_store", {})),
            context_store=dict(payload.get("context_store", {})),
            dependency_graph=dict(payload.get("dependency_graph", {})),
            truth_candidates=dict(payload.get("truth_candidates", {})),
            validated_truths=dict(payload.get("validated_truths", {})),
            memory_entries=dict(payload.get("memory_entries", {})),
            knowledge_objects=dict(payload.get("knowledge_objects", {})),
            knowledge_graph=dict(payload.get("knowledge_graph", {})),
            world_model=dict(payload.get("world_model", {})),
            dna_state=dict(payload.get("dna_state", {})),
            execution_metadata=dict(payload.get("execution_metadata", {})),
            runtime_metrics=dict(payload.get("runtime_metrics", {})),
            execution_profile=dict(payload.get("execution_profile", {})),
            ownership=dict(payload.get("ownership", {})),
            artifact_registry=dict(payload.get("artifact_registry", {})),
            artifact_lifecycle_events=list(payload.get("artifact_lifecycle_events", [])),
            artifact_validation_failures=list(payload.get("artifact_validation_failures", [])),
            artifact_promotion_events=list(payload.get("artifact_promotion_events", [])),
            artifact_promotion_failures=list(payload.get("artifact_promotion_failures", [])),
            artifact_persistence_store=dict(payload.get("artifact_persistence_store", {})),
            artifact_persistence_events=list(payload.get("artifact_persistence_events", [])),
            artifact_economy_events=list(payload.get("artifact_economy_events", [])),
            artifact_reuse_events=list(payload.get("artifact_reuse_events", [])),
            artifact_relationships=list(payload.get("artifact_relationships", [])),
            runtime_observability_snapshots=list(
                payload.get("runtime_observability_snapshots", [])
            ),
            runtime_observability_diagnostics=list(
                payload.get("runtime_observability_diagnostics", [])
            ),
            propagation_events=list(payload.get("propagation_events", [])),
            consumption_events=list(payload.get("consumption_events", [])),
            artifact_audit=dict(payload.get("artifact_audit", {})),
            subscriptions=dict(payload.get("subscriptions", {})),
            validation_warnings=list(payload.get("validation_warnings", [])),
            snapshots=list(payload.get("snapshots", [])),
        )
        latest = state.snapshots[-1].get("snapshot_id") if state.snapshots else None
        state.inherited_from_snapshot = latest
        return state

    def save(self, path: str | Path | None = None) -> dict[str, Any]:
        target = Path(path or STATE_PATH)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        return {
            "saved": True,
            "path": str(target),
            "snapshot_count": len(self.snapshots),
        }

    def validate_before(
        self,
        runtime_id: str,
        required: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        warnings = []
        for store_name in required:
            store = getattr(self, store_name, {})
            if not store:
                warnings.append({
                    "runtime_id": runtime_id,
                    "warning": f"{store_name}_empty_before_execution",
                    "severity": "diagnostic",
                })
        if self.execution_context is None or not isinstance(self.execution_context, dict):
            warnings.append({
                "runtime_id": runtime_id,
                "warning": "execution_context_invalid",
                "severity": "diagnostic",
            })
        report = {
            "runtime_id": runtime_id,
            "context_integrity": not any(
                item["warning"] == "execution_context_invalid"
                for item in warnings
            ),
            "registry_integrity": True,
            "binding_integrity": True,
            "execution_ownership": self._ownership_integrity(),
            "knowledge_references": bool(self.knowledge_objects or not required),
            "evidence_references": bool(self.evidence_store or "evidence_store" not in required),
            "context_references": bool(self.context_store or "context_store" not in required),
            "dependency_references": bool(self.dependency_graph or "dependency_graph" not in required),
            "memory_references": bool(self.memory_entries or "memory_entries" not in required),
            "truth_references": bool(self.truth_candidates or "truth_candidates" not in required),
            "warnings": warnings,
        }
        self.validation_warnings.extend(warnings)
        return report

    def publish(
        self,
        runtime_id: str,
        payload: Mapping[str, Any] | None,
        owner: str,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        data = dict(payload or {})
        if isinstance(context, Mapping):
            self.execution_context.update(_small_mapping(context, limit=80))
        self.execution_context[runtime_id] = _small_mapping(data, limit=40)
        before = self.counts()

        if runtime_id == "reasoning_runtime":
            self.reasoning_context.update(_small_mapping(data, limit=80))
        if runtime_id == "concept_formation_runtime":
            self._store_items("concept_store", owner, _extract_concepts(data))
        if runtime_id == "program_synthesis_runtime":
            self._store_items("program_store", owner, _extract_programs(data))
        if runtime_id in {"search_runtime", "adaptive_search_intelligence_runtime"}:
            self._store_items("search_routes", owner, _extract_routes(data))
        if runtime_id == "evidence_builder_runtime" or _has_explicit_evidence(data):
            self._store_items("evidence_store", owner, _extract_evidence(data, runtime_id))
        self._store_items("context_store", owner, _extract_contexts(data, runtime_id))
        self._store_items("dependency_graph", owner, _extract_dependencies(data, runtime_id))
        if runtime_id == "truth_runtime":
            self._store_items("truth_candidates", owner, _extract_truths(data))
            self._store_items("validated_truths", owner, _extract_validated_truths(data))
        if runtime_id == "memory_runtime":
            self._store_items("memory_entries", owner, _extract_memory(data))
        if runtime_id == "knowledge_integration_runtime":
            self._store_items("knowledge_objects", owner, _extract_knowledge_objects(data))
            graph = data.get("knowledge_graph")
            if isinstance(graph, Mapping):
                self.knowledge_graph = dict(graph)

        self._extract_common_state(data)
        after = self.counts()
        published_artifacts = _delta_artifacts(before, after)
        event = {
            "runtime_id": runtime_id,
            "owner": owner,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "before": before,
            "after": after,
            "delta": published_artifacts,
            "published_artifacts": published_artifacts,
            "propagation_latency_seconds": round(perf_counter() - started, 9),
        }
        self.propagation_events.append(event)
        artifact_refs = self._artifact_ids_for_runtime(runtime_id, owner, published_artifacts)
        self.runtime_observability_snapshots.append(
            cognitive_runtime_observability_engine.build_snapshot(
                runtime_id=runtime_id,
                purpose="runtime_publication",
                execution_id=str(
                    data.get("execution_id")
                    or self.execution_metadata.get("execution_id")
                    or f"{runtime_id}:shared_state_publication"
                ),
                artifact_references=artifact_refs,
                produced_artifacts=artifact_refs,
                published_artifacts=published_artifacts,
                confidence=_average([
                    _number(self.artifact_registry.get(artifact_id, {}).get("confidence"))
                    for artifact_id in artifact_refs
                ]) if artifact_refs else 0.9,
                duration_seconds=event["propagation_latency_seconds"],
                input_count=len(data),
                output_count=sum(published_artifacts.values()),
                failures=[],
                warnings=[],
                lifecycle_stage="PUBLISHED",
                summary=f"{runtime_id} published {sum(published_artifacts.values())} cognitive artifacts",
                metrics={
                    "input_fields": len(data),
                    "published_artifacts": sum(published_artifacts.values()),
                    "artifact_type_count": len([value for value in published_artifacts.values() if value]),
                },
                telemetry=event,
            )
        )
        return event

    def consume(
        self,
        runtime_id: str,
        artifact_types: tuple[str, ...] | list[str],
        required: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        started = perf_counter()
        if runtime_id == "memory_runtime":
            artifact_types = [
                artifact_type
                for artifact_type in artifact_types
                if artifact_type not in {"concept_store", "program_store", "search_routes"}
            ]
        artifacts = {
            artifact_type: dict(getattr(self, artifact_type, {}))
            for artifact_type in artifact_types
            if hasattr(self, artifact_type)
        }
        missing_required = [
            artifact_type
            for artifact_type in required
            if not artifacts.get(artifact_type)
        ]
        timestamp = datetime.now(timezone.utc).isoformat()
        consumed_ids = []
        for artifact_type, store in artifacts.items():
            for artifact_id in store:
                consumed_ids.append(artifact_id)
                artifact_record = self._artifact_engine().discover_and_consume(
                    artifact_id,
                    runtime_id=runtime_id,
                )
                audit = self.artifact_audit.setdefault(
                    artifact_id,
                    _artifact_audit_seed(
                        artifact_id,
                        artifact_type,
                        self.ownership.get(artifact_id, "unknown"),
                        timestamp,
                    ),
                )
                consumers = audit.setdefault("consumers", [])
                if runtime_id not in consumers:
                    consumers.append(runtime_id)
                audit["consumption_time"] = timestamp
                audit["propagation_delay_seconds"] = _timestamp_delta_seconds(
                    audit.get("publication_time"),
                    timestamp,
                )
                audit["current_state"] = "CONSUMED"
                if artifact_record:
                    audit["lifecycle"] = artifact_record.get("lifecycle_state")
                    store[artifact_id].update(
                        _artifact_overlay(artifact_record)
                    )
        event = {
            "runtime_id": runtime_id,
            "artifact_types": list(artifact_types),
            "required": list(required),
            "missing_required": missing_required,
            "consumed_artifact_count": len(consumed_ids),
            "consumed_artifact_ids": consumed_ids[:200],
            "timestamp": timestamp,
            "consumption_latency_seconds": round(perf_counter() - started, 9),
        }
        self.consumption_events.append(event)
        for artifact_type in missing_required:
            self.validation_warnings.append({
                "runtime_id": runtime_id,
                "warning": f"{artifact_type}_missing_on_consume",
                "severity": "critical" if runtime_id == "truth_runtime" else "diagnostic",
            })
        self.runtime_observability_snapshots.append(
            cognitive_runtime_observability_engine.build_snapshot(
                runtime_id=runtime_id,
                purpose="runtime_consumption",
                execution_id=str(
                    self.execution_metadata.get("execution_id")
                    or f"{runtime_id}:shared_state_consumption"
                ),
                artifact_references=consumed_ids[:200],
                consumed_artifacts=consumed_ids[:200],
                confidence=0.9 if not missing_required else 0.6,
                duration_seconds=event["consumption_latency_seconds"],
                input_count=len(consumed_ids),
                output_count=0,
                failures=[
                    {"missing_required": missing_required}
                ] if missing_required else [],
                warnings=[
                    f"{artifact_type}_missing_on_consume"
                    for artifact_type in missing_required
                ],
                lifecycle_stage="CONSUMED",
                summary=f"{runtime_id} consumed {len(consumed_ids)} cognitive artifacts",
                metrics={
                    "consumed_artifact_count": len(consumed_ids),
                    "required_artifact_type_count": len(required),
                    "missing_required_count": len(missing_required),
                },
                telemetry=event,
            )
        )
        return {"artifacts": artifacts, "event": event}

    def query(self, artifact_type: str, limit: int | None = None) -> dict[str, Any]:
        store = dict(getattr(self, artifact_type, {}))
        if limit is None:
            return store
        return dict(list(store.items())[:limit])

    def subscribe(self, runtime_id: str, artifact_types: tuple[str, ...] | list[str]) -> None:
        self.subscriptions[runtime_id] = list(artifact_types)

    def broadcast(self, artifact_types: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
        deliveries = []
        selected = set(artifact_types or ())
        for runtime_id, subscribed_types in self.subscriptions.items():
            types = [
                artifact_type
                for artifact_type in subscribed_types
                if not selected or artifact_type in selected
            ]
            if types:
                deliveries.append(self.consume(runtime_id, types)["event"])
        return {
            "broadcast": True,
            "delivery_count": len(deliveries),
            "deliveries": deliveries,
        }

    def snapshot(self, stage_name: str) -> dict[str, Any]:
        counts = self.counts()
        snapshot_id = _id("snapshot", stage_name, len(self.snapshots), counts)
        snapshot = {
            "snapshot_id": snapshot_id,
            "stage_name": stage_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counts": counts,
            "concept_ids": list(self.concept_store.keys())[:100],
            "program_ids": list(self.program_store.keys())[:100],
            "search_route_ids": list(self.search_routes.keys())[:100],
            "truth_ids": list(self.truth_candidates.keys())[:100],
            "validated_truth_ids": list(self.validated_truths.keys())[:100],
            "memory_ids": list(self.memory_entries.keys())[:100],
            "knowledge_object_ids": list(self.knowledge_objects.keys())[:100],
            "evidence_ids": list(self.evidence_store.keys())[:100],
            "context_ids": list(self.context_store.keys())[:100],
            "runtime_metrics": dict(self.runtime_metrics),
            "execution_metadata": dict(self.execution_metadata),
        }
        self.snapshots.append(snapshot)
        return snapshot

    def counts(self) -> dict[str, int]:
        return {
            "context_count": len(self.execution_context),
            "reasoning_context_count": len(self.reasoning_context),
            "concept_count": len(self.concept_store),
            "program_count": len(self.program_store),
            "search_route_count": len(self.search_routes),
            "evidence_count": len(self.evidence_store),
            "context_store_count": len(self.context_store),
            "dependency_count": len(self.dependency_graph),
            "truth_candidate_count": len(self.truth_candidates),
            "validated_truth_count": len(self.validated_truths),
            "memory_entry_count": len(self.memory_entries),
            "knowledge_object_count": len(self.knowledge_objects),
            "artifact_count": len(self.artifact_registry),
            "snapshot_count": len(self.snapshots),
            "runtime_observability_snapshot_count": len(self.runtime_observability_snapshots),
        }

    def build_report(self) -> dict[str, Any]:
        required_flow = [
            ("concept_formation_runtime", "program_synthesis_runtime"),
            ("program_synthesis_runtime", "adaptive_search_intelligence_runtime"),
            ("adaptive_search_intelligence_runtime", "evidence_builder_runtime"),
            ("evidence_builder_runtime", "knowledge_integration_runtime"),
            ("knowledge_integration_runtime", "truth_runtime"),
            ("truth_runtime", "memory_runtime"),
            ("memory_runtime", "reasoning_runtime"),
        ]
        observed_runtimes = [event["runtime_id"] for event in self.propagation_events]
        available = self.counts()
        inherited_counts = self.execution_metadata.get("inherited_counts_at_boot")
        if not isinstance(inherited_counts, Mapping):
            inherited_counts = {}
        inherit_requested = bool(self.execution_metadata.get("inherit_requested"))
        context_zero_reason = None
        if inherit_requested and int(inherited_counts.get("context_count", 0) or 0) == 0:
            context_zero_reason = (
                "no_prior_shared_cognitive_state_snapshot"
                if not self.inherited_from_snapshot
                else "prior_snapshot_had_zero_context"
            )
        missing_references = self._missing_references()
        return {
            "system": "shared_cognitive_state",
            "SHARED_COGNITIVE_STATE_REPORT": True,
            "execution_profile": dict(self.execution_profile),
            "inherited_from_snapshot": self.inherited_from_snapshot,
            "state_inheritance": {
                "inherit_requested": inherit_requested,
                "inherited_state": bool(self.inherited_from_snapshot),
                "inherited_from_snapshot": self.inherited_from_snapshot,
                "inherited_counts_at_boot": dict(inherited_counts),
                "context_count_at_boot": int(inherited_counts.get("context_count", 0) or 0),
                "context_zero_reason": context_zero_reason,
            },
            "context_propagation_coverage": self._coverage_score(),
            "shared_state_integrity": self._ownership_integrity() and not missing_references,
            "knowledge_flow": {
                "required_flow": required_flow,
                "observed_runtimes": observed_runtimes,
                "deterministic_propagation": True,
            },
            "context_ownership": dict(self.ownership),
            "snapshot_timeline": list(self.snapshots),
            "state_consistency": {
                "counts": available,
                "validation_warning_count": len(self.validation_warnings),
                "missing_reference_count": len(missing_references),
            },
            "cross_runtime_references": self._cross_runtime_references(),
            "evidence_architecture": self._evidence_architecture_summary(),
            "artifact_lifecycle": self.build_artifact_lifecycle_report(),
            "artifact_flow": self.build_artifact_flow_report(),
            "artifact_economy": self.build_artifact_economy_report(),
            "cognitive_observability": self.build_cognitive_observability_report(),
            "propagation_latency": {
                "events": [
                    {
                        "runtime_id": event["runtime_id"],
                        "latency_seconds": event["propagation_latency_seconds"],
                    }
                    for event in self.propagation_events
                ],
                "total_latency_seconds": round(
                    sum(event["propagation_latency_seconds"] for event in self.propagation_events),
                    9,
                ),
            },
            "knowledge_availability": available,
            "missing_references": missing_references,
            "validation_warnings": list(self.validation_warnings),
            "KNOWLEDGE_PROPAGATION_REPORT": self.build_knowledge_propagation_report(),
        }

    def build_knowledge_propagation_report(self) -> dict[str, Any]:
        counts = self.counts()
        published_total = sum(
            sum(max(value, 0) for value in event.get("published_artifacts", {}).values())
            for event in self.propagation_events
        )
        consumed_ids = {
            artifact_id
            for event in self.consumption_events
            for artifact_id in event.get("consumed_artifact_ids", [])
        }
        auditable_ids = set(self.artifact_audit)
        unconsumed = sorted(auditable_ids - consumed_ids)
        dropped = [
            warning
            for warning in self.validation_warnings
            if warning.get("warning", "").endswith("_missing_on_consume")
        ]
        return {
            "system": "cognitive_knowledge_bus",
            "KNOWLEDGE_PROPAGATION_REPORT": True,
            "artifacts_published": {
                "total": published_total,
                "by_store": {
                    "concepts": counts["concept_count"],
                    "programs": counts["program_count"],
                    "search_routes": counts["search_route_count"],
                    "evidence": counts["evidence_count"],
                    "contexts": counts["context_store_count"],
                    "dependencies": counts["dependency_count"],
                    "truth_candidates": counts["truth_candidate_count"],
                    "validated_truths": counts["validated_truth_count"],
                    "memory_entries": counts["memory_entry_count"],
                    "knowledge_objects": counts["knowledge_object_count"],
                },
            },
            "artifacts_consumed": {
                "total": len(consumed_ids),
                "events": list(self.consumption_events),
            },
            "propagation_success_rate": round(
                len(consumed_ids) / max(len(auditable_ids), 1),
                4,
            ),
            "dropped_artifacts": dropped,
            "unconsumed_artifacts": unconsumed[:200],
            "context_coverage": _coverage(counts["context_store_count"]),
            "evidence_coverage": _coverage(counts["evidence_count"]),
            "truth_coverage": _coverage(counts["truth_candidate_count"] + counts["validated_truth_count"]),
            "memory_coverage": _coverage(counts["memory_entry_count"]),
            "knowledge_bus_latency": {
                "publish_seconds": round(
                    sum(event["propagation_latency_seconds"] for event in self.propagation_events),
                    9,
                ),
                "consume_seconds": round(
                    sum(event["consumption_latency_seconds"] for event in self.consumption_events),
                    9,
                ),
            },
            "propagation_failures": dropped,
            "artifact_audit": list(self.artifact_audit.values())[:500],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_context": self.execution_context,
            "reasoning_context": self.reasoning_context,
            "concept_store": self.concept_store,
            "program_store": self.program_store,
            "search_routes": self.search_routes,
            "evidence_store": self.evidence_store,
            "context_store": self.context_store,
            "dependency_graph": self.dependency_graph,
            "truth_candidates": self.truth_candidates,
            "validated_truths": self.validated_truths,
            "memory_entries": self.memory_entries,
            "knowledge_objects": self.knowledge_objects,
            "knowledge_graph": self.knowledge_graph,
            "world_model": self.world_model,
            "dna_state": self.dna_state,
            "execution_metadata": self.execution_metadata,
            "runtime_metrics": self.runtime_metrics,
            "execution_profile": self.execution_profile,
            "ownership": self.ownership,
            "artifact_registry": self.artifact_registry,
            "artifact_lifecycle_events": self.artifact_lifecycle_events[-500:],
            "artifact_validation_failures": self.artifact_validation_failures[-500:],
            "artifact_promotion_events": self.artifact_promotion_events[-500:],
            "artifact_promotion_failures": self.artifact_promotion_failures[-500:],
            "artifact_persistence_store": self.artifact_persistence_store,
            "artifact_persistence_events": self.artifact_persistence_events[-500:],
            "artifact_economy_events": self.artifact_economy_events[-500:],
            "artifact_reuse_events": self.artifact_reuse_events[-500:],
            "artifact_relationships": self.artifact_relationships[-1000:],
            "runtime_observability_snapshots": self.runtime_observability_snapshots[-1000:],
            "runtime_observability_diagnostics": self.runtime_observability_diagnostics[-500:],
            "propagation_events": self.propagation_events[-200:],
            "consumption_events": self.consumption_events[-200:],
            "artifact_audit": dict(list(self.artifact_audit.items())[-1000:]),
            "subscriptions": self.subscriptions,
            "validation_warnings": self.validation_warnings[-200:],
            "snapshots": self.snapshots[-100:],
        }

    def _store_items(self, store_name: str, owner: str, items: list[dict[str, Any]]) -> None:
        store = getattr(self, store_name)
        timestamp = datetime.now(timezone.utc).isoformat()
        for item in items:
            item_id = str(item.get("id") or item.get("knowledge_id") or _id(store_name, item))
            if item_id in store and self.ownership.get(item_id) not in {None, owner}:
                self.artifact_validation_failures.append({
                    "artifact_id": item_id,
                    "failure": "invalid_ownership",
                    "detail": {
                        "existing_owner": self.ownership.get(item_id),
                        "attempted_owner": owner,
                    },
                    "timestamp": timestamp,
                })
                continue
            artifact_record = self._artifact_engine().create_published(
                store_name=store_name,
                artifact={**item, "id": item_id},
                owner_runtime=owner,
                origin_runtime=item.get("origin_runtime") or owner,
                artifact_id=item_id,
            )
            stored = {
                **item,
                "id": item_id,
                "owner": owner,
                "origin_runtime": item.get("origin_runtime") or owner,
                "publication_time": item.get("publication_time") or timestamp,
                "lineage": item.get("lineage") or _lineage_for(item),
                **_artifact_overlay(artifact_record),
            }
            store[item_id] = stored
            self.ownership[item_id] = owner
            audit = self.artifact_audit.setdefault(
                item_id,
                _artifact_audit_seed(item_id, store_name, owner, timestamp),
            )
            audit.update({
                "artifact_type": store_name,
                "producer_runtime": owner,
                "publication_time": stored["publication_time"],
                "current_state": "PUBLISHED",
                "lifecycle": stored.get("lifecycle") or stored.get("state") or "PUBLISHED",
                "lineage": stored.get("lineage", []),
                "confidence": stored.get("confidence"),
                "evidence_score": stored.get("evidence_score") or stored.get("support_score"),
                "artifact_id": stored.get("artifact_id"),
                "artifact_type": stored.get("artifact_type"),
                "artifact_version": stored.get("artifact_version"),
                "owner_runtime": stored.get("owner_runtime"),
                "origin_runtime": stored.get("origin_runtime"),
                "lifecycle_state": stored.get("lifecycle_state"),
                "validation_status": stored.get("validation_status"),
                "publication_status": stored.get("publication_status"),
                "consumption_status": stored.get("consumption_status"),
                "promotion_status": stored.get("promotion_status"),
                "archive_status": stored.get("archive_status"),
            })

    def _artifact_engine(self) -> ArtifactLifecycleEngine:
        return ArtifactLifecycleEngine(
            self.artifact_registry,
            self.artifact_lifecycle_events,
            self.artifact_validation_failures,
        )

    def build_artifact_lifecycle_report(self) -> dict[str, Any]:
        return self._artifact_engine().build_report()

    def build_cognitive_observability_report(self) -> dict[str, Any]:
        report = cognitive_runtime_observability_engine.build_report(self)
        self.runtime_observability_diagnostics.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": "cognitive_runtime_observability",
            "level_5_coverage": report.get("coverage", {}).get("level_5_coverage", 0.0),
            "gap_count": sum(
                len(value)
                for value in report.get("observability_gap_detection", {}).values()
                if isinstance(value, list)
            ),
        })
        self._sync_observable_cognition(report)
        return report

    def promote_artifacts(self, runtime_id: str = "artifact_governance") -> dict[str, Any]:
        report = ArtifactPromotionEngine(
            self._artifact_engine(),
            self.artifact_promotion_events,
            self.artifact_promotion_failures,
        ).evaluate_all(runtime_id=runtime_id)
        self._refresh_artifact_overlays()
        self._sync_stable_artifacts()
        return report

    def persist_artifacts(
        self,
        runtime_id: str = "artifact_persistence_layer",
        path: str | Path | None = None,
    ) -> dict[str, Any]:
        report = ArtifactPersistenceLayer(
            self.artifact_registry,
            self.artifact_persistence_store,
            self.artifact_persistence_events,
            path=path,
        ).persist_eligible(runtime_id=runtime_id)
        self._refresh_artifact_overlays()
        self._sync_stable_artifacts()
        return report

    def run_artifact_governance(
        self,
        runtime_id: str = "artifact_governance",
        persistence_path: str | Path | None = None,
    ) -> dict[str, Any]:
        promotion = self.promote_artifacts(runtime_id=runtime_id)
        persistence = self.persist_artifacts(
            runtime_id="artifact_persistence_layer",
            path=persistence_path,
        )
        economy = self.update_artifact_economy(runtime_id="artifact_economy_engine")
        return {
            "system": "artifact_governance",
            "ARTIFACT_GOVERNANCE_REPORT": True,
            "promotion": promotion,
            "persistence": persistence,
            "economy": economy,
            "flow": self.build_artifact_flow_report(),
            "governance_validates_only": True,
        }

    def update_artifact_economy(
        self,
        runtime_id: str = "artifact_economy_engine",
    ) -> dict[str, Any]:
        report = ArtifactEconomyEngine(
            self.artifact_registry,
            self.artifact_economy_events,
            self.artifact_reuse_events,
            self.artifact_relationships,
        ).update_all(runtime_id=runtime_id)
        self._refresh_artifact_overlays()
        self._sync_stable_artifacts()
        return report

    def record_artifact_experience(
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
        result = ArtifactEconomyEngine(
            self.artifact_registry,
            self.artifact_economy_events,
            self.artifact_reuse_events,
            self.artifact_relationships,
        ).record_experience(
            artifact_id,
            success=success,
            utility=utility,
            prediction_accuracy=prediction_accuracy,
            domain=domain,
            correction=correction,
            runtime_id=runtime_id,
        )
        self._refresh_artifact_overlays()
        self._sync_stable_artifacts()
        return result

    def discover_reusable_artifacts(
        self,
        query: Mapping[str, Any] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        self.update_artifact_economy(runtime_id="artifact_reuse_engine")
        return ArtifactEconomyEngine(
            self.artifact_registry,
            self.artifact_economy_events,
            self.artifact_reuse_events,
            self.artifact_relationships,
        ).recommend(query=query, limit=limit)

    def build_artifact_economy_report(self) -> dict[str, Any]:
        economy = ArtifactEconomyEngine(
            self.artifact_registry,
            self.artifact_economy_events,
            self.artifact_reuse_events,
            self.artifact_relationships,
        ).update_all()
        reuse = ArtifactEconomyEngine(
            self.artifact_registry,
            self.artifact_economy_events,
            self.artifact_reuse_events,
            self.artifact_relationships,
        ).recommend(limit=10)
        return {
            "system": "artifact_cognitive_economy",
            "ARTIFACT_ECONOMY_REPORT": True,
            "economy": economy,
            "reuse": reuse,
            "artifact_metrics": self._artifact_economy_metrics(),
            "meta_cognition": self._artifact_meta_cognition(),
            "world_model": {
                "mature_artifact_sources": self.world_model.get("committed_artifacts", []),
                "temporary_artifacts_excluded": True,
            },
            "dna": {
                "learns_from_artifact_populations": True,
                "stable_artifact_statistics": self.dna_state.get("artifact_statistics", {}),
                "temporary_hypotheses_excluded": True,
            },
        }

    def build_artifact_flow_report(self) -> dict[str, Any]:
        registry = self.artifact_registry
        lifecycle_counts = {}
        promotion_counts = {}
        for record in registry.values():
            lifecycle_counts[record.get("lifecycle_state", "UNKNOWN")] = (
                lifecycle_counts.get(record.get("lifecycle_state", "UNKNOWN"), 0) + 1
            )
            promotion_counts[record.get("promotion_stage", "CANDIDATE")] = (
                promotion_counts.get(record.get("promotion_stage", "CANDIDATE"), 0) + 1
            )
        promoted = [
            item for item in registry.values()
            if item.get("promotion_stage") not in {None, "CANDIDATE"}
        ]
        persisted = [
            item for item in registry.values()
            if item.get("persistence_status") in {"PERSISTENT", "LONG_TERM_MEMORY"}
        ]
        consumed = [
            item for item in registry.values()
            if item.get("consumption_status") == "CONSUMED"
        ]
        committed = [
            item for item in registry.values()
            if item.get("promotion_stage") in {"COMMITTED", "PERSISTENT", "LONG_TERM_MEMORY"}
            or item.get("lifecycle_state") == "COMMITTED"
        ]
        failures = self._artifact_failure_detection()
        return {
            "system": "artifact_flow_observability",
            "ARTIFACT_FLOW_REPORT": True,
            "artifacts_created": len(registry),
            "artifacts_published": lifecycle_counts.get("PUBLISHED", 0) + len(consumed) + len(promoted),
            "artifacts_consumed": len(consumed),
            "artifacts_validated": sum(
                1 for item in registry.values()
                if item.get("validation_status") == "VALIDATED"
            ),
            "artifacts_promoted": len(promoted),
            "artifacts_persisted": len(persisted),
            "artifacts_archived": lifecycle_counts.get("ARCHIVED", 0),
            "promotion_success_rate": round(
                len(promoted) / max(len(registry), 1),
                4,
            ),
            "promotion_failures": list(self.artifact_promotion_failures[-200:]),
            "lifecycle_violations": list(self.artifact_validation_failures[-200:]),
            "lineage_completeness": self._lineage_completeness(),
            "registry_consistency": self._artifact_engine().validate_registry(),
            "artifact_latency": self._artifact_latency_metrics(),
            "lifecycle_metrics": self._artifact_density_metrics(
                promoted=promoted,
                persisted=persisted,
                committed=committed,
            ),
            "failure_detection": failures,
            "world_model_integration": {
                "consumes_temporary_artifacts": False,
                "stable_artifact_count": len(self.world_model.get("committed_artifacts", [])),
            },
            "dna_integration": {
                "learns_from_temporary_hypotheses": False,
                "stable_artifact_count": len(self.dna_state.get("stable_artifacts", [])),
            },
            "promotion_states": promotion_counts,
        }

    def _refresh_artifact_overlays(self) -> None:
        for store in (
            self.concept_store,
            self.program_store,
            self.search_routes,
            self.evidence_store,
            self.context_store,
            self.dependency_graph,
            self.truth_candidates,
            self.validated_truths,
            self.memory_entries,
            self.knowledge_objects,
        ):
            for artifact_id, item in store.items():
                record = self.artifact_registry.get(artifact_id)
                if record:
                    item.update(_artifact_overlay(record))

    def _artifact_ids_for_runtime(
        self,
        runtime_id: str,
        owner: str,
        published_artifacts: Mapping[str, int],
    ) -> list[str]:
        store_by_count_key = {
            "concept_count": self.concept_store,
            "program_count": self.program_store,
            "search_route_count": self.search_routes,
            "evidence_count": self.evidence_store,
            "context_store_count": self.context_store,
            "dependency_count": self.dependency_graph,
            "truth_candidate_count": self.truth_candidates,
            "validated_truth_count": self.validated_truths,
            "memory_entry_count": self.memory_entries,
            "knowledge_object_count": self.knowledge_objects,
        }
        artifact_ids: list[str] = []
        for count_key, delta in published_artifacts.items():
            if int(delta or 0) <= 0:
                continue
            store = store_by_count_key.get(count_key)
            if not store:
                continue
            artifact_ids.extend(
                artifact_id
                for artifact_id, item in store.items()
                if item.get("owner") == owner
                or item.get("owner_runtime") == owner
                or item.get("origin_runtime") == runtime_id
            )
        return sorted(set(artifact_ids))

    def _sync_stable_artifacts(self) -> None:
        committed = [
            _small_mapping(record, limit=40)
            for record in self.artifact_registry.values()
            if record.get("promotion_stage") in {"COMMITTED", "PERSISTENT", "LONG_TERM_MEMORY"}
            and record.get("artifact_type") in {"KNOWLEDGE", "TRUTH", "CONTEXT", "DEPENDENCY", "MEMORY"}
        ]
        persistent = [
            _small_mapping(record, limit=40)
            for record in self.artifact_registry.values()
            if record.get("persistence_status") in {"PERSISTENT", "LONG_TERM_MEMORY"}
            and record.get("artifact_type") in {"KNOWLEDGE", "TRUTH", "MEMORY"}
        ]
        self.world_model["committed_artifacts"] = committed
        self.world_model["temporary_artifacts_excluded"] = True
        self.dna_state["stable_artifacts"] = persistent
        self.dna_state["temporary_hypotheses_excluded"] = True
        self.dna_state["artifact_statistics"] = self._artifact_economy_metrics()

    def _sync_observable_cognition(self, observability_report: Mapping[str, Any]) -> None:
        runtime_reports = observability_report.get("runtime_reports", {})
        if not isinstance(runtime_reports, Mapping):
            runtime_reports = {}
        level_5_runtimes = [
            runtime_id
            for runtime_id, report in runtime_reports.items()
            if isinstance(report, Mapping)
            and int(report.get("observability_level", 0) or 0) >= 5
        ]
        self.world_model["fully_observable_cognition"] = {
            "runtime_ids": level_5_runtimes,
            "runtime_count": len(level_5_runtimes),
            "knowledge_without_explainability_excluded": True,
        }
        self.world_model["opaque_cognition_excluded"] = True
        self.dna_state["observable_behavior_statistics"] = {
            "runtime_count": len(level_5_runtimes),
            "level_5_coverage": observability_report.get("coverage", {}).get(
                "level_5_coverage",
                0.0,
            ),
            "learns_only_from_explainable_behavior": True,
        }
        self.dna_state["opaque_execution_excluded"] = True

    def _artifact_failure_detection(self) -> dict[str, Any]:
        registry = self.artifact_registry
        never_consumed = [
            artifact_id for artifact_id, item in registry.items()
            if item.get("consumption_status") != "CONSUMED"
        ]
        never_promoted = [
            artifact_id for artifact_id, item in registry.items()
            if item.get("promotion_stage") in {None, "CANDIDATE"}
        ]
        promoted_without_evidence = [
            artifact_id for artifact_id, item in registry.items()
            if item.get("promotion_stage") not in {None, "CANDIDATE", "SUPPORTED"}
            and item.get("artifact_type") in {"TRUTH", "KNOWLEDGE", "MEMORY"}
            and not item.get("evidence_references")
        ]
        persisted_without_validation = [
            artifact_id for artifact_id, item in registry.items()
            if item.get("persistence_status") in {"PERSISTENT", "LONG_TERM_MEMORY"}
            and item.get("validation_status") != "VALIDATED"
        ]
        missing_lineage = [
            artifact_id for artifact_id, item in registry.items()
            if item.get("artifact_type") in {"EVIDENCE", "KNOWLEDGE", "TRUTH", "MEMORY"}
            and not item.get("lineage")
            and not item.get("evidence_references")
        ]
        duplicate_ids = [
            artifact_id for artifact_id, item in registry.items()
            if self.ownership.get(artifact_id) != item.get("owner_runtime")
        ]
        return {
            "artifacts_never_consumed": never_consumed[:100],
            "artifacts_never_promoted": never_promoted[:100],
            "artifacts_promoted_without_evidence": promoted_without_evidence[:100],
            "artifacts_persisted_without_validation": persisted_without_validation[:100],
            "artifacts_with_missing_lineage": missing_lineage[:100],
            "artifacts_with_broken_references": [
                item for item in self._artifact_engine().validate_registry().get("failures", [])
                if item.get("failure") == "broken_lineage"
            ][:100],
            "artifacts_duplicated_across_runtimes": duplicate_ids[:100],
            "artifacts_orphaned_in_registry": [
                artifact_id for artifact_id in registry
                if artifact_id not in self.ownership
            ][:100],
        }

    def _lineage_completeness(self) -> float:
        traceable = 0
        for item in self.artifact_registry.values():
            if (
                item.get("lineage")
                or item.get("evidence_references")
                or item.get("concept_references")
                or item.get("program_references")
                or item.get("route_references")
                or item.get("artifact_type") in {"CONCEPT", "CONTEXT"}
            ):
                traceable += 1
        return round(traceable / max(len(self.artifact_registry), 1), 4)

    def _artifact_latency_metrics(self) -> dict[str, Any]:
        durations = {
            "validation_delay": [],
            "consumption_delay": [],
            "promotion_delay": [],
            "persistence_delay": [],
            "average_artifact_lifetime": [],
        }
        for item in self.artifact_registry.values():
            created = item.get("creation_timestamp")
            durations["validation_delay"].append(_timestamp_delta_seconds(created, item.get("updated_timestamp")))
            durations["consumption_delay"].append(_timestamp_delta_seconds(created, item.get("consumption_time")))
            durations["promotion_delay"].append(_timestamp_delta_seconds(created, item.get("promotion_time")))
            durations["persistence_delay"].append(_timestamp_delta_seconds(created, item.get("persistence_time")))
            durations["average_artifact_lifetime"].append(_timestamp_delta_seconds(created, item.get("archive_time") or item.get("updated_timestamp")))
        return {
            key: _average([value for value in values if value is not None])
            for key, values in durations.items()
        }

    def _artifact_density_metrics(self, promoted, persisted, committed) -> dict[str, Any]:
        total = max(len(self.artifact_registry), 1)
        evidence_count = sum(
            1 for item in self.artifact_registry.values()
            if item.get("artifact_type") == "EVIDENCE"
        )
        truth_count = sum(
            1 for item in self.artifact_registry.values()
            if item.get("artifact_type") == "TRUTH"
        )
        memory_count = sum(
            1 for item in self.artifact_registry.values()
            if item.get("artifact_type") == "MEMORY"
        )
        return {
            "evidence_density": round(evidence_count / total, 4),
            "truth_density": round(truth_count / total, 4),
            "memory_density": round(memory_count / total, 4),
            "artifact_growth": total,
            "artifact_compression": round(
                len(self.artifact_persistence_store) / total,
                4,
            ),
            "artifact_survival_rate": round(len(committed) / total, 4),
            "artifact_reuse_rate": round(len(promoted) / total, 4),
            "persistent_artifact_rate": round(len(persisted) / total, 4),
        }

    def _artifact_economy_metrics(self) -> dict[str, Any]:
        total = max(len(self.artifact_registry), 1)
        values = list(self.artifact_registry.values())
        collaborations = [
            edge for edge in self.artifact_relationships
            if edge.get("relation") == "collaborates"
        ]
        competitions = [
            edge for edge in self.artifact_relationships
            if edge.get("relation") in {"competes", "contradicts"}
        ]
        successful = [
            item for item in values
            if int((item.get("artifact_experience") or {}).get("times_successful", 0)) > 0
        ]
        archived = [
            item for item in values
            if item.get("archive_status") == "ARCHIVED" or item.get("health_state") == "ARCHIVED"
        ]
        return {
            "reuse_rate": round(
                sum(1 for item in values if int(item.get("reuse_count", 0) or 0) > 0) / total,
                4,
            ),
            "artifact_utility": _average([
                _number(item.get("utility_score"))
                for item in values
            ]),
            "promotion_success": round(
                sum(1 for item in values if item.get("promotion_stage") not in {None, "CANDIDATE"}) / total,
                4,
            ),
            "generalization_rate": _average([
                _number(item.get("generalization_score"))
                for item in values
            ]),
            "prediction_success": _average([
                _number((item.get("artifact_experience") or {}).get("prediction_accuracy"))
                for item in values
            ]),
            "collaboration_rate": round(len(collaborations) / total, 4),
            "competition_resolution_rate": round(
                sum(1 for item in competitions if item.get("resolved")) / max(len(competitions), 1),
                4,
            ),
            "archive_rate": round(len(archived) / total, 4),
            "artifact_compression": round(len(self.artifact_persistence_store) / total, 4),
            "knowledge_density": round(
                sum(1 for item in values if item.get("artifact_type") in {"KNOWLEDGE", "TRUTH", "MEMORY"}) / total,
                4,
            ),
            "successful_artifact_count": len(successful),
        }

    def _artifact_meta_cognition(self) -> dict[str, Any]:
        values = list(self.artifact_registry.values())
        ranked = sorted(
            values,
            key=lambda item: (
                _number(item.get("cognitive_value")),
                _number(item.get("reuse_count")),
                _number(item.get("generalization_score")),
            ),
            reverse=True,
        )
        failing = [
            item.get("artifact_id") for item in values
            if item.get("health_state") in {"WEAK", "DEPRECATED", "CONFLICTING"}
        ]
        families = {}
        for item in values:
            families[item.get("artifact_type", "UNKNOWN")] = (
                families.get(item.get("artifact_type", "UNKNOWN"), 0) + 1
            )
        return {
            "widest_range_artifacts": [
                item.get("artifact_id") for item in ranked[:10]
            ],
            "consistently_failing_artifacts": failing[:25],
            "artifacts_should_evolve": [
                item.get("artifact_id") for item in values
                if item.get("health_state") in {"WEAK", "STABLE"}
                and item.get("promotion_stage") not in {"PERSISTENT", "LONG_TERM_MEMORY"}
            ][:25],
            "obsolete_artifacts": [
                item.get("artifact_id") for item in values
                if item.get("health_state") in {"DEPRECATED", "ARCHIVED"}
            ][:25],
            "dominant_artifact_families": dict(
                sorted(families.items(), key=lambda pair: pair[1], reverse=True)
            ),
        }

    def _extract_common_state(self, data: Mapping[str, Any]) -> None:
        for key in ("world_model", "world_model_report", "WORLD_GOVERNANCE_REPORT"):
            if isinstance(data.get(key), Mapping):
                self.world_model[key] = _small_mapping(data[key], limit=60)
        for key in ("dna_state", "DNA_REPORT", "constitutional_dna"):
            if isinstance(data.get(key), Mapping):
                self.dna_state[key] = _small_mapping(data[key], limit=60)
        for key in ("runtime_metrics", "canonical_metrics", "execution_statistics"):
            if isinstance(data.get(key), Mapping):
                self.runtime_metrics.update(_small_mapping(data[key], limit=80))

    def _ownership_integrity(self) -> bool:
        stores = (
            self.concept_store,
            self.program_store,
            self.search_routes,
            self.truth_candidates,
            self.memory_entries,
            self.knowledge_objects,
            self.evidence_store,
            self.context_store,
            self.dependency_graph,
            self.validated_truths,
        )
        return all(
            self.ownership.get(str(item.get("id") or item_id))
            for store in stores
            for item_id, item in store.items()
        )

    def _coverage_score(self) -> float:
        required = {
            "reasoning_runtime",
            "search_runtime",
            "concept_formation_runtime",
            "program_synthesis_runtime",
            "adaptive_search_intelligence_runtime",
            "knowledge_integration_runtime",
            "truth_runtime",
            "memory_runtime",
        }
        observed = {event["runtime_id"] for event in self.propagation_events}
        return round(len(required & observed) / len(required), 4)

    def _missing_references(self) -> list[dict[str, str]]:
        missing = []
        for program_id, program in self.program_store.items():
            for concept_id in _as_list(program.get("supporting_concepts")):
                if concept_id and concept_id not in self.concept_store:
                    missing.append({
                        "source": program_id,
                        "missing": str(concept_id),
                        "reference_type": "concept",
                    })
        for evidence_id, evidence in self.evidence_store.items():
            for concept_id in _as_list(evidence.get("supporting_concepts")):
                if concept_id and concept_id not in self.concept_store:
                    missing.append({
                        "source": evidence_id,
                        "missing": str(concept_id),
                        "reference_type": "evidence_concept",
                    })
            for program_id in _as_list(evidence.get("supporting_programs")):
                if program_id and program_id not in self.program_store:
                    missing.append({
                        "source": evidence_id,
                        "missing": str(program_id),
                        "reference_type": "evidence_program",
                    })
            for route_id in _as_list(evidence.get("supporting_routes")):
                if route_id and route_id not in self.search_routes:
                    missing.append({
                        "source": evidence_id,
                        "missing": str(route_id),
                        "reference_type": "evidence_route",
                    })
        return missing

    def _cross_runtime_references(self) -> dict[str, Any]:
        return {
            "concepts_available_to_programs": bool(self.concept_store),
            "programs_available_to_search": bool(self.program_store),
            "search_available_to_evidence_builder": bool(self.search_routes),
            "search_available_to_truth": False,
            "evidence_available_to_truth": bool(self.evidence_store),
            "context_available_to_truth": bool(self.context_store),
            "truth_available_to_memory": bool(self.truth_candidates),
            "validated_truth_available_to_memory": bool(self.validated_truths),
            "memory_available_to_reasoning": bool(self.memory_entries),
            "knowledge_graph_available": bool(self.knowledge_graph),
            "truth_raw_artifact_access_forbidden": True,
        }

    def _evidence_architecture_summary(self) -> dict[str, Any]:
        evidence = list(self.evidence_store.values())
        categories = sorted({
            str(item.get("evidence_type") or item.get("category") or "uncategorized")
            for item in evidence
        })
        confidence_values = [
            _number(item.get("confidence"))
            for item in evidence
            if item.get("confidence") is not None
        ]
        return {
            "evidence_layer_present": True,
            "evidence_builder_runtime_observed": any(
                event["runtime_id"] == "evidence_builder_runtime"
                for event in self.propagation_events
            ),
            "truth_consumes_raw_concepts": False,
            "truth_consumes_evidence_store": bool(self.evidence_store),
            "evidence_categories": categories,
            "average_confidence": round(
                sum(confidence_values) / max(len(confidence_values), 1),
                4,
            ),
        }


class CognitiveKnowledgeBus:
    """Thin bus facade over the authoritative shared cognitive state."""

    def __init__(self, state: SharedCognitiveState) -> None:
        self.state = state

    def publish(
        self,
        runtime_id: str,
        payload: Mapping[str, Any] | None,
        owner: str,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.state.publish(runtime_id, payload, owner=owner, context=context)

    def consume(
        self,
        runtime_id: str,
        artifact_types: tuple[str, ...] | list[str],
        required: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        return self.state.consume(runtime_id, artifact_types, required=required)

    def query(self, artifact_type: str, limit: int | None = None) -> dict[str, Any]:
        return self.state.query(artifact_type, limit=limit)

    def subscribe(self, runtime_id: str, artifact_types: tuple[str, ...] | list[str]) -> None:
        self.state.subscribe(runtime_id, artifact_types)

    def broadcast(self, artifact_types: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
        return self.state.broadcast(artifact_types)

    def report(self) -> dict[str, Any]:
        return self.state.build_knowledge_propagation_report()


def _extract_concepts(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _items(data, "discovered_concepts", "top_concepts", "validated_concepts", "concepts")
    count = int(_number(data.get("generated_concepts") or data.get("concept_count")))
    return _with_placeholders(items, count, "concept")


def _extract_programs(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _items(data, "generated_program_objects", "winning_programs", "programs")
    count = int(_number(data.get("generated_programs") or data.get("program_candidates")))
    return _with_placeholders(items, count, "program")


def _extract_routes(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    routes = []
    routes.extend(_items(data, "route_ranking", "search_routes", "paths"))
    cognitive_routes = data.get("cognitive_routes")
    if isinstance(cognitive_routes, Mapping):
        routes.extend(dict(item) for item in cognitive_routes.values() if isinstance(item, Mapping))
    count = int(_number(data.get("search_routes")))
    return _with_placeholders(routes, count, "route")


def _extract_evidence(data: Mapping[str, Any], runtime_id: str) -> list[dict[str, Any]]:
    items = _items(
        data,
        "evidence",
        "evidence_objects",
        "supporting_evidence",
        "runtime_evidence",
        "knowledge_evidence",
    )
    return _with_placeholders(items, int(_number(data.get("evidence_count"))), "evidence")


def _has_explicit_evidence(data: Mapping[str, Any]) -> bool:
    return any(
        key in data
        for key in (
            "evidence",
            "evidence_objects",
            "supporting_evidence",
            "runtime_evidence",
            "knowledge_evidence",
        )
    )


def _extract_contexts(data: Mapping[str, Any], runtime_id: str) -> list[dict[str, Any]]:
    items = _items(
        data,
        "contexts",
        "context_objects",
        "context_fragments",
        "semantic_contexts",
        "causal_contexts",
    )
    for key, value in data.items():
        key_text = str(key).lower()
        if "context" not in key_text:
            continue
        if isinstance(value, Mapping):
            items.append({
                "id": f"context:{runtime_id}:{key}",
                "context_type": key,
                "origin_runtime": runtime_id,
                "summary": _small_mapping(value, limit=30),
            })
        elif isinstance(value, list):
            for index, item in enumerate(value[:50]):
                if isinstance(item, Mapping):
                    items.append({
                        **dict(item),
                        "id": str(item.get("id") or f"context:{runtime_id}:{key}:{index}"),
                        "context_type": key,
                        "origin_runtime": runtime_id,
                    })
    if data:
        items.append({
            "id": f"context:{runtime_id}:execution",
            "context_type": "execution_context",
            "origin_runtime": runtime_id,
            "summary": _small_mapping(data, limit=20),
        })
    return items


def _extract_dependencies(data: Mapping[str, Any], runtime_id: str) -> list[dict[str, Any]]:
    items = _items(
        data,
        "dependencies",
        "dependency_objects",
        "dependency_edges",
        "dependency_references",
    )
    graph = data.get("dependency_graph")
    if isinstance(graph, Mapping):
        edges = graph.get("edges")
        if isinstance(edges, list):
            items.extend(dict(item) for item in edges if isinstance(item, Mapping))
        else:
            items.append({
                "id": f"dependency:{runtime_id}:graph",
                "origin_runtime": runtime_id,
                "summary": _small_mapping(graph, limit=30),
            })
    return [
        {
            **item,
            "id": str(item.get("id") or _id("dependency", runtime_id, item)),
            "origin_runtime": item.get("origin_runtime") or runtime_id,
        }
        for item in items
    ]


def _extract_truths(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _items(
        data,
        "truth_candidates",
        "truth_candidate_evaluations",
        "truth_commits",
        "truth_commit_evaluations",
        "validated_truths",
        "evaluations",
    )
    count = int(_number(data.get("truth_candidate_count") or data.get("generated_truth_candidates")))
    return _with_placeholders(items, count, "truth")


def _extract_validated_truths(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _items(
        data,
        "validated_truths",
        "truth_commits",
        "truth_commit_evaluations",
        "committed_truths",
        "truths",
    )
    return _with_placeholders(items, int(_number(data.get("validated_truth_count"))), "validated_truth")


def _extract_memory(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _items(data, "memory_entries", "retrieved_concepts", "retrieved_programs")
    if data:
        items.append({"id": "memory:summary", "summary": _small_mapping(data, limit=20)})
    return items


def _extract_knowledge_objects(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _items(data, "knowledge_objects")
    return [
        {**item, "id": str(item.get("knowledge_id") or item.get("id") or _id("knowledge", item))}
        for item in items
    ]


def _items(data: Mapping[str, Any], *keys: str) -> list[dict[str, Any]]:
    output = []
    for key in keys:
        value = data.get(key)
        if isinstance(value, Mapping):
            output.extend(dict(item) for item in value.values() if isinstance(item, Mapping))
        elif isinstance(value, list):
            output.extend(dict(item) for item in value if isinstance(item, Mapping))
    return output


def _with_placeholders(items: list[dict[str, Any]], count: int, prefix: str) -> list[dict[str, Any]]:
    output = list(items)
    missing = max(count - len(output), 0)
    for index in range(missing):
        output.append({"id": f"{prefix}:generated:{index}", "placeholder": True})
    return [
        {**item, "id": str(item.get("id") or item.get(f"{prefix}_id") or item.get("knowledge_id") or _id(prefix, item))}
        for item in output
    ]


def _delta_artifacts(before: Mapping[str, int], after: Mapping[str, int]) -> dict[str, int]:
    return {
        key: after.get(key, 0) - before.get(key, 0)
        for key in after
    }


def _artifact_audit_seed(
    artifact_id: str,
    artifact_type: str,
    producer_runtime: str,
    timestamp: str,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "producer_runtime": producer_runtime,
        "consumers": [],
        "publication_time": timestamp,
        "consumption_time": None,
        "propagation_delay_seconds": None,
        "current_state": "PUBLISHED",
        "lifecycle": "PUBLISHED",
        "lineage": [],
    }


def _artifact_overlay(record: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "artifact_id",
        "artifact_type",
        "artifact_version",
        "execution_id",
        "task_id",
        "owner_runtime",
        "origin_runtime",
        "creation_timestamp",
        "current_stage",
        "lifecycle_state",
        "confidence",
        "reliability",
        "priority",
        "evidence_references",
        "context_references",
        "dependency_references",
        "concept_references",
        "program_references",
        "route_references",
        "knowledge_references",
        "parent_artifact",
        "child_artifacts",
        "metadata",
        "validation_status",
        "publication_status",
        "consumption_status",
        "promotion_status",
        "archive_status",
        "promotion_stage",
        "promotion_score",
        "promotion_history",
        "persistence_status",
        "promotion_time",
        "persistence_time",
        "commit_time",
        "archive_time",
        "cognitive_value",
        "utility_score",
        "evidence_density",
        "reuse_count",
        "generalization_score",
        "novelty_score",
        "compression_value",
        "prediction_value",
        "learning_contribution",
        "health_score",
        "health_state",
        "reuse_priority",
        "artifact_experience",
        "times_reused",
        "times_successful",
        "times_failed",
        "prediction_accuracy",
        "correction_count",
        "average_utility",
        "historical_confidence",
        "immutable",
    )
    overlay = {key: record.get(key) for key in keys if key in record}
    if "lineage" in record:
        overlay["artifact_lineage"] = record.get("lineage")
    return overlay


def _lineage_for(item: Mapping[str, Any]) -> list[Any]:
    for key in (
        "lineage",
        "supporting_evidence",
        "supporting_concepts",
        "supporting_programs",
        "supporting_routes",
        "parent_concepts",
        "dependencies",
    ):
        value = item.get(key)
        if isinstance(value, list):
            return value[:50]
    parent = item.get("parent") or item.get("parent_id") or item.get("source")
    return [parent] if parent else []


def _coverage(count: int) -> float:
    return 1.0 if count > 0 else 0.0


def _timestamp_delta_seconds(start: Any, end: Any) -> float | None:
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    try:
        started = datetime.fromisoformat(start)
        ended = datetime.fromisoformat(end)
    except ValueError:
        return None
    return round(max((ended - started).total_seconds(), 0.0), 9)


def _average(values: list[float]) -> float:
    return round(sum(values) / max(len(values), 1), 9) if values else 0.0


def _small_mapping(value: Mapping[str, Any], limit: int = 40) -> dict[str, Any]:
    output = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= limit:
            break
        if isinstance(item, (str, int, float, bool)) or item is None:
            output[str(key)] = item
        elif isinstance(item, Mapping):
            output[str(key)] = {
                "key_count": len(item),
                "keys": sorted(str(k) for k in item.keys())[:20],
            }
        elif isinstance(item, list):
            output[str(key)] = {"count": len(item)}
        else:
            output[str(key)] = type(item).__name__
    return output


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _id(prefix: str, *values: Any) -> str:
    return f"{prefix}:{hashlib.sha1(json.dumps(values, sort_keys=True, default=str).encode('utf-8')).hexdigest()[:12]}"


__all__ = ["CognitiveKnowledgeBus", "SharedCognitiveState", "STATE_PATH"]
