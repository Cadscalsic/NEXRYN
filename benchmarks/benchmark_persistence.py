# ============================================
# NEXRYN BENCHMARK PERSISTENCE SYSTEM
# ============================================

import os
import json

from datetime import datetime


# ============================================
# BENCHMARK PERSISTENCE
# ============================================

class BenchmarkPersistence:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        storage_directory=
        "data/generated"
    ):

        self.storage_directory = (
            storage_directory
        )

        self.persistence_state = {

            "storage_active":
            True,

            "json_export":
            True,

            "report_tracking":
            True,

            "history_tracking":
            True
        }

        # ====================================
        # CREATE DIRECTORY
        # ====================================

        os.makedirs(

            self.storage_directory,

            exist_ok=True
        )

    # ========================================
    # SAVE REPORT
    # ========================================

    def save_report(

        self,

        benchmark_report,

        filename=
        "benchmark_report.json"
    ):

        output_path = os.path.join(

            self.storage_directory,

            filename
        )

        with open(

            output_path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                benchmark_report,

                file,

                indent=4
            )

        return {

            "saved":
            True,

            "path":
            output_path,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # LOAD REPORT
    # ========================================

    def load_report(

        self,

        filename=
        "benchmark_report.json"
    ):

        report_path = os.path.join(

            self.storage_directory,

            filename
        )

        if not os.path.exists(
            report_path
        ):

            return {

                "loaded":
                False,

                "reason":
                "missing_report"
            }

        with open(

            report_path,

            "r",

            encoding="utf-8"
        ) as file:

            report = json.load(file)

        return {

            "loaded":
            True,

            "report":
            report
        }

    # ========================================
    # SAVE HISTORY SNAPSHOT
    # ========================================

    def save_history_snapshot(

        self,

        execution_history
    ):

        snapshot_name = (

            "history_snapshot_"

            +

            datetime.utcnow().strftime(
                "%Y%m%d_%H%M%S"
            )

            +

            ".json"
        )

        snapshot_path = os.path.join(

            self.storage_directory,

            snapshot_name
        )

        with open(

            snapshot_path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                execution_history,

                file,

                indent=4
            )

        return {

            "snapshot_saved":
            True,

            "snapshot":
            snapshot_path
        }

    # ========================================
    # LIST REPORTS
    # ========================================

    def list_reports(self):

        reports = []

        for file_name in os.listdir(

            self.storage_directory
        ):

            if file_name.endswith(
                ".json"
            ):

                reports.append(
                    file_name
                )

        return reports

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "persistence_state":
            self.persistence_state,

            "storage_directory":
            self.storage_directory,

            "available_reports":
            self.list_reports(),

            "timestamp":
            str(datetime.utcnow())
        }