"""Validation for normalized context objects."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.context.context_serializer import normalize_context


class ContextValidationEngine:
    system_name = "context_validation_engine"

    def validate(self, context: Any) -> dict[str, Any]:
        normalized = normalize_context(context)
        issues = []
        context_id = (
            normalized.get("context_id")
            or normalized.get("context_name")
            or normalized.get("process_context")
            or normalized.get("generated_context")
        )
        if not context_id:
            issues.append("context_identifier_missing")

        semantic_fields = [
            "semantic_context",
            "properties",
            "capabilities",
            "constraints",
            "implications",
        ]
        semantic_complete = any(normalized.get(key) for key in semantic_fields)
        if not semantic_complete:
            issues.append("semantic_completeness_missing")

        hierarchy_consistent = self._hierarchy_consistent(normalized)
        if not hierarchy_consistent:
            issues.append("hierarchy_inconsistent")

        dependency_links = self._links_present(
            normalized,
            ("dependency_snapshot", "process_dependency_memory", "dependency_promotion_evidence"),
        )
        truth_links = self._links_present(
            normalized,
            ("truth_candidate_report", "truth_candidates", "contextual_truth"),
        )

        return {
            "system": self.system_name,
            "context_id": context_id,
            "context_structure_valid": not issues,
            "semantic_completeness": semantic_complete,
            "hierarchy_consistency": hierarchy_consistent,
            "dependency_links": dependency_links,
            "truth_links": truth_links,
            "issues": issues,
            "context_validation_report": {
                "normalized": True,
                "field_count": len(normalized),
                "safe_for_serialization": True,
            },
        }

    def _hierarchy_consistent(self, context: Mapping[str, Any]) -> bool:
        parent = context.get("hierarchy_root") or context.get("parent_context")
        children = context.get("hierarchy_children", [])
        if children is None:
            return True
        return isinstance(children, list) and (
            parent is not None or not children
        )

    def _links_present(
        self,
        context: Mapping[str, Any],
        keys: tuple[str, ...],
    ) -> list[str]:
        return [key for key in keys if context.get(key)]


context_validation_engine = ContextValidationEngine()


__all__ = ["ContextValidationEngine", "context_validation_engine"]
