# ============================================
# NEXRYN COGNITIVE CANDY MANAGER
# ============================================

from runtime.motivation.candy_decay_engine import candy_decay_engine
from runtime.motivation.candy_history import CandyHistory
from runtime.motivation.candy_reporter import candy_reporter
from runtime.motivation.candy_types import CANDY_TYPES
from runtime.motivation.motivation_state import clamp


class CognitiveCandyManager:

    def __init__(self):

        self.balances = {
            key: 0.0
            for key in CANDY_TYPES
        }
        self.history = CandyHistory()

    def allocate(
        self,
        reward_assets,
        penalty_score=0.0,
        safety_multiplier=None,
        task_id=None,
        reward_hacking_risk=0.0,
        dominant_motivation=None,
        reuse_bonus=0.0,
        budget_adjustments=None,
    ):

        penalty_score = clamp(penalty_score)
        base_multiplier = (
            1.0 - penalty_score * 0.6
            if safety_multiplier is None
            else safety_multiplier
        )
        base_multiplier = clamp(base_multiplier)
        for key in self.balances:
            multiplier = candy_decay_engine.safety_multiplier(
                key,
                base_multiplier,
            )
            reward = clamp(reward_assets.get(key, 0.0))
            decay = candy_decay_engine.rate(key)
            self.balances[key] = clamp(
                self.balances[key] * decay
                + reward * multiplier
            )
        balances = {
            key: round(value, 4)
            for key, value in self.balances.items()
        }
        self.history.append(
            reward_assets={
                key: round(clamp(reward_assets.get(key, 0.0)), 4)
                for key in self.balances
            },
            penalty_score=penalty_score,
            resulting_balances=balances,
            task_id=task_id,
            reward_hacking_risk=reward_hacking_risk,
        )
        return self.report(
            dominant_motivation=dominant_motivation,
            reward_hacking_risk=reward_hacking_risk,
            reuse_bonus=reuse_bonus,
            budget_adjustments=budget_adjustments,
        )

    def report(
        self,
        dominant_motivation=None,
        reward_hacking_risk=0.0,
        reuse_bonus=0.0,
        budget_adjustments=None,
    ):

        balances = {
            key: round(value, 4)
            for key, value in self.balances.items()
        }
        dominant = (
            dominant_motivation
            or (
                max(balances, key=lambda key: balances.get(key, 0.0))
                if balances
                else "balanced"
            )
        )
        return candy_reporter.build(
            balances,
            dominant,
            reward_hacking_risk,
            reuse_bonus,
            budget_adjustments or {},
        )
