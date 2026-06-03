# ============================================
# NEXRYN BENCHMARK DASHBOARD
# ============================================

from datetime import datetime


# ============================================
# BENCHMARK DASHBOARD
# ============================================

class BenchmarkDashboard:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        benchmark_report
    ):

        self.benchmark_report = (
            benchmark_report
        )

        self.dashboard_state = {

            "dashboard_active":
            True,

            "visualization_enabled":
            True,

            "failure_monitoring":
            True,

            "metrics_tracking":
            True
        }

    # ========================================
    # DISPLAY DASHBOARD
    # ========================================

    def display(self):

        summary = (

            self.benchmark_report.get(
                "benchmark_summary",
                {}
            )
        )

        metrics = summary.get(
            "metrics",
            {}
        )

        results = summary.get(
            "results",
            []
        )

        failures = summary.get(
            "failures",
            []
        )

        print("\n===================================")
        print("NEXRYN BENCHMARK DASHBOARD")
        print("===================================\n")

        # ====================================
        # GLOBAL METRICS
        # ====================================

        print("GLOBAL METRICS:\n")

        for key, value in (
            metrics.items()
        ):

            print(f"{key}: {value}")

        print()

        # ====================================
        # TASK RESULTS
        # ====================================

        print("TASK RESULTS:\n")

        if not results:

            print("NO RESULTS AVAILABLE\n")

        else:

            for result in results:

                print("-----------------------------------")

                print(
                    "TASK:",
                    result.get(
                        "task",
                        "unknown"
                    )
                )

                print(
                    "SUCCESS:",
                    result.get(
                        "success",
                        False
                    )
                )

                print(
                    "ACCURACY:",
                    result.get(
                        "accuracy",
                        0.0
                    )
                )

                print(
                    "TASK TYPE:",
                    result.get(
                        "task_type",
                        "unknown"
                    )
                )

                print(
                    "REASONING FAMILY:",
                    result.get(
                        "reasoning_family",
                        "unknown"
                    )
                )

                print(
                    "DIFFICULTY:",
                    result.get(
                        "difficulty",
                        "unknown"
                    )
                )

                print(
                    "REASONING DEPTH:",
                    result.get(
                        "reasoning_depth",
                        0
                    )
                )

                print(
                    "RECURSIVE DEPTH:",
                    result.get(
                        "recursive_depth",
                        0
                    )
                )

                print(
                    "PLANNING NODES:",
                    result.get(
                        "planning_nodes",
                        0
                    )
                )

                print(
                    "EXECUTION TIME:",
                    result.get(
                        "execution_time",
                        0.0
                    )
                )

                print()

        # ====================================
        # FAILURE REPORT
        # ====================================

        print("FAILURE REPORT:\n")

        if not failures:

            print("NO FAILURES DETECTED\n")

        else:

            for failure in failures:

                print("-----------------------------------")

                print(
                    "TASK:",
                    failure.get(
                        "task",
                        "unknown"
                    )
                )

                print(
                    "ERROR:",
                    failure.get(
                        "error",
                        "unknown"
                    )
                )

                print(
                    "STAGE:",
                    failure.get(
                        "stage",
                        "unknown"
                    )
                )

                print(
                    "TIMESTAMP:",
                    failure.get(
                        "timestamp",
                        "unknown"
                    )
                )

                print()

        # ====================================
        # FINALIZATION
        # ====================================

        print("DASHBOARD GENERATED:")
        print(str(datetime.utcnow()))

        print()

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "dashboard_state":
            self.dashboard_state,

            "timestamp":
            str(datetime.utcnow())
        }