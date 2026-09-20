"""Gate cognition through validated knowledge before reasoning."""

from __future__ import annotations

from typing import Any, Mapping


class KnowledgeReuseGate:
    def evaluate(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        reuse_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = dict(runtime_context or {})
        reuse = dict(reuse_report or {})
        reusable_strategy_exists = (
            reuse.get("reuse_existing_strategy") is True
            or context.get("reusable_strategy_exists") is True
        )
        validated_context_exists = (
            context.get("validated_context_exists") is True
            or self._validated(context.get("validated_context"))
        )
        locked_truth_exists = (
            context.get("locked_truth_exists") is True
            or self._locked_truth(context.get("locked_truth"))
        )
        return {
            "reusable_strategy_exists": reusable_strategy_exists,
            "validated_context_exists": validated_context_exists,
            "locked_truth_exists": locked_truth_exists,
            "skip_deep_reasoning": reusable_strategy_exists,
            "skip_context_discovery": validated_context_exists,
            "skip_truth_validation": locked_truth_exists,
            "preferred_order": [
                "knowledge_reuse_gate",
                "strategy_reuse_engine",
                "program_reuse",
                "reasoning",
                "evidence_collection",
                "commit",
                "shutdown",
            ],
        }

    def _validated(self, value: Any) -> bool:
        return isinstance(value, Mapping) and (
            value.get("validated") is True
            or value.get("status") in {"PROCESS_CONTEXT_VALIDATED", "VALIDATED_CONTEXT"}
        )

    def _locked_truth(self, value: Any) -> bool:
        return isinstance(value, Mapping) and (
            value.get("locked") is True
            or value.get("final_commit_state") == "LOCKED_TRUTH_PRESERVED"
        )


knowledge_reuse_gate = KnowledgeReuseGate()


__all__ = [
    "KnowledgeReuseGate",
    "knowledge_reuse_gate",
]
