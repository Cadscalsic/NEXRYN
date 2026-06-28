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
        "startup_hang_prevented": runtime_metrics.get(
            "startup_hang_prevented",
        ),
        "post_success_mode": args.post_success_mode,
        "profile_enabled": args.profile,
        "profile_output": args.profile_output,
        "profile_level": args.profile_level,
        "python_version": sys.version,
        "timestamp": str(datetime.utcnow()),
    }


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
                print({
                    "tasks_executed": results.get("tasks_executed", 0),
                    "successful_tasks": results.get("successful_tasks", 0),
                    "failed_tasks": results.get("failed_tasks", 0),
                    "architecture_bottleneck":
                    architecture_report.get("architecture_bottleneck"),
                    "recommended_next_step":
                    architecture_report.get("recommended_next_step"),
                    "dependency_chain_depth":
                    architecture_report.get("dependency_chain_depth"),
                    "dependency_chain_coverage":
                    architecture_report.get("dependency_chain_coverage"),
                    "performance_report":
                    compact_report_builder.compact_performance_report(
                        results.get("performance_report", {}),
                    ),
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

def print_training_batch_summary(training_batch, verbose=False):
    from runtime.reporting.compact_report_builder import (
        MAX_TASKS_DISPLAYED,
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: TRAINING ASSISTANT BATCH")
    print("==================================================\n")

    if verbose:
        print(compact_report_builder.compact_context(training_batch))
        return

    selected_files = training_batch.get("selected_task_files", [])
    print("training_mode:", training_batch.get("training_mode"))
    print("selected_tasks:", training_batch.get("selected_task_count", 0))
    print("tasks_completed:", 0)
    print("tasks_failed:", 0)
    print("tasks_remaining:", training_batch.get("selected_task_count", 0))
    print("current_batch_size:", training_batch.get("selected_task_count", 0))
    print("recent_tasks:", list(selected_files or [])[-MAX_TASKS_DISPLAYED:])
    print("prioritized_concepts:", training_batch.get("prioritized_concepts", []))


class _MinimalRuntimePrintFilter:
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
            self.original_print(*args, **kwargs)
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


def _walk_metric_mappings(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_metric_mappings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_metric_mappings(item)


def build_runtime_metric_bridge(
    all_results,
    training_report,
    task_performance_reports,
    module_timings,
    runtime_metrics=None,
):
    from runtime.profiling.metric_bridge import runtime_metric_bridge

    runtime_metrics = runtime_metrics or {}
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

    for mapping in _walk_metric_mappings({
        "all_results": all_results,
        "training_report": training_report,
    }):
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

    concepts_processed = max(concept_candidates + semantic_counts + [0])
    dependency_chain_depth = max(dependency_depths or [0])
    dependency_chain_coverage = max(dependency_coverages or [0.0])

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
        "dependency_chain_depth": dependency_chain_depth,
        "dependency_chain_coverage": round(dependency_chain_coverage, 4),
        "dependency_chains_executed": max(
            sum(
                int(_metric_number(
                    report.get("dependency_chains_executed"),
                ))
                for report in task_performance_reports
            ),
            dependency_chain_reports,
        ),
        **timing_bridge,
        "metric_bridge": {
            "concept_sources": {
                "task_performance_reports": concept_candidates[0],
                "training_concept_memory": concept_candidates[1],
                "completed_tasks_floor": concept_candidates[2],
            },
            "dependency_depth_samples": len(dependency_depths),
            "dependency_coverage_samples": len(dependency_coverages),
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
    choices=["fast", "adaptive", "deep"],
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
    choices=["minimal", "normal", "full"],
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

args = parser.parse_args()
effective_report_level = args.report_level or {
    "fast": "minimal",
    "adaptive": "normal",
    "deep": "full",
}.get(args.mode, "normal")
args.report_level = effective_report_level
training_batch_size, training_batch_size_source = (
    resolve_training_batch_size(args, parser)
)
governance_budget_seconds = governance_budget_for_mode(args.mode)
runtime_watchdog = RuntimeWatchdog()
runtime_watchdog.start("boot_total")
runtime_watchdog.checkpoint("boot_start")
runtime_metrics = {
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
        batch_size=training_batch_size
    )

    if args.reset_training_assistant:
        training_assistant.reset()

    concept_counts = {}
    concept_states = {}
    observed_task_ids = []

    runtime_watchdog.start("task_selection")
    training_batch = training_assistant.select_batch(
        discovered_task_files,
        concept_counts=concept_counts,
        concept_states=concept_states,
        task_directory=args.tasks_dir,
        observed_task_ids=observed_task_ids,
    )
    runtime_metrics["task_selection_duration"] = (
        runtime_watchdog.stop_and_warn(
            "task_selection",
            "task_selection",
        )
    )
    runtime_watchdog.checkpoint("task_selection_complete")

    task_files = training_batch["selected_task_files"]

    print_training_batch_summary(
        training_batch,
        verbose=args.verbose,
    )

    all_results = []
    successful_tasks = 0
    failed_tasks = 0
    first_task_started = False

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

            successful_tasks += 1

            all_results.append(
                {
                    "task": task_file,
                    "status": "completed",
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

    training_assistant_report = training_assistant.complete_cycle(
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
    )

    ledger_report = (
        pipeline
        .cross_task_replication_collector
        .ledger
        .report()
    )

    concept_lifecycle_report = (
        pipeline
        .concept_lifecycle_manager
        .knowledge_maturity_report
    )
    if not concept_lifecycle_report.get("concepts"):
        concept_lifecycle_report = (
            pipeline
            .concept_lifecycle_manager
            .update_knowledge_maturity(
                ledger_report,
                {
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

    from runtime.learning.training_report import build_training_report

    training_report = build_training_report(
        training_batch=training_batch,
        training_assistant_report=training_assistant_report,
        multi_task_results=all_results,
        ledger_report=ledger_report,
        concept_lifecycle_report=concept_lifecycle_report,
        include_truth_evaluations=True,
    )

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
    slowest_modules = sorted(
        [
            module
            for report in task_performance_reports
            for module in report.get("slowest_modules", [])
        ],
        key=lambda item: item.get("seconds", 0.0),
        reverse=True,
    )[:5]
    metric_bridge = build_runtime_metric_bridge(
        all_results=all_results,
        training_report=training_report,
        task_performance_reports=task_performance_reports,
        module_timings=module_timings,
        runtime_metrics=runtime_metrics,
    )
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
        "cache_hits": sum(
            report.get("cache_hits", 0)
            for report in task_performance_reports
        ),
        "cache_misses": sum(
            report.get("cache_misses", 0)
            for report in task_performance_reports
        ),
        "strategy_hits": sum(
            report.get("strategy_hits", 0)
            for report in task_performance_reports
        ),
        "strategy_misses": sum(
            report.get("strategy_misses", 0)
            for report in task_performance_reports
        ),
        "context_hits": sum(
            report.get("context_hits", 0)
            for report in task_performance_reports
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
        "truth_hits": sum(
            report.get("truth_hits", 0)
            for report in task_performance_reports
        ),
        "truth_misses": sum(
            report.get("truth_misses", 0)
            for report in task_performance_reports
        ),
        "dependency_snapshot_hits": sum(
            report.get("dependency_snapshot_hits", 0)
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
        "cache_time_seconds": metric_bridge["cache_time_seconds"],
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
    }
    reuse_total = (
        performance_report["cache_hits"]
        + performance_report["cache_misses"]
    )
    performance_report["reuse_rate"] = round(
        performance_report["cache_hits"] / reuse_total,
        4,
    ) if reuse_total else 0.0
    from runtime.performance.runtime_attribution_engine import (
        runtime_attribution_engine,
    )

    runtime_attribution_report = runtime_attribution_engine.build_report(
        total_runtime=total_runtime_seconds,
        performance_report=performance_report,
        runtime_metrics=runtime_metrics,
        module_timings=module_timings,
    )
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
    from runtime.profiling.performance_reporter import performance_reporter

    performance_intelligence_report = performance_reporter.build_report(
        runtime_context={
            "COGNITIVE_REUSE_REPORT": (
                pipeline.meta_supervisor.build_cognitive_reuse_report()
                if hasattr(pipeline, "meta_supervisor")
                else {}
            ),
            "task_performance_intelligence_reports":
            task_performance_intelligence_reports,
        },
        performance_report=performance_report,
        profile_level=args.profile_level,
    )

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
    discovery_only_truth_mode = False
    if discovery_only_truth_mode:
        truth_candidate_report = {}
        truth_commit_report = {}

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
        "truth_commit_report": truth_commit_report,
        "contextual_truth_report": contextual_truth_report,
        "context_validation_report": context_validation_report,
        "CONTEXT VALIDATION REPORT": context_validation_report,
        "context_reuse_report": context_reuse_report,
        "CONTEXT REUSE REPORT": context_reuse_report,
        "truth_registry_report": truth_registry_report,
        "truth_graveyard_consistency_report":
        truth_graveyard_consistency_report,
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
    results["RUNTIME ATTRIBUTION REPORT"] = final_runtime_attribution_report
    if isinstance(results.get("PERFORMANCE_REPORT"), dict):
        results["PERFORMANCE_REPORT"]["runtime_attribution_report"] = (
            final_runtime_attribution_report
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
        evaluation_context = {
            **results,
            "accuracy": successful_tasks / total_tasks,
            "difference_count": failed_tasks,
            "episode_completed": failed_tasks == 0,
            "retry_allowed": failed_tasks != 0,
            "shutdown_mode": "fast" if failed_tasks == 0 else "normal",
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

safe_print_context(
    results,
    report_level=effective_report_level,
)

if isinstance(results, dict) and results.get("performance_report"):
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

if isinstance(results, dict) and results.get("RUNTIME ATTRIBUTION REPORT"):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: RUNTIME ATTRIBUTION REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["RUNTIME ATTRIBUTION REPORT"],
            level=effective_report_level,
        )
    )

if isinstance(results, dict) and results.get("PERFORMANCE_REPORT"):
    from runtime.reporting.compact_report_builder import (
        compact_report_builder,
    )

    print("\n==================================================")
    print("NEXRYN :: PERFORMANCE INTELLIGENCE REPORT")
    print("==================================================\n")
    print(
        compact_report_builder.compact_context(
            results["PERFORMANCE_REPORT"],
            level=effective_report_level,
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
