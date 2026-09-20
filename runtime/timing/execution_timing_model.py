"""Canonical timing taxonomy, records, and reconciliation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping, Sequence


TIMING_VERSION = "execution-timing-v1"

CANONICAL_TIMING_SCOPES = {
    "BOOT_TIME": {
        "owner": "boot_manager",
        "included_components": [
            "configuration_loading",
            "registry_initialization",
            "runtime_initialization",
            "safe_cache_inspection",
        ],
        "excluded_components": ["task_execution"],
    },
    "TASK_SELECTION_TIME": {
        "owner": "task_manager",
        "included_components": ["task_discovery", "task_filtering", "task_ranking", "task_selection"],
        "excluded_components": ["cognitive_task_execution"],
    },
    "FIRST_TASK_START_LATENCY": {
        "owner": "top_level_runtime_coordinator",
        "included_components": ["boot", "task_selection", "pre_task_preparation"],
        "excluded_components": ["cognitive_runtime_execution"],
    },
    "COGNITIVE_RUNTIME_TIME": {
        "owner": "execution_runtime",
        "included_components": [
            "reasoning_runtime",
            "search_runtime",
            "concept_formation_runtime",
            "program_synthesis_runtime",
            "adaptive_search_intelligence_runtime",
            "acsc_runtime",
            "evidence_builder_runtime",
            "knowledge_integration_runtime",
            "memory_runtime",
            "truth_runtime",
            "evaluation_runtime",
        ],
        "excluded_components": ["external_training_orchestration", "external_report_generation"],
    },
    "CHILD_RUNTIME_TIME": {
        "owner": "child_runtime",
        "included_components": ["individual_child_runtime_work"],
        "excluded_components": ["parent_coordination_overhead"],
    },
    "POST_EXECUTION_COGNITIVE_TIME": {
        "owner": "post_execution_cognitive_pipeline",
        "included_components": [
            "cognitive_object_creation",
            "episode_construction",
            "reflection",
            "experience_formation",
            "semantic_memory_promotion",
            "knowledge_fabric_construction",
        ],
        "excluded_components": ["parent_cognitive_runtime_lifecycle"],
    },
    "TRAINING_TIME": {
        "owner": "training_assistant",
        "included_components": ["training_batch_preparation", "assistant_processing", "learning_updates"],
        "excluded_components": ["cognitive_runtime_time"],
    },
    "REUSE_TIME": {
        "owner": "reuse_runtime",
        "included_components": ["reuse_lookup", "reuse_validation", "reuse_selection", "reuse_application"],
        "excluded_components": ["non_reuse_runtime_work"],
    },
    "GOVERNANCE_TIME": {
        "owner": "governance_runtime",
        "included_components": ["governance_analysis", "policy_checks", "executive_control"],
        "excluded_components": ["reasoning_search_truth_memory_logic"],
    },
    "FINALIZATION_TIME": {
        "owner": "finalizer",
        "included_components": ["state_closure", "cleanup", "persistence", "final_lifecycle_transitions"],
        "excluded_components": ["report_generation_unless_explicit"],
    },
    "REPORT_GENERATION_TIME": {
        "owner": "report_builder",
        "included_components": ["report_building", "compression", "serialization", "printing"],
        "excluded_components": ["cognitive_execution"],
    },
    "TOTAL_WALL_TIME": {
        "owner": "top_level_runtime_coordinator",
        "included_components": ["end_to_end_process_wall_clock"],
        "excluded_components": [],
    },
}


LEGACY_TIMING_FIELDS = {
    "execution_time": "ambiguous_legacy_total_or_task_execution_time",
    "elapsed_time": "ambiguous_legacy_elapsed_duration",
    "duration": "ambiguous_legacy_duration",
    "task_execution_time": "legacy_task_execution_time_maps_to_COGNITIVE_RUNTIME_TIME_when_execution_runtime_owned",
    "pipeline_time": "legacy_pipeline_time_maps_to_POST_EXECUTION_COGNITIVE_TIME_when_pipeline_owned",
    "runtime_time": "ambiguous_legacy_runtime_duration",
    "duration_seconds": "legacy_runtime_duration_maps_by_runtime_owner",
    "elapsed_seconds": "legacy_runtime_duration_maps_by_runtime_owner",
}


@dataclass(frozen=True)
class ExecutionTimingRecord:
    timing_id: str
    execution_id: str
    runtime_id: str
    timing_name: str
    timing_scope: str
    timing_owner: str
    start_timestamp: str
    end_timestamp: str
    wall_duration_seconds: float
    cpu_duration_seconds: float
    inclusive_duration_seconds: float
    exclusive_duration_seconds: float
    included_components: tuple[str, ...]
    excluded_components: tuple[str, ...]
    parent_timing_id: str | None
    measurement_source: str
    measurement_method: str
    clock_type: str
    timing_version: str
    timing_status: str
    validation_status: str

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["included_components"] = list(self.included_components)
        data["excluded_components"] = list(self.excluded_components)
        return data


@dataclass(frozen=True)
class ExecutionTimingState:
    timing_version: str
    timing_records: tuple[ExecutionTimingRecord, ...]
    boot_time: float
    task_selection_time: float
    first_task_start_latency: float
    cognitive_runtime_time: float
    child_runtime_times: dict[str, float]
    post_execution_cognitive_time: float
    training_time: float
    reuse_time: float
    reuse_time_inclusion: str
    governance_time: float
    governance_time_location: str
    finalization_time: float
    report_generation_time: float
    total_wall_time: float
    pre_task_overhead: float
    unattributed_time: float
    accounted_wall_time: float
    overlap_time: float
    double_counted_time: float
    timing_coverage: float
    timing_consistency: str
    timing_consistency_score: float
    parent_timing: dict[str, Any]
    diagnostics: dict[str, Any]
    legacy_timing_semantics: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timing_records"] = [record.as_dict() for record in self.timing_records]
        return data


class ExecutionTimingUnificationEngine:
    """Convert lifecycle timings into one canonical execution timing state."""

    system_name = "execution_timing_unification_engine"

    def build_state(
        self,
        execution_instances: Sequence[Mapping[str, Any]] | None = None,
        total_wall_time: float | None = None,
        boot_time: float = 0.0,
        task_selection_time: float = 0.0,
        first_task_start_latency: float | None = None,
        post_execution_cognitive_time: float = 0.0,
        training_time: float = 0.0,
        governance_time: float = 0.0,
        finalization_time: float = 0.0,
        report_generation_time: float = 0.0,
        pre_task_overhead: float = 0.0,
        legacy_report: Mapping[str, Any] | None = None,
    ) -> ExecutionTimingState:
        instances = [
            dict(instance)
            for instance in (execution_instances or [])
            if isinstance(instance, Mapping)
        ]
        root = self._root_instance(instances)
        children = [
            instance for instance in instances
            if instance.get("execution_parent") == root.get("execution_id")
        ] if root else [
            instance for instance in instances
            if instance.get("runtime_id") != "execution_runtime"
        ]
        child_sum = round(sum(_duration(child) for child in children), 6)
        cognitive_runtime_time = _duration(root)
        child_union = self._interval_union(children)
        parent_exclusive = round(max(cognitive_runtime_time - child_union, 0.0), 6)
        overlap_time = round(max(child_sum - child_union, 0.0), 6)
        parallel_overlap = round(max(child_sum - cognitive_runtime_time, 0.0), 6)
        reuse_time, reuse_inclusion = self._reuse_time(instances, root)
        first_latency = (
            round(_number(first_task_start_latency), 6)
            if first_task_start_latency is not None
            else round(_number(boot_time) + _number(task_selection_time) + _number(pre_task_overhead), 6)
        )
        non_overlap_accounted = round(
            _number(boot_time)
            + _number(task_selection_time)
            + _number(pre_task_overhead)
            + cognitive_runtime_time
            + _number(post_execution_cognitive_time)
            + _number(training_time)
            + _number(governance_time)
            + _number(finalization_time)
            + _number(report_generation_time),
            6,
        )
        total = round(
            max(_number(total_wall_time), non_overlap_accounted, cognitive_runtime_time),
            6,
        )
        unattributed = round(max(total - non_overlap_accounted, 0.0), 6)
        coverage = round(non_overlap_accounted / max(total, 0.000001), 4)
        coverage = min(coverage, 1.0)
        diagnostics = self._diagnostics(
            instances=instances,
            root=root,
            children=children,
            total_wall_time=total,
            accounted_wall_time=non_overlap_accounted,
            unattributed_time=unattributed,
            legacy_report=legacy_report or {},
        )
        consistency_score = round(max(0.0, 1.0 - diagnostics["issue_count"] / 10.0), 4)
        status = "VALID" if diagnostics["issue_count"] == 0 else "VALID_WITH_DIAGNOSTICS"
        records = self._records(
            root=root,
            children=children,
            boot_time=boot_time,
            task_selection_time=task_selection_time,
            first_task_start_latency=first_latency,
            cognitive_runtime_time=cognitive_runtime_time,
            parent_exclusive=parent_exclusive,
            post_execution_cognitive_time=post_execution_cognitive_time,
            training_time=training_time,
            reuse_time=reuse_time,
            governance_time=governance_time,
            finalization_time=finalization_time,
            report_generation_time=report_generation_time,
            total_wall_time=total,
            pre_task_overhead=pre_task_overhead,
        )
        return ExecutionTimingState(
            timing_version=TIMING_VERSION,
            timing_records=tuple(records),
            boot_time=round(_number(boot_time), 6),
            task_selection_time=round(_number(task_selection_time), 6),
            first_task_start_latency=first_latency,
            cognitive_runtime_time=cognitive_runtime_time,
            child_runtime_times={
                str(child.get("execution_id")): _duration(child)
                for child in children
            },
            post_execution_cognitive_time=round(_number(post_execution_cognitive_time), 6),
            training_time=round(_number(training_time), 6),
            reuse_time=reuse_time,
            reuse_time_inclusion=reuse_inclusion,
            governance_time=round(_number(governance_time), 6),
            governance_time_location="outside_runtime" if governance_time > 0.0 else "not_observed",
            finalization_time=round(_number(finalization_time), 6),
            report_generation_time=round(_number(report_generation_time), 6),
            total_wall_time=total,
            pre_task_overhead=round(_number(pre_task_overhead), 6),
            unattributed_time=unattributed,
            accounted_wall_time=non_overlap_accounted,
            overlap_time=overlap_time,
            double_counted_time=overlap_time,
            timing_coverage=coverage,
            timing_consistency=status,
            timing_consistency_score=consistency_score,
            parent_timing={
                "parent_execution_id": root.get("execution_id") if root else "",
                "parent_inclusive_duration": cognitive_runtime_time,
                "parent_exclusive_duration": parent_exclusive,
                "child_duration_sum": child_sum,
                "parallel_overlap_duration": parallel_overlap,
                "coordination_overhead": parent_exclusive,
                "timing_consistency": status,
                "execution_relationship": self._relationship(root, children),
            },
            diagnostics=diagnostics,
            legacy_timing_semantics=self._legacy_semantics(legacy_report or {}),
        )

    def build_report(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        state = self.build_state(*args, **kwargs)
        summary = self.summary(state)
        return {
            "system": self.system_name,
            "EXECUTION_TIMING_UNIFICATION_REPORT": True,
            "canonical_timing_taxonomy": CANONICAL_TIMING_SCOPES,
            "execution_timing_state": state.as_dict(),
            "timing_summary": summary,
            "timing_records": [record.as_dict() for record in state.timing_records],
            "parent_timing": state.parent_timing,
            "timing_diagnostics": state.diagnostics,
            "legacy_timing_semantics": state.legacy_timing_semantics,
            "timing_version": state.timing_version,
            "timing_consistency": state.timing_consistency,
            "timing_coverage": state.timing_coverage,
        }

    def summary(self, state: ExecutionTimingState) -> dict[str, Any]:
        return {
            "total_wall_time": {
                "scope": "TOTAL_WALL_TIME",
                "duration_seconds": state.total_wall_time,
            },
            "boot_time": {"scope": "BOOT_TIME", "duration_seconds": state.boot_time},
            "task_selection_time": {
                "scope": "TASK_SELECTION_TIME",
                "duration_seconds": state.task_selection_time,
            },
            "first_task_start_latency": {
                "scope": "FIRST_TASK_START_LATENCY",
                "duration_seconds": state.first_task_start_latency,
            },
            "cognitive_runtime_time": {
                "scope": "COGNITIVE_RUNTIME_TIME",
                "duration_seconds": state.cognitive_runtime_time,
            },
            "post_execution_cognitive_time": {
                "scope": "POST_EXECUTION_COGNITIVE_TIME",
                "duration_seconds": state.post_execution_cognitive_time,
            },
            "training_time": {
                "scope": "TRAINING_TIME",
                "duration_seconds": state.training_time,
            },
            "reuse_time": {
                "scope": "REUSE_TIME",
                "duration_seconds": state.reuse_time,
                "inclusion": state.reuse_time_inclusion,
            },
            "governance_time": {
                "scope": "GOVERNANCE_TIME",
                "duration_seconds": state.governance_time,
                "location": state.governance_time_location,
            },
            "finalization_time": {
                "scope": "FINALIZATION_TIME",
                "duration_seconds": state.finalization_time,
            },
            "report_generation_time": {
                "scope": "REPORT_GENERATION_TIME",
                "duration_seconds": state.report_generation_time,
            },
            "unattributed_time": {
                "scope": "UNATTRIBUTED_TIME",
                "duration_seconds": state.unattributed_time,
            },
            "timing_coverage": state.timing_coverage,
            "timing_consistency": state.timing_consistency,
            "timing_consistency_score": state.timing_consistency_score,
        }

    def _records(
        self,
        root: Mapping[str, Any],
        children: Sequence[Mapping[str, Any]],
        boot_time: float,
        task_selection_time: float,
        first_task_start_latency: float,
        cognitive_runtime_time: float,
        parent_exclusive: float,
        post_execution_cognitive_time: float,
        training_time: float,
        reuse_time: float,
        governance_time: float,
        finalization_time: float,
        report_generation_time: float,
        total_wall_time: float,
        pre_task_overhead: float,
    ) -> list[ExecutionTimingRecord]:
        records = []
        root_id = str(root.get("execution_id") or "execution_cycle")
        records.extend([
            self._synthetic_record(root_id, "BOOT_TIME", boot_time),
            self._synthetic_record(root_id, "TASK_SELECTION_TIME", task_selection_time),
            self._synthetic_record(root_id, "FIRST_TASK_START_LATENCY", first_task_start_latency),
            self._record_from_instance(
                root,
                "COGNITIVE_RUNTIME_TIME",
                cognitive_runtime_time,
                parent_exclusive,
                None,
            ),
            self._synthetic_record(root_id, "POST_EXECUTION_COGNITIVE_TIME", post_execution_cognitive_time),
            self._synthetic_record(root_id, "TRAINING_TIME", training_time),
            self._synthetic_record(root_id, "REUSE_TIME", reuse_time),
            self._synthetic_record(root_id, "GOVERNANCE_TIME", governance_time),
            self._synthetic_record(root_id, "FINALIZATION_TIME", finalization_time),
            self._synthetic_record(root_id, "REPORT_GENERATION_TIME", report_generation_time),
            self._synthetic_record(root_id, "TOTAL_WALL_TIME", total_wall_time),
        ])
        parent_timing_id = records[3].timing_id
        for child in children:
            records.append(
                self._record_from_instance(
                    child,
                    "CHILD_RUNTIME_TIME",
                    _duration(child),
                    _duration(child),
                    parent_timing_id,
                )
            )
        if pre_task_overhead > 0.0:
            records.append(self._synthetic_record(root_id, "PRE_TASK_OVERHEAD", pre_task_overhead))
        return records

    def _record_from_instance(
        self,
        instance: Mapping[str, Any],
        timing_scope: str,
        inclusive_duration: float,
        exclusive_duration: float,
        parent_timing_id: str | None,
    ) -> ExecutionTimingRecord:
        runtime_id = str(instance.get("runtime_id") or "execution_runtime")
        execution_id = str(instance.get("execution_id") or "execution_cycle")
        taxonomy = CANONICAL_TIMING_SCOPES[timing_scope]
        duration = round(max(_number(inclusive_duration), 0.0), 6)
        return ExecutionTimingRecord(
            timing_id=f"{execution_id}:{timing_scope}",
            execution_id=execution_id,
            runtime_id=runtime_id,
            timing_name=timing_scope.lower(),
            timing_scope=timing_scope,
            timing_owner=runtime_id if timing_scope == "CHILD_RUNTIME_TIME" else taxonomy["owner"],
            start_timestamp=str(instance.get("execution_start") or ""),
            end_timestamp=str(instance.get("execution_end") or ""),
            wall_duration_seconds=duration,
            cpu_duration_seconds=round(max(_number(instance.get("cpu_time")), 0.0), 6),
            inclusive_duration_seconds=duration,
            exclusive_duration_seconds=round(max(_number(exclusive_duration), 0.0), 6),
            included_components=tuple(taxonomy["included_components"]),
            excluded_components=tuple(taxonomy["excluded_components"]),
            parent_timing_id=parent_timing_id,
            measurement_source="runtime_lifecycle",
            measurement_method="monotonic_perf_counter_duration_from_lifecycle",
            clock_type="monotonic_perf_counter",
            timing_version=TIMING_VERSION,
            timing_status="OBSERVED" if duration > 0.0 else "ZERO_DURATION",
            validation_status="VALID" if duration >= 0.0 else "REJECTED",
        )

    def _synthetic_record(
        self,
        root_execution_id: str,
        timing_scope: str,
        duration: float,
    ) -> ExecutionTimingRecord:
        taxonomy = CANONICAL_TIMING_SCOPES.get(
            timing_scope,
            {
                "owner": "top_level_runtime_coordinator",
                "included_components": [timing_scope.lower()],
                "excluded_components": [],
            },
        )
        value = round(max(_number(duration), 0.0), 6)
        timestamp = datetime.now(timezone.utc).isoformat()
        return ExecutionTimingRecord(
            timing_id=f"{root_execution_id}:{timing_scope}",
            execution_id=root_execution_id,
            runtime_id=str(taxonomy["owner"]),
            timing_name=timing_scope.lower(),
            timing_scope=timing_scope,
            timing_owner=str(taxonomy["owner"]),
            start_timestamp=timestamp if value > 0.0 else "",
            end_timestamp=timestamp if value > 0.0 else "",
            wall_duration_seconds=value,
            cpu_duration_seconds=0.0,
            inclusive_duration_seconds=value,
            exclusive_duration_seconds=value,
            included_components=tuple(taxonomy["included_components"]),
            excluded_components=tuple(taxonomy["excluded_components"]),
            parent_timing_id=None,
            measurement_source="execution_timing_unification_engine",
            measurement_method="external_scope_duration_or_zero_when_unobserved",
            clock_type="monotonic_perf_counter",
            timing_version=TIMING_VERSION,
            timing_status="OBSERVED" if value > 0.0 else "UNOBSERVED",
            validation_status="VALID",
        )

    def _diagnostics(
        self,
        instances: Sequence[Mapping[str, Any]],
        root: Mapping[str, Any],
        children: Sequence[Mapping[str, Any]],
        total_wall_time: float,
        accounted_wall_time: float,
        unattributed_time: float,
        legacy_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        missing_start = [
            str(item.get("execution_id"))
            for item in instances
            if item.get("execution_id") and not item.get("execution_start")
        ]
        missing_end = [
            str(item.get("execution_id"))
            for item in instances
            if item.get("execution_id") and not item.get("execution_end")
        ]
        negative = [
            str(item.get("execution_id"))
            for item in instances
            if _number(item.get("duration_seconds")) < 0.0
        ]
        boundary = self._boundary_violations(root, children)
        legacy = self._legacy_semantics(legacy_report)
        cpu_impossible = [
            str(item.get("execution_id"))
            for item in instances
            if _number(item.get("cpu_time")) > max(_duration(item), total_wall_time) + 0.000001
        ]
        issues = (
            len(missing_start)
            + len(missing_end)
            + len(negative)
            + len(boundary)
            + len(cpu_impossible)
        )
        return {
            "ambiguous_timing_fields": legacy["deprecated_fields"],
            "missing_start_timestamps": missing_start,
            "missing_end_timestamps": missing_end,
            "negative_durations": negative,
            "parent_child_boundary_violations": boundary,
            "double_counted_intervals": self._overlaps(children),
            "unattributed_time": round(unattributed_time, 6),
            "unexpected_timing_overlap": [],
            "clock_source_mismatch": [],
            "cpu_time_greater_than_bounds": cpu_impossible,
            "timing_state_version_mismatch": False,
            "total_wall_reconciles": accounted_wall_time <= total_wall_time + 0.000001,
            "issue_count": issues,
        }

    def _legacy_semantics(self, report: Mapping[str, Any]) -> dict[str, Any]:
        deprecated = {}
        for field, semantics in LEGACY_TIMING_FIELDS.items():
            if field in report:
                deprecated[field] = {
                    "legacy_timing_semantics": semantics,
                    "deprecated": True,
                    "canonical_consumption_allowed": False,
                }
        return {
            "deprecated_fields": deprecated,
            "canonical_replacements": {
                "execution_time": "TOTAL_WALL_TIME or COGNITIVE_RUNTIME_TIME depending on owner; ambiguous without owner",
                "duration_seconds": "runtime-owned CHILD_RUNTIME_TIME or COGNITIVE_RUNTIME_TIME",
                "elapsed_seconds": "runtime-owned CHILD_RUNTIME_TIME or COGNITIVE_RUNTIME_TIME",
            },
        }

    def _reuse_time(
        self,
        instances: Sequence[Mapping[str, Any]],
        root: Mapping[str, Any],
    ) -> tuple[float, str]:
        for instance in instances:
            if instance.get("runtime_id") == "reuse_runtime":
                inclusion = (
                    "included_inside_cognitive_runtime_time"
                    if instance.get("execution_parent") == root.get("execution_id")
                    else "outside_cognitive_runtime_time"
                )
                return _duration(instance), inclusion
        return 0.0, "not_observed"

    def _root_instance(self, instances: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
        for instance in instances:
            if instance.get("runtime_id") == "execution_runtime" and not instance.get("execution_parent"):
                return instance
        for instance in instances:
            if not instance.get("execution_parent"):
                return instance
        return {}

    def _interval_union(self, instances: Sequence[Mapping[str, Any]]) -> float:
        intervals = sorted(
            (
                (_parse_time(item.get("execution_start")), _parse_time(item.get("execution_end")), _duration(item))
                for item in instances
            ),
            key=lambda item: item[0] or 0.0,
        )
        merged: list[tuple[float, float]] = []
        fallback = 0.0
        for start, end, duration in intervals:
            if start is None or end is None or end < start:
                fallback += duration
                continue
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        return round(sum(end - start for start, end in merged) + fallback, 6)

    def _overlaps(self, children: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        intervals = []
        for child in children:
            start = _parse_time(child.get("execution_start"))
            end = _parse_time(child.get("execution_end"))
            if start is not None and end is not None:
                intervals.append((start, end, str(child.get("execution_id"))))
        overlaps = []
        for index, current in enumerate(intervals):
            for other in intervals[index + 1:]:
                overlap = min(current[1], other[1]) - max(current[0], other[0])
                if overlap > 0.0:
                    overlaps.append({
                        "first_execution_id": current[2],
                        "second_execution_id": other[2],
                        "overlap_seconds": round(overlap, 6),
                    })
        return overlaps

    def _boundary_violations(
        self,
        root: Mapping[str, Any],
        children: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        root_start = _parse_time(root.get("execution_start"))
        root_end = _parse_time(root.get("execution_end"))
        if root_start is None or root_end is None:
            return []
        violations = []
        for child in children:
            start = _parse_time(child.get("execution_start"))
            end = _parse_time(child.get("execution_end"))
            if start is None or end is None:
                continue
            if start < root_start or end > root_end:
                violations.append({
                    "execution_id": child.get("execution_id"),
                    "parent_execution_id": root.get("execution_id"),
                    "violation": "child_interval_outside_parent_boundary",
                })
        return violations

    def _relationship(self, root: Mapping[str, Any], children: Sequence[Mapping[str, Any]]) -> str:
        if not children:
            return "single_execution"
        if self._overlaps(children):
            return "overlapping_or_parallel_execution"
        if root and all(child.get("execution_parent") == root.get("execution_id") for child in children):
            return "nested_execution"
        return "sequential_execution"


def _duration(instance: Mapping[str, Any]) -> float:
    return round(max(
        _number(instance.get("duration_seconds")),
        _number(instance.get("elapsed_seconds")),
        _number(instance.get("elapsed_time")),
        _number(instance.get("wall_clock_time")),
    ), 6)


def _number(value: Any) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return number if isfinite(number) else 0.0


def _parse_time(value: Any) -> float | None:
    if not value:
        return None
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    return parsed.timestamp()


execution_timing_unification_engine = ExecutionTimingUnificationEngine()


__all__ = [
    "CANONICAL_TIMING_SCOPES",
    "ExecutionTimingRecord",
    "ExecutionTimingState",
    "ExecutionTimingUnificationEngine",
    "execution_timing_unification_engine",
]
