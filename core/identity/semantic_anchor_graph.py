# ============================================
# NEXRYN SEMANTIC ANCHOR GRAPH
# ============================================

from datetime import datetime
from runtime.semantics.concept_schema_validator import (
    concept_schema_validator,
)


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


class SemanticAnchorGraph:

    def __init__(self):

        self.anchors = {}
        self.edges = []
        self.graph_history = []
        self.confirmed_stability_state = None
        self.stability_recovery_streak = 0
        self.concept_contract_reports = {}

    def _regulate_stability_state(self, score, raw_state):

        previous_state = self.confirmed_stability_state
        transition = "raw_state_accepted"

        if raw_state == "semantic_spine_reconstruction_required":

            self.stability_recovery_streak = 0
            state = raw_state

        elif raw_state == "fragile_semantic_spine":

            self.stability_recovery_streak = 0

            if (
                previous_state == "stable_semantic_spine"
                and score >= 0.68
            ):

                state = "stable_semantic_spine"
                transition = "stable_hysteresis_hold"

            else:

                state = raw_state

        elif previous_state in [
            "fragile_semantic_spine",
            "semantic_spine_reconstruction_required",
            "semantic_spine_recovering",
        ]:

            self.stability_recovery_streak += 1

            state = (
                "stable_semantic_spine"
                if self.stability_recovery_streak >= 3
                else "semantic_spine_recovering"
            )

            transition = (
                "recovery_confirmed"
                if state == "stable_semantic_spine"
                else "recovery_confirmation_pending"
            )

        else:

            self.stability_recovery_streak = 0
            state = "stable_semantic_spine"

        self.confirmed_stability_state = state

        return {
            "raw_stability_state":
            raw_state,

            "stability_state":
            state,

            "previous_stability_state":
            previous_state,

            "stability_transition":
            transition,

            "recovery_streak":
            self.stability_recovery_streak,

            "required_recovery_cycles":
            3,
        }

    def add_anchor(self, anchor_id, semantic_state):

        state = (
            semantic_state
            if isinstance(
                semantic_state,
                dict,
            )
            else {
                "value":
                semantic_state,
            }
        )

        anchor = {
            "anchor_id":
            anchor_id,

            "semantic_state":
            state,

            "strength":
            _clamp(
                state.get(
                    "strength",
                    state.get(
                        "score",
                        state.get(
                            "continuity",
                            0.5,
                        ),
                    ),
                )
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.anchors[
            anchor_id
        ] = anchor

        return anchor

    def connect_anchors(self, source, target, relation):

        edge = {
            "source":
            source,

            "target":
            target,

            "relation":
            relation,

            "weight":
            _clamp(
                relation.get(
                    "weight",
                    relation.get(
                        "strength",
                        0.5,
                    ),
                )
                if isinstance(
                    relation,
                    dict,
                )
                else 0.5
            ),
        }

        self.edges.append(
            edge,
        )

        self.edges = (
            self.edges[-512:]
        )

        return edge

    def semantic_distance(self, state_a, state_b):

        if not isinstance(
            state_a,
            dict,
        ):

            state_a = {}

        if not isinstance(
            state_b,
            dict,
        ):

            state_b = {}

        keys = set(
            state_a.keys()
        ) | set(
            state_b.keys()
        )

        if not keys:

            return 0.0

        distances = []

        for key in keys:

            value_a = state_a.get(
                key,
            )

            value_b = state_b.get(
                key,
            )

            if isinstance(
                value_a,
                (int, float),
            ) or isinstance(
                value_b,
                (int, float),
            ):

                distances.append(
                    abs(
                        _clamp(value_a)
                        -
                        _clamp(value_b)
                    )
                )

            elif value_a == value_b:

                distances.append(
                    0.0,
                )

            else:

                distances.append(
                    0.35,
                )

        return _clamp(
            sum(
                distances,
            )
            /
            max(
                len(
                    distances,
                ),
                1,
            )
        )

    def _anchor_strength(self, anchor_id):

        return _clamp(
            self.anchors.get(
                anchor_id,
                {},
            ).get(
                "strength",
                0.0,
            )
        )

    def build_reputation_anchor(self, context, survival_score):

        concept_reputation = context.get(
            "concept_reputation_engine_report",
            {},
        )

        concept_reputations = concept_reputation.get(
            "concept_reputations",
            [],
        )

        if concept_reputations:

            average_reputation = _clamp(
                sum(
                    item.get(
                        "reputation",
                        0.0,
                    )
                    for item in concept_reputations
                )
                /
                max(
                    len(
                        concept_reputations,
                    ),
                    1,
                )
            )

            contradiction_load = _clamp(
                sum(
                    item.get(
                        "contradiction_history",
                        0.0,
                    )
                    for item in concept_reputations
                )
                /
                max(
                    len(
                        concept_reputations,
                    ),
                    1,
                )
            )

            failure_propagation = _clamp(
                sum(
                    item.get(
                        "failure_propagation_score",
                        0.0,
                    )
                    for item in concept_reputations
                )
                /
                max(
                    len(
                        concept_reputations,
                    ),
                    1,
                )
            )

            strength = _clamp(
                average_reputation
                -
                contradiction_load * 0.18
                -
                failure_propagation * 0.22
            )

            return {
                "average_reputation":
                average_reputation,

                "reputation_state":
                concept_reputation.get(
                    "reputation_state",
                    "epistemically_forming",
                ),

                "anchor_source":
                "concept_reputation_engine",

                "concept_count":
                len(
                    concept_reputations,
                ),

                "contradiction_load":
                contradiction_load,

                "failure_propagation_score":
                failure_propagation,

                "survival_history_strength":
                survival_score,

                "survival_is_not_truth":
                True,

                "strength":
                strength,
            }

        permission_reputation = context.get(
            "adaptive_permissioning_report",
            {},
        ).get(
            "cognitive_reputation",
            {},
        )

        if permission_reputation:

            average_reputation = _clamp(
                permission_reputation.get(
                    "average_reputation",
                    0.0,
                )
            )

            return {
                "average_reputation":
                average_reputation,

                "reputation_state":
                permission_reputation.get(
                    "reputation_state",
                    "unknown",
                ),

                "anchor_source":
                "adaptive_permissioning",

                "survival_is_not_truth":
                True,

                "strength":
                average_reputation,
            }

        return {
            "average_reputation":
            0.0,

            "reputation_state":
            "unknown",

            "anchor_source":
            "missing_epistemic_evidence",

            "survival_history_strength":
            survival_score,

            "survival_is_not_truth":
            True,

            "strength":
            0.0,
        }

    def _build_from_context(self, context):

        self.anchors = {}
        self.edges = []

        identity = context.get(
            "identity_stability_report",
            {},
        )

        verifier = identity.get(
            "continuity_verifier",
            {},
        )

        anchor = identity.get(
            "identity_anchor",
            {},
        )

        graph = identity.get(
            "self_consistency_graph",
            {},
        )

        causal_memory = identity.get(
            "causal_memory",
            {},
        )

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        traits = (
            evolutionary.get(
                "adaptive_trait_memory",
                {},
            ).get(
                "traits",
                [],
            )
        )

        compression = context.get(
            "memory_compression_report",
            {},
        )

        survival_score = _clamp(
            sum(
                trait.get(
                    "fitness",
                    trait.get(
                        "net_fitness",
                        0.0,
                    ),
                )
                for trait in traits
            )
            /
            max(
                len(
                    traits,
                ),
                1,
            )
        )

        reputation = self.build_reputation_anchor(
            context,
            survival_score,
        )

        self.add_anchor(
            "identity",
            {
                "continuity":
                verifier.get(
                    "continuity_score",
                    context.get(
                        "identity_continuity",
                        0.0,
                    ),
                ),

                "strength":
                verifier.get(
                    "continuity_score",
                    context.get(
                        "identity_continuity",
                        0.0,
                    ),
                ),

                "spine_state":
                identity.get(
                    "identity_spine_state",
                    "unknown",
                ),
            },
        )

        self.add_anchor(
            "memory",
            {
                "recorded_events":
                causal_memory.get(
                    "recorded_event_count",
                    len(
                        causal_memory.get(
                            "recent_events",
                            [],
                        )
                    ),
                ),

                "compression_ratio":
                compression.get(
                    "compression_ratio",
                    1.0,
                ),

                "strength":
                _clamp(
                    1.0
                    -
                    compression.get(
                        "compression_ratio",
                        1.0,
                    )
                    * 0.32
                ),
            },
        )

        self.add_anchor(
            "causality",
            {
                "recent_events":
                len(
                    causal_memory.get(
                        "recent_events",
                        [],
                    )
                ),

                "strength":
                _clamp(
                    min(
                        len(
                            causal_memory.get(
                                "recent_events",
                                [],
                            )
                        ),
                        12,
                    )
                    / 12
                    +
                    0.35
                ),
            },
        )

        self.add_anchor(
            "semantic_consistency",
            {
                "graph_consistency":
                graph.get(
                    "consistency_score",
                    verifier.get(
                        "graph_consistency",
                        0.0,
                    ),
                ),

                "anchor_strength":
                anchor.get(
                    "anchor_strength",
                    verifier.get(
                        "anchor_strength",
                        0.0,
                    ),
                ),

                "strength":
                _clamp(
                    graph.get(
                        "consistency_score",
                        verifier.get(
                            "graph_consistency",
                            0.0,
                        ),
                    )
                    * 0.52
                    +
                    anchor.get(
                        "anchor_strength",
                        verifier.get(
                            "anchor_strength",
                            0.0,
                        ),
                    )
                    * 0.48
                ),
            },
        )

        self.add_anchor(
            "reputation",
            {
                "average_reputation":
                reputation.get(
                    "average_reputation",
                    0.0,
                ),

                "reputation_state":
                reputation.get(
                    "reputation_state",
                    "unknown",
                ),

                "anchor_source":
                reputation.get(
                    "anchor_source",
                    "unknown",
                ),

                "concept_count":
                reputation.get(
                    "concept_count",
                    0,
                ),

                "contradiction_load":
                reputation.get(
                    "contradiction_load",
                    0.0,
                ),

                "failure_propagation_score":
                reputation.get(
                    "failure_propagation_score",
                    0.0,
                ),

                "survival_history_strength":
                reputation.get(
                    "survival_history_strength",
                    survival_score,
                ),

                "survival_is_not_truth":
                reputation.get(
                    "survival_is_not_truth",
                    True,
                ),

                "strength":
                reputation.get(
                    "strength",
                    reputation.get(
                        "average_reputation",
                        0.0,
                    ),
                ),
            },
        )

        self.add_anchor(
            "survival_history",
            {
                "trait_count":
                len(
                    traits,
                ),

                "average_trait_fitness":
                survival_score,

                "strength":
                survival_score,
            },
        )

        truth_commitments = context.get(
            "truth_commitments",
            context.get(
                "epistemic_cognition_report",
                {},
            ).get(
                "truth_commitments",
                [],
            ),
        )
        truth_contract = concept_schema_validator.normalize_items(
            truth_commitments,
            record_type="truth_commitment",
        )
        self.concept_contract_reports[
            "truth_commitments"
        ] = truth_contract
        truth_commitments = truth_contract["normalized_items"]

        if truth_commitments:

            self.add_anchor(
                "constitutional_truth",
                {
                    "commitment_count":
                    len(
                        truth_commitments,
                    ),

                    "concepts":
                    [
                        item.get(
                            "concept",
                            "unknown",
                        )
                        for item in truth_commitments
                    ],

                    "strength":
                    _clamp(
                        sum(
                            item.get(
                                "calibrated_confidence",
                                0.0,
                            )
                            for item in truth_commitments
                        )
                        /
                        len(
                            truth_commitments,
                        )
                    ),

                    "survival_is_not_truth":
                    True,
                },
            )

        self.connect_anchors(
            "identity",
            "semantic_consistency",
            {
                "type":
                "defines",

                "weight":
                0.86,
            },
        )

        self.connect_anchors(
            "identity",
            "memory",
            {
                "type":
                "preserves",

                "weight":
                0.78,
            },
        )

        self.connect_anchors(
            "memory",
            "causality",
            {
                "type":
                "explains",

                "weight":
                0.74,
            },
        )

        self.connect_anchors(
            "survival_history",
            "reputation",
            {
                "type":
                "earns",

                "weight":
                0.62,
            },
        )

        self.connect_anchors(
            "reputation",
            "semantic_consistency",
            {
                "type":
                "validates",

                "weight":
                0.58,
            },
        )

        if truth_commitments:

            self.connect_anchors(
                "causality",
                "constitutional_truth",
                {
                    "type":
                    "evidences",

                    "weight":
                    0.88,
                },
            )

            self.connect_anchors(
                "constitutional_truth",
                "semantic_consistency",
                {
                    "type":
                    "protects",

                    "weight":
                    0.92,
                },
            )

    def compute_identity_stability(self):

        required = [
            "identity",
            "memory",
            "causality",
            "semantic_consistency",
            "reputation",
            "survival_history",
        ]

        strengths = [
            self._anchor_strength(
                anchor_id,
            )
            for anchor_id in required
        ]

        edge_support = _clamp(
            sum(
                edge.get(
                    "weight",
                    0.0,
                )
                for edge in self.edges
            )
            /
            max(
                len(
                    self.edges,
                ),
                1,
            )
        )

        identity_stability = _clamp(
            sum(
                strengths,
            )
            /
            max(
                len(
                    strengths,
                ),
                1,
            )
            * 0.72
            +
            edge_support
            * 0.28
        )

        raw_stability_state = (
            "stable_semantic_spine"
            if identity_stability >= 0.72
            else "fragile_semantic_spine"
            if identity_stability >= 0.52
            else "semantic_spine_reconstruction_required"
        )

        regulated = self._regulate_stability_state(
            identity_stability,
            raw_stability_state,
        )

        return {
            "identity_stability":
            identity_stability,

            "average_anchor_strength":
            _clamp(
                sum(
                    strengths,
                )
                /
                max(
                    len(
                        strengths,
                    ),
                    1,
                )
            ),

            "edge_support":
            edge_support,

            **regulated,
        }

    def detect_drift_clusters(self):

        clusters = []

        pairs = [
            (
                "identity",
                "semantic_consistency",
            ),
            (
                "identity",
                "memory",
            ),
            (
                "memory",
                "causality",
            ),
            (
                "reputation",
                "survival_history",
            ),
            (
                "semantic_consistency",
                "reputation",
            ),
        ]

        for source, target in pairs:

            distance = self.semantic_distance(
                self.anchors.get(
                    source,
                    {},
                ).get(
                    "semantic_state",
                    {},
                ),
                self.anchors.get(
                    target,
                    {},
                ).get(
                    "semantic_state",
                    {},
                ),
            )

            if distance >= 0.34:

                clusters.append({
                    "source":
                    source,

                    "target":
                    target,

                    "semantic_distance":
                    distance,

                    "cluster_state":
                    (
                        "critical_drift_cluster"
                        if distance >= 0.62
                        else "watched_drift_cluster"
                    ),
                })

        return {
            "drift_clusters":
            clusters,

            "drift_cluster_count":
            len(
                clusters,
            ),

            "drift_state":
            (
                "semantic_fragmentation"
                if any(
                    cluster.get(
                        "cluster_state",
                    )
                    == "critical_drift_cluster"
                    for cluster in clusters
                )
                else "semantic_drift_watched"
                if clusters
                else "semantic_graph_coherent"
            ),
        }

    def reconstruct_missing_identity(self):

        missing = [
            anchor_id
            for anchor_id, anchor in self.anchors.items()
            if anchor.get(
                "strength",
                0.0,
            )
            < 0.34
        ]

        reconstruction_plan = []

        if "identity" in missing:

            reconstruction_plan.append(
                "restore_stable_identity_snapshot",
            )

        if "memory" in missing or "causality" in missing:

            reconstruction_plan.append(
                "rebuild_causal_memory_from_recent_events",
            )

        if "semantic_consistency" in missing:

            reconstruction_plan.append(
                "recompute_self_consistency_graph",
            )

        if "reputation" in missing:

            reconstruction_plan.append(
                "reseed_reputation_from_epistemic_history",
            )

        if "survival_history" in missing:

            reconstruction_plan.append(
                "restore_trait_lineage_summary",
            )

        return {
            "missing_or_weak_anchors":
            missing,

            "reconstruction_plan":
            reconstruction_plan,

            "reconstruction_state":
            (
                "reconstruction_required"
                if reconstruction_plan
                else "identity_reconstruction_not_needed"
            ),
        }

    def preserve_core_semantics(self):

        protected = [
            "identity",
            "memory",
            "causality",
            "semantic_consistency",
        ]

        locks = [
            anchor_id
            for anchor_id in protected
            if self._anchor_strength(
                anchor_id,
            )
            < 0.58
        ]

        return {
            "protected_semantic_anchors":
            protected,

            "semantic_locks":
            locks,

            "preservation_policy":
            (
                "lock_fragile_core_semantics"
                if locks
                else "preserve_with_monitoring"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        self._build_from_context(
            context,
        )

        stability = self.compute_identity_stability()
        drift = self.detect_drift_clusters()
        reconstruction = self.reconstruct_missing_identity()
        preservation = self.preserve_core_semantics()

        report = {
            "system":
            "semantic_anchor_graph",

            "graph_mode":
            "dynamic_identity_memory_causality_anchor_network",

            "anchors":
            self.anchors,

            "edges":
            self.edges,

            "identity_stability":
            stability,

            "drift_clusters":
            drift,

            "identity_reconstruction":
            reconstruction,

            "core_semantic_preservation":
            preservation,

            "concept_schema_validation":
            dict(self.concept_contract_reports),

            "semantic_anchor_state":
            (
                "semantic_reconstruction_required"
                if reconstruction.get(
                    "reconstruction_state",
                )
                == "reconstruction_required"
                else "semantic_drift_watched"
                if drift.get(
                    "drift_cluster_count",
                    0,
                )
                else "semantic_anchor_graph_stable"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.graph_history.append(
            report,
        )

        self.graph_history = (
            self.graph_history[-128:]
        )

        return report


semantic_anchor_graph = SemanticAnchorGraph()
