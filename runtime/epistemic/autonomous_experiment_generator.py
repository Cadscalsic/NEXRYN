class AutonomousExperimentGenerator:
    def generate(self, concept, bottleneck, strategy, sequence):
        feature = concept.removesuffix("_preservation")
        experiment_id = (
            f"truth_advancement:{concept}:{bottleneck}:"
            f"{strategy}:{sequence}"
        )
        return {
            "system": "autonomous_experiment_generator",
            "phase": "5.2",
            "experiment_id": experiment_id,
            "fingerprint": f"{concept}:{bottleneck}:{strategy}",
            "concept": concept,
            "target_metric": bottleneck,
            "strategy": strategy,
            "intervention_feature": feature,
            "hypothesis": (
                f"{concept} is causally relevant when controlled changes "
                f"to {feature} alter execution outcomes"
            ),
            "required_observations": [
                "baseline_execution_result",
                "intervention_execution_result",
                "causal_effect_delta",
                "contradiction_delta",
            ],
            "success_criteria": {
                "trial_causal_alignment": ">= 0.60",
                "truth_candidate_causal_alignment": ">= 0.80",
                "contradiction_score": "< 0.18",
            },
            "reversible": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "AutonomousExperimentGenerator",
]
