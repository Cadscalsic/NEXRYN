"""Hierarchical reconciliation for already-recorded execution timings."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from math import isfinite
from typing import Any, Iterable, Mapping


EPSILON = 0.000001
ROOT_ID = "TOTAL_WALL_TIME:ROOT"


PARENT_SCOPES = {
    "TOTAL_WALL_TIME",
    "COGNITIVE_RUNTIME_TIME",
    "TASK_EXECUTION_TIME",
    "TASK_EXECUTION",
}

TASK_CHILD_HINTS = {
    "CHILD_RUNTIME_TIME",
    "CONTEXT_TIME",
    "CONTEXT",
    "REASONING_TIME",
    "REASONING",
    "SEARCH_TIME",
    "SEARCH",
    "CONCEPT_FORMATION_TIME",
    "CONCEPT_FORMATION",
    "PROGRAM_SYNTHESIS_TIME",
    "PROGRAM_SYNTHESIS",
    "ADAPTIVE_SEARCH_TIME",
    "ADAPTIVE_SEARCH",
    "REUSE_TIME",
    "PROCESS_TIME",
    "PROCESS",
    "DEPENDENCY_TIME",
    "DEPENDENCY",
    "CAUSAL_TIME",
    "CAUSAL",
    "TRUTH_TIME",
    "TRUTH",
    "MEMORY_TIME",
    "MEMORY",
    "EVALUATION_TIME",
    "EVALUATION",
    "GOVERNANCE_TIME",
    "GOVERNANCE",
}

TASK_CHILD_PREFIXES = (
    "TASK_EXECUTION:",
    "TASK_EXECUTION_",
    "TASK_EXECUTION/",
)


SOURCE_PRIORITY = {
    "ExecutionTimingState": 0,
    "runtime_lifecycle": 0,
    "execution_timing_unification_engine": 1,
    "Per-Runtime Timing Records": 2,
    "Runtime Metric Attribution": 3,
    "RUNTIME_BREAKDOWN": 4,
}


class HierarchicalTimingReconciliationEngine:
    """Reconcile canonical timing records into lifecycle and resource views."""

    system_name = "hierarchical_timing_reconciliation_engine"

    def reconcile(
        self,
        timing_records: Iterable[Mapping[str, Any]] | None = None,
        *,
        total_wall_time: float | None = None,
        active_compute_time: float | None = None,
        stage_rows: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        raw_records = [
            dict(record)
            for record in (timing_records or [])
            if isinstance(record, Mapping)
        ]
        raw_records.extend(
            self._record_from_stage_row(row)
            for row in (stage_rows or [])
            if isinstance(row, Mapping)
        )
        canonical, source_conflicts = self._deduplicate(raw_records)
        nodes = [self._node(record) for record in canonical]
        nodes = [node for node in nodes if node["validation_status"] != "REJECTED"]
        root = self._root_node(nodes, total_wall_time)
        nodes = [root, *[node for node in nodes if node["timing_id"] != root["timing_id"]]]
        by_id = {node["timing_id"]: node for node in nodes}
        self._derive_parentage(nodes, root["timing_id"])
        boundary_violations = self._validate_graph(nodes, by_id, root["timing_id"])
        child_map = self._child_map(nodes)
        overlap_duration = 0.0
        parallel_overlap_duration = 0.0
        duplicate_overlap_duration = 0.0
        for node in nodes:
            children = [by_id[child_id] for child_id in child_map.get(node["timing_id"], [])]
            stats = self._child_interval_stats(node, children)
            node.update(stats)
            node["exclusive_duration_seconds"] = round(
                max(node["inclusive_duration_seconds"] - stats["child_interval_union_duration"], 0.0),
                6,
            )
            node["resource_exclusive_duration_seconds"] = node["exclusive_duration_seconds"]
            overlap_duration += stats["sibling_overlap_duration"]
            parallel_overlap_duration += stats["parallel_overlap_duration"]
            duplicate_overlap_duration += stats["duplicate_overlap_duration"]

        self._apply_sibling_resource_overlap_adjustments(nodes, child_map, by_id)
        hierarchy_rows = self._hierarchy_rows(nodes, child_map, root["timing_id"])
        resource_rows, denominator = self._resource_rows(nodes, root["timing_id"], active_compute_time)
        percentage_sum = round(sum(row["percentage_of_active_compute"] for row in resource_rows), 6)
        parent_count = sum(1 for node in nodes if child_map.get(node["timing_id"]))
        child_count = sum(1 for node in nodes if node.get("parent_timing_id"))
        valid = not boundary_violations and percentage_sum <= 100.0001
        return {
            "system": self.system_name,
            "timing_hierarchy_valid": valid,
            "timing_reconciliation_success": valid,
            "root_timing_id": root["timing_id"],
            "timing_node_count": len(nodes),
            "parent_node_count": parent_count,
            "child_node_count": child_count,
            "exclusive_time_total": round(sum(row["exclusive_duration"] for row in resource_rows), 6),
            "inclusive_time_total": round(sum(node["inclusive_duration_seconds"] for node in nodes), 6),
            "overlap_duration": round(overlap_duration, 6),
            "parallel_overlap_duration": round(parallel_overlap_duration, 6),
            "duplicate_overlap_duration": round(duplicate_overlap_duration, 6),
            "resource_percentage_sum": percentage_sum,
            "resource_percentage_denominator": "ACTIVE_COMPUTE_TIME",
            "active_compute_time": denominator,
            "timing_source_conflicts": source_conflicts,
            "timing_boundary_violations": boundary_violations,
            "timing_hierarchy_summary": hierarchy_rows,
            "execution_hierarchy_view": hierarchy_rows,
            "resource_consumption_ranking": resource_rows,
            "diagnostic_timing_nodes": nodes,
            "overlap_detected": overlap_duration > EPSILON or duplicate_overlap_duration > EPSILON,
            "overlap_accounted_for": True,
        }

    def _deduplicate(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for record in records:
            if self._duration(record) <= 0.0:
                continue
            key = (
                str(record.get("execution_id") or ""),
                self._semantic_scope(record),
                str(record.get("parent_timing_id") or ""),
            )
            groups.setdefault(key, []).append(record)
        canonical = []
        conflicts = []
        for key in sorted(groups, key=str):
            candidates = groups[key]
            ranked = sorted(candidates, key=self._source_rank)
            selected = ranked[0]
            alternatives = ranked[1:]
            if alternatives:
                conflicts.append({
                    "semantic_key": ":".join(key),
                    "canonical_timing_source": self._source(selected),
                    "alternate_timing_sources": [self._source(item) for item in alternatives],
                    "source_consistency": self._source_consistency(selected, alternatives),
                })
            selected = dict(selected)
            selected["canonical_timing_source"] = self._source(selected)
            selected["alternate_timing_sources"] = [self._source(item) for item in alternatives]
            selected["source_consistency"] = conflicts[-1]["source_consistency"] if alternatives else "CONSISTENT"
            canonical.append(selected)
        return canonical, conflicts

    def _node(self, record: Mapping[str, Any]) -> dict[str, Any]:
        duration = self._duration(record)
        scope = self._semantic_scope(record)
        timing_id = str(record.get("timing_id") or f"{record.get('execution_id') or 'execution'}:{scope}")
        start = record.get("start_timestamp") or record.get("execution_start")
        end = record.get("end_timestamp") or record.get("execution_end")
        parent = record.get("parent_timing_id")
        return {
            "timing_id": timing_id,
            "stage_name": self._stage_name(record, scope),
            "parent_timing_id": str(parent) if parent else None,
            "execution_id": str(record.get("execution_id") or ""),
            "start_timestamp": str(start or ""),
            "end_timestamp": str(end or ""),
            "inclusive_duration_seconds": round(duration, 6),
            "exclusive_duration_seconds": round(self._number(record.get("exclusive_duration_seconds"), duration), 6),
            "relationship_type": "INDEPENDENT",
            "timing_scope": scope,
            "measurement_source": self._source(record),
            "validation_status": str(record.get("validation_status") or "VALID"),
            "canonical_timing_source": record.get("canonical_timing_source") or self._source(record),
            "alternate_timing_sources": list(record.get("alternate_timing_sources") or []),
            "source_consistency": record.get("source_consistency") or "CONSISTENT",
        }

    def _root_node(self, nodes: list[dict[str, Any]], total_wall_time: float | None) -> dict[str, Any]:
        existing = next((node for node in nodes if node["timing_scope"] == "TOTAL_WALL_TIME"), None)
        if existing:
            existing["timing_id"] = ROOT_ID
            existing["parent_timing_id"] = None
            existing["relationship_type"] = "ROOT"
            return existing
        duration = self._number(total_wall_time, 0.0)
        if duration <= 0.0:
            duration = self._interval_union_duration(nodes) or sum(node["inclusive_duration_seconds"] for node in nodes)
        return {
            "timing_id": ROOT_ID,
            "stage_name": "Total Wall Time",
            "parent_timing_id": None,
            "execution_id": "",
            "start_timestamp": "",
            "end_timestamp": "",
            "inclusive_duration_seconds": round(duration, 6),
            "exclusive_duration_seconds": round(duration, 6),
            "relationship_type": "ROOT",
            "timing_scope": "TOTAL_WALL_TIME",
            "measurement_source": "hierarchical_timing_reconciliation_engine",
            "validation_status": "VALID",
            "canonical_timing_source": "hierarchical_timing_reconciliation_engine",
            "alternate_timing_sources": [],
            "source_consistency": "CONSISTENT",
        }

    def _derive_parentage(self, nodes: list[dict[str, Any]], root_id: str) -> None:
        ids = {node["timing_id"] for node in nodes}
        task_parent = next(
            (
                node for node in nodes
                if node["timing_scope"] in {"COGNITIVE_RUNTIME_TIME", "TASK_EXECUTION_TIME", "TASK_EXECUTION"}
            ),
            None,
        )
        for node in nodes:
            if node["timing_id"] == root_id:
                node["relationship_type"] = "ROOT"
                continue
            parent = node.get("parent_timing_id")
            if parent and parent in ids:
                node["relationship_type"] = "CHILD"
                continue
            if task_parent and node is not task_parent and self._is_task_child(node):
                node["parent_timing_id"] = task_parent["timing_id"]
                node["relationship_type"] = "CHILD"
                continue
            node["parent_timing_id"] = root_id
            node["relationship_type"] = "INDEPENDENT"
        for node in nodes:
            if node["timing_scope"] in PARENT_SCOPES and node["timing_id"] != root_id:
                node["relationship_type"] = "PARENT"

    def _validate_graph(
        self,
        nodes: list[dict[str, Any]],
        by_id: dict[str, dict[str, Any]],
        root_id: str,
    ) -> list[dict[str, Any]]:
        violations = []
        for node in nodes:
            parent_id = node.get("parent_timing_id")
            if not parent_id:
                continue
            if parent_id not in by_id:
                violations.append({"timing_id": node["timing_id"], "violation": "missing_parent"})
                node["parent_timing_id"] = root_id
                continue
            seen = {node["timing_id"]}
            current = by_id[parent_id]
            while current.get("parent_timing_id"):
                current_parent = current["parent_timing_id"]
                if current_parent in seen:
                    violations.append({"timing_id": node["timing_id"], "violation": "invalid_parent_child_cycle"})
                    node["validation_status"] = "REJECTED"
                    break
                seen.add(current["timing_id"])
                current = by_id.get(current_parent, {})
                if not current:
                    break
            parent = by_id.get(parent_id)
            if parent and self._outside_parent(node, parent):
                violations.append({
                    "timing_id": node["timing_id"],
                    "parent_timing_id": parent_id,
                    "violation": "child_interval_outside_parent_boundary",
                })
        return violations

    def _child_interval_stats(self, parent: dict[str, Any], children: list[dict[str, Any]]) -> dict[str, Any]:
        child_sum = round(sum(child["inclusive_duration_seconds"] for child in children), 6)
        union = self._interval_union_duration(children, parent=parent)
        sibling_overlap = max(child_sum - union, 0.0)
        duplicate_overlap = self._duplicate_overlap(children)
        return {
            "child_duration_sum": child_sum,
            "child_interval_union_duration": round(union, 6),
            "sibling_overlap_duration": round(sibling_overlap, 6),
            "parallel_overlap_duration": round(sibling_overlap, 6),
            "duplicate_overlap_duration": round(duplicate_overlap, 6),
        }

    def _resource_rows(
        self,
        nodes: list[dict[str, Any]],
        root_id: str,
        active_compute_time: float | None,
    ) -> tuple[list[dict[str, Any]], float]:
        candidates = [
            node for node in nodes
            if node["timing_id"] != root_id
            and node.get("resource_exclusive_duration_seconds", node["exclusive_duration_seconds"]) > EPSILON
        ]
        filtered_candidates = []
        seen_resource_intervals: set[tuple[str, float, str, str]] = set()
        for node in sorted(candidates, key=lambda item: (-item["exclusive_duration_seconds"], item["stage_name"], item["timing_id"])):
            duplicate_key = self._resource_duplicate_key(node)
            if duplicate_key in seen_resource_intervals:
                continue
            seen_resource_intervals.add(duplicate_key)
            filtered_candidates.append(node)
        fallback_denominator = round(
            sum(
                node.get("resource_exclusive_duration_seconds", node["exclusive_duration_seconds"])
                for node in filtered_candidates
            ),
            6,
        )
        denominator = fallback_denominator
        if denominator <= EPSILON:
            denominator = self._number(active_compute_time, 0.0)
        rows = []
        for node in filtered_candidates:
            rows.append({
                "rank": len(rows) + 1,
                "stage_name": node["stage_name"],
                "timing_id": node["timing_id"],
                "exclusive_duration": round(
                    node.get("resource_exclusive_duration_seconds", node["exclusive_duration_seconds"]),
                    6,
                ),
                "percentage_of_active_compute": round(
                    (
                        node.get("resource_exclusive_duration_seconds", node["exclusive_duration_seconds"])
                        / max(denominator, EPSILON)
                    ) * 100.0,
                    6,
                ),
                "percentage_denominator": "ACTIVE_COMPUTE_TIME",
                "relationship_type": node["relationship_type"],
            })
        return rows, round(denominator, 6)

    def _apply_sibling_resource_overlap_adjustments(
        self,
        nodes: list[dict[str, Any]],
        child_map: dict[str, list[str]],
        by_id: dict[str, dict[str, Any]],
    ) -> None:
        for parent_id, child_ids in child_map.items():
            children = [by_id[child_id] for child_id in child_ids]
            task_children = [
                child for child in children
                if self._is_per_task_execution(child)
            ]
            if not task_children:
                continue
            task_union = self._interval_union_duration(task_children)
            if task_union <= EPSILON:
                continue
            for child in children:
                if not self._is_reasoning_node(child):
                    continue
                overlap = self._overlap_with_nodes(child, task_children)
                if overlap <= EPSILON:
                    continue
                resource_exclusive = max(
                    child["exclusive_duration_seconds"] - overlap,
                    0.0,
                )
                child["reasoning_task_overlap_duration"] = round(overlap, 6)
                child["reasoning_resource_adjustment"] = (
                    "overlap_with_per_task_execution_removed_from_resource_ranking"
                )
                child["resource_exclusive_duration_seconds"] = round(
                    resource_exclusive,
                    6,
                )
                child["relationship_type"] = "OVERLAPPING"

    def _is_task_child(self, node: Mapping[str, Any]) -> bool:
        scope = str(node.get("timing_scope") or "").upper()
        stage_name = str(node.get("stage_name") or "")
        if scope in TASK_CHILD_HINTS:
            return True
        if scope.startswith(TASK_CHILD_PREFIXES):
            return True
        return stage_name.lower().startswith("task execution:")

    def _is_per_task_execution(self, node: Mapping[str, Any]) -> bool:
        scope = str(node.get("timing_scope") or "").upper()
        stage_name = str(node.get("stage_name") or "")
        if scope == "TASK_EXECUTION_TIME":
            return False
        return scope.startswith(TASK_CHILD_PREFIXES) or stage_name.lower().startswith("task execution:")

    def _is_reasoning_node(self, node: Mapping[str, Any]) -> bool:
        scope = str(node.get("timing_scope") or "").upper()
        stage_name = str(node.get("stage_name") or "").strip().lower()
        return scope in {"REASONING", "REASONING_TIME"} or stage_name == "reasoning"

    def _resource_duplicate_key(self, node: Mapping[str, Any]) -> tuple[str, float, str, str]:
        stage_name = str(node.get("stage_name") or "").strip().lower()
        scope = str(node.get("timing_scope") or "").strip().upper()
        semantic = scope
        if stage_name in {"context", "assemble final context"} or scope in {
            "CONTEXT",
            "CONTEXT_TIME",
            "ASSEMBLE_FINAL_CONTEXT",
            "ASSEMBLE_FINAL_CONTEXT_TIME",
        }:
            semantic = "CONTEXT_ASSEMBLY"
        return (
            semantic,
            round(float(node.get("exclusive_duration_seconds") or 0.0), 6),
            str(node.get("start_timestamp") or ""),
            str(node.get("end_timestamp") or ""),
        )

    def _hierarchy_rows(
        self,
        nodes: list[dict[str, Any]],
        child_map: dict[str, list[str]],
        root_id: str,
    ) -> list[dict[str, Any]]:
        by_id = {node["timing_id"]: node for node in nodes}
        rows: list[dict[str, Any]] = []

        def visit(timing_id: str, depth: int) -> None:
            node = by_id[timing_id]
            rows.append({
                "timing_id": node["timing_id"],
                "stage_name": node["stage_name"],
                "parent_timing_id": node.get("parent_timing_id"),
                "execution_id": node["execution_id"],
                "inclusive_duration": node["inclusive_duration_seconds"],
                "exclusive_duration": node["exclusive_duration_seconds"],
                "resource_exclusive_duration": node.get(
                    "resource_exclusive_duration_seconds",
                    node["exclusive_duration_seconds"],
                ),
                "duration_seconds": node["inclusive_duration_seconds"],
                "relationship_type": node["relationship_type"],
                "timing_scope": node["timing_scope"],
                "measurement_source": node["measurement_source"],
                "validation_status": node["validation_status"],
                "depth": depth,
                "child_duration_sum": node.get("child_duration_sum", 0.0),
                "child_interval_union_duration": node.get("child_interval_union_duration", 0.0),
                "parallel_overlap_duration": node.get("parallel_overlap_duration", 0.0),
                "duplicate_overlap_duration": node.get("duplicate_overlap_duration", 0.0),
                "reasoning_task_overlap_duration": node.get("reasoning_task_overlap_duration", 0.0),
                "reasoning_resource_adjustment": node.get("reasoning_resource_adjustment"),
                "canonical_timing_source": node["canonical_timing_source"],
                "alternate_timing_sources": node["alternate_timing_sources"],
                "source_consistency": node["source_consistency"],
            })
            children = sorted(
                child_map.get(timing_id, []),
                key=lambda child_id: (
                    by_id[child_id].get("start_timestamp") or "",
                    by_id[child_id]["stage_name"],
                    child_id,
                ),
            )
            for child_id in children:
                visit(child_id, depth + 1)

        visit(root_id, 0)
        return rows

    def _record_from_stage_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        raw = dict(row.get("raw") or {})
        raw.setdefault("timing_id", row.get("timing_id"))
        raw.setdefault("execution_id", row.get("execution_id"))
        raw.setdefault("timing_name", row.get("stage_name"))
        scope = row.get("timing_scope")
        if scope in {"RUNTIME_STAGE", "PER_RUNTIME_TIMING", "RUNTIME_BREAKDOWN", "TIMING_RECORD"}:
            scope = row.get("stage_name") or scope
        raw.setdefault("timing_scope", scope)
        raw.setdefault("wall_duration_seconds", row.get("duration_seconds"))
        raw.setdefault("inclusive_duration_seconds", row.get("inclusive_duration") or row.get("duration_seconds"))
        raw.setdefault("exclusive_duration_seconds", row.get("exclusive_duration") or row.get("duration_seconds"))
        raw.setdefault("parent_timing_id", row.get("parent_timing_id"))
        raw["measurement_source"] = row.get("measurement_source") or raw.get("measurement_source")
        raw.setdefault("validation_status", row.get("timing_status") or "VALID")
        return raw

    def _child_map(self, nodes: list[dict[str, Any]]) -> dict[str, list[str]]:
        child_map: dict[str, list[str]] = {}
        ids = {node["timing_id"] for node in nodes}
        for node in nodes:
            parent = node.get("parent_timing_id")
            if parent and parent in ids:
                child_map.setdefault(parent, []).append(node["timing_id"])
        return child_map

    def _interval_union_duration(
        self,
        nodes: Iterable[Mapping[str, Any]],
        *,
        parent: Mapping[str, Any] | None = None,
    ) -> float:
        intervals = []
        fallback = 0.0
        for node in nodes:
            start = self._parse_time(node.get("start_timestamp") or node.get("execution_start"))
            end = self._parse_time(node.get("end_timestamp") or node.get("execution_end"))
            duration = self._duration(node)
            if parent:
                p_start = self._parse_time(parent.get("start_timestamp"))
                p_end = self._parse_time(parent.get("end_timestamp"))
                if start is not None and p_start is not None:
                    start = max(start, p_start)
                if end is not None and p_end is not None:
                    end = min(end, p_end)
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

    def _overlap_with_nodes(
        self,
        node: Mapping[str, Any],
        others: Iterable[Mapping[str, Any]],
    ) -> float:
        node_interval = self._interval(node)
        if not node_interval:
            return 0.0
        intervals = []
        for other in others:
            other_interval = self._interval(other)
            if not other_interval:
                continue
            start = max(node_interval[0], other_interval[0])
            end = min(node_interval[1], other_interval[1])
            if end > start:
                intervals.append((start, end))
        intervals.sort()
        merged: list[tuple[float, float]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        return round(sum(end - start for start, end in merged), 6)

    def _duplicate_overlap(self, nodes: list[dict[str, Any]]) -> float:
        total = 0.0
        for index, node in enumerate(nodes):
            for other in nodes[index + 1:]:
                if node["stage_name"] != other["stage_name"]:
                    continue
                first = self._interval(node)
                second = self._interval(other)
                if first and second:
                    total += max(min(first[1], second[1]) - max(first[0], second[0]), 0.0)
        return round(total, 6)

    def _outside_parent(self, node: Mapping[str, Any], parent: Mapping[str, Any]) -> bool:
        child = self._interval(node)
        boundary = self._interval(parent)
        if not child or not boundary:
            return False
        return child[0] < boundary[0] - EPSILON or child[1] > boundary[1] + EPSILON

    def _interval(self, node: Mapping[str, Any]) -> tuple[float, float] | None:
        start = self._parse_time(node.get("start_timestamp") or node.get("execution_start"))
        end = self._parse_time(node.get("end_timestamp") or node.get("execution_end"))
        if start is None or end is None or end <= start:
            return None
        return start, end

    def _source_rank(self, record: Mapping[str, Any]) -> tuple[int, str]:
        source = self._source(record)
        return SOURCE_PRIORITY.get(source, SOURCE_PRIORITY.get(str(record.get("timing_scope")), 9)), source

    def _source_consistency(self, selected: Mapping[str, Any], alternatives: list[Mapping[str, Any]]) -> str:
        duration = self._duration(selected)
        for alternative in alternatives:
            if abs(self._duration(alternative) - duration) > 0.001:
                return "CONFLICTING_DURATION"
        return "CONSISTENT"

    def _semantic_scope(self, record: Mapping[str, Any]) -> str:
        scope = str(record.get("timing_scope") or record.get("scope") or record.get("timing_name") or "").upper()
        scope = scope.replace(" ", "_")
        if scope in {"RUNTIME_STAGE", "PER_RUNTIME_TIMING", "RUNTIME_BREAKDOWN", "TIMING_RECORD"}:
            scope = str(record.get("stage_name") or record.get("timing_name") or scope).upper().replace(" ", "_")
        if scope in {"COGNITIVE_RUNTIME_TIME", "TASK_EXECUTION"}:
            return "TASK_EXECUTION_TIME"
        if scope == "REPORT_TIME":
            return "REPORT_GENERATION_TIME"
        return scope or "TIMING_STAGE"

    def _stage_name(self, record: Mapping[str, Any], scope: str) -> str:
        raw = str(record.get("stage_name") or record.get("timing_name") or scope)
        labels = {
            "TOTAL_WALL_TIME": "Total Wall Time",
            "TASK_EXECUTION_TIME": "Task Execution",
            "CHILD_RUNTIME_TIME": "Task Execution",
            "CONTEXT_TIME": "Context",
            "CONTEXT": "Context",
            "REASONING_TIME": "Reasoning",
            "REASONING": "Reasoning",
            "SEARCH_TIME": "Search",
            "SEARCH": "Search",
            "REPORT_GENERATION_TIME": "Final Report Rendering",
        }
        normalized_raw = raw.upper().replace(" ", "_")
        if normalized_raw in labels:
            return labels[normalized_raw]
        if raw and raw != scope:
            return raw.replace("_", " ").title()
        return labels.get(scope, scope.removesuffix("_TIME").replace("_", " ").title())

    def _duration(self, record: Mapping[str, Any]) -> float:
        return max(
            self._number(record.get("inclusive_duration_seconds"), -1.0),
            self._number(record.get("wall_duration_seconds"), -1.0),
            self._number(record.get("duration_seconds"), -1.0),
            self._number(record.get("seconds"), -1.0),
            self._number(record.get("total_duration"), -1.0),
            0.0,
        )

    def _source(self, record: Mapping[str, Any]) -> str:
        return str(
            record.get("measurement_source")
            or record.get("canonical_timing_source")
            or record.get("timing_scope")
            or "UNKNOWN_SOURCE"
        )

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


hierarchical_timing_reconciliation_engine = HierarchicalTimingReconciliationEngine()


__all__ = [
    "HierarchicalTimingReconciliationEngine",
    "hierarchical_timing_reconciliation_engine",
]
