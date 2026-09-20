"""Isolated cognitive budget ablation experiment harness."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from statistics import mean
from time import perf_counter
from typing import Any, Callable, Iterable, Mapping


PRODUCTION_DEFAULT_ROUTES = 2
PRODUCTION_DEFAULT_DEPTH = 2
UNAVAILABLE = "UNAVAILABLE"

SCREENING_CONFIGS: tuple[tuple[int, int], ...] = (
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (2, 3),
    (3, 2),
    (3, 3),
    (4, 4),
)


class BudgetAblationError(ValueError):
    """Raised when an experiment request would be non-governed or ambiguous."""


@dataclass(frozen=True)
class BudgetExperimentConfig:
    route_budget: int
    depth_budget: int

    def __post_init__(self) -> None:
        if not isinstance(self.route_budget, int) or isinstance(self.route_budget, bool):
            raise BudgetAblationError("route_budget must be a positive integer")
        if not isinstance(self.depth_budget, int) or isinstance(self.depth_budget, bool):
            raise BudgetAblationError("depth_budget must be a positive integer")
        if self.route_budget <= 0:
            raise BudgetAblationError("route_budget must be positive")
        if self.depth_budget <= 0:
            raise BudgetAblationError("depth_budget must be positive")

    @property
    def config_id(self) -> str:
        return f"{self.route_budget}/{self.depth_budget}"

    def as_budget_override(self) -> dict[str, Any]:
        return {
            "experiment_only_override": True,
            "persistent": False,
            "authority": "NONE",
            "max_active_routes": self.route_budget,
            "max_reasoning_depth": self.depth_budget,
            "route_budget": self.route_budget,
            "depth_budget": self.depth_budget,
        }


@dataclass(frozen=True)
class BudgetExperimentTask:
    task_id: str
    task_signature: str
    payload: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not str(self.task_id or "").strip():
            raise BudgetAblationError("task_id is required")
        if not str(self.task_signature or "").strip():
            raise BudgetAblationError("task_signature is required")
        object.__setattr__(self, "payload", _freeze_value(deepcopy(self.payload or {})))


def screening_configs() -> list[BudgetExperimentConfig]:
    return [
        BudgetExperimentConfig(route_budget=routes, depth_budget=depth)
        for routes, depth in SCREENING_CONFIGS
    ]


def run_screening_ablation(
    *,
    tasks: Iterable[BudgetExperimentTask | Mapping[str, Any]],
    evaluator: Callable[[BudgetExperimentTask, BudgetExperimentConfig], Mapping[str, Any]],
    seed: int,
    execution_mode: str,
    report_policy: str,
    code_checkpoint: str,
    repeat_id: str = "repeat_001",
) -> dict[str, Any]:
    normalized_tasks = [_task_from(item) for item in tasks]
    if not normalized_tasks:
        raise BudgetAblationError("at least one task is required")

    task_order = [task.task_id for task in normalized_tasks]
    fingerprint = task_set_fingerprint(normalized_tasks)
    experiment_id = _experiment_id(
        seed=seed,
        execution_mode=execution_mode,
        report_policy=report_policy,
        code_checkpoint=code_checkpoint,
        repeat_id=repeat_id,
        task_set_fingerprint=fingerprint,
    )
    run_started = perf_counter()
    per_config = []
    per_task_results = []

    for config in screening_configs():
        config_results = []
        for task in normalized_tasks:
            task_started = perf_counter()
            raw = evaluator(task, config)
            if not isinstance(raw, Mapping):
                raise BudgetAblationError("evaluator must return a mapping")
            measurement = _measurement_from(
                raw,
                task=task,
                config=config,
                seed=seed,
                execution_mode=execution_mode,
                report_policy=report_policy,
                code_checkpoint=code_checkpoint,
                repeat_id=repeat_id,
                experiment_id=experiment_id,
                task_set_fingerprint=fingerprint,
                observed_wall_time=round(perf_counter() - task_started, 6),
            )
            _validate_capacity_within_experimental_ceiling(measurement)
            config_results.append(measurement)
            per_task_results.append(measurement)
        per_config.append(_summarize_config(config, config_results))

    comparisons = _dimension_comparisons(per_config)
    return {
        "system": "budget_ablation_experiment",
        "experiment_id": experiment_id,
        "repeat_id": repeat_id,
        "task_set_fingerprint": fingerprint,
        "frozen_task_set": [_task_identity(task) for task in normalized_tasks],
        "experiment_contract": _contract(
            seed=seed,
            execution_mode=execution_mode,
            report_policy=report_policy,
            code_checkpoint=code_checkpoint,
            repeat_id=repeat_id,
            task_set_fingerprint=fingerprint,
            task_order=task_order,
        ),
        "production_default": {
            "routes": PRODUCTION_DEFAULT_ROUTES,
            "depth": PRODUCTION_DEFAULT_DEPTH,
        },
        "production_policy_mutation": "FORBIDDEN",
        "production_default_changed": False,
        "runtime_authority_changed": False,
        "screening_configs": [config.config_id for config in screening_configs()],
        "per_task_results": per_task_results,
        "per_config_summary": per_config,
        "dimension_comparisons": comparisons,
        "screening_decision": _screening_decision(per_config, comparisons),
        "elapsed_time": round(perf_counter() - run_started, 6),
    }


def _task_from(value: BudgetExperimentTask | Mapping[str, Any]) -> BudgetExperimentTask:
    if isinstance(value, BudgetExperimentTask):
        return value
    if not isinstance(value, Mapping):
        raise BudgetAblationError("task must be a BudgetExperimentTask or mapping")
    return BudgetExperimentTask(
        task_id=str(value.get("task_id") or ""),
        task_signature=str(value.get("task_signature") or ""),
        payload=deepcopy(value.get("payload") or {}),
    )


def _contract(
    *,
    seed: int,
    execution_mode: str,
    report_policy: str,
    code_checkpoint: str,
    repeat_id: str,
    task_set_fingerprint: str,
    task_order: list[str],
) -> dict[str, Any]:
    return {
        "contract": "BUDGET_ABLATION_EXPERIMENT_CONTRACT",
        "experiment_only_override": {
            "allowed": True,
            "persistent": False,
            "authority": "NONE",
        },
        "controlled_variables": {
            "task_set": "IDENTICAL",
            "seed": seed,
            "execution_mode": execution_mode,
            "report_policy": report_policy,
            "code_checkpoint": code_checkpoint,
            "repeat_id": repeat_id,
            "task_set_fingerprint": task_set_fingerprint,
            "task_order": list(task_order),
        },
    }


def _measurement_from(
    raw: Mapping[str, Any],
    *,
    task: BudgetExperimentTask,
    config: BudgetExperimentConfig,
    seed: int,
    execution_mode: str,
    report_policy: str,
    code_checkpoint: str,
    repeat_id: str,
    experiment_id: str,
    task_set_fingerprint: str,
    observed_wall_time: float,
) -> dict[str, Any]:
    success_state = raw.get("success_state", UNAVAILABLE)
    exact_success = _bool_metric(
        raw.get("exact_success"),
        success_state == "EXACT_SUCCESS",
    )
    recoverable_failure = _bool_metric(
        raw.get("recoverable_failure"),
        success_state == "RECOVERABLE_FAILURE",
    )
    routing_overload = _bool_metric(
        raw.get("routing_overload_detected"),
        "routing_overload" in _failure_tokens(raw),
    )
    return {
        "experiment_id": experiment_id,
        "repeat_id": repeat_id,
        "task_set_fingerprint": task_set_fingerprint,
        "run_id": raw.get("run_id", UNAVAILABLE),
        "task_id": task.task_id,
        "task_signature": task.task_signature,
        "seed": seed,
        "execution_mode": execution_mode,
        "report_policy": report_policy,
        "code_checkpoint": code_checkpoint,
        "configuration_id": config.config_id,
        "route_budget": config.route_budget,
        "depth_budget": config.depth_budget,
        "budget_override": config.as_budget_override(),
        "requested_routes": _metric(raw, "requested_routes"),
        "admitted_routes": _metric(raw, "admitted_routes"),
        "peak_active_routes": _metric(raw, "peak_active_routes"),
        "requested_reasoning_depth": _metric(raw, "requested_reasoning_depth"),
        "entered_reasoning_depth": _metric(raw, "entered_reasoning_depth"),
        "completed_reasoning_depth": _metric(raw, "completed_reasoning_depth"),
        "accuracy": _metric(raw, "accuracy"),
        "final_score": _metric(raw, "final_score"),
        "success_state": success_state,
        "exact_success": exact_success,
        "recoverable_failure": recoverable_failure,
        "routing_overload_detected": routing_overload,
        "repair_attempts": _metric(raw, "repair_attempts"),
        "repair_successes": _metric(raw, "repair_successes"),
        "residual_count": _metric(raw, "residual_count"),
        "wall_time": raw.get("wall_time", observed_wall_time),
        "aggregate_active_compute_time": _metric(raw, "aggregate_active_compute_time"),
        "realized_overrun": raw.get("realized_overrun", UNAVAILABLE),
        "reachability_gap_count": _metric(raw, "reachability_gap_count"),
    }


def task_set_fingerprint(tasks: Iterable[BudgetExperimentTask]) -> str:
    canonical = [_task_identity(task) for task in tasks]
    canonical_bytes = json.dumps(
        canonical,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"task_set_sha256_{hashlib.sha256(canonical_bytes).hexdigest()}"


def _experiment_id(
    *,
    seed: int,
    execution_mode: str,
    report_policy: str,
    code_checkpoint: str,
    repeat_id: str,
    task_set_fingerprint: str,
) -> str:
    canonical = {
        "code_checkpoint": code_checkpoint,
        "execution_mode": execution_mode,
        "report_policy": report_policy,
        "repeat_id": repeat_id,
        "screening_configs": [f"{routes}/{depth}" for routes, depth in SCREENING_CONFIGS],
        "seed": seed,
        "task_set_fingerprint": task_set_fingerprint,
    }
    canonical_bytes = json.dumps(
        canonical,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"budget_ablation_sha256_{hashlib.sha256(canonical_bytes).hexdigest()}"


def _task_identity(task: BudgetExperimentTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "task_signature": task.task_signature,
        "payload": _jsonable(task.payload or {}),
    }


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_value(value[key]) for key in sorted(value, key=str)}
        )
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return tuple(_freeze_value(item) for item in sorted(value, key=repr))
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, set):
        return [_jsonable(item) for item in sorted(value, key=repr)]
    return value


def _metric(raw: Mapping[str, Any], key: str) -> Any:
    value = raw.get(key, UNAVAILABLE)
    return UNAVAILABLE if value is None else value


def _bool_metric(value: Any, fallback: bool) -> bool | str:
    if value is None:
        return bool(fallback)
    if isinstance(value, bool):
        return value
    return UNAVAILABLE


def _failure_tokens(raw: Mapping[str, Any]) -> set[str]:
    tokens = set()
    for key in ("failure_reason", "root_cause", "failure_causes"):
        value = raw.get(key)
        if isinstance(value, str):
            tokens.add(value)
        elif isinstance(value, Iterable) and not isinstance(value, (Mapping, str, bytes)):
            tokens.update(str(item) for item in value)
    return tokens


def _validate_capacity_within_experimental_ceiling(
    measurement: Mapping[str, Any],
) -> None:
    route_budget = measurement["route_budget"]
    depth_budget = measurement["depth_budget"]
    for key in ("admitted_routes", "peak_active_routes"):
        value = measurement.get(key)
        if _numeric(value) and value > route_budget:
            raise BudgetAblationError(
                f"{key} exceeds experimental route budget"
            )
    for key in ("entered_reasoning_depth", "completed_reasoning_depth"):
        value = measurement.get(key)
        if _numeric(value) and value > depth_budget:
            raise BudgetAblationError(
                f"{key} exceeds experimental depth budget"
            )


def _summarize_config(
    config: BudgetExperimentConfig,
    results: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "configuration_id": config.config_id,
        "route_budget": config.route_budget,
        "depth_budget": config.depth_budget,
        "task_count": len(results),
        "exact_success_rate": _rate(results, "exact_success"),
        "mean_accuracy": _mean_metric(results, "accuracy"),
        "mean_final_score": _mean_metric(results, "final_score"),
        "recoverable_failure_rate": _rate(results, "recoverable_failure"),
        "routing_overload_rate": _rate(results, "routing_overload_detected"),
        "mean_residual_count": _mean_metric(results, "residual_count"),
        "mean_repair_attempts": _mean_metric(results, "repair_attempts"),
        "mean_wall_time": _mean_metric(results, "wall_time"),
        "mean_active_compute_time": _mean_metric(results, "aggregate_active_compute_time"),
        "peak_route_utilization": _mean_ratio(results, "peak_active_routes", "route_budget"),
        "reasoning_depth_utilization": _mean_ratio(
            results,
            "completed_reasoning_depth",
            "depth_budget",
        ),
    }


def _rate(results: list[Mapping[str, Any]], key: str) -> float:
    values = [item.get(key) for item in results if isinstance(item.get(key), bool)]
    return round(sum(1 for value in values if value) / max(len(results), 1), 4)


def _mean_metric(results: list[Mapping[str, Any]], key: str) -> float | str:
    values = [
        float(item[key])
        for item in results
        if isinstance(item.get(key), (int, float)) and not isinstance(item.get(key), bool)
    ]
    if not values:
        return UNAVAILABLE
    return round(mean(values), 6)


def _mean_ratio(
    results: list[Mapping[str, Any]],
    numerator_key: str,
    denominator_key: str,
) -> float | str:
    ratios = []
    for item in results:
        numerator = item.get(numerator_key)
        denominator = item.get(denominator_key)
        if (
            isinstance(numerator, (int, float))
            and not isinstance(numerator, bool)
            and isinstance(denominator, (int, float))
            and not isinstance(denominator, bool)
            and denominator > 0
        ):
            ratios.append(float(numerator) / float(denominator))
    if not ratios:
        return UNAVAILABLE
    return round(mean(ratios), 6)


def _dimension_comparisons(summaries: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["configuration_id"]: item for item in summaries}
    transitions = [
        ("ROUTE_EFFECT", "1/2", "2/2"),
        ("ROUTE_EFFECT", "2/2", "3/2"),
        ("DEPTH_EFFECT", "2/1", "2/2"),
        ("DEPTH_EFFECT", "2/2", "2/3"),
        ("COUPLED_EFFECT", "2/2", "3/3"),
        ("COUPLED_EFFECT", "2/2", "4/4"),
    ]
    return [
        _comparison(kind, by_id[start], by_id[end])
        for kind, start, end in transitions
        if start in by_id and end in by_id
    ]


def _comparison(
    effect_type: str,
    start: Mapping[str, Any],
    end: Mapping[str, Any],
) -> dict[str, Any]:
    delta_wall = _delta(end, start, "mean_wall_time")
    return {
        "effect_type": effect_type,
        "from": start["configuration_id"],
        "to": end["configuration_id"],
        "delta_accuracy": _delta(end, start, "mean_accuracy"),
        "delta_exact_success_rate": _delta(end, start, "exact_success_rate"),
        "delta_recoverable_failure_rate": _delta(end, start, "recoverable_failure_rate"),
        "delta_wall_time": delta_wall,
        "delta_active_compute": _delta(end, start, "mean_active_compute_time"),
        "delta_routes_consumed": _delta(end, start, "peak_route_utilization"),
        "delta_depth_consumed": _delta(end, start, "reasoning_depth_utilization"),
        "mcv_accuracy_per_wall_time": _mcv(
            _delta(end, start, "mean_accuracy"),
            delta_wall,
        ),
        "mcv_exact_success_per_wall_time": _mcv(
            _delta(end, start, "exact_success_rate"),
            delta_wall,
        ),
    }


def _delta(end: Mapping[str, Any], start: Mapping[str, Any], key: str) -> float | str:
    end_value = end.get(key)
    start_value = start.get(key)
    if not isinstance(end_value, (int, float)) or isinstance(end_value, bool):
        return UNAVAILABLE
    if not isinstance(start_value, (int, float)) or isinstance(start_value, bool):
        return UNAVAILABLE
    return round(float(end_value) - float(start_value), 6)


def _mcv(delta_quality: float | str, delta_cost: float | str) -> float | str:
    if not isinstance(delta_quality, (int, float)) or isinstance(delta_quality, bool):
        return UNAVAILABLE
    if not isinstance(delta_cost, (int, float)) or isinstance(delta_cost, bool):
        return UNAVAILABLE
    if delta_cost == 0:
        return "DELTA_COST_ZERO"
    return round(float(delta_quality) / float(delta_cost), 6)


def _screening_decision(
    summaries: list[Mapping[str, Any]],
    comparisons: list[Mapping[str, Any]],
) -> dict[str, Any]:
    meaningful = [
        item
        for item in comparisons
        if _positive(item.get("delta_accuracy"))
        or _positive(item.get("delta_exact_success_rate"))
    ]
    if not meaningful:
        return {
            "decision": "NO_MEANINGFUL_GAIN",
            "full_factorial": False,
            "reason": "screening found no positive quality delta",
        }
    effect_types = {item["effect_type"] for item in meaningful}
    if effect_types == {"ROUTE_EFFECT"}:
        decision = "ROUTE_GAIN_ONLY"
    elif effect_types == {"DEPTH_EFFECT"}:
        decision = "DEPTH_GAIN_ONLY"
    elif "COUPLED_EFFECT" in effect_types:
        decision = "COUPLED_GAIN"
    else:
        decision = "INCONCLUSIVE"
    return {
        "decision": decision,
        "full_factorial": decision == "COUPLED_GAIN",
        "reason": "screening observed positive quality delta requiring repeat evidence",
    }


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


__all__ = [
    "BudgetAblationError",
    "BudgetExperimentConfig",
    "BudgetExperimentTask",
    "PRODUCTION_DEFAULT_DEPTH",
    "PRODUCTION_DEFAULT_ROUTES",
    "SCREENING_CONFIGS",
    "UNAVAILABLE",
    "run_screening_ablation",
    "screening_configs",
    "task_set_fingerprint",
]
