from core.cognitive_kernel.kernel_scheduler import (
    CognitiveKernelScheduler,
)


def test_cognitive_kernel_enters_stabilization_on_architectural_saturation():

    scheduler = CognitiveKernelScheduler()

    context = {
        "working_memory_pressure": 1.0,
        "attention_saturation": 0.7958,
        "runtime_entropy": 0.6757,
        "energy_state": "critical",
        "projected_overload": 0.7515,
        "executive_mode": "protective_arbitration",
        "selected_actions": [
            f"action_{index}"
            for index in range(28)
        ],
    }

    report = scheduler.run_cycle(
        context
    )

    assert report["active_mode"] == "stabilization_mode"

    assert (
        report["collapse_prevention"][
            "architectural_saturation"
        ]
        is True
    )

    assert "reasoning" not in report["enabled_subsystems"]

    assert "reasoning" in report["disabled_subsystems"]

    assert (
        report["kernel_budget"]["exploration"]
        ==
        0.0
    )

    assert (
        "collapse_governance_stack"
        in report["collapse_prevention"][
            "collapse_prevention_actions"
        ]
    )
