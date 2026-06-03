# ============================================
# NEXRYN TRANSFORMATION VALIDATION ENGINE
# ============================================

import numpy as np

from datetime import datetime

from copy import deepcopy


# ============================================
# TRANSFORMATION VALIDATION ENGINE
# ============================================

class TransformationValidationEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.validation_history = []

        self.failed_validations = []

        self.engine_state = {

            "output_validation":
            True,

            "shape_validation":
            True,

            "semantic_validation":
            True,

            "operator_validation":
            True,

            "adaptive_recovery":
            True
        }

    # ========================================
    # VALIDATE GRID STRUCTURE
    # ========================================

    def validate_grid_structure(

        self,

        grid
    ):

        try:

            grid = np.array(grid)

            if grid.ndim < 2:

                return False

            if grid.shape[0] == 0:

                return False

            if grid.shape[1] == 0:

                return False

            return True

        except Exception:

            return False

    # ========================================
    # VALIDATE SHAPE CONSISTENCY
    # ========================================

    def validate_shape_consistency(

        self,

        input_grid,

        output_grid
    ):

        try:

            input_grid = np.array(
                input_grid
            )

            output_grid = np.array(
                output_grid
            )

            return (

                input_grid.shape
                ==
                output_grid.shape
            )

        except Exception:

            return False

    # ========================================
    # VALIDATE VALUE RANGE
    # ========================================

    def validate_value_range(

        self,

        grid
    ):

        try:

            grid = np.array(grid)

            minimum_value = np.min(
                grid
            )

            maximum_value = np.max(
                grid
            )

            if minimum_value < 0:

                return False

            if maximum_value > 9:

                return False

            return True

        except Exception:

            return False

    # ========================================
    # VALIDATE TRANSFORMATION
    # ========================================

    def validate_transformation(

        self,

        input_grid,

        output_grid
    ):

        # ====================================
        # STRUCTURE VALIDATION
        # ====================================

        input_valid = (

            self.validate_grid_structure(
                input_grid
            )
        )

        output_valid = (

            self.validate_grid_structure(
                output_grid
            )
        )

        # ====================================
        # SHAPE VALIDATION
        # ====================================

        shape_valid = (

            self.validate_shape_consistency(

                input_grid,

                output_grid
            )
        )

        # ====================================
        # VALUE VALIDATION
        # ====================================

        value_valid = (

            self.validate_value_range(
                output_grid
            )
        )

        # ====================================
        # FINAL STATUS
        # ====================================

        validation_success = all([

            input_valid,

            output_valid,

            shape_valid,

            value_valid
        ])

        validation_report = {

            "validation_success":
            validation_success,

            "input_valid":
            input_valid,

            "output_valid":
            output_valid,

            "shape_valid":
            shape_valid,

            "value_valid":
            value_valid,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.validation_history.append(
            deepcopy(validation_report)
        )

        if not validation_success:

            self.failed_validations.append(
                validation_report
            )

        return validation_report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_validation = {}

        if self.validation_history:

            latest_validation = (

                self.validation_history[-1]
            )

        return {

            "validation_cycles":

            len(
                self.validation_history
            ),

            "failed_validations":

            len(
                self.failed_validations
            ),

            "engine_state":
            self.engine_state,

            "latest_validation":
            latest_validation
        }


# ============================================
# GLOBAL ENGINE
# ============================================

transformation_validation_engine = (
    TransformationValidationEngine()
)