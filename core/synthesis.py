import numpy as np

from core.transformations import (
    Rotate,
    Flip,
    Mirror,
    Translate,
    Crop,
    Scale,
    Recolor
)

# =========================================================
# PROGRAM NODE
# =========================================================

class ProgramNode:

    def __init__(self, transformations=None, score=0.0):

        self.transformations = transformations or []

        self.score = score

    def add(self, transformation):

        new_transformations = self.transformations + [transformation]

        return ProgramNode(
            new_transformations,
            self.score
        )

    def summary(self):

        return {
            "program": [
                str(t)
                for t in self.transformations
            ],
            "score": self.score
        }


# =========================================================
# PROGRAM SYNTHESIS ENGINE
# =========================================================

class ProgramSynthesisEngine:

    def __init__(self):

      self.available_transformations = [

     
     Flip(),
     Mirror(),
     Translate()
     

]

    # =====================================================
    # APPLY PROGRAM
    # =====================================================

    def apply_program(self, grid, program):

        result = np.copy(grid)

        for transformation in program.transformations:

            result = transformation.apply(result)

        return result

    # =====================================================
    # SCORE PROGRAM
    # =====================================================

    def score_program(self, predicted, target):

        if predicted.shape != target.shape:

            return 0.0

        correct = np.sum(predicted == target)

        total = predicted.size

        return correct / total

    # =====================================================
    # SEARCH
    # =====================================================

    def synthesize(
        self,
        input_grid,
        output_grid,
        max_depth=2
    ):

        best_program = None

        best_score = -1

        beam = [ProgramNode()]

        for depth in range(max_depth):

            new_beam = []

            for node in beam:

                for transformation in self.available_transformations:

                    candidate = node.add(transformation)

                    try:

                        predicted = self.apply_program(
                            input_grid,
                            candidate
                        )

                        score = self.score_program(
                            predicted,
                            output_grid
                        )

                        candidate.score = score

                        new_beam.append(candidate)

                        if score > best_score:

                            best_score = score

                            best_program = candidate

                    except Exception:

                        continue

            new_beam = sorted(
                new_beam,
                key=lambda x: x.score,
                reverse=True
            )

            beam = new_beam[:10]

        return {
            "best_program":
                best_program.summary(),

            "score":
                best_score
        }