from __future__ import annotations

from copy import deepcopy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from runtime.reporting.pre_final_report_diagnostics import (
    pre_final_report_diagnostics,
)


COMPRESSION_PROFILES = {
    "minimal": "MINIMAL",
    "normal": "NORMAL",
    "diagnostic_summary": "DIAGNOSTIC_SUMMARY",
    "full_diagnostic": "FULL_DIAGNOSTIC",
    "full": "FULL_DIAGNOSTIC",
    "debug": "FULL_DIAGNOSTIC",
    "audit": "DIAGNOSTIC_SUMMARY",
}

CONSOLE_BUDGETS = {
    "MINIMAL": 8000,
    "NORMAL": 20000,
    "DIAGNOSTIC_SUMMARY": 50000,
    "FULL_DIAGNOSTIC": 0,
}


class CompactReportCompressionEngine:
    """Compresses canonical report state into a deterministic report view."""

    HEAVY_KEYS = {
        "runtime_metric_confidence_by_id",
        "execution_timeline",
        "execution_telemetry",
        "runtime_telemetry",
        "execution_registry",
        "successful_bindings",
        "metric_ownership",
        "execution_costs",
        "snapshot_payloads",
        "validation_history",
        "snapshot_reports",
        "latest_snapshot_payload",
        "semantic_memory",
        "knowledge_fabric",
        "runtime_context",
        "final_context",
        "pipeline_context",
        "raw_runtime_context",
        "full_runtime_context",
    }
    CRITICAL_KEYS = {
        "runtime_status",
        "status",
        "final_status",
        "errors",
        "warnings",
        "critical_warnings",
        "tasks_executed",
        "successful_tasks",
        "failed_tasks",
        "execution_coverage",
        "snapshot_coverage",
        "lifecycle_coverage",
        "total_runtime_seconds",
        "execution_time",
        "generated_concepts",
        "generated_programs",
        "validated_programs",
        "truth_candidate_count",
        "average_program_confidence",
        "overall_search_quality",
        "search_efficiency",
        "search_coverage",
        "search_entropy",
        "runtime_timing_summary",
        "top_time_consumers",
        "timing_coverage",
        "untracked_time",
        "active_compute_time",
        "report_generation_time",
        "reporting_timing_summary",
        "report_lifecycle_total_time",
        "final_report_rendering_time",
        "finalization_time",
    }
    TIMING_SUMMARY_KEYS = {
        "stage_timing_summary",
        "runtime_timing_summary",
        "top_time_consumers",
        "timing_coverage",
        "untracked_time",
        "active_compute_time",
        "report_generation_time",
        "reporting_timing_summary",
        "report_lifecycle_total_time",
        "final_report_rendering_time",
        "finalization_time",
    }
    KNOWLEDGE_KEYS = {
        "cognitive_objects_generated",
        "experience_count",
        "semantic_memory_entries",
        "semantic_domains",
        "fabric_links",
        "fabric_bridges",
        "cross_domain_links",
        "fabric_connectivity",
        "orphan_concepts",
        "isolated_domains",
    }
    ANOMALY_KEYS = {
        "errors",
        "warnings",
        "rejected_metrics",
        "missing_snapshots",
        "missing_snapshot_runtimes",
        "missing_executions",
        "missing_execution_instances",
        "conflicting_counts",
        "timing_inconsistencies",
        "coverage_below_threshold",
        "lifecycle_gaps",
    }
    REPORT_SECTION_KEYS = {
        "EXECUTABLE_INTELLIGENCE_REPORT",
        "executable_intelligence_report",
        "EXECUTABLE_INTELLIGENCE_ENGINE_REPORT",
        "executable_intelligence_engine_report",
    }

    def __init__(self, console_budgets: dict[str, int] | None = None):
        self.console_budgets = dict(CONSOLE_BUDGETS)
        if console_budgets:
            self.console_budgets.update(console_budgets)
        self.stats = self._empty_stats()

    def compress(
        self,
        canonical_report: dict[str, Any] | None,
        *,
        profile: str = "normal",
        artifact_directory: str | os.PathLike[str] | None = None,
        write_appendix: bool = False,
    ) -> dict[str, Any]:
        canonical_report = (
            canonical_report if isinstance(canonical_report, dict) else {}
        )
        profile_name = self._profile(profile)
        self.stats = self._empty_stats()
        pre_final_report_diagnostics.phase_enter(
            "REPORT_COMPRESSION",
            profile=profile_name,
            top_level_keys=len(canonical_report),
        )
        pre_final_report_diagnostics.collection_snapshot(
            "COMPRESSION_INPUT",
            canonical_report,
        )
        actual_size_before = self._actual_size(canonical_report)

        if profile_name == "FULL_DIAGNOSTIC":
            compressed = deepcopy(canonical_report)
            appendix = {}
        else:
            compressed, appendix = self._compress_dict(
                canonical_report,
                profile_name=profile_name,
                path="",
                seen={},
                depth=0,
            )
            compressed = self._enforce_console_budget(
                compressed,
                appendix,
                profile_name,
            )

        compressed = self._preserve_semantic_summaries(
            canonical_report,
            compressed,
        )
        compressed = self._preserve_timing_summaries(
            canonical_report,
            compressed,
            profile_name,
        )
        warnings = self._collect_anomalies(canonical_report)
        if warnings:
            compressed.setdefault("compression_warnings", warnings)

        actual_size_after = self._actual_size(compressed)
        self.stats.update({
            "estimated_size_before": actual_size_before,
            "estimated_size_after": actual_size_after,
            "actual_size_before": actual_size_before,
            "actual_size_after": actual_size_after,
            "report_compression_ratio": self._compression_ratio(
                actual_size_before,
                actual_size_after,
            ),
            "semantic_preservation_score": (
                1.0 if self._critical_information_preserved(
                    canonical_report,
                    compressed,
                ) else 0.0
            ),
            "critical_information_preserved": (
                self._critical_information_preserved(
                    canonical_report,
                    compressed,
                )
            ),
            "technical_appendix_available": bool(appendix),
        })

        appendix_path = None
        if write_appendix and artifact_directory:
            appendix_path = Path(artifact_directory) / (
                "runtime_technical_appendix.json"
            )
            self.write_appendix({
                "canonical_report": canonical_report,
                "diagnostic_appendix": appendix,
                "compression_statistics": self.stats,
            }, appendix_path)
            self.stats["technical_appendix_artifact_written"] = True
            self.stats["technical_appendix_artifact_path"] = str(appendix_path)

        compressed["compact_report"] = dict(self.stats)
        compressed["compression_profile"] = profile_name
        compressed["technical_appendix_available"] = bool(appendix)
        if appendix_path is not None:
            compressed["technical_appendix_artifact_reference"] = str(
                appendix_path,
            )
        pre_final_report_diagnostics.phase_exit(
            "REPORT_COMPRESSION",
            actual_size_before=actual_size_before,
            actual_size_after=actual_size_after,
            compressed_keys=len(compressed),
            appendix_entries=len(appendix),
        )
        return {
            "canonical_report": canonical_report,
            "compressed_report": compressed,
            "diagnostic_appendix": appendix,
            "compression_statistics": dict(self.stats),
        }

    def write_appendix(self, payload: dict[str, Any], path: Path) -> None:
        text = json.dumps(
            self._json_safe(payload),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._atomic_write_text(text, path)

    def report(self) -> dict[str, Any]:
        return dict(self.stats)

    def _compress_dict(
        self,
        value: dict[str, Any],
        *,
        profile_name: str,
        path: str,
        seen: dict[str, str],
        depth: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        compressed: dict[str, Any] = {}
        appendix: dict[str, Any] = {}
        for key in sorted(value.keys(), key=str):
            pre_final_report_diagnostics.count("compression_dict_keys")
            item = value[key]
            child_path = f"{path}.{key}" if path else str(key)
            if key in self.HEAVY_KEYS and key not in self.CRITICAL_KEYS:
                self.stats["heavy_keys_detected"] += 1
                self.stats["heavy_keys_removed"] += 1
                compressed[f"{key}_summary"] = self._heavy_summary(key, item)
                appendix[child_path] = deepcopy(item)
                self.stats["diagnostic_fields_externalized"] += 1
                continue
            if profile_name == "MINIMAL" and not self._minimal_allowed(key):
                appendix[child_path] = deepcopy(item)
                self.stats["diagnostic_fields_externalized"] += 1
                continue

            signature = self._signature(item)
            if isinstance(item, (dict, list)) and signature in seen:
                self.stats["repeated_reports_detected"] += 1
                self.stats["repeated_reports_collapsed"] += 1
                self.stats["duplicate_fields_removed"] += 1
                compressed[key] = {
                    "collapsed_duplicate_report": True,
                    "canonical_reference": seen[signature],
                }
                appendix[child_path] = deepcopy(item)
                continue
            if isinstance(item, (dict, list)):
                seen[signature] = child_path

            compressed_item, appendix_item = self._compress_value(
                item,
                key=key,
                profile_name=profile_name,
                path=child_path,
                seen=seen,
                depth=depth + 1,
            )
            compressed[key] = compressed_item
            if appendix_item:
                appendix.update(appendix_item)
        return compressed, appendix

    def _compress_value(
        self,
        value: Any,
        *,
        key: str,
        profile_name: str,
        path: str,
        seen: dict[str, str],
        depth: int,
    ) -> tuple[Any, dict[str, Any]]:
        if self._is_array_like(value):
            self.stats["arrays_detected"] += 1
            self.stats["arrays_summarized"] += 1
            return self._array_summary(value), {path: deepcopy(value)}
        if isinstance(value, dict):
            specialized = self._specialized_dict_summary(key, value)
            if specialized is not None and profile_name != "FULL_DIAGNOSTIC":
                self.stats["heavy_keys_detected"] += 1
                self.stats["heavy_keys_removed"] += 1
                return specialized, {path: deepcopy(value)}
            max_depth = 2 if profile_name == "MINIMAL" else 5
            if depth > max_depth:
                self.stats["diagnostic_fields_externalized"] += 1
                return self._structure_summary(value), {path: deepcopy(value)}
            return self._compress_dict(
                value,
                profile_name=profile_name,
                path=path,
                seen=seen,
                depth=depth,
            )
        if isinstance(value, (list, tuple, set)):
            items = list(value)
            if self._should_summarize_list(key, items, profile_name):
                self.stats["arrays_detected"] += 1
                self.stats["arrays_summarized"] += 1
                return self._list_summary(key, items), {path: deepcopy(items)}
            limit = self._list_limit(profile_name)
            compressed_items = []
            appendix: dict[str, Any] = {}
            for index, item in enumerate(items[:limit]):
                compressed_item, child_appendix = self._compress_value(
                    item,
                    key=key,
                    profile_name=profile_name,
                    path=f"{path}[{index}]",
                    seen=seen,
                    depth=depth + 1,
                )
                compressed_items.append(compressed_item)
                appendix.update(child_appendix)
            if len(items) > limit:
                compressed_items.append({
                    "truncated": True,
                    "remaining_items": len(items) - limit,
                })
                appendix[path] = deepcopy(items)
                self.stats["diagnostic_fields_externalized"] += 1
            return compressed_items, appendix
        self.stats["canonical_fields_preserved"] += 1
        return value, {}

    def _specialized_dict_summary(
        self,
        key: str,
        value: dict[str, Any],
    ) -> dict[str, Any] | None:
        if key in {
            "runtime_metric_confidence_by_id",
            "metric_ownership",
            "canonical_metrics",
        }:
            return self._metric_map_summary(value)
        if key in {"execution_registry", "runtime_registry"}:
            return self._execution_registry_summary(value)
        if key in {"successful_bindings", "execution_binding_report"}:
            return self._binding_summary(value)
        if key in {"snapshot_payloads", "snapshot_reports"}:
            return self._snapshot_summary(value)
        if key in {"knowledge_fabric", "semantic_memory"}:
            return self._knowledge_summary(value)
        return None

    def _heavy_summary(self, key: str, value: Any) -> dict[str, Any]:
        if key in {"execution_timeline", "execution_telemetry"}:
            return self._timeline_summary(value)
        if key in {"runtime_metric_confidence_by_id", "metric_ownership"}:
            return self._metric_map_summary(value)
        if key == "successful_bindings":
            return self._binding_summary(value)
        if key in {"snapshot_payloads", "snapshot_reports"}:
            return self._snapshot_summary(value)
        if key == "execution_registry":
            return self._execution_registry_summary(value)
        if key in {"semantic_memory", "knowledge_fabric"}:
            return self._knowledge_summary(value)
        if isinstance(value, list):
            return self._list_summary(key, value)
        if isinstance(value, dict):
            summary = self._structure_summary(value)
            summary.update(self._counts_from_mapping(value))
            return summary
        return self._structure_summary(value)

    def _timeline_summary(self, value: Any) -> dict[str, Any]:
        events = value if isinstance(value, list) else []
        counts: dict[str, int] = {}
        timestamps = []
        for event in events:
            if not isinstance(event, dict):
                continue
            state = str(
                event.get("event")
                or event.get("status")
                or event.get("state")
                or "unknown",
            ).lower()
            counts[state] = counts.get(state, 0) + 1
            timestamp = event.get("timestamp") or event.get("time")
            if timestamp is not None:
                timestamps.append(str(timestamp))
        return {
            "summary": "execution_timeline_summarized",
            "total_events": len(events),
            "created_events": counts.get("created", 0),
            "started_events": counts.get("started", 0),
            "completed_events": counts.get("completed", 0),
            "failed_events": counts.get("failed", 0),
            "first_timestamp": min(timestamps) if timestamps else None,
            "last_timestamp": max(timestamps) if timestamps else None,
        }

    def _metric_map_summary(self, value: Any) -> dict[str, Any]:
        mapping = value if isinstance(value, dict) else {}
        confidences = []
        rejected = 0
        below_threshold = []
        for metric_id, metric_value in mapping.items():
            confidence = self._extract_confidence(metric_value)
            if confidence is not None:
                confidences.append(confidence)
                if confidence < 0.5:
                    below_threshold.append(str(metric_id))
            if isinstance(metric_value, dict) and (
                metric_value.get("status") == "rejected"
                or metric_value.get("valid") is False
            ):
                rejected += 1
        validated = len(confidences) - rejected
        return {
            "summary": "metric_map_compressed",
            "validated_metric_count": max(validated, 0),
            "rejected_metric_count": rejected,
            "overall_metric_confidence": (
                round(sum(confidences) / len(confidences), 4)
                if confidences else None
            ),
            "minimum_metric_confidence": min(confidences) if confidences else None,
            "maximum_metric_confidence": max(confidences) if confidences else None,
            "metrics_below_threshold": below_threshold[:10],
            "full_metric_map_artifact_reference": (
                "runtime_technical_appendix.json"
            ),
        }

    def _binding_summary(self, value: Any) -> dict[str, Any]:
        bindings = value
        if isinstance(value, dict):
            bindings = value.get("successful_bindings") or value.get("bindings")
        bindings = bindings if isinstance(bindings, list) else []
        failed = [
            item for item in bindings
            if isinstance(item, dict) and item.get("status") == "failed"
        ]
        latencies = [
            float(item.get("latency", item.get("binding_latency")))
            for item in bindings
            if isinstance(item, dict)
            and isinstance(item.get("latency", item.get("binding_latency")), (int, float))
        ]
        bound_count = len(bindings) - len(failed)
        return {
            "summary": "binding_compressed",
            "bound_runtime_count": bound_count,
            "failed_binding_count": len(failed),
            "binding_coverage": (
                round(bound_count / len(bindings), 4) if bindings else 0.0
            ),
            "average_binding_latency": (
                round(sum(latencies) / len(latencies), 4) if latencies else None
            ),
            "registry_synchronization": "summarized",
            "remaining_unbound_metrics": self._count_matching(
                bindings,
                "unbound",
            ),
            "failed_bindings": failed[:10],
        }

    def _snapshot_summary(self, value: Any) -> dict[str, Any]:
        snapshots = value
        if isinstance(value, dict):
            snapshots = value.get("snapshots") or value.get("snapshot_reports")
        snapshots = snapshots if isinstance(snapshots, list) else []
        failures = [
            item for item in snapshots
            if isinstance(item, dict)
            and item.get("snapshot_generation_success") is False
        ]
        latest = snapshots[-1] if snapshots else {}
        latest_type = latest.get("snapshot_type") if isinstance(latest, dict) else None
        return {
            "summary": "snapshot_payloads_compressed",
            "snapshot_count": len(snapshots),
            "latest_snapshot_type": latest_type,
            "snapshot_generation_success": len(failures) == 0,
            "snapshot_generation_failures": len(failures),
        }

    def _execution_registry_summary(self, value: Any) -> dict[str, Any]:
        registry = value if isinstance(value, dict) else {}
        runtimes = registry.get("runtimes") or registry.get("executions")
        runtime_count = len(runtimes) if isinstance(runtimes, (dict, list)) else len(registry)
        failures = self._count_status(registry, "failed")
        completed = self._count_status(registry, "completed")
        return {
            "summary": "execution_registry_compressed",
            "runtime_count": runtime_count,
            "completed_runtime_count": completed,
            "failed_runtime_count": failures,
            "coverage_score": (
                round(completed / runtime_count, 4) if runtime_count else 0.0
            ),
        }

    def _knowledge_summary(self, value: Any) -> dict[str, Any]:
        mapping = value if isinstance(value, dict) else {}
        summary = {"summary": "knowledge_pipeline_compressed"}
        for key in sorted(self.KNOWLEDGE_KEYS):
            if key in mapping:
                item = mapping[key]
                summary[key] = len(item) if isinstance(item, (list, dict)) else item
        summary.setdefault("semantic_memory_entries", len(mapping))
        return summary

    def _list_summary(self, key: str, items: list[Any]) -> dict[str, Any]:
        if key in {"execution_timeline", "execution_telemetry"}:
            return self._timeline_summary(items)
        if self._looks_like_grid(items):
            rows = len(items)
            columns = max([len(row) for row in items if isinstance(row, list)] or [0])
            return {
                "summary": "grid_summarized",
                "rows": rows,
                "columns": columns,
                "cell_count": sum(
                    len(row) for row in items if isinstance(row, list)
                ),
            }
        return {
            "summary": "array_summarized",
            "item_count": len(items),
            "error_count": self._count_matching(items, "error"),
            "warning_count": self._count_matching(items, "warning"),
        }

    def _array_summary(self, value: Any) -> dict[str, Any]:
        return {
            "summary": "array_summarized",
            "array_summary": True,
            "shape": list(getattr(value, "shape", [])),
            "dtype": str(getattr(value, "dtype", "unknown")),
        }

    def _structure_summary(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return {
                "summary": "structure_summarized",
                "type": "dict",
                "key_count": len(value),
            }
        if isinstance(value, list):
            return {
                "summary": "structure_summarized",
                "type": "list",
                "item_count": len(value),
            }
        return {
            "summary": "structure_summarized",
            "type": type(value).__name__,
        }

    def _counts_from_mapping(self, value: dict[str, Any]) -> dict[str, Any]:
        return {
            "item_count": len(value),
            "error_count": self._count_matching(value.values(), "error"),
            "warning_count": self._count_matching(value.values(), "warning"),
            "validation_status": value.get("validation_status"),
            "coverage_score": value.get("coverage_score"),
            "artifact_reference": "runtime_technical_appendix.json",
        }

    def _preserve_semantic_summaries(
        self,
        canonical: dict[str, Any],
        compressed: dict[str, Any],
    ) -> dict[str, Any]:
        for key in sorted(self.CRITICAL_KEYS | self.KNOWLEDGE_KEYS | self.REPORT_SECTION_KEYS):
            if key in canonical and (
                key not in compressed
                or key in self.REPORT_SECTION_KEYS
            ):
                compressed[key] = deepcopy(canonical[key])
                self.stats["canonical_fields_preserved"] += 1
        for source_key in ("knowledge_fabric", "semantic_memory"):
            source = canonical.get(source_key)
            if not isinstance(source, dict):
                continue
            for key in sorted(self.KNOWLEDGE_KEYS):
                if key in source and key not in compressed:
                    compressed[key] = deepcopy(source[key])
                    self.stats["canonical_fields_preserved"] += 1
        return compressed

    def _preserve_timing_summaries(
        self,
        canonical: dict[str, Any],
        compressed: dict[str, Any],
        profile_name: str,
    ) -> dict[str, Any]:
        allowed = set(self.TIMING_SUMMARY_KEYS)
        if profile_name == "MINIMAL":
            allowed.discard("stage_timing_summary")
        for key in sorted(allowed):
            if key in canonical and key not in compressed:
                compressed[key] = deepcopy(canonical[key])
                self.stats["canonical_fields_preserved"] += 1
        return compressed

    def _collect_anomalies(self, value: Any) -> list[str]:
        anomalies: list[str] = []

        def visit(item: Any, path: str) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    key_text = str(key)
                    child_path = f"{path}.{key_text}" if path else key_text
                    if key_text in self.ANOMALY_KEYS and child not in (None, [], {}, 0, False):
                        anomalies.append(f"{child_path}: {self._anomaly_summary(child)}")
                    if key_text.endswith("coverage") and isinstance(child, (int, float)) and child < 1.0:
                        anomalies.append(f"{child_path}: coverage below 1.0")
                    if key_text.endswith("entropy") and child == 0:
                        anomalies.append(f"{child_path}: suspicious zero entropy")
                    visit(child, child_path)
            elif isinstance(item, list):
                for index, child in enumerate(item[:100]):
                    visit(child, f"{path}[{index}]")

        visit(value, "")
        return list(dict.fromkeys(anomalies))[:25]

    def _anomaly_summary(self, value: Any) -> str:
        if isinstance(value, list):
            return f"{len(value)} entries"
        if isinstance(value, dict):
            return f"{len(value)} fields"
        return str(value)

    def _critical_information_preserved(
        self,
        canonical: dict[str, Any],
        compressed: dict[str, Any],
    ) -> bool:
        for key in self.CRITICAL_KEYS:
            if key in canonical and key not in compressed:
                return False
        return True

    def _enforce_console_budget(
        self,
        compressed: dict[str, Any],
        appendix: dict[str, Any],
        profile_name: str,
    ) -> dict[str, Any]:
        budget = self.console_budgets.get(profile_name, 0)
        if budget <= 0 or self._actual_size(compressed) <= budget:
            return compressed
        reduced = {}
        for key in sorted(compressed.keys(), key=str):
            value = compressed[key]
            if key in self.CRITICAL_KEYS or key.endswith("_summary"):
                reduced[key] = value
            else:
                reduced[key] = self._structure_summary(value)
                appendix[key] = deepcopy(value)
                self.stats["diagnostic_fields_externalized"] += 1
            if self._actual_size(reduced) > budget:
                break
        reduced["console_budget_enforced"] = True
        reduced["technical_appendix_available"] = True
        return reduced

    def _should_summarize_list(
        self,
        key: str,
        items: list[Any],
        profile_name: str,
    ) -> bool:
        if key in self.HEAVY_KEYS:
            return True
        threshold = 3 if profile_name == "MINIMAL" else 25
        if self._looks_like_grid(items):
            return True
        return len(items) > threshold

    def _minimal_allowed(self, key: str) -> bool:
        return (
            key in self.CRITICAL_KEYS
            or key in self.ANOMALY_KEYS
            or (
                key in self.TIMING_SUMMARY_KEYS
                and key != "stage_timing_summary"
            )
        )

    def _list_limit(self, profile_name: str) -> int:
        return {
            "MINIMAL": 3,
            "NORMAL": 10,
            "DIAGNOSTIC_SUMMARY": 25,
            "FULL_DIAGNOSTIC": 1000000,
        }[profile_name]

    def _profile(self, profile: str) -> str:
        return COMPRESSION_PROFILES.get(str(profile).lower(), "NORMAL")

    def _compression_ratio(self, before: int, after: int) -> float:
        if before <= 0:
            return 0.0
        return round(max(0.0, 1.0 - (after / before)), 4)

    def _actual_size(self, value: Any) -> int:
        pre_final_report_diagnostics.phase_enter("JSON_SIZE_SERIALIZATION")
        size = len(json.dumps(self._json_safe(value), sort_keys=True))
        pre_final_report_diagnostics.phase_exit(
            "JSON_SIZE_SERIALIZATION",
            serialized_chars=size,
        )
        return size

    def _signature(self, value: Any) -> str:
        try:
            return json.dumps(self._json_safe(value), sort_keys=True)
        except (TypeError, ValueError):
            return str(value)

    def _json_safe(
        self,
        value: Any,
        *,
        _depth: int = 0,
        _seen: set[int] | None = None,
        _count: list[int] | None = None,
    ) -> Any:
        pre_final_report_diagnostics.count("json_safe_objects")
        _count = _count or [0]
        _count[0] += 1
        if _count[0] > 50_000:
            return {"__json_node_budget_exceeded__": True}
        if _depth >= 6:
            return self._container_summary(value)
        if isinstance(value, dict):
            _seen = _seen or set()
            object_id = id(value)
            if object_id in _seen:
                return {"__recursive_reference__": True}
            _seen.add(object_id)
            result = {}
            for index, (key, item) in enumerate(value.items()):
                if index >= 200:
                    result["__truncated_dict_items__"] = len(value) - 200
                    break
                result[str(key)] = self._json_safe(
                    item,
                    _depth=_depth + 1,
                    _seen=_seen,
                    _count=_count,
                )
            return result
        if isinstance(value, (list, tuple, set)):
            _seen = _seen or set()
            object_id = id(value)
            if object_id in _seen:
                return [{"__recursive_reference__": True}]
            _seen.add(object_id)
            items = list(value)
            result = [
                self._json_safe(
                    item,
                    _depth=_depth + 1,
                    _seen=_seen,
                    _count=_count,
                )
                for item in items[:200]
            ]
            if len(items) > 200:
                result.append({"__truncated_list_items__": len(items) - 200})
            return result
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if hasattr(value, "tolist"):
            try:
                return value.tolist()
            except Exception:
                return str(value)
        return str(value)

    def _container_summary(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {"__dict_keys__": len(value)}
        if isinstance(value, (list, tuple, set)):
            return {"__list_items__": len(value)}
        return str(value)

    def _is_array_like(self, value: Any) -> bool:
        return (
            hasattr(value, "shape")
            and hasattr(value, "dtype")
            and hasattr(value, "tolist")
        )

    def _looks_like_grid(self, value: Any) -> bool:
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(row, list) for row in value[:20])
        )

    def _extract_confidence(self, value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            for key in ("confidence", "metric_confidence", "score"):
                if isinstance(value.get(key), (int, float)):
                    return float(value[key])
        return None

    def _count_matching(self, values: Any, needle: str) -> int:
        count = 0
        for item in values if isinstance(values, list) else list(values):
            if isinstance(item, dict):
                text = json.dumps(self._json_safe(item), sort_keys=True).lower()
            else:
                text = str(item).lower()
            if needle in text:
                count += 1
        return count

    def _count_status(self, value: Any, status: str) -> int:
        if isinstance(value, dict):
            return sum(self._count_status(item, status) for item in value.values())
        if isinstance(value, list):
            return sum(self._count_status(item, status) for item in value)
        if isinstance(value, str):
            return 1 if value.lower() == status else 0
        return 0

    def _atomic_write_text(self, text: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def _empty_stats(self) -> dict[str, Any]:
        return {
            "heavy_keys_detected": 0,
            "heavy_keys_removed": 0,
            "arrays_detected": 0,
            "arrays_summarized": 0,
            "repeated_reports_detected": 0,
            "repeated_reports_collapsed": 0,
            "duplicate_fields_removed": 0,
            "canonical_fields_preserved": 0,
            "diagnostic_fields_externalized": 0,
            "estimated_size_before": 0,
            "estimated_size_after": 0,
            "actual_size_before": 0,
            "actual_size_after": 0,
            "report_compression_ratio": 0.0,
            "semantic_preservation_score": 0.0,
            "critical_information_preserved": False,
            "technical_appendix_available": False,
            "technical_appendix_artifact_written": False,
            "technical_appendix_artifact_path": None,
        }


compact_report_compression_engine = CompactReportCompressionEngine()
