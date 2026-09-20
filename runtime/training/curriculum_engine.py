"""Curriculum stage assignment for knowledge expansion training."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


CURRICULUM_STAGES = ["FOUNDATIONAL", "INTERMEDIATE", "ADVANCED", "FRONTIER"]

FOUNDATIONAL_CONCEPTS = {
    "growth",
    "replication",
    "propagation",
    "color_preservation",
    "shape_preservation",
    "position_preservation",
    "size_preservation",
    "symmetry_preservation",
    "topology_preservation",
    "object_identity_preservation",
}

FRONTIER_CONCEPTS = {
    "occlusion",
    "containment",
    "hidden_object_recovery",
    "multi_object_reasoning",
    "symbolic_remapping",
    "topological_growth",
    "route_completion",
    "path_finding",
    "gravity_simulation",
    "count_by_color",
    "spatial_reasoning",
    "pattern_completion",
    "sequence_completion",
    "object_counting",
}


class CurriculumEngine:
    system_name = "curriculum_engine"

    def assign_stage(
        self,
        concept: str,
        concept_state: str | None = None,
        mastery: float | None = None,
    ) -> str:
        concept = str(concept or "")
        concept_state = str(concept_state or "")
        mastery_score = _score(mastery)
        if concept in FRONTIER_CONCEPTS:
            return "FRONTIER"
        if concept_state in {"CORE_KNOWLEDGE", "FOUNDATIONAL_TRUTH"}:
            return "FOUNDATIONAL"
        if concept in FOUNDATIONAL_CONCEPTS and mastery_score >= 0.85:
            return "FOUNDATIONAL"
        if concept_state in {"STABLE_TRUTH", "TRUTH_COMMITTED"}:
            return "INTERMEDIATE"
        if concept.endswith("_preservation"):
            return "INTERMEDIATE"
        return "ADVANCED"

    def distribution_for(
        self,
        concept_reports: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        counts = {stage: 0 for stage in CURRICULUM_STAGES}
        for item in concept_reports or []:
            if not isinstance(item, Mapping):
                continue
            stage = item.get("curriculum_stage") or self.assign_stage(
                str(item.get("concept") or ""),
                item.get("concept_state"),
                item.get("mastery_score"),
            )
            if stage in counts:
                counts[stage] += 1
        total = max(sum(counts.values()), 1)
        return {
            "system": self.system_name,
            "curriculum_stages": list(CURRICULUM_STAGES),
            "stage_distribution": counts,
            "target_distribution": {
                "FOUNDATIONAL": 0.10,
                "INTERMEDIATE": 0.30,
                "ADVANCED": 0.45,
                "FRONTIER": 0.15,
            },
            "frontier_share": round(counts["FRONTIER"] / total, 4),
        }


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "CURRICULUM_STAGES",
    "FRONTIER_CONCEPTS",
    "FOUNDATIONAL_CONCEPTS",
    "CurriculumEngine",
]
