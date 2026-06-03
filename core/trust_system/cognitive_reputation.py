# ============================================
# NEXRYN COGNITIVE REPUTATION
# ============================================

from datetime import datetime


MAX_REPUTATION_EVENTS = 32


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


class CognitiveReputation:

    def __init__(self):

        self.reputation_registry = {}

    def _event_key(self, event):

        source = event.get(
            "source",
            {},
        )

        first = source.get(
            "first",
            source.get(
                "concept",
                "unknown",
            ),
        )

        second = source.get(
            "second",
            source.get(
                "canonical_concept",
                "none",
            ),
        )

        return (
            event.get(
                "event_type",
                "unknown",
            ),
            str(
                first,
            ),
            str(
                second,
            ),
        )

    def evaluate(self, context, trust_report):

        firewall = context.get(
            "semantic_firewall_report",
            {},
        )

        sandbox = firewall.get(
            "concept_sandboxing",
            {},
        )

        events = sandbox.get(
            "sandboxed_events",
            [],
        )

        default_score = _clamp(
            trust_report.get(
                "trust_score",
                0.0,
            )
            * 0.70
            +
            0.15
        )

        legitimacy = context.get(
            "semantic_legitimacy_report",
            {},
        )

        constructive_bonus = _clamp(
            legitimacy.get(
                "evidence_exports",
                {},
            ).get(
                "constructive_mutation_score",
                0.0,
            )
            * 0.12
            +
            legitimacy.get(
                "semantic_legitimacy_score",
                0.0,
            )
            * 0.08
        )

        event_reputations = []

        for event in events:

            key = self._event_key(
                event,
            )

            current = self.reputation_registry.get(
                key,
                default_score,
            )

            policy = event.get(
                "sandbox_policy",
                "observe_only",
            )

            penalty = (
                0.10
                if policy == "deny_commit"
                else 0.04
                if policy == "quarantine_then_review"
                else 0.0
            )

            updated = _clamp(
                current * 0.82
                +
                default_score * 0.18
                +
                constructive_bonus
                -
                penalty
            )

            self.reputation_registry[
                key
            ] = updated

            event_reputations.append({
                "event_key":
                list(
                    key,
                ),

                "reputation":
                updated,

                "sandbox_policy":
                policy,
            })

        average_reputation = _clamp(
            sum(
                item.get(
                    "reputation",
                    0.0,
                )
                for item in event_reputations
            )
            /
            max(
                len(
                    event_reputations,
                ),
                1,
            )
            if event_reputations
            else default_score
        )

        return {
            "system":
            "cognitive_reputation",

            "average_reputation":
            average_reputation,

            "event_reputations":
            event_reputations[:MAX_REPUTATION_EVENTS],

            "registry_size":
            len(
                self.reputation_registry,
            ),

            "constructive_bonus":
            constructive_bonus,

            "reputation_state":
            (
                "established"
                if average_reputation >= 0.68
                else "forming"
                if average_reputation >= 0.36
                else "weak"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
