from __future__ import annotations

from typing import Any


class ProgramValidator:
    """Validate compiled programs before they may be recommended for execution."""

    REQUIRED_GOVERNANCE = (
        "truth_governance",
        "identity_governance",
        "context_governance",
        "dependency_governance",
        "execution_integrity_validation",
        "constitutional_validation",
    )

    def validate(
        self,
        compiled: dict[str, Any] | None,
        *,
        grounding_report: dict[str, Any] | None = None,
        governance_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        compiled_report = compiled if isinstance(compiled, dict) else {}
        program = compiled_report.get("compiled_program") if isinstance(compiled_report.get("compiled_program"), dict) else {}
        grounding = grounding_report if isinstance(grounding_report, dict) else {}
        context = governance_context if isinstance(governance_context, dict) else {}
        blocked = [
            name
            for name in self.REQUIRED_GOVERNANCE
            if context.get(name) in {False, "BLOCK", "BLOCKED", "FAIL", "FAILED"}
        ]
        step_count = int(program.get("step_count") or compiled_report.get("step_count") or 0)
        object_consistent = bool(grounding.get("target_objects")) or program.get("execution_scope") == "global"
        validation_success = (
            compiled_report.get("compiled_successfully") is True
            and step_count > 0
            and object_consistent
            and not blocked
        )
        return {
            "program_id": program.get("program_id") or compiled_report.get("program_id"),
            "validation_success": validation_success,
            "semantic_consistency": bool(program.get("semantic_intent")),
            "object_consistency": object_consistent,
            "identity_preservation": not bool(context.get("identity_violation")),
            "topology_preservation": not bool(context.get("topology_violation")),
            "dependency_validity": "dependency_governance" not in blocked,
            "truth_validity": "truth_governance" not in blocked,
            "context_validity": "context_governance" not in blocked,
            "governance_validity": not blocked,
            "governance_decision": "ALLOW_GOVERNED_EXECUTION" if validation_success else "BLOCK_PROGRAM",
            "validation_blockers": blocked + ([] if object_consistent else ["missing_object_grounding"]),
            "validated_programs": 1 if validation_success else 0,
            "real_execution_authorized": False,
            "program_validation_operational": True,
            "governed_execution_operational": True,
        }


program_validator = ProgramValidator()


__all__ = ["ProgramValidator", "program_validator"]
