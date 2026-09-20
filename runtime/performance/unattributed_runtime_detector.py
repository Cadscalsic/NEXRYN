"""Detect and explain runtime not assigned to a subsystem."""

from __future__ import annotations

from typing import Any, Mapping


class UnattributedRuntimeDetector:
    system_name = "unattributed_runtime_detector"

    def detect(
        self,
        attribution_report: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        attribution_report = attribution_report if isinstance(attribution_report, Mapping) else {}
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        unattributed = _number(attribution_report.get("unattributed_runtime"))
        suspects = []
        if unattributed > 0.001:
            suspects.extend([
                "hidden_loops",
                "silent_retries",
                "recursive_calls",
                "background_execution",
                "untracked_stages",
                "runtime_leaks",
            ])
        if _number(runtime_context.get("dependency_chains_executed")) > 100:
            suspects.append("dependency_reasoning_expansion")
        if _number(runtime_context.get("serialized_context_bytes")) > 10_000_000:
            suspects.append("oversized_context_serialization")
        return {
            "system": self.system_name,
            "unattributed_runtime_seconds": round(unattributed, 4),
            "hidden_loops_detected": "hidden_loops" in suspects,
            "silent_retries_detected": "silent_retries" in suspects,
            "recursive_calls_detected": "recursive_calls" in suspects,
            "background_execution_detected": "background_execution" in suspects,
            "untracked_stages_detected": "untracked_stages" in suspects,
            "runtime_leaks_detected": "runtime_leaks" in suspects,
            "suspected_unattributed_runtime_sources": sorted(set(suspects)),
            "unattributed_runtime_eliminated": unattributed <= 0.001,
        }


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


unattributed_runtime_detector = UnattributedRuntimeDetector()


__all__ = ["UnattributedRuntimeDetector", "unattributed_runtime_detector"]
