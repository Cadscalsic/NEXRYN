class EpistemicDriftContainmentEngine:
    """Reports drift containment separately from semantic conflict."""

    def evaluate(self, context=None, recovery_confirmed=False):
        context = context if isinstance(context, dict) else {}
        regulation = context.get("epistemic_drift_regulation", {})
        truth_commit_blocked = (
            regulation.get("truth_commit_blocked", False) is True
        )
        containment_active = (
            truth_commit_blocked
            and recovery_confirmed is not True
        )
        return {
            "system": "epistemic_drift_containment_engine",
            "containment_active": containment_active,
            "integration_allowed": not containment_active,
            "containment_state": (
                "EPISTEMIC_DRIFT_CONTAINED"
                if containment_active
                else "EPISTEMIC_DRIFT_CONTAINMENT_CLEAR"
            ),
            "regulation_mode": regulation.get("regulation_mode"),
            "truth_commit_blocked": truth_commit_blocked,
            "recovery_confirmed": recovery_confirmed is True,
        }


epistemic_drift_containment_engine = EpistemicDriftContainmentEngine()


__all__ = [
    "EpistemicDriftContainmentEngine",
    "epistemic_drift_containment_engine",
]
