from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from runtime.reporting.output_governor import (
    ADVANCED_REPORT_LEVELS,
    HISTORICAL_ARCHIVE_KEYS,
    output_governor,
)


MAX_TASKS_DISPLAYED = 3
MAX_HISTORY_DISPLAYED = 3
MAX_SOURCES_DISPLAYED = 10
MAX_DEPENDENCIES_DISPLAYED = 10
MAX_FULL_ENTRIES_DISPLAYED = 20


class CompactReportBuilder:
    HEAVY_KEYS = {
        "predicted_grid",
        "input_grid",
        "output_grid",
        "simulation",
        "simulation_trace",
        "graph_reasoning",
        "object_tracker",
        "dependency_evidence",
        "localization_reports",
        "OBJECT_MOTION_REPORT",
        "object_motion_report",
        "LOCALIZATION_REPORT",
        "runtime_context",
        "final_context",
        "pipeline_context",
        "nested_runtime_context",
        "raw_runtime_context",
        "full_runtime_context",
        "full_task_file_lists",
        "task_file_lists",
        "full_dependency_graph",
        "dependency_graph",
        "full_explanation_paths",
        "explanation_paths",
        "explanation_path",
        "full_context_registry",
        "context_registry",
        "typed_dependency_relations",
        "dependency_paths",
        "task_lists",
        "counterfactual_candidates",
    }
    HISTORICAL_LIST_KEYS = {
        *HISTORICAL_ARCHIVE_KEYS,
        "observed_tasks",
        "task_sources",
        "training_files",
        "evidence_sources",
        "source_files",
        "task_history",
        "historical_tasks",
        "concept_sources",
        "dependency_sources",
        "memory_sources",
        "training_examples",
        "observed_task_history",
        "concept_file_history",
        "dependency_source_files",
        "memory_source_tasks",
        "historical_task_lists",
        "task_ids",
        "tasks_executed",
        "discovered_task_files",
        "selected_task_files",
        "process_dependency_evidence_sources",
        "dependency_telemetry_report",
        "boundary_refinement_dependency_debug",
    }
    TASK_KEYS = {
        "observed_tasks",
        "task_sources",
        "task_history",
        "historical_tasks",
        "observed_task_history",
        "memory_source_tasks",
        "historical_task_lists",
        "task_ids",
        "tasks_executed",
        "discovered_task_files",
        "selected_task_files",
    }
    SOURCE_KEYS = {
        "training_files",
        "evidence_sources",
        "source_files",
        "concept_sources",
        "dependency_sources",
        "memory_sources",
        "concept_file_history",
        "dependency_source_files",
        "process_dependency_evidence_sources",
    }
    DEPENDENCY_KEYS = {
        "dependency_sources",
        "dependency_source_files",
        "dependency_telemetry_report",
        "boundary_refinement_dependency_debug",
    }
    REPEATED_REPORT_KEYS = {
        "ARBITRATION_REPORT",
        "arbitration_report",
    }
    ESSENTIAL_KEYS = {
        "success",
        "exact_success",
        "episode_completed",
        "final_score",
        "score",
        "accuracy",
        "prediction_accuracy",
        "winning_primitive",
        "primitive",
        "selected_primitive",
        "execution_time",
        "total_runtime_seconds",
        "cache_hits",
        "cache_misses",
        "cache_hit_rate",
        "slowest_modules",
        "top_bottlenecks",
        "performance_report",
        "EXECUTION_PLAN_REPORT",
        "execution_plan_report",
        "EXECUTION_DISPATCH_REPORT",
        "execution_dispatch_report",
        "EXECUTION_LAYER_AUDIT_REPORT",
        "execution_layer_audit_report",
        "evaluation_result",
        "answer",
        "shutdown_mode",
        "governance_budget_seconds",
        "governance_budget_exceeded",
        "governance_deferred",
        "recommended_next_step",
        "finalization_duration",
        "startup_hang_prevented",
    }

    def __init__(self):
        self.compact_reports_generated = 0
        self.heavy_keys_removed = 0
        self.arrays_summarized = 0
        self.repeated_reports_collapsed = 0
        self.final_context_size_estimate_before = 0
        self.final_context_size_estimate_after = 0

    def compact_context(
        self,
        context: dict,
        level: str = "normal",
    ) -> dict:
        level = self._level(level)
        context = context if isinstance(context, dict) else {}
        before = self._size_estimate(context)
        if level == "minimal":
            compacted = self._minimal_context(context)
        else:
            compacted = self._compact_value(
                context,
                level=level,
                depth=0,
                seen_reports=set(),
            )
        after = self._size_estimate(compacted)
        self.compact_reports_generated += 1
        self.final_context_size_estimate_before = before
        self.final_context_size_estimate_after = after
        compacted["compact_report"] = self.report()
        return compacted

    def compact_stage_report(
        self,
        report: dict,
        level: str = "normal",
    ) -> dict:
        level = self._level(level)
        return self._compact_value(
            report if isinstance(report, dict) else {},
            level=level,
            depth=0,
            seen_reports=set(),
        )

    def compact_performance_report(self, report: dict) -> dict:
        report = report if isinstance(report, dict) else {}
        return {
            "system": report.get("system", "performance_report"),
            "report_state": report.get("report_state", "final"),
            "status": report.get("status", "ok"),
            "execution_time": report.get(
                "execution_time",
                report.get("total_runtime_seconds"),
            ),
            "total_runtime_seconds": report.get("total_runtime_seconds"),
            "concepts_processed": report.get("concepts_processed"),
            "semantic_concept_count": report.get(
                "semantic_concept_count",
            ),
            "context_count": report.get("context_count"),
            "cache_hits": report.get("cache_hits"),
            "cache_misses": report.get("cache_misses"),
            "cache_hit_rate": report.get("cache_hit_rate"),
            "reuse_rate": report.get("reuse_rate"),
            "strategy_reuse_rate": report.get("strategy_reuse_rate"),
            "strategy_hits": report.get("strategy_hits"),
            "context_hits": report.get("context_hits"),
            "program_hits": report.get("program_hits"),
            "truth_hits": report.get("truth_hits"),
            "context_lookup_count": report.get("context_lookup_count"),
            "context_reuse_attempts": report.get("context_reuse_attempts"),
            "context_reuse_successes": report.get("context_reuse_successes"),
            "dependency_chains_executed": report.get(
                "dependency_chains_executed",
            ),
            "dependency_chain_depth": report.get(
                "dependency_chain_depth",
            ),
            "dependency_chain_coverage": report.get(
                "dependency_chain_coverage",
            ),
            "active_compute_time_seconds": report.get(
                "active_compute_time_seconds",
            ),
            "unattributed_runtime_seconds": report.get(
                "unattributed_runtime_seconds",
            ),
            "untracked_runtime_seconds": report.get(
                "untracked_runtime_seconds",
            ),
            "attributed_runtime_seconds": report.get(
                "attributed_runtime_seconds",
            ),
            "runtime_breakdown": report.get("runtime_breakdown"),
            "runtime_attribution_report": self._compact_value(
                report.get("runtime_attribution_report", {}),
                level="minimal",
                depth=0,
                seen_reports=set(),
            ),
            "governance_skip_count": report.get("governance_skip_count"),
            "dependency_snapshot_hits": report.get(
                "dependency_snapshot_hits",
            ),
            "dependency_executor_cache_hits": report.get(
                "dependency_executor_cache_hits",
            ),
            "dependency_executor_cache_misses": report.get(
                "dependency_executor_cache_misses",
            ),
            "dependency_reasoning_skipped": report.get(
                "dependency_reasoning_skipped",
            ),
            "dependency_activation_reason": report.get(
                "dependency_activation_reason",
            ),
            "dependency_skip_reason": report.get("dependency_skip_reason"),
            "dependency_usage_rate": report.get("dependency_usage_rate"),
            "concept_lifecycle_cost": report.get("concept_lifecycle_cost"),
            "concept_lifecycle_cache_hits": report.get(
                "concept_lifecycle_cache_hits",
            ),
            "report_generation_cost": report.get("report_generation_cost"),
            "report_compression_ratio": report.get("report_compression_ratio"),
            "report_budget_usage": report.get("report_budget_usage"),
            "pre_reasoning_router_enabled": report.get(
                "pre_reasoning_router_enabled",
            ),
            "task_profiles_generated": report.get(
                "task_profiles_generated",
            ),
            "selective_execution_enabled": report.get(
                "selective_execution_enabled",
            ),
            "layers_enabled_count": report.get("layers_enabled_count"),
            "layers_disabled_count": report.get("layers_disabled_count"),
            "layers_deferred_count": report.get("layers_deferred_count"),
            "full_stack_avoided": report.get("full_stack_avoided"),
            "estimated_layers_skipped": report.get(
                "estimated_layers_skipped",
            ),
            "estimated_runtime_saved": report.get(
                "estimated_runtime_saved",
            ),
            "estimated_compute_saved": report.get(
                "estimated_compute_saved",
            ),
            "skipped_reports_count": report.get("skipped_reports_count"),
            "premature_reports_prevented": report.get(
                "premature_reports_prevented",
            ),
            "compact_reports_generated": report.get(
                "compact_reports_generated",
            ),
            "heavy_keys_removed": report.get("heavy_keys_removed"),
            "arrays_summarized": report.get("arrays_summarized"),
            "repeated_reports_collapsed": report.get(
                "repeated_reports_collapsed",
            ),
            "final_context_size_estimate_before": report.get(
                "final_context_size_estimate_before",
            ),
            "final_context_size_estimate_after": report.get(
                "final_context_size_estimate_after",
            ),
            "slowest_modules": self._limit_list(
                report.get("slowest_modules", []),
                5,
            ),
            "module_timing_count": self._count_items(
                report.get("module_timings", []),
            ),
            "recent_module_timings": self._recent_items(
                report.get("module_timings", []),
                MAX_HISTORY_DISPLAYED,
            ),
            "metric_source_warnings": self._limit_list(
                report.get("metric_source_warnings", []),
                5,
            ),
            "canonical_metrics": self._compact_value(
                report.get("canonical_metrics", {}),
                level="normal",
                depth=0,
                seen_reports=set(),
            ),
            "METRIC_RECONCILIATION_REPORT": self._compact_value(
                report.get("METRIC_RECONCILIATION_REPORT", {}),
                level="normal",
                depth=0,
                seen_reports=set(),
            ),
            "METRIC_RECONCILIATION_WARNING": report.get(
                "METRIC_RECONCILIATION_WARNING",
            ),
            "DEEP_MODE_OPTIMIZATION_REPORT": self._compact_value(
                report.get("DEEP_MODE_OPTIMIZATION_REPORT", {}),
                level="normal",
                depth=0,
                seen_reports=set(),
            ),
        }

    def compact_concept_lifecycle_report(
        self,
        report: dict,
        report_budget_seconds: float | None = None,
        elapsed_seconds: float | None = None,
    ) -> dict:
        report = report if isinstance(report, dict) else {}

        def compact_concept(concept):
            promotion = concept.get("truth_candidate_promotion", {})
            promotion = promotion if isinstance(promotion, dict) else {}
            concept_name = concept.get("concept") or concept.get("concept_name")
            history_count = sum(
                self._count_items(concept.get(key))
                for key in self.HISTORICAL_LIST_KEYS
                if key in concept
            )
            return {
                "concept_name": concept_name,
                "current_stage": concept.get(
                    "current_stage",
                    concept.get(
                        "promotion_stage",
                        concept.get("state", concept.get("lifecycle_state")),
                    ),
                ),
                "confidence": concept.get(
                    "confidence",
                    concept.get("independent_success_rate", 0.0),
                ),
                "support_score": concept.get(
                    "support_score",
                    concept.get("independent_success_rate", 0.0),
                ),
                "contradiction_score": concept.get(
                    "contradiction_score",
                    concept.get(
                        "average_contradiction_score",
                        concept.get("ledger_average_contradiction_score", 0.0),
                    ),
                ),
                "promotion_score": concept.get("promotion_score"),
                "observation_count": concept.get(
                    "observation_count",
                    concept.get("used_task_count", 0),
                ),
                "candidate_ready": concept.get("candidate_ready"),
                "last_updated": concept.get("last_updated"),
                "state": concept.get("state", concept.get("lifecycle_state")),
                "history_count": history_count,
                "promotion_dependency_score":
                promotion.get("promotion_dependency_score"),
                "dependency_confidence": promotion.get("dependency_confidence"),
                "dependency_chain_depth":
                promotion.get("dependency_chain_depth"),
                "dependency_chain_coverage":
                promotion.get("dependency_chain_coverage"),
                "dependency_promotion_blockers": list(
                    promotion.get("dependency_promotion_blockers", [])
                ),
                "context_strength": promotion.get("context_strength"),
                "context_consumed": promotion.get("context_consumed", 0),
            }

        compact = {
            "system": report.get("system", "concept_maturity_tracker"),
            "report_state": report.get("report_state", "final"),
            "status": report.get("status", "ok"),
            "states": list(report.get("states", [])),
            "concepts": [
                compact_concept(concept)
                for concept in report.get("concepts", [])
                if isinstance(concept, dict)
            ],
            "promotion_report": self._limit_list(
                report.get("promotion_report", []),
                MAX_FULL_ENTRIES_DISPLAYED,
            ),
            "context_count": report.get("context_count", 0),
            "context_consumed": report.get("context_consumed", 0),
            "context_hits": report.get("context_hits", 0),
            "truth_candidate_count": report.get("truth_candidate_count", 0),
            "strategy_hits": report.get("strategy_hits", 0),
            "program_hits": report.get("program_hits", 0),
            "truth_hits": report.get("truth_hits", 0),
            "knowledge_reuse_rate": report.get("knowledge_reuse_rate", 0.0),
            "state_counts": dict(report.get("state_counts", {})),
            "closest_truth_candidate_concepts": self._limit_list(
                report.get("closest_truth_candidate_concepts", []),
                MAX_FULL_ENTRIES_DISPLAYED,
            ),
            "candidate_ready_lifecycle_invariant_preserved":
            report.get("candidate_ready_lifecycle_invariant_preserved"),
            "count_alone_cannot_promote_truth":
            report.get("count_alone_cannot_promote_truth"),
            "concept_lifecycle_compressed": True,
            "report_level": "compact",
        }
        if report_budget_seconds is not None:
            compact["report_budget_seconds"] = report_budget_seconds
        if elapsed_seconds is not None:
            compact["report_elapsed_seconds"] = elapsed_seconds
        if (
            report_budget_seconds is not None
            and elapsed_seconds is not None
            and elapsed_seconds > report_budget_seconds
        ):
            compact["report_budget_exceeded"] = True
            compact["report_truncated_reason"] = "concept_lifecycle_report_budget"
        return compact

    def compact_governance_report(self, report: dict) -> dict:
        report = report if isinstance(report, dict) else {}
        return {
            "status": report.get("status"),
            "truth_validation_mode": report.get("truth_validation_mode"),
            "skipped_governance": report.get("skipped_governance"),
            "reason": report.get("reason"),
            "reused_concepts": self._limit_list(
                report.get("reused_concepts", []),
                10,
            ),
            "validation_skipped": self._limit_list(
                report.get("validation_skipped", []),
                10,
            ),
        }

    def purge_heavy_objects(self, context: dict) -> dict:
        context = deepcopy(context if isinstance(context, dict) else {})
        purged = self._purge_value(context)
        performance = purged.get("performance_report")
        if isinstance(performance, dict):
            purged["performance_report"] = self.compact_performance_report(
                performance,
            )
        return purged

    def report(self) -> dict:
        return {
            "system": "compact_report_builder",
            "report_state": "final",
            "status": "ok",
            "compact_reports_generated": self.compact_reports_generated,
            "heavy_keys_removed": self.heavy_keys_removed,
            "arrays_summarized": self.arrays_summarized,
            "repeated_reports_collapsed": self.repeated_reports_collapsed,
            "final_context_size_estimate_before":
            self.final_context_size_estimate_before,
            "final_context_size_estimate_after":
            self.final_context_size_estimate_after,
        }

    def _minimal_context(self, context):
        compact = {}
        for key in self.ESSENTIAL_KEYS:
            if key not in context:
                continue
            value = context[key]
            if key == "performance_report" and isinstance(value, dict):
                compact[key] = self.compact_performance_report(value)
            elif key in {
                "EXECUTION_PLAN_REPORT",
                "execution_plan_report",
                "EXECUTION_DISPATCH_REPORT",
                "execution_dispatch_report",
            } and isinstance(value, dict):
                compact[key] = deepcopy(value)
            elif key in {
                "EXECUTION_LAYER_AUDIT_REPORT",
                "execution_layer_audit_report",
            } and isinstance(value, dict):
                compact[key] = deepcopy(value)
            elif key == "evaluation_result" and isinstance(value, dict):
                compact[key] = {
                    item: value.get(item)
                    for item in [
                        "success",
                        "exact_success",
                        "episode_completed",
                        "accuracy",
                        "score",
                        "final_score",
                        "prediction_accuracy",
                        "winning_primitive",
                        "primitive",
                        "shutdown_mode",
                    ]
                    if item in value
                }
            else:
                compact[key] = self._compact_value(
                    value,
                    level="minimal",
                    depth=0,
                    seen_reports=set(),
                )
        for key in [
            "transformation_report",
            "execution_result",
            "prediction_report",
            "governance_report",
            "LOCALIZATION_REPORT",
            "OBJECT_MOTION_REPORT",
        ]:
            if key in context and isinstance(context[key], dict):
                if key in self.HEAVY_KEYS:
                    self.heavy_keys_removed += 1
                    compact[f"{key}_summary"] = (
                        self._extract_summary(context[key])
                        or self._structure_summary(context[key])
                    )
                else:
                    compact[key] = self._extract_summary(context[key])
        return compact

    def _compact_value(self, value, level, depth, seen_reports):
        max_depth = 3 if level == "minimal" else 5
        max_list_items = {
            "minimal": MAX_HISTORY_DISPLAYED,
            "normal": 10,
            "full": MAX_FULL_ENTRIES_DISPLAYED,
            "debug": MAX_FULL_ENTRIES_DISPLAYED,
            "audit": MAX_FULL_ENTRIES_DISPLAYED,
        }[level]
        if self._is_array_like(value):
            self.arrays_summarized += 1
            return self._array_summary(value)
        if depth >= max_depth:
            return self._depth_summary(value)
        if isinstance(value, dict):
            compact = {}
            for key, item in value.items():
                if key == "counterfactual_candidates":
                    self.heavy_keys_removed += 1
                    compact[f"{key}_summary"] = (
                        self._counterfactual_candidates_summary(item)
                    )
                    continue
                if key in {
                    "EXECUTION_PLAN_REPORT",
                    "execution_plan_report",
                    "EXECUTION_DISPATCH_REPORT",
                    "execution_dispatch_report",
                } and isinstance(item, dict):
                    compact[key] = deepcopy(item)
                    continue
                if key in {
                    "EXECUTION_LAYER_AUDIT_REPORT",
                    "execution_layer_audit_report",
                } and isinstance(item, dict):
                    compact[key] = deepcopy(item)
                    continue
                if key in self.HISTORICAL_LIST_KEYS:
                    compact.update(self._historical_summary(key, item, level))
                    continue
                if key in self.HEAVY_KEYS:
                    self.heavy_keys_removed += 1
                    summary = self._extract_summary(item)
                    compact[f"{key}_summary"] = (
                        summary or self._structure_summary(item)
                    )
                    continue
                if key in self.REPEATED_REPORT_KEYS:
                    signature = self._report_signature(item)
                    if signature in seen_reports:
                        self.repeated_reports_collapsed += 1
                        compact[key] = {"collapsed_duplicate_report": True}
                        continue
                    seen_reports.add(signature)
                if key == "performance_report" and isinstance(item, dict):
                    compact[key] = self.compact_performance_report(item)
                    continue
                if key in {"governance_report", "governance_cache_report"}:
                    compact[key] = self.compact_governance_report(item)
                    continue
                compact[key] = self._compact_value(
                    item,
                    level,
                    depth + 1,
                    seen_reports,
                )
            return compact
        if isinstance(value, (list, tuple, set)):
            items = list(value)
            compact = [
                self._compact_value(item, level, depth + 1, seen_reports)
                for item in items[:max_list_items]
            ]
            if len(items) > max_list_items:
                compact.append({
                    "truncated": True,
                    "remaining_items": len(items) - max_list_items,
                })
            return compact
        return value

    def _purge_value(self, value):
        if isinstance(value, dict):
            purged = {}
            for key, item in value.items():
                if key == "counterfactual_candidates":
                    self.heavy_keys_removed += 1
                    purged[f"{key}_summary"] = (
                        self._counterfactual_candidates_summary(item)
                    )
                    continue
                if key in self.HEAVY_KEYS:
                    self.heavy_keys_removed += 1
                    summary = self._extract_summary(item)
                    purged[f"{key}_summary"] = (
                        summary or self._structure_summary(item)
                    )
                    continue
                if key in self.HISTORICAL_LIST_KEYS:
                    purged.update(self._historical_summary(key, item, "normal"))
                    continue
                purged[key] = self._purge_value(item)
            return purged
        if isinstance(value, list):
            return [self._purge_value(item) for item in value]
        if self._is_array_like(value):
            self.arrays_summarized += 1
            return self._array_summary(value)
        return value

    def _extract_summary(self, value):
        if not isinstance(value, dict):
            if isinstance(value, list):
                if self._looks_like_grid(value):
                    return self._grid_summary(value)
                return {"item_count": len(value)}
            return {}
        summary = {}
        for key in [
            "prediction_accuracy",
            "success",
            "exact_success",
            "winning_primitive",
            "primitive",
            "dependency_evidence_count",
            "localization_ready",
            "execution_ready",
            "confidence",
            "score",
            "status",
            "reason",
        ]:
            if key in value:
                summary[key] = value[key]
        if "dependency_evidence" in value and "dependency_evidence_count" not in summary:
            evidence = value.get("dependency_evidence")
            if isinstance(evidence, list):
                summary["dependency_evidence_count"] = len(evidence)
        return summary

    def _structure_summary(self, value):
        if self._is_array_like(value):
            return self._array_summary(value)
        if isinstance(value, dict):
            return {
                "summary": "heavy_runtime_object_summarized",
                "type": "dict",
                "key_count": len(value),
                "keys": list(value.keys())[:5],
            }
        if isinstance(value, list):
            if self._looks_like_grid(value):
                return self._grid_summary(value)
            return {
                "summary": "heavy_runtime_object_summarized",
                "type": "list",
                "item_count": len(value),
            }
        return {
            "summary": "heavy_runtime_object_summarized",
            "type": type(value).__name__,
        }

    def _looks_like_grid(self, value):
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(row, list) for row in value[:20])
        )

    def _grid_summary(self, value):
        rows = len(value)
        columns = max(
            [len(row) for row in value if isinstance(row, list)]
            or [0]
        )
        return {
            "summary": "grid_summarized",
            "rows": rows,
            "columns": columns,
            "cell_count": sum(
                len(row)
                for row in value
                if isinstance(row, list)
            ),
        }

    def _counterfactual_candidates_summary(self, value):
        candidates = list(value or []) if isinstance(value, list) else []
        best = None
        best_accuracy = None
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            accuracy = self._candidate_accuracy(candidate)
            if best_accuracy is None or accuracy > best_accuracy:
                best_accuracy = accuracy
                best = candidate
        summary = {"candidate_count": len(candidates)}
        if best is not None:
            summary.update({
                "best_accuracy": best_accuracy,
                "best_direction": self._first_present(
                    best,
                    "direction",
                    "placement_direction",
                    "movement_direction",
                ),
                "best_operation": self._first_present(
                    best,
                    "operation",
                    "primitive",
                    "winning_primitive",
                ),
                "best_confidence": self._first_present(
                    best,
                    "confidence",
                    "score",
                    "arbitration_score",
                ),
            })
            summary = {
                key: value
                for key, value in summary.items()
                if value is not None
            }
        return summary

    def _candidate_accuracy(self, candidate):
        for key in [
            "accuracy",
            "prediction_accuracy",
            "score",
            "confidence",
        ]:
            value = candidate.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        prediction = candidate.get("prediction_report")
        if isinstance(prediction, dict):
            value = prediction.get("prediction_accuracy")
            if isinstance(value, (int, float)):
                return float(value)
        return 0.0

    def _first_present(self, source, *keys):
        for key in keys:
            if key in source:
                return source[key]
        return None

    def _is_array_like(self, value):
        return (
            hasattr(value, "shape")
            and hasattr(value, "dtype")
            and hasattr(value, "tolist")
        )

    def _array_summary(self, value):
        return {
            "array_summary": True,
            "shape": list(getattr(value, "shape", [])),
            "dtype": str(getattr(value, "dtype", "unknown")),
        }

    def _depth_summary(self, value):
        if isinstance(value, dict):
            return {
                "summary": "max_depth_reached",
                "type": "dict",
                "key_count": len(value),
            }
        if isinstance(value, list):
            return {
                "summary": "max_depth_reached",
                "type": "list",
                "item_count": len(value),
            }
        return value

    def _limit_list(self, value, limit):
        if not isinstance(value, list):
            return []
        limited = value[:limit]
        if len(value) > limit:
            return [
                *limited,
                {"truncated": True, "remaining_items": len(value) - limit},
            ]
        return limited

    def _historical_summary(self, key, value, level):
        count = self._count_items(value)
        if level not in ADVANCED_REPORT_LEVELS:
            prefix, _recent_key = self._summary_names_for(key)
            return {prefix: count}
        if level == "audit":
            return {key: deepcopy(value), f"{key}_count": count}
        limit = self._historical_limit_for(key, level)
        recent = self._recent_items(value, limit)
        prefix, recent_key = self._summary_names_for(key)
        summary = {prefix: count}
        if recent:
            summary[recent_key] = self._compact_recent_values(recent)
        if count > limit:
            summary[f"{key}_truncated"] = True
        return summary

    def _summary_names_for(self, key):
        if key in {"observed_tasks", "observed_task_history"}:
            return "observation_count", "recent_tasks"
        if key in self.TASK_KEYS:
            return f"{key}_count", "recent_tasks"
        if key in self.DEPENDENCY_KEYS:
            return f"{key}_count", "recent_dependencies"
        if key in self.SOURCE_KEYS:
            return f"{key}_count", "recent_sources"
        if key == "training_examples":
            return "training_example_count", "recent_training_examples"
        return f"{key}_count", f"recent_{key}"

    def _historical_limit_for(self, key, level):
        if level == "full":
            return MAX_FULL_ENTRIES_DISPLAYED
        if key in self.DEPENDENCY_KEYS:
            return MAX_DEPENDENCIES_DISPLAYED
        if key in self.SOURCE_KEYS:
            return MAX_SOURCES_DISPLAYED
        if key in self.TASK_KEYS:
            return MAX_TASKS_DISPLAYED
        return MAX_HISTORY_DISPLAYED

    def _count_items(self, value):
        if isinstance(value, dict):
            return len(value)
        if isinstance(value, (list, tuple, set)):
            return len(value)
        if value in (None, ""):
            return 0
        return 1

    def _recent_items(self, value, limit):
        if limit <= 0:
            return []
        if isinstance(value, dict):
            items = list(value.items())[-limit:]
            return [{str(key): item} for key, item in items]
        if isinstance(value, (list, tuple, set)):
            return list(value)[-limit:]
        if value in (None, ""):
            return []
        return [value]

    def _compact_recent_values(self, values):
        compacted = []
        for value in values:
            if isinstance(value, dict):
                compacted.append(self._extract_summary(value) or {
                    "keys": list(value.keys())[:5],
                })
            else:
                compacted.append(value)
        return compacted

    def _size_estimate(self, value):
        return self._bounded_size_estimate(value, budget=50000)

    def _bounded_size_estimate(self, value, budget):
        if budget <= 0:
            return 0
        if isinstance(value, dict):
            total = 2
            for key, item in value.items():
                total += min(len(str(key)), budget - total)
                if total >= budget:
                    return budget
                total += self._bounded_size_estimate(item, budget - total)
                if total >= budget:
                    return budget
            return total
        if isinstance(value, (list, tuple, set)):
            total = 2
            for item in list(value)[:MAX_FULL_ENTRIES_DISPLAYED]:
                total += self._bounded_size_estimate(item, budget - total)
                if total >= budget:
                    return budget
            if self._count_items(value) > MAX_FULL_ENTRIES_DISPLAYED:
                total += 32
            return min(total, budget)
        return min(len(str(value)), budget)

    def _report_signature(self, value):
        try:
            return json.dumps(value, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return str(value)

    def _level(self, level):
        return output_governor.normalize_level(level)


compact_report_builder = CompactReportBuilder()


__all__ = [
    "CompactReportBuilder",
    "compact_report_builder",
]
