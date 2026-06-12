# ============================================
# NEXRYN MAIN RUNTIME
# ============================================

import argparse
import os
import sys
import time
import traceback
from datetime import datetime

# ============================================
# PIPELINE
# ============================================

from runtime.pipeline import pipeline

from runtime.learning.training_assistant import TrainingAssistant

from runtime.learning.training_report import (
    build_training_report,
    print_training_report,
)

from runtime.diagnostics import RuntimeDiagnostics


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

def build_runtime_metadata(args, execution_time, runtime_status, context_count=0):
    return {
        "tasks_directory": args.tasks_dir,
        "mode": args.mode,
        "runtime_status": runtime_status,
        "execution_time": execution_time,
        "context_count": context_count,
        "python_version": sys.version,
        "timestamp": str(datetime.utcnow()),
    }


# ============================================
# SAFE PRINT
# ============================================

def safe_print_context(results):
    try:
        if isinstance(results, dict):
            training_report = results.get("training_report", {})

            if training_report:
                print_training_report(training_report)
            else:
                print(results)
        else:
            print("INVALID RUNTIME CONTEXT")

    except Exception as error:
        print(f"CONTEXT PRINT FAILURE: {error}")


# ============================================
# RUNTIME OUTPUT HELPERS
# ============================================

def print_training_batch_summary(training_batch, verbose=False):
    print("\n==================================================")
    print("NEXRYN :: TRAINING ASSISTANT BATCH")
    print("==================================================\n")

    if verbose:
        print(training_batch)
        return

    print("training_mode:", training_batch.get("training_mode"))
    print("selected_task_count:", training_batch.get("selected_task_count", 0))
    print("selected_task_files:", training_batch.get("selected_task_files", []))
    print("prioritized_concepts:", training_batch.get("prioritized_concepts", []))


# ============================================
# DIAGNOSTIC HELPERS
# ============================================

def normalize_concept_diagnostics(training_report):
    concepts = {}

    for concept, stats in training_report.get("concept_memory", {}).items():
        concepts[concept] = {
            **stats,
            "state": stats.get("lifecycle_state", "DISCOVERING"),
            "candidate_ready": stats.get(
                "preliminary_truth_candidate_ready",
                False,
            ),
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


def collect_governance_reports(all_results, possible_keys):
    collected = {}

    for item in all_results:
        result = item.get("result", {})

        if not isinstance(result, dict):
            continue

        governance_reports = result.get("governance_reports", {})

        if not isinstance(governance_reports, dict):
            continue

        for key in possible_keys:
            report = governance_reports.get(key)

            if isinstance(report, dict):
                collected.update(report)

    return collected


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
    help="Runtime mode",
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
    default=5,
    help="Number of ARC training tasks executed per runtime cycle",
)

parser.add_argument(
    "--reset-training-assistant",
    action="store_true",
    help="Reset the persistent training batch cursor before execution",
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


# ============================================
# START RUNTIME
# ============================================

print_runtime_banner()

runtime_start = time.time()
runtime_status = "booting"
results = {}


# ============================================
# PIPELINE VALIDATION
# ============================================

try:
    if args.verbose:
        print("NEXRYN :: VALIDATING PIPELINE...\n")

    if pipeline is None:
        raise RuntimeError("Pipeline initialization failed")

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

    training_assistant = TrainingAssistant(
        batch_size=args.training_batch_size
    )

    if args.reset_training_assistant:
        training_assistant.reset()

    initial_ledger_report = (
        pipeline
        .cross_task_replication_collector
        .ledger
        .report()
    )

    concept_counts = {
        concept.get("concept"): concept.get("used_task_count", 0)
        for concept in initial_ledger_report.get("concepts", [])
        if concept.get("concept")
    }

    concept_lifecycle_report = (
        pipeline
        .concept_lifecycle_manager
        .knowledge_maturity_report
    )

    concept_states = {
        concept.get("concept"): concept.get("state", "DISCOVERING")
        for concept in concept_lifecycle_report.get("concepts", [])
        if concept.get("concept")
    }

    observed_task_ids = initial_ledger_report.get(
        "observed_task_ids",
        []
    )

    training_batch = training_assistant.select_batch(
        discovered_task_files,
        concept_counts=concept_counts,
        concept_states=concept_states,
        task_directory=args.tasks_dir,
        observed_task_ids=observed_task_ids,
    )

    task_files = training_batch["selected_task_files"]

    print_training_batch_summary(
        training_batch,
        verbose=args.verbose,
    )

    all_results = []
    successful_tasks = 0
    failed_tasks = 0

    for task_file in task_files:
        task_path = os.path.join(
            args.tasks_dir,
            task_file,
        )

        print("\n==================================================")
        print(f"NEXRYN :: RUNNING TASK :: {task_file}")
        print("==================================================\n")

        try:
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
                print("\n==================================================")
                print("NEXRYN :: GOVERNANCE REPORT")
                print("==================================================\n")
                print(governance_reports)

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

    training_report = build_training_report(
        training_batch=training_batch,
        training_assistant_report=training_assistant_report,
        multi_task_results=all_results,
        ledger_report=ledger_report,
        concept_lifecycle_report=concept_lifecycle_report,
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

    truth_graveyard_consistency_report = collect_governance_reports(
        all_results,
        [
            "truth_graveyard_consistency",
            "truth_graveyard_consistency_report",
        ],
    )

    concepts = normalize_concept_diagnostics(training_report)
    truth_candidates = normalize_truth_candidates(training_report)
    truth_commits = training_report.get("truth_commit_evaluations", {})
    contexts = normalize_context_diagnostics(training_report)

    results = {
        "multi_task_results": all_results,
        "tasks_discovered": len(discovered_task_files),
        "discovered_task_files": discovered_task_files,
        "training_assistant_batch": training_batch,
        "training_assistant_report": training_assistant_report,
        "training_report": training_report,
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
        "truth_commit_report": truth_commit_report,
        "contextual_truth_report": contextual_truth_report,
        "truth_graveyard_consistency_report":
        truth_graveyard_consistency_report,
    }

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


# ============================================
# FINAL CONTEXT
# ============================================

print("\n==================================================")
print("NEXRYN :: FINAL CONTEXT")
print("==================================================\n")

safe_print_context(results)


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
        print(pipeline_report)

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
    context_count=len(results) if isinstance(results, dict) else 0,
)

print("\n==================================================")
print("NEXRYN :: RUNTIME METADATA")
print("==================================================\n")
print(runtime_metadata)


# ============================================
# DIAGNOSTICS
# ============================================

try:
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
