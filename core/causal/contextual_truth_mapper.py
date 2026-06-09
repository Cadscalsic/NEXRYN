from core.epistemic_models import clamp


class ContextualTruthMapper:
    """Converts absolute truth candidates into contextual truth maps."""

    def map_truth(
        self,
        concept,
        context_report=None,
        dependencies=None,
        counterfactual_report=None,
    ):
        context_report = context_report or {}
        dependencies = list(dependencies or [])
        counterfactual_report = counterfactual_report or {}
        valid_contexts = []
        invalid_contexts = []

        for dependency in dependencies:
            context_label = (
                f"{dependency.get('context_key')}="
                f"{dependency.get('context_value')}"
            )
            if dependency.get("supported"):
                valid_contexts.append(context_label)
            else:
                invalid_contexts.append(context_label)

        for key in [
            "transformation_family",
            "topology_behavior",
            "identity_behavior",
            "color_behavior",
        ]:
            if key in context_report:
                label = f"{key}={context_report[key]}"
                if label not in valid_contexts and label not in invalid_contexts:
                    valid_contexts.append(label)

        invalid_contexts.extend([
            f"counterfactual:{factor}"
            for factor in counterfactual_report.get(
                "invalidating_factors",
                [],
            )
        ])

        total = max(len(valid_contexts) + len(invalid_contexts), 1)
        context_confidence = clamp(len(valid_contexts) / total)
        transfer_reliability = clamp(
            (
                context_confidence
                + counterfactual_report.get(
                    "counterfactual_robustness",
                    context_confidence,
                )
            )
            / 2.0
        )
        return {
            "system": "contextual_truth_mapper",
            "concept": concept,
            "truth_type": (
                "CONTEXTUAL_TRUTH"
                if invalid_contexts
                else "ABSOLUTE_TRUTH_CANDIDATE"
            ),
            "valid_contexts": valid_contexts,
            "invalid_contexts": invalid_contexts,
            "transfer_reliability": transfer_reliability,
            "context_confidence": context_confidence,
            "context_transfer_reliability": transfer_reliability,
        }


__all__ = [
    "ContextualTruthMapper",
]
