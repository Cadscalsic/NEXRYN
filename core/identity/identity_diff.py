# ============================================
# NEXRYN IDENTITY DIFF
# ============================================


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


class IdentityDiff:

    def compare(self, current_snapshot, stable_snapshot):

        if not stable_snapshot:

            stable_snapshot = {}

        drift_delta = _clamp(
            current_snapshot.get(
                "identity_drift",
                0.0,
            )
            -
            stable_snapshot.get(
                "identity_drift",
                0.0,
            ),
            minimum=0.0,
        )

        action_delta = max(
            current_snapshot.get(
                "selected_action_count",
                0,
            )
            -
            stable_snapshot.get(
                "selected_action_count",
                0,
            ),
            0,
        )

        mode_changed = (
            current_snapshot.get(
                "executive_mode",
            )
            !=
            stable_snapshot.get(
                "executive_mode",
            )
            if stable_snapshot
            else False
        )

        behavior_shift = current_snapshot.get(
            "behavior_shift",
            {},
        ).get(
            "shift_detected",
            False,
        )

        shift_score = _clamp(
            drift_delta * 0.45
            +
            min(
                action_delta,
                30,
            )
            / 30
            * 0.25
            +
            (
                0.20
                if mode_changed
                else 0.0
            )
            +
            (
                0.30
                if behavior_shift
                else 0.0
            )
        )

        return {
            "identity_shift":
            shift_score,

            "drift_delta":
            drift_delta,

            "action_delta":
            action_delta,

            "mode_changed":
            mode_changed,

            "behavior_shift_detected":
            behavior_shift,

            "shift_state":
            (
                "critical"
                if shift_score >= 0.55
                else "elevated"
                if shift_score >= 0.30
                else "stable"
            ),
        }
