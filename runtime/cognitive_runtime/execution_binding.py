"""Canonical execution-ID binding between lifecycle evidence and runtime registry."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Mapping, MutableMapping


TERMINAL_STATES = {"COMPLETED", "FAILED", "BLOCKED", "REPORTED"}


class ExecutionBindingLayer:
    """Transfer existing lifecycle evidence without measuring or profiling it."""

    system_name = "execution_binding_layer"

    def bind(
        self,
        runtime_registry: MutableMapping[str, Any] | None,
        lifecycle_report: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        started = perf_counter()
        registry = runtime_registry if isinstance(runtime_registry, MutableMapping) else {}
        lifecycle = lifecycle_report if isinstance(lifecycle_report, Mapping) else {}
        executions = [
            item for item in lifecycle.get("executions", []) or []
            if isinstance(item, Mapping)
        ]
        execution_index = {
            str(item.get("execution_id")): item
            for item in executions
            if item.get("execution_id")
        }
        timestamp = datetime.now(timezone.utc).isoformat()
        successful: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        seen: set[str] = set()

        for runtime_id, raw_entry in registry.items():
            if not isinstance(raw_entry, MutableMapping):
                continue
            execution_id = str(raw_entry.get("execution_id") or "")
            errors = self._validate(runtime_id, raw_entry, execution_id, execution_index, seen)
            if errors:
                failed.append(self._telemetry(
                    runtime_id, execution_id, timestamp, "FAILED", errors, 0.0
                ))
                continue

            execution = execution_index[execution_id]
            binding_started = perf_counter()
            self._transfer(raw_entry, execution, timestamp)
            raw_entry.setdefault("bound_executions", {})[execution_id] = (
                self._execution_evidence(execution, timestamp)
            )
            latency = max(perf_counter() - binding_started, 0.0)
            telemetry = self._telemetry(
                runtime_id, execution_id, timestamp, "BOUND", [], latency
            )
            raw_entry.setdefault("telemetry", {}).update(telemetry)
            successful.append(telemetry)
            seen.add(execution_id)

        bound_ids = {item["execution_id"] for item in successful}
        for execution in executions:
            execution_id = str(execution.get("execution_id") or "")
            if not execution_id or execution_id in bound_ids:
                continue
            runtime_id = self._runtime_id(execution)
            entry = registry.get(runtime_id)
            if isinstance(entry, MutableMapping):
                if execution_id in (entry.get("bound_executions") or {}):
                    failed.append(self._telemetry(
                        runtime_id, execution_id, timestamp, "FAILED",
                        ["Duplicate execution"], 0.0,
                    ))
                    continue
                duration = self._duration(execution)
                if duration <= 0.0:
                    failed.append(self._telemetry(
                        runtime_id, execution_id, timestamp, "FAILED",
                        ["Timing unavailable"], 0.0,
                    ))
                    continue
                binding_started = perf_counter()
                self._merge(entry, execution, timestamp)
                latency = max(perf_counter() - binding_started, 0.0)
                telemetry = self._telemetry(
                    runtime_id, execution_id, timestamp, "BOUND", [], latency
                )
                successful.append(telemetry)
                bound_ids.add(execution_id)
            else:
                failed.append(self._telemetry(
                    str(execution.get("runtime_name") or execution.get("module_name") or "unknown"),
                    execution_id,
                    timestamp,
                    "UNBOUND",
                    ["Registry entry missing"],
                    0.0,
                ))

        elapsed = max(perf_counter() - started, 0.0)
        completed = [
            item for item in executions
            if str(item.get("status", "")).upper() in TERMINAL_STATES
        ]
        timed = [item for item in completed if self._duration(item) > 0.0]
        bound_timed = [
            item for item in successful
            if _number(registry.get(item["binding_target"], {}).get("duration_seconds")) > 0.0
        ]
        total = len(successful) + len(failed)
        report = {
            "system": self.system_name,
            "EXECUTION_BINDING_REPORT": True,
            "bound_runtimes": sorted({item["binding_target"] for item in successful}),
            "successful_bindings": successful,
            "failed_bindings": failed,
            "average_binding_latency": round(
                sum(item["binding_latency"] for item in successful)
                / max(len(successful), 1),
                9,
            ),
            "binding_coverage": round(len(successful) / max(total, 1), 4),
            "timing_coverage": round(
                min(1.0, len(bound_timed) / max(len(timed), 1)),
                4,
            ),
            "registry_synchronization": (
                "SYNCHRONIZED" if successful and not failed else
                "PARTIAL" if successful else "UNSYNCHRONIZED"
            ),
            "remaining_unbound_metrics": [
                str(entry.get("timing_metric"))
                for entry in registry.values()
                if isinstance(entry, Mapping)
                and entry.get("timing_metric")
                and _number(entry.get("duration_seconds")) <= 0.0
            ],
            "binding_overhead_seconds": round(elapsed, 9),
            "binding_timestamp": timestamp,
        }
        return report

    def _merge(self, entry, execution, timestamp):
        evidence = self._execution_evidence(execution, timestamp)
        execution_id = str(execution["execution_id"])
        entry.setdefault("bound_executions", {})[execution_id] = evidence
        entry["execution_start"] = min(
            filter(None, [entry.get("execution_start"), evidence["execution_start"]]),
            default=None,
        )
        entry["execution_end"] = max(
            filter(None, [entry.get("execution_end"), evidence["execution_end"]]),
            default=None,
        )
        entry["duration_seconds"] = round(
            _number(entry.get("duration_seconds")) + evidence["duration_seconds"],
            6,
        )
        entry["cpu_time"] = round(
            _number(entry.get("cpu_time")) + evidence["cpu_time"], 6
        )
        entry["memory_cost"] = (
            _number(entry.get("memory_cost")) + evidence["memory_cost"]
        )
        entry.setdefault("lifecycle_events", []).extend(evidence["lifecycle_events"])
        entry["status"] = evidence["status"]
        entry["completion_reason"] = evidence["completion_reason"]
        entry["telemetry_source"] = "runtime_lifecycle"
        entry["last_binding_timestamp"] = timestamp
        timing_metric = entry.get("timing_metric")
        if timing_metric:
            entry.setdefault("metrics", {})[str(timing_metric)] = entry["duration_seconds"]

    def _execution_evidence(self, execution, timestamp):
        return {
            "execution_id": str(execution.get("execution_id") or ""),
            "execution_start": execution.get("execution_start") or execution.get("start_timestamp"),
            "execution_end": execution.get("execution_end") or execution.get("end_timestamp"),
            "duration_seconds": round(self._duration(execution), 6),
            "cpu_time": round(_number(execution.get("cpu_time")), 6),
            "memory_cost": _number(execution.get("memory_cost")),
            "lifecycle_events": list(execution.get("lifecycle_events") or []),
            "status": str(execution.get("status") or "UNKNOWN"),
            "completion_reason": str(
                execution.get("completion_reason")
                or execution.get("failure_reason")
                or ""
            ),
            "telemetry_source": "runtime_lifecycle",
            "last_binding_timestamp": timestamp,
        }

    def _validate(self, runtime_id, entry, execution_id, execution_index, seen):
        errors = []
        if not execution_id:
            errors.append("Missing execution_id")
            return errors
        if execution_id in seen:
            errors.append("Duplicate execution")
        if execution_id in (entry.get("bound_executions") or {}):
            errors.append("Duplicate execution")
        execution = execution_index.get(execution_id)
        if execution is None:
            errors.append("Lifecycle incomplete" if ":synthetic_execution" in execution_id else "Lifecycle missing")
            return errors
        if self._duration(execution) <= 0.0:
            errors.append("Timing unavailable")
        expected_owner = str(entry.get("owner") or runtime_id).lower()
        actual_owner = self._runtime_id(execution)
        if actual_owner and expected_owner != actual_owner:
            errors.append("Owner mismatch")
        previous = entry.get("last_binding_timestamp")
        end = execution.get("execution_end") or execution.get("end_timestamp")
        if previous and end and str(previous) > str(end):
            errors.append("Stale binding")
        return errors

    def _transfer(self, entry, execution, timestamp):
        duration = self._duration(execution)
        entry.update({
            "execution_start": execution.get("execution_start") or execution.get("start_timestamp"),
            "execution_end": execution.get("execution_end") or execution.get("end_timestamp"),
            "duration_seconds": round(duration, 6),
            "cpu_time": round(_number(execution.get("cpu_time")), 6),
            "memory_cost": _number(execution.get("memory_cost")),
            "lifecycle_events": list(execution.get("lifecycle_events") or []),
            "status": str(execution.get("status") or entry.get("status") or "UNKNOWN"),
            "completion_reason": str(
                execution.get("completion_reason")
                or execution.get("failure_reason")
                or ""
            ),
            "telemetry_source": "runtime_lifecycle",
            "last_binding_timestamp": timestamp,
        })
        timing_metric = entry.get("timing_metric")
        if timing_metric:
            entry.setdefault("metrics", {})[str(timing_metric)] = round(duration, 6)

    def _telemetry(self, target, execution_id, timestamp, status, errors, latency):
        return {
            "binding_source": "runtime_lifecycle",
            "binding_target": target,
            "execution_id": execution_id or None,
            "binding_timestamp": timestamp,
            "binding_latency": round(latency, 9),
            "binding_status": status,
            "binding_confidence": 1.0 if status == "BOUND" else 0.0,
            "binding_errors": list(errors),
        }

    def _runtime_id(self, execution):
        text = " ".join([
            str(execution.get("runtime_name", "")),
            str(execution.get("module_name", "")),
            str(execution.get("trigger", "")),
        ]).lower()
        for token in (
            "dependency", "evaluation", "reasoning", "search", "memory",
            "truth", "process", "causal", "reuse", "execution",
        ):
            if token in text:
                return f"{token}_runtime"
        return ""

    def _duration(self, execution):
        return max(
            _number(execution.get("elapsed_seconds")),
            _number(execution.get("duration_seconds")),
            _number(execution.get("elapsed_time")),
            _number(execution.get("wall_clock_time")),
        )


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


execution_binding_layer = ExecutionBindingLayer()


__all__ = ["ExecutionBindingLayer", "execution_binding_layer"]
