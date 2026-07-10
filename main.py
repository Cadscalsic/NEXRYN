# ============================================
# NEXRYN MAIN RUNTIME
# ============================================

import argparse
import builtins
from contextlib import contextmanager
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime

from runtime.diagnostics import RuntimeWatchdog
from runtime.planning.execution_profile import build_execution_profile
from runtime.state.shared_cognitive_state import (
    CognitiveKnowledgeBus,
    SharedCognitiveState,
)


# ============================================
# BUILD RUNTIME BANNER
# ============================================

def print_runtime_banner():
    print("\n==================================================")
    print("NEXRYN :: ADAPTIVE COGNITIVE RUNTIME")
    print("==================================================")
    print("BOOT MODE :: META-COGNITIVE EXECUTION")
    print("==================================================\n")


# ============================================
# BUILD FINAL REPORT
# ============================================

def build_runtime_metadata(
    args,
    execution_time,
    runtime_status,
    context_count=0,
    runtime_metrics=None,
):
    runtime_metrics = runtime_metrics or {}
    return {
        "tasks_directory": args.tasks_dir,
        "mode": args.mode,
        "execution_profile": runtime_metrics.get("execution_profile"),
        "cognitive_pipeline": runtime_metrics.get("cognitive_pipeline"),
        "pipeline_contract": runtime_metrics.get("pipeline_contract"),
        "runtime_status": runtime_status,
        "execution_time": execution_time,
        "context_count": context_count,
        "max_chain_depth": args.max_chain_depth,
        "max_concepts": args.max_concepts,
        "telemetry_enabled": not args.disable_telemetry,
        "cache_dependencies": args.cache_dependencies,
        "report_level": args.report_level,
        "training_batch_size": runtime_metrics.get(
            "training_batch_size",
        ),
        "training_batch_size_source": runtime_metrics.get(
            "training_batch_size_source",
        ),
        "boot_duration": runtime_metrics.get("boot_duration"),
        "task_selection_duration": runtime_metrics.get(
            "task_selection_duration",
        ),
        "first_task_start_latency": runtime_metrics.get(
            "first_task_start_latency",
        ),
        "cache_boot_loaded": runtime_metrics.get("cache_boot_loaded"),
        "cache_boot_skipped": runtime_metrics.get("cache_boot_skipped"),
        "legacy_cache_detected": runtime_metrics.get(
            "legacy_cache_detected",
        ),
        "legacy_cache_migration_skipped": runtime_metrics.get(
            "legacy_cache_migration_skipped",
        ),
        "governance_budget_seconds": runtime_metrics.get(
            "governance_budget_seconds",
        ),
        "governance_budget_exceeded": runtime_metrics.get(
            "governance_budget_exceeded",
        ),
        "finalization_duration": runtime_metrics.get(
            "finalization_duration",
        ),
        "concept_lifecycle_cost": runtime_metrics.get(
            "concept_lifecycle_cost",
        ),
        "report_generation_cost": runtime_metrics.get(
            "report_generation_cost",
        ),
        "report_compression_ratio": runtime_metrics.get(
            "report_compression_ratio",
        ),
        "report_budget_usage": runtime_metrics.get(
            "report_budget_usage",
        ),
        "startup_hang_prevented": runtime_metrics.get(
            "startup_hang_prevented",
        ),
        "post_success_mode": args.post_success_mode,
        "performance_profile_enabled": args.profile,
        "performance_profile_output": args.profile_output,
        "performance_profile_level": args.profile_level,
        "profile_enabled": args.profile,
        "profile_output": args.profile_output,
        "profile_level": args.profile_level,
        "python_version": sys.version,
        "timestamp": str(datetime.utcnow()),
    }


def load_core_knowledge_from_truth_registry(
    registry_path="runtime/memory/storage/truth_registry.json",
):
    if not os.path.exists(registry_path):
        return []
    try:
        with open(registry_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return []

    from runtime.truth.core_knowledge_registry import CoreKnowledgeRegistry
    from runtime.truth.truth_graduation_engine import TruthGraduationEngine

    truths = payload.get("truths", [])
    normalized_truths = []
    for truth in truths if isinstance(truths, list) else []:
        if not isinstance(truth, dict):
            continue
        evidence = [
            item for item in truth.get("evidence", [])
            if isinstance(item, dict)
        ]
        normalized_truths.append({
            "concept": truth.get("concept") or truth.get("truth_name"),
            "truth_state": truth.get("truth_state", "TRUTH_COMMITTED"),
            "truth_confidence": truth.get(
                "truth_confidence",
                truth.get(
                    "calibrated_confidence",
                    truth.get("evidence_strength"),
                ),
            ),
            "commit_score": truth.get(
                "commit_score",
                truth.get(
                    "calibrated_confidence",
                    truth.get("evidence_strength"),
                ),
            ),
            "cross_task_stability": truth.get(
                "cross_task_stability",
                truth.get(
                    "evidence_strength",
                    truth.get("calibrated_confidence"),
                ),
            ),
            "contradiction_rate": truth.get(
                "contradiction_rate",
                truth.get("contradiction_score", 0.0),
            ),
            "truth_commit_count": truth.get(
                "truth_commit_count",
                truth.get("trial_count", len(evidence)),
            ),
            "supporting_tasks": [
                item.get("metadata", {}).get("task_id")
                for item in evidence
                if item.get("metadata", {}).get("task_id")
            ],
        })

    graduation_report = TruthGraduationEngine().graduate(
        normalized_truths,
        reuse_report={"truth_reuse_rate": 1.0},
    )
    registry = CoreKnowledgeRegistry()
    registry.register_graduated(
        graduation_report.get("graduation_records", [])
    )
    return registry.all_records()


# ============================================
# SAFE PRINT
# ============================================

def safe_print_context(results, report_level="normal"):
    try:
        from runtime.reporting.compact_report_builder import (
            compact_report_builder,
        )
        from runtime.context.context_serializer import normalize_context
        from runtime.context.context_validation_engine import (
            context_validation_engine,
        )

        results = normalize_context(results)
        results.setdefault(
            "context_validation_report",
            context_validation_engine.validate(results),
        )

        if isinstance(results, dict):
            training_report = results.get("training_report", {})

            if training_report and report_level == "minimal":
                architecture_report = training_report.get(
                    "architecture_bottleneck_report",
                    {},
                )
                raw_performance_report = results.get(
                    "performance_report",
                    {},
                )
                raw_adaptive_reuse_report = (
                    results.get("ADAPTIVE_REUSE_REPORT")
                    or raw_performance_report.get("ADAPTIVE_REUSE_REPORT")
                    or raw_performance_report.get("adaptive_reuse_report")
                    or raw_performance_report.get("adaptive_reuse_engine")
                    or {}
                )
                if not raw_adaptive_reuse_report:
                    task_adaptive_reports = []
                    for item in results.get("multi_task_results", []) or []:
                        result = (
                            item.get("result", {})
                            if isinstance(item, dict)
                            else {}
                        )
                        if not isinstance(result, dict):
                            continue
                        candidate = (
                            result.get("ADAPTIVE_REUSE_REPORT")
                            or result.get("adaptive_reuse_report")
                            or (
                                result.get("performance_report", {})
                                .get("adaptive_reuse_engine", {})
                                if isinstance(
                                    result.get("performance_report"),
                                    dict,
                                )
                                else {}
                            )
                        )
                        nested = (
                            candidate.get("ADAPTIVE_REUSE_REPORT")
                            if isinstance(candidate, dict)
                            else {}
                        )
                        if isinstance(nested, dict) and nested:
                            candidate = nested
                        if isinstance(candidate, dict) and candidate:
                            task_adaptive_reports.append(candidate)
                    if task_adaptive_reports:
                        raw_adaptive_reuse_report = {
                            "experience_count": max(
                                int(
                                    _metric_number(
                                        report.get("experience_count"),
                                    )
                                )
                                for report in task_adaptive_reports
                            ),
                            "retrieval_attempts": sum(
                                int(
                                    _metric_number(
                                        report.get("retrieval_attempts"),
                                    )
                                )
                                for report in task_adaptive_reports
                            ),
                            "retrieval_successes": sum(
                                int(
                                    _metric_number(
                                        report.get("retrieval_successes"),
                                    )
                                )
                                for report in task_adaptive_reports
                            ),
                            "strategy_hits": sum(
                                int(_metric_number(report.get("strategy_hits")))
                                for report in task_adaptive_reports
                            ),
                            "program_hits": sum(
                                int(_metric_number(report.get("program_hits")))
                                for report in task_adaptive_reports
                            ),
                            "context_hits": sum(
                                int(_metric_number(report.get("context_hits")))
                                for report in task_adaptive_reports
                            ),
                            "truth_hits": sum(
                                int(_metric_number(report.get("truth_hits")))
                                for report in task_adaptive_reports
                            ),
                            "dependency_hits": sum(
                                int(
                                    _metric_number(
                                        report.get(
                                            "dependency_hits",
                                            report.get(
                                                "dependency_snapshot_hits",
                                            ),
                                        ),
                                    )
                                )
                                for report in task_adaptive_reports
                            ),
                            "cache_hits": sum(
                                int(_metric_number(report.get("cache_hits")))
                                for report in task_adaptive_reports
                            ),
                            "cache_misses": sum(
                                int(_metric_number(report.get("cache_misses")))
                                for report in task_adaptive_reports
                            ),
                            "estimated_runtime_saved": round(
                                sum(
                                    _metric_number(
                                        report.get("estimated_runtime_saved"),
                                    )
                                    for report in task_adaptive_reports
                                ),
                                4,
                            ),
                            "estimated_compute_saved": round(
                                sum(
                                    _metric_number(
                                        report.get("estimated_compute_saved"),
                                    )
                                    for report in task_adaptive_reports
                                ),
                                4,
                            ),
                        }
                        raw_adaptive_reuse_report["reuse_success_rate"] = round(
                            raw_adaptive_reuse_report["retrieval_successes"]
                            / max(
                                raw_adaptive_reuse_report[
                                    "retrieval_attempts"
                                ],
                                1,
                            ),
                            4,
                        )
                if not raw_adaptive_reuse_report:
                    try:
                        from runtime.adaptive_reuse import adaptive_reuse_layer

                        raw_adaptive_reuse_report = (
                            adaptive_reuse_layer.last_report
                        )
                    except Exception:
                        raw_adaptive_reuse_report = {}
                performance_report = (
                    compact_report_builder.compact_performance_report(
                        raw_performance_report,
                    )
                )
                print({
                    "system": "runtime_final_context",
                    "report_state": "final",
                    "status": (
                        "failed"
                        if results.get("failed_tasks", 0)
                        else "ok"
                    ),
                    "tasks_executed": results.get("tasks_executed", 0),
                    "successful_tasks": results.get("successful_tasks", 0),
                    "failed_tasks": results.get("failed_tasks", 0),
                    "incomplete_tasks": results.get("incomplete_tasks", 0),
                    "architecture_bottleneck":
                    architecture_report.get("architecture_bottleneck"),
                    "recommended_next_step":
                    architecture_report.get("recommended_next_step"),
                    "dependency_chain_depth":
                    architecture_report.get("dependency_chain_depth"),
                    "dependency_chain_coverage":
                    architecture_report.get("dependency_chain_coverage"),
                    "resource_usage": {
                        "execution_time":
                        performance_report.get("execution_time"),
                        "total_runtime_seconds":
                        performance_report.get("total_runtime_seconds"),
                        "cache_hits": performance_report.get("cache_hits"),
                        "cache_misses": performance_report.get("cache_misses"),
                        "reuse_rate": performance_report.get("reuse_rate"),
                        "strategy_hits":
                        performance_report.get("strategy_hits"),
                        "truth_hits": performance_report.get("truth_hits"),
                        "context_hits": performance_report.get("context_hits"),
                        "estimated_runtime_saved":
                        performance_report.get("estimated_runtime_saved"),
                        "estimated_compute_saved":
                        performance_report.get("estimated_compute_saved"),
                    },
                    "ADAPTIVE_REUSE_REPORT": {
                        key: raw_adaptive_reuse_report.get(key)
                        for key in (
                            "experience_count",
                            "retrieval_attempts",
                            "retrieval_successes",
                            "strategy_hits",
                            "program_hits",
                            "context_hits",
                            "truth_hits",
                            "dependency_hits",
                            "cache_hits",
                            "cache_misses",
                            "reuse_success_rate",
                            "estimated_runtime_saved",
                            "estimated_compute_saved",
                        )
                        if raw_adaptive_reuse_report.get(key) is not None
                    },
                })
            elif training_report:
                from runtime.learning.training_report import (
                    print_training_report,
                )

                print_training_report(
                    training_report,
                    report_level=report_level,
                )
            else:
                print(
                    compact_report_builder.compact_context(
                        results,
                        level=report_level,
                    )
                )
        else:
            print("INVALID RUNTIME CONTEXT")

    except Exception as error:
        print(f"CONTEXT PRINT FAILURE: {error}")
        try:
            from runtime.context.context_serializer import serialize_context

            serialized = serialize_context(results)
            print({
                "context_print_fallback": True,
                "context_id": serialized.context_id,
                "serialized_context_bytes": len(serialized.payload),
            })
        except Exception as fallback_error:
            print({
                "context_print_fallback": False,
                "failure_reason": str(fallback_error),
            })


# ============================================
# RUNTIME OUTPUT HELPERS
# ============================================

def print_training_batch_summary(
    training_batch,
    verbose=False,
    report_level="normal",
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )
    from runtime.reporting.output_governor import output_governor

    print("\n==================================================")
    print("NEXRYN :: TRAINING ASSISTANT BATCH")
    print("==================================================\n")

    if verbose:
        print(compact_report_builder.compact_context(training_batch))
        return

    selected_files = list(training_batch.get("selected_task_files", []) or [])
    print("training_mode:", training_batch.get("training_mode"))
    print("selected_tasks:", training_batch.get("selected_task_count", 0))
    print("tasks_completed:", 0)
    print("tasks_failed:", 0)
    print("tasks_remaining:", training_batch.get("selected_task_count", 0))
    print("current_batch_size:", training_batch.get("selected_task_count", 0))
    print(
        "selected_task_files:",
        output_governor.limit(
            selected_files,
            output_governor.max_visible_tasks,
        ),
    )
    if report_level != "minimal":
        print(
            "prioritized_concepts:",
            output_governor.limit(
                training_batch.get("prioritized_concepts", []),
                output_governor.max_visible_candidates,
            ),
        )
    selection_report = training_batch.get("selection_diversity_report", {})
    if selection_report and report_level != "minimal":
        print()
        print("TRAINING SELECTION DIVERSITY REPORT")
        print(
            "total_available_tasks=",
            selection_report.get("total_available_tasks", 0),
            "selected_tasks=",
            output_governor.limit(
                selection_report.get("selected_tasks", []),
                output_governor.max_visible_tasks,
            ),
            "selection_mode=",
            selection_report.get("selection_mode"),
            "random_seed=",
            selection_report.get("random_seed"),
        )
        print(
            "previous_batch_overlap_count=",
            selection_report.get("previous_batch_overlap_count", 0),
            "unseen_tasks_selected=",
            selection_report.get("unseen_tasks_selected", 0),
            "cooldown_filtered_tasks=",
            selection_report.get("cooldown_filtered_tasks", 0),
            "average_task_selection_frequency=",
            selection_report.get("average_task_selection_frequency", 0.0),
            "repeated_task_penalty_applied=",
            selection_report.get("repeated_task_penalty_applied", False),
            "diversity_score=",
            selection_report.get("diversity_score", 0.0),
        )


class _MinimalRuntimePrintFilter:
    ALLOWED_MARKERS = {
        "CRITICAL",
        "FATAL",
        "RUNTIME WARNING",
    }
    HEAVY_MARKERS = {
        "predicted_grid",
        "counterfactual_candidates",
        "graph_reasoning",
        "object_tracker",
        "dependency_evidence",
        "localization_reports",
        "object_motion_report",
        "OBJECT_MOTION_REPORT",
        "LOCALIZATION_REPORT",
    }

    def __init__(self, original_print):
        self.original_print = original_print
        self._suppress_next_payload = False

    def __call__(self, *args, **kwargs):
        if self._suppress_next_payload:
            self._suppress_next_payload = False
            return
        if not args:
            return
        text_args = []
        for arg in args:
            if self._is_heavy(arg):
                return
            text = str(arg)
            if self._is_heavy_text(text):
                return
            if text.strip().upper() in {
                "PREDICTED OUTPUT:",
                "SYNTHESIZED PROGRAM:",
                "EXECUTION PLAN:",
                "SEARCH RESULT:",
                "SEMANTIC GRAPH:",
            }:
                self._suppress_next_payload = True
                return
            text_args.append(text)
        joined = " ".join(text_args).upper()
        if not any(marker in joined for marker in self.ALLOWED_MARKERS):
            return
        self.original_print(*text_args, **kwargs)

    def _is_heavy(self, value):
        if hasattr(value, "shape") and hasattr(value, "dtype"):
            return True
        if isinstance(value, dict):
            return any(key in value for key in self.HEAVY_MARKERS)
        if isinstance(value, (list, tuple)) and len(value) > 12:
            return True
        return False

    def _is_heavy_text(self, text):
        if len(text) > 1200:
            return True
        return any(marker in text for marker in self.HEAVY_MARKERS)


@contextmanager
def minimal_runtime_output(enabled):
    if not enabled:
        yield
        return
    original_print = builtins.print
    builtins.print = _MinimalRuntimePrintFilter(original_print)
    try:
        yield
    finally:
        builtins.print = original_print


# ============================================
# OPTIONAL MATH REASONING HOOK
# ============================================

def build_passive_math_reasoning_report(
    task_path,
    concept=None,
    context=None,
):
    with open(task_path, "r", encoding="utf-8") as task_file:
        task_payload = json.load(task_file)

    train_pairs = task_payload.get("train", [])
    if not train_pairs:
        return {
            "system": "mathematical_reasoning_pipeline",
            "task_id": os.path.basename(task_path),
            "math_reasoning_available": False,
            "reason": "no_training_pairs_available",
        }

    first_pair = train_pairs[0]

    from core.math_reasoning import MathematicalReasoningPipeline

    return MathematicalReasoningPipeline().analyze_task(
        task_id=os.path.basename(task_path),
        input_grid=first_pair.get("input", []),
        output_grid=first_pair.get("output"),
        concept=concept,
        context=context,
    )


# ============================================
# DIAGNOSTIC HELPERS
# ============================================

def normalize_concept_diagnostics(training_report):
    concepts = {}

    for concept, stats in training_report.get("concept_memory", {}).items():
        concepts[concept] = {
            **stats,
            "state": stats.get(
                "promotion_stage",
                stats.get("lifecycle_state", "DISCOVERING"),
            ),
            "candidate_ready": stats.get(
                "candidate_ready",
                stats.get("preliminary_truth_candidate_ready", False),
            ),
            "promotion_score": stats.get("promotion_score"),
            "promotion_stage": stats.get(
                "promotion_stage",
                stats.get("lifecycle_state", "DISCOVERING"),
            ),
            "eligible_for_context": stats.get(
                "eligible_for_context",
                False,
            ),
            "eligible_for_truth_candidate": stats.get(
                "eligible_for_truth_candidate",
                False,
            ),
            "blocked_metrics": stats.get("blocked_metrics", []),
            "promotion_reason": stats.get("promotion_reason"),
            "ledger_average_contradiction": stats.get(
                "ledger_average_contradiction_score",
                stats.get("average_contradiction_score"),
            ),
        }

    return concepts


def normalize_truth_candidates(training_report):
    candidates = {}

    for concept, evaluation in training_report.get(
        "truth_candidate_evaluations",
        {},
    ).items():
        candidates[concept] = {
            **evaluation,
            "eligible": evaluation.get("eligible_for_truth_candidate", False),
            "blocked": evaluation.get("blocked_metrics", []),
            "effective_contradiction": evaluation.get(
                "effective_contradiction_score",
            ),
        }

    return candidates


def normalize_context_diagnostics(training_report):
    contexts = {}

    for report_name in [
        "contextual_truth_reports",
        "context_discovery_reports",
        "context_hierarchy_reports",
        "semantic_context_reports",
    ]:
        report = training_report.get(report_name, {})

        if isinstance(report, dict):
            contexts.update(report)

    return contexts


def _metric_number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def task_execution_status(task_result):
    if not isinstance(task_result, dict):
        return "failed"
    evaluation = task_result.get("evaluation_result", {})
    if not isinstance(evaluation, dict):
        evaluation = {}
    success_state = str(
        evaluation.get("success_state")
        or task_result.get("success_state")
        or ""
    )
    task_status = str(
        evaluation.get("task_status")
        or task_result.get("task_status")
        or ""
    )
    if (
        task_result.get("pipeline_incomplete") is True
        or task_result.get("evaluation_complete") is False
        or evaluation.get("pipeline_incomplete") is True
        or task_status == "TASK_INCOMPLETE"
        or success_state in {
            "PREDICTION_NOT_PRODUCED",
            "TARGET_OUTPUT_MISSING",
        }
    ):
        return "incomplete"
    if evaluation.get("success") is True or evaluation.get("exact_success") is True:
        return "completed"
    if success_state in {
        "SUCCESS",
        "EXACT_SUCCESS",
        "SUCCESS_WITH_RESIDUALS",
        "HIGH_VALUE_PARTIAL_SUCCESS",
        "LEARNING_PROGRESS",
        "PARTIAL_SUCCESS",
    }:
        return "completed"
    return "failed"


def build_runtime_metric_bridge(
    all_results,
    training_report,
    task_performance_reports,
    module_timings,
    runtime_metrics=None,
):
    from runtime.profiling.metric_bridge import runtime_metric_bridge
    from runtime.metrics.canonical_metric_registry import (
        CanonicalMetricRegistry,
    )
    from runtime.metrics.metric_validation_engine import MetricValidationEngine
    from runtime.metrics.unified_metric_store import UnifiedMetricStore
    from runtime.observability.runtime_observability_layer import (
        RuntimeObservabilityLayer,
    )

    runtime_metrics = runtime_metrics or {}
    registry = CanonicalMetricRegistry()
    store = UnifiedMetricStore(registry=registry)
    observability = RuntimeObservabilityLayer(
        store=store,
        registry=registry,
        validator=MetricValidationEngine(store=store),
    )
    concept_memory = training_report.get("concept_memory", {})
    contexts = normalize_context_diagnostics(training_report)
    completed_tasks = sum(
        1
        for item in all_results
        if item.get("status") == "completed"
    )

    concept_candidates = [
        sum(
            int(_metric_number(report.get("concepts_processed")))
            for report in task_performance_reports
        ),
        len(concept_memory) if isinstance(concept_memory, dict) else 0,
        completed_tasks,
    ]

    dependency_depths = []
    dependency_coverages = []
    dependency_chain_reports = 0
    semantic_counts = []

    metric_sources = [
        report
        for report in task_performance_reports
        if isinstance(report, dict)
    ]
    for item in all_results:
        result = item.get("result", {})
        if not isinstance(result, dict):
            continue
        for key in (
            "performance_report",
            "PERFORMANCE_REPORT",
            "performance_intelligence_report",
            "runtime_metadata",
        ):
            report = result.get(key)
            if isinstance(report, dict):
                metric_sources.append(report)
    metric_sources.append(training_report)
    for key in (
        "concept_lifecycle",
        "concept_lifecycle_report",
        "architecture_bottleneck_report",
        "dependency_visibility_report",
        "runtime_attribution_report",
    ):
        report = training_report.get(key)
        if isinstance(report, dict):
            metric_sources.append(report)

    source_payloads = {}
    for index, mapping in enumerate(metric_sources):
        producer = str(mapping.get("system") or f"metric_source_{index}")
        source_name = f"{producer}:{index}"
        source_payloads[source_name] = mapping
        observability.ingest_report(
            mapping,
            producer=producer,
            source=source_name,
            confidence=0.80,
        )

    for mapping in metric_sources:
        if "dependency_chain_depth" in mapping:
            depth = int(_metric_number(mapping.get("dependency_chain_depth")))
            dependency_depths.append(depth)
            if depth > 0:
                dependency_chain_reports += 1
        if "dependency_chain_coverage" in mapping:
            coverage = _metric_number(
                mapping.get("dependency_chain_coverage"),
            )
            dependency_coverages.append(coverage)
        if "semantic_concept_count" in mapping:
            semantic_counts.append(
                int(_metric_number(mapping.get("semantic_concept_count")))
            )

    active_compute_time = sum(
        _metric_number(item.get("seconds"))
        for item in module_timings
        if isinstance(item, dict)
    )
    timing_bridge = runtime_metric_bridge.synchronize(
        {
            "total_runtime_seconds": sum(
                _metric_number(report.get("total_runtime_seconds"))
                for report in task_performance_reports
            ),
            "active_compute_time_seconds": active_compute_time,
            "module_timings": module_timings,
        },
        module_timings=module_timings,
        runtime_metrics=runtime_metrics,
    )
    observability.ingest_report(
        timing_bridge,
        producer="runtime_metric_bridge",
        source="timing_bridge",
        confidence=0.95,
    )

    concepts_processed = max(concept_candidates + semantic_counts + [0])
    dependency_chain_depth = max(dependency_depths or [0])
    dependency_chain_coverage = max(dependency_coverages or [0.0])
    dependency_executor_cache_misses = sum(
        int(_metric_number(report.get("dependency_executor_cache_misses")))
        for report in task_performance_reports
    )
    dependency_executor_cache_hits = sum(
        int(_metric_number(report.get("dependency_executor_cache_hits")))
        for report in task_performance_reports
    )
    reported_dependency_executions = sum(
        int(_metric_number(report.get("dependency_chains_executed")))
        for report in task_performance_reports
    )
    dependency_chains_executed = (
        dependency_executor_cache_misses
        if (dependency_executor_cache_hits or dependency_executor_cache_misses)
        else max(reported_dependency_executions, dependency_chain_reports)
    )
    bridge_metrics = {
        "dependency_chain_depth": dependency_chain_depth,
        "dependency_depth": dependency_chain_depth,
        "dependency_chains_executed": dependency_chains_executed,
        "cache_hits": sum(
            int(_metric_number(report.get("cache_hits")))
            for report in task_performance_reports
        ),
        "cache_misses": sum(
            int(_metric_number(report.get("cache_misses")))
            for report in task_performance_reports
        ),
    }
    for metric_name, value in bridge_metrics.items():
        observability.store.update_metric(
            metric_name,
            value,
            producer=observability.store.registry.owner_for(metric_name),
            source="runtime_metric_bridge",
            confidence=0.98,
        )
    reconciliation = observability.build_reconciliation_report(
        source_payloads,
    )
    canonical_metrics = reconciliation.get("canonical_metrics", {})

    warnings = []
    if concepts_processed == 0 and completed_tasks:
        warnings.append("concept_metrics_missing_despite_completed_tasks")
    if dependency_chain_depth == 0 and dependency_chain_reports:
        warnings.append("dependency_depth_missing_despite_chain_reports")

    return {
        "concepts_processed": concepts_processed,
        "semantic_concept_count": max(
            semantic_counts + [concepts_processed],
        ),
        "context_count": len(contexts),
        "dependency_chain_depth": int(
            _metric_number(
                canonical_metrics.get(
                    "dependency_chain_depth",
                    dependency_chain_depth,
                )
            )
        ),
        "dependency_chain_coverage": round(dependency_chain_coverage, 4),
        "dependency_chains_executed": int(
            _metric_number(
                canonical_metrics.get(
                    "dependency_chains_executed",
                    dependency_chains_executed,
                )
            )
        ),
        "dependency_chain_reports_observed": dependency_chain_reports,
        "canonical_metrics": canonical_metrics,
        "METRIC_RECONCILIATION_REPORT":
        reconciliation["METRIC_RECONCILIATION_REPORT"],
        "METRIC_SOURCE_AUDIT": reconciliation["METRIC_SOURCE_AUDIT"],
        "METRIC_CONFLICT_REPORT": reconciliation["METRIC_CONFLICT_REPORT"],
        "METRIC_RECONCILIATION_WARNING":
        reconciliation["METRIC_RECONCILIATION_WARNING"],
        **timing_bridge,
        "metric_bridge": {
            "concept_sources": {
                "task_performance_reports": concept_candidates[0],
                "training_concept_memory": concept_candidates[1],
                "completed_tasks_floor": concept_candidates[2],
            },
            "dependency_depth_samples": len(dependency_depths),
            "dependency_coverage_samples": len(dependency_coverages),
            "reported_dependency_executions": reported_dependency_executions,
            "dependency_executor_cache_hits": dependency_executor_cache_hits,
            "dependency_executor_cache_misses": dependency_executor_cache_misses,
            "semantic_count_samples": len(semantic_counts),
            "timing_fields_synchronized": True,
        },
        "metric_source_warnings": warnings,
    }


def collect_governance_reports(all_results, possible_keys):
    collected = {}

    for item in all_results:
        result = item.get("result", {})

        if not isinstance(result, dict):
            continue

        governance_reports = result.get("governance_reports", {})

        report_sources = [result]
        if isinstance(governance_reports, dict):
            report_sources.append(governance_reports)
        for nested_key in (
            "performance_report",
            "runtime_context",
            "execution_result",
            "execution_report",
        ):
            nested_report = result.get(nested_key)
            if isinstance(nested_report, dict):
                report_sources.append(nested_report)

        for source in report_sources:
            for key in possible_keys:
                report = source.get(key)

                if isinstance(report, dict):
                    collected.update(report)

    return collected


def resolve_training_batch_size(args, parser):
    explicit = any(
        item == "--training-batch-size"
        or item.startswith("--training-batch-size=")
        for item in sys.argv[1:]
    )
    if explicit:
        return max(1, int(args.training_batch_size)), "cli"
    if args.mode == "fast":
        return 3, "mode_default"
    return 3, "default"


def governance_budget_for_mode(mode):
    return {
        "fast": 5,
        "adaptive": 10,
        "deep": None,
    }.get(mode)


# ============================================
# ARGUMENT PARSER
# ============================================

parser = argparse.ArgumentParser(
    description="NEXRYN Cognitive Runtime"
)

parser.add_argument(
    "--tasks_dir",
    type=str,
    default="data/training",
    help="Directory containing ARC tasks",
)

parser.add_argument(
    "--mode",
    type=str,
    default="adaptive",
    choices=["fast", "adaptive", "deep", "full"],
    help="Runtime mode",
)

parser.add_argument(
    "--max-chain-depth",
    type=int,
    default=None,
    help="Maximum dependency chain depth per concept",
)

parser.add_argument(
    "--max-concepts",
    type=int,
    default=None,
    help="Maximum dependency concepts processed per runtime cycle",
)

parser.add_argument(
    "--disable-telemetry",
    action="store_true",
    help="Disable full dependency telemetry collection",
)

parser.add_argument(
    "--cache-dependencies",
    action="store_true",
    default=None,
    help="Reuse cached dependency chains when inputs are unchanged",
)

parser.add_argument(
    "--report-level",
    type=str,
    default=None,
    choices=["minimal", "normal", "full", "debug", "audit"],
    help="Runtime report detail level",
)

parser.add_argument(
    "--post-success-mode",
    type=str,
    default="fast",
    choices=["fast", "normal", "deep"],
    help="Post-success processing mode after exact successful execution",
)

parser.add_argument(
    "--profile",
    action="store_true",
    help="Enable runtime profiling and performance intelligence output",
)

parser.add_argument(
    "--profile-output",
    type=str,
    default="runtime_profile.json",
    help="Write profiling output to this JSON file when --profile is enabled",
)

parser.add_argument(
    "--profile-level",
    type=str,
    default="minimal",
    choices=["minimal", "detailed"],
    help="Runtime profiling detail level",
)

parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable debug mode",
)

parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose runtime output",
)

parser.add_argument(
    "--training-batch-size",
    type=int,
    default=None,
    help="Number of ARC training tasks executed per runtime cycle",
)

parser.add_argument(
    "--migrate-cache",
    action="store_true",
    help="Explicitly migrate legacy concept_cache.json before execution",
)

parser.add_argument(
    "--reset-training-assistant",
    action="store_true",
    help="Reset the persistent training batch cursor before execution",
)

parser.add_argument(
    "--selection-mode",
    type=str,
    default="weighted_random",
    choices=["random", "weighted_random", "curriculum"],
    help="Training task selection mode",
)

parser.add_argument(
    "--random-seed",
    type=int,
    default=None,
    help="Optional reproducible random seed for training task selection",
)

parser.add_argument(
    "--math-reasoning",
    action="store_true",
    help="Enable passive mathematical reasoning evidence reports",
)

parser.add_argument(
    "--export-typed-dependencies",
    action="store_true",
    help="Export math reasoning typed dependencies when math reasoning is enabled",
)

# ============================================
# DIAGNOSTIC ARGUMENTS
# ============================================

parser.add_argument(
    "--stats",
    action="store_true",
    help="Show cognitive runtime statistics",
)

parser.add_argument(
    "--audit",
    action="store_true",
    help="Run full concept audit",
)

parser.add_argument(
    "--explain",
    type=str,
    default=None,
    help="Explain a specific concept",
)

parser.add_argument(
    "--identity",
    action="store_true",
    help="Show identity governance diagnostics",
)

parser.add_argument(
    "--contexts",
    action="store_true",
    help="Show context diagnostics",
)

parser.add_argument(
    "--truths",
    action="store_true",
    help="Show stable truths",
)

parser.add_argument(
    "--candidates",
    action="store_true",
    help="Show truth candidates",
)

parser.add_argument(
    "--audit-concepts",
    action="store_true",
    help="Expand concept lifecycle diagnostics in deep/full reports",
)

parser.add_argument(
    "--audit-dependencies",
    action="store_true",
    help="Expand dependency diagnostics in deep/full reports",
)

parser.add_argument(
    "--audit-truth",
    action="store_true",
    help="Expand truth diagnostics in deep/full reports",
)

parser.add_argument(
    "--audit-cache",
    action="store_true",
    help="Expand cache diagnostics in deep/full reports",
)

parser.add_argument(
    "--audit-lineage",
    action="store_true",
    help="Expand lineage diagnostics in deep/full reports",
)

parser.add_argument(
    "--deep-max-total-runtime",
    type=float,
    default=None,
    help="Maximum total deep-mode runtime budget in seconds",
)

parser.add_argument(
    "--deep-max-task-runtime",
    type=float,
    default=None,
    help="Maximum per-task deep-mode runtime budget in seconds",
)

parser.add_argument(
    "--deep-max-report-time",
    type=float,
    default=None,
    help="Maximum deep-mode report generation budget in seconds",
)

parser.add_argument(
    "--deep-max-concept-lifecycle-time",
    type=float,
    default=None,
    help="Maximum deep-mode concept lifecycle budget in seconds",
)

args = parser.parse_args()
from runtime.budget.deep_mode_budget_manager import deep_mode_budget_manager

deep_audit_flags = deep_mode_budget_manager.audit_flags_from_args(args)
deep_audit_sections = deep_mode_budget_manager.requested_sections(
    deep_audit_flags,
)
deep_budget = deep_mode_budget_manager.build_budget(
    max_total_runtime_seconds=args.deep_max_total_runtime,
    max_task_runtime_seconds=args.deep_max_task_runtime,
    max_report_time_seconds=args.deep_max_report_time,
    max_concept_lifecycle_seconds=args.deep_max_concept_lifecycle_time,
)
execution_profile = build_execution_profile(
    args.mode,
    report_level=args.report_level,
    audit_sections_requested=deep_audit_sections,
)
effective_report_level = args.report_level or execution_profile.report_level
args.report_level = effective_report_level
training_batch_size, training_batch_size_source = (
    resolve_training_batch_size(args, parser)
)
governance_budget_seconds = execution_profile.governance_budget_seconds
runtime_watchdog = RuntimeWatchdog()
runtime_watchdog.start("boot_total")
runtime_watchdog.checkpoint("boot_start")
runtime_metrics = {
    "execution_profile": execution_profile.as_runtime_metadata(),
    "cognitive_pipeline": execution_profile.pipeline_name,
    "pipeline_contract": "unified_execution_architecture",
    "training_batch_size": training_batch_size,
    "training_batch_size_source": training_batch_size_source,
    "governance_budget_seconds": governance_budget_seconds,
    "governance_budget_exceeded": False,
    "cache_boot_loaded": False,
    "cache_boot_skipped": True,
    "legacy_cache_detected": os.path.exists(
        os.path.join("runtime", "cache", "concept_cache.json")
    ),
    "legacy_cache_migration_skipped": not args.migrate_cache
    and os.path.exists(os.path.join("runtime", "cache", "concept_cache.json")),
    "startup_hang_prevented": True,
}


# ============================================
# START RUNTIME
# ============================================

print_runtime_banner()

runtime_start = time.time()
runtime_status = "booting"
results = {}
shutdown_controller = None
shared_cognitive_state = None
knowledge_bus = None


# ============================================
# PIPELINE VALIDATION
# ============================================

try:
    if args.verbose:
        print("NEXRYN :: VALIDATING PIPELINE...\n")

    from runtime.pipeline import pipeline

    if pipeline is None:
        raise RuntimeError("Pipeline initialization failed")
    runtime_watchdog.checkpoint("config_loaded")

except Exception as initialization_error:
    print("\nPIPELINE INITIALIZATION ERROR:\n")
    print(initialization_error)

    if args.debug:
        traceback.print_exc()

    sys.exit(1)


# ============================================
# EXECUTE PIPELINE
# ============================================

