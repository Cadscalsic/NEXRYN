class ExperimentHypothesisGenerator:
    def generate(self, proposal):
        if not proposal:
            return None

        experiment_id = proposal["experiment_id"]
        concept = proposal["concept"]
        target_metric = proposal["target_metric"]
        feature = proposal["intervention_feature"]

        return {
            "system": "experiment_hypothesis_generator",
            "phase": "5.3",
            "hypothesis_id": f"hypothesis:{experiment_id}",
            "experiment_id": experiment_id,
            "concept": concept,
            "target_metric": target_metric,
            "strategy": proposal["strategy"],
            "proposition": proposal["hypothesis"],
            "intervention_feature": feature,
            "expected_observation": (
                f"controlled intervention on {feature} changes execution "
                f"outcomes and raises measured {target_metric}"
            ),
            "falsification_criterion": (
                f"controlled intervention on {feature} does not produce "
                "a reproducible execution delta"
            ),
            "required_observations": list(
                proposal.get("required_observations", [])
            ),
            "sandbox_only": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "ExperimentHypothesisGenerator",
]
