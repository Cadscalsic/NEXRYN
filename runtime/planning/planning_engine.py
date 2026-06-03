# ============================================
# NEXRYN RECURSIVE COGNITIVE PLANNING ENGINE
# ============================================

from datetime import datetime
import uuid


# ============================================
# PLANNING ENGINE
# ============================================

class PlanningEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # PLAN STORAGE
        # ====================================

        self.plans = []

        # ====================================
        # RECURSIVE PLANS
        # ====================================

        self.recursive_plans = []

        # ====================================
        # PLAN HIERARCHY
        # ====================================

        self.plan_hierarchy = {}

        # ====================================
        # EXECUTION GRAPH
        # ====================================

        self.execution_graph = {

            "nodes": [],

            "edges": []
        }

        # ====================================
        # RESOURCE BUDGET
        # ====================================

        self.resource_budget = {

            "max_recursive_depth":
            12,

            "semantic_budget":
            256,

            "execution_budget":
            128,

            "stabilization_budget":
            32
        }

        # ====================================
        # STABILIZATION PLANS
        # ====================================

        self.stabilization_plans = []

        # ====================================
        # PLAN MEMORY
        # ====================================

        self.plan_memory = []

        # ====================================
        # FAILURE RECOVERY
        # ====================================

        self.failure_recovery_plans = []

        # ====================================
        # TEMPORAL PLANS
        # ====================================

        self.temporal_plans = []

        # ====================================
        # AUTONOMOUS DIRECTIVES
        # ====================================

        self.autonomous_directives = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "planning_mode":
            "recursive_cognitive_planning",

            "recursive_planning":
            "enabled",

            "adaptive_orchestration":
            "enabled",

            "temporal_planning":
            "enabled",

            "stabilization":
            "enabled",

            "autonomous_directives":
            "enabled",

            "planning_cycles":
            0
        }

    # ========================================
    # BUILD PLAN
    # ========================================

    def build_plan(

        self,

        synthesized_program
    ):

        steps = synthesized_program.get(
            "steps",
            []
        )

        planning_nodes = []

        # ====================================
        # CREATE NODES
        # ====================================

        for index, step in enumerate(
            steps
        ):

            node = {

                "node_id":
                str(uuid.uuid4()),

                "execution_index":
                index,

                "operation":
                step.get(
                    "operation"
                ),

                "parameters":
                step.get(
                    "parameters",
                    {}
                ),

                "dependencies":

                [index - 1]

                if index > 0

                else [],

                "priority":
                1.0,

                "semantic_weight":
                0.5,

                "recursive_depth":
                0,

                "status":
                "pending",

                "created_at":
                str(datetime.utcnow())
            }

            planning_nodes.append(
                node
            )

        # ====================================
        # BUILD PLAN
        # ====================================

        plan = {

            "plan_id":
            str(uuid.uuid4()),

            "node_count":
            len(planning_nodes),

            "nodes":
            planning_nodes,

            "plan_state":
            "active",

            "created_at":
            str(datetime.utcnow())
        }

        self.plans.append(
            plan
        )

        self.plan_memory.append({

            "type":
            "primary_plan",

            "plan":
            plan
        })

        return plan

    # ========================================
    # BUILD RECURSIVE PLAN
    # ========================================

    def build_recursive_plan(

        self,

        plan,

        recursive_depth=0
    ):

        if recursive_depth > self.resource_budget[
            "max_recursive_depth"
        ]:

            return {

                "recursive_state":
                "depth_limit_exceeded"
            }

        recursive_nodes = []

        for node in plan["nodes"]:

            recursive_node = {

                "recursive_node_id":
                str(uuid.uuid4()),

                "source_node":
                node["node_id"],

                "operation":
                node["operation"],

                "recursive_depth":
                recursive_depth + 1,

                "status":
                "recursive_pending"
            }

            recursive_nodes.append(
                recursive_node
            )

        recursive_plan = {

            "recursive_plan_id":
            str(uuid.uuid4()),

            "source_plan":
            plan["plan_id"],

            "recursive_depth":
            recursive_depth + 1,

            "recursive_nodes":
            recursive_nodes,

            "created_at":
            str(datetime.utcnow())
        }

        self.recursive_plans.append(
            recursive_plan
        )

        return recursive_plan

    # ========================================
    # BUILD PLAN HIERARCHY
    # ========================================

    def build_plan_hierarchy(

        self,

        plan
    ):

        hierarchy = {

            "root_plan":
            plan["plan_id"],

            "execution_layer":
            [],

            "semantic_layer":
            [],

            "stabilization_layer":
            [],

            "meta_layer":
            []
        }

        for node in plan["nodes"]:

            operation = str(
                node["operation"]
            )

            if "transform" in operation:

                hierarchy[
                    "execution_layer"
                ].append(node)

            elif "semantic" in operation:

                hierarchy[
                    "semantic_layer"
                ].append(node)

            elif "stabilize" in operation:

                hierarchy[
                    "stabilization_layer"
                ].append(node)

            else:

                hierarchy[
                    "meta_layer"
                ].append(node)

        self.plan_hierarchy = (
            hierarchy
        )

        return hierarchy

    # ========================================
    # BUILD STABILIZATION PLAN
    # ========================================

    def build_stabilization_plan(

        self,

        runtime_pressure=0.0
    ):

        actions = []

        if runtime_pressure >= 0.80:

            actions.extend([

                "recursive_throttling",

                "semantic_graph_pruning",

                "context_compression",

                "latency_reduction"
            ])

        elif runtime_pressure >= 0.45:

            actions.extend([

                "adaptive_scheduling",

                "partial_stabilization"
            ])

        else:

            actions.append(
                "maintain_runtime"
            )

        plan = {

            "plan_id":
            str(uuid.uuid4()),

            "runtime_pressure":
            runtime_pressure,

            "actions":
            actions,

            "created_at":
            str(datetime.utcnow())
        }

        self.stabilization_plans.append(
            plan
        )

        return plan

    # ========================================
    # BUILD TEMPORAL PLAN
    # ========================================

    def build_temporal_plan(

        self,

        future_projection_report
    ):

        plan = {

            "plan_id":
            str(uuid.uuid4()),

            "future_horizon":
            "adaptive_temporal_projection",

            "projection_state":
            future_projection_report,

            "temporal_actions": [

                "future_stabilization",

                "strategy_projection",

                "runtime_forecasting"
            ],

            "created_at":
            str(datetime.utcnow())
        }

        self.temporal_plans.append(
            plan
        )

        return plan

    # ========================================
    # GENERATE DIRECTIVES
    # ========================================

    def generate_directives(

        self,

        plan
    ):

        directives = []

        for node in plan["nodes"]:

            operation = str(
                node["operation"]
            )

            if "transform" in operation:

                directives.append(
                    "optimize_transformation"
                )

            elif "semantic" in operation:

                directives.append(
                    "expand_semantic_runtime"
                )

            else:

                directives.append(
                    "maintain_runtime_balance"
                )

        self.autonomous_directives = (
            directives
        )

        return directives

    # ========================================
    # BUILD EXECUTION GRAPH
    # ========================================

    def build_execution_graph(

        self,

        plan
    ):

        nodes = []

        edges = []

        for index, node in enumerate(
            plan["nodes"]
        ):

            nodes.append({

                "node_id":
                index,

                "operation":
                node["operation"],

                "status":
                node["status"]
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

        self.execution_graph = {

            "nodes":
            nodes,

            "edges":
            edges
        }

        return self.execution_graph

    # ========================================
    # FAILURE RECOVERY PLAN
    # ========================================

    def build_failure_recovery(

        self,

        failure_reason="unknown"
    ):

        recovery_plan = {

            "recovery_id":
            str(uuid.uuid4()),

            "failure_reason":
            failure_reason,

            "recovery_actions": [

                "runtime_stabilization",

                "context_recovery",

                "recursive_reset",

                "scheduler_rebalancing"
            ],

            "created_at":
            str(datetime.utcnow())
        }

        self.failure_recovery_plans.append(
            recovery_plan
        )

        return recovery_plan

    # ========================================
    # RUN PLANNING CYCLE
    # ========================================

    def run_planning_cycle(

        self,

        synthesized_program,

        runtime_pressure=0.0,

        future_projection_report=None,

        runtime_context=None
    ):

        # ====================================
        # SAFE RUNTIME CONTEXT
        # ====================================

        if runtime_context is None:

            runtime_context = {}

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        # ====================================
        # SAFE SYNTHESIZED PROGRAM
        # ====================================

        if synthesized_program is None:

            synthesized_program = {}

        if not isinstance(
            synthesized_program,
            dict
        ):

            synthesized_program = {}

        # ====================================
        # PRIMARY PLAN
        # ====================================

        plan = self.build_plan(
            synthesized_program
        )

        # ====================================
        # RECURSIVE DEPTH
        # ====================================

        recursive_paths = runtime_context.get(

            "recursive_paths",

            []
        )

        if recursive_paths is None:

            recursive_paths = []

        if not isinstance(
            recursive_paths,
            list
        ):

            recursive_paths = []

        recursive_depth = len(
            recursive_paths
        )

        # ====================================
        # RECURSIVE PROTECTION
        # ====================================

        recursive_limit = self.resource_budget.get(

            "max_recursive_depth",

            12
        )

        recursive_allowed = (

            recursive_depth
            < recursive_limit
        )

        # ====================================
        # RECURSIVE PLAN
        # ====================================

        if recursive_allowed:

            recursive_plan = (

                self.build_recursive_plan(

                    plan,

                    recursive_depth
                )
            )

        else:

            recursive_plan = {

                "recursive_state":
                "blocked",

                "reason":
                "recursive_limit_reached",

                "recursive_depth":
                recursive_depth
            }

        # ====================================
        # HIERARCHY
        # ====================================

        hierarchy = (

            self.build_plan_hierarchy(
                plan
            )
        )

        # ====================================
        # STABILIZATION
        # ====================================

        stabilization = (

            self.build_stabilization_plan(
                runtime_pressure
            )
        )

        # ====================================
        # TEMPORAL PLAN
        # ====================================

        temporal_plan = None

        if future_projection_report:

            temporal_plan = (

                self.build_temporal_plan(
                    future_projection_report
                )
            )

        # ====================================
        # DIRECTIVES
        # ====================================

        directives = (

            self.generate_directives(
                plan
            )
        )

        # ====================================
        # EXECUTION GRAPH
        # ====================================

        graph = (

            self.build_execution_graph(
                plan
            )
        )

        # ====================================
        # GOVERNANCE SAFE MODE
        # ====================================

        pressure_score = runtime_context.get(

            "pressure_score",

            0.0
        )

        governance_safe_mode = (

            pressure_score >= 50
        )

        # ====================================
        # SAFE MODE ACTIONS
        # ====================================

        if governance_safe_mode:

            stabilization[
                "safe_mode"
            ] = True

            stabilization[
                "recursive_expansion"
            ] = "disabled"

            stabilization[
                "advanced_planning"
            ] = "restricted"

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state[
            "planning_cycles"
        ] += 1

        # ====================================
        # FINAL REPORT
        # ====================================

        planning_report = {

            "plan":
            plan,

            "recursive_plan":
            recursive_plan,

            "hierarchy":
            hierarchy,

            "stabilization":
            stabilization,

            "temporal_plan":
            temporal_plan,

            "directives":
            directives,

            "execution_graph":
            graph,

            "recursive_depth":
            recursive_depth,

            "recursive_allowed":
            recursive_allowed,

            "governance_safe_mode":
            governance_safe_mode,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        return planning_report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "plans":
            len(self.plans),

            "recursive_plans":
            len(self.recursive_plans),

            "stabilization_plans":
            len(self.stabilization_plans),

            "temporal_plans":
            len(self.temporal_plans),

            "failure_recovery":
            len(self.failure_recovery_plans),

            "plan_memory":
            len(self.plan_memory),

            "execution_graph_nodes":
            len(
                self.execution_graph[
                    "nodes"
                ]
            ),

            "execution_graph_edges":
            len(
                self.execution_graph[
                    "edges"
                ]
            )
        }


# ============================================
# GLOBAL PLANNING ENGINE
# ============================================

planning_engine = (
    PlanningEngine()
)