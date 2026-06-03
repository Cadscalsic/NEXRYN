# ============================================
# NEXRYN OPERATOR SELECTION ENGINE
# ============================================

from datetime import datetime

from copy import deepcopy


# ============================================
# OPERATOR SELECTION ENGINE
# ============================================

class OperatorSelectionEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.selection_history = []

        self.operator_scores = {}

        self.engine_state = {

            "adaptive_selection":
            True,

            "confidence_routing":
            True,

            "operator_prioritization":
            True,

            "dynamic_scoring":
            True,

            "execution_optimization":
            True
        }

    # ========================================
    # SCORE OPERATOR
    # ========================================

    def score_operator(

        self,

        program_step
    ):

        base_score = program_step.get(
            "confidence",
            0.0
        )

        operator_name = program_step.get(
            "operator",
            "unknown"
        )

        historical_bonus = (

            self.operator_scores.get(
                operator_name,
                0.0
            )
        )

        final_score = (

            base_score
            +
            historical_bonus
        )

        return round(
            final_score,
            4
        )

    # ========================================
    # RANK OPERATORS
    # ========================================

    def rank_operators(

        self,

        program_steps
    ):

        ranked_steps = []

        for step in program_steps:

            ranked_step = {

                "program_step":
                step,

                "selection_score":

                self.score_operator(
                    step
                )
            }

            ranked_steps.append(
                ranked_step
            )

        ranked_steps = sorted(

            ranked_steps,

            key=lambda item:

            item.get(
                "selection_score",
                0.0
            ),

            reverse=True
        )

        return ranked_steps

    # ========================================
    # SELECT BEST OPERATOR
    # ========================================

    def select_best_operator(

        self,

        ranked_steps
    ):

        if not ranked_steps:

            return {}

        return ranked_steps[0]

    # ========================================
    # UPDATE OPERATOR PERFORMANCE
    # ========================================

    def update_operator_performance(

        self,

        operator_name,

        success=True
    ):

        current_score = (

            self.operator_scores.get(
                operator_name,
                0.0
            )
        )

        if success:

            current_score += 0.05

        else:

            current_score -= 0.05

        self.operator_scores[
            operator_name
        ] = round(
            current_score,
            4
        )

    # ========================================
    # BUILD SELECTION REPORT
    # ========================================

    def build_selection_report(

        self,

        program_steps
    ):

        # ====================================
        # RANK OPERATORS
        # ====================================

        ranked_steps = (

            self.rank_operators(
                program_steps
            )
        )

        # ====================================
        # SELECT BEST
        # ====================================

        selected_operator = (

            self.select_best_operator(
                ranked_steps
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "candidate_count":
            len(program_steps),

            "ranked_steps":
            ranked_steps,

            "selected_operator":
            selected_operator,

            "operator_scores":
            self.operator_scores,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.selection_history.append(
            deepcopy(report)
        )

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.selection_history:

            latest_report = (

                self.selection_history[-1]
            )

        return {

            "selection_cycles":

            len(
                self.selection_history
            ),

            "tracked_operators":

            len(
                self.operator_scores
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

operator_selection_engine = (
    OperatorSelectionEngine()
)