def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class CognitiveFusionStability:

    UNSTABLE_THRESHOLD = 0.58
    CRITICAL_THRESHOLD = 0.42

    def evaluate(self, alignment=None, hybridization=None, firewall=None, runtime_context=None):
        alignment = alignment or {}
        hybridization = hybridization or {}
        firewall = firewall or {}
        runtime_context = runtime_context or {}

        alignment_score = _clamp(alignment.get("alignment_score", 0.0))
        hybridization_risk = _clamp(hybridization.get("hybridization_risk", 0.0))

        firewall_actions = firewall.get("firewall_actions", [])
        firewall_penalty = 0.14 if firewall_actions else 0.0

        fusion_stability = _clamp(
            alignment_score * 0.62
            + (1.0 - hybridization_risk) * 0.38
            - firewall_penalty
        )

        fast_mode = (
            runtime_context.get("episode_completed") is True
            or runtime_context.get("shutdown_mode") == "fast"
            or runtime_context.get("post_success_mode") == "fast"
        )

        critical = fusion_stability < self.CRITICAL_THRESHOLD
        unstable = fusion_stability < self.UNSTABLE_THRESHOLD

        if fast_mode and unstable and not critical:
            return {
                "system": "cognitive_fusion_stability",
                "fusion_stability": fusion_stability,
                "fusion_state": "deferred_in_fast_mode",
                "fusion_actions": [],
                "deferred_actions": [
                    "sandbox_hybrid_cognitive_fusion",
                    "require_stability_rehearsal_before_commit",
                ],
                "reason": "noncritical_fusion_rehearsal_deferred_after_success",
            }

        if critical:
            actions = [
                "sandbox_hybrid_cognitive_fusion",
                "require_stability_rehearsal_before_commit",
                "block_fusion_commit",
            ]
            state = "hybrid_fusion_critical_unstable"

        elif unstable:
            actions = [
                "sandbox_hybrid_cognitive_fusion",
                "require_stability_rehearsal_before_commit",
            ]
            state = "hybrid_fusion_unstable"

        else:
            actions = ["allow_guarded_cognitive_fusion"]
            state = "hybrid_fusion_guarded_stable"

        return {
            "system": "cognitive_fusion_stability",
            "fusion_stability": fusion_stability,
            "fusion_state": state,
            "fusion_actions": actions,
            "critical": critical,
            "unstable": unstable,
            "scores": {
                "alignment_score": alignment_score,
                "hybridization_risk": hybridization_risk,
                "firewall_penalty": firewall_penalty,
            },
        }