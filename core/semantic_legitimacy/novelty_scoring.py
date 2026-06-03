# ============================================
# NEXRYN NOVELTY SCORING
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


class NoveltyScoring:

    def score(self, context):

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        simulations = rehearsal.get(
            "mutation_simulator",
            {},
        ).get(
            "simulations",
            [],
        )

        novelty = _clamp(
            sum(
                item.get(
                    "novelty",
                    0.0,
                )
                for item in simulations
            )
            /
            max(
                len(
                    simulations,
                ),
                1,
            )
        )

        safe_novelty = context.get(
            "controlled_safe_novelty_report",
            {},
        )

        novelty_budget = _clamp(
            safe_novelty.get(
                "novelty_release_budget",
                safe_novelty.get(
                    "novelty_promotion_gate",
                    {},
                ).get(
                    "novelty_release_budget",
                    0.0,
                ),
            ),
        )

        productive_novelty = _clamp(
            novelty * 0.70
            +
            novelty_budget * 0.30
        )

        return {
            "system":
            "novelty_scoring",

            "raw_novelty":
            novelty,

            "novelty_release_budget":
            novelty_budget,

            "productive_novelty":
            productive_novelty,

            "novelty_state":
            (
                "productive"
                if productive_novelty >= 0.55
                else "uncertain"
                if productive_novelty >= 0.28
                else "low_signal"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
