# ============================================
# NEXRYN GOAL PRIORITY ENGINE
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


class GoalPriorityEngine:

    LEVEL_WEIGHTS = {
        "core": 1.00,
        "strategic": 0.82,
        "task": 0.64,
        "temporary": 0.38,
    }

    def score_goal(self, goal, context=None):

        if context is None:

            context = {}

        base = goal.get(
            "priority",
            0.5,
        )

        persistence = goal.get(
            "persistence",
            0.5,
        )

        urgency = goal.get(
            "urgency",
            0.3,
        )

        level_weight = self.LEVEL_WEIGHTS.get(
            goal.get(
                "level",
                "temporary",
            ),
            0.38,
        )

        entropy = context.get(
            "runtime_entropy",
            0.0,
        )

        thermal_modifier = (
            0.92
            if entropy >= 0.70
            and goal.get(
                "level",
            )
            in [
                "core",
                "strategic",
            ]
            else 0.72
            if entropy >= 0.70
            else 1.0
        )

        return _clamp(
            (
                base * 0.45
                +
                persistence * 0.30
                +
                urgency * 0.25
            )
            *
            level_weight
            *
            thermal_modifier
        )

    def rank_goals(self, goals, context=None):

        ranked = []

        for goal in goals:

            enriched = dict(
                goal,
            )

            enriched[
                "priority_score"
            ] = self.score_goal(
                goal,
                context,
            )

            ranked.append(
                enriched,
            )

        return sorted(
            ranked,
            key=lambda goal: goal.get(
                "priority_score",
                0.0,
            ),
            reverse=True,
        )
