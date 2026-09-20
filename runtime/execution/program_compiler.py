from __future__ import annotations

import hashlib
from typing import Any


class ProgramCompiler:
    """Compile validated primitive sequences into executable program candidates."""

    def compile(
        self,
        *,
        semantic_intent: str | None = None,
        primitive_sequence: list[str] | None = None,
        execution_plan: dict[str, Any] | None = None,
        synthesized_program: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        synthesis = synthesized_program if isinstance(synthesized_program, dict) else {}
        steps = synthesis.get("program") if isinstance(synthesis.get("program"), list) else []
        primitives = list(primitive_sequence or synthesis.get("primitive_sequence") or [])
        plan = execution_plan if isinstance(execution_plan, dict) else {}
        compiled_successfully = bool(primitives and steps)
        program_id = self._program_id(semantic_intent, primitives)
        return {
            "program_id": program_id,
            "compiled_successfully": compiled_successfully,
            "step_count": len(steps),
            "execution_requirements": self._requirements(primitives, plan),
            "compiled_program": {
                "program_id": program_id,
                "semantic_intent": semantic_intent,
                "steps": steps,
                "step_count": len(steps),
                "execution_scope": plan.get("execution_scope", "local"),
                "requires_validation": True,
                "real_execution_authorized": False,
            },
            "compiled_programs": 1 if compiled_successfully else 0,
            "compiler_participation": 1 if compiled_successfully else 0,
            "program_compilation_operational": True,
        }

    def _program_id(self, semantic_intent: str | None, primitives: list[str]) -> str:
        intent = str(semantic_intent or "intent").replace(" ", "_").lower()
        signature = "_".join(str(item) for item in primitives) or "empty"
        digest = hashlib.sha1(signature.encode("utf-8")).hexdigest()[:10]
        return f"program:{intent}:{digest}"

    def _requirements(
        self,
        primitives: list[str],
        plan: dict[str, Any],
    ) -> list[str]:
        requirements = [
            "truth_governance",
            "identity_governance",
            "context_governance",
            "dependency_governance",
            "execution_integrity_validation",
            "constitutional_validation",
        ]
        if plan.get("execution_scope") in {"local", "mixed"}:
            requirements.append("object_grounding")
        if "recolor" in primitives:
            requirements.append("color_mapping")
        return requirements


program_compiler = ProgramCompiler()


__all__ = ["ProgramCompiler", "program_compiler"]
