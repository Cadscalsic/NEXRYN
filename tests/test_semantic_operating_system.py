from core.semantic_os.semantic_operating_system import (
    SemanticOperatingSystem,
)


def test_semantic_operating_system_executes_semantic_memory_as_processes():

    os_layer = SemanticOperatingSystem()

    context = {
        "runtime_entropy": 0.82,
        "dynamic_cognitive_swapping_report": {
            "loaded_concepts": [
                {
                    "concept": "object_identity_preservation",
                },
                {
                    "concept": "shape_preservation",
                },
            ],
            "latent_concepts": [
                {
                    "concept": "latent_bridge",
                },
            ],
            "paged_out_concepts": [],
        },
        "semantic_cache_compiler_report": {
            "executable_semantic_macros": [
                {
                    "macro_id": "semantic_macro:shape_rule",
                    "semantic_path": "shape_rule",
                },
            ],
        },
        "cognitive_immune_system_v2_report": {
            "identity_firewall": {
                "blocked_payloads": [],
            },
        },
        "cognitive_thermodynamics_report": {
            "semantic_heat_dissipation": {
                "semantic_heat_after": 0.72,
            },
        },
    }

    report = os_layer.run_cycle(
        context
    )

    assert (
        report["semantic_memory_mode"]
        ==
        "executable_semantic_infrastructure"
    )

    assert (
        report["virtual_semantic_memory"][
            "working_count"
        ]
        ==
        2
    )

    assert (
        report["virtual_semantic_memory"][
            "executable_count"
        ]
        ==
        1
    )

    assert (
        report["concept_router"]["route_count"]
        ==
        3
    )

    assert (
        report["semantic_process_manager"][
            "ready_count"
        ]
        ==
        3
    )

    assert (
        report["semantic_scheduler"][
            "scheduler_policy"
        ]
        ==
        "thermal_limited_semantic_execution"
    )
