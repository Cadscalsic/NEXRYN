"""Invariant tagging and penalties for hypothesis arbitration."""

from __future__ import annotations

from typing import Any, Mapping


class InvariantFilter:
    """Keep invariants as constraints without letting them explain tasks."""

    system_name = "invariant_filter"

    INVARIANT_PRIMITIVES = {
        "preserve_size",
        "preserve_shape",
        "preserve_colors",
        "preserve_density",
        "preserve_topology",
        "preserve_symmetry",
        "preserve_objects",
        "preserve_position",
    }

    EXPLANATORY_PENALTY = 0.30

    def semantic_class(self, hypothesis: Mapping[str, Any] | None) -> str:
        if not isinstance(hypothesis, Mapping):
            return "unknown"
        primitive = str(hypothesis.get("primitive", ""))
        hypothesis_type = str(hypothesis.get("type", ""))
        if (
            primitive in self.INVARIANT_PRIMITIVES
            or primitive.startswith("preserve_")
            or "preservation" in hypothesis_type
            or "conservation" in hypothesis_type
        ):
            return "invariant"
        return "transformation"

    def penalty(self, hypothesis: Mapping[str, Any] | None) -> float:
        return self.EXPLANATORY_PENALTY if self.semantic_class(hypothesis) == "invariant" else 0.0

    def annotate(
        self,
        hypotheses: list[Mapping[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        annotated = []
        for hypothesis in hypotheses or []:
            if not isinstance(hypothesis, Mapping):
                continue
            updated = dict(hypothesis)
            semantic_class = self.semantic_class(updated)
            updated["semantic_class"] = semantic_class
            updated["invariant_penalty"] = self.penalty(updated)
            annotated.append(updated)
        return annotated

    def can_invariant_win(
        self,
        hypothesis: Mapping[str, Any] | None,
        max_transformation_salience: float,
        invariant_salience: float,
    ) -> bool:
        if self.semantic_class(hypothesis) != "invariant":
            return True
        return not max_transformation_salience > invariant_salience


invariant_filter = InvariantFilter()


__all__ = [
    "InvariantFilter",
    "invariant_filter",
]
