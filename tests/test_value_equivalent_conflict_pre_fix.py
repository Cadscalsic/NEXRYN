import pytest

from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def make_canonical(field_path, numeric_value, string_value):
    # Build a minimal canonical dict where one source is numeric and another
    # is a string representation under report_binding.field_values
    root = {
        "performance": {},
        "runtime_metadata": {},
        "report_state": {},
    }
    # top-level search payload
    root_field = field_path.split(".")[0]
    root[root_field] = {field_path.split(".")[-1]: numeric_value}
    # emulated binding display
    root["report_binding"] = {"field_values": {field_path.split(".")[-1]: string_value}}
    return root


@pytest.mark.parametrize(
    "field,numeric,string",
    [
        ("overall_search_quality", 0.4714, "0.4714"),
        ("search_efficiency", 0.0296, "0.0296"),
        ("search_coverage", 1.0, "1.0"),
        ("average_route_quality", 0.0978, "0.0978"),
        ("search_coverage", 1, "1"),
        ("overall_search_quality", 0.4714, " 0.4714 "),
    ],
)
def test_pre_fix_representation_conflict(field, numeric, string):
    renderer = DeterministicFinalReportRenderer()
    canonical = make_canonical(field, numeric, string)
    binding = renderer._build_human_report_binding(canonical)
    fields = binding.get("field_bindings", {})
    # Post-fix: representation-only differences should not produce SOURCE_CONFLICT
    assert fields[field]["state"] == "VALUE_AVAILABLE"
