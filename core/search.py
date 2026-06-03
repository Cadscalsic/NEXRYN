import numpy as np

# =========================================================
# SEARCH NODE
# =========================================================

class SearchNode:

    def __init__(
        self,
        grid,
        program=None,
        score=0.0,
        depth=0
    ):

        self.grid = grid

        self.program = program or []

        self.score = score

        self.depth = depth

    def extend(self, transformation, new_grid, score):

        return SearchNode(

            grid=new_grid,

            program=self.program + [str(transformation)],

            score=score,

            depth=self.depth + 1
        )

    def summary(self):

        return {

            "program": self.program,

            "score": self.score,

            "depth": self.depth

        }


# =========================================================
# BEAM SEARCH ENGINE
# =========================================================

class BeamSearchEngine:

    def __init__(
        self,
        transformations,
        beam_width=10,
        max_depth=3
    ):

        self.transformations = transformations

        self.beam_width = beam_width

        self.max_depth = max_depth

    # =====================================================
    # SCORE
    # =====================================================

    def score(self, predicted, target):

        if predicted.shape != target.shape:

            return 0.0

        correct = np.sum(predicted == target)

        total = predicted.size

        return correct / total

    # =====================================================
    # SEARCH
    # =====================================================

    def search(
        self,
        input_grid,
        target_grid
    ):

        root = SearchNode(input_grid)

        beam = [root]

        best_node = root

        for depth in range(self.max_depth):

            candidates = []

            for node in beam:

                for transformation in self.transformations:

                    try:

                        new_grid = transformation.apply(
                            node.grid
                        )

                        score = self.score(
                            new_grid,
                            target_grid
                        )

                        child = node.extend(
                            transformation,
                            new_grid,
                            score
                        )

                        candidates.append(child)

                        if child.score > best_node.score:

                            best_node = child

                    except Exception:

                        continue

            candidates = sorted(
                candidates,
                key=lambda x: x.score,
                reverse=True
            )

            beam = candidates[:self.beam_width]

        return {

            "best_program": best_node.program,

            "best_score": best_node.score,

            "depth": best_node.depth

        }