"""Track counterfactual reuse and success against committed truths."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class CounterfactualReuseEngine:
    system_name = "counterfactual_reuse_engine"

    def evaluate(
        self,
        counterfactuals: Iterable[Mapping[str, Any]] | None = None,
        truths: Iterable[Mapping[str, Any]] | None = None,
        hypotheses: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        truth_concepts = {
            self._concept(truth)
            for truth in truths or []
            if isinstance(truth, Mapping)
        }
        hypothesis_concepts = {
            self._concept(hypothesis)
            for hypothesis in hypotheses or []
            if isinstance(hypothesis, Mapping)
            and hypothesis.get("status") == "ACCEPTED_HYPOTHESIS"
        }
        supported_concepts = {
            concept
            for concept in truth_concepts | hypothesis_concepts
            if concept
        }

        reused = []
        misses = []
        successes = []
        for item in counterfactuals or []:
            if not isinstance(item, Mapping):
                continue
            concept = self._concept(item)
            robustness = self._score(item.get("counterfactual_robustness"))
            if concept in supported_concepts:
                reused_item = {
                    **dict(item),
                    "counterfactual_reuse_state": "COUNTERFACTUAL_REUSED",
                    "reuse_score": robustness,
                    "learned_from": "committed_truth_and_accepted_hypothesis",
                }
                reused.append(reused_item)
                if robustness >= 0.86:
                    successes.append({
                        "counterfactual_id": item.get("counterfactual_id"),
                        "concept": concept,
                        "success_score": robustness,
                        "success_state": "COUNTERFACTUAL_SUCCESS",
                    })
            else:
                misses.append({
                    "counterfactual_id": item.get("counterfactual_id"),
                    "concept": concept,
                    "reason": "no_matching_truth_or_accepted_hypothesis",
                })

        hit_count = len(reused)
        miss_count = len(misses)
        success_count = len(successes)
        return {
            "system": self.system_name,
            "report_state": "final",
            "counterfactual_hits": hit_count,
            "counterfactual_misses": miss_count,
            "counterfactual_reuse_rate": round(
                hit_count / max(hit_count + miss_count, 1),
                4,
            ),
            "counterfactual_success": success_count,
            "counterfactual_success_rate": round(
                success_count / max(hit_count, 1),
                4,
            ),
            "reused_counterfactuals": reused,
            "missed_counterfactuals": misses,
            "successful_counterfactuals": successes,
            "counterfactual_learning_state": (
                "COUNTERFACTUAL_REUSE_LEARNED"
                if successes
                else "COUNTERFACTUAL_REUSE_PENDING"
            ),
        }

    def _concept(self, item: Mapping[str, Any]) -> str:
        return str(
            item.get("concept")
            or item.get("source_truth")
            or item.get("truth_name")
            or ""
        )

    def _score(self, value: Any) -> float:
        try:
            return round(max(0.0, min(1.0, float(value))), 4)
        except (TypeError, ValueError):
            return 0.0


counterfactual_reuse_engine = CounterfactualReuseEngine()


__all__ = ["CounterfactualReuseEngine", "counterfactual_reuse_engine"]
