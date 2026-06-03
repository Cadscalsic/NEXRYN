# ============================================
# NEXRYN MEMORY COMPRESSION LAYER
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


class MemoryCompressionLayer:

    def __init__(self, max_items_per_trace=6):

        self.max_items_per_trace = max_items_per_trace
        self.compression_history = []

    def _take_recent(self, items):

        if not isinstance(
            items,
            list,
        ):

            return []

        return items[
            -self.max_items_per_trace:
        ]

    def importance_decay(self, item, index, total):

        recency = _clamp(
            (
                index
                + 1
            )
            /
            max(
                total,
                1,
            )
        )

        explicit_importance = _clamp(
            item.get(
                "importance",
                item.get(
                    "fitness",
                    item.get(
                        "semantic_alignment",
                        item.get(
                            "constructive_score",
                            0.5,
                        ),
                    ),
                ),
            )
            if isinstance(
                item,
                dict,
            )
            else 0.4
        )

        return _clamp(
            explicit_importance * 0.62
            +
            recency * 0.38
        )

    def semantic_compression(self, items, label):

        if not isinstance(
            items,
            list,
        ):

            items = []

        total = len(
            items,
        )

        scored = []

        for index, item in enumerate(
            items,
        ):

            importance = self.importance_decay(
                item,
                index,
                total,
            )

            if isinstance(
                item,
                dict,
            ):

                scored.append({
                    "importance":
                    importance,

                    "item":
                    item,
                })

        selected = sorted(
            scored,
            key=lambda entry: entry.get(
                "importance",
                0.0,
            ),
            reverse=True,
        )[
            :self.max_items_per_trace
        ]

        selected_items = [
            entry.get(
                "item",
                {},
            )
            for entry in selected
        ]

        semantic_keys = []

        for item in selected_items:

            for key in [
                "id",
                "trait_id",
                "niche",
                "trait_state",
                "reason",
                "event_type",
                "decision",
                "reputation_state",
            ]:

                value = item.get(
                    key,
                )

                if value is not None:

                    semantic_keys.append(
                        str(
                            value,
                        )
                    )

        return {
            "label":
            label,

            "original_count":
            total,

            "retained_count":
            len(
                selected_items,
            ),

            "retention_ratio":
            _clamp(
                len(
                    selected_items,
                )
                /
                max(
                    total,
                    1,
                )
            ),

            "semantic_keys":
            sorted(
                set(
                    semantic_keys,
                )
            )[
                :24
            ],

            "compressed_items":
            selected_items,
        }

    def causal_summarization(self, context):

        identity = context.get(
            "identity_stability_report",
            {},
        )

        causal_memory = identity.get(
            "causal_memory",
            {},
        )

        recent_events = causal_memory.get(
            "recent_events",
            [],
        )

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        simulations = (
            rehearsal.get(
                "mutation_simulator",
                {},
            ).get(
                "simulations",
                []
            )
        )

        return {
            "causal_events":
            self.semantic_compression(
                recent_events,
                "causal_events",
            ),

            "mutation_simulations":
            self.semantic_compression(
                simulations,
                "mutation_simulations",
            ),
        }

    def identity_preserving_reduction(self, context):

        identity = context.get(
            "identity_stability_report",
            {},
        )

        verifier = identity.get(
            "continuity_verifier",
            {},
        )

        anchors = context.get(
            "cognitive_homeostasis_report",
            {},
        ).get(
            "identity_anchors",
            {},
        )

        continuity = _clamp(
            verifier.get(
                "continuity_score",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            )
        )

        protected_keys = [
            "identity_snapshot",
            "stable_snapshot",
            "continuity_verifier",
            "identity_anchor",
            "self_consistency_graph",
            "semantic_anchor_graph",
            "epistemic_beliefs",
            "truth_commitments",
        ]

        semantic_anchor_graph = context.get(
            "identity_continuity_guardian_report",
            {},
        ).get(
            "semantic_anchor_graph",
            {},
        )

        return {
            "identity_continuity":
            continuity,

            "anchor_strength":
            _clamp(
                anchors.get(
                    "anchor_strength",
                    verifier.get(
                        "anchor_strength",
                        0.0,
                    ),
                )
            ),

            "protected_memory_keys":
            protected_keys,

            "semantic_anchor_graph":
            semantic_anchor_graph,

            "reduction_policy":
            (
                "preserve_identity_full"
                if continuity < 0.58
                or semantic_anchor_graph.get(
                    "semantic_anchor_state",
                )
                == "semantic_reconstruction_required"
                else "compress_non_identity_memory"
            ),
        }

    def _evolutionary_memory(self, context):

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        adaptive_traits = (
            evolutionary.get(
                "adaptive_trait_memory",
                {},
            ).get(
                "traits",
                [],
            )
        )

        lineage = (
            evolutionary.get(
                "mutation_lineage",
                {},
            ).get(
                "lineage_records",
                evolutionary.get(
                    "mutation_lineage",
                    {},
                ).get(
                    "lineages",
                    [],
                ),
            )
        )

        extinction = context.get(
            "extinction_engine_report",
            {},
        )

        reputation = context.get(
            "adaptive_permissioning_report",
            {},
        ).get(
            "cognitive_reputation",
            {},
        )

        return {
            "survival_histories":
            self.semantic_compression(
                adaptive_traits,
                "survival_histories",
            ),

            "mutation_lineage":
            self.semantic_compression(
                lineage,
                "mutation_lineage",
            ),

            "extinction_logs":
            self.semantic_compression(
                extinction.get(
                    "extinction_archive",
                    [],
                ),
                "extinction_logs",
            ),

            "reputation_logs":
            self.semantic_compression(
                reputation.get(
                    "reputation_history",
                    reputation.get(
                        "merge_reputation_logs",
                        [],
                    ),
                ),
                "reputation_logs",
            ),
        }

    def _epistemic_memory(self, context):

        epistemic = context.get(
            "epistemic_cognition_report",
            {},
        )
        truth_registry = context.get(
            "truth_registry_report",
            {},
        )
        truth_commitments = epistemic.get(
            "truth_commitments",
            context.get(
                "truth_commitments",
                [],
            ),
        )
        if not truth_commitments:
            truth_commitments = (
                context.get("reusable_truth_commitments", [])
                or truth_registry.get("active_truths", [])
            )

        return {
            "beliefs":
            self.semantic_compression(
                epistemic.get(
                    "beliefs",
                    context.get(
                        "active_beliefs",
                        [],
                    ),
                ),
                "epistemic_beliefs",
            ),

            "truth_commitments":
            self.semantic_compression(
                truth_commitments,
                "truth_commitments",
            ),

            "compression_policy":
            "preserve_truth_commitments_and_decay_non_core_beliefs",
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        evolutionary_summary = self._evolutionary_memory(
            context,
        )

        causal_summary = self.causal_summarization(
            context,
        )

        epistemic_summary = self._epistemic_memory(
            context,
        )

        identity_reduction = self.identity_preserving_reduction(
            context,
        )

        original_count = sum([
            evolutionary_summary[key].get(
                "original_count",
                0,
            )
            for key in evolutionary_summary
        ]) + sum([
            causal_summary[key].get(
                "original_count",
                0,
            )
            for key in causal_summary
        ]) + sum([
            epistemic_summary[key].get(
                "original_count",
                0,
            )
            for key in [
                "beliefs",
                "truth_commitments",
            ]
        ])

        retained_count = sum([
            evolutionary_summary[key].get(
                "retained_count",
                0,
            )
            for key in evolutionary_summary
        ]) + sum([
            causal_summary[key].get(
                "retained_count",
                0,
            )
            for key in causal_summary
        ]) + sum([
            epistemic_summary[key].get(
                "retained_count",
                0,
            )
            for key in [
                "beliefs",
                "truth_commitments",
            ]
        ])

        compression_ratio = _clamp(
            retained_count
            /
            max(
                original_count,
                1,
            )
        )

        report = {
            "system":
            "memory_compression_layer",

            "compression_mode":
            "semantic_causal_identity_preserving",

            "evolutionary_memory":
            evolutionary_summary,

            "causal_summarization":
            causal_summary,

            "epistemic_memory":
            epistemic_summary,

            "identity_preserving_reduction":
            identity_reduction,

            "original_item_count":
            original_count,

            "retained_item_count":
            retained_count,

            "compression_ratio":
            compression_ratio,

            "memory_pressure_state":
            (
                "compressed"
                if compression_ratio <= 0.55
                and original_count > retained_count
                else "compression_ready"
                if original_count > retained_count
                else "memory_pressure_low"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.compression_history.append(
            report,
        )

        self.compression_history = (
            self.compression_history[-128:]
        )

        return report


memory_compression_layer = MemoryCompressionLayer()
