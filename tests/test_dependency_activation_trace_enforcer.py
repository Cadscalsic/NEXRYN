from runtime.dependency.dependency_activation_enforcer import (
    DependencyActivationEnforcer,
)
from runtime.dependency.dependency_activation_trace import (
    DependencyActivationTrace,
)


def test_enforcer_generates_request_for_mandatory_dependency_concept():
    trace = DependencyActivationTrace()
    result = DependencyActivationEnforcer().enforce(
        ["gravity", "falling"],
        {},
        trace=trace,
    )
    context = result["runtime_context"]
    request = context["runtime_tool_requests"]["dependency_reasoning"]

    assert result["activation_required"] is True
    assert result["activation_request_generated"] is True
    assert request["request_state"] == "REQUESTED"
    assert "dependency_reasoning" in context["enabled_tools"]
    assert trace.report()["activation_request_count"] == 1


def test_trace_reports_structured_skip_and_missing_activation_warning():
    trace = DependencyActivationTrace()
    trace.detect_concepts(["path_finding"])
    skip_report = trace.skip_report(
        requested_tool="dependency_reasoning",
        activation_attempted=False,
        activation_blocked=True,
        block_reason="disabled_by_tool_selection",
        blocking_module="unit_test",
        blocking_condition="tool_not_enabled",
    )
    warning = trace.assert_requested_when_concepts_exist()
    report = trace.report()

    assert skip_report["report_type"] == "DEPENDENCY_SKIP_REPORT"
    assert skip_report["requested_tool"] == "dependency_reasoning"
    assert warning["warning"] == "DEPENDENCY_ACTIVATION_MISSING"
    assert report["concepts_detected"] == ["path_finding"]
    assert report["skip_reasons"] == [skip_report]
    assert report["activation_success_rate"] == 0.0
