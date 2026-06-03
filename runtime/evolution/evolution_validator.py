# ============================================
# NEXRYN EVOLUTION VALIDATOR
# ============================================

from runtime.evolution.promotion_registry import PromotionRegistry


# ============================================
# EVOLUTION VALIDATOR
# ============================================

class EvolutionValidator:

    def __init__(self):

        self.validation_history = []

        self.promotion_registry = PromotionRegistry()

        self.rejected_strategies = []

        self.temporal_validation_history = {}

        self.temporal_horizon = 3

    # ============================================
    # VALIDATE EVOLVED STRATEGY
    # ============================================

    def validate_strategy(

        self,

        original_hypothesis,

        evolved_hypothesis,

        evaluation_result
    ):

        original_confidence = original_hypothesis.get(
            "confidence",
            0.0
        )

        evolved_confidence = evolved_hypothesis.get(
            "confidence",
            0.0
        )

        accuracy = evaluation_result.get(
            "accuracy",
            0.0
        )

        success = evaluation_result.get(
            "success",
            False
        )

        validation = {

            "original_strategy":
            original_hypothesis.get(
                "type",
                "unknown"
            ),

            "evolved_strategy":
            evolved_hypothesis.get(
                "type",
                "unknown"
            ),

            "accuracy":
            accuracy,

            "original_confidence":
            original_confidence,

            "evolved_confidence":
            evolved_confidence,

            "confidence_delta":
            round(

                evolved_confidence
                -
                original_confidence,

                4
            ),

            "validation_status":
            "pending",

            "promotion_candidate":
            False,

            "base_promotion_candidate":
            False,

            "promotion_score":
            0.0,

            "temporal_validation":
            {},

            "rejection_reason":
            None
        }

        # ====================================
        # VALIDATION RULES
        # ====================================

        if accuracy < 0.5:

            validation[
                "validation_status"
            ] = "rejected"

            validation[
                "rejection_reason"
            ] = "low_accuracy"

        elif evolved_confidence < (
            original_confidence - 0.15
        ):

            validation[
                "validation_status"
            ] = "rejected"

            validation[
                "rejection_reason"
            ] = (
                "confidence_regression"
            )

        elif evolved_confidence >= (
            original_confidence
        ):

            validation[
                "validation_status"
            ] = "validated"

            validation[
                "base_promotion_candidate"
            ] = True

        else:

            validation[
                "validation_status"
            ] = "stable"

        temporal_validation = self.update_temporal_validation(
            strategy_name=validation.get(
                "evolved_strategy",
                "unknown"
            ),
            accuracy=accuracy,
            success=success,
            semantic_consistency=evaluation_result.get(
                "semantic_consistency",
                True
            ),
            entropy_stable=evaluation_result.get(
                "entropy_stable",
                True
            ),
            ontology_safe=evaluation_result.get(
                "ontology_safe",
                True
            )
        )

        validation[
            "temporal_validation"
        ] = temporal_validation

        validation[
            "promotion_score"
        ] = temporal_validation.get(
            "promotion_score",
            0.0
        )

        if (
            validation.get(
                "base_promotion_candidate",
                False
            )
            and
            temporal_validation.get(
                "promotion_allowed",
                False
            )
        ):

            validation[
                "promotion_candidate"
            ] = True

        elif validation.get(
            "base_promotion_candidate",
            False
        ):

            validation[
                "promotion_deferred_reason"
            ] = temporal_validation.get(
                "deferred_reason",
                "temporal_validation_incomplete"
            )

        return validation

    # ============================================
    # TEMPORAL VALIDATION
    # ============================================

    def update_temporal_validation(
        self,
        strategy_name,
        accuracy,
        success,
        semantic_consistency=True,
        entropy_stable=True,
        ontology_safe=True
    ):

        history = self.temporal_validation_history.setdefault(
            strategy_name,
            []
        )

        history.append({
            "accuracy":
            accuracy,

            "success":
            success,

            "semantic_consistency":
            semantic_consistency,

            "entropy_stable":
            entropy_stable,

            "ontology_safe":
            ontology_safe
        })

        history[:] = history[
            -self.temporal_horizon:
        ]

        horizon_complete = (
            len(history)
            >=
            self.temporal_horizon
        )

        average_accuracy = 0.0

        if history:

            average_accuracy = (
                sum(
                    item.get(
                        "accuracy",
                        0.0
                    )
                    for item in history
                )
                /
                len(history)
            )

        survival_stability = all(
            item.get(
                "success",
                False
            )
            or
            item.get(
                "accuracy",
                0.0
            ) >= 0.90
            for item in history
        )

        semantic_stability = all(
            item.get(
                "semantic_consistency",
                True
            )
            for item in history
        )

        entropy_stability = all(
            item.get(
                "entropy_stable",
                True
            )
            for item in history
        )

        ontology_safety = all(
            item.get(
                "ontology_safe",
                True
            )
            for item in history
        )

        promotion_score = round(
            (
                average_accuracy * 0.35
                +
                (1.0 if survival_stability else 0.0) * 0.25
                +
                (1.0 if semantic_stability else 0.0) * 0.15
                +
                (1.0 if entropy_stability else 0.0) * 0.15
                +
                (1.0 if ontology_safety else 0.0) * 0.10
            ),
            4
        )

        promotion_allowed = (
            horizon_complete
            and
            promotion_score >= 0.85
            and
            average_accuracy >= 0.90
            and
            survival_stability
            and
            semantic_stability
            and
            entropy_stability
            and
            ontology_safety
        )

        deferred_reason = None

        if not horizon_complete:

            deferred_reason = "temporal_horizon_incomplete"

        elif not promotion_allowed:

            deferred_reason = "stability_requirements_unmet"

        return {
            "window_size":
            len(history),

            "required_window":
            self.temporal_horizon,

            "average_accuracy":
            round(
                average_accuracy,
                4
            ),

            "survival_stability":
            survival_stability,

            "semantic_stability":
            semantic_stability,

            "entropy_stability":
            entropy_stability,

            "ontology_safety":
            ontology_safety,

            "promotion_score":
            promotion_score,

            "promotion_allowed":
            promotion_allowed,

            "deferred_reason":
            deferred_reason
        }

    # ============================================
    # PROMOTE STRATEGY
    # ============================================

    def promote_strategy(

        self,

        evolved_hypothesis
    ):

        promoted = {

            "strategy":
            evolved_hypothesis.get(
                "type",
                "unknown"
            ),

            "status":
            "promoted",

            "confidence":
            evolved_hypothesis.get(
                "confidence",
                0.0
            )
        }

        registered, newly_promoted = self.promotion_registry.register(
            promoted
        )

        return {
            **registered,
            "newly_promoted":
            newly_promoted
        }

    # ============================================
    # REJECT STRATEGY
    # ============================================

    def reject_strategy(

        self,

        evolved_hypothesis,

        reason
    ):

        rejected = {

            "strategy":
            evolved_hypothesis.get(
                "type",
                "unknown"
            ),

            "status":
            "rejected",

            "reason":
            reason
        }

        self.rejected_strategies.append(
            rejected
        )

        return rejected

    # ============================================
    # STORE VALIDATION EVENT
    # ============================================

    def store_validation_event(

        self,

        validation
    ):

        self.validation_history.append(
            validation
        )

    # ============================================
    # BUILD VALIDATION REPORT
    # ============================================

    def build_validation_report(self):

        validated = 0

        rejected = 0

        stable = 0

        for event in self.validation_history:

            status = event.get(
                "validation_status",
                "unknown"
            )

            if status == "validated":

                validated += 1

            elif status == "rejected":

                rejected += 1

            elif status == "stable":

                stable += 1

        report = {

            "validation_events":
            len(
                self.validation_history
            ),

            "validated_strategies":
            validated,

            "rejected_strategies":
            rejected,

            "stable_strategies":
            stable,

            "promoted_count":
            len(
                self.promotion_registry.promotions()
            ),

            "latest_validation":

            self.validation_history[-1]

            if self.validation_history

            else {},

            "temporal_horizon":
            self.temporal_horizon,

            "temporal_validation_tracks":
            len(
                self.temporal_validation_history
            )
        }

        return report

    # ============================================
    # BUILD PROMOTION SUMMARY
    # ============================================

    def build_promotion_summary(self):

        return {

            "promoted_strategies":
            self.promotion_registry.promotions(),

            "rejected_strategies":
            self.rejected_strategies,

            "promotion_count":
            len(
                self.promotion_registry.promotions()
            ),

            "rejection_count":
            len(
                self.rejected_strategies
            )
        }
