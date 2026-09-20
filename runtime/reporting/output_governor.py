from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any


REPORT_LEVELS = ("minimal", "normal", "full", "debug", "audit")
ADVANCED_REPORT_LEVELS = {"full", "debug", "audit"}
REPORT_STATES = {"pending", "running", "partial", "final", "skipped", "failed"}

DEFAULT_LIMITS = {
    "tasks": 3,
    "contexts": 3,
    "candidates": 3,
    "failures": 5,
    "warnings": 5,
}

HISTORICAL_ARCHIVE_KEYS = {
    "observed_tasks",
    "task_sources",
    "task_history",
    "training_files",
    "source_tasks",
    "observation_history",
    "observed_task_history",
    "concept_history",
    "dependency_history",
    "semantic_history",
    "trace_history",
    "lineage_history",
    "knowledge_sources",
    "evidence_sources",
    "memory_archives",
    "context_archives",
    "cache_entries",
    "historical_diagnostics",
    "historical_tasks",
    "historical_task_lists",
    "concept_sources",
    "dependency_sources",
    "dependency_source_files",
    "concept_file_history",
    "memory_source_tasks",
    "process_dependency_evidence_sources",
    "resolved_dependency_chain",
    "full_dependency_chains",
    "dependency_lineage_tree",
    "context_history",
    "truth_history",
    "promotion_traces",
    "cache_inventory",
    "cache_contents",
}

ADVANCED_SCHEMA_KEYS = {"details", "archives", "traces", "history"}


