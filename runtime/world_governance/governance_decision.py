"""Decision objects for the inner world governance kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


WORLD_GOVERNANCE_DECISIONS: tuple[str, ...] = (
    "ADMIT",
    "ADMIT_WITH_LIMITS",
    "QUARANTINE",
    "REJECT",
    "REQUIRE_MORE_EVIDENCE",
    "PROTECT_CORE",
)


@dataclass
class WorldGovernanceDecision:
    candidate_name: str
    candidate_type: str
    decision: str
    admission_level: str
    reason: str
    evolution_value: float
    identity_risk: float
    truth_risk: float
    governance_risk: float
    requires_review: bool
    allowed_actions: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.decision in {"ADMIT", "ADMIT_WITH_LIMITS"}

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["allowed"] = self.allowed
        return payload


__all__ = [
    "WORLD_GOVERNANCE_DECISIONS",
    "WorldGovernanceDecision",
]
