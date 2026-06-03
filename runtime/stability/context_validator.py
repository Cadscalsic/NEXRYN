# ============================================
# NEXRYN CONTEXT VALIDATOR
# ============================================

from datetime import datetime


# ============================================
# CONTEXT VALIDATOR
# ============================================

class ContextValidator:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.validation_state = {

            "validation_active":
            True,

            "context_monitoring":
            True,

            "required_keys_validation":
            True,

            "cognitive_integrity":
            True
        }

        # ====================================
        # REQUIRED CONTEXT KEYS
        # ====================================

        self.required_keys = [

            "runtime_initialized",

            "runtime_metadata",

            "execution_state"
        ]

        # ====================================
        # VALIDATION REPORT
        # ====================================

        self.validation_report = {

            "valid":
            True,

            "missing_keys":
            [],

            "warnings":
            [],

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # VALIDATE REQUIRED KEYS
    # ========================================

    def validate_required_keys(

        self,

        runtime_context
    ):

        missing_keys = []

        for key in self.required_keys:

            if key not in runtime_context:

                missing_keys.append(
                    key
                )

        self.validation_report[
            "missing_keys"
        ] = missing_keys

        if missing_keys:

            self.validation_report[
                "valid"
            ] = False

        return missing_keys

    # ========================================
    # VALIDATE CONTEXT SIZE
    # ========================================

    def validate_context_size(

        self,

        runtime_context
    ):

        context_size = len(
            runtime_context
        )

        if context_size > 1000:

            self.validation_report[
                "warnings"
            ].append({

                "warning":
                "large_runtime_context",

                "context_size":
                context_size
            })

        return context_size

    # ========================================
    # VALIDATE EXECUTION STATE
    # ========================================

    def validate_execution_state(

        self,

        runtime_context
    ):

        execution_state = (

            runtime_context.get(
                "execution_state",
                {}
            )
        )

        if not execution_state:

            self.validation_report[
                "warnings"
            ].append({

                "warning":
                "missing_execution_state"
            })

        return execution_state

    # ========================================
    # VALIDATE RUNTIME CONTEXT
    # ========================================

    def validate(

        self,

        runtime_context
    ):

        self.validate_required_keys(
            runtime_context
        )

        self.validate_context_size(
            runtime_context
        )

        self.validate_execution_state(
            runtime_context
        )

        return self.validation_report

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "validation_state":
            self.validation_state,

            "validation_report":
            self.validation_report
        }