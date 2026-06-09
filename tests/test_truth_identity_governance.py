from core.belief_engine import EpistemicCognitionLayer
from core.epistemic_models import Belief, BeliefState, EvidenceAggregate
from core.identity.identity_continuity_engine import IdentityContinuityEngine
from core.identity.semantic_containment_engine import SemanticContainmentEngine
from runtime.identity.semantic_containment_engine import (
    SemanticContainmentEngine as RuntimeSemanticContainmentEngine,
)
from runtime.identity_safe_truth_integration import (
    IdentitySafeTruthIntegrationEngine,
)
from core.knowledge.final_commit_decision_engine import (
    FinalCommitDecisionEngine,
)
from core.knowledge.adaptive_contradiction_governance import (
    AdaptiveContradictionGovernance,
)
from core.knowledge.knowledge_promotion_policy import (
    KnowledgePromotionPolicy,
)
from core.knowledge.contextual_truth_support_policy import (
    ContextualTruthSupportPolicy,
)
from core.knowledge.identity_continuity_stabilization_policy import (
    IdentityContinuityStabilizationPolicy,
)
from core.knowledge.contradiction_review_policy import (
    classify_contradiction_review,
)


def strong_evidence(concept, source):
    return {
        "concept": concept,
        "source": source,
        "support_score": 1.0,
        "contradiction_score": 0.0,
        "reliability": 1.0,
        "semantic_consistency": 1.0,
        "causal_alignment": 1.0,
    }


def unsafe_merge_context():
    return {
        "identity_continuity": 0.82,
        "truth_candidate_semantic_sources": [
            "object_translation",
            "color_change",
        ],
        "cognitive_failure_memory": {
            "latest_failure": {
                "contradiction_type": "unsafe_merge",
                "collapse_source": "object_translation::color_change",
                "ontology_damage": 0.72,
                "recovery_action": "block_merge",
            },
        },
    }


def test_identity_continuity_forecasts_new_truth_against_old_spine():
    report = IdentityContinuityEngine().evaluate(
        "position_preservation",
        old_spine_continuity=0.78,
        new_truth_delta=-0.08,
    )

    assert report["continuity_score"] == 0.70
    assert report["allowed_transition"] is True


def test_semantic_containment_blocks_remembered_unsafe_merge():
    report = SemanticContainmentEngine().evaluate(
        "unsafe_composite_truth",
        unsafe_merge_context(),
    )

    assert report["containment_state"] == "UNSAFE_MERGE_CONTAINED"
    assert report["integration_allowed"] is False
    assert report["blocked_collapse_source"] == (
        "object_translation::color_change"
    )


def causal_containment_context(conflicting_observations, reliability):
    return {
        "causal_graph_validation": {
            "relationship_checks": [{
                "source": "density_preservation",
                "target": "topology_preservation",
                "causal_support": {
                    "observation_count": 4,
                    "conflicting_observation_count":
                    conflicting_observations,
                    "support_reliability": reliability,
                    "causal_support_score": reliability,
                },
            }],
        },
    }


def test_runtime_semantic_containment_allows_accumulating_causal_support():
    report = RuntimeSemanticContainmentEngine().evaluate(
        "topology_preservation",
        causal_containment_context(
            conflicting_observations=1,
            reliability=0.25,
        ),
    )

    assert report["integration_allowed"] is True
    assert report["causal_containment_active"] is False
    assert report["accumulating_causal_support_is_not_identity_conflict"] is (
        True
    )


def test_runtime_semantic_containment_blocks_repeated_causal_conflict():
    report = RuntimeSemanticContainmentEngine().evaluate(
        "topology_preservation",
        causal_containment_context(
            conflicting_observations=3,
            reliability=0.25,
        ),
    )

    assert report["integration_allowed"] is False
    assert report["causal_containment_active"] is True
    assert report["containment_state"] == (
        "CAUSAL_IDENTITY_CONFLICT_CONTAINED"
    )
    assert report["causal_identity_conflicts"][0]["source"] == (
        "density_preservation"
    )


