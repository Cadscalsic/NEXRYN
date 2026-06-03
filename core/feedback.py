# ============================================
# NEXRYN ADAPTIVE FEEDBACK ENGINE
# ============================================

from datetime import datetime


# ============================================
# FEEDBACK ENGINE
# ============================================

class FeedbackEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # ADAPTIVE THRESHOLDS
        # ====================================

        self.thresholds = {

            "excellent":
            0.90,

            "good":
            0.70,

            "acceptable":
            0.50,

            "unstable":
            0.30
        }

        # ====================================
        # ENGINE ROUTING
        # ====================================

        self.routing_policy = {

            "inference": [

                "planner",

                "search",

                "synthesis"
            ],

            "planner": [

                "synthesis",

                "search"
            ],

            "synthesis": [

                "search"
            ],

            "search": [

                "search"
            ]
        }

        # ====================================
        # FEEDBACK HISTORY
        # ====================================

        self.feedback_history = []

        # ====================================
        # ENGINE PERFORMANCE MEMORY
        # ====================================

        self.performance_memory = {}

    # ========================================
    # EVALUATE RESULT
    # ========================================

    def evaluate(

        self,

        engine_name,

        result,

        runtime_context=None
    ):

        runtime_context = (
            runtime_context or {}
        )

        score = self.extract_score(
            result
        )

        confidence = self.extract_confidence(
            result
        )

        cognitive_pressure = (

            self.extract_cognitive_pressure(
                runtime_context
            )
        )

        quality_state = (
            self.classify(score)
        )

        feedback_result = {

            "engine":
            engine_name,

            "score":
            score,

            "confidence":
            confidence,

            "quality_state":
            quality_state,

            "cognitive_pressure":
            cognitive_pressure,

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE FEEDBACK
        # ====================================

        self.store_feedback(
            feedback_result
        )

        return feedback_result

    # ========================================
    # EXTRACT SCORE
    # ========================================

    def extract_score(

        self,

        result
    ):

        return float(

            result.get(
                "score",

                result.get(
                    "accuracy",

                    result.get(
                        "best_score",
                        0.0
                    )
                )
            )
        )

    # ========================================
    # EXTRACT CONFIDENCE
    # ========================================

    def extract_confidence(

        self,

        result
    ):

        return float(

            result.get(
                "confidence",

                result.get(
                    "certainty",
                    0.0
                )
            )
        )

    # ========================================
    # COGNITIVE PRESSURE
    # ========================================

    def extract_cognitive_pressure(

        self,

        runtime_context
    ):

        inference_report = (

            runtime_context.get(
                "inference_report"
            )

            or {}
        )

        return float(

            inference_report.get(
                "cognitive_pressure",
                0.0
            )
        )

    # ========================================
    # CLASSIFY QUALITY
    # ========================================

    def classify(

        self,

        score
    ):

        if score >= self.thresholds[
            "excellent"
        ]:

            return "excellent"

        if score >= self.thresholds[
            "good"
        ]:

            return "good"

        if score >= self.thresholds[
            "acceptable"
        ]:

            return "acceptable"

        if score >= self.thresholds[
            "unstable"
        ]:

            return "unstable"

        return "critical"

    # ========================================
    # SHOULD RETRY
    # ========================================

    def should_retry(

        self,

        feedback_result
    ):

        return feedback_result[
            "quality_state"
        ] in [

            "unstable",

            "critical"
        ]

    # ========================================
    # NEXT ENGINE
    # ========================================

    def next_engine(

        self,

        current_engine
    ):

        candidates = (

            self.routing_policy.get(
                current_engine,
                ["search"]
            )
        )

        return candidates[0]

    # ========================================
    # STORE FEEDBACK
    # ========================================

    def store_feedback(

        self,

        feedback_result
    ):

        self.feedback_history.append(
            feedback_result
        )

        engine_name = (
            feedback_result["engine"]
        )

        if engine_name not in (
            self.performance_memory
        ):

            self.performance_memory[
                engine_name
            ] = []

        self.performance_memory[
            engine_name
        ].append(
            feedback_result["score"]
        )

    # ========================================
    # ENGINE PERFORMANCE
    # ========================================

    def engine_performance(

        self,

        engine_name
    ):

        scores = (

            self.performance_memory.get(
                engine_name,
                []
            )
        )

        if not scores:

            return 0.0

        return round(

            sum(scores)
            / len(scores),

            4
        )

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def summary(

        self,

        feedback_result
    ):

        engine_name = (
            feedback_result["engine"]
        )

        return {

            "engine":
            engine_name,

            "score":
            feedback_result["score"],

            "confidence":

            feedback_result[
                "confidence"
            ],

            "quality_state":

            feedback_result[
                "quality_state"
            ],

            "retry":

            self.should_retry(
                feedback_result
            ),

            "next_engine":

            self.next_engine(
                engine_name
            ),

            "historical_performance":

            self.engine_performance(
                engine_name
            ),

            "feedback_history":
            len(self.feedback_history)
        }