# ============================================
# NEXRYN RUNTIME WATCHDOG
# ============================================

import time

from datetime import datetime


# ============================================
# RUNTIME WATCHDOG
# ============================================

class RuntimeWatchdog:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.watchdog_state = {

            "watchdog_active":
            True,

            "runtime_monitoring":
            True,

            "recursion_protection":
            True,

            "memory_monitoring":
            True,

            "execution_timeout":
            True
        }

        # ====================================
        # LIMITS
        # ====================================

        self.max_execution_time = 60

        self.max_context_size = 1000

        self.max_recursion_depth = 50

        # ====================================
        # RUNTIME STATUS
        # ====================================

        self.runtime_status = {

            "runtime_safe":
            True,

            "warnings":
            [],

            "critical_events":
            []
        }

    # ========================================
    # MONITOR EXECUTION TIME
    # ========================================

    def monitor_execution_time(

        self,

        start_time
    ):

        elapsed = (

            time.time()
            - start_time
        )

        if elapsed > (
            self.max_execution_time
        ):

            self.runtime_status[
                "runtime_safe"
            ] = False

            self.runtime_status[
                "critical_events"
            ].append({

                "event":
                "execution_timeout",

                "elapsed":
                elapsed,

                "timestamp":
                str(datetime.utcnow())
            })

        return elapsed

    # ========================================
    # MONITOR CONTEXT SIZE
    # ========================================

    def monitor_context(

        self,

        runtime_context
    ):

        context_size = len(
            runtime_context
        )

        if context_size > (
            self.max_context_size
        ):

            self.runtime_status[
                "warnings"
            ].append({

                "warning":
                "large_context",

                "context_size":
                context_size,

                "timestamp":
                str(datetime.utcnow())
            })

        return context_size

    # ========================================
    # MONITOR RECURSION
    # ========================================

    def monitor_recursion(

        self,

        recursive_depth
    ):

        if recursive_depth > (
            self.max_recursion_depth
        ):

            self.runtime_status[
                "runtime_safe"
            ] = False

            self.runtime_status[
                "critical_events"
            ].append({

                "event":
                "recursive_overflow",

                "recursive_depth":
                recursive_depth,

                "timestamp":
                str(datetime.utcnow())
            })

        return recursive_depth

    # ========================================
    # VALIDATE RUNTIME
    # ========================================

    def validate_runtime(

        self,

        runtime_context,

        recursive_depth,

        start_time
    ):

        execution_time = (
            self.monitor_execution_time(
                start_time
            )
        )

        context_size = (
            self.monitor_context(
                runtime_context
            )
        )

        recursion_depth = (
            self.monitor_recursion(
                recursive_depth
            )
        )

        return {

            "runtime_safe":

            self.runtime_status.get(
                "runtime_safe",
                True
            ),

            "execution_time":
            execution_time,

            "context_size":
            context_size,

            "recursive_depth":
            recursion_depth,

            "runtime_status":
            self.runtime_status
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "watchdog_state":
            self.watchdog_state,

            "runtime_status":
            self.runtime_status
        }