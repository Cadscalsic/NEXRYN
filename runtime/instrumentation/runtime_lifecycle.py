"""Event-driven runtime lifecycle instrumentation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter, process_time
from typing import Any, Mapping
from uuid import uuid4


ORDER = {
    "CREATED": 0,
    "REQUESTED": 1,
    "QUEUED": 2,
    "STARTED": 3,
    "RUNNING": 4,
    "CHECKPOINT": 4,
    "PAUSED": 4,
    "RESUMED": 4,
    "COMPLETED": 5,
    "FAILED": 5,
    "BLOCKED": 5,
    "VALIDATED": 6,
    "BOUND": 7,
    "REPORTED": 8,
    "ARCHIVED": 9,
}


EVENT_BY_STATUS = {
    "REQUESTED": "ExecutionRequested",
    "STARTED": "ExecutionStarted",
    "RUNNING": "ExecutionRunning",
    "COMPLETED": "ExecutionCompleted",
    "FAILED": "ExecutionFailed",
    "BLOCKED": "ExecutionBlocked",
    "CHECKPOINT": "ExecutionCheckpoint",
    "PAUSED": "ExecutionPaused",
    "RESUMED": "ExecutionResumed",
    "VALIDATED": "ExecutionValidated",
    "BOUND": "ExecutionBound",
    "REPORTED": "ExecutionReported",
    "ARCHIVED": "ExecutionArchived",
}


@dataclass
class RuntimeLifecycleExecution:
    execution_id: str
    module_name: str
    runtime_name: str
    parent_execution: str | None = None
    caller: str = ""
    trigger: str = ""
    execution_depth: int = 0
    execution_path: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: str(datetime.utcnow()))
    start_timestamp: str | None = None
    end_timestamp: str | None = None
    perf_started_at: float | None = None
    cpu_started_at: float | None = None
    elapsed_seconds: float = 0.0
    cpu_time: float = 0.0
    exclusive_time: float = 0.0
    inclusive_time: float = 0.0
    cpu_cost: float = 0.0
    memory_cost: int = 0
    input_count: int = 0
    output_count: int = 0
    status: str = "CREATED"
    failure_reason: Any = None
    completion_reason: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[str] = field(default_factory=lambda: ["CREATED"])

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "module_name": self.module_name,
            "runtime_name": self.runtime_name,
            "parent_execution": self.parent_execution,
            "caller": self.caller,
            "execution_start": self.start_timestamp,
            "execution_end": self.end_timestamp,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
            "elapsed_time": round(self.elapsed_seconds, 6),
            "duration_seconds": round(self.elapsed_seconds, 6),
            "wall_clock_time": round(self.elapsed_seconds, 6),
            "cpu_time": round(self.cpu_time, 6),
            "exclusive_time": round(self.exclusive_time, 6),
            "inclusive_time": round(self.inclusive_time, 6),
            "cpu_cost": round(self.cpu_cost, 6),
            "memory_cost": self.memory_cost,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "completion_reason": self.completion_reason,
            "trigger": self.trigger,
            "execution_depth": self.execution_depth,
            "execution_path": list(self.execution_path),
            "lifecycle_transitions": list(self.transitions),
            "lifecycle_events": [dict(event) for event in self.events],
            "snapshots": [dict(snapshot) for snapshot in self.snapshots],
        }


class RuntimeLifecycle:
    """Collect standardized lifecycle transitions and validation reports."""

    system_name = "runtime_lifecycle"

    def __init__(self) -> None:
        self.executions: dict[str, RuntimeLifecycleExecution] = {}
        self.events: list[dict[str, Any]] = []

    def clear(self) -> None:
        self.executions = {}
        self.events = []

    def create(
        self,
        module_name: str,
        runtime_name: str | None = None,
        parent_execution: str | None = None,
        caller: str = "",
        trigger: str = "",
        execution_depth: int = 0,
        execution_path: list[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> RuntimeLifecycleExecution:
        execution_id = f"{module_name}:{uuid4().hex[:12]}"
        path = list(execution_path or [])
        if not path or path[-1] != module_name:
            path.append(module_name)
        execution = RuntimeLifecycleExecution(
            execution_id=execution_id,
            module_name=str(module_name),
            runtime_name=str(runtime_name or module_name),
            parent_execution=parent_execution,
            caller=str(caller or ""),
            trigger=str(trigger or ""),
            execution_depth=int(execution_depth or 0),
            execution_path=path,
        )
        self.executions[execution_id] = execution
        self._record(execution, "CREATED", metadata=metadata)
        return execution

    def requested(self, execution, metadata=None):
        return self.transition(execution, "REQUESTED", metadata=metadata)

    def queued(self, execution, metadata=None):
        return self.transition(execution, "QUEUED", metadata=metadata)

    def started(self, execution, metadata=None):
        execution = self._resolve(execution)
        if not execution:
            return {}
        now = str(datetime.utcnow())
        execution.start_timestamp = now
        execution.perf_started_at = perf_counter()
        execution.cpu_started_at = process_time()
        return self.transition(execution, "STARTED", timestamp=now, metadata=metadata)

    def running(self, execution, metadata=None):
        return self.transition(execution, "RUNNING", metadata=metadata)

    def checkpoint(self, execution, metadata=None):
        return self.transition(execution, "CHECKPOINT", metadata=metadata)

    def paused(self, execution, metadata=None):
        return self.transition(execution, "PAUSED", metadata=metadata)

    def resumed(self, execution, metadata=None):
        return self.transition(execution, "RESUMED", metadata=metadata)

    def completed(
        self,
        execution,
        completion_reason: str = "completed",
        output_count: int | None = None,
        memory_cost: int | None = None,
        metadata: Mapping[str, Any] | None = None,
    ):
        execution = self._resolve(execution)
        if not execution:
            return {}
        if output_count is not None:
            execution.output_count = int(output_count or 0)
        if memory_cost is not None:
            execution.memory_cost = int(memory_cost or 0)
        execution.completion_reason = str(completion_reason or "completed")
        self._finish(execution)
        return self.transition(execution, "COMPLETED", metadata=metadata)

    def failed(self, execution, failure_reason, metadata=None):
        execution = self._resolve(execution)
        if not execution:
            return {}
        execution.failure_reason = failure_reason
        self._finish(execution)
        return self.transition(
            execution,
            "FAILED",
            metadata={
                **dict(metadata or {}),
                "failure_reason": failure_reason,
            },
        )

    def blocked(self, execution, block_reason, metadata=None):
        execution = self._resolve(execution)
        if not execution:
            return {}
        execution.failure_reason = block_reason
        self._finish(execution)
        return self.transition(
            execution,
            "BLOCKED",
            metadata={
                **dict(metadata or {}),
                "block_reason": block_reason,
            },
        )

    def reported(self, execution, metadata=None):
        return self.transition(execution, "REPORTED", metadata=metadata)

    def validated(self, execution, metadata=None):
        return self.transition(execution, "VALIDATED", metadata=metadata)

    def bound(self, execution, metadata=None):
        return self.transition(execution, "BOUND", metadata=metadata)

    def archived(self, execution, metadata=None):
        return self.transition(execution, "ARCHIVED", metadata=metadata)

    def transition(self, execution, status: str, timestamp=None, metadata=None):
        execution = self._resolve(execution)
        if not execution:
            return {}
        status = str(status).upper()
        execution.status = status
        execution.transitions.append(status)
        return self._record(execution, status, timestamp=timestamp, metadata=metadata)

    def decorate_report(
        self,
        report: Mapping[str, Any],
        execution,
        success: bool | None = None,
        failure_reason: Any = None,
    ) -> dict[str, Any]:
        execution = self._resolve(execution)
        merged = dict(report or {})
        if not execution:
            return merged
        lifecycle = execution.as_dict()
        merged.update({
            key: value
            for key, value in lifecycle.items()
            if value is not None or key in {"failure_reason", "completion_reason"}
        })
        merged["runtime_lifecycle"] = lifecycle
        merged["success"] = bool(success) if success is not None else execution.status == "COMPLETED"
        merged["failure"] = failure_reason if failure_reason else execution.failure_reason
        return merged

    def build_report(self) -> dict[str, Any]:
        executions = list(self.executions.values())
        validation = self._validate(executions)
        durations = [
            execution.elapsed_seconds
            for execution in executions
            if execution.elapsed_seconds > 0.0
        ]
        tree = self._execution_tree(executions)
        return {
            "system": self.system_name,
            "RUNTIME_LIFECYCLE_REPORT": True,
            "executions_created": len(executions),
            "executions_started": sum(1 for item in executions if "STARTED" in item.transitions),
            "executions_completed": sum(1 for item in executions if "COMPLETED" in item.transitions),
            "executions_failed": sum(1 for item in executions if "FAILED" in item.transitions),
            "executions_blocked": sum(1 for item in executions if "BLOCKED" in item.transitions),
            "average_runtime": round(sum(durations) / max(len(durations), 1), 6),
            "longest_runtime": round(max(durations or [0.0]), 6),
            "shortest_runtime": round(min(durations or [0.0]), 6),
            "execution_tree": tree,
            "event_count": len(self.events),
            "lifecycle_consistency": validation["lifecycle_consistency"],
            "missing_transitions": validation["missing_transitions"],
            "missing_timestamps": validation["missing_timestamps"],
            "invalid_transitions": validation["invalid_transitions"],
            "negative_durations": validation["negative_durations"],
            "duplicated_transitions": validation["duplicated_transitions"],
            "event_timeline": [dict(event) for event in self.events],
            "timing_attribution": {
                execution.execution_id: {
                    "module": execution.module_name,
                    "wall_clock_time": round(execution.elapsed_seconds, 6),
                    "cpu_time": round(execution.cpu_time, 6),
                    "exclusive_time": round(execution.exclusive_time, 6),
                    "inclusive_time": round(execution.inclusive_time, 6),
                    "status": execution.status,
                }
                for execution in executions
            },
            "executions": [execution.as_dict() for execution in executions],
            "timestamp": str(datetime.utcnow()),
        }

    def _finish(self, execution: RuntimeLifecycleExecution) -> None:
        if execution.perf_started_at is None:
            execution.start_timestamp = execution.start_timestamp or str(datetime.utcnow())
            execution.perf_started_at = perf_counter()
            execution.cpu_started_at = process_time()
        execution.end_timestamp = str(datetime.utcnow())
        execution.elapsed_seconds = round(max(perf_counter() - execution.perf_started_at, 0.0), 6)
        execution.cpu_time = round(max(process_time() - (execution.cpu_started_at or process_time()), 0.0), 6)
        execution.exclusive_time = execution.elapsed_seconds
        execution.inclusive_time = execution.elapsed_seconds
        execution.cpu_cost = execution.cpu_time

    def _record(self, execution, status, timestamp=None, metadata=None):
        duration = 0.0
        if execution.perf_started_at is not None:
            duration = round(max(perf_counter() - execution.perf_started_at, 0.0), 6)
        event = {
            "event_type": EVENT_BY_STATUS.get(status, f"Execution{status.title()}"),
            "timestamp": timestamp or str(datetime.utcnow()),
            "module": execution.module_name,
            "stage": status,
            "execution_id": execution.execution_id,
            "parent_execution": execution.parent_execution,
            "duration": duration,
            "status": status,
            "metadata": dict(metadata or {}),
        }
        execution.events.append(event)
        self.events.append(event)
        return event

    def _resolve(self, execution):
        if isinstance(execution, RuntimeLifecycleExecution):
            return execution
        return self.executions.get(str(execution))

    def _validate(self, executions):
        missing_transitions = []
        missing_timestamps = []
        invalid_transitions = []
        negative_durations = []
        duplicated_transitions = []
        terminal = {"COMPLETED", "FAILED", "BLOCKED"}
        for execution in executions:
            transitions = execution.transitions
            if "STARTED" not in transitions:
                missing_transitions.append({
                    "execution_id": execution.execution_id,
                    "missing": "STARTED",
                })
            if not terminal.intersection(transitions):
                missing_transitions.append({
                    "execution_id": execution.execution_id,
                    "missing": "TERMINAL",
                })
            if not execution.start_timestamp:
                missing_timestamps.append({
                    "execution_id": execution.execution_id,
                    "missing": "execution_start",
                })
            if not execution.end_timestamp:
                missing_timestamps.append({
                    "execution_id": execution.execution_id,
                    "missing": "execution_end",
                })
            if execution.elapsed_seconds < 0.0:
                negative_durations.append(execution.execution_id)
            seen = set()
            for transition in transitions:
                if transition in seen and transition not in {"RUNNING", "CHECKPOINT"}:
                    duplicated_transitions.append({
                        "execution_id": execution.execution_id,
                        "transition": transition,
                    })
                seen.add(transition)
            for previous, current in zip(transitions, transitions[1:]):
                if ORDER.get(current, 99) < ORDER.get(previous, -1):
                    invalid_transitions.append({
                        "execution_id": execution.execution_id,
                        "from": previous,
                        "to": current,
                    })
        issue_count = (
            len(missing_transitions)
            + len(missing_timestamps)
            + len(invalid_transitions)
            + len(negative_durations)
            + len(duplicated_transitions)
        )
        return {
            "missing_transitions": missing_transitions,
            "missing_timestamps": missing_timestamps,
            "invalid_transitions": invalid_transitions,
            "negative_durations": negative_durations,
            "duplicated_transitions": duplicated_transitions,
            "lifecycle_consistency": round(max(0.0, 1.0 - issue_count / max(len(executions), 1)), 4),
        }

    def _execution_tree(self, executions):
        nodes = {
            execution.execution_id: {
                "execution_id": execution.execution_id,
                "module": execution.module_name,
                "runtime": execution.runtime_name,
                "status": execution.status,
                "duration": round(execution.elapsed_seconds, 6),
                "children": [],
            }
            for execution in executions
        }
        roots = []
        for execution in executions:
            node = nodes[execution.execution_id]
            parent = execution.parent_execution
            if parent and parent in nodes:
                nodes[parent]["children"].append(node)
            else:
                roots.append(node)
        return roots


runtime_lifecycle = RuntimeLifecycle()


__all__ = [
    "RuntimeLifecycle",
    "RuntimeLifecycleExecution",
    "runtime_lifecycle",
]
