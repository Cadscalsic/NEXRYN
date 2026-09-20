"""Program reuse and execution safety guard."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.permission_manager import permission_manager
from runtime.security.security_reporter import security_reporter


class ProgramSafetyGuard:
    def evaluate(
        self,
        program: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ):
        program = program if isinstance(program, Mapping) else {}
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        task_signature = context.get("task_signature") or context.get("task_signature_id")
        program_signature = program.get("task_signature") or program.get("task_signature_id")
        if task_signature and program_signature and task_signature != program_signature:
            decision = permission_manager.deny(
                "reuse_program",
                "program_signature_task_signature_mismatch",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "program", dict(program))

        if program.get("program_version_hash_unchanged") is False:
            decision = permission_manager.deny(
                "reuse_program",
                "program_version_hash_changed",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "program", dict(program))

        if program.get("execution_integrity_preserved") is False:
            decision = permission_manager.deny(
                "execute_program",
                "EXECUTION_INTEGRITY_VIOLATION",
                "CRITICAL",
            )
            return security_reporter.record_decision(decision, "program", dict(program))

        allowed_ops = set(context.get("allowed_ops") or program.get("allowed_ops") or [])
        planned_ops = list(program.get("planned_ops") or [])
        if allowed_ops and any(op not in allowed_ops for op in planned_ops):
            decision = permission_manager.deny(
                "execute_program",
                "program_contains_disallowed_ops",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "program", dict(program))

        expected_shape = context.get("expected_output_shape")
        program_shape = program.get("expected_output_shape")
        if expected_shape and program_shape and expected_shape != program_shape:
            decision = permission_manager.deny(
                "execute_program",
                "expected_output_shape_mismatch",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "program", dict(program))

        if program.get("integrity_verified") is False:
            decision = permission_manager.deny(
                "reuse_program",
                "program_integrity_unverified",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "program", dict(program))

        return security_reporter.record_decision(
            permission_manager.allow("reuse_program", "program_reuse_safe", "HIGH"),
            "program",
            dict(program),
        )


program_safety_guard = ProgramSafetyGuard()


__all__ = [
    "ProgramSafetyGuard",
    "program_safety_guard",
]
