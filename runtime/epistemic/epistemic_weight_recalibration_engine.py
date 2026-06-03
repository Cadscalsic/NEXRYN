class EpistemicWeightRecalibrationEngine:
    def evaluate(self, evidence_registry, measurements):
        recalibrations = []
        for measurement in measurements or []:
            if (
                measurement.get("sandbox_validated") is not True
                or measurement.get("analysis_state")
                != "DIRECT_CAUSAL_EFFECT_OBSERVED"
            ):
                continue

            concept = measurement["concept"]
            previous_ratio = evidence_registry.fitness_ratio_for(concept)
            recalibrated_ratio = max(previous_ratio - 0.05, 0.10)
            evidence_registry.set_fitness_ratio(
                concept,
                recalibrated_ratio,
            )
            recalibrations.append({
                "concept": concept,
                "experiment_id": measurement["experiment_id"],
                "previous_evolutionary_fitness_ratio": previous_ratio,
                "recalibrated_evolutionary_fitness_ratio":
                recalibrated_ratio,
                "reason":
                "verified_direct_causal_intervention_reduces_survival_noise",
            })

        return {
            "system": "epistemic_weight_recalibration_engine",
            "phase": "5.7",
            "recalibrations": recalibrations,
            "survival_history_can_only_lose_influence": True,
            "direct_metric_inflation_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "EpistemicWeightRecalibrationEngine",
]
