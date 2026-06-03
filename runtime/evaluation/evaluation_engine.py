# ============================================
# NEXRYN UNIFIED EVALUATION ENGINE
# ============================================

import numpy as np

from runtime.evaluation.partial_success_engine import PartialSuccessEngine


# ============================================
# UNIFIED EVALUATION ENGINE
# ============================================

class UnifiedEvaluationEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self, partial_success_engine=None):

        # ====================================
        # EVALUATION HISTORY
        # ====================================

        self.history = []

        # ====================================
        # LAST CONFIDENCE
        # ====================================

        self.last_confidence = "unknown"
        self.partial_success_engine = (
            partial_success_engine
            or PartialSuccessEngine()
        )

    # ============================================
    # COMPUTE CELL ACCURACY
    # ============================================

    def compute_accuracy(

        self,

        predicted,

        target
    ):

        total_cells = predicted.size

        correct_cells = np.sum(

            predicted == target
        )

        accuracy = (

            correct_cells

            /

            total_cells
        )

        return float(

            round(
                accuracy,
                4
            )
        )

    # ============================================
    # COMPUTE DIFFERENCE COUNT
    # ============================================

    def compute_difference_count(

        self,

        predicted,

        target
    ):

        differences = np.sum(

            predicted != target
        )

        return int(
            differences
        )

    # ============================================
    # COLOR SIMILARITY
    # ============================================

    def compute_color_similarity(

        self,

        predicted,

        target
    ):

        predicted_colors = set(
            np.unique(predicted)
        )

        target_colors = set(
            np.unique(target)
        )

        common_colors = len(

            predicted_colors.intersection(
                target_colors
            )
        )

        total_colors = len(

            predicted_colors.union(
                target_colors
            )
        )

        if total_colors == 0:

            return 0.0

        return float(

            round(

                common_colors

                /

                total_colors,

                4
            )
        )

    # ============================================
    # STRUCTURAL SCORE
    # ============================================

    def compute_structural_score(

        self,

        predicted,

        target
    ):

        score = 0.0

        # ====================================
        # SHAPE MATCH
        # ====================================

        if predicted.shape == target.shape:

            score += 0.5

        # ====================================
        # DENSITY MATCH
        # ====================================

        predicted_density = np.mean(
            predicted != 0
        )

        target_density = np.mean(
            target != 0
        )

        density_difference = abs(

            predicted_density

            -

            target_density
        )

        score += max(

            0,

            0.5 - density_difference
        )

        return float(

            round(
                min(score, 1.0),
                4
            )
        )

    # ============================================
    # CONFIDENCE
    # ============================================

    def confidence(

        self,

        accuracy
    ):

        if accuracy >= 0.95:

            return "very_high"

        elif accuracy >= 0.80:

            return "high"

        elif accuracy >= 0.60:

            return "moderate"

        elif accuracy >= 0.40:

            return "low"

        return "very_low"

    # ============================================
    # EVALUATE
    # ============================================

    def evaluate(

        self,

        predicted_output,

        target_output
    ):

        # ====================================
        # ACCURACY
        # ====================================

        accuracy = self.compute_accuracy(

            predicted_output,

            target_output
        )

        # ====================================
        # DIFFERENCES
        # ====================================

        difference_count = (

            self.compute_difference_count(

                predicted_output,

                target_output
            )
        )

        # ====================================
        # COLOR SIMILARITY
        # ====================================

        color_similarity = (

            self.compute_color_similarity(

                predicted_output,

                target_output
            )
        )

        # ====================================
        # STRUCTURAL SCORE
        # ====================================

        structural_score = (

            self.compute_structural_score(

                predicted_output,

                target_output
            )
        )

        # ====================================
        # FINAL SCORE
        # ====================================

        final_score = (

            accuracy * 0.6

            +

            color_similarity * 0.2

            +

            structural_score * 0.2
        )

        final_score = float(

            round(
                final_score,
                4
            )
        )

        # ====================================
        # CONFIDENCE
        # ====================================

        confidence = self.confidence(
            final_score
        )

        self.last_confidence = confidence

        # ====================================
        # SUCCESS
        # ====================================

        success = bool(
            accuracy == 1.0
        )
        partial_success = self.partial_success_engine.evaluate(
            accuracy,
            exact_success=success,
        )

        # ====================================
        # BUILD RESULT
        # ====================================

        result = {

            "accuracy":
            accuracy,

            "difference_count":
            difference_count,

            "color_similarity":
            color_similarity,

            "structural_score":
            structural_score,

            "final_score":
            final_score,

            "confidence":
            confidence,

            "success":
            success,

            **partial_success
        }

        # ====================================
        # STORE HISTORY
        # ====================================

        self.history.append(
            result
        )

        return result

    # ============================================
    # GET HISTORY
    # ============================================

    def get_history(self):

        return self.history

    # ============================================
    # SUMMARY
    # ============================================

    def summary(self):

        return {

            "evaluations":
            len(self.history),

            "last_confidence":
            self.last_confidence
        }

    # ============================================
    # PRINT EVALUATION
    # ============================================

    def print_evaluation(

        self,

        evaluation_result
    ):

        print("\n==================================================")
        print("NEXRYN :: UNIFIED EVALUATION")
        print("==================================================\n")

        print(
            evaluation_result
        )

        print()


# ============================================
# BACKWARD COMPATIBILITY
# ============================================

EvaluationEngine = UnifiedEvaluationEngine
