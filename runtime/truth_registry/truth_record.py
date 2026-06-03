from dataclasses import asdict, dataclass, field
from datetime import datetime
from uuid import uuid4


def utc_timestamp():
    return datetime.utcnow().isoformat()


def new_truth_id():
    return f"truth:{uuid4().hex}"


@dataclass
class TruthRecord:
    truth_id: str
    concept: str
    claim: str
    status: str
    evidence_strength: float
    calibrated_confidence: float
    contradiction_score: float
    causal_alignment: float
    trial_count: int
    creation_time: str
    reviewed_at: str
    commit_timestamp: str = ""
    lineage: dict = field(default_factory=dict)
    evidence: list = field(default_factory=list)
    causal_history: list = field(default_factory=list)
    generalization_score: float = 0.0
    identity_impact: dict = field(default_factory=dict)
    parent_truths: list = field(default_factory=list)
    evidence_sources: list = field(default_factory=list)
    verification_history: list = field(default_factory=list)
    revision: int = 1
    reusable: bool = True
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(cls, **kwargs):
        timestamp = kwargs.pop("creation_time", utc_timestamp())
        return cls(
            truth_id=kwargs.pop("truth_id", new_truth_id()),
            creation_time=timestamp,
            reviewed_at=kwargs.pop("reviewed_at", timestamp),
            **kwargs,
        )

    def as_dict(self):
        return asdict(self)
