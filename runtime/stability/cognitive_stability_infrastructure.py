# ============================================
# NEXRYN COGNITIVE STABILITY INFRASTRUCTURE
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
                maximum
            )
        ),
        4
    )


def _as_list(value):

    if isinstance(
        value,
        list
    ):

        return value

    if value is None:

        return []

    return [
        value
    ]


def _concept_name(item):

    if isinstance(
        item,
        dict
    ):

        return str(
            item.get(
                "concept",
                item.get(
                    "name",
                    item.get(
                        "id",
                        "unknown"
                    )
                )
            )
        )

    return str(
        item
    )


class SemanticVirtualMemory:

    def __init__(self):

        self.page_history = []

    def partition(self, context):

        activation_report = context.get(
            "semantic_activation_report",
            {}
        )

        active = [
            item
            for item in activation_report.get(
                "top_activations",
                []
            )
            if item.get(
                "activation_strength",
                0.0
            ) >= 0.45
        ]

        latent_report = context.get(
            "latent_reservoir_report",
            {}
        )

        latent = _as_list(
            latent_report.get(
                "latent_candidates",
                latent_report.get(
                    "latent_concepts",
                    []
                )
            )
        )

        archive = _as_list(
            context.get(
                "archived_cognition",
                context.get(
                    "semantic_archive",
                    []
                )
            )
        )

        report = {
            "active_cognition":
            active,

            "latent_cognition":
            latent,

            "archived_cognition":
            archive[-128:],

            "partition_counts":
            {
                "active":
                len(
                    active
                ),

                "latent":
                len(
                    latent
                ),

                "archived":
                min(
                    len(
                        archive
                    ),
                    128
                )
            },

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.page_history.append(
            report
        )

        self.page_history = (
            self.page_history[-64:]
        )

        return report


class OntologyDefragmenter:

    def estimate_fragmentation(self, context):

        explicit = context.get(
            "semantic_fragmentation"
        )

        if explicit is not None:

            return _clamp(
                explicit
            )

        pointer_report = context.get(
            "semantic_pointer_report",
            {}
        )

        rejected = len(
            context.get(
                "rejected_merges",
                []
            )
        )

        pointers = len(
            pointer_report.get(
                "pointers",
                []
            )
        )

        return _clamp(
            rejected / max(
                pointers + rejected,
                1
            )
        )

    def defragment(self, context, virtual_memory_report):

        fragmentation = self.estimate_fragmentation(
            context
        )

        active = virtual_memory_report.get(
            "active_cognition",
            []
        )

        canonical_routes = []
        seen = set()

        for item in active:

            name = _concept_name(
                item
            )

            canonical = (
                name.strip()
                .lower()
                .replace(
                    " ",
                    "_"
                )
            )

            if canonical in seen:

                continue

            seen.add(
                canonical
            )

            canonical_routes.append({
                "source_concept":
                name,

                "canonical_concept":
                canonical
            })

        estimated_after = _clamp(
            fragmentation * 0.42
            if fragmentation >= 0.70
            else fragmentation * 0.70
        )

        return {
            "semantic_fragmentation_before":
            fragmentation,

            "semantic_fragmentation_after":
            estimated_after,

            "defragmentation_state":
            (
                "critical_defragmentation"
                if fragmentation >= 0.80
                else "active_defragmentation"
                if fragmentation >= 0.55
                else "maintenance"
            ),

            "canonical_routes":
            canonical_routes,

            "route_count":
            len(
                canonical_routes
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


class IdentityAnchorCore:

    def estimate_identity_drift(self, context):

        explicit = context.get(
            "identity_drift"
        )

        if explicit is not None:

            return _clamp(
                explicit
            )

        identity_core_report = context.get(
            "identity_core_report",
            {}
        )

        return _clamp(
            identity_core_report.get(
                "identity_drift",
                0.0
            )
        )

    def anchor(self, context):

        drift = self.estimate_identity_drift(
            context
        )

        anchors = [
            "execution_grounding",
            "ontology_identity",
            "reward_alignment"
        ]

        if drift >= 0.40:

            anchors.extend([
                "memory_continuity",
                "strategy_coherence"
            ])

        return {
            "identity_drift_before":
            drift,

            "identity_drift_after":
            _clamp(
                drift * 0.56
            ),

            "anchor_state":
            (
                "reinforced"
                if drift >= 0.40
                else "watched"
                if drift >= 0.25
                else "stable"
            ),

            "active_anchors":
            anchors,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


class CognitiveGarbageCollector:

    def collect(self, context, virtual_memory_report):

        active_names = {
            _concept_name(
                item
            )
            for item in virtual_memory_report.get(
                "active_cognition",
                []
            )
        }

        dead_abstractions = _as_list(
            context.get(
                "dead_abstractions",
                []
            )
        )

        stale_routes = _as_list(
            context.get(
                "stale_semantic_routes",
                []
            )
        )

        orphan_concepts = [
            concept
            for concept in _as_list(
                context.get(
                    "orphan_concepts",
                    []
                )
            )
            if _concept_name(
                concept
            ) not in active_names
        ]

        return {
            "dead_abstractions_removed":
            len(
                dead_abstractions
            ),

            "stale_semantic_routes_removed":
            len(
                stale_routes
            ),

            "orphan_concepts_removed":
            len(
                orphan_concepts
            ),

            "removed_items":
            {
                "dead_abstractions":
                dead_abstractions,

                "stale_semantic_routes":
                stale_routes,

                "orphan_concepts":
                orphan_concepts
            },

            "collection_state":
            "completed",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


class PredictiveCollapseEngine:

    def estimate_overload(self, context):

        explicit = context.get(
            "projected_overload"
        )

        if explicit is not None:

            return _clamp(
                explicit
            )

        energy = context.get(
            "cognitive_energy_economy_report",
            {}
        )

        entropy = context.get(
            "cognitive_entropy_report",
            {}
        )

        return _clamp(
            energy.get(
                "energy_pressure",
                0.0
            )
            * 0.55
            +
            entropy.get(
                "entropy_level",
                0.0
            )
            * 0.45
        )

    def predict(self, context):

        overload = self.estimate_overload(
            context
        )

        return {
            "projected_overload":
            overload,

            "collapse_risk":
            (
                "imminent"
                if overload >= 0.82
                else "elevated"
                if overload >= 0.65
                else "contained"
            ),

            "preventive_actions":
            (
                [
                    "page_latent_cognition",
                    "compress_semantic_routes",
                    "cap_recursive_pressure",
                    "freeze_nonessential_abstractions"
                ]
                if overload >= 0.82
                else [
                    "increase_memory_paging",
                    "monitor_recursive_pressure"
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


class RecursivePressureGovernor:

    def estimate_depth(self, context):

        explicit = context.get(
            "raw_reasoning_depth"
        )

        if explicit is not None:

            try:

                return int(
                    explicit
                )

            except Exception:

                return 0

        inference = context.get(
            "inference_report",
            {}
        )

        return int(
            inference.get(
                "reasoning_depth",
                0
            )
        )

    def govern(self, context):

        depth = self.estimate_depth(
            context
        )

        target_depth = (
            7
            if depth >= 11
            else 9
            if depth >= 8
            else depth
        )

        return {
            "raw_reasoning_depth":
            depth,

            "regulated_reasoning_depth":
            target_depth,

            "pressure_state":
            (
                "capped"
                if depth >= 11
                else "regulated"
                if depth >= 8
                else "stable"
            ),

            "governor_actions":
            (
                [
                    "cap_recursive_expansion",
                    "merge_equivalent_branches",
                    "defer_low_priority_hypotheses"
                ]
                if depth >= 11
                else [
                    "monitor_depth"
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


class SemanticPagingSystem:

    def page(self, virtual_memory_report, collapse_report):

        overload = collapse_report.get(
            "projected_overload",
            0.0
        )

        active = virtual_memory_report.get(
            "active_cognition",
            []
        )

        latent = virtual_memory_report.get(
            "latent_cognition",
            []
        )

        archive = virtual_memory_report.get(
            "archived_cognition",
            []
        )

        page_out_count = (
            max(
                len(
                    active
                )
                - 8,
                0
            )
            if overload >= 0.75
            else 0
        )

        return {
            "working_memory":
            active[:8],

            "latent_memory":
            latent[:64] + active[8:],

            "semantic_memory":
            active[:16] + latent[:16],

            "archive_memory":
            archive[-128:],

            "paging_actions":
            {
                "active_to_latent":
                page_out_count,

                "latent_to_semantic":
                min(
                    len(
                        latent
                    ),
                    16
                ),

                "semantic_to_archive":
                max(
                    len(
                        archive
                    )
                    - 128,
                    0
                )
            },

            "timestamp":
            str(
                datetime.utcnow()
            )
        }


class CognitiveStabilityInfrastructure:

    def __init__(self):

        self.semantic_virtual_memory = (
            SemanticVirtualMemory()
        )

        self.ontology_defragmenter = (
            OntologyDefragmenter()
        )

        self.identity_anchor_core = (
            IdentityAnchorCore()
        )

        self.cognitive_garbage_collector = (
            CognitiveGarbageCollector()
        )

        self.predictive_collapse_engine = (
            PredictiveCollapseEngine()
        )

        self.recursive_pressure_governor = (
            RecursivePressureGovernor()
        )

        self.semantic_paging_system = (
            SemanticPagingSystem()
        )

        self.infrastructure_history = []

    def run_cycle(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        virtual_memory_report = (
            self.semantic_virtual_memory
            .partition(runtime_context)
        )

        ontology_report = (
            self.ontology_defragmenter
            .defragment(
                runtime_context,
                virtual_memory_report
            )
        )

        identity_anchor_report = (
            self.identity_anchor_core
            .anchor(runtime_context)
        )

        garbage_collection_report = (
            self.cognitive_garbage_collector
            .collect(
                runtime_context,
                virtual_memory_report
            )
        )

        collapse_report = (
            self.predictive_collapse_engine
            .predict(runtime_context)
        )

        recursive_pressure_report = (
            self.recursive_pressure_governor
            .govern(runtime_context)
        )

        paging_report = (
            self.semantic_paging_system
            .page(
                virtual_memory_report,
                collapse_report
            )
        )

        report = {
            "phase":
            "Phase 5 - Cognitive Stability Infrastructure",

            "semantic_virtual_memory":
            virtual_memory_report,

            "ontology_defragmenter":
            ontology_report,

            "identity_anchor_core":
            identity_anchor_report,

            "cognitive_garbage_collector":
            garbage_collection_report,

            "predictive_collapse_engine":
            collapse_report,

            "recursive_pressure_governor":
            recursive_pressure_report,

            "semantic_paging_system":
            paging_report,

            "stability_state":
            (
                "protected"
                if collapse_report.get(
                    "projected_overload",
                    0.0
                ) >= 0.82
                or ontology_report.get(
                    "semantic_fragmentation_before",
                    0.0
                ) >= 0.80
                else "regulated"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        runtime_context[
            "semantic_virtual_memory_report"
        ] = virtual_memory_report

        runtime_context[
            "ontology_defragmenter_report"
        ] = ontology_report

        runtime_context[
            "identity_anchor_core_report"
        ] = identity_anchor_report

        runtime_context[
            "cognitive_garbage_collector_report"
        ] = garbage_collection_report

        runtime_context[
            "predictive_collapse_report"
        ] = collapse_report

        runtime_context[
            "recursive_pressure_governor_report"
        ] = recursive_pressure_report

        runtime_context[
            "semantic_paging_report"
        ] = paging_report

        runtime_context[
            "phase_5_cognitive_stability_report"
        ] = report

        self.infrastructure_history.append(
            report
        )

        self.infrastructure_history = (
            self.infrastructure_history[-64:]
        )

        return runtime_context


cognitive_stability_infrastructure = (
    CognitiveStabilityInfrastructure()
)