def test_identity_safe_truth_integration_applies_semantic_containment():
    report = IdentitySafeTruthIntegrationEngine().evaluate(
        Belief(
            concept="unsafe_composite_truth",
            claim="unsafe_composite_truth",
            state=BeliefState.TRUTH_CANDIDATE,
            confidence=0.95,
        ),
        EvidenceAggregate(
            concept="unsafe_composite_truth",
            semantic_consistency=1.0,
            causal_alignment=1.0,
        ),
        {"eligible_for_truth_candidate": True},
        unsafe_merge_context(),
    )

    assert report["integration_safe"] is False
    assert report["semantic_containment"]["containment_active"] is True
    assert "semantic_containment_inactive" in report["failed_checks"]


def test_identity_integration_applies_accumulated_causal_containment():
    report = IdentitySafeTruthIntegrationEngine().evaluate(
        Belief(
            concept="topology_preservation",
            claim="topology_preservation",
            state=BeliefState.TRUTH_CANDIDATE,
            confidence=0.95,
        ),
        EvidenceAggregate(
            concept="topology_preservation",
            semantic_consistency=1.0,
            causal_alignment=1.0,
        ),
        {"eligible_for_truth_candidate": True},
        {
            "identity_continuity": 0.82,
            **causal_containment_context(
                conflicting_observations=3,
                reliability=0.25,
            ),
        },
    )

    assert report["integration_safe"] is False
    assert report["semantic_containment"]["causal_containment_active"] is True
    assert "semantic_containment_inactive" in report["failed_checks"]


def test_identity_integration_reports_drift_containment_separately():
    report = IdentitySafeTruthIntegrationEngine().evaluate(
        Belief(
            concept="topology_preservation",
            claim="topology_preservation",
            state=BeliefState.TRUTH_CANDIDATE,
            confidence=0.95,
        ),
        EvidenceAggregate(
            concept="topology_preservation",
            semantic_consistency=1.0,
            causal_alignment=1.0,
        ),
        {"eligible_for_truth_candidate": True},
        {
            "identity_continuity": 0.82,
            "epistemic_drift_regulation": {
                "truth_commit_blocked": True,
            },
        },
    )

    assert report["semantic_containment"]["integration_allowed"] is True
    assert "semantic_containment_inactive" not in report["failed_checks"]
    assert "epistemic_drift_containment_inactive" in report["failed_checks"]


