# ============================================
# NEXRYN CONFIDENCE MODEL
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


class ConfidenceModel:

    def estimate(self, context, capability_report, limitation_report):

        available = capability_report.get(
            "available_count",
            0,
        )

        limitation_count = limitation_report.get(
            "limitation_count",
            0,
        )

        thermodynamics = context.get(
            "cognitive_thermodynamics_report",
            {},
        )

        equilibrium = (
            thermodynamics.get(
                "semantic_heat_dissipation",
                {},
            ).get(
                "cognitive_equilibrium",
                0.5,
            )
        )

        confidence = _clamp(
            available / 6 * 0.35
            +
            equilibrium * 0.45
            +
            max(
                0.0,
                1.0 - limitation_count / 5,
            )
            * 0.20
        )

        return {
            "self_confidence":
            confidence,

            "uncertainty":
            _clamp(
                1.0 - confidence,
            ),

            "confidence_state":
            (
                "calibrated"
                if confidence >= 0.55
                else "uncertain"
            ),
        }
