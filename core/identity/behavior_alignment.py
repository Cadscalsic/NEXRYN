# ============================================
# NEXRYN BEHAVIOR ALIGNMENT
# ============================================


class BehaviorAlignment:

    def evaluate(self, snapshot, diff_report):

        action_count = snapshot.get(
            "selected_action_count",
            0,
        )

        protective_mode = (
            snapshot.get(
                "executive_mode",
            )
            == "protective_arbitration"
        )

        aligned = (
            action_count <= 18
            and not protective_mode
            and diff_report.get(
                "identity_shift",
                0.0,
            )
            < 0.55
        )

        return {
            "behavior_aligned":
            aligned,

            "protective_mode_detected":
            protective_mode,

            "selected_action_count":
            action_count,

            "alignment_policy":
            (
                "rollback_behavior"
                if not aligned
                else "maintain_behavior"
            ),
        }
