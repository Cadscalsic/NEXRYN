# ============================================
# NEXRYN COGNITIVE LOAD BALANCER
# ============================================

from datetime import datetime


# ============================================
# COGNITIVE LOAD BALANCER
# ============================================

class CognitiveLoadBalancer:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # BALANCING STATE
        # ====================================

        self.balancing_state = {

            "cognitive_balancing":
            True,

            "pressure_regulation":
            True,

            "recursive_stabilization":
            True,

            "energy_distribution":
            True,

            "adaptive_load_control":
            True,

            "balancing_cycles":
            0
        }

        # ====================================
        # LOAD HISTORY
        # ====================================

        self.load_history = []

    # ========================================
    # ANALYZE LOAD
    # ========================================

    def analyze_load(

        self,

        runtime_context
    ):

        inference_report = (

            runtime_context.get(
                "inference_report"
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

        context_size = len(
            runtime_context
        )

        return {

            "reasoning_depth":
            reasoning_depth,

            "cognitive_pressure":
            cognitive_pressure,

            "context_size":
            context_size,

            "load_state":
            self.classify_load_state(

                reasoning_depth,

                cognitive_pressure,

                context_size
            )
        }

    # ========================================
    # CLASSIFY LOAD STATE
    # ========================================

    def classify_load_state(

        self,

        reasoning_depth,

        cognitive_pressure,

        context_size
    ):

        if (

            reasoning_depth >= 20
            or cognitive_pressure >= 0.85
            or context_size >= 200
        ):

            return "critical"

        if (

            reasoning_depth >= 15
            or cognitive_pressure >= 0.7
            or context_size >= 120
        ):

            return "high"

        if (

            reasoning_depth >= 8
            or cognitive_pressure >= 0.5
        ):

            return "moderate"

        return "stable"

    # ========================================
    # BUILD BALANCING ACTIONS
    # ========================================

    def build_balancing_actions(

        self,

        load_report
    ):

        actions = []

        load_state = load_report.get(
            "load_state"
        )

        # ====================================
        # CRITICAL STATE
        # ====================================

        if load_state == "critical":

            actions.extend([

                {

                    "action":
                    "activate_hierarchical_compression",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "reduce_recursive_depth",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "limit_exploration",

                    "priority":
                    "high"
                }
            ])

        # ====================================
        # HIGH STATE
        # ====================================

        elif load_state == "high":

            actions.extend([

                {

                    "action":
                    "compress_context_memory",

                    "priority":
                    "high"
                },

                {

                    "action":
                    "stabilize_reasoning_routes",

                    "priority":
                    "medium"
                }
            ])

        # ====================================
        # MODERATE STATE
        # ====================================

        elif load_state == "moderate":

            actions.append({

                "action":
                "maintain_balanced_cognition",

                "priority":
                "medium"
            })

        # ====================================
        # STABLE STATE
        # ====================================

        else:

            actions.append({

                "action":
                "allow_semantic_expansion",

                "priority":
                "low"
            })

        return actions

    # ========================================
    # RUN BALANCING CYCLE
    # ========================================

    def run_balancing_cycle(

        self,

        runtime_context
    ):

        load_report = (

            self.analyze_load(
                runtime_context
            )
        )

        balancing_actions = (

            self.build_balancing_actions(
                load_report
            )
        )

        balancing_report = {

            "load_report":
            load_report,

            "balancing_actions":
            balancing_actions,

            "timestamp":
            str(datetime.utcnow())
        }

        runtime_context[
            "cognitive_load_report"
        ] = balancing_report

        self.load_history.append(
            balancing_report
        )

        self.balancing_state[
            "balancing_cycles"
        ] += 1

        return runtime_context

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "balancing_cycles":
            self.balancing_state[
                "balancing_cycles"
            ],

            "load_history":
            len(
                self.load_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL LOAD BALANCER
# ============================================

cognitive_load_balancer = (
    CognitiveLoadBalancer()
)