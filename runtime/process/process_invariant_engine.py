"""Invariant extraction for semantic process models."""

from __future__ import annotations

from typing import Any, Mapping


PROCESS_INVARIANTS = {
    "growth": ["identity_preserved", "topology_preserved"],
    "propagation": ["source_pattern_preserved", "direction_preserved"],
    "replication": ["source_shape_preserved", "local_topology_preserved"],
    "directional_motion": ["identity_preserved", "shape_preserved"],
    "topological_growth": ["identity_preserved", "local_shape_preserved"],
    "size_preservation": ["object_extent_preserved", "identity_preserved"],
    "symbolic_remapping": ["symbol_identity_preserved", "mapping_consistent"],
    "density_preservation": ["density_ratio_preserved", "coverage_preserved"],
}


class ProcessInvariantEngine:
    system_name = "process_invariant_engine"

    def extract(self, concept: str, context: Mapping[str, Any] | None = None) -> dict:
        context = context if isinstance(context, Mapping) else {}
        invariants = list(
            context.get("invariants")
            or PROCESS_INVARIANTS.get(str(concept), [])
        )
        return {
            "system": self.system_name,
            "concept": str(concept),
            "invariants": invariants,
            "invariant_count": len(invariants),
            "process_invariants_available": bool(invariants),
        }


__all__ = ["PROCESS_INVARIANTS", "ProcessInvariantEngine"]
