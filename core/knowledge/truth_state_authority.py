from core.epistemic_models import BeliefState


class TruthStateAuthority:
    """Keeps durable truth state separate from temporary validation gates."""

    def is_active_truth(self, truth_record):
        if truth_record is None:
            return False
        status = (
            truth_record.get("status")
            if isinstance(truth_record, dict)
            else getattr(truth_record, "status", None)
        )
        reusable = (
            truth_record.get("reusable", True)
            if isinstance(truth_record, dict)
            else getattr(truth_record, "reusable", True)
        )
        return status in [None, "ACTIVE"] and reusable is not False

    def lock_belief_state(self, belief, truth_record):
        locked = self.is_active_truth(truth_record)
        if locked:
            belief.state = BeliefState.TRUTH_COMMITTED
        return locked

    def stable_truth_concepts(self, truth_registry):
        truths = truth_registry.get(
            "truths",
            truth_registry.get("records", []),
        )
        return {
            str(item.get("concept"))
            for item in truths
            if (
                isinstance(item, dict)
                and item.get("concept")
                and self.is_active_truth(item)
            )
        }


__all__ = [
    "TruthStateAuthority",
]
