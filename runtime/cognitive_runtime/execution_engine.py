"""Lifecycle-backed execution instances for first-class cognitive runtimes."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Iterator, Mapping
import sys

from runtime.cognitive_runtime.snapshots import (
    runtime_snapshot_consumer,
    RuntimeSnapshotProducer,
    supported_snapshot_types,
)
from runtime.instrumentation import runtime_lifecycle
from runtime.metrics.runtime_metric_attribution_engine import (
    runtime_metric_attribution_engine,
)
from runtime.truth.truth_metric_synchronization_engine import (
    truth_metric_synchronization_engine,
)
from runtime.timing import execution_timing_unification_engine


RUNTIME_TYPES = {
    "execution_runtime": ("ExecutionExecution", "Execution Runtime"),
    "reasoning_runtime": ("ReasoningExecution", "Reasoning Runtime"),
    "search_runtime": ("SearchExecution", "Search Runtime"),
    "concept_formation_runtime": (
        "ConceptFormationExecution",
        "Concept Formation Runtime",
    ),
    "program_synthesis_runtime": (
        "ProgramSynthesisExecution",
        "Program Synthesis Runtime",
    ),
    "adaptive_search_intelligence_runtime": (
        "AdaptiveSearchIntelligenceExecution",
        "Adaptive Search Intelligence Runtime",
    ),
    "evidence_builder_runtime": (
        "EvidenceBuilderExecution",
        "Evidence Builder Runtime",
    ),
    "acsc_runtime": (
        "AdaptiveCognitiveSuperCoolingExecution",
        "Adaptive Cognitive Super Cooling Runtime",
    ),
    "knowledge_integration_runtime": (
        "CognitiveKnowledgeIntegrationExecution",
        "Cognitive Knowledge Integration Runtime",
    ),
    "memory_runtime": ("MemoryExecution", "Memory Runtime"),
    "truth_runtime": ("TruthExecution", "Truth Runtime"),
    "evaluation_runtime": ("EvaluationExecution", "Evaluation Runtime"),
    "dependency_runtime": ("DependencyExecution", "Dependency Runtime"),
    "process_runtime": ("ProcessExecution", "Process Runtime"),
    "causal_runtime": ("CausalExecution", "Causal Runtime"),
    "reuse_runtime": ("ReuseExecution", "Reuse Runtime"),
}


@dataclass
class CognitiveExecutionInstance:
    """One execution-cycle object; identity never changes or gets reused."""

    execution_id: str
    execution_type: str
    runtime_id: str
    runtime_name: str
    execution_parent: str | None
    execution_children: list[str]
    execution_context: dict[str, Any]
    execution_trigger: str
    execution_reason: str
    execution_mode: str
    creation_timestamp: str
    start_timestamp: str | None = None
    end_timestamp: str | None = None
    duration_seconds: float = 0.0
    cpu_time: float = 0.0
    memory_usage: int = 0
    concept_cost: float = 0.0
    search_cost: float = 0.0
    overall_search_quality: float = 0.0
    search_efficiency: float = 0.0
    search_coverage: float = 0.0
    search_entropy: float = 0.0
    average_route_quality: float = 0.0
    analytics_generation_success: bool = False
    confidence: float = 0.0
    completion_status: str = "CREATED"
    completion_reason: str = ""
    failure_reason: Any = None
    concept_count: int = 0
    search_routes: int = 0
    generated_programs: int = 0
    program_confidence: float = 0.0
    average_program_confidence: float = 0.0
    highest_program_confidence: float = 0.0
    lowest_program_confidence: float = 0.0
    confidence_distribution: dict[str, int] = field(default_factory=dict)
    validated_program_count: int = 0
    low_confidence_program_count: int = 0
    high_confidence_program_count: int = 0
    generated_concepts: int = 0
    generated_truth_candidates: int = 0
    validated_truth: int = 0
    promoted_truth: int = 0
    committed_truth: int = 0
    rejected_truth: int = 0
    truth_confidence: float = 0.0
    truth_validation_count: int = 0
    truth_lifecycle_statistics: dict[str, Any] = field(default_factory=dict)
    generated_memory_entries: int = 0
    lifecycle_events: list[dict[str, Any]] = field(default_factory=list)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)
    binding_status: str = "PENDING"
    archived: bool = False
    _lifecycle_execution: Any = field(default=None, repr=False, compare=False)

    def capture(self, payload: Mapping[str, Any] | None) -> None:
        data = payload if isinstance(payload, Mapping) else {}
        self.memory_usage = max(self.memory_usage, _deep_size(data))
        self.confidence = max(
            self.confidence,
            _number(data.get("confidence")),
            _number(data.get("confidence_score")),
        )
        self.concept_count = max(
            self.concept_count,
            _count(data.get("concepts")),
            int(_number(data.get("concept_count"))),
        )
        self.generated_concepts = max(
            self.generated_concepts,
            _count(data.get("generated_concepts")),
            self.concept_count,
        )
        self.search_routes = max(
            self.search_routes,
            int(_number(data.get("search_routes"))),
            int(_number((data.get("route_statistics") or {}).get("routes_created")))
            if isinstance(data.get("route_statistics"), Mapping) else 0,
        )
        self.generated_programs = max(
            self.generated_programs,
            _count(data.get("generated_programs")),
            int(_number(data.get("generated_programs"))),
            int(_number(data.get("program_candidates"))),
            _count(data.get("programs")),
            _count(data.get("generated_program_objects")),
            int(bool(data.get("synthesized_program"))),
        )
        confidence_report = (
            data.get("program_confidence")
            if isinstance(data.get("program_confidence"), Mapping)
            else {}
        )
        program_confidence = max(
            _number(data.get("program_confidence")),
            _number(data.get("average_program_confidence")),
            _number(confidence_report.get("average_program_confidence")),
            _average(
                _number(item.get("confidence"))
                for item in data.get("generated_program_objects", [])
                if isinstance(item, Mapping)
            ) if isinstance(data.get("generated_program_objects"), list) else 0.0,
        )
        self.program_confidence = max(self.program_confidence, program_confidence)
        self.average_program_confidence = max(
            self.average_program_confidence,
            program_confidence,
        )
        self.highest_program_confidence = max(
            self.highest_program_confidence,
            _number(data.get("highest_program_confidence")),
            _number(confidence_report.get("highest_program_confidence")),
            program_confidence,
        )
        lowest = max(
            _number(data.get("lowest_program_confidence")),
            _number(confidence_report.get("lowest_program_confidence")),
        )
        if lowest > 0.0:
            self.lowest_program_confidence = (
                lowest
                if self.lowest_program_confidence <= 0.0
                else min(self.lowest_program_confidence, lowest)
            )
        distribution = (
            data.get("confidence_distribution")
            or confidence_report.get("confidence_distribution")
        )
        if isinstance(distribution, Mapping):
            for level, count in distribution.items():
                self.confidence_distribution[str(level)] = (
                    self.confidence_distribution.get(str(level), 0)
                    + int(_number(count))
                )
        self.validated_program_count = max(
            self.validated_program_count,
            int(_number(data.get("validated_program_count"))),
            int(_number(confidence_report.get("validated_program_count"))),
        )
        self.low_confidence_program_count = max(
            self.low_confidence_program_count,
            int(_number(data.get("low_confidence_program_count"))),
            int(_number(confidence_report.get("low_confidence_program_count"))),
        )
        self.high_confidence_program_count = max(
            self.high_confidence_program_count,
            int(_number(data.get("high_confidence_program_count"))),
            int(_number(confidence_report.get("high_confidence_program_count"))),
        )
        evaluation_truths = (
            _count(data.get("evaluations"))
            if self.runtime_id == "truth_runtime"
            else 0
        )
        self.generated_truth_candidates = max(
            self.generated_truth_candidates,
            _count(data.get("truth_candidates")),
            int(_number(data.get("truth_candidate_count"))),
            int(_number(data.get("generated_truth_candidates"))),
            evaluation_truths,
        )
        if self.runtime_id == "truth_runtime":
            self.validated_truth = max(
                self.validated_truth,
                _count(data.get("validated_truth")),
                _count(data.get("validated_truths")),
                int(_number(data.get("truth_validation_count"))),
            )
            self.promoted_truth = max(
                self.promoted_truth,
                _count(data.get("promoted_truth")),
                _count(data.get("promoted_truths")),
                int(_number(data.get("promoted_truth_count"))),
            )
            self.committed_truth = max(
                self.committed_truth,
                _count(data.get("committed_truth")),
                _count(data.get("committed_truths")),
                _count(data.get("truth_commits")),
                int(_number(data.get("committed_truth_count"))),
            )
            self.rejected_truth = max(
                self.rejected_truth,
                _count(data.get("rejected_truth")),
                _count(data.get("rejected_truths")),
                int(_number(data.get("rejected_truth_count"))),
            )
            self.truth_confidence = max(
                self.truth_confidence,
                _number(data.get("truth_confidence")),
                _average(
                    _number(item.get("truth_confidence", item.get("confidence", 0.0)))
                    for item in data.get("truth_candidates", [])
                    if isinstance(item, Mapping)
                ) if isinstance(data.get("truth_candidates"), list) else 0.0,
                _average(
                    _number(item.get("truth_confidence", item.get("confidence", 0.0)))
                    for item in data.get("committed_truths", [])
                    if isinstance(item, Mapping)
                ) if isinstance(data.get("committed_truths"), list) else 0.0,
            )
            self.truth_validation_count = max(
                self.truth_validation_count,
                int(_number(data.get("truth_validation_count"))),
                self.validated_truth,
            )
            lifecycle_statistics = data.get("truth_lifecycle_statistics")
            if isinstance(lifecycle_statistics, Mapping):
                self.truth_lifecycle_statistics = dict(lifecycle_statistics)
        self.generated_memory_entries = max(
            self.generated_memory_entries,
            int(_number(data.get("entries_stored"))),
            _count(data.get("memory_entries")),
        )
        self.concept_cost = max(
            self.concept_cost,
            _number(data.get("concept_cost")),
            _number(data.get("semantic_cost")),
        )
        search_cost = data.get("search_cost")
        self.search_cost = max(
            self.search_cost,
            _number(search_cost.get("total_search_cost"))
            if isinstance(search_cost, Mapping) else _number(search_cost),
            _number(data.get("search_cost")),
        )
        analytics_report = (
            data.get("search_analytics")
            if isinstance(data.get("search_analytics"), Mapping)
            else {}
        )
        route_stats = (
            data.get("route_statistics")
            if isinstance(data.get("route_statistics"), Mapping)
            else {}
        )
        self.overall_search_quality = max(
            self.overall_search_quality,
            _number(data.get("overall_search_quality")),
            _number(analytics_report.get("overall_search_quality")),
            _number(route_stats.get("overall_search_quality")),
        )
        self.search_efficiency = max(
            self.search_efficiency,
            _number(data.get("search_efficiency")),
            _number(analytics_report.get("search_efficiency")),
            _number(route_stats.get("search_efficiency")),
        )
        self.search_coverage = max(
            self.search_coverage,
            _number(data.get("search_coverage")),
            _number(analytics_report.get("search_coverage")),
            _number(route_stats.get("search_coverage")),
        )
        self.search_entropy = max(
            self.search_entropy,
            _number(data.get("search_entropy")),
            _number(analytics_report.get("search_entropy")),
            _number(route_stats.get("search_entropy")),
        )
        self.average_route_quality = max(
            self.average_route_quality,
            _number(data.get("average_route_quality")),
            _number(analytics_report.get("average_route_quality")),
            _number(route_stats.get("average_route_quality")),
        )
        self.analytics_generation_success = (
            self.analytics_generation_success
            or bool(data.get("analytics_generation_success"))
            or bool(analytics_report.get("analytics_generation_success"))
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "execution_type": self.execution_type,
            "runtime_id": self.runtime_id,
            "runtime_name": self.runtime_name,
            "execution_parent": self.execution_parent,
            "execution_children": list(self.execution_children),
            "execution_context": dict(self.execution_context),
            "execution_trigger": self.execution_trigger,
            "execution_reason": self.execution_reason,
            "execution_mode": self.execution_mode,
            "creation_timestamp": self.creation_timestamp,
            "execution_start": self.start_timestamp,
            "execution_end": self.end_timestamp,
            "duration_seconds": self.duration_seconds,
            "elapsed_seconds": self.duration_seconds,
            "cpu_time": self.cpu_time,
            "memory_cost": self.memory_usage,
            "memory_usage": self.memory_usage,
            "concept_cost": self.concept_cost,
            "search_cost": self.search_cost,
            "overall_search_quality": self.overall_search_quality,
            "search_efficiency": self.search_efficiency,
            "search_coverage": self.search_coverage,
            "search_entropy": self.search_entropy,
            "average_route_quality": self.average_route_quality,
            "analytics_generation_success": self.analytics_generation_success,
            "confidence": self.confidence,
            "status": self.completion_status,
            "completion_status": self.completion_status,
            "completion_reason": self.completion_reason,
            "failure_reason": self.failure_reason,
            "concept_count": self.concept_count,
            "search_routes": self.search_routes,
            "generated_programs": self.generated_programs,
            "program_confidence": self.program_confidence,
            "average_program_confidence": self.average_program_confidence,
            "highest_program_confidence": self.highest_program_confidence,
            "lowest_program_confidence": self.lowest_program_confidence,
            "confidence_distribution": dict(self.confidence_distribution),
            "validated_program_count": self.validated_program_count,
            "low_confidence_program_count": self.low_confidence_program_count,
            "high_confidence_program_count": self.high_confidence_program_count,
            "generated_concepts": self.generated_concepts,
            "generated_truth_candidates": self.generated_truth_candidates,
            "truth_candidates": self.generated_truth_candidates,
            "validated_truth": self.validated_truth,
            "promoted_truth": self.promoted_truth,
            "committed_truth": self.committed_truth,
            "rejected_truth": self.rejected_truth,
            "truth_confidence": self.truth_confidence,
            "truth_validation_count": self.truth_validation_count,
            "truth_lifecycle_statistics": dict(self.truth_lifecycle_statistics),
            "generated_memory_entries": self.generated_memory_entries,
            "lifecycle_events": [dict(event) for event in self.lifecycle_events],
            "snapshots": [dict(snapshot) for snapshot in self.snapshots],
            "telemetry": dict(self.telemetry),
            "binding_status": self.binding_status,
            "archived": self.archived,
        }


class CognitiveExecutionRegistry:
    """Dedicated active/completed/archived execution registry."""

    def __init__(self) -> None:
        self.executions: dict[str, CognitiveExecutionInstance] = {}
        self.active_execution_ids: set[str] = set()
        self.completed_execution_ids: set[str] = set()
        self.archived_execution_ids: set[str] = set()

    def clear(self) -> None:
        self.executions.clear()
        self.active_execution_ids.clear()
        self.completed_execution_ids.clear()
        self.archived_execution_ids.clear()

    def register(self, instance: CognitiveExecutionInstance) -> None:
        if instance.execution_id in self.executions:
            raise ValueError(f"Duplicate execution_id: {instance.execution_id}")
        self.executions[instance.execution_id] = instance
        self.active_execution_ids.add(instance.execution_id)

    def complete(self, instance: CognitiveExecutionInstance) -> None:
        self.active_execution_ids.discard(instance.execution_id)
        self.completed_execution_ids.add(instance.execution_id)

    def archive(self, instance: CognitiveExecutionInstance) -> None:
        self.active_execution_ids.discard(instance.execution_id)
        self.completed_execution_ids.add(instance.execution_id)
        self.archived_execution_ids.add(instance.execution_id)

    def by_runtime(self, runtime_id: str) -> list[CognitiveExecutionInstance]:
        return [
            instance for instance in self.executions.values()
            if instance.runtime_id == runtime_id
        ]

    def execution_tree(self) -> list[dict[str, Any]]:
        nodes = {
            execution_id: {
                "execution_id": execution_id,
                "execution_type": instance.execution_type,
                "runtime_id": instance.runtime_id,
                "status": instance.completion_status,
                "duration_seconds": instance.duration_seconds,
                "generated_programs": instance.generated_programs,
                "program_confidence": instance.program_confidence,
                "average_program_confidence": instance.average_program_confidence,
                "highest_program_confidence": instance.highest_program_confidence,
                "lowest_program_confidence": instance.lowest_program_confidence,
                "confidence_distribution": dict(instance.confidence_distribution),
                "validated_program_count": instance.validated_program_count,
                "low_confidence_program_count": instance.low_confidence_program_count,
                "high_confidence_program_count": instance.high_confidence_program_count,
                "generated_concepts": instance.generated_concepts,
                "generated_truth_candidates": instance.generated_truth_candidates,
                "generated_memory_entries": instance.generated_memory_entries,
                "search_routes": instance.search_routes,
                "overall_search_quality": instance.overall_search_quality,
                "search_efficiency": instance.search_efficiency,
                "search_coverage": instance.search_coverage,
                "search_entropy": instance.search_entropy,
                "average_route_quality": instance.average_route_quality,
                "analytics_generation_success": instance.analytics_generation_success,
                "concept_count": instance.concept_count,
                "snapshot_count": len(instance.snapshots),
                "latest_snapshot": (
                    dict(instance.snapshots[-1])
                    if instance.snapshots else None
                ),
                "children": [],
            }
            for execution_id, instance in self.executions.items()
        }
        roots = []
        for execution_id, instance in self.executions.items():
            parent = instance.execution_parent
            if parent and parent in nodes:
                nodes[parent]["children"].append(nodes[execution_id])
            else:
                roots.append(nodes[execution_id])
        return roots


class RuntimeExecutionFactory:
    """Create, lifecycle-attach, register, and finalize execution instances."""

    def __init__(self, registry: CognitiveExecutionRegistry) -> None:
        self.registry = registry
        self.overhead_seconds = 0.0

    def create(
        self,
        runtime_id: str,
        parent_execution: str | None = None,
        context: Mapping[str, Any] | None = None,
        trigger: str = "runtime_execution",
        reason: str = "execute cognitive runtime",
        mode: str = "adaptive",
    ) -> CognitiveExecutionInstance:
        overhead_started = perf_counter()
        execution_type, runtime_name = RUNTIME_TYPES[runtime_id]
        lifecycle_execution = runtime_lifecycle.create(
            module_name=execution_type,
            runtime_name=runtime_name,
            parent_execution=parent_execution,
            caller="cognitive_runtime_execution_engine",
            trigger=trigger,
            metadata={"runtime_id": runtime_id, "execution_type": execution_type},
        )
        instance = CognitiveExecutionInstance(
            execution_id=lifecycle_execution.execution_id,
            execution_type=execution_type,
            runtime_id=runtime_id,
            runtime_name=runtime_name,
            execution_parent=parent_execution,
            execution_children=[],
            execution_context=dict(context or {}),
            execution_trigger=trigger,
            execution_reason=reason,
            execution_mode=mode,
            creation_timestamp=lifecycle_execution.created_at,
            _lifecycle_execution=lifecycle_execution,
        )
        self.registry.register(instance)
        if parent_execution and parent_execution in self.registry.executions:
            self.registry.executions[parent_execution].execution_children.append(
                instance.execution_id
            )
        self._publish_snapshot(
            instance,
            self._snapshot(instance, self._initial_snapshot_type(runtime_id), "CREATED"),
        )
        runtime_lifecycle.requested(lifecycle_execution)
        runtime_lifecycle.queued(lifecycle_execution)
        runtime_lifecycle.started(lifecycle_execution)
        runtime_lifecycle.running(lifecycle_execution)
        instance.start_timestamp = lifecycle_execution.start_timestamp
        instance.completion_status = "RUNNING"
        self._sync(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)
        return instance

    def checkpoint(self, instance: CognitiveExecutionInstance, reason: str) -> None:
        overhead_started = perf_counter()
        runtime_lifecycle.checkpoint(
            instance._lifecycle_execution,
            metadata={"reason": reason},
        )
        self._publish_snapshot(
            instance,
            self._snapshot(
                instance,
                self._checkpoint_snapshot_type(instance),
                "CHECKPOINT",
                reason,
            ),
        )
        self._sync(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)

    def complete(self, instance: CognitiveExecutionInstance, reason: str = "completed") -> None:
        overhead_started = perf_counter()
        runtime_lifecycle.completed(
            instance._lifecycle_execution,
            completion_reason=reason,
            memory_cost=instance.memory_usage,
        )
        runtime_lifecycle.validated(instance._lifecycle_execution)
        instance.completion_status = "VALIDATED"
        instance.completion_reason = reason
        self._sync(instance)
        for snapshot_type in self._completion_snapshot_types(instance):
            self._publish_snapshot(
                instance,
                self._snapshot(instance, snapshot_type, instance.completion_status, reason),
            )
        self.registry.complete(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)

    def fail(self, instance: CognitiveExecutionInstance, error: Any) -> None:
        overhead_started = perf_counter()
        runtime_lifecycle.failed(instance._lifecycle_execution, error)
        instance.completion_status = "FAILED"
        instance.failure_reason = error
        self._sync(instance)
        self._publish_snapshot(
            instance,
            self._snapshot(instance, self._summary_snapshot_type(instance), "FAILED", str(error)),
        )
        self.registry.complete(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)

    def bind_and_archive(self, instance: CognitiveExecutionInstance) -> None:
        overhead_started = perf_counter()
        if instance.completion_status == "FAILED":
            self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)
            return
        runtime_lifecycle.bound(instance._lifecycle_execution)
        instance.binding_status = "BOUND"
        self._publish_snapshot(
            instance,
            self._snapshot(instance, self._summary_snapshot_type(instance), "BOUND"),
        )
        runtime_lifecycle.reported(instance._lifecycle_execution)
        runtime_lifecycle.archived(instance._lifecycle_execution)
        instance.completion_status = "ARCHIVED"
        instance.archived = True
        self._sync(instance)
        self.registry.archive(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)

    def _sync(self, instance: CognitiveExecutionInstance) -> None:
        lifecycle_execution = instance._lifecycle_execution
        instance.start_timestamp = lifecycle_execution.start_timestamp
        instance.end_timestamp = lifecycle_execution.end_timestamp
        instance.duration_seconds = lifecycle_execution.elapsed_seconds
        instance.cpu_time = lifecycle_execution.cpu_time
        instance.lifecycle_events = [
            dict(event) for event in lifecycle_execution.events
        ]
        instance.telemetry = {
            "execution_start": instance.start_timestamp,
            "execution_end": instance.end_timestamp,
            "elapsed_time": instance.duration_seconds,
            "cpu_time": instance.cpu_time,
            "memory_cost": instance.memory_usage,
            "concept_count": instance.concept_count,
            "search_routes": instance.search_routes,
            "overall_search_quality": instance.overall_search_quality,
            "search_efficiency": instance.search_efficiency,
            "search_coverage": instance.search_coverage,
            "search_entropy": instance.search_entropy,
            "average_route_quality": instance.average_route_quality,
            "analytics_generation_success": instance.analytics_generation_success,
            "generated_programs": instance.generated_programs,
            "program_confidence": instance.program_confidence,
            "average_program_confidence": instance.average_program_confidence,
            "highest_program_confidence": instance.highest_program_confidence,
            "lowest_program_confidence": instance.lowest_program_confidence,
            "confidence_distribution": dict(instance.confidence_distribution),
            "validated_program_count": instance.validated_program_count,
            "low_confidence_program_count": instance.low_confidence_program_count,
            "high_confidence_program_count": instance.high_confidence_program_count,
            "generated_concepts": instance.generated_concepts,
            "generated_truth_candidates": instance.generated_truth_candidates,
            "generated_memory_entries": instance.generated_memory_entries,
            "lifecycle_events": len(instance.lifecycle_events),
        }

    def _snapshot(self, instance, snapshot_type, status, reason=""):
        producer = RuntimeSnapshotProducer(instance.runtime_id)
        sequence = len(instance.snapshots)
        metrics = _execution_metric_totals(instance)
        metrics.update({
            "cpu_time": instance.cpu_time,
            "memory_usage": instance.memory_usage,
            "lifecycle_event_count": len(instance.lifecycle_events),
        })
        return producer.build(
            execution_id=instance.execution_id,
            snapshot_type=snapshot_type,
            execution_stage=snapshot_type,
            status=status,
            sequence=sequence,
            input_summary=instance.execution_context,
            output_summary={
                "completion_reason": reason,
                "completion_status": instance.completion_status,
                "binding_status": instance.binding_status,
            },
            metrics=metrics,
            observations=[reason] if reason else [],
            errors=[str(instance.failure_reason)] if instance.failure_reason else [],
            duration=instance.duration_seconds,
            parent_execution=instance.execution_parent,
            episode_id=instance.execution_context.get("episode_id"),
        )

    def _publish_snapshot(
        self,
        instance: CognitiveExecutionInstance,
        snapshot: Mapping[str, Any],
    ) -> None:
        instance.snapshots.append(dict(snapshot))
        if instance._lifecycle_execution is not None:
            instance._lifecycle_execution.snapshots = [
                dict(item) for item in instance.snapshots
            ]

    def _initial_snapshot_type(self, runtime_id: str) -> str:
        return supported_snapshot_types(runtime_id)[0]

    def _checkpoint_snapshot_type(self, instance: CognitiveExecutionInstance) -> str:
        types = supported_snapshot_types(instance.runtime_id)
        if len(types) <= 2:
            return types[-1]
        return types[min(len(instance.snapshots), len(types) - 2)]

    def _completion_snapshot_types(self, instance: CognitiveExecutionInstance) -> list[str]:
        types = supported_snapshot_types(instance.runtime_id)
        existing = {
            str(snapshot.get("snapshot_type"))
            for snapshot in instance.snapshots
            if isinstance(snapshot, Mapping)
        }
        remaining = [snapshot_type for snapshot_type in types if snapshot_type not in existing]
        return remaining or [types[-1]]

    def _summary_snapshot_type(self, instance: CognitiveExecutionInstance) -> str:
        return supported_snapshot_types(instance.runtime_id)[-1]


class CognitiveRuntimeExecutionEngine:
    """Own execution cycles for all first-class cognitive runtimes."""

    system_name = "cognitive_runtime_execution_engine"

    def __init__(self) -> None:
        self.registry = CognitiveExecutionRegistry()
        self.factory = RuntimeExecutionFactory(self.registry)
        self.root_execution: CognitiveExecutionInstance | None = None
        self._started_at = 0.0
        self._post_execution_pipeline_report: dict[str, Any] = {}
        self._post_execution_pipeline_signature: tuple[Any, ...] | None = None
        self._post_execution_cognitive_seconds = 0.0

    def clear(self) -> None:
        self.registry.clear()
        self.factory.overhead_seconds = 0.0
        self.root_execution = None
        self._started_at = 0.0
        self._post_execution_pipeline_report = {}
        self._post_execution_pipeline_signature = None
        self._post_execution_cognitive_seconds = 0.0

    def start_cycle(self, mode: str = "adaptive", context=None) -> CognitiveExecutionInstance:
        if self.root_execution and not self.root_execution.archived:
            return self.root_execution
        self._started_at = perf_counter()
        self.root_execution = self.factory.create(
            "execution_runtime",
            context=context,
            trigger="cognitive_execution_cycle",
            reason="coordinate cognitive runtime executions",
            mode=mode,
        )
        return self.root_execution

    @contextmanager
    def execution(
        self,
        runtime_id: str,
        mode: str = "adaptive",
        context: Mapping[str, Any] | None = None,
        trigger: str = "runtime_report_generation",
        reason: str = "execute cognitive runtime cycle",
    ) -> Iterator[CognitiveExecutionInstance]:
        root = self.start_cycle(mode=mode, context=context)
        instance = self.factory.create(
            runtime_id,
            parent_execution=root.execution_id,
            context=context,
            trigger=trigger,
            reason=reason,
            mode=mode,
        )
        try:
            yield instance
        except Exception as error:
            self.factory.fail(instance, error)
            raise
        else:
            self.factory.complete(instance)

    def materialize(
        self,
        runtime_id: str,
        evidence: Mapping[str, Any] | None,
        mode: str = "adaptive",
    ) -> CognitiveExecutionInstance:
        with self.execution(
            runtime_id,
            mode=mode,
            context={"evidence_keys": sorted((evidence or {}).keys())[:25]},
            trigger="existing_runtime_evidence",
            reason="materialize existing cognitive runtime evidence",
        ) as instance:
            instance.capture(evidence)
            self.factory.checkpoint(instance, "runtime evidence attached")
        return instance

    def ensure_required_instances(
        self,
        evidence: Mapping[str, Mapping[str, Any]] | None = None,
        mode: str = "adaptive",
    ) -> None:
        sources = evidence if isinstance(evidence, Mapping) else {}
        for runtime_id in (
            "reasoning_runtime",
            "search_runtime",
            "evidence_builder_runtime",
            "memory_runtime",
            "truth_runtime",
            "evaluation_runtime",
            "dependency_runtime",
            "process_runtime",
            "causal_runtime",
            "reuse_runtime",
        ):
            if not self.registry.by_runtime(runtime_id):
                self.materialize(runtime_id, sources.get(runtime_id, {}), mode=mode)

    def complete_cycle(self) -> None:
        if self.root_execution and self.root_execution.completion_status == "RUNNING":
            self.factory.complete(self.root_execution, "cognitive runtime cycle completed")

    def bind_and_archive(self) -> None:
        for instance in list(self.registry.executions.values()):
            self.factory.bind_and_archive(instance)

    def build_report(self, total_runtime_seconds: float = 0.0) -> dict[str, Any]:
        report_started = perf_counter()
        self._aggregate_parent_execution_state()
        self._produce_post_execution_cognitive_memory()
        self._aggregate_parent_execution_state()
        instances = [
            instance.as_dict() for instance in self.registry.executions.values()
        ]
        metric_attribution_report = runtime_metric_attribution_engine.build_report(
            instances,
            post_execution_pipeline_report=self._post_execution_pipeline_report,
        )
        parent_aggregation = self._parent_execution_aggregation(instances)
        truth_metric_sync_report = truth_metric_synchronization_engine.synchronize(
            execution_instances=instances,
            parent_aggregation=parent_aggregation,
            execution_report={
                "generated_truth_candidates": parent_aggregation.get(
                    "generated_truth_candidates",
                    0,
                ),
            },
        )
        truth_report_fields = truth_metric_synchronization_engine.report_fields(
            truth_metric_sync_report
        )
        parent_aggregation.update(truth_report_fields)
        required = {
            "reasoning_runtime",
            "search_runtime",
            "evidence_builder_runtime",
            "memory_runtime",
            "truth_runtime",
            "evaluation_runtime",
        }
        snapshot_required = required | {
            "execution_runtime",
            "dependency_runtime",
            "process_runtime",
            "causal_runtime",
            "reuse_runtime",
        }
        present = {instance["runtime_id"] for instance in instances}
        cognitive = [
            instance for instance in instances
            if instance["runtime_id"] in required
        ]
        lifecycle_complete = [
            instance for instance in cognitive
            if {"CREATED", "REQUESTED", "STARTED", "COMPLETED", "VALIDATED"}.issubset({
                event.get("status") for event in instance["lifecycle_events"]
            })
        ]
        total_duration = sum(instance["duration_seconds"] for instance in cognitive)
        root_duration = (
            self.root_execution.duration_seconds
            if self.root_execution is not None else 0.0
        )
        overhead = self.factory.overhead_seconds
        overhead_denominator = max(
            _number(total_runtime_seconds),
            root_duration,
            0.001,
        )
        snapshot_telemetry = self._snapshot_telemetry(instances)
        timing_report = execution_timing_unification_engine.build_report(
            execution_instances=instances,
            total_wall_time=total_runtime_seconds,
            post_execution_cognitive_time=self._post_execution_cognitive_seconds,
            report_generation_time=max(perf_counter() - report_started, 0.0),
            legacy_report={
                "duration_seconds": root_duration,
                "elapsed_seconds": root_duration,
            },
        )
        timing_summary = timing_report["timing_summary"]
        return {
            "system": self.system_name,
            "COGNITIVE_EXECUTION_ENGINE_REPORT": True,
            "execution_timing": timing_report,
            "EXECUTION_TIMING_UNIFICATION_REPORT": timing_report,
            "timing_summary": timing_summary,
            "timing_records": timing_report["timing_records"],
            "parent_timing": timing_report["parent_timing"],
            "timing_diagnostics": timing_report["timing_diagnostics"],
            "legacy_timing_semantics": timing_report["legacy_timing_semantics"],
            "timing_version": timing_report["timing_version"],
            "timing_consistency": timing_report["timing_consistency"],
            "timing_coverage": timing_report["timing_coverage"],
            "execution_instances": instances,
            "execution_registry": {
                "active_executions": sorted(self.registry.active_execution_ids),
                "completed_executions": sorted(self.registry.completed_execution_ids),
                "archived_executions": sorted(self.registry.archived_execution_ids),
                "execution_history": [item["execution_id"] for item in instances],
            },
            "parent_execution_aggregation": parent_aggregation,
            "post_execution_cognitive_pipeline": dict(self._post_execution_pipeline_report),
            "truth_metric_synchronization": truth_metric_sync_report,
            "TRUTH_METRIC_SYNCHRONIZATION_REPORT": truth_metric_sync_report,
            **truth_report_fields,
            "runtime_metric_attribution": metric_attribution_report,
            "RUNTIME_METRIC_ATTRIBUTION_REPORT": metric_attribution_report,
            "runtime_metric_summary": metric_attribution_report["runtime_metric_summary"],
            "runtime_metric_breakdown": metric_attribution_report["runtime_metric_breakdown"],
            "runtime_metric_sources": metric_attribution_report["runtime_metric_sources"],
            "runtime_metric_validation": metric_attribution_report["runtime_metric_validation"],
            "runtime_metric_confidence": metric_attribution_report["runtime_metric_confidence"],
            "runtime_metric_consistency": metric_attribution_report["runtime_metric_consistency"],
            "runtime_metric_coverage": metric_attribution_report["runtime_metric_coverage"],
            "execution_tree": self.registry.execution_tree(),
            "execution_timeline": sorted(
                [
                    event
                    for instance in instances
                    for event in instance["lifecycle_events"]
                ] + [
                    {
                        "timestamp": snapshot.get("timestamp"),
                        "runtime_id": instance.get("runtime_id"),
                        "execution_id": instance.get("execution_id"),
                        "status": snapshot.get("status"),
                        "event": "runtime_snapshot",
                        "snapshot_type": snapshot.get("snapshot_type"),
                    }
                    for instance in instances
                    for snapshot in instance.get("snapshots", [])
                ],
                key=lambda event: str(event.get("timestamp")),
            ),
            "runtime_telemetry": snapshot_telemetry,
            "execution_coverage": round(len(present & required) / len(required), 4),
            "snapshot_coverage": round(
                len(present & snapshot_required) / len(snapshot_required),
                4,
            ),
            "lifecycle_coverage": round(len(lifecycle_complete) / len(required), 4),
            "execution_statistics": {
                "total_executions": len(instances),
                "active_executions": len(self.registry.active_execution_ids),
                "completed_executions": len(self.registry.completed_execution_ids),
                "archived_executions": len(self.registry.archived_execution_ids),
                "average_cognitive_duration": round(total_duration / max(len(cognitive), 1), 6),
            },
            "execution_costs": {
                item["execution_id"]: {
                    "duration_seconds": item["duration_seconds"],
                    "cpu_time": item["cpu_time"],
                    "memory_usage": item["memory_usage"],
                    "concept_cost": item["concept_cost"],
                    "search_cost": item["search_cost"],
                }
                for item in instances
            },
            "execution_telemetry": {
                item["execution_id"]: item["telemetry"] for item in instances
            },
            "binding_status": {
                item["execution_id"]: item["binding_status"] for item in instances
            },
            "synthetic_execution_count": sum(
                1 for item in instances
                if "synthetic_execution" in item["execution_id"]
            ),
            "missing_execution_instances": sorted(required - present),
            "missing_snapshot_runtimes": [
                runtime_id for runtime_id in sorted(snapshot_required & present)
                if snapshot_telemetry.get(runtime_id, {}).get("snapshot_count", 0) <= 0
            ],
            "instrumentation_overhead_seconds": round(overhead, 6),
            "instrumentation_overhead_below_2_percent": (
                overhead / overhead_denominator < 0.02
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _snapshot_telemetry(self, instances: list[dict[str, Any]]) -> dict[str, Any]:
        telemetry: dict[str, Any] = {}
        by_runtime: dict[str, list[dict[str, Any]]] = {}
        for instance in instances:
            by_runtime.setdefault(str(instance.get("runtime_id")), []).extend(
                [
                    dict(snapshot)
                    for snapshot in instance.get("snapshots", [])
                    if isinstance(snapshot, Mapping)
                ]
            )
        for runtime_id, snapshots in by_runtime.items():
            telemetry[runtime_id] = runtime_snapshot_consumer.summarize(snapshots)
        return telemetry

    def _aggregate_parent_execution_state(self) -> None:
        children_by_parent: dict[str, list[CognitiveExecutionInstance]] = {}
        for instance in self.registry.executions.values():
            if instance.execution_parent:
                children_by_parent.setdefault(instance.execution_parent, []).append(instance)

        def aggregate(instance: CognitiveExecutionInstance) -> dict[str, Any]:
            children = children_by_parent.get(instance.execution_id, [])
            child_totals = [aggregate(child) for child in children]
            if not child_totals:
                return _execution_metric_totals(instance)

            totals = _execution_metric_totals(instance)
            for key in (
                "concept_count",
                "search_routes",
                "generated_programs",
                "generated_concepts",
                "generated_truth_candidates",
                "validated_truth",
                "promoted_truth",
                "committed_truth",
                "rejected_truth",
                "truth_validation_count",
                "generated_memory_entries",
                "validated_program_count",
                "low_confidence_program_count",
                "high_confidence_program_count",
            ):
                child_sum = sum(int(total.get(key, 0)) for total in child_totals)
                totals[key] = max(int(totals.get(key, 0)), child_sum)
                setattr(instance, key, totals[key])

            child_confidences = [
                float(total.get("average_program_confidence", 0.0) or 0.0)
                for total in child_totals
                if float(total.get("average_program_confidence", 0.0) or 0.0) > 0.0
            ]
            if child_confidences:
                instance.average_program_confidence = max(
                    instance.average_program_confidence,
                    round(sum(child_confidences) / len(child_confidences), 4),
                )
                instance.program_confidence = instance.average_program_confidence
                instance.highest_program_confidence = max(
                    instance.highest_program_confidence,
                    max(
                        float(total.get("highest_program_confidence", 0.0) or 0.0)
                        for total in child_totals
                    ),
                )
                lows = [
                    float(total.get("lowest_program_confidence", 0.0) or 0.0)
                    for total in child_totals
                    if float(total.get("lowest_program_confidence", 0.0) or 0.0) > 0.0
                ]
                if lows:
                    instance.lowest_program_confidence = (
                        min(lows)
                        if instance.lowest_program_confidence <= 0.0
                        else min(instance.lowest_program_confidence, min(lows))
                    )
            distribution: dict[str, int] = {}
            for total in child_totals:
                for level, count in (total.get("confidence_distribution") or {}).items():
                    distribution[str(level)] = distribution.get(str(level), 0) + int(count or 0)
            if distribution:
                instance.confidence_distribution = distribution

            instance.memory_usage = max(
                instance.memory_usage,
                sum(int(total.get("memory_usage", 0)) for total in child_totals),
            )
            instance.concept_cost = max(
                instance.concept_cost,
                sum(float(total.get("concept_cost", 0.0)) for total in child_totals),
            )
            instance.search_cost = max(
                instance.search_cost,
                sum(float(total.get("search_cost", 0.0)) for total in child_totals),
            )
            search_quality_values = [
                float(total.get("overall_search_quality", 0.0) or 0.0)
                for total in child_totals
                if float(total.get("overall_search_quality", 0.0) or 0.0) > 0.0
            ]
            if search_quality_values:
                instance.overall_search_quality = max(
                    instance.overall_search_quality,
                    round(sum(search_quality_values) / len(search_quality_values), 4),
                )
            for key in (
                "search_efficiency",
                "search_coverage",
                "search_entropy",
                "average_route_quality",
            ):
                values = [
                    float(total.get(key, 0.0) or 0.0)
                    for total in child_totals
                    if float(total.get(key, 0.0) or 0.0) > 0.0
                ]
                if values:
                    setattr(instance, key, max(float(getattr(instance, key)), round(sum(values) / len(values), 4)))
            instance.analytics_generation_success = any(
                bool(total.get("analytics_generation_success"))
                for total in child_totals
            )
            instance.confidence = max(
                instance.confidence,
                _average(total.get("confidence", 0.0) for total in child_totals),
            )
            truth_confidences = [
                float(total.get("truth_confidence", 0.0) or 0.0)
                for total in child_totals
                if float(total.get("truth_confidence", 0.0) or 0.0) > 0.0
            ]
            if truth_confidences:
                instance.truth_confidence = max(
                    instance.truth_confidence,
                    round(sum(truth_confidences) / len(truth_confidences), 4),
                )
            self.factory._sync(instance)
            totals.update(_execution_metric_totals(instance))
            return totals

        roots = [
            instance for instance in self.registry.executions.values()
            if not instance.execution_parent
        ]
        for root in roots:
            aggregate(root)

    def _produce_post_execution_cognitive_memory(self) -> None:
        post_started = perf_counter()
        root = self.root_execution
        if root is None:
            return
        signature = (
            root.execution_id,
            root.generated_concepts,
            root.generated_programs,
            root.generated_truth_candidates,
            len(root.execution_children),
        )
        if self._post_execution_pipeline_signature == signature:
            return
        if (
            root.generated_memory_entries > 0
            or max(
                root.generated_concepts,
                root.generated_programs,
                root.generated_truth_candidates,
            ) <= 0
        ):
            self._post_execution_pipeline_report = {
                "pipeline_available": False,
                "reason": "no_unconverted_cognitive_outputs",
                "reflection_to_experience_to_semantic_memory_productive": False,
                "post_execution_cognitive_time": 0.0,
            }
            self._post_execution_pipeline_signature = signature
            return
        if str(root.execution_mode).lower() == "fast":
            self._post_execution_pipeline_report = {
                "pipeline_available": False,
                "reason": "fast_mode_post_execution_cognitive_memory_deferred",
                "reflection_to_experience_to_semantic_memory_productive": False,
                "semantic_memory_to_knowledge_fabric_productive": False,
                "post_execution_cognitive_time": 0.0,
                "deferred_to_offline_cognitive_maintenance": True,
            }
            self._post_execution_pipeline_signature = signature
            return

        try:
            from runtime.experience import ExperienceEngine
            from runtime.knowledge import KnowledgeFabricEngine
            from runtime.knowledge.cognitive_episode_engine import CognitiveEpisodeEngine
            from runtime.memory import SemanticMemoryEngine
        except ImportError as error:
            self._post_execution_pipeline_report = {
                "pipeline_available": False,
                "reason": f"pipeline_import_failed: {error}",
                "reflection_to_experience_to_semantic_memory_productive": False,
                "post_execution_cognitive_time": 0.0,
            }
            self._post_execution_pipeline_signature = signature
            return

        objects = _post_execution_objects(self.registry.executions.values(), root)
        episode = CognitiveEpisodeEngine().build_episode(
            execution_id=root.execution_id,
            objects=objects,
        )
        experience_report = ExperienceEngine().build_report(
            execution_report={
                "execution_id": root.execution_id,
                "execution_summary": _execution_metric_totals(root),
                "parent_execution_aggregation": _execution_metric_totals(root),
            },
            concept_report={
                "discovered_concepts": [
                    {
                        "concept_id": obj["object_id"],
                        "concept_name": obj["semantic_payload"]["name"],
                        "confidence": obj["object_confidence"],
                    }
                    for obj in objects
                    if obj["object_type"] == "CONCEPT"
                ]
            },
            program_report={
                "generated_program_objects": [
                    {
                        "program_id": obj["object_id"],
                        "program_name": obj["semantic_payload"]["name"],
                        "confidence": obj["object_confidence"],
                    }
                    for obj in objects
                    if obj["object_type"] == "PROGRAM"
                ]
            },
            truth_report={
                "truth_candidates": [
                    {
                        "truth_id": obj["object_id"],
                        "confidence": obj["object_confidence"],
                    }
                    for obj in objects
                    if obj["object_type"] == "TRUTH_CANDIDATE"
                ]
            },
            semantic_report={
                "discovered_domains": ["Execution Cognition"],
                "semantic_confidence": root.confidence,
            },
            task_identity=f"post execution cognition for {root.execution_id}",
            execution_id=root.execution_id,
            persist=False,
        )
        semantic_memory_report = SemanticMemoryEngine().integrate(
            experience_report=experience_report,
            reflection_report=episode.reflection.get("reflection_report", episode.reflection),
        )
        knowledge_fabric_report = KnowledgeFabricEngine().integrate(
            semantic_memory_report=semantic_memory_report,
        )
        fabric_metrics = _fabric_metrics(
            semantic_memory_report=semantic_memory_report,
            knowledge_fabric_report=knowledge_fabric_report,
        )
        semantic_entities = semantic_memory_report.get("Semantic Entities", [])
        produced_entries = int(semantic_memory_report.get("semantic_entity_count") or len(semantic_entities))
        root.generated_memory_entries = max(root.generated_memory_entries, produced_entries)
        root.memory_usage = max(
            root.memory_usage,
            _deep_size(semantic_memory_report) + _deep_size(knowledge_fabric_report),
        )
        self.factory._sync(root)
        self._post_execution_cognitive_seconds = round(
            max(perf_counter() - post_started, 0.0),
            6,
        )
        self._post_execution_pipeline_report = {
            "pipeline_available": True,
            "post_execution_cognitive_time": self._post_execution_cognitive_seconds,
            "reflection_to_experience_to_semantic_memory_productive": produced_entries > 0,
            "semantic_memory_to_knowledge_fabric_productive": fabric_metrics["fabric_links"] > 0,
            "source_execution_id": root.execution_id,
            "cognitive_objects_generated": len(objects),
            "episode_id": episode.episode_id,
            "reflection_id": episode.reflection_id,
            "reflection_status": episode.reflection_status,
            "experience_id": experience_report.get("experience", {}).get("experience_id", ""),
            "experience_count": experience_report.get("experience_count", 0),
            "semantic_memory_entries_generated": produced_entries,
            "semantic_domains": semantic_memory_report.get("Domains", []),
            "knowledge_fabric_report": {
                "fabric_links": fabric_metrics["fabric_links"],
                "fabric_bridges": fabric_metrics["fabric_bridges"],
                "cross_domain_links": fabric_metrics["cross_domain_links"],
                "fabric_density": fabric_metrics["fabric_density"],
                "fabric_connectivity": fabric_metrics["fabric_connectivity"],
                "orphan_concepts": fabric_metrics["orphan_concepts"],
                "isolated_domains": fabric_metrics["isolated_domains"],
            },
            "fabric_links": fabric_metrics["fabric_links"],
            "fabric_bridges": fabric_metrics["fabric_bridges"],
            "cross_domain_links": fabric_metrics["cross_domain_links"],
            "fabric_density": fabric_metrics["fabric_density"],
            "fabric_connectivity": fabric_metrics["fabric_connectivity"],
            "orphan_concepts": fabric_metrics["orphan_concepts"],
            "isolated_domains": fabric_metrics["isolated_domains"],
            "semantic_memory_is_canonical_destination": True,
            "knowledge_fabric_connects_semantic_memory": True,
            "knowledge_fabric_stores_relationships_only": True,
            "memory_runtime_replaced": False,
            "raw_execution_stored_as_memory": False,
        }
        self._post_execution_pipeline_signature = signature

    def _parent_execution_aggregation(self, instances: list[dict[str, Any]]) -> dict[str, Any]:
        root = self.root_execution.as_dict() if self.root_execution is not None else {}
        return {
            "parent_execution_id": root.get("execution_id"),
            "parent_runtime_id": root.get("runtime_id"),
            "parent_is_cognitive_state_source": bool(root),
            "aggregates_child_runtime_outputs": bool(root),
            "generated_concepts": root.get("generated_concepts", 0),
            "generated_programs": root.get("generated_programs", 0),
            "program_confidence": root.get("program_confidence", 0.0),
            "average_program_confidence": root.get("average_program_confidence", 0.0),
            "highest_program_confidence": root.get("highest_program_confidence", 0.0),
            "lowest_program_confidence": root.get("lowest_program_confidence", 0.0),
            "confidence_distribution": root.get("confidence_distribution", {}),
            "validated_program_count": root.get("validated_program_count", 0),
            "low_confidence_program_count": root.get("low_confidence_program_count", 0),
            "high_confidence_program_count": root.get("high_confidence_program_count", 0),
            "generated_truth_candidates": root.get("generated_truth_candidates", 0),
            "truth_candidates": root.get("generated_truth_candidates", 0),
            "validated_truth": root.get("validated_truth", 0),
            "promoted_truth": root.get("promoted_truth", 0),
            "committed_truth": root.get("committed_truth", 0),
            "rejected_truth": root.get("rejected_truth", 0),
            "truth_confidence": root.get("truth_confidence", 0.0),
            "truth_validation_count": root.get("truth_validation_count", 0),
            "truth_lifecycle_statistics": root.get("truth_lifecycle_statistics", {}),
            "generated_memory_entries": root.get("generated_memory_entries", 0),
            "search_routes": root.get("search_routes", 0),
            "overall_search_quality": root.get("overall_search_quality", 0.0),
            "search_efficiency": root.get("search_efficiency", 0.0),
            "search_coverage": root.get("search_coverage", 0.0),
            "search_entropy": root.get("search_entropy", 0.0),
            "average_route_quality": root.get("average_route_quality", 0.0),
            "analytics_generation_success": root.get("analytics_generation_success", False),
            "concept_count": root.get("concept_count", 0),
            "total_child_executions": sum(
                1 for item in instances
                if item.get("execution_parent") == root.get("execution_id")
            ) if root else 0,
        }


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _count(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple, set, dict)) else 0


def _execution_metric_totals(instance: CognitiveExecutionInstance) -> dict[str, Any]:
    return {
        "concept_count": instance.concept_count,
        "search_routes": instance.search_routes,
        "generated_programs": instance.generated_programs,
        "program_confidence": instance.program_confidence,
        "average_program_confidence": instance.average_program_confidence,
        "highest_program_confidence": instance.highest_program_confidence,
        "lowest_program_confidence": instance.lowest_program_confidence,
        "confidence_distribution": dict(instance.confidence_distribution),
        "validated_program_count": instance.validated_program_count,
        "low_confidence_program_count": instance.low_confidence_program_count,
        "high_confidence_program_count": instance.high_confidence_program_count,
        "generated_concepts": instance.generated_concepts,
        "generated_truth_candidates": instance.generated_truth_candidates,
        "validated_truth": instance.validated_truth,
        "promoted_truth": instance.promoted_truth,
        "committed_truth": instance.committed_truth,
        "rejected_truth": instance.rejected_truth,
        "truth_confidence": instance.truth_confidence,
        "truth_validation_count": instance.truth_validation_count,
        "truth_lifecycle_statistics": dict(instance.truth_lifecycle_statistics),
        "generated_memory_entries": instance.generated_memory_entries,
        "memory_usage": instance.memory_usage,
        "concept_cost": instance.concept_cost,
        "search_cost": instance.search_cost,
        "overall_search_quality": instance.overall_search_quality,
        "search_efficiency": instance.search_efficiency,
        "search_coverage": instance.search_coverage,
        "search_entropy": instance.search_entropy,
        "average_route_quality": instance.average_route_quality,
        "analytics_generation_success": instance.analytics_generation_success,
        "confidence": instance.confidence,
    }


def _average(values: Any) -> float:
    items = [float(value or 0.0) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


def _post_execution_objects(
    instances: Any,
    root: CognitiveExecutionInstance,
) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for instance in instances:
        if instance.runtime_id == "execution_runtime":
            continue
        objects.extend(_metric_objects(instance, "CONCEPT", instance.generated_concepts))
        objects.extend(_metric_objects(instance, "PROGRAM", instance.generated_programs))
        objects.extend(_metric_objects(instance, "TRUTH_CANDIDATE", instance.generated_truth_candidates))
    if not objects:
        objects.extend(_metric_objects(root, "CONCEPT", root.generated_concepts))
        objects.extend(_metric_objects(root, "PROGRAM", root.generated_programs))
        objects.extend(_metric_objects(root, "TRUTH_CANDIDATE", root.generated_truth_candidates))
    return objects


def _metric_objects(
    instance: CognitiveExecutionInstance,
    object_type: str,
    count: int,
) -> list[dict[str, Any]]:
    limit = max(int(count or 0), 0)
    label = {
        "CONCEPT": "generated concept",
        "PROGRAM": "generated program",
        "TRUTH_CANDIDATE": "generated truth candidate",
    }[object_type]
    return [
        {
            "object_id": f"{instance.execution_id}:{object_type.lower()}:{index + 1}",
            "object_type": object_type,
            "object_family": "POST_EXECUTION_COGNITIVE_OUTPUT",
            "object_confidence": instance.confidence or 0.5,
            "object_status": "VALIDATED" if object_type == "TRUTH_CANDIDATE" else "SUPPORTED",
            "runtime_origin": instance.runtime_id,
            "execution_cycle": f"{instance.execution_id}:cycle",
            "creation_timestamp": instance.creation_timestamp,
            "last_update_timestamp": instance.end_timestamp or instance.creation_timestamp,
            "semantic_payload": {
                "domain": "Execution Cognition",
                "name": f"{label} {index + 1}",
                "source_runtime": instance.runtime_id,
            },
            "lineage": {
                "source_execution_id": [instance.execution_id],
            },
        }
        for index in range(limit)
    ]


def _fabric_metrics(
    *,
    semantic_memory_report: Mapping[str, Any],
    knowledge_fabric_report: Mapping[str, Any],
) -> dict[str, Any]:
    relationships = knowledge_fabric_report.get("Fabric Relationships", [])
    cross_domain_links = knowledge_fabric_report.get("Cross-Domain Links", [])
    bridges = knowledge_fabric_report.get("Emerging Bridges", [])
    connectivity = knowledge_fabric_report.get("Connectivity Metrics", {})
    semantic_entities = semantic_memory_report.get("Semantic Entities", [])
    referenced = {
        str(relation.get("source_entity_id"))
        for relation in relationships
        if isinstance(relation, Mapping)
    } | {
        str(relation.get("target_entity_id"))
        for relation in relationships
        if isinstance(relation, Mapping)
    }
    orphan_concepts = [
        entity.get("semantic_memory_id")
        for entity in semantic_entities
        if isinstance(entity, Mapping)
        and entity.get("semantic_category") == "Concept"
        and entity.get("semantic_memory_id") not in referenced
    ]
    return {
        "fabric_links": len(relationships),
        "fabric_bridges": len(bridges),
        "cross_domain_links": len(cross_domain_links),
        "fabric_density": knowledge_fabric_report.get("Fabric Density", 0.0),
        "fabric_connectivity": connectivity.get(
            "knowledge_connectivity",
            connectivity.get("global_connectivity", 0.0),
        ),
        "orphan_concepts": orphan_concepts,
        "isolated_domains": knowledge_fabric_report.get("Disconnected Domains", []),
    }


def _deep_size(value: Any, seen: set[int] | None = None) -> int:
    seen = seen or set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, Mapping):
        size += sum(
            _deep_size(key, seen) + _deep_size(item, seen)
            for key, item in value.items()
        )
    elif isinstance(value, (list, tuple, set)):
        size += sum(_deep_size(item, seen) for item in value)
    return size


cognitive_runtime_execution_engine = CognitiveRuntimeExecutionEngine()


__all__ = [
    "CognitiveExecutionInstance",
    "CognitiveExecutionRegistry",
    "RuntimeExecutionFactory",
    "CognitiveRuntimeExecutionEngine",
    "cognitive_runtime_execution_engine",
]
