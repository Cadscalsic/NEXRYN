from core.epistemic_models import clamp


class DependencyCoherenceEngine:
    """Discovers, validates, and scores dependency chain coherence."""

    SEMANTIC_RELATION_WEIGHTS = {
        "causes": 1.0,
        "creates": 1.0,
        "requires": 0.98,
        "preserves": 0.96,
        "modifies": 0.94,
        "depends_on": 0.92,
        "derived_from": 0.90,
        "enables": 0.90,
        "supports": 0.82,
        "context_requires": 0.86,
        "context_strengthens": 0.78,
        "context_weakens": 0.62,
    }

    def __init__(self, coherence_threshold=0.80):
        self.coherence_threshold = clamp(coherence_threshold)

    def _relation_type(self, dependency):
        metadata = dependency.get("metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        return str(
            dependency.get(
                "relation",
                dependency.get(
                    "relation_type",
                    metadata.get("relation", "supports"),
                ),
            )
            or "supports"
        )

    def _relation_semantics_score(self, dependency):
        relation = self._relation_type(dependency)
        return self.SEMANTIC_RELATION_WEIGHTS.get(relation, 0.68)

    def _dependency_support_score(self, dependency):
        if dependency.get("requires_review") or dependency.get("context_value") is None:
            return 0.0
        supported = dependency.get("supported") is True
        confidence = clamp(
            dependency.get(
                "confidence",
                dependency.get("support_score", 1.0 if supported else 0.0),
            )
        )
        if not supported:
            return 0.0
        return clamp(confidence * self._relation_semantics_score(dependency))

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
                "causes",
                "creates",
                "depends_on",
                "derived_from",
                "enables",
                "modifies",
                "preserves",
                "requires",
                "supports",
                "context_requires",
                "context_strengthens",
                "context_weakens",
            }
        ]
        dependency_scores = [
            self._dependency_support_score(item)
            for item in dependencies
        ]
        relation_semantics_score = clamp(
            sum(
                self._relation_semantics_score(item)
                for item in dependencies
                if item not in missing
            )
            / max(len([item for item in dependencies if item not in missing]), 1)
        )
        hidden_scores = [
            clamp(item["edge"].get("confidence", 0.0))
            * self.SEMANTIC_RELATION_WEIGHTS.get(
                item["edge"].get("relation_type"),
                0.68,
            )
            for item in hidden
        ]
        total = max(len(dependencies) + len(hidden), 1)
        dependency_strength = clamp(
            (
                sum(dependency_scores)
                + sum(hidden_scores)
            )
            / total
        )
        dependency_coherence = clamp(
            dependency_strength * 0.58
            + (1.0 - len(missing) / max(len(dependencies), 1)) * 0.27
            + relation_semantics_score * 0.15
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
            "relation_semantics_score": relation_semantics_score,
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
