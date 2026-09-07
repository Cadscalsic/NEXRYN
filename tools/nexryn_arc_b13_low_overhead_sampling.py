"""B13 low-overhead candidate prediction/evaluation sampling runner."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any


ROOT = Path(r"C:\Users\SERVICE INFO\AMIS")
ART = Path(r"C:\tmp")
EVAL = ROOT / "datasets" / "arc_agi_2_official" / "data" / "evaluation"
WORKER = ART / "nexryn_arc_b1_final_worker_20260905_000000.py"
B11_RESIDUAL = ART / "nexryn_arc_b11_residual_timeout_trace_20260907_000000.jsonl"
B11_CONTROL = ART / "nexryn_arc_b11_completed_control_trace_20260907_000000.jsonl"
TIMEOUT_SECONDS = 20


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def clean(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    return value


def digest(value: Any) -> str:
    payload = json.dumps(clean(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def terminal_class(record: dict[str, Any]) -> str:
    reason = str(record.get("termination_reason") or record.get("prediction_status"))
    if "TIMEOUT" in reason:
        return "TIMEOUT"
    if record.get("task_exact") is True or reason == "TASK_SOLVED":
        return "EXACT_SUCCESS"
    if "NO_PREDICTION" in reason:
        return "NO_PREDICTION"
    if "INVALID_OUTPUT" in reason:
        return "INVALID_OUTPUT"
    if "RUNTIME_EXCEPTION" in reason:
        return "RUNTIME_EXCEPTION"
    return "WRONG_OUTPUT"


def run_worker(
    task_id: str,
    run_id: str,
    *,
    profile_path: Path | None = None,
) -> dict[str, Any]:
    env = dict(os.environ)
    for key in (
        "NEXRYN_LOCALIZATION_TELEMETRY_PATH",
        "NEXRYN_WORLD_MODEL_TELEMETRY_PATH",
        "NEXRYN_LOCALIZATION_TELEMETRY_TASK_ID",
        "NEXRYN_WORLD_MODEL_TELEMETRY_TASK_ID",
    ):
        env.pop(key, None)
    if profile_path is not None:
        env["NEXRYN_CANDIDATE_COST_PROFILE_ENABLED"] = "1"
        env["NEXRYN_CANDIDATE_COST_PROFILE_PATH"] = str(profile_path)
        env["NEXRYN_CANDIDATE_COST_PROFILE_TASK_ID"] = task_id
    else:
        env.pop("NEXRYN_CANDIDATE_COST_PROFILE_ENABLED", None)
        env.pop("NEXRYN_CANDIDATE_COST_PROFILE_PATH", None)
        env.pop("NEXRYN_CANDIDATE_COST_PROFILE_TASK_ID", None)

    task_path = EVAL / task_id
    started_at = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(WORKER), str(task_path), run_id],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "task_id": task_id,
            "termination_reason": "TASK_FAILED_TIMEOUT",
            "prediction_status": "TASK_FAILED_TIMEOUT",
            "task_exact": False,
            "wall_time": round(time.perf_counter() - started_at, 4),
        }
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode == 0 and lines:
        record = json.loads(lines[-1])
    else:
        record = {
            "task_id": task_id,
            "termination_reason": "TASK_FAILED_RUNTIME_EXCEPTION",
            "prediction_status": "TASK_FAILED_RUNTIME_EXCEPTION",
            "task_exact": False,
            "exception": {
                "type": "WorkerNonZeroExit",
                "message": (proc.stderr or proc.stdout)[-1000:],
            },
        }
    record["wall_time"] = round(time.perf_counter() - started_at, 4)
    return record


def profile_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return read_jsonl(path)


def aggregate_profiles(records: list[dict[str, Any]]) -> dict[str, Any]:
    sums = Counter()
    sampled_prediction = []
    sampled_evaluation = []
    source_nodes = []
    target_nodes = []
    attempts = []
    for record in records:
        for key in (
            "candidate_count",
            "candidates_started",
            "candidates_completed",
            "aggregate_prediction_ms",
            "aggregate_evaluation_ms",
            "aggregate_scene_graph_ms",
            "aggregate_matching_ms",
            "aggregate_scoring_ms",
        ):
            sums[key] += float(record.get(key, 0.0) or 0.0)
        sampled_prediction.extend(record.get("sampled_prediction_duration_ms", []))
        sampled_evaluation.extend(record.get("sampled_evaluation_duration_ms", []))
        source_nodes.extend(_expand_distribution(record, "source_node_count_distribution"))
        target_nodes.extend(_expand_distribution(record, "target_node_count_distribution"))
        attempts.extend(_expand_distribution(record, "match_attempt_distribution"))
    total = sums["aggregate_prediction_ms"] + sums["aggregate_evaluation_ms"]
    return {
        "candidate_count": int(sums["candidate_count"]),
        "candidates_started": int(sums["candidates_started"]),
        "candidates_completed": int(sums["candidates_completed"]),
        "sampled_prediction_duration_ms": sampled_prediction,
        "sampled_evaluation_duration_ms": sampled_evaluation,
        "aggregate_prediction_ms": round(sums["aggregate_prediction_ms"], 4),
        "aggregate_evaluation_ms": round(sums["aggregate_evaluation_ms"], 4),
        "aggregate_scene_graph_ms": round(sums["aggregate_scene_graph_ms"], 4),
        "aggregate_matching_ms": round(sums["aggregate_matching_ms"], 4),
        "aggregate_scoring_ms": round(sums["aggregate_scoring_ms"], 4),
        "prediction_time_share": share(sums["aggregate_prediction_ms"], total),
        "evaluation_time_share": share(sums["aggregate_evaluation_ms"], total),
        "scene_graph_time_share": share(sums["aggregate_scene_graph_ms"], total),
        "matching_time_share": share(sums["aggregate_matching_ms"], total),
        "scoring_time_share": share(sums["aggregate_scoring_ms"], total),
        "source_node_counts": source_nodes,
        "target_node_counts": target_nodes,
        "match_attempts": attempts,
    }


def _expand_distribution(record: dict[str, Any], key: str) -> list[int]:
    values = []
    for raw_value, count in (record.get(key) or {}).items():
        values.extend([int(raw_value)] * int(count))
    return values


def distribution(values: list[Any]) -> dict[str, int]:
    counts = Counter(str(value) for value in values)
    return dict(sorted(counts.items()))


def mean(values: list[float]) -> float | str:
    return round(statistics.mean(values), 4) if values else "NOT_MEASURABLE"


def median(values: list[float]) -> float | str:
    return round(statistics.median(values), 4) if values else "NOT_MEASURABLE"


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ranked = sorted(values)
    index = (len(ranked) - 1) * (p / 100.0)
    low = int(index)
    high = min(low + 1, len(ranked) - 1)
    if low == high:
        return round(ranked[low], 4)
    return round(ranked[low] + (ranked[high] - ranked[low]) * (index - low), 4)


def share(value: float, total: float) -> float:
    return round(float(value) / total, 4) if total > 0 else 0.0


def classify_dominance(profile: dict[str, Any]) -> str:
    if not profile["candidates_completed"]:
        return "NOT_MEASURABLE"
    if profile["evaluation_time_share"] >= 0.65:
        return "EVALUATION_DOMINANT"
    if profile["prediction_time_share"] >= 0.65:
        return "PREDICTION_DOMINANT"
    return "MIXED"


def pathological_result(candidate_samples: list[float]) -> tuple[str, str]:
    if len(candidate_samples) < 3:
        return "UNKNOWN", "UNKNOWN"
    med = statistics.median(candidate_samples)
    peak = max(candidate_samples)
    if med <= 0:
        return "UNKNOWN", "UNKNOWN"
    if peak >= med * 5:
        return "HEAVY_TAIL", "YES"
    if peak >= med * 3:
        return "MIXED", "POSSIBLE"
    return "UNIFORM_EXPENSIVE", "NO"


def main() -> None:
    if not WORKER.exists():
        raise RuntimeError(f"missing frozen worker: {WORKER}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"arc_b13_low_overhead_sampling_{stamp}"
    profile_dir = ART / f"nexryn_arc_b13_low_overhead_profiles_{stamp}"
    report_path = ART / f"nexryn_arc_b13_low_overhead_sampling_report_{stamp}.json"
    control_pairs_path = ART / f"nexryn_arc_b13_control_pairs_{stamp}.jsonl"
    residual_path = ART / f"nexryn_arc_b13_residual_replay_{stamp}.jsonl"

    residual_ids = [record["task_id"] for record in read_jsonl(B11_RESIDUAL)]
    control_ids = [record["task_id"] for record in read_jsonl(B11_CONTROL)]

    profile_dir.mkdir(parents=True, exist_ok=True)
    control_pairs = []
    with control_pairs_path.open("w", encoding="utf-8") as handle:
        for index, task_id in enumerate(control_ids, 1):
            off = run_worker(task_id, run_id + "_off", profile_path=None)
            on_profile = profile_dir / f"control_{index:02d}_{task_id}.jsonl"
            on = run_worker(task_id, run_id + "_on", profile_path=on_profile)
            pair = {
                "task_id": task_id,
                "off_terminal": terminal_class(off),
                "on_terminal": terminal_class(on),
                "terminal_parity": terminal_class(off) == terminal_class(on),
                "prediction_parity": digest(off.get("frozen_attempt_id", []))
                == digest(on.get("frozen_attempt_id", [])),
                "candidate_count_parity": off.get("candidate_count")
                == on.get("candidate_count"),
                "candidate_winner_parity": off.get("selected_program_candidate")
                == on.get("selected_program_candidate"),
                "off_wall_time": float(off.get("wall_time", 0.0) or 0.0),
                "on_wall_time": float(on.get("wall_time", 0.0) or 0.0),
                "overhead_ms": round(
                    (
                        float(on.get("wall_time", 0.0) or 0.0)
                        - float(off.get("wall_time", 0.0) or 0.0)
                    )
                    * 1000,
                    4,
                ),
                "profile_records": profile_records(on_profile),
            }
            control_pairs.append(pair)
            handle.write(json.dumps(clean(pair), sort_keys=True) + "\n")
            handle.flush()
            print(
                f"B13 controls {index}/{len(control_ids)} {task_id} "
                f"{pair['off_terminal']}->{pair['on_terminal']} "
                f"overhead_ms={pair['overhead_ms']}",
                flush=True,
            )

    residual_rows = []
    with residual_path.open("w", encoding="utf-8") as handle:
        for index, task_id in enumerate(residual_ids, 1):
            on_profile = profile_dir / f"residual_{index:02d}_{task_id}.jsonl"
            record = run_worker(task_id, run_id + "_residual", profile_path=on_profile)
            row = {
                "task_id": task_id,
                "terminal": terminal_class(record),
                "wall_time": float(record.get("wall_time", 0.0) or 0.0),
                "profile_records": profile_records(on_profile),
            }
            residual_rows.append(row)
            handle.write(json.dumps(clean(row), sort_keys=True) + "\n")
            handle.flush()
            print(
                f"B13 residual {index}/{len(residual_ids)} {task_id} "
                f"{row['terminal']} time={row['wall_time']}",
                flush=True,
            )

    control_profiles = [
        item
        for pair in control_pairs
        for item in pair.get("profile_records", [])
    ]
    residual_profiles = [
        item
        for row in residual_rows
        for item in row.get("profile_records", [])
    ]
    all_profile = aggregate_profiles([*control_profiles, *residual_profiles])
    residual_profile = aggregate_profiles(residual_profiles)
    control_profile = aggregate_profiles(control_profiles)
    terminal_parity = [
        pair["terminal_parity"] for pair in control_pairs
    ]
    overheads = [pair["overhead_ms"] for pair in control_pairs]
    path_class, heavy_tail = pathological_result(
        all_profile["sampled_prediction_duration_ms"]
        + all_profile["sampled_evaluation_duration_ms"]
    )
    dominance = classify_dominance(all_profile)
    attribution_authority = (
        "AUTHORITATIVE_FOR_B13_LOW_OVERHEAD_SAMPLE"
        if all(terminal_parity) and all_profile["candidates_completed"]
        else "NON_AUTHORITATIVE"
    )
    if not all(terminal_parity):
        decision = "ARC.B13-F"
    elif not all_profile["candidates_completed"]:
        decision = "ARC.B13-G"
    elif dominance == "EVALUATION_DOMINANT":
        decision = "ARC.B13-A"
    elif all_profile["matching_time_share"] >= 0.50:
        decision = "ARC.B13-B"
    elif path_class in {"HEAVY_TAIL", "SINGLE_PATHOLOGICAL_CANDIDATE"}:
        decision = "ARC.B13-C"
    elif path_class == "UNIFORM_EXPENSIVE":
        decision = "ARC.B13-D"
    else:
        decision = "ARC.B13-E"

    report = {
        "1_B13_STATUS": "CLOSED_FOR_LOW_OVERHEAD_SAMPLED_MEASUREMENT",
        "2_DECISION_GATE": decision,
        "3_PROFILER_DESIGN": (
            "Opt-in in-process monotonic aggregate counters; sampled first/middle/"
            "last/every-N candidates; compact append-only per-call JSON records; "
            "no profiler output consumed by behavior."
        ),
        "4_PROFILER_FILES_CHANGED": [
            "runtime/telemetry/candidate_cost_profiler.py",
            "core/world_model/counterfactual_simulator.py",
            "core/world_model/position_predictor.py",
            "core/world_model/placement_reasoner.py",
            "runtime/spatial/transformation_localization_engine.py",
            "runtime/world/world_model.py",
        ],
        "5_PROFILER_TEST_FILES": ["tests/test_candidate_cost_profiler_b13.py"],
        "6_TERMINAL_PARITY_RATE": share(sum(terminal_parity), len(terminal_parity)),
        "7_MEDIAN_PROFILER_OVERHEAD": median(overheads),
        "8_P95_PROFILER_OVERHEAD": percentile(overheads, 95),
        "9_PERTURBATION_RESULT": (
            "TERMINAL_STABLE" if all(terminal_parity) else "TERMINAL_PERTURBED"
        ),
        "10_RESIDUAL_19_REPLAY_COUNT": len(residual_rows),
        "11_RESIDUAL_TIMEOUT_COUNT": sum(
            1 for row in residual_rows if row["terminal"] == "TIMEOUT"
        ),
        "12_RESIDUAL_COMPLETED_COUNT": sum(
            1 for row in residual_rows if row["terminal"] != "TIMEOUT"
        ),
        "13_CONTROL_COHORT_COUNT": len(control_pairs),
        "14_CONTROL_TERMINAL_PARITY": distribution(terminal_parity),
        "15_CANDIDATE_COUNT_DISTRIBUTION": distribution(
            [record.get("candidate_count") for record in [*control_profiles, *residual_profiles]]
        ),
        "16_CANDIDATES_COMPLETED_DISTRIBUTION": distribution(
            [record.get("candidates_completed") for record in [*control_profiles, *residual_profiles]]
        ),
        "17_MEAN_PREDICTION_COST": mean(all_profile["sampled_prediction_duration_ms"]),
        "18_MEDIAN_PREDICTION_COST": median(all_profile["sampled_prediction_duration_ms"]),
        "19_MEAN_EVALUATION_COST": mean(all_profile["sampled_evaluation_duration_ms"]),
        "20_MEDIAN_EVALUATION_COST": median(all_profile["sampled_evaluation_duration_ms"]),
        "21_EVALUATION_TIME_SHARE": all_profile["evaluation_time_share"],
        "22_PREDICTION_TIME_SHARE": all_profile["prediction_time_share"],
        "23_SCENE_GRAPH_TIME_SHARE": all_profile["scene_graph_time_share"],
        "24_MATCHING_TIME_SHARE": all_profile["matching_time_share"],
        "25_SCORING_TIME_SHARE": all_profile["scoring_time_share"],
        "26_NODE_COUNT_DISTRIBUTION": {
            "source": distribution(all_profile["source_node_counts"]),
            "target": distribution(all_profile["target_node_counts"]),
        },
        "27_MATCH_ATTEMPT_DISTRIBUTION": distribution(all_profile["match_attempts"]),
        "28_PATHOLOGICAL_CANDIDATE_RESULT": path_class,
        "29_HEAVY_TAIL_RESULT": heavy_tail,
        "30_CONTROL-vs-TIMEOUT_DIVERGENCE": {
            "control_profile": control_profile,
            "residual_profile": residual_profile,
        },
        "31_LOCAL_COST_MODEL": (
            "T_task ~= N_candidates * (C_prediction + C_scene_graph + "
            "C_matching + C_scoring), using measured aggregate terms only."
        ),
        "32_ROUTE_BUDGET_COVERAGE": "NOT_COUNTED",
        "33_DEPTH_BUDGET_COVERAGE": "NOT_COUNTED",
        "34_WORLD-MODEL_INTERNAL_WORK_ACCOUNTING": "OBSERVED_NOT_GOVERNED",
        "35_GOVERNANCE_GAP_RESULT": (
            "candidate-dependent prediction/evaluation is measured but still not "
            "explicitly governed by route/depth budget"
        ),
        "36_ROOT_CAUSE_OBSERVABLE": bool(all_profile["candidates_completed"]),
        "37_ATTRIBUTION_AUTHORITY": attribution_authority,
        "38_SEMANTIC-PRESERVING_REPAIR_ELIGIBILITY": (
            "NOT_APPLIED; future optimization must preserve candidate set/order/"
            "prediction/score/winner"
        ),
        "39_PATCH_REQUIRED": "NO_BEHAVIORAL_PATCH_FOR_B13_MEASUREMENT",
        "40_PATCH_APPLIED_NO": True,
        "41_PROPOSED_NEXT_TARGET": (
            "If attribution remains stable, design semantic-preserving evaluation "
            "owner optimization; otherwise improve profiler perturbation boundary."
        ),
        "42_COGNITIVE_SEMANTICS_RISK": (
            "HIGH for behavior changes; LOW for current observation-only profiler"
        ),
        "43_FULL_120_RERUN_ALLOWED": False,
        "44_A2_RESULT": "UNCHANGED_FROM_B12_INPUT",
        "45_REGRESSION_SUITE_RESULT": "RUN_SEPARATELY",
        "46_ARTIFACT_PATHS": {
            "report": report_path,
            "control_pairs": control_pairs_path,
            "residual_replay": residual_path,
            "profiles": profile_dir,
        },
        "47_git_diff_--check": "RUN_SEPARATELY",
        "48_git_status_--short": "RUN_SEPARATELY",
        "49_NEXT_ACTION": "Run focused regressions and inspect B13 decision before any repair.",
    }
    report_path.write_text(json.dumps(clean(report), indent=2), encoding="utf-8")
    print(json.dumps(clean({
        "decision": decision,
        "terminal_parity_rate": report["6_TERMINAL_PARITY_RATE"],
        "residual_replay_count": len(residual_rows),
        "artifact": report_path,
    }), indent=2))


if __name__ == "__main__":
    main()
