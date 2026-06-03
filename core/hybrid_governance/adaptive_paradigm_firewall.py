class AdaptiveParadigmFirewall:

    def inspect(self, conflict, hybridization, translation):

        risk_active = (
            conflict.get("paradigm_conflict_score", 0.0) >= 0.34
            or hybridization.get("hybridization_risk", 0.0) >= 0.36
            or translation.get("translation_load", 0.0) >= 0.34
        )

        return {
            "system": "adaptive_paradigm_firewall",
            "firewall_actions": [
                "require_cross_paradigm_attestation",
                "block_unattested_paradigm_fusion",
            ]
            if risk_active
            else [],
            "firewall_state": (
                "adaptive_paradigm_firewall_active"
                if risk_active
                else "adaptive_paradigm_firewall_standby"
            ),
        }
