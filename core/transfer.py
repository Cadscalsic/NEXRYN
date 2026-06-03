import numpy as np


class TransferLearningEngine:

    def __init__(self, memory_engine=None):

        self.memory_engine = memory_engine

    # =====================================================
    # TASK SIGNATURE
    # =====================================================

    def task_signature(

        self,

        input_grid,

        output_grid

    ):

        return {

            "input_shape":
                tuple(input_grid.shape),

            "output_shape":
                tuple(output_grid.shape),

            "input_colors":
                sorted(
                    list(np.unique(input_grid))
                ),

            "output_colors":
                sorted(
                    list(np.unique(output_grid))
                ),

            "color_difference":
                int(
                    len(np.unique(output_grid))
                    -
                    len(np.unique(input_grid))
                ),

            "density":

                float(
                    np.mean(input_grid != 0)
                )
        }

    # =====================================================
    # SIMILARITY SCORE
    # =====================================================

    def similarity_score(

        self,

        sig1,

        sig2

    ):

        score = 0.0

        # ---------------------------------------------
        # SHAPE MATCH
        # ---------------------------------------------

        if sig1["input_shape"] == sig2["input_shape"]:

            score += 0.30

        if sig1["output_shape"] == sig2["output_shape"]:

            score += 0.30

        # ---------------------------------------------
        # COLOR MATCH
        # ---------------------------------------------

        common_input_colors = len(

            set(sig1["input_colors"])

            &

            set(sig2["input_colors"])
        )

        common_output_colors = len(

            set(sig1["output_colors"])

            &

            set(sig2["output_colors"])
        )

        score += common_input_colors * 0.05

        score += common_output_colors * 0.05

        # ---------------------------------------------
        # DENSITY MATCH
        # ---------------------------------------------

        density_diff = abs(

            sig1["density"]

            -

            sig2["density"]

        )

        score += max(

            0,

            0.30 - density_diff

        )

        return min(score, 1.0)

    # =====================================================
    # FIND SIMILAR TASKS
    # =====================================================

    def find_similar_tasks(

        self,

        current_signature,

        stored_tasks

    ):

        similarities = []

        for task in stored_tasks:

            stored_signature = task.get(

                "signature",

                {}
            )

            similarity = self.similarity_score(

                current_signature,

                stored_signature
            )

            similarities.append({

                "task":
                    task,

                "similarity":
                    similarity
            })

        similarities = sorted(

            similarities,

            key=lambda x: x["similarity"],

            reverse=True
        )

        return similarities

    # =====================================================
    # TRANSFER KNOWLEDGE
    # =====================================================

    def transfer(

        self,

        input_grid,

        output_grid,

        stored_tasks

    ):

        current_signature = self.task_signature(

            input_grid,

            output_grid
        )

        similar_tasks = self.find_similar_tasks(

            current_signature,

            stored_tasks
        )

        return {

            "current_signature":
                current_signature,

            "similar_tasks":
                similar_tasks[:5]
        }