from core.identity.semantic_containment_engine import (
    SemanticContainmentEngine as CoreSemanticContainmentEngine,
)


class SemanticContainmentEngine:
    """Applies remembered merge and accumulated causal identity containment."""

    def __init__(
        self,
        minimum_conflicting_observations=2,
        maximum_conflict_reliability=0.50,
        core_engine=None,
    ):
        self.minimum_conflicting_observations = max(
            int(minimum_conflicting_observations),
            1,
        )
        self.maximum_conflict_reliability = maximum_conflict_reliability
        self.core_engine = core_engine or CoreSemanticContainmentEngine()

    def _causal_relationships(self, context):
        validation = context.get("causal_graph_validation", {})
        relationships = validation.get("relationship_checks", [])
        if relationships:
            return relationships
        accumulator = context.get("causal_evidence_accumulator", {})
        return [
            {
                "source": relationship.get("source"),
                "target": relationship.get("target"),
                "causal_support": relationship,
            }
            for relationship in accumulator.get("relationships", [])
        ]

    def _causal_identity_conflicts(self, concept, context):
        conflicts = []
        for relationship in self._causal_relationships(context):
            if concept not in [
                relationship.get("source"),
                relationship.get("target"),
            ]:
                continue
            support = relationship.get("causal_support", {})
            observations = support.get("observation_count", 0)
            conflicting = support.get("conflicting_observation_count", 0)
            reliability = support.get("support_reliability", 0.0)
            if (
                observations
                and conflicting >= self.minimum_conflicting_observations
                and reliability < self.maximum_conflict_reliability
            ):
                conflicts.append({
                    "source": relationship.get("source"),
                    "target": relationship.get("target"),
                    "observation_count": observations,
                    "conflicting_observation_count": conflicting,
                    "support_reliability": reliability,
                    "causal_support_score":
                    support.get("causal_support_score", 0.0),
                })
        return conflicts

    def evaluate(self, concept, context=None):
        context = context if isinstance(context, dict) else {}
        core_report = self.core_engine.evaluate(concept, context)
        causal_identity_conflicts = self._causal_identity_conflicts(
            concept,
            context,
        )
        causal_containment_active = bool(causal_identity_conflicts)
        containment_active = (
            core_report["containment_active"]
            or causal_containment_active
        )
        return {
            **core_report,
            "system": "runtime_semantic_containment_engine",
            "core_semantic_containment": core_report,
            "causal_identity_conflicts": causal_identity_conflicts,
            "causal_containment_active": causal_containment_active,
            "containment_active": containment_active,
            "integration_allowed": not containment_active,
            "containment_state": (
                core_report["containment_state"]
                if core_report["containment_active"]
                else "CAUSAL_IDENTITY_CONFLICT_CONTAINED"
                if causal_containment_active
                else "SEMANTIC_CONTAINMENT_CLEAR"
            ),
            "accumulating_causal_support_is_not_identity_conflict": True,
        }


semantic_containment_engine = SemanticContainmentEngine()


__all__ = [
    "SemanticContainmentEngine",
    "semantic_containment_engine",
]