try:
    runtime_status = "running"

    if args.verbose:
        print("NEXRYN :: EXECUTING PIPELINE...\n")

    if not os.path.isdir(args.tasks_dir):
        raise FileNotFoundError(
            f"Tasks directory not found: {args.tasks_dir}"
        )

    discovered_task_files = sorted(
        [
            file
            for file in os.listdir(args.tasks_dir)
            if file.endswith(".json")
        ]
    )
    runtime_watchdog.checkpoint("task_list_loaded")

    from runtime.learning.training_assistant import TrainingAssistant

    training_assistant = TrainingAssistant(
        batch_size=training_batch_size,
        selection_mode=args.selection_mode,
        random_seed=args.random_seed,
    )

    if args.reset_training_assistant:
        training_assistant.reset()

    core_knowledge = load_core_knowledge_from_truth_registry()
    concept_counts = {}
    concept_states = {
        item["concept"]: item.get("graduation_level", "TRUTH_COMMITTED")
        for item in core_knowledge
        if item.get("concept")
    }
    observed_task_ids = []

    runtime_watchdog.start("task_selection")
    training_batch = training_assistant.select_batch(
        discovered_task_files,
        concept_counts=concept_counts,
        concept_states=concept_states,
        task_directory=args.tasks_dir,
        observed_task_ids=observed_task_ids,
        core_knowledge=core_knowledge,
        selection_mode=args.selection_mode,
        random_seed=args.random_seed,
    )
    runtime_metrics["task_selection_duration"] = (
        runtime_watchdog.stop_and_warn(
            "task_selection",
            "task_selection",
        )
    )
    runtime_watchdog.checkpoint("task_selection_complete")

    selection_training_diversity_report = dict(
        training_batch.get("training_diversity_report", {})
    )
    selection_diversity_report = dict(
        training_batch.get("selection_diversity_report", {})
    )
    task_files = training_batch["selected_task_files"]

    print_training_batch_summary(
        training_batch,
        verbose=args.verbose,
        report_level=args.report_level,
    )

    all_results = []
    successful_tasks = 0
    failed_tasks = 0
    incomplete_tasks = 0
    first_task_started = False
    main_module_timings = []
    task_execution_timings = []
    runtime_metrics["task_execution_time_seconds"] = 0.0

    def record_main_timing(module_name, started_at):
        main_module_timings.append({
            "module": module_name,
            "seconds": round(time.perf_counter() - started_at, 4),
        })

    if args.migrate_cache:
        from runtime.cache import CacheManager

        runtime_watchdog.start("cache_init")
        cache_manager = CacheManager(enable_legacy_cache_migration=True)
        runtime_metrics["cache_boot_loaded"] = True
        runtime_metrics["cache_boot_skipped"] = False
        runtime_metrics.update(cache_manager.boot_report())
        runtime_metrics["cache_init_duration"] = (
            runtime_watchdog.stop_and_warn("cache_init", "cache_init")
        )
    else:
        runtime_watchdog.checkpoint("cache_manager_initialized")

    for task_file in task_files:
        task_path = os.path.join(
            args.tasks_dir,
            task_file,
        )

        print("\n==================================================")
        print(f"NEXRYN :: RUNNING TASK :: {task_file}")
        print("==================================================\n")
        if not first_task_started:
            runtime_watchdog.checkpoint("first_task_started")
            runtime_metrics["first_task_start_latency"] = round(
                time.perf_counter()
                - runtime_watchdog.checkpoints["boot_start"],
                4,
            )
            runtime_metrics["boot_duration"] = (
                runtime_watchdog.stop_and_warn(
                    "boot_total",
                    "boot_total",
                )
            )
            print("NEXRYN :: TASK EXECUTION STARTED")
            first_task_started = True

        task_execution_started_at = time.perf_counter()
        try:
            with minimal_runtime_output(args.report_level == "minimal"):
                task_result = pipeline.run(
                    task_path=task_path,
                    arc_replication_candidates=[
                        {
                            "task_path": os.path.join(
                                args.tasks_dir,
                                candidate_file,
                            )
                        }
                        for candidate_file in task_files
                        if candidate_file != task_file
                    ],
                    mode=args.mode,
                    max_chain_depth=args.max_chain_depth,
                    max_concepts=args.max_concepts,
                    telemetry_enabled=(
                        False
                        if args.disable_telemetry
                        else None
                    ),
                    cache_dependencies=args.cache_dependencies,
                    report_level=args.report_level,
                    post_success_mode=args.post_success_mode,
                    profile=args.profile,
                    profile_level=args.profile_level,
                    audit_sections_requested=deep_audit_sections,
                    deep_budget_overrides=deep_budget.as_dict(),
                )
            if first_task_started and "first_task_completed" not in (
                runtime_watchdog.checkpoints
            ):
                runtime_watchdog.checkpoint("first_task_completed")

            if args.math_reasoning:
                math_report = build_passive_math_reasoning_report(
                    task_path,
                    concept=None,
                    context=None,
                )
                task_result[
                    "math_reasoning_report"
                ] = math_report

                if args.export_typed_dependencies:
                    from core.math_reasoning import MathematicalReasoningPipeline

                    process_memory = getattr(
                        getattr(
                            pipeline,
                            "process_dependency_graph",
                            None,
                        ),
                        "process_dependency_memory",
                        None,
                    )
                    if process_memory is not None:
                        task_result[
                            "math_reasoning_dependency_export"
                        ] = (
                            MathematicalReasoningPipeline()
                            .export_to_process_dependency_memory(
                                process_memory,
                                math_report,
                                export_typed_dependencies=True,
                            )
                        )

            task_status = task_execution_status(task_result)
            if task_status == "completed":
                successful_tasks += 1
            elif task_status == "failed":
                failed_tasks += 1
            else:
                incomplete_tasks += 1

            all_results.append(
                {
                    "task": task_file,
                    "status": task_status,
                    "result": task_result,
                }
            )

            governance_reports = task_result.get(
                "governance_reports",
                {},
            )

            if args.verbose:
                from runtime.reporting.compact_report_builder import (
                    compact_report_builder,
                )

                print("\n==================================================")
                print("NEXRYN :: GOVERNANCE REPORT")
                print("==================================================\n")
                print(
                    compact_report_builder.compact_context(
                        governance_reports,
                        level=args.report_level,
                    )
                )

        except Exception as task_error:
            failed_tasks += 1

            print(f"\nTASK FAILURE :: {task_file}")
            print(task_error)

            print("\n====================================")
            print("FULL TASK TRACEBACK")
            print("====================================\n")

            full_traceback = traceback.format_exc()
            print(full_traceback)

            all_results.append(
                {
                    "task": task_file,
                    "status": "failed",
                    "error": str(task_error),
                    "traceback": full_traceback,
                }
            )

        task_execution_elapsed = round(
            time.perf_counter() - task_execution_started_at,
            4,
        )
        task_execution_timings.append({
            "module": f"task_execution:{task_file}",
            "seconds": task_execution_elapsed,
        })
        if (
            args.mode in {"deep", "full"}
            and deep_mode_budget_manager.task_budget_exceeded(
                task_execution_elapsed,
                deep_budget,
            )
        ):
            budget_warning = {
                "system": "deep_mode_task_guard",
                "warning": "TASK_RUNTIME_BUDGET_EXCEEDED",
                "task": task_file,
                "task_runtime_seconds": task_execution_elapsed,
                "max_task_runtime_seconds":
                deep_budget.max_task_runtime_seconds,
                "partial_diagnostics_saved": True,
            }
            if all_results and all_results[-1].get("task") == task_file:
                all_results[-1].setdefault("result", {})
                if isinstance(all_results[-1]["result"], dict):
                    all_results[-1]["result"][
                        "TASK_RUNTIME_BUDGET_EXCEEDED"
                    ] = budget_warning
            runtime_metrics["task_budget_exceeded"] = True
            print(budget_warning)
        runtime_metrics["task_execution_time_seconds"] = round(
            runtime_metrics.get("task_execution_time_seconds", 0.0)
            + task_execution_elapsed,
            4,
        )

    module_start = time.perf_counter()
    training_assistant_report = training_assistant.complete_cycle(
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
        incomplete_tasks=incomplete_tasks,
    )
    record_main_timing("training_assistant_complete", module_start)

    module_start = time.perf_counter()
    ledger_report = (
        pipeline
        .cross_task_replication_collector
        .ledger
        .report()
    )
    record_main_timing("ledger_report", module_start)

    module_start = time.perf_counter()
    concepts_recomputed = 0
    concepts_reused = 0
    concept_lifecycle_report = (
        pipeline
        .concept_lifecycle_manager
        .knowledge_maturity_report
    )
    deep_concept_audit_requested = (
        args.mode in {"deep", "full"}
        and deep_mode_budget_manager.should_expand(
            "concepts",
            deep_audit_flags,
        )
    )
    if (
        not concept_lifecycle_report.get("concepts")
        and not (
            args.mode in {"deep", "full"}
            and not deep_concept_audit_requested
        )
    ):
        concept_lifecycle_report = (
            pipeline
            .concept_lifecycle_manager
            .update_knowledge_maturity(
                ledger_report,
                {
                    "report_level": args.report_level,
                    "truth_candidate_report": collect_governance_reports(
                        all_results,
                        [
                            "truth_candidate_report",
                            "truth_candidates",
                            "TRUTH CANDIDATE REPORT",
                        ],
                    ),
                },
            )
        )
        concepts_recomputed = len(
            concept_lifecycle_report.get("concepts", []) or []
        )
    elif args.mode in {"deep", "full"} and not deep_concept_audit_requested:
        concept_lifecycle_report = {
            "system": "concept_maturity_tracker",
            "report_state": "summary",
            "status": "ok",
            "concept_lifecycle_compressed": True,
            "lifecycle_processing_mode": "delta_summary",
            "summary_first_reporting": True,
            "lazy_expansion_required_for_full_details": "--audit-concepts",
            "concepts": [],
            "concept_count": len(
                concept_lifecycle_report.get("concepts", []) or []
            ),
            "ledger_entry_count": len(
                ledger_report.get("entries", [])
                if isinstance(ledger_report, dict)
                else []
            ),
            "cache_reuse_enabled": True,
        }
        concepts_reused = concept_lifecycle_report["concept_count"]
    concept_lifecycle_elapsed = round(time.perf_counter() - module_start, 4)
    if (
        (
            args.report_level not in {"full", "debug", "audit"}
            or (
                args.mode in {"deep", "full"}
                and not deep_concept_audit_requested
            )
        )
        and not concept_lifecycle_report.get("concept_lifecycle_compressed")
    ):
        from runtime.reporting.compact_report_builder import (
            compact_report_builder,
        )

        concept_lifecycle_report = (
            compact_report_builder.compact_concept_lifecycle_report(
                concept_lifecycle_report,
                report_budget_seconds=2.0,
                elapsed_seconds=concept_lifecycle_elapsed,
            )
        )
        pipeline.concept_lifecycle_manager.knowledge_maturity_report = (
            concept_lifecycle_report
        )
    elif deep_mode_budget_manager.concept_lifecycle_budget_exceeded(
        concept_lifecycle_elapsed,
        deep_budget,
    ):
        concept_lifecycle_report["report_budget_seconds"] = (
            deep_budget.max_concept_lifecycle_seconds
        )
        concept_lifecycle_report["report_elapsed_seconds"] = (
            concept_lifecycle_elapsed
        )
        concept_lifecycle_report["report_budget_exceeded"] = True
        concept_lifecycle_report["report_truncated_reason"] = (
            "deep_concept_lifecycle_budget"
        )
    if selection_training_diversity_report:
        concept_lifecycle_report["selection_training_diversity_report"] = (
            selection_training_diversity_report
        )
    if selection_diversity_report:
        concept_lifecycle_report["selection_diversity_report"] = (
            selection_diversity_report
        )
    record_main_timing("concept_lifecycle_report", module_start)

    from runtime.learning.training_report import build_training_report

    module_start = time.perf_counter()
    training_report = build_training_report(
        training_batch=training_batch,
        training_assistant_report=training_assistant_report,
        multi_task_results=all_results,
        ledger_report=ledger_report,
        concept_lifecycle_report=concept_lifecycle_report,
        include_truth_evaluations=(
            args.mode not in {"deep", "full"}
            or deep_mode_budget_manager.should_expand(
                "truth",
                deep_audit_flags,
            )
        ),
    )
    if (
        selection_training_diversity_report.get(
            "knowledge_expansion_score",
            0.0,
        )
        > training_report.get(
            "training_diversity_report",
            {},
        ).get("knowledge_expansion_score", 0.0)
    ):
        existing_training_diversity_report = training_report.get(
            "training_diversity_report",
            {},
        )
        merged_training_diversity_report = {
            **selection_training_diversity_report,
            **{
                key: value
                for key, value in existing_training_diversity_report.items()
                if key
                in {
                    "graduated_concepts",
                    "graduated_concept_count",
                    "core_concepts",
                    "core_concept_count",
                }
            },
        }
        if not merged_training_diversity_report.get("graduated_concept_count"):
            committed_concepts = sorted({
                str(concept)
                for concept, evaluation in training_report.get(
                    "truth_commit_evaluations",
                    {},
                ).items()
                if isinstance(evaluation, dict)
                and (
                    evaluation.get("final_commit_state") == "TRUTH_COMMITTED"
                    or evaluation.get("decision") == "TRUTH_COMMITTED"
                )
            })
            if committed_concepts:
                merged_training_diversity_report["graduated_concepts"] = (
                    committed_concepts
                )
                merged_training_diversity_report["graduated_concept_count"] = (
                    len(committed_concepts)
                )
        training_report["training_diversity_report"] = (
            merged_training_diversity_report
        )
        concept_lifecycle_report["training_diversity_report"] = (
            merged_training_diversity_report
        )
    record_main_timing("build_training_report", module_start)

    module_start = time.perf_counter()
    task_performance_reports = [
        item.get("result", {}).get("performance_report", {})
        for item in all_results
        if isinstance(item.get("result"), dict)
        and item.get("result", {}).get("performance_report")
    ]
    task_performance_intelligence_reports = [
        item.get("result", {}).get("PERFORMANCE_REPORT", {})
        for item in all_results
        if isinstance(item.get("result"), dict)
        and item.get("result", {}).get("PERFORMANCE_REPORT")
    ]
    module_timings = [
        module
        for report in task_performance_reports
        for module in report.get("module_timings", [])
    ]
    module_timings.extend(task_execution_timings)
    module_timings.extend(main_module_timings)
    slowest_modules = sorted(
        [
            module
            for report in task_performance_reports
            for module in report.get("slowest_modules", [])
        ] + task_execution_timings + main_module_timings,
        key=lambda item: item.get("seconds", 0.0),
        reverse=True,
    )[:5]
    record_main_timing("collect_task_performance_reports", module_start)
    module_timings.append(main_module_timings[-1])
    slowest_modules = sorted(
        slowest_modules + [main_module_timings[-1]],
        key=lambda item: item.get("seconds", 0.0),
        reverse=True,
    )[:5]

    module_start = time.perf_counter()
    metric_bridge = build_runtime_metric_bridge(
        all_results=all_results,
        training_report=training_report,
        task_performance_reports=task_performance_reports,
        module_timings=module_timings,
        runtime_metrics=runtime_metrics,
    )
    canonical_metrics = metric_bridge.get("canonical_metrics", {})
    record_main_timing("build_runtime_metric_bridge", module_start)
    module_timings.append(main_module_timings[-1])
    slowest_modules = sorted(
        slowest_modules + [main_module_timings[-1]],
        key=lambda item: item.get("seconds", 0.0),
        reverse=True,
    )[:5]
    module_start = time.perf_counter()
    total_runtime_seconds = round(
        sum(
            report.get("total_runtime_seconds", 0.0)
            for report in task_performance_reports
        ),
        4,
    )
    active_compute_time_seconds = metric_bridge[
        "active_compute_time_seconds"
    ]
    performance_report = {
        "system": "runtime_reasoning_budget",
        "total_runtime_seconds": total_runtime_seconds,
        "concepts_processed": metric_bridge["concepts_processed"],
        "semantic_concept_count": metric_bridge["semantic_concept_count"],
        "context_count": metric_bridge["context_count"],
        "cache_hits": canonical_metrics.get(
            "cache_hits",
            sum(
            report.get("cache_hits", 0)
            for report in task_performance_reports
            ),
        ),
        "cache_misses": canonical_metrics.get(
            "cache_misses",
            sum(
            report.get("cache_misses", 0)
            for report in task_performance_reports
            ),
        ),
        "strategy_hits": canonical_metrics.get(
            "strategy_hits",
            sum(
            report.get("strategy_hits", 0)
            for report in task_performance_reports
            ),
        ),
        "strategy_misses": sum(
            report.get("strategy_misses", 0)
            for report in task_performance_reports
        ),
        "context_hits": canonical_metrics.get(
            "context_hits",
            sum(
            report.get("context_hits", 0)
            for report in task_performance_reports
            ),
        ),
        "context_misses": sum(
            report.get("context_misses", 0)
            for report in task_performance_reports
        ),
        "program_hits": sum(
            report.get("program_hits", 0)
            for report in task_performance_reports
        ),
        "program_misses": sum(
            report.get("program_misses", 0)
            for report in task_performance_reports
        ),
        "truth_hits": canonical_metrics.get(
            "truth_hits",
            sum(
            report.get("truth_hits", 0)
            for report in task_performance_reports
            ),
        ),
        "truth_misses": sum(
            report.get("truth_misses", 0)
            for report in task_performance_reports
        ),
        "dependency_snapshot_hits": sum(
            report.get("dependency_snapshot_hits", 0)
            for report in task_performance_reports
        ),
        "dependency_executor_cache_hits": sum(
            report.get("dependency_executor_cache_hits", 0)
            for report in task_performance_reports
        ),
        "dependency_executor_cache_misses": sum(
            report.get("dependency_executor_cache_misses", 0)
            for report in task_performance_reports
        ),
        "dependency_snapshot_misses": sum(
            report.get("dependency_snapshot_misses", 0)
            for report in task_performance_reports
        ),
        "world_model_hits": sum(
            report.get("world_model_hits", 0)
            for report in task_performance_reports
        ),
        "world_model_misses": sum(
            report.get("world_model_misses", 0)
            for report in task_performance_reports
        ),
        "estimated_compute_saved": round(
            sum(
                report.get("estimated_compute_saved", 0.0)
                for report in task_performance_reports
            ),
            4,
        ),
        "estimated_runtime_saved": round(
            sum(
                report.get("estimated_runtime_saved", 0.0)
                for report in task_performance_reports
            ),
            4,
        ),
        "dependency_chains_executed":
        metric_bridge["dependency_chains_executed"],
        "dependency_chain_depth": metric_bridge["dependency_chain_depth"],
        "dependency_chain_coverage":
        metric_bridge["dependency_chain_coverage"],
        "pre_reasoning_router_enabled": any(
            report.get("pre_reasoning_router_enabled", False)
            for report in task_performance_reports
        ),
        "task_profiles_generated": sum(
            report.get("task_profiles_generated", 0)
            for report in task_performance_reports
        ),
        "selective_execution_enabled": any(
            report.get("selective_execution_enabled", False)
            for report in task_performance_reports
        ),
        "layers_enabled_count": sum(
            report.get("layers_enabled_count", 0)
            for report in task_performance_reports
        ),
        "layers_disabled_count": sum(
            report.get("layers_disabled_count", 0)
            for report in task_performance_reports
        ),
        "layers_deferred_count": sum(
            report.get("layers_deferred_count", 0)
            for report in task_performance_reports
        ),
        "full_stack_avoided": any(
            report.get("full_stack_avoided", False)
            for report in task_performance_reports
        ),
        "estimated_layers_skipped": sum(
            report.get("estimated_layers_skipped", 0)
            for report in task_performance_reports
        ),
        "skipped_reports_count": sum(
            report.get("skipped_reports_count", 0)
            for report in task_performance_reports
        ),
        "premature_reports_prevented": sum(
            report.get("premature_reports_prevented", 0)
            for report in task_performance_reports
        ),
        "active_compute_time_seconds": active_compute_time_seconds,
        "idle_time_seconds": metric_bridge["idle_time_seconds"],
        "startup_time_seconds": metric_bridge["startup_time_seconds"],
        "shutdown_time_seconds": metric_bridge["shutdown_time_seconds"],
        "task_execution_time_seconds":
        metric_bridge["task_execution_time_seconds"],
        "governance_time_seconds": metric_bridge["governance_time_seconds"],
        "dependency_reasoning_time_seconds":
        metric_bridge["dependency_reasoning_time_seconds"],
        "reasoning_time_seconds": metric_bridge["reasoning_time_seconds"],
        "truth_time_seconds": metric_bridge["truth_time_seconds"],
        "cache_time_seconds": metric_bridge["cache_time_seconds"],
        "reuse_time_seconds": metric_bridge["reuse_time_seconds"],
        "context_time_seconds": metric_bridge["context_time_seconds"],
        "memory_time_seconds": metric_bridge["memory_time_seconds"],
        "localization_time_seconds": metric_bridge["localization_time_seconds"],
        "evaluation_time_seconds": metric_bridge["evaluation_time_seconds"],
        "report_time_seconds": metric_bridge["report_time_seconds"],
        "process_generation_time": metric_bridge["process_generation_time"],
        "causal_generation_time": metric_bridge["causal_generation_time"],
        "finalization_time_seconds":
        metric_bridge["finalization_time_seconds"],
        "unattributed_runtime_seconds": round(
            max(0.0, total_runtime_seconds - active_compute_time_seconds),
            4,
        ),
        "telemetry_enabled": not args.disable_telemetry
        and args.mode != "fast",
        "report_level": args.report_level
        or {
            "fast": "minimal",
            "adaptive": "normal",
            "deep": "full",
        }.get(args.mode, "normal"),
        "slowest_modules": slowest_modules,
        "module_timings": module_timings,
        "metric_bridge": metric_bridge["metric_bridge"],
        "metric_source_warnings": metric_bridge["metric_source_warnings"],
        "canonical_metrics": canonical_metrics,
        "METRIC_RECONCILIATION_REPORT":
        metric_bridge.get("METRIC_RECONCILIATION_REPORT", {}),
        "METRIC_SOURCE_AUDIT": metric_bridge.get("METRIC_SOURCE_AUDIT", {}),
        "METRIC_CONFLICT_REPORT": metric_bridge.get(
            "METRIC_CONFLICT_REPORT",
            {},
        ),
        "METRIC_RECONCILIATION_WARNING":
        metric_bridge.get("METRIC_RECONCILIATION_WARNING", False),
    }
    reuse_total = (
        performance_report["cache_hits"]
        + performance_report["cache_misses"]
    )
    performance_report["reuse_rate"] = round(
        performance_report["cache_hits"] / reuse_total,
        4,
    ) if reuse_total else 0.0
    lifecycle_knowledge_reuse_report = concept_lifecycle_report.get(
        "knowledge_reuse_report",
        {},
    )
    lifecycle_truth_reuse_report = concept_lifecycle_report.get(
        "truth_reuse_report",
        {},
    )
    lifecycle_strategy_reuse_report = concept_lifecycle_report.get(
        "strategy_reuse_report",
        {},
    )
    lifecycle_counterfactual_reuse_report = concept_lifecycle_report.get(
        "counterfactual_reuse_report",
        {},
    )
    adaptive_reuse_reports = []
    for item in all_results:
        result = item.get("result", {}) if isinstance(item, dict) else {}
        if not isinstance(result, dict):
            continue
        for candidate in (
            result.get("ADAPTIVE_REUSE_REPORT"),
            result.get("adaptive_reuse_report"),
            result.get("performance_report", {}).get("adaptive_reuse_engine", {})
            if isinstance(result.get("performance_report"), dict)
            else {},
        ):
            if isinstance(candidate, dict) and candidate:
                adaptive_reuse_reports.append(candidate)

    def _nested_adaptive_report(report):
        if not isinstance(report, dict):
            return {}
        nested = report.get("ADAPTIVE_REUSE_REPORT", {})
        if isinstance(nested, dict) and nested:
            return nested
        nested = report.get("experience_reuse_report", {})
        if isinstance(nested, dict) and nested:
            return nested
        return report

    def _sum_adaptive_metric(metric_name):
        return sum(
            int(_metric_number(_nested_adaptive_report(report).get(metric_name)))
            for report in adaptive_reuse_reports
        )

    def _sum_adaptive_float(metric_name):
        return round(
            sum(
                _metric_number(
                    _nested_adaptive_report(report).get(metric_name),
                    0.0,
                )
                for report in adaptive_reuse_reports
            ),
            4,
        )

    adaptive_reuse_report = {
        "system": "adaptive_reuse_layer",
        "ADAPTIVE_REUSE_REPORT": True,
        "experience_count": max(
            [
                int(_metric_number(_nested_adaptive_report(report).get("experience_count")))
                for report in adaptive_reuse_reports
            ]
            or [0]
        ),
        "retrieval_attempts": _sum_adaptive_metric("retrieval_attempts"),
        "retrieval_successes": _sum_adaptive_metric("retrieval_successes"),
        "strategy_hits": _sum_adaptive_metric("strategy_hits"),
        "program_hits": _sum_adaptive_metric("program_hits"),
        "context_hits": _sum_adaptive_metric("context_hits"),
        "truth_hits": _sum_adaptive_metric("truth_hits"),
        "dependency_hits": max(
            _sum_adaptive_metric("dependency_hits"),
            _sum_adaptive_metric("dependency_snapshot_hits"),
        ),
        "cache_hits": _sum_adaptive_metric("cache_hits"),
        "cache_misses": _sum_adaptive_metric("cache_misses"),
        "experience_similarity": round(
            sum(
                _metric_number(
                    _nested_adaptive_report(report).get("experience_similarity"),
                    0.0,
                )
                for report in adaptive_reuse_reports
            )
            / max(len(adaptive_reuse_reports), 1),
            4,
        ),
        "adaptation_operations": sorted({
            operation
            for report in adaptive_reuse_reports
            for operation in (
                _nested_adaptive_report(report).get(
                    "adaptation_operations",
                    [],
                )
                or []
            )
        }),
        "reuse_failures": [
            failure
            for report in adaptive_reuse_reports
            for failure in (
                _nested_adaptive_report(report).get("reuse_failures", [])
                or []
            )
            if isinstance(failure, dict)
        ][:20],
        "estimated_runtime_saved": _sum_adaptive_float(
            "estimated_runtime_saved"
        ),
        "estimated_compute_saved": _sum_adaptive_float(
            "estimated_compute_saved"
        ),
        "knowledge_growth": next(
            (
                _nested_adaptive_report(report).get("knowledge_growth", {})
                for report in reversed(adaptive_reuse_reports)
                if isinstance(
                    _nested_adaptive_report(report).get(
                        "knowledge_growth",
                    ),
                    dict,
                )
            ),
            {},
        ),
    }
    adaptive_attempts = max(adaptive_reuse_report["retrieval_attempts"], 1)
    adaptive_reuse_report["reuse_success_rate"] = round(
        adaptive_reuse_report["retrieval_successes"] / adaptive_attempts,
        4,
    )
    performance_report.update({
        "context_hits": max(
            concept_lifecycle_report.get("context_hits", 0),
            lifecycle_knowledge_reuse_report.get("context_hits", 0),
            adaptive_reuse_report.get("context_hits", 0),
        ),
        "truth_hits": max(
            lifecycle_truth_reuse_report.get("truth_hits", 0),
            adaptive_reuse_report.get("truth_hits", 0),
        ),
        "strategy_hits": max(
            lifecycle_strategy_reuse_report.get(
                "strategy_hits",
                lifecycle_knowledge_reuse_report.get("strategy_hits", 0),
            ),
            adaptive_reuse_report.get("strategy_hits", 0),
        ),
        "program_hits": max(
            lifecycle_knowledge_reuse_report.get("program_hits", 0),
            adaptive_reuse_report.get("program_hits", 0),
        ),
        "context_misses": min(
            lifecycle_knowledge_reuse_report.get("context_misses", 0),
            adaptive_reuse_report.get("cache_misses", 0),
        ),
        "truth_misses": min(
            lifecycle_truth_reuse_report.get("truth_misses", 0),
            adaptive_reuse_report.get("cache_misses", 0),
        ),
        "strategy_misses": lifecycle_strategy_reuse_report.get(
            "strategy_misses",
            lifecycle_knowledge_reuse_report.get("strategy_misses", 0),
        ),
        "program_misses": min(
            lifecycle_knowledge_reuse_report.get("program_misses", 0),
            adaptive_reuse_report.get("cache_misses", 0),
        ),
        "cache_hits": max(
            performance_report.get("cache_hits", 0),
            adaptive_reuse_report.get("cache_hits", 0),
        ),
        "cache_misses": min(
            performance_report.get("cache_misses", 0),
            adaptive_reuse_report.get("cache_misses", 0),
        ),
        "estimated_runtime_saved": max(
            performance_report.get("estimated_runtime_saved", 0.0),
            adaptive_reuse_report.get("estimated_runtime_saved", 0.0),
        ),
        "estimated_compute_saved": max(
            performance_report.get("estimated_compute_saved", 0.0),
            adaptive_reuse_report.get("estimated_compute_saved", 0.0),
        ),
        "knowledge_reuse_rate":
        max(
            lifecycle_knowledge_reuse_report.get("knowledge_reuse_rate", 0.0),
            adaptive_reuse_report.get("reuse_success_rate", 0.0),
        ),
        "strategy_reuse_rate": lifecycle_strategy_reuse_report.get(
            "strategy_reuse_rate",
            adaptive_reuse_report.get("reuse_success_rate", 0.0),
        ),
        "ADAPTIVE_REUSE_REPORT": adaptive_reuse_report,
        "adaptive_reuse_report": adaptive_reuse_report,
        "adaptive_reuse_engine": adaptive_reuse_report,
        "counterfactual_hits": lifecycle_counterfactual_reuse_report.get(
            "counterfactual_hits",
            0,
        ),
        "counterfactual_misses": lifecycle_counterfactual_reuse_report.get(
            "counterfactual_misses",
            0,
        ),
        "counterfactual_reuse_rate":
        lifecycle_counterfactual_reuse_report.get(
            "counterfactual_reuse_rate",
            0.0,
        ),
        "counterfactual_success":
        lifecycle_counterfactual_reuse_report.get(
            "counterfactual_success",
            0,
        ),
        "context_count": concept_lifecycle_report.get("context_count", 0),
        "context_consumed": concept_lifecycle_report.get("context_consumed", 0),
        "truth_candidate_count":
        concept_lifecycle_report.get("truth_candidate_count", 0),
    })
    for metric_name in (
        "reasoning_depth",
        "active_routes",
        "strategy_hits",
        "truth_hits",
        "context_hits",
        "cache_hits",
        "cache_misses",
        "reuse_rate",
        "prediction_accuracy",
        "repair_success_rate",
        "process_context_count",
        "causal_context_count",
    ):
        if metric_name in canonical_metrics:
            if metric_name in {
                "strategy_hits",
                "truth_hits",
                "context_hits",
                "cache_hits",
                "cache_misses",
                "reuse_rate",
            }:
                performance_report[metric_name] = max(
                    _metric_number(performance_report.get(metric_name), 0.0),
                    _metric_number(canonical_metrics.get(metric_name), 0.0),
                )
            else:
                performance_report[metric_name] = canonical_metrics[metric_name]
    record_main_timing("assemble_performance_report", module_start)
    module_timings.append(main_module_timings[-1])
    slowest_modules = sorted(
        slowest_modules + [main_module_timings[-1]],
        key=lambda item: item.get("seconds", 0.0),
        reverse=True,
    )[:5]
    from runtime.performance.runtime_attribution_engine import (
        runtime_attribution_engine,
    )
    from runtime.dependency.dependency_visibility_engine import (
        dependency_visibility_engine,
    )

    module_start = time.perf_counter()
    dependency_visibility_report = dependency_visibility_engine.summarize(
        performance_report,
    )
    record_main_timing("dependency_visibility_report", module_start)
    module_timings.append(main_module_timings[-1])
    performance_report["dependency_visibility_report"] = (
        dependency_visibility_report
    )
    performance_report["dependency_chain_execution_time"] = (
        dependency_visibility_report["dependency_chain_execution_time"]
    )
    module_start = time.perf_counter()
    runtime_attribution_report = runtime_attribution_engine.build_report(
        total_runtime=total_runtime_seconds,
        performance_report=performance_report,
        runtime_metrics=runtime_metrics,
        module_timings=module_timings,
    )
    record_main_timing("runtime_attribution_report", module_start)
    module_timings.append(main_module_timings[-1])
    performance_report["runtime_attribution_report"] = (
        runtime_attribution_report
    )
    performance_report["runtime_breakdown"] = (
        runtime_attribution_report["runtime_breakdown"]
    )
    performance_report["attributed_runtime_seconds"] = (
        runtime_attribution_report["attributed_runtime"]
    )
    performance_report["unattributed_runtime_seconds"] = (
        runtime_attribution_report["unattributed_runtime"]
    )
    performance_report["untracked_runtime_seconds"] = (
        runtime_attribution_report["untracked_runtime"]
    )
    from runtime.performance.unattributed_runtime_detector import (
        unattributed_runtime_detector,
    )

    performance_report["unattributed_runtime_detector_report"] = (
        unattributed_runtime_detector.detect(
            runtime_attribution_report,
            {
                **runtime_metrics,
                **performance_report,
            },
        )
    )
    from runtime.profiling.performance_reporter import performance_reporter

    module_start = time.perf_counter()
    performance_intelligence_report = performance_reporter.build_report(
        runtime_context={
            "COGNITIVE_REUSE_REPORT": (
                pipeline.meta_supervisor.build_cognitive_reuse_report()
                if hasattr(pipeline, "meta_supervisor")
                else {}
            ),
            "knowledge_reuse_report": lifecycle_knowledge_reuse_report,
            "truth_reuse_report": lifecycle_truth_reuse_report,
            "strategy_reuse_report": lifecycle_strategy_reuse_report,
            "counterfactual_reuse_report":
            lifecycle_counterfactual_reuse_report,
            "hypotheses": concept_lifecycle_report.get("hypotheses", []),
            "counterfactuals": concept_lifecycle_report.get(
                "counterfactuals",
                [],
            ),
            "hypothesis_generation_report":
            concept_lifecycle_report.get("hypothesis_generation_report", {}),
            "counterfactual_reasoning_report":
            concept_lifecycle_report.get(
                "counterfactual_reasoning_report",
                {},
            ),
            "task_performance_intelligence_reports":
            task_performance_intelligence_reports,
        },
        performance_report=performance_report,
        profile_level=args.profile_level,
    )
    if isinstance(performance_intelligence_report, dict):
        cognitive_efficiency = performance_intelligence_report.setdefault(
            "cognitive_efficiency",
            {},
        )
        if isinstance(cognitive_efficiency, dict):
            for metric_name in ("reasoning_depth", "active_routes"):
                if metric_name in canonical_metrics:
                    cognitive_efficiency[metric_name] = (
                        canonical_metrics[metric_name]
                    )
        memory_efficiency = performance_intelligence_report.setdefault(
            "memory_efficiency",
            {},
        )
        if isinstance(memory_efficiency, dict):
            for metric_name in (
                "strategy_hits",
                "truth_hits",
                "context_hits",
                "reuse_rate",
                "cache_hits",
                "cache_misses",
            ):
                if metric_name in canonical_metrics:
                    memory_efficiency[metric_name] = (
                        canonical_metrics[metric_name]
                    )
        performance_intelligence_report[
            "METRIC_RECONCILIATION_REPORT"
        ] = performance_report.get("METRIC_RECONCILIATION_REPORT", {})
        performance_intelligence_report[
            "canonical_metrics"
        ] = canonical_metrics
    record_main_timing("performance_intelligence_report", module_start)
    module_timings.append(main_module_timings[-1])
    from runtime.reporting.report_budget_manager import report_budget_manager

    report_generation_cost = round(
        sum(
            item.get("seconds", 0.0)
            for item in main_module_timings
            if item.get("module") in {
                "concept_lifecycle_report",
                "build_training_report",
                "collect_task_performance_reports",
                "build_runtime_metric_bridge",
                "assemble_performance_report",
                "dependency_visibility_report",
                "runtime_attribution_report",
                "performance_intelligence_report",
            }
        ),
        4,
    )
    report_budget_report = report_budget_manager.evaluate(
        report_generation_cost,
        total_runtime_seconds,
        performance_report,
    )
    if args.mode in {"deep", "full"}:
        report_budget_report["report_budget_seconds"] = (
            deep_budget.max_report_time_seconds
        )
        report_budget_report["report_budget_exceeded"] = (
            deep_mode_budget_manager.report_budget_exceeded(
                report_generation_cost,
                deep_budget,
            )
        )
        report_budget_report["report_compression_required"] = (
            report_budget_report["report_budget_exceeded"]
        )
    performance_report.update({
        "report_generation_cost":
        report_budget_report["report_generation_cost"],
        "report_budget_usage": report_budget_report["report_budget_usage"],
        "report_compression_ratio":
        report_budget_report["report_compression_ratio"],
        "report_budget_exceeded":
        report_budget_report["report_budget_exceeded"],
        "report_budget_report": report_budget_report,
        "concept_lifecycle_cost": concept_lifecycle_elapsed,
        "concept_lifecycle_cache_hits":
        concept_lifecycle_report.get(
            "concept_lifecycle_cache_report",
            {},
        ).get("concept_lifecycle_cache_hits", 0),
    })
    runtime_metrics.update({
        "report_generation_cost":
        report_budget_report["report_generation_cost"],
        "report_budget_usage": report_budget_report["report_budget_usage"],
        "report_compression_ratio":
        report_budget_report["report_compression_ratio"],
        "concept_lifecycle_cost": concept_lifecycle_elapsed,
    })
    runtime_metrics["deep_budget"] = deep_budget.as_dict()

    def synchronize_training_report_metrics(
        training_report,
        performance_report,
        performance_intelligence_report,
    ):
        if not isinstance(training_report, dict):
            return training_report
        if isinstance(performance_report, dict):
            training_report["performance_report"] = performance_report
            reuse_authority = performance_report.get(
                "adaptive_reuse_engine",
                {},
            )
            if not isinstance(reuse_authority, dict):
                reuse_authority = {}
            for key in (
                "strategy_hits",
                "strategy_misses",
                "truth_hits",
                "truth_misses",
                "context_hits",
                "context_misses",
                "program_hits",
                "program_misses",
                "reuse_rate",
                "estimated_compute_saved",
                "estimated_runtime_saved",
            ):
                value = performance_report.get(key)
                if value is not None:
                    reuse_authority[key] = value
            performance_report["adaptive_reuse_engine"] = reuse_authority
            training_report["reuse_metric_authority"] = reuse_authority
            training_report["cache_metric_authority"] = {
                key: performance_report.get(key)
                for key in (
                    "cache_hits",
                    "cache_misses",
                    "cache_hit_rate",
                )
                if performance_report.get(key) is not None
            }
        if isinstance(performance_intelligence_report, dict):
            training_report["PERFORMANCE_REPORT"] = (
                performance_intelligence_report
            )
            training_report["performance_intelligence_report"] = (
                performance_intelligence_report
            )
            memory = performance_intelligence_report.get(
                "memory_efficiency",
                {},
            )
            if isinstance(memory, dict):
                training_report.setdefault(
                    "performance_report",
                    {},
                ).update({
                    key: value
                    for key, value in memory.items()
                    if key
                    in {
                        "strategy_hits",
                        "strategy_misses",
                        "truth_hits",
                        "truth_misses",
                        "context_hits",
                        "context_misses",
                        "program_hits",
                        "program_misses",
                        "reuse_rate",
                    }
                    and value is not None
                })
        return training_report

    training_report = synchronize_training_report_metrics(
        training_report,
        performance_report,
        performance_intelligence_report,
    )

    module_start = time.perf_counter()
    truth_candidate_report = collect_governance_reports(
        all_results,
        [
            "truth_candidate_report",
            "truth_candidates",
            "TRUTH CANDIDATE REPORT",
        ],
    )

    truth_commit_report = collect_governance_reports(
        all_results,
        [
            "truth_commit_report",
            "truth_commits",
            "TRUTH COMMIT REPORT",
        ],
    )

    contextual_truth_report = collect_governance_reports(
        all_results,
        [
            "contextual_truth_report",
            "contexts",
            "CONTEXTUAL TRUTH REPORT",
        ],
    )

    context_reuse_report = collect_governance_reports(
        all_results,
        [
            "context_reuse_report",
            "CONTEXT REUSE REPORT",
        ],
    )

    truth_registry_report = collect_governance_reports(
        all_results,
        [
            "truth_registry_report",
            "TRUTH REGISTRY REPORT",
        ],
    )

    truth_graveyard_consistency_report = collect_governance_reports(
        all_results,
        [
            "truth_graveyard_consistency",
            "truth_graveyard_consistency_report",
        ],
    )
    causal_context_report = collect_governance_reports(
        all_results,
        [
            "causal_context_report",
            "causal_context_runtime_report",
            "CAUSAL_CONTEXT_REPORT",
        ],
    )
    if not causal_context_report:
        def max_nested_metric(value, metric_name, depth=0):
            if depth > 8:
                return 0.0
            if isinstance(value, dict):
                candidates = [
                    _metric_number(value.get(metric_name), 0),
                ]
                candidates.extend(
                    max_nested_metric(item, metric_name, depth + 1)
                    for item in value.values()
                )
                return max(candidates or [0.0])
            if isinstance(value, list):
                return max(
                    (
                        max_nested_metric(item, metric_name, depth + 1)
                        for item in value
                    ),
                    default=0.0,
                )
            return 0.0

        def sum_marked_reports(value, marker_name, metric_name, depth=0):
            if depth > 8:
                return 0.0
            if isinstance(value, dict):
                if value.get(marker_name) is True:
                    return _metric_number(value.get(metric_name), 0)
                return sum(
                    sum_marked_reports(
                        item,
                        marker_name,
                        metric_name,
                        depth + 1,
                    )
                    for item in value.values()
                )
            if isinstance(value, list):
                return sum(
                    sum_marked_reports(
                        item,
                        marker_name,
                        metric_name,
                        depth + 1,
                    )
                    for item in value
                )
            return 0.0

        def collect_nested_causal_contexts(value, depth=0):
            if depth > 8:
                return []
            contexts = []
            if isinstance(value, dict):
                for key in ("causal_contexts", "generated_contexts"):
                    nested = value.get(key)
                    if isinstance(nested, list):
                        contexts.extend(
                            item for item in nested if isinstance(item, dict)
                        )
                for item in value.values():
                    contexts.extend(
                        collect_nested_causal_contexts(item, depth + 1)
                    )
            elif isinstance(value, list):
                for item in value:
                    contexts.extend(
                        collect_nested_causal_contexts(item, depth + 1)
                    )
            return contexts

        def unique_contexts(contexts):
            seen = set()
            unique = []
            for index, context in enumerate(contexts):
                key = (
                    context.get("context_id"),
                    context.get("cause"),
                    context.get("effect"),
                    context.get("causal_family"),
                    index if not context.get("cause") else "",
                )
                if key in seen:
                    continue
                seen.add(key)
                unique.append(context)
            return unique

        def relation_from_context(context, index):
            cause = str(context.get("cause") or context.get("root_cause") or "unknown_cause")
            effect = str(context.get("effect") or "unknown_effect")
            dependencies = [
                str(item)
                for item in (context.get("supporting_dependencies", []) or [])
                if item is not None
            ]
            processes = [
                str(item)
                for item in (context.get("supporting_processes", []) or [])
                if item is not None
            ]
            truths = [
                str(item)
                for item in (context.get("supporting_truths", []) or [])
                if item is not None
            ]
            confidence = round(float(
                context.get("confidence", context.get("causal_confidence", 0.0)) or 0.0
            ), 4)
            validation = context.get("validation", {})
            validated = (
                validation.get("causal_context_validated")
                if isinstance(validation, dict)
                else None
            )
            support_count = len([
                item for item in [
                    context.get("evidence"),
                    dependencies,
                    processes or context.get("supporting_process"),
                    truths,
                    validation,
                ]
                if item
            ])
            return {
                "relation_id": (
                    context.get("relation_id")
                    or f"causal_relation:fallback:{index}:{cause}->{effect}"
                ),
                "cause_id": cause,
                "effect_id": effect,
                "cause": cause,
                "effect": effect,
                "relation_type": str(
                    context.get("relation_type")
                    or context.get("causal_family")
                    or "causal_relation"
                ),
                "confidence": confidence,
                "support_count": support_count,
                "contradicting_evidence": list(context.get("contradictions", []) or []),
                "validation_status": (
                    "validated" if validated else "unvalidated"
                ),
                "evidence": context.get("evidence", {}),
                "temporal_order": int(context.get("temporal_order", index) or 0),
                "dependency_reference": (
                    context.get("dependency_source")
                    or ",".join(dependencies)
                ),
                "process_reference": (
                    context.get("process_source")
                    or context.get("supporting_process")
                    or ",".join(processes)
                ),
                "truth_reference": (
                    context.get("truth_source")
                    or ",".join(truths)
                ),
            }

        def chain_from_context(context):
            cause = str(context.get("cause") or context.get("root_cause") or "unknown_cause")
            effect = str(context.get("effect") or "unknown_effect")
            chain = (
                context.get("propagation_chain")
                or context.get("causal_chain")
                or [cause, effect]
            )
            chain = [str(item) for item in chain if item is not None and str(item)]
            if cause not in chain:
                chain.insert(0, cause)
            if effect not in chain:
                chain.append(effect)
            return list(dict.fromkeys(chain))

        def confidence_distribution(relations):
            distribution = {"high": 0, "medium": 0, "low": 0, "by_relation": {}}
            for relation in relations:
                confidence = float(relation.get("confidence", 0.0) or 0.0)
                if confidence >= 0.80:
                    distribution["high"] += 1
                elif confidence >= 0.60:
                    distribution["medium"] += 1
                else:
                    distribution["low"] += 1
                distribution["by_relation"][relation["relation_id"]] = round(confidence, 4)
            return distribution

        causal_context_count = int(max(
            _metric_number(performance_report.get("causal_context_count"), 0),
            _metric_number(training_report.get("causal_context_count"), 0),
            _metric_number(
                concept_lifecycle_report.get("causal_context_count"),
                0,
            ),
            max_nested_metric(all_results, "causal_context_count"),
            sum_marked_reports(
                all_results,
                "CAUSAL_CONTEXT_REPORT",
                "causal_context_count",
            ),
        ))
        dependency_chains = int(max(
            _metric_number(
                performance_report.get("dependency_chains_executed"),
                0,
            ),
            _metric_number(
                training_report.get("dependency_chains_executed"),
                0,
            ),
            _metric_number(
                concept_lifecycle_report.get("dependency_chains_executed"),
                0,
            ),
            max_nested_metric(all_results, "dependency_chains_executed"),
        ))
        process_context_count = int(max(
            _metric_number(performance_report.get("process_context_count"), 0),
            _metric_number(training_report.get("process_context_count"), 0),
            _metric_number(
                concept_lifecycle_report.get("process_context_count"),
                0,
            ),
            max_nested_metric(all_results, "process_context_count"),
        ))
        generated_contexts = unique_contexts(
            collect_nested_causal_contexts(all_results)
        )
        effective_causal_context_count = max(
            causal_context_count,
            len(generated_contexts),
        )
        cause_effect_pairs = [
            relation_from_context(context, index)
            for index, context in enumerate(generated_contexts)
            if context.get("cause") or context.get("effect") or context.get("root_cause")
        ]
        propagation_paths = [
            {
                "path_id": f"propagation_path:fallback:{index}",
                "root_cause": context.get("root_cause") or context.get("cause"),
                "observed_effect": context.get("effect"),
                "final_state": chain_from_context(context)[-1],
                "chain": chain_from_context(context),
                "chain_depth": len(chain_from_context(context)),
                "confidence": round(float(
                    context.get("confidence", context.get("causal_confidence", 0.0)) or 0.0
                ), 4),
            }
            for index, context in enumerate(generated_contexts)
        ]
        root_causes = list(dict.fromkeys(
            str(context.get("root_cause") or context.get("cause"))
            for context in generated_contexts
            if context.get("root_cause") or context.get("cause")
        ))
        secondary_causes = list(dict.fromkeys(
            str(dependency)
            for context in generated_contexts
            for dependency in (context.get("supporting_dependencies", []) or [])
            if str(dependency) not in root_causes
        ))
        average_chain_depth = round(
            sum(path["chain_depth"] for path in propagation_paths)
            / max(len(propagation_paths), 1),
            4,
        ) if propagation_paths else 0.0
        average_confidence = round(
            sum(pair["confidence"] for pair in cause_effect_pairs)
            / max(len(cause_effect_pairs), 1),
            4,
        ) if cause_effect_pairs else 0.0
        highest_confidence_relation = (
            max(cause_effect_pairs, key=lambda item: item["confidence"])
            if cause_effect_pairs else {}
        )
        lowest_confidence_relation = (
            min(cause_effect_pairs, key=lambda item: item["confidence"])
            if cause_effect_pairs else {}
        )
        graph_nodes = sorted({
            value
            for pair in cause_effect_pairs
            for value in (pair.get("cause_id"), pair.get("effect_id"))
            if value
        })
        graph_edge_count = len(cause_effect_pairs)
        possible_edges = len(graph_nodes) * max(len(graph_nodes) - 1, 0)
        causal_density = round(
            graph_edge_count / possible_edges,
            4,
        ) if possible_edges else 0.0
        causal_graph_statistics = {
            "node_count": len(graph_nodes),
            "edge_count": graph_edge_count,
            "relation_count": len(cause_effect_pairs),
            "average_out_degree": round(graph_edge_count / max(len(graph_nodes), 1), 4),
            "causal_density": causal_density,
            "cycles_detected": False,
        }
        block_reasons = []
        if effective_causal_context_count == 0:
            if dependency_chains <= 0:
                block_reasons.append("MISSING_DEPENDENCY_GRAPH")
            if process_context_count <= 0:
                block_reasons.append("MISSING_PROCESS_TRANSITIONS")
            if not block_reasons:
                block_reasons.append("NO_CAUSAL_PATTERN_FOUND")
        causal_context_report = {
            "system": "causal_context_runtime",
            "CAUSAL_CONTEXT_REPORT": True,
            "causal_runtime_called": causal_context_count > 0,
            "causal_generation_attempted": (
                dependency_chains > 0 or process_context_count > 0
            ),
            "causal_context_count": effective_causal_context_count,
            "causal_graph_count": effective_causal_context_count,
            "cause_effect_pairs": cause_effect_pairs,
            "causal_chain_depth": (
                max(
                    _metric_number(performance_report.get("dependency_chain_depth", 0), 0),
                    average_chain_depth,
                )
            ),
            "root_causes": root_causes,
            "secondary_causes": secondary_causes,
            "propagation_paths": propagation_paths,
            "generated_contexts": generated_contexts or causal_context_count,
            "blocked_contexts": 1 if block_reasons else 0,
            "block_reasons": block_reasons,
            "generation_time": 0.0,
            "confidence_distribution": confidence_distribution(cause_effect_pairs),
            "causal_relation_count": len(cause_effect_pairs),
            "average_chain_depth": average_chain_depth,
            "average_confidence": average_confidence,
            "highest_confidence_relation": highest_confidence_relation,
            "lowest_confidence_relation": lowest_confidence_relation,
            "causal_density": causal_density,
            "causal_graph_statistics": causal_graph_statistics,
            "generation_summary": (
                f"Generated {effective_causal_context_count} causal contexts."
                if effective_causal_context_count > 0
                else {
                    "state": "CAUSAL_CONTEXT_BLOCKED",
                    "reasons": block_reasons,
                }
            ),
        }
    cognitive_capability_report = collect_governance_reports(
        all_results,
        [
            "cognitive_capability_report",
            "COGNITIVE_CAPABILITY_REPORT",
        ],
    )
    if not cognitive_capability_report:
        from runtime.capabilities import cognitive_capability_orchestrator

        cognitive_capability_report = (
            cognitive_capability_orchestrator.build_report(
                runtime_context={
                    "truth_commitments": truth_commit_report.get(
                        "committed_truths",
                        [],
                    ),
                    "reusable_truth_commitments": truth_registry_report.get(
                        "truths",
                        [],
                    ),
                    "adaptive_reuse_report": adaptive_reuse_report,
                },
                reports={
                    "adaptive_reuse_report": adaptive_reuse_report,
                    "causal_context_runtime_report": causal_context_report,
                    "context_reuse_report": context_reuse_report,
                    "truth_commit_report": truth_commit_report,
                    "truth_registry_report": truth_registry_report,
                },
            )
        )
    record_main_timing("collect_governance_reports", module_start)
    module_timings.append(main_module_timings[-1])
    discovery_only_truth_mode = False
    if discovery_only_truth_mode:
        truth_candidate_report = {}
        truth_commit_report = {}

    module_start = time.perf_counter()
    concepts = normalize_concept_diagnostics(training_report)
    truth_candidates = normalize_truth_candidates(training_report)
    truth_commits = training_report.get("truth_commit_evaluations", {})
    contexts = normalize_context_diagnostics(training_report)
    from runtime.dependency.dependency_injection_audit import (
        dependency_injection_audit,
    )
    from runtime.context.context_validation_engine import (
        context_validation_engine,
    )

    dependency_audit_report = dependency_injection_audit.audit(
        truth_candidate_report.get("evaluations", [])
        if isinstance(truth_candidate_report, dict)
        else concepts
    )
    context_validation_report = {
        "system": "context_validation_batch",
        "context_count": len(contexts),
        "reports": [
            context_validation_engine.validate(context)
            for context in contexts.values()
        ],
    }
    layers_requested = sorted({
        layer
        for report in task_performance_reports
        for layer in (
            report.get("pre_reasoning_execution_plan", {})
            if isinstance(report.get("pre_reasoning_execution_plan"), dict)
            else {}
        ).get("required_layers", [])
    })
    layers_executed = sorted({
        layer
        for report in task_performance_reports
        for layer in (
            report.get("pre_reasoning_execution_plan", {})
            if isinstance(report.get("pre_reasoning_execution_plan"), dict)
            else {}
        ).get("enabled_layers", [])
    })
    layers_deferred = sorted({
        layer
        for report in task_performance_reports
        for layer in (
            report.get("pre_reasoning_execution_plan", {})
            if isinstance(report.get("pre_reasoning_execution_plan"), dict)
            else {}
        ).get("deferred_layers", [])
    })
    reports_generated = [
        "training_report",
        "performance_report",
        "runtime_attribution_report",
        "performance_intelligence_report",
        "cognitive_analytics_report",
        "reasoning_intelligence_report",
    ]
    reports_skipped = []
    if args.mode in {"deep", "full"} and not deep_concept_audit_requested:
        reports_skipped.append("expanded_concept_lifecycle_report")
    if args.mode in {"deep", "full"} and not deep_mode_budget_manager.should_expand(
        "truth",
        deep_audit_flags,
    ):
        reports_skipped.append("expanded_truth_evaluations")
    if report_budget_report.get("report_compression_required"):
        reports_skipped.append("unbounded_full_report_expansion")
    deep_mode_optimization_report = deep_mode_budget_manager.build_report(
        mode=args.mode,
        deep_budget=deep_budget,
        audit_flags=deep_audit_flags,
        layers_requested=layers_requested,
        layers_executed=layers_executed,
        layers_deferred=layers_deferred,
        reports_generated=reports_generated,
        reports_skipped=reports_skipped,
        concepts_recomputed=concepts_recomputed,
        concepts_reused=concepts_reused,
        elapsed={
            "total_runtime_seconds": total_runtime_seconds,
            "report_generation_seconds": report_generation_cost,
            "concept_lifecycle_seconds": concept_lifecycle_elapsed,
            "task_runtime_seconds": runtime_metrics.get(
                "task_execution_time_seconds",
                0.0,
            ),
        },
        task_budget_exceeded=runtime_metrics.get(
            "task_budget_exceeded",
            False,
        ),
    )
    performance_report["DEEP_MODE_OPTIMIZATION_REPORT"] = (
        deep_mode_optimization_report
    )
    from runtime.analytics import (
        cognitive_analytics_builder,
        reasoning_intelligence_builder,
    )

    cognitive_analytics_report = cognitive_analytics_builder.build_report(
        task_count=len(all_results),
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
        all_results=all_results,
        training_report=training_report,
        concept_lifecycle_report=concept_lifecycle_report,
        performance_report=performance_report,
        cognitive_capability_report=cognitive_capability_report,
        causal_context_report=causal_context_report,
        adaptive_reuse_report=adaptive_reuse_report,
        context_validation_report=context_validation_report,
    )
    performance_report["COGNITIVE_ANALYTICS_REPORT"] = (
        cognitive_analytics_report
    )
    reasoning_intelligence_report = (
        reasoning_intelligence_builder.build_report(
            cognitive_analytics_report=cognitive_analytics_report,
            all_results=all_results,
            performance_report=performance_report,
            cognitive_capability_report=cognitive_capability_report,
            causal_context_report=causal_context_report,
            adaptive_reuse_report=adaptive_reuse_report,
            context_validation_report=context_validation_report,
        )
    )
    performance_report["REASONING_INTELLIGENCE_REPORT"] = (
        reasoning_intelligence_report
    )
    from runtime.reasoning import reasoning_graph_report_builder

    reasoning_graph_report = reasoning_graph_report_builder.build_report(
        cognitive_analytics_report=cognitive_analytics_report,
        reasoning_intelligence_report=reasoning_intelligence_report,
        all_results=all_results,
        training_report=training_report,
        performance_report=performance_report,
        cognitive_capability_report=cognitive_capability_report,
        causal_context_report=causal_context_report,
        adaptive_reuse_report=adaptive_reuse_report,
        context_validation_report=context_validation_report,
        dependency_audit_report=dependency_audit_report,
    )
    performance_report["REASONING_GRAPH_REPORT"] = reasoning_graph_report
    from runtime.analytics import reasoning_quality_analytics_builder

    reasoning_analytics_report = (
        reasoning_quality_analytics_builder.build_report(
            reasoning_graph_report=reasoning_graph_report,
            reasoning_intelligence_report=reasoning_intelligence_report,
            cognitive_analytics_report=cognitive_analytics_report,
            performance_report=performance_report,
            cognitive_capability_report=cognitive_capability_report,
            causal_context_report=causal_context_report,
            adaptive_reuse_report=adaptive_reuse_report,
            dependency_audit_report=dependency_audit_report,
            context_validation_report=context_validation_report,
            all_results=all_results,
        )
    )
    performance_report["REASONING_ANALYTICS_REPORT"] = (
        reasoning_analytics_report
    )
    from runtime.analytics import meta_cognitive_optimizer

    meta_cognitive_report = meta_cognitive_optimizer.build_report(
        reasoning_graph_report=reasoning_graph_report,
        reasoning_analytics_report=reasoning_analytics_report,
        reasoning_intelligence_report=reasoning_intelligence_report,
        cognitive_analytics_report=cognitive_analytics_report,
        performance_report=performance_report,
        cognitive_capability_report=cognitive_capability_report,
        causal_context_report=causal_context_report,
        dependency_audit_report=dependency_audit_report,
        adaptive_reuse_report=adaptive_reuse_report,
        all_results=all_results,
    )
    performance_report["META_COGNITIVE_REPORT"] = meta_cognitive_report
    from runtime import solver_intelligence_report, solver_reasoning_report
    from runtime.cognitive_pipeline import build_cognitive_pipeline_report
    from runtime.concepts import concept_formation_engine
    from runtime.search import (
        adaptive_search_intelligence_engine,
        adaptive_cognitive_super_cooling_engine,
        build_cognitive_search_report,
        cognitive_route_intelligence_engine,
    )
    from runtime.knowledge import cognitive_knowledge_integration_layer
    from runtime.evidence import evidence_builder_runtime
    from runtime.synthesis import program_synthesis_intelligence_engine
    from runtime.cognitive_runtime import cognitive_runtime_execution_engine

    cognitive_runtime_execution_engine.clear()
    shared_cognitive_state = SharedCognitiveState.create(
        execution_profile=execution_profile.as_runtime_metadata(),
        mode=args.mode,
        inherit_latest=args.mode in {"deep", "full"},
    )
    knowledge_bus = CognitiveKnowledgeBus(shared_cognitive_state)
    performance_report["shared_cognitive_state_inherited_counts"] = (
        shared_cognitive_state.counts()
    )
    shared_cognitive_state.snapshot("runtime_initialization")

    def consume_shared_state(runtime_id, artifact_types, required=()):
        consumption = knowledge_bus.consume(
            runtime_id,
            artifact_types,
            required=required,
        )
        performance_report.setdefault(
            "knowledge_bus_consumption",
            [],
        ).append(consumption["event"])
        performance_report.setdefault(
            "shared_cognitive_state_inputs",
            {},
        )[runtime_id] = {
            key: {"count": len(value)}
            for key, value in consumption["artifacts"].items()
        }
        return consumption["artifacts"]

    def publish_shared_state(runtime_id, payload, owner, stage_name, required=()):
        validation = shared_cognitive_state.validate_before(
            runtime_id,
            required=required,
        )
        performance_report.setdefault(
            "shared_cognitive_state_validation",
            [],
        ).append(validation)
        event = knowledge_bus.publish(
            runtime_id,
            payload,
            owner=owner,
            context=performance_report,
        )
        snapshot = shared_cognitive_state.snapshot(stage_name)
        performance_report.setdefault(
            "shared_cognitive_state_propagation",
            [],
        ).append(event)
        performance_report.setdefault(
            "shared_cognitive_state_snapshots",
            [],
        ).append(snapshot)
        return event

    cognitive_runtime_execution_engine.start_cycle(
        mode=args.mode,
        context={"report_level": args.report_level or "normal"},
    )

    with cognitive_runtime_execution_engine.execution(
        "reasoning_runtime",
        mode=args.mode,
        trigger="reasoning_report_generation",
        reason="materialize reasoning runtime execution",
    ) as reasoning_execution:
        solver_intelligence_report_payload = (
            solver_intelligence_report.build_report(
                all_results=all_results,
                performance_report=performance_report,
                cognitive_capability_report=cognitive_capability_report,
            )
        )
        performance_report["SOLVER_INTELLIGENCE_REPORT"] = (
            solver_intelligence_report_payload
        )
        solver_reasoning_report_payload = solver_reasoning_report.build_report(
            all_results=all_results,
            solver_intelligence_report=solver_intelligence_report_payload,
            performance_report=performance_report,
            cognitive_capability_report=cognitive_capability_report,
            causal_context_report=causal_context_report,
            dependency_audit_report=dependency_audit_report,
            adaptive_reuse_report=adaptive_reuse_report,
        )
        reasoning_execution.capture(solver_reasoning_report_payload)
        publish_shared_state(
            "reasoning_runtime",
            solver_reasoning_report_payload,
            owner="reasoning_runtime",
            stage_name="reasoning_runtime",
        )
    performance_report["SOLVER_REASONING_REPORT"] = (
        solver_reasoning_report_payload
    )
    cognitive_pipeline_report = build_cognitive_pipeline_report(
        all_results=all_results,
        performance_report=performance_report,
    )
    performance_report["COGNITIVE_PIPELINE_REPORT"] = cognitive_pipeline_report
    with cognitive_runtime_execution_engine.execution(
        "search_runtime",
        mode=args.mode,
        trigger="cognitive_search_report_generation",
        reason="materialize adaptive search runtime execution",
    ) as search_execution:
        performance_report["search_execution_id"] = (
            search_execution.execution_id
        )
        cognitive_search_report = build_cognitive_search_report(
            all_results=all_results,
            cognitive_pipeline_report=cognitive_pipeline_report,
            solver_reasoning_report=solver_reasoning_report_payload,
            performance_report=performance_report,
            adaptive_reuse_report=adaptive_reuse_report,
            dependency_report=dependency_audit_report,
            causal_context_report=causal_context_report,
        )
        search_execution.capture(cognitive_search_report)
        publish_shared_state(
            "search_runtime",
            cognitive_search_report,
            owner="search_runtime",
            stage_name="adaptive_search",
            required=("reasoning_context",),
        )
    performance_report["COGNITIVE_SEARCH_REPORT"] = cognitive_search_report
    adaptive_search_policy_report = cognitive_search_report.get(
        "ADAPTIVE_SEARCH_POLICY_REPORT",
        {},
    )
    performance_report["adaptive_search_policy_report"] = (
        adaptive_search_policy_report
    )
    performance_report["ADAPTIVE_SEARCH_POLICY_REPORT"] = (
        adaptive_search_policy_report
    )
    cognitive_route_intelligence_report = cognitive_search_report.get(
        "COGNITIVE_ROUTE_INTELLIGENCE_REPORT",
        {},
    )
    performance_report["cognitive_route_intelligence_report"] = (
        cognitive_route_intelligence_report
    )
    performance_report["COGNITIVE_ROUTE_INTELLIGENCE_REPORT"] = (
        cognitive_route_intelligence_report
    )
    with cognitive_runtime_execution_engine.execution(
        "concept_formation_runtime",
        mode=args.mode,
        trigger="cognitive_concept_formation",
        reason="materialize canonical cognitive concept formation",
    ) as concept_execution:
        concept_formation_report = concept_formation_engine.build_report(
            all_results=all_results,
            performance_report=performance_report,
            cognitive_pipeline_report=cognitive_pipeline_report,
            cognitive_search_report=cognitive_search_report,
            solver_reasoning_report=solver_reasoning_report_payload,
            truth_report=truth_candidate_report,
            memory_report=adaptive_reuse_report,
            dependency_report=dependency_audit_report,
            causal_report=causal_context_report,
            lifecycle_report=concept_lifecycle_report,
            report_level=args.report_level or "normal",
        )
        concept_execution.capture(concept_formation_report)
        publish_shared_state(
            "concept_formation_runtime",
            concept_formation_report,
            owner="concept_formation_runtime",
            stage_name="concept_formation",
            required=("reasoning_context", "search_routes"),
        )
    performance_report["CONCEPT_FORMATION_REPORT"] = concept_formation_report
    performance_report["concept_formation_report"] = concept_formation_report
    performance_report["generated_concepts"] = concept_formation_report.get(
        "generated_concepts",
        0,
    )
    performance_report["concept_count"] = concept_formation_report.get(
        "concept_count",
        0,
    )
    performance_report["concept_cost"] = concept_formation_report.get(
        "concept_cost",
        0,
    )
    performance_report["confidence"] = max(
        float(performance_report.get("confidence", 0) or 0),
        float(concept_formation_report.get("confidence", 0) or 0),
    )
    performance_report["concept_graph"] = concept_formation_report.get(
        "concept_graph",
        {},
    )
    training_report["CONCEPT_FORMATION_REPORT"] = concept_formation_report
    training_report["generated_concepts"] = concept_formation_report.get(
        "generated_concepts",
        0,
    )
    program_shared_inputs = consume_shared_state(
        "program_synthesis_runtime",
        ("concept_store", "context_store", "evidence_store"),
        required=("concept_store",),
    )
    with cognitive_runtime_execution_engine.execution(
        "program_synthesis_runtime",
        mode=args.mode,
        trigger="program_synthesis_intelligence",
        reason="materialize concept-derived program synthesis",
    ) as program_execution:
        program_synthesis_report = (
            program_synthesis_intelligence_engine.build_report(
                concept_formation_report=concept_formation_report,
                cognitive_search_report=cognitive_search_report,
                solver_reasoning_report=solver_reasoning_report_payload,
                dependency_report=dependency_audit_report,
                causal_report=causal_context_report,
                memory_report=adaptive_reuse_report,
                all_results=all_results,
                report_level=args.report_level or "normal",
            )
        )
        program_execution.capture(program_synthesis_report)
        publish_shared_state(
            "program_synthesis_runtime",
            program_synthesis_report,
            owner="program_synthesis_runtime",
            stage_name="program_synthesis",
            required=("concept_store",),
        )
    performance_report["PROGRAM_SYNTHESIS_REPORT"] = (
        program_synthesis_report
    )
    performance_report["program_synthesis_report"] = (
        program_synthesis_report
    )
    performance_report["generated_programs"] = (
        program_synthesis_report.get("generated_programs", 0)
    )
    performance_report["program_candidates"] = (
        program_synthesis_report.get("program_candidates", 0)
    )
    training_report["PROGRAM_SYNTHESIS_REPORT"] = (
        program_synthesis_report
    )
    training_report["generated_programs"] = (
        program_synthesis_report.get("generated_programs", 0)
    )
    adaptive_search_shared_inputs = consume_shared_state(
        "adaptive_search_intelligence_runtime",
        ("concept_store", "program_store", "evidence_store", "context_store"),
        required=("concept_store", "program_store"),
    )
    with cognitive_runtime_execution_engine.execution(
        "adaptive_search_intelligence_runtime",
        mode=args.mode,
        trigger="adaptive_search_intelligence",
        reason="optimize search strategy from concept and program evidence",
    ) as search_intelligence_execution:
        adaptive_search_intelligence_report = (
            adaptive_search_intelligence_engine.build_report(
                cognitive_search_report=cognitive_search_report,
                adaptive_search_policy_report=adaptive_search_policy_report,
                cognitive_route_intelligence_report=(
                    cognitive_route_intelligence_report
                ),
                concept_formation_report=concept_formation_report,
                program_synthesis_report=program_synthesis_report,
                truth_report=truth_candidate_report,
                memory_report=adaptive_reuse_report,
                dependency_report=dependency_audit_report,
                causal_report=causal_context_report,
                all_results=all_results,
                report_level=args.report_level or "normal",
            )
        )
        search_intelligence_execution.capture(
            adaptive_search_intelligence_report,
        )
        publish_shared_state(
            "adaptive_search_intelligence_runtime",
            adaptive_search_intelligence_report,
            owner="adaptive_search_intelligence_runtime",
            stage_name="adaptive_search_intelligence",
            required=("concept_store", "program_store"),
        )
    performance_report["ADAPTIVE_SEARCH_INTELLIGENCE_REPORT"] = (
        adaptive_search_intelligence_report
    )
    performance_report["adaptive_search_intelligence_report"] = (
        adaptive_search_intelligence_report
    )
    training_report["ADAPTIVE_SEARCH_INTELLIGENCE_REPORT"] = (
        adaptive_search_intelligence_report
    )
    cognitive_route_intelligence_report = (
        cognitive_route_intelligence_engine.build_report(
            routes=cognitive_search_report.get("route_ranking", []),
            search_policy_report=adaptive_search_policy_report,
            adaptive_search_intelligence_report=(
                adaptive_search_intelligence_report
            ),
            concept_formation_report=concept_formation_report,
            program_synthesis_report=program_synthesis_report,
            truth_report=truth_candidate_report,
            memory_report=adaptive_reuse_report,
            search_report=cognitive_search_report,
            performance_report=performance_report,
        )
    )
    performance_report["COGNITIVE_ROUTE_INTELLIGENCE_REPORT"] = (
        cognitive_route_intelligence_report
    )
    performance_report["cognitive_route_intelligence_report"] = (
        cognitive_route_intelligence_report
    )
    training_report["COGNITIVE_ROUTE_INTELLIGENCE_REPORT"] = (
        cognitive_route_intelligence_report
    )
    with cognitive_runtime_execution_engine.execution(
        "acsc_runtime",
        mode=args.mode,
        trigger="adaptive_cognitive_super_cooling",
        reason="allocate cognitive resources from route intelligence",
    ) as acsc_execution:
        acsc_report = adaptive_cognitive_super_cooling_engine.build_report(
            cognitive_route_intelligence_report=(
                cognitive_route_intelligence_report
            ),
            adaptive_search_intelligence_report=(
                adaptive_search_intelligence_report
            ),
            concept_formation_report=concept_formation_report,
            program_synthesis_report=program_synthesis_report,
            performance_report=performance_report,
            report_level=args.report_level or "normal",
        )
        acsc_execution.capture(acsc_report)
        publish_shared_state(
            "acsc_runtime",
            acsc_report,
            owner="acsc_runtime",
            stage_name="adaptive_cognitive_super_cooling",
            required=("search_routes",),
        )
    performance_report["ACSC_REPORT"] = acsc_report
    performance_report["acsc_report"] = acsc_report
    training_report["ACSC_REPORT"] = acsc_report
    evidence_builder_shared_inputs = consume_shared_state(
        "evidence_builder_runtime",
        (
            "concept_store",
            "program_store",
            "search_routes",
            "context_store",
            "dependency_graph",
        ),
        required=("concept_store", "program_store", "search_routes"),
    )
    with cognitive_runtime_execution_engine.execution(
        "evidence_builder_runtime",
        mode=args.mode,
        trigger="evidence_builder_runtime",
        reason="normalize cognitive observations into canonical evidence",
    ) as evidence_builder_execution:
        evidence_architecture_report = evidence_builder_runtime.build_report(
            concept_formation_report=concept_formation_report,
            program_synthesis_report=program_synthesis_report,
            adaptive_search_intelligence_report=(
                adaptive_search_intelligence_report
            ),
            cognitive_route_intelligence_report=(
                cognitive_route_intelligence_report
            ),
            dependency_report=dependency_audit_report,
            context_report={
                "causal_context_report": causal_context_report,
                "shared_state_inputs": evidence_builder_shared_inputs,
            },
            shared_state=shared_cognitive_state.to_dict(),
            execution_id=evidence_builder_execution.execution_id,
        )
        evidence_builder_execution.capture(evidence_architecture_report)
        publish_shared_state(
            "evidence_builder_runtime",
            evidence_architecture_report,
            owner="evidence_builder_runtime",
            stage_name="evidence_builder",
            required=("concept_store", "program_store", "search_routes"),
        )
    performance_report["EVIDENCE_ARCHITECTURE_REPORT"] = (
        evidence_architecture_report
    )
    performance_report["evidence_architecture_report"] = (
        evidence_architecture_report
    )
    training_report["EVIDENCE_ARCHITECTURE_REPORT"] = (
        evidence_architecture_report
    )
    knowledge_shared_inputs = consume_shared_state(
        "knowledge_integration_runtime",
        (
            "concept_store",
            "program_store",
            "search_routes",
            "evidence_store",
            "context_store",
            "dependency_graph",
        ),
        required=("concept_store", "program_store", "search_routes", "evidence_store"),
    )
    with cognitive_runtime_execution_engine.execution(
        "knowledge_integration_runtime",
        mode=args.mode,
        trigger="cognitive_knowledge_integration",
        reason="circulate cognitive artifacts through the unified knowledge bus",
    ) as knowledge_integration_execution:
        cognitive_knowledge_integration_report = (
            cognitive_knowledge_integration_layer.build_report(
                concept_formation_report=concept_formation_report,
                program_synthesis_report=program_synthesis_report,
                adaptive_search_intelligence_report=(
                    adaptive_search_intelligence_report
                ),
                cognitive_route_intelligence_report=(
                    cognitive_route_intelligence_report
                ),
                evidence_architecture_report=evidence_architecture_report,
                truth_report=truth_candidate_report,
                memory_report=adaptive_reuse_report,
                reasoning_report=solver_reasoning_report_payload,
                acsc_report=acsc_report,
                all_results=all_results,
                performance_report=performance_report,
                report_level=args.report_level or "normal",
            )
        )
        knowledge_integration_execution.capture(
            cognitive_knowledge_integration_report,
        )
        publish_shared_state(
            "knowledge_integration_runtime",
            cognitive_knowledge_integration_report,
            owner="knowledge_integration_runtime",
            stage_name="knowledge_integration",
            required=("concept_store", "program_store", "search_routes"),
        )
    performance_report["COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT"] = (
        cognitive_knowledge_integration_report
    )
    performance_report["cognitive_knowledge_integration_report"] = (
        cognitive_knowledge_integration_report
    )
    training_report["COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT"] = (
        cognitive_knowledge_integration_report
    )
    truth_shared_inputs = consume_shared_state(
        "truth_runtime",
        (
            "knowledge_objects",
            "evidence_store",
            "context_store",
            "dependency_graph",
        ),
        required=("knowledge_objects", "evidence_store", "context_store"),
    )
    publish_shared_state(
        "truth_runtime",
        {
            "truth_candidates": truth_candidates,
            "truth_commits": truth_commits,
            "shared_state_inputs": truth_shared_inputs,
            **(
                truth_candidate_report
                if isinstance(truth_candidate_report, dict)
                else {}
            ),
        },
        owner="truth_runtime",
        stage_name="truth_runtime",
        required=("knowledge_objects", "evidence_store", "context_store"),
    )
    memory_shared_inputs = consume_shared_state(
        "memory_runtime",
        (
            "validated_truths",
            "truth_candidates",
            "knowledge_objects",
            "evidence_store",
            "context_store",
        ),
        required=("truth_candidates", "knowledge_objects", "evidence_store"),
    )
    publish_shared_state(
        "memory_runtime",
        {
            **(
                adaptive_reuse_report
                if isinstance(adaptive_reuse_report, dict)
                else {}
            ),
            "shared_state_inputs": memory_shared_inputs,
        },
        owner="memory_runtime",
        stage_name="memory_runtime",
        required=("truth_candidates", "knowledge_objects", "evidence_store"),
    )
    artifact_governance_report = shared_cognitive_state.run_artifact_governance()
    performance_report["ARTIFACT_GOVERNANCE_REPORT"] = artifact_governance_report
    performance_report["ARTIFACT_FLOW_REPORT"] = artifact_governance_report.get(
        "flow",
        {},
    )
    training_report["ARTIFACT_GOVERNANCE_REPORT"] = artifact_governance_report
    training_report["ARTIFACT_FLOW_REPORT"] = artifact_governance_report.get(
        "flow",
        {},
    )
    shared_state_save_report = shared_cognitive_state.save()
    shared_cognitive_state_report = shared_cognitive_state.build_report()
    cognitive_observability_report = shared_cognitive_state_report.get(
        "cognitive_observability",
        {},
    )
    knowledge_propagation_report = knowledge_bus.report()
    performance_report["SHARED_COGNITIVE_STATE_REPORT"] = (
        shared_cognitive_state_report
    )
    performance_report["KNOWLEDGE_PROPAGATION_REPORT"] = (
        knowledge_propagation_report
    )
    performance_report["shared_cognitive_state_report"] = (
        shared_cognitive_state_report
    )
    performance_report["knowledge_propagation_report"] = (
        knowledge_propagation_report
    )
    performance_report["shared_cognitive_state_save_report"] = (
        shared_state_save_report
    )
    performance_report["COGNITIVE_OBSERVABILITY_REPORT"] = (
        cognitive_observability_report
    )
    performance_report["cognitive_observability_report"] = (
        cognitive_observability_report
    )
    training_report["SHARED_COGNITIVE_STATE_REPORT"] = (
        shared_cognitive_state_report
    )
    training_report["KNOWLEDGE_PROPAGATION_REPORT"] = (
        knowledge_propagation_report
    )
    training_report["COGNITIVE_OBSERVABILITY_REPORT"] = (
        cognitive_observability_report
    )

    results = {
        "multi_task_results": all_results,
        "tasks_discovered": len(discovered_task_files),
        "discovered_task_files": discovered_task_files,
        "training_assistant_batch": training_batch,
        "training_assistant_report": training_assistant_report,
        "training_report": training_report,
        "performance_report": performance_report,
        "PERFORMANCE_REPORT": performance_intelligence_report,
        "performance_intelligence_report": performance_intelligence_report,
        "tasks_executed": len(all_results),
        "successful_tasks": successful_tasks,
        "failed_tasks": failed_tasks,
        "incomplete_tasks": incomplete_tasks,

        # Diagnostics bridge
        "concepts": concepts,
        "truth_candidates": truth_candidates,
        "truth_commits": truth_commits,
        "contexts": contexts,
        "ledger_report": ledger_report,
        "concept_lifecycle_report": concept_lifecycle_report,
        "truth_candidate_report": truth_candidate_report,
        "dependency_injection_audit": dependency_audit_report,
        "DEPENDENCY INJECTION AUDIT": dependency_audit_report,
        "context_injection_audit":
        concept_lifecycle_report.get("context_injection_audit", {}),
        "CONTEXT INJECTION AUDIT":
        concept_lifecycle_report.get("context_injection_audit", {}),
        "knowledge_flow_report":
        concept_lifecycle_report.get("knowledge_flow_report", {}),
        "KNOWLEDGE FLOW REPORT":
        concept_lifecycle_report.get("knowledge_flow_report", {}),
        "knowledge_reuse_report": lifecycle_knowledge_reuse_report,
        "KNOWLEDGE REUSE REPORT": lifecycle_knowledge_reuse_report,
        "adaptive_reuse_report": adaptive_reuse_report,
        "ADAPTIVE_REUSE_REPORT": adaptive_reuse_report,
        "cognitive_capability_report": cognitive_capability_report,
        "COGNITIVE_CAPABILITY_REPORT": cognitive_capability_report,
        "cognitive_analytics_report": cognitive_analytics_report,
        "COGNITIVE_ANALYTICS_REPORT": cognitive_analytics_report,
        "reasoning_intelligence_report": reasoning_intelligence_report,
        "REASONING_INTELLIGENCE_REPORT": reasoning_intelligence_report,
        "reasoning_graph_report": reasoning_graph_report,
        "REASONING_GRAPH_REPORT": reasoning_graph_report,
        "reasoning_analytics_report": reasoning_analytics_report,
        "REASONING_ANALYTICS_REPORT": reasoning_analytics_report,
        "meta_cognitive_report": meta_cognitive_report,
        "META_COGNITIVE_REPORT": meta_cognitive_report,
        "solver_intelligence_report": solver_intelligence_report_payload,
        "SOLVER_INTELLIGENCE_REPORT": solver_intelligence_report_payload,
        "solver_reasoning_report": solver_reasoning_report_payload,
        "SOLVER_REASONING_REPORT": solver_reasoning_report_payload,
        "cognitive_pipeline_report": cognitive_pipeline_report,
        "COGNITIVE_PIPELINE_REPORT": cognitive_pipeline_report,
        "cognitive_search_report": cognitive_search_report,
        "COGNITIVE_SEARCH_REPORT": cognitive_search_report,
        "adaptive_search_policy_report": adaptive_search_policy_report,
        "ADAPTIVE_SEARCH_POLICY_REPORT": adaptive_search_policy_report,
        "cognitive_route_intelligence_report":
        cognitive_route_intelligence_report,
        "COGNITIVE_ROUTE_INTELLIGENCE_REPORT":
        cognitive_route_intelligence_report,
        "concept_formation_report": concept_formation_report,
        "CONCEPT_FORMATION_REPORT": concept_formation_report,
        "program_synthesis_report": program_synthesis_report,
        "PROGRAM_SYNTHESIS_REPORT": program_synthesis_report,
        "adaptive_search_intelligence_report":
        adaptive_search_intelligence_report,
        "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT":
        adaptive_search_intelligence_report,
        "acsc_report": acsc_report,
        "ACSC_REPORT": acsc_report,
        "cognitive_knowledge_integration_report":
        cognitive_knowledge_integration_report,
        "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT":
        cognitive_knowledge_integration_report,
        "shared_cognitive_state_report": shared_cognitive_state_report,
        "SHARED_COGNITIVE_STATE_REPORT": shared_cognitive_state_report,
        "cognitive_observability_report": cognitive_observability_report,
        "COGNITIVE_OBSERVABILITY_REPORT": cognitive_observability_report,
        "knowledge_propagation_report": knowledge_propagation_report,
        "KNOWLEDGE_PROPAGATION_REPORT": knowledge_propagation_report,
        "shared_cognitive_state_save_report": shared_state_save_report,
        "truth_reuse_report": lifecycle_truth_reuse_report,
        "TRUTH REUSE REPORT": lifecycle_truth_reuse_report,
        "hypothesis_generation_report":
        concept_lifecycle_report.get("hypothesis_generation_report", {}),
        "HYPOTHESIS GENERATION REPORT":
        concept_lifecycle_report.get("hypothesis_generation_report", {}),
        "counterfactual_reasoning_report":
        concept_lifecycle_report.get("counterfactual_reasoning_report", {}),
        "COUNTERFACTUAL REASONING REPORT":
        concept_lifecycle_report.get("counterfactual_reasoning_report", {}),
        "training_diversity_report":
        concept_lifecycle_report.get("training_diversity_report", {}),
        "TRAINING DIVERSITY REPORT":
        concept_lifecycle_report.get("training_diversity_report", {}),
        "recursive_context_audit":
        concept_lifecycle_report.get("recursive_context_audit", {}),
        "Recursive Context Audit":
        concept_lifecycle_report.get("recursive_context_audit", {}),
        "truth_commit_report": truth_commit_report,
        "contextual_truth_report": contextual_truth_report,
        "context_validation_report": context_validation_report,
        "CONTEXT VALIDATION REPORT": context_validation_report,
        "context_reuse_report": context_reuse_report,
        "CONTEXT REUSE REPORT": context_reuse_report,
        "causal_context_report": causal_context_report,
        "CAUSAL_CONTEXT_REPORT": causal_context_report,
        "capabilities_executed":
        cognitive_capability_report.get("capabilities_executed", []),
        "capability_success_rate":
        cognitive_capability_report.get("capability_success_rate", 0.0),
        "truth_registry_report": truth_registry_report,
        "truth_graveyard_consistency_report":
        truth_graveyard_consistency_report,
        "report_budget_report": report_budget_report,
        "DEEP_MODE_OPTIMIZATION_REPORT": deep_mode_optimization_report,
        "deep_mode_optimization_report": deep_mode_optimization_report,
        "METRIC_RECONCILIATION_REPORT":
        performance_report.get("METRIC_RECONCILIATION_REPORT", {}),
        "METRIC_SOURCE_AUDIT":
        performance_report.get("METRIC_SOURCE_AUDIT", {}),
        "METRIC_CONFLICT_REPORT":
        performance_report.get("METRIC_CONFLICT_REPORT", {}),
        "METRIC_RECONCILIATION_WARNING":
        performance_report.get("METRIC_RECONCILIATION_WARNING", False),
        "canonical_metrics":
        performance_report.get("canonical_metrics", {}),
    }
    governance_budget_exceeded = any(
        isinstance(item.get("result"), dict)
        and item["result"].get(
            "governance_budget_exceeded",
            False,
        )
        for item in all_results
    )
    finalization_durations = [
        module.get("seconds", 0.0)
        for item in all_results
        if isinstance(item.get("result"), dict)
        for module in item["result"]
        .get("performance_report", {})
        .get("module_timings", [])
        if module.get("module") == "finalize_runtime"
    ]
    runtime_metrics["governance_budget_exceeded"] = (
        governance_budget_exceeded
    )
    runtime_metrics["finalization_duration"] = round(
        sum(finalization_durations),
        4,
    )
    results["runtime_watchdog_report"] = runtime_watchdog.report()
    results["runtime_metadata"] = dict(runtime_metrics)
    results["runtime_metadata"]["canonical_metrics"] = (
        performance_report.get("canonical_metrics", {})
    )
    results["runtime_metadata"]["METRIC_RECONCILIATION_REPORT"] = (
        performance_report.get("METRIC_RECONCILIATION_REPORT", {})
    )
    record_main_timing("assemble_final_context", module_start)
    module_timings.append(main_module_timings[-1])
    performance_report["module_timings"] = module_timings
    performance_report["slowest_modules"] = sorted(
        module_timings,
        key=lambda item: item.get("seconds", 0.0),
        reverse=True,
    )[:5]

    runtime_status = "completed"

