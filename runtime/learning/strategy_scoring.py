# ============================================
# NEXRYN STRATEGY SCORING ENGINE
# ============================================

from datetime import datetime
import uuid


# ============================================
# STRATEGY SCORING ENGINE
# ============================================

class StrategyScoringEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # STRATEGY DATABASE
        # ====================================

        self.strategy_scores = {}

        # ====================================
        # SCORE HISTORY
        # ====================================

        self.score_history = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "engine_mode":
            "adaptive_strategy_scoring",

            "adaptive_scoring":
            True,

            "normalization":
            True,

            "scoring_cycles":
            0
        }

    # ========================================
    # NORMALIZE SCORE
    # ========================================

    def normalize_score(

        self,

        score
    ):

        # ====================================
        # INVALID VALUES
        # ====================================

        if score is None:

            score = 0.0

        if not isinstance(

            score,

            (int, float)
        ):

            score = 0.0

        # ====================================
        # CLAMP SCORE
        # ====================================

        score = max(
            0.0,
            score
        )

        score = min(
            1.0,
            score
        )

        return round(
            score,
            4
        )

    # ========================================
    # REGISTER STRATEGY
    # ========================================

    def register_strategy(

        self,

        strategy_name
    ):

        # ====================================
        # NORMALIZATION
        # ====================================

        if strategy_name is None:

            strategy_name = (
                "unknown_strategy"
            )

        if not isinstance(
            strategy_name,
            str
        ):

            strategy_name = str(
                strategy_name
            )

        # ====================================
        # CREATE STRATEGY
        # ====================================

        if strategy_name not in (

            self.strategy_scores
        ):

            self.strategy_scores[
                strategy_name
            ] = {

                "strategy_id":
                str(uuid.uuid4()),

                "success_count":
                0,

                "failure_count":
                0,

                "total_score":
                0.0,

                "average_score":
                0.0,

                "stability_score":
                0.0,

                "usage_count":
                0,

                "last_updated":
                None,

                "strategy_state":
                "emerging"
            }

    # ========================================
    # COMPUTE STABILITY
    # ========================================

    def compute_stability(

        self,

        success_count,

        failure_count
    ):

        total_attempts = (
            success_count
            + failure_count
        )

        if total_attempts == 0:

            return 0.0

        stability = (
            success_count
            / total_attempts
        )

        return round(
            stability,
            4
        )

    # ========================================
    # COMPUTE STRATEGY STATE
    # ========================================

    def compute_strategy_state(

        self,

        average_score,

        stability_score
    ):

        if (

            average_score >= 0.85

            and

            stability_score >= 0.80
        ):

            return "elite"

        elif (

            average_score >= 0.65

            and

            stability_score >= 0.60
        ):

            return "stable"

        elif average_score >= 0.40:

            return "adaptive"

        return "unstable"

    # ========================================
    # BUILD SCORE EVENT
    # ========================================

    def build_score_event(

        self,

        strategy_name,

        success,

        accuracy
    ):

        return {

            "event_id":
            str(uuid.uuid4()),

            "strategy_name":
            strategy_name,

            "success":
            success,

            "accuracy":
            accuracy,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # UPDATE STRATEGY
    # ========================================

    def update_strategy(

        self,

        strategy_name,

        success,

        accuracy
    ):

        # ====================================
        # NORMALIZATION
        # ====================================

        accuracy = (
            self.normalize_score(
                accuracy
            )
        )

        if success is None:

            success = False

        success = bool(success)

        # ====================================
        # REGISTER STRATEGY
        # ====================================

        self.register_strategy(
            strategy_name
        )

        # ====================================
        # LOAD STRATEGY
        # ====================================

        strategy_data = (

            self.strategy_scores[
                strategy_name
            ]
        )

        # ====================================
        # UPDATE COUNTS
        # ====================================

        if success:

            strategy_data[
                "success_count"
            ] += 1

        else:

            strategy_data[
                "failure_count"
            ] += 1

        # ====================================
        # UPDATE TOTAL SCORE
        # ====================================

        strategy_data[
            "total_score"
        ] += accuracy

        # ====================================
        # UPDATE USAGE
        # ====================================

        strategy_data[
            "usage_count"
        ] += 1

        # ====================================
        # COMPUTE ATTEMPTS
        # ====================================

        total_attempts = (

            strategy_data[
                "success_count"
            ]

            +

            strategy_data[
                "failure_count"
            ]
        )

        # ====================================
        # SAFE DIVISION
        # ====================================

        if total_attempts <= 0:

            total_attempts = 1

        # ====================================
        # COMPUTE AVERAGE
        # ====================================

        strategy_data[
            "average_score"
        ] = round(

            strategy_data[
                "total_score"
            ]

            /

            total_attempts,

            4
        )

        # ====================================
        # STABILITY SCORE
        # ====================================

        stability_score = (

            self.compute_stability(

                strategy_data[
                    "success_count"
                ],

                strategy_data[
                    "failure_count"
                ]
            )
        )

        strategy_data[
            "stability_score"
        ] = stability_score

        # ====================================
        # STRATEGY STATE
        # ====================================

        strategy_state = (

            self.compute_strategy_state(

                strategy_data[
                    "average_score"
                ],

                stability_score
            )
        )

        strategy_data[
            "strategy_state"
        ] = strategy_state

        # ====================================
        # TIMESTAMP
        # ====================================

        strategy_data[
            "last_updated"
        ] = str(
            datetime.utcnow()
        )

        # ====================================
        # SCORE EVENT
        # ====================================

        score_event = (

            self.build_score_event(

                strategy_name,

                success,

                accuracy
            )
        )

        self.score_history.append(
            score_event
        )

        # ====================================
        # UPDATE ENGINE STATE
        # ====================================

        self.engine_state[
            "scoring_cycles"
        ] += 1

        return strategy_data

    # ========================================
    # GET BEST STRATEGY
    # ========================================

    def get_best_strategy(self):

        if not self.strategy_scores:

            return None

        best_strategy = None

        best_score = -1

        for strategy_name, data in (

            self.strategy_scores.items()
        ):

            if not isinstance(
                data,
                dict
            ):

                continue

            score = data.get(
                "average_score",
                0.0
            )

            stability = data.get(
                "stability_score",
                0.0
            )

            combined_score = round(

                (
                    score * 0.7
                )

                +

                (
                    stability * 0.3
                ),

                4
            )

            if combined_score > best_score:

                best_score = combined_score

                best_strategy = {

                    "strategy_name":
                    strategy_name,

                    "combined_score":
                    combined_score,

                    "data":
                    data
                }

        return best_strategy

    # ========================================
    # GET STRATEGY DATABASE
    # ========================================

    def get_strategy_database(self):

        return self.strategy_scores

    # ========================================
    # GET TOP STRATEGIES
    # ========================================

    def get_top_strategies(

        self,

        limit=5
    ):

        strategies = []

        for strategy_name, data in (

            self.strategy_scores.items()
        ):

            if not isinstance(
                data,
                dict
            ):

                continue

            strategies.append({

                "strategy_name":
                strategy_name,

                "average_score":
                data.get(
                    "average_score",
                    0.0
                ),

                "stability_score":
                data.get(
                    "stability_score",
                    0.0
                ),

                "strategy_state":
                data.get(
                    "strategy_state",
                    "unknown"
                )
            })

        strategies = sorted(

            strategies,

            key=lambda x: x[
                "average_score"
            ],

            reverse=True
        )

        return strategies[:limit]

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "strategy_count":
            len(
                self.strategy_scores
            ),

            "score_history":
            len(
                self.score_history
            ),

            "best_strategy":
            self.get_best_strategy()
        }

    # ========================================
    # PRINT STRATEGIES
    # ========================================

    def print_strategies(self):

        print(
            "\n=================================================="
        )

        print(
            "NEXRYN :: STRATEGY SCORES"
        )

        print(
            "==================================================\n"
        )

        for strategy_name, data in (

            self.strategy_scores.items()
        ):

            print(strategy_name)

            print(data)

            print()


# ============================================
# GLOBAL STRATEGY SCORING ENGINE
# ============================================

strategy_scoring_engine = (
    StrategyScoringEngine()
)