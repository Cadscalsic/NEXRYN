"""Audit dependency promotion and injection state for concept reports."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.dependency.dependency_sync_engine import dependency_sync_engine


class DependencyInjectionAudit:
    """Produces one dependency injection audit row per concept report."""

    system_name = "dependency_injection_audit"

    def audit(
        self,
        concept_reports: Any,
    ) -> dict[str, Any]:
        reports = self._concept_reports(concept_reports)
        audits = []
        for report in reports:
            concept = str(
                report.get("concept")
                or report.get("name")
                or report.get("truth")
                or report.get("source_concept")
                or "unknown"
            )
            snapshot = dependency_sync_engine.snapshot(concept, report)
            audits.append(snapshot.as_dict())
        blocked = [
            item for item in audits
            if item.get("dependency_block_reason")
        ]
        return {
            "system": self.system_name,
            "concept_count": len(audits),
            "blocked_count": len(blocked),
            "dependency_injection_audit": audits,
            "blocked_dependency_injections": blocked,
        }

    def _concept_reports(self, value: Any) -> list[Mapping[str, Any]]:
        if isinstance(value, Mapping):
            if isinstance(value.get("concepts"), list):
                return [
                    item for item in value["concepts"]
                    if isinstance(item, Mapping)
                ]
            if isinstance(value.get("evaluations"), list):
                return [
                    item for item in value["evaluations"]
                    if isinstance(item, Mapping)
                ]
            return [value]
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        return []


dependency_injection_audit = DependencyInjectionAudit()


__all__ = ["DependencyInjectionAudit", "dependency_injection_audit"]
