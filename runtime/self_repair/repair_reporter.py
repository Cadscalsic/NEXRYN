"""Build self-repair reports."""

from __future__ import annotations

from typing import Any


class RepairReporter:
    def build_report(
        self,
        anomalies,
        plans,
        execution_results,
        rollback_report,
        runtime_context,
    ) -> dict[str, Any]:
        executed = [
            result
            for result in execution_results
            if result.success
        ]
        skipped = [
            result
            for result in execution_results
            if not result.success
        ]
        rollback_used = any(
            result.rollback_used
            for result in execution_results
        )
        report = {
            "anomalies_detected": [
                anomaly.as_dict()
                for anomaly in anomalies
            ],
            "repair_plans_created": [
                plan.as_dict()
                for plan in plans
            ],
            "repairs_executed": [
                result.as_dict()
                for result in executed
            ],
            "repairs_skipped": [
                result.as_dict()
                for result in skipped
            ],
            "rollback_used": rollback_used,
            "runtime_state_after_repair": {
                "episode_completed": runtime_context.get("episode_completed"),
                "shutdown_mode": runtime_context.get("shutdown_mode"),
                "post_success_shutdown": runtime_context.get(
                    "post_success_shutdown"
                ),
                "recommended_next_step": runtime_context.get(
                    "recommended_next_step"
                ),
                "governance_review_requested": runtime_context.get(
                    "governance_review_requested",
                    False,
                ),
            },
            "rollback_report": rollback_report,
        }
        report["SELF_REPAIR_REPORT"] = {
            "anomaly_count": len(anomalies),
            "repair_plan_count": len(plans),
            "executed_count": len(executed),
            "skipped_count": len(skipped),
            "rollback_used": rollback_used,
        }
        return report


repair_reporter = RepairReporter()


__all__ = [
    "RepairReporter",
    "repair_reporter",
]
