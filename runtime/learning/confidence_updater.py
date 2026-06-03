# ============================================
# NEXRYN CONFIDENCE UPDATER
# ============================================

from datetime import datetime
import uuid


# ============================================
# CONFIDENCE UPDATER
# ============================================

class ConfidenceUpdater:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # UPDATE HISTORY
        # ====================================

        self.update_history = []

        # ====================================
        # LEARNING CONFIGURATION
        # ====================================

        self.learning_rate = 0.05

        self.minimum_confidence = 0.0

        self.maximum_confidence = 1.0

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "engine_mode":
            "adaptive_confidence_update",

            "adaptive_updates":
            True,

            "normalization":
            True,

            "update_cycles":
            0
        }

    # ========================================
    # NORMALIZE CONFIDENCE
    # ========================================

    def normalize_confidence(

        self,

        confidence
    ):

        # ====================================
        # INVALID TYPES
        # ====================================

        if confidence is None:

            confidence = 0.5

        if not isinstance(

            confidence,

            (int, float)
        ):

            confidence = 0.5

        # ====================================
        # CLAMP VALUES
        # ====================================

        confidence = max(

            self.minimum_confidence,

            confidence
        )

        confidence = min(

            self.maximum_confidence,

            confidence
        )

        return round(
            confidence,
            4
        )

    # ========================================
    # COMPUTE ADAPTIVE RATE
    # ========================================

    def compute_learning_rate(

        self,

        confidence
    ):

        confidence = (

            self.normalize_confidence(
                confidence
            )
        )

        # ====================================
        # ADAPTIVE LEARNING
        # ====================================

        if confidence >= 0.85:

            adaptive_rate = (
                self.learning_rate * 0.5
            )

        elif confidence <= 0.25:

            adaptive_rate = (
                self.learning_rate * 1.5
            )

        else:

            adaptive_rate = (
                self.learning_rate
            )

        return round(
            adaptive_rate,
            4
        )

    # ========================================
    # INCREASE CONFIDENCE
    # ========================================

    def increase_confidence(

        self,

        confidence
    ):

        confidence = (

            self.normalize_confidence(
                confidence
            )
        )

        adaptive_rate = (

            self.compute_learning_rate(
                confidence
            )
        )

        updated = (
            confidence
            + adaptive_rate
        )

        updated = min(

            updated,

            self.maximum_confidence
        )

        return round(
            updated,
            4
        )

    # ========================================
    # DECREASE CONFIDENCE
    # ========================================

    def decrease_confidence(

        self,

        confidence
    ):

        confidence = (

            self.normalize_confidence(
                confidence
            )
        )

        adaptive_rate = (

            self.compute_learning_rate(
                confidence
            )
        )

        updated = (
            confidence
            - adaptive_rate
        )

        updated = max(

            updated,

            self.minimum_confidence
        )

        return round(
            updated,
            4
        )

    # ========================================
    # BUILD UPDATE EVENT
    # ========================================

    def build_update_event(

        self,

        hypothesis_id,

        previous_confidence,

        updated_confidence,

        success
    ):

        return {

            "event_id":
            str(uuid.uuid4()),

            "hypothesis_id":
            hypothesis_id,

            "success":
            success,

            "previous_confidence":
            previous_confidence,

            "updated_confidence":
            updated_confidence,

            "confidence_delta":
            round(

                updated_confidence
                - previous_confidence,

                4
            ),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # UPDATE HYPOTHESES
    # ========================================

    def update_hypotheses(

        self,

        hypotheses,

        success
    ):

        # ====================================
        # NORMALIZATION
        # ====================================

        if hypotheses is None:

            hypotheses = []

        if not isinstance(
            hypotheses,
            list
        ):

            hypotheses = []

        updated_hypotheses = []

        # ====================================
        # UPDATE LOOP
        # ====================================

        for hypothesis in hypotheses:

            # ================================
            # INVALID HYPOTHESIS
            # ================================

            if not isinstance(
                hypothesis,
                dict
            ):

                continue

            current_confidence = (

                hypothesis.get(
                    "confidence",
                    0.5
                )
            )

            current_confidence = (

                self.normalize_confidence(
                    current_confidence
                )
            )

            # ================================
            # SUCCESS
            # ================================

            if success:

                updated_confidence = (

                    self.increase_confidence(
                        current_confidence
                    )
                )

            # ================================
            # FAILURE
            # ================================

            else:

                updated_confidence = (

                    self.decrease_confidence(
                        current_confidence
                    )
                )

            # ================================
            # COPY HYPOTHESIS
            # ================================

            updated_hypothesis = dict(
                hypothesis
            )

            updated_hypothesis[
                "confidence"
            ] = updated_confidence

            updated_hypothesis[
                "last_updated"
            ] = str(
                datetime.utcnow()
            )

            updated_hypothesis[
                "confidence_state"
            ] = (

                "high"

                if updated_confidence >= 0.75

                else

                "moderate"

                if updated_confidence >= 0.4

                else

                "low"
            )

            # ================================
            # UPDATE EVENT
            # ================================

            update_event = (

                self.build_update_event(

                    updated_hypothesis.get(
                        "hypothesis_id",
                        "unknown"
                    ),

                    current_confidence,

                    updated_confidence,

                    success
                )
            )

            updated_hypothesis[
                "update_event"
            ] = update_event

            updated_hypotheses.append(
                updated_hypothesis
            )

            self.update_history.append(
                update_event
            )

        # ====================================
        # UPDATE ENGINE STATE
        # ====================================

        self.engine_state[
            "update_cycles"
        ] += 1

        return updated_hypotheses

    # ========================================
    # GET HISTORY
    # ========================================

    def get_history(self):

        return self.update_history

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "history_size":
            len(
                self.update_history
            ),

            "learning_rate":
            self.learning_rate,

            "minimum_confidence":
            self.minimum_confidence,

            "maximum_confidence":
            self.maximum_confidence
        }


# ============================================
# GLOBAL CONFIDENCE UPDATER
# ============================================

confidence_updater = (
    ConfidenceUpdater()
)