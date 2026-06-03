# ============================================
# NEXRYN COGNITIVE RESOURCE ALLOCATOR
# ============================================

from datetime import datetime


# ============================================
# COGNITIVE RESOURCE ALLOCATOR
# ============================================

class CognitiveResourceAllocator:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # RESOURCE STATE
        # ====================================

        self.resource_state = {

            "adaptive_resource_allocation":
            True,

            "recursive_resource_control":
            True,

            "semantic_bandwidth_management":
            True,

            "planning_distribution":
            True,

            "cognitive_resource_balancing":
            True,

            "allocation_cycles":
            0
        }

        # ====================================
        # RESOURCE HISTORY
        # ====================================

        self.resource_history = []

    # ========================================
    # ANALYZE RESOURCE DEMANDS
    # ========================================

    def analyze_resource_demands(

        self,

        runtime_context
    ):

        inference_report = (

            runtime_context.get(
                "inference_report"
            )

            or {}
        )

        recursive_report = (

            runtime_context.get(
                "recursive_report"
            )

            or {}
        )

        planning_report = (

            runtime_context.get(
                "autonomous_planning_report"
            )

            or {}
        )

        reasoning_depth = (

            inference_report.get(
                "reasoning_depth",
                0
            )
        )

        cognitive_pressure = (

            inference_report.get(
                "cognitive_pressure",
                0.0
            )
        )

        hypothesis_count = (

            recursive_report.get(
                "hypothesis_count",
                0
            )
        )

        planning_cycles = (

            planning_report.get(
                "planning_cycles",
                0
            )
        )

        return {

            "recursive_demand":
            reasoning_depth * 0.4,

            "semantic_demand":
            cognitive_pressure * 10,

            "planning_demand":
            planning_cycles * 0.5,

            "hypothesis_demand":
            hypothesis_count * 0.3
        }

    # ========================================
    # BUILD RESOURCE ALLOCATION
    # ========================================

    def build_resource_allocation(

        self,

        demand_report
    ):

        total_demand = sum(
            demand_report.values()
        )

        if total_demand <= 0:

            total_demand = 1

        allocation = {

            "recursive_budget":
            round(

                demand_report[
                    "recursive_demand"
                ] / total_demand,

                3
            ),

            "semantic_budget":
            round(

                demand_report[
                    "semantic_demand"
                ] / total_demand,

                3
            ),

            "planning_budget":
            round(

                demand_report[
                    "planning_demand"
                ] / total_demand,

                3
            ),

            "hypothesis_budget":
            round(

                demand_report[
                    "hypothesis_demand"
                ] / total_demand,

                3
            )
        }

        return allocation

    # ========================================
    # RUN RESOURCE CYCLE
    # ========================================

    def run_resource_cycle(

        self,

        runtime_context
    ):

        demand_report = (

            self.analyze_resource_demands(
                runtime_context
            )
        )

        resource_allocation = (

            self.build_resource_allocation(
                demand_report
            )
        )

        allocation_report = {

            "resource_demands":
            demand_report,

            "resource_allocation":
            resource_allocation,

            "timestamp":
            str(datetime.utcnow())
        }

        runtime_context[
            "cognitive_resource_report"
        ] = allocation_report

        self.resource_history.append(
            allocation_report
        )

        self.resource_state[
            "allocation_cycles"
        ] += 1

        return runtime_context

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "allocation_cycles":
            self.resource_state[
                "allocation_cycles"
            ],

            "resource_history":
            len(
                self.resource_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL RESOURCE ALLOCATOR
# ============================================

cognitive_resource_allocator = (
    CognitiveResourceAllocator()
)