def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class CognitiveFusionStability:

    def evaluate(self, alignment, hybridization, firewall):

        alignment_score = _clamp(alignment.get("alignment_score", 0.0))
        hybridization_risk = _clamp(hybridization.get("hybridization_risk", 0.0))
        firewall_penalty = 0.14 if firewall.get("firewall_actions", []) else 0.0

        fusion_stability = _clamp(
            alignment_score * 0.62
            +
            (1.0 - hybridization_risk) * 0.38
            -
            firewall_penalty
        )

        return {
            "system": "cognitive_fusion_stability",
            "fusion_stability": fusion_stability,
            "fusion_actions": [
                "sandbox_hybrid_cognitive_fusion",
                "require_stability_rehearsal_before_commit",
            ]
            if fusion_stability < 0.58
            else [
                "allow_guarded_cognitive_fusion",
            ],
            "fusion_state": (
                "hybrid_fusion_unstable"
                if fusion_stability < 0.58
                else "hybrid_fusion_guarded_stable"
            ),
        }
