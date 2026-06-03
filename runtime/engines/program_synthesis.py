# ============================================
# NEXRYN PROGRAM SYNTHESIS
# ============================================


# ============================================
# PROGRAM SYNTHESIS ENGINE
# ============================================

class ProgramSynthesisEngine:

    def __init__(self):

        self.programs = []

    # ============================================
    # SYNTHESIZE PROGRAM
    # ============================================

    def synthesize(

        self,

        hypotheses,

        winner_hypothesis=None
    ):

        program_steps = []

        selected_hypotheses = []

        if isinstance(
            winner_hypothesis,
            dict
        ):

            selected_hypotheses.append(
                winner_hypothesis
            )

        for hypothesis in hypotheses:

            if not isinstance(
                hypothesis,
                dict
            ):

                continue

            if (

                winner_hypothesis

                and

                hypothesis.get(
                    "primitive"
                )
                ==
                winner_hypothesis.get(
                    "primitive"
                )
            ):

                continue

            if self.causal_consistency(
                selected_hypotheses,
                hypothesis
            ):

                selected_hypotheses.append(
                    hypothesis
                )

        if not selected_hypotheses:

            selected_hypotheses = hypotheses

        for hypothesis in selected_hypotheses:

            if not isinstance(
                hypothesis,
                dict
            ):

                continue

            primitive_name = hypothesis.get(
                "primitive"
            )

            if primitive_name is not None:

                program_steps.append(
                    self.build_step(
                        hypothesis
                    )
                )

                continue

            hypothesis_type = hypothesis.get(
                "type"
            )

            if hypothesis_type is None:

                continue

            metadata = hypothesis.get(
                "metadata",
                {}
            )

            # ====================================
            # COLOR TRANSFORMATION
            # ====================================

            if (

    "color_transformation"

    in

    hypothesis_type
):

                program_steps.append({

                    "operation":
                    "replace_color",

                    "parameters": {

                        "source":
                        metadata.get(
                            "removed_colors",
                            []
                        ),

                        "target":
                        metadata.get(
                            "added_colors",
                            []
                        )
                    }
                })

            # ====================================
            # SYMMETRY
            # ====================================

            elif hypothesis_type == (
                "symmetry_preservation"
            ):

                program_steps.append({

                    "operation":
                    "preserve_symmetry",

                    "parameters": {}
                })

            # ====================================
            # DENSITY
            # ====================================

            elif hypothesis_type == (
                "density_conservation"
            ):

                program_steps.append({

                    "operation":
                    "preserve_density",

                    "parameters": {}
                })

        synthesized_program = {

            "step_count":
            len(program_steps),

            "steps":
            program_steps
        }

        self.programs.append(
            synthesized_program
        )

        return synthesized_program

    # ============================================
    # BUILD STEP
    # ============================================

    def build_step(
        self,
        hypothesis
    ):

        primitive_name = hypothesis.get(
            "primitive"
        )

        parameters = hypothesis.get(
            "parameters",
            {}
        )

        if parameters:

            return {

                "operation":
                primitive_name,

                "parameters":
                parameters
            }

        grounding = hypothesis.get(
            "geometric_grounding",
            {}
        )

        if primitive_name == "replace_color":

            parameters = {

                "added_colors":
                grounding.get(
                    "added_colors",
                    []
                ),

                "removed_colors":
                grounding.get(
                    "removed_colors",
                    []
                )
            }

        elif primitive_name in [

            "translate_left",
            "translate_right",
            "translate_up",
            "translate_down"
        ]:

            parameters = {

                "translation":
                grounding.get(
                    "dominant_translation",
                    (
                        0,
                        0
                    )
                )
            }

        elif primitive_name in [

            "duplicate_object",
            "remove_object",
            "expand_object",
            "shrink_object"
        ]:

            parameters = {

                "delta":
                grounding.get(
                    "delta",
                    0
                )
            }

        return {

            "operation":
            primitive_name,

            "parameters":
            parameters
        }

    # ============================================
    # CAUSAL CONSISTENCY
    # ============================================

    def causal_consistency(
        self,
        selected_hypotheses,
        candidate
    ):

        primitive = candidate.get(
            "primitive"
        )

        if primitive is None:

            return False

        if not selected_hypotheses:

            return True

        no_op_primitives = {
            "preserve_objects",
            "preserve_shape",
            "preserve_density",
            "preserve_colors",
            "preserve_topology",
            "preserve_symmetry"
        }

        if primitive in no_op_primitives:

            return False

        selected_primitives = {

            hypothesis.get(
                "primitive"
            )

            for hypothesis in selected_hypotheses

            if isinstance(
                hypothesis,
                dict
            )
        }

        if primitive in selected_primitives:

            return False

        primitive_groups = {

            "color":
            {
                "replace_color"
            },

            "movement":
            {
                "translate_left",
                "translate_right",
                "translate_up",
                "translate_down"
            },

            "growth":
            {
                "duplicate_object",
                "expand_object",
                "expand_pattern",
                "grow_topology"
            },

            "removal":
            {
                "remove_object",
                "shrink_object",
                "shrink_grid"
            }
        }

        used_groups = set()

        candidate_group = None

        for group_name, group_primitives in (
            primitive_groups.items()
        ):

            if primitive in group_primitives:

                candidate_group = group_name

            if selected_primitives.intersection(
                group_primitives
            ):

                used_groups.add(
                    group_name
                )

        if candidate_group is None:

            return False

        if candidate_group in used_groups:

            return False

        return True

    # ============================================
    # GET PROGRAMS
    # ============================================

    def get_programs(self):

        return self.programs
