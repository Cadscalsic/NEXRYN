from core.reality.cognitive_physics_engine import (
    CognitivePhysicsEngine,
)


def test_cognitive_physics_engine_blocks_low_identity_world_commits():

    engine = CognitivePhysicsEngine()

    context = {
        "runtime_entropy": 0.6757,
        "safe_exploratory_sandbox_report": {
            "simulation_count": 24,
        },
        "recursive_simulation_worlds_report": {
            "world_count": 8,
            "worlds": [
                {
                    "world_id": f"sim_world:{index}",
                    "identity_continuity": 0.4401,
                    "predicted_entropy_delta": 0.41,
                }
                for index in range(8)
            ],
        },
    }

    report = engine.run_cycle(
        context
    )

    assert (
        report["simulation_budget"]["max_active_worlds"]
        ==
        2
    )

    assert (
        report["world_isolation"][
            "write_barrier_architecture"
        ]
        is True
    )

    assert all(
        world["commit_to_core"] is False
        for world in report["world_isolation"][
            "isolated_worlds"
        ]
    )

    assert (
        report["branch_collapse"]["collapsed_count"]
        ==
        2
    )

    assert all(
        branch["commit_allowed"] is False
        for branch in report["branch_collapse"][
            "collapsed_branches"
        ]
    )

    assert (
        report["write_barrier"]["direct_core_commit"]
        is False
    )
