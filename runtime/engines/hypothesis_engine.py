# ============================================
# NEXRYN HYPOTHESIS ENGINE
# ============================================


# ============================================
# HYPOTHESIS ENGINE
# ============================================

class HypothesisEngine:

    def __init__(self):

        # ========================================
        # MINIMUM CONFIDENCE
        # ========================================

        self.minimum_confidence = 0.50

    # ============================================
    # RANK HYPOTHESES
    # ============================================

    def rank_hypotheses(

        self,

        hypotheses
    ):

        ranked = sorted(

            hypotheses,

            key=lambda hypothesis: hypothesis.get(
                "confidence",
                0
            ),

            reverse=True
        )

        return ranked

    # ============================================
    # FILTER HYPOTHESES
    # ============================================

    def filter_hypotheses(

        self,

        hypotheses
    ):

        filtered = []

        for hypothesis in hypotheses:

            confidence = hypothesis.get(
                "confidence",
                0
            )

            if confidence >= (
                self.minimum_confidence
            ):

                filtered.append(
                    hypothesis
                )

        return filtered

    # ============================================
    # SELECT WINNER
    # ============================================

    def select_winner(

        self,

        hypotheses
    ):

        if not hypotheses:

            return None

        ranked = self.rank_hypotheses(
            hypotheses
        )

        return ranked[0]

    # ============================================
    # COMPETE HYPOTHESES
    # ============================================

    def compete(

        self,

        hypotheses
    ):

        # ========================================
        # RANK HYPOTHESES
        # ========================================

        ranked = self.rank_hypotheses(
            hypotheses
        )

        # ========================================
        # FILTER HYPOTHESES
        # ========================================

        filtered = self.filter_hypotheses(
            ranked
        )

        # ========================================
        # SELECT WINNER
        # ========================================

        winner = self.select_winner(
            filtered
        )

        # ========================================
        # BUILD RESULT
        # ========================================

        return {

            "ranked":
            ranked,

            "selected":
            filtered,

            "winner":
            winner,

            "competition_count":
            len(hypotheses),

            "selected_count":
            len(filtered)
        }

    # ============================================
    # UPDATE MINIMUM CONFIDENCE
    # ============================================

    def set_minimum_confidence(

        self,

        value
    ):

        self.minimum_confidence = value

    # ============================================
    # GET CONFIG
    # ============================================

    def get_config(self):

        return {

            "minimum_confidence":
            self.minimum_confidence
        }

    # ============================================
    # PRINT REPORT
    # ============================================

    def print_report(

        self,

        result
    ):

        print("\n==================================================")
        print("NEXRYN :: HYPOTHESIS COMPETITION")
        print("==================================================\n")

        print({

            "competition_count":
            result.get(
                "competition_count"
            ),

            "selected_count":
            result.get(
                "selected_count"
            ),

            "winner":
            result.get(
                "winner"
            )
        })

        print()