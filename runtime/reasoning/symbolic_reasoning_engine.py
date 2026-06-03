# ============================================
# NEXRYN SYMBOLIC REASONING ENGINE
# ============================================

from datetime import datetime

import copy


# ============================================
# SYMBOLIC REASONING ENGINE
# ============================================

class SymbolicReasoningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.symbolic_history = []

        self.symbolic_rules = []

        self.engine_state = {

            "symbolic_abstraction":
            True,

            "rule_extraction":
            True,

            "symbolic_mapping":
            True,

            "rule_generalization":
            True,

            "semantic_symbolism":
            True
        }

    # ========================================
    # EXTRACT SYMBOLIC RULE
    # ========================================

    def extract_symbolic_rule(

        self,

        hypothesis
    ):

        symbolic_rule = {

            "symbolic_type":

            hypothesis.get(
                "type",
                "unknown"
            ),

            "category":

            hypothesis.get(
                "category",
                "unknown"
            ),

            "rule":

            hypothesis.get(
                "description",
                "unknown"
            ),

            "confidence":

            hypothesis.get(
                "confidence",
                0.0
            ),

            "metadata":

            hypothesis.get(
                "metadata",
                {}
            )
        }

        return symbolic_rule

    # ========================================
    # BUILD SYMBOLIC RULES
    # ========================================

    def build_symbolic_rules(

        self,

        hypotheses
    ):

        symbolic_rules = []

        for hypothesis in hypotheses:

            symbolic_rule = (

                self.extract_symbolic_rule(
                    hypothesis
                )
            )

            symbolic_rules.append(
                symbolic_rule
            )

        return symbolic_rules

    # ========================================
    # GENERALIZE SYMBOLIC RULES
    # ========================================

    def generalize_rules(

        self,

        symbolic_rules
    ):

        generalized_rules = []

        for rule in symbolic_rules:

            generalized_rule = {

                "abstract_rule":

                rule.get(
                    "symbolic_type"
                ),

                "semantic_meaning":

                rule.get(
                    "rule"
                ),

                "confidence":

                rule.get(
                    "confidence",
                    0.0
                ),

                "generalization_state":
                "semantic_abstraction"
            }

            generalized_rules.append(
                generalized_rule
            )

        return generalized_rules

    # ========================================
    # BUILD SYMBOLIC REPORT
    # ========================================

    def build_symbolic_report(

        self,

        hypotheses
    ):

        # ====================================
        # BUILD RULES
        # ====================================

        symbolic_rules = (

            self.build_symbolic_rules(
                hypotheses
            )
        )

        # ====================================
        # GENERALIZE RULES
        # ====================================

        generalized_rules = (

            self.generalize_rules(
                symbolic_rules
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "rule_count":
            len(symbolic_rules),

            "symbolic_rules":
            symbolic_rules,

            "generalized_rules":
            generalized_rules,

            "generalization_count":
            len(generalized_rules),

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.symbolic_history.append(
            copy.deepcopy(report)
        )

        self.symbolic_rules.extend(
            symbolic_rules
        )

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.symbolic_history:

            latest_report = (

                self.symbolic_history[-1]
            )

        return {

            "symbolic_cycles":

            len(
                self.symbolic_history
            ),

            "stored_rules":

            len(
                self.symbolic_rules
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

symbolic_reasoning_engine = (
    SymbolicReasoningEngine()
)