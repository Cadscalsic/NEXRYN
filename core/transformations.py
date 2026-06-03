import numpy as np


# ============================================================
# BASE TRANSFORMATION
# ============================================================

class Transformation:

    def __init__(self, name):
        self.name = name

    def apply(self, grid):
        raise NotImplementedError

    def __repr__(self):
        return f"{self.name}()"


# ============================================================
# ROTATION
# ============================================================

class Rotate(Transformation):

    def __init__(self, k=1):
        super().__init__("Rotate")
        self.k = k

    def apply(self, grid):
        return np.rot90(grid, self.k)


# ============================================================
# FLIP
# ============================================================

class Flip(Transformation):

    def __init__(self, axis=0):
        super().__init__("Flip")
        self.axis = axis

    def apply(self, grid):

        if self.axis == 0:
            return np.flipud(grid)

        return np.fliplr(grid)


# ============================================================
# MIRROR
# ============================================================

class Mirror(Transformation):

    def __init__(self):
        super().__init__("Mirror")

    def apply(self, grid):

        left = np.fliplr(grid)

        return np.concatenate(
            [grid, left],
            axis=1
        )


# ============================================================
# TRANSLATE
# ============================================================

class Translate(Transformation):

    def __init__(self, dx=0, dy=0):
        super().__init__("Translate")

        self.dx = dx
        self.dy = dy

    def apply(self, grid):

        rows, cols = grid.shape

        result = np.zeros_like(grid)

        for r in range(rows):

            for c in range(cols):

                nr = r + self.dy
                nc = c + self.dx

                if 0 <= nr < rows and 0 <= nc < cols:
                    result[nr, nc] = grid[r, c]

        return result


# ============================================================
# SCALE
# ============================================================

class Scale(Transformation):

    def __init__(self, factor=2):
        super().__init__("Scale")

        self.factor = factor

    def apply(self, grid):

        return np.kron(
            grid,
            np.ones(
                (self.factor, self.factor),
                dtype=int
            )
        )


# ============================================================
# RECOLOR
# ============================================================

class Recolor(Transformation):

    def __init__(self, source_color, target_color):
        super().__init__("Recolor")

        self.source_color = source_color
        self.target_color = target_color

    def apply(self, grid):

        result = grid.copy()

        result[result == self.source_color] = self.target_color

        return result


# ============================================================
# DELETE
# ============================================================

class Delete(Transformation):

    def __init__(self, target_color=0):
        super().__init__("Delete")

        self.target_color = target_color

    def apply(self, grid):

        result = grid.copy()

        result[result == self.target_color] = 0

        return result


# ============================================================
# FILL
# ============================================================

class Fill(Transformation):

    def __init__(self, color=1):
        super().__init__("Fill")

        self.color = color

    def apply(self, grid):

        result = grid.copy()

        result[result == 0] = self.color

        return result


# ============================================================
# CROP
# ============================================================

class Crop(Transformation):

    def __init__(self, min_row, max_row, min_col, max_col):
        super().__init__("Crop")

        self.min_row = min_row
        self.max_row = max_row
        self.min_col = min_col
        self.max_col = max_col

    def apply(self, grid):

        return grid[
            self.min_row:self.max_row + 1,
            self.min_col:self.max_col + 1
        ]


# ============================================================
# DUPLICATE
# ============================================================

class Duplicate(Transformation):

    def __init__(self, axis=1):
        super().__init__("Duplicate")

        self.axis = axis

    def apply(self, grid):

        return np.concatenate(
            [grid, grid],
            axis=self.axis
        )


# ============================================================
# TRANSFORMATION ENGINE
# ============================================================

class TransformationEngine:

    def __init__(self):

        self.transformations = []

    def add(self, transformation):

        self.transformations.append(
            transformation
        )

    def apply_all(self, grid):

        result = grid.copy()

        for transformation in self.transformations:

            result = transformation.apply(
                result
            )

        return result

    def clear(self):

        self.transformations = []

    def summary(self):

        return [
            str(t)
            for t in self.transformations
        ]