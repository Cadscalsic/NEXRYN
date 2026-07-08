from runtime.analytics import meta_cognitive_optimizer


def _graph_report():
    return {
        "REASONING_GRAPH_REPORT": True,
        "hypotheses": [
            {
                "hypothesis_id": "h:win",
                "status": "VALIDATED",
                "supporting_capabilities": ["color_mapping"],
                "confidence_history": [
                    {
                        "confidence_before": 0.0,
                        "confidence_after": 0.72,
                        "reason_for_change": "created",
                    },
                    {
                        "confidence_before": 0.72,
                        "confidence_after": 0.91,
                        "reason_for_change": "validation confirmed",
                    },
                ],
            },
            {
                "hypothesis_id": "h:lose",
                "status": "REJECTED",
                "supporting_capabilities": ["spatial_reasoning"],
                "confidence_history": [
                    {
                        "confidence_before": 0.65,
                        "confidence_after": 0.24,
                        "reason_for_change": "prediction residual rejected it",
                    },
                ],
            },
        ],
        "discarded_branches": [
            {
                "branch_id": "branch:lose",
                "state": "DISCARDED",
                "confidence": 0.24,
                "branch_depth": 2,
                "branch_width": 1,
                "generated_hypotheses": ["h:lose"],
            },
        ],
        "validated_branches": [
            {
                "branch_id": "branch:win",
                "state": "VALIDATED",
                "confidence": 0.91,
                "branch_depth": 2,
                "branch_width": 1,
                "generated_hypotheses": ["h:win"],
                "selection_reason": "dominant",
            },
        ],
        "reasoning_timeline": [
            {"stage": "Observation"},
            {"stage": "Hypothesis Generation"},
            {"stage": "Validation"},
            {"stage": "Solution"},
        ],
        "confidence_evolution": [
            {
                "hypothesis_id": "h:win",
                "confidence_before": 0.72,
                "confidence_after": 0.91,
                "reason_for_change": "validation confirmed",
            },
        ],
        "decision_trace": {
            "why_branch_selected": "dominant confidence",
            "why_another_rejected": "prediction residual",
            "final_candidate": {
                "hypothesis_id": "h:win",
                "confidence": 0.91,
            },
        },
    }


def _analytics_report():
    return {
        "REASONING_ANALYTICS_REPORT": True,
        "reasoning_quality_score": 0.78,
        "reasoning_health": "Good",
        "reasoning_efficiency": {
            "reasoning_width": 2,
            "maximum_branch_depth": 2,
            "branch_expansion_rate": 1.0,
            "branch_collapse_rate": 0.5,
            "average_confidence_gain": 0.19,
        },
        "reasoning_convergence": {
            "convergence_point": "branch:win",
            "late_convergence": True,
            "dead_ends": ["branch:lose"],
            "evidence_triggered_convergence": ["validation"],
        },
        "reasoning_cost": {
            "cost_per_capability": 0.2,
            "cost_per_validation": 0.3,
        },
        "reasoning_generalization_potential": 0.7,
        "quality_warnings": [
            {"warning": "late_convergence", "severity": "medium"},
        ],
        "rejected_hypothesis_analysis": [
            {
                "hypothesis_id": "h:lose",
                "why_rejected": "prediction residual",
                "evidence_rejected_it": ["validation"],
                "capability_rejected_it": "spatial_reasoning",
                "rejection_correctness": "likely_correct",
                "should_remain_dormant": True,
                "confidence_after_rejection": 0.24,
            },
        ],
        "capability_statistics": {
            "color_mapping": {
                "capability_influence_score": 0.81,
                "success_rate": 1.0,
                "average_confidence": 0.92,
            },
            "spatial_reasoning": {
                "capability_influence_score": 0.22,
                "success_rate": 0.3,
                "average_confidence": 0.35,
            },
        },
        "decision_quality": {
            "decisions": [
                {
                    "decision_id": "decision:h:win",
                    "hypothesis_id": "h:win",
                    "quality_score": 0.9,
                    "later_confirmed": True,
                },
            ],
        },
        "learning_opportunities": [
            {
                "type": "reusable validation patterns",
                "candidates": [{"pattern": "validate_after_gain"}],
            },
        ],
        "quality_dashboard": {
            "most_useful_capability": "color_mapping",
            "least_useful_capability": "spatial_reasoning",
            "most_reused_reasoning_pattern": "reusable validation patterns",
        },
    }


def test_meta_cognitive_report_updates_policy_memory(tmp_path):
    memory_path = tmp_path / "reasoning_policy_memory.json"

    report = meta_cognitive_optimizer.build_report(
        reasoning_graph_report=_graph_report(),
        reasoning_analytics_report=_analytics_report(),
        cognitive_capability_report={
            "cooperation_events": [
                {
                    "source_capability": "color_mapping",
                    "target_capability": "spatial_reasoning",
                },
            ],
        },
        causal_context_report={
            "cause_effect_pairs": [
                {
                    "cause": "palette_delta",
                    "effect": "validated_solution",
                    "confidence": 0.8,
                },
            ],
        },
        policy_memory_path=str(memory_path),
    )

    assert report["META_COGNITIVE_REPORT"] is True
    assert report["policy_memory_persistence"]["persisted"] is True
    assert report["new_policies"]
    assert "color_mapping" in report["capability_ordering"]["preferred_order"]
    assert report["pre_reasoning_strategy"]["adaptive_reasoning_strategy"]
    assert report["self_improvement_score"]["meta_cognitive_score"] > 0.0
    assert memory_path.exists()


def test_meta_cognitive_report_reinforces_existing_policy(tmp_path):
    memory_path = tmp_path / "reasoning_policy_memory.json"

    first = meta_cognitive_optimizer.build_report(
        reasoning_graph_report=_graph_report(),
        reasoning_analytics_report=_analytics_report(),
        policy_memory_path=str(memory_path),
    )
    second = meta_cognitive_optimizer.build_report(
        reasoning_graph_report=_graph_report(),
        reasoning_analytics_report=_analytics_report(),
        policy_memory_path=str(memory_path),
    )

    assert first["knowledge_growth"]["new_policies"]
    assert second["knowledge_growth"]["updated_policies"]
    assert second["reasoning_policy_memory"]["episodes_reviewed"] == 2
    assert second["optimization_safety"]["runtime_behavior_modified"] is False
