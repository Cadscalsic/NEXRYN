class TruthInternalizationEngine:
    ACTIONS = {
        "identity_continuity_preserved":
        "restore_identity_continuity",

        "identity_not_degrading":
        "rollback_unstable_identity_edges",

        "identity_stable_not_explicitly_false":
        "repair_identity_stability",

        "semantic_drift_below_limit":
        "reduce_semantic_drift",

        "mutation_rehearsal_safe":
        "run_safe_mutation_rehearsal",

        "identity_repair_inactive":
        "complete_identity_repair_cycle",

        "semantic_containment_inactive":
        "complete_semantic_containment_recovery",

        "epistemic_drift_containment_inactive":
        "restore_epistemic_drift_equilibrium",
    }

    def _required_actions(self, failed_checks):
        actions = [
            self.ACTIONS[check]
            for check in failed_checks
            if check in self.ACTIONS
        ]
        if "semantic_drift_below_limit" in failed_checks:
            actions.append("reanchor_semantic_spine")
        if "identity_repair_inactive" in failed_checks:
            actions.append("confirm_identity_recovery_cycles")
        if actions:
            actions.append("run_reversible_truth_internalization_rehearsal")
        return list(dict.fromkeys(actions))

    def evaluate(self, belief, aggregate, integration, context=None):
        context = context if isinstance(context, dict) else {}
        failed_checks = integration.get("failed_checks", [])
        candidate_ready = integration.get(
            "checks",
            {},
        ).get(
            "truth_candidate_ready",
            False,
        )
        integration_safe = integration.get("integration_safe", False)
        required_actions = self._required_actions(failed_checks)
        identity_repair_required = "identity_repair_inactive" in failed_checks
        semantic_drift_recovery_required = (
            "semantic_drift_below_limit" in failed_checks
        )

        internalization_state = (
            "WAITING_FOR_TRUTH_CANDIDATE"
            if not candidate_ready
            else "IDENTITY_SAFE_FOR_TRUTH_COMMIT"
            if integration_safe
            else "IDENTITY_GOVERNANCE_REPAIR_REQUIRED"
            if identity_repair_required
            else "SEMANTIC_DRIFT_RECOVERY_REQUIRED"
            if semantic_drift_recovery_required
            else "REVERSIBLE_INTERNALIZATION_REHEARSAL_REQUIRED"
        )
        rehearsal = (
            {
                "concept": belief.concept,
                "claim": belief.claim,
                "rehearsal_type":
                "reversible_truth_internalization_rehearsal",
                "anchor_targets": [
                    "causal_history",
                    "semantic_anchors",
                    "identity_lineage",
                ],
                "baseline_identity_continuity":
                integration.get("identity_continuity"),
                "baseline_semantic_drift":
                integration.get("semantic_drift"),
                "candidate_semantic_consistency":
                aggregate.semantic_consistency,
                "candidate_causal_alignment":
                aggregate.causal_alignment,
                "success_criteria": {
                    "identity_continuity_preserved": True,
                    "semantic_drift_below_limit": True,
                    "identity_repair_inactive": True,
                    "semantic_spine_recovery_confirmed": True,
                },
                "required_result_fields": [
                    "concept",
                    "rehearsal_cycle_id",
                    "identity_continuity",
                    "semantic_drift",
                    "identity_repair_inactive",
                    "semantic_containment_inactive",
                    "semantic_spine_state",
                    "sandbox_validated",
                    "isolated_world",
                    "reversible",
                ],
                "sandbox_only": True,
                "reversible": True,
                "persistent_identity_write_forbidden": True,
                "automatic_truth_commit_forbidden": True,
            }
            if candidate_ready and not integration_safe
            else None
        )

        return {
            "system": "truth_internalization_engine",
            "concept": belief.concept,
            "internalization_state": internalization_state,
            "knowledge_internalization_required":
            candidate_ready and not integration_safe,
            "identity_repair_required": identity_repair_required,
            "semantic_drift_recovery_required":
            semantic_drift_recovery_required,
            "failed_identity_safety_checks": list(failed_checks),
            "required_actions": required_actions,
            "reversible_internalization_rehearsal": rehearsal,
            "persistent_identity_write_forbidden": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "TruthInternalizationEngine",
]
