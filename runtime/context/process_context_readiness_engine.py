"""Explain process-context readiness rather than returning an opaque boolean."""

from __future__ import annotations

from typing import Any, Mapping


class ProcessContextReadinessEngine:
    system_name = "process_context_readiness_engine"

    def evaluate(
        self,
        concept: str,
        consumption_report: Mapping[str, Any] | None = None,
        dependency_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        consumption_report = consumption_report if isinstance(consumption_report, Mapping) else {}
        dependency_report = dependency_report if isinstance(dependency_report, Mapping) else {}
        process = _find(consumption_report.get("consumption", []), "PROCESS_CONTEXT")
        dependency = _find(consumption_report.get("consumption", []), "DEPENDENCY_SURFACE")
        process_score = max(
            _score(process.get("context_support_score")),
            _score(consumption_report.get("context_support_score")),
        )
        dependency_score = max(
            _score(dependency.get("context_support_score")),
            _score(dependency_report.get("dependency_confidence")),
            _score(dependency_report.get("promotion_dependency_score")),
        )
        completeness = round(
            (
                float(bool(process.get("consumed")))
                + float(bool(dependency.get("consumed") or dependency_score >= 0.72))
                + float(bool(consumption_report.get("valid_context_consumption")))
            )
            / 3.0,
            4,
        )
        strength = round((process_score * 0.5) + (dependency_score * 0.3) + (completeness * 0.2), 4)
        blockers = []
        if not process.get("consumed"):
            blockers.append("process_context_not_consumed")
        if process_score < 0.72:
            blockers.append("process_context_strength_below_0.72")
        if dependency_score < 0.70:
            blockers.append("dependency_surface_strength_below_0.70")
        if completeness < 0.67:
            blockers.append("process_context_incomplete")
        ready = not blockers
        return {
            "system": self.system_name,
            "concept": concept,
            "process_context_score": process_score,
            "process_context_strength": strength,
            "process_context_dependencies": {
                "dependency_score": dependency_score,
                "dependency_surface_consumed": bool(dependency.get("consumed")),
            },
            "process_context_completeness": completeness,
            "process_context_readiness": ready,
            "process_context_ready": ready,
            "process_context_ready_false_reasons": blockers,
        }


def _find(items: Any, context_type: str) -> dict[str, Any]:
    if not isinstance(items, list):
        return {}
    for item in items:
        if isinstance(item, Mapping) and item.get("context_type") == context_type:
            return dict(item)
    return {}


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


process_context_readiness_engine = ProcessContextReadinessEngine()


__all__ = ["ProcessContextReadinessEngine", "process_context_readiness_engine"]
