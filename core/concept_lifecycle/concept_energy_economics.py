# ============================================
# NEXRYN CONCEPT ENERGY ECONOMICS
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


class ConceptEnergyEconomics:

    def evaluate(self, concept_registry):

        evaluated = []

        for concept_id, record in concept_registry.items():

            activation = _clamp(
                record.get(
                    "activation",
                    record.get(
                        "viability",
                        0.0,
                    ),
                )
            )

            viability = _clamp(
                record.get(
                    "viability",
                    activation,
                )
            )

            lineage_weight = _clamp(
                len(
                    record.get(
                        "lineage",
                        [],
                    )
                )
                * 0.03
            )

            bridge_weight = (
                0.10
                if "bridge" in str(
                    record.get(
                        "concept",
                        concept_id,
                    )
                )
                else 0.0
            )

            state = record.get(
                "state",
                "unknown",
            )

            state_penalty = (
                0.18
                if state in [
                    "retired",
                    "rejected",
                ]
                else 0.08
                if state == "decaying"
                else 0.0
            )

            survival_cost = _clamp(
                0.10
                +
                bridge_weight
                +
                lineage_weight
                +
                state_penalty
            )

            maintenance_cost = _clamp(
                survival_cost
                +
                max(
                    0.0,
                    0.35 - activation,
                )
                * 0.35
            )

            semantic_utility = _clamp(
                viability * 0.45
                +
                activation * 0.45
                +
                (
                    0.10
                    if state == "validated"
                    else 0.04
                    if state == "latent"
                    else 0.0
                )
                -
                state_penalty * 0.25
            )

            record[
                "survival_cost"
            ] = survival_cost

            record[
                "maintenance_cost"
            ] = maintenance_cost

            record[
                "semantic_utility"
            ] = semantic_utility

            record[
                "energy_state"
            ] = (
                "unsustainable"
                if maintenance_cost > semantic_utility + 0.20
                else "expensive"
                if maintenance_cost > semantic_utility
                else "viable"
            )

            evaluated.append({
                "concept_id":
                concept_id,

                "concept":
                record.get(
                    "concept",
                    concept_id,
                ),

                "survival_cost":
                survival_cost,

                "maintenance_cost":
                maintenance_cost,

                "semantic_utility":
                semantic_utility,

                "energy_state":
                record[
                    "energy_state"
                ],
            })

        unsustainable_count = len([
            item
            for item in evaluated
            if item.get(
                "energy_state",
            )
            == "unsustainable"
        ])

        return {
            "system":
            "concept_energy_economics",

            "evaluated_concepts":
            evaluated,

            "evaluated_count":
            len(
                evaluated,
            ),

            "unsustainable_count":
            unsustainable_count,
        }
