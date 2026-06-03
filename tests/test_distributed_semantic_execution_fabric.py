from runtime.stability.distributed_semantic_execution_fabric import (
    DistributedSemanticExecutionFabric,
)


def test_distributed_semantic_execution_fabric_regulates_semantic_heat():

    fabric = DistributedSemanticExecutionFabric()

    context = {
        "runtime_entropy": 0.7686,
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
                {
                    "concept": "semantic_bridge",
                    "demand_score": 0.76,
                },
            ],
        },
        "distributed_cognitive_execution_report": {
            "cognitive_threading": {
                "threads": [
                    {
                        "thread_id": f"cog_thread:{index}",
                        "work_id": f"semantic_path_{index}",
                        "priority": 0.9 - index * 0.08,
                        "recursion_budget": 3,
                    }
                    for index in range(1, 6)
                ],
            },
        },
    }

    updated = fabric.run_cycle(
        context
    )

    report = updated[
        "distributed_semantic_execution_fabric_report"
    ]

    scheduler = report[
        "semantic_thread_scheduler"
    ]

    assert scheduler["max_parallel_threads"] == 2

    assert scheduler["scheduled_thread_count"] == 2

    assert scheduler["deferred_thread_count"] == 3

    dma = report[
        "cognitive_dma"
    ]

    assert dma["executive_overhead_bypass"] is True

    assert dma["transfer_count"] > 0

    compiler = report[
        "semantic_cache_compiler"
    ]

    assert compiler["macro_count"] == 2

    assert compiler["cache_size"] >= 1

    regulator = report[
        "entropy_field_regulator"
    ]

    assert regulator["semantic_overheating"] is True

    assert (
        regulator["semantic_heat_after"]
        <
        regulator["semantic_heat_before"]
    )
