# ============================================
# NEXRYN TASK INGESTION SYSTEM
# ============================================

import os
import json

from datetime import datetime

from core.grid import ARCGrid


# ============================================
# ARC JSON LOADER
# ============================================

class ARCJSONLoader:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        json_path
    ):

        self.json_path = (
            json_path
        )

        self.task_data = {}

        self.task_metadata = {

            "task_loaded":
            False,

            "validation_passed":
            False,

            "task_profile_created":
            False,

            "ingestion_timestamp":
            str(datetime.utcnow())
        }

        self.load_report = {}

    # ========================================
    # LOAD TASK
    # ========================================

    def load(self):

        try:

            self.task_data = (
                self.load_json()
            )

            validation_result = (
                self.validate_task()
            )

            if not validation_result:

                return False

            self.task_metadata[
                "task_loaded"
            ] = True

            self.task_metadata[
                "validation_passed"
            ] = True

            self.task_metadata[
                "task_profile_created"
            ] = True

            self.load_report = (
                self.build_report()
            )

            return True

        except Exception as error:

            print("\n===================================")
            print("NEXRYN LOADER ERROR")
            print("===================================\n")

            print("TASK PATH:")
            print(self.json_path)

            print()

            print("ERROR:")
            print(error)

            print()

            self.load_report = {

                "status":
                "failed",

                "error":
                str(error),

                "timestamp":
                str(datetime.utcnow())
            }

            return False

    # ========================================
    # LOAD JSON
    # ========================================

    def load_json(self):

        print("\n===================================")
        print("NEXRYN TASK INGESTION")
        print("===================================\n")

        print("TASK PATH:")
        print(self.json_path)

        print()

        print(
            "FILE EXISTS:",
            os.path.exists(
                self.json_path
            )
        )

        print()

        with open(

            self.json_path,

            "r",

            encoding="utf-8"
        ) as file:

            data = json.load(file)

        print("TASK LOADED SUCCESSFULLY\n")

        return data

    # ========================================
    # VALIDATE TASK
    # ========================================

    def validate_task(self):

        # ====================================
        # REQUIRED KEYS
        # ====================================

        required_keys = [

            "train",

            "test"
        ]

        for key in required_keys:

            if key not in self.task_data:

                return False

        # ====================================
        # VALIDATE TYPES
        # ====================================

        if not isinstance(

            self.task_data["train"],

            list
        ):

            return False

        if not isinstance(

            self.task_data["test"],

            list
        ):

            return False

        # ====================================
        # EMPTY TRAINING SET
        # ====================================

        if len(self.task_data["train"]) == 0:

            return False

        # ====================================
        # VALIDATE TRAIN EXAMPLES
        # ====================================

        for example in self.task_data["train"]:

            if not isinstance(
                example,
                dict
            ):

                return False

            if "input" not in example:

                return False

            if "output" not in example:

                return False

            if not example["input"]:

                return False

            if not example["output"]:

                return False

        # ====================================
        # VALIDATE TEST EXAMPLES
        # ====================================

        for example in self.task_data["test"]:

            if not isinstance(
                example,
                dict
            ):

                return False

            if "input" not in example:

                return False

            if not example["input"]:

                return False

        return True

    # ========================================
    # TRAIN EXAMPLES
    # ========================================

    def get_train_examples(self):

        examples = []

        for example in (
            self.task_data.get(
                "train",
                []
            )
        ):

            examples.append({

                "input":
                ARCGrid(
                    example["input"]
                ),

                "output":
                ARCGrid(
                    example["output"]
                )
            })

        return examples

    # ========================================
    # SINGLE TRAIN EXAMPLE
    # ========================================

    def get_train_example(

        self,

        index=0
    ):

        examples = (
            self.get_train_examples()
        )

        if index >= len(examples):

            return None

        return examples[index]

    # ========================================
    # TEST EXAMPLES
    # ========================================

    def get_test_examples(self):

        examples = []

        for example in (
            self.task_data.get(
                "test",
                []
            )
        ):

            examples.append({

                "input":
                ARCGrid(
                    example["input"]
                )
            })

        return examples

    # ========================================
    # SINGLE TEST EXAMPLE
    # ========================================

    def get_test_example(

        self,

        index=0
    ):

        examples = (
            self.get_test_examples()
        )

        if index >= len(examples):

            return None

        return examples[index]

    # ========================================
    # TASK COMPLEXITY
    # ========================================

    def task_complexity(self):

        train_examples = (
            self.get_train_examples()
        )

        total_cells = 0

        for example in train_examples:

            input_grid = (
                example["input"]
            )

            rows, cols = (
                input_grid.shape()
            )

            total_cells += (
              rows * cols
            )

        return {

            "example_count":
            len(train_examples),

            "total_cells":
            total_cells,

            "average_grid_size":

            round(

                total_cells
                / max(
                    len(train_examples),
                    1
                ),

                2
            )
        }

    # ========================================
    # TASK PROFILE
    # ========================================

    def task_profile(self):

        complexity = (
            self.task_complexity()
        )

        return {

            "task_path":
            self.json_path,

            "train_examples":

            len(
                self.task_data.get(
                    "train",
                    []
                )
            ),

            "test_examples":

            len(
                self.task_data.get(
                    "test",
                    []
                )
            ),

            "complexity":
            complexity,

            "metadata":
            self.task_metadata
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "status":
            "loaded",

            "task_profile":
            self.task_profile(),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return self.task_profile()

    # ========================================
    # PRINT SUMMARY
    # ========================================

    def print_summary(self):

        report = (
            self.summary()
        )

        print(
            "\n========== "
            "NEXRYN TASK SUMMARY "
            "==========\n"
        )

        for key, value in (
            report.items()
        ):

            print(f"{key}: {value}")

        print()

    # ========================================
    # EXPORT REPORT
    # ========================================

    def export_report(self):

        return self.build_report()