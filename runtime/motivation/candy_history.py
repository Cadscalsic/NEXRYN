"""Candy event history and trend tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CandyEvent:
    timestamp: str
    task_id: str | None
    reward_assets: dict[str, float]
    penalty_score: float
    resulting_balances: dict[str, float]
    reward_hacking_risk: float = 0.0


@dataclass
class CandyHistory:
    events: list[CandyEvent] = field(default_factory=list)
    max_events: int = 200

    def append(
        self,
        reward_assets: dict[str, float],
        penalty_score: float,
        resulting_balances: dict[str, float],
        task_id: str | None = None,
        reward_hacking_risk: float = 0.0,
    ) -> CandyEvent:
        event = CandyEvent(
            timestamp=str(datetime.utcnow()),
            task_id=task_id,
            reward_assets=dict(reward_assets),
            penalty_score=float(penalty_score),
            resulting_balances=dict(resulting_balances),
            reward_hacking_risk=float(reward_hacking_risk),
        )
        self.events.append(event)
        self.events = self.events[-self.max_events:]
        return event

    def trends(self) -> dict[str, float]:
        if len(self.events) < 2:
            return {}
        previous = self.events[-2].resulting_balances
        current = self.events[-1].resulting_balances
        return {
            key: round(current.get(key, 0.0) - previous.get(key, 0.0), 4)
            for key in current
        }

    def instability(self) -> float:
        if len(self.events) < 3:
            return 0.0
        recent = self.events[-5:]
        penalties = [event.penalty_score + event.reward_hacking_risk for event in recent]
        return round(min(sum(penalties) / len(penalties), 1.0), 4)

    def hacking_patterns(self) -> dict[str, Any]:
        recent = self.events[-10:]
        count = sum(1 for event in recent if event.reward_hacking_risk > 0.0)
        return {
            "recent_reward_hacking_events": count,
            "reward_instability": self.instability(),
        }


__all__ = [
    "CandyEvent",
    "CandyHistory",
]
