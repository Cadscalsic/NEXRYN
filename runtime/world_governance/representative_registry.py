"""Registry of existing cognitive systems acting as parliament representatives."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class CognitiveRepresentative:
    name: str
    domain: str
    authority_weight: float
    diversity_weight: float
    trust_score: float
    voting_enabled: bool
    constitutional_exempt: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


class RepresentativeRegistry:
    def __init__(self):
        self._representatives: dict[str, CognitiveRepresentative] = {}
        self.register_defaults()

    def register(self, representative: CognitiveRepresentative) -> CognitiveRepresentative:
        self._representatives[representative.name] = representative
        return representative

    def register_defaults(self) -> None:
        self._representatives.clear()
        defaults = (
            CognitiveRepresentative("Object-Centric Reasoning", "reasoning", 0.78, 0.82, 0.82, True),
            CognitiveRepresentative("Transformation Salience", "reasoning", 0.72, 0.76, 0.78, True),
            CognitiveRepresentative("Strategy Memory", "strategy", 0.76, 0.60, 0.84, True),
            CognitiveRepresentative("Program Memory", "program", 0.74, 0.58, 0.80, True),
            CognitiveRepresentative("Context Engine", "context", 0.73, 0.86, 0.81, True),
            CognitiveRepresentative("World Model", "world_model", 0.82, 0.70, 0.86, True),
            CognitiveRepresentative("Meta Supervisor", "meta", 0.80, 0.66, 0.84, True),
            CognitiveRepresentative("Resource Governor", "resource", 0.77, 0.52, 0.83, True),
            CognitiveRepresentative("Truth Governance", "truth", 0.92, 0.50, 0.94, True),
            CognitiveRepresentative("Learning Saturation Controller", "learning", 0.70, 0.62, 0.78, True),
            CognitiveRepresentative("Security Layer", "security", 0.94, 0.45, 0.95, True),
            CognitiveRepresentative("Self Repair", "self_repair", 0.72, 0.64, 0.79, True),
            CognitiveRepresentative("Identity Governance", "identity", 0.93, 0.55, 0.94, True),
        )
        for representative in defaults:
            self.register(representative)

    def voting_representatives(self) -> list[CognitiveRepresentative]:
        return [
            representative
            for representative in self._representatives.values()
            if representative.voting_enabled
            and not representative.constitutional_exempt
        ]

    def all(self) -> list[CognitiveRepresentative]:
        return list(self._representatives.values())

    def as_report(self) -> list[dict]:
        return [representative.as_dict() for representative in self.all()]


representative_registry = RepresentativeRegistry()


__all__ = [
    "CognitiveRepresentative",
    "RepresentativeRegistry",
    "representative_registry",
]
