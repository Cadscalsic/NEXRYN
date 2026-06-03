# ============================================
# NEXRYN EXECUTIVE BRAIN
# ============================================

from datetime import datetime

from runtime.executive.attention_controller import (
    AttentionController
)

from runtime.executive.executive_scheduler import (
    ExecutiveScheduler
)

from runtime.executive.runtime_awareness import (
    RuntimeAwareness
)


# ============================================
# EXECUTIVE BRAIN
# ============================================

class ExecutiveBrain:

    def __init__(self):

        # ========================================
        # EXECUTIVE SUBSYSTEMS
        # ========================================

        self.attention_controller = (
            AttentionController()
        )

        self.scheduler = (
            ExecutiveScheduler()
        )

        self.runtime_awareness = (
            RuntimeAwareness()
        )

        # ========================================
        # EXECUTIVE STATE
        # ========================================

        self.executive_state = {

            "executive_mode":
            "integrated_recursive_orchestration",

            "strategic_coordination":
            "enabled",

            "attention_regulation":
            "active",

            "execution_balancing":
            "active",

            "runtime_awareness":
            "active",

            "mission_persistence":
            "enabled",

            "resource_arbitration":
            "enabled",

            "executive_stability":
            "stable",

            "executive_cycles":
            0
        }

        # ========================================
        # EXECUTIVE HISTORY
        # ========================================

        self.executive_history = []

        # ========================================
        # ACTIVE MISSIONS
        # ========================================

        self.active_missions = []

        # ========================================
        # RESOURCE HISTORY
        # ========================================

        self.resource_history = []

        # ========================================
        # STRATEGIC HISTORY
        # ========================================

        self.strategic_history = []

    # ============================================
    # BUILD COGNITIVE CYCLE
    # ============================================

    def build_cognitive_cycle(

        self,

        runtime_context
    ):

        cognitive_cycle = {

            "reasoning":

            runtime_context.get(

                "recursive_report",

                {}
            ),

            "goals":

            runtime_context.get(

                "goal_state",

                {}
            ),

            "semantics":

            runtime_context.get(

                "knowledge_expansion_report",

                {}
            ),

            "routing":

            runtime_context.get(

                "routing_state",

                {}
            ),

            "control":

            runtime_context.get(

                "governance_report",

                {}
            )
        }

        return cognitive_cycle

    # ============================================
    # BUILD EXECUTION STAGES
    # ============================================

    def build_execution_stages(

        self,

        runtime_context
    ):

        stages = [

            "task_loading",

            "grid_analysis",

            "object_detection",

            "pattern_rule",

            "inference",

            "transformation",

            "evaluation",

            "self_improvement"
        ]

        # ========================================
        # ADD ADVANCED STAGES
        # ========================================

        if "execution_report" in runtime_context:

            stages.append(
                "execution_monitoring"
            )

        if "memory_report" in runtime_context:

            stages.append(
                "memory_consolidation"
            )

        if "context_report" in runtime_context:

            stages.append(
                "context_compression"
            )

        if "self_repair_report" in runtime_context:

            stages.append(
                "runtime_stabilization"
            )

        return stages

    # ============================================
    # BUILD STRATEGIC OBJECTIVES
    # ============================================

    def build_strategic_objectives(

        self,

        runtime_context
    ):

        objectives = []

        # ========================================
        # EXECUTION OBJECTIVE
        # ========================================

        if "execution_report" in runtime_context:

            objectives.append({

                "objective":
                "maintain_execution_continuity",

                "priority":
                "critical"
            })

        # ========================================
        # MEMORY OBJECTIVE
        # ========================================

        if "memory_state" in runtime_context:

            objectives.append({

                "objective":
                "preserve_memory_integrity",

                "priority":
                "critical"
            })

        # ========================================
        # CONTEXT OBJECTIVE
        # ========================================

        if "context_state" in runtime_context:

            objectives.append({

                "objective":
                "optimize_context_scalability",

                "priority":
                "high"
            })

        # ========================================
        # REPAIR OBJECTIVE
        # ========================================

        if "self_repair_state" in runtime_context:

            objectives.append({

                "objective":
                "maintain_runtime_stability",

                "priority":
                "high"
            })

        # ========================================
        # KNOWLEDGE OBJECTIVE
        # ========================================

        if "knowledge_expansion_report" in runtime_context:

            objectives.append({

                "objective":
                "expand_semantic_reasoning",

                "priority":
                "high"
            })

        return objectives

    # ============================================
    # ALLOCATE RESOURCES
    # ============================================

    def allocate_resources(

        self,

        attention_plan,

        scheduler_report
    ):

        attention_score = attention_plan.get(
            "attention_score",
            0.0
        )

        execution_load = (

            scheduler_report.get(

                "runtime_state",

                {}
            ).get(
                "execution_load",
                0.0
            )
        )

        memory_resources = 0.25
        execution_resources = 0.25
        repair_resources = 0.15
        context_resources = 0.20
        governance_resources = 0.15

        # ========================================
        # ADAPT RESOURCE BALANCING
        # ========================================

        if attention_score > 8:

            execution_resources += 0.05
            context_resources += 0.05

            governance_resources -= 0.05
            repair_resources -= 0.05

        if execution_load > 20:

            repair_resources += 0.05
            context_resources += 0.05

            execution_resources -= 0.05
            memory_resources -= 0.05

        allocation = {

            "memory_resources":
            round(
                memory_resources,
                4
            ),

            "execution_resources":
            round(
                execution_resources,
                4
            ),

            "repair_resources":
            round(
                repair_resources,
                4
            ),

            "context_resources":
            round(
                context_resources,
                4
            ),

            "governance_resources":
            round(
                governance_resources,
                4
            ),

            "allocation_mode":
            "adaptive_recursive_balancing",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.resource_history.append(
            allocation
        )

        return allocation

    # ============================================
    # BUILD EXECUTIVE MISSION
    # ============================================

    def build_executive_mission(

        self,

        objectives
    ):

        mission = {

            "mission_type":
            "persistent_recursive_optimization",

            "mission_objectives":

            [
                objective.get(
                    "objective"
                )

                for objective in objectives
            ],

            "mission_depth":
            len(objectives),

            "mission_state":
            "active",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.active_missions.append(
            mission
        )

        return mission

    # ============================================
    # BUILD EXECUTIVE GRAPH
    # ============================================

    def build_executive_graph(

        self,

        objectives
    ):

        nodes = []
        edges = []

        for index, objective in enumerate(

            objectives
        ):

            nodes.append({

                "node_id":
                index,

                "objective":

                objective.get(
                    "objective"
                ),

                "priority":

                objective.get(
                    "priority"
                )
            })

            if index > 0:

                edges.append({

                    "source":
                    index - 1,

                    "target":
                    index,

                    "relation":
                    "executive_transition"
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
            "executive_orchestration_graph",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return graph

    # ============================================
    # BUILD EXECUTIVE SUMMARY
    # ============================================

    def build_executive_summary(

        self,

        runtime_context,

        attention_report,

        scheduler_report,
    ):

        summary = {

            "systems_active":

            len(
                runtime_context
            ),

            "attention_focus":

            attention_report.get(
                "current_focus"
            ),

            "attention_score":

            attention_report.get(
                "attention_score"
            ),

            "current_stage":

            scheduler_report.get(

                "runtime_state",

                {}
            ).get(
                "current_stage"
            ),

            "execution_load":

            scheduler_report.get(

                "runtime_state",

                {}
            ).get(
                "execution_load"
            ),

            "runtime_health":

            self.runtime_awareness.build_report().get(
                "runtime_health"
            ),

            "executive_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return summary

    # ============================================
    # RUN EXECUTIVE CYCLE
    # ============================================

    def run_executive_cycle(

        self,

        runtime_context
    ):

        # ========================================
        # BUILD COGNITIVE CYCLE
        # ========================================

        cognitive_cycle = (

            self.build_cognitive_cycle(

                runtime_context
            )
        )

        # ========================================
        # BUILD ATTENTION PLAN
        # ========================================

        attention_plan = (

            self.attention_controller.build_attention_plan(

                cognitive_cycle
            )
        )

        self.attention_controller.store_attention_event(

            attention_plan
        )

        # ========================================
        # BUILD EXECUTION STAGES
        # ========================================

        stages = (

            self.build_execution_stages(

                runtime_context
            )
        )

        # ========================================
        # BUILD EXECUTION PLAN
        # ========================================

        execution_plan = (

            self.scheduler.build_execution_plan(

                stages,

                cognitive_cycle
            )
        )

        # ========================================
        # ADAPT EXECUTION PLAN
        # ========================================

        execution_plan = (

            self.scheduler.adapt_execution_plan(

                execution_plan
            )
        )

        # ========================================
        # STORE EXECUTION EVENT
        # ========================================

        self.scheduler.store_execution_event(

            execution_plan
        )

        # ========================================
        # UPDATE RUNTIME STATE
        # ========================================

        self.scheduler.update_runtime_state(

            execution_plan
        )

        # ========================================
        # UPDATE RUNTIME AWARENESS
        # ========================================

        if len(execution_plan) > 0:

            active_stage = (

                execution_plan[0].get(
                    "stage"
                )
            )

            self.runtime_awareness.update_stage(

                active_stage
            )

            self.runtime_awareness.complete_stage(

                active_stage
            )

        overload_state = (

            self.scheduler.detect_execution_overload(

                execution_plan
            )
        )

        self.runtime_awareness.update_load(

            overload_state.get(
                "execution_load",
                0.0
            )
        )

        # ========================================
        # BUILD STRATEGIC OBJECTIVES
        # ========================================

        objectives = (

            self.build_strategic_objectives(

                runtime_context
            )
        )

        # ========================================
        # ALLOCATE RESOURCES
        # ========================================

        resource_allocation = (

            self.allocate_resources(

                attention_plan,

                self.scheduler.build_scheduler_report()
            )
        )

        # ========================================
        # BUILD EXECUTIVE MISSION
        # ========================================

        mission = (

            self.build_executive_mission(
                objectives
            )
        )

        # ========================================
        # BUILD EXECUTIVE GRAPH
        # ========================================

        executive_graph = (

            self.build_executive_graph(
                objectives
            )
        )

        # ========================================
        # BUILD REPORTS
        # ========================================

        attention_report = (

            self.attention_controller.build_attention_report()
        )

        scheduler_report = (

            self.scheduler.build_scheduler_report()
        )

        runtime_awareness_report = (

            self.runtime_awareness.build_report()
        )

        executive_summary = (

            self.build_executive_summary(

                runtime_context,

                attention_report,

                scheduler_report
            )
        )

        # ========================================
        # BUILD EXECUTIVE REPORT
        # ========================================

        executive_report = {

            "attention_report":
            attention_report,

            "scheduler_report":
            scheduler_report,

            "runtime_awareness":
            runtime_awareness_report,

            "strategic_objectives":
            objectives,

            "resource_allocation":
            resource_allocation,

            "mission":
            mission,

            "executive_graph":
            executive_graph,

            "executive_summary":
            executive_summary,

            "executive_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.executive_history.append(
            executive_report
        )

        self.strategic_history.append(
            executive_summary
        )

        self.executive_state[
            "executive_cycles"
        ] += 1

        return executive_report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "executive_state":
            self.executive_state,

            "executive_history":

            len(
                self.executive_history
            ),

            "active_missions":

            len(
                self.active_missions
            ),

            "resource_history":

            len(
                self.resource_history
            ),

            "strategic_history":

            len(
                self.strategic_history
            ),

            "attention_summary":

            self.attention_controller.build_executive_summary(),

            "scheduler_summary":

            self.scheduler.build_runtime_summary(),

            "runtime_awareness":

            self.runtime_awareness.build_report(),

            "latest_cycle":

            self.executive_history[-1]

            if self.executive_history

            else {}
        }


# ============================================
# GLOBAL EXECUTIVE BRAIN
# ============================================

executive_brain = (
    ExecutiveBrain()
)
