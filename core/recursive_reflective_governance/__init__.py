from core.recursive_reflective_governance.recursive_reflection_engine import (
    RecursiveReflectionEngine,
)
from core.recursive_reflective_governance.propagation_topology_monitor import (
    PropagationTopologyMonitor,
)
from core.recursive_reflective_governance.distributed_identity_manager import (
    DistributedIdentityManager,
)
from core.recursive_reflective_governance.recursive_growth_regulator import (
    RecursiveGrowthRegulator,
)
from core.recursive_reflective_governance.semantic_pruning_controller import (
    SemanticPruningController,
)
from core.recursive_reflective_governance.reflective_recursion_limits import (
    ReflectiveRecursionLimits,
)
from core.recursive_reflective_governance.topology_prediction_engine import (
    TopologyPredictionEngine,
)
from core.recursive_reflective_governance.adaptive_diffusion_balancer import (
    AdaptiveDiffusionBalancer,
)
from core.recursive_reflective_governance.recursive_stability_supervisor import (
    RecursiveStabilitySupervisor,
)
from core.recursive_reflective_governance.organized_recursive_runtime import (
    OrganizedRecursiveRuntime,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class RecursiveReflectiveGovernanceLayer:

    def __init__(self):

        self.recursive_reflection_engine = RecursiveReflectionEngine()
        self.propagation_topology_monitor = PropagationTopologyMonitor()
        self.distributed_identity_manager = DistributedIdentityManager()
        self.recursive_growth_regulator = RecursiveGrowthRegulator()
        self.semantic_pruning_controller = SemanticPruningController()
        self.reflective_recursion_limits = ReflectiveRecursionLimits()
        self.topology_prediction_engine = TopologyPredictionEngine()
        self.adaptive_diffusion_balancer = AdaptiveDiffusionBalancer()
        self.recursive_stability_supervisor = RecursiveStabilitySupervisor()
        self.organized_recursive_runtime = OrganizedRecursiveRuntime()
        self.reflective_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        reflection = self.recursive_reflection_engine.reflect(context)
        topology = self.propagation_topology_monitor.monitor(context)
        distributed_identity = self.distributed_identity_manager.manage(context)
        growth = self.recursive_growth_regulator.regulate(
            reflection,
            topology,
            distributed_identity,
        )
        pruning = self.semantic_pruning_controller.control(context, growth)
        limits = self.reflective_recursion_limits.enforce(
            reflection,
            growth,
            pruning,
        )
        topology_prediction = self.topology_prediction_engine.predict(
            context,
            topology,
        )
        diffusion = self.adaptive_diffusion_balancer.balance(context, pruning)
        supervisor = self.recursive_stability_supervisor.supervise([
            reflection,
            topology,
            distributed_identity,
            growth,
            pruning,
            limits,
            topology_prediction,
            diffusion,
        ])
        organized_runtime = self.organized_recursive_runtime.organize(
            supervisor,
            limits,
            diffusion,
        )

        reflective_score = _clamp(
            (1.0 - reflection.get("reflection_load", 0.0)) * 0.18
            +
            (1.0 - topology.get("topology_risk", 0.0)) * 0.18
            +
            (1.0 - distributed_identity.get("distributed_identity_risk", 0.0)) * 0.16
            +
            (1.0 - growth.get("recursive_growth_pressure", 0.0)) * 0.18
            +
            (1.0 - pruning.get("semantic_pruning_need", 0.0)) * 0.14
            +
            diffusion.get("diffusion_balance", 0.0) * 0.16
        )

        policy = {
            "reflect_before_recursion":
            bool(reflection.get("reflection_actions", [])),

            "localize_recursive_propagation":
            bool(topology.get("monitor_actions", [])),

            "cap_recursive_growth":
            bool(growth.get("growth_actions", [])),

            "control_semantic_pruning":
            bool(pruning.get("pruning_actions", [])),

            "enforce_reflective_recursion_limits":
            limits.get("limit_required", False),

            "balance_recursive_diffusion":
            bool(diffusion.get("diffusion_actions", [])),

            "organize_recursive_runtime":
            bool(organized_runtime.get("runtime_actions", [])),
        }

        report = {
            "system": "recursive_reflective_governance",
            "layer": "recursive_reflective_governance_layer",
            "recursive_reflection": reflection,
            "propagation_topology_monitor": topology,
            "distributed_identity_manager": distributed_identity,
            "recursive_growth_regulator": growth,
            "semantic_pruning_controller": pruning,
            "reflective_recursion_limits": limits,
            "topology_prediction": topology_prediction,
            "adaptive_diffusion_balancer": diffusion,
            "recursive_stability_supervisor": supervisor,
            "organized_recursive_runtime": organized_runtime,
            "recursive_reflective_score": reflective_score,
            "recursive_reflective_policy": policy,
            "recursive_reflective_state": (
                "recursive_reflective_governance_active"
                if any(policy.values())
                else "recursive_reflective_governance_standby"
            ),
        }

        self.reflective_history.append(report)
        self.reflective_history = self.reflective_history[-128:]

        return report


recursive_reflective_governance = RecursiveReflectiveGovernanceLayer()


__all__ = [
    "AdaptiveDiffusionBalancer",
    "DistributedIdentityManager",
    "OrganizedRecursiveRuntime",
    "PropagationTopologyMonitor",
    "RecursiveGrowthRegulator",
    "RecursiveReflectionEngine",
    "RecursiveReflectiveGovernanceLayer",
    "RecursiveStabilitySupervisor",
    "ReflectiveRecursionLimits",
    "SemanticPruningController",
    "TopologyPredictionEngine",
    "recursive_reflective_governance",
]
