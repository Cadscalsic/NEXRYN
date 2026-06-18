"""Validation for typed process dependency links."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.process.process_dependency_types import (
    SUPPORTED_PROCESS_DEPENDENCY_TYPES,
)


class ProcessDependencyValidator:
    """Validate dependency typing without lowering governance thresholds."""

    system_name = "process_dependency_validator"

    def validate(self, dependency_report: Mapping[str, Any]) -> dict[str, Any]:
        links = dependency_report.get("typed_dependency_relations", []) or []
        invalid = [
            link
            for link in links
            if link.get("dependency_type") not in SUPPORTED_PROCESS_DEPENDENCY_TYPES
        ]
        coverage = (
            (len(links) - len(invalid)) / len(links)
            if links
            else 0.0
        )
        return {
            "system": self.system_name,
            "typed_process_dependencies": "enabled",
            "typed_dependency_validation_passed": bool(links and not invalid),
            "typed_dependency_coverage": round(coverage, 4),
            "invalid_typed_dependencies": invalid,
            "process_dependency_links_used":
            dependency_report.get("process_dependency_links_used", len(links)),
            "process_dependency_links_loaded":
            dependency_report.get("process_dependency_links_loaded", len(links)),
        }


__all__ = ["ProcessDependencyValidator"]
