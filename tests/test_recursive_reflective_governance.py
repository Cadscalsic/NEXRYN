from core.recursive_reflective_governance import (
    recursive_reflective_governance,
)


def test_recursive_reflective_governance_organizes_recursive_runtime():

    context = {
        "recursive_paths":
        [
            "self_reflection",
            "lineage_projection",
            "topology_growth",
            "distributed_diffusion",
        ],

        "existential_pressure_report":
        {
            "managed_pressure": 0.58,
            "identity_strain_regulator":
            {
                "identity_strain": 0.52,
            },
        },

        "adaptive_equilibrium_report":
        {
            "propagation_stability_manager":
            {
                "failure_propagation_score": 0.56,
            },
            "contextual_topology_regulator":
            {
                "contextual_topology_flexibility": 0.34,
            },
        },

        "distributed_cognitive_execution_report":
        {
            "thread_count": 4,
        },

        "distributed_semantic_execution_fabric_report":
        {
            "semantic_thread_count": 3,
        },

        "memory_pressure_score": 0.66,

        "memory_compression_report":
        {
            "compression_ratio": 0.42,
        },

        "topology_result":
        {
            "topology_delta": 0.62,
        },

        "semantic_field_dynamics_report":
        {
            "drift_diffusion_equations":
            {
                "diffusion_rate": 0.68,
            },
        },
    }

    report = recursive_reflective_governance.run_cycle(
        context,
    )

    policy = report["recursive_reflective_policy"]

    assert report["layer"] == "recursive_reflective_governance_layer"
    assert policy["reflect_before_recursion"] is True
    assert policy["localize_recursive_propagation"] is True
    assert policy["cap_recursive_growth"] is True
    assert policy["control_semantic_pruning"] is True
    assert policy["enforce_reflective_recursion_limits"] is True
    assert policy["balance_recursive_diffusion"] is True
    assert policy["organize_recursive_runtime"] is True
    assert report["organized_recursive_runtime"]["runtime_actions"]
    assert report["recursive_reflective_state"] == "recursive_reflective_governance_active"
