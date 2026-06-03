class RetryEngine:

    def __init__(self):

        self.retry_limit = 3

    # =====================================================
    # SHOULD RETRY
    # =====================================================

    def should_retry(

        self,

        feedback_result

    ):

        return feedback_result.get(

            "retry",

            False

        )

    # =====================================================
    # NEXT ENGINE
    # =====================================================

    def next_engine(

        self,

        feedback_result

    ):

        return feedback_result.get(

            "next_engine",

            "search"

        )

    # =====================================================
    # EXECUTE RETRY
    # =====================================================

    def retry(

        self,

        orchestrator,

        input_grid,

        output_grid,

        feedback_result

    ):

        retries = []

        current_engine = self.next_engine(

            feedback_result

        )

        attempts = 0

        while attempts < self.retry_limit:

            result = self.execute_engine(

                orchestrator,

                current_engine,

                input_grid,

                output_grid

            )

            retries.append({

                "engine": current_engine,

                "result": result

            })

            score = self.extract_score(

                current_engine,

                result

            )

            # ------------------------------------------
            # STOP IF GOOD ENOUGH
            # ------------------------------------------

            if score >= 0.90:

                break

            # ------------------------------------------
            # NEXT ENGINE
            # ------------------------------------------

            current_engine = self.advance_engine(

                current_engine

            )

            attempts += 1

        return retries

    # =====================================================
    # EXECUTE ENGINE
    # =====================================================

    def execute_engine(

        self,

        orchestrator,

        engine_name,

        input_grid,

        output_grid

    ):

        # ------------------------------------------
        # INFERENCE
        # ------------------------------------------

        if engine_name == "inference":

            return orchestrator.inference_engine.infer(

                input_grid,

                output_grid

            )

        # ------------------------------------------
        # PLANNER
        # ------------------------------------------

        elif engine_name == "planner":

            return orchestrator.planner_engine.plan(

                input_grid,

                output_grid,

                max_depth=2

            )

        # ------------------------------------------
        # SYNTHESIS
        # ------------------------------------------

        elif engine_name == "synthesis":

            return orchestrator.synthesis_engine.synthesize(

                input_grid,

                output_grid,

                max_depth=2

            )

        # ------------------------------------------
        # SEARCH
        # ------------------------------------------

        elif engine_name == "search":

            return orchestrator.search_engine.search(

                input_grid,

                output_grid

            )

        return {}

    # =====================================================
    # EXTRACT SCORE
    # =====================================================

    def extract_score(

        self,

        engine_name,

        result

    ):

        if engine_name == "search":

            return float(

                result.get(

                    "best_score",

                    0.0

                )

            )

        return float(

            result.get(

                "score",

                0.0

            )

        )

    # =====================================================
    # ENGINE ORDER
    # =====================================================

    def advance_engine(

        self,

        current_engine

    ):

        order = [

            "inference",

            "planner",

            "synthesis",

            "search"

        ]

        if current_engine not in order:

            return "search"

        index = order.index(current_engine)

        if index + 1 >= len(order):

            return "search"

        return order[index + 1]