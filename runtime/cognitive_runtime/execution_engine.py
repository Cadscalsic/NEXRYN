"""Lifecycle-backed execution instances for first-class cognitive runtimes."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Iterator, Mapping
import sys

from runtime.instrumentation import runtime_lifecycle


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
    "acsc_runtime": (
        "AdaptiveCognitiveSuperCoolingExecution",
        "Adaptive Cognitive Super Cooling Runtime",
    ),
    "memory_runtime": ("MemoryExecution", "Memory Runtime"),
    "truth_runtime": ("TruthExecution", "Truth Runtime"),
    "evaluation_runtime": ("EvaluationExecution", "Evaluation Runtime"),
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
    confidence: float = 0.0
    completion_status: str = "CREATED"
    completion_reason: str = ""
    failure_reason: Any = None
    concept_count: int = 0
    search_routes: int = 0
    generated_programs: int = 0
    generated_concepts: int = 0
    generated_truth_candidates: int = 0
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
        self.generated_truth_candidates = max(
            self.generated_truth_candidates,
            _count(data.get("truth_candidates")),
            _count(data.get("evaluations")),
        )
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
            "confidence": self.confidence,
            "status": self.completion_status,
            "completion_status": self.completion_status,
            "completion_reason": self.completion_reason,
            "failure_reason": self.failure_reason,
            "concept_count": self.concept_count,
            "search_routes": self.search_routes,
            "generated_programs": self.generated_programs,
            "generated_concepts": self.generated_concepts,
            "generated_truth_candidates": self.generated_truth_candidates,
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
        instance.snapshots.append(self._snapshot(instance, "Execution Start", "CREATED"))
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
        instance.snapshots.append(self._snapshot(instance, "Checkpoint", "CHECKPOINT", reason))
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
        instance.snapshots.append(self._snapshot(instance, "Execution End", "COMPLETED", reason))
        instance.snapshots.append(self._snapshot(instance, "Validation", "VALIDATED", reason))
        self.registry.complete(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)

    def fail(self, instance: CognitiveExecutionInstance, error: Any) -> None:
        overhead_started = perf_counter()
        runtime_lifecycle.failed(instance._lifecycle_execution, error)
        instance.completion_status = "FAILED"
        instance.failure_reason = error
        self._sync(instance)
        instance.snapshots.append(self._snapshot(instance, "Failure", "FAILED", str(error)))
        self.registry.complete(instance)
        self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)

    def bind_and_archive(self, instance: CognitiveExecutionInstance) -> None:
        overhead_started = perf_counter()
        if instance.completion_status == "FAILED":
            self.overhead_seconds += max(perf_counter() - overhead_started, 0.0)
            return
        runtime_lifecycle.bound(instance._lifecycle_execution)
        instance.binding_status = "BOUND"
        instance.snapshots.append(self._snapshot(instance, "Binding", "BOUND"))
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
            "generated_programs": instance.generated_programs,
            "generated_concepts": instance.generated_concepts,
            "generated_truth_candidates": instance.generated_truth_candidates,
            "generated_memory_entries": instance.generated_memory_entries,
            "lifecycle_events": len(instance.lifecycle_events),
        }

    def _snapshot(self, instance, snapshot_type, status, reason=""):
        return {
            "execution_id": instance.execution_id,
            "snapshot_type": snapshot_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "telemetry": dict(instance.telemetry),
        }


class CognitiveRuntimeExecutionEngine:
    """Own execution cycles for all first-class cognitive runtimes."""

    system_name = "cognitive_runtime_execution_engine"

    def __init__(self) -> None:
        self.registry = CognitiveExecutionRegistry()
        self.factory = RuntimeExecutionFactory(self.registry)
        self.root_execution: CognitiveExecutionInstance | None = None
        self._started_at = 0.0

    def clear(self) -> None:
        self.registry.clear()
        self.factory.overhead_seconds = 0.0
        self.root_execution = None
        self._started_at = 0.0

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
            "memory_runtime",
            "truth_runtime",
            "evaluation_runtime",
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
        instances = [
            instance.as_dict() for instance in self.registry.executions.values()
        ]
        required = {
            "reasoning_runtime",
            "search_runtime",
            "memory_runtime",
            "truth_runtime",
            "evaluation_runtime",
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
        return {
            "system": self.system_name,
            "COGNITIVE_EXECUTION_ENGINE_REPORT": True,
            "execution_instances": instances,
            "execution_registry": {
                "active_executions": sorted(self.registry.active_execution_ids),
                "completed_executions": sorted(self.registry.completed_execution_ids),
                "archived_executions": sorted(self.registry.archived_execution_ids),
                "execution_history": [item["execution_id"] for item in instances],
            },
            "execution_tree": self.registry.execution_tree(),
            "execution_timeline": sorted(
                [
                    event
                    for instance in instances
                    for event in instance["lifecycle_events"]
                ],
                key=lambda event: str(event.get("timestamp")),
            ),
            "execution_coverage": round(len(present & required) / len(required), 4),
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
            "instrumentation_overhead_seconds": round(overhead, 6),
            "instrumentation_overhead_below_2_percent": (
                overhead / overhead_denominator < 0.02
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _count(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple, set, dict)) else 0


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
