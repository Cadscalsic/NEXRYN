# ============================================
# NEXRYN IDENTITY CONTINUITY GUARDIAN
# ============================================

from datetime import datetime

from core.identity.semantic_anchor_graph import (
    semantic_anchor_graph,
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


class IdentityContinuityGuardian:

    def __init__(self):

        self.previous_state = None
        self.guardian_history = []
        self.semantic_anchor_graph = semantic_anchor_graph

    def _continuity(self, context):

        identity = context.get(
            "identity_stability_report",
            {},
        )

        verifier = identity.get(
            "continuity_verifier",
            {},
        )

        return _clamp(
            verifier.get(
                "continuity_score",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            )
        )

    def capture_state(self, context):

        identity = context.get(
            "identity_stability_report",
            {},
        )

        homeostasis = context.get(
            "cognitive_homeostasis_report",
            {},
        )

        natural_selection = context.get(
            "cognitive_natural_selection_report",
            {},
        )

        recovery = context.get(
            "trait_recovery_report",
            {},
        )

        return {
            "identity_continuity":
            self._continuity(
                context,
            ),

            "identity_spine_state":
            identity.get(
                "identity_spine_state",
                "unknown",
            ),

            "identity_shift":
            _clamp(
                identity.get(
                    "identity_diff",
                    {},
                ).get(
                    "identity_shift",
                    0.0,
                )
            ),

            "semantic_drift":
            _clamp(
                homeostasis.get(
                    "semantic_drift_detection",
                    {},
                ).get(
                    "semantic_drift",
                    context.get(
                        "semantic_drift",
                        0.0,
                    ),
                )
            ),

            "extinct_count":
            natural_selection.get(
                "extinct_count",
                0,
            ),

            "suppressed_count":
            natural_selection.get(
                "suppressed_count",
                0,
            ),

            "recovered_count":
            recovery.get(
                "recovered_count",
                0,
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

    def compare_state_transitions(self, current_state):

        previous = self.previous_state or current_state

        continuity_delta = round(
            current_state.get(
                "identity_continuity",
                0.0,
            )
            -
            previous.get(
                "identity_continuity",
                0.0,
            ),
            4,
        )

        drift_delta = round(
            current_state.get(
                "semantic_drift",
                0.0,
            )
            -
            previous.get(
                "semantic_drift",
                0.0,
            ),
            4,
        )

        extinction_delta = (
            current_state.get(
                "extinct_count",
                0,
            )
            -
            previous.get(
                "extinct_count",
                0,
            )
        )

        recovery_delta = (
            current_state.get(
                "recovered_count",
                0,
            )
            -
            previous.get(
                "recovered_count",
                0,
            )
        )

        transition_risk = _clamp(
            max(
                -continuity_delta,
                0.0,
            )
            * 1.45
            +
            max(
                drift_delta,
                0.0,
            )
            * 0.72
            +
            min(
                max(
                    extinction_delta,
                    0,
                ),
                8,
            )
            / 8
            * 0.20
            +
            min(
                max(
                    recovery_delta,
                    0,
                ),
                8,
            )
            / 8
            * 0.12
        )

        return {
            "previous_state":
            previous,

            "current_state":
            current_state,

            "continuity_delta":
            continuity_delta,

            "drift_delta":
            drift_delta,

            "extinction_delta":
            extinction_delta,

            "recovery_delta":
            recovery_delta,

            "transition_risk":
            transition_risk,

            "transition_state":
            (
                "catastrophic_transition"
                if transition_risk >= 0.62
                else "unsafe_transition"
                if transition_risk >= 0.38
                else "watched_transition"
                if transition_risk >= 0.18
                else "stable_transition"
            ),
        }

    def monitor_drift(self, context, transition_report):

        continuity = transition_report.get(
            "current_state",
            {},
        ).get(
            "identity_continuity",
            0.0,
        )

        semantic_drift = transition_report.get(
            "current_state",
            {},
        ).get(
            "semantic_drift",
            0.0,
        )

        identity_shift = transition_report.get(
            "current_state",
            {},
        ).get(
            "identity_shift",
            0.0,
        )

        drift_pressure = _clamp(
            (
                1.0
                -
                continuity
            )
            * 0.46
            +
            semantic_drift
            * 0.34
            +
            identity_shift
            * 0.20
        )

        return {
            "drift_pressure":
            drift_pressure,

            "drift_state":
            (
                "identity_collapse_risk"
                if drift_pressure >= 0.62
                else "identity_fragile"
                if drift_pressure >= 0.38
                else "identity_watched"
                if drift_pressure >= 0.20
                else "identity_stable"
            ),
        }

    def prevent_catastrophic_rewrites(
        self,
        transition_report,
        drift_report,
        semantic_anchor_report=None,
    ):

        transition_state = transition_report.get(
            "transition_state",
            "stable_transition",
        )

        drift_state = drift_report.get(
            "drift_state",
            "identity_stable",
        )

        if semantic_anchor_report is None:

            semantic_anchor_report = {}

        semantic_anchor_state = semantic_anchor_report.get(
            "semantic_anchor_state",
            "semantic_anchor_graph_stable",
        )

        semantic_fragmentation = (
            semantic_anchor_state
            in [
                "semantic_reconstruction_required",
                "semantic_drift_watched",
            ]
            and semantic_anchor_report.get(
                "drift_clusters",
                {},
            ).get(
                "drift_state",
            )
            == "semantic_fragmentation"
        )

        block_rewrite = (
            transition_state
            in [
                "catastrophic_transition",
                "unsafe_transition",
            ]
            or drift_state
            == "identity_collapse_risk"
            or semantic_anchor_state
            == "semantic_reconstruction_required"
            or semantic_fragmentation
        )

        return {
            "block_rewrite":
            block_rewrite,

            "rewrite_policy":
            (
                "rollback_unsafe_evolution"
                if block_rewrite
                else "allow_guarded_evolution"
            ),

            "blocked_operations":
            (
                [
                    "identity_rewrite",
                    "dominant_trait_replacement",
                    "ontology_bridge_commit",
                    "high_entropy_mutation",
                    "semantic_anchor_rewire",
                ]
                if block_rewrite
                else []
            ),

            "semantic_anchor_state":
            semantic_anchor_state,
        }

    def rollback_unsafe_evolution(self, context, rewrite_guard):

        identity = context.get(
            "identity_stability_report",
            {},
        )

        stable_snapshot = identity.get(
            "stable_snapshot",
            {},
        )

        if not rewrite_guard.get(
            "block_rewrite",
            False,
        ):

            return {
                "rollback_required":
                False,

                "rollback_actions":
                [
                    "continue_identity_monitoring",
                ],

                "rollback_target":
                {},
            }

        return {
            "rollback_required":
            True,

            "rollback_actions":
            [
                "restore_stable_identity_snapshot",
                "freeze_recovered_traits",
                "suspend_high_entropy_mutations",
                "require_rehearsal_before_commit",
            ],

            "rollback_target":
            stable_snapshot,
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        current_state = self.capture_state(
            context,
        )

        transition_report = self.compare_state_transitions(
            current_state,
        )

        drift_report = self.monitor_drift(
            context,
            transition_report,
        )

        semantic_anchor_report = (
            self.semantic_anchor_graph
            .run_cycle(context)
        )

        rewrite_guard = self.prevent_catastrophic_rewrites(
            transition_report,
            drift_report,
            semantic_anchor_report,
        )

        rollback_report = self.rollback_unsafe_evolution(
            context,
            rewrite_guard,
        )

        report = {
            "system":
            "identity_continuity_guardian",

            "guardian_mode":
            "drift_transition_rewrite_guard",

            "state_transition":
            transition_report,

            "drift_monitoring":
            drift_report,

            "semantic_anchor_graph":
            semantic_anchor_report,

            "catastrophic_rewrite_guard":
            rewrite_guard,

            "rollback":
            rollback_report,

            "identity_guardian_state":
            (
                "rollback_required"
                if rollback_report.get(
                    "rollback_required",
                    False,
                )
                else "rewrite_guarded"
                if drift_report.get(
                    "drift_state",
                )
                in [
                    "identity_fragile",
                    "identity_watched",
                ]
                or semantic_anchor_report.get(
                    "semantic_anchor_state",
                )
                != "semantic_anchor_graph_stable"
                else "continuity_guardian_stable"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.previous_state = current_state

        self.guardian_history.append(
            report,
        )

        self.guardian_history = (
            self.guardian_history[-128:]
        )

        return report


identity_continuity_guardian = IdentityContinuityGuardian()
