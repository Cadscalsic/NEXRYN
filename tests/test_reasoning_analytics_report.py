from runtime.analytics import reasoning_quality_analytics_builder
from runtime.reasoning.reasoning_graph_report import ReasoningGraphReportBuilder


def _reasoning_graph_report():
    cognitive_report = {
        "average_confidence": 0.76,
        "hypotheses": [
            {
                "hypothesis_id": "h:color",
                "claim": "color remapping solves task",
                "creation_reason": "palette delta",
                "supporting_evidence": ["palette changed"],
                "confidence": 0.91,
                "required_capabilities": ["color_mapping"],
                "validation_status": "validated",
            },
            {
                "hypothesis_id": "h:shape",
                "claim": "shape expansion solves task",
                "creation_reason": "shape delta",
                "supporting_evidence": ["weak shape evidence"],
                "confidence": 0.28,
                "required_capabilities": ["spatial_reasoning"],
                "validation_status": "rejected",
                "rejection_reason": "prediction residual too high",
            },
        ],
        "capability_contribution": [
            {"capability": "color_mapping", "contribution_percent": 78.0},
            {"capability": "spatial_reasoning", "contribution_percent": 22.0},
        ],
        "reasoning_graph": {
            "branches": [
                {
                    "branch_id": "branch:color",
                    "starting_assumption": "h:color",
                    "intermediate_decisions": ["ranked_first"],
                    "final_result": "dominant",
                },
                {
                    "branch_id": "branch:shape",
                    "starting_assumption": "h:shape",
                    "intermediate_decisions": ["ranked_second"],
                    "final_result": "abandoned",
                },
            ],
        },
    }
    capability_report = {
        "capabilities_executed": ["color_mapping", "spatial_reasoning"],
        "capability_confidence": {
            "color_mapping": 0.94,
            "spatial_reasoning": 0.34,
        },
        "cooperation_events": [
            {
                "source_capability": "color_mapping",
                "target_capability": "spatial_reasoning",
            },
        ],
        "reusable_assets": {
            "successful_strategies": [{"strategy_id": "color_strategy"}],
            "successful_validation_patterns": [{"pattern": "exact_match"}],
        },
    }
    return ReasoningGraphReportBuilder().build_report(
        cognitive_analytics_report=cognitive_report,
        cognitive_capability_report=capability_report,
        causal_context_report={
            "CAUSAL_CONTEXT_REPORT": True,
            "average_confidence": 0.82,
            "cause_effect_pairs": [
                {
                    "cause": "palette_delta",
                    "effect": "replace_color",
                    "confidence": 0.82,
                },
            ],
        },
        dependency_audit_report={"injected_dependencies": ["palette_rule"]},
        context_validation_report={"reports": [{"valid": True}]},
    )


def test_reasoning_analytics_report_scores_reasoning_quality():
    graph_report = _reasoning_graph_report()

    report = reasoning_quality_analytics_builder.build_report(
        reasoning_graph_report=graph_report,
        cognitive_analytics_report={
            "capability_contribution": [
                {
                    "capability": "color_mapping",
                    "contribution_percent": 78.0,
                },
                {
                    "capability": "spatial_reasoning",
                    "contribution_percent": 22.0,
                },
            ],
        },
        reasoning_intelligence_report={
            "decision_log": [
                {
                    "decision_id": "decision:h:color",
                    "hypothesis_id": "h:color",
                    "why_survived": "validated confidence and evidence",
                    "why_competing_hypotheses_failed": "shape residual",
                    "evidence_changed_confidence": ["palette_delta"],
                    "confidence": 0.91,
                },
            ],
        },
        performance_report={
            "reasoning_time_seconds": 0.4,
            "color_mapping_time_seconds": 0.05,
        },
        cognitive_capability_report={
            "capabilities_executed": ["color_mapping", "spatial_reasoning"],
            "capability_confidence": {
                "color_mapping": 0.94,
                "spatial_reasoning": 0.34,
            },
            "cooperation_events": [
                {
                    "source_capability": "color_mapping",
                    "target_capability": "spatial_reasoning",
                },
            ],
            "reusable_assets": {
                "successful_strategies": [{"strategy_id": "color_strategy"}],
            },
        },
        context_validation_report={"reports": [{"valid": True}]},
        adaptive_reuse_report={"strategy_hits": 2},
    )

    assert report["REASONING_ANALYTICS_REPORT"] is True
    assert 0.0 <= report["reasoning_quality_score"] <= 1.0
    assert report["reasoning_health"] in {
        "Excellent",
        "Good",
        "Stable",
        "Weak",
        "Critical",
    }
    assert report["hypothesis_statistics"]["hypotheses_generated"] == 2
    assert report["hypothesis_statistics"]["hypotheses_rejected"] == 1
    assert report["rejected_hypothesis_analysis"][0]["why_rejected"]
    assert report["capability_statistics"]["color_mapping"][
        "capability_influence_score"
    ] > report["capability_statistics"]["spatial_reasoning"][
        "capability_influence_score"
    ]
    assert report["decision_quality"]["decisions"][0]["later_confirmed"] is True
    assert report["quality_dashboard"]["most_useful_capability"] == "color_mapping"
    assert report["learning_opportunities"]


def test_reasoning_analytics_report_handles_sparse_graph():
    report = reasoning_quality_analytics_builder.build_report(
        reasoning_graph_report={
            "REASONING_GRAPH_REPORT": True,
            "reasoning_graph": {"nodes": [], "edges": []},
            "hypotheses": [],
            "graph_size": {"nodes": 0, "edges": 0},
        },
        performance_report={},
    )

    assert report["REASONING_ANALYTICS_REPORT"] is True
    assert report["profiling_overhead"]["additional_solver_calls"] == 0
    assert report["quality_warnings"]
