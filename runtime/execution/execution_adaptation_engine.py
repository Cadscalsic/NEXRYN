from __future__ import annotations

from copy import deepcopy
from typing import Any


class ExecutionAdaptationEngine:
    """Adapt validated programs using localized repair proposals."""

    def adapt(
        self,
        compiled_program: dict[str, Any] | None,
        repair_report: dict[str, Any] | None,
        *,
        repair_budget: int = 3,
    ) -> dict[str, Any]:
        program = deepcopy(compiled_program) if isinstance(compiled_program, dict) else {}
        repairs = repair_report.get("repair_proposals") if isinstance(repair_report, dict) and isinstance(repair_report.get("repair_proposals"), list) else []
        applied = []
        steps = program.get("steps") if isinstance(program.get("steps"), list) else []
        for proposal in repairs[: max(0, repair_budget)]:
            if not isinstance(proposal, dict):
                continue
            step = {
                "step_id": f"repair_step_{len(steps) + 1}",
                "primitive": proposal.get("primitive"),
                "operation": proposal.get("operation"),
                "target_region": proposal.get("target_region", {}),
                "parameters": {"repair_id": proposal.get("repair_id")},
            }
            steps.append(step)
            applied.append(proposal.get("repair_id"))
        program["steps"] = steps
        program["step_count"] = len(steps)
        program["adapted_from_repairs"] = applied
        program["real_execution_authorized"] = False
        return {
            "adapted_program": program,
            "applied_repairs": applied,
            "execution_retries": 1 if applied else 0,
            "repair_budget_used": len(applied),
            "repair_budget_remaining": max(0, repair_budget - len(applied)),
            "execution_adaptations": len(applied),
            "execution_adaptation_operational": True,
        }


execution_adaptation_engine = ExecutionAdaptationEngine()


__all__ = ["ExecutionAdaptationEngine", "execution_adaptation_engine"]
