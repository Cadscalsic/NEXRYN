"""Task signature mapping from task profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskSignature:
    signature: str
    task_family: str
    features: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "signature": self.signature,
            "task_family": self.task_family,
            "features": list(self.features),
        }


class TaskSignatureMapper:
    def map_profile(self, task_profile: Any) -> TaskSignature:
        families = set(getattr(task_profile, "expected_reasoning_families", set()) or set())
        capabilities = set(getattr(task_profile, "expected_capabilities", set()) or set())
        features = sorted(families.union(capabilities))
        family = self._family_for(features)
        signature = "_".join(features) if features else "unknown"
        return TaskSignature(signature=signature, task_family=family, features=tuple(features))

    def _family_for(self, features: list[str]) -> str:
        joined = " ".join(features)
        if "color_mapping" in joined:
            return "color_mapping"
        if "gravity" in joined:
            return "gravity"
        if "rotation" in joined and "scaling" in joined:
            return "rotation_scaling"
        if "topology" in joined:
            return "topology"
        if "spatial" in joined:
            return "spatial"
        if "dependency" in joined:
            return "multi_step_transformations"
        if "symbolic" in joined:
            return "symbolic_mapping"
        return "ARC_abstraction_tasks"


__all__ = ["TaskSignature", "TaskSignatureMapper"]
