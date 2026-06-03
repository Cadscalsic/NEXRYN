from runtime.stability.distributed_cognitive_execution import (
    DistributedCognitiveExecution,
)


def test_distributed_cognitive_execution_threads_dma_and_compiles_macros():

    execution = DistributedCognitiveExecution()

    context = {
        "dynamic_cognitive_swapping_report": {
            "loaded_concepts": [
                {
                    "concept": "object_identity_preservation",
                    "demand_score": 0.91,
                },
                {
                    "concept": "shape_preservation",
                    "demand_score": 0.83,
                },
            ],
        },
        "predictive_attention_routing_v2_report": {
            "rebuilt_routes": [
                {
                    "alternate_route": "low_entropy_shape_rule",
                    "collapse_risk_after": 0.22,
                },
            ],
        },
        "recursive_budget_market_report": {
            "allocations": [
                {
                    "hypothesis": "low_entropy_shape_rule",
                    "market_bid": 0.72,
                    "recursion_budget_granted": 3,
                },
                {
                    "hypothesis": "compact_color_rule",
                    "market_bid": 0.61,
                    "recursion_budget_granted": 2,
                },
            ],
        },
    }

    updated = execution.run_cycle(
        context
    )

    report = updated[
        "distributed_cognitive_execution_report"
    ]

    threading = report[
        "cognitive_threading"
    ]

    assert threading[
        "multiple_independent_reasoning_streams"
    ] is True

    assert threading["thread_count"] == 2

    assert all(
        thread["branch_isolation"] == "isolated_context_delta"
        for thread in threading["threads"]
    )

    dma = report[
        "semantic_dma"
    ]

    assert dma["executive_overhead_bypass"] is True

    assert dma["transfer_count"] >= 4

    compilation = report[
        "predictive_cognitive_compilation"
    ]

    assert compilation[
        "create_executable_semantic_macros"
    ] is True

    assert compilation["compiled_macro_count"] == 2

    assert compilation["macro_cache_size"] >= 1