class OutputGovernor:
    """Applies the runtime reporting hierarchy before terminal output."""

    def __init__(
        self,
        max_visible_tasks: int = DEFAULT_LIMITS["tasks"],
        max_visible_contexts: int = DEFAULT_LIMITS["contexts"],
        max_visible_candidates: int = DEFAULT_LIMITS["candidates"],
        max_visible_failures: int = DEFAULT_LIMITS["failures"],
        max_visible_warnings: int = DEFAULT_LIMITS["warnings"],
    ):
        self.max_visible_tasks = max_visible_tasks
        self.max_visible_contexts = max_visible_contexts
        self.max_visible_candidates = max_visible_candidates
        self.max_visible_failures = max_visible_failures
        self.max_visible_warnings = max_visible_warnings

    def normalize_level(self, level: str | None) -> str:
        normalized = str(level or "normal").lower()
        if normalized == "summary":
            return "normal"
        if normalized not in REPORT_LEVELS:
            return "normal"
        return normalized

    def is_advanced(self, level: str | None) -> bool:
        return self.normalize_level(level) in ADVANCED_REPORT_LEVELS

    def report_state(self, state: str | None = "final") -> str:
        state = str(state or "final").lower()
        return state if state in REPORT_STATES else "final"

    def limit(self, values: Any, limit: int, *, summarize_dict: bool = False):
        if values is None:
            return []
        if isinstance(values, dict):
            items = list(values.items())
            limited = [
                {str(key): self._compact_item(value) if summarize_dict else value}
                for key, value in items[:limit]
            ]
            hidden = len(items) - limit
        else:
            items = list(values) if isinstance(values, (list, tuple, set)) else [values]
            limited = [self._compact_item(item) for item in items[:limit]]
            hidden = len(items) - limit
        if hidden > 0:
            limited.append(f"... {hidden} additional entries hidden")
        return limited

    def count(self, values: Any) -> int:
        if values is None:
            return 0
        if isinstance(values, dict):
            return len(values)
        if isinstance(values, (list, tuple, set)):
            return len(values)
        return 1

    def unified_report(
        self,
        *,
        system: str,
        status: str = "ok",
        report_state: str = "final",
        summary: dict | None = None,
        metrics: dict | None = None,
        warnings: list | None = None,
        failures: list | None = None,
        recommendations: list | None = None,
        level: str = "normal",
        details: dict | None = None,
        archives: dict | None = None,
        traces: dict | None = None,
        history: dict | None = None,
    ) -> dict:
        level = self.normalize_level(level)
        report = {
            "system": system,
            "report_state": self.report_state(report_state),
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary or {},
            "metrics": metrics or {},
            "warnings": self.limit(warnings or [], self.max_visible_warnings),
            "failures": self.limit(failures or [], self.max_visible_failures),
            "recommendations": self.limit(
                recommendations or [],
                self.max_visible_warnings,
            ),
        }
        if level in ADVANCED_REPORT_LEVELS:
            for key, value in {
                "details": details,
                "archives": archives,
                "traces": traces,
                "history": history,
            }.items():
                if value not in (None, {}, []):
                    report[key] = value
        return report

    def govern_value(self, value: Any, level: str = "normal", key: str | None = None):
        level = self.normalize_level(level)
        if key in HISTORICAL_ARCHIVE_KEYS and level not in ADVANCED_REPORT_LEVELS:
            return {f"{key}_count": self.count(value)}
        if key in ADVANCED_SCHEMA_KEYS and level not in ADVANCED_REPORT_LEVELS:
            return {f"{key}_count": self.count(value)}
        if isinstance(value, dict):
            governed = {}
            for child_key, child_value in value.items():
                governed_child = self.govern_value(
                    child_value,
                    level=level,
                    key=str(child_key),
                )
                if (
                    isinstance(governed_child, dict)
                    and set(governed_child) == {f"{child_key}_count"}
                ):
                    governed.update(governed_child)
                else:
                    governed[child_key] = governed_child
            return governed
        if isinstance(value, list):
            limit = self._limit_for_key(key)
            if level == "audit":
                return deepcopy(value)
            if level in ADVANCED_REPORT_LEVELS:
                return [self.govern_value(item, level=level) for item in value]
            return self.limit(value, limit)
        return value

    def concept_summary(self, concept_name: str, stats: dict) -> dict:
        stats = stats if isinstance(stats, dict) else {}
        history_count = sum(
            self.count(stats.get(key))
            for key in HISTORICAL_ARCHIVE_KEYS
            if key in stats
        )
        observation_count = (
            stats.get("observation_count")
            or stats.get("used_task_count")
            or self.count(stats.get("task_ids"))
            or self.count(stats.get("observed_tasks"))
        )
        contradiction_score = (
            stats.get("contradiction_score")
            or stats.get("average_contradiction_score")
            or stats.get("ledger_average_contradiction_score")
            or 0.0
        )
        support_score = (
            stats.get("support_score")
            or stats.get("independent_success_rate")
            or stats.get("confidence")
            or 0.0
        )
        return {
            "concept_name": concept_name,
            "current_stage": stats.get(
                "current_stage",
                stats.get("promotion_stage", stats.get("lifecycle_state", stats.get("state"))),
            ),
            "confidence": stats.get("confidence", support_score),
            "support_score": support_score,
            "contradiction_score": contradiction_score,
            "promotion_score": stats.get("promotion_score"),
            "observation_count": observation_count,
            "candidate_ready": stats.get(
                "candidate_ready",
                stats.get("preliminary_truth_candidate_ready", False),
            ),
            "last_updated": stats.get("last_updated") or stats.get("updated_at"),
            "state": stats.get("state", stats.get("lifecycle_state")),
            "history_count": history_count,
        }

    def runtime_dashboard(self, report: dict, level: str = "normal") -> dict:
        level = self.normalize_level(level)
        report = report if isinstance(report, dict) else {}
        task_results = report.get("multi_task_results", [])
        tasks_executed = report.get("tasks_executed", [])
        failures = [
            item
            for item in task_results
            if isinstance(item, dict) and item.get("status") == "failed"
        ]
        concepts = [
            self.concept_summary(str(concept), stats)
            for concept, stats in report.get("concept_memory", {}).items()
        ]
        architecture = report.get("architecture_bottleneck_report", {})
        truth_candidates = report.get("truth_candidate_evaluations", {})
        truth_commits = report.get("truth_commit_evaluations", {})
        dependency = self.dependency_summary(report)
        context = self.context_summary(report)
        truth = self.truth_summary(report)
        cache = self.cache_summary(report)
        selected_limit = self.max_visible_tasks

        summary = {
            "selected_tasks": self.limit(tasks_executed, selected_limit),
            "active_tasks": [],
            "completed_tasks": report.get("successful_tasks", 0),
            "failed_tasks": report.get("failed_tasks", 0),
            "skipped_tasks": report.get("skipped_tasks", 0),
            "training_batch_size": report.get("tasks_selected", 0),
            "execution_progress": {
                "completed": report.get("successful_tasks", 0),
                "failed": report.get("failed_tasks", 0),
                "incomplete": report.get("incomplete_tasks", 0),
                "total": report.get("tasks_selected", 0),
            },
            "concepts": self.limit(concepts, self.max_visible_candidates),
        }
        metrics = {
            "tasks_executed_count": self.count(tasks_executed),
            "multi_task_result_count": self.count(task_results),
            "concept_count": self.count(report.get("concepts_discovered", {})),
            **dependency,
            **context,
            **truth,
            **cache,
        }
        warnings = []
        if architecture.get("bottleneck_type"):
            warnings.append({
                "bottleneck_type": architecture.get("bottleneck_type"),
                "recommended_next_step": architecture.get("recommended_next_step"),
            })
        warnings.extend(architecture.get("blocking_factors", []) or [])

        return self.unified_report(
            system=report.get("system", "training_report"),
            status="failed" if failures else "ok",
            report_state=report.get("report_state", "final"),
            summary=summary,
            metrics=metrics,
            warnings=warnings,
            failures=failures,
            recommendations=[
                item
                for item in [
                    architecture.get("recommended_next_step"),
                    report.get("recommended_next_step"),
                ]
                if item
            ],
            level=level,
            details={
                "truth_candidate_evaluations": truth_candidates,
                "truth_commit_evaluations": truth_commits,
                "architecture_bottleneck_report": architecture,
            },
            history={
                "training_batch_snapshot": report.get("training_batch_snapshot", {}),
                "concept_lifecycle": report.get("concept_lifecycle", {}),
            },
        )

    def dependency_summary(self, report: dict) -> dict:
        architecture = report.get("architecture_bottleneck_report", {})
        return {
            "dependency_chains_executed": architecture.get(
                "dependency_chains_executed",
                architecture.get("process_dependency_links_used"),
            ),
            "dependency_chain_depth": architecture.get("dependency_chain_depth"),
            "dependency_chain_coverage": architecture.get("dependency_chain_coverage"),
            "dependency_coherence": architecture.get("dependency_coherence"),
            "dependency_reasoning_time": architecture.get(
                "dependency_reasoning_time",
                architecture.get("dependency_time"),
            ),
            "dependency_activation_state": architecture.get(
                "dependency_activation_state",
                architecture.get(
                    "dependency_lifecycle_state",
                    "UNKNOWN" if architecture else "NOT_REQUESTED",
                ),
            ),
            "dependency_failures": self.count(architecture.get("dependency_failures", [])),
        }

    def context_summary(self, report: dict) -> dict:
        semantic = report.get("semantic_context_reports", {})
        registry_report = self._mapping(report.get("context_registry_report"))
        registry_contexts = registry_report.get("contexts", [])
        if not isinstance(registry_contexts, list):
            registry_contexts = []
        context_type_counts = {
            "SEMANTIC_CONTEXT": 0,
            "PROCESS_CONTEXT": 0,
            "CAUSAL_CONTEXT": 0,
            "WORLD_CONTEXT": 0,
        }
        for context in registry_contexts:
            if not isinstance(context, dict):
                continue
            context_type = str(context.get("context_type") or "SEMANTIC_CONTEXT")
            if context_type in context_type_counts:
                context_type_counts[context_type] += 1
        contextual = report.get("contextual_truth_reports", {})
        discovery = report.get("context_discovery_reports", {})
        total_contexts = max(
            len(registry_contexts),
            self.count(semantic),
            self.count(contextual),
            self.count(discovery),
        )
        return {
            "context_count": total_contexts,
            "semantic_context_count": (
                context_type_counts["SEMANTIC_CONTEXT"]
                or self.count(semantic)
            ),
            "process_context_count": context_type_counts["PROCESS_CONTEXT"],
            "causal_context_count": (
                context_type_counts["CAUSAL_CONTEXT"]
                or self.count(report.get("causal_validation_reports", {}))
            ),
            "world_context_count": (
                context_type_counts["WORLD_CONTEXT"]
                or self.count(report.get("world_context_reports", {}))
            ),
            "context_generation_time": report.get("context_generation_time"),
            "context_confidence": report.get("context_confidence"),
            "context_registration_rate": report.get("context_registration_rate"),
        }

    def truth_summary(self, report: dict) -> dict:
        candidates = report.get("truth_candidate_evaluations", {})
        commits = report.get("truth_commit_evaluations", {})
        committed = [
            item
            for item in commits.values()
            if isinstance(item, dict)
            and item.get("final_commit_state") == "TRUTH_COMMITTED"
        ] if isinstance(commits, dict) else []
        return {
            "discovering_count": report.get("discovering_count"),
            "supported_count": report.get("supported_count"),
            "validated_count": report.get("validated_count"),
            "candidate_count": self.count(candidates),
            "committed_count": len(committed),
            "locked_truth_count": report.get("locked_truth_count"),
            "promotion_rate": report.get("promotion_rate"),
            "truth_commit_rate": (
                round(len(committed) / max(self.count(commits), 1), 4)
                if commits
                else 0.0
            ),
            "promotion_failures": report.get("promotion_failures", 0),
            "blocking_factors": self.count(
                report.get("architecture_bottleneck_report", {}).get(
                    "blocking_factors",
                    [],
                )
            ),
        }

    def cache_summary(self, report: dict) -> dict:
        performance_report = self._mapping(report.get("performance_report"))
        performance_intelligence = self._mapping(
            report.get("PERFORMANCE_REPORT")
            or report.get("performance_intelligence_report")
        )
        memory_efficiency = self._mapping(
            performance_intelligence.get("memory_efficiency")
        )
        cache_sources = [
            performance_report,
            self._mapping(report.get("cache_metric_authority")),
            self._mapping(performance_report.get("adaptive_cache_layer")),
            report,
        ]
        reuse_sources = [
            performance_report,
            self._mapping(performance_report.get("adaptive_reuse_engine")),
            self._mapping(report.get("reuse_metric_authority")),
            self._mapping(report.get("ADAPTIVE_REUSE_REPORT")),
            self._mapping(report.get("adaptive_reuse_report")),
            memory_efficiency,
            self._mapping(report.get("knowledge_reuse_report")),
            self._mapping(report.get("strategy_reuse_report")),
            self._mapping(report.get("truth_reuse_report")),
            report,
        ]
        return {
            "cache_hits": self._first_metric(cache_sources, "cache_hits"),
            "cache_misses": self._first_metric(cache_sources, "cache_misses"),
            "cache_hit_rate": self._first_metric(cache_sources, "cache_hit_rate"),
            "reuse_rate": self._first_metric(reuse_sources, "reuse_rate"),
            "strategy_hits": self._first_metric(reuse_sources, "strategy_hits"),
            "truth_hits": self._first_metric(reuse_sources, "truth_hits"),
            "context_hits": self._first_metric(reuse_sources, "context_hits"),
            "estimated_compute_saved": self._first_metric(
                reuse_sources,
                "estimated_compute_saved",
            ),
            "estimated_runtime_saved": self._first_metric(
                reuse_sources,
                "estimated_runtime_saved",
            ),
        }

    def _first_metric(self, sources: list, key: str):
        for source in sources:
            if isinstance(source, dict) and source.get(key) is not None:
                return source.get(key)
        return 0

    def _mapping(self, value):
        return value if isinstance(value, dict) else {}

    def _limit_for_key(self, key: str | None) -> int:
        key = str(key or "")
        if "task" in key:
            return self.max_visible_tasks
        if "context" in key:
            return self.max_visible_contexts
        if "candidate" in key or "concept" in key:
            return self.max_visible_candidates
        if "failure" in key or "error" in key:
            return self.max_visible_failures
        if "warning" in key:
            return self.max_visible_warnings
        return self.max_visible_candidates

    def _compact_item(self, item: Any):
        if not isinstance(item, dict):
            return item
        return {
            key: value
            for key, value in item.items()
            if key
            in {
                "task",
                "status",
                "error",
                "concept",
                "concept_name",
                "current_stage",
                "confidence",
                "support_score",
                "contradiction_score",
                "promotion_score",
                "observation_count",
                "candidate_ready",
                "last_updated",
                "state",
                "history_count",
                "bottleneck_type",
                "recommended_next_step",
            }
        }


output_governor = OutputGovernor()


__all__ = [
    "ADVANCED_REPORT_LEVELS",
    "DEFAULT_LIMITS",
    "HISTORICAL_ARCHIVE_KEYS",
    "OutputGovernor",
    "REPORT_LEVELS",
    "REPORT_STATES",
    "output_governor",
]
