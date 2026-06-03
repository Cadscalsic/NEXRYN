# ============================================
# NEXRYN ENVIRONMENTAL COMPETITION
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


class EnvironmentalCompetition:

    def compete(self, niche_report, resource_report):

        resource_pressure = _clamp(
            resource_report.get(
                "resource_pressure",
                0.0,
            ),
        )

        competitors = []

        for item in niche_report.get(
            "niches",
            [],
        ):

            fitness = _clamp(
                item.get(
                    "fitness",
                    0.0,
                ),
            )

            scarcity_cost = _clamp(
                resource_pressure
                *
                (
                    0.18
                    +
                    fitness * 0.12
                )
            )

            competitive_score = _clamp(
                fitness * 0.72
                +
                item.get(
                    "observations",
                    0,
                )
                /
                12
                * 0.10
                -
                scarcity_cost
                +
                (
                    1.0 - resource_pressure
                )
                * 0.18
            )

            competitors.append({
                "trait":
                item.get(
                    "trait",
                    "unknown",
                ),

                "niche":
                item.get(
                    "niche",
                    "general_adaptation",
                ),

                "fitness":
                fitness,

                "scarcity_cost":
                scarcity_cost,

                "competitive_score":
                competitive_score,

                "competition_state":
                (
                    "dominant"
                    if competitive_score >= 0.62
                    else "surviving"
                    if competitive_score >= 0.34
                    else "outcompeted"
                ),
            })

        ranked = sorted(
            competitors,
            key=lambda item: item.get(
                "competitive_score",
                0.0,
            ),
            reverse=True,
        )

        return {
            "system":
            "environmental_competition",

            "competitors":
            ranked,

            "winner_count":
            len([
                item
                for item in ranked
                if item.get(
                    "competition_state",
                )
                in [
                    "dominant",
                    "surviving",
                ]
            ]),

            "outcompeted_count":
            len([
                item
                for item in ranked
                if item.get(
                    "competition_state",
                )
                == "outcompeted"
            ]),

            "competition_state":
            (
                "active_competition"
                if ranked
                else "no_competitors"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
