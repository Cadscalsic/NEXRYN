# ============================================
# NEXRYN IDENTITY RECOVERY
# ============================================

from datetime import datetime


class IdentityRecovery:

    def rollback_behavior(self, diff_report, stable_snapshot):

        should_rollback = (
            diff_report.get(
                "identity_shift",
                0.0,
            )
            >= 0.55
            or diff_report.get(
                "behavior_shift_detected",
                False,
            )
        )

        return {
            "rollback_required":
            should_rollback,

            "rollback_target":
            stable_snapshot,

            "recovery_actions":
            (
                [
                    "rollback_behavior",
                    "restore_stable_identity_snapshot",
                    "reduce_selected_actions",
                    "exit_protective_arbitration",
                ]
                if should_rollback
                else [
                    "monitor_identity_drift",
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
