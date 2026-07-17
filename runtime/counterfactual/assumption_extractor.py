"""Extract challengeable assumptions from a preliminary arena winner."""

from __future__ import annotations

from typing import Any, Mapping


class AssumptionExtractor:
    system_name = "assumption_extractor"

    def extract(
        self,
        candidate: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidate = candidate if isinstance(candidate, Mapping) else {}
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        assumptions = []
        program = candidate.get("program", {}) if isinstance(candidate.get("program"), Mapping) else {}
        steps = program.get("steps", []) if isinstance(program.get("steps"), list) else []
        operation = candidate.get("operation") or (steps[0].get("operation") if steps and isinstance(steps[0], Mapping) else None)
        self._add(assumptions, "operation_assumption", "selected operation is correct", operation, candidate)
        self._add(assumptions, "scope_assumption", "operation scope is appropriate", candidate.get("metadata", {}).get("scope", "local"), candidate)
        self._add(assumptions, "identity_assumption", "object identity is preserved", "identity_preserved", candidate, protected=True)
        self._add(assumptions, "topology_assumption", "object topology is preserved", "topology_preserved", candidate)
        for index, step in enumerate(steps):
            params = step.get("parameters", {}) if isinstance(step, Mapping) and isinstance(step.get("parameters"), Mapping) else {}
            if params.get("color_mapping"):
                self._add(assumptions, "color_mapping_assumption", "color mapping is correct", params.get("color_mapping"), candidate)
            if params.get("path_cells"):
                self._add(assumptions, "target_region_assumption", "target region is correct", params.get("path_cells"), candidate)
            if params.get("cells_to_write"):
                self._add(assumptions, "object_assumption", "target object cells are correct", params.get("cells_to_write"), candidate)
            self._add(assumptions, "ordering_assumption", "program step order is correct", index, candidate, challengeable=len(steps) > 1)
        return {
            "system": self.system_name,
            "assumptions": assumptions,
            "assumption_count": len(assumptions),
            "challengeable_assumption_count": len([item for item in assumptions if item["challengeable"]]),
        }

    def _add(self, rows, assumption_type, description, value, candidate, protected=False, challengeable=True):
        if value is None:
            return
        idx = len(rows)
        rows.append({
            "assumption_id": f"assumption:{candidate.get('candidate_id', 'candidate')}:{idx}",
            "assumption_type": assumption_type,
            "description": description,
            "value": value,
            "confidence": _score(candidate.get("source_confidence", candidate.get("confidence", 0.7))),
            "evidence": [candidate.get("candidate_id")],
            "truth_support": _score(candidate.get("truth_support", 0.0)),
            "context_support": _score(candidate.get("context_support", 0.0)),
            "dependency_support": _score(candidate.get("dependency_support", 0.0)),
            "challengeable": bool(challengeable and not protected),
            "protected_invariant": bool(protected),
        })


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


assumption_extractor = AssumptionExtractor()

__all__ = ["AssumptionExtractor", "assumption_extractor"]
