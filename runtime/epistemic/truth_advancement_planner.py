from runtime.experiment_generator import (
    ExperimentGenerator,
)


class TruthAdvancementPlanner:
    """
    NEXRYN Truth Advancement Planner

    Responsible for selecting the next epistemic action
    when a concept cannot yet advance toward truth commitment.
    """

    EXPERIMENT_STRATEGIES = {
        "causal_alignment": [
            "controlled_feature_ablation",
            "counterfactual_feature_swap",
            "matched_pair_intervention",
        ],
        "evidence_strength": [
            "independent_execution_replication",
            "cross_task_execution_validation",
        ],
        "contradiction_score": [
            "dominant_contradiction_source_isolation",
            "disambiguating_execution_replay",
        ],
        "semantic_consistency": [
            "semantic_invariance_probe",
        ],
        "concept_boundary": [
            "matched_boundary_replication",
            "counterexample_condition_isolation",
            "success_failure_pair_replay",
        ],
        "knowledge_acquisition": [
            "discover_supported_region",
            "probe_counterexample_region",
            "independent_cross_task_execution_validation",
        ],

        # -------------------------
        # NEXRYN Phase-5 Extensions
        # -------------------------

        "dependency_coherence": [
            "targeted_dependency_chain_validation",
            "weakest_dependency_intervention",
            "cross_context_dependency_confirmation",
        ],

        "process_dependency_memory": [
            "dependency_chain_replay",
            "missing_dependency_probe",
            "typed_process_dependency_validation",
        ],

        "identity_governance": [
            "identity_continuity_rehearsal",
            "semantic_spine_stability_probe",
            "epistemic_drift_containment_probe",
        ],

        "semantic_drift": [
            "semantic_drift_boundary_probe",
            "semantic_anchor_revalidation",
        ],

        "epistemic_drift_containment": [
            "containment_activation_probe",
            "drift_recovery_simulation",
        ],
    }

    def __init__(self):
        self.proposal_history = {}
        self.experiment_generator = ExperimentGenerator()

    def _strategies(self, bottleneck):
        return self.EXPERIMENT_STRATEGIES.get(
            bottleneck,
            ["targeted_epistemic_probe"],
        )

    def _extract_bottleneck(
        self,
        trial_resolution,
        truth_candidate,
        causal_failure_analysis,
        evidence_gap_analysis,
    ):
        """
        Determines the dominant bottleneck using all
        currently available runtime signals.
        """

        boundary_refinement = causal_failure_analysis.get(
            "mixed_outcomes_detected",
            False,
        )

        acquisition_required = evidence_gap_analysis.get(
            "acquisition_required",
            False,
        )

        if boundary_refinement:
            return "concept_boundary"

        if acquisition_required:
            return "knowledge_acquisition"

        dominant_gate = (
            trial_resolution.get("dominant_unresolved_gate")
            or truth_candidate.get("dominant_bottleneck")
            or {}
        )

        if isinstance(dominant_gate, dict):
            gate_name = (
                dominant_gate.get("gate_name")
                or dominant_gate.get("metric")
            )

            if gate_name:
                return gate_name

        dependency_blockers = (
            truth_candidate.get(
                "dependency_promotion_blockers",
                [],
            )
            or []
        )

        for blocker in dependency_blockers:
            if "dependency" in str(blocker):
                return "dependency_coherence"

        failed_identity_governance_gates = (
            truth_candidate.get(
                "failed_identity_governance_gates",
                [],
            )
            or []
        )

        if failed_identity_governance_gates:
            return "identity_governance"

        blocked = truth_candidate.get("blocked", []) or []

        if "causal_alignment" in blocked:
            return "causal_alignment"

        if "semantic_drift" in blocked:
            return "semantic_drift"

        if "epistemic_drift_containment" in blocked:
            return "epistemic_drift_containment"

        return None

    def evaluate(
        self,
        concept,
        trial_resolution,
        causal_attestation,
        contradiction_resolution,
        truth_candidate,
        causal_failure_analysis=None,
        evidence_gap_analysis=None,
    ):
        causal_failure_analysis = (
            causal_failure_analysis or {}
        )

        evidence_gap_analysis = (
            evidence_gap_analysis or {}
        )

        stalled = trial_resolution.get(
            "stalled_inconclusive_pattern",
            False,
        )

        truth_metric_gaps = (
            truth_candidate.get(
                "eligibility_reason"
            )
            == "truth_candidate_metric_gaps"
            and truth_candidate.get(
                "stage_eligible_for_truth_candidate",
                False,
            )
        )

        contradiction_review_required = (
            truth_candidate.get(
                "eligibility_reason"
            )
            == "truth_candidate_contradiction_review_required"
        )

        boundary_refinement = causal_failure_analysis.get(
            "mixed_outcomes_detected",
            False,
        )

        acquisition_required = evidence_gap_analysis.get(
            "acquisition_required",
            False,
        )

        advancement_required = (
            stalled
            or truth_metric_gaps
            or contradiction_review_required
            or boundary_refinement
            or acquisition_required
        )

        bottleneck = self._extract_bottleneck(
            trial_resolution,
            truth_candidate,
            causal_failure_analysis,
            evidence_gap_analysis,
        )

        history = self.proposal_history.setdefault(
            concept,
            [],
        )

        used_fingerprints = {
            item["fingerprint"]
            for item in history
        }

        proposal = None

        if advancement_required and bottleneck:
            for strategy in self._strategies(
                bottleneck
            ):
                fingerprint = (
                    f"{concept}:{bottleneck}:{strategy}"
                )

                if fingerprint in used_fingerprints:
                    continue

                proposal = (
                    self.experiment_generator.generate(
                        concept,
                        bottleneck,
                        strategy,
                        len(history) + 1,
                        evidence_gap_analysis,
                    )
                )

                history.append(proposal)
                break

        planner_state = (
            "EXPERIMENT_PROPOSED"
            if proposal
            else (
                "EXPERIMENT_STRATEGIES_EXHAUSTED"
                if advancement_required
                and bottleneck
                else "MONITORING_EPISTEMIC_PROGRESS"
            )
        )

        return {
            "system": "truth_advancement_planner",
            "concept": concept,
            "planner_state": planner_state,
            "stalled_inconclusive_pattern": stalled,
            "truth_candidate_metric_gaps": truth_metric_gaps,
            "truth_candidate_contradiction_review_required":
                contradiction_review_required,
            "counterexample_boundary_refinement_required":
                boundary_refinement,
            "active_knowledge_acquisition_required":
                acquisition_required,
            "evidence_gap_analysis":
                evidence_gap_analysis,
            "advancement_trigger": (
                "stalled_inconclusive_pattern"
                if stalled
                else "mixed_causal_outcomes"
                if boundary_refinement
                else "active_knowledge_acquisition_required"
                if acquisition_required
                else "truth_candidate_contradiction_review_required"
                if contradiction_review_required
                else "truth_candidate_metric_gaps"
                if truth_metric_gaps
                else None
            ),
            "dominant_bottleneck":
                bottleneck,
            "experiment_proposal":
                proposal,
            "proposal_count":
                len(history),
            "previous_proposal_fingerprints": [
                item["fingerprint"]
                for item in history
            ],
            "duplicate_experiment_forbidden": True,
            "causal_attestation_state":
                causal_attestation.get(
                    "architecture_state"
                ),
            "contradiction_resolution_state":
                contradiction_resolution.get(
                    "resolution_state"
                ),
            "autonomous_execution_forbidden": True,
            "autonomous_sandbox_execution_permitted": True,
            "persistent_external_execution_forbidden": True,
        }


__all__ = [
    "TruthAdvancementPlanner",
]