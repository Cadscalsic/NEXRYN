# ============================================
# NEXRYN SYMBOLIC COMPONENT SYSTEM
# ============================================

import numpy as np

from collections import deque

from datetime import datetime


# ============================================
# CONNECTED COMPONENT
# Symbolic Cognitive Entity
# ============================================

class ConnectedComponent:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        cells,

        color
    ):

        self.cells = cells

        self.color = int(color)

        self.component_id = (
            id(self)
        )

        self.created_at = (
            str(datetime.utcnow())
        )

        # ====================================
        # COGNITIVE FEATURES
        # ====================================

        self.semantic_profile = {

            "symbolic_entity":
            True,

            "topological_structure":
            True,

            "relational_ready":
            True,

            "graph_compatible":
            True
        }

    # ========================================
    # BASIC FEATURES
    # ========================================

    def size(self):

        return len(self.cells)

    def rows(self):

        return [

            cell[0]

            for cell in self.cells
        ]

    def cols(self):

        return [

            cell[1]

            for cell in self.cells
        ]

    # ========================================
    # BOUNDING BOX
    # ========================================

    def bounding_box(self):

        return {

            "min_row":
            min(self.rows()),

            "max_row":
            max(self.rows()),

            "min_col":
            min(self.cols()),

            "max_col":
            max(self.cols())
        }

    # ========================================
    # DIMENSIONS
    # ========================================

    def width(self):

        bbox = self.bounding_box()

        return (

            bbox["max_col"]
            -
            bbox["min_col"]
            + 1
        )

    def height(self):

        bbox = self.bounding_box()

        return (

            bbox["max_row"]
            -
            bbox["min_row"]
            + 1
        )

    # ========================================
    # CENTROID
    # ========================================

    def centroid(self):

        return {

            "row":

            round(
                sum(self.rows())
                / self.size(),

                3
            ),

            "col":

            round(
                sum(self.cols())
                / self.size(),

                3
            )
        }

    # ========================================
    # SHAPE MATRIX
    # ========================================

    def shape_matrix(self):

        bbox = self.bounding_box()

        matrix = np.zeros(

            (
                self.height(),
                self.width()
            ),

            dtype=int
        )

        for row, col in self.cells:

            local_row = (
                row - bbox["min_row"]
            )

            local_col = (
                col - bbox["min_col"]
            )

            matrix[
                local_row,
                local_col
            ] = self.color

        return matrix

    # ========================================
    # DENSITY
    # ========================================

    def density(self):

        area = (

            self.width()
            *
            self.height()
        )

        if area == 0:
            return 0.0

        return round(

            self.size() / area,

            4
        )

    # ========================================
    # PERIMETER ESTIMATION
    # ========================================

    def perimeter(self):

        cell_set = set(
            self.cells
        )

        perimeter = 0

        directions = [

            (-1, 0),
            (1, 0),

            (0, -1),
            (0, 1)
        ]

        for row, col in self.cells:

            for dr, dc in directions:

                neighbor = (
                    row + dr,
                    col + dc
                )

                if neighbor not in cell_set:

                    perimeter += 1

        return perimeter

    # ========================================
    # COMPLEXITY SCORE
    # ========================================

    def complexity_score(self):

        return round(

            (
                self.perimeter()
                *
                self.density()
            )

            / max(
                self.size(),
                1
            ),

            4
        )

    # ========================================
    # TOPOLOGY PROFILE
    # ========================================

    def topology_profile(self):

        return {

            "size":
            self.size(),

            "width":
            self.width(),

            "height":
            self.height(),

            "density":
            self.density(),

            "perimeter":
            self.perimeter(),

            "complexity":
            self.complexity_score()
        }

    # ========================================
    # SYMBOLIC SIGNATURE
    # ========================================

    def symbolic_signature(self):

        topology = (
            self.topology_profile()
        )

        return (

            f"C{self.color}_"
            f"S{topology['size']}_"
            f"W{topology['width']}_"
            f"H{topology['height']}"
        )

    # ========================================
    # EXPORT SUMMARY
    # ========================================

    def summary(self):

        return {

            "component_id":
            self.component_id,

            "color":
            self.color,

            "cells":
            len(self.cells),

            "centroid":
            self.centroid(),

            "bounding_box":
            self.bounding_box(),

            "topology":
            self.topology_profile(),

            "symbolic_signature":
            self.symbolic_signature(),

            "semantic_profile":
            self.semantic_profile
        }

    # ========================================
    # REPRESENTATION
    # ========================================

    def __repr__(self):

        return (

            f"ConnectedComponent("
            f"id={self.component_id}, "
            f"color={self.color}, "
            f"size={self.size()}"
            f")"
        )


# ============================================
# CONNECTED COMPONENT EXTRACTOR
# ============================================

class ConnectedComponentExtractor:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        grid
    ):

        self.grid = np.array(
            grid,
            dtype=int
        )

        self.rows = (
            self.grid.shape[0]
        )

        self.cols = (
            self.grid.shape[1]
        )

        self.visited = np.zeros_like(

            self.grid,

            dtype=bool
        )

        self.extraction_report = {

            "components_detected":
            0,

            "symbolic_entities":
            0,

            "extraction_timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # EXTRACT COMPONENTS
    # ========================================

    def extract(self):

        components = []

        for row in range(self.rows):

            for col in range(self.cols):

                color = (
                    self.grid[row][col]
                )

                if color == 0:
                    continue

                if self.visited[row][col]:
                    continue

                cells = []

                self._bfs(

                    row,
                    col,
                    color,
                    cells
                )

                component = (

                    ConnectedComponent(

                        cells=cells,

                        color=color
                    )
                )

                components.append(
                    component
                )

        self.extraction_report[
            "components_detected"
        ] = len(components)

        self.extraction_report[
            "symbolic_entities"
        ] = len(components)

        return components

    # ========================================
    # BFS EXTRACTION
    # ========================================

    def _bfs(

        self,

        start_row,
        start_col,
        color,
        cells
    ):

        queue = deque()

        queue.append(
            (start_row, start_col)
        )

        self.visited[
            start_row
        ][
            start_col
        ] = True

        directions = [

            (-1, 0),
            (1, 0),

            (0, -1),
            (0, 1)
        ]

        while queue:

            row, col = queue.popleft()

            cells.append(
                (row, col)
            )

            for dr, dc in directions:

                nr = row + dr
                nc = col + dc

                if (

                    nr < 0
                    or nr >= self.rows
                ):

                    continue

                if (

                    nc < 0
                    or nc >= self.cols
                ):

                    continue

                if self.visited[nr][nc]:

                    continue

                if self.grid[nr][nc] != color:

                    continue

                self.visited[nr][nc] = True

                queue.append(
                    (nr, nc)
                )

    # ========================================
    # EXTRACTION REPORT
    # ========================================

    def report(self):

        return (
            self.extraction_report
        )