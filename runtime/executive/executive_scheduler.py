# ============================================
# NEXRYN EXECUTIVE SCHEDULER
# ============================================


# ============================================
# EXECUTIVE SCHEDULER
# ============================================

from runtime import runtime_state


class ExecutiveScheduler:

    def __init__(self):

        self.execution_history = []

        self.runtime_state = {

            "current_stage":
            None,

            "execution_load":
            0.0,

            "overload_detected":
            False,

            "scheduler_mode":
            "adaptive"
        }

    # ============================================
    # COMPUTE STAGE PRIORITY
    # ============================================

    def compute_stage_priority(

        self,

        stage_name,

        cognitive_cycle
    ):

        reasoning = cognitive_cycle.get(
            "reasoning",
            {}
        )

        routing = cognitive_cycle.get(
            "routing",
            {}
        )

        semantics = cognitive_cycle.get(
            "semantics",
            {}
        )

        control = cognitive_cycle.get(
            "control",
            {}
        )

        reasoning_depth = reasoning.get(
            "reasoning_depth",
            0
        )

        route_count = routing.get(
            "route_count",
            0
        )

        semantic_density = semantics.get(
            "concept_count",
            0
        )

        exploration_rate = control.get(
            "exploration_rate",
            0.0
        )

        base_priority = 1.0

        # ====================================
        # STAGE WEIGHTS
        # ====================================

        stage_weights = {

            "task_loading":
            0.5,

            "grid_analysis":
            0.8,

            "object_detection":
            1.0,

            "pattern_rule":
            1.2,

            "inference":
            2.0,

            "transformation":
            1.5,

            "evaluation":
            1.7,

            "self_improvement":
            1.3
        }

        weight = stage_weights.get(
            stage_name,
            1.0
        )

        priority_score = (

            base_priority

            +

            weight

            +

            reasoning_depth * 0.10

            +

            semantic_density * 0.08

            +

            route_count * 0.06

            +

            exploration_rate * 0.15
        )

        return round(
            priority_score,
            4
        )

    # ============================================
    # BUILD EXECUTION PLAN
    # ============================================

    def build_execution_plan(

        self,

        stages,

        cognitive_cycle
    ):

        plan = []

        for stage in stages:

            priority = (

                self.compute_stage_priority(

                    stage,

                    cognitive_cycle
                )
            )

            plan.append({

                "stage":
                stage,

                "priority":
                priority
            })

        plan = sorted(

            plan,

            key=lambda x: x[
                "priority"
            ],

            reverse=True
        )

        return plan

    # ============================================
    # BUILD EXECUTIVE RUNTIME SUMMARY
    # ============================================

    # ============================================
    # DETECT EXECUTION OVERLOAD
    # ============================================

    def detect_execution_overload(

        self,

        execution_plan
    ):

        total_priority = 0.0

        for stage in execution_plan:

            total_priority += stage.get(
                "priority",
                0.0
            )

        overload = (
            total_priority > 20
        )

        return {

            "overload":
            overload,

            "execution_load":
            round(
                total_priority,
                4
            )
        }

    # ============================================
    # ADAPT EXECUTION PLAN
    # ============================================

    def adapt_execution_plan(

        self,

        execution_plan
    ):

        overload_state = (

            self.detect_execution_overload(

                execution_plan
            )
        )

        if not overload_state.get(
            "overload",
            False
        ):

            return execution_plan

        adapted_plan = []

        for stage in execution_plan:

            stage_name = stage.get(
                "stage",
                "unknown"
            )

            if stage_name in [

                "exploration",
                "analogical_transfer",
                "self_improvement"
            ]:

                continue

            adapted_plan.append(
                stage
            )

        return adapted_plan

    # ============================================
    # STORE EXECUTION EVENT
    # ============================================

    def store_execution_event(

        self,

        execution_plan
    ):

        self.execution_history.append(
            execution_plan
        )

    # ============================================
    # UPDATE RUNTIME STATE
    # ============================================

    def update_runtime_state(

        self,

        execution_plan
    ):

        overload_state = (

            self.detect_execution_overload(

                execution_plan
            )
        )

        current_stage = None

        # ====================================
        # INITIAL STAGE
        # ====================================

        if len(execution_plan) > 0:

            current_stage = execution_plan[
                0
            ].get(
                "stage"
            )

        # ====================================
        # UPDATE EXECUTION LOAD
        # ====================================

        self.runtime_state[
            "execution_load"
        ] = overload_state.get(

            "execution_load",

            0.0
        )

        # ====================================
        # UPDATE OVERLOAD STATE
        # ====================================

        self.runtime_state[
            "overload_detected"
        ] = overload_state.get(

            "overload",

            False
        )

        # ====================================
        # UPDATE SCHEDULER MODE
        # ====================================

        self.runtime_state[
            "scheduler_mode"
        ] = "adaptive"

        # ====================================
        # INITIAL CURRENT STAGE
        # ====================================

        if current_stage is not None:

            self.runtime_state[
                "current_stage"
            ] = current_stage
    # ============================================
    # BUILD SCHEDULER REPORT
    # ============================================

    def build_scheduler_report(self):

        return {

            "history_size":
            len(
                self.execution_history
            ),

            "runtime_state":
            self.runtime_state
        }

     # ============================================
    # BUILD EXECUTIVE_RUNTIME SUMMARY
    # ============================================

    def build_runtime_summary(self):

        overload_events = 0

        for plan in self.execution_history:

            overload_state = (

                self.detect_execution_overload(
                    plan
                )
            )

            if overload_state.get(
                "overload",
                False
            ):

                overload_events += 1

        return {

            "execution_cycles":
            len(
                self.execution_history
            ),

            "overload_events":
            overload_events,

            "current_stage":

            self.runtime_state.get(

                "current_stage",

                "unknown"
            ),

            "runtime_stability":

            "stable"

            if overload_events < 3

            else "execution_stressed"
        }
