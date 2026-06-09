from core.epistemic_models import clamp


class DependencyCoherenceEngine:
    """Discovers, validates, and scores dependency chain coherence."""

    def __init__(self, coherence_threshold=0.80):
        self.coherence_threshold = clamp(coherence_threshold)

    def evaluate(self, dependencies=None, graph=None, concept=None):
        dependencies = list(dependencies or [])
        validated = [
            item
            for item in dependencies
            if item.get("supported") and not item.get("requires_review")
        ]
        missing = [
            item
            for item in dependencies
            if item.get("requires_review")
            or item.get("context_value") is None
        ]
        graph_links = []
        if graph is not None and concept:
            node_id = f"concept:{concept}"
            graph_links = graph.find_dependencies(node_id)
        hidden = [
            item
            for item in graph_links
            if item["edge"]["relation_type"] in {
                "depends_on",
                "context_requires",
                "context_strengthens",
                "context_weakens",
            }
        ]
        total = max(len(dependencies) + len(hidden), 1)
        dependency_strength = clamp(
            (
                len(validated)
                + sum(item["edge"].get("confidence", 0.0) for item in hidden)
            )
            / total
        )
        dependency_coherence = clamp(
            (
                dependency_strength
                + (1.0 - len(missing) / max(len(dependencies), 1))
            )
            / 2.0
        )
        if dependency_coherence >= 0.80:
            risk = "LOW"
        elif dependency_coherence >= 0.55:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        return {
            "system": "dependency_coherence_engine",
            "concept": concept,
            "dependency_coherence": dependency_coherence,
            "dependency_strength": dependency_strength,
            "dependency_confidence": dependency_strength,
            "validated_dependencies": validated,
            "missing_dependencies": missing,
            "hidden_dependencies": hidden,
            "dependency_gaps": missing,
            "dependency_risk": risk,
            "coherence_ready":
            dependency_coherence >= self.coherence_threshold,
            "recommended_action": (
                "USE_FOR_TRUTH_PROMOTION"
                if dependency_coherence >= self.coherence_threshold
                else "COLLECT_EVIDENCE"
            ),
        }


__all__ = [
    "DependencyCoherenceEngine",
]
