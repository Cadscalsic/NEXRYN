# ============================================
# NEXRYN CONCEPT LINEAGE
# ============================================

from datetime import datetime

from core.cognition.recursive_guardian import (
    recursive_guardian,
)

from core.cognition.mutation_firewall import (
    mutation_firewall,
)


MAX_MUTATIONS_PER_CONCEPT = 8
MAX_LOG_ITEMS_PER_SECTION = 20
MAX_REPUTATION_EVENTS = 32


class ConceptLineage:

    def __init__(self):

        self.lineage_records = {}
        self.lineage_history = []
        self.recursive_guardian = recursive_guardian
        self.mutation_firewall = mutation_firewall

    def _concept_id(self, concept):

        return concept.get(
            "concept_id",
            concept.get(
                "meta_concept_id",
                concept.get(
                    "concept",
                    concept.get(
                        "id",
                        "unknown_concept",
                    ),
                ),
            ),
        )

    def _record(self, concept_id, origin, parents=None, mutations=None):

        if parents is None:

            parents = []

        if mutations is None:

            mutations = []

        mutations = mutations[
            :MAX_MUTATIONS_PER_CONCEPT
        ]

        existing = self.lineage_records.get(
            concept_id,
            {},
        )

        existing_mutations = existing.get(
            "mutations",
            [],
        )[
            :MAX_MUTATIONS_PER_CONCEPT
        ]

        existing_keys = {
            (
                mutation.get(
                    "type",
                ),
                mutation.get(
                    "fusion_stability",
                ),
                mutation.get(
                    "primitive",
                ),
                mutation.get(
                    "survival_state",
                ),
                mutation.get(
                    "recovery_action",
                ),
            )
            for mutation in existing_mutations
        }

        deduped_mutations = []

        for mutation in mutations:

            if not self.mutation_firewall.allow(
                concept_id,
                mutation,
            ):

                continue

            event_key = (
                mutation.get(
                    "type",
                ),
                mutation.get(
                    "fusion_stability",
                ),
                mutation.get(
                    "primitive",
                ),
                mutation.get(
                    "survival_state",
                ),
                mutation.get(
                    "recovery_action",
                ),
            )

            if event_key in existing_keys:

                continue

            existing_keys.add(
                event_key,
            )

            deduped_mutations.append(
                mutation,
            )

            if (
                len(
                    existing_mutations,
                )
                +
                len(
                    deduped_mutations,
                )
                >= MAX_MUTATIONS_PER_CONCEPT
            ):

                break

        record = {
            "concept_id":
            concept_id,

            "origin":
            existing.get(
                "origin",
                origin,
            ),

            "parents":
            sorted(
                set(
                    existing.get(
                        "parents",
                        [],
                    )
                    +
                    parents
                )
            ),

            "mutations":
            (
                existing_mutations
                +
                deduped_mutations
            )[
                :MAX_MUTATIONS_PER_CONCEPT
            ],

            "generation":
            max(
                existing.get(
                    "generation",
                    0,
                ),
                1
                +
                len(
                    parents,
                ),
            ),

            "updated_at":
            str(
                datetime.utcnow()
            ),
        }

        cycle_guard = self.recursive_guardian.graph_cycle_breaker(
            record,
            list(
                self.lineage_records.values()
            ),
        )

        record = cycle_guard.get(
            "record",
            record,
        )

        if cycle_guard.get(
            "removed_edges",
            [],
        ):

            record[
                "cycle_breaks"
            ] = (
                existing.get(
                    "cycle_breaks",
                    [],
                )
                +
                cycle_guard.get(
                    "removed_edges",
                    [],
                )
            )

        self.lineage_records[
            concept_id
        ] = record

        return record

    def track_generated_concepts(self, context):

        records = []

        for concept in context.get(
            "conceptive_neurogenesis_report",
            {},
        ).get(
            "generated_concepts",
            [],
        ):

            if not isinstance(
                concept,
                dict,
            ):

                concept = {
                    "concept":
                    concept,
                }

            records.append(
                self._record(
                    self._concept_id(
                        concept,
                    ),
                    "conceptive_neurogenesis",
                    mutations=[
                        {
                            "type":
                            "birth",

                            "source":
                            "conceptive_neurogenesis",
                        },
                    ],
                )
            )

        return records

    def track_semantic_graph_concepts(self, context):

        records = []

        for concept in context.get(
            "semantic_graph",
            {},
        ).get(
            "concept_nodes",
            [],
        ):

            if not isinstance(
                concept,
                dict,
            ):

                continue

            records.append(
                self._record(
                    self._concept_id(
                        concept,
                    ),
                    "semantic_graph",
                    parents=[],
                    mutations=[
                        {
                            "type":
                            "semantic_observation",

                            "primitive":
                            concept.get(
                                "primitive",
                                "unknown",
                            ),
                        },
                    ],
                )
            )

        return records

    def track_fused_concepts(self, context):

        records = []

        for fusion in context.get(
            "concept_fusion_report",
            {},
        ).get(
            "fused_concepts",
            [],
        )[
            :MAX_LOG_ITEMS_PER_SECTION
        ]:

            meta = fusion.get(
                "meta_concept",
                {},
            )

            concept_id = self._concept_id(
                meta,
            )

            parents = meta.get(
                "source_concepts",
                [],
            )

            records.append(
                self._record(
                    concept_id,
                    "concept_fusion",
                    parents=parents,
                    mutations=[
                        {
                            "type":
                            "fusion",

                            "fusion_stability":
                            fusion.get(
                                "fusion_stability",
                                meta.get(
                                    "fusion_stability",
                                    0.0,
                                ),
                            ),
                        },
                    ],
                )
            )

        return records

    def track_recovered_concepts(self, context):

        records = []

        for trait in context.get(
            "trait_recovery_report",
            {},
        ).get(
            "recovered_traits",
            [],
        )[
            :MAX_LOG_ITEMS_PER_SECTION
        ]:

            concept_id = self._concept_id(
                trait,
            )

            records.append(
                self._record(
                    concept_id,
                    "trait_recovery",
                    parents=trait.get(
                        "source_concepts",
                        [],
                    ),
                    mutations=[
                        {
                            "type":
                            "resurrection",

                            "resurrection_score":
                            trait.get(
                                "resurrection_score",
                                0.0,
                            ),
                        },
                    ],
                )
            )

        return records

    def track_evolved_hypotheses(self, context):

        records = []

        evolved = context.get(
            "evolved_hypotheses",
            [],
        )

        if isinstance(
            evolved,
            dict,
        ):

            evolved = [
                evolved,
            ]

        for hypothesis in evolved:

            if not isinstance(
                hypothesis,
                dict,
            ):

                continue

            concept_id = self._concept_id(
                {
                    "concept":
                    hypothesis.get(
                        "type",
                        hypothesis.get(
                            "concept",
                            "unknown_concept",
                        ),
                    ),
                }
            )

            parent = hypothesis.get(
                "parent_strategy",
            )

            records.append(
                self._record(
                    concept_id,
                    "strategy_evolution",
                    parents=[
                        parent,
                    ]
                    if parent
                    else [],
                    mutations=[
                        {
                            "type":
                            "strategy_evolution",

                            "primitive":
                            hypothesis.get(
                                "primitive",
                                "unknown",
                            ),

                            "confidence":
                            hypothesis.get(
                                "confidence",
                                0.0,
                            ),
                        },
                    ],
                )
            )

        return records

    def track_failure_memory(self, context):

        latest_failure = context.get(
            "cognitive_failure_memory",
            {},
        ).get(
            "latest_failure",
            {},
        )

        collapse_source = latest_failure.get(
            "collapse_source",
            "",
        )

        if "::" not in collapse_source:

            return []

        left, right = collapse_source.split(
            "::",
            1,
        )

        records = []

        records.append(
            self._record(
                right,
                "unsafe_merge_failure",
                parents=[
                    left,
                ],
                mutations=[
                    {
                        "type":
                        latest_failure.get(
                            "contradiction_type",
                            "unsafe_merge",
                        ),

                        "ontology_damage":
                        latest_failure.get(
                            "ontology_damage",
                            0.0,
                        ),

                        "recovery_action":
                        latest_failure.get(
                            "recovery_action",
                            "unknown",
                        ),
                    },
                ],
            )
        )

        return records

    def track_mutation_lineage(self, context):

        records = []

        lineages = (
            context.get(
                "evolutionary_memory_report",
                {},
            ).get(
                "mutation_lineage",
                {},
            ).get(
                "lineage_records",
                context.get(
                    "evolutionary_memory_report",
                    {},
                ).get(
                    "mutation_lineage",
                    {},
                ).get(
                    "lineages",
                    [],
                ),
            )
        )

        for lineage in lineages:

            if len(
                records,
            ) >= MAX_LOG_ITEMS_PER_SECTION:

                break

            if not isinstance(
                lineage,
                dict,
            ):

                continue

            concept_id = self._concept_id(
                lineage,
            )

            records.append(
                self._record(
                    concept_id,
                    "mutation_lineage",
                    parents=lineage.get(
                        "parents",
                        lineage.get(
                            "source_concepts",
                            [],
                        ),
                    ),
                    mutations=[
                        {
                            "type":
                            lineage.get(
                                "mutation_type",
                                "mutation",
                            ),

                            "survival_state":
                            lineage.get(
                                "survival_state",
                                "unknown",
                            ),
                        },
                    ],
                )
            )

        return records

    def ancestry_for(self, concept_id, visited=None, depth=0):

        if visited is None:

            visited = set()

        cached = self.recursive_guardian.ancestry_cache_guard(
            concept_id,
        )

        if cached is not None and depth == 0:

            return cached

        if concept_id in visited:

            return {
                "concept_id":
                concept_id,

                "ancestors":
                [],

                "cycle_detected":
                True,

                "depth":
                depth,
            }

        if depth >= self.recursive_guardian.max_depth:

            return {
                "concept_id":
                concept_id,

                "ancestors":
                [],

                "cycle_detected":
                False,

                "depth":
                depth,

                "depth_limited":
                True,
            }

        visited.add(
            concept_id,
        )

        record = self.lineage_records.get(
            concept_id,
            {},
        )

        parents = record.get(
            "parents",
            [],
        )

        ancestors = []
        cycle_detected = False
        max_depth = depth

        for parent in parents:

            ancestors.append(
                parent,
            )

            parent_report = self.ancestry_for(
                parent,
                set(
                    visited,
                ),
                depth + 1,
            )

            cycle_detected = (
                cycle_detected
                or parent_report.get(
                    "cycle_detected",
                    False,
                )
            )

            max_depth = max(
                max_depth,
                parent_report.get(
                    "depth",
                    depth,
                ),
            )

            ancestors.extend(
                parent_report.get(
                    "ancestors",
                    [],
                )
            )

        report = {
            "concept_id":
            concept_id,

            "ancestors":
            sorted(
                set(
                    ancestors,
                )
            ),

            "cycle_detected":
            cycle_detected,

            "depth":
            max_depth,
        }

        if depth == 0:

            self.recursive_guardian.ancestry_cache_guard(
                concept_id,
                report,
            )

        return report

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        generated = self.track_generated_concepts(
            context,
        )
        semantic_graph_records = self.track_semantic_graph_concepts(
            context,
        )
        fused = self.track_fused_concepts(
            context,
        )
        recovered = self.track_recovered_concepts(
            context,
        )
        evolved = self.track_evolved_hypotheses(
            context,
        )
        failure_records = self.track_failure_memory(
            context,
        )
        mutation_records = self.track_mutation_lineage(
            context,
        )

        records = list(
            self.lineage_records.values()
        )[
            -MAX_LOG_ITEMS_PER_SECTION:
        ]

        recursive_safety_report = (
            self.recursive_guardian
            .self_reference_safety(records)
        )

        ancestry = [
            self.ancestry_for(
                record.get(
                    "concept_id",
                )
            )
            for record in records
        ]

        report = {
            "system":
            "concept_lineage",

            "lineage_mode":
            "cognitive_ancestry_tracking",

            "generated_records":
            generated[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "semantic_graph_records":
            semantic_graph_records[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "fused_records":
            fused[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "recovered_records":
            recovered[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "evolved_records":
            evolved[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "failure_records":
            failure_records[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "mutation_records":
            mutation_records[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "lineage_records":
            records,

            "recursive_safety":
            recursive_safety_report,

            "ancestry":
            ancestry[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "lineage_count":
            len(
                records,
            ),

            "lineage_state":
            (
                "cyclic_lineage_blocked"
                if recursive_safety_report.get(
                    "self_reference_state",
                )
                == "recursive_safety_intervention"
                else
                "cognitive_ancestry_tracked"
                if records
                else "no_concept_lineage_observed"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.lineage_history.append(
            report,
        )

        self.lineage_history = (
            self.lineage_history[-128:]
        )

        return report


concept_lineage = ConceptLineage()
