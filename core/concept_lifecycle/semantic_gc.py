# ============================================
# NEXRYN SEMANTIC GARBAGE COLLECTOR
# ============================================


class SemanticGarbageCollector:

    DEAD_STATES = [
        "retired",
        "rejected",
        "extinct",
    ]

    def should_collect(self, record):

        state = record.get(
            "state",
            "unknown",
        )

        activation = record.get(
            "activation",
            record.get(
                "viability",
                0.0,
            ),
        )

        utility = record.get(
            "semantic_utility",
            0.0,
        )

        maintenance = record.get(
            "maintenance_cost",
            0.0,
        )

        concept = str(
            record.get(
                "concept",
                "",
            )
        )

        if state in self.DEAD_STATES and activation < 0.18:

            return "dead_concept"

        if (
            "bridge" in concept
            and state in [
                "decaying",
                "retired",
                "rejected",
            ]
            and utility < maintenance
        ):

            return "weak_bridge"

        if (
            record.get(
                "energy_state",
            )
            == "unsustainable"
            and utility < 0.18
        ):

            return "failed_overlap"

        return None

    def collect(self, concept_registry, context=None):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        revival_candidates = set()

        for item in context.get(
            "active_concept_decay_report",
            {},
        ).get(
            "activation_state",
            [],
        ):

            concept = item.get(
                "concept",
            )

            if concept is not None:

                revival_candidates.add(
                    f"concept:{concept}",
                )

        collected = []
        weak_bridges_removed = []
        lineage_cleaned = []

        for concept_id, record in list(
            concept_registry.items()
        ):

            if concept_id in revival_candidates:

                continue

            lineage = record.get(
                "lineage",
                [],
            )

            if lineage:

                cleaned_lineage = [
                    item
                    for item in lineage
                    if item in concept_registry
                ]

                if len(
                    cleaned_lineage,
                ) != len(
                    lineage,
                ):

                    record[
                        "lineage"
                    ] = cleaned_lineage

                    lineage_cleaned.append(
                        concept_id,
                    )

            reason = self.should_collect(
                record,
            )

            if reason is None:

                continue

            removed = concept_registry.pop(
                concept_id,
            )

            collected.append({
                "concept_id":
                concept_id,

                "concept":
                removed.get(
                    "concept",
                    concept_id,
                ),

                "reason":
                reason,
            })

            if reason == "weak_bridge":

                weak_bridges_removed.append(
                    concept_id,
                )

        entropy_reduction_estimate = round(
            min(
                1.0,
                len(
                    collected,
                )
                * 0.035
                +
                len(
                    lineage_cleaned,
                )
                * 0.01,
            ),
            4,
        )

        return {
            "system":
            "semantic_gc",

            "mode":
            "constructive_forgetting",

            "collected_concepts":
            collected,

            "collected_count":
            len(
                collected,
            ),

            "weak_bridges_removed":
            weak_bridges_removed,

            "lineage_cleaned":
            lineage_cleaned,

            "entropy_reduction_estimate":
            entropy_reduction_estimate,
        }
