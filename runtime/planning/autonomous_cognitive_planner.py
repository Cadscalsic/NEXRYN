# ============================================
# NEXRYN AUTONOMOUS COGNITIVE PLANNER
# ============================================

from datetime import datetime
import uuid


# ============================================
# AUTONOMOUS COGNITIVE PLANNER
# ============================================

class AutonomousCognitivePlanner:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # PLANNING STATE
        # ====================================

        self.planning_state = {

            "autonomous_planning":
            True,

            "recursive_goal_expansion":
            True,

            "adaptive_goal_routing":
            True,

            "failure_aware_planning":
            True,

            "execution_scheduling":
            True,

            "planning_cycles":
            0
        }

        # ====================================
        # PLAN HISTORY
        # ====================================

        self.plan_history = []

    # ========================================
    # BUILD PRIMARY GOAL
    # ========================================

    def build_primary_goal(

        self,

        runtime_context
    ):

        winner_hypothesis = (

            runtime_context.get(
                "winner_hypothesis"
            )

            or {}
        )

        return {

            "goal_id":
            str(uuid.uuid4()),

            "goal_type":
            winner_hypothesis.get(
                "type",
                "unknown_goal"
            ),

            "goal_confidence":
            winner_hypothesis.get(
                "confidence",
                0.0
            ),

            "goal_priority":
            "critical",

            "created_at":
            str(datetime.utcnow())
        }

    # ========================================
    # BUILD SUBGOALS
    # ========================================

    def build_subgoals(

        self,

        runtime_context
    ):

        semantic_graph = (

            runtime_context.get(
                "semantic_graph"
            )

            or {}
        )

        concept_nodes = (

            semantic_graph.get(
                "concept_nodes",
                []
            )
        )

        subgoals = []

        for index, node in enumerate(
            concept_nodes
        ):

            subgoals.append({

                "subgoal_id":
                str(uuid.uuid4()),

                "concept":
                node.get(
                    "concept"
                ),

                "confidence":
                node.get(
                    "confidence",
                    0.0
                ),

                "priority":
                index + 1,

                "status":
                "pending"
            })

        return subgoals

    # ========================================
    # BUILD EXECUTION SCHEDULE
    # ========================================

    def build_execution_schedule(

        self,

        subgoals
    ):

        schedule = []

        for index, subgoal in enumerate(
            subgoals
        ):

            schedule.append({

                "execution_step":
                index,

                "target_subgoal":
                subgoal.get(
                    "concept"
                ),

                "scheduled":
                True
            })

        return schedule

    # ========================================
    # BUILD COGNITIVE PLAN
    # ========================================

    def build_cognitive_plan(

        self,

        runtime_context
    ):

        primary_goal = (

            self.build_primary_goal(
                runtime_context
            )
        )

        subgoals = (

            self.build_subgoals(
                runtime_context
            )
        )

        execution_schedule = (

            self.build_execution_schedule(
                subgoals
            )
        )

        plan = {

            "plan_id":
            str(uuid.uuid4()),

            "primary_goal":
            primary_goal,

            "subgoals":
            subgoals,

            "execution_schedule":
            execution_schedule,

            "plan_depth":
            len(subgoals),

            "planning_timestamp":
            str(datetime.utcnow())
        }

        self.plan_history.append(
            plan
        )

        self.planning_state[
            "planning_cycles"
        ] += 1

        return plan

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "planning_cycles":
            self.planning_state[
                "planning_cycles"
            ],

            "stored_plans":
            len(
                self.plan_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL COGNITIVE PLANNER
# ============================================

autonomous_cognitive_planner = (
    AutonomousCognitivePlanner()
)