from __future__ import annotations

from typing import Any


class ProgramSynthesisEngine:
    """Synthesize object-centric primitive sequences from validated intent."""

    def synthesize(
        self,
        *,
        semantic_intent: str | None = None,
        hypotheses: list[dict[str, Any]] | None = None,
        validated_candidate: dict[str, Any] | None = None,
        counterfactual_revision: dict[str, Any] | None = None,
        execution_plan: dict[str, Any] | None = None,
        primitive_selection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidate = validated_candidate if isinstance(validated_candidate, dict) else {}
        plan = execution_plan if isinstance(execution_plan, dict) else {}
        selection = primitive_selection if isinstance(primitive_selection, dict) else {}
        primitives = selection.get("selected_primitives")
        primitives = primitives if isinstance(primitives, list) else []
        localized = plan.get("localized_operations")
        localized = localized if isinstance(localized, list) else []
        revision = counterfactual_revision if isinstance(counterfactual_revision, dict) else {}
        steps = []
        for index, primitive in enumerate(primitives, start=1):
            local_op = localized[min(index - 1, len(localized) - 1)] if localized else {}
            steps.append({
                "step_id": f"step_{index}",
                "primitive": primitive,
                "operation": candidate.get("operation") or plan.get("operation") or semantic_intent,
                "target_object": local_op.get("target_object") if isinstance(local_op, dict) else None,
                "target_region": local_op.get("target_region") if isinstance(local_op, dict) else {},
                "execution_scope": plan.get("execution_scope", "local"),
                "parameters": self._parameters_for(primitive, candidate, revision),
            })
        return {
            "program": steps,
            "primitive_sequence": [step["primitive"] for step in steps],
            "step_count": len(steps),
            "localized_program": bool(localized),
            "object_centric_program": any(step.get("target_object") for step in steps),
            "hierarchical_program": len(steps) > 1,
            "source_hypotheses": [
                item.get("hypothesis_id")
                for item in (hypotheses or [])
                if isinstance(item, dict) and item.get("hypothesis_id")
            ],
            "synthesized_programs": 1 if steps else 0,
            "program_synthesis_operational": True,
        }

    def _parameters_for(
        self,
        primitive: str,
        candidate: dict[str, Any],
        revision: dict[str, Any],
    ) -> dict[str, Any]:
        program = candidate.get("program") if isinstance(candidate.get("program"), dict) else {}
        steps = program.get("steps") if isinstance(program.get("steps"), list) else []
        for step in steps:
            if not isinstance(step, dict):
                continue
            params = step.get("parameters") if isinstance(step.get("parameters"), dict) else {}
            if primitive in {step.get("primitive"), step.get("operation")} or params:
                return dict(params)
        if isinstance(revision.get("revision_parameters"), dict):
            return dict(revision["revision_parameters"])
        return {}


program_synthesis_engine = ProgramSynthesisEngine()


__all__ = ["ProgramSynthesisEngine", "program_synthesis_engine"]
