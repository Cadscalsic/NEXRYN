# ============================================
# NEXRYN INTROSPECTION ENGINE
# ============================================


# ============================================
# INTROSPECTION ENGINE
# ============================================

class IntrospectionEngine:

    def __init__(self):

        self.introspection_history = []

    # ============================================
    # ANALYZE COGNITIVE CYCLE
    # ============================================

    def analyze_cycle(

        self,

        cognitive_cycle,

        evaluation_result
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

        execution = cognitive_cycle.get(
            "execution",
            {}
        )

        introspection_report = {

            "reasoning_depth":
            reasoning.get(
                "reasoning_depth",
                0
            ),

            "cognitive_complexity":
            reasoning.get(
                "cognitive_complexity",
                "unknown"
            ),

            "goal_confidence":
            goals.get(
                "confidence",
                0.0
            ),

            "semantic_concept_count":
            semantics.get(
                "concept_count",
                0
            ),

            "active_routes":
            routing.get(
                "route_count",
                0
            ),

            "execution_nodes":
            execution.get(
                "node_count",
                0
            ),

            "accuracy":
            evaluation_result.get(
                "accuracy",
                0.0
            ),

            "success":
            evaluation_result.get(
                "success",
                False
            ),

            "success_state":
            evaluation_result.get(
                "success_state",
                "FAILURE"
            ),

            "partial_success":
            evaluation_result.get(
                "partial_success",
                False
            )
        }

        return introspection_report

    # ============================================
    # BUILD INSIGHTS
    # ============================================

    def build_insights(

        self,

        introspection_report
    ):

        insights = []

        if introspection_report[
            "accuracy"
        ] < 1.0:

            insights.append(

                "Cognition requires improvement"
            )

        if introspection_report[
            "reasoning_depth"
        ] > 15:

            insights.append(

                "Reasoning depth is high"
            )

        if introspection_report[
            "semantic_concept_count"
        ] < 2:

            insights.append(

                "Low semantic abstraction richness"
            )

        if introspection_report[
            "active_routes"
        ] > 8:

            insights.append(

                "Routing complexity is increasing"
            )

        if not insights:

            insights.append(

                "Cognitive cycle is stable"
            )

        return insights

    # ============================================
    # STORE REPORT
    # ============================================

    def store_report(

        self,

        introspection_report
    ):

        self.introspection_history.append(

            introspection_report
        )

    # ============================================
    # BUILD SUMMARY
    # ============================================

    def build_summary(self):

        return {

            "history_size":
            len(
                self.introspection_history
            ),

            "latest_report":
            self.introspection_history[-1]

            if self.introspection_history

            else {}
        }
