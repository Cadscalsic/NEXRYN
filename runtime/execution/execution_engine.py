# ============================================
# NEXRYN EXECUTION ENGINE
# ============================================

from datetime import datetime


# ============================================
# EXECUTION ENGINE
# ============================================

class ExecutionEngine:

    def __init__(self):

        # ========================================
        # EXECUTION STATE
        # ========================================

        self.execution_state = {

            "execution_mode":
            "autonomous_recursive",

            "action_planning":
            "enabled",

            "tool_orchestration":
            "enabled",

            "recursive_monitoring":
            "active",

            "execution_adaptation":
            "enabled",

            "environment_interaction":
            "enabled",

            "execution_cycles":
            0,

            "execution_stability":
            "stable"
        }

        # ========================================
        # EXECUTION HISTORY
        # ========================================

        self.execution_history = []

        # ========================================
        # ACTIVE EXECUTIONS
        # ========================================

        self.active_executions = []

        # ========================================
        # EXECUTION TRACE
        # ========================================

        self.execution_trace = []

    # ============================================
    # BUILD EXECUTION ACTIONS
    # ============================================

    def build_execution_actions(

        self,

        execution_plan
    ):

        actions = []

        objectives = (

            execution_plan.get(

                "objectives",

                []
            )
        )

        for index, objective in enumerate(

            objectives
        ):

            action = {

                "action_id":
                index + 1,

                "objective":
                objective,

                "execution_type":
                "cognitive_operation",

                "priority":
                1.0,

                "status":
                "pending"
            }

            actions.append(
                action
            )

        return actions

    # ============================================
    # EXECUTE ACTIONS
    # ============================================

    def execute_actions(

        self,

        actions
    ):

        executed_actions = []

        for action in actions:

            executed_action = dict(
                action
            )

            executed_action[
                "status"
            ] = "executed"

            executed_action[
                "execution_result"
            ] = "success"

            executed_action[
                "timestamp"
            ] = str(
                datetime.utcnow()
            )

            executed_actions.append(
                executed_action
            )

            self.execution_trace.append({

                "action_id":

                executed_action.get(
                    "action_id"
                ),

                "objective":

                executed_action.get(
                    "objective"
                ),

                "status":
                "executed",

                "timestamp":
                str(
                    datetime.utcnow()
                )
            })

        return executed_actions

    # ============================================
    # MONITOR EXECUTION
    # ============================================

    def monitor_execution(

        self,

        executed_actions
    ):

        successful_actions = 0

        failed_actions = 0

        for action in executed_actions:

            if action.get(
                "execution_result"
            ) == "success":

                successful_actions += 1

            else:

                failed_actions += 1

        monitoring_report = {

            "total_actions":
            len(executed_actions),

            "successful_actions":
            successful_actions,

            "failed_actions":
            failed_actions,

            "execution_health":

            "stable"

            if failed_actions == 0

            else "degraded",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return monitoring_report

    # ============================================
    # ADAPT EXECUTION
    # ============================================

    def adapt_execution(

        self,

        monitoring_report
    ):

        adaptation = {

            "adaptation_required":

            monitoring_report.get(
                "failed_actions",
                0
            ) > 0,

            "adaptation_strategy":

            "recursive_recovery"

            if monitoring_report.get(
                "failed_actions",
                0
            ) > 0

            else "stable_execution",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return adaptation

    # ============================================
    # BUILD EXECUTION GRAPH
    # ============================================

    def build_execution_graph(

        self,

        executed_actions
    ):

        nodes = []

        edges = []

        for index, action in enumerate(

            executed_actions
        ):

            nodes.append({

                "node_id":
                index,

                "objective":

                action.get(
                    "objective"
                ),

                "state":
                "executed"
            })

            if index > 0:

                edges.append({

                    "source":
                    index - 1,

                    "target":
                    index,

                    "relation":
                    "execution_transition"
                })

        graph = {

            "node_count":
            len(nodes),

            "edge_count":
            len(edges),

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "recursive_execution_graph",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return graph

    # ============================================
    # RUN EXECUTION CYCLE
    # ============================================

    def run_execution_cycle(

        self,

        execution_plan
    ):

        # ========================================
        # BUILD ACTIONS
        # ========================================

        actions = (

            self.build_execution_actions(

                execution_plan
            )
        )

        # ========================================
        # REGISTER ACTIVE EXECUTION
        # ========================================

        self.active_executions.append({

            "execution_id":

            len(
                self.active_executions
            ) + 1,

            "objective_count":
            len(actions),

            "status":
            "running",

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

        # ========================================
        # EXECUTE ACTIONS
        # ========================================

        executed_actions = (

            self.execute_actions(
                actions
            )
        )

        # ========================================
        # MONITOR EXECUTION
        # ========================================

        monitoring_report = (

            self.monitor_execution(

                executed_actions
            )
        )

        # ========================================
        # ADAPT EXECUTION
        # ========================================

        adaptation_report = (

            self.adapt_execution(

                monitoring_report
            )
        )

        # ========================================
        # BUILD EXECUTION GRAPH
        # ========================================

        execution_graph = (

            self.build_execution_graph(

                executed_actions
            )
        )

        # ========================================
        # BUILD EXECUTION REPORT
        # ========================================

        execution_report = {

            "actions":
            actions,

            "executed_actions":
            executed_actions,

            "monitoring_report":
            monitoring_report,

            "adaptation_report":
            adaptation_report,

            "execution_graph":
            execution_graph,

            "execution_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.execution_history.append(
            execution_report
        )

        self.execution_state[
            "execution_cycles"
        ] += 1

        return execution_report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "execution_state":
            self.execution_state,

            "execution_history":
            len(
                self.execution_history
            ),

            "active_executions":
            len(
                self.active_executions
            ),

            "execution_trace":
            len(
                self.execution_trace
            ),

            "latest_execution":

            self.execution_history[-1]

            if self.execution_history

            else {}
        }


# ============================================
# GLOBAL EXECUTION ENGINE
# ============================================

execution_engine = (
    ExecutionEngine()
)