import numpy as np

from core.objects import ObjectDetector


# =========================================================
# ARC GRID
# High-Level Visual Reasoning Primitive
# =========================================================

class ARCGrid:

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self, grid):

        if isinstance(grid, ARCGrid):

            self.grid = grid.to_numpy().copy()

        else:

            self.grid = np.array(
                grid,
                dtype=int
            )

        self.validate_grid()

        self._object_cache = None
        self._scene_graph_cache = None

    # =====================================================
    # VALIDATION
    # =====================================================

    def validate_grid(self):

        if len(self.grid.shape) != 2:

            raise ValueError(
                "ARCGrid requires a 2D grid."
            )

        if self.grid.size == 0:

            raise ValueError(
                "ARCGrid cannot be empty."
            )

    # =====================================================
    # BASIC GRID INFORMATION
    # =====================================================

    def shape(self):

        return self.grid.shape

    def height(self):

        return self.grid.shape[0]

    def width(self):

        return self.grid.shape[1]

    def total_cells(self):

        return self.grid.size

    # =====================================================
    # COLOR ANALYSIS
    # =====================================================

    def unique_colors(self):

        return np.unique(self.grid)

    def unique_colors_list(self):

        return self.unique_colors().tolist()

    def color_count(self):

        return len(self.unique_colors())

    def dominant_color(self):

        values, counts = np.unique(
            self.grid,
            return_counts=True
        )

        return int(
            values[np.argmax(counts)]
        )

    # =====================================================
    # GRID DENSITY
    # =====================================================

    def filled_cells(self):

        return int(
            np.count_nonzero(self.grid)
        )

    def empty_cells(self):

        return int(
            self.total_cells() -
            self.filled_cells()
        )

    def filled_ratio(self):

        return (
            self.filled_cells() /
            self.total_cells()
        )

    def empty_ratio(self):

        return 1.0 - self.filled_ratio()

    def density(self):

        return self.filled_ratio()

    # =====================================================
    # SYMMETRY ANALYSIS
    # =====================================================

    def is_horizontally_symmetric(self):

        return np.array_equal(
            self.grid,
            np.flipud(self.grid)
        )

    def is_vertically_symmetric(self):

        return np.array_equal(
            self.grid,
            np.fliplr(self.grid)
        )

    # =====================================================
    # OBJECT DETECTION INTERFACE
    # =====================================================

    def find_objects(self):

        if self._object_cache is not None:

            return self._object_cache

        detector = ObjectDetector(
            self.grid
        )

        self._object_cache = (
            detector.detect_objects()
        )

        return self._object_cache

    def object_count(self):

        return len(
            self.find_objects()
        )

    # =====================================================
    # SCENE GRAPH
    # =====================================================

    def scene_graph(self):

        if self._scene_graph_cache is not None:

            return self._scene_graph_cache

        graph = []

        objects = self.find_objects()

        for idx, obj in enumerate(objects):

            graph.append({

                "id": idx,

                "color": obj.color,

                "size": obj.size(),

                "bounding_box":
                    obj.bounding_box(),

                "centroid":
                    obj.centroid()
            })

        self._scene_graph_cache = graph

        return graph

    # =====================================================
    # GRID SUMMARY
    # =====================================================

    def grid_summary(self):

        return {

            "shape":
                self.shape(),

            "height":
                self.height(),

            "width":
                self.width(),

            "total_cells":
                self.total_cells(),

            "colors":
                self.unique_colors_list(),

            "color_count":
                self.color_count(),

            "dominant_color":
                self.dominant_color(),

            "object_count":
                self.object_count(),

            "density":
                self.density(),

            "horizontal_symmetry":
                self.is_horizontally_symmetric(),

            "vertical_symmetry":
                self.is_vertically_symmetric()
        }

    # =====================================================
    # EXPORT SYSTEM
    # =====================================================

    def export_dict(self):

        return {

            "summary":
                self.grid_summary(),

            "objects":
                [
                    obj.summary()
                    for obj in self.find_objects()
                ],

            "scene_graph":
                self.scene_graph()
        }

    # =====================================================
    # RAW EXPORT
    # =====================================================

    def to_numpy(self):

        return self.grid.copy()

    def to_list(self):

        return self.grid.tolist()

    # =====================================================
    # DEBUG UTILITIES
    # =====================================================

    def print_grid(self):

        print("\n===== ARC GRID =====\n")

        print(self.grid)

    def print_analysis(self):

        analysis = self.export_dict()

        print(
            "\n===== AMIS GRID ANALYSIS =====\n"
        )

        for key, value in analysis.items():

            print(f"{key}:")
            print(value)
            print()

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __repr__(self):

        return (
            f"ARCGrid("
            f"shape={self.shape()}, "
            f"colors={self.color_count()}, "
            f"objects={self.object_count()}"
            f")"
        )