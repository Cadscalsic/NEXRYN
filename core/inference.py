import numpy as np

from core.transformations import (
    Rotate,
    Flip,
    Mirror,
    Translate,
    Scale,
    Recolor,
    Duplicate
)


# ============================================================
# RULE SCORE
# ============================================================

class RuleScore:

    def __init__(self, transformation, score):

        self.transformation = transformation
        self.score = score

    def summary(self):

        return {
            "transformation": str(self.transformation),
            "score": self.score
        }


# ============================================================
# TRANSFORMATION MATCHER
# ============================================================

class TransformationMatcher:

    def __init__(self, input_grid, output_grid):

        self.input_grid = np.array(input_grid)
        self.output_grid = np.array(output_grid)

    def exact_match(self, candidate_grid):

        if candidate_grid.shape != self.output_grid.shape:
            return False

        return np.array_equal(
            candidate_grid,
            self.output_grid
        )

    def similarity_score(self, candidate_grid):

        if candidate_grid.shape != self.output_grid.shape:
            return 0.0

        total = candidate_grid.size

        correct = np.sum(
            candidate_grid == self.output_grid
        )

        return correct / total


# ============================================================
# CANDIDATE GENERATOR
# ============================================================

class CandidateGenerator:

    def __init__(self):

        self.transformations = []

        self.build_default_candidates()

    def build_default_candidates(self):

        # ROTATIONS
        self.transformations.append(Rotate(1))
        self.transformations.append(Rotate(2))
        self.transformations.append(Rotate(3))

        # FLIPS
        self.transformations.append(Flip(0))
        self.transformations.append(Flip(1))

        # MIRROR
        self.transformations.append(Mirror())

        # DUPLICATE
        self.transformations.append(Duplicate(0))
        self.transformations.append(Duplicate(1))

        # SCALE
        self.transformations.append(Scale(2))

    def all(self):

        return self.transformations


# ============================================================
# RULE SCORER
# ============================================================

class RuleScorer:

    def __init__(self, input_grid, output_grid):

        self.input_grid = np.array(input_grid)
        self.output_grid = np.array(output_grid)

        self.matcher = TransformationMatcher(
            input_grid,
            output_grid
        )

    def evaluate(self, transformation):

        try:

            candidate = transformation.apply(
                self.input_grid
            )

            score = self.matcher.similarity_score(
                candidate
            )

            return RuleScore(
                transformation,
                score
            )

        except Exception:

            return RuleScore(
                transformation,
                0.0
            )


# ============================================================
# BEST RULE SELECTOR
# ============================================================

class BestRuleSelector:

    def __init__(self, input_grid, output_grid):

        self.input_grid = input_grid
        self.output_grid = output_grid

        self.generator = CandidateGenerator()

        self.scorer = RuleScorer(
            input_grid,
            output_grid
        )

    def select_best(self):

        best_score = -1
        best_rule = None

        for transformation in self.generator.all():

            result = self.scorer.evaluate(
                transformation
            )

            if result.score > best_score:

                best_score = result.score
                best_rule = result

        return best_rule


# ============================================================
# INFERENCE ENGINE
# ============================================================

class InferenceEngine:

    def __init__(self):

        pass

    def infer(self, input_grid, output_grid):

        selector = BestRuleSelector(
            input_grid,
            output_grid
        )

        best = selector.select_best()

        return {
            "best_transformation":
                str(best.transformation),

            "score":
                best.score
        }