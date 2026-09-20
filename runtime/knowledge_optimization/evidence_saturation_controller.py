"""Hard-stop evidence saturation controller."""

from __future__ import annotations

from typing import Any, Mapping


MAX_SUPPORT_SAMPLES = 20
MAX_EVIDENCE_COLLECTION_TIME = 3.0
MAX_VALIDATION_CYCLES = 5

SATURATION_DECISIONS = ("PROMOTE", "QUARANTINE", "REJECT")


class EvidenceSaturationController:
    def evaluate(
        self,
        metrics: Mapping[str, Any] | None = None,
        threshold: float | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        support_confidence = self._number(data.get("support_confidence", data.get("support_score", 0.0)))
        contradiction_score = self._number(data.get("contradiction_score", 0.0))
        support_samples = int(self._number(data.get("support_samples", data.get("supporting_evidence_count", 0))))
        collection_time = self._number(data.get("collection_time", data.get("evidence_collection_time", 0.0)))
        validation_cycles = int(self._number(data.get("validation_cycles", 0)))
        required = self._number(threshold if threshold is not None else data.get("support_threshold", 0.85))

        saturated = (
            support_confidence >= required
            or support_samples >= MAX_SUPPORT_SAMPLES
            or collection_time >= MAX_EVIDENCE_COLLECTION_TIME
            or validation_cycles >= MAX_VALIDATION_CYCLES
        )
        if support_confidence >= required and contradiction_score <= 0.30:
            decision = "PROMOTE"
        elif contradiction_score > 0.30:
            decision = "QUARANTINE"
        else:
            decision = "REJECT"
        return {
            "evidence_saturated": True if saturated else False,
            "decision": decision,
            "support_confidence": support_confidence,
            "support_threshold": required,
            "contradiction_score": contradiction_score,
            "support_samples": support_samples,
            "collection_time": min(collection_time, MAX_EVIDENCE_COLLECTION_TIME),
            "validation_cycles": min(validation_cycles, MAX_VALIDATION_CYCLES),
            "continue_collecting": False if saturated else True,
            "hard_limits": {
                "MAX_SUPPORT_SAMPLES": MAX_SUPPORT_SAMPLES,
                "MAX_EVIDENCE_COLLECTION_TIME": MAX_EVIDENCE_COLLECTION_TIME,
                "MAX_VALIDATION_CYCLES": MAX_VALIDATION_CYCLES,
            },
        }

    def _number(self, value: Any) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0


evidence_saturation_controller = EvidenceSaturationController()


__all__ = [
    "MAX_SUPPORT_SAMPLES",
    "MAX_EVIDENCE_COLLECTION_TIME",
    "MAX_VALIDATION_CYCLES",
    "SATURATION_DECISIONS",
    "EvidenceSaturationController",
    "evidence_saturation_controller",
]
