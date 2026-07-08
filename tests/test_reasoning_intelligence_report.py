from runtime.analytics import reasoning_intelligence_builder


def test_reasoning_intelligence_report_profiles_reasoning_episode():
    cognitive_report = {
        "COGNITIVE_ANALYTICS_REPORT": True,
        "reasoning_summary": "Observed 2 hypotheses.",
        "reasoning_depth": 3,
        "reasoning_width": 2,
        "branching_factor": 0.667,
        "reasoning_iterations": 2,
        "reasoning_convergence": "h:win",
        "average_confidence": 0.72,
        "hypothesis_statistics": {
            "hypotheses_generated": 2,
            "hypotheses_validated": 1,
            "hypotheses_rejected": 1,
            "hypotheses_merged": 0,
            "hypotheses_reactivated": 0,
            "hypotheses_remaining": 0,
        },
        "hypotheses": [
            {
                "hypothesis_id": "h:win",
                "claim": "color rule solves task",
                "creation_reason": "generated_hypotheses",
                "supporting_evidence": ["palette delta"],
                "confidence": 0.91,
                "required_capabilities": ["color_mapping"],
                "validation_status": "validated",
            },
            {
                "hypothesis_id": "h:lose",
                "claim": "shape rule solves task",
                "creation_reason": "generated_hypotheses",
                "supporting_evidence": [],
                "confidence": 0.33,
                "required_capabilities": ["object_reasoning"],
                "rejection_reason": "prediction mismatch",
                "validation_status": "rejected",
            },
        ],
        "capability_contribution": [
            {
                "capability": "color_mapping",
                "contribution_percent": 76.0,
            },
            {
                "capability": "object_reasoning",
                "contribution_percent": 24.0,
            },
        ],
        "reasoning_graph": {
            "branches": [
                {
                    "branch_id": "branch:0:h:win",
                    "final_result": "dominant",
                    "intermediate_decisions": ["hypothesis_generated"],
                    "causal_links": [],
                },
                {
                    "branch_id": "branch:1:h:lose",
                    "final_result": "abandoned",
                    "intermediate_decisions": ["hypothesis_generated"],
                    "causal_links": [],
                },
            ],
        },
        "convergence_points": ["h:win"],
        "divergence_points": ["branch:1:h:lose"],
        "failure_analytics": {
            "reasoning_failed": True,
            "missing_information": ["object_reasoning"],
        },
        "task_intelligence": {
            "winning_reasoning_path": "branch:0:h:win",
            "decisive_capability": "color_mapping",
        },
        "knowledge_candidates": [{"strategy_id": "h:win"}],
        "recommended_improvements": ["attach failure reasons"],
    }

    report = reasoning_intelligence_builder.build_report(
        cognitive_analytics_report=cognitive_report,
        performance_report={"reasoning_time_seconds": 0.5},
        cognitive_capability_report={
            "capability_inventory": [
                {
                    "capability_id": "color_mapping",
                    "executed": True,
                    "confidence": 0.91,
                    "failure_cases": [],
                },
                {
                    "capability_id": "object_reasoning",
                    "executed": True,
                    "confidence": 0.33,
                    "failure_cases": ["object_identity"],
                },
            ],
            "cooperation_events": [
                {
                    "source_capability": "color_mapping",
                    "target_capability": "object_reasoning",
                },
            ],
            "reusable_assets": {
                "successful_strategies": [{"strategy_id": "h:win"}],
            },
        },
        causal_context_report={
            "cause_effect_pairs": [
                {
                    "cause_id": "palette_delta",
                    "effect_id": "output_color",
                    "confidence": 0.8,
                },
            ],
        },
        adaptive_reuse_report={"reuse_success_rate": 1.0},
    )

    assert report["REASONING_INTELLIGENCE_REPORT"] is True
    assert report["reasoning_depth"] == 3
    assert report["branch_statistics"]["discarded_routes"] == 1
    assert report["hypothesis_statistics"]["hypotheses_active"] == 0
    assert report["hypothesis_profiles"][0]["confidence_history"]
    assert report["capability_contribution"][0]["capability"] == "color_mapping"
    assert report["decision_log"][0]["decision"] == "survived"
    assert report["reasoning_profiler"]["time_spent_generating_hypotheses"] > 0
    assert report["success_intelligence"]["winning_strategy"] == "branch:0:h:win"
    assert report["failure_intelligence"]["recommended_capability"] == "object_reasoning"
    assert report["visual_reasoning_trace"]
