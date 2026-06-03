# ============================================
# NEXRYN TOPOLOGY ENGINE
# EXECUTABLE TOPOLOGICAL REASONING
# ============================================

from datetime import datetime

import numpy as np


# ============================================
# TOPOLOGY ENGINE
# ============================================

class TopologyEngine:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.analysis_history = []

        self.topology_memory = []

        self.operator_statistics = {}

    # ========================================
    # SAFE ARRAY
    # ========================================

    def safe_array(
        self,
        grid
    ):

        if grid is None:

            return np.array([])

        if hasattr(
            grid,
            "grid"
        ):

            return np.array(
                grid.grid
            )

        return np.array(grid)

    # ========================================
    # CONNECTED COMPONENTS
    # ========================================

    def count_components(
        self,
        grid
    ):

        visited = np.zeros_like(
            grid,
            dtype=bool
        )

        rows, cols = grid.shape

        component_count = 0

        directions = [

            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1)
        ]

        def dfs(row, col):

            stack = [(row, col)]

            while stack:

                r, c = stack.pop()

                if (

                    r < 0
                    or
                    r >= rows
                    or
                    c < 0
                    or
                    c >= cols
                ):

                    continue

                if visited[r, c]:

                    continue

                if grid[r, c] == 0:

                    continue

                visited[r, c] = True

                for dy, dx in directions:

                    stack.append(

                        (
                            r + dy,
                            c + dx
                        )
                    )

        for row in range(rows):

            for col in range(cols):

                if (

                    grid[row, col] != 0

                    and

                    not visited[row, col]
                ):

                    dfs(row, col)

                    component_count += 1

        return component_count

    # ========================================
    # DENSITY
    # ========================================

    def compute_density(
        self,
        grid
    ):

        total = grid.size

        if total == 0:

            return 0.0

        active = np.count_nonzero(
            grid
        )

        return float(
            active / total
        )

    # ========================================
    # SYMMETRY
    # ========================================

    def analyze_symmetry(
        self,
        grid
    ):

        horizontal = np.array_equal(

            grid,

            np.fliplr(grid)
        )

        vertical = np.array_equal(

            grid,

            np.flipud(grid)
        )

        rotational = np.array_equal(

            grid,

            np.rot90(
                grid,
                2
            )
        )

        return {

            "horizontal":
            horizontal,

            "vertical":
            vertical,

            "rotational":
            rotational
        }

    # ========================================
    # TOPOLOGY ANALYSIS
    # ========================================

    def analyze_topology(
        self,
        grid
    ):

        grid = self.safe_array(
            grid
        )

        component_count = (
            self.count_components(
                grid
            )
        )

        density = (
            self.compute_density(
                grid
            )
        )

        symmetry = (
            self.analyze_symmetry(
                grid
            )
        )

        return {

            "component_count":
            component_count,

            "density":
            density,

            "symmetry":
            symmetry
        }

    # ========================================
    # TOPOLOGY DIFFERENCE
    # ========================================

    def analyze_delta(

        self,

        input_topology,

        output_topology
    ):

        input_components = (

            input_topology.get(
                "component_count",
                0
            )
        )

        output_components = (

            output_topology.get(
                "component_count",
                0
            )
        )

        component_delta = (

            output_components
            -
            input_components
        )

        input_density = (

            input_topology.get(
                "density",
                0.0
            )
        )

        output_density = (

            output_topology.get(
                "density",
                0.0
            )
        )

        density_delta = (

            output_density
            -
            input_density
        )

        operator = (
            "preserve_topology"
        )

        confidence = 0.84

        if component_delta > 0:

            operator = (
                "grow_topology"
            )

            confidence = 0.93

        elif component_delta < 0:

            operator = (
                "compress_topology"
            )

            confidence = 0.89

        elif density_delta > 0:

            operator = (
                "expand_pattern"
            )

            confidence = 0.90

        elif density_delta < 0:

            operator = (
                "reduce_pattern"
            )

            confidence = 0.87

        return {

            "reasoning_type":
            "topology_delta",

            "component_delta":
            component_delta,

            "density_delta":
            density_delta,

            "operator":
            operator,

            "confidence":
            confidence
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(
        self,
        delta_report
    ):

        return {

            "operator":
            delta_report.get(
                "operator"
            ),

            "confidence":
            delta_report.get(
                "confidence"
            ),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN ANALYSIS
    # ========================================

    def run_analysis(

        self,

        input_grid,

        output_grid
    ):

        input_grid = self.safe_array(
            input_grid
        )

        output_grid = self.safe_array(
            output_grid
        )

        input_topology = (

            self.analyze_topology(
                input_grid
            )
        )

        output_topology = (

            self.analyze_topology(
                output_grid
            )
        )

        delta_report = (

            self.analyze_delta(

                input_topology,

                output_topology
            )
        )

        topology_report = (

            self.build_report(
                delta_report
            )
        )

        self.analysis_history.append({

            "input_topology":
            input_topology,

            "output_topology":
            output_topology,

            "delta_report":
            delta_report
        })

        return {

            "input_topology":
            input_topology,

            "output_topology":
            output_topology,

            "delta_report":
            delta_report,

            "topology_report":
            topology_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

topology_engine = (
    TopologyEngine()
)