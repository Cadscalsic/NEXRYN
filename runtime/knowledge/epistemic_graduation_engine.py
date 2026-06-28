from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


DEFAULT_PROMOTION_WEIGHTS = {
    "observations": 0.20,
    "confidence": 0.20,
    "dependency_confidence": 0.20,
    "cross_task_stability": 0.15,
    "causal_support": 0.15,
    "context_support": 0.10,
}

DEFAULT_GRADUATION_THRESHOLDS = {
    "minimum_observations": 5,
    "observation_saturation": 32,
    "maximum_contradiction_rate": 0.10,
    "SUPPORTED": 0.55,
    "CANDIDATE": 0.70,
    "PROCESS_CONTEXT": 0.80,
    "TRUTH_CANDIDATE": 0.90,
    "ESTABLISHED_TRUTH": 0.95,
}

PROMOTION_PATH = [
    "DISCOVERING",
    "SUPPORTED",
    "CANDIDATE",
    "PROCESS_CONTEXT",
    "TRUTH_CANDIDATE",
    "ESTABLISHED_TRUTH",
]


@dataclass
class EpistemicGraduationEngine:
    thresholds: Mapping[str, Any] | None = None
    weights: Mapping[str, Any] | None = None
    promotion_path: list[str] = field(
        default_factory=lambda: list(PROMOTION_PATH),
    )

    def __post_init__(self):
        self.thresholds = {
            **DEFAULT_GRADUATION_THRESHOLDS,
            **dict(self.thresholds or {}),
        }
        self.weights = _normalize_weights({
            **DEFAULT_PROMOTION_WEIGHTS,
            **dict(self.weights or {}),
        })

    def evaluate(
        self,
        observations=0,
        confidence=0.0,
        dependency_confidence=0.0,
        contradiction_rate=0.0,
        cross_task_stability=0.0,
        causal_support=0.0,
        context_support=0.0,
        cross_task_validation_passed=False,
    ) -> dict[str, Any]:
        metrics = {
            "observations": _observation_score(
                observations,
                self.thresholds["observation_saturation"],
            ),
            "confidence": _clamp(confidence),
            "dependency_confidence": _clamp(dependency_confidence),
            "cross_task_stability": _clamp(cross_task_stability),
            "causal_support": _clamp(causal_support),
            "context_support": _clamp(context_support),
        }
        promotion_score = _clamp(
            sum(metrics[name] * self.weights[name] for name in self.weights)
        )
        contradiction_rate = _clamp(contradiction_rate)
        blocked_metrics = self._blocked_metrics(
            observations=observations,
            contradiction_rate=contradiction_rate,
            metrics=metrics,
            promotion_score=promotion_score,
            cross_task_validation_passed=cross_task_validation_passed,
        )
        stage = self._stage_for(
            observations=observations,
            promotion_score=promotion_score,
            contradiction_rate=contradiction_rate,
            cross_task_validation_passed=cross_task_validation_passed,
        )
        next_stage = self._next_stage(stage)
        return {
            "system": "epistemic_graduation_engine",
            "graduation_score": promotion_score,
            "promotion_score": promotion_score,
            "graduation_stage": stage,
            "promotion_stage": stage,
            "current_stage": stage,
            "next_stage": next_stage,
            "candidate_ready": stage in {
                "CANDIDATE",
                "PROCESS_CONTEXT",
                "TRUTH_CANDIDATE",
                "ESTABLISHED_TRUTH",
            },
            "eligible_for_context": stage in {
                "PROCESS_CONTEXT",
                "TRUTH_CANDIDATE",
                "ESTABLISHED_TRUTH",
            },
            "eligible_for_truth_candidate": stage in {
                "TRUTH_CANDIDATE",
                "ESTABLISHED_TRUTH",
            },
            "eligible_for_established_truth": stage == "ESTABLISHED_TRUTH",
            "blocked_metrics": blocked_metrics,
            "graduation_reason": self._reason(
                stage,
                promotion_score,
                blocked_metrics,
            ),
            "promotion_reason": self._reason(
                stage,
                promotion_score,
                blocked_metrics,
            ),
            "next_required_evidence": self._next_required_evidence(
                next_stage,
                blocked_metrics,
                metrics,
                promotion_score,
            ),
            "component_scores": metrics,
            "weights": dict(self.weights),
            "thresholds": dict(self.thresholds),
            "contradiction_rate": contradiction_rate,
            "cross_task_validation_passed": bool(cross_task_validation_passed),
        }

    def _stage_for(
        self,
        observations,
        promotion_score,
        contradiction_rate,
        cross_task_validation_passed,
    ):
        if observations < self.thresholds["minimum_observations"]:
            return "DISCOVERING"
        if contradiction_rate > self.thresholds["maximum_contradiction_rate"]:
            return "SUPPORTED" if promotion_score >= self.thresholds["SUPPORTED"] else "DISCOVERING"
        if (
            promotion_score >= self.thresholds["ESTABLISHED_TRUTH"]
            and cross_task_validation_passed
        ):
            return "ESTABLISHED_TRUTH"
        for stage in [
            "TRUTH_CANDIDATE",
            "PROCESS_CONTEXT",
            "CANDIDATE",
            "SUPPORTED",
        ]:
            if promotion_score >= self.thresholds[stage]:
                return stage
        return "DISCOVERING"

    def _blocked_metrics(
        self,
        observations,
        contradiction_rate,
        metrics,
        promotion_score,
        cross_task_validation_passed,
    ):
        blocked = []
        if observations < self.thresholds["minimum_observations"]:
            blocked.append("observations")
        if contradiction_rate > self.thresholds["maximum_contradiction_rate"]:
            blocked.append("contradiction_rate")
        for metric, score in metrics.items():
            if score < 0.55:
                blocked.append(metric)
        if (
            promotion_score >= self.thresholds["ESTABLISHED_TRUTH"]
            and not cross_task_validation_passed
        ):
            blocked.append("cross_task_validation")
        return list(dict.fromkeys(blocked))

    def _next_stage(self, stage):
        try:
            index = self.promotion_path.index(stage)
        except ValueError:
            return "DISCOVERING"
        if index >= len(self.promotion_path) - 1:
            return None
        return self.promotion_path[index + 1]

    def _reason(self, stage, promotion_score, blocked_metrics):
        if blocked_metrics:
            return (
                f"{stage}: promotion_score={promotion_score:.4f}; "
                f"blocked_metrics={blocked_metrics}"
            )
        return f"{stage}: promotion_score={promotion_score:.4f}; evidence gates satisfied"

    def _next_required_evidence(
        self,
        next_stage,
        blocked_metrics,
        metrics,
        promotion_score,
    ):
        requirements = []
        if next_stage and next_stage in self.thresholds:
            requirements.append({
                "metric": "promotion_score",
                "current_value": promotion_score,
                "required": self.thresholds[next_stage],
            })
        for metric in blocked_metrics:
            if metric == "observations":
                requirements.append({
                    "metric": metric,
                    "required": self.thresholds["minimum_observations"],
                })
            elif metric == "contradiction_rate":
                requirements.append({
                    "metric": metric,
                    "required": f"<= {self.thresholds['maximum_contradiction_rate']}",
                })
            elif metric == "cross_task_validation":
                requirements.append({
                    "metric": metric,
                    "required": "cross_task_validation_passed",
                })
            else:
                requirements.append({
                    "metric": metric,
                    "current_value": metrics.get(metric, 0.0),
                    "required": "raise evidence contribution above 0.55",
                })
        return requirements


