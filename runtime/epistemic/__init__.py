"""Epistemic runtime compatibility namespace."""

from runtime.epistemic.accepted_evidence_assessment import (
    AcceptedEvidenceEpistemicAssessmentEngine,
)
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)

__all__ = [
    "AcceptedEvidenceEpistemicAssessmentEngine",
    "EvidenceSourceIndependenceEngine",
]
