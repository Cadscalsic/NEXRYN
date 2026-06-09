import re

from core.epistemic_models import clamp
from core.knowledge.contradiction_review_policy import (
    CONTRADICTION_THRESHOLD,
    SOFT_REVIEW_ZONE,
    classify_contradiction_review,
)


class AdaptiveContradictionGovernance:
    BASE_THRESHOLD = CONTRADICTION_THRESHOLD
    MAX_CANDIDATE_THRESHOLD = CONTRADICTION_THRESHOLD + SOFT_REVIEW_ZONE
    MAX_LOCKED_TRUTH_THRESHOLD = 0.16

    def _walk(self, value):
        if isinstance(value, dict):
            for item in value.values():
                yield from self._walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from self._walk(item)
        elif isinstance(value, str):
            yield value

    def _count_from_text(self, context, pattern):
        count = 0
        for text in self._walk(context):
            for match in re.finditer(pattern, text):
                count = max(count, int(match.group(1)))
        return count

    def _observed_count(self, context):
        generalization = context.get("knowledge_generalization", {})
        candidate = context.get("truth_candidate", {})
        return max(
            int(generalization.get("used_task_count", 0) or 0),
            int(generalization.get("independent_replications", 0) or 0),
            int(candidate.get("observed_task_count", 0) or 0),
            self._count_from_text(context, r"observed in (\d+) tasks"),
        )

    def _validation_count(self, context, observed_count):
        generalization = context.get("knowledge_generalization", {})
        candidate = context.get("truth_candidate", {})
        return max(
            int(generalization.get("validation_count", 0) or 0),
            int(candidate.get("validation_count", 0) or 0),
            self._count_from_text(context, r"validated across (\d+) tasks"),
            observed_count if observed_count >= 8 else 0,
        )

    def _score(self, context, paths, default=0.0):
        for path in paths:
            data = context
            for key in path:
                if not isinstance(data, dict):
                    data = None
                    break
                data = data.get(key)
            if data is not None:
                return clamp(data)
        return clamp(default)

    def _recovery_streak(self, context):
        streak = 0
        for path in [
            ("semantic_spine_recovery_report", "recovery_streak"),
            ("semantic_spine_recovery", "recovery_streak"),
            (
                "truth_candidate",
                "semantic_spine_recovery",
                "recovery_streak",
            ),
            (
                "identity_safe_truth_integration",
                "semantic_spine_recovery",
                "recovery_streak",
            ),
        ]:
            data = context
            for key in path:
                if not isinstance(data, dict):
                    data = None
                    break
                data = data.get(key)
            if data is not None:
                streak = max(streak, int(data or 0))
        return streak

    def evaluate(
        self,
        contradiction_score,
        context=None,
        stable_truth_authority_locked=False,
    ):
        context = context if isinstance(context, dict) else {}
        observed_count = self._observed_count(context)
        validation_count = self._validation_count(context, observed_count)
        causal_stability = max(
            self._score(
                context,
                [
                    ("causal_validation", "validation_score"),
                    ("causal_graph_alignment", "alignment_score"),
                ],
                0.0,
            ),
            self._score(
                context,
                [
                    ("knowledge_generalization", "average_causal_alignment"),
                ],
                0.0,
            ),
        )
        contextual_authority = max(
            self._score(
                context,
                [
                    (
                        "contextual_truth_authority",
                        "effective_contextual_truth",
                    ),
                    ("contextual_truth", "effective_contextual_truth"),
                    ("contextual_truth", "contextual_truth_score"),
                ],
                0.0,
            ),
            0.70
            if context.get(
                "contextual_truth_authority",
                {},
            ).get("contextual_truth_supported") is True
            else 0.0,
        )
        maturity_bonus = min(observed_count, 80) / 80 * 0.025
        validation_bonus = min(validation_count, 80) / 80 * 0.020
        causal_bonus = max(causal_stability - 0.75, 0.0) / 0.25 * 0.006
        context_bonus = max(contextual_authority - 0.69, 0.0) / 0.31 * 0.006
        recovery_streak = self._recovery_streak(context)
        recovery_bonus = (
            min(recovery_streak, 100) / 100 * 0.015
            if stable_truth_authority_locked
            else 0.0
        )
        raw_threshold = (
            self.BASE_THRESHOLD
            + maturity_bonus
            + validation_bonus
            + causal_bonus
            + context_bonus
            + recovery_bonus
        )
        cap = (
            self.MAX_LOCKED_TRUTH_THRESHOLD
            if stable_truth_authority_locked
            else self.MAX_CANDIDATE_THRESHOLD
        )
        dynamic_threshold = clamp(raw_threshold, maximum=cap)
        review = classify_contradiction_review(
            contradiction_score,
            threshold=dynamic_threshold,
            soft_review_zone=SOFT_REVIEW_ZONE,
        )
        return {
            "system": "adaptive_contradiction_governance",
            "phase": "5.7",
            "base_threshold": self.BASE_THRESHOLD,
            "dynamic_threshold": dynamic_threshold,
            "threshold_cap": cap,
            "threshold_bonus": round(
                dynamic_threshold - self.BASE_THRESHOLD,
                4,
            ),
            "observed_count": observed_count,
            "validation_count": validation_count,
            "causal_stability": causal_stability,
            "contextual_authority": contextual_authority,
            "recovery_streak": recovery_streak,
            "maturity_bonus": round(maturity_bonus, 4),
            "validation_bonus": round(validation_bonus, 4),
            "causal_bonus": round(causal_bonus, 4),
            "context_bonus": round(context_bonus, 4),
            "recovery_bonus": round(recovery_bonus, 4),
            "contradiction_score": contradiction_score,
            "contradiction_below_dynamic_threshold":
            contradiction_score < dynamic_threshold,
            **review,
        }


__all__ = [
    "AdaptiveContradictionGovernance",
]