def test_truth_commit_is_held_for_remembered_unsafe_merge():
    layer = EpistemicCognitionLayer()
    context = {
        **unsafe_merge_context(),
        "epistemic_hypotheses": [{
            "concept": "unsafe_composite_truth",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("unsafe_composite_truth", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
    }

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    commit = report["evaluations"][0]["truth_commit"]

    assert commit["decision"] == "REMAIN_BELIEF"
    assert "semantic_containment_inactive" in commit["reasons"]
    assert report["truth_commitments"] == []


def test_final_commit_preserves_locked_truth_when_only_stage_gate_differs():
    report = FinalCommitDecisionEngine().evaluate(
        {
            "belief_is_truth_candidate": False,
            "contradiction_below_limit": True,
            "causal_spine_alignment": True,
        },
        stable_truth_authority_locked=True,
    )

    assert report["decision"] == "TRUTH_COMMITTED"
    assert report["final_commit_state"] == "LOCKED_TRUTH_PRESERVED"
    assert report["effective_failed_gates"] == []


def test_final_commit_classifies_locked_truth_revocation_review_severity():
    engine = FinalCommitDecisionEngine()
    gates = {
        "belief_is_truth_candidate": False,
        "contradiction_below_limit": False,
    }

    low = engine.evaluate(
        gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1121,
    )
    medium = engine.evaluate(
        gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1355,
    )
    high = engine.evaluate(
        gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.18,
    )

    assert low["decision"] == "TRUTH_REVOCATION_REVIEW_REQUIRED"
    assert low["revocation_severity"] == "LOW_RISK_REVIEW"
    assert medium["revocation_severity"] == "MEDIUM_RISK_REVIEW"
    assert high["revocation_severity"] == "HIGH_RISK_REVIEW"


def test_locked_truth_uses_bounded_grace_period_for_low_risk_contradiction():
    engine = FinalCommitDecisionEngine(revocation_grace_period=2)
    gates = {
        "belief_is_truth_candidate": False,
        "contradiction_below_limit": False,
    }

    first = engine.evaluate(
        gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1044,
        truth_key="size_preservation",
    )
    second = engine.evaluate(
        gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1044,
        truth_key="size_preservation",
    )
    third = engine.evaluate(
        gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1044,
        truth_key="size_preservation",
    )

    assert first["decision"] == "TRUTH_COMMITTED"
    assert first["revocation_grace_period_active"] is True
    assert first["preventive_review_observation"] is True
    assert second["low_risk_review_streak"] == 2
    assert third["decision"] == "TRUTH_REVOCATION_REVIEW_REQUIRED"
    assert third["revocation_grace_period_active"] is False


def test_locked_truth_grace_period_resets_after_clear_observation():
    engine = FinalCommitDecisionEngine(revocation_grace_period=1)
    review_gates = {"contradiction_below_limit": False}
    clear_gates = {"contradiction_below_limit": True}

    engine.evaluate(
        review_gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1044,
        truth_key="size_preservation",
    )
    engine.evaluate(
        clear_gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.08,
        truth_key="size_preservation",
    )
    report = engine.evaluate(
        review_gates,
        stable_truth_authority_locked=True,
        contradiction_score=0.1044,
        truth_key="size_preservation",
    )

    assert report["decision"] == "TRUTH_COMMITTED"
    assert report["low_risk_review_streak"] == 1


def test_contradiction_review_policy_distinguishes_soft_zone_from_review():
    clear = classify_contradiction_review(0.098)
    low = classify_contradiction_review(0.1121)
    medium = classify_contradiction_review(0.122)

    assert clear["contradiction_review_required"] is False
    assert low["contradiction_review_required"] is True
    assert low["within_soft_review_zone"] is True
    assert low["contradiction_review_severity"] == "LOW_RISK_REVIEW"
    assert medium["contradiction_gap"] == 0.022
    assert medium["contradiction_review_required"] is True
    assert medium["within_soft_review_zone"] is False
    assert medium["contradiction_review_severity"] == (
        "MEDIUM_RISK_REVIEW"
    )


def test_adaptive_contradiction_governance_lifts_mature_reasoning_threshold():
    report = AdaptiveContradictionGovernance().evaluate(
        0.1159,
        {
            "knowledge_generalization": {
                "used_task_count": 31,
            },
            "causal_validation": {
                "validation_score": 0.8004,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8164,
            },
            "contextual_truth_authority": {
                "effective_contextual_truth": 0.6907,
                "contextual_truth_supported": True,
            },
            "causal_explanation": {
                "why": ["observed in 31 tasks"],
            },
            "causal_validation_report": {
                "how_we_know": ["validated across 34 tasks"],
            },
        },
    )

    assert report["dynamic_threshold"] >= 0.1159
    assert report["base_threshold"] == 0.10
    assert report["observed_count"] == 31
    assert report["validation_count"] == 34
    assert report["contradiction_below_dynamic_threshold"] is True


def test_final_commit_preserves_locked_truth_under_adaptive_threshold():
    governance = AdaptiveContradictionGovernance().evaluate(
        0.1346,
        {
            "knowledge_generalization": {
                "used_task_count": 71,
            },
            "causal_validation": {
                "validation_score": 0.8004,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8164,
            },
            "contextual_truth_authority": {
                "effective_contextual_truth": 0.6907,
                "contextual_truth_supported": True,
            },
            "causal_explanation": {
                "why": ["observed in 71 tasks"],
            },
            "causal_validation_report": {
                "how_we_know": ["validated across 74 tasks"],
            },
        },
        stable_truth_authority_locked=True,
    )
    report = FinalCommitDecisionEngine().evaluate(
        {
            "belief_is_truth_candidate": False,
            "contradiction_below_limit": False,
        },
        stable_truth_authority_locked=True,
        contradiction_score=0.1346,
        adaptive_contradiction_governance=governance,
    )

    assert governance["contradiction_below_dynamic_threshold"] is True
    assert report["decision"] == "TRUTH_COMMITTED"
    assert report["final_commit_state"] == "LOCKED_TRUTH_PRESERVED"
    assert report["effective_failed_gates"] == []


def test_adaptive_governance_v2_preserves_recovered_locked_truth():
    governance = AdaptiveContradictionGovernance().evaluate(
        0.1505,
        {
            "knowledge_generalization": {
                "used_task_count": 71,
                "validation_count": 74,
            },
            "causal_validation": {
                "validation_score": 0.8004,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8164,
            },
            "semantic_spine_recovery_report": {
                "recovery_state": "STABLE_SEMANTIC_SPINE",
                "recovery_streak": 113,
                "required_recovery_cycles": 3,
            },
        },
        stable_truth_authority_locked=True,
    )

    assert governance["dynamic_threshold"] >= 0.1505
    assert governance["threshold_cap"] == 0.16
    assert governance["recovery_bonus"] > 0
    assert governance["contradiction_below_dynamic_threshold"] is True


def test_contextual_truth_support_policy_softens_strong_context_boundary():
    support = ContextualTruthSupportPolicy().evaluate(
        contextual_truth={
            "contextual_truth_score": 0.6872,
        },
        contextual_truth_authority={
            "contextual_truth_authority": 0.6803,
        },
        context_hierarchy={
            "context_hierarchy_score": 0.94,
        },
        semantic_context={
            "semantic_context_score": 0.90,
        },
    )

    assert support["contextual_truth_supported"] is True
    assert abs(support["effective_support_floor"] - 0.685) < 0.0001
    assert support["strong_context_floor_applied"] is True


def test_identity_stabilization_unblocks_mature_reasoning_candidate():
    report = IdentityContinuityStabilizationPolicy().evaluate(
        {
            "truth_candidate_ready": False,
            "identity_stable": False,
            "semantic_spine_stable": False,
            "identity_continuity_above_limit": False,
            "identity_continuity_preserved": False,
            "semantic_drift_below_limit": False,
            "epistemic_drift_containment_inactive": False,
        },
        {
            "truth_candidate": {
                "concept": "symmetry_reasoning",
                "eligible_for_truth_candidate": True,
            },
            "adaptive_contradiction_governance": {
                "contradiction_below_dynamic_threshold": True,
            },
            "contextual_truth_authority": {
                "contextual_truth_supported": True,
                "effective_contextual_truth": 0.6904,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8157,
            },
            "causal_validation": {
                "validation_score": 0.7988,
            },
        },
        concept="symmetry_reasoning",
        observed_count=31,
        validation_count=34,
    )

    assert report["stabilization_ready"] is True
    assert report["adjusted_gates"]["truth_candidate_ready"] is True
    assert report["adjusted_gates"]["identity_stable"] is True
    assert report["adjusted_gates"]["semantic_spine_stable"] is True
    assert (
        report["adjusted_gates"]["identity_continuity_above_limit"]
        is True
    )
    assert (
        report["adjusted_gates"]["identity_continuity_preserved"]
        is True
    )
    assert report["adjusted_gates"]["semantic_drift_below_limit"] is True
    assert (
        report["adjusted_gates"]["epistemic_drift_containment_inactive"]
        is True
    )


def object_identity_phase_58_context(recovery_report=None):
    context = {
        "concept": "object_identity_preservation",
        "truth_candidate": {
            "concept": "object_identity_preservation",
            "eligible_for_truth_candidate": True,
        },
        "adaptive_contradiction_governance": {
            "observed_count": 29,
            "validation_count": 29,
            "contradiction_below_dynamic_threshold": True,
        },
        "contextual_truth_authority": {
            "contextual_truth_supported": True,
            "effective_contextual_truth": 0.7756,
        },
        "contextual_truth": {
            "effective_contextual_truth": 0.7756,
            "contextual_truth_score": 0.7756,
        },
        "context_hierarchy": {
            "context_hierarchy_score": 0.94,
            "hierarchy_ready": True,
        },
        "semantic_context": {
            "semantic_context_score": 0.90,
            "semantically_validated": True,
        },
        "causal_graph_alignment": {
            "alignment_score": 0.8157,
        },
        "causal_validation": {
            "validation_score": 0.7988,
        },
    }
    if recovery_report is not None:
        context["semantic_spine_recovery_report"] = recovery_report
    return context


def test_object_identity_waits_for_three_recovery_cycles_before_phase_59():
    blocked_gates = {
        "belief_is_truth_candidate": False,
        "minimum_trials": False,
        "identity_stable": False,
        "semantic_spine_stable": False,
        "identity_continuity_above_limit": False,
        "identity_continuity_preserved": False,
        "semantic_drift_below_limit": False,
        "epistemic_drift_containment_inactive": False,
    }

    awaiting_recovery = KnowledgePromotionPolicy().evaluate(
        blocked_gates,
        object_identity_phase_58_context({
            "recovery_state": "RECOVERY_MONITORING",
            "recovery_streak": 2,
            "required_recovery_cycles": 3,
            "semantic_spine_recovery_confirmed": False,
        }),
    )

    assert awaiting_recovery["phase"] == "5.9"
    assert awaiting_recovery[
        "requires_phase_5_8_identity_continuity_stabilization"
    ] is True
    assert awaiting_recovery["promotion_ready"] is True
    assert awaiting_recovery["identity_continuity_stabilization"][
        "identity_recovery_required"
    ] is True
    assert awaiting_recovery["identity_continuity_stabilization"][
        "identity_recovery_ready"
    ] is False
    assert awaiting_recovery["adjusted_gates"][
        "belief_is_truth_candidate"
    ] is True
    assert awaiting_recovery["adjusted_gates"]["minimum_trials"] is True
    assert awaiting_recovery["adjusted_gates"]["identity_stable"] is False
    assert awaiting_recovery["adjusted_gates"][
        "semantic_spine_stable"
    ] is False
    assert awaiting_recovery["adjusted_gates"][
        "identity_continuity_above_limit"
    ] is False
    assert awaiting_recovery["adjusted_gates"][
        "epistemic_drift_containment_inactive"
    ] is False

    recovered = KnowledgePromotionPolicy().evaluate(
        blocked_gates,
        object_identity_phase_58_context({
            "recovery_state": "STABLE_SEMANTIC_SPINE",
            "recovery_streak": 3,
            "required_recovery_cycles": 3,
            "semantic_spine_recovery_confirmed": True,
        }),
    )

    assert recovered["identity_continuity_stabilization"][
        "identity_recovery_ready"
    ] is True
    assert recovered["adjusted_gates"]["identity_stable"] is True
    assert recovered["adjusted_gates"]["semantic_spine_stable"] is True
    assert recovered["adjusted_gates"][
        "identity_continuity_above_limit"
    ] is True
    assert recovered["adjusted_gates"][
        "epistemic_drift_containment_inactive"
    ] is True


def test_identity_integration_stabilizes_stage_only_mature_candidate():
    candidate = {
        "concept": "symmetry_reasoning",
        "eligible_for_truth_candidate": False,
        "metrics_eligible_for_truth_candidate": True,
        "qualified_metrics": True,
        "blocked_metrics": [],
        "eligibility_reason": "validated_stage_required",
        "adaptive_contradiction_governance": {
            "contradiction_below_dynamic_threshold": True,
            "observed_count": 31,
            "validation_count": 34,
        },
    }
    report = IdentitySafeTruthIntegrationEngine().evaluate(
        Belief(
            concept="symmetry_reasoning",
            claim="symmetry_reasoning",
            state=BeliefState.SUPPORTED,
            confidence=0.95,
        ),
        EvidenceAggregate(
            concept="symmetry_reasoning",
            semantic_consistency=1.0,
            causal_alignment=0.82,
        ),
        candidate,
        {
            "identity_stability_report": {
                "identity_stability_state": "fragile_semantic_spine",
            },
            "identity_continuity": 0.55,
            "semantic_drift": 0.61,
            "knowledge_generalization": {
                "used_task_count": 31,
                "validation_count": 34,
            },
            "contextual_truth_authority": {
                "contextual_truth_supported": True,
                "effective_contextual_truth": 0.6904,
            },
            "contextual_truth": {
                "effective_contextual_truth": 0.6904,
                "contextual_truth_score": 0.6904,
            },
            "context_hierarchy": {
                "context_hierarchy_score": 0.94,
                "hierarchy_ready": True,
            },
            "semantic_context": {
                "semantic_context_score": 0.90,
                "semantically_validated": True,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8157,
            },
            "causal_validation": {
                "validation_score": 0.7988,
            },
        },
    )

    assert report["integration_safe"] is True
    assert report["integration_state"] in [
        "IDENTITY_SAFE_TRUTH",
        "IDENTITY_REINFORCING_TRUTH",
    ]
    assert report["identity_continuity_stabilization"][
        "stabilization_ready"
    ] is True
    assert "truth_candidate_ready" not in report["failed_checks"]
    assert "identity_continuity_preserved" not in report["failed_checks"]


def test_identity_stabilization_respects_explicit_identity_block():
    report = IdentityContinuityStabilizationPolicy().evaluate(
        {
            "identity_stable": False,
            "semantic_spine_stable": False,
        },
        {
            "identity_stable": False,
            "truth_candidate": {
                "concept": "symmetry_reasoning",
                "eligible_for_truth_candidate": True,
            },
            "adaptive_contradiction_governance": {
                "contradiction_below_dynamic_threshold": True,
            },
            "contextual_truth_authority": {
                "contextual_truth_supported": True,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.8157,
            },
            "causal_validation": {
                "validation_score": 0.7988,
            },
        },
        concept="symmetry_reasoning",
        observed_count=31,
        validation_count=34,
    )

    assert report["stabilization_ready"] is False
    assert report["adjusted_gates"]["identity_stable"] is False


def test_knowledge_promotion_policy_uses_accumulated_validations():
    report = KnowledgePromotionPolicy().evaluate(
        {
            "belief_is_truth_candidate": False,
            "minimum_trials": False,
            "identity_stable": True,
            "semantic_spine_stable": True,
        },
        {
            "truth_candidate": {
                "eligible_for_truth_candidate": True,
            },
            "adaptive_contradiction_governance": {
                "observed_count": 31,
                "validation_count": 34,
                "contradiction_below_dynamic_threshold": True,
            },
            "contextual_truth_authority": {
                "contextual_truth_supported": True,
            },
        },
    )

    assert report["promotion_ready"] is True
    assert report["adjusted_gates"]["belief_is_truth_candidate"] is True
    assert report["adjusted_gates"]["minimum_trials"] is True
    assert report["overrides"] == {
        "belief_is_truth_candidate": "ACCUMULATED_VALIDATION_PROMOTION",
        "minimum_trials": "ACCUMULATED_VALIDATION_PROMOTION",
    }


def test_knowledge_promotion_policy_preserves_stable_truth_identity_hold():
    report = KnowledgePromotionPolicy().evaluate(
        {
            "minimum_trials": False,
            "semantic_drift_below_limit": False,
            "identity_continuity_above_limit": False,
            "mutation_rehearsal_safe": True,
        },
        {
            "adaptive_contradiction_governance": {
                "contradiction_below_dynamic_threshold": True,
            },
            "contextual_truth_authority": {
                "contextual_truth_supported": True,
            },
            "semantic_spine_recovery_report": {
                "recovery_state": "STABLE_SEMANTIC_SPINE",
                "recovery_streak": 107,
                "required_recovery_cycles": 3,
            },
        },
        stable_truth_authority_locked=True,
    )

    assert report["preservation_ready"] is True
    assert report["adjusted_gates"]["minimum_trials"] is True
    assert report["adjusted_gates"]["semantic_drift_below_limit"] is True
    assert (
        report["adjusted_gates"]["identity_continuity_above_limit"]
        is True
    )
    assert report["overrides"] == {
        "minimum_trials": "STABLE_TRUTH_PRESERVATION_LOCK",
        "semantic_drift_below_limit": "STABLE_TRUTH_PRESERVATION_LOCK",
        "identity_continuity_above_limit":
        "STABLE_TRUTH_PRESERVATION_LOCK",
    }


def test_knowledge_promotion_policy_preserves_mature_locked_truth():
    report = KnowledgePromotionPolicy().evaluate(
        {
            "minimum_trials": False,
            "semantic_drift_below_limit": False,
            "identity_continuity_above_limit": False,
            "contextual_truth_score": False,
        },
        {
            "adaptive_contradiction_governance": {
                "observed_count": 71,
                "validation_count": 74,
                "contradiction_below_dynamic_threshold": True,
            },
            "contextual_truth": {
                "contextual_truth_score": 0.5907,
            },
            "semantic_spine_recovery_report": {
                "recovery_state": "STABLE_SEMANTIC_SPINE",
                "recovery_streak": 113,
                "required_recovery_cycles": 3,
            },
        },
        stable_truth_authority_locked=True,
    )

    assert report["preservation_ready"] is True
    assert report["mature_stable_truth_preservation"] is True
    assert report["adjusted_gates"]["minimum_trials"] is True
    assert report["adjusted_gates"]["semantic_drift_below_limit"] is True
    assert (
        report["adjusted_gates"]["identity_continuity_above_limit"]
        is True
    )
    assert report["adjusted_gates"]["contextual_truth_score"] is True