except KeyboardInterrupt:
    runtime_status = "interrupted"
    print("\nNEXRYN :: EXECUTION INTERRUPTED")

except Exception as runtime_error:
    runtime_status = "failed"

    print("\nNEXRYN RUNTIME ERROR:\n")
    print(runtime_error)

    if args.debug:
        print("\n==================================================")
        print("NEXRYN :: DEBUG TRACEBACK")
        print("==================================================\n")
        traceback.print_exc()


# ============================================
# EXECUTION TIME
# ============================================

execution_time = round(
    time.time() - runtime_start,
    4,
)

if isinstance(results, dict) and isinstance(results.get("performance_report"), dict):
    from runtime.performance.runtime_attribution_engine import (
        runtime_attribution_engine,
    )
    from runtime.instrumentation import runtime_lifecycle
    from runtime.metrics import runtime_metric_synchronizer

    final_performance_report = results["performance_report"]
    final_runtime_attribution_report = (
        runtime_attribution_engine.build_report(
            total_runtime=execution_time,
            performance_report=final_performance_report,
            runtime_metrics=runtime_metrics,
            module_timings=final_performance_report.get(
                "module_timings",
                [],
            ),
        )
    )
    final_performance_report["execution_time"] = execution_time
    final_performance_report["total_runtime_seconds"] = execution_time
    final_performance_report["runtime_attribution_report"] = (
        final_runtime_attribution_report
    )
    final_performance_report["runtime_breakdown"] = (
        final_runtime_attribution_report["runtime_breakdown"]
    )
    final_performance_report["attributed_runtime_seconds"] = (
        final_runtime_attribution_report["attributed_runtime"]
    )
    final_performance_report["unattributed_runtime_seconds"] = (
        final_runtime_attribution_report["unattributed_runtime"]
    )
    final_performance_report["untracked_runtime_seconds"] = (
        final_runtime_attribution_report["untracked_runtime"]
    )
    from runtime.performance.unattributed_runtime_detector import (
        unattributed_runtime_detector,
    )

    final_performance_report["unattributed_runtime_detector_report"] = (
        unattributed_runtime_detector.detect(
            final_runtime_attribution_report,
            {
                **runtime_metrics,
                **final_performance_report,
            },
        )
    )
    from runtime.cognitive_runtime import cognitive_runtime_execution_engine

    completed_task_results = [
        item.get("result", {})
        for item in results.get("multi_task_results", [])
        if isinstance(item, dict) and isinstance(item.get("result"), dict)
    ]
    evaluation_evidence = {
        "evaluations": [
            item.get("evaluation_result")
            for item in completed_task_results
            if isinstance(item.get("evaluation_result"), dict)
        ],
    }
    cognitive_runtime_execution_engine.ensure_required_instances(
        evidence={
            "reasoning_runtime": results.get("SOLVER_REASONING_REPORT", {}),
            "search_runtime": results.get("COGNITIVE_SEARCH_REPORT", {}),
            "memory_runtime": results.get("ADAPTIVE_REUSE_REPORT", {}),
            "truth_runtime": {
                "truth_candidates": results.get("truth_candidates", []),
                "truth_commits": results.get("truth_commits", []),
            },
            "evaluation_runtime": evaluation_evidence,
        },
        mode=args.mode,
    )
    if shared_cognitive_state is not None:
        evaluation_shared_inputs = consume_shared_state(
            "evaluation_runtime",
            (
                "concept_store",
                "program_store",
                "search_routes",
                "knowledge_objects",
                "evidence_store",
                "context_store",
                "truth_candidates",
                "validated_truths",
                "memory_entries",
            ),
            required=("truth_candidates", "knowledge_objects", "evidence_store"),
        )
        shared_cognitive_state.validate_before(
            "evaluation_runtime",
            required=("memory_entries", "truth_candidates"),
        )
        shared_cognitive_state.publish(
            "evaluation_runtime",
            {
                **evaluation_evidence,
                "shared_state_inputs": evaluation_shared_inputs,
            },
            owner="evaluation_runtime",
            context=final_performance_report,
        )
        shared_cognitive_state.snapshot("final_evaluation")
    cognitive_runtime_execution_engine.complete_cycle()
    final_runtime_lifecycle_report = runtime_lifecycle.build_report()
    final_performance_report["runtime_lifecycle_report"] = (
        final_runtime_lifecycle_report
    )
    metric_sync_result = runtime_metric_synchronizer.synchronize(
        performance_report=final_performance_report,
        lifecycle_report=final_runtime_lifecycle_report,
    )
    final_performance_report = metric_sync_result["performance_report"]
    results["performance_report"] = final_performance_report
    final_metric_synchronization_report = (
        metric_sync_result["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"]
    )
    final_runtime_attribution_report = (
        runtime_attribution_engine.build_report(
            total_runtime=execution_time,
            performance_report=final_performance_report,
            runtime_metrics={
                **runtime_metrics,
                **final_performance_report.get("canonical_metrics", {}),
                **{
                    key: value
                    for key, value in final_performance_report.items()
                    if key.endswith("_time_seconds")
                    or key.endswith("_generation_time")
                },
            },
            module_timings=final_performance_report.get(
                "module_timings",
                [],
            ),
        )
    )
    final_performance_report["runtime_attribution_report"] = (
        final_runtime_attribution_report
    )
    final_performance_report["runtime_breakdown"] = (
        final_runtime_attribution_report["runtime_breakdown"]
    )
    final_performance_report["attributed_runtime_seconds"] = (
        final_runtime_attribution_report["attributed_runtime"]
    )
    final_performance_report["unattributed_runtime_seconds"] = (
        final_runtime_attribution_report["unattributed_runtime"]
    )
    final_performance_report["untracked_runtime_seconds"] = (
        final_runtime_attribution_report["untracked_runtime"]
    )
    final_performance_report["unattributed_runtime_detector_report"] = (
        unattributed_runtime_detector.detect(
            final_runtime_attribution_report,
            {
                **runtime_metrics,
                **final_performance_report.get("canonical_metrics", {}),
                **final_performance_report,
            },
        )
    )
    from runtime.metrics.canonical_metric_registry import (
        CanonicalMetricRegistry,
    )
    from runtime.metrics.metric_validation_engine import MetricValidationEngine
    from runtime.metrics.unified_metric_store import UnifiedMetricStore
    from runtime.observability.runtime_observability_layer import (
        RuntimeObservabilityLayer,
    )
    from runtime.cognitive_runtime import (
        build_cognitive_runtime_report,
        execution_binding_layer,
    )

    observability_registry = CanonicalMetricRegistry()
    observability_store = UnifiedMetricStore(registry=observability_registry)
    observability_layer = RuntimeObservabilityLayer(
        store=observability_store,
        registry=observability_registry,
        validator=MetricValidationEngine(store=observability_store),
    )
    final_observability_report = (
        observability_layer.build_runtime_observability_report(
            performance_report=final_performance_report,
            runtime_attribution_report=final_runtime_attribution_report,
            sources={
                "performance_report": final_performance_report,
                "runtime_attribution_report": final_runtime_attribution_report,
            },
        )
    )
    final_performance_report["runtime_observability_report"] = (
        final_observability_report
    )
    cognitive_runtime_report = build_cognitive_runtime_report(
        performance_report=final_performance_report,
        runtime_lifecycle_report=final_runtime_lifecycle_report,
        runtime_observability_report=final_observability_report,
        cognitive_pipeline_report=results.get("COGNITIVE_PIPELINE_REPORT", {}),
        cognitive_search_report=results.get("COGNITIVE_SEARCH_REPORT", {}),
        solver_reasoning_report=results.get("SOLVER_REASONING_REPORT", {}),
        truth_report=results.get("truth_candidate_report", {}),
        memory_report=results.get("ADAPTIVE_REUSE_REPORT", {}),
        evaluation_report=results.get("evaluation_result", {}),
    )
    execution_binding_report = execution_binding_layer.bind(
        cognitive_runtime_report["runtime_registry"],
        final_runtime_lifecycle_report,
    )
    cognitive_runtime_execution_engine.bind_and_archive()
    cognitive_execution_engine_report = (
        cognitive_runtime_execution_engine.build_report(
            total_runtime_seconds=execution_time,
        )
    )
    if shared_cognitive_state is not None:
        shared_cognitive_state.publish(
            "execution_registry",
            cognitive_execution_engine_report,
            owner="execution_runtime",
            context=final_performance_report,
        )
        shared_cognitive_state.snapshot("execution_finalization")
        shared_state_save_report = shared_cognitive_state.save()
        shared_cognitive_state_report = shared_cognitive_state.build_report()
        cognitive_observability_report = shared_cognitive_state_report.get(
            "cognitive_observability",
            {},
        )
        knowledge_propagation_report = knowledge_bus.report()
        final_performance_report["SHARED_COGNITIVE_STATE_REPORT"] = (
            shared_cognitive_state_report
        )
        final_performance_report["KNOWLEDGE_PROPAGATION_REPORT"] = (
            knowledge_propagation_report
        )
        final_performance_report["shared_cognitive_state_report"] = (
            shared_cognitive_state_report
        )
        final_performance_report["knowledge_propagation_report"] = (
            knowledge_propagation_report
        )
        final_performance_report["shared_cognitive_state_save_report"] = (
            shared_state_save_report
        )
        final_performance_report["COGNITIVE_OBSERVABILITY_REPORT"] = (
            cognitive_observability_report
        )
        final_performance_report["cognitive_observability_report"] = (
            cognitive_observability_report
        )
        results["SHARED_COGNITIVE_STATE_REPORT"] = (
            shared_cognitive_state_report
        )
        results["shared_cognitive_state_report"] = (
            shared_cognitive_state_report
        )
        results["KNOWLEDGE_PROPAGATION_REPORT"] = (
            knowledge_propagation_report
        )
        results["knowledge_propagation_report"] = (
            knowledge_propagation_report
        )
        results["COGNITIVE_OBSERVABILITY_REPORT"] = (
            cognitive_observability_report
        )
        results["cognitive_observability_report"] = (
            cognitive_observability_report
        )
    final_runtime_lifecycle_report = runtime_lifecycle.build_report()
    final_performance_report["runtime_lifecycle_report"] = (
        final_runtime_lifecycle_report
    )
    metric_sync_result = runtime_metric_synchronizer.synchronize(
        performance_report=final_performance_report,
        lifecycle_report=final_runtime_lifecycle_report,
        runtime_registry=cognitive_runtime_report["runtime_registry"],
    )
    final_performance_report = metric_sync_result["performance_report"]
    final_metric_synchronization_report = (
        metric_sync_result["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"]
    )
    cognitive_runtime_report["execution_binding_report"] = (
        execution_binding_report
    )
    cognitive_runtime_report["EXECUTION_BINDING_REPORT"] = (
        execution_binding_report
    )
    final_performance_report["execution_binding_report"] = (
        execution_binding_report
    )
    final_performance_report["EXECUTION_BINDING_REPORT"] = (
        execution_binding_report
    )
    final_performance_report["cognitive_execution_engine_report"] = (
        cognitive_execution_engine_report
    )
    final_performance_report["COGNITIVE_EXECUTION_ENGINE_REPORT"] = (
        cognitive_execution_engine_report
    )
    final_performance_report["cognitive_runtime_report"] = (
        cognitive_runtime_report
    )
    final_performance_report["COGNITIVE_RUNTIME_REPORT"] = (
        cognitive_runtime_report
    )
    results["RUNTIME ATTRIBUTION REPORT"] = final_runtime_attribution_report
    results["RUNTIME_LIFECYCLE_REPORT"] = final_runtime_lifecycle_report
    results["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"] = (
        final_metric_synchronization_report
    )
    results["RUNTIME_OBSERVABILITY_REPORT"] = final_observability_report
    results["EXECUTION_BINDING_REPORT"] = execution_binding_report
    results["cognitive_execution_engine_report"] = (
        cognitive_execution_engine_report
    )
    results["COGNITIVE_EXECUTION_ENGINE_REPORT"] = (
        cognitive_execution_engine_report
    )
    results["cognitive_runtime_report"] = cognitive_runtime_report
    results["COGNITIVE_RUNTIME_REPORT"] = cognitive_runtime_report
    if isinstance(results.get("PERFORMANCE_REPORT"), dict):
        performance_intelligence = results["PERFORMANCE_REPORT"]
        performance_intelligence["runtime_attribution_report"] = (
            final_runtime_attribution_report
        )
        performance_intelligence["runtime_lifecycle_report"] = (
            final_runtime_lifecycle_report
        )
        performance_intelligence["runtime_metric_synchronization_report"] = (
            final_metric_synchronization_report
        )
        performance_intelligence["runtime_observability_report"] = (
            final_observability_report
        )
        performance_intelligence["cognitive_runtime_report"] = (
            cognitive_runtime_report
        )
        performance_intelligence["execution_binding_report"] = (
            execution_binding_report
        )
        performance_intelligence["cognitive_execution_engine_report"] = (
            cognitive_execution_engine_report
        )
        runtime_breakdown = final_runtime_attribution_report.get(
            "runtime_breakdown",
            {},
        )
        if isinstance(performance_intelligence.get("runtime_summary"), dict):
            runtime_summary = performance_intelligence["runtime_summary"]
            runtime_summary["total_runtime_seconds"] = execution_time
            runtime_summary["startup_time_seconds"] = runtime_breakdown.get(
                "boot_time",
                runtime_summary.get("startup_time_seconds", 0.0),
            )
            runtime_summary["task_execution_time_seconds"] = (
                runtime_breakdown.get(
                    "task_execution_time",
                    runtime_summary.get("task_execution_time_seconds", 0.0),
                )
            )
            runtime_summary["active_compute_time_seconds"] = (
                runtime_summary["task_execution_time_seconds"]
            )
            runtime_summary["idle_time_seconds"] = runtime_breakdown.get(
                "idle_time",
                max(
                    0.0,
                    execution_time
                    - runtime_summary["active_compute_time_seconds"],
                ),
            )
            runtime_summary["untracked_runtime_seconds"] = (
                final_runtime_attribution_report.get("untracked_runtime", 0.0)
            )
        for stage in performance_intelligence.get("stage_metrics", []):
            if isinstance(stage, dict):
                stage["percentage_of_runtime"] = round(
                    float(stage.get("total_duration", 0.0) or 0.0)
                    / max(execution_time, 0.0001),
                    4,
                )


