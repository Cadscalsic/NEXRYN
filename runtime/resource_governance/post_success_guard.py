"""Post-terminal success guard."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.resource_governance.execution_policy import ExecutionPolicyName
from runtime.resource_governance.maintenance_classifier import MaintenanceWorkCategory


class PostSuccessRejectionReason:
    POST_SUCCESS_BUDGET_EXCEEDED = "POST_SUCCESS_BUDGET_EXCEEDED"
    WORK_CLASSIFIED_AS_DEFERRED = "WORK_CLASSIFIED_AS_DEFERRED"
    CHANGE_TRIGGER_NOT_SATISFIED = "CHANGE_TRIGGER_NOT_SATISFIED"
    DIAGNOSTIC_POLICY_REQUIRED = "DIAGNOSTIC_POLICY_REQUIRED"
    TERMINAL_STATE_RESTRICTION = "TERMINAL_STATE_RESTRICTION"
    DUPLICATE_MAINTENANCE_WORK = "DUPLICATE_MAINTENANCE_WORK"
    UNCHANGED_STATE = "UNCHANGED_STATE"


@dataclass
class PostSuccessGuard:
    rejections: list[dict[str, str]] = field(default_factory=list)

    def allow(
        self,
        work_type: str,
        category: MaintenanceWorkCategory,
        policy: ExecutionPolicyName,
        elapsed: float,
        budget: float,
        trigger_satisfied: bool = True,
        duplicate: bool = False,
        unchanged: bool = False,
    ) -> tuple[bool, str | None]:
        reason = None
        if elapsed > budget:
            reason = PostSuccessRejectionReason.POST_SUCCESS_BUDGET_EXCEEDED
        elif duplicate:
            reason = PostSuccessRejectionReason.DUPLICATE_MAINTENANCE_WORK
        elif unchanged:
            reason = PostSuccessRejectionReason.UNCHANGED_STATE
        elif category == MaintenanceWorkCategory.PROHIBITED_AFTER_TERMINAL:
            reason = PostSuccessRejectionReason.TERMINAL_STATE_RESTRICTION
        elif category == MaintenanceWorkCategory.DEFERRED:
            reason = PostSuccessRejectionReason.WORK_CLASSIFIED_AS_DEFERRED
        elif category == MaintenanceWorkCategory.CHANGE_TRIGGERED and not trigger_satisfied:
            reason = PostSuccessRejectionReason.CHANGE_TRIGGER_NOT_SATISFIED
        elif category == MaintenanceWorkCategory.DIAGNOSTIC_ONLY and policy != ExecutionPolicyName.DIAGNOSTIC:
            reason = PostSuccessRejectionReason.DIAGNOSTIC_POLICY_REQUIRED
        if reason:
            self.rejections.append({"work_type": work_type, "reason": reason})
            return False, reason
        return True, None


__all__ = ["PostSuccessGuard", "PostSuccessRejectionReason"]
