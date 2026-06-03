# ============================================
# NEXRYN SPATIAL ABSTRACTION ENGINE
# ============================================

from datetime import datetime


# ============================================
# SPATIAL ABSTRACTION ENGINE
# ============================================

class SpatialAbstractionEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.abstraction_history = []

        self.abstract_patterns = []

        self.engine_state = {

            "topology_abstraction":
            True,

            "coordinate_semantics":
            True,

            "movement_abstraction":
            True,

            "shape_abstraction":
            True,

            "spatial_generalization":
            True
        }

    # ========================================
    # ABSTRACT TRANSLATION
    # ========================================

    def abstract_translation(

        self,

        spatial_hypothesis
    ):

        metadata = spatial_hypothesis.get(
            "metadata",
            {}
        )

        delta_row = metadata.get(
            "delta_row",
            0
        )

        delta_col = metadata.get(
            "delta_col",
            0
        )

        abstraction = {

            "abstract_type":
            "spatial_translation",

            "movement_vector": {

                "row_shift":
                delta_row,

                "col_shift":
                delta_col
            },

            "semantic_meaning":
            "object_relocation",

            "topology_state":
            "preserved"
        }

        return abstraction

    # ========================================
    # ABSTRACT REFLECTION
    # ========================================

    def abstract_reflection(

        self,

        spatial_hypothesis
    ):

        return {

            "abstract_type":
            "spatial_reflection",

            "semantic_meaning":
            "mirror_transformation",

            "reflection_mode":

            spatial_hypothesis.get(
                "type",
                "unknown"
            )
        }

    # ========================================
    # ABSTRACT ROTATION
    # ========================================

    def abstract_rotation(

        self,

        spatial_hypothesis
    ):

        metadata = spatial_hypothesis.get(
            "metadata",
            {}
        )

        return {

            "abstract_type":
            "spatial_rotation",

            "rotation_degree":

            metadata.get(
                "rotation",
                0
            ),

            "semantic_meaning":
            "topological_rotation"
        }

    # ========================================
    # BUILD SPATIAL ABSTRACTIONS
    # ========================================

    def build_spatial_abstractions(

        self,

        spatial_hypotheses
    ):

        abstractions = []

        for hypothesis in spatial_hypotheses:

            hypothesis_type = hypothesis.get(
                "type"
            )

            # ====================================
            # TRANSLATION
            # ====================================

            if hypothesis_type == (

                "object_translation"
            ):

                abstraction = (

                    self.abstract_translation(
                        hypothesis
                    )
                )

                abstractions.append(
                    abstraction
                )

            # ====================================
            # REFLECTION
            # ====================================

            elif "reflection" in str(
                hypothesis_type
            ):

                abstraction = (

                    self.abstract_reflection(
                        hypothesis
                    )
                )

                abstractions.append(
                    abstraction
                )

            # ====================================
            # ROTATION
            # ====================================

            elif hypothesis_type == (
                "rotation"
            ):

                abstraction = (

                    self.abstract_rotation(
                        hypothesis
                    )
                )

                abstractions.append(
                    abstraction
                )

        # ========================================
        # BUILD REPORT
        # ========================================

        abstraction_report = {

            "abstraction_count":
            len(abstractions),

            "abstractions":
            abstractions,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.abstraction_history.append(
            abstraction_report
        )

        return abstraction_report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.abstraction_history:

            latest_report = (

                self.abstraction_history[-1]
            )

        return {

            "history_size":

            len(
                self.abstraction_history
            ),

            "abstract_pattern_count":

            len(
                self.abstract_patterns
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

spatial_abstraction_engine = (
    SpatialAbstractionEngine()
)