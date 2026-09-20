# ============================================
# NEXRYN COGNITIVE COST ESTIMATOR
# ============================================

from dataclasses import dataclass


@dataclass
class CognitiveCost:

    object_cost: float

    relation_cost: float

    dependency_cost: float

    governance_cost: float

    explanation_cost: float

    total_cost: float


@dataclass
class CognitiveCostWeights:

    object_weight: float = 0.24

    relation_weight: float = 0.18

    dependency_weight: float = 0.24

    governance_weight: float = 0.16

    explanation_weight: float = 0.18


class CognitiveCostEstimator:

    def __init__(self, weights=None):

        self.weights = weights or CognitiveCostWeights()

    def estimate(self, task_profile):

        object_cost = self._clamp(
            (task_profile.object_count / 12.0)
            + (task_profile.estimated_concepts / 24.0)
        )

        relation_cost = self._clamp(
            task_profile.spatial_complexity
            + (task_profile.object_count / 20.0)
        )

        dependency_cost = self._clamp(
            task_profile.process_complexity
            + (task_profile.transformation_count / 8.0)
            + (task_profile.temporal_complexity * 0.35)
        )

        governance_cost = self._clamp(
            task_profile.uncertainty
            + (task_profile.process_complexity * 0.35)
            + (1.0 - task_profile.historical_similarity) * 0.25
        )

        explanation_cost = self._clamp(
            (task_profile.estimated_concepts / 18.0)
            + (task_profile.transformation_count / 10.0)
            + (task_profile.spatial_complexity * 0.25)
        )

        total_cost = self._clamp(
            object_cost * self.weights.object_weight
            + relation_cost * self.weights.relation_weight
            + dependency_cost * self.weights.dependency_weight
            + governance_cost * self.weights.governance_weight
            + explanation_cost * self.weights.explanation_weight
        )

        return CognitiveCost(
            object_cost=round(object_cost, 4),
            relation_cost=round(relation_cost, 4),
            dependency_cost=round(dependency_cost, 4),
            governance_cost=round(governance_cost, 4),
            explanation_cost=round(explanation_cost, 4),
            total_cost=round(total_cost, 4),
        )

    def build_report(self, cognitive_cost):

        return {
            "object_cost": cognitive_cost.object_cost,
            "relation_cost": cognitive_cost.relation_cost,
            "dependency_cost": cognitive_cost.dependency_cost,
            "governance_cost": cognitive_cost.governance_cost,
            "explanation_cost": cognitive_cost.explanation_cost,
            "total_cost": cognitive_cost.total_cost,
        }

    @staticmethod
    def _clamp(value):

        return max(0.0, min(1.0, float(value)))


cognitive_cost_estimator = CognitiveCostEstimator()
