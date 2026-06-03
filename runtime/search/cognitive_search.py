# ============================================
# NEXRYN COGNITIVE SEARCH ENGINE
# ============================================

import copy


# ============================================
# COGNITIVE SEARCH ENGINE
# ============================================

class CognitiveSearchEngine:

    def __init__(self):

        # ========================================
        # SEARCH STORAGE
        # ========================================

        self.search_history = []

        # ========================================
        # MAX SEARCH PATHS
        # ========================================

        self.max_paths = 5

    # ============================================
    # SAFE SCORE
    # ============================================

    def safe_score(

        self,

        value,

        default=0.0
    ):

        if not isinstance(
            value,
            (
                int,
                float
            )
        ):

            value = default

        value = max(
            0.0,
            float(value)
        )

        value = min(
            1.0,
            value
        )

        return value

    # ============================================
    # SCORE HYPOTHESIS
    # ============================================

    def score_hypothesis(

        self,

        hypothesis
    ):

        confidence = self.safe_score(
            hypothesis.get(
                "confidence",
                0.0
            )
        )

        execution_score = self.safe_score(
            hypothesis.get(
                "execution_score",
                0.0
            )
        )

        grounded_execution_score = self.safe_score(
            hypothesis.get(
                "grounded_execution_score",
                execution_score
            ),
            default=execution_score
        )

        operator_reward_score = self.safe_score(
            hypothesis.get(
                "operator_reward_score",
                hypothesis.get(
                    "operator_weight",
                    0.5
                )
            ),
            default=0.5
        )

        final_score = (
            confidence * 0.20
            +
            execution_score * 0.25
            +
            grounded_execution_score * 0.35
            +
            operator_reward_score * 0.20
        )

        return round(
            final_score,
            4
        )

    # ============================================
    # GENERATE SEARCH PATHS
    # ============================================

    def generate_paths(

        self,

        hypotheses
    ):

        paths = []

        # ========================================
        # SINGLE PATHS
        # ========================================

        for hypothesis in hypotheses:

            paths.append({

                "path_type":
                "single",

                "hypotheses":
                [hypothesis]
            })

        # ========================================
        # COMBINED PATHS
        # ========================================

        for i in range(len(hypotheses)):

            for j in range(

                i + 1,

                len(hypotheses)
            ):

                paths.append({

                    "path_type":
                    "combined",

                    "hypotheses": [

                        hypotheses[i],

                        hypotheses[j]
                    ]
                })

        return paths[:self.max_paths]

    # ============================================
    # SCORE PATH
    # ============================================

    def score_path(

        self,

        path
    ):

        hypotheses = path.get(
            "hypotheses",
            []
        )

        if not hypotheses:

            return 0.0

        score_sum = sum([

            self.score_hypothesis(
                hypothesis
            )

            for hypothesis in hypotheses
        ])

        score = (

            score_sum

            /

            len(hypotheses)
        )

        return round(
            score,
            4
        )

    # ============================================
    # SEARCH
    # ============================================

    def search(

        self,

        hypotheses
    ):

        # ========================================
        # GENERATE PATHS
        # ========================================

        paths = self.generate_paths(
            hypotheses
        )

        evaluated_paths = []

        # ========================================
        # SCORE PATHS
        # ========================================

        for path in paths:

            score = self.score_path(
                path
            )

            evaluated_path = copy.deepcopy(
                path
            )

            evaluated_path[
                "score"
            ] = score

            evaluated_paths.append(
                evaluated_path
            )

        # ========================================
        # SORT PATHS
        # ========================================

        evaluated_paths = sorted(

            evaluated_paths,

            key=lambda p: p[
                "score"
            ],

            reverse=True
        )

        # ========================================
        # BEST PATH
        # ========================================

        best_path = (

            evaluated_paths[0]
            if evaluated_paths
            else None
        )

        # ========================================
        # SAVE HISTORY
        # ========================================

        self.search_history.append({

            "path_count":
            len(evaluated_paths),

            "best_path":
            best_path
        })

        return {

            "paths":
            evaluated_paths,

            "best_path":
            best_path,

            "path_count":
            len(evaluated_paths)
        }

    # ============================================
    # GET HISTORY
    # ============================================

    def get_history(self):

        return self.search_history

    # ============================================
    # PRINT SEARCH RESULTS
    # ============================================

    def print_search(

        self,

        search_result
    ):

        print("\n==================================================")
        print("NEXRYN :: COGNITIVE SEARCH")
        print("==================================================\n")

        for path in search_result["paths"]:

            print(path)

        print()
