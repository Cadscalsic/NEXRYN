# ============================================
# NEXRYN IDENTITY STABILITY CORE
# ============================================

from datetime import datetime

from core.identity.behavior_alignment import (
    BehaviorAlignment,
)

from core.identity.causal_memory import (
    CausalMemory,
)

from core.identity.continuity_verifier import (
    ContinuityVerifier,
)

from core.identity.identity_diff import (
    IdentityDiff,
)

from core.identity.identity_anchor import (
    IdentityAnchor,
)

from core.identity.identity_recovery import (
    IdentityRecovery,
)

from core.identity.identity_snapshot import (
    IdentitySnapshot,
)

from core.identity.self_consistency_graph import (
    SelfConsistencyGraph,
)


class IdentityStabilityCore:

    def __init__(self):

        self.identity_snapshot = IdentitySnapshot()
        self.identity_anchor = IdentityAnchor()
        self.causal_memory = CausalMemory()
        self.self_consistency_graph = SelfConsistencyGraph()
        self.continuity_verifier = ContinuityVerifier()
        self.identity_diff = IdentityDiff()
        self.identity_recovery = IdentityRecovery()
        self.behavior_alignment = BehaviorAlignment()
        self.identity_history = []
        self.rollback_active = False
        self.recovery_streak = 0

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        current_snapshot = self.identity_snapshot.capture(
            context,
        )

        stable_snapshot = self.identity_snapshot.latest_stable()

        diff_report = self.identity_diff.compare(
            current_snapshot,
            stable_snapshot,
        )

        alignment_report = self.behavior_alignment.evaluate(
            current_snapshot,
            diff_report,
        )

        anchor_report = self.identity_anchor.anchor(
            context,
        )

        causal_memory_report = self.causal_memory.record(
            context,
        )

        graph_report = self.self_consistency_graph.build(
            anchor_report,
            causal_memory_report,
            context,
        )

        continuity_report = self.continuity_verifier.verify(
            anchor_report,
            graph_report,
            context,
        )

        recovery_report = self.identity_recovery.rollback_behavior(
            diff_report,
            stable_snapshot,
        )
        raw_rollback_required = recovery_report.get(
            "rollback_required",
            False,
        )

        if raw_rollback_required:

            self.rollback_active = True
            self.recovery_streak = 0
            identity_stability_state = "rollback_required"

        elif self.rollback_active:

            self.recovery_streak += 1

            if self.recovery_streak >= 3:

                self.rollback_active = False
                identity_stability_state = "stable"

            else:

                identity_stability_state = "recovery_monitoring"

        else:

            self.recovery_streak = 0
            identity_stability_state = "stable"

        report = {
            "system":
            "identity_stability_core",

            "identity_snapshot":
            current_snapshot,

            "stable_snapshot":
            stable_snapshot,

            "identity_diff":
            diff_report,

            "behavior_alignment":
            alignment_report,

            "identity_anchor":
            anchor_report,

            "causal_memory":
            causal_memory_report,

            "self_consistency_graph":
            graph_report,

            "continuity_verifier":
            continuity_report,

            "identity_recovery":
            recovery_report,

            "identity_spine_state":
            (
                "identity_spine_reinforced"
                if continuity_report.get(
                    "verification_state",
                )
                == "fragile_verified"
                else "identity_repair_required"
                if continuity_report.get(
                    "verification_state",
                )
                == "blocked_for_identity_repair"
                else "identity_spine_stable"
            ),

            "identity_stability_state":
            identity_stability_state,

            "identity_recovery_confirmation":
            {
                "raw_rollback_required":
                raw_rollback_required,

                "rollback_active":
                self.rollback_active,

                "recovery_streak":
                self.recovery_streak,

                "required_recovery_cycles":
                3,
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.identity_history.append(
            report,
        )

        self.identity_history = (
            self.identity_history[-128:]
        )

        return report


identity_stability_core = (
    IdentityStabilityCore()
)
