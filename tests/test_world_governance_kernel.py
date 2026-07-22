import pytest

from runtime.world_governance import (
    CapabilityPromotionPolicyEngine,
    CONSTITUTIONAL_IDENTITY,
    WorldKernel,
)


def test_constitutional_identity_is_immutable():
    with pytest.raises(TypeError):
        CONSTITUTIONAL_IDENTITY["truth_priority"] = "changed"


def test_protected_core_modification_is_blocked():
    kernel = WorldKernel()

    decision = kernel.evaluate_world_change({
        "candidate_name": "unsafe_truth_override",
        "candidate_type": "program",
        "modifies": ["truth_priority"],
        "runtime_efficiency": 0.9,
    })

    assert decision.decision == "PROTECT_CORE"
    assert decision.allowed is False
    assert decision.requires_review is True
    assert "modify_constitutional_principles" in decision.blocked_actions


def test_new_useful_concept_starts_as_candidate():
    kernel = WorldKernel()

    decision = kernel.evaluate_concept_admission({
        "candidate_name": "relational_color_anchor",
        "generalization": 0.4,
        "identity_risk": 0.1,
        "truth_risk": 0.1,
        "governance_risk": 0.1,
    })

    assert decision.decision == "ADMIT"
    assert decision.admission_level == "CANDIDATE"
    assert "relational_color_anchor" in kernel.world_state.admitted_concepts


def test_reusable_strategy_can_become_trusted_tool():
    kernel = WorldKernel()

    decision = kernel.evaluate_strategy_admission({
        "candidate_name": "symmetry_reuse_probe",
        "admission_level": "TRUSTED_TOOL",
        "strategy_reuse": 0.8,
        "successful_observations": 3,
        "reusable": True,
        "identity_risk": 0.1,
        "truth_risk": 0.1,
        "governance_risk": 0.1,
    })

    assert decision.decision == "ADMIT_WITH_LIMITS"
    assert decision.admission_level == "TRUSTED_TOOL"
    assert kernel.world_state.admitted_strategies["symmetry_reuse_probe"] == "TRUSTED_TOOL"


def test_locked_core_cannot_be_granted_automatically():
    kernel = WorldKernel()

    decision = kernel.evaluate_concept_admission({
        "candidate_name": "identity_helper",
        "admission_level": "LOCKED_CORE",
        "identity_supporting": True,
        "stable": True,
        "successful_observations": 100,
        "contextual_understanding": 0.9,
    })

    assert decision.decision == "REQUIRE_MORE_EVIDENCE"
    assert decision.admission_level == "IDENTITY_SUPPORTING_COMPONENT"
    assert decision.allowed is False
    assert decision.requires_review is True


def test_report_contains_required_world_governance_fields():
    kernel = WorldKernel()
    kernel.evaluate_concept_admission({
        "candidate_name": "process_bridge",
        "process_understanding": 0.5,
    })

    report = kernel.build_report()["WORLD_GOVERNANCE_REPORT"]

    assert report["candidate_name"] == "process_bridge"
    assert report["candidate_type"] == "concept"
    assert "allowed_actions" in report
    assert "blocked_actions" in report
    assert report["protected_core_touched"] is False


def test_world_governance_relaxes_only_sandbox_citizenship_policy():
    policy = CapabilityPromotionPolicyEngine().decide({
        "generated_survival_candidate_count": 79,
        "operational_citizen_count": 1,
        "operational_domain_citizenship_coverage": 0.1429,
        "domain_monopoly_share": 1.0,
        "generated_to_citizen_pressure_ratio": 79.0,
        "capability_crystallization_state": "SEVERE_CRYSTALLIZATION_FAILURE",
    }).as_dict()

    assert policy["policy_state"] == "RELAX_SANDBOX_CITIZENSHIP"
    assert policy["sandbox_citizenship_thresholds"] == {
        "min_distinct_tasks": 3,
        "min_arena_quality_count": 3,
        "min_average_accuracy": 0.8,
        "min_best_accuracy": 0.0,
        "allowed_trends": [
            "STABLE",
            "IMPROVING",
            "STABLE_HIGH_PERFORMANCE",
            "DECLINING_MINOR",
        ],
    }
    assert policy["authority_boundary"]["citizenship_authority"] == "SANDBOX_ONLY"
    assert policy["authority_boundary"]["trusted_for_decision"] is False
    assert policy["trusted_capability_policy"]["policy_state"] == (
        "STRICT_REVIEW_REQUIRED"
    )
    assert policy["decision_authority_policy"][
        "automatic_authority_transfer"
    ] is False
