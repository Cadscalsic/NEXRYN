import numpy as np

# =========================================================
# ARC OBJECT
# =========================================================

class ARCObject:

    def __init__(self, cells, color):

        self.cells = cells
        self.color = int(color)

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    def size(self):

        return len(self.cells)

    def centroid(self):

        rows = [cell[0] for cell in self.cells]
        cols = [cell[1] for cell in self.cells]

        return {
            "row": sum(rows) / len(rows),
            "col": sum(cols) / len(cols)
        }

    def bounding_box(self):

        rows = [cell[0] for cell in self.cells]
        cols = [cell[1] for cell in self.cells]

        return {
            "min_row": min(rows),
            "max_row": max(rows),
            "min_col": min(cols),
            "max_col": max(cols)
        }

    def width(self):

        box = self.bounding_box()

        return (
            box["max_col"] - box["min_col"] + 1
        )

    def height(self):

        box = self.bounding_box()

        return (
            box["max_row"] - box["min_row"] + 1
        )

    def aspect_ratio(self):

        h = self.height()

        if h == 0:
            return 0

        return self.width() / h

    # =====================================================
    # SHAPE ANALYSIS
    # =====================================================

    def is_single_pixel(self):

        return self.size() == 1

    def is_horizontal_line(self):

        box = self.bounding_box()

        return (
            box["min_row"] == box["max_row"]
            and self.width() > 1
        )

    def is_vertical_line(self):

        box = self.bounding_box()

        return (
            box["min_col"] == box["max_col"]
            and self.height() > 1
        )

    def is_rectangle(self):

        return (
            self.size()
            ==
            self.width() * self.height()
        )

    def density(self):

        area = self.width() * self.height()

        if area == 0:
            return 0

        return self.size() / area

    # =====================================================
    # GEOMETRIC FEATURES
    # =====================================================

    def corners(self):

        box = self.bounding_box()

        return [
            (box["min_row"], box["min_col"]),
            (box["min_row"], box["max_col"]),
            (box["max_row"], box["min_col"]),
            (box["max_row"], box["max_col"])
        ]

    def to_mask(self):

        box = self.bounding_box()

        h = self.height()
        w = self.width()

        mask = np.zeros((h, w), dtype=int)

        for row, col in self.cells:

            local_row = row - box["min_row"]
            local_col = col - box["min_col"]

            mask[local_row][local_col] = 1

        return mask

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def summary(self):

        return {
            "color": self.color,

            "size":
                self.size(),

            "centroid":
                self.centroid(),

            "bounding_box":
                self.bounding_box(),

            "width":
                self.width(),

            "height":
                self.height(),

            "density":
                round(self.density(), 3),

            "horizontal_line":
                self.is_horizontal_line(),

            "vertical_line":
                self.is_vertical_line(),

            "rectangle":
                self.is_rectangle()
        }

    def __repr__(self):

        return (
            f"ARCObject("
            f"color={self.color}, "
            f"size={self.size()}, "
            f"bbox={self.bounding_box()}"
            f")"
        )


# =========================================================
# OBJECT DETECTOR
# =========================================================

class ObjectDetector:

    def __init__(self, grid):

        self.grid = np.array(
            grid,
            dtype=int
        )

        self.rows = self.grid.shape[0]
        self.cols = self.grid.shape[1]

        self.visited = np.zeros_like(
            self.grid,
            dtype=bool
        )

    # =====================================================
    # OBJECT DETECTION
    # =====================================================

    def detect_objects(self):

        objects = []

        for row in range(self.rows):

            for col in range(self.cols):

                color = self.grid[row][col]

                # BACKGROUND
                if color == 0:
                    continue

                # ALREADY VISITED
                if self.visited[row][col]:
                    continue

                cells = []

                self._dfs(
                    row=row,
                    col=col,
                    color=color,
                    cells=cells
                )

                arc_object = ARCObject(
                    cells=cells,
                    color=color
                )

                objects.append(arc_object)

        return objects

    # =====================================================
    # CONNECTED COMPONENT DFS
    # =====================================================

    def _dfs(
        self,
        row,
        col,
        color,
        cells
    ):

        # OUTSIDE GRID
        if row < 0 or row >= self.rows:
            return

        if col < 0 or col >= self.cols:
            return

        # VISITED
        if self.visited[row][col]:
            return

        # DIFFERENT COLOR
        if self.grid[row][col] != color:
            return

        self.visited[row][col] = True

        cells.append((row, col))

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1)
        ]

        for dr, dc in directions:

            self._dfs(
                row + dr,
                col + dc,
                color,
                cells
            )