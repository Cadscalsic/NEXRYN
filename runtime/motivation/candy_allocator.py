"""Allocate reward assets with reuse as the highest-value signal."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.motivation.candy_types import CANDY_TYPES
from runtime.motivation.motivation_state import clamp


class CandyAllocator:
    weights = {
        "accuracy_gain": 0.25,
        "reuse_gain": 0.30,
        "efficiency_gain": 0.20,
        "generalization_gain": 0.15,
        "truth_alignment": 0.10,
    }

    def allocate(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        reward_assets: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        assets = dict(reward_assets or {})
        gains = self._gains(context, assets)
        reward_score = sum(
            gains[key] * self.weights[key]
            for key in self.weights
        )
        allocated = {
            "truth_candy": max(assets.get("truth_candy", 0.0), gains["truth_alignment"]),
            "curiosity_candy": assets.get("curiosity_candy", 0.0),
            "efficiency_candy": max(assets.get("efficiency_candy", 0.0), gains["efficiency_gain"]),
            "generalization_candy": max(
                assets.get("generalization_candy", 0.0),
                gains["generalization_gain"],
            ),
            "reuse_candy": max(assets.get("reuse_candy", 0.0), gains["reuse_gain"]),
            "recovery_candy": assets.get("recovery_candy", 0.0),
        }
        return {
            "reward_score": round(clamp(reward_score), 4),
            "reward_assets": {
                key: round(clamp(allocated.get(key, 0.0)), 4)
                for key in CANDY_TYPES
            },
            "reward_formula": dict(self.weights),
            "gains": {
                key: round(value, 4)
                for key, value in gains.items()
            },
            "reuse_bonus": round(gains["reuse_gain"] * self.weights["reuse_gain"], 4),
        }

    def _gains(
        self,
        context: Mapping[str, Any],
        assets: Mapping[str, Any],
    ) -> dict[str, float]:
        evaluation = self._mapping(context.get("evaluation_result"))
        prediction = self._mapping(context.get("prediction_report"))
        accuracy_gain = clamp(
            evaluation.get("accuracy", prediction.get("prediction_accuracy", 0.0))
        )
        reuse_gain = self._reuse_gain(context, assets)
        efficiency_gain = clamp(assets.get("efficiency_candy", 0.0))
        generalization_gain = clamp(assets.get("generalization_candy", 0.0))
        truth_alignment = clamp(
            context.get("truth_alignment", context.get("causal_consistency", assets.get("truth_candy", 0.0)))
        )
        return {
            "accuracy_gain": accuracy_gain,
            "reuse_gain": reuse_gain,
            "efficiency_gain": efficiency_gain,
            "generalization_gain": generalization_gain,
            "truth_alignment": truth_alignment,
        }

    def _reuse_gain(
        self,
        context: Mapping[str, Any],
        assets: Mapping[str, Any],
    ) -> float:
        memory_lookup = self._mapping(context.get("memory_lookup_report"))
        cache_metrics = self._mapping(context.get("cache_metrics_report"))
        reuse_signals = [
            assets.get("reuse_candy", 0.0),
            1.0 if context.get("pipeline_cache_hit") is True else 0.0,
            1.0 if context.get("strategy_reuse_applied") is True else 0.0,
            1.0 if context.get("program_reuse_applied") is True else 0.0,
            1.0 if context.get("context_reuse_applied") is True else 0.0,
            1.0 if memory_lookup.get("exact_cache_hit") is True else 0.0,
            cache_metrics.get("cache_hit_rate", 0.0),
            context.get("thinking_avoidance_score", 0.0),
        ]
        numeric = [clamp(value) for value in reuse_signals]
        return max(numeric) if numeric else 0.0

    def _mapping(self, value):
        return value if isinstance(value, Mapping) else {}


candy_allocator = CandyAllocator()


__all__ = [
    "CandyAllocator",
    "candy_allocator",
]
