class TruthGateRemediationEngine:
    ACTIONS = {
        "belief_is_truth_candidate":
        "continue_belief_promotion_trials",

        "minimum_evidence":
        "collect_independent_evidence_sources",

        "minimum_trials":
        "run_additional_epistemic_trials",

        "minimum_consistency":
        "validate_semantic_consistency",

        "minimum_confidence":
        "reinforce_reliable_evidence",

        "minimum_strength":
        "collect_execution_validation_evidence",

        "contradiction_below_limit":
        "resolve_or_explain_contradictory_evidence",

        "identity_stable":
        "repair_identity_stability",

        "semantic_anchor_stable":
        "repair_semantic_anchor_graph",

        "semantic_spine_stable":
        "stabilize_cognitive_spine",

        "mutation_rehearsal_safe":
        "run_safe_mutation_rehearsal",

        "semantic_drift_below_limit":
        "reduce_semantic_drift",

        "identity_continuity_above_limit":
        "restore_identity_continuity",

        "causal_spine_alignment":
        "validate_causal_alignment_with_semantic_spine_truths",

        "compatible_with_core_truths":
        "prove_compatibility_with_locked_core_truths",

        "causal_graph_validation":
        "validate_required_core_causal_relationships",

        "semantic_containment_inactive":
        "complete_semantic_containment_recovery",

        "epistemic_drift_containment_inactive":
        "restore_epistemic_drift_equilibrium",
    }

    def build_plan(self, gates):
        blocked = [
            name
            for name, passed in gates.items()
            if not passed
        ]
        return {
            "system": "truth_gate_remediation_engine",
            "blocked_gates": blocked,
            "required_actions": [
                self.ACTIONS.get(
                    name,
                    "review_epistemic_gate",
                )
                for name in blocked
            ],
            "automatic_bypass_forbidden": True,
        }


__all__ = [
    "TruthGateRemediationEngine",
]
