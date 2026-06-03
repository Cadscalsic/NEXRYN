# ============================================
# NEXRYN RUNTIME SCHEDULER
# ============================================

from datetime import datetime


# ============================================
# RUNTIME SCHEDULER
# ============================================

class RuntimeScheduler:

    def __init__(self):

        # ====================================
        # EXECUTION QUEUE
        # ====================================

        self.stage_queue = []

        # ====================================
        # EXECUTION HISTORY
        # ====================================

        self.execution_history = []

        # ====================================
        # FAILED STAGES
        # ====================================

        self.failed_stages = []

        # ====================================
        # COMPLETED STAGES
        # ====================================

        self.completed_stages = []

        # ====================================
        # ACTIVE STAGE
        # ====================================

        self.active_stage = None

        # ====================================
        # SCHEDULER METRICS
        # ====================================

        self.metrics = {

            "scheduled_stages":
            0,

            "completed_stages":
            0,

            "failed_stages":
            0,

            "rescheduled_stages":
            0,

            "scheduler_cycles":
            0,

            "scheduler_health":
            "stable"
        }

        # ====================================
        # SCHEDULER STATE
        # ====================================

        self.scheduler_state = {

            "scheduler_mode":
            "adaptive_runtime_scheduler",

            "runtime_balancing":
            "enabled",

            "priority_scheduling":
            "enabled",

            "failure_recovery":
            "enabled"
        }

    # ============================================
    # ADD STAGE
    # ============================================

    def add_stage(

        self,

        stage_name,

        priority="medium"
    ):

        if not self.has_stage(
            stage_name
        ):

            stage_record = {

                "name":
                stage_name,

                "priority":
                priority,

                "status":
                "scheduled",

                "retries":
                0,

                "scheduled_at":
                str(
                    datetime.utcnow()
                )
            }

            self.stage_queue.append(
                stage_record
            )

            self.metrics[
                "scheduled_stages"
            ] += 1

    # ============================================
    # REMOVE STAGE
    # ============================================

    def remove_stage(

        self,

        stage_name
    ):

        self.stage_queue = [

            stage

            for stage in self.stage_queue

            if stage["name"] != stage_name
        ]

    # ============================================
    # GET NEXT STAGE
    # ============================================

    def get_next_stage(self):

        if len(self.stage_queue) == 0:

            return None

        # ====================================
        # PRIORITY SORTING
        # ====================================

        priority_order = {

            "critical": 0,

            "high": 1,

            "medium": 2,

            "low": 3
        }

        self.stage_queue.sort(

            key=lambda stage:

            priority_order.get(

                stage["priority"],

                2
            )
        )

        next_stage = self.stage_queue.pop(0)

        self.active_stage = next_stage

        self.metrics[
            "scheduler_cycles"
        ] += 1

        return next_stage

    # ============================================
    # COMPLETE STAGE
    # ============================================

    def complete_stage(

        self,

        stage_name
    ):

        self.completed_stages.append({

            "stage":
            stage_name,

            "completed_at":
            str(
                datetime.utcnow()
            )
        })

        self.metrics[
            "completed_stages"
        ] += 1

        self.execution_history.append({

            "stage":
            stage_name,

            "status":
            "completed",

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

        if (

            self.active_stage

            and

            self.active_stage["name"]

            ==

            stage_name
        ):

            self.active_stage = None

    # ============================================
    # FAIL STAGE
    # ============================================

    def fail_stage(

        self,

        stage_name,

        retry=True
    ):

        self.failed_stages.append({

            "stage":
            stage_name,

            "failed_at":
            str(
                datetime.utcnow()
            )
        })

        self.metrics[
            "failed_stages"
        ] += 1

        self.metrics[
            "scheduler_health"
        ] = "degraded"

        self.execution_history.append({

            "stage":
            stage_name,

            "status":
            "failed",

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

        # ====================================
        # RETRY LOGIC
        # ====================================

        if retry:

            self.add_stage(

                stage_name,

                priority="high"
            )

            self.metrics[
                "rescheduled_stages"
            ] += 1

    # ============================================
    # CLEAR SCHEDULE
    # ============================================

    def clear(self):

        self.stage_queue.clear()

    # ============================================
    # GET STAGES
    # ============================================

    def get_stages(self):

        return [

            stage["name"]

            for stage in self.stage_queue
        ]

    # ============================================
    # HAS STAGE
    # ============================================

    def has_stage(

        self,

        stage_name
    ):

        return any(

            stage["name"] == stage_name

            for stage in self.stage_queue
        )

    # ============================================
    # GET ACTIVE STAGE
    # ============================================

    def get_active_stage(self):

        return self.active_stage

    # ============================================
    # HEALTH CHECK
    # ============================================

    def health_check(self):

        healthy = True

        if self.metrics[
            "failed_stages"
        ] > 5:

            healthy = False

        return {

            "healthy":
            healthy,

            "scheduler_health":
            self.metrics[
                "scheduler_health"
            ],

            "queued_stages":
            len(
                self.stage_queue
            ),

            "failed_stages":
            self.metrics[
                "failed_stages"
            ]
        }

    # ============================================
    # BUILD SCHEDULER REPORT
    # ============================================

    def build_scheduler_report(self):

        return {

            "scheduler_state":
            self.scheduler_state,

            "metrics":
            self.metrics,

            "health":
            self.health_check(),

            "active_stage":
            self.active_stage,

            "queued_stages":
            len(
                self.stage_queue
            ),

            "completed_stages":
            len(
                self.completed_stages
            ),

            "failed_stages":
            len(
                self.failed_stages
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

    # ============================================
    # PRINT SCHEDULE
    # ============================================

    def print_schedule(self):

        print(
            "\n=================================================="
        )

        print(
            "NEXRYN :: RUNTIME SCHEDULE"
        )

        print(
            "==================================================\n"
        )

        for index, stage in enumerate(
            self.stage_queue
        ):

            print(

                f"{index + 1}. "

                f"{stage['name']} "

                f"[{stage['priority']}]"
            )

        print()