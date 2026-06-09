from core.epistemic_models import clamp


class ContextualTruthSupportPolicy:
    """Single support decision for contextual truth governance."""

    SUPPORT_THRESHOLD = 0.70
    SUPPORT_GRACE = 0.015
    STRONG_CONTEXT_SUPPORT_FLOOR = 0.685
    STRONG_HIERARCHY_SCORE = 0.90
    STRONG_SEMANTIC_SCORE = 0.85

    def _score(self, report, keys, default=0.0):
        report = report if isinstance(report, dict) else {}
        for key in keys:
            value = report.get(key)
            if value is not None:
                return clamp(value)
        return clamp(default)

    def evaluate(
        self,
        contextual_truth=None,
        contextual_truth_authority=None,
        context_hierarchy=None,
        semantic_context=None,
        effective_score=None,
    ):
        contextual_truth = (
            contextual_truth if isinstance(contextual_truth, dict) else {}
        )
        authority = (
            contextual_truth_authority
            if isinstance(contextual_truth_authority, dict)
            else {}
        )
        context_hierarchy = (
            context_hierarchy if isinstance(context_hierarchy, dict) else {}
        )
        semantic_context = (
            semantic_context if isinstance(semantic_context, dict) else {}
        )
        effective_contextual_truth = max(
            clamp(effective_score if effective_score is not None else 0.0),
            self._score(
                contextual_truth,
                ["effective_contextual_truth", "contextual_truth_score"],
                0.0,
            ),
            self._score(
                authority,
                ["effective_contextual_truth", "contextual_truth_authority"],
                0.0,
            ),
        )
        hierarchy_score = self._score(
            context_hierarchy,
            ["context_hierarchy_score", "score", "confidence"],
            0.0,
        )
        semantic_score = self._score(
            semantic_context,
            ["semantic_context_score", "confidence", "score"],
            0.0,
        )
        strong_context = (
            hierarchy_score >= self.STRONG_HIERARCHY_SCORE
            and semantic_score >= self.STRONG_SEMANTIC_SCORE
        )
        support_floor = self.SUPPORT_THRESHOLD - self.SUPPORT_GRACE
        if strong_context:
            support_floor = min(
                support_floor,
                self.STRONG_CONTEXT_SUPPORT_FLOOR,
            )
        explicit_support = (
            authority.get("contextual_truth_supported") is True
            or contextual_truth.get("contextual_truth_supported") is True
        )
        supported = explicit_support or effective_contextual_truth >= (
            support_floor
        )
        return {
            "system": "contextual_truth_support_policy",
            "phase": "5.8",
            "contextual_truth_supported": supported,
            "effective_contextual_truth": effective_contextual_truth,
            "support_threshold": self.SUPPORT_THRESHOLD,
            "support_grace_margin": self.SUPPORT_GRACE,
            "effective_support_floor": support_floor,
            "strong_context_floor_applied": strong_context,
            "context_hierarchy_score": hierarchy_score,
            "semantic_context_score": semantic_score,
            "explicit_contextual_truth_support": explicit_support,
        }


__all__ = [
    "ContextualTruthSupportPolicy",
]
