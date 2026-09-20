from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer
from tests.test_human_report_contract import _metadata, _state


def test_program_lifecycle_counts_do_not_conflict_across_semantics():
    state = _state()
    state["COGNITIVE_PROGRAM_LIFECYCLE_REPORT"] = {
        "total_program_blueprints": 10,
    }
    state["PROGRAM_GENERATION_REPORT"] = {
        "program_blueprint_generation_success_count": 15,
    }
    state["PROGRAM_SYNTHESIS_REPORT"] = {
        "generated_programs": 6,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Generated Programs:" not in report
    assert "Program Blueprint Inventory:" not in report
    assert "Program Type Lifecycle Entries: 10" in report
    assert "Successful Blueprint Generations: 15" in report
    assert "Synthesized Programs Persisted: 6" in report
    assert "Human Report Binding Conflict Count: 0" in report


def test_program_lifecycle_counts_still_conflict_within_same_semantics():
    state = _state()
    state["program_blueprint_generation_success_count"] = 14
    state["PROGRAM_GENERATION_REPORT"] = {
        "program_blueprint_generation_success_count": 15,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Successful Blueprint Generations: Canonical source conflict" in report
    assert "field=program_blueprint_generation_success_count" in report
    assert "expected_value=14" in report
    assert "observed_value=15" in report
    assert "Human Report Binding Conflict Count: 1" in report


def test_activation_count_does_not_override_blueprint_generation_success():
    state = _state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "program_blueprint_generation_success_count": 5,
        "generated_programs": 12,
        "generated_blueprints": 12,
        "executable_candidate_activation_count": 12,
        "activation_bridge_generated_programs": 12,
    }
    state["EXECUTABLE_ACTIVATION_REPORT"] = {
        "candidate_proposal_count": 12,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Successful Blueprint Generations: 5" in report
    assert "Successful Blueprint Generations: 12" not in report
    assert "Human Report Binding Conflict Count: 0" in report
