# ============================================
# NEXRYN CAUSAL REASONING ENGINE
# ============================================

from datetime import datetime

import copy


# ============================================
# CAUSAL REASONING ENGINE
# ============================================

class CausalReasoningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.causal_history = []

        self.causal_chains = []

        self.engine_state = {

            "causal_inference":
            True,

            "operation_linking":
            True,

            "multi_step_reasoning":
            True,

            "causal_dependency_tracking":
            True,

            "effect_prediction":
            True
        }

    # ========================================
    # BUILD CAUSAL CHAIN
    # ========================================

    def build_causal_chain(

        self,

        hypotheses
    ):

        causal_chain = []

        for index, hypothesis in enumerate(
            hypotheses
        ):

            causal_node = {

                "step":
                index,

                "cause":
                hypothesis.get(
                    "type",
                    "unknown"
                ),

                "effect":
                hypothesis.get(
                    "description",
                    "unknown"
                ),

                "confidence":
                hypothesis.get(
                    "confidence",
                    0.0
                ),

                "category":
                hypothesis.get(
                    "category",
                    "unknown"
                )
            }

            causal_chain.append(
                causal_node
            )

        return causal_chain

    # ========================================
    # DETECT CAUSAL DEPENDENCIES
    # ========================================

    def detect_dependencies(

        self,

        causal_chain
    ):

        dependencies = []

        for index in range(

            len(causal_chain) - 1
        ):

            current_node = (
                causal_chain[index]
            )

            next_node = (
                causal_chain[index + 1]
            )

            dependency = {

                "source":
                current_node.get(
                    "cause"
                ),

                "target":
                next_node.get(
                    "cause"
                ),

                "relation":
                "causal_dependency"
            }

            dependencies.append(
                dependency
            )

        return dependencies

    # ========================================
    # ESTIMATE CAUSAL STRENGTH
    # ========================================

    def estimate_causal_strength(

        self,

        causal_chain
    ):

        if not causal_chain:

            return 0.0

        confidence_values = []

        for node in causal_chain:

            confidence_values.append(

                node.get(
                    "confidence",
                    0.0
                )
            )

        average_strength = (

            sum(confidence_values)
            / len(confidence_values)
        )

        return round(
            average_strength,
            3
        )

    # ========================================
    # BUILD CAUSAL REPORT
    # ========================================

    def build_causal_report(

        self,

        hypotheses
    ):

        # ====================================
        # BUILD CHAIN
        # ====================================

        causal_chain = (

            self.build_causal_chain(
                hypotheses
            )
        )

        # ====================================
        # BUILD DEPENDENCIES
        # ====================================

        dependencies = (

            self.detect_dependencies(
                causal_chain
            )
        )

        # ====================================
        # ESTIMATE STRENGTH
        # ====================================

        causal_strength = (

            self.estimate_causal_strength(
                causal_chain
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "causal_steps":
            len(causal_chain),

            "causal_chain":
            causal_chain,

            "dependencies":
            dependencies,

            "dependency_count":
            len(dependencies),

            "causal_strength":
            causal_strength,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.causal_history.append(
            copy.deepcopy(report)
        )

        self.causal_chains.append(
            causal_chain
        )

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.causal_history:

            latest_report = (

                self.causal_history[-1]
            )

        return {

            "causal_cycles":

            len(
                self.causal_history
            ),

            "stored_chains":

            len(
                self.causal_chains
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

causal_reasoning_engine = (
    CausalReasoningEngine()
)