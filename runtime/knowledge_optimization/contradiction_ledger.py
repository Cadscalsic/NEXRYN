"""Weighted contradiction ledger for proportional evidence handling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping


EVIDENCE_WEIGHT: dict[str, float] = {
    "exact_success": 1.00,
    "high_confidence_success": 0.85,
    "transfer_success": 0.75,
    "partial_success": 0.50,
    "contradiction": -1.00,
}


@dataclass
class EvidenceRecord:
    concept_name: str
    evidence_type: str
    confidence: float = 1.0
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContradictionLedger:
    """Track support and contradiction as weighted proportions."""

    def __init__(self) -> None:
        self.records: dict[str, list[EvidenceRecord]] = {}

    def record(
        self,
        concept_name: str,
        evidence_type: str,
        confidence: float = 1.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvidenceRecord:
        record = EvidenceRecord(
            concept_name=str(concept_name),
            evidence_type=str(evidence_type),
            confidence=self._bounded(confidence),
            timestamp=str(datetime.utcnow()),
            metadata=dict(metadata or {}),
        )
        self.records.setdefault(record.concept_name, []).append(record)
        return record

    def evaluate(
        self,
        concept_name: str,
        evidence: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        records = [self._coerce(item, concept_name) for item in evidence] if evidence is not None else list(self.records.get(str(concept_name), []))
        total_count = len(records)
        conflicting_count = sum(1 for item in records if item.evidence_type == "contradiction")
        contradiction_score = conflicting_count / max(1, total_count)

        support_score = 0.0
        contradiction_weight = 0.0
        for index, item in enumerate(records):
            recency_multiplier = 1.0 + min(0.10, index / max(1, total_count) * 0.10)
            weight = EVIDENCE_WEIGHT.get(item.evidence_type, 0.0)
            weighted = abs(weight) * item.confidence * recency_multiplier
            if weight >= 0:
                support_score += weighted
            else:
                contradiction_weight += weighted

        weighted_total = support_score + contradiction_weight
        weighted_contradiction_score = contradiction_weight / max(1.0, weighted_total)
        support_confidence = support_score / max(1.0, weighted_total)
        report = {
            "concept_name": str(concept_name),
            "total_evidence_count": total_count,
            "supporting_evidence_count": total_count - conflicting_count,
            "conflicting_evidence_count": conflicting_count,
            "contradiction_score": round(contradiction_score, 6),
            "weighted_contradiction_score": round(weighted_contradiction_score, 6),
            "support_score": round(support_score, 6),
            "support_confidence": round(support_confidence, 6),
            "binary_contradiction": False,
            "evidence_weight": dict(EVIDENCE_WEIGHT),
        }
        return report

    def _coerce(
        self,
        item: Mapping[str, Any],
        concept_name: str,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            concept_name=str(item.get("concept_name", concept_name)),
            evidence_type=str(item.get("evidence_type", item.get("type", "partial_success"))),
            confidence=self._bounded(item.get("confidence", 1.0)),
            timestamp=item.get("timestamp"),
            metadata=dict(item.get("metadata", {})),
        )

    def _bounded(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


contradiction_ledger = ContradictionLedger()


__all__ = [
    "EVIDENCE_WEIGHT",
    "EvidenceRecord",
    "ContradictionLedger",
    "contradiction_ledger",
]
