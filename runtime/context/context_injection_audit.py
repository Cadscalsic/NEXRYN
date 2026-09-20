"""Per-concept audit of context visibility, injection, and gate blockers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class ContextInjectionAudit:
    system_name = "context_injection_audit"

    def audit_concept(
        self,
        concept: str,
        contexts: Iterable[Mapping[str, Any]] | None = None,
        consumption_report: Mapping[str, Any] | None = None,
        readiness_report: Mapping[str, Any] | None = None,
        promotion: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contexts = list(contexts or [])
        consumption_report = consumption_report if isinstance(consumption_report, Mapping) else {}
        readiness_report = readiness_report if isinstance(readiness_report, Mapping) else {}
        promotion = promotion if isinstance(promotion, Mapping) else {}
        context_support = _score(consumption_report.get("context_support_score"))
        process_ready = bool(readiness_report.get("process_context_ready"))
        blockers = list(readiness_report.get("process_context_ready_false_reasons", []))
        if context_support <= 0.0:
            blockers.append("context_support_zero")
        failed_gates = promotion.get("failed_gates", [])
        for gate in failed_gates if isinstance(failed_gates, list) else []:
            if "context" in str(gate) and str(gate) not in blockers:
                blockers.append(str(gate))
        return {
            "system": self.system_name,
            "concept": concept,
            "context_exists": bool(contexts),
            "context_registered": any(context.get("context_id") for context in contexts if isinstance(context, Mapping)),
            "context_available": bool(consumption_report.get("available", 0)),
            "context_injected": bool(consumption_report.get("injected", 0)),
            "context_consumed": bool(consumption_report.get("consumed", 0)),
            "context_support_score": context_support,
            "process_context_ready": process_ready,
            "context_gate_reason": "context_consumed" if consumption_report.get("consumed") else "context_not_consumed",
            "context_gate_blockers": blockers,
            "context_gate_explainable": True,
        }

    def audit(self, concept_reports: Any) -> dict[str, Any]:
        reports = _reports(concept_reports)
        audits = [
            self.audit_concept(
                str(report.get("concept") or "unknown"),
                report.get("context_artifacts", {}).get("contexts", []),
                report.get("context_consumption_report", {}),
                report.get("process_context_readiness_report", {}),
                report.get("truth_candidate_promotion", {}),
            )
            for report in reports
            if isinstance(report, Mapping)
        ]
        blocked = [item for item in audits if item["context_gate_blockers"]]
        return {
            "system": self.system_name,
            "concept_count": len(audits),
            "context_blocked_count": len(blocked),
            "context_injection_audit": audits,
            "blocked_context_injections": blocked,
        }


def _reports(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if isinstance(value.get("concepts"), list):
            return [item for item in value["concepts"] if isinstance(item, Mapping)]
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


context_injection_audit = ContextInjectionAudit()


__all__ = ["ContextInjectionAudit", "context_injection_audit"]
