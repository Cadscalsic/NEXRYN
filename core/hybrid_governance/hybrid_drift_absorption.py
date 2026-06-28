def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class HybridDriftAbsorption:

    OBSERVATION_THRESHOLD = 0.28
    ACTION_THRESHOLD = 0.52
    CRITICAL_CONFLICT_THRESHOLD = 0.68

    def absorb(self, context=None, conflict=None):
        context = context or {}
        conflict = conflict or {}

        assimilated = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("drift_assimilation", {})
            .get("assimilated_drift", 0.0)
        )

        conflict_score = _clamp(
            conflict.get("paradigm_conflict_score", 0.0)
        )

        hybrid_absorption = _clamp(
            assimilated * 0.60
            + (1.0 - conflict_score) * 0.24
        )

        fast_mode = (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
        )

        observation_active = hybrid_absorption >= self.OBSERVATION_THRESHOLD
        action_required = (
            hybrid_absorption >= self.ACTION_THRESHOLD
            or conflict_score >= self.CRITICAL_CONFLICT_THRESHOLD
        )

        if fast_mode and not action_required:
            return {
                "system": "hybrid_drift_absorption",
                "hybrid_drift_absorption": hybrid_absorption,
                "absorption_state": "observation_deferred_in_fast_mode",
                "absorption_actions": [],
                "observation_active": observation_active,
                "action_required": False,
                "reason": "noncritical_hybrid_drift_absorption_deferred_after_success",
                "scores": {
                    "assimilated_drift": assimilated,
                    "paradigm_conflict_score": conflict_score,
                },
            }

        actions = []

        if action_required:
            actions.append("absorb_cross_paradigm_drift_in_buffers")

        state = (
            "hybrid_drift_absorption_active"
            if action_required
            else "hybrid_drift_absorption_observed"
            if observation_active
            else "hybrid_drift_absorption_standby"
        )

        return {
            "system": "hybrid_drift_absorption",
            "hybrid_drift_absorption": hybrid_absorption,
            "absorption_state": state,
            "absorption_actions": actions,
            "observation_active": observation_active,
            "action_required": action_required,
            "scores": {
                "assimilated_drift": assimilated,
                "paradigm_conflict_score": conflict_score,
            },
        }