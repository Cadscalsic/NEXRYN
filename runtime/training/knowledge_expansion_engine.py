"""Score whether a training batch expands knowledge instead of repeating it."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.training.curriculum_engine import FRONTIER_CONCEPTS


class KnowledgeExpansionEngine:
    system_name = "knowledge_expansion_engine"

    def score(
        self,
        concept_reports: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        reports = [
            dict(item)
            for item in concept_reports or []
            if isinstance(item, Mapping)
        ]
        if not reports:
            return {
                "system": self.system_name,
                "knowledge_expansion_score": 0.0,
                "novel_concepts_discovered": [],
                "frontier_concepts_explored": [],
                "rare_concepts": [],
                "overtrained_concepts": [],
            }
        novel = [
            item["concept"]
            for item in reports
            if item.get("novelty_score", 0.0) >= 0.65
        ]
        frontier = [
            item["concept"]
            for item in reports
            if item.get("concept") in FRONTIER_CONCEPTS
            or item.get("curriculum_stage") == "FRONTIER"
        ]
        rare = [
            item["concept"]
            for item in reports
            if item.get("coverage_ratio", 1.0) < 0.5
        ]
        overtrained = [
            item["concept"]
            for item in reports
            if item.get("overtrained", False)
        ]
        total = max(len(reports), 1)
        score = (
            len(set(novel)) / total * 0.35
            + len(set(frontier)) / total * 0.35
            + len(set(rare)) / total * 0.20
            + (1.0 - len(set(overtrained)) / total) * 0.10
        )
        return {
            "system": self.system_name,
            "knowledge_expansion_score": round(min(1.0, score), 4),
            "novel_concepts_discovered": sorted(set(novel)),
            "frontier_concepts_explored": sorted(set(frontier)),
            "rare_concepts": sorted(set(rare)),
            "overtrained_concepts": sorted(set(overtrained)),
        }


__all__ = ["KnowledgeExpansionEngine"]
