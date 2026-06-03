# ============================================
# NEXRYN PATTERN ENGINE
# ============================================

from core.interfaces import (
    CognitiveEngine
)

from core.grid import ARCGrid

from runtime.evaluation import (
    UnifiedEvaluationEngine
)


class PatternEngine(CognitiveEngine):

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        super().__init__()

        self.patterns = []

        self.evaluation_engine = (
            UnifiedEvaluationEngine()
        )

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def initialize(self):

        self.engine_status = "initialized"

    # ========================================
    # EXECUTE ENGINE
    # ========================================

    def execute(

        self,

        cognitive_state,

        blackboard
    ):

        self.engine_status = "active"

        input_grid = ARCGrid(
            cognitive_state.input_grid
        )

        output_grid = ARCGrid(
            cognitive_state.output_grid
        )

        # ====================================
        # ANALYZE
        # ====================================

        self.patterns = self.analyze(

            input_grid,

            output_grid
        )

        # ====================================
        # STORE IN BLACKBOARD
        # ====================================

        blackboard.patterns.extend(
            self.patterns
        )

        # ====================================
        # STORE IN COGNITIVE STATE
        # ====================================

        cognitive_state.patterns.extend(
            self.patterns
        )

        # ====================================
        # EVALUATE
        # ====================================

        evaluation = (

            self.evaluation_engine.evaluate(

                cognitive_state.input_grid,

                cognitive_state.output_grid
            )
        )

        # ====================================
        # UPDATE CONFIDENCE
        # ====================================

        self.update_confidence(

            evaluation["final_score"]
        )

        # ====================================
        # SUCCESS
        # ====================================

        self.mark_success()

        # ====================================
        # RETURN
        # ====================================

        return {

            "patterns":
            self.patterns,

            "evaluation":
            evaluation
        }

    # ========================================
    # ANALYZE PATTERNS
    # ========================================

    def analyze(

        self,

        input_grid,

        output_grid
    ):

        patterns = [

            {
                "pattern":
                "grid_size_changed",

                "value":

                (
                    input_grid.shape()
                    !=
                    output_grid.shape()
                )
            },

            {
                "pattern":
                "colors_added",

                "value":

                list(

                    set(
                        output_grid.unique_colors()
                    )

                    -

                    set(
                        input_grid.unique_colors()
                    )
                )
            },

            {
                "pattern":
                "colors_removed",

                "value":

                list(

                    set(
                        input_grid.unique_colors()
                    )

                    -

                    set(
                        output_grid.unique_colors()
                    )
                )
            },

            {
                "pattern":
                "colors_preserved",

                "value":

                list(

                    set(
                        input_grid.unique_colors()
                    ).intersection(

                        set(
                            output_grid.unique_colors()
                        )
                    )
                )
            },

            {
                "pattern":
                "input_object_count",

                "value":

                len(
                    input_grid.find_objects()
                )
            },

            {
                "pattern":
                "output_object_count",

                "value":

                len(
                    output_grid.find_objects()
                )
            },

            {
                "pattern":
                "object_count_changed",

                "value":

                (

                    len(
                        input_grid.find_objects()
                    )

                    !=

                    len(
                        output_grid.find_objects()
                    )
                )
            },

            {
                "pattern":
                "symmetry_changes",

                "value":

                {

                    "input_horizontal":

                    input_grid.is_horizontally_symmetric(),

                    "output_horizontal":

                    output_grid.is_horizontally_symmetric(),

                    "input_vertical":

                    input_grid.is_vertically_symmetric(),

                    "output_vertical":

                    output_grid.is_vertically_symmetric()
                }
            },

            {
                "pattern":
                "density_change",

                "value":

                {

                    "input_density":

                    input_grid.filled_ratio(),

                    "output_density":

                    output_grid.filled_ratio(),

                    "difference":

                    output_grid.filled_ratio()

                    -

                    input_grid.filled_ratio()
                }
            }
        ]

        return patterns

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "engine":
            self.engine_name,

            "status":
            self.engine_status,

            "patterns_detected":

            len(
                self.patterns
            ),

            "confidence":
            self.last_confidence
        }