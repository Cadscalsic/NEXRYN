# ============================================
# NEXRYN EXECUTION GOVERNOR
# ============================================

from datetime import datetime


# ============================================
# EXECUTION GOVERNOR
# ============================================

class ExecutionGovernor:

    def __init__(self):

        # ========================================
        # GOVERNOR STATE
        # ========================================

        self.governor_state = {

            "governor_mode":
            "adaptive_execution_governance",

            "dynamic_suppression":
            "enabled",

            "execution_throttling":
            "enabled",

            "priority_routing":
            "enabled",

            "context_budgeting":
            "enabled",

            "recursive_scaling":
            "enabled",

            "resource_balancing":
            "enabled",

            "governor_stability":
            "stable",

            "governor_cycles":
            0
        }

        # ========================================
        # EXECUTION HISTORY
        # ========================================

        self.execution_history = []

        # ========================================
        # LOAD HISTORY
        # ========================================

        self.load_history = []

        # ========================================
        # SUPPRESSION HISTORY
        # ========================================

        self.suppression_history = []

        # ========================================
        # ACTIVATION HISTORY
        # ========================================

        self.activation_history = []

        # ========================================
        # RESOURCE HISTORY
        # ========================================

        self.resource_history = []

    # ============================================
    # ANALYZE EXECUTION LOAD
    # ============================================

    def analyze_execution_load(

        self,

        runtime_context
    ):

        context_size = len(
            runtime_context
        )

        active_systems = max(

            context_size - 20,
            0
        )

        execution_pressure = round(

            active_systems / 5,
            4
        )

        overload_detected = (
            execution_pressure > 25
        )

        if execution_pressure < 15:

            load_state = "stable"

        elif execution_pressure < 25:

            load_state = "elevated"

        else:

            load_state = "critical"

        load_report = {

            "context_size":
            context_size,

            "active_systems":
            active_systems,

            "execution_pressure":
            execution_pressure,

            "load_state":
            load_state,

            "overload_detected":
            overload_detected,

            "analysis_mode":
            "adaptive_recursive_analysis",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.load_history.append(
            load_report
        )

        return load_report

    # ============================================
    # BUILD EXECUTION PRIORITIES
    # ============================================

    def build_execution_priorities(

        self,

        runtime_context
    ):

        critical_contexts = [

            "execution_plan",
            "inference_report",
            "transformation_report",
            "evaluation_result",
            "memory_report",
            "executive_brain_report",
            "reasoning_orchestration_report",
            "context_report",
            "self_repair_report"
        ]

        high_priority = []
        medium_priority = []
        suppressed = []

        for key in runtime_context.keys():

            if key in critical_contexts:

                high_priority.append(
                    key
                )

            elif (

                "report" in key
                or
                "state" in key
            ):

                medium_priority.append(
                    key
                )

            else:

                suppressed.append(
                    key
                )

        priority_report = {

            "critical_execution_paths":
            high_priority,

            "medium_execution_paths":
            medium_priority,

            "suppressed_paths":
            suppressed,

            "priority_mode":
            "hierarchical_execution_priority",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return priority_report

    # ============================================
    # APPLY DYNAMIC SUPPRESSION
    # ============================================

    def apply_dynamic_suppression(

        self,

        priority_report,

        load_report
    ):

        overload_detected = (
            load_report.get(
                "overload_detected",
                False
            )
        )

        suppressed_paths = []

        if overload_detected:

            suppressed_paths = (

                priority_report.get(
                    "suppressed_paths",
                    []
                )[:30]
            )

            suppression_state = (
                "active"
            )

        else:

            suppression_state = (
                "inactive"
            )

        suppression_report = {

            "suppression_state":
            suppression_state,

            "suppressed_count":

            len(
                suppressed_paths
            ),

            "suppressed_paths":
            suppressed_paths,

            "suppression_mode":
            "adaptive_recursive_suppression",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.suppression_history.append(
            suppression_report
        )

        return suppression_report

    # ============================================
    # BUILD RESOURCE BUDGET
    # ============================================

    def build_resource_budget(

        self,

        load_report
    ):

        execution_pressure = (

            load_report.get(
                "execution_pressure",
                0
            )
        )

        if execution_pressure > 25:

            budget = {

                "reasoning_budget":
                0.30,

                "memory_budget":
                0.20,

                "context_budget":
                0.15,

                "repair_budget":
                0.15,

                "governance_budget":
                0.10,

                "research_budget":
                0.10
            }

        else:

            budget = {

                "reasoning_budget":
                0.25,

                "memory_budget":
                0.20,

                "context_budget":
                0.20,

                "repair_budget":
                0.15,

                "governance_budget":
                0.10,

                "research_budget":
                0.10
            }

        resource_report = {

            "resource_budget":
            budget,

            "budget_mode":
            "adaptive_recursive_budgeting",

            "execution_pressure":
            execution_pressure,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.resource_history.append(
            resource_report
        )

        return resource_report

    # ============================================
    # BUILD EXECUTION GRAPH
    # ============================================

    def build_execution_graph(

        self,

        priority_report
    ):

        critical_paths = (

            priority_report.get(
                "critical_execution_paths",
                []
            )
        )

        nodes = []
        edges = []

        for index, path in enumerate(
            critical_paths
        ):

            nodes.append({

                "node_id":
                index,

                "path":
                path,

                "state":
                "critical"
            })

        for index in range(

            len(nodes) - 1
        ):

            edges.append({

                "source":
                index,

                "target":
                index + 1,

                "relation":
                "execution_transition"
            })

        execution_graph = {

            "node_count":
            len(nodes),

            "edge_count":
            len(edges),

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "adaptive_execution_graph",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return execution_graph

    # ============================================
    # BUILD GOVERNOR SUMMARY
    # ============================================

    def build_governor_summary(

        self,

        load_report,

        suppression_report
    ):

        summary = {

            "execution_pressure":

            load_report.get(
                "execution_pressure",
                0
            ),

            "load_state":

            load_report.get(
                "load_state",
                "unknown"
            ),

            "overload_detected":

            load_report.get(
                "overload_detected",
                False
            ),

            "suppressed_paths":

            suppression_report.get(
                "suppressed_count",
                0
            ),

            "governor_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return summary

    # ============================================
    # RUN GOVERNOR CYCLE
    # ============================================

    def run_governor_cycle(

        self,

        runtime_context
    ):

        # ========================================
        # ANALYZE LOAD
        # ========================================

        load_report = (

            self.analyze_execution_load(

                runtime_context
            )
        )

        # ========================================
        # PRIORITY ROUTING
        # ========================================

        priority_report = (

            self.build_execution_priorities(

                runtime_context
            )
        )

        # ========================================
        # DYNAMIC SUPPRESSION
        # ========================================

        suppression_report = (

            self.apply_dynamic_suppression(

                priority_report,

                load_report
            )
        )

        # ========================================
        # RESOURCE BUDGET
        # ========================================

        resource_report = (

            self.build_resource_budget(

                load_report
            )
        )

        # ========================================
        # EXECUTION GRAPH
        # ========================================

        execution_graph = (

            self.build_execution_graph(

                priority_report
            )
        )

        # ========================================
        # SUMMARY
        # ========================================

        governor_summary = (

            self.build_governor_summary(

                load_report,

                suppression_report
            )
        )

        # ========================================
        # BUILD REPORT
        # ========================================

        report = {

            "load_report":
            load_report,

            "priority_report":
            priority_report,

            "suppression_report":
            suppression_report,

            "resource_report":
            resource_report,

            "execution_graph":
            execution_graph,

            "governor_summary":
            governor_summary,

            "governor_state":
            self.governor_state,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.execution_history.append(
            report
        )

        self.governor_state[
            "governor_cycles"
        ] += 1

        return report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        latest_cycle = {}

        if self.execution_history:

            latest_cycle = (

                self.execution_history[-1]
            )

        return {

            "governor_state":
            self.governor_state,

            "execution_cycles":

            len(
                self.execution_history
            ),

            "load_history":

            len(
                self.load_history
            ),

            "suppression_history":

            len(
                self.suppression_history
            ),

            "resource_history":

            len(
                self.resource_history
            ),

            "latest_cycle":
            latest_cycle
        }


# ============================================
# GLOBAL EXECUTION GOVERNOR
# ============================================

execution_governor = (
    ExecutionGovernor()
)