# ============================================
# DETERMINISTIC POST-SUCCESS SHUTDOWN
# ============================================

if runtime_status == "completed" and isinstance(results, dict):
    try:
        from runtime.evaluation.evaluation_controller import (
            EvaluationController,
        )
        from runtime.shutdown.shutdown_controller import ShutdownController

        shutdown_controller = ShutdownController(
            logger=logging.getLogger("nexryn.shutdown")
        )

        total_tasks = max(1, int(results.get("tasks_executed", 0) or 0))
        successful_tasks = int(results.get("successful_tasks", 0) or 0)
        failed_tasks = int(results.get("failed_tasks", 0) or 0)
        incomplete_tasks = int(results.get("incomplete_tasks", 0) or 0)
        unresolved_tasks = failed_tasks + incomplete_tasks
        evaluation_context = {
            **results,
            "accuracy": successful_tasks / total_tasks,
            "difference_count": unresolved_tasks,
            "episode_completed": unresolved_tasks == 0,
            "retry_allowed": unresolved_tasks != 0,
            "shutdown_mode": "fast" if unresolved_tasks == 0 else "normal",
            "execution_time": execution_time,
        }
        evaluated_context = EvaluationController(
            logger=logging.getLogger("nexryn.evaluation")
        ).evaluate(evaluation_context)
        results["evaluation_result"] = evaluated_context.get(
            "evaluation_result",
            {},

        )
        results["evaluation_metrics"] = evaluated_context.get(
            "evaluation_metrics",
            {},
        )
        
        results["evaluation_report"] = evaluated_context.get(
            "evaluation_report",
            {},
        )
        results["deferred_reporting_queue"] = evaluated_context.get(
            "deferred_reporting_queue",
            [],
        )
        results["FAST_EVALUATION_MODE"] = evaluated_context.get(
            "FAST_EVALUATION_MODE",
            False,
        )
        shutdown_context = {
            **results,
            "shutdown_mode": evaluated_context.get("shutdown_mode", "fast"),
            "evaluation_metrics": results.get("evaluation_metrics", {}),
            "evaluation_result": results.get("evaluation_result", {}),
            "learning_state": results.get("training_report", {}),
            "reward_state": results.get("training_assistant_report", {}),
            "task_outcome": {
                "successful_tasks": results.get("successful_tasks", 0),
                "failed_tasks": results.get("failed_tasks", 0),
            },
        }
        shutdown_context = shutdown_controller.execute_shutdown(
            shutdown_context,
            exit_process=False,
        )
        results["SHUTDOWN_REPORT"] = shutdown_context.get(
            "SHUTDOWN_REPORT",
            {},
        )
        results["post_success_isolation"] = shutdown_context.get(
            "post_success_isolation",
            {},
        )
    except Exception as shutdown_error:
        results["SHUTDOWN_REPORT"] = {
            "cleanup_failures": [
                {
                    "resource_type": "shutdown_controller",
                    "success": False,
                    "failure_reason": str(shutdown_error),
                }
            ],
            "forced_termination": False,
        }


