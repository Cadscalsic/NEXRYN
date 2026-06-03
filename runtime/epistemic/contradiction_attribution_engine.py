from core.epistemic_models import clamp


CONTRADICTION_SOURCE_WEIGHTS = {
    "sandbox_causal_intervention": 1.0,
    "execution_validation": 1.0,
    "independent_execution_replication": 0.9,
    "causal_attestation": 0.8,
    "constructive_reasoning": 0.6,
    "mutation_rehearsal": 0.4,
    "evolutionary_trait_observation": 0.2,
    "evolutionary_trait_survival_history": 0.2,
}


class ContradictionAttributionEngine:
    DEFAULT_SOURCE_WEIGHT = 0.6
    DIRECT_EXECUTION_SOURCES = {
        "sandbox_causal_intervention",
        "execution_validation",
        "independent_execution_replication",
        "causal_attestation",
    }
    SURVIVAL_CONTEXT_SOURCES = {
        "evolutionary_trait_observation",
        "evolutionary_trait_survival_history",
    }

    def __init__(self, source_weights=None):
        self.source_weights = {
            **CONTRADICTION_SOURCE_WEIGHTS,
            **(source_weights or {}),
        }
        self._reports = {}

    def source_weight(self, source):
        return clamp(
            self.source_weights.get(
                source,
                self.DEFAULT_SOURCE_WEIGHT,
            )
        )

    def evaluate(
        self,
        concept,
        aggregate,
        evidence_items=None,
        evidence_weight=None,
    ):
        source_groups = {}
        for item in evidence_items or []:
            source_groups.setdefault(item.source, []).append(item)

        source_attributions = []
        raw_total_weight = 0.0
        attributed_total_weight = 0.0
        raw_contradiction_load = 0.0
        effective_contradiction_load = 0.0
        for source, items in sorted(source_groups.items()):
            source_policy_weight = self.source_weight(source)
            weighted = [
                (
                    item,
                    evidence_weight(item)
                    if evidence_weight
                    else 1.0,
                )
                for item in items
            ]
            source_raw_weight = sum(weight for _, weight in weighted)
            source_attributed_weight = (
                source_raw_weight * source_policy_weight
            )
            source_raw_load = sum(
                item.contradiction_score * weight
                for item, weight in weighted
            )
            source_effective_load = (
                source_raw_load * source_policy_weight
            )
            raw_total_weight += source_raw_weight
            attributed_total_weight += source_attributed_weight
            raw_contradiction_load += source_raw_load
            effective_contradiction_load += source_effective_load
            source_attributions.append({
                "source": source,
                "evidence_count": len(items),
                "source_weight": source_policy_weight,
                "raw_evidence_weight": round(source_raw_weight, 4),
                "attributed_evidence_weight":
                round(source_attributed_weight, 4),
                "average_contradiction_score": clamp(
                    source_raw_load / max(source_raw_weight, 0.0001)
                ),
                "raw_weighted_contradiction_load":
                round(source_raw_load, 4),
                "effective_weighted_contradiction_load":
                round(source_effective_load, 4),
                "direct_execution_evidence":
                source in self.DIRECT_EXECUTION_SOURCES,
                "survival_context_evidence":
                source in self.SURVIVAL_CONTEXT_SOURCES,
            })

        raw_score = (
            clamp(raw_contradiction_load / max(raw_total_weight, 0.0001))
            if source_attributions
            else aggregate.contradiction_score
        )
        effective_score = (
            clamp(
                effective_contradiction_load
                / max(attributed_total_weight, 0.0001)
            )
            if source_attributions
            else aggregate.contradiction_score
        )
        for item in source_attributions:
            item["raw_contradiction_load_share"] = clamp(
                item["raw_weighted_contradiction_load"]
                / max(raw_contradiction_load, 0.0001)
            )
            item["effective_contradiction_load_share"] = clamp(
                item["effective_weighted_contradiction_load"]
                / max(effective_contradiction_load, 0.0001)
            )

        ranked_raw = sorted(
            source_attributions,
            key=lambda item: item["raw_weighted_contradiction_load"],
            reverse=True,
        )
        ranked_effective = sorted(
            source_attributions,
            key=lambda item:
            item["effective_weighted_contradiction_load"],
            reverse=True,
        )
        report = {
            "system": "contradiction_attribution_engine",
            "phase": "6.92",
            "concept": concept,
            "policy":
            "direct_execution_contradiction_precedes_survival_context",
            "contradiction_source_weights": dict(self.source_weights),
            "raw_contradiction_score": raw_score,
            "effective_contradiction_score": effective_score,
            "source_attributions": source_attributions,
            "ranked_raw_contradiction_sources": ranked_raw,
            "ranked_effective_contradiction_sources": ranked_effective,
            "dominant_raw_contradiction_source":
            ranked_raw[0] if ranked_raw else None,
            "dominant_effective_contradiction_source":
            ranked_effective[0] if ranked_effective else None,
            "survival_context_attenuated": any(
                item["survival_context_evidence"]
                and item["source_weight"] < 1.0
                for item in source_attributions
            ),
            "survival_is_not_truth": True,
            "automatic_truth_promotion_forbidden": True,
        }
        self._reports[concept] = report
        return report

    def apply(
        self,
        concept,
        aggregate,
        evidence_items=None,
        evidence_weight=None,
    ):
        report = self.evaluate(
            concept,
            aggregate,
            evidence_items,
            evidence_weight,
        )
        aggregate.contradiction_score = report[
            "effective_contradiction_score"
        ]
        return aggregate

    def report_for(self, concept):
        return self._reports.get(concept, {})


__all__ = [
    "CONTRADICTION_SOURCE_WEIGHTS",
    "ContradictionAttributionEngine",
]
