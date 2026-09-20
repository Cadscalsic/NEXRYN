"""Semantic reconciliation for reporting lifecycle timing values."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from math import isfinite
from typing import Any, Iterable, Mapping


REPORT_TIMING_SCHEMA_VERSION = "report-timing-semantics-v1"
EPSILON = 0.000001
ROOT_SCOPE = "REPORT_LIFECYCLE_TOTAL_TIME"


REPORT_TIMING_TAXONOMY = {
    "REPORT_INPUT_COLLECTION_TIME": {
        "owner": "Top-Level Reporting Coordinator",
        "label": "Report Input Collection Time",
    },
    "CANONICAL_REPORT_ASSEMBLY_TIME": {
        "owner": "Canonical Report Builder",
        "label": "Canonical Report Assembly Time",
    },
    "COGNITIVE_SUMMARY_AGGREGATION_TIME": {
        "owner": "Cognitive Aggregation Layer",
        "label": "Cognitive Summary Aggregation Time",
    },
    "REPORT_BINDING_TIME": {
        "owner": "Canonical Report Binding Engine",
        "label": "Report Binding Time",
    },
    "REPORT_VISIBILITY_FILTERING_TIME": {
        "owner": "Report Level Separation Contract",
        "label": "Report Visibility Filtering Time",
    },
    "REPORT_COMPRESSION_TIME": {
        "owner": "Compact Report Compression Engine",
        "label": "Report Compression Time",
    },
    "REPRESENTATION_VALIDATION_TIME": {
        "owner": "Representation Layer Validation Engine",
        "label": "Representation Validation Time",
    },
    "FINAL_REPORT_RENDERING_TIME": {
        "owner": "Final Report Renderer",
        "label": "Final Report Rendering Time",
    },
    "TECHNICAL_APPENDIX_SERIALIZATION_TIME": {
        "owner": "Technical Appendix Writer",
        "label": "Technical Appendix Serialization Time",
    },
    "REPORT_ARTIFACT_WRITING_TIME": {
        "owner": "Artifact Writer",
        "label": "Report Artifact Writing Time",
    },
    "CONSOLE_EMISSION_TIME": {
        "owner": "Final Report Renderer",
        "label": "Console Emission Time",
    },
    ROOT_SCOPE: {
        "owner": "Top-Level Reporting Coordinator",
        "label": "Report Lifecycle Total Time",
    },
}


LEGACY_REPORT_TIMING_FIELDS = {
    "report_generation_time": "AMBIGUOUS",
    "report_time": "AMBIGUOUS",
    "render_time": "FINAL_REPORT_RENDERING_TIME",
    "final_report_time": "AMBIGUOUS",
    "report_builder_duration": "CANONICAL_REPORT_ASSEMBLY_TIME",
    "reporting_duration": "REPORT_LIFECYCLE_TOTAL_TIME",
    "serialization_time": "TECHNICAL_APPENDIX_SERIALIZATION_TIME",
    "final_context_time": "REPORT_INPUT_COLLECTION_TIME",
}


MODULE_SCOPE_HINTS = {
    "assemble_final_context": "REPORT_INPUT_COLLECTION_TIME",
    "build_runtime_metric_bridge": "REPORT_INPUT_COLLECTION_TIME",
    "assemble_performance_report": "CANONICAL_REPORT_ASSEMBLY_TIME",
    "runtime_attribution_report": "CANONICAL_REPORT_ASSEMBLY_TIME",
    "performance_intelligence_report": "COGNITIVE_SUMMARY_AGGREGATION_TIME",
    "build_training_report": "COGNITIVE_SUMMARY_AGGREGATION_TIME",
    "ledger_report": "COGNITIVE_SUMMARY_AGGREGATION_TIME",
    "concept_lifecycle_report": "COGNITIVE_SUMMARY_AGGREGATION_TIME",
    "collect_task_performance_reports": "REPORT_INPUT_COLLECTION_TIME",
    "collect_governance_reports": "REPORT_INPUT_COLLECTION_TIME",
    "report_generation": "FINAL_REPORT_RENDERING_TIME",
    "report": "FINAL_REPORT_RENDERING_TIME",
}


SOURCE_PRIORITY = {
    "Report Timing Semantics": 0,
    "Final Report Renderer": 1,
    "ExecutionTimingState": 2,
    "Per-Runtime Timing Records": 3,
    "Runtime Metric Attribution": 4,
    "Legacy Timing Field": 9,
}


class ReportTimingSemanticEngine:
    """Build one explicit reporting timing contract from existing values."""

    system_name = "report_timing_semantic_engine"

    def reconcile(
        self,
        *,
        timing_records: Iterable[Mapping[str, Any]] | None = None,
        performance: Mapping[str, Any] | None = None,
        timing_state: Mapping[str, Any] | None = None,
        timing_summary: Mapping[str, Any] | None = None,
        runtime_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        performance = performance if isinstance(performance, Mapping) else {}
        timing_state = timing_state if isinstance(timing_state, Mapping) else {}
        timing_summary = timing_summary if isinstance(timing_summary, Mapping) else {}
        runtime_metadata = runtime_metadata if isinstance(runtime_metadata, Mapping) else {}
        execution_id = str(runtime_metadata.get("execution_id") or "")
        records = self._collect_records(
            timing_records or [],
            performance=performance,
            timing_state=timing_state,
            timing_summary=timing_summary,
            execution_id=execution_id,
        )
        canonical, conflicts = self._deduplicate(records)
        root = self._root_record(canonical, execution_id)
        if root and root not in canonical:
            canonical.insert(0, root)
        nodes = self._nodes(canonical, root)
        phase_nodes = [node for node in nodes if node["timing_scope"] != ROOT_SCOPE]
        phase_sum = round(sum(node["inclusive_duration_seconds"] for node in phase_nodes), 6)
        phase_union = self._interval_union(phase_nodes)
        lifecycle_total = self._duration(root or {}) if root else (phase_union or None)
        overlap = round(max(phase_sum - phase_union, 0.0), 6)
        ambiguous = self._legacy_mappings(performance, timing_state, timing_summary)
        source_conflict_detected = any(
            item.get("source_consistency") != "CONSISTENT" for item in conflicts
        )
        semantics_valid = not source_conflict_detected
        summary = self._summary(nodes, lifecycle_total)
        summary.update({
            "report_timing_semantics_valid": semantics_valid,
            "report_timing_reconciliation_success": semantics_valid,
            "report_phase_duration_sum": phase_sum,
            "report_phase_interval_union": phase_union,
            "report_overlap_duration": overlap,
            "report_exclusive_total": phase_union,
            "report_timing_reconciliation_status": (
                "VALID" if semantics_valid else "VALID_WITH_SOURCE_CONFLICTS"
            ),
            "report_timing_source_conflicts": conflicts,
            "ambiguous_legacy_timing_fields": [
                item for item in ambiguous
                if item["legacy_timing_semantics"] == "AMBIGUOUS"
            ],
        })
        return {
            "system": self.system_name,
            "schema_version": REPORT_TIMING_SCHEMA_VERSION,
            "report_timing_taxonomy": deepcopy(REPORT_TIMING_TAXONOMY),
            "report_timing_nodes": nodes,
            "report_timing_summary": summary,
            "report_timing_source_conflicts": conflicts,
            "legacy_report_timing_mappings": ambiguous,
            "report_timing_semantics_valid": semantics_valid,
            "report_timing_reconciliation_success": semantics_valid,
        }

    def _collect_records(
        self,
        timing_records: Iterable[Mapping[str, Any]],
        *,
        performance: Mapping[str, Any],
        timing_state: Mapping[str, Any],
        timing_summary: Mapping[str, Any],
        execution_id: str,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for record in timing_records:
            if not isinstance(record, Mapping):
                continue
            mapped = self._map_timing_record(record)
            if mapped:
                records.append(mapped)
        for item in self._list(performance.get("module_timings")) + self._list(performance.get("stage_metrics")):
            scope = self._module_scope(item)
            if not scope:
                continue
            duration = self._duration(item)
            if duration <= 0.0:
                continue
            records.append(self._record(
                scope,
                duration,
                execution_id=execution_id or str(item.get("execution_id") or ""),
                report_id=str(item.get("report_id") or "runtime_report"),
                source="Per-Runtime Timing Records",
                method="existing_module_timing_duration",
                raw=item,
            ))
        reporting_duration = self._legacy_number(performance, timing_state, timing_summary, "reporting_duration")
        if reporting_duration is not None:
            records.append(self._record(
                ROOT_SCOPE,
                reporting_duration,
                execution_id=execution_id,
                source="Legacy Timing Field",
                method="legacy_reporting_duration",
            ))
        return records

    def _map_timing_record(self, record: Mapping[str, Any]) -> dict[str, Any] | None:
        scope = str(record.get("timing_scope") or record.get("scope") or "").upper()
        if scope == "REPORT_GENERATION_TIME":
            mapped_scope = "FINAL_REPORT_RENDERING_TIME"
        elif scope == ROOT_SCOPE:
            mapped_scope = ROOT_SCOPE
        elif scope in REPORT_TIMING_TAXONOMY:
            mapped_scope = scope
        else:
            return None
        duration = self._duration(record)
        if duration <= 0.0:
            return None
        mapped = dict(record)
        mapped["timing_scope"] = mapped_scope
        mapped.setdefault("measurement_source", "ExecutionTimingState")
        mapped.setdefault("measurement_method", "existing_timing_record_semantic_mapping")
        return mapped

    def _deduplicate(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            grouped.setdefault(str(record.get("timing_scope")), []).append(record)
        canonical = []
        conflicts = []
        for scope in sorted(grouped):
            candidates = sorted(grouped[scope], key=self._source_rank)
            selected = candidates[0]
            alternates = candidates[1:]
            consistency = "CONSISTENT"
            if any(abs(self._duration(item) - self._duration(selected)) > 0.001 for item in alternates):
                consistency = "CONFLICTING_DURATION"
            selected = dict(selected)
            selected["canonical_timing_source"] = self._source(selected)
            selected["alternate_timing_sources"] = [self._source(item) for item in alternates]
            selected["source_consistency"] = consistency
            selected["source_conflict_detected"] = consistency != "CONSISTENT"
            canonical.append(selected)
            if alternates:
                conflicts.append({
                    "timing_scope": scope,
                    "canonical_timing_source": selected["canonical_timing_source"],
                    "alternate_timing_sources": selected["alternate_timing_sources"],
                    "source_consistency": consistency,
                    "source_conflict_detected": consistency != "CONSISTENT",
                })
        return canonical, conflicts

    def _root_record(self, records: list[dict[str, Any]], execution_id: str) -> dict[str, Any] | None:
        existing = next((record for record in records if record.get("timing_scope") == ROOT_SCOPE), None)
        if existing:
            return existing
        union = self._interval_union(records)
        if union > 0.0:
            return self._record(
                ROOT_SCOPE,
                union,
                execution_id=execution_id,
                source="Report Timing Semantics",
                method="phase_interval_union",
            )
        if records:
            return self._record(
                ROOT_SCOPE,
                sum(self._duration(record) for record in records),
                execution_id=execution_id,
                source="Report Timing Semantics",
                method="phase_duration_sum_without_intervals",
            )
        return None

    def _nodes(self, records: list[dict[str, Any]], root: Mapping[str, Any] | None) -> list[dict[str, Any]]:
        root_id = str((root or {}).get("timing_id") or f"runtime_report:{ROOT_SCOPE}")
        nodes = []
        for record in records:
            scope = str(record.get("timing_scope"))
            taxonomy = REPORT_TIMING_TAXONOMY[scope]
            timing_id = str(record.get("timing_id") or f"{record.get('report_id') or 'runtime_report'}:{scope}")
            is_root = scope == ROOT_SCOPE
            nodes.append({
                "timing_id": timing_id,
                "execution_id": str(record.get("execution_id") or ""),
                "report_id": str(record.get("report_id") or "runtime_report"),
                "timing_scope": scope,
                "stage_name": taxonomy["label"],
                "timing_owner": taxonomy["owner"],
                "parent_timing_id": None if is_root else root_id,
                "start_timestamp": str(record.get("start_timestamp") or record.get("execution_start") or ""),
                "end_timestamp": str(record.get("end_timestamp") or record.get("execution_end") or ""),
                "inclusive_duration_seconds": round(self._duration(record), 6),
                "exclusive_duration_seconds": round(self._duration(record), 6),
                "measurement_source": self._source(record),
                "measurement_method": str(record.get("measurement_method") or "existing_duration"),
                "clock_type": str(record.get("clock_type") or "existing_runtime_clock"),
                "timing_status": str(record.get("timing_status") or "OBSERVED"),
                "validation_status": str(record.get("validation_status") or "VALID"),
                "schema_version": REPORT_TIMING_SCHEMA_VERSION,
                "canonical_timing_source": record.get("canonical_timing_source") or self._source(record),
                "alternate_timing_sources": list(record.get("alternate_timing_sources") or []),
                "source_consistency": record.get("source_consistency") or "CONSISTENT",
                "source_conflict_detected": bool(record.get("source_conflict_detected")),
            })
        return sorted(nodes, key=lambda node: (node["parent_timing_id"] is not None, node["timing_scope"]))

    def _summary(self, nodes: list[dict[str, Any]], lifecycle_total: float | None) -> dict[str, Any]:
        by_scope = {node["timing_scope"]: node["inclusive_duration_seconds"] for node in nodes}
        result = {
            "report_lifecycle_total_time": lifecycle_total,
            "report_input_collection_time": by_scope.get("REPORT_INPUT_COLLECTION_TIME"),
            "canonical_report_assembly_time": by_scope.get("CANONICAL_REPORT_ASSEMBLY_TIME"),
            "cognitive_summary_aggregation_time": by_scope.get("COGNITIVE_SUMMARY_AGGREGATION_TIME"),
            "report_binding_time": by_scope.get("REPORT_BINDING_TIME"),
            "report_visibility_filtering_time": by_scope.get("REPORT_VISIBILITY_FILTERING_TIME"),
            "report_compression_time": by_scope.get("REPORT_COMPRESSION_TIME"),
            "representation_validation_time": by_scope.get("REPRESENTATION_VALIDATION_TIME"),
            "final_report_rendering_time": by_scope.get("FINAL_REPORT_RENDERING_TIME"),
            "technical_appendix_serialization_time": by_scope.get("TECHNICAL_APPENDIX_SERIALIZATION_TIME"),
            "report_artifact_writing_time": by_scope.get("REPORT_ARTIFACT_WRITING_TIME"),
            "console_emission_time": by_scope.get("CONSOLE_EMISSION_TIME"),
            "report_timing_status": "VALID",
        }
        return result

    def _legacy_mappings(self, *sources: Mapping[str, Any]) -> list[dict[str, Any]]:
        mappings = []
        for source in sources:
            candidates = [source]
            nested_breakdown = source.get("runtime_breakdown") if isinstance(source, Mapping) else None
            if isinstance(nested_breakdown, Mapping):
                candidates.append(nested_breakdown)
            for candidate in candidates:
                for field, target in LEGACY_REPORT_TIMING_FIELDS.items():
                    if field not in candidate:
                        continue
                    mappings.append({
                        "legacy_field": field,
                        "canonical_timing_scope": None if target == "AMBIGUOUS" else target,
                        "legacy_timing_semantics": target,
                        "normal_reporting_allowed": target != "AMBIGUOUS",
                        "diagnostic_compatibility_only": target == "AMBIGUOUS",
                    })
        return list({item["legacy_field"]: item for item in mappings}.values())

    def _module_scope(self, item: Mapping[str, Any]) -> str | None:
        name = str(item.get("module") or item.get("stage_name") or item.get("stage") or "").lower()
        name = name.removesuffix("_time").removesuffix("_seconds")
        return MODULE_SCOPE_HINTS.get(name)

    def _record(
        self,
        scope: str,
        duration: float,
        *,
        execution_id: str = "",
        report_id: str = "runtime_report",
        source: str,
        method: str,
        raw: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw = raw if isinstance(raw, Mapping) else {}
        return {
            "timing_id": f"{report_id}:{scope}",
            "execution_id": execution_id,
            "report_id": report_id,
            "timing_scope": scope,
            "inclusive_duration_seconds": round(max(float(duration), 0.0), 6),
            "exclusive_duration_seconds": round(max(float(duration), 0.0), 6),
            "start_timestamp": raw.get("start_timestamp") or raw.get("execution_start") or "",
            "end_timestamp": raw.get("end_timestamp") or raw.get("execution_end") or "",
            "measurement_source": source,
            "measurement_method": method,
            "clock_type": raw.get("clock_type") or "existing_runtime_clock",
            "timing_status": "OBSERVED",
            "validation_status": "VALID",
            "schema_version": REPORT_TIMING_SCHEMA_VERSION,
        }

    def _interval_union(self, nodes: Iterable[Mapping[str, Any]]) -> float:
        intervals = []
        fallback = 0.0
        for node in nodes:
            start = self._parse_time(node.get("start_timestamp") or node.get("execution_start"))
            end = self._parse_time(node.get("end_timestamp") or node.get("execution_end"))
            duration = self._duration(node)
            if start is None or end is None or end <= start:
                fallback += duration
            else:
                intervals.append((start, end))
        intervals.sort()
        merged: list[tuple[float, float]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        return round(sum(end - start for start, end in merged) + fallback, 6)

    def _legacy_number(self, *sources_and_field: Any) -> float | None:
        field = str(sources_and_field[-1])
        for source in sources_and_field[:-1]:
            if isinstance(source, Mapping) and field in source:
                value = self._number(source.get(field), -1.0)
                if value >= 0.0:
                    return value
        return None

    def _duration(self, record: Mapping[str, Any]) -> float:
        return max(
            self._number(record.get("inclusive_duration_seconds"), -1.0),
            self._number(record.get("wall_duration_seconds"), -1.0),
            self._number(record.get("duration_seconds"), -1.0),
            self._number(record.get("seconds"), -1.0),
            self._number(record.get("total_duration"), -1.0),
            0.0,
        )

    def _source_rank(self, record: Mapping[str, Any]) -> tuple[int, str]:
        source = self._source(record)
        return SOURCE_PRIORITY.get(source, 5), source

    def _source(self, record: Mapping[str, Any]) -> str:
        return str(record.get("measurement_source") or "UNKNOWN_SOURCE")

    def _list(self, value: Any) -> list[Mapping[str, Any]]:
        return [item for item in (value if isinstance(value, list) else []) if isinstance(item, Mapping)]

    def _number(self, value: Any, default: float = 0.0) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        return number if isfinite(number) else default

    def _parse_time(self, value: Any) -> float | None:
        if not value:
            return None
        text = str(value)
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(text, fmt).timestamp()
                except ValueError:
                    continue
        return None


report_timing_semantic_engine = ReportTimingSemanticEngine()


__all__ = [
    "LEGACY_REPORT_TIMING_FIELDS",
    "REPORT_TIMING_SCHEMA_VERSION",
    "REPORT_TIMING_TAXONOMY",
    "ReportTimingSemanticEngine",
    "report_timing_semantic_engine",
]
