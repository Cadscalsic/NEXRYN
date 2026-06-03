# ============================================
# NEXRYN FAILURE ANALYSIS SYSTEM
# ============================================

import traceback

from datetime import datetime


# ============================================
# BENCHMARK FAILURE ANALYZER
# ============================================

class BenchmarkFailureAnalyzer:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.failures = []

        self.failure_metrics = {

            "total_failures":
            0,

            "runtime_failures":
            0,

            "inference_failures":
            0,

            "planning_failures":
            0,

            "transformation_failures":
            0,

            "evaluation_failures":
            0
        }

    # ========================================
    # RECORD FAILURE
    # ========================================

    def record_failure(

        self,

        task_path,

        error,

        stage="unknown",

        runtime_context=None
    ):

        failure = {

            "task":
            task_path,

            "stage":
            stage,

            "error":
            str(error),

            "traceback":
            traceback.format_exc(),

            "context_size":

            len(
                runtime_context or {}
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.failures.append(
            failure
        )

        self.update_metrics(stage)

        return failure

    # ========================================
    # UPDATE METRICS
    # ========================================

    def update_metrics(

        self,

        stage
    ):

        self.failure_metrics[
            "total_failures"
        ] += 1

        if stage == "runtime":

            self.failure_metrics[
                "runtime_failures"
            ] += 1

        elif stage == "inference":

            self.failure_metrics[
                "inference_failures"
            ] += 1

        elif stage == "planning":

            self.failure_metrics[
                "planning_failures"
            ] += 1

        elif stage == "transformation":

            self.failure_metrics[
                "transformation_failures"
            ] += 1

        elif stage == "evaluation":

            self.failure_metrics[
                "evaluation_failures"
            ] += 1

    # ========================================
    # FAILURE SUMMARY
    # ========================================

    def summary(self):

        return {

            "configuration":
            self.configuration,

            "metrics":
            self.metrics,

            "results":
            self.results,

            "failures":
            self.failures,

            "failure_analysis":

            self.failure_analyzer.summary(),

            "execution_history":
            self.execution_history
        }

    # ========================================
    # LATEST FAILURE
    # ========================================

    def latest_failure(self):

        if not self.failures:

            return {}

        return self.failures[-1]