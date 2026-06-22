"""Strict minimal evaluation result."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvaluationResult:
    accuracy: float
    success_state: str
    difference_count: int
    confidence: float
    episode_completed: bool
    retry_allowed: bool
    shutdown_mode: str
    evaluation_duration: float
