"""Rule-based State -> Transition -> State extraction for process concepts."""

from __future__ import annotations

from typing import Any, Mapping


PROCESS_RULES = {
    "growth": {
        "context_name": "growth_context",
        "process_family": "growth",
        "preconditions": [
            "object_exists",
            "identity_preserved",
            "object_count_constant",
        ],
        "transition_signature": ["area_increased"],
        "postconditions": [
            "topology_consistent",
            "local_shape_preserved",
        ],
        "invariants": ["identity_continuity", "object_persistence"],
        "constraints": ["identity_split_false", "causal_alignment_high"],
    },
    "replication": {
        "context_name": "replication_context",
        "process_family": "replication",
        "preconditions": ["source_object_exists"],
        "transition_signature": ["object_count_increased"],
        "postconditions": ["structural_similarity_high"],
        "invariants": ["source_identity_preserved", "shape_similarity"],
        "constraints": [
            "source_identity_preserved",
            "topology_splitting_allowed",
        ],
    },
    "propagation": {
        "context_name": "propagation_context",
        "process_family": "propagation",
        "preconditions": ["source_pattern_exists"],
        "transition_signature": ["neighboring_state_changes"],
        "postconditions": ["directional_consistency"],
        "invariants": ["source_pattern_preserved", "directional_consistency"],
        "constraints": ["source_pattern_preserved"],
    },
    "directional_motion": {
        "context_name": "directional_motion_context",
        "process_family": "directional_motion",
        "preconditions": ["object_exists", "direction_vector_exists"],
        "transition_signature": ["position_delta_applied"],
        "postconditions": ["position_updated"],
        "invariants": ["identity_continuity", "shape_preservation"],
        "constraints": ["identity_split_false"],
    },
    "topological_growth": {
        "context_name": "topological_growth_context",
        "process_family": "topological_growth",
        "preconditions": ["object_exists", "topology_anchor_exists"],
        "transition_signature": ["connectivity_expanded"],
        "postconditions": ["expanded_connectivity"],
        "invariants": ["local_shape_preservation", "topology_consistency"],
        "constraints": ["identity_anchor_required"],
    },
}


class ProcessTransitionExtractor:
    """Extract canonical process signatures without enabling temporal reasoning."""

    system_name = "process_transition_extractor"

    def extract(
        self,
        concept: str,
        dependency_chain: list[str] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = str(concept)
        rule = PROCESS_RULES.get(concept)
        if not rule:
            return {
                "system": self.system_name,
                "concept": concept,
                "process_context_discovered": False,
                "reason": "unsupported_process_concept",
            }
        dependencies = self._dependency_links(dependency_chain)
        return {
            "system": self.system_name,
            "concept": concept,
            "process_context_discovered": True,
            "context_name": rule["context_name"],
            "process_family": rule["process_family"],
            "preconditions": list(rule["preconditions"]),
            "transition_signature": list(rule["transition_signature"]),
            "transitions": list(rule["transition_signature"]),
            "postconditions": list(rule["postconditions"]),
            "invariants": list(rule["invariants"]),
            "constraints": list(rule["constraints"]),
            "dependency_links": dependencies,
            "temporal_signature": {
                "model": "STATE_TRANSITION_STATE",
                "temporal_reasoning_enabled": False,
                "state_sequence_represented": True,
                "transition_count": len(rule["transition_signature"]),
            },
        }

    def _dependency_links(self, dependency_chain):
        if isinstance(dependency_chain, Mapping):
            dependency_chain = (
                dependency_chain.get("resolved_dependency_chain")
                or dependency_chain.get("dependency_chain")
                or dependency_chain.get("links")
                or []
            )
        if not dependency_chain:
            return []
        return [str(item) for item in dependency_chain if item]


__all__ = ["PROCESS_RULES", "ProcessTransitionExtractor"]
