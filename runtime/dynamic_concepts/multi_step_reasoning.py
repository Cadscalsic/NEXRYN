"""Multi-step dynamic reasoning for ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping


class MultiStepReasoning:
    """Represent A -> B -> C -> D style transformations explicitly."""

    family = "multi_step_reasoning"

    def reason(
        self,
        input_grid=None,
        output_grid=None,
        causal_context_report: Mapping[str, Any] | None = None,
        process_context_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        process_context_report = process_context_report if isinstance(process_context_report, Mapping) else {}
        concepts = set(str(item) for item in runtime_context.get("detected_concepts", []) or [])
        process_contexts = process_context_report.get("process_contexts", []) or []
        if "multi_step_reasoning" not in concepts and not process_contexts:
            return []
        steps = []
        for model in process_contexts[:3]:
            steps.extend(model.get("transition_sequence", []) or [])
        if not steps:
            steps = ["initial_state", "intermediate_state", "terminal_state"]
        return [{
            "concept_family": self.family,
            "dynamic_concept": "multi_step_reasoning",
            "activation_reason": "process_context_or_multi_step_concept_requires_intermediate_states",
            "intermediate_states": [
                {"state_index": index + 1, "transition": step}
                for index, step in enumerate(steps[:-1])
            ],
            "state_transitions": steps,
            "dependency_sequence": [
                "previous_state_enables_next_state",
                "terminal_state_requires_all_steps",
            ],
            "simulation_plan": {
                "type": "multi_step",
                "steps": steps,
            },
            "confidence": min(0.72 + 0.03 * len(steps), 0.95),
        }]


multi_step_reasoning = MultiStepReasoning()


__all__ = ["MultiStepReasoning", "multi_step_reasoning"]
