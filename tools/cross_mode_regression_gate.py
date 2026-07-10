"""Cross-mode parity regression gate.

Default mode is intentionally lightweight for CI.  Use --run-main to execute
real adaptive and deep/full runtime commands with a fixed seed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.validation import (
    CrossModeParityValidator,
    DifferentialExecutionHarness,
)


def synthetic_report(mode: str, *, report_level: str = "normal") -> dict:
    sections = {
        "runtime_metadata",
        "performance_report",
        "COGNITIVE_RUNTIME_REPORT",
        "COGNITIVE_EXECUTION_ENGINE_REPORT",
        "EXECUTION_BINDING_REPORT",
        "SHARED_COGNITIVE_STATE_REPORT",
        "truth_candidates",
        "truth_commits",
        "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT",
    }
    if report_level == "full":
        sections |= {"DEEP_MODE_OPTIMIZATION_REPORT", "FULL_REPORT_DETAIL"}
    report = {key: {} for key in sections}
    report["runtime_metadata"] = {
        "mode": mode,
        "execution_time": 1.0 if mode == "adaptive" else 1.4,
        "governance_budget_seconds": 10.0 if mode == "adaptive" else 20.0,
        "execution_profile": {
            "execution_profile": mode,
            "cognitive_pipeline": "adaptive",
        },
    }
    report["COGNITIVE_RUNTIME_REPORT"] = {
        "runtime_registry": {
            runtime_id: {"runtime_id": runtime_id}
            for runtime_id in (
                "reasoning_runtime",
                "search_runtime",
                "truth_runtime",
                "memory_runtime",
                "evaluation_runtime",
            )
        }
    }
    report["COGNITIVE_EXECUTION_ENGINE_REPORT"] = {
        "lifecycle_coverage": 1.0,
        "synthetic_execution_count": 0,
        "execution_tree": [
            {
                "runtime_id": "execution_runtime",
                "children": [
                    {"runtime_id": "reasoning_runtime", "children": []},
                    {"runtime_id": "search_runtime", "children": []},
                    {"runtime_id": "truth_runtime", "children": []},
                    {"runtime_id": "memory_runtime", "children": []},
                    {"runtime_id": "evaluation_runtime", "children": []},
                ],
            }
        ],
    }
    report["EXECUTION_BINDING_REPORT"] = {
        "binding_coverage": 1.0,
        "timing_coverage": 1.0,
        "registry_synchronization": "SYNCHRONIZED",
    }
    report["SHARED_COGNITIVE_STATE_REPORT"] = {
        "context_propagation_coverage": 1.0,
        "state_consistency": {
            "counts": {
                "context_count": 15,
                "concept_count": 43 if mode == "adaptive" else 48,
                "program_count": 6 if mode == "adaptive" else 8,
                "search_route_count": 3 if mode == "adaptive" else 5,
                "truth_candidate_count": 18 if mode == "adaptive" else 22,
                "memory_entry_count": 1,
                "knowledge_object_count": 56 if mode == "adaptive" else 60,
                "snapshot_count": 8 if mode == "adaptive" else 12,
            }
        },
    }
    truth_count = (
        report["SHARED_COGNITIVE_STATE_REPORT"]["state_consistency"]["counts"][
            "truth_candidate_count"
        ]
    )
    report["truth_candidates"] = [
        {"id": f"truth:{index}"} for index in range(truth_count)
    ]
    report["truth_candidate_report"] = {
        "evaluations": [
            {"id": f"truth:{index}", "eligible": True}
            for index in range(truth_count)
        ]
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="NEXRYN cross-mode parity gate")
    parser.add_argument("--run-main", action="store_true")
    parser.add_argument("--full-mode", default="deep", choices=["deep", "full"])
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--task-count", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument(
        "--output",
        default="runtime_data/mode_parity/mode_comparison_report.json",
    )
    args = parser.parse_args()

    if args.run_main:
        report = DifferentialExecutionHarness().run_and_compare(
            seed=args.seed,
            task_count=args.task_count,
            full_mode=args.full_mode,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        report = CrossModeParityValidator().compare(
            synthetic_report("adaptive"),
            synthetic_report(args.full_mode, report_level="full"),
            full_label=args.full_mode,
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    stabilization = report["FULL_MODE_STABILIZATION_REPORT"]
    print(json.dumps({
        "mode_parity_score": stabilization["mode_parity_score"],
        "semantic_parity_status": stabilization["semantic_parity_status"],
        "regression_status": stabilization["regression_status"],
        "output": str(output),
    }, indent=2, sort_keys=True))
    return 0 if stabilization["regression_status"] == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
