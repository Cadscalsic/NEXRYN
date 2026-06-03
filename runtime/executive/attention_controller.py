# ============================================
# NEXRYN EXECUTIVE ATTENTION CONTROLLER
# ============================================


# ============================================
# ATTENTION CONTROLLER
# ============================================

class AttentionController:

    def __init__(self):

        self.attention_history = []

        self.focus_state = {

            "active_focus":
            None,

            "attention_score":
            0.0,

            "overload_detected":
            False,

            "suppressed_routes":
            []
        }

    # ============================================
    # COMPUTE ATTENTION PRIORITY
    # ============================================

    def compute_priority(

        self,

        cognitive_cycle
    ):

        reasoning = cognitive_cycle.get(
            "reasoning",
            {}
        )

        goals = cognitive_cycle.get(
            "goals",
            {}
        )

        semantics = cognitive_cycle.get(
            "semantics",
            {}
        )

        routing = cognitive_cycle.get(
            "routing",
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

        semantic_density = semantics.get(
            "concept_count",
            0
        )

        route_count = routing.get(
            "route_count",
            0
        )

        goal_confidence = goals.get(
            "confidence",
            0.0
        )

        exploration_rate = control.get(
            "exploration_rate",
            0.0
        )

        # ====================================
        # COMPUTE ATTENTION SCORE
        # ====================================

        attention_score = (

            reasoning_depth * 0.25

            +

            semantic_density * 0.20

            +

            route_count * 0.20

            +

            goal_confidence * 10 * 0.25

            +

            exploration_rate * 10 * 0.10
        )

        overload_detected = (
            attention_score > 8.0
        )

        focus_target = goals.get(
            "goal_type",
            "general_reasoning"
        )

        result = {

            "focus_target":
            focus_target,

            "attention_score":
            round(
                attention_score,
                4
            ),

            "reasoning_depth":
            reasoning_depth,

            "semantic_density":
            semantic_density,

            "route_count":
            route_count,

            "goal_confidence":
            goal_confidence,

            "overload_detected":
            overload_detected
        }

        return result

    # ============================================
    # SUPPRESS LOW PRIORITY ROUTES
    # ============================================

    def suppress_routes(

        self,

        routing_plan,

        threshold=6
    ):

        suppressed = []

        active_routes = routing_plan.get(
            "active_routes",
            []
        )

        if len(active_routes) <= threshold:

            return suppressed

        low_priority_routes = [

            "exploration",
            "analogical_transfer",
            "self_improvement"
        ]

        for route in low_priority_routes:

            if route in active_routes:

                suppressed.append(
                    route
                )

        return suppressed

    # ============================================
    # BUILD ATTENTION PLAN
    # ============================================

    def build_attention_plan(

        self,

        cognitive_cycle
    ):

        priority = self.compute_priority(

            cognitive_cycle
        )

        routing = cognitive_cycle.get(
            "routing",
            {}
        )

        suppressed_routes = (

            self.suppress_routes(
                routing
            )
        )

        plan = {

            "focus_target":
            priority.get(
                "focus_target"
            ),

            "attention_score":
            priority.get(
                "attention_score"
            ),

            "overload_detected":
            priority.get(
                "overload_detected"
            ),

            "suppressed_routes":
            suppressed_routes,

            "semantic_focus":
            priority.get(
                "semantic_density",
                0
            ) > 3,

            "deep_reasoning_enabled":
            priority.get(
                "reasoning_depth",
                0
            ) < 12
        }

        self.focus_state = {

            "active_focus":
            plan.get(
                "focus_target"
            ),

            "attention_score":
            plan.get(
                "attention_score"
            ),

            "overload_detected":
            plan.get(
                "overload_detected"
            ),

            "suppressed_routes":
            suppressed_routes
        }

        return plan

    # ============================================
    # STORE ATTENTION EVENT
    # ============================================

    def store_attention_event(

        self,

        plan
    ):

        self.attention_history.append(
            plan
        )

    # ============================================
    # BUILD ATTENTION REPORT
    # ============================================

    def build_attention_report(self):

        return {

            "history_size":
            len(
                self.attention_history
            ),

            "current_focus":
            self.focus_state.get(
                "active_focus"
            ),

            "attention_score":
            self.focus_state.get(
                "attention_score"
            ),

            "overload_detected":
            self.focus_state.get(
                "overload_detected"
            ),

            "suppressed_routes":
            self.focus_state.get(
                "suppressed_routes"
            )
        }

    # ============================================
    # DETECT COGNITIVE OVERLOAD
    # ============================================

    def detect_overload(

        self,

        cognitive_cycle
    ):

        priority = self.compute_priority(

            cognitive_cycle
        )

        return {

            "overload":
            priority.get(
                "overload_detected",
                False
            ),

            "attention_score":
            priority.get(
                "attention_score",
                0.0
            )
        }

    # ============================================
    # BUILD EXECUTIVE SUMMARY
    # ============================================

    def build_executive_summary(self):

        overload_events = 0

        for event in self.attention_history:

            if event.get(
                "overload_detected",
                False
            ):

                overload_events += 1

        return {

            "attention_cycles":
            len(
                self.attention_history
            ),

            "overload_events":
            overload_events,

            "current_focus":
            self.focus_state.get(
                "active_focus"
            ),

            "system_stability":

            "stable"

            if overload_events < 3

            else "attention_stressed"
        }