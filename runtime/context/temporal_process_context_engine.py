"""Temporal process contexts for State -> Transition -> State reasoning."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.context.process_context_engine import ProcessContextEngine


PROCESS_CONCEPTS = {
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
}


class TemporalProcessContextEngine:
    """Model process concepts as ordered temporal state transitions."""

    system_name = "temporal_process_context_engine"

    def __init__(self):
        self.process_context_engine = ProcessContextEngine()

    def evaluate(
        self,
        concept: str,
        dependency_chain: Mapping[str, Any] | Iterable[Any] | None = None,
        transformational_identity: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        if concept not in PROCESS_CONCEPTS:
            return {
                "system": self.system_name,
                "concept": concept,
                "initial_state": [],
                "transitions": [],
                "final_state": [],
                "temporal_consistency": 0.0,
                "process_context_strength": 0.0,
                "process_context_generated": False,
                "process_context_ready": False,
                "status": "PROCESS_CONTEXT_REJECTED",
                "reason": "unsupported_process_concept",
            }

        structural_context = self.process_context_engine.evaluate(
            concept,
            dependency_chain=dependency_chain,
            transformational_identity=transformational_identity,
            runtime_context=runtime_context,
        )
        initial_state = self._initial_state(structural_context)
        transitions = self._temporal_transitions(structural_context)
        final_state = self._final_state(structural_context)
        temporal_consistency = self._temporal_consistency(
            concept,
            initial_state,
            transitions,
            final_state,
            structural_context,
        )
        process_context_strength = clamp(
            structural_context.get("process_context_strength", 0.0) * 0.62
            + temporal_consistency * 0.38
        )
        ready = (
            process_context_strength > 0.90
            and temporal_consistency > 0.90
            and bool(initial_state)
            and bool(transitions)
            and bool(final_state)
        )
        status = (
            "PROCESS_CONTEXT_VALIDATED"
            if ready
            else "PROCESS_CONTEXT_SUPPORTED"
            if process_context_strength >= 0.78
            else "PROCESS_CONTEXT_CANDIDATE"
        )

        return {
            **structural_context,
            "system": self.system_name,
            "concept": concept,
            "initial_state": initial_state,
            "transitions": transitions,
            "final_state": final_state,
            "temporal_consistency": round(temporal_consistency, 4),
            "process_context_strength": round(process_context_strength, 4),
            "process_context_generated": True,
            "process_context_ready": ready,
            "status": status,
            "confidence": round(
                max(
                    structural_context.get("confidence", 0.0),
                    process_context_strength,
                ),
                4,
            ),
            "state_transition_state_model": True,
            "processes_are_temporal_structures": True,
            "static_context_representation_insufficient": True,
            "temporal_context_governance_bypass_forbidden": True,
            "supporting_math_evidence": {
                **structural_context.get("supporting_math_evidence", {}),
                "temporal_state_sequence_generated": True,
                "initial_state_identified": bool(initial_state),
                "temporal_transitions_identified": bool(transitions),
                "final_state_identified": bool(final_state),
                "temporal_consistency": temporal_consistency,
                "process_signature_strength": process_context_strength,
                "dependency_semantics_score": max(
                    structural_context.get(
                        "supporting_math_evidence",
                        {},
                    ).get("dependency_semantics_score", 0.0),
                    process_context_strength,
                ),
            },
        }

    def dependency_semantics_report(self, temporal_context_report):
        report = (
            temporal_context_report
            if isinstance(temporal_context_report, Mapping)
            else {}
        )
        concept = _normalize(report.get("concept"))
        transitions = [
            item
            for item in report.get("transitions", [])
            if isinstance(item, Mapping)
        ]
        typed_dependencies = [
            {
                "source": item.get("from"),
                "target": item.get("to"),
                "relation": item.get("transition", "transitions_to"),
                "confidence": item.get("confidence", 0.0),
                "contexts": [report.get("process_context", f"{concept}_context")],
                "temporal_step": item.get("step"),
            }
            for item in transitions
        ]
        return {
            "system": self.system_name,
            "dependency_semantics_score": clamp(
                report.get("process_context_strength", 0.0)
            ),
            "typed_dependencies": typed_dependencies,
            "semantic_dependency_signature": {
                "relation_types": sorted(
                    {
                        str(item.get("relation"))
                        for item in typed_dependencies
                        if item.get("relation")
                    }
                ),
                "process_context": report.get(
                    "process_context",
                    f"{concept}_context",
                ),
                "has_causal_chain": bool(typed_dependencies),
                "temporal_transition_context": True,
                "state_transition_state_model": True,
            },
        }

    def _initial_state(self, structural_context):
        state = []
        for item in structural_context.get("preconditions", []):
            if not isinstance(item, Mapping):
                continue
            state.append({
                "state": item.get("target"),
                "source": item.get("source"),
                "relation": item.get("relation"),
                "confidence": item.get("confidence", 0.0),
            })
        return state

    def _temporal_transitions(self, structural_context):
        transitions = []
        steps = [
            item
            for item in structural_context.get("transition_steps", [])
            if isinstance(item, Mapping)
        ]
        for index, item in enumerate(steps, start=1):
            transitions.append({
                "step": index,
                "from": item.get("source"),
                "transition": item.get("relation", "transitions_to"),
                "to": item.get("target"),
                "confidence": item.get("confidence", 0.0),
            })
        return transitions

    def _final_state(self, structural_context):
        state = []
        for item in structural_context.get("postconditions", []):
            if not isinstance(item, Mapping):
                continue
            state.append({
                "state": item.get("target"),
                "source": item.get("source"),
                "relation": item.get("relation"),
                "confidence": item.get("confidence", 0.0),
            })
        return state

    def _temporal_consistency(
        self,
        concept,
        initial_state,
        transitions,
        final_state,
        structural_context,
    ):
        state_coverage = clamp(
            bool(initial_state) * 0.30
            + bool(transitions) * 0.40
            + bool(final_state) * 0.30
        )
        ordered_steps = [
            int(item.get("step", 0) or 0)
            for item in transitions
        ]
        ordering = (
            1.0
            if ordered_steps
            and ordered_steps == list(range(1, len(ordered_steps) + 1))
            else 0.0
        )
        concept_anchor = clamp(
            sum(
                item.get("from") == concept or item.get("to") == concept
                for item in transitions[:3]
            ) / 2
        )
        transition_confidence = (
            sum(clamp(item.get("confidence", 0.0)) for item in transitions)
            / len(transitions)
            if transitions
            else 0.0
        )
        return clamp(
            state_coverage * 0.35
            + ordering * 0.24
            + concept_anchor * 0.16
            + transition_confidence * 0.15
            + clamp(structural_context.get("temporal_ordering", 0.0)) * 0.10
        )


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


temporal_process_context_engine = TemporalProcessContextEngine()


__all__ = [
    "TemporalProcessContextEngine",
    "temporal_process_context_engine",
]
