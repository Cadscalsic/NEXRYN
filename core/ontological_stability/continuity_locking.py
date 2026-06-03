class ContinuityLocking:

    def run_cycle(self, spine_report, identity_report):

        lock_required = (
            spine_report.get(
                "fragile_semantic_spine",
                False,
            )
            or identity_report.get(
                "blocked_identity_fusions",
                0,
            )
            > 0
        )

        return {
            "system":
            "continuity_locking",

            "continuity_lock_required":
            lock_required,

            "locked_domains":
            [
                "identity_anchors",
                "causal_continuity",
                "semantic_spine",
            ]
            if lock_required
            else [],

            "continuity_state":
            (
                "continuity_lock_engaged"
                if lock_required
                else "continuity_lock_standby"
            ),
        }
