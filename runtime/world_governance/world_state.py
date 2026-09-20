"""State tracked by the NEXRYN inner world governance kernel."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.world_governance.constitutional_identity import (
    LOCKED_CORE_PRINCIPLE_NAMES,
)


ADMISSION_LEVELS: tuple[str, ...] = (
    "OUTSIDE_WORLD",
    "CANDIDATE",
    "OBSERVED_USEFUL",
    "TRUSTED_TOOL",
    "WORLD_CITIZEN",
    "IDENTITY_SUPPORTING_COMPONENT",
    "LOCKED_CORE",
)


@dataclass
class WorldState:
    locked_core_principles: tuple[str, ...] = LOCKED_CORE_PRINCIPLE_NAMES
    admitted_concepts: dict[str, str] = field(default_factory=dict)
    admitted_contexts: dict[str, str] = field(default_factory=dict)
    admitted_strategies: dict[str, str] = field(default_factory=dict)
    quarantined_candidates: list[dict] = field(default_factory=list)
    rejected_candidates: list[dict] = field(default_factory=list)
    evolution_history: list[dict] = field(default_factory=list)

    def record_decision(self, decision) -> dict:
        report = (
            decision.as_dict()
            if hasattr(decision, "as_dict")
            else dict(decision)
        )
        self.evolution_history.append(report)

        name = report.get("candidate_name")
        candidate_type = report.get("candidate_type")
        level = report.get("admission_level")
        decision_name = report.get("decision")

        if not name:
            return report

        if decision_name in {"QUARANTINE", "PROTECT_CORE"}:
            self.quarantined_candidates.append(report)
            return report

        if decision_name == "REJECT":
            self.rejected_candidates.append(report)
            return report

        if decision_name in {"ADMIT", "ADMIT_WITH_LIMITS"}:
            if candidate_type == "concept":
                self.admitted_concepts[name] = level
            elif candidate_type == "context":
                self.admitted_contexts[name] = level
            elif candidate_type in {"strategy", "program"}:
                self.admitted_strategies[name] = level

        return report

    def as_report(self) -> dict:
        return {
            "locked_core_principles": list(self.locked_core_principles),
            "admitted_concepts": dict(self.admitted_concepts),
            "admitted_contexts": dict(self.admitted_contexts),
            "admitted_strategies": dict(self.admitted_strategies),
            "quarantined_candidates": list(self.quarantined_candidates[-100:]),
            "rejected_candidates": list(self.rejected_candidates[-100:]),
            "evolution_history": list(self.evolution_history[-200:]),
        }


__all__ = [
    "ADMISSION_LEVELS",
    "WorldState",
]
