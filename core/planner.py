import itertools
import numpy as np

from core.transformations import (
    Rotate,
    Flip,
    Mirror,
    Translate,
    Scale,
    Recolor,
    Duplicate,
    Crop,
    Fill,
    Delete
)


# ============================================================
# PLAN STEP
# ============================================================

class PlanStep:

    def __init__(self, transformation):

        self.transformation = transformation

    def apply(self, grid):

        return self.transformation.apply(grid)

    def __repr__(self):

        return str(self.transformation)


# ============================================================
# TRANSFORMATION PLAN
# ============================================================

class TransformationPlan:

    def __init__(self, steps=None):

        self.steps = steps if steps else []

    def add_step(self, transformation):

        self.steps.append(
            PlanStep(transformation)
        )

    def execute(self, grid):

        result = np.array(grid)

        for step in self.steps:

            result = step.apply(result)

        return result

    def summary(self):

        return [

            str(step)

            for step in self.steps
        ]

    def __repr__(self):

        return (
            f"TransformationPlan("
            f"steps={self.summary()}"
            f")"
        )


# ============================================================
# PLAN EVALUATOR
# ============================================================

class PlanEvaluator:

    def __init__(self, target_grid):

        self.target_grid = np.array(
            target_grid
        )

    def similarity(self, grid):

        if grid.shape != self.target_grid.shape:

            return 0.0

        total = grid.size

        correct = np.sum(
            grid == self.target_grid
        )

        return correct / total

    def evaluate(self, candidate_grid):

        return self.similarity(
            candidate_grid
        )


# ============================================================
# CANDIDATE PLAN GENERATOR
# ============================================================

class CandidatePlanGenerator:

    def __init__(self):

        self.transformations = []

        self.build_default_library()

    # ========================================================
    # DEFAULT TRANSFORMATION LIBRARY
    # ========================================================

    def build_default_library(self):

        # ROTATIONS

        self.transformations.append(
            Rotate(1)
        )

        self.transformations.append(
            Rotate(2)
        )

        self.transformations.append(
            Rotate(3)
        )

        # FLIPS

        self.transformations.append(
            Flip(0)
        )

        self.transformations.append(
            Flip(1)
        )

        # MIRROR

        self.transformations.append(
            Mirror()
        )

        # DUPLICATE

        self.transformations.append(
            Duplicate(0)
        )

        self.transformations.append(
            Duplicate(1)
        )

        # SCALE

        self.transformations.append(
            Scale(2)
        )

        # FILL

        self.transformations.append(
            Fill(1)
        )

        # DELETE

        self.transformations.append(
            Delete(1)
        )

    # ========================================================
    # GENERATE PLANS
    # ========================================================

    def generate(self, max_depth=2):

        plans = []

        for depth in range(1, max_depth + 1):

            combinations = itertools.product(
                self.transformations,
                repeat=depth
            )

            for combo in combinations:

                plan = TransformationPlan()

                for transformation in combo:

                    plan.add_step(
                        transformation
                    )

                plans.append(plan)

        return plans


# ============================================================
# BEST PLAN SEARCH
# ============================================================

class BestPlanSearch:

    def __init__(
        self,
        input_grid,
        output_grid
    ):

        self.input_grid = np.array(
            input_grid
        )

        self.output_grid = np.array(
            output_grid
        )

        self.generator = (
            CandidatePlanGenerator()
        )

        self.evaluator = (
            PlanEvaluator(output_grid)
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search(self, max_depth=2):

        best_score = -1.0

        best_plan = None

        plans = self.generator.generate(
            max_depth=max_depth
        )

        for plan in plans:

            try:

                candidate = plan.execute(
                    self.input_grid
                )

                score = self.evaluator.evaluate(
                    candidate
                )

                if score > best_score:

                    best_score = score

                    best_plan = plan

            except Exception:

                continue

        return {

            "best_plan":
                best_plan.summary()
                if best_plan else [],

            "score":
                best_score
        }


# ============================================================
# PLANNER ENGINE
# ============================================================

class PlannerEngine:

    def __init__(self):

        pass

    def plan(
        self,
        input_grid,
        output_grid,
        max_depth=2
    ):

        search_engine = BestPlanSearch(
            input_grid,
            output_grid
        )

        result = search_engine.search(
            max_depth=max_depth
        )

        return result