"""Reuse-first strategy selection for knowledge optimization."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.knowledge.current_knowledge_admission import CurrentKnowledgeAdmissionGate


SEARCH_ORDER: tuple[str, ...] = (
    "strategy_memory",
    "program_memory",
    "context_memory",
    "truth_memory",
    "reasoning",
)


class KnowledgeStrategyReuseEngine:
    SHAPE_SIMILARITY_THRESHOLD = 0.95
    CONTEXT_SIMILARITY_THRESHOLD = 0.90
    STRATEGY_CONFIDENCE_THRESHOLD = 0.85

    def __init__(
        self,
        knowledge_admission_gate: CurrentKnowledgeAdmissionGate | None = None,
    ) -> None:
        self.strategy_hits = 0
        self.strategy_misses = 0
        self.knowledge_admission_gate = (
            knowledge_admission_gate or CurrentKnowledgeAdmissionGate()
        )
        self.current_knowledge_inputs: list[dict[str, Any]] = []
        self.excluded_noncurrent_knowledge: list[dict[str, Any]] = []

    def find_reusable_strategy(
        self,
        query: Mapping[str, Any] | None = None,
        memories: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        query_data = dict(query or {})
        memory_data = dict(memories or {})
        checked: list[str] = []
        best_candidate: Mapping[str, Any] | None = None
        best_source = "reasoning"

        for source in SEARCH_ORDER[:-1]:
            checked.append(source)
            candidates = self._candidates(memory_data.get(source, query_data.get(source)))
            for candidate in candidates:
                candidate = self._admit_current_knowledge_if_required(candidate)
                if candidate is None:
                    continue
                if self._eligible(candidate):
                    best_candidate = candidate
                    best_source = source
                    break
            if best_candidate is not None:
                break

        reusable = best_candidate is not None
        if reusable:
            self.strategy_hits += 1
        else:
            self.strategy_misses += 1
            checked.append("reasoning")
        total = self.strategy_hits + self.strategy_misses
        return {
            "reuse_existing_strategy": reusable,
            "selected_source": best_source,
            "search_order": SEARCH_ORDER,
            "checked_sources": checked,
            "strategy_candidate": dict(best_candidate or {}),
            "skip_deep_reasoning": reusable,
            "strategy_hits": self.strategy_hits,
            "strategy_misses": self.strategy_misses,
            "current_knowledge_input_count": len(self.current_knowledge_inputs),
            "excluded_noncurrent_knowledge_count": len(
                self.excluded_noncurrent_knowledge
            ),
            "reuse_rate": self.strategy_hits / max(1, total),
        }

    def _admit_current_knowledge_if_required(
        self,
        candidate: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        item = dict(candidate)
        if not (item.get("knowledge_id") or item.get("source_knowledge_id")):
            return item
        admission_candidate = item
        if item.get("source_knowledge_id") and not item.get("knowledge_id"):
            admission_candidate = {
                "knowledge_id": item.get("source_knowledge_id"),
                "subject_id": item.get("source_knowledge_subject_id"),
                "current_knowledge_decision_id": item.get(
                    "source_knowledge_decision_id"
                ),
                "current_state_fingerprint": item.get(
                    "source_knowledge_fingerprint"
                ),
                "support_fingerprint": item.get(
                    "source_knowledge_support_fingerprint"
                ),
            }
        admission = self.knowledge_admission_gate.admit_current_knowledge(
            admission_candidate,
            consumer_scope="knowledge_strategy_reuse_engine",
        )
        record = {**item, "current_knowledge_admission": admission.to_dict()}
        if not admission.admitted:
            self.excluded_noncurrent_knowledge.append(record)
            return None
        record.update({
            "source_knowledge_id": admission.knowledge_id,
            "source_knowledge_subject_id": admission.subject_id,
            "source_knowledge_decision_id": admission.current_knowledge_decision_id,
            "source_knowledge_status": admission.current_status,
            "source_knowledge_fingerprint": admission.current_state_fingerprint,
        })
        self.current_knowledge_inputs.append(record)
        return record

    def _eligible(self, candidate: Mapping[str, Any]) -> bool:
        return (
            self._number(candidate.get("shape_similarity", 0.0)) >= self.SHAPE_SIMILARITY_THRESHOLD
            and self._number(candidate.get("context_similarity", candidate.get("context_match", 0.0))) >= self.CONTEXT_SIMILARITY_THRESHOLD
            and self._number(candidate.get("strategy_confidence", candidate.get("confidence", candidate.get("success_rate", 0.0)))) >= self.STRATEGY_CONFIDENCE_THRESHOLD
        )

    def _candidates(self, value: Any) -> list[Mapping[str, Any]]:
        if isinstance(value, Mapping):
            return [value]
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        return []

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


strategy_reuse_engine = KnowledgeStrategyReuseEngine()


__all__ = [
    "SEARCH_ORDER",
    "KnowledgeStrategyReuseEngine",
    "strategy_reuse_engine",
]
