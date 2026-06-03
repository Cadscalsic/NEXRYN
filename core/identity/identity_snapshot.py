# ============================================
# NEXRYN IDENTITY SNAPSHOT
# ============================================

from datetime import datetime


class IdentitySnapshot:

    def __init__(self):

        self.snapshots = []

    def capture(self, context):

        snapshot = {
            "identity_state":
            context.get(
                "cognitive_identity_report",
                {},
            ).get(
                "identity_state",
                "unknown",
            ),

            "identity_drift":
            context.get(
                "identity_core_report",
                {},
            ).get(
                "identity_drift",
                context.get(
                    "identity_drift",
                    0.0,
                ),
            ),

            "continuity_state":
            context.get(
                "identity_core_report",
                {},
            ).get(
                "continuity_state",
                "unknown",
            ),

            "executive_mode":
            context.get(
                "executive_mode",
                context.get(
                    "executive_arbitration_report",
                    {},
                ).get(
                    "executive_mode",
                    "unknown",
                ),
            ),

            "selected_action_count":
            len(
                context.get(
                    "selected_actions",
                    context.get(
                        "executive_arbitration_report",
                        {},
                    ).get(
                        "selected_actions",
                        [],
                    ),
                )
            )
            if isinstance(
                context.get(
                    "selected_actions",
                    context.get(
                        "executive_arbitration_report",
                        {},
                    ).get(
                        "selected_actions",
                        [],
                    ),
                ),
                list,
            )
            else 0,

            "behavior_shift":
            context.get(
                "identity_core_report",
                {},
            ).get(
                "behavior_shift",
                {},
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.snapshots.append(
            snapshot,
        )

        self.snapshots = (
            self.snapshots[-128:]
        )

        return snapshot

    def latest_stable(self):

        for snapshot in reversed(
            self.snapshots,
        ):

            if snapshot.get(
                "identity_drift",
                1.0,
            ) < 0.45 and not snapshot.get(
                "behavior_shift",
                {},
            ).get(
                "shift_detected",
                False,
            ):

                return snapshot

        return (
            self.snapshots[0]
            if self.snapshots
            else {}
        )
