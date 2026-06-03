# ============================================
# NEXRYN EXECUTION PLAN BUILDER
# ============================================

from datetime import datetime

from copy import deepcopy


# ============================================
# EXECUTION PLAN BUILDER
# ============================================

class ExecutionPlanBuilder:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.plan_history = []

        self.execution_graphs = []

        self.engine_state = {

            "execution_planning":
            True,

            "dependency_mapping":
            True,

            "operator_scheduling":
            True,

            "plan_optimization":
            True,

            "adaptive_execution_order":
            True
        }

    # ========================================
    # BUILD EXECUTION NODE
    # ========================================

    def build_execution_node(

        self,

        step_index,

        program_step
    ):

        execution_node = {

            "node_id":
            f"step_{step_index}",

            "step_index":
            step_index,

            "operator":

            program_step.get(
                "operator",
                "unknown"
            ),

            "parameters":

            program_step.get(
                "parameters",
                {}
            ),

            "confidence":

            program_step.get(
                "confidence",
                0.0
            ),

            "dependencies":
            [],

            "execution_state":
            "pending"
        }

        return execution_node

    # ========================================
    # BUILD DEPENDENCIES
    # ========================================

    def build_dependencies(

        self,

        execution_nodes
    ):

        for index in range(

            len(execution_nodes)
        ):

            if index == 0:

                continue

            previous_node = (

                execution_nodes[
                    index - 1
                ]
            )

            current_node = (

                execution_nodes[
                    index
                ]
            )

            current_node[
                "dependencies"
            ].append(

                previous_node.get(
                    "node_id"
                )
            )

        return execution_nodes

    # ========================================
    # OPTIMIZE EXECUTION ORDER
    # ========================================

    def optimize_execution_order(

        self,

        execution_nodes
    ):

        optimized_nodes = sorted(

            execution_nodes,

            key=lambda node:

            node.get(
                "confidence",
                0.0
            ),

            reverse=True
        )

        return optimized_nodes

    # ========================================
    # BUILD EXECUTION GRAPH
    # ========================================

    def build_execution_graph(

        self,

        program_steps
    ):

        execution_nodes = []

        for index, step in enumerate(
            program_steps
        ):

            execution_node = (

                self.build_execution_node(

                    index,

                    step
                )
            )

            execution_nodes.append(
                execution_node
            )

        # ====================================
        # BUILD DEPENDENCIES
        # ====================================

        execution_nodes = (

            self.build_dependencies(

                execution_nodes
            )
        )

        # ====================================
        # OPTIMIZE ORDER
        # ====================================

        optimized_nodes = (

            self.optimize_execution_order(

                execution_nodes
            )
        )

        execution_graph = {

            "node_count":
            len(optimized_nodes),

            "execution_nodes":
            optimized_nodes,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.execution_graphs.append(
            deepcopy(execution_graph)
        )

        self.plan_history.append(
            optimized_nodes
        )

        return execution_graph

    # ========================================
    # BUILD EXECUTION SCHEDULE
    # ========================================

    def build_execution_schedule(

        self,

        execution_graph
    ):

        schedule = []

        execution_nodes = execution_graph.get(

            "execution_nodes",

            []
        )

        for node in execution_nodes:

            schedule.append({

                "node_id":

                node.get(
                    "node_id"
                ),

                "operator":

                node.get(
                    "operator"
                ),

                "execution_order":
                len(schedule),

                "scheduled":
                True
            })

        return {

            "schedule_size":
            len(schedule),

            "schedule":
            schedule
        }

    # ========================================
    # BUILD PLAN REPORT
    # ========================================

    def build_plan_report(

        self,

        program_steps
    ):

        # ====================================
        # BUILD GRAPH
        # ====================================

        execution_graph = (

            self.build_execution_graph(

                program_steps
            )
        )

        # ====================================
        # BUILD SCHEDULE
        # ====================================

        execution_schedule = (

            self.build_execution_schedule(

                execution_graph
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "execution_graph":
            execution_graph,

            "execution_schedule":
            execution_schedule,

            "graph_node_count":

            execution_graph.get(
                "node_count",
                0
            ),

            "schedule_size":

            execution_schedule.get(
                "schedule_size",
                0
            ),

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_graph = {}

        if self.execution_graphs:

            latest_graph = (

                self.execution_graphs[-1]
            )

        return {

            "execution_graphs":

            len(
                self.execution_graphs
            ),

            "plan_history":

            len(
                self.plan_history
            ),

            "engine_state":
            self.engine_state,

            "latest_graph":
            latest_graph
        }


# ============================================
# GLOBAL ENGINE
# ============================================

execution_plan_builder = (
    ExecutionPlanBuilder()
)