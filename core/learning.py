import json
import os


class AdaptiveLearningEngine:

    def __init__(self, memory_engine=None):

        self.memory_engine = memory_engine

        self.engine_scores = {

            "planner": 0,

            "search": 0,

            "synthesis": 0,

            "inference": 0

        }

        self.engine_usage = {

            "planner": 0,

            "search": 0,

            "synthesis": 0,

            "inference": 0

        }

    # ==========================================
    # UPDATE ENGINE PERFORMANCE
    # ==========================================

    def update_engine_score(

        self,

        engine_name,

        success_score

    ):

        if engine_name not in self.engine_scores:

            return

        self.engine_scores[engine_name] += float(success_score)

        self.engine_usage[engine_name] += 1

    # ==========================================
    # GET ENGINE RANKING
    # ==========================================

    def get_engine_ranking(self):

        ranking = {}

        for engine in self.engine_scores:

            usage = self.engine_usage[engine]

            score = self.engine_scores[engine]

            if usage == 0:

                ranking[engine] = 0

            else:

                ranking[engine] = score / usage

        return ranking

    # ==========================================
    # BEST ENGINE
    # ==========================================

    def best_engine(self):

        ranking = self.get_engine_ranking()

        best = max(ranking, key=ranking.get)

        return {

            "best_engine": best,

            "score": ranking[best]

        }

    # ==========================================
    # LEARN FROM RESULT
    # ==========================================

    def learn(

        self,

        engine_name,

        result

    ):

        score = 0.0

        # --------------------------------------
        # SEARCH ENGINE
        # --------------------------------------

        if engine_name == "search":

            score = float(

                result.get(

                    "best_score",

                    0.0

                )

            )

        # --------------------------------------
        # PLANNER
        # --------------------------------------

        elif engine_name == "planner":

            score = float(

                result.get(

                    "score",

                    0.0

                )

            )

        # --------------------------------------
        # SYNTHESIS
        # --------------------------------------

        elif engine_name == "synthesis":

            score = float(

                result.get(

                    "score",

                    0.0

                )

            )

        # --------------------------------------
        # INFERENCE
        # --------------------------------------

        elif engine_name == "inference":

            score = float(

                result.get(

                    "score",

                    0.0

                )

            )

        self.update_engine_score(

            engine_name,

            score

        )

    # ==========================================
    # SUMMARY
    # ==========================================

    def summary(self):

        return {

            "ranking": self.get_engine_ranking(),

            "best_engine": self.best_engine(),

            "usage": self.engine_usage

        }