# ============================================
# NEXRYN CONCEPT DECAY
# ============================================


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


class ConceptDecay:

    def decay(self, concept_registry):

        decayed = []

        for concept_id, record in concept_registry.items():

            updated = dict(
                record,
            )

            if updated.get(
                "state",
            ) in [
                "retired",
                "rejected",
            ]:

                decayed.append(
                    updated,
                )

                continue

            updated[
                "activation"
            ] = _clamp(
                updated.get(
                    "activation",
                    updated.get(
                        "viability",
                        0.0,
                    ),
                )
                -
                0.08
            )

            if updated[
                "activation"
            ] < 0.20 and updated.get(
                "state",
            ) != "validated":

                updated[
                    "state"
                ] = "decaying"

            concept_registry[
                concept_id
            ] = updated

            decayed.append(
                updated,
            )

        return {
            "system":
            "concept_decay",

            "decayed_concepts":
            decayed,

            "decaying_count":
            len([
                item
                for item in decayed
                if item.get(
                    "state",
                )
                == "decaying"
            ]),
        }
