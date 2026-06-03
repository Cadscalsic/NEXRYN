from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


def clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = minimum
    return round(max(minimum, min(value, maximum)), 4)


def utcnow():
    return datetime.utcnow()


class TrialResult(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


class BeliefState(str, Enum):
    CANDIDATE = "CANDIDATE"
    PROBATION = "PROBATION"
    SUPPORTED = "SUPPORTED"
    VALIDATED = "VALIDATED"
    TRUTH_CANDIDATE = "TRUTH_CANDIDATE"
    ESTABLISHED = "ESTABLISHED"
    TRUTH_COMMITTED = "TRUTH_COMMITTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


@dataclass
class Evidence:
    concept: str
    source: str
    support_score: float = 0.0
    contradiction_score: float = 0.0
    reliability: float = 0.5
    causal_alignment: float = 0.5
    semantic_consistency: float = 0.5
    observed_at: datetime = field(default_factory=utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.support_score = clamp(self.support_score)
        self.contradiction_score = clamp(self.contradiction_score)
        self.reliability = clamp(self.reliability)
        self.causal_alignment = clamp(self.causal_alignment)
        self.semantic_consistency = clamp(self.semantic_consistency)
        if isinstance(self.observed_at, str):
            self.observed_at = datetime.fromisoformat(self.observed_at)

    def as_dict(self):
        report = asdict(self)
        report["observed_at"] = self.observed_at.isoformat()
        return report


@dataclass
class Hypothesis:
    concept: str
    claim: str = ""
    prior_confidence: float = 0.5
    semantic_consistency: float = 0.5
    causal_alignment: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.claim = self.claim or self.concept
        self.prior_confidence = clamp(self.prior_confidence)
        self.semantic_consistency = clamp(self.semantic_consistency)
        self.causal_alignment = clamp(self.causal_alignment)


@dataclass
class EvidenceAggregate:
    concept: str
    evidence_count: int = 0
    support_score: float = 0.0
    contradiction_score: float = 0.0
    evidence_strength: float = 0.0
    semantic_consistency: float = 0.0
    causal_alignment: float = 0.0
    historical_reliability: float = 0.0
    effective_weight: float = 0.0

    def as_dict(self):
        return asdict(self)


@dataclass
class EpistemicTrial:
    concept: str
    support_score: float
    contradiction_score: float
    evidence_strength: float
    semantic_consistency: float
    causal_alignment: float
    trial_result: TrialResult
    evidence_count: int
    trial_number: int
    timestamp: datetime = field(default_factory=utcnow)

    def as_dict(self):
        report = asdict(self)
        report["trial_result"] = self.trial_result.value
        report["timestamp"] = self.timestamp.isoformat()
        return report


@dataclass
class Belief:
    concept: str
    claim: str
    state: BeliefState = BeliefState.CANDIDATE
    confidence: float = 0.0
    evidence_strength: float = 0.0
    contradiction_score: float = 0.0
    trial_count: int = 0
    updated_at: datetime = field(default_factory=utcnow)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self):
        report = asdict(self)
        report["state"] = self.state.value
        report["updated_at"] = self.updated_at.isoformat()
        return report


@dataclass
class TruthCommit:
    concept: str
    decision: str
    committed: bool
    reasons: List[str]
    belief_state: BeliefState
    evidence_strength: float
    calibrated_confidence: float
    contradiction_score: float
    trial_count: int
    constitutional_invariants: Dict[str, bool]
    timestamp: datetime = field(default_factory=utcnow)
    metadata: Optional[Dict[str, Any]] = None

    def as_dict(self):
        report = asdict(self)
        report["belief_state"] = self.belief_state.value
        report["timestamp"] = self.timestamp.isoformat()
        return report
