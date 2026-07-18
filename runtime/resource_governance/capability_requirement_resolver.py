"""Resolve lightweight task profiles into expected cognitive capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.resource_governance.complexity_estimator import ComplexityLevel


@dataclass(frozen=True)
class CapabilityRequirement:
    expected_capabilities: set[str]
    potential_capabilities: set[str]
    not_required_capabilities: set[str]
    reasoning_families: set[str]

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "expected_capabilities": sorted(self.expected_capabilities),
            "potential_capabilities": sorted(self.potential_capabilities),
            "not_required_capabilities": sorted(self.not_required_capabilities),
            "reasoning_families": sorted(self.reasoning_families),
        }


class CapabilityRequirementResolver:
    def resolve(
        self,
        task: Any,
        complexity: dict[str, ComplexityLevel],
    ) -> CapabilityRequirement:
        text = _task_text(task)
        expected = {"object_tracking"}
        potential: set[str] = set()
        families = {"object_tracking"}

        if _has_any(text, {"color", "colour", "remap", "replace", "mapping", "map"}):
            expected.add("color_mapping")
            potential.add("semantic_compilation")
            families.add("color_mapping")

        if _has_any(text, {"rotate", "rotation", "scale", "scaling", "mirror", "reflect", "transform", "translate", "shift"}):
            expected.add("transformation_reasoning")
            expected.add("semantic_compilation")
            potential.add("spatial_reasoning")
            families.add("transformation")

        if _has_any(text, {"spatial", "left", "right", "above", "below", "inside", "outside", "adjacent", "distance"}):
            expected.add("spatial_reasoning")
            families.add("spatial")

        if _has_any(text, {"gravity", "fall", "drop", "support", "collision"}):
            expected.add("spatial_reasoning")
            expected.add("gravity_reasoning")
            potential.add("topology_reasoning")
            families.update({"spatial", "causal"})

        if complexity["topology_complexity"] in {ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.EXTREME}:
            potential.add("topology_reasoning")
            families.add("topology")

        if complexity["dependency_complexity"] in {ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.EXTREME}:
            expected.add("dependency_reasoning")
            families.add("dependency")

        if complexity["semantic_complexity"] in {ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.EXTREME}:
            potential.add("semantic_memory_integration")
            potential.add("knowledge_fabric")
            families.add("semantic")

        if complexity["execution_uncertainty"] in {ComplexityLevel.HIGH, ComplexityLevel.EXTREME}:
            potential.add("candidate_arena")
            potential.add("diagnostic_probe")
            families.add("pattern_completion")

        if not expected.intersection({"color_mapping", "transformation_reasoning", "gravity_reasoning"}):
            potential.add("semantic_compilation")
            families.add("symbolic")

        all_capabilities = {
            "object_tracking",
            "color_mapping",
            "transformation_reasoning",
            "semantic_compilation",
            "spatial_reasoning",
            "topology_reasoning",
            "gravity_reasoning",
            "dependency_reasoning",
            "knowledge_fabric",
            "semantic_memory_integration",
            "candidate_arena",
            "diagnostic_probe",
        }
        not_required = all_capabilities - expected - potential
        return CapabilityRequirement(
            expected_capabilities=expected,
            potential_capabilities=potential,
            not_required_capabilities=not_required,
            reasoning_families=families,
        )


def _task_text(task: Any) -> str:
    if isinstance(task, dict):
        return " ".join(
            str(task.get(key, ""))
            for key in ("description", "prompt", "task", "instruction", "notes")
            if task.get(key)
        ).lower()
    return str(task or "").lower()


def _has_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


__all__ = [
    "CapabilityRequirement",
    "CapabilityRequirementResolver",
]
