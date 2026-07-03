"""Memory for reusable causal context models."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping


class CausalContextMemory:
    """Store successful and failed causal contexts by cause-effect signature."""

    system_name = "causal_context_memory"

    def __init__(self):
        self.successful_contexts = []
        self.failed_contexts = []
        self.signature_index = {}
        self.cause_effect_mappings = {}
        self.confidence_history = {}

    def build_signature(
        self,
        causal_context: Mapping[str, Any] | None = None,
    ) -> str:
        causal_context = causal_context if isinstance(causal_context, Mapping) else {}
        return "|".join([
            str(causal_context.get("causal_family", "unknown")),
            str(causal_context.get("cause", "unknown")),
            str(causal_context.get("effect", "unknown")),
            str(causal_context.get("supporting_process", "")),
        ])

    def remember(
        self,
        causal_context: Mapping[str, Any],
        simulation_accuracy: float = 0.0,
        success: bool | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        success = (
            bool(simulation_accuracy >= 0.90)
            if success is None
            else bool(success)
        )
        signature = self.build_signature(causal_context)
        confidence = float(causal_context.get("confidence", 0.0) or 0.0)
        record = {
            "signature": signature,
            "causal_context": copy.deepcopy(dict(causal_context)),
            "simulation_accuracy": round(float(simulation_accuracy or 0.0), 4),
            "success": success,
            "evidence": copy.deepcopy(dict(evidence or {})),
            "timestamp": str(datetime.utcnow()),
        }
        target = self.successful_contexts if success else self.failed_contexts
        target.append(record)
        self.signature_index[signature] = record

        cause = str(causal_context.get("cause", "unknown"))
        effect = str(causal_context.get("effect", "unknown"))
        self.cause_effect_mappings.setdefault(cause, [])
        self.cause_effect_mappings[cause].append(effect)
        self.confidence_history.setdefault(signature, [])
        self.confidence_history[signature].append(round(confidence, 4))
        return record

    def retrieve_successful(
        self,
        causal_family: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not causal_family:
            return [
                copy.deepcopy(record)
                for record in self.successful_contexts[-limit:]
            ]
        matches = [
            record
            for record in self.successful_contexts
            if record.get("causal_context", {}).get("causal_family") == causal_family
        ]
        return [copy.deepcopy(record) for record in matches[-limit:]]

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "successful_causal_contexts": len(self.successful_contexts),
            "failed_causal_contexts": len(self.failed_contexts),
            "known_signatures": len(self.signature_index),
            "cause_effect_mappings": dict(self.cause_effect_mappings),
            "causal_confidence_history": dict(self.confidence_history),
        }


causal_context_memory = CausalContextMemory()


__all__ = [
    "CausalContextMemory",
    "causal_context_memory",
]
