class CausalExplainer:
    """Builds printable causal explanations from graph and dependency data."""

    def explain(self, concept, graph, dependencies=None, validation=None):
        dependencies = list(dependencies or [])
        validation = validation or {}
        complete, path = graph.concept_path_complete(concept)
        supporting = [
            item for item in dependencies if item.get("supported")
        ]
        contradicting = [
            item
            for item in dependencies
            if item.get("relation") in {"contradicts", "context_requires"}
            and not item.get("supported")
        ]

        when_valid = [
            (
                f"{item['context_key']} is "
                f"{item.get('context_value')}"
            )
            for item in supporting
        ]
        when_invalid = [
            (
                f"{item['context_key']} requires review under "
                f"{item.get('context_value')}"
            )
            for item in contradicting
        ]

        return {
            "concept": concept,
            "why": [
                "context dependencies support this concept"
                if supporting
                else "supporting dependencies are not yet established",
                "causal explanation path is complete"
                if complete
                else "causal explanation path is incomplete",
            ],
            "how_we_know": [
                (
                    f"{len(supporting)} supporting dependencies and "
                    f"{len(contradicting)} review dependencies observed"
                ),
                (
                    f"causal validation score "
                    f"{validation.get('causal_validation_score', 0.0)}"
                ),
            ],
            "when_valid": when_valid,
            "when_invalid": when_invalid,
            "supporting_dependencies": supporting,
            "contradicting_dependencies": contradicting,
            "explanation_path": path,
            "causal_path_complete": complete,
        }


__all__ = [
    "CausalExplainer",
]
