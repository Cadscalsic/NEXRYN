from __future__ import annotations

from copy import deepcopy
from typing import Any


class ExecutionMemory:
    """In-memory store for execution, repair, residual, and grounding patterns."""

    def __init__(self) -> None:
        self.successful_programs: list[dict[str, Any]] = []
        self.failed_programs: list[dict[str, Any]] = []
        self.repair_strategies: list[dict[str, Any]] = []
        self.residual_patterns: list[dict[str, Any]] = []
        self.execution_signatures: list[dict[str, Any]] = []
        self.object_grounding_patterns: list[dict[str, Any]] = []

    def record_execution(
        self,
        *,
        program: dict[str, Any] | None = None,
        validation: dict[str, Any] | None = None,
        residual: dict[str, Any] | None = None,
        repair: dict[str, Any] | None = None,
        grounding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        program_data = deepcopy(program) if isinstance(program, dict) else {}
        validation_data = validation if isinstance(validation, dict) else {}
        residual_data = residual if isinstance(residual, dict) else {}
        repair_data = repair if isinstance(repair, dict) else {}
        grounding_data = grounding if isinstance(grounding, dict) else {}
        bucket = self.successful_programs if validation_data.get("validation_success") else self.failed_programs
        bucket.append(program_data)
        if repair_data.get("repair_proposals"):
            self.repair_strategies.append(deepcopy(repair_data))
        if residual_data:
            self.residual_patterns.append(deepcopy(residual_data))
        if program_data:
            self.execution_signatures.append({
                "program_id": program_data.get("program_id"),
                "step_count": program_data.get("step_count"),
                "execution_scope": program_data.get("execution_scope"),
            })
        if grounding_data:
            self.object_grounding_patterns.append(deepcopy(grounding_data))
        return self.report()

    def retrieve_programs(self, signature: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not isinstance(signature, dict) or not signature:
            return deepcopy(self.successful_programs)
        return [
            deepcopy(program)
            for program in self.successful_programs
            if all(program.get(key) == value for key, value in signature.items())
        ]

    def retrieve_repairs(self, primitive: str | None = None) -> list[dict[str, Any]]:
        repairs = self.repair_strategies
        if primitive:
            repairs = [
                repair for repair in repairs
                if primitive in repair.get("primitive_repairs", [])
            ]
        return deepcopy(repairs)

    def retrieve_localizations(self) -> list[dict[str, Any]]:
        return deepcopy(self.object_grounding_patterns)

    def report(self) -> dict[str, Any]:
        return {
            "successful_programs": len(self.successful_programs),
            "failed_programs": len(self.failed_programs),
            "repair_strategies": len(self.repair_strategies),
            "residual_patterns": len(self.residual_patterns),
            "execution_signatures": len(self.execution_signatures),
            "object_grounding_patterns": len(self.object_grounding_patterns),
            "execution_memory_operational": True,
        }


execution_memory = ExecutionMemory()


__all__ = ["ExecutionMemory", "execution_memory"]
