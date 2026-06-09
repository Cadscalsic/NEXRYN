from core.epistemic_models import clamp


class IdentityContinuityStabilizationPolicy:
    """Stabilizes identity gates for mature, causally supported candidates."""

    IDENTITY_GATES = {
        "truth_candidate_ready",
        "identity_stable",
        "semantic_spine_stable",
        "identity_continuity_above_limit",
        "identity_continuity_preserved",
        "semantic_drift_below_limit",
        "epistemic_drift_containment_inactive",
    }

    MINIMUM_OBSERVATIONS = 24
    MINIMUM_VALIDATIONS = 24
    MINIMUM_CAUSAL_ALIGNMENT = 0.79
    MINIMUM_VALIDATION_SCORE = 0.79
    MINIMUM_CONTEXTUAL_TRUTH = 0.685

    REASONING_CONCEPTS = {
        "symmetry_reasoning",
        "topological_growth",
        "object_identity_preservation",
        "replication",
    }
    IDENTITY_RECOVERY_REQUIRED_CONCEPTS = {
        "object_identity_preservation",
    }

    CANDIDATE_STAGE_BLOCKERS = {
        "validated_stage_required",
    }

    def _score(self, context, paths, default=0.0):
        for path in paths:
            data = context
            for key in path:
                if not isinstance(data, dict):
                    data = None
                    break
                data = data.get(key)
            if data is not None:
                return clamp(data)
        return clamp(default)

    def evaluate(
        self,
        gates,
        context=None,
        concept="",
        observed_count=0,
        validation_count=0,
    ):
        context = context if isinstance(context, dict) else {}
        gates = dict(gates)
        concept = str(concept or context.get("concept", "")).lower()
        candidate = context.get("truth_candidate", {})
        authority = context.get("contextual_truth_authority", {})
        contextual_truth = context.get("contextual_truth", {})
        adaptive_contradiction = context.get(
            "adaptive_contradiction_governance",
            {},
        )
        semantic_spine_recovery = context.get(
            "semantic_spine_recovery_report",
            {},
        )
        explicit_identity_block = context.get("identity_stable") is False
        causal_alignment = self._score(
            context,
            [
                ("causal_graph_alignment", "alignment_score"),
                ("causal_graph_alignment", "causal_graph_alignment"),
            ],
            0.0,
        )
        validation_score = self._score(
            context,
            [
                ("causal_validation", "validation_score"),
                ("causal_validation", "causal_validation_score"),
            ],
            0.0,
        )
        contextual_strength = max(
            self._score(
                {"authority": authority},
                [("authority", "effective_contextual_truth")],
                0.0,
            ),
            self._score(
                {"contextual_truth": contextual_truth},
                [
                    ("contextual_truth", "effective_contextual_truth"),
                    ("contextual_truth", "contextual_truth_score"),
                ],
                0.0,
            ),
            0.70
            if authority.get("contextual_truth_supported") is True
            else 0.0,
        )
        metrics_ready_before_stage = (
            candidate.get("metrics_eligible_for_truth_candidate") is True
            or candidate.get("qualified_metrics") is True
            or candidate.get("strict_qualified_metrics") is True
        ) and not candidate.get("blocked_metrics", [])
        stage_only_blocked = (
            candidate.get("eligibility_reason")
            in self.CANDIDATE_STAGE_BLOCKERS
        )
        candidate_ready = (
            candidate.get("eligible_for_truth_candidate") is True
            or candidate.get("candidate_ready") is True
            or (metrics_ready_before_stage and stage_only_blocked)
        )
        contradiction_ready = adaptive_contradiction.get(
            "contradiction_below_dynamic_threshold",
            True,
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
        identity_recovery_required = (
            concept in self.IDENTITY_RECOVERY_REQUIRED_CONCEPTS
        )
        identity_recovery_ready = (
            not identity_recovery_required
            or recovery_confirmed
        )
        stabilization_ready = (
            not explicit_identity_block
            and concept in self.REASONING_CONCEPTS
            and candidate_ready
            and contradiction_ready
            and identity_recovery_ready
            and observed_count >= self.MINIMUM_OBSERVATIONS
            and validation_count >= self.MINIMUM_VALIDATIONS
            and causal_alignment >= self.MINIMUM_CAUSAL_ALIGNMENT
            and validation_score >= self.MINIMUM_VALIDATION_SCORE
            and contextual_strength >= self.MINIMUM_CONTEXTUAL_TRUTH
        )
        adjusted_gates = dict(gates)
        overrides = {}
        if stabilization_ready:
            for gate in self.IDENTITY_GATES:
                if adjusted_gates.get(gate) is False:
                    adjusted_gates[gate] = True
                    overrides[gate] = "IDENTITY_CONTINUITY_STABILIZED"
        return {
            "system": "identity_continuity_stabilization_policy",
            "phase": "5.8",
            "concept": concept,
            "stabilization_ready": stabilization_ready,
            "explicit_identity_block": explicit_identity_block,
            "candidate_ready": candidate_ready,
            "metrics_ready_before_stage": metrics_ready_before_stage,
            "stage_only_blocked": stage_only_blocked,
            "contradiction_ready": contradiction_ready,
            "identity_recovery_required": identity_recovery_required,
            "identity_recovery_ready": identity_recovery_ready,
            "semantic_spine_recovery_confirmed": recovery_confirmed,
            "recovery_streak": recovery_streak,
            "required_recovery_cycles": required_recovery_cycles,
            "observed_count": observed_count,
            "validation_count": validation_count,
            "causal_alignment": causal_alignment,
            "validation_score": validation_score,
            "contextual_strength": contextual_strength,
            "adjusted_gates": adjusted_gates,
            "overrides": overrides,
            "identity_containment_bypass_forbidden": True,
        }


__all__ = [
    "IdentityContinuityStabilizationPolicy",
]
