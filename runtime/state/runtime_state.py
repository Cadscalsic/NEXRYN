# ============================================
# NEXRYN RUNTIME STATE
# ============================================

from datetime import datetime

from runtime.context import (
    context_bus
)

from runtime.context import (
    context_delta_engine
)


# ============================================
# RUNTIME STATE
# ============================================

class RuntimeState:

    def __init__(self):

        # ====================================
        # EXECUTION STAGES
        # ====================================

        self.current_stage = None

        self.completed_stages = []

        self.failed_stages = []

        # ====================================
        # RUNTIME CONTEXT
        # ====================================

        self.context = {}

        # ====================================
        # ACTIVE ENGINE
        # ====================================

        self.active_engine = None

        # ====================================
        # EXECUTION STATUS
        # ====================================

        self.is_running = False

        self.has_failed = False

        # ====================================
        # TRACE LOGS
        # ====================================

        self.logs = []

        # ====================================
        # RUNTIME EVENTS
        # ====================================

        self.runtime_events = []

        # ====================================
        # DELTA ENGINE
        # ====================================

        self.delta_engine = (
            context_delta_engine
        )

        # ====================================
        # EXECUTION METRICS
        # ====================================

        self.metrics = {

            "runtime_cycles":
            0,

            "context_updates":
            0,

            "stage_transitions":
            0,

            "runtime_errors":
            0,

            "runtime_health":
            "stable"
        }

        # ====================================
        # RUNTIME TIMING
        # ====================================

        self.start_timestamp = None

        self.stop_timestamp = None

    # ========================================
    # BULK UPDATE CONTEXT
    # ========================================

    def bulk_update_context(

        self,

        updates
    ):

        # ====================================
        # SAFE NORMALIZATION
        # ====================================

        if updates is None:

            return {

                "bulk_update_state":
                "skipped",

                "reason":
                "updates_none"
            }

        if not isinstance(
            updates,
            dict
        ):

            return {

                "bulk_update_state":
                "invalid",

                "reason":
                "updates_not_dict"
            }

        # ====================================
        # CONTEXT STORAGE
        # ====================================

        if not hasattr(
            self,
            "context"
        ):

            self.context = {}

        if self.context is None:

            self.context = {}

        if not isinstance(
            self.context,
            dict
        ):

            self.context = {}

        # ====================================
        # BULK UPDATE
        # ====================================

        for key, value in updates.items():

            self.context[key] = value

        # ====================================
        # UPDATE METADATA
        # ====================================

        if not hasattr(
            self,
            "update_history"
        ):

            self.update_history = []

        self.update_history.append({

            "updated_keys":
            list(updates.keys()),

            "update_count":
            len(updates),

            "timestamp":
            str(datetime.utcnow())
        })

        # ====================================
        # FINAL REPORT
        # ====================================

        return {

            "bulk_update_state":
            "completed",

            "updated_keys":
            len(updates),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        metadata=None
    ):

        self.runtime_events.append({

            "event":
            event_type,

            "metadata":
            metadata or {},

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

    # ========================================
    # START RUNTIME
    # ========================================

    def start(self):

        self.is_running = True

        self.start_timestamp = (
            datetime.utcnow()
        )

        self.metrics[
            "runtime_cycles"
        ] += 1

        self.logs.append(
            "RUNTIME STARTED"
        )

        self.register_event(
            "runtime_started"
        )

    # ========================================
    # STOP RUNTIME
    # ========================================

    def stop(self):

        self.is_running = False

        self.stop_timestamp = (
            datetime.utcnow()
        )

        self.logs.append(
            "RUNTIME STOPPED"
        )

        self.register_event(
            "runtime_stopped"
        )

    # ========================================
    # SET ACTIVE ENGINE
    # ========================================

    def set_active_engine(

        self,

        engine_name
    ):

        self.active_engine = engine_name

        self.logs.append(
            f"ACTIVE ENGINE :: {engine_name}"
        )

        self.register_event(

            "engine_activation",

            {
                "engine":
                engine_name
            }
        )

    # ========================================
    # ENTER STAGE
    # ========================================

    def set_stage(

        self,

        stage_name
    ):

        self.current_stage = stage_name

        self.metrics[
            "stage_transitions"
        ] += 1

        self.logs.append(
            f"ENTER STAGE :: {stage_name}"
        )

        self.register_event(

            "stage_entered",

            {
                "stage":
                stage_name
            }
        )

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

        self.register_event(

            "stage_completed",

            {
                "stage":
                stage_name
            }
        )

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

        self.has_failed = True

        self.metrics[
            "runtime_errors"
        ] += 1

        self.metrics[
            "runtime_health"
        ] = "degraded"

        self.logs.append(
            f"FAILED STAGE :: {stage_name}"
        )

        self.register_event(

            "stage_failed",

            {
                "stage":
                stage_name
            }
        )

    # ========================================
    # UPDATE CONTEXT
    # ========================================

    def update_context(

        self,

        key,

        value,

        priority="medium"
    ):

        # ====================================
        # STRUCTURED CONTEXT STORAGE
        # ====================================

        self.context[key] = {

            "value":
            value,

            "priority":
            priority,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        # ====================================
        # DELTA TRACKING
        # ====================================

        self.delta_engine.detect_changes(
            self.context
        )

        # ====================================
        # METRICS
        # ====================================

        self.metrics[
            "context_updates"
        ] += 1

        # ====================================
        # CONTEXT BUS
        # ====================================

        context_bus.publish(

            key,

            value,

            priority
        )

        # ====================================
        # AUTO COMPRESSION
        # ====================================

        context_bus.compress_contexts(
            max_active=64
        )

        # ====================================
        # LOGS
        # ====================================

        self.logs.append(

            f"CONTEXT UPDATE :: {key}"
        )


    # ============================================
    # SET FULL CONTEXT
    # ============================================

    def set_context(

        self,

        context
    ):

        self.context = {}

        for key, value in context.items():

            self.context[key] = {

                "value":
                value,

                "priority":
                "medium"
            }

   
    # ========================================
    # GET CONTEXT VALUE
    # ========================================

    def get_context_value(

        self,

        key,

        default=None
    ):

        if key not in self.context:

            return default

        stored_value = self.context.get(

            key,

            {}
        )

        if isinstance(

            stored_value,

            dict
        ) and "value" in stored_value:

            return stored_value["value"]

        return stored_value

    # ========================================
    # RUNTIME HEALTH CHECK
    # ========================================

    def health_check(self):

        healthy = True

        if len(self.failed_stages) > 3:

            healthy = False

        if self.metrics[
            "runtime_errors"
        ] > 5:

            healthy = False

        return {

            "healthy":
            healthy,

            "runtime_health":
            self.metrics[
                "runtime_health"
            ],

            "failed_stages":
            len(
                self.failed_stages
            ),

            "runtime_errors":
            self.metrics[
                "runtime_errors"
            ]
        }

    # ========================================
    # BUILD RUNTIME REPORT
    # ========================================

    def build_runtime_report(self):

        return {

            "runtime_metrics":
            self.metrics,

            "health":
            self.health_check(),

            "context_count":
            len(
                self.context
            ),

            "events":
            len(
                self.runtime_events
            ),

            "active_engine":
            self.active_engine,

            "current_stage":
            self.current_stage
        }
        
    def get_context(self):

        return self.context

    # ========================================
    # GET DELTA SNAPSHOT
    # ========================================

    def get_delta_snapshot(self):

        return (

            self.delta_engine
            .build_summary()
        )

    def summary(self):

        return {

            "current_stage":
            self.current_stage,

            "active_engine":
            self.active_engine,

            "completed_stages":
            len(
                self.completed_stages
            ),

            "failed_stages":
            len(
                self.failed_stages
            ),

            "is_running":
            self.is_running,

            "has_failed":
            self.has_failed,

            "active_contexts":
            len(
                context_bus.active_contexts
            ),

            "dormant_contexts":
            len(
                context_bus.dormant_contexts
            ),

            "archived_contexts":
            len(
                context_bus.archived_contexts
            ),

            "runtime_health":
            self.metrics[
                "runtime_health"
            ],

            "runtime_cycles":
            self.metrics[
                "runtime_cycles"
            ]
        }