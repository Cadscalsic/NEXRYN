# ============================================
# NEXRYN RECURSIVE GOAL HIERARCHY MANAGER
# ============================================

from datetime import datetime
import uuid


# ============================================
# GOAL HIERARCHY MANAGER
# ============================================

class GoalHierarchyManager:

    # ========================================
    # INITIALIZE HIERARCHY
    # ========================================

    def __init__(self):

        # ====================================
        # GOAL STORAGE
        # ====================================

        self.goal_hierarchy = []

        self.root_goals = []

        self.subgoals = {}

        self.completed_hierarchy = []

        self.failed_hierarchy = []

        # ====================================
        # GOAL GRAPH
        # ====================================

        self.goal_graph = []

        self.goal_dependencies = {}

        self.execution_routes = []

        self.blocked_goals = []

        self.goal_memory = []

        self.goal_events = []

        # ====================================
        # EXECUTIVE STATE
        # ====================================

        self.executive_state = {

            "planning_mode":
            "recursive_executive_planning",

            "hierarchical_reasoning":
            "enabled",

            "adaptive_replanning":
            "enabled",

            "goal_governance":
            "active",

            "recursive_execution":
            "enabled",

            "executive_cycles":
            0
        }

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        payload
    ):

        event = {

            "event_id":
            str(uuid.uuid4()),

            "event_type":
            event_type,

            "payload":
            payload,

            "timestamp":
            str(datetime.utcnow())
        }

        self.goal_events.append(
            event
        )

        return event

    # ========================================
    # REGISTER ROOT GOAL
    # ========================================

    def register_root_goal(

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
            str(uuid.uuid4()),

            "goal_type":
            goal_type,

            "goal_level":
            "root",

            "priority":
            priority,

            "persistence":
            persistence,

            "status":
            "active",

            "progress":
            0.0,

            "created_at":
            str(datetime.utcnow()),

            "metadata":
            metadata
        }

        self.goal_hierarchy.append(
            goal
        )

        self.root_goals.append(
            goal
        )

        self.subgoals[
            goal_type
        ] = []

        self.goal_memory.append(
            goal
        )

        self.register_event(

            "root_goal_registered",

            goal
        )

        return goal

    # ========================================
    # REGISTER SUBGOAL
    # ========================================

    def register_subgoal(

        self,

        parent_goal,

        subgoal_type,

        priority=1.0,

        metadata=None
    ):

        if metadata is None:

            metadata = {}

        subgoal = {

            "goal_id":
            str(uuid.uuid4()),

            "goal_type":
            subgoal_type,

            "goal_level":
            "subgoal",

            "parent_goal":
            parent_goal,

            "priority":
            priority,

            "status":
            "active",

            "progress":
            0.0,

            "created_at":
            str(datetime.utcnow()),

            "metadata":
            metadata
        }

        self.goal_hierarchy.append(
            subgoal
        )

        if parent_goal not in self.subgoals:

            self.subgoals[
                parent_goal
            ] = []

        self.subgoals[
            parent_goal
        ].append(
            subgoal
        )

        # ====================================
        # GOAL DEPENDENCIES
        # ====================================

        if parent_goal not in self.goal_dependencies:

            self.goal_dependencies[
                parent_goal
            ] = []

        self.goal_dependencies[
            parent_goal
        ].append(
            subgoal_type
        )

        self.goal_memory.append(
            subgoal
        )

        self.register_event(

            "subgoal_registered",

            subgoal
        )

        return subgoal

    # ========================================
    # UPDATE GOAL PROGRESS
    # ========================================

    def update_goal_progress(

        self,

        goal_type,

        progress
    ):

        for goal in self.goal_hierarchy:

            if goal.get(
                "goal_type"
            ) == goal_type:

                goal[
                    "progress"
                ] = round(
                    progress,
                    4
                )

                if progress >= 1.0:

                    goal[
                        "status"
                    ] = "completed"

                    goal[
                        "completed_at"
                    ] = str(
                        datetime.utcnow()
                    )

                    self.completed_hierarchy.append(
                        goal
                    )

                    self.register_event(

                        "goal_completed",

                        goal
                    )

                break

        self.update_parent_progress()

    # ========================================
    # UPDATE PARENT PROGRESS
    # ========================================

    def update_parent_progress(self):

        for root_goal in self.root_goals:

            root_type = root_goal.get(
                "goal_type"
            )

            children = self.subgoals.get(
                root_type,
                []
            )

            if len(children) == 0:

                continue

            weighted_progress = 0.0

            total_weight = 0.0

            for child in children:

                progress = child.get(
                    "progress",
                    0.0
                )

                priority = child.get(
                    "priority",
                    1.0
                )

                weighted_progress += (
                    progress * priority
                )

                total_weight += priority

            if total_weight == 0:

                continue

            average_progress = (

                weighted_progress
                /
                total_weight
            )

            root_goal[
                "progress"
            ] = round(
                average_progress,
                4
            )

            if average_progress >= 1.0:

                root_goal[
                    "status"
                ] = "completed"

    # ========================================
    # FAIL GOAL
    # ========================================

    def fail_goal(

        self,

        goal_type,

        reason=None
    ):

        for goal in self.goal_hierarchy:

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

                self.failed_hierarchy.append(
                    goal
                )

                self.register_event(

                    "goal_failed",

                    goal
                )

                break

    # ========================================
    # BUILD GOAL GRAPH
    # ========================================

    def build_goal_graph(self):

        self.goal_graph = []

        for root_goal in self.root_goals:

            root_type = root_goal.get(
                "goal_type"
            )

            children = self.subgoals.get(
                root_type,
                []
            )

            for child in children:

                edge = {

                    "source":
                    root_type,

                    "target":
                    child.get(
                        "goal_type"
                    ),

                    "relation":
                    "hierarchical_dependency"
                }

                self.goal_graph.append(
                    edge
                )

        return self.goal_graph

    # ========================================
    # DETECT BLOCKED GOALS
    # ========================================

    def detect_blocked_goals(self):

        blocked = []

        for goal in self.goal_hierarchy:

            progress = goal.get(
                "progress",
                0.0
            )

            status = goal.get(
                "status"
            )

            if (

                status == "active"

                and

                progress <= 0.05
            ):

                blocked.append(
                    goal
                )

        self.blocked_goals = blocked

        return blocked

    # ========================================
    # EXECUTIVE REPLANNING
    # ========================================

    def executive_replanning(self):

        replanning = []

        for goal in self.blocked_goals:

            replanning.append({

                "goal":
                goal.get(
                    "goal_type"
                ),

                "action":
                "adaptive_restructuring",

                "priority":
                "high"
            })

        return replanning

    # ========================================
    # BUILD HIERARCHY REPORT
    # ========================================

    def build_hierarchy_report(self):

        return {

            "total_goals":
            len(self.goal_hierarchy),

            "root_goals":
            self.root_goals,

            "subgoal_map":
            self.subgoals,

            "completed_goals":
            self.completed_hierarchy,

            "failed_goals":
            self.failed_hierarchy,

            "goal_graph":
            self.goal_graph,

            "blocked_goals":
            self.blocked_goals
        }

    # ========================================
    # BUILD STRATEGIC SUMMARY
    # ========================================

    def build_strategic_summary(self):

        active_goals = 0

        completed_goals = 0

        failed_goals = 0

        for goal in self.goal_hierarchy:

            status = goal.get(
                "status"
            )

            if status == "active":

                active_goals += 1

            elif status == "completed":

                completed_goals += 1

            elif status == "failed":

                failed_goals += 1

        return {

            "active_goals":
            active_goals,

            "completed_goals":
            completed_goals,

            "failed_goals":
            failed_goals,

            "hierarchy_depth":
            len(self.subgoals),

            "strategic_state":

            "stable"

            if failed_goals == 0

            else "adaptive_recovery"
        }

    # ========================================
    # BUILD EXECUTIVE MISSION
    # ========================================

    def build_executive_mission(self):

        dominant_goal = None

        highest_priority = 0.0

        for goal in self.root_goals:

            priority = goal.get(
                "priority",
                0.0
            )

            if priority > highest_priority:

                highest_priority = priority

                dominant_goal = goal.get(
                    "goal_type"
                )

        return {

            "dominant_mission":
            dominant_goal,

            "mission_count":
            len(self.root_goals),

            "strategic_focus":
            "hierarchical_goal_execution",

            "executive_mode":
            "persistent_recursive_planning"
        }

    # ========================================
    # RUN EXECUTIVE CYCLE
    # ========================================

    def run_executive_cycle(self):

        goal_graph = (
            self.build_goal_graph()
        )

        blocked_goals = (
            self.detect_blocked_goals()
        )

        replanning = (
            self.executive_replanning()
        )

        executive_mission = (
            self.build_executive_mission()
        )

        strategic_summary = (
            self.build_strategic_summary()
        )

        self.executive_state[
            "executive_cycles"
        ] += 1

        report = {

            "goal_graph":
            goal_graph,

            "blocked_goals":
            blocked_goals,

            "replanning":
            replanning,

            "executive_mission":
            executive_mission,

            "strategic_summary":
            strategic_summary,

            "executive_state":
            self.executive_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "executive_cycle",

            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "total_goals":
            len(self.goal_hierarchy),

            "root_goals":
            len(self.root_goals),

            "subgoal_groups":
            len(self.subgoals),

            "completed_goals":
            len(self.completed_hierarchy),

            "failed_goals":
            len(self.failed_hierarchy),

            "goal_graph":
            len(self.goal_graph),

            "blocked_goals":
            len(self.blocked_goals),

            "goal_events":
            len(self.goal_events),

            "goal_memory":
            len(self.goal_memory),

            "executive_state":
            self.executive_state
        }