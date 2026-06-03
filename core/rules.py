import numpy as np

from core.grid import ARCGrid


class ARCRuleEngine:

    def __init__(self, input_grid, output_grid):

        # =========================================
        # AUTO CONVERT TO ARCGRID
        # =========================================

        self.input_grid = (
            input_grid
            if isinstance(input_grid, ARCGrid)
            else ARCGrid(input_grid)
        )

        self.output_grid = (
            output_grid
            if isinstance(output_grid, ARCGrid)
            else ARCGrid(output_grid)
        )

        self.rules = []

    # =========================================
    # COLOR TRANSFORMATION
    # =========================================

    def detect_color_changes(self):

        input_colors = set(np.unique(self.input_grid.grid))
        output_colors = set(np.unique(self.output_grid.grid))

        added_colors = output_colors - input_colors
        removed_colors = input_colors - output_colors

        rule = {
            "rule": "color_changes",
            "added_colors": list(added_colors),
            "removed_colors": list(removed_colors)
        }

        self.rules.append(rule)

        return rule

    # =========================================
    # SIZE TRANSFORMATION
    # =========================================

    def detect_size_change(self):

        input_shape = self.input_grid.shape()
        output_shape = self.output_grid.shape()

        rule = {
            "rule": "size_change",
            "input_shape": input_shape,
            "output_shape": output_shape,
            "changed": input_shape != output_shape
        }

        self.rules.append(rule)

        return rule

    # =========================================
    # OBJECT COUNT TRANSFORMATION
    # =========================================

    def detect_object_change(self):

        input_objects = self.input_grid.find_objects()
        output_objects = self.output_grid.find_objects()

        rule = {
            "rule": "object_change",
            "input_count": len(input_objects),
            "output_count": len(output_objects),
            "difference": len(output_objects) - len(input_objects)
        }

        self.rules.append(rule)

        return rule

    # =========================================
    # DENSITY TRANSFORMATION
    # =========================================

    def detect_density_change(self):

        input_density = self.input_grid.density()
        output_density = self.output_grid.density()

        rule = {
            "rule": "density_change",
            "input_density": input_density,
            "output_density": output_density,
            "difference": output_density - input_density
        }

        self.rules.append(rule)

        return rule

    # =========================================
    # SYMMETRY TRANSFORMATION
    # =========================================

    def detect_symmetry_change(self):

        input_horizontal = self.input_grid.is_horizontally_symmetric()
        output_horizontal = self.output_grid.is_horizontally_symmetric()

        input_vertical = self.input_grid.is_vertically_symmetric()
        output_vertical = self.output_grid.is_vertically_symmetric()

        rule = {
            "rule": "symmetry_change",

            "input_horizontal": input_horizontal,
            "output_horizontal": output_horizontal,

            "input_vertical": input_vertical,
            "output_vertical": output_vertical
        }

        self.rules.append(rule)

        return rule

    # =========================================
    # RUN FULL ANALYSIS
    # =========================================

    def analyze(self):

        self.detect_color_changes()

        self.detect_size_change()

        self.detect_object_change()

        self.detect_density_change()

        self.detect_symmetry_change()

        return self.rules

    # =========================================
    # PRINT REPORT
    # =========================================

    def print_report(self):

        print("\n========== AMIS RULE ENGINE ==========\n")

        for rule in self.rules:

            print(rule)

            print()