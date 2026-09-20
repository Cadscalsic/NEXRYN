# ============================================
# NEXRYN GOALS PACKAGE
# ============================================

from runtime.goals.goal_arbitration import (
    GoalArbitrationEngine
)

from runtime.goals.persistent_goal_manager import (
    PersistentGoalManager
)

from runtime.goals.goal_hierarchy_manager import (
    GoalHierarchyManager
)

from runtime.goals.current_goal_authority import (
    GoalAssessment,
    GoalCurrentAuthorityEngine,
    GoalLifecycleStatus,
    GoalProposal,
    GoalSubject,
    goal_current_authority_engine,
)

# ============================================
# GLOBAL GOAL MANAGER
# ============================================

persistent_goal_manager = (
    PersistentGoalManager()
)

# ============================================
# GLOBAL GOAL HIERARCHY
# ============================================

goal_hierarchy_manager = (
    GoalHierarchyManager()
)

# ============================================
# EXPORTS
# ============================================

__all__ = [

    "GoalArbitrationEngine",

    "PersistentGoalManager",

    "GoalHierarchyManager",

    "GoalAssessment",

    "GoalCurrentAuthorityEngine",

    "GoalLifecycleStatus",

    "GoalProposal",

    "GoalSubject",

    "persistent_goal_manager",

    "goal_hierarchy_manager",

    "goal_current_authority_engine"
]
