from core.epistemic_models import clamp


class CausalEvidenceArbitrationEngine:
    DIRECT_CAUSAL_SOURCE_PRIORITY = {
        "sandbox_causal_intervention": 3,
        "execution_validation": 2,
        "causal_attestation": 1,
    }
    EVOLUTIONARY_CONTEXT_SOURCES = {
        "evolutionary_trait_observation",
        "evolutionary_trait_survival_history",
    }

    def __init__(
        self,
        conflict_threshold=0.20,
        minimum_direct_reliability=0.70,
        conflicting_survival_ratio=0.10,
    ):
        self.conflict_threshold = clamp(conflict_threshold)
        self.minimum_direct_reliability = clamp(
            minimum_direct_reliability
        )
        self.conflicting_survival_ratio = clamp(
            conflicting_survival_ratio
        )

    def _average(self, items, attribute):
        if not items:
            return 0.0
        return clamp(
            sum(getattr(item, attribute) for item in items)
            / len(items)
        )

    def evaluate(self, evidence_registry, concept):
        evidence = evidence_registry.evidence_for(concept)
        direct = [
            item
            for item in evidence
            if (
                item.source in self.DIRECT_CAUSAL_SOURCE_PRIORITY
                and item.reliability >= self.minimum_direct_reliability
            )
        ]
        evolutionary = [
            item
            for item in evidence
            if item.source in self.EVOLUTIONARY_CONTEXT_SOURCES
        ]
        direct_alignment = self._average(direct, "causal_alignment")
        evolutionary_alignment = self._average(
            evolutionary,
            "causal_alignment",
        )
        conflict_gap = round(
            abs(direct_alignment - evolutionary_alignment),
            4,
        )
        conflict_detected = bool(
            direct
            and evolutionary
            and conflict_gap >= self.conflict_threshold
        )
        previous_ratio = evidence_registry.fitness_ratio_for(concept)
        winner = None
        decision = "NO_CAUSAL_SOURCE_CONFLICT"

        if conflict_detected:
            winner = max(
                direct,
                key=lambda item: (
                    self.DIRECT_CAUSAL_SOURCE_PRIORITY[item.source],
                    item.reliability,
                    item.causal_alignment,
                ),
            ).source
            evidence_registry.set_fitness_ratio(
                concept,
                self.conflicting_survival_ratio,
            )
            decision = "DIRECT_CAUSAL_EVIDENCE_PREVAILS"

        return {
            "system": "causal_evidence_arbitration_engine",
            "phase": "5.8",
            "concept": concept,
            "decision": decision,
            "conflict_detected": conflict_detected,
            "conflict_gap": conflict_gap,
            "conflict_threshold": self.conflict_threshold,
            "direct_causal_evidence_count": len(direct),
            "evolutionary_context_evidence_count": len(evolutionary),
            "direct_causal_average_alignment": direct_alignment,
            "evolutionary_context_average_alignment":
            evolutionary_alignment,
            "winning_source": winner,
            "previous_evolutionary_fitness_ratio": previous_ratio,
            "effective_evolutionary_fitness_ratio":
            evidence_registry.fitness_ratio_for(concept),
            "arbitration_policy":
            "direct_causal_execution_precedes_evolutionary_survival_context",
            "evolutionary_history_preserved_as_context": True,
            "direct_metric_inflation_forbidden": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "CausalEvidenceArbitrationEngine",
]
