# ============================================
# NEXRYN EVOLUTIONARY PRESSURE
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


class EvolutionaryPressure:

    def compute(self, lineage_report, archive_report, trait_report, context):

        survived = lineage_report.get(
            "survived_count",
            0,
        )

        collapsed = lineage_report.get(
            "collapsed_count",
            0,
        )

        survival_ratio = _clamp(
            survived
            /
            max(
                survived + collapsed,
                1,
            )
        )

        elite_ratio = _clamp(
            archive_report.get(
                "elite_count",
                0,
            )
            /
            max(
                archive_report.get(
                    "archive_size",
                    0,
                ),
                1,
            )
        )

        adaptive_trait_ratio = _clamp(
            trait_report.get(
                "adaptive_trait_count",
                0,
            )
            /
            max(
                trait_report.get(
                    "trait_count",
                    0,
                ),
                1,
            )
        )

        identity_state = context.get(
            "identity_stability_report",
            {},
        ).get(
            "identity_spine_state",
            "unknown",
        )

        identity_penalty = (
            0.22
            if identity_state == "identity_repair_required"
            else 0.10
            if identity_state == "identity_spine_reinforced"
            else 0.0
        )

        pressure_score = _clamp(
            survival_ratio * 0.42
            +
            elite_ratio * 0.28
            +
            adaptive_trait_ratio * 0.20
            -
            identity_penalty
            +
            0.10
        )

        return {
            "system":
            "evolutionary_pressure",

            "pressure_score":
            pressure_score,

            "survival_ratio":
            survival_ratio,

            "elite_ratio":
            elite_ratio,

            "adaptive_trait_ratio":
            adaptive_trait_ratio,

            "identity_penalty":
            identity_penalty,

            "selection_state":
            (
                "promote_lineage"
                if pressure_score >= 0.62
                else "continue_rehearsal"
                if pressure_score >= 0.34
                else "suppress_lineage"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
