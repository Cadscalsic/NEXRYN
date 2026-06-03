import numpy as np

from core.inference import InferenceEngine
from core.planner import PlannerEngine
from core.synthesis import ProgramSynthesisEngine
from core.search import BeamSearchEngine

from core.transformations import (
    Rotate,
    Flip,
    Mirror,
    Translate
)


class OrchestratorEngine:

    def __init__(self):

        self.inference_engine = InferenceEngine()

        self.planner_engine = PlannerEngine()

        self.synthesis_engine = ProgramSynthesisEngine()

        self.search_engine = BeamSearchEngine(

            transformations=[

                Rotate(),

                Flip(),

                Mirror(),

                Translate()

            ],

            beam_width=5,

            max_depth=3
        )

    # ==========================================
    # SELECT ENGINE
    # ==========================================

    def select_engine(self, meta_result):

        engine = meta_result["selected_engine"]

        return engine

    # ==========================================
    # EXECUTE
    # ==========================================

    def execute(

        self,

        input_grid,

        output_grid,

        meta_result

    ):

        selected = self.select_engine(meta_result)

        # --------------------------------------
        # INFERENCE
        # --------------------------------------

        if selected == "inference":

            result = self.inference_engine.infer(

                input_grid,

                output_grid

            )

            return {

                "engine": "inference",

                "result": result

            }

        # --------------------------------------
        # PLANNER
        # --------------------------------------

        elif selected == "planner":

            result = self.planner_engine.plan(

                input_grid,

                output_grid,

                max_depth=2

            )

            return {

                "engine": "planner",

                "result": result

            }

        # --------------------------------------
        # SYNTHESIS
        # --------------------------------------

        elif selected == "synthesis":

            result = self.synthesis_engine.synthesize(

                input_grid,

                output_grid,

                max_depth=2

            )

            return {

                "engine": "synthesis",

                "result": result

            }

        # --------------------------------------
        # SEARCH
        # --------------------------------------

        elif selected == "search":

            result = self.search_engine.search(

                input_grid,

                output_grid

            )

            return {

                "engine": "search",

                "result": result

            }

        # --------------------------------------
        # FALLBACK
        # --------------------------------------

        else:

            result = self.planner_engine.plan(

                input_grid,

                output_grid,

                max_depth=2

            )

            return {

                "engine": "fallback_planner",

                "result": result

            }