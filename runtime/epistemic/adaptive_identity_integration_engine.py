from core.epistemic_models import clamp


class AdaptiveIdentityIntegrationEngine:
    def __init__(
        self,
        base_maximum_semantic_drift=0.58,
        base_minimum_identity_continuity=0.62,
        maximum_drift_tolerance_bonus=0.06,
        maximum_continuity_tolerance_bonus=0.03,
        truth_candidate_pressure_threshold=2,
    ):
        self.base_maximum_semantic_drift = base_maximum_semantic_drift
        self.base_minimum_identity_continuity = (
            base_minimum_identity_continuity
        )
        self.maximum_drift_tolerance_bonus = (
            maximum_drift_tolerance_bonus
        )
        self.maximum_continuity_tolerance_bonus = (
            maximum_continuity_tolerance_bonus
        )
        self.truth_candidate_pressure_threshold = max(
            int(truth_candidate_pressure_threshold),
            1,
        )

    def _strengthens_existing_truths(self, concept, context, registry):
        explicit = context.get("concept_strengthens_existing_truths")
        if explicit is not None:
            return explicit is True

        lineage = context.get("truth_lineage", {}).get(concept, {})
        parent_truths = set(lineage.get("parent_truths", []))
        active_truth_ids = {
            item["truth_id"]
            for item in registry.active_truths()
        }
        return bool(parent_truths & active_truth_ids)

    def evaluate(
        self,
        concept,
        aggregate,
        candidate,
        truth_candidate_count,
        context,
        registry,
    ):
        context = context if isinstance(context, dict) else {}
        generalization = context.get("knowledge_generalization", {})
        generalization_score = clamp(
            generalization.get("generalization_score", 0.0)
        )
        strengthens_existing_truths = self._strengthens_existing_truths(
            concept,
            context,
            registry,
        )
        adaptive_contradiction = candidate.get(
            "adaptive_contradiction_governance",
            context.get("adaptive_contradiction_governance", {}),
        )
        contradiction_supported = (
            adaptive_contradiction.get(
                "contradiction_below_dynamic_threshold",
                False,
            )
            or aggregate.contradiction_score < 0.10
        )
        epistemic_ready = (
            candidate.get("eligible_for_truth_candidate", False)
            and aggregate.semantic_consistency >= 0.90
            and aggregate.causal_alignment >= 0.80
            and contradiction_supported
        )
        candidate_pressure = clamp(
            max(
                truth_candidate_count
                - self.truth_candidate_pressure_threshold
                + 1,
                0,
            )
            / 3.0
        )
        consistency_reward = clamp(
            max(aggregate.semantic_consistency - 0.90, 0.0) / 0.10
        )
        truth_reinforcement_reward = (
            1.0 if strengthens_existing_truths else 0.0
        )
        generalization_reward = clamp(
            max(generalization_score - 0.80, 0.0) / 0.20
        )
        drift_tolerance_bonus = (
            clamp(
                candidate_pressure * 0.020
                + consistency_reward * 0.020
                + truth_reinforcement_reward * 0.015
                + generalization_reward * 0.005,
                0.0,
                self.maximum_drift_tolerance_bonus,
            )
            if epistemic_ready
            else 0.0
        )
        continuity_tolerance_bonus = (
            clamp(
                candidate_pressure * 0.010
                + consistency_reward * 0.010
                + truth_reinforcement_reward * 0.0075
                + generalization_reward * 0.0025,
                0.0,
                self.maximum_continuity_tolerance_bonus,
            )
            if epistemic_ready
            else 0.0
        )
        resistance_reduction = (
            clamp(
                candidate_pressure * 0.30
                + consistency_reward * 0.30
                + truth_reinforcement_reward * 0.25
                + generalization_reward * 0.15
            )
            if epistemic_ready
            else 0.0
        )
        return {
            "system": "adaptive_identity_integration_engine",
            "phase": "6.6",
            "concept": concept,
            "adaptive_tolerance_enabled": epistemic_ready,
            "truth_candidate_count": truth_candidate_count,
            "truth_candidate_pressure_threshold":
            self.truth_candidate_pressure_threshold,
            "semantic_consistency": aggregate.semantic_consistency,
            "adaptive_contradiction_governance":
            adaptive_contradiction,
            "contradiction_supported_by_adaptive_governance":
            contradiction_supported,
            "generalization_score": generalization_score,
            "concept_strengthens_existing_truths":
            strengthens_existing_truths,
            "identity_tolerance_bonus": drift_tolerance_bonus,
            "identity_continuity_tolerance_bonus":
            continuity_tolerance_bonus,
            "identity_resistance_reduction": resistance_reduction,
            "effective_maximum_semantic_drift": clamp(
                self.base_maximum_semantic_drift
                + drift_tolerance_bonus
            ),
            "effective_minimum_identity_continuity": clamp(
                self.base_minimum_identity_continuity
                - continuity_tolerance_bonus
            ),
            "identity_integration_reward": clamp(
                truth_reinforcement_reward * 0.04
                + generalization_reward * 0.02
            ),
            "bounded_adaptation_only": True,
            "semantic_containment_bypass_forbidden": True,
            "high_drift_rehearsal_bypass_forbidden": True,
            "high_drift_recovery_bypass_forbidden": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "AdaptiveIdentityIntegrationEngine",
]
