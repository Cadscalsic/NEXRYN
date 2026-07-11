from runtime.world_governance import (
    CognitiveIntelligenceAnalytics,
    WorldKernel,
)


def test_cia_generates_cognitive_kpis_and_summary():
    analytics = CognitiveIntelligenceAnalytics()

    report = analytics.analyze({
        "execution_progress": 0.8,
        "resource_consumption": 0.35,
        "confidence_values": [0.78, 0.84],
        "evidence_growth": 4,
        "truth_growth": 2,
        "knowledge_density": 0.7,
        "decision_confidence": 0.82,
        "decision_utility": 0.75,
        "policy_confidence": 0.8,
        "policy_selection_score": 0.76,
        "memory_utilization": 0.65,
        "memory_promotion": 0.6,
    })

    cia = report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]

    assert cia["Executive Summary"]["overall_score"] > 0
    assert cia["Cognitive KPIs"]["Overall Cognitive Intelligence"] > 0
    assert cia["Execution Health"]["Analytical Conclusion"]
    assert cia["Truth Health"]["Recommendation"]
    assert cia["World Model Readiness"]["readiness_score"] >= 0
    assert cia["DNA Evolution Readiness"]["readiness_score"] >= 0


def test_cia_detects_anomalies_and_root_causes():
    analytics = CognitiveIntelligenceAnalytics()

    report = analytics.analyze({
        "execution_progress": 0.1,
        "resource_consumption": 0.9,
        "confidence_values": [0.15],
        "evidence_growth": 0,
        "truth_candidates": 8,
        "truth_promotion_rate": 0.1,
        "memory_utilization": 0.0,
        "memory_promotion": 0.0,
        "decision_confidence": 0.2,
        "decision_utility": 0.2,
        "policy_confidence": 0.2,
        "policy_selection_score": 0.2,
    })

    cia = report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]

    assert cia["Detected Anomalies"]
    assert cia["Root Cause Analysis"]
    assert cia["Recommended Actions"]
    assert any(
        item["anomaly_type"] == "resource_waste"
        for item in cia["Detected Anomalies"]
    )


def test_cia_truth_bottleneck_recommendation_is_interpretable():
    analytics = CognitiveIntelligenceAnalytics()

    report = analytics.analyze({
        "truth_candidates": 18,
        "truth_validation_rate": 0.35,
        "truth_promotion_rate": 0.2,
        "confidence_values": [0.5],
        "evidence_growth": 1,
    })

    truth = report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]["Truth Health"]

    assert truth["Insight"].startswith("18 Truth Candidates generated")
    assert truth["Recommendation"] == "increase evidence quality before promotion"


def test_cia_tracks_trends_and_predictions():
    analytics = CognitiveIntelligenceAnalytics()
    analytics.analyze({
        "execution_progress": 0.4,
        "confidence_values": [0.4],
        "decision_confidence": 0.4,
        "policy_confidence": 0.4,
    })

    report = analytics.analyze({
        "execution_progress": 0.8,
        "confidence_values": [0.8],
        "decision_confidence": 0.8,
        "decision_utility": 0.75,
        "policy_confidence": 0.8,
        "policy_selection_score": 0.75,
        "evidence_growth": 3,
        "truth_growth": 2,
        "memory_utilization": 0.7,
    })

    cia = report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]

    assert cia["Trend Analysis"]["Overall Trend Delta"] != 0
    assert cia["Predictive Analysis"]["Prediction Measurable"] is True
    assert "Expected World Model Readiness" in cia["Predictive Analysis"]


def test_world_kernel_exposes_cia_report():
    kernel = WorldKernel()

    report = kernel.analyze_cognitive_intelligence({
        "execution_progress": 0.7,
        "confidence_values": [0.75],
        "decision_confidence": 0.7,
        "policy_confidence": 0.7,
    })
    world_report = kernel.build_report()

    assert report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]["Cognitive KPIs"]
    assert world_report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"][
        "Cognitive KPIs"
    ]


def test_governed_cycle_generates_cia_report():
    kernel = WorldKernel()

    report = kernel.govern_cognitive_cycle(
        {
            "goal": "analytics_cycle",
            "difficulty": 0.6,
            "novelty": 0.6,
            "risk_level": 0.3,
        },
        runtime_events=[
            {
                "runtime_id": "evidence_builder",
                "confidence": 0.72,
                "progress": 0.75,
                "evidence_growth": 4,
                "truth_growth": 2,
                "knowledge_density": 0.7,
                "resource_consumption": 0.4,
            }
        ],
        execution_result={"success": True},
    )

    cia = report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]

    assert cia["Execution Health"]["Execution Intelligence Score"] > 0
    assert cia["Decision Health"]["Decision Quality"] >= 0
    assert cia["Policy Health"]["Policy Evolution"] >= 0
