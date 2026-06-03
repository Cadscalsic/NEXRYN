# ============================================
# NEXRYN SEMANTIC COURT
# ============================================


def _score(value):

    try:
        return max(
            0.0,
            min(
                float(
                    value,
                ),
                1.0,
            ),
        )
    except Exception:
        return 0.0


class SemanticCourt:

    def constitutional_review(self, context):

        constitutional = context.get(
            "constitutional_runtime_report",
            {},
        )

        violations = constitutional.get(
            "cognitive_constitution",
            {},
        ).get(
            "violations",
            [],
        )

        return {
            "violations":
            violations,

            "review_state":
            (
                "constitutional_objection"
                if violations
                else "constitutionally_clear"
            ),
        }

    def merge_legality(self, context):

        judiciary = context.get(
            "constitutional_runtime_report",
            {},
        ).get(
            "semantic_judiciary",
            {},
        )

        verdict = judiciary.get(
            "verdicts",
            {},
        ).get(
            "merge_legality",
            "illegal_or_deferred",
        )

        requested_action = context.get(
            "requested_action",
            "governed_runtime_cycle",
        )

        rehearsal = context.get(
            "constitutional_rehearsal_report",
            {},
        )

        direct_core_merge_blocked = (
            requested_action == "direct_core_merge"
            and not rehearsal.get(
                "constitutional_verification",
                {},
            ).get(
                "direct_core_merge_allowed",
                False,
            )
        )

        return {
            "merge_verdict":
            (
                "illegal_direct_core_merge"
                if direct_core_merge_blocked
                else verdict
            ),

            "merge_allowed":
            verdict == "legal"
            and not direct_core_merge_blocked,

            "direct_core_merge_blocked":
            direct_core_merge_blocked,
        }

    def mutation_legality(self, context):

        judiciary = context.get(
            "constitutional_runtime_report",
            {},
        ).get(
            "semantic_judiciary",
            {},
        )

        verdict = judiciary.get(
            "verdicts",
            {},
        ).get(
            "mutation_legality",
            "illegal_or_deferred",
        )

        return {
            "mutation_verdict":
            verdict,

            "mutation_allowed":
            verdict == "legal",
        }

    def causal_ethics(self, context):

        legitimacy = context.get(
            "semantic_legitimacy_report",
            {},
        )

        causal_score = _score(
            legitimacy.get(
                "evidence_exports",
                {},
            ).get(
                "causal_attestation_score",
                0.0,
            )
        )

        return {
            "causal_attestation_score":
            round(
                causal_score,
                4,
            ),

            "causal_ethics_state":
            (
                "causally_ethical"
                if causal_score >= 0.5
                else "causal_ethics_unproven"
            ),
        }

    def adjudicate(self, context):

        review = self.constitutional_review(
            context,
        )
        merge = self.merge_legality(
            context,
        )
        mutation = self.mutation_legality(
            context,
        )
        ethics = self.causal_ethics(
            context,
        )

        blocking_findings = [
            review.get(
                "review_state",
            ) == "constitutional_objection",
            not merge.get(
                "merge_allowed",
                False,
            ),
            not mutation.get(
                "mutation_allowed",
                False,
            ),
            ethics.get(
                "causal_ethics_state",
            ) == "causal_ethics_unproven",
        ]

        return {
            "system":
            "semantic_court",

            "constitutional_review":
            review,

            "merge_legality":
            merge,

            "mutation_legality":
            mutation,

            "causal_ethics":
            ethics,

            "court_state":
            (
                "semantic_injunction"
                if any(
                    blocking_findings,
                )
                else "semantic_court_clearance"
            ),
        }


semantic_court = SemanticCourt()
