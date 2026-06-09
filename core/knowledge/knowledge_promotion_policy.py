import re

from core.knowledge.contextual_truth_support_policy import (
    ContextualTruthSupportPolicy,
)
from core.knowledge.identity_continuity_stabilization_policy import (
    IdentityContinuityStabilizationPolicy,
)


class KnowledgePromotionPolicy:
    PROMOTION_GATES = {
        "belief_is_truth_candidate",
        "minimum_trials",
    }
    PRESERVATION_GATES = {
        "minimum_trials",
        "semantic_drift_below_limit",
        "identity_continuity_above_limit",
        "contextual_truth_score",
    }

    def __init__(self):
        self.contextual_truth_support_policy = (
            ContextualTruthSupportPolicy()
        )
        self.identity_stabilization_policy = (
            IdentityContinuityStabilizationPolicy()
        )

    def _walk_text(self, value):
        if isinstance(value, dict):
            for item in value.values():
                yield from self._walk_text(item)
        elif isinstance(value, list):
            for item in value:
                yield from self._walk_text(item)
        elif isinstance(value, str):
            yield value

    def _count_from_text(self, context, pattern):
        count = 0
        for text in self._walk_text(context):
            for match in re.finditer(pattern, text):
                count = max(count, int(match.group(1)))
        return count

    def _observed_count(self, context):
        generalization = context.get("knowledge_generalization", {})
        truth_candidate = context.get("truth_candidate", {})
        adaptive_contradiction = context.get(
            "adaptive_contradiction_governance",
            {},
        )
        return max(
            int(generalization.get("used_task_count", 0) or 0),
            int(generalization.get("independent_replications", 0) or 0),
            int(truth_candidate.get("observed_task_count", 0) or 0),
            int(adaptive_contradiction.get("observed_count", 0) or 0),
            self._count_from_text(context, r"observed in (\d+) tasks"),
        )

    def _validation_count(self, context, observed_count):
        generalization = context.get("knowledge_generalization", {})
        truth_candidate = context.get("truth_candidate", {})
        adaptive_contradiction = context.get(
            "adaptive_contradiction_governance",
            {},
        )
        return max(
            int(generalization.get("validation_count", 0) or 0),
            int(truth_candidate.get("validation_count", 0) or 0),
            int(adaptive_contradiction.get("validation_count", 0) or 0),
            self._count_from_text(context, r"validated across (\d+) tasks"),
            observed_count if observed_count >= 8 else 0,
        )

    def _contextual_truth_supported(self, context):
        authority = context.get("contextual_truth_authority", {})
        contextual_truth = context.get("contextual_truth", {})
        support = self.contextual_truth_support_policy.evaluate(
            contextual_truth=contextual_truth,
            contextual_truth_authority=authority,
            context_hierarchy=context.get("context_hierarchy", {}),
            semantic_context=context.get("semantic_context", {}),
        )
        return support["contextual_truth_supported"]

    def _candidate_ready(self, context):
        truth_candidate = context.get("truth_candidate", {})
        adaptive_contradiction = context.get(
            "adaptive_contradiction_governance",
            {},
        )
        return (
            truth_candidate.get("eligible_for_truth_candidate") is True
            or truth_candidate.get("candidate_ready") is True
            or (
                adaptive_contradiction.get(
                    "contradiction_below_dynamic_threshold",
                    False,
                )
                and self._contextual_truth_supported(context)
            )
        )

    def _preservation_ready(
        self,
        context,
        stable_truth_authority_locked,
        observed_count=0,
        validation_count=0,
        minimum_trials=2,
    ):
        if not stable_truth_authority_locked:
            return False
        semantic_spine_recovery = context.get(
            "semantic_spine_recovery_report",
            {},
        )
        adaptive_contradiction = context.get(
            "adaptive_contradiction_governance",
            {},
        )
        recovery_streak = int(
            semantic_spine_recovery.get("recovery_streak", 0) or 0
        )
        required_recovery_cycles = int(
            semantic_spine_recovery.get("required_recovery_cycles", 3) or 3
        )
        recovery_confirmed = (
            semantic_spine_recovery.get(
                "semantic_spine_recovery_confirmed",
                False,
            )
            is True
            or semantic_spine_recovery.get("recovery_state")
            == "STABLE_SEMANTIC_SPINE"
            or recovery_streak >= required_recovery_cycles
        )
        mature_stable_truth = (
            observed_count >= 32
            and validation_count >= max(minimum_trials, 8)
        )
        return (
            recovery_confirmed
            and (
                self._contextual_truth_supported(context)
                or mature_stable_truth
            )
            and adaptive_contradiction.get(
                "contradiction_below_dynamic_threshold",
                True,
            )
        )

    def evaluate(
        self,
        gates,
        context=None,
        stable_truth_authority_locked=False,
        minimum_trials=2,
    ):
        context = context if isinstance(context, dict) else {}
        adjusted_gates = dict(gates)
        observed_count = self._observed_count(context)
        validation_count = self._validation_count(context, observed_count)
        concept = str(
            context.get(
                "concept",
                context.get("truth_candidate", {}).get("concept", ""),
            )
        )
        candidate_ready = self._candidate_ready(context)
        promotion_ready = (
            candidate_ready
            and observed_count >= 8
            and validation_count >= minimum_trials
        )
        preservation_ready = self._preservation_ready(
            context,
            stable_truth_authority_locked,
            observed_count,
            validation_count,
            minimum_trials,
        )
        overrides = {}

        if promotion_ready:
            for gate in self.PROMOTION_GATES:
                if adjusted_gates.get(gate) is False:
                    adjusted_gates[gate] = True
                    overrides[gate] = "ACCUMULATED_VALIDATION_PROMOTION"

        if preservation_ready:
            for gate in self.PRESERVATION_GATES:
                if adjusted_gates.get(gate) is False:
                    adjusted_gates[gate] = True
                    overrides[gate] = "STABLE_TRUTH_PRESERVATION_LOCK"

        identity_stabilization = (
            self.identity_stabilization_policy.evaluate(
                adjusted_gates,
                context,
                concept=concept,
                observed_count=observed_count,
                validation_count=validation_count,
            )
        )
        adjusted_gates = identity_stabilization["adjusted_gates"]
        overrides.update(identity_stabilization["overrides"])

        return {
            "system": "knowledge_promotion_policy",
            "phase": "5.9",
            "requires_phase_5_8_identity_continuity_stabilization": True,
            "observed_count": observed_count,
            "validation_count": validation_count,
            "candidate_ready": candidate_ready,
            "promotion_ready": promotion_ready,
            "preservation_ready": preservation_ready,
            "mature_stable_truth_preservation":
            stable_truth_authority_locked
            and observed_count >= 32
            and validation_count >= max(minimum_trials, 8),
            "identity_continuity_stabilization":
            identity_stabilization,
            "adjusted_gates": adjusted_gates,
            "overrides": overrides,
            "blocked_gates_after_policy": [
                name
                for name, passed in adjusted_gates.items()
                if not passed
            ],
            "promotion_policy_is_not_truth_proof": True,
            "identity_containment_bypass_forbidden": True,
        }


__all__ = [
    "KnowledgePromotionPolicy",
]
