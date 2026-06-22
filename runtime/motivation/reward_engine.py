# ============================================
# NEXRYN GRADUATED REWARD ENGINE
# ============================================

from runtime.motivation.motivation_state import clamp


class RewardEngine:

    def evaluate(self, runtime_context=None):

        context = runtime_context if isinstance(runtime_context, dict) else {}
        evaluation = self._mapping(context.get("evaluation_result"))
        prediction = self._mapping(context.get("prediction_report"))
        localization = self._mapping(
            context.get("transformation_localization")
        )
        performance = self._mapping(context.get("performance_report"))
        cache_report = self._mapping(context.get("cache_metrics_report"))

        accuracy = self._number(
            evaluation.get(
                "accuracy",
                prediction.get("prediction_accuracy", 0.0),
            )
        )
        exact_success = (
            evaluation.get("exact_success") is True
            or evaluation.get("success") is True
            and accuracy >= 1.0
        )
        success_state = evaluation.get(
            "success_state",
            context.get("success_state"),
        )
        success_with_residuals = (
            success_state == "SUCCESS_WITH_RESIDUALS"
        )
        partial_success = (
            evaluation.get("partial_success") is True
            or prediction.get("partial_success") is True
            or accuracy >= 0.80
        )

        truth_reward = self._average([
            context.get("causal_consistency", 0.0),
            context.get("identity_confidence", 0.0),
            1.0 if context.get("stable_truth") is True else 0.0,
            1.0 if context.get("identity_governance_state") in {
                "IDENTITY_GOVERNANCE_STABLE",
                "STABLE",
                "stable",
            } else 0.0,
        ])
        discovery_reward = self._average([
            1.0 if context.get("new_dependencies") else 0.0,
            1.0 if context.get("new_contexts") else 0.0,
            1.0 if context.get("semantic_abstractions") else 0.0,
            context.get("dependency_chain_coverage", 0.0),
        ])
        localization_reward = self._average([
            1.0 if localization.get("localization_ready") is True else 0.0,
            localization.get("localization_confidence", 0.0),
            1.0 - min(
                float(context.get("residual_difference_count", 0) or 0)
                / 5.0,
                1.0,
            ),
        ])
        generalization_reward = self._average([
            1.0 if context.get("pipeline_cache_hit") is True else 0.0,
            1.0 if cache_report.get("cache_hit_rate", 0.0) else 0.0,
            1.0 if context.get("reusable_truth_commitments") else 0.0,
            context.get("dependency_coherence_average", 0.0),
        ])
        reuse_reward = self._reuse_reward(context, cache_report)
        efficiency_reward = self._efficiency_reward(context, performance)
        recovery_reward = self._average([
            1.0 if context.get("recovery_confirmed") is True else 0.0,
            1.0 if context.get("localized_prediction_mismatch_resolved") is True else 0.0,
            1.0 if context.get("future_error_rate_reduced") is True else 0.0,
        ])

        distribution = {
            "truth_reward": truth_reward,
            "discovery_reward": discovery_reward,
            "localization_reward": localization_reward,
            "generalization_reward": generalization_reward,
            "reuse_reward": reuse_reward,
            "efficiency_reward": efficiency_reward,
            "recovery_reward": recovery_reward,
        }
        base = self._average([
            truth_reward * 0.15,
            discovery_reward * 0.10,
            localization_reward * 0.12,
            generalization_reward * 0.15,
            reuse_reward * 0.30,
            efficiency_reward * 0.13,
            recovery_reward * 0.05,
        ]) * 7.0
        if exact_success:
            base = max(base, 0.92)
        elif success_with_residuals:
            base = max(base, 0.80)
        elif partial_success:
            base = max(base, min(0.78, accuracy))

        return {
            "system": "graduated_reward_engine",
            "reward_score": round(clamp(base), 4),
            "reward_distribution": distribution,
            "reward_assets": {
                "truth_candy": truth_reward,
                "curiosity_candy": discovery_reward,
                "efficiency_candy": efficiency_reward,
                "generalization_candy": generalization_reward,
                "reuse_candy": reuse_reward,
                "recovery_candy": recovery_reward,
            },
            "exact_success": exact_success,
            "success_with_residuals": success_with_residuals,
            "partial_success": partial_success,
        }

    def _efficiency_reward(self, context, performance):

        reasoning_depth = self._number(
            context.get("reasoning_depth", context.get("reasoning_depth_limit", 4))
        )
        active_routes = self._number(
            context.get("active_routes", context.get("max_active_routes", 4))
        )
        fast_execution = self._number(
            performance.get("total_runtime_seconds", 5.0)
        )
        memory_reuse = (
            context.get("pipeline_cache_hit") is True
            or self._mapping(context.get("memory_lookup_report")).get(
                "exact_cache_hit"
            ) is True
        )
        return self._average([
            1.0 - min(reasoning_depth / 8.0, 1.0),
            1.0 - min(active_routes / 8.0, 1.0),
            1.0 - min(fast_execution / 10.0, 1.0),
            1.0 if memory_reuse else 0.0,
        ])

    def _reuse_reward(self, context, cache_report):

        memory_lookup = self._mapping(context.get("memory_lookup_report"))
        return self._average([
            1.0 if context.get("pipeline_cache_hit") is True else 0.0,
            1.0 if context.get("strategy_reuse_applied") is True else 0.0,
            1.0 if context.get("program_reuse_applied") is True else 0.0,
            1.0 if context.get("context_reuse_applied") is True else 0.0,
            1.0 if memory_lookup.get("exact_cache_hit") is True else 0.0,
            cache_report.get("cache_hit_rate", 0.0),
            context.get("thinking_avoidance_score", 0.0),
        ])

    def _average(self, values):

        numeric = [clamp(value) for value in values]
        if not numeric:
            return 0.0
        return round(sum(numeric) / len(numeric), 4)

    def _mapping(self, value):

        return value if isinstance(value, dict) else {}

    def _number(self, value, default=0.0):

        try:
            return float(value)
        except (TypeError, ValueError):
            return default
