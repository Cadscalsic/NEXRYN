"""Graduate committed truths into stable core knowledge levels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


GRADUATION_LEVELS = [
    "TRUTH_CANDIDATE",
    "TRUTH_COMMITTED",
    "STABLE_TRUTH",
    "FOUNDATIONAL_TRUTH",
    "CORE_KNOWLEDGE",
]


@dataclass(frozen=True)
class TruthGraduationThresholds:
    stable_commit_count: int = 1
    foundational_commit_count: int = 2
    core_commit_count: int = 3
    stable_score: float = 0.86
    foundational_score: float = 0.90
    core_score: float = 0.94
    max_contradiction_rate: float = 0.10


class TruthGraduationEngine:
    system_name = "truth_graduation_engine"

    def __init__(
        self,
        thresholds: TruthGraduationThresholds | None = None,
    ) -> None:
        self.thresholds = thresholds or TruthGraduationThresholds()

    def graduate(
        self,
        committed_truths: Iterable[Mapping[str, Any]] | None = None,
        reuse_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        reuse_report = reuse_report if isinstance(reuse_report, Mapping) else {}
        reuse_score = _score(
            reuse_report.get("truth_reuse_rate")
            or reuse_report.get("reuse_rate")
            or reuse_report.get("truth_hits", 0)
        )
        reuse_by_concept = {
            str(item.get("concept") or item.get("truth_name")): _score(
                item.get("truth_relevance")
                or item.get("truth_contribution_score")
                or reuse_score
            )
            for item in reuse_report.get("reused_truths", [])
            if isinstance(item, Mapping)
        }

        records = []
        for truth in committed_truths or []:
            if not isinstance(truth, Mapping):
                continue
            concept = str(truth.get("concept") or truth.get("truth_name") or "")
            if not concept:
                continue
            commit_count = _commit_count(truth)
            stability_score = _score(
                truth.get("cross_task_stability")
                or truth.get("stability_score")
                or truth.get("truth_confidence")
                or truth.get("commit_score")
            )
            contradiction_rate = _score(
                truth.get("contradiction_rate")
                or truth.get("contradiction_score")
                or 0.0
            )
            concept_reuse = max(reuse_score, reuse_by_concept.get(concept, 0.0))
            mastery_score = _mastery_score(
                truth=truth,
                stability_score=stability_score,
                reuse_score=concept_reuse,
                contradiction_rate=contradiction_rate,
            )
            level = self._level_for(
                commit_count=commit_count,
                mastery_score=mastery_score,
                stability_score=stability_score,
                reuse_score=concept_reuse,
                contradiction_rate=contradiction_rate,
            )
            records.append({
                "concept": concept,
                "truth_state": truth.get("truth_state", "TRUTH_COMMITTED"),
                "graduation_level": level,
                "truth_commit_count": commit_count,
                "mastery_score": mastery_score,
                "stability_score": stability_score,
                "reuse_score": concept_reuse,
                "contradiction_rate": contradiction_rate,
                "eligible_for_graduation": level not in {
                    "TRUTH_CANDIDATE",
                    "TRUTH_COMMITTED",
                },
                "truth_id": truth.get("truth_id"),
            })

        graduated = [
            item
            for item in records
            if item["graduation_level"] in {
                "STABLE_TRUTH",
                "FOUNDATIONAL_TRUTH",
                "CORE_KNOWLEDGE",
            }
        ]
        return {
            "system": self.system_name,
            "graduation_levels": list(GRADUATION_LEVELS),
            "truth_count": len(records),
            "graduated_concept_count": len(graduated),
            "graduated_concepts": [item["concept"] for item in graduated],
            "graduation_records": records,
        }

    def _level_for(
        self,
        commit_count: int,
        mastery_score: float,
        stability_score: float,
        reuse_score: float,
        contradiction_rate: float,
    ) -> str:
        if contradiction_rate > self.thresholds.max_contradiction_rate:
            return "TRUTH_COMMITTED"
        if (
            commit_count >= self.thresholds.core_commit_count
            and mastery_score >= self.thresholds.core_score
            and stability_score >= self.thresholds.core_score
            and reuse_score >= 0.75
        ):
            return "CORE_KNOWLEDGE"
        if (
            commit_count >= self.thresholds.foundational_commit_count
            and mastery_score >= self.thresholds.foundational_score
            and stability_score >= self.thresholds.foundational_score
        ):
            return "FOUNDATIONAL_TRUTH"
        if (
            commit_count >= self.thresholds.stable_commit_count
            and mastery_score >= self.thresholds.stable_score
            and stability_score >= self.thresholds.stable_score
        ):
            return "STABLE_TRUTH"
        return "TRUTH_COMMITTED"


def _mastery_score(
    truth: Mapping[str, Any],
    stability_score: float,
    reuse_score: float,
    contradiction_rate: float,
) -> float:
    confidence = _score(
        truth.get("truth_confidence")
        or truth.get("commit_score")
        or truth.get("promotion_score")
    )
    context = _score(
        truth.get("context_strength")
        or truth.get("contextual_truth_score")
        or confidence
    )
    contradiction_support = 1.0 - contradiction_rate
    return round(
        confidence * 0.35
        + stability_score * 0.30
        + context * 0.15
        + reuse_score * 0.10
        + contradiction_support * 0.10,
        4,
    )


def _commit_count(truth: Mapping[str, Any]) -> int:
    for key in ("truth_commit_count", "commit_count", "reuse_count"):
        value = truth.get(key)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            continue
    supporting_tasks = truth.get("supporting_tasks")
    if isinstance(supporting_tasks, list) and supporting_tasks:
        return max(1, len(set(map(str, supporting_tasks))))
    return 1


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "GRADUATION_LEVELS",
    "TruthGraduationEngine",
    "TruthGraduationThresholds",
]
