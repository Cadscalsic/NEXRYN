# ============================================
# NEXRYN SEMANTIC HOMEOSTASIS
# ============================================


def _clamp(value):

    try:
        value = float(
            value,
        )
    except Exception:
        value = 0.0

    return round(
        max(
            0.0,
            min(
                value,
                1.0,
            ),
        ),
        4,
    )


class SemanticHomeostasis:

    def entropy_balancing(self, context):

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                context.get(
                    "entropy",
                    0.0,
                ),
            )
        )

        return {
            "entropy":
            entropy,

            "entropy_balance_state":
            (
                "entropy_cooling_required"
                if entropy >= 0.68
                else "entropy_balanced"
            ),
        }

    def identity_stabilization(self, context):

        continuity = _clamp(
            context.get(
                "identity_continuity",
                0.72,
            )
        )

        return {
            "identity_continuity":
            continuity,

            "identity_stabilization_state":
            (
                "identity_stabilization_required"
                if continuity < 0.68
                else "identity_stable"
            ),
        }

    def adaptive_cooling(self, entropy_report, identity_report):

        cooling = (
            entropy_report.get(
                "entropy_balance_state",
            )
            == "entropy_cooling_required"
            or identity_report.get(
                "identity_stabilization_state",
            )
            == "identity_stabilization_required"
        )

        return {
            "adaptive_cooling_active":
            cooling,

            "cooling_policy":
            (
                "slow_mutations_and_freeze_unverified_fusions"
                if cooling
                else "normal_adaptive_temperature"
            ),
        }

    def pressure_decay(self, context):

        pressure = _clamp(
            context.get(
                "memory_pressure_score",
                0.0,
            )
        )

        return {
            "pressure_score":
            pressure,

            "pressure_decay_state":
            (
                "pressure_decay_required"
                if pressure >= 0.75
                else "pressure_nominal"
            ),
        }

    def run_cycle(self, context):

        entropy = self.entropy_balancing(
            context,
        )
        identity = self.identity_stabilization(
            context,
        )
        cooling = self.adaptive_cooling(
            entropy,
            identity,
        )
        pressure = self.pressure_decay(
            context,
        )

        return {
            "system":
            "semantic_homeostasis",

            "entropy_balancing":
            entropy,

            "identity_stabilization":
            identity,

            "adaptive_cooling":
            cooling,

            "pressure_decay":
            pressure,

            "homeostasis_state":
            (
                "semantic_cooling"
                if cooling.get(
                    "adaptive_cooling_active",
                    False,
                )
                or pressure.get(
                    "pressure_decay_state",
                )
                == "pressure_decay_required"
                else "semantic_homeostasis_stable"
            ),
        }


semantic_homeostasis = SemanticHomeostasis()
