from runtime.analytics import cognitive_analytics_builder


def test_cognitive_analytics_report_derives_cognitive_intelligence():
    report = cognitive_analytics_builder.build_report(
        task_count=1,
        successful_tasks=1,
        failed_tasks=0,
        all_results=[
            {
                "result": {
                    "generated_hypotheses": [
                        {
                            "hypothesis_id": "h:color",
                            "claim": "color mapping explains the task",
                            "confidence": 0.82,
                            "capability_id": "color_mapping",
                            "validation_status": "validated",
                        },
                        {
                            "hypothesis_id": "h:shape",
                            "claim": "shape count explains the task",
                            "confidence": 0.31,
                            "capability_id": "object_reasoning",
                            "validation_status": "rejected",
                            "rejection_reason": "prediction mismatch",
                        },
                    ],
                },
            },
        ],
        cognitive_capability_report={
            "capabilities_executed": ["color_mapping", "program_synthesis"],
            "capability_confidence": {
                "color_mapping": 0.82,
                "program_synthesis": 0.68,
            },
            "capability_inventory": [
                {
                    "capability_id": "color_mapping",
                    "executed": True,
                    "confidence": 0.82,
                    "potential_cooperation": ["program_synthesis"],
                },
                {
                    "capability_id": "program_synthesis",
                    "executed": True,
                    "confidence": 0.68,
                    "potential_cooperation": ["color_mapping"],
                },
                {
                    "capability_id": "causal_reasoning",
                    "executed": False,
                    "confidence": 0.2,
                    "missing_reasoning_patterns": ["root_cause"],
                    "potential_cooperation": ["dependency_reasoning"],
                },
            ],
            "cooperation_events": [
                {
                    "source_capability": "color_mapping",
                    "target_capability": "program_synthesis",
                },
            ],
            "reusable_assets": {
                "successful_strategies": [{"strategy_id": "h:color"}],
            },
        },
        causal_context_report={
            "CAUSAL_CONTEXT_REPORT": True,
            "causal_chain_depth": 2,
            "average_confidence": 0.7,
            "cause_effect_pairs": [
                {
                    "cause_id": "palette_change",
                    "effect_id": "output_color",
                    "confidence": 0.7,
                },
            ],
        },
    )

    assert report["COGNITIVE_ANALYTICS_REPORT"] is True
    assert report["hypothesis_statistics"]["hypotheses_generated"] == 2
    assert report["hypothesis_statistics"]["hypotheses_validated"] == 1
    assert report["hypothesis_statistics"]["hypotheses_rejected"] == 1
    assert report["reasoning_depth"] == 2
    assert report["capability_contribution"][0]["capability"] == "color_mapping"
    assert report["task_intelligence"]["decisive_capability"] == "color_mapping"
    assert report["missing_capabilities"][0]["capability"] == "causal_reasoning"
