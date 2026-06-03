# ============================================
# NEXRYN RUNTIME STATE
# ============================================

from datetime import datetime


# ============================================
# RUNTIME STATE
# ============================================

class RuntimeState:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # CORE CONTEXT
        # ====================================

        self.context = {}

        # ====================================
        # STAGES
        # ====================================

        self.current_stage = None

        self.completed_stages = []

        self.failed_stages = []

        # ====================================
        # EXECUTION LOGS
        # ====================================

        self.logs = []

        # ====================================
        # CONTEXT HISTORY
        # ====================================

        self.context_history = []

        # ====================================
        # EXECUTION METRICS
        # ====================================

        self.execution_metrics = {

            "stages_completed":
            0,

            "stages_failed":
            0,

            "context_updates":
            0,

            "runtime_events":
            0
        }

        # ====================================
        # GOVERNANCE STATE
        # ====================================

        self.governance_state = {

            "governance_active":
            True,

            "runtime_stable":
            True,

            "recovery_mode":
            False
        }

        # ====================================
        # MULTI TASK STATE
        # ====================================

        self.multi_task_state = {

            "multi_task_mode":
            False,

            "active_tasks":
            0,

            "shared_reasoning":
            False
        }

        # ====================================
        # RUNTIME STATUS
        # ====================================

        self.runtime_status = {

            "runtime_initialized":
            True,

            "runtime_active":
            False,

            "runtime_completed":
            False,

            "initialization_timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # SET STAGE
    # ========================================

    def set_stage(

        self,

        stage_name
    ):

        self.current_stage = (
            stage_name
        )

        self.logs.append(

            f"ENTER STAGE :: {stage_name}"
        )

        self.execution_metrics[
            "runtime_events"
        ] += 1

    # ========================================
    # COMPLETE STAGE
    # ========================================

    def complete_stage(

        self,

        stage_name
    ):

        self.completed_stages.append(
            stage_name
        )

        self.logs.append(

            f"COMPLETE STAGE :: {stage_name}"
        )

        self.execution_metrics[
            "stages_completed"
        ] += 1

    # ========================================
    # FAIL STAGE
    # ========================================

    def fail_stage(

        self,

        stage_name
    ):

        self.failed_stages.append(
            stage_name
        )

        self.logs.append(

            f"FAILED STAGE :: {stage_name}"
        )

        self.execution_metrics[
            "stages_failed"
        ] += 1

        self.governance_state[
            "runtime_stable"
        ] = False

    # ========================================
    # UPDATE CONTEXT
    # ========================================

    def update_context(

        self,

        key,

        value
    ):

        self.context[key] = value

        self.context_history.append({

            "key":
            key,

            "timestamp":
            str(datetime.utcnow())
        })

        self.execution_metrics[
            "context_updates"
        ] += 1

    # ========================================
    # BULK UPDATE CONTEXT
    # ========================================

    def bulk_update_context(

        self,

        updates
    ):

        for key, value in (
            updates.items()
        ):

            self.update_context(
                key,
                value
            )

    # ========================================
    # GET CONTEXT
    # ========================================

    def get_context(self):

        return self.context

    # ========================================
    # ENABLE MULTI TASK MODE
    # ========================================

    def enable_multi_task_mode(

        self,

        task_count=0
    ):

        self.multi_task_state = {

            "multi_task_mode":
            True,

            "active_tasks":
            task_count,

            "shared_reasoning":
            True
        }

    # ========================================
    # START RUNTIME
    # ========================================

    def start_runtime(self):

        self.runtime_status[
            "runtime_active"
        ] = True

        self.logs.append(
            "RUNTIME STARTED"
        )

    # ========================================
    # COMPLETE RUNTIME
    # ========================================

    def complete_runtime(self):

        self.runtime_status[
            "runtime_completed"
        ] = True

        self.runtime_status[
            "runtime_active"
        ] = False

        self.logs.append(
            "RUNTIME COMPLETED"
        )

    # ========================================
    # ENABLE RECOVERY MODE
    # ========================================

    def enable_recovery_mode(self):

        self.governance_state[
            "recovery_mode"
        ] = True

        self.logs.append(
            "RECOVERY MODE ENABLED"
        )

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "current_stage":
            self.current_stage,

            "completed_stages":
            self.completed_stages,

            "failed_stages":
            self.failed_stages,

            "execution_metrics":
            self.execution_metrics,

            "governance_state":
            self.governance_state,

            "multi_task_state":
            self.multi_task_state,

            "runtime_status":
            self.runtime_status,

            "context_size":
            len(self.context),

            "log_count":
            len(self.logs)
        }