"""Budgets for lightweight object motion reasoning."""

MAX_MOTION_SIMULATIONS = 10
MAX_COLLISION_CHECKS = 50
MAX_GRAVITY_ITERATIONS = 20
MAX_SUPPORT_SURFACES = 10


class MotionBudgetController:
    def __init__(self):
        self.motion_simulations = 0
        self.collision_checks = 0
        self.gravity_iterations = 0

    def reset(self):
        self.motion_simulations = 0
        self.collision_checks = 0
        self.gravity_iterations = 0

    def can_simulate_motion(self):
        return self.motion_simulations < MAX_MOTION_SIMULATIONS

    def can_check_collision(self):
        return self.collision_checks < MAX_COLLISION_CHECKS

    def can_iterate_gravity(self):
        return self.gravity_iterations < MAX_GRAVITY_ITERATIONS

    def record_motion(self):
        self.motion_simulations += 1

    def record_collision(self):
        self.collision_checks += 1

    def record_gravity(self):
        self.gravity_iterations += 1

    def report(self):
        return {
            "max_motion_simulations": MAX_MOTION_SIMULATIONS,
            "max_collision_checks": MAX_COLLISION_CHECKS,
            "max_gravity_iterations": MAX_GRAVITY_ITERATIONS,
            "max_support_surfaces": MAX_SUPPORT_SURFACES,
            "motion_simulations": self.motion_simulations,
            "collision_checks": self.collision_checks,
            "gravity_iterations": self.gravity_iterations,
        }


motion_budget_controller = MotionBudgetController()


__all__ = [
    "MAX_MOTION_SIMULATIONS",
    "MAX_COLLISION_CHECKS",
    "MAX_GRAVITY_ITERATIONS",
    "MAX_SUPPORT_SURFACES",
    "MotionBudgetController",
    "motion_budget_controller",
]
