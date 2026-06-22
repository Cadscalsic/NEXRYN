# ============================================
# NEXRYN CURIOSITY BALANCE ENGINE
# ============================================

from runtime.motivation.motivation_state import clamp


class CuriosityBalanceEngine:

    def evaluate(
        self,
        motivation_state,
        reward_report,
        penalty_report,
    ):

        reward_score = clamp(reward_report.get("reward_score", 0.0))
        penalty_score = clamp(penalty_report.get("penalty_score", 0.0))
        critical = penalty_report.get("highest_severity") == "critical"
        major = penalty_report.get("highest_severity") == "major"

        curiosity_balance = clamp(
            0.50
            + motivation_state.exploration_drive * 0.25
            + reward_score * 0.20
            - penalty_score * 0.35
        )
        if critical:
            curiosity_balance = min(curiosity_balance, 0.15)
        elif major:
            curiosity_balance = min(curiosity_balance, 0.30)

        motivation_state.curiosity_balance = curiosity_balance

        return {
            "system": "curiosity_balance_engine",
            "curiosity_balance": round(curiosity_balance, 4),
            "exploration_mode": (
                "governance_locked"
                if critical
                else "cautious_validation"
                if major
                else "bounded_exploration"
                if curiosity_balance >= 0.55
                else "exploit_known_safe_paths"
            ),
            "reward_hacking_guard_active": True,
            "rewards_cannot_override_governance": True,
        }
