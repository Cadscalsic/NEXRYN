# ============================================
# NEXRYN TRANSFORMATION ENGINE
# ============================================

import numpy as np


# ============================================
# TRANSFORMATION ENGINE
# ============================================

class TransformationEngine:

    def __init__(self):

        # ========================================
        # REGISTERED STRATEGIES
        # ========================================

        self.strategies = {}

        # ========================================
        # REGISTER DEFAULT STRATEGIES
        # ========================================

        self.register_default_strategies()

    # ============================================
    # REGISTER DEFAULT STRATEGIES
    # ============================================

    def register_default_strategies(self):

        self.register_strategy(

            "replace_color",

            self.execute_replace_color
        )

        self.register_strategy(

            "preserve_objects",

            self.execute_preserve_objects
        )

        self.register_strategy(

            "preserve_symmetry",

            self.execute_preserve_symmetry
        )

        self.register_strategy(

            "preserve_density",

            self.execute_preserve_density
        )

    # ============================================
    # REGISTER STRATEGY
    # ============================================

    def register_strategy(

        self,

        strategy_name,

        strategy_function
    ):

        self.strategies[
            strategy_name
        ] = strategy_function

    # ============================================
    # STRATEGY EXISTS
    # ============================================

    def strategy_exists(

        self,

        strategy_name
    ):

        return (
            strategy_name
            in self.strategies
        )

    # ============================================
    # GET STRATEGY
    # ============================================

    def get_strategy(

        self,

        strategy_name
    ):

        return self.strategies.get(
            strategy_name
        )

    # ============================================
    # EXECUTE REPLACE COLOR
    # ============================================

    def execute_replace_color(

        self,

        grid,

        parameters
    ):

        transformed = np.copy(
            grid
        )

        source_colors = parameters.get(
            "source",
            []
        )

        target_colors = parameters.get(
            "target",
            []
        )

        if not source_colors:

            return transformed

        if not target_colors:

            return transformed

        source_color = (
            source_colors[0]
        )

        target_color = (
            target_colors[0]
        )

        transformed[
            transformed == source_color
        ] = target_color

        return transformed

    # ============================================
    # EXECUTE PRESERVE OBJECTS
    # ============================================

    def execute_preserve_objects(

        self,

        grid,

        parameters
    ):

        return np.copy(
            grid
        )

    # ============================================
    # EXECUTE PRESERVE SYMMETRY
    # ============================================

    def execute_preserve_symmetry(

        self,

        grid,

        parameters
    ):

        return np.copy(
            grid
        )

    # ============================================
    # EXECUTE PRESERVE DENSITY
    # ============================================

    def execute_preserve_density(

        self,

        grid,

        parameters
    ):

        return np.copy(
            grid
        )

    # ============================================
    # EXECUTE SYNTHESIZED PROGRAM
    # ============================================

    def execute(

        self,

        input_grid,

        synthesized_program
    ):

        # ========================================
        # COPY INPUT
        # ========================================

        current_grid = np.copy(
            input_grid
        )

        # ========================================
        # EXECUTION TRACE
        # ========================================

        execution_trace = []

        # ========================================
        # PROGRAM STEPS
        # ========================================

        steps = synthesized_program.get(
            "steps",
            []
        )

        # ========================================
        # EXECUTE PROGRAM STEPS
        # ========================================

        for step_index, step in enumerate(
            steps
        ):

            operation = step.get(
                "operation"
            )

            parameters = step.get(
                "parameters",
                {}
            )

            # ====================================
            # CHECK STRATEGY
            # ====================================

            if not self.strategy_exists(
                operation
            ):

                execution_trace.append({

                    "step":
                    step_index,

                    "operation":
                    operation,

                    "status":
                    "missing_strategy"
                })

                continue

            # ====================================
            # GET STRATEGY
            # ====================================

            strategy = self.get_strategy(
                operation
            )

            # ====================================
            # EXECUTE STRATEGY
            # ====================================

            previous_grid = np.copy(
                current_grid
            )

            current_grid = strategy(

                current_grid,

                parameters
            )

            # ====================================
            # DETECT CHANGES
            # ====================================

            grid_changed = not np.array_equal(

                previous_grid,

                current_grid
            )

            # ====================================
            # SAVE TRACE
            # ====================================

            execution_trace.append({

                "step":
                step_index,

                "operation":
                operation,

                "status":
                "executed",

                "grid_changed":
                grid_changed
            })

        # ========================================
        # RETURN RESULTS
        # ========================================

        return {

            "output_grid":
            current_grid,

            "execution_trace":
            execution_trace,

            "executed_steps":
            len(steps),

            "strategy_count":
            len(self.strategies)
        }

    # ============================================
    # PRINT STRATEGIES
    # ============================================

    def print_strategies(self):

        print("\n==================================================")
        print("NEXRYN :: TRANSFORMATION STRATEGIES")
        print("==================================================\n")

        for strategy_name in (

            self.strategies.keys()
        ):

            print(strategy_name)

        print()