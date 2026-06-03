# ============================================
# NEXRYN TASK TAXONOMY SYSTEM
# ============================================

from datetime import datetime


# ============================================
# TASK TAXONOMY
# ============================================

class TaskTaxonomy:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.taxonomy_state = {

            "symbolic_reasoning":
            True,

            "spatial_reasoning":
            True,

            "structural_reasoning":
            True,

            "topology_reasoning":
            True,

            "adaptive_classification":
            True
        }

    # ========================================
    # CLASSIFY TASK
    # ========================================

    def classify(

        self,

        runtime_context
    ):

        patterns = runtime_context.get(
            "patterns",
            []
        )

        rules = runtime_context.get(
            "rules",
            []
        )

        input_summary = runtime_context.get(
            "input_summary",
            {}
        )

        output_summary = runtime_context.get(
            "output_summary",
            {}
        )

        # ========================================
        # RUNTIME CONTEXT NORMALIZATION
        # ========================================

        runtime_context = (

            self.normalize_runtime_context(

                runtime_context
            )
        )

        # ====================================
        # TASK TYPE
        # ====================================

        task_type = self.detect_task_type(

            patterns,

            rules
        )

        # ====================================
        # REASONING FAMILY
        # ====================================

        reasoning_family = (
            self.detect_reasoning_family(
                task_type
            )
        )

        # ====================================
        # TASK DIFFICULTY
        # ====================================

        difficulty = self.estimate_difficulty(

            input_summary,

            output_summary,

            patterns
        )

        # ====================================
        # CLASSIFICATION
        # ====================================

        classification = {

            "task_type":
            task_type,

            "reasoning_family":
            reasoning_family,

            "difficulty":
            difficulty,

            "taxonomy_timestamp":
            str(datetime.utcnow())
        }

        return classification

    # ========================================
    # DETECT TASK TYPE
    # ========================================

    def detect_task_type(

        self,

        patterns,

        rules
    ):

        pattern_names = [

            pattern.get(
                "pattern",
                ""
            )

            for pattern in patterns
        ]

        # ====================================
        # COLOR TRANSFORMATION
        # ====================================

        if "colors_added" in pattern_names:

            return (
                "symbolic_color_transformation"
            )

        # ====================================
        # OBJECT REASONING
        # ====================================

        if "object_count_changed" in (
            pattern_names
        ):

            return (
                "object_structural_reasoning"
            )

        # ====================================
        # SYMMETRY
        # ====================================

        if "symmetry_changes" in (
            pattern_names
        ):

            return (
                "symmetry_preservation"
            )

        # ====================================
        # DEFAULT
        # ====================================

        return "general_reasoning"

    # ========================================
    # DETECT REASONING FAMILY
    # ========================================

    def detect_reasoning_family(

        self,

        task_type
    ):

        if "symbolic" in task_type:

            return "symbolic"

        if "structural" in task_type:

            return "structural"

        if "symmetry" in task_type:

            return "spatial"

        return "general"

    # ========================================
    # ESTIMATE DIFFICULTY
    # ========================================

    def estimate_difficulty(

        self,

        input_summary,

        output_summary,

        patterns
    ):

        color_count = input_summary.get(
            "color_count",
            0
        )

        object_count = input_summary.get(
            "object_count",
            0
        )

        total_patterns = len(patterns)

        complexity_score = (

            color_count
            +
            object_count
            +
            total_patterns
        )

        # ====================================
        # LOW
        # ====================================

        if complexity_score <= 6:

            return "low"

        # ====================================
        # MEDIUM
        # ====================================

        if complexity_score <= 12:

            return "medium"

        # ====================================
        # HIGH
        # ====================================

        return "high"

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "taxonomy_state":
            self.taxonomy_state
        }