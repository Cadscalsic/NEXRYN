# ============================================
# NEXRYN RECURSIVE COGNITION ENGINE
# ============================================


# ============================================
# RECURSIVE COGNITION ENGINE
# ============================================

class RecursiveCognitionEngine:

    def __init__(self):

        self.recursive_history = []

    # ============================================
    # ANALYZE REASONING
    # ============================================

    def analyze_reasoning(

        self,

        hypotheses,

        reasoning_trace,

        hierarchy
    ):

        recursive_report = {

            "hypothesis_count":
            len(hypotheses),

            "reasoning_depth":
            len(reasoning_trace),

            "hierarchy_levels":
            {},

            "mutation_detected":
            False,

            "exploration_detected":
            False,

            "dominant_reasoning":
            None,

            "cognitive_complexity":
            "low"
        }

        # ========================================
        # HIERARCHY ANALYSIS
        # ========================================

        for level, items in hierarchy.items():

            recursive_report[
                "hierarchy_levels"
            ][level] = len(items)

        # ========================================
        # DETECT MUTATION
        # ========================================

        for hypothesis in hypotheses:

            if hypothesis.get(
                "mutation_applied",
                False
            ):

                recursive_report[
                    "mutation_detected"
                ] = True

            if hypothesis.get(
                "exploration_applied",
                False
            ):

                recursive_report[
                    "exploration_detected"
                ] = True

        # ========================================
        # DOMINANT REASONING
        # ========================================

        if hypotheses:

            dominant = max(

                hypotheses,

                key=lambda h: h.get(
                    "confidence",
                    0.0
                )
            )

            recursive_report[
                "dominant_reasoning"
            ] = dominant.get(
                "type"
            )

        # ========================================
        # COGNITIVE COMPLEXITY
        # ========================================

        total_hierarchy_items = sum(

            recursive_report[
                "hierarchy_levels"
            ].values()
        )

        if total_hierarchy_items >= 6:

            recursive_report[
                "cognitive_complexity"
            ] = "high"

        elif total_hierarchy_items >= 3:

            recursive_report[
                "cognitive_complexity"
            ] = "medium"

        # ========================================
        # STORE HISTORY
        # ========================================

        self.recursive_history.append(
            recursive_report
        )

        return recursive_report

    # ============================================
    # GET HISTORY
    # ============================================

    def get_history(self):

        return self.recursive_history

    # ============================================
    # PRINT RECURSIVE REPORT
    # ============================================

    def print_recursive_report(

        self,

        recursive_report
    ):

        print("\n==================================================")
        print("NEXRYN :: RECURSIVE COGNITION")
        print("==================================================\n")

        print(
            recursive_report
        )