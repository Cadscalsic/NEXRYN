# ============================================
# NEXRYN DYNAMIC COGNITIVE ROUTER
# ============================================


# ============================================
# DYNAMIC COGNITIVE ROUTER
# ============================================

class DynamicCognitiveRouter:

    def __init__(self):

        self.available_routes = {

            "exploration":
            True,

            "mutation":
            True,

            "search":
            True,

            "planning":
            True,

            "recursive_cognition":
            True,

            "analogical_transfer":
            True,

            "world_modeling":
            True,

            "self_improvement":
            True
        }

    # ============================================
    # BUILD ROUTING PLAN
    # ============================================

    def build_routing_plan(

        self,

        cognitive_state
    ):

        routing_plan = {

            "exploration":
            False,

            "mutation":
            False,

            "search":
            False,

            "planning":
            True,

            "recursive_cognition":
            True,

            "analogical_transfer":
            True,

            "world_modeling":
            True,

            "self_improvement":
            True
        }

        confidence = cognitive_state.get(
            "confidence",
            0.0
        )

        mode = cognitive_state.get(
            "cognitive_mode",
            "idle"
        )

        reasoning_depth = cognitive_state.get(
            "reasoning_depth",
            0
        )

        # ========================================
        # LOW CONFIDENCE
        # ========================================

        if confidence < 0.4:

            routing_plan[
                "exploration"
            ] = True

            routing_plan[
                "mutation"
            ] = True

            routing_plan[
                "search"
            ] = True

        # ========================================
        # MID CONFIDENCE
        # ========================================

        elif confidence < 0.75:

            routing_plan[
                "search"
            ] = True

            routing_plan[
                "mutation"
            ] = True

        # ========================================
        # HIGH CONFIDENCE
        # ========================================

        else:

            routing_plan[
                "search"
            ] = False

            routing_plan[
                "mutation"
            ] = False

            routing_plan[
                "exploration"
            ] = False

        # ========================================
        # DEEP REASONING
        # ========================================

        if reasoning_depth > 15:

            routing_plan[
                "recursive_cognition"
            ] = True

        # ========================================
        # EXPLORATION MODE
        # ========================================

        if mode == "exploration":

            routing_plan[
                "exploration"
            ] = True

        return routing_plan

    # ============================================
    # BUILD ROUTING REPORT
    # ============================================

    def build_routing_report(

        self,

        routing_plan
    ):

        active_routes = []

        for route in routing_plan:

            if routing_plan[
                route
            ]:

                active_routes.append(
                    route
                )

        return {

            "active_routes":
            active_routes,

            "route_count":
            len(active_routes),

            "routing_plan":
            routing_plan
        }