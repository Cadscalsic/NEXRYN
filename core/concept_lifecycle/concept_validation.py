# ============================================
# NEXRYN CONCEPT VALIDATION
# ============================================


class ConceptValidation:

    def validate(self, births, context, admission_report=None):

        promotion = context.get(
            "novelty_promotion_gate_report",
            {},
        )

        decisions = {
            item.get(
                "concept",
            ):
            item.get(
                "decision",
                "latent",
            )
            for item in promotion.get(
                "evaluations",
                [],
            )
        }

        admissions = {}

        if isinstance(
            admission_report,
            dict,
        ):

            admissions = {
                item.get(
                    "concept",
                ):
                item.get(
                    "controlled_integration",
                    {},
                ).get(
                    "decision",
                    "historical_reputation_required",
                )
                for item in admission_report.get(
                    "evaluations",
                    [],
                )
            }

        validated = []

        for birth in births.get(
            "births",
            [],
        ):

            concept = birth.get(
                "concept",
            )

            decision = decisions.get(
                concept,
                "latent"
                if birth.get(
                    "viability",
                    0.0,
                )
                >= 0.35
                else "reject",
            )

            admission_decision = admissions.get(
                concept,
                "controlled_integration",
            )

            if admission_decision == "reject":

                decision = "reject"

            elif (
                decision == "promote"
                and admission_decision
                != "controlled_integration"
            ):

                decision = "latent"

            item = dict(
                birth,
            )

            item[
                "admission_decision"
            ] = admission_decision

            item[
                "validation_decision"
            ] = decision

            item[
                "state"
            ] = (
                "validated"
                if decision == "promote"
                else "latent"
                if decision == "latent"
                else "rejected"
            )

            validated.append(
                item,
            )

        return {
            "system":
            "concept_validation",

            "validated_concepts":
            validated,

            "validated_count":
            len([
                item
                for item in validated
                if item.get(
                    "state",
                )
                == "validated"
            ]),

            "latent_count":
            len([
                item
                for item in validated
                if item.get(
                    "state",
                )
                == "latent"
            ]),

            "rejected_count":
            len([
                item
                for item in validated
                if item.get(
                    "state",
                )
                == "rejected"
            ]),
        }
