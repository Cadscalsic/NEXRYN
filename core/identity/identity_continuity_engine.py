from core.epistemic_models import clamp


class IdentityContinuityEngine:
    """Forecasts whether a new truth can join the existing identity spine."""

    def __init__(self, minimum_continuity=0.62):
        self.minimum_continuity = minimum_continuity

    def evaluate(
        self,
        concept,
        old_spine_continuity,
        new_truth_delta=0.0,
        minimum_continuity=None,
        breaks_core_truths=False,
    ):
        threshold = (
            self.minimum_continuity
            if minimum_continuity is None
            else clamp(minimum_continuity)
        )
        old_spine_continuity = clamp(old_spine_continuity)
        try:
            new_truth_delta = float(new_truth_delta)
        except (TypeError, ValueError):
            new_truth_delta = 0.0
        new_truth_delta = max(min(new_truth_delta, 1.0), -1.0)
        continuity_score = clamp(old_spine_continuity + new_truth_delta)
        core_truths_preserved = breaks_core_truths is not True
        allowed_transition = (
            core_truths_preserved
            and continuity_score >= threshold
        )

        return {
            "system": "identity_continuity_engine",
            "concept": concept,
            "old_spine_continuity": old_spine_continuity,
            "new_truth_identity_delta": round(new_truth_delta, 4),
            "continuity_score": continuity_score,
            "minimum_continuity": threshold,
            "core_truths_preserved": core_truths_preserved,
            "allowed_transition": allowed_transition,
            "transition_state": (
                "IDENTITY_CONTINUITY_PRESERVED"
                if allowed_transition
                else "CORE_TRUTH_CONFLICT"
                if not core_truths_preserved
                else "IDENTITY_CONTINUITY_HOLD"
            ),
        }


identity_continuity_engine = IdentityContinuityEngine()


__all__ = [
    "IdentityContinuityEngine",
    "identity_continuity_engine",
]
