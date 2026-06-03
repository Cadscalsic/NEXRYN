from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4


def utc_timestamp():
    return datetime.utcnow().isoformat()


def new_truth_id():
    return f"truth:{uuid4().hex}"


@dataclass
class TruthRecord:
    truth_id: str
    concept: str
    truth_state: str = "PROVISIONAL_TRUTH_COMMITMENT"
    confidence: float = 0.0
    evidence_strength: float = 0.0
    causal_alignment: float = 0.0
    contradiction_score: float = 1.0
    semantic_consistency: float = 0.0
    generalization_score: float = 0.0
    identity_continuity: float = 0.0
    semantic_drift: float = 1.0
    source_tasks: List[str] = field(default_factory=list)
    evidence_sources: List[str] = field(default_factory=list)
    lineage: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_timestamp)
    revision_count: int = 0

    @classmethod
    def create(cls, concept, **kwargs):
        truth_id = kwargs.pop("truth_id", None) or new_truth_id()
        created_at = kwargs.pop("created_at", None) or utc_timestamp()
        return cls(
            truth_id=truth_id,
            concept=concept,
            created_at=created_at,
            **kwargs,
        )

    def as_dict(self):
        return asdict(self)


__all__ = [
    "TruthRecord",
    "new_truth_id",
    "utc_timestamp",
]
