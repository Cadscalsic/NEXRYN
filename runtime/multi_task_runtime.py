# ============================================
# NEXRYN MULTI TASK RUNTIME
# ============================================

import time

from datetime import datetime

from runtime.pipeline import (
    NEXRYNPipeline
)

from runtime.shared_transfer_memory import (
    SharedTransferMemory
)

from runtime.strategy_reuse_engine import (
    StrategyReuseEngine
)

from runtime.adaptive_task_scheduler import (
    AdaptiveTaskScheduler
)


# ============================================
# MULTI TASK RUNTIME
# ============================================

class MultiTaskRuntime:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        task_paths
    ):

        # ====================================
        # TASKS
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
        # SHARED MEMORY
        # ====================================

        self.shared_memory = {

            "successful_strategies":
            [],

            "failed_strategies":
            [],

            "semantic_patterns":
            [],

            "reasoning_history":
            []
        }

        # ====================================
        # TRANSFER MEMORY
        # ====================================

        self.transfer_memory = (

            SharedTransferMemory()
        )

        # ====================================
        # STRATEGY REUSE ENGINE
        # ====================================

        self.strategy_reuse_engine = (

            StrategyReuseEngine(
                self.transfer_memory
            )
        )

        # ====================================
        # TASK SCHEDULER
        # ====================================

        self.task_scheduler = (

            AdaptiveTaskScheduler()
        )

        # ====================================
        # GLOBAL METRICS
        # ====================================

        self.runtime_metrics = {

            "tasks_completed":
            0,

            "tasks_failed":
            0,

            "global_accuracy":
            0.0,

            "total_execution_time":
            0.0,

            "average_reasoning_depth":
            0.0
        }

        # ====================================
        # EXECUTION STATE
        # ====================================

        self.runtime_state = {

            "runtime_mode":
            "multi_task_cognition",

            "cross_task_learning":
            True,

            "shared_reasoning":
            True,

            "adaptive_transfer":
            True,

            "adaptive_scheduling":
            True,

            "runtime_status":
            "initialized"
        }

    # ========================================
    # RUN SINGLE TASK
    # ========================================

    def run_task(

        self,

        task_path
    ):

        print("\n===================================")
        print("NEXRYN MULTI TASK EXECUTION")
        print("===================================\n")

        print("TASK:")
        print(task_path)

        print()

        start_time = time.time()

        # ====================================
        # REUSE CONTEXT
        # ====================================

        reuse_context = (

            self.strategy_reuse_engine
            .build_reuse_context()
        )

        reuse_hints = (

            self.strategy_reuse_engine
            .generate_reuse_hints()
        )

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
            # EVALUATION
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

                "execution_time":
                execution_time,

                "reuse_context":
                reuse_context,

                "reuse_hints":
                reuse_hints,

                "timestamp":
                str(datetime.utcnow())
            }

            # ================================
            # STORE RESULT
            # ================================

            self.results.append(
                result
            )

            # ================================
            # UPDATE MEMORY
            # ================================

            self.update_shared_memory(
                final_context
            )

            # ================================
            # TRANSFER LEARNING
            # ================================

            transfer_report = (

                self.transfer_memory
                .transfer_knowledge(
                    final_context
                )
            )

            result[
                "transfer_report"
            ] = transfer_report

            # ================================
            # UPDATE METRICS
            # ================================

            self.runtime_metrics[
                "tasks_completed"
            ] += 1

            print("TASK RESULT:\n")

            print(result)

            print()

            return result

        except Exception as error:

            failure = {

                "task":
                task_path,

                "error":
                str(error),

                "timestamp":
                str(datetime.utcnow())
            }

            self.failures.append(
                failure
            )

            self.runtime_metrics[
                "tasks_failed"
            ] += 1

            print("TASK FAILURE:\n")

            print(failure)

            print()

            return failure

    # ========================================
    # UPDATE SHARED MEMORY
    # ========================================

    def update_shared_memory(

        self,

        final_context
    ):

        hypotheses = (

            final_context.get(
                "hypotheses",
                []
            )
        )

        semantic_abstractions = (

            final_context.get(
                "semantic_abstractions",
                []
            )
        )

        # ====================================
        # STORE HYPOTHESES
        # ====================================

        for hypothesis in hypotheses:

            self.shared_memory[
                "successful_strategies"
            ].append(
                hypothesis
            )

        # ====================================
        # STORE SEMANTICS
        # ====================================

        for abstraction in (
            semantic_abstractions
        ):

            self.shared_memory[
                "semantic_patterns"
            ].append(
                abstraction
            )

        # ====================================
        # STORE REASONING HISTORY
        # ====================================

        self.shared_memory[
            "reasoning_history"
        ].append({

            "hypothesis_count":
            len(hypotheses),

            "semantic_count":
            len(semantic_abstractions),

            "timestamp":
            str(datetime.utcnow())
        })

    # ========================================
    # RUN ALL TASKS
    # ========================================

    def run_all_tasks(self):

        print("\n===================================")
        print("NEXRYN MULTI TASK RUNTIME")
        print("===================================\n")

        runtime_start = time.time()

        # ====================================
        # GENERATE EXECUTION PLAN
        # ====================================

        execution_plan = (

            self.task_scheduler
            .generate_execution_plan(
                self.task_paths
            )
        )

        scheduled_tasks = (

            execution_plan.get(
                "scheduled_tasks",
                []
            )
        )

        # ====================================
        # EXECUTE TASKS
        # ====================================

        for scheduled_task in (
            scheduled_tasks
        ):

            task_path = (
                scheduled_task.get(
                    "task"
                )
            )

            self.run_task(
                task_path
            )

        # ====================================
        # TOTAL TASKS
        # ====================================

        total_tasks = len(
            self.results
        )

        # ====================================
        # GLOBAL ACCURACY
        # ====================================

        global_accuracy = round(

            sum([

                result.get(
                    "accuracy",
                    0.0
                )

                for result in self.results

            ])

            / max(
                total_tasks,
                1
            ),

            4
        )

        # ====================================
        # REASONING DEPTH
        # ====================================

        average_reasoning_depth = round(

            sum([

                result.get(
                    "reasoning_depth",
                    0
                )

                for result in self.results

            ])

            / max(
                total_tasks,
                1
            ),

            4
        )

        # ====================================
        # EXECUTION TIME
        # ====================================

        total_execution_time = round(

            time.time()
            - runtime_start,

            4
        )

        # ====================================
        # STORE METRICS
        # ====================================

        self.runtime_metrics = {

            "tasks_completed":

            self.runtime_metrics.get(
                "tasks_completed",
                0
            ),

            "tasks_failed":

            self.runtime_metrics.get(
                "tasks_failed",
                0
            ),

            "global_accuracy":
            global_accuracy,

            "total_execution_time":
            total_execution_time,

            "average_reasoning_depth":
            average_reasoning_depth
        }

        # ====================================
        # UPDATE STATE
        # ====================================

        self.runtime_state[
            "runtime_status"
        ] = "completed"

        return self.summary()

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "runtime_state":
            self.runtime_state,

            "runtime_metrics":
            self.runtime_metrics,

            "results":
            self.results,

            "failures":
            self.failures,

            "shared_memory":
            self.shared_memory,

            "transfer_memory":

            self.transfer_memory.summary(),

            "strategy_reuse_engine":

            self.strategy_reuse_engine
            .summary(),

            "task_scheduler":

            self.task_scheduler
            .summary()
        }


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":

    task_paths = [

        "data/training/task_001.json",

        "data/training/task_002.json",

        "data/training/task_003.json",

        "data/training/task_004.json",

        "data/training/task_005.json",

        "data/training/task_006.json",

        "data/training/task_007.json",

        "data/training/task_008.json",

        "data/training/task_009.json",

        "data/training/task_010.json"
    ]

    runtime = (
        MultiTaskRuntime(
            task_paths
        )
    )

    report = (
        runtime.run_all_tasks()
    )

    print("\n===================================")
    print("MULTI TASK SUMMARY")
    print("===================================\n")

    print(report)