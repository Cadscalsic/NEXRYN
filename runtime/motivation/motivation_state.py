# ============================================
# NEXRYN MOTIVATION STATE
# ============================================

from dataclasses import dataclass, field


def clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = minimum
    return max(minimum, min(value, maximum))


@dataclass
class MotivationState:

    balances: dict = field(default_factory=dict)

    trends: dict = field(default_factory=dict)

    dominant_motivation: str = "balanced"

    reward_stability: float = 1.0

    reward_hacking_risk: float = 0.0

    exploration_drive: float = 0.35

    failure_tolerance: float = 0.35

    curiosity_balance: float = 0.50

    reward_saturation: float = 0.0

    risk_appetite: float = 0.25

    history: list[dict] = field(default_factory=list)

    def adapt(
        self,
        reward_score,
        penalty_score,
        outcome_class,
    ):

        reward_score = clamp(reward_score)
        penalty_score = clamp(penalty_score)
        net = reward_score - penalty_score

        if outcome_class in {
            "knowledge_gain",
            "partial_success",
            "recoverable_failure",
        }:
            self.exploration_drive = clamp(
                self.exploration_drive + 0.05 + max(net, 0.0) * 0.05
            )
            self.failure_tolerance = clamp(
                self.failure_tolerance + 0.04
            )
        elif outcome_class in {
            "critical_failure",
            "repeated_failure",
        }:
            self.exploration_drive = clamp(
                self.exploration_drive - penalty_score * 0.08
            )
            self.failure_tolerance = clamp(
                self.failure_tolerance - penalty_score * 0.10
            )
        elif outcome_class in {
            "exact_success",
            "high_value_success",
            "success_with_residuals",
        }:
            self.exploration_drive = clamp(
                self.exploration_drive - 0.02
            )
            self.failure_tolerance = clamp(
                self.failure_tolerance + 0.02
            )

        self.reward_saturation = clamp(
            self.reward_saturation * 0.75 + reward_score * 0.25
        )
        self.risk_appetite = clamp(
            0.20
            + self.exploration_drive * 0.35
            + self.failure_tolerance * 0.20
            - penalty_score * 0.25
        )
        return self

    def synchronize_candy_state(
        self,
        balances=None,
        trends=None,
        reward_hacking_risk=0.0,
        reward_instability=0.0,
    ):

        self.balances = dict(balances or {})
        self.trends = dict(trends or {})
        if self.balances:
            self.dominant_motivation = max(
                self.balances,
                key=lambda key: self.balances.get(key, 0.0),
            )
        self.reward_hacking_risk = clamp(reward_hacking_risk)
        self.reward_stability = clamp(1.0 - reward_instability)
        return self

    def report(self):

        return {
            "balances": {
                key: round(value, 4)
                for key, value in self.balances.items()
            },
            "trends": {
                key: round(value, 4)
                for key, value in self.trends.items()
            },
            "dominant_motivation": self.dominant_motivation,
            "reward_stability": round(self.reward_stability, 4),
            "reward_hacking_risk": round(self.reward_hacking_risk, 4),
            "exploration_drive": round(self.exploration_drive, 4),
            "failure_tolerance": round(self.failure_tolerance, 4),
            "curiosity_balance": round(self.curiosity_balance, 4),
            "reward_saturation": round(self.reward_saturation, 4),
            "risk_appetite": round(self.risk_appetite, 4),
        }
