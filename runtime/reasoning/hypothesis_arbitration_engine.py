# ============================================
# NEXRYN HYPOTHESIS ARBITRATION ENGINE
# ============================================

from datetime import datetime

import copy

from runtime.semantics.semantic_ontology import (
    lookup_operator_semantics,
)


# ============================================
# HYPOTHESIS ARBITRATION ENGINE
# ============================================

class HypothesisArbitrationEngine:

    EXECUTION_CANDIDATE_LIMIT = 5

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.arbitration_history = []

        self.winning_hypotheses = []

        self.engine_state = {

            "confidence_arbitration":
            True,

            "reasoning_selection":
            True,

            "conflict_resolution":
            True,

            "priority_balancing":
            True,

            "adaptive_selection":
            True
        }

    # ========================================
    # SCORE HYPOTHESIS
    # ========================================

    def score_hypothesis(

        self,

        hypothesis
    ):

        grounding = hypothesis.get("geometric_grounding", {})
        search_score = self.safe_score(
            hypothesis.get(
                "search_final_score",
                hypothesis.get("execution_score", 0.0),
            )
        )
        causal_support = self.safe_score(
            hypothesis.get(
                "causal_support",
                grounding.get("confidence", 0.0),
            )
        )
        semantic_support = self.safe_score(
            hypothesis.get(
                "semantic_support",
                1.0
                if lookup_operator_semantics(hypothesis.get("primitive"))
                else 0.0,
            )
        )
        world_model_fit = self.safe_score(
            hypothesis.get("world_model_fit", 0.0)
        )
        historical_success = self.safe_score(
            hypothesis.get(
                "historical_success",
                hypothesis.get(
                    "operator_reward_score",
                    hypothesis.get("operator_weight", 0.0),
                ),
            )
        )

        final_score = (
            search_score * 0.20
            +
            causal_support * 0.15
            +
            semantic_support * 0.10
            +
            world_model_fit * 0.45
            +
            historical_success * 0.10
        )

        return round(
            final_score,
            4
        )

    def safe_score(self, value):
        if not isinstance(value, (int, float)):
            return 0.0
        return min(max(float(value), 0.0), 1.0)

    def arbitrate_execution_candidates(
        self,
        hypotheses,
        input_grid,
        target_grid,
        world_model_engine,
        program_synthesis_engine,
    ):
        candidates = sorted(
            [
                hypothesis
                for hypothesis in hypotheses
                if isinstance(hypothesis, dict)
                and hypothesis.get("primitive")
            ],
            key=lambda hypothesis: hypothesis.get(
                "search_final_score",
                0.0,
            ),
            reverse=True,
        )[:self.EXECUTION_CANDIDATE_LIMIT]
        evaluated = []

        for hypothesis in candidates:
            candidate_program = program_synthesis_engine.synthesize(
                [],
                winner_hypothesis=hypothesis,
            )
            anticipation = world_model_engine.anticipate_program(
                input_grid=input_grid,
                target_grid=target_grid,
                synthesized_program=candidate_program,
                minimum_accuracy=0.75,
            )
            scored = {
                **hypothesis,
                "world_model_fit":
                anticipation.get(
                    "prediction_report",
                    {},
                ).get(
                    "prediction_accuracy",
                    0.0,
                ),
                "causal_support":
                hypothesis.get(
                    "geometric_grounding",
                    {},
                ).get(
                    "confidence",
                    0.0,
                ),
                "semantic_support":
                1.0
                if lookup_operator_semantics(hypothesis.get("primitive"))
                else 0.0,
                "historical_success":
                hypothesis.get(
                    "operator_reward_score",
                    hypothesis.get("operator_weight", 0.0),
                ),
            }
            evaluated.append({
                "hypothesis": scored,
                "program": candidate_program,
                "score": self.score_hypothesis(scored),
                "anticipation": anticipation,
            })

        evaluated.sort(
            key=lambda item: item["score"],
            reverse=True,
        )
        winner = evaluated[0] if evaluated else {}
        return {
            "system": "hypothesis_arbitration_engine",
            "candidate_count": len(evaluated),
            "ranked_candidates": evaluated,
            "winner": winner,
            "world_model_rehearsal_required": True,
            "selection_factors": [
                "search_final_score",
                "causal_support",
                "semantic_support",
                "world_model_fit",
                "historical_success",
            ],
        }

    # ========================================
    # RANK HYPOTHESES
    # ========================================

    def rank_hypotheses(

        self,

        hypotheses
    ):

        ranked_hypotheses = []

        for hypothesis in hypotheses:

            scored_hypothesis = {

                "hypothesis":
                hypothesis,

                "score":

                self.score_hypothesis(
                    hypothesis
                )
            }

            ranked_hypotheses.append(
                scored_hypothesis
            )

        ranked_hypotheses = sorted(

            ranked_hypotheses,

            key=lambda item:

            item.get(
                "score",
                0.0
            ),

            reverse=True
        )

        return ranked_hypotheses

    # ========================================
    # SELECT WINNER
    # ========================================

    def select_winner(

        self,

        hypotheses
    ):

        if not hypotheses:

            return {}

        ranked_hypotheses = (

            self.rank_hypotheses(
                hypotheses
            )
        )

        winner = ranked_hypotheses[0]

        return winner

    # ========================================
    # DETECT CONFLICTS
    # ========================================

    def detect_conflicts(

        self,

        hypotheses
    ):

        conflicts = []

        hypothesis_types = []

        for hypothesis in hypotheses:

            hypothesis_type = (

                hypothesis.get(
                    "type",
                    "unknown"
                )
            )

            if hypothesis_type in (
                hypothesis_types
            ):

                conflicts.append({

                    "conflict_type":
                    "duplicate_reasoning",

                    "hypothesis":
                    hypothesis_type
                })

            hypothesis_types.append(
                hypothesis_type
            )

        return conflicts

    # ========================================
    # BUILD ARBITRATION REPORT
    # ========================================

    def build_arbitration_report(

        self,

        hypotheses
    ):

        # ====================================
        # RANK HYPOTHESES
        # ====================================

        ranked_hypotheses = (

            self.rank_hypotheses(
                hypotheses
            )
        )

        # ====================================
        # SELECT WINNER
        # ====================================

        winner = {}

        if ranked_hypotheses:

            winner = (
                ranked_hypotheses[0]
            )

        # ====================================
        # DETECT CONFLICTS
        # ====================================

        conflicts = (

            self.detect_conflicts(
                hypotheses
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "candidate_count":
            len(hypotheses),

            "ranked_hypotheses":
            ranked_hypotheses,

            "winner":
            winner,

            "conflict_count":
            len(conflicts),

            "conflicts":
            conflicts,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.arbitration_history.append(
            copy.deepcopy(report)
        )

        if winner:

            self.winning_hypotheses.append(
                winner
            )

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.arbitration_history:

            latest_report = (

                self.arbitration_history[-1]
            )

        return {

            "arbitration_cycles":

            len(
                self.arbitration_history
            ),

            "winning_hypotheses":

            len(
                self.winning_hypotheses
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

hypothesis_arbitration_engine = (
    HypothesisArbitrationEngine()
)
