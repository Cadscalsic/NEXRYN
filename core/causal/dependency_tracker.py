from core.epistemic_models import clamp


class DependencyTracker:
    """Maps concepts to contextual factors that support or constrain them."""

    DEFAULT_RULES = {
        "color_preservation": [
            {
                "context_key": "color_behavior",
                "dependency": "color_behavior",
                "supports_unless": {"color_reassigned", "palette_changed"},
                "review_if": {"color_reassigned", "palette_changed"},
            },
        ],
        "shape_preservation": [
            {
                "context_key": "transformation_family",
                "dependency": "object_integrity",
                "supports_unless": {"shape_transform", "reshape"},
                "review_if": {"shape_transform", "reshape"},
            },
        ],
        "topology_preservation": [
            {
                "context_key": "topology_behavior",
                "dependency": "topology_behavior",
                "supports_unless": {"split", "merge", "topology_changed"},
                "review_if": {"split", "merge", "topology_changed"},
            },
        ],
        "identity_preservation": [
            {
                "context_key": "identity_behavior",
                "dependency": "identity_behavior",
                "supports_unless": {"identity_split", "identity_reassigned"},
                "review_if": {"identity_split", "identity_reassigned"},
            },
        ],
        "symmetry_reasoning": [
            {
                "context_key": "topology_behavior",
                "dependency": "symmetry_context",
                "supports_unless": {"asymmetric_split"},
                "review_if": {"asymmetric_split"},
            },
        ],
        "object_identity_preservation": [
            {
                "context_key": "identity_behavior",
                "dependency": "identity_behavior",
                "supports_unless": {"identity_split", "identity_reassigned"},
                "review_if": {"identity_split", "identity_reassigned"},
            },
            {
                "context_key": "object_count",
                "dependency": "object_count",
                "supports_unless": {"changed", "increased", "decreased"},
                "review_if": {"changed", "increased", "decreased"},
            },
        ],
    }

    def __init__(self, rules=None):
        self.rules = dict(self.DEFAULT_RULES)
        if rules:
            self.rules.update(rules)

    def _read_context(self, context, key):
        if not isinstance(context, dict):
            return None
        value = context.get(key)
        if value is None:
            value = context.get("context", {}).get(key, None)
        if value is None:
            value = context.get("metadata", {}).get(key, None)
        return value

    def dependencies_for(self, concept, context=None):
        dependencies = []
        for rule in self.rules.get(concept, []):
            key = rule["context_key"]
            value = self._read_context(context, key)
            value_key = str(value) if value is not None else "unknown"
            review_values = {str(item) for item in rule.get("review_if", set())}
            support_blockers = {
                str(item)
                for item in rule.get("supports_unless", set())
            }
            supported = value is not None and value_key not in support_blockers
            requires_review = value is None or value_key in review_values
            dependencies.append({
                "concept": concept,
                "dependency": rule.get("dependency", key),
                "context_key": key,
                "context_value": value,
                "supported": supported,
                "requires_review": requires_review,
                "relation": (
                    "supports"
                    if supported
                    else "context_requires"
                    if requires_review
                    else "contradicts"
                ),
                "confidence": 1.0 if value is not None else 0.35,
            })
        return dependencies

    def build_dependency_chain(self, concept, context=None):
        chain = [concept]
        for dependency in self.dependencies_for(concept, context):
            chain.append(dependency["dependency"])
            if dependency["requires_review"]:
                chain.append("contextual_truth_required")
        return chain

    def attach_dependencies(self, graph, concept, context=None):
        concept_node = graph.ensure_concept(concept)
        dependencies = self.dependencies_for(concept, context)
        for dependency in dependencies:
            context_node = graph.ensure_context(
                dependency["context_key"],
                dependency["context_value"],
                confidence=dependency["confidence"],
            )
            graph.add_edge(
                source=context_node.node_id,
                target=concept_node.node_id,
                relation_type=dependency["relation"],
                confidence=dependency["confidence"],
                weight=1.0,
                evidence=[dependency],
            )
        return dependencies

    def coherence(self, dependencies):
        if not dependencies:
            return 0.0
        support = sum(1 for item in dependencies if item["supported"])
        review_penalty = sum(
            0.5 for item in dependencies if item["requires_review"]
        )
        return clamp((support + review_penalty) / len(dependencies))

    def report(self, concept, context=None):
        dependencies = self.dependencies_for(concept, context)
        validated_links = [
            item
            for item in dependencies
            if item["supported"] and not item["requires_review"]
        ]
        missing_links = [
            item
            for item in dependencies
            if item["context_value"] is None or item["requires_review"]
        ]
        ranked_links = sorted(
            dependencies,
            key=lambda item: (
                item["supported"],
                item["confidence"],
            ),
            reverse=True,
        )
        return {
            "system": "dependency_tracker",
            "concept": concept,
            "dependency_coherence": self.coherence(dependencies),
            "missing_links": missing_links,
            "validated_links": validated_links,
            "ranked_links": ranked_links,
            "dependency_chain": self.build_dependency_chain(
                concept,
                context,
            ),
        }


__all__ = [
    "DependencyTracker",
]
