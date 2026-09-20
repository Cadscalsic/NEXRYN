from runtime.planning.execution_profile import build_execution_profile
from runtime.validation import CrossModeParityValidator


def _report(
    mode,
    *,
    context_count=15,
    concept_count=43,
    program_count=6,
    truth_count=18,
    memory_count=1,
    knowledge_count=56,
    lifecycle=1.0,
    binding=1.0,
    timing=1.0,
    registry="SYNCHRONIZED",
    governance_budget=20.0,
    extra_sections=None,
):
    sections = {
        "runtime_metadata": {
            "mode": mode,
            "execution_time": 1.0,
            "governance_budget_seconds": governance_budget,
            "execution_profile": {
                "execution_profile": mode,
                "cognitive_pipeline": "adaptive",
            },
        },
        "performance_report": {},
        "COGNITIVE_RUNTIME_REPORT": {
            "runtime_registry": {
                key: {"runtime_id": key}
                for key in (
                    "reasoning_runtime",
                    "search_runtime",
                    "truth_runtime",
                    "memory_runtime",
                    "evaluation_runtime",
                )
            },
        },
        "COGNITIVE_EXECUTION_ENGINE_REPORT": {
            "lifecycle_coverage": lifecycle,
            "synthetic_execution_count": 0,
            "execution_tree": [
                {
                    "runtime_id": "execution_runtime",
                    "children": [
                        {"runtime_id": "reasoning_runtime", "children": []},
                        {"runtime_id": "search_runtime", "children": []},
                        {"runtime_id": "truth_runtime", "children": []},
                        {"runtime_id": "memory_runtime", "children": []},
                        {"runtime_id": "evaluation_runtime", "children": []},
                    ],
                }
            ],
        },
        "EXECUTION_BINDING_REPORT": {
            "binding_coverage": binding,
            "timing_coverage": timing,
            "registry_synchronization": registry,
        },
        "SHARED_COGNITIVE_STATE_REPORT": {
            "context_propagation_coverage": 1.0 if context_count else 0.0,
            "state_consistency": {
                "counts": {
                    "context_count": context_count,
                    "concept_count": concept_count,
                    "program_count": program_count,
                    "search_route_count": 3,
                    "truth_candidate_count": truth_count,
                    "memory_entry_count": memory_count,
                    "knowledge_object_count": knowledge_count,
                    "snapshot_count": 8 if mode == "adaptive" else 12,
                }
            },
        },
        "truth_candidates": [{"id": f"truth:{index}"} for index in range(truth_count)],
        "truth_candidate_report": {
            "evaluations": [{"id": f"truth:{index}", "eligible": True} for index in range(truth_count)]
        },
        "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT": {
            "knowledge_object_count": knowledge_count,
        },
    }
    for key in extra_sections or ():
        sections[key] = {}
    return sections


def test_cross_mode_parity_accepts_declared_profile_differences():
    adaptive = _report("adaptive")
    deep = _report(
        "deep",
        concept_count=48,
        program_count=8,
        truth_count=22,
        knowledge_count=60,
        extra_sections=["DEEP_MODE_OPTIMIZATION_REPORT", "FULL_REPORT_DETAIL"],
    )

    result = CrossModeParityValidator().compare(adaptive, deep)

    stabilization = result["FULL_MODE_STABILIZATION_REPORT"]
    assert stabilization["regression_status"] == "PASSED"
    assert stabilization["mode_parity_score"] >= 90
    assert stabilization["expected_differences"]


def test_cross_mode_parity_flags_critical_truth_and_context_loss():
    adaptive = _report("adaptive", context_count=15, truth_count=18)
    deep = _report(
        "deep",
        context_count=0,
        truth_count=0,
        extra_sections=["DEEP_MODE_OPTIMIZATION_REPORT"],
    )

    result = CrossModeParityValidator().compare(adaptive, deep)
    categories = {
        item["category"]
        for item in result["FULL_MODE_STABILIZATION_REPORT"]["critical_divergences"]
    }

    assert "CONTEXT_LOSS" in categories
    assert "TRUTH_LOSS" in categories
    assert result["FULL_MODE_STABILIZATION_REPORT"]["regression_status"] == "FAILED"
    assert (
        result["MODE_COMPARISON_REPORT"]["first_divergence"][
            "first_divergence_runtime"
        ]
        == "context_coverage"
    )


def test_cross_mode_parity_rejects_binding_lifecycle_and_registry_drops():
    adaptive = _report("adaptive")
    deep = _report(
        "deep",
        lifecycle=0.75,
        binding=0.5,
        timing=0.5,
        registry="UNSYNCHRONIZED",
    )

    result = CrossModeParityValidator().compare(adaptive, deep)
    categories = {
        item["category"]
        for item in result["FULL_MODE_STABILIZATION_REPORT"]["critical_divergences"]
    }

    assert "LIFECYCLE_DIVERGENCE" in categories
    assert "BINDING_DIVERGENCE" in categories
    assert "REGISTRY_DIVERGENCE" in categories


def test_cross_mode_parity_requires_full_report_superset_and_governance_budget():
    adaptive = _report("adaptive", extra_sections=["NORMAL_SECTION"])
    deep = _report("full", governance_budget=None)

    result = CrossModeParityValidator().compare(
        adaptive,
        deep,
        full_label="full",
    )
    unexpected = result["FULL_MODE_STABILIZATION_REPORT"]["unexpected_differences"]
    categories = {item["category"] for item in unexpected}

    assert "REPORTING_DEFECT" in categories
    assert "GOVERNANCE_DIVERGENCE" in categories


def test_full_profile_extends_adaptive_pipeline_with_explicit_budget():
    profile = build_execution_profile("full")
    budget = profile.as_budget_defaults()

    assert profile.name == "full"
    assert profile.pipeline_name == "adaptive"
    assert budget["governance_budget_seconds"] == 20.0
    assert budget["max_reasoning_depth"] > build_execution_profile(
        "adaptive"
    ).as_budget_defaults()["max_reasoning_depth"]
