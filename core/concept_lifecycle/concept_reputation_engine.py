# ============================================
# NEXRYN CONCEPT REPUTATION ENGINE
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class ConceptReputationEngine:

    def __init__(self):

        self.reputation_registry = {}

    def _concept_key(self, concept):

        return f"concept:{concept}"

    def _events_for(self, concept, context):

        events = []

        explicit = context.get(
            "concept_reputation_events",
            [],
        )

        for event in explicit:

            if event.get(
                "concept",
            ) == concept:

                events.append(
                    event,
                )

        for evaluation in context.get(
            "novelty_promotion_gate_report",
            {},
        ).get(
            "evaluations",
            [],
        ):

            if evaluation.get(
                "concept",
            ) == concept:

                events.append({
                    "event_type":
                    "promotion_evaluation",

                    "historical_consistency":
                    evaluation.get(
                        "average_identity_continuity",
                        0.0,
                    ),

                    "long_term_usefulness":
                    evaluation.get(
                        "average_execution_usefulness",
                        0.0,
                    ),

                    "contradiction":
                    evaluation.get(
                        "decision",
                    )
                    == "reject",
                })

        return events

    def _metric_average(self, events, key, default):

        values = [
            _clamp(
                event.get(
                    key,
                    default,
                )
            )
            for event in events
            if key in event
        ]

        if not values:

            return _clamp(
                default,
            )

        return _clamp(
            sum(
                values,
            )
            /
            len(
                values,
            )
        )

    def evaluate_concept(self, concept, concept_registry, context):

        concept_id = self._concept_key(
            concept,
        )

        record = concept_registry.get(
            concept_id,
            {},
        )

        prior = self.reputation_registry.get(
            concept_id,
            record.get(
                "concept_reputation",
                {},
            ),
        )

        events = self._events_for(
            concept,
            context,
        )

        viability = _clamp(
            record.get(
                "viability",
                0.0,
            )
        )

        activation = _clamp(
            record.get(
                "activation",
                viability,
            )
        )

        historical_consistency = self._metric_average(
            events,
            "historical_consistency",
            prior.get(
                "historical_consistency",
                activation,
            ),
        )

        causal_reliability = self._metric_average(
            events,
            "causal_reliability",
            prior.get(
                "causal_reliability",
                viability,
            ),
        )

        long_term_usefulness = self._metric_average(
            events,
            "long_term_usefulness",
            prior.get(
                "long_term_usefulness",
                record.get(
                    "semantic_utility",
                    viability,
                ),
            ),
        )

        contradiction_events = len([
            event
            for event in events
            if event.get(
                "contradiction",
                False,
            )
        ])

        contradiction_history = _clamp(
            prior.get(
                "contradiction_history",
                0.0,
            )
            * 0.80
            +
            min(
                1.0,
                contradiction_events / 3,
            )
            * 0.20
        )

        recovery_success = self._metric_average(
            events,
            "recovery_success",
            prior.get(
                "recovery_success",
                0.0,
            ),
        )

        failure_propagation_score = self._metric_average(
            events,
            "failure_propagation_score",
            prior.get(
                "failure_propagation_score",
                0.0,
            ),
        )

        reputation = _clamp(
            historical_consistency * 0.22
            +
            causal_reliability * 0.24
            +
            long_term_usefulness * 0.22
            +
            recovery_success * 0.12
            +
            (1.0 - contradiction_history) * 0.10
            +
            (1.0 - failure_propagation_score) * 0.10
        )

        report = {
            "concept_id":
            concept_id,

            "concept":
            concept,

            "historical_consistency":
            historical_consistency,

            "causal_reliability":
            causal_reliability,

            "long_term_usefulness":
            long_term_usefulness,

            "contradiction_history":
            contradiction_history,

            "recovery_success":
            recovery_success,

            "failure_propagation_score":
            failure_propagation_score,

            "reputation":
            reputation,

            "reputation_state":
            (
                "established"
                if reputation >= 0.68
                else "forming"
                if reputation >= 0.36
                else "weak"
            ),

            "event_count":
            len(
                events,
            ),
        }

        self.reputation_registry[
            concept_id
        ] = report

        if concept_id in concept_registry:

            concept_registry[
                concept_id
            ][
                "concept_reputation"
            ] = report

            concept_registry[
                concept_id
            ][
                "reputation"
            ] = reputation

        return report

    def evaluate(self, births, concept_registry, context):

        concepts = []

        for birth in births.get(
            "births",
            [],
        ):

            concept = birth.get(
                "concept",
            )

            if concept is not None:

                concepts.append(
                    concept,
                )

        for record in concept_registry.values():

            concept = record.get(
                "concept",
            )

            if concept is not None:

                concepts.append(
                    concept,
                )

        seen = []
        reports = []

        for concept in concepts:

            if concept in seen:

                continue

            seen.append(
                concept,
            )

            reports.append(
                self.evaluate_concept(
                    concept,
                    concept_registry,
                    context,
                )
            )

        average_reputation = _clamp(
            sum(
                report.get(
                    "reputation",
                    0.0,
                )
                for report in reports
            )
            /
            max(
                len(
                    reports,
                ),
                1,
            )
        )

        return {
            "system":
            "concept_reputation_engine",

            "concept_reputations":
            reports,

            "concept_count":
            len(
                reports,
            ),

            "average_concept_reputation":
            average_reputation,

            "reputation_state":
            (
                "epistemically_established"
                if average_reputation >= 0.68
                else "epistemically_forming"
                if average_reputation >= 0.36
                else "epistemically_weak"
            ),

            "epistemic_constraints":
            {
                "high_reputation_is_not_truth":
                True,

                "reputation_cannot_commit_truth":
                True,
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
