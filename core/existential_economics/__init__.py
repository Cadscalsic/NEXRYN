from core.existential_economics.identity_cost_engine import IdentityCostEngine
from core.existential_economics.invariant_cost_model import InvariantCostModel
from core.existential_economics.merge_cost_estimator import MergeCostEstimator
from core.existential_economics.semantic_energy_budget import SemanticEnergyBudget
from core.existential_economics.continuity_resource_allocator import (
    ContinuityResourceAllocator,
)
from core.existential_economics.drift_cost_tracker import DriftCostTracker
from core.existential_economics.abstraction_overhead_engine import (
    AbstractionOverheadEngine,
)
from core.existential_economics.topology_maintenance_costs import (
    TopologyMaintenanceCosts,
)
from core.existential_economics.cognitive_resource_pressure import (
    CognitiveResourcePressure,
)
from core.existential_economics.existential_homeostasis import (
    ExistentialHomeostasis,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class CognitiveExistentialEconomics:

    def __init__(self):

        self.identity_cost_engine = IdentityCostEngine()
        self.invariant_cost_model = InvariantCostModel()
        self.merge_cost_estimator = MergeCostEstimator()
        self.semantic_energy_budget = SemanticEnergyBudget()
        self.continuity_resource_allocator = ContinuityResourceAllocator()
        self.drift_cost_tracker = DriftCostTracker()
        self.abstraction_overhead_engine = AbstractionOverheadEngine()
        self.topology_maintenance_costs = TopologyMaintenanceCosts()
        self.cognitive_resource_pressure = CognitiveResourcePressure()
        self.existential_homeostasis = ExistentialHomeostasis()
        self.economic_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        identity = self.identity_cost_engine.compute(context)
        invariant = self.invariant_cost_model.compute(context)
        merge = self.merge_cost_estimator.compute(context)
        semantic_budget = self.semantic_energy_budget.compute(context)
        continuity = self.continuity_resource_allocator.compute(
            identity,
            invariant,
            semantic_budget,
        )
        drift = self.drift_cost_tracker.compute(context)
        abstraction = self.abstraction_overhead_engine.compute(context)
        topology = self.topology_maintenance_costs.compute(context)

        component_reports = [
            identity,
            invariant,
            merge,
            semantic_budget,
            drift,
            abstraction,
            topology,
        ]

        pressure = self.cognitive_resource_pressure.compute(
            component_reports,
        )

        homeostasis = self.existential_homeostasis.compute(
            pressure,
            continuity,
        )

        total_cost = _clamp(
            pressure.get(
                "pressure_score",
                0.0,
            )
            * 0.72
            +
            continuity.get(
                "continuity_allocation",
                0.0,
            )
            * 0.28
        )

        report = {
            "system":
            "cognitive_existential_economics",

            "layer":
            "cost_of_being_a_self",

            "identity_cost":
            identity,

            "invariant_cost":
            invariant,

            "merge_cost":
            merge,

            "semantic_energy_budget":
            semantic_budget,

            "continuity_resource_allocation":
            continuity,

            "drift_cost":
            drift,

            "abstraction_overhead":
            abstraction,

            "topology_maintenance_cost":
            topology,

            "cognitive_resource_pressure":
            pressure,

            "existential_homeostasis":
            homeostasis,

            "total_existential_cost":
            total_cost,

            "economic_policy":
            {
                "price_identity_before_evolution":
                total_cost >= 0.28,

                "reduce_merge_frequency":
                total_cost >= 0.48,

                "reserve_continuity_budget":
                continuity.get(
                    "allocator_state",
                )
                == "continuity_prioritized",

                "defer_noncritical_abstractions":
                total_cost >= 0.48,

                "enter_existential_budget_emergency_mode":
                total_cost >= 0.72,
            },

            "economics_state":
            (
                "existential_cost_critical"
                if total_cost >= 0.72
                else "existential_cost_high"
                if total_cost >= 0.48
                else "existential_cost_elevated"
                if total_cost >= 0.28
                else "existential_cost_contained"
            ),
        }

        self.economic_history.append(report)
        self.economic_history = self.economic_history[-128:]

        return report


cognitive_existential_economics = CognitiveExistentialEconomics()


__all__ = [
    "AbstractionOverheadEngine",
    "CognitiveExistentialEconomics",
    "CognitiveResourcePressure",
    "ContinuityResourceAllocator",
    "DriftCostTracker",
    "ExistentialHomeostasis",
    "IdentityCostEngine",
    "InvariantCostModel",
    "MergeCostEstimator",
    "SemanticEnergyBudget",
    "TopologyMaintenanceCosts",
    "cognitive_existential_economics",
]
