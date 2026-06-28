"""Commit valid truth candidates with configurable policy gates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TruthCommitThresholds:
    promotion_score: float = 0.90
    dependency_confidence: float = 0.85
    contradiction_rate: float = 0.10
    cross_task_stability: float = 0.80
    causal_validation_score: float = 0.80
    context_strength: float = 0.75

    def as_dict(self) -> dict[str, float]:
        return {
            "promotion_score": self.promotion_score,
            "dependency_confidence": self.dependency_confidence,
            "contradiction_rate": self.contradiction_rate,
            "cross_task_stability": self.cross_task_stability,
            "causal_validation_score": self.causal_validation_score,
            "context_strength": self.context_strength,
        }


def evaluate_truth_commit(
    promotion_score: Any = 0.0,
    dependency_confidence: Any = 0.0,
    contradiction_rate: Any = 1.0,
    context_strength: Any = 0.0,
    cross_task_stability: Any = 0.0,
    causal_validation_score: Any = 0.0,
    truth_candidate_age: Any = 0,
    thresholds: TruthCommitThresholds | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    threshold_values = _thresholds(thresholds)
    scores = {
        "promotion_score": _score(promotion_score),
        "dependency_confidence": _score(dependency_confidence),
        "contradiction_rate": _score(contradiction_rate),
        "context_strength": _score(context_strength),
        "cross_task_stability": _score(cross_task_stability),
        "causal_validation_score": _score(causal_validation_score),
        "truth_candidate_age": _age(truth_candidate_age),
    }
    blockers = []
    for key in (
        "promotion_score",
        "dependency_confidence",
        "cross_task_stability",
        "causal_validation_score",
        "context_strength",
    ):
        if scores[key] < threshold_values[key]:
            blockers.append({
                "metric": key,
                "value": scores[key],
                "threshold": threshold_values[key],
                "reason": f"{key}_below_threshold",
            })
    if scores["contradiction_rate"] > threshold_values["contradiction_rate"]:
        blockers.append({
            "metric": "contradiction_rate",
            "value": scores["contradiction_rate"],
            "threshold": threshold_values["contradiction_rate"],
            "reason": "contradiction_rate_above_threshold",
        })

    positive = [
        scores["promotion_score"],
        scores["dependency_confidence"],
        1.0 - scores["contradiction_rate"],
        scores["context_strength"],
        scores["cross_task_stability"],
        scores["causal_validation_score"],
    ]
    commit_score = round(sum(positive) / len(positive), 4)
    commit_ready = not blockers
    return {
        "commit_score": commit_score,
        "commit_ready": commit_ready,
        "commit_reason": (
            "truth_candidate_met_commit_policy"
            if commit_ready
            else "truth_candidate_blocked_by_commit_policy"
        ),
        "commit_blockers": blockers,
        "thresholds": threshold_values,
        **scores,
    }


class TruthCommitEngine:
    system_name = "truth_commit_engine"

    def __init__(self, thresholds: TruthCommitThresholds | Mapping[str, Any] | None = None):
        self.thresholds = _thresholds(thresholds)

    def commit(
        self,
        candidates: Iterable[Mapping[str, Any]] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidates = [dict(candidate) for candidate in list(candidates or [])]
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        if not candidates:
            return {
                "system": self.system_name,
                "report_state": "final",
                "result_count": 0,
                "committed_truths": [],
                "probationary_truths": [],
                "rejected_truths": [],
                "truth_committed": False,
                "truth_rejected": False,
                "reason": "no_truth_candidates",
                "thresholds": dict(self.thresholds),
            }

        committed = []
        probationary = []
        rejected = []
        evaluations = []
        max_validations = int(runtime_context.get("MAX_TRUTH_VALIDATIONS", 24) or 24)
        for candidate in candidates[:max(1, max_validations)]:
            evaluation = evaluate_truth_commit(
                promotion_score=_first(candidate, runtime_context, "promotion_score", default=0.0),
                dependency_confidence=_first(
                    candidate,
                    runtime_context,
                    "dependency_confidence",
                    "dependency_support",
                    "promotion_dependency_score",
                    default=0.0,
                ),
                contradiction_rate=_first(
                    candidate,
                    runtime_context,
                    "contradiction_rate",
                    "contradiction_score",
                    default=0.0,
                ),
                context_strength=_first(
                    candidate,
                    runtime_context,
                    "context_strength",
                    "context_support",
                    "promotion_context_score",
                    default=0.0,
                ),
                cross_task_stability=_first(
                    candidate,
                    runtime_context,
                    "cross_task_stability",
                    "stability_score",
                    default=candidate.get("candidate_confidence", 0.0),
                ),
                causal_validation_score=_first(
                    candidate,
                    runtime_context,
                    "causal_validation_score",
                    "causal_support",
                    default=0.0,
                ),
                truth_candidate_age=candidate.get("truth_candidate_age", 0),
                thresholds=self.thresholds,
            )
            record = {
                **candidate,
                **evaluation,
                "candidate_state": candidate.get("candidate_state", "TRUTH_CANDIDATE"),
            }
            evaluations.append(record)
            if evaluation["commit_ready"]:
                record.update(_truth_record(record))
                committed.append(record)
            elif evaluation["commit_score"] >= 0.78:
                record["truth_state"] = "TRUTH_PROBATIONARY"
                probationary.append(record)
            else:
                record["truth_state"] = "TRUTH_REJECTED"
                record["rejection_reason"] = "commit_policy_blocked"
                rejected.append(record)

        return {
            "system": self.system_name,
            "report_state": "final",
            "result_count": len(committed),
            "truth_candidate": candidates[0].get("concept") if candidates else None,
            "committed_truths": committed,
            "probationary_truths": probationary,
            "rejected_truths": rejected,
            "truth_committed": bool(committed),
            "truth_rejected": bool(rejected),
            "commit_score": _average(item.get("commit_score", 0.0) for item in evaluations),
            "commit_ready": bool(committed),
            "commit_reason": (
                "committed_truths_available"
                if committed
                else "probationary_truths_available"
                if probationary
                else "all_candidates_blocked"
            ),
            "commit_blockers": [
                blocker
                for item in evaluations
                for blocker in item.get("commit_blockers", [])
            ],
            "truth_commit_evaluations": evaluations,
            "thresholds": dict(self.thresholds),
        }


def _truth_record(candidate: Mapping[str, Any]) -> dict[str, Any]:
    concept = str(candidate.get("concept") or "runtime_truth")
    return {
        "truth_name": concept,
        "truth_type": "COMMITTED_TRUTH",
        "truth_state": "COMMITTED_TRUTH",
        "truth_confidence": candidate.get("commit_score", 0.0),
        "supporting_contexts": _list(candidate.get("supporting_contexts")),
        "supporting_dependencies": _list(candidate.get("supporting_dependencies")),
        "supporting_tasks": _list(candidate.get("supporting_tasks")),
        "commit_timestamp": datetime.utcnow().isoformat(),
        "truth_lineage": _list(candidate.get("truth_lineage")) + [
            "TRUTH_CANDIDATE",
            "COMMITTED_TRUTH",
        ],
    }


def _thresholds(
    thresholds: TruthCommitThresholds | Mapping[str, Any] | None,
) -> dict[str, float]:
    values = TruthCommitThresholds().as_dict()
    if isinstance(thresholds, TruthCommitThresholds):
        values.update(thresholds.as_dict())
    elif isinstance(thresholds, Mapping):
        for key in values:
            if key in thresholds:
                values[key] = _score(thresholds[key])
    return values


def _first(
    candidate: Mapping[str, Any],
    runtime_context: Mapping[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        value = candidate.get(key)
        if value is not None:
            return value
    for key in keys:
        value = runtime_context.get(key)
        if value is not None:
            return value
    return default


def _average(values: Iterable[Any]) -> float:
    numbers = [_score(value) for value in values]
    return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _age(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


truth_commit_engine = TruthCommitEngine()


__all__ = [
    "TruthCommitEngine",
    "TruthCommitThresholds",
    "evaluate_truth_commit",
    "truth_commit_engine",
]
