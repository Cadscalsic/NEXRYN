from dataclasses import asdict, dataclass, field
from datetime import datetime

from core.epistemic_models import clamp


VALID_NODE_TYPES = {
    "concept",
    "truth",
    "contextual_truth",
    "event",
    "transformation",
    "context",
    "observation",
    "evidence",
    "contradiction",
    "implication",
    "evidence_event",
    "outcome",
}


@dataclass
class CausalNode:
    node_id: str
    node_type: str
    name: str
    confidence: float = 0.0
    support_score: float = 0.0
    contradiction_score: float = 0.0
    metadata: dict = field(default_factory=dict)
    evidence_count: int = 0
    timestamp: str = ""

    def __post_init__(self):
        self.node_id = str(self.node_id or self.name).strip()
        self.node_type = str(self.node_type or "concept").strip()
        self.name = str(self.name or self.node_id).strip()
        if self.node_type not in VALID_NODE_TYPES:
            raise ValueError(f"invalid causal node type: {self.node_type}")
        self.confidence = clamp(self.confidence)
        self.support_score = clamp(self.support_score)
        self.contradiction_score = clamp(self.contradiction_score)
        self.metadata = dict(self.metadata or {})
        self.evidence_count = max(int(self.evidence_count or 0), 0)
        self.timestamp = self.timestamp or datetime.utcnow().isoformat()

    def merge(self, other):
        self.confidence = max(self.confidence, clamp(other.confidence))
        self.support_score = max(
            self.support_score,
            clamp(other.support_score),
        )
        self.contradiction_score = max(
            self.contradiction_score,
            clamp(other.contradiction_score),
        )
        self.evidence_count += max(int(other.evidence_count or 0), 0)
        self.metadata.update(dict(other.metadata or {}))
        return self

    def as_dict(self):
        return asdict(self)


__all__ = [
    "CausalNode",
    "VALID_NODE_TYPES",
]
