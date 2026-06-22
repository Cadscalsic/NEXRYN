"""Independent decay for cognitive candy balances."""

from __future__ import annotations

from runtime.motivation.candy_types import PROTECTED_CANDIES
from runtime.motivation.motivation_state import clamp

DECAY_RATES = {
    "truth_candy": 0.98,
    "generalization_candy": 0.95,
    "reuse_candy": 0.95,
    "efficiency_candy": 0.90,
    "curiosity_candy": 0.85,
    "recovery_candy": 0.80,
}


class CandyDecayEngine:
    def rate(self, candy_type: str) -> float:
        return DECAY_RATES.get(candy_type, 0.85)

    def apply(self, candy_type: str, balance: float) -> float:
        return clamp(balance * self.rate(candy_type))

    def safety_multiplier(self, candy_type: str, multiplier: float) -> float:
        multiplier = clamp(multiplier)
        if candy_type in PROTECTED_CANDIES:
            return max(multiplier, 0.75)
        return multiplier

    def average_decay(self, candy_types=None) -> float:
        keys = list(candy_types or DECAY_RATES)
        if not keys:
            return 0.0
        return round(sum(self.rate(key) for key in keys) / len(keys), 4)


candy_decay_engine = CandyDecayEngine()


__all__ = [
    "DECAY_RATES",
    "PROTECTED_CANDIES",
    "CandyDecayEngine",
    "candy_decay_engine",
]
