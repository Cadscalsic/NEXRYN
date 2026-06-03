from core.cognitive_health.physician_engine import (
    CognitivePhysicianEngine,
)

from core.cognitive_pharmacy.pharmacy_engine import (
    CognitivePharmacyEngine,
)

from core.governance_compression.governance_kernel import (
    GovernanceKernel,
)


def _physician_report():

    physician = CognitivePhysicianEngine()

    return physician.run_cycle({
        "runtime_entropy": 0.86,
        "identity_drift": 0.55,
        "raw_reasoning_depth": 10,
        "semantic_fragmentation": 0.74,
        "memory_pressure_score": 0.78,
        "latent_conflict_density": 0.69,
        "fusion_failure_rate": 0.60,
    })


def test_pharmacy_blocks_medication_without_governance_approval():

    pharmacy = CognitivePharmacyEngine()

    report = pharmacy.run_cycle({
        "cognitive_physician_report": _physician_report(),
        "governance_physician_review": {
            "approved_for_controlled_execution": False,
        },
    })

    assert report["governance_required"] is True

    assert (
        report["pharmacological_ethics"][
            "constitutional_state"
        ]
        ==
        "administration_blocked_pending_governance"
    )

    assert all(
        item["administered_dose"] == 0.0
        for item in report["medication_administration"][
            "administrations"
        ]
    )

    assert (
        report["medication_administration"][
            "direct_runtime_mutation"
        ]
        is False
    )


def test_pharmacy_administers_controlled_dynamic_dosage_after_kernel_review():

    physician_report = _physician_report()
    kernel = GovernanceKernel()
    pharmacy = CognitivePharmacyEngine()

    governance = kernel.run_cycle({
        "cognitive_physician_report": physician_report,
        "runtime_entropy": 0.86,
    })

    report = pharmacy.run_cycle({
        "cognitive_physician_report": physician_report,
        "governance_physician_review": governance[
            "physician_review"
        ],
    })

    assert (
        report["dosage_plan"]["dosage_is_static"]
        is False
    )

    assert (
        report["pharmacological_ethics"][
            "constitutional_state"
        ]
        ==
        "administration_constitutionally_bounded"
    )

    assert any(
        item["administered_dose"] > 0.0
        for item in report["medication_administration"][
            "administrations"
        ]
    )

    assert (
        report["homeostasis_model"]["goal"]
        ==
        "ADAPTIVE_COGNITIVE_EQUILIBRIUM"
    )

    assert (
        report["homeostasis_model"]["maximizes_stability"]
        is False
    )


def test_pharmacy_detects_dependency_and_rebound():

    physician_report = _physician_report()
    pharmacy = CognitivePharmacyEngine()

    report = pharmacy.run_cycle({
        "cognitive_physician_report": physician_report,
        "governance_physician_review": {
            "approved_for_controlled_execution": True,
        },
        "pharmacy_dependency_accumulation": 0.90,
        "sedation_reliance": 0.92,
        "rollback_usage_rate": 0.80,
        "exploration_suppression_rate": 0.86,
        "previous_pharmacy_report": {
            "dosage_plan": {
                "SEMANTIC_SEDATIVE": 0.95,
            },
        },
        "semantic_noise": 0.70,
    })

    assert (
        report["dependency_prevention"]["dependency_detected"]
        is True
    )

    assert (
        report["adaptive_pharmacology"][
            "long_term_dependency_avoided"
        ]
        is False
    )

    assert "semantic_entropy" in report[
        "visual_dashboards"
    ]

    assert report["side_effect_monitor"][
        "side_effect_count"
    ] >= 1
