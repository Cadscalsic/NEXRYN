# ============================================
# NEXRYN CONCEPT RETIREMENT
# ============================================


class ConceptRetirement:

    def retire(self, concept_registry):

        retired = []

        for concept_id, record in concept_registry.items():

            if record.get(
                "state",
            ) == "decaying" and record.get(
                "activation",
                0.0,
            ) < 0.12:

                record[
                    "state"
                ] = "retired"

                retired.append(
                    record,
                )

        return {
            "system":
            "concept_retirement",

            "retired_concepts":
            retired,

            "retired_count":
            len(
                retired,
            ),
        }
