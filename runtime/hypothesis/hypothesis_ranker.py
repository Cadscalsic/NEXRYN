"""Ranking for validated cognitive hypotheses."""

from __future__ import annotations

from typing import Any, Mapping


class HypothesisRanker:
    """Rank hypotheses without running an arena or executing programs."""

    system_name = "hypothesis_ranker"

    WEIGHTS = {
        "truth_support": 0.20,
        "dependency_support": 0.16,
        "context_support": 0.16,
        "identity_confidence": 0.16,
        "semantic_confidence": 0.17,
        "execution_confidence": 0.15,
    }

    def rank(
        self,
        hypotheses: list[Mapping[str, Any]],
        validation_report: Mapping[str, Any] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        validation_report = validation_report if isinstance(validation_report, Mapping) else {}
        validations = {
            item.get("hypothesis_id"): item
            for item in validation_report.get("validated_hypotheses", []) or []
            if isinstance(item, Mapping)
        }
        ranking_scores = {}
        ranked = []
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, Mapping):
                continue
            hypothesis_id = hypothesis.get("hypothesis_id")
            validation = validations.get(hypothesis_id, {})
            score = self._score_hypothesis(hypothesis, validation)
            ranking_scores[hypothesis_id] = score
            row = dict(hypothesis)
            row["ranking_score"] = score
            row["validation_passed"] = validation.get("validation_passed", True)
            ranked.append(row)
        ranked.sort(
            key=lambda item: (
                bool(item.get("validation_passed")),
                item.get("ranking_score", 0.0),
                item.get("confidence", 0.0),
                str(item.get("hypothesis_id")),
            ),
            reverse=True,
        )
        best = [item for item in ranked if item.get("validation_passed")][:limit]
        return {
            "system": self.system_name,
            "hypothesis_ranking_operational": True,
            "best_candidates": best,
            "ranked_hypotheses": ranked,
            "ranking_scores": ranking_scores,
            "ranking_count": len(ranked),
        }

    def _score_hypothesis(self, hypothesis: Mapping[str, Any], validation: Mapping[str, Any]) -> float:
        validation_factor = _score(validation.get("validation_score", 1.0))
        semantic_confidence = _score(
            hypothesis.get("semantic_confidence")
            or hypothesis.get("semantic_support")
            or hypothesis.get("confidence")
        )
        execution_confidence = _score(
            hypothesis.get("execution_confidence")
            or hypothesis.get("confidence")
            if hypothesis.get("execution_ready")
            else 0.0
        )
        values = {
            "truth_support": _score(hypothesis.get("truth_support", hypothesis.get("confidence", 0.0))),
            "dependency_support": _score(hypothesis.get("dependency_support", hypothesis.get("confidence", 0.0))),
            "context_support": _score(hypothesis.get("context_support", 0.0)),
            "identity_confidence": _score(hypothesis.get("identity_confidence", hypothesis.get("confidence", 0.0))),
            "semantic_confidence": semantic_confidence,
            "execution_confidence": execution_confidence,
        }
        weighted = sum(values[key] * self.WEIGHTS[key] for key in self.WEIGHTS)
        return round(weighted * validation_factor, 4)


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


hypothesis_ranker = HypothesisRanker()

__all__ = ["HypothesisRanker", "hypothesis_ranker"]
