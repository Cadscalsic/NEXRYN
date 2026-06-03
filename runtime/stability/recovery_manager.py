# ============================================
# NEXRYN RECOVERY MANAGER
# ============================================

from datetime import datetime


# ============================================
# RECOVERY MANAGER
# ============================================

class RecoveryManager:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.recovery_state = {

            "recovery_active":
            True,

            "automatic_recovery":
            True,

            "context_repair":
            True,

            "runtime_restoration":
            True
        }

        # ====================================
        # RECOVERY REPORT
        # ====================================

        self.recovery_report = {

            "recoveries":
            0,

            "repaired_contexts":
            0,

            "restored_runtime":
            0,

            "failed_recoveries":
            0,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # REPAIR CONTEXT
    # ========================================

    def repair_context(

        self,

        runtime_context
    ):

        # ====================================
        # REQUIRED KEYS
        # ====================================

        required_keys = {

            "runtime_initialized":
            False,

            "runtime_metadata":
            {},

            "execution_state":
            {}
        }

        repaired = False

        for key, default_value in (
            required_keys.items()
        ):

            if key not in runtime_context:

                runtime_context[
                    key
                ] = default_value

                repaired = True

        if repaired:

            self.recovery_report[
                "repaired_contexts"
            ] += 1

        return runtime_context

    # ========================================
    # RESTORE RUNTIME
    # ========================================

    def restore_runtime(

        self,

        runtime_context
    ):

        runtime_context[
            "runtime_restored"
        ] = True

        runtime_context[
            "recovery_timestamp"
        ] = str(datetime.utcnow())

        self.recovery_report[
            "restored_runtime"
        ] += 1

        return runtime_context

    # ========================================
    # EXECUTE RECOVERY
    # ========================================

    def recover(

        self,

        runtime_context
    ):

        try:

            repaired_context = (
                self.repair_context(
                    runtime_context
                )
            )

            restored_context = (
                self.restore_runtime(
                    repaired_context
                )
            )

            self.recovery_report[
                "recoveries"
            ] += 1

            return {

                "recovered":
                True,

                "runtime_context":
                restored_context,

                "recovery_report":
                self.recovery_report
            }

        except Exception as error:

            self.recovery_report[
                "failed_recoveries"
            ] += 1

            return {

                "recovered":
                False,

                "error":
                str(error),

                "recovery_report":
                self.recovery_report
            }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "recovery_state":
            self.recovery_state,

            "recovery_report":
            self.recovery_report
        }