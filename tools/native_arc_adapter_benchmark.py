from __future__ import annotations

import json
from pathlib import Path

from runtime.evaluation.arc_hidden_test_harness import NativeARCEvaluationHarness
from runtime.evaluation.native_arc_solver_adapter import NativeARCSolverAdapter

ROOT = Path(r"C:\Users\SERVICE INFO\AMIS")
TASK_DIR = ROOT / "data" / "training"
TASK_LIMIT = 5


def main() -> None:
    tasks = sorted(TASK_DIR.glob("task_*.json"))[:TASK_LIMIT]
    harness = NativeARCEvaluationHarness()
    exact = 0
    total_outputs = 0
    unsupported = 0
    conflicting = 0
    predictions = 0
    diversity_state = "ATTEMPT_DIVERSITY_NOT_AVAILABLE"
    for task_path in tasks:
        data = json.loads(task_path.read_text(encoding="utf-8"))
        try:
            report = harness.evaluate_task(data, task_path.stem, NativeARCSolverAdapter())
            total_outputs += len(report["test_reports"])
            exact += sum(1 for item in report["test_reports"] if item["exact_match"])
            predictions += len(report["attempts"])
            print(f"{task_path.name}: task_score={report['task_score']} exact_tests={sum(1 for item in report['test_reports'] if item['exact_match'])} attempts={len(report['attempts'])}")
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            print(f"{task_path.name}: FAIL_CLOSED: {reason}")
            unsupported += 1
            if "TRAINING_TRANSFORMATION_CONFLICT" in str(exc):
                conflicting += 1
    aggregate = 0.0 if total_outputs == 0 else round(exact / total_outputs, 4)
    print("SUMMARY")
    print(f"tasks={len(tasks)}")
    print(f"total_outputs={total_outputs}")
    print(f"exact={exact}")
    print(f"aggregate_exact_accuracy={aggregate}")
    print(f"unsupported_tasks={unsupported}")
    print(f"conflicting_tasks={conflicting}")
    print(f"predictions_produced={predictions}")
    print(f"attempt_diversity_state={diversity_state}")


if __name__ == "__main__":
    main()
