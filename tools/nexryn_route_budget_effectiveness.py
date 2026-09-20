"""Investigation-only active-route budget effectiveness runner.

This script compares route caps without mutating the checked-in production
budget. It launches main.py in a child process after applying an in-memory
production_budget override inside that process, captures stdout, parses the
observable report fields, and writes a structured JSON artifact.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "route_budget_effectiveness"
STATE_PATHS = (
    ROOT / "runtime" / "artifacts" / "runtime_data" / "training_assistant_state.json",
    ROOT / "runtime" / "cache" / "task_selection_memory.json",
)
FIXED_TASK_ORDER = [
    "elite_cognitive_task_20.json",
    "elite_cognitive_task_12.json",
    "elite_cognitive_task_06.json",
    "elite_cognitive_task_01.json",
    "elite_cognitive_task_17.json",
    "elite_cognitive_task_14.json",
    "elite_cognitive_task_16.json",
    "elite_cognitive_task_19.json",
    "elite_cognitive_task_02.json",
    "elite_cognitive_task_07.json",
    "elite_cognitive_task_09.json",
    "elite_cognitive_task_18.json",
    "elite_cognitive_task_05.json",
    "elite_cognitive_task_11.json",
    "elite_cognitive_task_15.json",
    "elite_cognitive_task_04.json",
    "elite_cognitive_task_13.json",
    "elite_cognitive_task_08.json",
    "elite_cognitive_task_10.json",
    "elite_cognitive_task_03.json",
]


@dataclass(frozen=True)
class RunConfig:
    route_cap: int
    repeat: int

    @property
    def config_id(self) -> str:
        return f"route_cap_{self.route_cap}"

    @property
    def repeat_id(self) -> str:
        return f"repeat_{self.repeat:03d}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-count", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--selection-mode", default="random")
    parser.add_argument("--mode", default="adaptive")
    parser.add_argument("--report-level", default=None)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    run_id = "route_budget_effectiveness_" + datetime.utcnow().strftime(
        "%Y%m%d_%H%M%S"
    )
    artifact_dir = ARTIFACT_ROOT / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    code_revision = _code_revision()
    code_state = _code_state_fingerprint()
    raw_runs = []
    for repeat in range(1, args.repeats + 1):
        for route_cap in (2, 6):
            raw_runs.append(
                _run_main(
                    RunConfig(route_cap=route_cap, repeat=repeat),
                    args=args,
                    artifact_dir=artifact_dir,
                )
            )

    report = _build_report(
        run_id=run_id,
        args=args,
        code_revision=code_revision,
        code_state=code_state,
        raw_runs=raw_runs,
        artifact_dir=artifact_dir,
    )
    artifact_path = artifact_dir / "active_route_budget_effectiveness.json"
    artifact_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True),
        encoding="utf-8",
    )
    print(str(artifact_path))
    return 0


def _run_main(
    config: RunConfig,
    *,
    args: argparse.Namespace,
    artifact_dir: Path,
) -> dict[str, Any]:
    log_path = artifact_dir / f"{config.config_id}_{config.repeat_id}.log"
    wrapper_path = artifact_dir / f"{config.config_id}_{config.repeat_id}_wrapper.py"
    argv = [
        "main.py",
        "--mode",
        args.mode,
        "--training-batch-size",
        str(args.task_count),
        "--selection-mode",
        args.selection_mode,
        "--random-seed",
        str(args.seed),
        "--reset-training-assistant",
    ]
    if args.report_level:
        argv.extend(["--report-level", args.report_level])
    wrapper_path.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "import runpy",
                "import sys",
                f"sys.path.insert(0, {str(ROOT)!r})",
                "import runtime.planning.production_budget as production_budget",
                f"production_budget.PRODUCTION_MAX_ACTIVE_ROUTES = {config.route_cap}",
                "import runtime.meta.meta_controller as meta_controller",
                f"meta_controller.PRODUCTION_MAX_ACTIVE_ROUTES = {config.route_cap}",
                "import runtime.pipeline.legacy_pipeline as legacy_pipeline",
                "import runtime.search.adaptive_search_policy as adaptive_search_policy",
                "import runtime.budget.experimental_budget_authority as budget_authority",
                "from runtime.learning.training_assistant import TrainingAssistant",
                f"_fixed_task_order = {FIXED_TASK_ORDER[:args.task_count]!r}",
                "_orig_select_batch = TrainingAssistant.select_batch",
                "def _patched_select_batch(self, task_files, *args, **kwargs):",
                "    report = _orig_select_batch(self, task_files, *args, **kwargs)",
                "    available = {str(task) for task in task_files or []}",
                "    selected = [task for task in _fixed_task_order if task in available]",
                "    if len(selected) == len(_fixed_task_order):",
                "        report = dict(report)",
                "        report['training_mode'] = 'fixed_experiment_order'",
                "        report['selected_task_count'] = len(selected)",
                "        report['selected_task_files'] = list(selected)",
                "        report['selected_elite_task_files'] = list(selected)",
                "        report['batch_size'] = len(selected)",
                "        selection = dict(report.get('selection_diversity_report') or {})",
                "        selection['selection_mode'] = 'fixed_experiment_order'",
                f"        selection['random_seed'] = {args.seed}",
                "        selection['selected_tasks'] = list(selected)",
                "        selection['fixed_order_override'] = True",
                "        report['selection_diversity_report'] = selection",
                "    return report",
                "TrainingAssistant.select_batch = _patched_select_batch",
                "_orig_apply_search_budget = adaptive_search_policy.AdaptiveSearchPolicyEngine.apply_budget",
                "def _patched_apply_search_budget(self, reasoning_budget, report):",
                "    reasoning_budget = _orig_apply_search_budget(self, reasoning_budget, report)",
                "    if reasoning_budget is not None and getattr(reasoning_budget, 'max_active_routes', 0) > 0:",
                f"        reasoning_budget.max_active_routes = min(int(reasoning_budget.max_active_routes), {config.route_cap})",
                "    return reasoning_budget",
                "adaptive_search_policy.AdaptiveSearchPolicyEngine.apply_budget = _patched_apply_search_budget",
                "_orig_resolve_budget = budget_authority.resolve_runtime_budget_authority",
                "def _patched_resolve_budget(*args, **kwargs):",
                "    result = _orig_resolve_budget(*args, **kwargs)",
                "    budget = result.get('budget') if isinstance(result, dict) else None",
                "    if budget is not None and getattr(budget, 'max_active_routes', 0) > 0:",
                f"        budget.max_active_routes = min(int(budget.max_active_routes), {config.route_cap})",
                "    binding = result.get('binding') if isinstance(result, dict) else None",
                "    if isinstance(binding, dict) and binding.get('effective_max_active_routes'):",
                f"        binding['effective_max_active_routes'] = min(int(binding['effective_max_active_routes']), {config.route_cap})",
                "    return result",
                "budget_authority.resolve_runtime_budget_authority = _patched_resolve_budget",
                "_orig_default_budget = legacy_pipeline.AdaptiveCognitivePipeline._default_reasoning_budget",
                "def _patched_default_budget(self):",
                "    budget = _orig_default_budget(self)",
                f"    budget['max_active_routes'] = {config.route_cap}",
                "    return budget",
                "legacy_pipeline.AdaptiveCognitivePipeline._default_reasoning_budget = _patched_default_budget",
                "_orig_configure_budget = legacy_pipeline.AdaptiveCognitivePipeline.configure_reasoning_budget",
                "def _patched_configure_budget(self, *args, **kwargs):",
                "    budget = _orig_configure_budget(self, *args, **kwargs)",
                f"    budget['max_active_routes'] = {config.route_cap}",
                "    return budget",
                "legacy_pipeline.AdaptiveCognitivePipeline.configure_reasoning_budget = _patched_configure_budget",
                f"sys.argv = {argv!r}",
                "runpy.run_path(str(Path('main.py')), run_name='__main__')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    backups = _backup_state_files(artifact_dir, config)
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(args.seed)
    env["PYTHONUNBUFFERED"] = "1"
    started = datetime.utcnow().isoformat()
    returncode = None
    timed_out = False
    try:
        with log_path.open("w", encoding="utf-8", newline="\n") as log_file:
            completed = subprocess.run(
                [sys.executable, "-u", str(wrapper_path)],
                cwd=ROOT,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=args.timeout,
                check=False,
                env=env,
            )
            returncode = completed.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        returncode = 124
    finally:
        _restore_state_files(backups)
    ended = datetime.utcnow().isoformat()
    text = log_path.read_text(encoding="utf-8", errors="replace")
    parsed = _parse_log(text)
    route_manifests = _load_route_manifests(parsed.get("human_report", {}).get("Run Id"))
    return {
        "configuration_id": config.config_id,
        "route_cap": config.route_cap,
        "repeat_id": config.repeat_id,
        "started_at": started,
        "ended_at": ended,
        "returncode": returncode,
        "timed_out": timed_out,
        "log_path": str(log_path),
        "wrapper_path": str(wrapper_path),
        "route_manifest_count": len(route_manifests),
        "route_manifests": route_manifests,
        **parsed,
    }


def _backup_state_files(artifact_dir: Path, config: RunConfig) -> list[tuple[Path, Path | None]]:
    backups = []
    backup_dir = artifact_dir / f"{config.config_id}_{config.repeat_id}_state_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in STATE_PATHS:
        if path.exists():
            backup = backup_dir / path.name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            backups.append((path, backup))
        else:
            backups.append((path, None))
    return backups


def _restore_state_files(backups: list[tuple[Path, Path | None]]) -> None:
    for path, backup in backups:
        if backup is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, path)


def _parse_log(text: str) -> dict[str, Any]:
    task_ids = re.findall(r"NEXRYN :: RUNNING TASK :: ([^\r\n]+)", text)
    selected_task_files = []
    match = re.search(r"selected_task_files:\s*(\[[^\r\n]+\])", text)
    if match:
        selected_task_files = _literal(match.group(1), [])
    if (
        not selected_task_files
        or any(str(item).startswith("... ") for item in selected_task_files)
    ) and task_ids:
        selected_task_files = list(task_ids)
    evaluation_results = _dicts_after_label(text, "EVALUATION RESULT:")
    budget_reports = _dicts_after_label(text, "COGNITIVE BUDGET REPORT:")
    evaluation_metrics = _dicts_after_label(text, "EVALUATION METRICS:")
    per_task = []
    count = max(len(task_ids), len(evaluation_results), len(budget_reports))
    for index in range(count):
        evaluation = _at(evaluation_results, index)
        budget = _at(budget_reports, index)
        metrics = _at(evaluation_metrics, index)
        per_task.append(
            {
                "task_id": _at(task_ids, index, f"task_{index + 1}"),
                "success_state": evaluation.get("success_state"),
                "exact_success": evaluation.get("exact_success") is True,
                "partial_success": evaluation.get("partial_success") is True,
                "accuracy": _number(evaluation.get("accuracy")),
                "final_score": _number(evaluation.get("final_score")),
                "residual_difference_count": _number(
                    evaluation.get("residual_analysis", {}).get(
                        "residual_difference_count"
                    )
                    if isinstance(evaluation.get("residual_analysis"), dict)
                    else evaluation.get("difference_count")
                ),
                "difference_count": _number(evaluation.get("difference_count")),
                "repair_attempts": _number(metrics.get("repair_attempts")),
                "repair_successes": _number(metrics.get("repair_successes")),
                "repair_failures": _number(metrics.get("repair_failures")),
                "repair_success_rate": _number(metrics.get("repair_success_rate")),
                "average_residual_reduction": _number(
                    metrics.get("average_residual_reduction")
                ),
                "max_active_routes": _number(budget.get("max_active_routes")),
                "effective_max_active_routes": _number(
                    budget.get("effective_max_active_routes")
                ),
                "max_reasoning_depth": _number(budget.get("max_reasoning_depth")),
                "max_dependency_depth": _number(budget.get("max_dependency_depth")),
                "max_hypotheses": _number(budget.get("max_hypotheses")),
            }
        )
    human = _human_report_fields(text)
    return {
        "selected_task_files": selected_task_files,
        "task_ids": task_ids,
        "task_count_observed": len(per_task),
        "per_task": per_task,
        "human_report": human,
    }


def _dicts_after_label(text: str, label: str) -> list[dict[str, Any]]:
    pattern = re.compile(re.escape(label) + r"\s*\n\s*(\{[^\n]*\})")
    return [
        item
        for item in (_literal(match.group(1), {}) for match in pattern.finditer(text))
        if isinstance(item, dict)
    ]


def _human_report_fields(text: str) -> dict[str, Any]:
    fields = {}
    for key in (
        "Run Id",
        "Total Wall Time",
        "Aggregate Active Compute Time",
        "Overall Search Quality",
        "Search Efficiency",
        "Search Coverage",
        "Average Route Quality",
        "Successful Blueprint Generations",
        "Synthesized Programs Persisted",
        "Arena Decision",
        "Highest Natural Runtime Level",
        "Phase-3 State",
        "Maximum Active Routes",
        "Selected Routes",
        "Admitted Routes",
        "Peak Concurrent Active Routes",
        "Routes Deferred or Rejected by Budget",
        "Maximum Reasoning Depth",
        "Maximum Dependency Depth",
        "Maximum Hypotheses",
        "Maximum Entered Reasoning Depth",
        "Maximum Completed Reasoning Depth",
        "Attempted Overrun State",
        "Prevented Overrun State",
        "Realized Overrun State",
        "Declared/Observed Active Routes",
        "Human Report Completeness Contract Version",
        "Canonical Completeness State",
        "Render Completeness State",
        "Delivery Completeness State",
        "Attribution State",
        "Lineage State",
        "Executed Routes",
        "Unique Useful Routes",
        "Duplicate Routes",
        "Low-Value Routes",
        "No Observable Routes",
        "Unmeasurable Routes",
        "Marginal Routes Executed",
        "Marginal Useful Routes",
        "Marginal Unique Contribution Rate",
        "Marginal Redundancy Rate",
        "Telemetry Consumed By Cognition",
        "Route Manifest Artifact",
    ):
        match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
        if match:
            fields[key] = match.group(1).strip()
    return fields


def _load_route_manifests(run_id: Any) -> list[dict[str, Any]]:
    run_token = _safe_token(run_id)
    if not run_token:
        return []
    root = ROOT / "runtime" / "artifacts" / "route_contribution"
    manifests = []
    for path in sorted(root.glob(f"{run_token}_*_route_contribution_manifest.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(manifest, dict):
            continue
        manifests.append(_compact_manifest(path, manifest))
    return manifests


def _compact_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    routes = [row for row in manifest.get("routes", []) if isinstance(row, dict)]
    return {
        "artifact_path": str(path),
        "run_id": manifest.get("run_id"),
        "task_id": manifest.get("task_id"),
        "route_cap": manifest.get("route_cap"),
        "attribution_completeness_state": manifest.get("attribution_completeness_state"),
        "lineage_continuity_state": manifest.get("lineage_continuity_state"),
        "identity_validation_state": manifest.get("identity_validation_state"),
        "aggregate_summary": manifest.get("aggregate_summary", {}),
        "collection_cost": manifest.get("collection_cost", {}),
        "routes": [_compact_route(row) for row in routes],
    }


def _compact_route(route: dict[str, Any]) -> dict[str, Any]:
    outputs = [row for row in route.get("outputs", []) if isinstance(row, dict)]
    return {
        "route_execution_id": route.get("route_execution_id"),
        "route_position": route.get("route_position"),
        "route_id": route.get("route_id"),
        "route_family": route.get("route_family"),
        "route_source": route.get("route_source"),
        "lifecycle_state": route.get("lifecycle_state"),
        "admitted": route.get("admitted"),
        "executed": route.get("executed"),
        "completed": route.get("completed"),
        "candidate_ids": route.get("candidate_ids", []),
        "program_ids": route.get("program_ids", []),
        "evidence_ids": route.get("evidence_ids", []),
        "arena_participation": route.get("arena_participation"),
        "repair_participation": route.get("repair_participation"),
        "output_count": route.get("output_count"),
        "unique_output_count": route.get("unique_output_count"),
        "duplicate_output_count": route.get("duplicate_output_count"),
        "contribution_state": route.get("contribution_state"),
        "outputs": [_compact_output(row) for row in outputs],
    }


def _compact_output(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "output_type": output.get("output_type"),
        "output_id": output.get("output_id"),
        "output_fingerprint": output.get("output_fingerprint"),
        "candidate_id": output.get("candidate_id"),
        "program_id": output.get("program_id"),
        "evidence_id": output.get("evidence_id"),
        "producer_component": output.get("producer_component"),
        "produced_at_stage": output.get("produced_at_stage"),
        "validation_state": output.get("validation_state"),
        "qualification_state": output.get("qualification_state"),
        "arena_state": output.get("arena_state"),
        "repair_state": output.get("repair_state"),
        "origin_route_execution_ids": output.get("origin_route_execution_ids", []),
    }


def _build_report(
    *,
    run_id: str,
    args: argparse.Namespace,
    code_revision: str,
    code_state: str,
    raw_runs: list[dict[str, Any]],
    artifact_dir: Path,
) -> dict[str, Any]:
    by_cap = {
        cap: [run for run in raw_runs if run["route_cap"] == cap]
        for cap in (2, 6)
    }
    summaries = {
        str(cap): _summarize_runs(runs)
        for cap, runs in by_cap.items()
    }
    paired = _paired_results(by_cap.get(2, []), by_cap.get(6, []))
    comparison = _comparison(summaries, paired)
    route_comparison = _route_comparison(by_cap.get(2, []), by_cap.get(6, []), paired)
    comparability = _comparability(raw_runs, args, code_revision, code_state)
    return {
        "system": "active_route_budget_effectiveness_investigation",
        "investigation_id": run_id,
        "created_at": datetime.utcnow().isoformat(),
        "artifact_dir": str(artifact_dir),
        "raw_measurements": raw_runs,
        "derived": {
            "comparability": comparability,
            "configuration_summaries": summaries,
            "paired_task_results": paired,
            "aggregate_comparison": comparison,
            "route_level_marginal_contribution": route_comparison,
            "route_redundancy": route_comparison.get("redundancy", {}),
            "budget_enforcement_proof": _budget_enforcement(raw_runs),
            "final_classification": _final_classification(
                comparability,
                comparison,
                route_comparison,
            ),
        },
    }


def _summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    tasks = [task for run in runs for task in run.get("per_task", [])]
    human = [run.get("human_report", {}) for run in runs]
    return {
        "run_count": len(runs),
        "episode_count": len(tasks),
        "task_order": runs[0].get("selected_task_files", []) if runs else [],
        "returncodes": [run.get("returncode") for run in runs],
        "exact_success_count": sum(1 for task in tasks if task.get("exact_success")),
        "exact_success_rate": _rate(
            sum(1 for task in tasks if task.get("exact_success")),
            len(tasks),
        ),
        "recoverable_failure_count": sum(
            1 for task in tasks if task.get("success_state") == "RECOVERABLE_FAILURE"
        ),
        "terminal_failure_count": sum(
            1
            for task in tasks
            if task.get("success_state")
            not in {"EXACT_SUCCESS", "RECOVERABLE_FAILURE", None}
        ),
        "accuracy": _stats([task.get("accuracy") for task in tasks]),
        "final_score": _stats([task.get("final_score") for task in tasks]),
        "residual_difference_count": _stats(
            [task.get("residual_difference_count") for task in tasks]
        ),
        "repair_attempts": _stats([task.get("repair_attempts") for task in tasks]),
        "repair_successes": _stats([task.get("repair_successes") for task in tasks]),
        "average_residual_reduction": _stats(
            [task.get("average_residual_reduction") for task in tasks]
        ),
        "budget": _latest_fields(
            human,
            [
                "Maximum Active Routes",
                "Selected Routes",
                "Admitted Routes",
                "Peak Concurrent Active Routes",
                "Routes Deferred or Rejected by Budget",
                "Maximum Reasoning Depth",
                "Maximum Dependency Depth",
                "Maximum Hypotheses",
                "Attempted Overrun State",
                "Prevented Overrun State",
                "Realized Overrun State",
                "Declared/Observed Active Routes",
            ],
        ),
        "search": _latest_fields(
            human,
            [
                "Overall Search Quality",
                "Search Efficiency",
                "Search Coverage",
                "Average Route Quality",
            ],
        ),
        "candidate": _latest_fields(
            human,
            [
                "Successful Blueprint Generations",
                "Synthesized Programs Persisted",
                "Arena Decision",
            ],
        ),
        "e4": _latest_fields(
            human,
            ["Phase-3 State", "Highest Natural Runtime Level"],
        ),
        "time": _latest_fields(
            human,
            ["Total Wall Time", "Aggregate Active Compute Time"],
        ),
        "human_report_contract": _latest_fields(
            human,
            [
                "Human Report Completeness Contract Version",
                "Canonical Completeness State",
                "Render Completeness State",
                "Delivery Completeness State",
            ],
        ),
        "route_contribution": _latest_fields(
            human,
            [
                "Attribution State",
                "Lineage State",
                "Executed Routes",
                "Unique Useful Routes",
                "Duplicate Routes",
                "Low-Value Routes",
                "No Observable Routes",
                "Unmeasurable Routes",
                "Marginal Routes Executed",
                "Marginal Useful Routes",
                "Marginal Unique Contribution Rate",
                "Marginal Redundancy Rate",
                "Telemetry Consumed By Cognition",
                "Route Manifest Artifact",
            ],
        ),
        "route_manifest_summary": _route_manifest_summary(runs),
    }


def _paired_results(runs_2: list[dict[str, Any]], runs_6: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    by_key_2 = {
        (run["repeat_id"], task["task_id"]): task
        for run in runs_2
        for task in run.get("per_task", [])
    }
    by_key_6 = {
        (run["repeat_id"], task["task_id"]): task
        for run in runs_6
        for task in run.get("per_task", [])
    }
    for key in sorted(set(by_key_2) & set(by_key_6)):
        left = by_key_2[key]
        right = by_key_6[key]
        delta_accuracy = _delta(right.get("accuracy"), left.get("accuracy"))
        delta_score = _delta(right.get("final_score"), left.get("final_score"))
        delta_residual = _delta(
            right.get("residual_difference_count"),
            left.get("residual_difference_count"),
        )
        if delta_accuracy is None and delta_score is None and delta_residual is None:
            classification = "INCOMPARABLE"
        elif (
            (delta_accuracy or 0) > 0
            or (delta_score or 0) > 0
            or (delta_residual is not None and delta_residual < 0)
        ):
            classification = "IMPROVED_WITH_6"
        elif (
            (delta_accuracy or 0) < 0
            or (delta_score or 0) < 0
            or (delta_residual is not None and delta_residual > 0)
        ):
            classification = "REGRESSED_WITH_6"
        else:
            classification = "UNCHANGED"
        pairs.append(
            {
                "repeat_id": key[0],
                "task_id": key[1],
                "route_cap_2": left,
                "route_cap_6": right,
                "delta": {
                    "accuracy": delta_accuracy,
                    "final_score": delta_score,
                    "residual_difference_count": delta_residual,
                },
                "classification": classification,
            }
        )
    return pairs


def _comparison(summaries: dict[str, Any], paired: list[dict[str, Any]]) -> dict[str, Any]:
    a = summaries.get("2", {})
    b = summaries.get("6", {})
    return {
        "delta_exact_success_rate": _delta(
            b.get("exact_success_rate"),
            a.get("exact_success_rate"),
        ),
        "delta_mean_accuracy": _delta(
            b.get("accuracy", {}).get("mean"),
            a.get("accuracy", {}).get("mean"),
        ),
        "delta_median_accuracy": _delta(
            b.get("accuracy", {}).get("median"),
            a.get("accuracy", {}).get("median"),
        ),
        "delta_mean_final_score": _delta(
            b.get("final_score", {}).get("mean"),
            a.get("final_score", {}).get("mean"),
        ),
        "delta_median_final_score": _delta(
            b.get("final_score", {}).get("median"),
            a.get("final_score", {}).get("median"),
        ),
        "delta_mean_residual": _delta(
            b.get("residual_difference_count", {}).get("mean"),
            a.get("residual_difference_count", {}).get("mean"),
        ),
        "paired_improved_with_6": sum(
            1 for item in paired if item["classification"] == "IMPROVED_WITH_6"
        ),
        "paired_regressed_with_6": sum(
            1 for item in paired if item["classification"] == "REGRESSED_WITH_6"
        ),
        "paired_unchanged": sum(
            1 for item in paired if item["classification"] == "UNCHANGED"
        ),
        "paired_incomparable": sum(
            1 for item in paired if item["classification"] == "INCOMPARABLE"
        ),
    }


def _route_manifest_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    manifests = [
        manifest
        for run in runs
        for manifest in run.get("route_manifests", [])
        if isinstance(manifest, dict)
    ]
    routes = [
        route
        for manifest in manifests
        for route in manifest.get("routes", [])
        if isinstance(route, dict)
    ]
    marginal = [
        route for route in routes
        if 3 <= int(route.get("route_position") or 0) <= 6
    ]
    outputs = [
        output
        for route in routes
        for output in route.get("outputs", [])
        if isinstance(output, dict)
    ]
    return {
        "manifest_count": len(manifests),
        "attribution_states": sorted({
            str(manifest.get("attribution_completeness_state"))
            for manifest in manifests
            if manifest.get("attribution_completeness_state")
        }),
        "lineage_states": sorted({
            str(manifest.get("lineage_continuity_state"))
            for manifest in manifests
            if manifest.get("lineage_continuity_state")
        }),
        "executed_routes": sum(1 for route in routes if route.get("executed") is True),
        "marginal_routes_executed": sum(1 for route in marginal if route.get("executed") is True),
        "marginal_unique_useful_count": sum(
            1 for route in marginal
            if route.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"
        ),
        "marginal_duplicate_count": sum(
            1 for route in marginal
            if route.get("contribution_state") == "DUPLICATE_CONTRIBUTION"
        ),
        "marginal_low_value_count": sum(
            1 for route in marginal
            if route.get("contribution_state") == "LOW_VALUE_CONTRIBUTION"
        ),
        "marginal_no_observable_count": sum(
            1 for route in marginal
            if route.get("contribution_state") == "NO_OBSERVABLE_CONTRIBUTION"
        ),
        "marginal_unmeasurable_count": sum(
            1 for route in marginal
            if route.get("contribution_state") == "CONTRIBUTION_NOT_MEASURABLE"
        ),
        "marginal_unique_contribution_rate": _rate(
            sum(
                1 for route in marginal
                if route.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"
            ),
            sum(1 for route in marginal if route.get("executed") is True),
        ),
        "marginal_redundancy_rate": _rate(
            sum(
                1 for route in marginal
                if route.get("contribution_state") == "DUPLICATE_CONTRIBUTION"
            ),
            sum(1 for route in marginal if route.get("executed") is True),
        ),
        "candidate_output_count": sum(1 for output in outputs if output.get("output_type") == "candidate"),
        "program_output_count": sum(1 for output in outputs if output.get("output_type") == "program"),
        "evidence_output_count": sum(1 for output in outputs if output.get("output_type") == "evidence"),
        "arena_output_count": sum(1 for output in outputs if output.get("producer_component") == "cognitive_candidate_arena"),
        "repair_output_count": sum(1 for output in outputs if output.get("repair_state")),
        "collection_time_seconds": round(sum(
            float((manifest.get("collection_cost") or {}).get("collection_time_seconds") or 0.0)
            for manifest in manifests
        ), 6),
        "manifest_size_bytes": sum(
            int((manifest.get("collection_cost") or {}).get("manifest_size_bytes") or 0)
            for manifest in manifests
        ),
        "record_count": sum(
            int((manifest.get("collection_cost") or {}).get("record_count") or 0)
            for manifest in manifests
        ),
        "by_position": _route_position_summary(marginal),
        "by_family": _route_family_summary(marginal),
    }


def _route_position_summary(routes: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for position in (3, 4, 5, 6):
        rows = [route for route in routes if int(route.get("route_position") or 0) == position]
        executed = sum(1 for route in rows if route.get("executed") is True)
        useful = sum(1 for route in rows if route.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION")
        result[str(position)] = {
            "executed": executed,
            "unique_useful": useful,
            "duplicate": sum(1 for route in rows if route.get("contribution_state") == "DUPLICATE_CONTRIBUTION"),
            "low_value": sum(1 for route in rows if route.get("contribution_state") == "LOW_VALUE_CONTRIBUTION"),
            "no_observable": sum(1 for route in rows if route.get("contribution_state") == "NO_OBSERVABLE_CONTRIBUTION"),
            "unmeasurable": sum(1 for route in rows if route.get("contribution_state") == "CONTRIBUTION_NOT_MEASURABLE"),
            "unique_useful_rate": _rate(useful, executed),
        }
    return result


def _route_family_summary(routes: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for route in routes:
        by_family.setdefault(str(route.get("route_id") or route.get("route_family") or "unknown"), []).append(route)
    result = {}
    for family, rows in sorted(by_family.items()):
        result[family] = {
            "execution_count": sum(1 for route in rows if route.get("executed") is True),
            "unique_useful_count": sum(1 for route in rows if route.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"),
            "duplicate_count": sum(1 for route in rows if route.get("contribution_state") == "DUPLICATE_CONTRIBUTION"),
            "low_value_count": sum(1 for route in rows if route.get("contribution_state") == "LOW_VALUE_CONTRIBUTION"),
            "no_output_count": sum(1 for route in rows if route.get("contribution_state") == "NO_OBSERVABLE_CONTRIBUTION"),
            "arena_contribution_count": sum(1 for route in rows if route.get("arena_participation") is True),
            "repair_contribution_count": sum(1 for route in rows if route.get("repair_participation") is True),
        }
    return result


def _route_comparison(
    runs_2: list[dict[str, Any]],
    runs_6: list[dict[str, Any]],
    paired: list[dict[str, Any]],
) -> dict[str, Any]:
    cap2_outputs = _fingerprints_by_type(runs_2)
    cap6_base_outputs = _fingerprints_by_type(runs_6, route_positions={1, 2})
    cap6_marginal_outputs = _fingerprints_by_type(runs_6, route_positions={3, 4, 5, 6})
    missing = {
        output_type: sorted(
            set(values)
            - set(cap2_outputs.get(output_type, set()))
            - set(cap6_base_outputs.get(output_type, set()))
        )
        for output_type, values in cap6_marginal_outputs.items()
    }
    summary2 = _route_manifest_summary(runs_2)
    summary6 = _route_manifest_summary(runs_6)
    tasks_with_marginal_value = _tasks_with_marginal_value(runs_6)
    paired_by_task = {item.get("task_id"): item for item in paired}
    cognitive_differences = [
        task_id
        for task_id in tasks_with_marginal_value
        if paired_by_task.get(task_id, {}).get("classification") == "UNCHANGED"
    ]
    decisive = [
        task_id
        for task_id in tasks_with_marginal_value
        if paired_by_task.get(task_id, {}).get("classification") in {
            "IMPROVED_WITH_6",
            "REGRESSED_WITH_6",
        }
    ]
    return {
        "cap_2": summary2,
        "cap_6": summary6,
        "fingerprints_only_under_cap6_marginal": missing,
        "unique_candidates_only_under_cap6": len(missing.get("candidate", [])),
        "unique_programs_only_under_cap6": len(missing.get("program", [])),
        "unique_evidence_only_under_cap6": len(missing.get("evidence", [])),
        "tasks_with_marginal_value": tasks_with_marginal_value,
        "tasks_with_outcome_invariance_but_cognitive_difference": cognitive_differences,
        "decisive_marginal_tasks": decisive,
        "non_decisive_useful_tasks": [
            task_id for task_id in tasks_with_marginal_value if task_id not in decisive
        ],
        "redundancy": {
            "marginal_duplicate_route_count": summary6["marginal_duplicate_count"],
            "marginal_duplicate_output_count": _duplicate_output_count(runs_6, {3, 4, 5, 6}),
            "marginal_redundancy_rate": summary6["marginal_redundancy_rate"],
        },
        "first_downstream_value_loss_boundary": (
            "ARENA_DECISION"
            if summary6.get("arena_output_count", 0) > 0
            and not decisive
            else "NOT_IDENTIFIED"
        ),
        "cognitive_diversity_effect": (
            "COGNITION_DIFFERENT"
            if tasks_with_marginal_value
            else "COGNITION_INVARIANT_OR_NOT_OBSERVED"
        ),
    }


def _fingerprints_by_type(
    runs: list[dict[str, Any]],
    route_positions: set[int] | None = None,
) -> dict[str, set[str]]:
    values: dict[str, set[str]] = {}
    for _run, _manifest, route, output in _iter_outputs(runs):
        if route_positions is not None and int(route.get("route_position") or 0) not in route_positions:
            continue
        output_type = str(output.get("output_type") or "unknown")
        fingerprint = output.get("output_fingerprint") or output.get("output_id")
        if fingerprint:
            values.setdefault(output_type, set()).add(str(fingerprint))
    return values


def _tasks_with_marginal_value(runs: list[dict[str, Any]]) -> list[str]:
    task_ids = set()
    for run in runs:
        for manifest in run.get("route_manifests", []):
            for route in manifest.get("routes", []):
                if (
                    isinstance(route, dict)
                    and 3 <= int(route.get("route_position") or 0) <= 6
                    and route.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"
                ):
                    task_ids.add(_task_identity(manifest.get("task_id")))
    return sorted(task_ids)


def _duplicate_output_count(runs: list[dict[str, Any]], route_positions: set[int]) -> int:
    count = 0
    for _run, _manifest, route, _output in _iter_outputs(runs):
        if int(route.get("route_position") or 0) in route_positions:
            count += int(route.get("duplicate_output_count") or 0)
    return count


def _iter_outputs(runs: list[dict[str, Any]]):
    for run in runs:
        for manifest in run.get("route_manifests", []):
            if not isinstance(manifest, dict):
                continue
            for route in manifest.get("routes", []):
                if not isinstance(route, dict):
                    continue
                for output in route.get("outputs", []):
                    if isinstance(output, dict):
                        yield run, manifest, route, output


def _comparability(
    raw_runs: list[dict[str, Any]],
    args: argparse.Namespace,
    code_revision: str,
    code_state: str,
) -> dict[str, Any]:
    task_orders = [run.get("selected_task_files", []) for run in raw_runs]
    same_task_order = bool(task_orders) and all(order == task_orders[0] for order in task_orders)
    returncodes_ok = all(run.get("returncode") == 0 for run in raw_runs)
    classification = "COMPARABLE" if same_task_order and returncodes_ok else "PARTIALLY_COMPARABLE"
    return {
        "classification": classification,
        "code_revision": code_revision,
        "code_state_fingerprint": code_state,
        "runtime_version": f"python {sys.version.split()[0]}",
        "mode": args.mode,
        "report_level": args.report_level or "default",
        "selection_mode": args.selection_mode,
        "seed": args.seed,
        "same_task_order": same_task_order,
        "task_order": task_orders[0] if task_orders else [],
        "route_cap_only_intended_difference": True,
        "reasoning_depth": "2",
        "dependency_depth": "2",
        "hypothesis_cap": "unchanged production profile value",
        "repair_configuration": "unchanged",
        "arena_configuration": "unchanged",
        "authority_configuration": "unchanged",
        "randomness_determinism_state": (
            "seeded task selection; runtime internals may still contain non-determinism"
        ),
        "returncodes_ok": returncodes_ok,
    }


def _budget_enforcement(raw_runs: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    valid = True
    for run in raw_runs:
        human = run.get("human_report", {})
        cap = run.get("route_cap")
        peak = _number(human.get("Peak Concurrent Active Routes"))
        realized = human.get("Realized Overrun State")
        ok = peak is not None and peak <= cap and realized == "NO_REALIZED_OVERRUN"
        valid = valid and bool(ok)
        rows.append(
            {
                "configuration_id": run.get("configuration_id"),
                "repeat_id": run.get("repeat_id"),
                "route_cap": cap,
                "peak_active_routes": peak,
                "realized_overrun_state": realized,
                "valid": ok,
            }
        )
    return {"valid": valid, "runs": rows}


def _final_classification(
    comparability: dict[str, Any],
    comparison: dict[str, Any],
    route_comparison: dict[str, Any],
) -> str:
    if comparability.get("classification") != "COMPARABLE":
        return "INSUFFICIENT_EVIDENCE"
    if comparison.get("paired_improved_with_6", 0) > comparison.get(
        "paired_regressed_with_6", 0
    ):
        return "6_PROVIDES_QUALITY_GAIN_AT_MEASURED_COST"
    if comparison.get("paired_regressed_with_6", 0) > comparison.get(
        "paired_improved_with_6", 0
    ):
        return "6_REGRESSED_OUTCOMES_IN_THIS_SAMPLE"
    if route_comparison.get("tasks_with_marginal_value"):
        return "KEEP_6_FOR_COGNITIVE_DIVERSITY"
    return "NO_MEANINGFUL_DIFFERENCE_OR_NOT_OBSERVABLE"


def _latest_fields(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, Any]:
    result = {}
    for key in keys:
        values = [row.get(key) for row in rows if row.get(key) is not None]
        result[key] = values[-1] if values else None
    return result


def _stats(values: list[Any]) -> dict[str, Any]:
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "count": len(numeric),
        "mean": round(mean(numeric), 6),
        "median": round(median(numeric), 6),
        "min": min(numeric),
        "max": max(numeric),
    }


def _rate(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round(count / total, 6)


def _delta(right: Any, left: Any) -> float | None:
    if not isinstance(right, (int, float)) or not isinstance(left, (int, float)):
        return None
    return round(float(right) - float(left), 6)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0))


def _literal(text: str, default: Any) -> Any:
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return default


def _at(items: list[Any], index: int, default: Any = None) -> Any:
    if 0 <= index < len(items):
        return items[index]
    return default if default is not None else {}


def _task_identity(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("value") or value.get("task_id") or value.get("task")
    text = str(value or "")
    if text.startswith("{") and "value" in text:
        parsed = _literal(text, {})
        if isinstance(parsed, dict):
            text = str(parsed.get("value") or parsed.get("task_id") or parsed.get("task") or text)
    text = text.replace("\\\\", "\\").replace("/", "\\")
    return text.rsplit("\\", 1)[-1] if "\\" in text else text


def _code_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _code_state_fingerprint() -> str:
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--", "."],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        diff = ""
    return hashlib.sha256(diff.encode("utf-8")).hexdigest()


def _safe_token(value: Any) -> str:
    return "".join(
        ch if ch.isalnum() or ch in {"-", "_"} else "_"
        for ch in str(value or "")
    )[:120]


if __name__ == "__main__":
    raise SystemExit(main())
