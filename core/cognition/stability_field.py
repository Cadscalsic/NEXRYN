# ============================================
# NEXRYN COGNITIVE STABILITY FIELD
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


class StabilityField:

    def __init__(self):

        self.field_history = []

    def _entropy(self, context):

        return _clamp(
            context.get(
                "runtime_entropy",
                context.get(
                    "entropy_regulator_report",
                    {},
                ).get(
                    "entropy_delta_report",
                    {},
                ).get(
                    "runtime_entropy",
                    0.0,
                ),
            )
        )

    def compute_identity_pressure(self, context):

        natural_selection = context.get(
            "cognitive_natural_selection_report",
            {},
        )

        extinction = context.get(
            "extinction_engine_report",
            {},
        )

        fusion = context.get(
            "concept_fusion_report",
            {},
        )

        memory = context.get(
            "memory_compression_report",
            {},
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        causal_events = (
            context.get(
                "identity_stability_report",
                {},
            ).get(
                "causal_memory",
                {},
            ).get(
                "recent_events",
                [],
            )
        )

        mutation_overload = _clamp(
            (
                natural_selection.get(
                    "decaying_count",
                    0,
                )
                +
                natural_selection.get(
                    "suppressed_count",
                    0,
                )
                +
                extinction.get(
                    "extinct_count",
                    0,
                )
            )
            / 12
        )

        abstraction_overload = _clamp(
            (
                len(
                    fusion.get(
                        "fused_concepts",
                        [],
                    )
                )
                +
                len(
                    fusion.get(
                        "rejected_fusions",
                        [],
                    )
                )
            )
            / 10
        )

        semantic_divergence = _clamp(
            guardian.get(
                "semantic_anchor_graph",
                {},
            ).get(
                "drift_clusters",
                {},
            ).get(
                "drift_cluster_count",
                0,
            )
            / 6
        )

        memory_compression_stress = _clamp(
            1.0
            -
            memory.get(
                "compression_ratio",
                1.0,
            )
        )

        causal_fragmentation = _clamp(
            1.0
            -
            min(
                len(
                    causal_events,
                ),
                8,
            )
            / 8
        )

        identity_pressure = _clamp(
            mutation_overload * 0.24
            +
            abstraction_overload * 0.18
            +
            semantic_divergence * 0.22
            +
            memory_compression_stress * 0.18
            +
            causal_fragmentation * 0.18
        )

        return {
            "identity_pressure":
            identity_pressure,

            "mutation_overload":
            mutation_overload,

            "abstraction_overload":
            abstraction_overload,

            "semantic_divergence":
            semantic_divergence,

            "memory_compression_stress":
            memory_compression_stress,

            "causal_fragmentation":
            causal_fragmentation,

            "pressure_state":
            (
                "critical_identity_pressure"
                if identity_pressure >= 0.68
                else "elevated_identity_pressure"
                if identity_pressure >= 0.42
                else "regulated_identity_pressure"
            ),
        }

    def compute_semantic_drift(self, context):

        homeostasis = context.get(
            "cognitive_homeostasis_report",
            {},
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        drift = _clamp(
            homeostasis.get(
                "semantic_drift_detection",
                {},
            ).get(
                "semantic_drift",
                guardian.get(
                    "drift_monitoring",
                    {},
                ).get(
                    "drift_pressure",
                    0.0,
                ),
            )
        )

        return {
            "semantic_drift":
            drift,

            "drift_state":
            (
                "semantic_spine_drift"
                if drift >= 0.58
                else "semantic_drift_watched"
                if drift >= 0.32
                else "semantic_drift_low"
            ),
        }

    def compute_anchor_integrity(self, context):

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        semantic_anchor = guardian.get(
            "semantic_anchor_graph",
            {},
        )

        graph_score = _clamp(
            semantic_anchor.get(
                "identity_stability",
                {},
            ).get(
                "identity_stability",
                0.0,
            )
        )

        homeostasis_anchor = _clamp(
            context.get(
                "cognitive_homeostasis_report",
                {},
            ).get(
                "identity_anchors",
                {},
            ).get(
                "anchor_strength",
                context.get(
                    "anchor_strength",
                    0.0,
                ),
            )
        )

        integrity = _clamp(
            graph_score * 0.56
            +
            homeostasis_anchor * 0.44
        )

        return {
            "anchor_integrity":
            integrity,

            "semantic_anchor_score":
            graph_score,

            "homeostasis_anchor_strength":
            homeostasis_anchor,

            "anchor_state":
            (
                "anchor_integrity_strong"
                if integrity >= 0.72
                else "anchor_integrity_fragile"
                if integrity >= 0.48
                else "anchor_integrity_compromised"
            ),
        }

    def detect_identity_fragmentation(
        self,
        identity_pressure_report,
        drift_report,
        anchor_report,
    ):

        fragmentation = _clamp(
            identity_pressure_report.get(
                "identity_pressure",
                0.0,
            )
            * 0.42
            +
            drift_report.get(
                "semantic_drift",
                0.0,
            )
            * 0.30
            +
            (
                1.0
                -
                anchor_report.get(
                    "anchor_integrity",
                    0.0,
                )
            )
            * 0.28
        )

        return {
            "fragmentation_score":
            fragmentation,

            "fragmentation_state":
            (
                "identity_fragmentation"
                if fragmentation >= 0.64
                else "fragmentation_watch"
                if fragmentation >= 0.38
                else "identity_coherent"
            ),
        }

    def stabilize_semantic_spine(
        self,
        fragmentation_report,
        anchor_report,
    ):

        actions = []

        if anchor_report.get(
            "anchor_integrity",
            0.0,
        ) < 0.58:

            actions.append(
                "reinforce_semantic_anchor_graph",
            )

        if fragmentation_report.get(
            "fragmentation_score",
            0.0,
        ) >= 0.38:

            actions.extend([
                "freeze_unstable_fusion",
                "require_causal_rehearsal",
                "preserve_identity_spine",
            ])

        if not actions:

            actions.append(
                "continue_semantic_spine_monitoring",
            )

        return {
            "stabilization_actions":
            actions,

            "spine_state":
            (
                "semantic_spine_stabilizing"
                if len(actions) > 1
                else "semantic_spine_stable"
            ),
        }

    def reinforce_identity(self, anchor_report, pressure_report):

        reinforcement_strength = _clamp(
            (
                1.0
                -
                pressure_report.get(
                    "identity_pressure",
                    0.0,
                )
            )
            * 0.46
            +
            anchor_report.get(
                "anchor_integrity",
                0.0,
            )
            * 0.54
        )

        return {
            "reinforcement_strength":
            reinforcement_strength,

            "reinforcement_policy":
            (
                "identity_reinforced"
                if reinforcement_strength >= 0.62
                else "identity_reinforcement_required"
            ),
        }

    def reject_destructive_mutation(
        self,
        pressure_report,
        fragmentation_report,
        drift_report,
    ):

        reject = (
            pressure_report.get(
                "identity_pressure",
                0.0,
            )
            >= 0.68
            or fragmentation_report.get(
                "fragmentation_score",
                0.0,
            )
            >= 0.64
            or drift_report.get(
                "semantic_drift",
                0.0,
            )
            >= 0.72
        )

        return {
            "reject_destructive_mutation":
            reject,

            "rejection_policy":
            (
                "reject_and_rehearse"
                if reject
                else "allow_stability_gated_mutation"
            ),
        }

    def preserve_core_semantics(self, anchor_report, fragmentation_report):

        locks = []

        if anchor_report.get(
            "anchor_integrity",
            0.0,
        ) < 0.58:

            locks.append(
                "semantic_anchor_graph",
            )

        if fragmentation_report.get(
            "fragmentation_score",
            0.0,
        ) >= 0.38:

            locks.extend([
                "identity_spine",
                "causal_memory",
                "stable_snapshot",
            ])

        return {
            "semantic_locks":
            sorted(
                set(
                    locks,
                )
            ),

            "preservation_state":
            (
                "core_semantics_locked"
                if locks
                else "core_semantics_preserved"
            ),
        }

    def semantic_entropy(self, context, drift_report, pressure_report):

        entropy = _clamp(
            self._entropy(context) * 0.50
            +
            drift_report.get(
                "semantic_drift",
                0.0,
            )
            * 0.24
            +
            pressure_report.get(
                "semantic_divergence",
                0.0,
            )
            * 0.26
        )

        return {
            "semantic_entropy":
            entropy,

            "semantic_entropy_state":
            (
                "semantic_entropy_high"
                if entropy >= 0.68
                else "semantic_entropy_elevated"
                if entropy >= 0.42
                else "semantic_entropy_regulated"
            ),
        }

    def identity_resilience_score(
        self,
        pressure_report,
        anchor_report,
        entropy_report,
    ):

        resilience = _clamp(
            anchor_report.get(
                "anchor_integrity",
                0.0,
            )
            * 0.44
            +
            (
                1.0
                -
                pressure_report.get(
                    "identity_pressure",
                    0.0,
                )
            )
            * 0.34
            +
            (
                1.0
                -
                entropy_report.get(
                    "semantic_entropy",
                    0.0,
                )
            )
            * 0.22
        )

        return {
            "identity_resilience_score":
            resilience,

            "resilience_state":
            (
                "resilient_identity_field"
                if resilience >= 0.68
                else "fragile_identity_field"
                if resilience >= 0.42
                else "identity_field_failure"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        pressure = self.compute_identity_pressure(
            context,
        )
        drift = self.compute_semantic_drift(
            context,
        )
        anchors = self.compute_anchor_integrity(
            context,
        )
        fragmentation = self.detect_identity_fragmentation(
            pressure,
            drift,
            anchors,
        )
        spine = self.stabilize_semantic_spine(
            fragmentation,
            anchors,
        )
        reinforcement = self.reinforce_identity(
            anchors,
            pressure,
        )
        rejection = self.reject_destructive_mutation(
            pressure,
            fragmentation,
            drift,
        )
        preservation = self.preserve_core_semantics(
            anchors,
            fragmentation,
        )
        entropy = self.semantic_entropy(
            context,
            drift,
            pressure,
        )
        resilience = self.identity_resilience_score(
            pressure,
            anchors,
            entropy,
        )

        report = {
            "system":
            "stability_field",

            "field_mode":
            "semantic_immune_identity_pressure_field",

            "identity_pressure":
            pressure,

            "semantic_drift":
            drift,

            "anchor_integrity":
            anchors,

            "identity_fragmentation":
            fragmentation,

            "semantic_spine":
            spine,

            "identity_reinforcement":
            reinforcement,

            "destructive_mutation_filter":
            rejection,

            "core_semantic_preservation":
            preservation,

            "semantic_entropy":
            entropy,

            "identity_resilience":
            resilience,

            "stability_field_state":
            (
                "immune_rejection_active"
                if rejection.get(
                    "reject_destructive_mutation",
                    False,
                )
                else "semantic_spine_reinforcing"
                if spine.get(
                    "spine_state",
                )
                == "semantic_spine_stabilizing"
                else "stability_field_regulated"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.field_history.append(
            report,
        )

        self.field_history = (
            self.field_history[-128:]
        )

        return report


stability_field = StabilityField()
