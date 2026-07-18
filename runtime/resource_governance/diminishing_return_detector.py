"""Diminishing return detection for bounded adaptive execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DiminishingReturnState(str, Enum):
    VALUE_INCREASING = "VALUE_INCREASING"
    VALUE_STABLE = "VALUE_STABLE"
    DIMINISHING_RETURNS = "DIMINISHING_RETURNS"
    NO_VALUE = "NO_VALUE"
    NEGATIVE_VALUE = "NEGATIVE_VALUE"


@dataclass
class DiminishingReturnDetector:
    history: list[dict[str, Any]] = field(default_factory=list)
    current_state: DiminishingReturnState = DiminishingReturnState.VALUE_STABLE

    def evaluate(self, evidence: dict[str, Any]) -> DiminishingReturnState:
        self.history.append(dict(evidence))
        if evidence.get("negative_value"):
            self.current_state = DiminishingReturnState.NEGATIVE_VALUE
        elif evidence.get("no_value") or evidence.get("no_new_concepts") or evidence.get("duplicate_candidates") or evidence.get("unchanged_residual"):
            recent_no_value = sum(1 for item in self.history[-3:] if item.get("no_value") or item.get("duplicate_candidates") or item.get("unchanged_residual"))
            self.current_state = DiminishingReturnState.NO_VALUE if recent_no_value >= 3 else DiminishingReturnState.DIMINISHING_RETURNS
        elif evidence.get("confidence_delta", 0.0) > 0 or evidence.get("residual_delta", 0.0) > 0:
            self.current_state = DiminishingReturnState.VALUE_INCREASING
        elif len(self.history) >= 2:
            self.current_state = DiminishingReturnState.VALUE_STABLE
        return self.current_state


__all__ = ["DiminishingReturnDetector", "DiminishingReturnState"]
