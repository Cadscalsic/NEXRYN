# ============================================
# NEXRYN COGNITIVE PHYSICS ENGINE
# ============================================

from datetime import datetime

from core.reality.branch_collapse import (
    BranchCollapse,
)

from core.reality.reality_scheduler import (
    RealityScheduler,
)

from core.reality.sandbox_lifetime import (
    SandboxLifetime,
)

from core.reality.simulation_budget import (
    SimulationBudget,
)

from core.reality.world_isolation import (
    WorldIsolation,
)


class CognitivePhysicsEngine:

    def __init__(self):

        self.simulation_budget = SimulationBudget()
        self.world_isolation = WorldIsolation()
        self.branch_collapse = BranchCollapse()
        self.reality_scheduler = RealityScheduler()
        self.sandbox_lifetime = SandboxLifetime()
        self.physics_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        budget_report = self.simulation_budget.allocate(
            context,
        )

        isolation_report = self.world_isolation.isolate_worlds(
            context,
            budget_report,
        )

        collapse_report = self.branch_collapse.collapse_unstable(
            isolation_report,
        )

        lifetime_report = self.sandbox_lifetime.assign_lifetime(
            isolation_report,
            collapse_report,
        )

        schedule_report = self.reality_scheduler.schedule(
            budget_report,
            isolation_report,
            lifetime_report,
        )

        report = {
            "system":
            "cognitive_physics_engine",

            "simulation_budget":
            budget_report,

            "world_isolation":
            isolation_report,

            "branch_collapse":
            collapse_report,

            "sandbox_lifetime":
            lifetime_report,

            "reality_scheduler":
            schedule_report,

            "write_barrier":
            {
                "sandbox_memory":
                "isolated_copy",

                "direct_core_commit":
                False,

                "commit_requirements":
                [
                    "identity_validation",
                    "causal_validation",
                    "entropy_validation",
                ],
            },

            "physics_state":
            (
                "branches_collapsed"
                if collapse_report.get(
                    "collapsed_count",
                    0,
                )
                else "bounded_parallel_reality"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.physics_history.append(
            report,
        )

        self.physics_history = (
            self.physics_history[-64:]
        )

        return report


cognitive_physics_engine = (
    CognitivePhysicsEngine()
)