def evaluate_concept_graduation(
    observations=0,
    confidence=0.0,
    dependency_confidence=0.0,
    contradiction_rate=0.0,
    cross_task_stability=0.0,
    causal_support=0.0,
    context_support=0.0,
    cross_task_validation_passed=False,
    thresholds=None,
    weights=None,
) -> dict[str, Any]:
    return EpistemicGraduationEngine(
        thresholds=thresholds,
        weights=weights,
    ).evaluate(
        observations=observations,
        confidence=confidence,
        dependency_confidence=dependency_confidence,
        contradiction_rate=contradiction_rate,
        cross_task_stability=cross_task_stability,
        causal_support=causal_support,
        context_support=context_support,
        cross_task_validation_passed=cross_task_validation_passed,
    )


def _normalize_weights(weights):
    numeric = {
        key: max(0.0, float(value))
        for key, value in weights.items()
    }
    total = sum(numeric.values()) or 1.0
    return {
        key: value / total
        for key, value in numeric.items()
    }


def _observation_score(observations, saturation):
    try:
        observations = max(0.0, float(observations))
    except (TypeError, ValueError):
        observations = 0.0
    try:
        saturation = max(1.0, float(saturation))
    except (TypeError, ValueError):
        saturation = 32.0
    return _clamp(observations / saturation)


def _clamp(value):
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0
