# ============================================
# NEXRYN SEMANTIC SCHEDULER
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class SemanticScheduler:

    def __init__(self):

        self.schedule_history = []

    def schedule(self, context, process_report):

        thermodynamics = context.get(
            "cognitive_thermodynamics_report",
            {},
        )

        heat = thermodynamics.get(
            "semantic_heat_dissipation",
            {},
        ).get(
            "semantic_heat_after",
            context.get(
                "runtime_entropy",
                0.0,
            ),
        )

        ready = [
            process
            for process in process_report.get(
                "processes",
                [],
            )
            if process.get(
                "process_state",
            )
            == "ready"
        ]

        max_slots = (
            3
            if heat >= 0.70
            else 6
            if heat >= 0.45
            else 10
        )

        scheduled = ready[:max_slots]
        deferred = ready[max_slots:]

        report = {
            "system":
            "semantic_scheduler",

            "semantic_heat":
            _clamp(
                heat,
            ),

            "max_execution_slots":
            max_slots,

            "scheduled_processes":
            scheduled,

            "deferred_processes":
            deferred,

            "scheduled_count":
            len(
                scheduled,
            ),

            "deferred_count":
            len(
                deferred,
            ),

            "scheduler_policy":
            (
                "thermal_limited_semantic_execution"
                if heat >= 0.70
                else "balanced_semantic_execution"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.schedule_history.append(
            report,
        )

        self.schedule_history = (
            self.schedule_history[-64:]
        )

        return report
