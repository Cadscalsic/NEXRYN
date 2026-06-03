# ============================================
# NEXRYN COGNITIVE IMMUNE ENGINE
# ============================================


def _clamp(value):

    try:
        value = float(
            value,
        )
    except Exception:
        value = 0.0

    return round(
        max(
            0.0,
            min(
                value,
                1.0,
            ),
        ),
        4,
    )


class CognitiveImmuneEngine:

    def cognitive_fever(self, context):

        memory_pressure = _clamp(
            context.get(
                "memory_pressure_score",
                0.0,
            )
        )
        repair_count = context.get(
            "repair_required_count",
            0,
        )
        identity_drift = _clamp(
            context.get(
                "identity_drift",
                0.0,
            )
        )

        fever_score = _clamp(
            (
                memory_pressure
                * 0.5
            )
            +
            min(
                repair_count / 240,
                1.0,
            )
            * 0.3
            +
            identity_drift
            * 0.2
        )

        return {
            "fever_score":
            fever_score,

            "cognitive_fever_state":
            (
                "cognitive_fever"
                if fever_score >= 0.72
                else "immune_watch"
                if fever_score >= 0.42
                else "immune_calm"
            ),
        }

    def semantic_quarantine(self, context, fever_report):

        court = context.get(
            "semantic_court_report",
            {},
        )

        quarantine = (
            fever_report.get(
                "cognitive_fever_state",
            )
            == "cognitive_fever"
            or court.get(
                "court_state",
            )
            == "semantic_injunction"
        )

        return {
            "quarantine_active":
            quarantine,

            "quarantine_scope":
            (
                [
                    "fusion",
                    "direct_core_merge",
                    "unverified_mutation",
                ]
                if quarantine
                else []
            ),
        }

    def mutation_immunity(self, context):

        rehearsal = context.get(
            "constitutional_rehearsal_report",
            {},
        )

        verified = rehearsal.get(
            "constitutional_verification",
            {},
        ).get(
            "verified",
            False,
        )

        return {
            "verified_by_rehearsal":
            verified,

            "mutation_immunity_state":
            (
                "mutation_allowed_under_immunity"
                if verified
                else "mutation_requires_rehearsal"
            ),
        }

    def drift_suppression(self, context):

        drift = _clamp(
            context.get(
                "identity_drift",
                context.get(
                    "semantic_drift",
                    0.0,
                ),
            )
        )

        return {
            "drift_score":
            drift,

            "drift_suppression_active":
            drift >= 0.55,
        }

    def collapse_prediction(self, fever_report, quarantine_report):

        risk = _clamp(
            fever_report.get(
                "fever_score",
                0.0,
            )
            +
            (
                0.18
                if quarantine_report.get(
                    "quarantine_active",
                    False,
                )
                else 0.0
            )
        )

        return {
            "collapse_risk":
            risk,

            "collapse_prediction_state":
            (
                "collapse_risk_high"
                if risk >= 0.82
                else "collapse_risk_watch"
                if risk >= 0.52
                else "collapse_risk_low"
            ),
        }

    def run_cycle(self, context):

        fever = self.cognitive_fever(
            context,
        )
        quarantine = self.semantic_quarantine(
            context,
            fever,
        )
        immunity = self.mutation_immunity(
            context,
        )
        drift = self.drift_suppression(
            context,
        )
        collapse = self.collapse_prediction(
            fever,
            quarantine,
        )

        return {
            "system":
            "cognitive_immune_engine",

            "cognitive_fever":
            fever,

            "semantic_quarantine":
            quarantine,

            "mutation_immunity":
            immunity,

            "drift_suppression":
            drift,

            "collapse_prediction":
            collapse,

            "immune_state":
            (
                "immune_emergency"
                if quarantine.get(
                    "quarantine_active",
                    False,
                )
                or collapse.get(
                    "collapse_prediction_state",
                )
                == "collapse_risk_high"
                else "immune_monitoring"
            ),
        }


cognitive_immune_engine = CognitiveImmuneEngine()
