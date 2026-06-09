from dataclasses import asdict, dataclass, field
from datetime import datetime

from core.epistemic_models import clamp


VALID_RELATION_TYPES = {
    "supports",
    "contradicts",
    "enables",
    "depends_on",
    "causes",
    "explains",
    "invalidates",
    "context_requires",
    "context_strengthens",
    "context_weakens",
    "implies",
}


@dataclass
class CausalEdge:
    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    confidence: float = 0.0
    evidence: list = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        self.source = str(self.source).strip()
        self.target = str(self.target).strip()
        self.relation_type = str(self.relation_type or "supports").strip()
        if self.relation_type not in VALID_RELATION_TYPES:
            raise ValueError(
                f"invalid causal relation type: {self.relation_type}"
            )
        self.weight = clamp(self.weight)
        self.confidence = clamp(self.confidence)
        self.evidence = list(self.evidence or [])
        self.timestamp = self.timestamp or datetime.utcnow().isoformat()

    def merge(self, other):
        self.weight = max(self.weight, clamp(other.weight))
        self.confidence = max(self.confidence, clamp(other.confidence))
        for item in other.evidence:
            if item not in self.evidence:
                self.evidence.append(item)
        return self

    def as_dict(self):
        return asdict(self)


__all__ = [
    "CausalEdge",
    "VALID_RELATION_TYPES",
]
