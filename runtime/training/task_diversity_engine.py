"""Apply task and concept cooldowns before training batch selection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.training.curriculum_engine import CurriculumEngine
from runtime.training.knowledge_expansion_engine import KnowledgeExpansionEngine


class TaskDiversityEngine:
    system_name = "task_diversity_engine"

    def __init__(
        self,
        task_cooldown_window: int = 50,
        concept_cooldown_window: int = 50,
    ) -> None:
        self.task_cooldown_window = max(1, int(task_cooldown_window))
        self.concept_cooldown_window = max(1, int(concept_cooldown_window))
        self.curriculum_engine = CurriculumEngine()
        self.expansion_engine = KnowledgeExpansionEngine()

    def rerank(
        self,
        task_reports: Iterable[Mapping[str, Any]] | None = None,
        history: Iterable[Mapping[str, Any]] | None = None,
        core_knowledge: Iterable[Mapping[str, Any]] | None = None,
        concept_counts: Mapping[str, Any] | None = None,
        concept_states: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        reports = [
            dict(report)
            for report in task_reports or []
            if isinstance(report, Mapping)
        ]
        recent_tasks = self._recent_tasks(history)
        recent_concepts = self._recent_concepts(history)
        concept_counts = {
            str(concept): _int(count)
            for concept, count in (concept_counts or {}).items()
        }
        concept_states = {
            str(concept): str(state)
            for concept, state in (concept_states or {}).items()
        }
        core_records = {
            str(item.get("concept")): dict(item)
            for item in core_knowledge or []
            if isinstance(item, Mapping) and item.get("concept")
        }

        reranked = []
        concept_reports = {}
        cooldown_filtered_tasks = []
        cooldown_filtered_concepts = set()
        for report in reports:
            task_file = str(report.get("task_file") or "")
            target_concepts = [
                str(concept)
                for concept in report.get("target_concepts", [])
                if concept
            ]
            base_priority = _float(report.get("priority"))
            task_penalty = self._task_penalty(task_file, recent_tasks)
            concept_penalty = sum(
                self._concept_penalty(
                    concept,
                    recent_concepts=recent_concepts,
                    core_records=core_records,
                )
                for concept in target_concepts
            )
            novelty_bonus = sum(
                self._novelty_bonus(concept, concept_counts)
                for concept in target_concepts
            )
            frontier_bonus = sum(
                self._frontier_bonus(concept)
                for concept in target_concepts
            )
            diversity_priority = round(
                base_priority
                - task_penalty
                - concept_penalty
                + novelty_bonus
                + frontier_bonus,
                4,
            )
            if task_penalty:
                cooldown_filtered_tasks.append(task_file)
            for concept in target_concepts:
                if self._concept_penalty(
                    concept,
                    recent_concepts=recent_concepts,
                    core_records=core_records,
                ):
                    cooldown_filtered_concepts.add(concept)
                concept_report = concept_reports.setdefault(
                    concept,
                    self._concept_report(
                        concept,
                        concept_counts,
                        concept_states,
                        core_records,
                    ),
                )
                concept_report["task_count"] += 1
            reranked.append({
                **report,
                "base_priority": base_priority,
                "task_cooldown_penalty": round(task_penalty, 4),
                "concept_cooldown_penalty": round(concept_penalty, 4),
                "novelty_weight": round(novelty_bonus, 4),
                "frontier_weight": round(frontier_bonus, 4),
                "diversity_priority": diversity_priority,
            })

        reranked.sort(
            key=lambda item: (
                -item["diversity_priority"],
                -item.get("target_coverage_gap", 0),
                item.get("original_order", 0),
            )
        )
        concept_report_list = list(concept_reports.values())
        expansion_report = self.expansion_engine.score(concept_report_list)
        return {
            "system": self.system_name,
            "ranked_task_reports": reranked,
            "ranked_task_files": [item["task_file"] for item in reranked],
            "task_recent_history": sorted(recent_tasks),
            "concept_recent_usage": sorted(recent_concepts),
            "cooldown_filtered_tasks": sorted(set(cooldown_filtered_tasks)),
            "cooldown_filtered_concepts": sorted(cooldown_filtered_concepts),
            "cooldown_filtered_task_count": len(set(cooldown_filtered_tasks)),
            "cooldown_filtered_concept_count": len(cooldown_filtered_concepts),
            "task_diversity_score": self._diversity_score(
                [item.get("task_file") for item in reranked]
            ),
            "concept_diversity_score": self._diversity_score(
                [
                    concept
                    for item in reranked
                    for concept in item.get("target_concepts", [])
                ]
            ),
            "concept_reports": concept_report_list,
            **expansion_report,
        }

    def _recent_tasks(
        self,
        history: Iterable[Mapping[str, Any]] | None,
    ) -> set[str]:
        tasks = []
        for item in history or []:
            if not isinstance(item, Mapping):
                continue
            tasks.extend([
                Path(str(task)).name
                for task in item.get("task_files", [])
                if task
            ])
        return set(tasks[-self.task_cooldown_window:])

    def _recent_concepts(
        self,
        history: Iterable[Mapping[str, Any]] | None,
    ) -> set[str]:
        concepts = []
        for item in history or []:
            if not isinstance(item, Mapping):
                continue
            concepts.extend([
                str(concept)
                for concept in item.get("concepts", [])
                if concept
            ])
        return set(concepts[-self.concept_cooldown_window:])

    def _task_penalty(self, task_file: str, recent_tasks: set[str]) -> float:
        return 100.0 if Path(task_file).name in recent_tasks else 0.0

    def _concept_penalty(
        self,
        concept: str,
        recent_concepts: set[str],
        core_records: Mapping[str, Mapping[str, Any]],
    ) -> float:
        penalty = 0.0
        if concept in recent_concepts:
            penalty += 20.0
        core_record = core_records.get(concept, {})
        penalty += _float(core_record.get("training_dominance_penalty")) * 80.0
        return penalty

    def _novelty_bonus(
        self,
        concept: str,
        concept_counts: Mapping[str, int],
    ) -> float:
        count = concept_counts.get(concept, 0)
        if count <= 0:
            return 60.0
        if count < 5:
            return 30.0
        return 0.0

    def _frontier_bonus(self, concept: str) -> float:
        stage = self.curriculum_engine.assign_stage(concept)
        return 45.0 if stage == "FRONTIER" else 0.0

    def _concept_report(
        self,
        concept: str,
        concept_counts: Mapping[str, int],
        concept_states: Mapping[str, str],
        core_records: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        count = concept_counts.get(concept, 0)
        core_record = core_records.get(concept, {})
        mastery = _float(core_record.get("mastery_score"))
        stage = self.curriculum_engine.assign_stage(
            concept,
            concept_states.get(concept),
            mastery,
        )
        coverage_ratio = min(count / 10.0, 1.0)
        return {
            "concept": concept,
            "task_count": 0,
            "usage_count": count,
            "concept_state": concept_states.get(concept, "UNKNOWN"),
            "graduation_level": core_record.get("graduation_level"),
            "mastery_score": mastery,
            "curriculum_stage": stage,
            "coverage_ratio": round(coverage_ratio, 4),
            "novelty_score": round(1.0 - coverage_ratio, 4),
            "overtrained": bool(
                core_record
                and core_record.get("graduation_level")
                in {"FOUNDATIONAL_TRUTH", "CORE_KNOWLEDGE"}
            ),
        }

    def _diversity_score(self, values: Iterable[Any]) -> float:
        values = [str(value) for value in values if value]
        if not values:
            return 0.0
        return round(len(set(values)) / len(values), 4)


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = ["TaskDiversityEngine"]
