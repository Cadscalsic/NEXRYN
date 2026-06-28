from runtime.execution.world_model_gate import WorldModelGate
from runtime.governance.world_governance_introspection import (
    WorldGovernanceIntrospection,
)


def high_quality_rejected_learning_event():
    return {
        "execution_accepted": False,
        "sandbox_execution_accepted": False,
        "acceptance_state": "SEARCH_CANDIDATE_ONLY",
        "prediction_accuracy": 0.92,
        "evaluation_success": True,
        "episode_completed": True,
        "prediction_report": {
            "prediction_accuracy": 0.92,
            "partial_success": True,
            "success_state": "PARTIAL_SUCCESS",
        },
        "dependency_confidence": 0.88,
        "cross_task_stability": 0.87,
        "contradiction_score": 0.02,
        "observation_count": 42,
    }


def test_world_model_rejection_becomes_explainable_sandbox_learning_credit():
    report = WorldModelGate().evaluate(high_quality_rejected_learning_event())

    introspection = report["WORLD GOVERNANCE INTROSPECTION REPORT"]
    assert report["execution_authorized"] is False
    assert report["sandbox_execution_authorized"] is True
    assert report["gate_state"] == "EXECUTION_ROUTED_TO_SANDBOX"
    assert report["learning_credit_authorized"] is True
    assert introspection["decision"] == "ALLOW_SANDBOX"
    assert introspection["sandbox_eligible"] is True
    assert introspection["false_rejection_probability"] >= 0.65
    assert introspection["potential_governance_overreach"] is True
    assert introspection["risk_category"] in {
        "Confidence Deficit",
        "Evidence Deficit",
        "Unknown Reason",
    }


def test_world_model_gate_allows_probation_execution_after_grounding_recovery():
    event = high_quality_rejected_learning_event()
    event.update({
        "residual_locations": [(1, 2), (2, 2)],
        "localized_synthesized_program": {
            "step_count": 1,
            "steps": [{
                "operation": "replace_color",
                "parameters": {},
            }],
        },
        "transformation_localization": {
            "localization_ready": False,
            "localization_confidence": 0.1675,
            "localized_step_count": 0,
            "target_objects": [],
            "localization_reports": [],
        },
        "execution_integrity_report": {
            "integrity_preserved": True,
        },
    })

    report = WorldModelGate().evaluate(event)

    assert report["gate_state"] == "EXECUTION_PROBATION"
    assert report["sandbox_execution_authorized"] is True
    assert report["execution_authorized"] is False
    assert report["probation_execution"] is True
    assert report["LOCALIZATION_REPORT"]["target_objects"]
    assert report["LOCALIZATION_REPORT"]["EXECUTION READINESS REPORT"][
        "readiness_class"
    ] == "EXECUTION_PROBATION"


def test_critical_identity_risk_still_denies_execution():
    event = high_quality_rejected_learning_event()
    event["identity_runtime_state"] = "UNSTABLE"

    report = WorldModelGate().evaluate(event)
    introspection = report["WORLD GOVERNANCE INTROSPECTION REPORT"]

    assert report["execution_authorized"] is False
    assert report["sandbox_execution_authorized"] is False
    assert introspection["decision"] == "DENY"
    assert introspection["risk_category"] == "Identity Protection"
    assert introspection["critical_governance_risk"] is True


def test_adaptive_truth_thresholds_lower_with_strong_evidence():
    report = WorldGovernanceIntrospection().adaptive_truth_thresholds({
        "observation_count": 80,
        "dependency_support": 0.91,
        "cross_task_stability": 0.92,
        "contradiction_score": 0.01,
    })

    assert report["threshold_lowered"] is True
    assert report["required_truth_threshold"] < report["base_truth_threshold"]
    assert report["required_truth_threshold"] >= 0.84


def test_false_rejection_audit_flags_successful_rejected_episode():
    audit = WorldGovernanceIntrospection().audit_false_rejection(
        {
            "execution_authorized": False,
            "sandbox_execution_authorized": False,
            "gate_state": "EXECUTION_ABORTED_WORLD_MODEL_REJECTION",
        },
        {
            "success": True,
            "episode_completed": True,
            "accuracy": 0.92,
        },
    )

    assert audit["potential_governance_overreach"] is True
    assert audit["false_rejection_probability"] >= 0.65