# ============================================
# FINAL CONTEXT
# ============================================

print("\n==================================================")
print("NEXRYN :: FINAL CONTEXT")
print("==================================================\n")

final_report_level = effective_report_level
if args.mode in {"deep", "full"}:
    final_report_level = deep_mode_budget_manager.bounded_report_level(
        args.mode,
        effective_report_level,
        deep_audit_flags,
    )
if (
    isinstance(results, dict)
    and results.get("report_budget_report", {}).get("report_budget_exceeded")
    and effective_report_level in {"full", "debug", "audit"}
):
    final_report_level = "normal"
    results["report_budget_report"]["forced_report_level"] = final_report_level
    results["report_budget_report"]["compression_action"] = (
        "deep_report_forced_to_normal_summary"
    )

safe_print_context(
    results,
    report_level=final_report_level,
)

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("performance_report")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: PERFORMANCE REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_performance_report(
            results["performance_report"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("CAUSAL_CONTEXT_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: CAUSAL_CONTEXT_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["CAUSAL_CONTEXT_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_ANALYTICS_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_ANALYTICS_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["COGNITIVE_ANALYTICS_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("REASONING_INTELLIGENCE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: REASONING_INTELLIGENCE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["REASONING_INTELLIGENCE_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("REASONING_GRAPH_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: REASONING_GRAPH_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["REASONING_GRAPH_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("REASONING_ANALYTICS_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: REASONING_ANALYTICS_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["REASONING_ANALYTICS_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("META_COGNITIVE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: META_COGNITIVE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["META_COGNITIVE_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("SOLVER_INTELLIGENCE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: SOLVER_INTELLIGENCE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["SOLVER_INTELLIGENCE_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("SOLVER_REASONING_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: SOLVER_REASONING_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["SOLVER_REASONING_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_PIPELINE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_PIPELINE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["COGNITIVE_PIPELINE_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_SEARCH_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_SEARCH_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["COGNITIVE_SEARCH_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("CONCEPT_FORMATION_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: CONCEPT_FORMATION_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_concept_formation_report(
            results["CONCEPT_FORMATION_REPORT"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("PROGRAM_SYNTHESIS_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: PROGRAM_SYNTHESIS_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_program_synthesis_report(
            results["PROGRAM_SYNTHESIS_REPORT"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("ADAPTIVE_SEARCH_INTELLIGENCE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: ADAPTIVE_SEARCH_INTELLIGENCE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_adaptive_search_intelligence_report(
            results["ADAPTIVE_SEARCH_INTELLIGENCE_REPORT"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("ADAPTIVE_SEARCH_POLICY_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: ADAPTIVE_SEARCH_POLICY_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["ADAPTIVE_SEARCH_POLICY_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_ROUTE_INTELLIGENCE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_ROUTE_INTELLIGENCE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_cognitive_route_intelligence_report(
            results["COGNITIVE_ROUTE_INTELLIGENCE_REPORT"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("ACSC_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: ACSC_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_acsc_report(
            results["ACSC_REPORT"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_cognitive_knowledge_integration_report(
            results["COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT"],
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_RUNTIME_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_RUNTIME_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["COGNITIVE_RUNTIME_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("COGNITIVE_EXECUTION_ENGINE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: COGNITIVE_EXECUTION_ENGINE_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["COGNITIVE_EXECUTION_ENGINE_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("EXECUTION_BINDING_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: EXECUTION_BINDING_REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["EXECUTION_BINDING_REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("RUNTIME ATTRIBUTION REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: RUNTIME ATTRIBUTION REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["RUNTIME ATTRIBUTION REPORT"],
            level=final_report_level,
        )
    )

if (
    effective_report_level != "minimal"
    and isinstance(results, dict)
    and results.get("PERFORMANCE_REPORT")
):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: PERFORMANCE INTELLIGENCE REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["PERFORMANCE_REPORT"],
            level=final_report_level,
        )
    )

if args.profile and isinstance(results, dict):
    from runtime.profiling.performance_reporter import performance_reporter
    from runtime.profiling.telemetry_collector import telemetry

    profile_payload = {
        "PERFORMANCE_REPORT": results.get("PERFORMANCE_REPORT", {}),
        "performance_report": results.get("performance_report", {}),
        "telemetry": telemetry.report(),
        "runtime_status": runtime_status,
        "execution_time": execution_time,
    }
    write_report = performance_reporter.write_report(
        profile_payload,
        args.profile_output,
    )
    results["profile_output_report"] = write_report
    print("\n==================================================")
    print("NEXRYN :: PROFILE OUTPUT")
    print("==================================================\n")
    print(write_report)


# ============================================
# CONTEXT DETAILS
# ============================================

if args.verbose and isinstance(results, dict):
    print("\n==================================================")
    print("NEXRYN :: CONTEXT DETAILS")
    print("==================================================\n")

    for key in results.keys():
        print(f"- {key}")


# ============================================
# PIPELINE REPORT
# ============================================

if args.verbose:
    try:
        pipeline_report = pipeline.build_pipeline_report()

        print("\n==================================================")
        print("NEXRYN :: PIPELINE REPORT")
        print("==================================================\n")
        from runtime.reporting.compact_report_builder import (
            compact_report_builder,
        )

        print(
            compact_report_builder.compact_context(
                pipeline_report,
                level=effective_report_level,
            )
        )

    except Exception as report_error:
        print("\nPIPELINE REPORT UNAVAILABLE")
        print(report_error)


# ============================================
# RUNTIME METADATA
# ============================================

runtime_metadata = build_runtime_metadata(
    args,
    execution_time,
    runtime_status,
    context_count=(
        results.get("performance_report", {}).get(
            "context_count",
            len(normalize_context_diagnostics(
                results.get("training_report", {}),
            )),
        )
        if isinstance(results, dict)
        else 0
    ),
    runtime_metrics={
        **runtime_metrics,
        "watchdog": runtime_watchdog.report(),
    },
)

print("\n==================================================")
print("NEXRYN :: RUNTIME METADATA")
print("==================================================\n")
if effective_report_level == "minimal":
    print({
        "system": "runtime_metadata",
        "report_state": "final",
        "status": runtime_metadata.get("runtime_status"),
        "mode": runtime_metadata.get("mode"),
        "report_level": runtime_metadata.get("report_level"),
        "execution_time": runtime_metadata.get("execution_time"),
        "training_batch_size": runtime_metadata.get("training_batch_size"),
        "tasks_directory": runtime_metadata.get("tasks_directory"),
        "governance_budget_seconds":
        runtime_metadata.get("governance_budget_seconds"),
        "governance_budget_exceeded":
        runtime_metadata.get("governance_budget_exceeded"),
        "cache_boot_loaded": runtime_metadata.get("cache_boot_loaded"),
        "cache_boot_skipped": runtime_metadata.get("cache_boot_skipped"),
        "timestamp": runtime_metadata.get("timestamp"),
    })
else:
    print(runtime_metadata)


# ============================================
# DIAGNOSTICS
# ============================================

try:
    from runtime.diagnostics import RuntimeDiagnostics

    runtime_snapshot = type(
        "RuntimeSnapshot",
        (),
        {
            "report": results,
            "runtime_report": results,
            "last_report": results,
        },
    )()

    diagnostics = RuntimeDiagnostics(
        runtime=runtime_snapshot
    )

    if args.stats:
        diagnostics.stats()

    if args.audit:
        diagnostics.audit()

    if args.explain:
        diagnostics.explain(args.explain)

    if args.identity:
        diagnostics.identity()

    if args.contexts:
        diagnostics.contexts()

    if args.truths:
        diagnostics.truths()

    if args.candidates:
        diagnostics.candidates()

except Exception as diagnostic_error:
    print("\n==================================================")
    print("NEXRYN :: DIAGNOSTIC FAILURE")
    print("==================================================\n")
    print(diagnostic_error)

    if args.debug:
        traceback.print_exc()


# ============================================
# FINAL STATUS
# ============================================

print("\n==================================================")
print("NEXRYN :: EXECUTION COMPLETE")
print("==================================================\n")

if runtime_status == "completed":
    shutdown_controller.exit_enforcer.enforce_exit(
        exit_process=True,
        code=0,
    )
