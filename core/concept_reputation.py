"""
Concept Reputation Engine: Tracks reputation based on survival, utility, and stability.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import math


@dataclass
class ReputationMetrics:
    """Metrics used to compute reputation score."""
    survival_duration_hours: float = 0.0  # How long has this concept survived?
    contradiction_count: int = 0  # How many contradictions did it encounter?
    utility_recurrence: float = 0.0  # How often is it used (0-1)?
    causal_stability: float = 1.0  # How stable are its causal relationships (0-1)?
    merge_success_rate: float = 0.0  # % of merges that succeeded
    last_used_hours_ago: float = float("inf")  # Recency of last use


class ConceptReputationEngine:
    """
    Computes and tracks concept reputation based on:
    - Survival duration
    - Contradiction count
    - Utility recurrence
    - Causal stability
    """

    def __init__(self):
        self._reputation_scores: Dict[str, float] = {}
        self._metrics: Dict[str, ReputationMetrics] = {}
        self._created_times: Dict[str, datetime] = {}

    def register_concept(self, concept_id: str) -> None:
        """Register a new concept with initial reputation."""
        self._created_times[concept_id] = datetime.utcnow()
        self._metrics[concept_id] = ReputationMetrics()
        self._reputation_scores[concept_id] = 0.5  # Start at neutral

    def record_contradiction(self, concept_id: str) -> None:
        """Penalize a concept for a contradiction."""
        if concept_id not in self._metrics:
            return
        self._metrics[concept_id].contradiction_count += 1

    def record_usage(self, concept_id: str, utility: float = 0.05) -> None:
        """Record a usage event, incrementing utility."""
        if concept_id not in self._metrics:
            return
        # Decay old utility, add new
        self._metrics[concept_id].utility_recurrence = min(
            1.0,
            self._metrics[concept_id].utility_recurrence * 0.95 + utility,
        )
        self._metrics[concept_id].last_used_hours_ago = 0.0

    def record_merge_attempt(self, concept_id: str, success: bool) -> None:
        """Record a merge attempt."""
        if concept_id not in self._metrics:
            return
        metrics = self._metrics[concept_id]
        total = 1.0  # Incremental count
        current_rate = metrics.merge_success_rate or 0.0
        metrics.merge_success_rate = (current_rate + (1.0 if success else 0.0)) / (
            current_rate + total
        )

    def set_causal_stability(self, concept_id: str, stability: float) -> None:
        """Set causal stability (0-1)."""
        if concept_id not in self._metrics:
            return
        self._metrics[concept_id].causal_stability = max(0.0, min(1.0, stability))

    def compute_reputation(self, concept_id: str) -> float:
        """
        Compute overall reputation score (0-1).
        Formula: weighted average of survival, utility, stability, minus contradiction penalty.
        """
        if concept_id not in self._metrics:
            return 0.0

        metrics = self._metrics[concept_id]

        # Survival component (0-1): logarithmic growth
        survival_hours = (
            datetime.utcnow() - self._created_times[concept_id]
        ).total_seconds() / 3600
        survival_score = min(1.0, math.log(1 + survival_hours) / 10.0)

        # Utility component (0-1): direct
        utility_score = metrics.utility_recurrence

        # Stability component (0-1): direct
        stability_score = metrics.causal_stability

        # Merge success component (0-1): direct
        merge_score = metrics.merge_success_rate

        # Contradiction penalty: each contradiction reduces by 0.05
        contradiction_penalty = max(0.0, 1.0 - metrics.contradiction_count * 0.05)

        # Recency bonus: concepts used recently get a slight boost
        if metrics.last_used_hours_ago < 1.0:
            recency_bonus = 1.0
        else:
            recency_bonus = 0.0

        # Keep a neutral baseline for newly registered concepts. Positive
        # evidence then raises reputation instead of replacing that baseline.
        reputation = (
            0.35
            + 0.10 * survival_score
            + 0.25 * utility_score
            + 0.15 * stability_score
            + 0.05 * merge_score
            + 0.10 * recency_bonus
        ) * contradiction_penalty

        # Clamp to [0, 1]
        reputation = max(0.0, min(1.0, reputation))

        self._reputation_scores[concept_id] = reputation
        return reputation

    def get_reputation(self, concept_id: str) -> float:
        """Get cached reputation score."""
        return self._reputation_scores.get(concept_id, 0.0)

    def get_metrics(self, concept_id: str) -> Optional[ReputationMetrics]:
        """Get underlying metrics for a concept."""
        return self._metrics.get(concept_id)

    def rank_concepts_by_reputation(self) -> list[tuple[str, float]]:
        """Return concepts sorted by reputation (highest first)."""
        return sorted(
            [
                (cid, self.compute_reputation(cid))
                for cid in self._metrics.keys()
            ],
            key=lambda x: x[1],
            reverse=True,
        )

    def export_report(self) -> Dict[str, Any]:
        """Export reputation engine state."""
        return {
            "total_concepts": len(self._metrics),
            "average_reputation": (
                sum(self._reputation_scores.values()) / len(self._reputation_scores)
                if self._reputation_scores
                else 0.0
            ),
            "top_concepts": [
                {"id": cid, "reputation": rep}
                for cid, rep in self.rank_concepts_by_reputation()[:10]
            ],
        }


__all__ = ["ReputationMetrics", "ConceptReputationEngine"]
