# ============================================
# NEXRYN FUTURE PROJECTION ENGINE
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


class FutureProjectionEngine:

    def estimate_entropy(self, context):

        thermodynamics = context.get(
            "cognitive_thermodynamics_report",
            {},
        )

        heat = thermodynamics.get(
            "semantic_heat_dissipation",
            {},
        ).get(
            "semantic_heat_after",
            context.get(
                "runtime_entropy",
                0.0,
            ),
        )

        return _clamp(
            max(
                heat,
                context.get(
                    "runtime_entropy",
                    0.0,
                ),
            )
        )

    def simulate_future(self, context, horizon=3):

        entropy = self.estimate_entropy(
            context,
        )

        cooling = context.get(
            "semantic_cooling_system_report",
            {},
        ).get(
            "cooling_strength",
            0.0,
        )

        projections = []

        current_entropy = entropy

        for step in range(1, horizon + 1):

            current_entropy = _clamp(
                current_entropy
                -
                cooling * 0.18
                +
                step * 0.035,
            )

            projections.append({
                "step":
                step,

                "projected_entropy":
                current_entropy,

                "projected_state":
                (
                    "collapse_risk"
                    if current_entropy >= 0.82
                    else "unstable"
                    if current_entropy >= 0.65
                    else "stable"
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            })

        return {
            "system":
            "future_projection_engine",

            "horizon":
            horizon,

            "projections":
            projections,

            "terminal_entropy":
            (
                projections[-1].get(
                    "projected_entropy",
                    entropy,
                )
                if projections
                else entropy
            ),
        }
