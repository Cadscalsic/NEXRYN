# ============================================
# NEXRYN COGNITIVE PRESSURE ENGINE
# ============================================

from datetime import datetime

import copy


# ============================================
# COGNITIVE PRESSURE ENGINE
# ============================================

class CognitivePressureEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.pressure_history = []

        self.pressure_events = []

        self.engine_state = {

            "pressure_monitoring":
            True,

            "adaptive_regulation":
            True,

            "overload_detection":
            True,

            "cognitive_balancing":
            True,

            "reasoning_stabilization":
            True
        }

    # ========================================
    # COMPUTE PRESSURE SCORE
    # ========================================

    def compute_pressure_score(

        self,

        runtime_context
    ):

        context_size = len(
            runtime_context
        )

        pressure_score = round(

            context_size / 100,

            3
        )

        return pressure_score

    # ========================================
    # DETECT PRESSURE STATE
    # ========================================

    def detect_pressure_state(

        self,

        pressure_score
    ):

        if pressure_score < 0.5:

            return "stable"

        elif pressure_score < 1.0:

            return "elevated"

        elif pressure_score < 1.5:

            return "high"

        return "critical"

    # ========================================
    # BUILD REGULATION STRATEGY
    # ========================================

    def build_regulation_strategy(

        self,

        pressure_state
    ):

        if pressure_state == "stable":

            return {

                "strategy":
                "maintain_reasoning_flow",

                "actions": [

                    "preserve_reasoning_routes",

                    "maintain_recursive_depth"
                ]
            }

        elif pressure_state == "elevated":

            return {

                "strategy":
                "moderate_balancing",

                "actions": [

                    "reduce_low_priority_routes",

                    "stabilize_context_growth"
                ]
            }

        elif pressure_state == "high":

            return {

                "strategy":
                "adaptive_suppression",

                "actions": [

                    "compress_context_memory",

                    "freeze_noncritical_routes",

                    "reduce_recursive_depth"
                ]
            }

        return {

            "strategy":
            "critical_mitigation",

            "actions": [

                "activate_emergency_balancing",

                "compress_semantic_memory",

                "suspend_background_reasoning"
            ]
        }

    # ========================================
    # ANALYZE PRESSURE
    # ========================================

    def analyze_pressure(

        self,

        runtime_context
    ):

        # ====================================
        # COMPUTE SCORE
        # ====================================

        pressure_score = (

            self.compute_pressure_score(

                runtime_context
            )
        )

        # ====================================
        # DETECT STATE
        # ====================================

        pressure_state = (

            self.detect_pressure_state(

                pressure_score
            )
        )

        # ====================================
        # BUILD STRATEGY
        # ====================================

        regulation_strategy = (

            self.build_regulation_strategy(

                pressure_state
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "context_size":

            len(runtime_context),

            "pressure_score":
            pressure_score,

            "pressure_state":
            pressure_state,

            "regulation_strategy":
            regulation_strategy,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.pressure_history.append(
            copy.deepcopy(report)
        )

        if pressure_state in [

            "high",

            "critical"
        ]:

            self.pressure_events.append(
                report
            )

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.pressure_history:

            latest_report = (

                self.pressure_history[-1]
            )

        return {

            "pressure_cycles":

            len(
                self.pressure_history
            ),

            "pressure_events":

            len(
                self.pressure_events
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

cognitive_pressure_engine = (
    CognitivePressureEngine()
)