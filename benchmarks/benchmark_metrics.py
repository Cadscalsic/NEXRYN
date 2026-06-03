# ============================================
# NEXRYN BENCHMARK METRICS SYSTEM
# ============================================

from datetime import datetime


# ============================================
# BENCHMARK METRICS
# ============================================

class BenchmarkMetrics:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.metrics = {

            "tasks_run":
            0,

            "successful_tasks":
            0,

            "failed_tasks":
            0,

            "success_rate":
            0.0,

            "average_accuracy":
            0.0,

            "average_reasoning_depth":
            0.0,

            "average_recursive_depth":
            0.0,

            "average_execution_time":
            0.0,

            "average_context_size":
            0.0,

            "average_planning_nodes":
            0.0,

            "cognitive_stability":
            0.0
        }

    # ========================================
    # COMPUTE METRICS
    # ========================================

    def compute(

        self,

        results,

        failures
    ):

        # ====================================
        # COUNTS
        # ====================================

        tasks_run = (
            len(results)
            +
            len(failures)
        )

        successful_tasks = len([

            result

            for result in results

            if result.get(
                "success",
                False
            )
        ])

        failed_tasks = len(
            failures
        )

        # ====================================
        # SUCCESS RATE
        # ====================================

        success_rate = round(

            successful_tasks
            / max(
                tasks_run,
                1
            ),

            4
        )

        # ====================================
        # ACCURACY
        # ====================================

        average_accuracy = (
            self.average(
                results,
                "accuracy"
            )
        )

        # ====================================
        # REASONING DEPTH
        # ====================================

        average_reasoning_depth = (
            self.average(
                results,
                "reasoning_depth"
            )
        )

        # ====================================
        # RECURSIVE DEPTH
        # ====================================

        average_recursive_depth = (
            self.average(
                results,
                "recursive_depth"
            )
        )

        # ====================================
        # EXECUTION TIME
        # ====================================

        average_execution_time = (
            self.average(
                results,
                "execution_time"
            )
        )

        # ====================================
        # CONTEXT SIZE
        # ====================================

        average_context_size = (
            self.average(
                results,
                "context_size"
            )
        )

        # ====================================
        # PLANNING NODES
        # ====================================

        average_planning_nodes = (
            self.average(
                results,
                "planning_nodes"
            )
        )

        # ====================================
        # COGNITIVE STABILITY
        # ====================================

        cognitive_stability = round(

            (
                success_rate
                *
                average_accuracy
            ),

            4
        )

        # ====================================
        # STORE METRICS
        # ====================================

        self.metrics = {

            "tasks_run":
            tasks_run,

            "successful_tasks":
            successful_tasks,

            "failed_tasks":
            failed_tasks,

            "success_rate":
            success_rate,

            "average_accuracy":
            average_accuracy,

            "average_reasoning_depth":
            average_reasoning_depth,

            "average_recursive_depth":
            average_recursive_depth,

            "average_execution_time":
            average_execution_time,

            "average_context_size":
            average_context_size,

            "average_planning_nodes":
            average_planning_nodes,

            "cognitive_stability":
            cognitive_stability,

            "timestamp":
            str(datetime.utcnow())
        }

        return self.metrics

    # ========================================
    # AVERAGE
    # ========================================

    def average(

        self,

        results,

        key
    ):

        if not results:

            return 0.0

        return round(

            sum([

                result.get(
                    key,
                    0
                )

                for result in results

            ])

            / len(results),

            4
        )

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return self.metrics