# ============================================
# NEXRYN BENCHMARK VALIDATOR
# ============================================

import os

from datetime import datetime


# ============================================
# BENCHMARK VALIDATOR
# ============================================

class BenchmarkValidator:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.validation_report = {

            "validated_tasks":
            0,

            "invalid_tasks":
            0,

            "missing_files":
            0,

            "empty_files":
            0,

            "validation_timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # VALIDATE TASK PATH
    # ========================================

    def validate_task_path(

        self,

        task_path
    ):

        # ====================================
        # FILE EXISTS
        # ====================================

        if not os.path.exists(task_path):

            self.validation_report[
                "missing_files"
            ] += 1

            self.validation_report[
                "invalid_tasks"
            ] += 1

            return {

                "valid":
                False,

                "reason":
                "missing_file",

                "task":
                task_path
            }

        # ====================================
        # EMPTY FILE
        # ====================================

        if os.path.getsize(task_path) == 0:

            self.validation_report[
                "empty_files"
            ] += 1

            self.validation_report[
                "invalid_tasks"
            ] += 1

            return {

                "valid":
                False,

                "reason":
                "empty_file",

                "task":
                task_path
            }

        # ====================================
        # VALID TASK
        # ====================================

        self.validation_report[
            "validated_tasks"
        ] += 1

        return {

            "valid":
            True,

            "reason":
            "validated",

            "task":
            task_path
        }

    # ========================================
    # VALIDATE MULTIPLE TASKS
    # ========================================

    def validate_tasks(

        self,

        task_paths
    ):

        results = []

        for task_path in task_paths:

            result = (

                self.validate_task_path(
                    task_path
                )
            )

            results.append(
                result
            )

        return results

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return self.validation_report