from core.cognitive_health.physician_engine import (
    CognitivePhysicianEngine,
)

from core.governance_compression.governance_kernel import (
    GovernanceKernel,
)


def test_cognitive_physician_diagnoses_overload_without_control():

    physician = CognitivePhysicianEngine()

    report = physician.run_cycle({
        "runtime_entropy": 0.88,
        "identity_drift": 0.52,
        "raw_reasoning_depth": 11,
        "semantic_fragmentation": 0.78,
        "memory_pressure_score": 0.81,
        "latent_conflict_density": 0.72,
        "fusion_failure_rate": 0.64,
        "constitutional_stability": 0.46,
    })

    assert report["system"] == "cognitive_physician_engine"

    assert report["non_emotional_system"] is True

    assert report["authority"] == "advisory_only"

    assert (
        report["diagnosis_report"]["state"]
        in report["diagnosis_report"]["known_states"]
    )

    assert (
        report["diagnosis_report"]["risk_escalation"]
        in [
            "elevated",
            "critical",
        ]
    )

    assert (
        report["dosage_controller"]["dosage_is_static"]
        is False
    )

    assert (
        report["governance_submission"][
            "physician_can_bypass_governance"
        ]
        is False
    )

    assert (
        report["constitutional_safety_assessment"][
            "final_authority"
        ]
        ==
        "governance_kernel"
    )


def test_dependency_monitor_reduces_treatment_strength():

    physician = CognitivePhysicianEngine()

    dependent = physician.run_cycle({
        "runtime_entropy": 0.72,
        "identity_drift": 0.40,
        "sedation_reliance": 0.90,
        "rollback_usage_rate": 0.84,
        "exploration_suppression_rate": 0.88,
        "stabilization_dependence": 0.86,
    })

    assert (
        dependent["dependency_alerts"]["dependency_detected"]
        is True
    )

    assert (
        dependent["adaptive_regulation"]["regulation_posture"]
        ==
        "restore_cognitive_flexibility"
    )

    assert (
        dependent["homeostasis_controller"]["maximizes_stability"]
        is False
    )


def test_governance_kernel_reviews_physician_recommendations():

    physician = CognitivePhysicianEngine()
    kernel = GovernanceKernel()

    physician_report = physician.run_cycle({
        "runtime_entropy": 0.86,
        "identity_drift": 0.60,
        "memory_pressure_score": 0.80,
        "semantic_fragmentation": 0.74,
    })

    report = kernel.run_cycle({
        "cognitive_physician_report": physician_report,
        "runtime_entropy": 0.86,
    })

    review = report["physician_review"]

    assert review["governance_kernel_final_authority"] is True

    assert review["physician_authority"] == "advisor_only"

    assert (
        "physician_recommendations_require_governance_review"
        in report["policies"]
    )

    assert "cognitive_physician_review_required" in [
        signal.get(
            "signal",
        )
        for signal in report["signals"]
    ]
