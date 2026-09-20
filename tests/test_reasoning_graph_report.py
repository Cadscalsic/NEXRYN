from runtime.reasoning.reasoning_graph_report import ReasoningGraphReportBuilder


def test_reasoning_graph_report_exposes_replayable_reasoning_contract():
    cognitive_report = {
        "average_confidence": 0.82,
        "hypotheses": [
            {
                "hypothesis_id": "hypothesis:color_map",
                "claim": "replace 1 with 5",
                "creation_reason": "color delta observed",
                "supporting_evidence": ["input_output_color_delta"],
                "confidence": 0.91,
                "required_capabilities": ["color_mapping"],
                "validation_status": "validated",
            },
            {
                "hypothesis_id": "hypothesis:density",
                "claim": "expand pattern",
                "creation_reason": "density delta observed",
                "supporting_evidence": ["density_delta"],
                "confidence": 0.44,
                "required_capabilities": ["spatial_reasoning"],
                "validation_status": "rejected",
                "rejection_reason": "prediction residual too high",
            },
        ],
        "capability_contribution": [
            {"capability": "color_mapping", "contribution_percent": 72.0},
            {"capability": "spatial_reasoning", "contribution_percent": 28.0},
        ],
        "reasoning_graph": {
            "branches": [
                {
                    "branch_id": "branch:color",
                    "starting_assumption": "hypothesis:color_map",
                    "intermediate_decisions": ["ranked_first"],
                    "final_result": "dominant",
                },
                {
                    "branch_id": "branch:density",
                    "starting_assumption": "hypothesis:density",
                    "intermediate_decisions": ["ranked_second"],
                    "final_result": "abandoned",
                },
            ],
        },
    }
    capability_report = {
        "capabilities_executed": ["color_mapping", "spatial_reasoning"],
        "capability_confidence": {
            "color_mapping": 0.93,
            "spatial_reasoning": 0.52,
        },
    }
    causal_report = {
        "CAUSAL_CONTEXT_REPORT": True,
        "cause_effect_pairs": [
            {
                "cause": "palette_rule",
                "effect": "replace_color",
                "confidence": 0.88,
            },
        ],
    }

    report = ReasoningGraphReportBuilder().build_report(
        cognitive_analytics_report=cognitive_report,
        cognitive_capability_report=capability_report,
        causal_context_report=causal_report,
        dependency_audit_report={"injected_dependencies": ["palette_rule"]},
        context_validation_report={"reports": [{"valid": True}]},
    )

    assert report["REASONING_GRAPH_REPORT"] is True
    assert report["node_count"] == len(report["reasoning_graph"]["nodes"])
    assert report["edge_count"] == len(report["reasoning_graph"]["edges"])
    assert report["winning_branch"]["branch_id"] == "branch:color"
    assert report["discarded_branches"][0]["branch_id"] == "branch:density"
    assert report["hypothesis_statistics"]["validated"] == 1
    assert report["hypothesis_statistics"]["rejected"] == 1
    assert report["reasoning_snapshots"]
    assert report["decision_trace"]["which_capability_contributed"][0] == "color_mapping"

    node = report["reasoning_graph"]["nodes"][0]
    assert {
        "node_id",
        "node_type",
        "creation_time",
        "confidence",
        "parent_nodes",
        "child_nodes",
        "state",
    }.issubset(node)

    edge = report["reasoning_graph"]["edges"][0]
    assert {
        "source",
        "target",
        "relationship",
        "confidence",
        "timestamp",
    }.issubset(edge)

    confidence_update = report["hypotheses"][0]["confidence_history"][1]
    assert confidence_update["confidence_before"] < confidence_update["confidence_after"]
    assert confidence_update["reason_for_change"]


def test_reasoning_graph_report_handles_sparse_runtime_without_solver_calls():
    report = ReasoningGraphReportBuilder().build_report(
        cognitive_analytics_report={},
        performance_report={"reasoning_iterations": 0},
    )

    assert report["REASONING_GRAPH_REPORT"] is True
    assert report["runtime_overhead"]["additional_solver_calls"] == 0
    assert report["reasoning_graph"]["nodes"]
    assert report["graph_size"]["nodes"] == report["node_count"]
