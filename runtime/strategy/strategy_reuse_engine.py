"""Reuse solution strategies derived from committed truths."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class StrategyReuseEngine:
    system_name = "strategy_reuse_engine"

    def evaluate(
        self,
        truths: Iterable[Mapping[str, Any]] | None = None,
        hypotheses: Iterable[Mapping[str, Any]] | None = None,
        stored_strategies: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        truths_by_concept = {
            concept: dict(truth)
            for truth in truths or []
            if isinstance(truth, Mapping)
            for concept in [self._concept(truth)]
            if concept
        }
        hypotheses_by_concept = {
            concept: dict(hypothesis)
            for hypothesis in hypotheses or []
            if isinstance(hypothesis, Mapping)
            for concept in [self._concept(hypothesis)]
            if concept
        }
        stored_by_concept = {
            concept: dict(strategy)
            for strategy in stored_strategies or []
            if isinstance(strategy, Mapping)
            for concept in [self._concept(strategy)]
            if concept
        }

        reused = []
        misses = []
        for concept, truth in truths_by_concept.items():
            hypothesis = hypotheses_by_concept.get(concept, {})
            stored = stored_by_concept.get(concept, {})
            confidence = max(
                self._score(truth.get("truth_confidence")),
                self._score(truth.get("commit_score")),
                self._score(hypothesis.get("confidence")),
                self._score(stored.get("confidence")),
                self._score(stored.get("success_rate")),
            )
            if confidence >= 0.86:
                reused.append({
                    "strategy_id": (
                        stored.get("strategy_id")
                        or f"strategy:{concept}:truth_guided_reuse"
                    ),
                    "concept": concept,
                    "strategy_type": (
                        stored.get("strategy_type")
                        or stored.get("type")
                        or "truth_guided_solution_method"
                    ),
                    "source_truth": truth.get("truth_id") or concept,
                    "source_hypothesis": hypothesis.get("hypothesis_id"),
                    "reuse_score": round(confidence, 4),
                    "reuse_state": "STRATEGY_REUSED",
                    "method": (
                        f"reuse committed {concept} as a solving constraint "
                        "before generating a new search path"
                    ),
                })
            else:
                misses.append({
                    "concept": concept,
                    "reason": "strategy_confidence_below_reuse_floor",
                    "reuse_score": round(confidence, 4),
                })

        hit_count = len(reused)
        miss_count = len(misses)
        return {
            "system": self.system_name,
            "report_state": "final",
            "strategy_hits": hit_count,
            "strategy_misses": miss_count,
            "strategy_reuse_rate": round(
                hit_count / max(hit_count + miss_count, 1),
                4,
            ),
            "reused_strategies": reused,
            "missed_strategies": misses,
            "strategy_reuse_available": bool(reused),
            "reason": (
                "truth_commits_converted_to_reusable_solution_methods"
                if reused
                else "no_truth_backed_strategy_reuse_available"
            ),
        }

    def _concept(self, item: Mapping[str, Any]) -> str:
        return str(
            item.get("concept")
            or item.get("truth_name")
            or item.get("source_truth")
            or item.get("name")
            or ""
        )

    def _score(self, value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


strategy_reuse_engine = StrategyReuseEngine()


__all__ = ["StrategyReuseEngine", "strategy_reuse_engine"]
