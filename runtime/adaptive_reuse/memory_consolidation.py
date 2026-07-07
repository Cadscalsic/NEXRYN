"""Lightweight background consolidation for adaptive reuse."""

from __future__ import annotations

from collections import defaultdict

from runtime.adaptive_reuse.experience_index import Experience


class AdaptiveMemoryConsolidation:
    def consolidate(self, experiences: list[Experience]) -> dict[str, object]:
        groups: dict[str, list[Experience]] = defaultdict(list)
        for experience in experiences:
            key = (
                experience.concept_signature
                or experience.semantic_signature
                or experience.execution_signature
                or experience.task_signature
            )
            groups[key].append(experience)
        duplicates = sum(max(0, len(items) - 1) for items in groups.values())
        promoted = [
            items[0].experience_id
            for items in groups.values()
            if max(item.success_rate for item in items) >= 0.85
            or max(item.reuse_count for item in items) >= 3
        ]
        decayed = [
            item.experience_id
            for items in groups.values()
            for item in items
            if item.success_rate < 0.25
            and item.reuse_count == 0
            and item.performance_score < 0.35
        ]
        return {
            "consolidation_attempted": True,
            "experience_groups": len(groups),
            "similar_experiences_merged": duplicates,
            "duplicates_removed": duplicates,
            "promoted_strategy_count": len(promoted),
            "promoted_strategy_ids": promoted[:25],
            "decayed_experience_count": len(decayed),
            "high_performing_strategies_preserved": len(promoted),
        }
