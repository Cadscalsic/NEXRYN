# ============================================
# NEXRYN CONCEPT REVIVAL
# ============================================


class ConceptRevival:

    def revive(self, concept_registry, context):

        active_names = {
            item.get(
                "concept",
            )
            for item in context.get(
                "active_concept_decay_report",
                {},
            ).get(
                "activation_state",
                [],
            )
        }

        revived = []

        for concept_id, record in concept_registry.items():

            if record.get(
                "state",
            ) in [
                "retired",
                "decaying",
            ] and record.get(
                "concept",
            ) in active_names:

                record[
                    "state"
                ] = "revived"

                record[
                    "activation"
                ] = max(
                    record.get(
                        "activation",
                        0.0,
                    ),
                    0.35,
                )

                revived.append(
                    record,
                )

        return {
            "system":
            "concept_revival",

            "revived_concepts":
            revived,

            "revived_count":
            len(
                revived,
            ),
        }
