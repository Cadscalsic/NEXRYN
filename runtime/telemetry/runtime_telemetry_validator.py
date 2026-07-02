"""Runtime telemetry contradiction detection."""

from __future__ import annotations

from typing import Any, Mapping


DEPENDENCY_LIFECYCLE_STATES = {
    "NOT_REQUESTED",
    "REQUESTED",
    "ACTIVATED",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "SKIPPED",
}


class RuntimeTelemetryValidator:
    def validate(self, telemetry: Mapping[str, Any] | None) -> dict[str, Any]:
        telemetry = telemetry if isinstance(telemetry, Mapping) else {}
        contradictions: list[dict[str, Any]] = []
        self._dependency_consistency(telemetry, contradictions)
        self._context_consistency(telemetry, contradictions)
        self._truth_consistency(telemetry, contradictions)
        self._cache_reuse_consistency(telemetry, contradictions)

        score = round(max(0.0, 1.0 - len(contradictions) * 0.12), 4)
        dependency_score = self._component_score(contradictions, "dependency")
        context_score = self._component_score(contradictions, "context")
        truth_score = self._component_score(contradictions, "truth")
        cache_score = self._component_score(contradictions, "cache")
        reuse_score = self._component_score(contradictions, "reuse")
        return {
            "system": "runtime_telemetry_validator",
            "report_state": "final",
            "metric_consistency_score": score,
            "dependency_integrity_score": dependency_score,
            "context_integrity_score": context_score,
            "truth_integrity_score": truth_score,
            "cache_integrity_score": cache_score,
            "reuse_integrity_score": reuse_score,
            "performance_integrity_score": score,
            "telemetry_health_score": round(
                (
                    score
                    + dependency_score
                    + context_score
                    + truth_score
                    + cache_score
                    + reuse_score
                )
                / 6,
                4,
            ),
            "contradictions": contradictions,
        }

    def _dependency_consistency(self, telemetry, contradictions):
        state = str(telemetry.get("dependency_activation_state", "")).upper()
        executed = _number(telemetry.get("dependency_chains_executed"))
        depth = _number(telemetry.get("dependency_chain_depth"))
        coverage = _number(telemetry.get("dependency_chain_coverage"))
        dependency_time = _number(telemetry.get("dependency_time"))
        if state and state not in DEPENDENCY_LIFECYCLE_STATES:
            contradictions.append(_issue(
                "DEPENDENCY_STATE_UNKNOWN",
                "dependency",
                f"unknown dependency lifecycle state {state}",
            ))
        if state in {"ACTIVATED", "EXECUTING", "COMPLETED"} and executed <= 0:
            contradictions.append(_issue(
                "DEPENDENCY_STATE_CONTRADICTION",
                "dependency",
                "dependency state reports execution while no chains executed",
            ))
        if executed > 0 and depth <= 0 and coverage <= 0.0:
            contradictions.append(_issue(
                "DEPENDENCY_EXECUTION_WITHOUT_SUPPORT",
                "dependency",
                "executed dependency chains have no depth or coverage",
            ))
        if state == "COMPLETED" and dependency_time <= 0.0 and executed > 0:
            contradictions.append(_issue(
                "DEPENDENCY_TIME_MISSING",
                "dependency",
                "completed dependency execution has zero dependency time",
            ))

    def _context_consistency(self, telemetry, contradictions):
        contexts = _number(telemetry.get("context_count"))
        semantic = _number(telemetry.get("semantic_context_count"))
        registered = _number(telemetry.get("registered_context_count"))
        if semantic > contexts and contexts > 0:
            contradictions.append(_issue(
                "SEMANTIC_CONTEXT_COUNT_EXCEEDS_CONTEXT_COUNT",
                "context",
                "semantic context count exceeds total context count",
            ))
        if registered > contexts and contexts > 0:
            contradictions.append(_issue(
                "REGISTERED_CONTEXT_COUNT_EXCEEDS_CONTEXT_COUNT",
                "context",
                "registered context count exceeds total context count",
            ))

    def _truth_consistency(self, telemetry, contradictions):
        candidates = _number(telemetry.get("candidate_count"))
        committed = _number(
            telemetry.get("committed_count", telemetry.get("truth_commit_count"))
        )
        if committed > candidates and candidates > 0:
            contradictions.append(_issue(
                "TRUTH_COMMITTED_EXCEEDS_CANDIDATES",
                "truth",
                "committed truth count exceeds candidate count",
            ))
        if committed > 0 and _number(telemetry.get("context_count")) <= 0:
            contradictions.append(_issue(
                "TRUTH_COMMITTED_WITHOUT_CONTEXT",
                "truth",
                "truth committed without any registered context",
            ))

    def _cache_reuse_consistency(self, telemetry, contradictions):
        reuse_report = telemetry.get("reuse_metric_authority", {})
        if not isinstance(reuse_report, Mapping):
            return
        public_rate = telemetry.get("reuse_rate")
        reuse_rate = reuse_report.get("reuse_rate")
        if public_rate is None or reuse_rate is None:
            return
        if abs(_number(public_rate) - _number(reuse_rate)) > 0.0:
            contradictions.append(_issue(
                "REUSE_RATE_AUTHORITY_CONFLICT",
                "reuse",
                "public reuse_rate differs from adaptive reuse authority",
            ))

    def _component_score(self, contradictions, category):
        count = sum(1 for item in contradictions if item.get("category") == category)
        return round(max(0.0, 1.0 - count * 0.25), 4)


class MetricIntegrityValidator:
    def validate(self, metrics: Mapping[str, Any] | None) -> dict[str, Any]:
        metrics = metrics if isinstance(metrics, Mapping) else {}
        issues = []
        for key, value in metrics.items():
            if key.startswith("_") or isinstance(value, (dict, list, tuple, set)):
                continue
            if value is None:
                issues.append(_issue("NONE_METRIC_VALUE", "metric", key))
            if key.endswith(("count", "hits", "misses", "executed")):
                if _number(value, 0.0) < 0:
                    issues.append(_issue("NEGATIVE_COUNT", "metric", key))
        for conflict in metrics.get("metric_authority_conflicts", []) or []:
            issues.append(_issue(
                "DUPLICATE_METRIC_SOURCE",
                "metric",
                conflict.get("metric_name"),
            ))
        return {
            "system": "metric_integrity_validator",
            "report_state": "final",
            "metric_quality_gate_passed": not issues,
            "metric_quality_issues": issues,
        }


def _issue(code: str, category: str, detail: str | None) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "detail": detail,
    }


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "DEPENDENCY_LIFECYCLE_STATES",
    "MetricIntegrityValidator",
    "RuntimeTelemetryValidator",
]
