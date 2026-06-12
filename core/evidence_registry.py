from datetime import datetime
from math import exp, log

from core.epistemic_models import Evidence, EvidenceAggregate, clamp, utcnow
from runtime.contradiction_attribution_engine import (
    ContradictionAttributionEngine,
)
from runtime.evidence_reinforcement_engine import EvidenceReinforcementEngine


class EvidenceRegistry:
    EVOLUTIONARY_FITNESS_SOURCES = {
        "evolutionary_trait_observation",
        "evolutionary_trait_survival_history",
    }

    def __init__(
        self,
        half_life_days=30.0,
        maximum_evolutionary_fitness_ratio=0.25,
    ):
        self.half_life_days = max(float(half_life_days), 0.001)
        self.maximum_evolutionary_fitness_ratio = clamp(
            maximum_evolutionary_fitness_ratio,
            0.0,
            0.95,
        )
        self.registry = {}
        self._seen_signatures = set()
        self._concept_fitness_ratio_overrides = {}
        self.fusion_engine = None
        self.reinforcement_engine = EvidenceReinforcementEngine()
        self.contradiction_attribution_engine = (
            ContradictionAttributionEngine()
        )

    def collect(self, evidence=None, **kwargs):
        if evidence is None:
            evidence = Evidence(**kwargs)
        elif isinstance(evidence, dict):
            evidence = Evidence(**evidence)
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence must be an Evidence object or mapping")
        evidence_id = evidence.metadata.get("evidence_id")
        signature = (
            evidence_id
            if evidence_id is not None
            else (
                evidence.concept,
                evidence.source,
                evidence.support_score,
                evidence.contradiction_score,
                evidence.reliability,
                evidence.causal_alignment,
                evidence.semantic_consistency,
                evidence.metadata.get("observation_id"),
            )
        )
        if signature in self._seen_signatures:
            return evidence
        evidence = self.reinforcement_engine.reinforce(
            evidence,
            self.registry.get(
                evidence.concept,
                [],
            ),
        )
        self._seen_signatures.add(signature)
        self.registry.setdefault(evidence.concept, []).append(evidence)
        return evidence

    def evidence_for(self, concept):
        return list(self.registry.get(concept, []))

    def age_weight(self, evidence, now=None):
        now = now or utcnow()
        age_days = max((now - evidence.observed_at).total_seconds(), 0.0) / 86400
        return clamp(exp(-log(2) * age_days / self.half_life_days))

    def evidence_weight(self, evidence, now=None):
        quality = (
            evidence.reliability * 0.50
            + evidence.causal_alignment * 0.30
            + evidence.semantic_consistency * 0.20
        )
        return clamp(quality * self.age_weight(evidence, now))

    def is_evolutionary_fitness_evidence(self, evidence):
        return (
            evidence.source in self.EVOLUTIONARY_FITNESS_SOURCES
            or evidence.metadata.get("survival_is_not_truth") is True
        )

    def fitness_ratio_for(self, concept):
        return self._concept_fitness_ratio_overrides.get(
            concept,
            self.maximum_evolutionary_fitness_ratio,
        )

    def set_fitness_ratio(self, concept, ratio):
        ratio = clamp(
            ratio,
            0.0,
            self.maximum_evolutionary_fitness_ratio,
        )
        current = self.fitness_ratio_for(concept)
        self._concept_fitness_ratio_overrides[concept] = min(
            current,
            ratio,
        )
        return self._concept_fitness_ratio_overrides[concept]

    def weighted_evidence_for(self, concept, now=None):
        weighted = []
        for item in self.evidence_for(concept):
            raw_weight = self.evidence_weight(item, now)
            weighted.append({
                "evidence": item,
                "raw_weight": raw_weight,
                "effective_weight": raw_weight,
                "evolutionary_fitness_evidence":
                self.is_evolutionary_fitness_evidence(item),
            })
        epistemic_weight = sum(
            item["raw_weight"]
            for item in weighted
            if not item["evolutionary_fitness_evidence"]
        )
        fitness_weight = sum(
            item["raw_weight"]
            for item in weighted
            if item["evolutionary_fitness_evidence"]
        )
        ratio = self.fitness_ratio_for(concept)
        maximum_fitness_weight = (
            epistemic_weight * ratio / max(1.0 - ratio, 0.0001)
            if epistemic_weight
            else fitness_weight
        )
        fitness_scale = (
            min(maximum_fitness_weight / fitness_weight, 1.0)
            if fitness_weight
            else 1.0
        )
        for item in weighted:
            if item["evolutionary_fitness_evidence"]:
                item["effective_weight"] = round(
                    item["raw_weight"] * fitness_scale,
                    4,
                )
        return weighted

    def epistemic_partition(self, concept, now=None):
        weighted = self.weighted_evidence_for(concept, now)
        raw_fitness_weight = sum(
            item["raw_weight"]
            for item in weighted
            if item["evolutionary_fitness_evidence"]
        )
        effective_fitness_weight = sum(
            item["effective_weight"]
            for item in weighted
            if item["evolutionary_fitness_evidence"]
        )
        raw_total_weight = sum(item["raw_weight"] for item in weighted)
        effective_total_weight = sum(
            item["effective_weight"]
            for item in weighted
        )
        return {
            "evolutionary_fitness_raw_weight":
            round(raw_fitness_weight, 4),
            "evolutionary_fitness_effective_weight":
            round(effective_fitness_weight, 4),
            "epistemic_raw_weight":
            round(raw_total_weight - raw_fitness_weight, 4),
            "epistemic_effective_weight":
            round(effective_total_weight - effective_fitness_weight, 4),
            "evolutionary_fitness_raw_ratio": clamp(
                raw_fitness_weight / max(raw_total_weight, 0.0001)
            ),
            "evolutionary_fitness_effective_ratio": clamp(
                effective_fitness_weight
                / max(effective_total_weight, 0.0001)
            ),
            "maximum_evolutionary_fitness_ratio":
            self.fitness_ratio_for(concept),
            "cap_applied":
            effective_fitness_weight < raw_fitness_weight,
            "survival_is_not_truth": True,
        }

    def effective_evidence_weight(self, evidence, now=None):
        for item in self.weighted_evidence_for(evidence.concept, now):
            if item["evidence"] is evidence:
                return item["effective_weight"]
        return self.evidence_weight(evidence, now)

    def aggregate(self, concept, now=None):
        if self.fusion_engine is not None:
            aggregate = self.fusion_engine.fuse(self, concept, now)
            return self._apply_contradiction_attribution(
                concept,
                aggregate,
                now,
            )

        evidence_items = self.evidence_for(concept)
        if not evidence_items:
            return EvidenceAggregate(concept=concept)

        weighted = self.weighted_evidence_for(concept, now)
        total_weight = sum(item["effective_weight"] for item in weighted)
        denominator = max(total_weight, 0.0001)

        def average(attribute):
            return clamp(
                sum(
                    getattr(item["evidence"], attribute)
                    * item["effective_weight"]
                    for item in weighted
                )
                / denominator
            )

        support = average("support_score")
        contradiction = average("contradiction_score")
        coverage = clamp(total_weight / max(len(evidence_items), 3))
        evidence_strength = clamp(support * 0.72 + coverage * 0.28)

        aggregate = EvidenceAggregate(
            concept=concept,
            evidence_count=len(evidence_items),
            support_score=support,
            contradiction_score=contradiction,
            evidence_strength=evidence_strength,
            semantic_consistency=average("semantic_consistency"),
            causal_alignment=average("causal_alignment"),
            historical_reliability=average("reliability"),
            effective_weight=clamp(total_weight),
        )

        aggregate.audit = {
            "raw_causal_alignment":
                average("causal_alignment"),
            "support_score":
                support,
            "contradiction_score":
                contradiction,
            "evidence_strength":
                evidence_strength,
            "semantic_consistency":
                average("semantic_consistency"),
            "historical_reliability":
                average("reliability"),
            "evidence_count":
                len(evidence_items),
            "effective_weight":
                clamp(total_weight),
        }
        return self._apply_contradiction_attribution(
            concept,
            aggregate,
            now,
        )

    def _apply_contradiction_attribution(self, concept, aggregate, now=None):
        result = self.contradiction_attribution_engine.apply(
            concept,
            aggregate,
            self.evidence_for(concept),
            lambda item: self.effective_evidence_weight(item, now),
        )

        if hasattr(aggregate, "audit"):
            setattr(
                result,
                "causal_alignment_audit",
                aggregate.audit,
            )

        return result

    def report(self):
        evidence_items = [
            item
            for items in self.registry.values()
            for item in items
        ]
        source_counts = {}
        for item in evidence_items:
            source_counts[item.source] = (
                source_counts.get(item.source, 0) + 1
            )
        return {
            "system": "evidence_registry",
            "concept_count": len(self.registry),
            "evidence_count": sum(len(items) for items in self.registry.values()),
            "reinforced_evidence_count": sum(
                item.metadata.get(
                    "reinforcement_applied",
                    False,
                )
                for item in evidence_items
            ),
            "source_counts": source_counts,
            "reinforcement_policy":
            "consistent_repetition_increases_reliability_not_truth",
            "evolutionary_fitness_policy": {
                "maximum_aggregate_weight_ratio":
                self.maximum_evolutionary_fitness_ratio,
                "policy":
                "evolutionary_fitness_informs_but_cannot_dominate_epistemic_truth",
            },
            "concept_fitness_ratio_overrides":
            dict(self._concept_fitness_ratio_overrides),
            "survival_is_not_truth": True,
        }
