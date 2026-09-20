# ============================================
# NEXRYN HYPOTHESIS ARBITRATION ENGINE
# ============================================

from datetime import datetime

import copy

from runtime.semantics.semantic_ontology import (
    lookup_operator_semantics,
)

from runtime.reasoning.invariant_filter import (
    InvariantFilter,
)

from runtime.meta.supervisor import meta_supervisor


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

        self.invariant_filter = InvariantFilter()

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
        confidence = self.safe_score(
            hypothesis.get("confidence", grounding.get("confidence", 0.0))
        )
        explanatory_power = self.safe_score(
            hypothesis.get("explanatory_power", hypothesis.get("world_model_fit", 0.0))
        )
        residual_reduction = self.safe_score(
            hypothesis.get(
                "residual_reduction",
                hypothesis.get("world_model_fit", 0.0),
            )
        )
        transformation_salience = self.safe_score(
            hypothesis.get("transformation_salience", 0.0)
        )
        causal_support = self.safe_score(
            hypothesis.get(
                "causal_support",
                grounding.get("confidence", 0.0),
            )
        )
        explanatory_penalty = self.safe_score(
            hypothesis.get(
                "invariant_penalty",
                self.invariant_filter.penalty(hypothesis),
            )
        )

        final_score = (
            confidence * 0.15
            +
            explanatory_power * 0.35
            +
            residual_reduction * 0.25
            +
            transformation_salience * 0.15
            +
            causal_support * 0.10
            -
            explanatory_penalty
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
        annotated = self.invariant_filter.annotate(hypotheses)
        max_transformation_salience = max(
            [
                self.safe_score(hypothesis.get("transformation_salience", 0.0))
                for hypothesis in annotated
                if hypothesis.get("semantic_class") != "invariant"
            ]
            or [0.0]
        )
        filtered = [
            hypothesis
            for hypothesis in annotated
            if self.invariant_filter.can_invariant_win(
                hypothesis,
                max_transformation_salience,
                self.safe_score(hypothesis.get("transformation_salience", 0.0)),
            )
        ]
        candidates = sorted(
            [
                hypothesis
                for hypothesis in filtered
                if isinstance(hypothesis, dict)
                and hypothesis.get("primitive")
            ],
            key=lambda hypothesis: (
                hypothesis.get("transformation_salience", 0.0),
                hypothesis.get("explanatory_power", 0.0),
                hypothesis.get("residual_reduction", 0.0),
                hypothesis.get("search_final_score", 0.0),
            ),
            reverse=True,
        )[:self.EXECUTION_CANDIDATE_LIMIT]
        evaluated = []

        for hypothesis in candidates:
            if not meta_supervisor.is_action_allowed("program_synthesis"):
                evaluated.append({
                    "hypothesis": hypothesis,
                    "program": {},
                    "score": self.score_hypothesis(hypothesis),
                    "anticipation": {
                        "status": "program_synthesis_blocked_by_meta_supervisor",
                    },
                })
                continue
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
            }
            scored["semantic_class"] = self.invariant_filter.semantic_class(scored)
            scored["invariant_penalty"] = self.invariant_filter.penalty(scored)
            scored["explanatory_power"] = max(
                self.safe_score(scored.get("explanatory_power", 0.0)),
                self.safe_score(scored.get("world_model_fit", 0.0)),
            )
            scored["residual_reduction"] = max(
                self.safe_score(scored.get("residual_reduction", 0.0)),
                self.safe_score(scored.get("world_model_fit", 0.0)),
            )
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
            "ARBITRATION_REPORT": self._compact_report(
                evaluated,
                winner,
            ),
            "world_model_rehearsal_required": True,
            "selection_factors": [
                "explanatory_power",
                "residual_reduction",
                "transformation_salience",
                "causal_support",
                "invariant_penalty",
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

    def _compact_report(
        self,
        evaluated,
        winner
    ):

        winning_hypothesis = winner.get(
            "hypothesis",
            {}
        ) if isinstance(winner, dict) else {}

        return {

            "candidate_count":
            len(evaluated),

            "winning_hypothesis":
            winning_hypothesis.get(
                "primitive"
            ),

            "explanatory_power":
            winning_hypothesis.get(
                "explanatory_power",
                0.0
            ),

            "residual_reduction":
            winning_hypothesis.get(
                "residual_reduction",
                0.0
            ),

            "invariant_penalty":
            winning_hypothesis.get(
                "invariant_penalty",
                0.0
            ),

            "final_score":
            winner.get(
                "score",
                0.0
            ) if isinstance(winner, dict) else 0.0
        }

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
