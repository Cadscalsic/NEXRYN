"""Source dominance detection for cognitive candidate competition."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


class SourceDominanceGuard:
    """Prevent source identity from acting as winner evidence."""

    system_name = "source_dominance_guard"

    def review(
        self,
        candidates: list[Mapping[str, Any]] | None,
        scores: list[Mapping[str, Any]] | None = None,
        winner: Mapping[str, Any] | None = None,
        expected_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        candidates = [dict(item) for item in candidates or [] if isinstance(item, Mapping)]
        scores = [dict(item) for item in scores or [] if isinstance(item, Mapping)]
        distribution = Counter(
            source
            for candidate in candidates
            for source in candidate.get("sources", [candidate.get("source")])
            if source
        )
        source_count = len(distribution)
        total = sum(distribution.values())
        dominant_source = distribution.most_common(1)[0][0] if distribution else None
        diversity = round(source_count / max(total, 1), 4)
        reasons = []
        if source_count <= 1 and candidates:
            reasons.append("single_source_candidate_pool")
        winner_source = None
        if isinstance(winner, Mapping):
            winner_source = winner.get("source")
            if winner_source == "adaptive_reuse" and source_count <= 1:
                reasons.append("adaptive_reuse_without_meaningful_competition")
        if self._score_inflation(scores):
            reasons.append("source_specific_score_inflation")
        missing = sorted(set(expected_sources or []) - set(distribution))
        if missing:
            reasons.append("missing_candidate_sources")
        dominance = bool(reasons)
        return {
            "system": self.system_name,
            "dominance_detected": dominance,
            "dominant_source": dominant_source if dominance else None,
            "source_distribution": dict(distribution),
            "competition_diversity": diversity,
            "dominance_reasons": reasons,
            "missing_candidate_sources": missing,
            "corrective_action": (
                "require_quality_based_selection_or_report_single_source_only"
                if dominance else None
            ),
        }

    def _score_inflation(self, scores: list[Mapping[str, Any]]) -> bool:
        by_source: dict[str, list[float]] = {}
        for score in scores:
            source = score.get("source")
            if not source:
                continue
            by_source.setdefault(source, []).append(float(score.get("final_score", 0.0) or 0.0))
        if len(by_source) < 2:
            return False
        averages = [sum(values) / max(len(values), 1) for values in by_source.values()]
        return max(averages) - min(averages) > 0.35


source_dominance_guard = SourceDominanceGuard()

__all__ = ["SourceDominanceGuard", "source_dominance_guard"]
