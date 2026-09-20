"""Canonical synchronization for truth runtime metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping, Sequence


TRUTH_METRIC_FIELDS = (
    "truth_candidates",
    "validated_truth",
    "promoted_truth",
    "committed_truth",
    "rejected_truth",
    "truth_confidence",
    "truth_validation_count",
    "truth_lifecycle_statistics",
    "truth_runtime_duration",
    "truth_runtime_status",
)


@dataclass(frozen=True)
class CanonicalTruthMetricState:
    truth_metric_version: str
    truth_metric_source: str
    truth_metric_timestamp: str
    execution_id: str
    truth_runtime_execution_id: str
    truth_candidates: int = 0
    validated_truth: int = 0
    promoted_truth: int = 0
    committed_truth: int = 0
    rejected_truth: int = 0
    truth_confidence: float = 0.0
    truth_validation_count: int = 0
    truth_lifecycle_statistics: dict[str, Any] = field(default_factory=dict)
    truth_runtime_duration: float = 0.0
    truth_runtime_status: str = "UNKNOWN"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TruthMetricSynchronizationEngine:
    """Create one immutable truth metric state for all report consumers."""

    system_name = "truth_metric_synchronization_engine"
    source_name = "canonical_truth_metric_state"

    def synchronize(
        self,
        execution_instances: Sequence[Mapping[str, Any]] | None = None,
        parent_aggregation: Mapping[str, Any] | None = None,
        execution_report: Mapping[str, Any] | None = None,
        diagnostics: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        instances = [
            dict(instance)
            for instance in (execution_instances or [])
            if isinstance(instance, Mapping)
        ]
        truth_instance = self._truth_instance(instances)
        state = self._canonical_state(truth_instance, instances, truth_report)
        validation = self._validation(
            state=state,
            instances=instances,
            parent_aggregation=parent_aggregation or {},
            execution_report=execution_report or {},
            diagnostics=diagnostics or {},
            truth_report=truth_report or {},
        )
        consistency = {
            "truth_metrics_synchronized": validation["validation_success"],
            "single_canonical_source": True,
            "truth_runtime_owns_generation": True,
            "synchronization_engine_owns_consistency": True,
            "execution_runtime_aggregate_only": True,
            "parent_aggregation_synchronized": not validation["parent_conflicts"],
            "execution_report_synchronized": not validation["execution_report_conflicts"],
            "diagnostics_synchronized": not validation["diagnostic_conflicts"],
            "truth_counter_sources": validation["truth_counter_sources"],
        }
        status = "SYNCHRONIZED" if validation["validation_success"] else "CONFLICTS_DETECTED"
        return {
            "system": self.system_name,
            "TRUTH_METRIC_SYNCHRONIZATION_REPORT": True,
            "canonical_truth_state": state.as_dict(),
            "truth_metric_version": state.truth_metric_version,
            "truth_metric_source": state.truth_metric_source,
            "truth_metric_timestamp": state.truth_metric_timestamp,
            "truth_metric_consistency": consistency,
            "truth_metric_validation": validation,
            "truth_metric_status": status,
            "truth_metrics": state.as_dict(),
            "truth_state_immutable": True,
        }

    def report_fields(self, synchronization_report: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "truth_metric_version": synchronization_report.get("truth_metric_version"),
            "truth_metric_source": synchronization_report.get("truth_metric_source"),
            "truth_metric_timestamp": synchronization_report.get("truth_metric_timestamp"),
            "truth_metric_consistency": synchronization_report.get("truth_metric_consistency"),
            "truth_metric_validation": synchronization_report.get("truth_metric_validation"),
            "truth_metric_status": synchronization_report.get("truth_metric_status"),
        }

    def _truth_instance(
        self,
        instances: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        for instance in instances:
            if instance.get("runtime_id") == "truth_runtime":
                return instance
        return {}

    def _canonical_state(
        self,
        truth_instance: Mapping[str, Any],
        instances: Sequence[Mapping[str, Any]],
        truth_report: Mapping[str, Any] | None,
    ) -> CanonicalTruthMetricState:
        report = truth_report if isinstance(truth_report, Mapping) else {}
        source = truth_instance if truth_instance else report
        candidates = max(
            _count(source.get("truth_candidates")),
            int(_number(source.get("truth_candidates"))),
            int(_number(source.get("generated_truth_candidates"))),
            int(_number(source.get("truth_candidate_count"))),
            _count(report.get("truth_candidates")),
            int(_number(report.get("truth_candidates"))),
        )
        validated = max(
            _count(source.get("validated_truth")),
            int(_number(source.get("validated_truth"))),
            _count(source.get("validated_truths")),
            int(_number(source.get("truth_validation_count"))),
            _count(report.get("validated_truth")),
            int(_number(report.get("validated_truth"))),
            _count(report.get("validated_truths")),
        )
        promoted = max(
            _count(source.get("promoted_truth")),
            int(_number(source.get("promoted_truth"))),
            _count(source.get("promoted_truths")),
            int(_number(source.get("promoted_truth_count"))),
            _count(report.get("promoted_truth")),
            int(_number(report.get("promoted_truth"))),
            _count(report.get("promoted_truths")),
        )
        committed = max(
            _count(source.get("committed_truth")),
            int(_number(source.get("committed_truth"))),
            _count(source.get("committed_truths")),
            _count(source.get("truth_commits")),
            int(_number(source.get("truth_commits"))),
            int(_number(source.get("committed_truth_count"))),
            _count(report.get("committed_truth")),
            int(_number(report.get("committed_truth"))),
            _count(report.get("committed_truths")),
            _count(report.get("truths")),
        )
        rejected = max(
            _count(source.get("rejected_truth")),
            int(_number(source.get("rejected_truth"))),
            _count(source.get("rejected_truths")),
            int(_number(source.get("rejected_truth_count"))),
            _count(report.get("rejected_truth")),
            int(_number(report.get("rejected_truth"))),
            _count(report.get("rejected_truths")),
        )
        confidence = max(
            _number(source.get("truth_confidence")),
            _average_confidence(source.get("truth_candidates")),
            _average_confidence(source.get("validated_truths")),
            _average_confidence(source.get("committed_truths")),
            _average_confidence(report.get("truth_candidates")),
            _average_confidence(report.get("validated_truths")),
            _average_confidence(report.get("committed_truths")),
            _number(source.get("confidence")) if truth_instance else 0.0,
        )
        validation_count = max(
            int(_number(source.get("truth_validation_count"))),
            validated,
        )
        lifecycle_stats = source.get("truth_lifecycle_statistics")
        if not isinstance(lifecycle_stats, Mapping):
            lifecycle_stats = {
                "lifecycle_event_count": _count(source.get("lifecycle_events")),
                "snapshot_count": _count(source.get("snapshots")),
            }
        execution_id = self._root_execution_id(instances)
        truth_execution_id = str(truth_instance.get("execution_id") or report.get("execution_id") or "")
        timestamp = str(
            truth_instance.get("execution_end")
            or report.get("generated_at")
            or datetime.now(timezone.utc).isoformat()
        )
        version = self._version([
            execution_id,
            truth_execution_id,
            candidates,
            validated,
            promoted,
            committed,
            rejected,
            round(confidence, 4),
            validation_count,
            truth_instance.get("duration_seconds"),
            truth_instance.get("completion_status") or truth_instance.get("status"),
        ])
        return CanonicalTruthMetricState(
            truth_metric_version=version,
            truth_metric_source=self.source_name,
            truth_metric_timestamp=timestamp,
            execution_id=execution_id,
            truth_runtime_execution_id=truth_execution_id,
            truth_candidates=candidates,
            validated_truth=validated,
            promoted_truth=promoted,
            committed_truth=committed,
            rejected_truth=rejected,
            truth_confidence=round(confidence, 4),
            truth_validation_count=validation_count,
            truth_lifecycle_statistics=dict(lifecycle_stats),
            truth_runtime_duration=round(_number(truth_instance.get("duration_seconds")), 6),
            truth_runtime_status=str(
                truth_instance.get("completion_status")
                or truth_instance.get("status")
                or ("AVAILABLE" if report else "MISSING")
            ),
        )

    def _validation(
        self,
        state: CanonicalTruthMetricState,
        instances: Sequence[Mapping[str, Any]],
        parent_aggregation: Mapping[str, Any],
        execution_report: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
        truth_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        sources = self._truth_counter_sources(instances, parent_aggregation, execution_report, diagnostics, truth_report)
        parent_conflicts = self._conflicts(
            "parent_aggregation",
            parent_aggregation,
            state,
            {"generated_truth_candidates": "truth_candidates"},
        )
        execution_conflicts = self._conflicts(
            "execution_report",
            execution_report,
            state,
            {"generated_truth_candidates": "truth_candidates"},
        )
        diagnostic_conflicts = self._conflicts(
            "diagnostics",
            diagnostics,
            state,
            {"truth_candidates": "truth_candidates"},
        )
        truth_report_conflicts = self._conflicts(
            "truth_report",
            truth_report,
            state,
            {
                "truth_candidate_count": "truth_candidates",
                "committed_truth_count": "committed_truth",
                "rejected_truth_count": "rejected_truth",
            },
        )
        missing = [
            field for field in TRUTH_METRIC_FIELDS
            if getattr(state, field) in ("", None)
        ]
        duplicated = [
            key for key, source_names in sources.items()
            if len(source_names) > 1 and key != "truth_candidates"
        ]
        conflicts = (
            parent_conflicts
            + execution_conflicts
            + diagnostic_conflicts
            + truth_report_conflicts
        )
        return {
            "validation_success": not missing and not conflicts,
            "missing_truth_metrics": missing,
            "duplicated_truth_counters": duplicated,
            "conflicting_truth_values": conflicts,
            "outdated_truth_statistics": [],
            "parent_conflicts": parent_conflicts,
            "execution_report_conflicts": execution_conflicts,
            "diagnostic_conflicts": diagnostic_conflicts,
            "truth_report_conflicts": truth_report_conflicts,
            "unsynchronized_parent_aggregation": bool(parent_conflicts),
            "unsynchronized_execution_reports": bool(execution_conflicts),
            "unsynchronized_diagnostics": bool(diagnostic_conflicts),
            "truth_counter_sources": sources,
        }

    def _truth_counter_sources(
        self,
        instances: Sequence[Mapping[str, Any]],
        parent_aggregation: Mapping[str, Any],
        execution_report: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
        truth_report: Mapping[str, Any],
    ) -> dict[str, list[str]]:
        sources: dict[str, list[str]] = {}
        truth_instance = self._truth_instance(instances)
        if truth_instance:
            sources.setdefault("truth_candidates", []).append("truth_runtime")
        if parent_aggregation.get("generated_truth_candidates") is not None:
            sources.setdefault("truth_candidates", []).append("parent_aggregation")
        if execution_report.get("generated_truth_candidates") is not None:
            sources.setdefault("truth_candidates", []).append("execution_report")
        if diagnostics.get("truth_candidates") is not None:
            sources.setdefault("truth_candidates", []).append("diagnostics")
        for key in ("truth_candidates", "validated_truths", "committed_truths", "rejected_truths"):
            if truth_report.get(key) is not None:
                sources.setdefault(key, []).append("truth_report")
        return sources

    def _conflicts(
        self,
        source_name: str,
        source: Mapping[str, Any],
        state: CanonicalTruthMetricState,
        field_map: Mapping[str, str],
    ) -> list[dict[str, Any]]:
        conflicts = []
        for source_field, state_field in field_map.items():
            if source_field not in source:
                continue
            source_value = int(_number(source.get(source_field)))
            canonical_value = int(_number(getattr(state, state_field)))
            if source_value != canonical_value:
                conflicts.append({
                    "source": source_name,
                    "field": source_field,
                    "canonical_field": state_field,
                    "source_value": source_value,
                    "canonical_value": canonical_value,
                })
        return conflicts

    def _root_execution_id(self, instances: Sequence[Mapping[str, Any]]) -> str:
        for instance in instances:
            if not instance.get("execution_parent") and instance.get("execution_id"):
                return str(instance["execution_id"])
        for instance in instances:
            if instance.get("execution_id"):
                return str(instance["execution_id"])
        return ""

    def _version(self, values: Sequence[Any]) -> str:
        digest = sha256("|".join(str(value) for value in values).encode("utf-8")).hexdigest()
        return f"truth-metrics:{digest[:16]}"


def _count(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple, set, dict)) else 0


def _number(value: Any) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return number if isfinite(number) else 0.0


def _average_confidence(value: Any) -> float:
    if not isinstance(value, list):
        return 0.0
    confidences = [
        _number(item.get("truth_confidence", item.get("confidence", item.get("commit_score"))))
        for item in value
        if isinstance(item, Mapping)
    ]
    confidences = [value for value in confidences if value > 0.0]
    return round(sum(confidences) / len(confidences), 4) if confidences else 0.0


truth_metric_synchronization_engine = TruthMetricSynchronizationEngine()


__all__ = [
    "CanonicalTruthMetricState",
    "TruthMetricSynchronizationEngine",
    "TRUTH_METRIC_FIELDS",
    "truth_metric_synchronization_engine",
]
