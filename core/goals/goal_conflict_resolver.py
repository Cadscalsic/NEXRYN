# ============================================
# NEXRYN GOAL CONFLICT RESOLVER
# ============================================


class GoalConflictResolver:

    CONFLICT_PAIRS = {
        ("preserve_identity", "maximize_exploration"):
        "identity_exploration_conflict",

        ("reduce_entropy", "expand_search"):
        "thermal_exploration_conflict",

        ("conserve_energy", "increase_recursion"):
        "energy_recursion_conflict",
    }

    def detect_conflicts(self, goals):

        active = [
            goal
            for goal in goals
            if goal.get(
                "status",
                "active",
            )
            == "active"
        ]

        conflicts = []

        for first in active:

            for second in active:

                if first is second:

                    continue

                pair = (
                    first.get(
                        "goal_type",
                    ),
                    second.get(
                        "goal_type",
                    ),
                )

                conflict_type = self.CONFLICT_PAIRS.get(
                    pair,
                )

                if not conflict_type:

                    continue

                conflicts.append({
                    "conflict_type":
                    conflict_type,

                    "first_goal":
                    first.get(
                        "goal_id",
                    ),

                    "second_goal":
                    second.get(
                        "goal_id",
                    ),

                    "resolution":
                    "rank_by_priority_and_persistence",
                })

        return conflicts

    def resolve(self, ranked_goals):

        conflicts = self.detect_conflicts(
            ranked_goals,
        )

        blocked_goal_ids = set()

        for conflict in conflicts:

            first_index = next(
                (
                    index
                    for index, goal in enumerate(
                        ranked_goals,
                    )
                    if goal.get(
                        "goal_id",
                    )
                    == conflict.get(
                        "first_goal",
                    )
                ),
                999,
            )

            second_index = next(
                (
                    index
                    for index, goal in enumerate(
                        ranked_goals,
                    )
                    if goal.get(
                        "goal_id",
                    )
                    == conflict.get(
                        "second_goal",
                    )
                ),
                999,
            )

            blocked_goal_ids.add(
                conflict.get(
                    "second_goal"
                    if first_index < second_index
                    else "first_goal",
                )
            )

        resolved = []

        for goal in ranked_goals:

            enriched = dict(
                goal,
            )

            if goal.get(
                "goal_id",
            ) in blocked_goal_ids:

                enriched[
                    "status"
                ] = "deferred_by_conflict"

            resolved.append(
                enriched,
            )

        return {
            "conflicts":
            conflicts,

            "resolved_goals":
            resolved,

            "blocked_goal_ids":
            sorted(
                blocked_goal_ids,
            ),
        }
