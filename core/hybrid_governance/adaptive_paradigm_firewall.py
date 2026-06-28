class AdaptiveParadigmFirewall:
    """
    Lightweight firewall for hybrid/paradigm conflicts.
    Designed to be cheap, deterministic, and safe for fast runtime.
    """

    CONFLICT_THRESHOLD = 0.34
    HYBRIDIZATION_THRESHOLD = 0.36
    TRANSLATION_THRESHOLD = 0.34

    HIGH_RISK_THRESHOLD = 0.65

    def inspect(self, conflict=None, hybridization=None, translation=None, runtime_context=None):
        conflict = conflict or {}
        hybridization = hybridization or {}
        translation = translation or {}
        runtime_context = runtime_context or {}

        paradigm_conflict_score = float(
            conflict.get("paradigm_conflict_score", 0.0) or 0.0
        )
        hybridization_risk = float(
            hybridization.get("hybridization_risk", 0.0) or 0.0
        )
        translation_load = float(
            translation.get("translation_load", 0.0) or 0.0
        )

        max_risk = max(
            paradigm_conflict_score,
            hybridization_risk,
            translation_load,
        )

        risk_active = (
            paradigm_conflict_score >= self.CONFLICT_THRESHOLD
            or hybridization_risk >= self.HYBRIDIZATION_THRESHOLD
            or translation_load >= self.TRANSLATION_THRESHOLD
        )

        high_risk = max_risk >= self.HIGH_RISK_THRESHOLD

        fast_mode = (
            runtime_context.get("shutdown_mode") == "fast"
            or runtime_context.get("post_success_mode") == "fast"
            or runtime_context.get("episode_completed") is True
        )

        if fast_mode and not high_risk:
            return {
                "system": "adaptive_paradigm_firewall",
                "firewall_state": "skipped_fast_mode",
                "firewall_actions": [],
                "risk_active": False,
                "risk_level": "low_or_medium",
                "max_risk": round(max_risk, 4),
                "reason": "fast_mode_blocks_noncritical_paradigm_firewall",
            }

        actions = []

        if risk_active:
            actions.append("require_cross_paradigm_attestation")

        if high_risk:
            actions.append("block_unattested_paradigm_fusion")

        return {
            "system": "adaptive_paradigm_firewall",
            "firewall_state": (
                "adaptive_paradigm_firewall_active"
                if risk_active
                else "adaptive_paradigm_firewall_standby"
            ),
            "firewall_actions": actions,
            "risk_active": risk_active,
            "risk_level": (
                "high" if high_risk else
                "medium" if risk_active else
                "low"
            ),
            "max_risk": round(max_risk, 4),
            "scores": {
                "paradigm_conflict_score": paradigm_conflict_score,
                "hybridization_risk": hybridization_risk,
                "translation_load": translation_load,
            },
        }