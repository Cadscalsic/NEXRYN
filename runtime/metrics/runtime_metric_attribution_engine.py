"""Authoritative runtime metric ownership attribution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping, Sequence


SUPPORTED_METRICS = (
    "execution_time",
    "cpu_time",
    "wall_time",
    "reasoning_time",
    "waiting_time",
    "dependency_time",
    "memory_usage",
    "object_count",
    "concept_count",
    "program_count",
    "truth_count",
    "experience_count",
    "semantic_entries",
    "fabric_operations",
    "snapshot_count",
    "event_count",
)

SELF_MEASURED_METRICS = {
    "execution_time": "duration_seconds",
    "cpu_time": "cpu_time",
    "wall_time": "elapsed_seconds",
    "memory_usage": "memory_usage",
    "snapshot_count": "snapshots",
    "event_count": "lifecycle_events",
}

OUTPUT_METRICS = {
    "concept_count": "generated_concepts",
    "program_count": "generated_programs",
    "truth_count": "generated_truth_candidates",
    "semantic_entries": "generated_memory_entries",
}

RUNTIME_DURATION_METRICS = {
    "reasoning_runtime": "reasoning_time",
    "dependency_runtime": "dependency_time",
}

PIPELINE_METRICS = {
    "experience_count": "experience_count",
    "fabric_operations": "fabric_links",
}


@dataclass(frozen=True)
class RuntimeMetricAttribution:
    """Immutable record for one runtime-owned metric measurement."""

    metric_id: str
    metric_name: str
    runtime_owner: str
    execution_id: str
    measurement_scope: str
    measurement_start: str
    measurement_end: str
    measurement_duration: float
    measurement_source: str
    measurement_method: str
    measurement_confidence: float
    metric_value: float
    parent_execution: str | None = None
    aggregation_role: str = "owner"
    validation_status: str = "validated"
    validation_errors: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "runtime_owner": self.runtime_owner,
            "execution_id": self.execution_id,
            "measurement_scope": self.measurement_scope,
            "measurement_start": self.measurement_start,
            "measurement_end": self.measurement_end,
            "measurement_duration": self.measurement_duration,
            "measurement_source": self.measurement_source,
            "measurement_method": self.measurement_method,
            "measurement_confidence": self.measurement_confidence,
            "metric_value": self.metric_value,
            "parent_execution": self.parent_execution,
            "aggregation_role": self.aggregation_role,
            "validation_status": self.validation_status,
            "validation_errors": list(self.validation_errors),
        }


class RuntimeMetricAttributionEngine:
    """Build deterministic ownership records from completed runtime executions."""

    system_name = "runtime_metric_attribution_engine"
    schema_version = "1.0"

    def build_report(
        self,
        execution_instances: Sequence[Mapping[str, Any]] | None,
        post_execution_pipeline_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        instances = [
            dict(instance)
            for instance in (execution_instances or [])
            if isinstance(instance, Mapping)
        ]
        pipeline = (
            dict(post_execution_pipeline_report)
            if isinstance(post_execution_pipeline_report, Mapping)
            else {}
        )
        parent_bounds = {
            str(instance.get("execution_id")): instance
            for instance in instances
            if instance.get("execution_id")
        }
        records: list[RuntimeMetricAttribution] = []
        for instance in instances:
            records.extend(self._records_for_instance(instance, pipeline))

        validated, rejected = self._validate(records, parent_bounds)
        record_dicts = [record.as_dict() for record in validated]
        summary = self._summary(validated, instances)
        consistency = self._consistency(validated, rejected, instances, parent_bounds)
        coverage = self._coverage(validated, instances, pipeline)
        confidence = self._confidence(validated, rejected)
        sources = {
            record.metric_id: {
                "measurement_source": record.measurement_source,
                "measurement_method": record.measurement_method,
                "runtime_owner": record.runtime_owner,
                "execution_id": record.execution_id,
            }
            for record in validated
        }
        validation = {
            "validation_success": not rejected,
            "validated_metric_count": len(validated),
            "rejected_metric_count": len(rejected),
            "rejected_metrics": [record.as_dict() for record in rejected],
            "duplicate_metrics_rejected": sum(
                1
                for record in rejected
                if "duplicate_metric" in record.validation_errors
            ),
            "missing_owner_rejected": sum(
                1
                for record in rejected
                if "missing_runtime_owner" in record.validation_errors
            ),
            "negative_duration_rejected": sum(
                1
                for record in rejected
                if "negative_duration" in record.validation_errors
            ),
            "missing_timestamp_rejected": sum(
                1
                for record in rejected
                if "missing_timestamp" in record.validation_errors
            ),
            "outside_execution_boundary_rejected": sum(
                1
                for record in rejected
                if "outside_execution_boundary" in record.validation_errors
            ),
        }
        report = {
            "system": self.system_name,
            "RUNTIME_METRIC_ATTRIBUTION_REPORT": True,
            "snapshot_schema_version": self.schema_version,
            "supported_metrics": list(SUPPORTED_METRICS),
            "verified_runtime_metrics": record_dicts,
            "runtime_metric_summary": summary,
            "runtime_metric_breakdown": self._breakdown(validated),
            "runtime_metric_sources": sources,
            "runtime_metric_validation": validation,
            "runtime_metric_confidence": confidence,
            "runtime_metric_consistency": consistency,
            "runtime_metric_coverage": coverage,
            "metric_attribution_authority": True,
            "parent_runtimes_aggregate_only": True,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return report

    def _records_for_instance(
        self,
        instance: Mapping[str, Any],
        pipeline: Mapping[str, Any],
    ) -> list[RuntimeMetricAttribution]:
        runtime_owner = str(instance.get("runtime_id") or "")
        execution_id = str(instance.get("execution_id") or "")
        start = str(instance.get("execution_start") or "")
        end = str(instance.get("execution_end") or "")
        duration = round(max(_number(instance.get("duration_seconds")), 0.0), 6)
        parent_execution = instance.get("execution_parent")
        records = []

        for metric_name, field_name in SELF_MEASURED_METRICS.items():
            value = self._value(instance, field_name)
            if metric_name == "wall_time" and value <= 0.0:
                value = duration
            records.append(
                self._record(
                    metric_name=metric_name,
                    metric_value=value,
                    runtime_owner=runtime_owner,
                    execution_id=execution_id,
                    start=start,
                    end=end,
                    duration=duration,
                    source="runtime_execution_instance",
                    method=f"direct_field:{field_name}",
                    parent_execution=parent_execution,
                )
            )

        runtime_duration_metric = RUNTIME_DURATION_METRICS.get(runtime_owner)
        if runtime_duration_metric:
            records.append(
                self._record(
                    metric_name=runtime_duration_metric,
                    metric_value=duration,
                    runtime_owner=runtime_owner,
                    execution_id=execution_id,
                    start=start,
                    end=end,
                    duration=duration,
                    source="runtime_execution_instance",
                    method="runtime_owned_duration",
                    parent_execution=parent_execution,
                )
            )

        if runtime_owner != "execution_runtime":
            for metric_name, field_name in OUTPUT_METRICS.items():
                value = self._value(instance, field_name)
                if value <= 0.0:
                    continue
                records.append(
                    self._record(
                        metric_name=metric_name,
                        metric_value=value,
                        runtime_owner=runtime_owner,
                        execution_id=execution_id,
                        start=start,
                        end=end,
                        duration=duration,
                        source="runtime_output",
                        method=f"direct_field:{field_name}",
                        parent_execution=parent_execution,
                    )
                )
            object_count = sum(
                self._value(instance, field_name)
                for field_name in OUTPUT_METRICS.values()
            )
            if object_count <= 0.0:
                return records
            records.append(
                self._record(
                    metric_name="object_count",
                    metric_value=object_count,
                    runtime_owner=runtime_owner,
                    execution_id=execution_id,
                    start=start,
                    end=end,
                    duration=duration,
                    source="runtime_output",
                    method="derived_from_owned_output_counts",
                    parent_execution=parent_execution,
                )
            )

        if runtime_owner == "memory_runtime":
            for metric_name, field_name in PIPELINE_METRICS.items():
                value = self._value(pipeline, field_name)
                if value <= 0.0:
                    continue
                records.append(
                    self._record(
                        metric_name=metric_name,
                        metric_value=value,
                        runtime_owner=runtime_owner,
                        execution_id=execution_id,
                        start=start,
                        end=end,
                        duration=duration,
                        source="post_execution_cognitive_pipeline",
                        method=f"direct_field:{field_name}",
                        parent_execution=parent_execution,
                    )
                )
        return records

    def _record(
        self,
        metric_name: str,
        metric_value: float,
        runtime_owner: str,
        execution_id: str,
        start: str,
        end: str,
        duration: float,
        source: str,
        method: str,
        parent_execution: Any,
    ) -> RuntimeMetricAttribution:
        metric_value = round(_number(metric_value), 6)
        confidence = 1.0 if start and end and runtime_owner and execution_id else 0.0
        metric_id = ":".join([
            execution_id or "missing_execution",
            runtime_owner or "missing_owner",
            metric_name,
        ])
        return RuntimeMetricAttribution(
            metric_id=metric_id,
            metric_name=metric_name,
            runtime_owner=runtime_owner,
            execution_id=execution_id,
            measurement_scope=f"execution:{execution_id}",
            measurement_start=start,
            measurement_end=end,
            measurement_duration=round(duration, 6),
            measurement_source=source,
            measurement_method=method,
            measurement_confidence=confidence,
            metric_value=metric_value,
            parent_execution=str(parent_execution) if parent_execution else None,
        )

    def _validate(
        self,
        records: Sequence[RuntimeMetricAttribution],
        parent_bounds: Mapping[str, Mapping[str, Any]],
    ) -> tuple[list[RuntimeMetricAttribution], list[RuntimeMetricAttribution]]:
        seen: set[str] = set()
        validated = []
        rejected = []
        for record in records:
            errors = []
            if not record.runtime_owner:
                errors.append("missing_runtime_owner")
            if not record.execution_id:
                errors.append("missing_execution_id")
            if record.metric_id in seen:
                errors.append("duplicate_metric")
            if record.measurement_duration < 0.0:
                errors.append("negative_duration")
            if not isfinite(record.measurement_duration) or not isfinite(record.metric_value):
                errors.append("invalid_numeric_value")
            if not record.measurement_start or not record.measurement_end:
                errors.append("missing_timestamp")
            if self._outside_parent_boundary(record, parent_bounds):
                errors.append("outside_execution_boundary")
            if errors:
                rejected.append(
                    RuntimeMetricAttribution(
                        **{
                            **record.as_dict(),
                            "validation_status": "rejected",
                            "validation_errors": tuple(errors),
                        }
                    )
                )
                continue
            seen.add(record.metric_id)
            validated.append(record)
        return validated, rejected

    def _outside_parent_boundary(
        self,
        record: RuntimeMetricAttribution,
        parent_bounds: Mapping[str, Mapping[str, Any]],
    ) -> bool:
        if not record.parent_execution:
            return False
        parent = parent_bounds.get(record.parent_execution)
        if not parent:
            return False
        child_start = _parse_time(record.measurement_start)
        child_end = _parse_time(record.measurement_end)
        parent_start = _parse_time(parent.get("execution_start"))
        parent_end = _parse_time(parent.get("execution_end"))
        if not all((child_start, child_end, parent_start, parent_end)):
            return False
        return child_start < parent_start or child_end > parent_end

    def _summary(
        self,
        records: Sequence[RuntimeMetricAttribution],
        instances: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        by_runtime: dict[str, dict[str, Any]] = {}
        for record in records:
            entry = by_runtime.setdefault(
                record.runtime_owner,
                {
                    "runtime_owner": record.runtime_owner,
                    "owned_metric_count": 0,
                    "owned_metric_names": [],
                    "total_measurement_duration": 0.0,
                    "average_measurement_confidence": 0.0,
                    "parent_aggregation_only": record.runtime_owner == "execution_runtime",
                },
            )
            entry["owned_metric_count"] += 1
            if record.metric_name not in entry["owned_metric_names"]:
                entry["owned_metric_names"].append(record.metric_name)
            entry["total_measurement_duration"] = round(
                entry["total_measurement_duration"] + record.measurement_duration,
                6,
            )
            entry["average_measurement_confidence"] = round(
                (
                    entry["average_measurement_confidence"] * (entry["owned_metric_count"] - 1)
                    + record.measurement_confidence
                ) / entry["owned_metric_count"],
                4,
            )
        return {
            "runtime_count": len({str(item.get("runtime_id")) for item in instances}),
            "owned_metric_count": len(records),
            "runtime_owners": by_runtime,
            "unowned_metric_count": 0,
            "duplicate_metric_count": 0,
        }

    def _breakdown(
        self,
        records: Sequence[RuntimeMetricAttribution],
    ) -> dict[str, list[dict[str, Any]]]:
        breakdown: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            breakdown.setdefault(record.runtime_owner, []).append(record.as_dict())
        return breakdown

    def _confidence(
        self,
        validated: Sequence[RuntimeMetricAttribution],
        rejected: Sequence[RuntimeMetricAttribution],
    ) -> dict[str, Any]:
        total = len(validated) + len(rejected)
        average = (
            sum(record.measurement_confidence for record in validated)
            / max(len(validated), 1)
        )
        return {
            "overall_metric_confidence": round(average, 4) if validated else 0.0,
            "validated_ratio": round(len(validated) / max(total, 1), 4),
            "metric_confidence_by_id": {
                record.metric_id: record.measurement_confidence
                for record in validated
            },
        }

    def _coverage(
        self,
        records: Sequence[RuntimeMetricAttribution],
        instances: Sequence[Mapping[str, Any]],
        pipeline: Mapping[str, Any],
    ) -> dict[str, Any]:
        attributed = sorted({record.metric_name for record in records})
        observable = set(SELF_MEASURED_METRICS)
        observable.update(OUTPUT_METRICS)
        for runtime_id in {str(item.get("runtime_id")) for item in instances}:
            if runtime_id in RUNTIME_DURATION_METRICS:
                observable.add(RUNTIME_DURATION_METRICS[runtime_id])
        if _number(pipeline.get("experience_count")) > 0.0:
            observable.add("experience_count")
        if _number(pipeline.get("fabric_links")) > 0.0:
            observable.add("fabric_operations")
        return {
            "supported_metrics": list(SUPPORTED_METRICS),
            "observable_metrics": sorted(observable),
            "attributed_metric_names": attributed,
            "unobserved_supported_metrics": sorted(set(SUPPORTED_METRICS) - set(attributed)),
            "coverage_score": round(
                len(set(attributed) & observable) / max(len(observable), 1),
                4,
            ),
            "metric_count": len(records),
        }

    def _consistency(
        self,
        validated: Sequence[RuntimeMetricAttribution],
        rejected: Sequence[RuntimeMetricAttribution],
        instances: Sequence[Mapping[str, Any]],
        parent_bounds: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        child_boundary_failures = [
            record.metric_id
            for record in rejected
            if "outside_execution_boundary" in record.validation_errors
        ]
        runtime_ids = {str(instance.get("runtime_id")) for instance in instances}
        owner_pairs = {
            (record.metric_name, record.measurement_scope): record.runtime_owner
            for record in validated
        }
        parent_duration_consistent = not child_boundary_failures
        return {
            "parent_duration_consistency": parent_duration_consistent,
            "child_duration_consistency": all(
                record.measurement_duration >= 0.0 for record in validated
            ),
            "pipeline_duration_consistency": parent_duration_consistent,
            "timeline_consistency": self._timeline_consistent(instances),
            "metric_ownership_consistency": len(owner_pairs) == len(validated),
            "aggregation_consistency": "execution_runtime" in runtime_ids,
            "parent_child_metric_ownership_separated": True,
            "boundary_failures": child_boundary_failures,
            "known_execution_boundaries": len(parent_bounds),
        }

    def _timeline_consistent(self, instances: Sequence[Mapping[str, Any]]) -> bool:
        for instance in instances:
            start = _parse_time(instance.get("execution_start"))
            end = _parse_time(instance.get("execution_end"))
            if start and end and end < start:
                return False
        return True

    def _value(self, mapping: Mapping[str, Any], field_name: str) -> float:
        value = mapping.get(field_name)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return float(len(value))
        return _number(value)


def _number(value: Any) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return number if isfinite(number) else 0.0


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None


runtime_metric_attribution_engine = RuntimeMetricAttributionEngine()


__all__ = [
    "RuntimeMetricAttribution",
    "RuntimeMetricAttributionEngine",
    "SUPPORTED_METRICS",
    "runtime_metric_attribution_engine",
]
