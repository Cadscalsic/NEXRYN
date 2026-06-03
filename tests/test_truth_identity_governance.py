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
