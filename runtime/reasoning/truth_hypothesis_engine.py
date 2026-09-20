"""Generate testable hypotheses from committed truths."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from runtime.reasoning.hypothesis_arbitration_engine import (
    HypothesisArbitrationEngine,
)


class TruthHypothesisEngine:
    system_name = "truth_hypothesis_engine"

    def __init__(self, arbitration_engine=None):
        self.arbitration_engine = arbitration_engine or HypothesisArbitrationEngine()

    def generate(
        self,
        truths: Iterable[Mapping[str, Any]] | None = None,
        contexts: Mapping[str, Any] | None = None,
        max_hypotheses: int = 24,
    ) -> dict[str, Any]:
        contexts = contexts if isinstance(contexts, Mapping) else {}
        candidates = []
        counterfactuals = []
        for truth in list(truths or [])[:max(1, max_hypotheses)]:
            if not isinstance(truth, Mapping):
                continue
            concept = str(
                truth.get("concept")
                or truth.get("truth_name")
                or ""
            )
            if not concept:
                continue
            confidence = _score(
                truth.get("truth_confidence")
                or truth.get("commit_score")
                or truth.get("calibrated_confidence")
            )
            context = contexts.get(concept, {})
            context = context if isinstance(context, Mapping) else {}
            context_confidence = _score(
                context.get("context_confidence")
                or context.get("confidence")
                or confidence
            )
            hypothesis = {
                "hypothesis_id": f"hypothesis:{concept}:truth_reuse",
                "concept": concept,
                "type": "truth_reuse_generalization",
                "semantic_class": "inference",
                "source_truth": concept,
                "confidence": confidence,
                "explanatory_power": max(confidence, context_confidence),
                "residual_reduction": round(
                    max(confidence, context_confidence) * 0.92,
                    4,
                ),
                "transformation_salience": context_confidence,
                "causal_support": confidence,
                "proposition": (
                    f"{concept} can constrain future transformations in "
                    "matching process contexts"
                ),
                "expected_observation": (
                    f"future tasks preserving {concept} should reuse the "
                    "committed truth with low contradiction"
                ),
                "falsification_criterion": (
                    f"repeated matching contexts violate {concept} without "
                    "identity-safe explanation"
                ),
                "generated_from": "TRUTH_COMMITTED",
                "requires_counterfactual_testing": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
            hypothesis["status"] = (
                "ACCEPTED_HYPOTHESIS"
                if confidence >= 0.86 and context_confidence >= 0.86
                else "GENERATED_HYPOTHESIS"
            )
            candidates.append(hypothesis)
            counterfactuals.append({
                "counterfactual_id": (
                    f"counterfactual:{concept}:truth_removed"
                ),
                "concept": concept,
                "source_hypothesis": hypothesis["hypothesis_id"],
                "what_if": f"{concept} is not reused as a committed truth",
                "expected_effect": (
                    "prediction should lose contextual support or increase "
                    "contradiction pressure"
                ),
                "counterfactual_robustness": round(
                    min(confidence, context_confidence),
                    4,
                ),
                "status": "COUNTERFACTUAL_READY",
            })

        arbitration = self.arbitration_engine.build_arbitration_report(
            candidates,
        )
        accepted = [
            item
            for item in candidates
            if item.get("status") == "ACCEPTED_HYPOTHESIS"
        ]
        rejected = [
            item
            for item in candidates
            if item.get("status") == "REJECTED_HYPOTHESIS"
        ]
        return {
            "system": self.system_name,
            "report_state": "final",
            "generated_hypotheses": candidates,
            "accepted_hypotheses": accepted,
            "rejected_hypotheses": rejected,
            "counterfactual_hypotheses": counterfactuals,
            "hypothesis_count": len(candidates),
            "accepted_hypothesis_count": len(accepted),
            "rejected_hypothesis_count": len(rejected),
            "counterfactual_count": len(counterfactuals),
            "arbitration_report": arbitration,
            "reason": (
                "committed_truths_converted_to_testable_hypotheses"
                if candidates
                else "no_committed_truths_available"
            ),
        }


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


truth_hypothesis_engine = TruthHypothesisEngine()


__all__ = [
    "TruthHypothesisEngine",
    "truth_hypothesis_engine",
]
