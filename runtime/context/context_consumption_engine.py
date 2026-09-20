"""Context consumption layer for promotion and truth pipelines."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.context.context_serialization_engine import normalize_context


class ContextConsumptionEngine:
    system_name = "context_consumption_engine"

    def consume_process_context(self, concept: str, contexts: Iterable[Any]) -> dict[str, Any]:
        return self._consume_type(concept, contexts, "PROCESS_CONTEXT")

    def consume_semantic_context(self, concept: str, contexts: Iterable[Any]) -> dict[str, Any]:
        return self._consume_type(concept, contexts, "SEMANTIC_CONTEXT")

    def consume_dependency_surface(self, concept: str, contexts: Iterable[Any]) -> dict[str, Any]:
        return self._consume_type(concept, contexts, "DEPENDENCY_SURFACE")

    def consume_context_hierarchy(self, concept: str, hierarchy: Any) -> dict[str, Any]:
        normalized = normalize_context(hierarchy)
        available = bool(normalized)
        score = _score(
            normalized.get("confidence")
            or normalized.get("hierarchy_confidence")
            or normalized.get("context_strength")
            or (0.75 if available else 0.0)
        )
        return {
            "context_type": "CONTEXT_HIERARCHY",
            "concept": concept,
            "available": available,
            "consumed": available,
            "context_support_score": score,
            "context": normalized if available else {},
        }

    def consume_all(
        self,
        concept: str,
        contexts: Iterable[Any] | None = None,
        hierarchy: Any | None = None,
    ) -> dict[str, Any]:
        contexts = list(contexts or [])
        process = self.consume_process_context(concept, contexts)
        semantic = self.consume_semantic_context(concept, contexts)
        dependency = self.consume_dependency_surface(concept, contexts)
        hierarchy_result = self.consume_context_hierarchy(concept, hierarchy)
        consumed = [process, semantic, dependency, hierarchy_result]
        hits = [item for item in consumed if item["consumed"]]
        support = max([item["context_support_score"] for item in consumed] or [0.0])
        return {
            "system": self.system_name,
            "concept": concept,
            "created": len(contexts),
            "registered": sum(1 for item in contexts if normalize_context(item).get("context_id")),
            "available": sum(1 for item in consumed if item["available"]),
            "injected": len(hits),
            "consumed": len(hits),
            "context_hits": len(hits),
            "context_consumed": len(hits),
            "context_support_score": round(support, 4),
            "process_context_ready": process["consumed"] and process["context_support_score"] >= 0.72,
            "consumption": consumed,
            "valid_context_consumption": bool(hits),
        }

    def validate_context_consumption(self, report: Mapping[str, Any] | None) -> dict[str, Any]:
        report = report if isinstance(report, Mapping) else {}
        blockers = []
        if not report.get("consumed", 0):
            blockers.append("no_context_consumed")
        if report.get("context_support_score", 0.0) <= 0.0:
            blockers.append("context_support_zero")
        return {
            "system": self.system_name,
            "valid": not blockers,
            "blockers": blockers,
            "context_consumed": int(report.get("consumed", 0) or 0),
        }

    def _consume_type(
        self,
        concept: str,
        contexts: Iterable[Any],
        context_type: str,
    ) -> dict[str, Any]:
        candidates = []
        for context in contexts:
            normalized = normalize_context(context)
            if _matches(concept, normalized, context_type):
                candidates.append(normalized)
        best = max(candidates, key=lambda item: _confidence(item), default={})
        score = _confidence(best)
        return {
            "context_type": context_type,
            "concept": concept,
            "created": bool(candidates),
            "registered": bool(best.get("context_id")),
            "available": bool(best),
            "injected": bool(best),
            "consumed": bool(best),
            "context_support_score": score,
            "context": best,
        }


def _matches(concept: str, context: Mapping[str, Any], context_type: str) -> bool:
    return (
        bool(context)
        and str(context.get("concept") or "") == str(concept)
        and str(context.get("context_type") or "").upper() == context_type
    )


def _confidence(context: Mapping[str, Any]) -> float:
    return _score(
        context.get("confidence")
        or context.get("context_confidence")
        or context.get("support_score")
        or context.get("dependency_confidence")
    )


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


context_consumption_engine = ContextConsumptionEngine()


__all__ = ["ContextConsumptionEngine", "context_consumption_engine"]
