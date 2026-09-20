"""Run P3 held-out route-value prediction in shadow-only mode."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "p3_route_predictive_validation"
STATE_PATHS = (
    ROOT / "runtime" / "artifacts" / "runtime_data" / "training_assistant_state.json",
    ROOT / "runtime" / "cache" / "task_selection_memory.json",
)

from runtime.experiments.p3_route_predictive_validation import (  # noqa: E402
    default_held_out_task_ids,
    development_task_ids,
    freeze_signal_contract,
    run_p3_analysis,
)
from tools.nexryn_route_budget_effectiveness import (  # noqa: E402
    _code_revision,
    _code_state_fingerprint,
    _load_route_manifests,
    _parse_log,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--selection-mode", default="random")
    parser.add_argument("--mode", default="adaptive")
    parser.add_argument("--report-level", default=None)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    artifact_dir = ARTIFACT_ROOT / timestamp
    artifact_dir.mkdir(parents=True, exist_ok=True)

    development_ids = development_task_ids()
    held_out_ids = default_held_out_task_ids(args.held_out_count)
    contract = freeze_signal_contract(
        development_ids=development_ids,
        held_out_ids=held_out_ids,
    )
    contract_path = artifact_dir / "p3_signal_contract.pre_run.json"
    prediction_path = artifact_dir / "p3_shadow_predictions.jsonl"
    contract_path.write_text(
        json.dumps(contract, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    raw_run = _run_held_out(
        held_out_ids=held_out_ids,
        contract_path=contract_path,
        prediction_path=prediction_path,
        artifact_dir=artifact_dir,
        args=args,
    )
    predictions = _read_predictions(prediction_path)
    summary = run_p3_analysis(
        raw_run=raw_run,
        development_ids=development_ids,
        held_out_ids=held_out_ids,
        contract=contract,
        predictions=predictions,
        output_dir=artifact_dir,
    )
    summary["code_revision"] = _code_revision()
    summary["code_state_fingerprint"] = _code_state_fingerprint()
    (artifact_dir / "p3_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    print(str(artifact_dir))
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


def _run_held_out(
    *,
    held_out_ids: list[str],
    contract_path: Path,
    prediction_path: Path,
    artifact_dir: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    log_path = artifact_dir / "p3_held_out_run.log"
    wrapper_path = artifact_dir / "p3_held_out_wrapper.py"
    argv = [
        "main.py",
        "--mode",
        args.mode,
        "--training-batch-size",
        str(len(held_out_ids)),
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
                "import json",
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
                "runtime_budget_enforcer = importlib.import_module('runtime.budget.runtime_budget_enforcer')",
                "from runtime.learning.training_assistant import TrainingAssistant",
                "from runtime.experiments.p3_route_predictive_validation import score_snapshot",
                f"_held_out_ids = {held_out_ids!r}",
                f"_contract_path = Path({str(contract_path)!r})",
                f"_prediction_path = Path({str(prediction_path)!r})",
                "_contract = json.loads(_contract_path.read_text(encoding='utf-8'))",
                "_prediction_path.parent.mkdir(parents=True, exist_ok=True)",
                "_prediction_path.write_text('', encoding='utf-8')",
                "_orig_select_batch = TrainingAssistant.select_batch",
                "def _patched_select_batch(self, task_files, *args, **kwargs):",
                "    report = _orig_select_batch(self, task_files, *args, **kwargs)",
                "    available = {str(task) for task in task_files or []}",
                "    selected = [task for task in _held_out_ids if task in available]",
                "    if len(selected) == len(_held_out_ids):",
                "        report = dict(report)",
                "        report['training_mode'] = 'p3_fixed_held_out_order'",
                "        report['selected_task_count'] = len(selected)",
                "        report['selected_task_files'] = list(selected)",
                "        report['selected_elite_task_files'] = []",
                "        report['batch_size'] = len(selected)",
                "        diversity = dict(report.get('selection_diversity_report') or {})",
                "        diversity['selection_mode'] = 'p3_fixed_held_out_order'",
                f"        diversity['random_seed'] = {args.seed}",
                "        diversity['selected_tasks'] = list(selected)",
                "        diversity['held_out_override'] = True",
                "        report['selection_diversity_report'] = diversity",
                "    return report",
                "TrainingAssistant.select_batch = _patched_select_batch",
                "_orig_pre_route_snapshots = runtime_budget_enforcer.RuntimeBudgetEnforcer._pre_route_snapshots",
                "def _patched_pre_route_snapshots(self, *args, **kwargs):",
                "    snapshots, linkages, overhead = _orig_pre_route_snapshots(self, *args, **kwargs)",
                "    with _prediction_path.open('a', encoding='utf-8', newline='\\n') as handle:",
                "        for snapshot in snapshots:",
                "            position = int(snapshot.get('route_position') or 0)",
                "            if position in {3, 4, 5, 6}:",
                "                prediction = score_snapshot(snapshot, _contract)",
                "                handle.write(json.dumps(prediction, sort_keys=True, default=str) + '\\n')",
                "    return snapshots, linkages, overhead",
                "runtime_budget_enforcer.RuntimeBudgetEnforcer._pre_route_snapshots = _patched_pre_route_snapshots",
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
    backups = _backup_state_files(artifact_dir)
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
        "configuration_id": "p3_held_out_cap_6_production_order",
        "route_cap": 6,
        "started_at": started,
        "ended_at": ended,
        "returncode": returncode,
        "timed_out": timed_out,
        "log_path": str(log_path),
        "wrapper_path": str(wrapper_path),
        "prediction_path": str(prediction_path),
        "route_manifest_count": len(route_manifests),
        "route_manifests": route_manifests,
        **parsed,
    }


def _read_predictions(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _backup_state_files(artifact_dir: Path) -> list[tuple[Path, Path | None]]:
    backups = []
    backup_dir = artifact_dir / "state_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in STATE_PATHS:
        if path.exists():
            backup = backup_dir / path.name
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
