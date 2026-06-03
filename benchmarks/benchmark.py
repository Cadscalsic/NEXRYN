# ============================================
# NEXRYN COGNITIVE BENCHMARK SYSTEM
# ============================================

import os
import json
import time
import traceback

from datetime import datetime

from runtime.pipeline import (
    NEXRYNPipeline
)

# ============================================
# BENCHMARK METRICS
# ============================================

from benchmarks.benchmark_metrics import (
    BenchmarkMetrics
)

# ============================================
# FAILURE ANALYZER
# ============================================

from benchmarks.benchmark_failures import (
    BenchmarkFailureAnalyzer
)

# ============================================
# TASK TAXONOMY
# ============================================

from benchmarks.task_taxonomy import (
    TaskTaxonomy
)

# ============================================
# NEXRYN BENCHMARK
# ============================================

class NEXRYNBenchmark:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        task_paths
    ):

        # ====================================
        # TASK PATHS
        # ====================================

        self.task_paths = (
            task_paths
        )

        # ====================================
        # RESULTS
        # ====================================

        self.results = []

        # ====================================
        # FAILURES
        # ====================================

        self.failures = []

        # ====================================
        # EXECUTION HISTORY
        # ====================================

        self.execution_history = []

        # ====================================
        # METRICS SYSTEM
        # ====================================

        self.metrics_engine = (
            BenchmarkMetrics()
        )

        # ====================================
        # FAILURE ANALYZER
        # ====================================

        self.failure_analyzer = (
            BenchmarkFailureAnalyzer()
        )

        # ====================================
        # TASK TAXONOMY
        # ====================================

        self.task_taxonomy = (
            TaskTaxonomy()
        )

        # ====================================
        # BENCHMARK METRICS
        # ====================================

        self.metrics = {}

        # ====================================
        # CONFIGURATION
        # ====================================

        self.configuration = {

            "runtime_mode":
            "benchmark",

            "adaptive_evaluation":
            True,

            "failure_analysis":
            True,

            "cognitive_metrics":
            True,

            "recursive_monitoring":
            True,

            "planning_metrics":
            True
        }

    # ========================================
    # RUN SINGLE TASK
    # ========================================

    def run_task(

        self,

        task_path
    ):

        print("\n===================================")
        print("NEXRYN BENCHMARK TASK")
        print("===================================\n")

        print("TASK:")
        print(task_path)

        print()

        start_time = time.time()

        try:

            # ================================
            # INITIALIZE PIPELINE
            # ================================

            pipeline = (
                NEXRYNPipeline(
                    task_path
                )
            )

            # ================================
            # RUN PIPELINE
            # ================================

            final_context = (
                pipeline.run()
            )

            # ================================
            # EXECUTION TIME
            # ================================

            execution_time = round(

                time.time()
                - start_time,

                4
            )

            # ================================
            # REPORTS
            # ================================

            evaluation_result = (

                final_context.get(
                    "evaluation_result",
                    {}
                )
            )

            inference_report = (

                final_context.get(
                    "inference_report",
                    {}
                )
            )

            planning_report = (

                final_context.get(
                    "planning_report",
                    {}
                )
            )

            recursive_report = (

                final_context.get(
                    "recursive_report",
                    {}
                )
            )

            # ================================
            # TASK CLASSIFICATION
            # ================================

            task_classification = (

                self.task_taxonomy.classify(
                    final_context
                )
            )

            # ================================
            # RESULT
            # ================================

            result = {

                "task":
                task_path,

                "success":

                evaluation_result.get(
                    "success",
                    False
                ),

                "accuracy":

                evaluation_result.get(
                    "accuracy",
                    0.0
                ),

                "reasoning_depth":

                inference_report.get(
                    "reasoning_depth",
                    0
                ),

                "recursive_depth":

                recursive_report.get(
                    "recursive_depth",
                    0
                ),

                "planning_nodes":

                planning_report.get(
                    "planning_nodes",
                    0
                ),

                "execution_time":
                execution_time,

                "context_size":

                len(
                    final_context
                ),

                "runtime_status":

                final_context.get(
                    "runtime_metadata",
                    {}
                ).get(
                    "runtime_status",
                    "unknown"
                ),

                "task_type":

                task_classification.get(
                    "task_type",
                    "unknown"
                ),

                "reasoning_family":

                task_classification.get(
                    "reasoning_family",
                    "unknown"
                ),

                "difficulty":

                task_classification.get(
                    "difficulty",
                    "unknown"
                ),

                "timestamp":
                str(datetime.utcnow())
            }

            # ================================
            # STORE RESULT
            # ================================

            self.results.append(
                result
            )

            self.execution_history.append({

                "task":
                task_path,

                "status":
                "completed",

                "timestamp":
                str(datetime.utcnow())
            })

            print("TASK RESULT:\n")

            print(result)

            print()

            return result

        except Exception as error:

            execution_time = round(

                time.time()
                - start_time,

                4
            )

            # ================================
            # FAILURE REPORT
            # ================================

            failure_report = (

                self.failure_analyzer
                .record_failure(

                    task_path=
                    task_path,

                    error=
                    error,

                    stage=
                    "runtime"
                )
            )

            failure_report[
                "execution_time"
            ] = execution_time

            # ================================
            # STORE FAILURE
            # ================================

            self.failures.append(
                failure_report
            )

            self.execution_history.append({

                "task":
                task_path,

                "status":
                "failed",

                "timestamp":
                str(datetime.utcnow())
            })

            print("TASK FAILURE:\n")

            print(failure_report)

            print()

            return failure_report

    # ========================================
    # RUN ALL TASKS
    # ========================================

    def run_all_tasks(self):

        print("\n===================================")
        print("NEXRYN MULTI-TASK BENCHMARK")
        print("===================================\n")

        for task_path in (
            self.task_paths
        ):

            self.run_task(
                task_path
            )

        # ====================================
        # COMPUTE METRICS
        # ====================================

        self.compute_metrics()

        return self.export_report()

    # ========================================
    # COMPUTE METRICS
    # ========================================

    def compute_metrics(self):

        self.metrics = (

            self.metrics_engine.compute(

                self.results,

                self.failures
            )
        )

        return self.metrics

    # ========================================
    # SAVE REPORT
    # ========================================

    def save_report(

        self,

        output_path=
        "data/generated/benchmark_report.json"
    ):

        os.makedirs(

            os.path.dirname(
                output_path
            ),

            exist_ok=True
        )

        with open(

            output_path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                self.export_report(),

                file,

                indent=4
            )

    # ========================================
    # SUMMARY
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
    # PRINT SUMMARY
    # ========================================

    def print_summary(self):

        report = (
            self.summary()
        )

        print("\n===================================")
        print("NEXRYN BENCHMARK SUMMARY")
        print("===================================\n")

        print("METRICS:\n")

        print(
            report["metrics"]
        )

        print()

        print("RESULT COUNT:")

        print(
            len(
                report["results"]
            )
        )

        print()

        print("FAILURE COUNT:")

        print(
            len(
                report["failures"]
            )
        )

        print()

    # ========================================
    # EXPORT REPORT
    # ========================================

    def export_report(self):

        return {

            "benchmark_summary":
            self.summary(),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":

    benchmark_tasks = [

        "data/training/task_001.json"
    ]

    benchmark = (
        NEXRYNBenchmark(
            benchmark_tasks
        )
    )

    benchmark.run_all_tasks()

    benchmark.print_summary()

    benchmark.save_report()