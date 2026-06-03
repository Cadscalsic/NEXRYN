from core.grid import ARCGrid


class ARCPatternEngine:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, input_grid, output_grid):

        self.input_grid = input_grid

        self.output_grid = output_grid

        self.patterns = []

    # =====================================================
    # GRID SIZE ANALYSIS
    # =====================================================

    def grid_size_changed(self):

        return (
            self.input_grid.shape()
            !=
            self.output_grid.shape()
        )

    # =====================================================
    # COLOR ANALYSIS
    # =====================================================

    def colors_added(self):

        input_colors = set(
            self.input_grid.unique_colors()
        )

        output_colors = set(
            self.output_grid.unique_colors()
        )

        return list(output_colors - input_colors)

    def colors_removed(self):

        input_colors = set(
            self.input_grid.unique_colors()
        )

        output_colors = set(
            self.output_grid.unique_colors()
        )

        return list(input_colors - output_colors)

    def colors_preserved(self):

        input_colors = set(
            self.input_grid.unique_colors()
        )

        output_colors = set(
            self.output_grid.unique_colors()
        )

        return list(
            input_colors.intersection(output_colors)
        )

    # =====================================================
    # OBJECT ANALYSIS
    # =====================================================

    def input_object_count(self):

        return len(
            self.input_grid.find_objects()
        )

    def output_object_count(self):

        return len(
            self.output_grid.find_objects()
        )

    def object_count_changed(self):

        return (
            self.input_object_count()
            !=
            self.output_object_count()
        )

    # =====================================================
    # SYMMETRY ANALYSIS
    # =====================================================

    def symmetry_changes(self):

        return {

            "input_horizontal":
                self.input_grid.is_horizontally_symmetric(),

            "output_horizontal":
                self.output_grid.is_horizontally_symmetric(),

            "input_vertical":
                self.input_grid.is_vertically_symmetric(),

            "output_vertical":
                self.output_grid.is_vertically_symmetric()
        }

    # =====================================================
    # DENSITY ANALYSIS
    # =====================================================

    def density_change(self):

        input_density = self.input_grid.filled_ratio()

        output_density = self.output_grid.filled_ratio()

        return {

            "input_density":
                input_density,

            "output_density":
                output_density,

            "difference":
                output_density - input_density
        }

    # =====================================================
    # PATTERN ANALYSIS
    # =====================================================

    def analyze_patterns(self):

        self.patterns = [

            {
                "pattern": "grid_size_changed",
                "value": self.grid_size_changed()
            },

            {
                "pattern": "colors_added",
                "value": self.colors_added()
            },

            {
                "pattern": "colors_removed",
                "value": self.colors_removed()
            },

            {
                "pattern": "colors_preserved",
                "value": self.colors_preserved()
            },

            {
                "pattern": "input_object_count",
                "value": self.input_object_count()
            },

            {
                "pattern": "output_object_count",
                "value": self.output_object_count()
            },

            {
                "pattern": "object_count_changed",
                "value": self.object_count_changed()
            },

            {
                "pattern": "symmetry_changes",
                "value": self.symmetry_changes()
            },

            {
                "pattern": "density_change",
                "value": self.density_change()
            }
        ]

    # =====================================================
    # FULL REPORT
    # =====================================================

    def full_report(self):

        return self.patterns

    # =====================================================
    # PRINT REPORT
    # =====================================================

    def print_report(self):

        print("\n========== AMIS PATTERN ANALYSIS ==========\n")

        for pattern in self.patterns:

            print(pattern)
            print()