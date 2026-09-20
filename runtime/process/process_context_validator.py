"""Validation for process contexts under governance constraints."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp


class ProcessContextValidator:
    """Validate process contexts without weakening identity or contradiction rules."""

    system_name = "process_context_validator"

    def validate(
        self,
        context: Mapping[str, Any],
        identity_continuity: float,
        causal_alignment: float,
        contradiction_score: float = 0.0,
    ) -> dict[str, Any]:
        blockers = []
        if identity_continuity < 0.85:
            blockers.append("identity_continuity_below_process_floor")
        if causal_alignment < 0.85:
            blockers.append("causal_alignment_below_process_floor")
        if contradiction_score > 0.10:
            blockers.append("contradiction_threshold_exceeded")
        if not (
            context.get("transition_signature")
            or context.get("transitions")
        ):
            blockers.append("process_transition_missing")

        return {
            "system": self.system_name,
            "process_context_valid": not blockers,
            "process_context_ready": not blockers,
            "semantic_validation": not blockers,
            "identity_compatible": identity_continuity >= 0.85,
            "governance_visible": not blockers,
            "identity_continuity": clamp(identity_continuity),
            "causal_alignment": clamp(causal_alignment),
            "contradiction_score": clamp(contradiction_score),
            "validation_blockers": blockers,
        }

    def validate_generated(
        self,
        process_context: Mapping[str, Any],
        simulation_report: Mapping[str, Any] | None = None,
        dependency_graph: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        simulation_report = (
            simulation_report
            if isinstance(simulation_report, Mapping)
            else {}
        )
        dependency_graph = (
            dependency_graph
            if isinstance(dependency_graph, Mapping)
            else {}
        )
        states = [
            process_context.get("initial_state"),
            *list(process_context.get("intermediate_states", []) or []),
            process_context.get("final_state"),
        ]
        states = [state for state in states if isinstance(state, Mapping) and state]
        transitions = list(process_context.get("transition_sequence", []) or [])
        dependencies = list(process_context.get("dependencies", []) or [])
        blockers = []
        if len(states) < 2:
            blockers.append("state_continuity_missing")
        if not transitions:
            blockers.append("transition_sequence_missing")
        if len(transitions) > max(len(states) - 1, 0) + 1:
            blockers.append("transition_ordering_exceeds_state_path")
        if dependency_graph and not dependency_graph.get("edges"):
            blockers.append("dependency_graph_edges_missing")
        if not dependencies:
            blockers.append("dependency_consistency_missing")

        transition_validity = 1.0 if transitions and len(states) >= 2 else 0.0
        state_continuity = min(1.0, len(transitions) / max(len(states) - 1, 1)) if states else 0.0
        dependency_consistency = 1.0 if dependencies else 0.0
        topology_consistency = 1.0 if dependency_graph.get("edge_count", 0) or dependency_graph.get("edges") else 0.5
        identity_consistency = 0.9 if process_context.get("initial_state") and process_context.get("final_state") else 0.5
        transformation_consistency = float(
            simulation_report.get(
                "transition_consistency",
                simulation_report.get("graph_flow_fit", 0.0),
            )
            or 0.0
        )
        support_score = float(process_context.get("support_score", 0.0) or 0.0)
        contradiction_score = float(process_context.get("contradiction_score", 0.0) or 0.0)
        score = round(
            max(
                0.0,
                transition_validity * 0.18
                + state_continuity * 0.17
                + dependency_consistency * 0.18
                + topology_consistency * 0.14
                + identity_consistency * 0.13
                + transformation_consistency * 0.10
                + support_score * 0.10
                - contradiction_score * 0.25,
            ),
            4,
        )
        return {
            "system": self.system_name,
            "state_continuity": round(state_continuity, 4),
            "transition_validity": round(transition_validity, 4),
            "dependency_consistency": round(dependency_consistency, 4),
            "topology_consistency": round(topology_consistency, 4),
            "identity_consistency": round(identity_consistency, 4),
            "transformation_consistency": round(transformation_consistency, 4),
            "process_validation_score": score,
            "process_validated": score >= 0.70 and not blockers,
            "validation_blockers": blockers,
        }


__all__ = ["ProcessContextValidator"]
