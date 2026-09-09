"""Experiment-only balanced marginal route-order deconfounding runner."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "route_order_deconfounding"
STATE_PATHS = (
    ROOT / "runtime" / "artifacts" / "runtime_data" / "training_assistant_state.json",
    ROOT / "runtime" / "cache" / "task_selection_memory.json",
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.experiments.route_order_deconfounding import (  # noqa: E402
    build_order_design,
    run_route_order_deconfounding_analysis,
)
from tools.nexryn_route_budget_effectiveness import (  # noqa: E402
    FIXED_TASK_ORDER,
    _code_revision,
    _code_state_fingerprint,
    _load_route_manifests,
    _parse_log,
)


PRODUCTION_CAP6_ORDER = [
    "causal_validation",
    "color_mapping",
    "contradiction_checks",
    "dependency_reasoning",
    "identity_governance",
    "object_tracking",
    "process_semantics",
    "semantic_to_transformation_compiler",
    "spatial_reasoning",
    "transformation_compilation",
    "transformation_execution",
    "truth_governance",
]


@dataclass(frozen=True)
class Condition:
    condition_id: str
    order_id: str
    marginal_order: list[str]
    full_order: list[str]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--selection-mode", default="random")
    parser.add_argument("--mode", default="adaptive")
    parser.add_argument("--report-level", default=None)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    artifact_dir = ARTIFACT_ROOT / timestamp
    artifact_dir.mkdir(parents=True, exist_ok=True)

    order_design = build_order_design(PRODUCTION_CAP6_ORDER)
    (artifact_dir / "deconfounding_order_design.pre_run.json").write_text(
        json.dumps(order_design, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    conditions = [
        Condition(
            condition_id=row["condition_id"],
            order_id=row["order_id"],
            marginal_order=list(row["marginal_routes"]),
            full_order=list(row["full_route_order"]),
        )
        for row in order_design["conditions"]
    ]
    raw_runs = []
    for condition in conditions:
        raw_runs.append(
            _run_condition(
                condition,
                args=args,
                artifact_dir=artifact_dir,
            )
        )
    task_order = FIXED_TASK_ORDER[: args.task_count]
    summary = run_route_order_deconfounding_analysis(
        raw_runs=raw_runs,
        task_order=task_order,
        order_design=order_design,
        output_dir=artifact_dir,
        seed=args.seed,
    )
    summary["code_revision"] = _code_revision()
    summary["code_state_fingerprint"] = _code_state_fingerprint()
    (artifact_dir / "route_order_deconfounding_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    print(str(artifact_dir))
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


def _run_condition(
    condition: Condition,
    *,
    args: argparse.Namespace,
    artifact_dir: Path,
) -> dict[str, Any]:
    log_path = artifact_dir / f"condition_{condition.condition_id}.log"
    wrapper_path = artifact_dir / f"condition_{condition.condition_id}_wrapper.py"
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
                "production_budget.PRODUCTION_MAX_ACTIVE_ROUTES = 6",
                "import runtime.meta.meta_controller as meta_controller",
                "meta_controller.PRODUCTION_MAX_ACTIVE_ROUTES = 6",
                "import runtime.pipeline.legacy_pipeline as legacy_pipeline",
                "import runtime.search.adaptive_search_policy as adaptive_search_policy",
                "import runtime.budget.experimental_budget_authority as budget_authority",
                "import importlib",
                "tool_selection_module = importlib.import_module('runtime.planning.tool_selection_engine')",
                "from runtime.learning.training_assistant import TrainingAssistant",
                f"_fixed_task_order = {FIXED_TASK_ORDER[:args.task_count]!r}",
                f"_condition_id = {condition.condition_id!r}",
                f"_order_id = {condition.order_id!r}",
                f"_full_order = {condition.full_order!r}",
                "def _ordered_subset(values):",
                "    current = set(values or [])",
                "    ordered = [route for route in _full_order if route in current]",
                "    ordered.extend(route for route in values or [] if route not in ordered)",
                "    return ordered",
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
                "        diversity = dict(report.get('selection_diversity_report') or {})",
                "        diversity['selection_mode'] = 'fixed_experiment_order'",
                f"        diversity['random_seed'] = {args.seed}",
                "        diversity['selected_tasks'] = list(selected)",
                "        diversity['fixed_order_override'] = True",
                "        report['selection_diversity_report'] = diversity",
                "    return report",
                "TrainingAssistant.select_batch = _patched_select_batch",
                "_orig_build_report = tool_selection_module.ToolSelectionEngine.build_report",
                "def _patched_build_report(self, selection):",
                "    report = dict(_orig_build_report(self, selection))",
                "    report['enabled_tools'] = _ordered_subset(report.get('enabled_tools') or [])",
                "    report['selected_tools'] = _ordered_subset(report.get('selected_tools') or report.get('enabled_tools') or [])",
                "    report['experimental_route_order_condition'] = _condition_id",
                "    report['experimental_route_order_id'] = _order_id",
                "    report['experimental_route_order_authority'] = 'NONE'",
                "    report['experimental_route_order_scope'] = 'EXPERIMENT_HARNESS_ONLY'",
                "    return report",
                "tool_selection_module.ToolSelectionEngine.build_report = _patched_build_report",
                "_orig_apply_search_budget = adaptive_search_policy.AdaptiveSearchPolicyEngine.apply_budget",
                "def _patched_apply_search_budget(self, reasoning_budget, report):",
                "    reasoning_budget = _orig_apply_search_budget(self, reasoning_budget, report)",
                "    if reasoning_budget is not None and getattr(reasoning_budget, 'max_active_routes', 0) > 0:",
                "        reasoning_budget.max_active_routes = min(int(reasoning_budget.max_active_routes), 6)",
                "    return reasoning_budget",
                "adaptive_search_policy.AdaptiveSearchPolicyEngine.apply_budget = _patched_apply_search_budget",
                "_orig_resolve_budget = budget_authority.resolve_runtime_budget_authority",
                "def _patched_resolve_budget(*args, **kwargs):",
                "    result = _orig_resolve_budget(*args, **kwargs)",
                "    budget = result.get('budget') if isinstance(result, dict) else None",
                "    if budget is not None and getattr(budget, 'max_active_routes', 0) > 0:",
                "        budget.max_active_routes = min(int(budget.max_active_routes), 6)",
                "    binding = result.get('binding') if isinstance(result, dict) else None",
                "    if isinstance(binding, dict) and binding.get('effective_max_active_routes'):",
                "        binding['effective_max_active_routes'] = min(int(binding['effective_max_active_routes']), 6)",
                "    return result",
                "budget_authority.resolve_runtime_budget_authority = _patched_resolve_budget",
                "_orig_default_budget = legacy_pipeline.AdaptiveCognitivePipeline._default_reasoning_budget",
                "def _patched_default_budget(self):",
                "    budget = _orig_default_budget(self)",
                "    budget['max_active_routes'] = 6",
                "    return budget",
                "legacy_pipeline.AdaptiveCognitivePipeline._default_reasoning_budget = _patched_default_budget",
                "_orig_configure_budget = legacy_pipeline.AdaptiveCognitivePipeline.configure_reasoning_budget",
                "def _patched_configure_budget(self, *args, **kwargs):",
                "    budget = _orig_configure_budget(self, *args, **kwargs)",
                "    budget['max_active_routes'] = 6",
                "    return budget",
                "legacy_pipeline.AdaptiveCognitivePipeline.configure_reasoning_budget = _patched_configure_budget",
                f"sys.argv = {argv!r}",
                "runpy.run_path(str(Path('main.py')), run_name='__main__')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    backups = _backup_state_files(artifact_dir, condition)
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
        "condition_id": condition.condition_id,
        "order_id": condition.order_id,
        "route_cap": 6,
        "marginal_order": condition.marginal_order,
        "full_order": condition.full_order,
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


def _backup_state_files(artifact_dir: Path, condition: Condition) -> list[tuple[Path, Path | None]]:
    backups = []
    backup_dir = artifact_dir / f"condition_{condition.condition_id}_state_backup"
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


if __name__ == "__main__":
    raise SystemExit(main())
