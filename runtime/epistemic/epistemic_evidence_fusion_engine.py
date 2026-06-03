from core.epistemic_models import EvidenceAggregate, clamp


class EpistemicEvidenceFusionEngine:
    DIRECT_CAUSAL_SOURCE_PRIORITY = {
        "sandbox_causal_intervention": 3,
        "execution_validation": 2,
        "causal_attestation": 1,
    }
    INDEPENDENT_REPLICATION_SOURCES = {
        "independent_execution_replication",
    }

    def __init__(self, replication_ledger=None):
        self._reports = {}
        self.replication_ledger = replication_ledger

    def _average(self, weighted, attribute):
        total_weight = sum(item["effective_weight"] for item in weighted)
        if not total_weight:
            return 0.0
        return clamp(
            sum(
                getattr(item["evidence"], attribute)
                * item["effective_weight"]
                for item in weighted
            )
            / total_weight
        )

    def fuse(self, evidence_registry, concept, now=None):
        evidence = evidence_registry.evidence_for(concept)
        if not evidence:
            aggregate = EvidenceAggregate(concept=concept)
            self._reports[concept] = self._report(
                concept,
                aggregate,
                [],
                [],
                [],
                "NO_EVIDENCE",
            )
            return aggregate

        weighted = evidence_registry.weighted_evidence_for(concept, now)
        direct_causal = [
            item
            for item in weighted
            if (
                item["evidence"].source
                in self.DIRECT_CAUSAL_SOURCE_PRIORITY
            )
        ]
        evolutionary_context = [
            item
            for item in weighted
            if item["evolutionary_fitness_evidence"]
        ]
        independent_replication = [
            item
            for item in weighted
            if (
                item["evidence"].source
                in self.INDEPENDENT_REPLICATION_SOURCES
            )
        ]
        semantic_context = [
            item
            for item in weighted
            if (
                item not in direct_causal
                and item not in evolutionary_context
                and item not in independent_replication
            )
        ]
        total_weight = sum(item["effective_weight"] for item in weighted)
        support = self._average(weighted, "support_score")
        contradiction = self._average(weighted, "contradiction_score")
        coverage = clamp(total_weight / max(len(evidence), 3))
        ledger_report = (
            self.replication_ledger.concept_report(concept)
            if self.replication_ledger is not None
            else {}
        )
        replication_coverage_bonus = (
            ledger_report.get("replication_bonus")
            if ledger_report
            else clamp(
                min(len(independent_replication), 5) * 0.025,
                0.0,
                0.125,
            )
        )
        evidence_strength = clamp(
            support * 0.72
            + coverage * 0.28
            + replication_coverage_bonus
        )

        selected_direct_source = None
        if direct_causal:
            selected_direct_source = max(
                direct_causal,
                key=lambda item: self.DIRECT_CAUSAL_SOURCE_PRIORITY[
                    item["evidence"].source
                ],
            )["evidence"].source
            causal_channel = [
                item
                for item in direct_causal
                if item["evidence"].source == selected_direct_source
            ]
            causal_policy = "DIRECT_CAUSAL_CHANNEL_PREVAILS"
        elif semantic_context:
            causal_channel = semantic_context
            causal_policy = "SEMANTIC_CONTEXT_FALLBACK"
        else:
            causal_channel = evolutionary_context
            causal_policy = "EVOLUTIONARY_CONTEXT_ONLY"

        aggregate = EvidenceAggregate(
            concept=concept,
            evidence_count=len(evidence),
            support_score=support,
            contradiction_score=contradiction,
            evidence_strength=evidence_strength,
            semantic_consistency=self._average(
                weighted,
                "semantic_consistency",
            ),
            causal_alignment=self._average(
                causal_channel,
                "causal_alignment",
            ),
            historical_reliability=self._average(weighted, "reliability"),
            effective_weight=clamp(total_weight),
        )
        self._reports[concept] = self._report(
            concept,
            aggregate,
            direct_causal,
            semantic_context,
            evolutionary_context,
            causal_policy,
            selected_direct_source,
            causal_channel,
            independent_replication,
            replication_coverage_bonus,
            ledger_report,
        )
        return aggregate

    def _report(
        self,
        concept,
        aggregate,
        direct_causal,
        semantic_context,
        evolutionary_context,
        causal_policy,
        selected_direct_source=None,
        selected_causal_channel=None,
        independent_replication=None,
        replication_coverage_bonus=0.0,
        ledger_report=None,
    ):
        return {
            "system": "epistemic_evidence_fusion_engine",
            "phase": "5.8.5",
            "concept": concept,
            "causal_fusion_policy": causal_policy,
            "selected_direct_causal_source": selected_direct_source,
            "fused_causal_alignment": aggregate.causal_alignment,
            "fused_evidence_strength": aggregate.evidence_strength,
            "independent_replication_coverage_bonus":
            replication_coverage_bonus,
            "knowledge_replication_ledger": ledger_report or {},
            "channels": {
                "direct_causal": {
                    "evidence_count": len(selected_causal_channel or []),
                    "average_causal_alignment":
                    self._average(
                        selected_causal_channel or [],
                        "causal_alignment",
                    ),
                },
                "all_direct_sources": {
                    "evidence_count": len(direct_causal),
                    "average_causal_alignment":
                    self._average(direct_causal, "causal_alignment"),
                },
                "semantic_context": {
                    "evidence_count": len(semantic_context),
                    "average_causal_alignment":
                    self._average(semantic_context, "causal_alignment"),
                },
                "independent_replication": {
                    "evidence_count": len(independent_replication or []),
                    "average_support_score":
                    self._average(
                        independent_replication or [],
                        "support_score",
                    ),
                },
                "evolutionary_context": {
                    "evidence_count": len(evolutionary_context),
                    "average_causal_alignment":
                    self._average(evolutionary_context, "causal_alignment"),
                },
            },
            "weak_context_cannot_reduce_direct_causal_alignment": True,
            "lower_priority_causal_sources_cannot_reduce_stronger_proof":
            True,
            "context_is_preserved_for_support_and_contradiction": True,
            "automatic_truth_promotion_forbidden": True,
        }

    def report_for(self, concept):
        return self._reports.get(concept, {})


__all__ = [
    "EpistemicEvidenceFusionEngine",
]
