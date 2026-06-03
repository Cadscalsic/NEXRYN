# ============================================
# NEXRYN CORE GOAL MANAGER
# ============================================

from datetime import datetime

from core.goals.goal_conflict_resolver import (
    GoalConflictResolver,
)

from core.goals.goal_priority import (
    GoalPriorityEngine,
)


class GoalManager:

    def __init__(self):

        self.goals = []
        self.goal_events = []
        self.priority_engine = GoalPriorityEngine()
        self.conflict_resolver = GoalConflictResolver()
        self.ensure_core_goals()

    def ensure_core_goals(self):

        if self.goals:

            return

        self.register_goal(
            "preserve_identity",
            "core",
            priority=1.0,
            persistence=1.0,
            urgency=0.8,
        )

        self.register_goal(
            "reduce_entropy",
            "core",
            priority=0.95,
            persistence=1.0,
            urgency=0.9,
        )

        self.register_goal(
            "maintain_task_accuracy",
            "core",
            priority=0.92,
            persistence=0.95,
            urgency=0.7,
        )

        self.register_goal(
            "maximize_exploration",
            "strategic",
            priority=0.62,
            persistence=0.55,
            urgency=0.35,
        )

    def register_goal(
        self,
        goal_type,
        level,
        priority=0.5,
        persistence=0.5,
        urgency=0.3,
        metadata=None,
    ):

        if metadata is None:

            metadata = {}

        goal = {
            "goal_id":
            f"{level}:{goal_type}",

            "goal_type":
            goal_type,

            "level":
            level,

            "priority":
            priority,

            "persistence":
            persistence,

            "urgency":
            urgency,

            "status":
            "active",

            "metadata":
            metadata,

            "created_at":
            str(
                datetime.utcnow()
            ),
        }

        existing = [
            item
            for item in self.goals
            if item.get(
                "goal_id",
            )
            == goal.get(
                "goal_id",
            )
        ]

        if not existing:

            self.goals.append(
                goal,
            )

            self.goal_events.append({
                "event":
                "goal_registered",

                "goal_id":
                goal.get(
                    "goal_id",
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            })

        return goal

    def ingest_context_goals(self, context):

        task_path = context.get(
            "task_path",
        )

        if task_path:

            self.register_goal(
                "solve_current_task",
                "task",
                priority=0.86,
                persistence=0.45,
                urgency=0.90,
                metadata={
                    "task_path":
                    task_path,
                },
            )

        novelty = context.get(
            "controlled_safe_novelty_report",
            {},
        )

        if novelty:

            self.register_goal(
                "evaluate_safe_novelty",
                "temporary",
                priority=0.48,
                persistence=0.22,
                urgency=0.35,
            )

    def build_layers(self, goals):

        layers = {
            "core_goals": [],
            "strategic_goals": [],
            "task_goals": [],
            "temporary_goals": [],
        }

        for goal in goals:

            level = goal.get(
                "level",
            )

            key = f"{level}_goals"

            if key in layers:

                layers[key].append(
                    goal,
                )

        return layers

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        self.ingest_context_goals(
            context,
        )

        ranked = self.priority_engine.rank_goals(
            self.goals,
            context,
        )

        resolution = self.conflict_resolver.resolve(
            ranked,
        )

        resolved_goals = resolution.get(
            "resolved_goals",
            ranked,
        )

        report = {
            "system":
            "goal_hierarchy_system",

            "layers":
            self.build_layers(
                resolved_goals,
            ),

            "ranked_goals":
            resolved_goals,

            "dominant_goal":
            (
                resolved_goals[0]
                if resolved_goals
                else {}
            ),

            "conflicts":
            resolution.get(
                "conflicts",
                [],
            ),

            "objective_persistence":
            True,

            "long_term_coherence":
            True,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        return report


goal_manager = (
    GoalManager()
)
