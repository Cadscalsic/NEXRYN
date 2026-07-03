from runtime.budget.deep_mode_budget_manager import DeepModeBudgetManager
from runtime.reporting.compact_report_builder import CompactReportBuilder
from runtime.routing.pre_reasoning_router import PreReasoningRouter


def test_deep_budget_manager_bounds_full_report_without_audit_flags():
    manager = DeepModeBudgetManager()
    budget = manager.build_budget()
    constrained = manager.constrain_reasoning_budget(
        {
            "mode": "deep",
            "cache_dependencies": False,
            "full_governance": True,
            "max_concepts": None,
            "max_chain_depth": None,
        },
        budget,
    )

    assert constrained["cache_dependencies"] is True
    assert constrained["full_governance"] is False
    assert constrained["max_concepts"] == 12
    assert constrained["max_chain_depth"] == 6
    assert manager.bounded_report_level("deep", "full", {}) == "normal"


def test_deep_budget_manager_allows_explicit_audit_expansion():
    manager = DeepModeBudgetManager()
    flags = {"audit_concepts": True, "audit_truth": True}

    assert manager.requested_sections(flags) == ["concepts", "truth"]
    assert manager.should_expand("concepts", flags) is True
    assert manager.bounded_report_level("deep", "full", flags) == "full"


def test_pre_reasoning_router_keeps_deep_mode_selective():
    router = PreReasoningRouter()
    plan = router.select_layers(
        {
            "task_family": "simple_translation",
            "confidence": 0.95,
            "required_capabilities": ["spatial_reasoning"],
            "requires_spatial_reasoning": True,
            "requires_context_discovery": False,
            "requires_governance": False,
        },
        {
            "mode": "deep",
            "audit_sections_requested": [],
        },
    )

    assert plan["execution_mode"] == "selective_deep"
    assert plan["enabled_layers"]
    assert plan["disabled_layers"] or plan["deferred_layers"]
    assert "self_improvement" not in plan["enabled_layers"]
    assert router.report()["full_stack_avoided"] is True


def test_deep_router_expands_requested_diagnostic_sections_only():
    router = PreReasoningRouter()
    plan = router.select_layers(
        {
            "task_family": "truth_sensitive",
            "confidence": 0.80,
            "required_capabilities": ["dependency_reasoning"],
        },
        {
            "mode": "deep",
            "audit_sections_requested": ["truth", "dependencies"],
        },
    )

    assert "dependency_reasoning" in plan["enabled_layers"]
    assert "truth_candidate" in plan["enabled_layers"]
    assert "truth_commit" in plan["enabled_layers"]
    assert "self_improvement" not in plan["enabled_layers"]


def test_deep_optimization_report_contains_budget_and_deferred_layers():
    manager = DeepModeBudgetManager()
    report = manager.build_report(
        mode="deep",
        audit_flags={},
        layers_requested=["inference", "reporting"],
        layers_executed=["inference", "reporting"],
        layers_deferred=["self_improvement"],
        reports_generated=["training_report"],
        reports_skipped=["expanded_concept_lifecycle_report"],
        concepts_recomputed=0,
        concepts_reused=8,
        elapsed={
            "total_runtime_seconds": 10.0,
            "report_generation_seconds": 1.0,
            "concept_lifecycle_seconds": 0.1,
            "task_runtime_seconds": 4.0,
        },
    )

    assert report["DEEP_MODE_OPTIMIZATION_REPORT"] is True
    assert report["bounded_deep_mode"] is True
    assert report["layers_deferred"] == ["self_improvement"]
    assert report["reports_skipped"] == ["expanded_concept_lifecycle_report"]
    assert report["concepts_reused"] == 8
    assert report["task_budget_exceeded"] is False


def test_compact_performance_report_surfaces_deep_optimization_report():
    optimization = DeepModeBudgetManager().build_report(
        mode="deep",
        layers_deferred=["self_improvement"],
        reports_skipped=["expanded_truth_evaluations"],
    )

    compact = CompactReportBuilder().compact_performance_report({
        "system": "runtime_reasoning_budget",
        "DEEP_MODE_OPTIMIZATION_REPORT": optimization,
    })

    assert compact["DEEP_MODE_OPTIMIZATION_REPORT"]["bounded_deep_mode"] is True
    assert compact["DEEP_MODE_OPTIMIZATION_REPORT"]["layers_deferred"] == [
        "self_improvement",
    ]
