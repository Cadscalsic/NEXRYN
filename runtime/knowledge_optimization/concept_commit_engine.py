"""Commit saturated, well-supported concepts into trusted states."""

from __future__ import annotations

from typing import Any, Mapping


class ConceptCommitEngine:
    TRUSTED_CONCEPT = "TRUSTED_CONCEPT"
    LOCKED_CONCEPT = "LOCKED_CONCEPT"
    QUARANTINED_CONCEPT = "QUARANTINED_CONCEPT"
    REJECTED_CONCEPT = "REJECTED_CONCEPT"

    def __init__(self) -> None:
        self.commits: list[dict[str, Any]] = []

    def evaluate(
        self,
        concept_name: str,
        metrics: Mapping[str, Any] | None = None,
        governance_approved: bool = False,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        support_score = self._number(data.get("support_score", data.get("support_confidence", 0.0)))
        support_threshold = self._number(data.get("support_threshold", 0.85))
        contradiction_score = self._number(data.get("contradiction_score", 0.0))
        contradiction_limit = self._number(data.get("contradiction_limit", 0.10))
        evidence_saturated = data.get("evidence_saturated") is True

        promoted = (
            support_score >= support_threshold
            and contradiction_score <= contradiction_limit
            and evidence_saturated
        )
        if promoted:
            state = self.LOCKED_CONCEPT if governance_approved else self.TRUSTED_CONCEPT
            action = "COMMIT"
        elif contradiction_score > contradiction_limit:
            state = self.QUARANTINED_CONCEPT
            action = "QUARANTINE"
        else:
            state = self.REJECTED_CONCEPT
            action = "REJECT"
        report = {
            "concept_name": str(concept_name),
            "action": action,
            "concept_state": state,
            "promoted": promoted,
            "support_score": support_score,
            "support_threshold": support_threshold,
            "contradiction_score": contradiction_score,
            "contradiction_limit": contradiction_limit,
            "evidence_saturated": evidence_saturated,
            "governance_approved": bool(governance_approved),
            "shutdown_runtime": bool(promoted),
            "post_commit_action": "shutdown_runtime" if promoted else "continue_review",
        }
        self.commits.append(report)
        return report

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


concept_commit_engine = ConceptCommitEngine()


__all__ = [
    "ConceptCommitEngine",
    "concept_commit_engine",
]
