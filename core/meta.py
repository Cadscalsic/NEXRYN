# ============================================
# NEXRYN META COGNITIVE ROUTER
# ============================================

import numpy as np

from datetime import datetime


# ============================================
# META REASONING ENGINE
# ============================================

class MetaReasoningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # ENGINE PERFORMANCE MEMORY
        # ====================================

        self.engine_profiles = {

            "inference": {

                "base_confidence":
                0.70,

                "specialization":
                "symbolic_reasoning"
            },

            "planner": {

                "base_confidence":
                0.75,

                "specialization":
                "structured_transformation"
            },

            "synthesis": {

                "base_confidence":
                0.72,

                "specialization":
                "pattern_generation"
            },

            "search": {

                "base_confidence":
                0.68,

                "specialization":
                "exploratory_reasoning"
            }
        }

        # ====================================
        # ROUTING HISTORY
        # ====================================

        self.routing_history = []

        # ====================================
        # META STATE
        # ====================================

        self.meta_state = {

            "adaptive_routing":
            True,

            "multi_engine_reasoning":
            True,

            "recursive_awareness":
            True,

            "optimization_aware":
            True,

            "semantic_analysis":
            True
        }

    # ========================================
    # TASK ANALYSIS
    # ========================================

    def analyze_task(

        self,

        input_grid,

        output_grid
    ):

        input_grid = np.array(
            input_grid
        )

        output_grid = np.array(
            output_grid
        )

        color_changes = int(

            np.sum(
                input_grid != output_grid
            )
        )

        input_colors = len(
            np.unique(input_grid)
        )

        output_colors = len(
            np.unique(output_grid)
        )

        grid_complexity = (

            input_grid.shape[0]
            *
            input_grid.shape[1]
        )

        transformation_ratio = round(

            color_changes
            / max(
                grid_complexity,
                1
            ),

            4
        )

        symbolic_entropy = round(

            (
                input_colors
                +
                output_colors
            )

            / max(
                grid_complexity,
                1
            ),

            4
        )

        return {

            "input_shape":
            input_grid.shape,

            "output_shape":
            output_grid.shape,

            "same_shape":

            input_grid.shape
            ==
            output_grid.shape,

            "color_changes":
            color_changes,

            "input_colors":
            input_colors,

            "output_colors":
            output_colors,

            "grid_complexity":
            grid_complexity,

            "transformation_ratio":
            transformation_ratio,

            "symbolic_entropy":
            symbolic_entropy
        }

    # ========================================
    # ENGINE SCORING
    # ========================================

    def score_engines(

        self,

        analysis
    ):

        scores = {}

        # ====================================
        # INFERENCE
        # ====================================

        inference_score = 0.0

        if analysis["same_shape"]:

            inference_score += 0.4

        if analysis["color_changes"] <= 5:

            inference_score += 0.4

        if analysis["symbolic_entropy"] <= 0.15:

            inference_score += 0.2

        scores["inference"] = round(
            inference_score,
            4
        )

        # ====================================
        # PLANNER
        # ====================================

        planner_score = 0.0

        if analysis["same_shape"]:

            planner_score += 0.3

        if analysis["color_changes"] > 5:

            planner_score += 0.3

        if analysis[
            "transformation_ratio"
        ] >= 0.1:

            planner_score += 0.4

        scores["planner"] = round(
            planner_score,
            4
        )

        # ====================================
        # SYNTHESIS
        # ====================================

        synthesis_score = 0.0

        if not analysis["same_shape"]:

            synthesis_score += 0.5

        if analysis[
            "symbolic_entropy"
        ] >= 0.2:

            synthesis_score += 0.3

        if analysis[
            "grid_complexity"
        ] >= 100:

            synthesis_score += 0.2

        scores["synthesis"] = round(
            synthesis_score,
            4
        )

        # ====================================
        # SEARCH
        # ====================================

        search_score = 0.0

        if analysis[
            "transformation_ratio"
        ] >= 0.3:

            search_score += 0.5

        if analysis[
            "grid_complexity"
        ] >= 150:

            search_score += 0.3

        if analysis[
            "symbolic_entropy"
        ] >= 0.25:

            search_score += 0.2

        scores["search"] = round(
            search_score,
            4
        )

        return scores

    # ========================================
    # ENGINE SELECTION
    # ========================================

    def select_engines(

        self,

        engine_scores
    ):

        ranked = sorted(

            engine_scores.items(),

            key=lambda item:
            item[1],

            reverse=True
        )

        primary_engine = (
            ranked[0][0]
        )

        secondary_engine = (
            ranked[1][0]
        )

        return {

            "primary":
            primary_engine,

            "secondary":
            secondary_engine,

            "ranking":
            ranked
        }

    # ========================================
    # CONFIDENCE ESTIMATION
    # ========================================

    def estimate_confidence(

        self,

        engine_name,

        score
    ):

        base_confidence = (

            self.engine_profiles[
                engine_name
            ][
                "base_confidence"
            ]
        )

        confidence = (

            base_confidence
            *
            score
        )

        return round(
            confidence,
            4
        )

    # ========================================
    # META REASONING
    # ========================================

    def reason(

        self,

        input_grid,

        output_grid
    ):

        # ====================================
        # TASK ANALYSIS
        # ====================================

        analysis = (

            self.analyze_task(

                input_grid,

                output_grid
            )
        )

        # ====================================
        # ENGINE SCORING
        # ====================================

        engine_scores = (

            self.score_engines(
                analysis
            )
        )

        # ====================================
        # ENGINE SELECTION
        # ====================================

        selected_engines = (

            self.select_engines(
                engine_scores
            )
        )

        primary_engine = (
            selected_engines[
                "primary"
            ]
        )

        confidence = (

            self.estimate_confidence(

                primary_engine,

                engine_scores[
                    primary_engine
                ]
            )
        )

        reasoning_result = {

            "primary_engine":
            primary_engine,

            "secondary_engine":

            selected_engines[
                "secondary"
            ],

            "confidence":
            confidence,

            "engine_scores":
            engine_scores,

            "analysis":
            analysis,

            "meta_state":
            self.meta_state,

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE ROUTING
        # ====================================

        self.routing_history.append(
            reasoning_result
        )

        return reasoning_result

    # ========================================
    # ROUTING SUMMARY
    # ========================================

    def summary(self):

        return {

            "routing_history":
            len(
                self.routing_history
            ),

            "meta_state":
            self.meta_state,

            "engine_profiles":
            self.engine_profiles
        }