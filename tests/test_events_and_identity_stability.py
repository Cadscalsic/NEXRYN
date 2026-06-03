from core.events.event_bus import CognitiveEventBus
from core.identity.identity_stability_core import IdentityStabilityCore


def test_cognitive_event_bus_routes_priority_signals():

    bus = CognitiveEventBus()

    bus.subscribe(
        "identity_behavior_shift",
        "identity_stability_core",
    )

    routed = bus.priority_route({
        "event_type": "identity_behavior_shift",
        "priority": 0.95,
        "payload": {
            "shift_detected": True,
        },
    })

    assert routed["route"] == "critical_signal_lane"

    assert (
        "identity_stability_core"
        in routed["subscribers"]
    )

    assert bus.run_cycle({
        "identity_core_report": {
            "behavior_shift": {
                "shift_detected": True,
            },
        },
    })["emitted_count"] == 1


def test_identity_stability_core_rolls_back_behavior_shift():

    identity = IdentityStabilityCore()

    identity.run_cycle({
        "identity_core_report": {
            "identity_drift": 0.20,
            "continuity_state": "stable",
            "behavior_shift": {
                "shift_detected": False,
            },
        },
        "executive_mode": "balanced_reasoning",
        "selected_actions": [
            "reason",
        ],
    })

    report = identity.run_cycle({
        "identity_core_report": {
            "identity_drift": 0.62,
            "continuity_state": "watched",
            "behavior_shift": {
                "shift_detected": True,
                "action_count": 28,
            },
        },
        "executive_mode": "protective_arbitration",
        "selected_actions": [
            f"action_{index}"
            for index in range(28)
        ],
    })

    assert (
        report["identity_stability_state"]
        ==
        "rollback_required"
    )

    assert (
        "rollback_behavior"
        in report["identity_recovery"][
            "recovery_actions"
        ]
    )

    assert (
        report["behavior_alignment"][
            "behavior_aligned"
        ]
        is False
    )


def test_identity_stability_core_requires_confirmed_recovery_cycles():

    identity = IdentityStabilityCore()

    identity.run_cycle({
        "identity_core_report": {
            "identity_drift": 0.62,
            "behavior_shift": {
                "shift_detected": True,
            },
        },
    })

    healthy = {
        "identity_core_report": {
            "identity_drift": 0.10,
            "behavior_shift": {
                "shift_detected": False,
            },
        },
    }

    first = identity.run_cycle(
        healthy,
    )

    second = identity.run_cycle(
        healthy,
    )

    third = identity.run_cycle(
        healthy,
    )

    assert first["identity_stability_state"] == "recovery_monitoring"
    assert second["identity_stability_state"] == "recovery_monitoring"
    assert third["identity_stability_state"] == "stable"
