from runtime.world.soft_execution_gate import SoftExecutionGate


def test_soft_execution_gate_authorizes_soft_execution_zone():
    report = SoftExecutionGate().evaluate({
        "sandbox_execution_accepted": True,
        "acceptance_state": "SOFT_EXECUTION_ZONE",
    })

    assert report["soft_execution_authorized"] is True
    assert report["soft_execution_enabled"] is True
    assert report["soft_execution_state"] == "SOFT_EXECUTION_ZONE"


def test_soft_execution_gate_rejects_invalid_zone():
    report = SoftExecutionGate().evaluate({
        "sandbox_execution_accepted": True,
        "acceptance_state": "SEARCH_CANDIDATE_ONLY",
    })

    assert report["soft_execution_authorized"] is False
    assert report["soft_execution_enabled"] is True


def test_soft_execution_gate_rejects_when_not_enabled():
    report = SoftExecutionGate().evaluate({
        "sandbox_execution_accepted": False,
        "acceptance_state": "SOFT_EXECUTION_ZONE",
    })

    assert report["soft_execution_authorized"] is False
    assert report["soft_execution_enabled"] is False


def test_soft_execution_gate_authorizes_difference_count_two_fallback():
    report = SoftExecutionGate().evaluate({
        "sandbox_execution_accepted": False,
        "acceptance_state": "SEARCH_CANDIDATE_ONLY",
        "prediction_report": {
            "prediction_accuracy": 0.92,
            "partial_success": True,
        },
        "residual_difference_count": 2,
    })

    assert report["soft_execution_authorized"] is True
    assert report["soft_execution_enabled"] is True
    assert report["soft_execution_override_applied"] is True
    assert report["maximum_soft_execution_difference_count"] == 2
    assert report["minimum_soft_execution_accuracy"] == 0.90


def test_soft_execution_gate_authorizes_success_state_partial_success():
    report = SoftExecutionGate().evaluate({
        "sandbox_execution_accepted": False,
        "acceptance_state": "SEARCH_CANDIDATE_ONLY",
        "prediction_report": {
            "prediction_accuracy": 0.92,
            "success_state": "PARTIAL_SUCCESS",
        },
        "residual_difference_count": 2,
    })

    assert report["soft_execution_authorized"] is True
    assert report["soft_execution_enabled"] is True
    assert report["soft_execution_override_applied"] is True
