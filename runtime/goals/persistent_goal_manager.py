# ============================================
# NEXRYN PERSISTENT GOAL MANAGER
# ============================================

from datetime import datetime


# ============================================
# PERSISTENT GOAL MANAGER
# ============================================

class PersistentGoalManager:

    # ========================================
    # INITIALIZE GOAL SYSTEM
    # ========================================

    def __init__(self):

        self.active_goals = []

        self.completed_goals = []

        self.failed_goals = []

        self.goal_history = []

        self.goal_state = {

            "dominant_goal":
            None,

            "goal_count":
            0,

            "completed_count":
            0,

            "failed_count":
            0,

            "goal_stability":
            "stable",

            "strategic_mode":
            "adaptive"
        }

    # ============================================
    # REGISTER GOAL
    # ============================================

    def register_goal(

        self,

        goal_type,

        priority=1.0,

        persistence=1.0,

        metadata=None
    ):

        if metadata is None:

            metadata = {}

        goal = {

            "goal_id":

            len(
                self.goal_history
            ) + 1,

            "goal_type":
            goal_type,

            "priority":
            priority,

            "persistence":
            persistence,

            "progress":
            0.0,

            "status":
            "active",

            "created_at":
            str(
                datetime.utcnow()
            ),

            "last_updated":
            str(
                datetime.utcnow()
            ),

            "metadata":
            metadata
        }

        self.active_goals.append(
            goal
        )

        self.goal_history.append(
            goal
        )

        self.goal_state[
            "goal_count"
        ] = len(
            self.active_goals
        )

        self.update_dominant_goal()

        return goal

    # ============================================
    # UPDATE GOAL PROGRESS
    # ============================================

    def update_goal_progress(

        self,

        goal_type,

        progress
    ):

        for goal in self.active_goals:

            if goal.get(
                "goal_type"
            ) == goal_type:

                goal[
                    "progress"
                ] = round(
                    progress,
                    4
                )

                goal[
                    "last_updated"
                ] = str(
                    datetime.utcnow()
                )

                # ================================
                # COMPLETE GOAL
                # ================================

                if progress >= 1.0:

                    self.complete_goal(
                        goal_type
                    )

                break

    # ============================================
    # COMPLETE GOAL
    # ============================================

    def complete_goal(

        self,

        goal_type
    ):

        remaining_goals = []

        for goal in self.active_goals:

            if goal.get(
                "goal_type"
            ) == goal_type:

                goal[
                    "status"
                ] = "completed"

                goal[
                    "completed_at"
                ] = str(
                    datetime.utcnow()
                )

                self.completed_goals.append(
                    goal
                )

            else:

                remaining_goals.append(
                    goal
                )

        self.active_goals = (
            remaining_goals
        )

        self.goal_state[
            "completed_count"
        ] = len(
            self.completed_goals
        )

        self.update_dominant_goal()

    # ============================================
    # FAIL GOAL
    # ============================================

    def fail_goal(

        self,

        goal_type,

        reason=None
    ):

        remaining_goals = []

        for goal in self.active_goals:

            if goal.get(
                "goal_type"
            ) == goal_type:

                goal[
                    "status"
                ] = "failed"

                goal[
                    "failure_reason"
                ] = reason

                goal[
                    "failed_at"
                ] = str(
                    datetime.utcnow()
                )

                self.failed_goals.append(
                    goal
                )

            else:

                remaining_goals.append(
                    goal
                )

        self.active_goals = (
            remaining_goals
        )

        self.goal_state[
            "failed_count"
        ] = len(
            self.failed_goals
        )

        self.goal_state[
            "goal_stability"
        ] = "degraded"

        self.update_dominant_goal()

    # ============================================
    # UPDATE DOMINANT GOAL
    # ============================================

    def update_dominant_goal(self):

        if len(
            self.active_goals
        ) == 0:

            self.goal_state[
                "dominant_goal"
            ] = None

            return

        ranked_goals = sorted(

            self.active_goals,

            key=lambda x:

            x.get(
                "priority",
                0.0
            )

            *

            x.get(
                "persistence",
                0.0
            ),

            reverse=True
        )

        self.goal_state[
            "dominant_goal"
        ] = ranked_goals[
            0
        ].get(
            "goal_type"
        )

    # ============================================
    # ADAPT GOAL PRIORITIES
    # ============================================

    def adapt_goal_priorities(

        self,

        evaluation_result
    ):

        success = evaluation_result.get(

            "success",

            False
        )

        accuracy = evaluation_result.get(

            "accuracy",

            0.0
        )

        for goal in self.active_goals:

            if success:

                goal[
                    "priority"
                ] = min(

                    goal.get(
                        "priority",
                        1.0
                    )

                    + 0.05,

                    5.0
                )

            else:

                goal[
                    "priority"
                ] = max(

                    goal.get(
                        "priority",
                        1.0
                    )

                    - 0.05,

                    0.1
                )

            goal[
                "persistence"
            ] = round(

                (
                    goal.get(
                        "persistence",
                        1.0
                    )

                    + accuracy
                )

                / 2,

                4
            )

        self.update_dominant_goal()

    # ============================================
    # BUILD GOAL REPORT
    # ============================================

    def build_goal_report(self):

        return {

            "goal_state":
            self.goal_state,

            "active_goals":
            self.active_goals,

            "completed_goals":
            self.completed_goals,

            "failed_goals":
            self.failed_goals,

            "goal_history_size":

            len(
                self.goal_history
            )
        }

    # ============================================
    # BUILD EXECUTIVE INTENT
    # ============================================

    def build_executive_intent(self):

        dominant_goal = (

            self.goal_state.get(
                "dominant_goal"
            )
        )

        # ====================================
        # FALLBACK TO LATEST COMPLETED GOAL
        # ====================================

        if dominant_goal is None:

            if len(
                self.completed_goals
            ) > 0:

                dominant_goal = (

                    self.completed_goals[-1].get(
                        "goal_type"
                    )
                )

        return {

            "dominant_goal":

            dominant_goal,

            "strategic_mode":

            self.goal_state.get(
                "strategic_mode"
            ),

            "goal_stability":

            self.goal_state.get(
                "goal_stability"
            ),

            "active_goal_count":

            len(
                self.active_goals
            ),

            "completed_goal_count":

            len(
                self.completed_goals
            )
        }