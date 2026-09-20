from runtime.planning.cognitive_cache_manager import (
    CognitiveCacheManager,
)
from runtime.planning.early_exit_controller import (
    EarlyExitController,
)
from runtime.planning.performance_optimizer import (
    PerformanceOptimizer,
)
from runtime.meta.meta_controller import (
    MetaControllerEngine,
    MetaDecision,
)
from runtime.state.runtime_state import (
    RuntimeState,
)


def test_early_exit_triggers_only_after_safety_conditions_are_met():

    controller = EarlyExitController()
    context = {
        "prediction_report": {
            "prediction_accuracy": 1.0,
            "prediction_confidence": 1.0,
            "uncertainty": 0.0,
            "world_model_fit": 1.0,
            "identity_continuity": 1.0,
        },
        "governance_report": {
            "status": "passed",
        },
    }

    decision = controller.evaluate(context)
    report = controller.build_report(decision)

    assert decision.should_stop is True
    assert report["should_stop"] is True
    assert report["prediction_accuracy"] == 1.0


def test_early_exit_refuses_unresolved_contradictions():

    controller = EarlyExitController()
    context = {
        "prediction_report": {
            "prediction_accuracy": 1.0,
            "prediction_confidence": 1.0,
            "uncertainty": 0.0,
            "world_model_fit": 1.0,
            "identity_continuity": 1.0,
        },
        "unresolved_contradictions": ["color_mapping_conflict"],
    }

    decision = controller.evaluate(context)

    assert decision.should_stop is False
    assert decision.reason == "unresolved_contradictions_present"


def test_cognitive_cache_returns_immutable_copies():

    cache = CognitiveCacheManager(persistence_enabled=False)
    key = cache.build_key(
        task_signature="task",
        concept_signature="concept",
        dependency_hash="dep",
        evidence_hash="evidence",
        runtime_version="test",
        artifact_type="dependency_chain",
    )

    cache.store(key, {"chain": ["a", "b"]})
    cached = cache.lookup(key)
    cached["chain"].append("mutated")
    cached_again = cache.lookup(key)

    assert cached_again == {"chain": ["a", "b"]}
    assert cache.metrics().cache_hits == 2


def test_performance_optimizer_prefers_cache_reuse():

    cache = CognitiveCacheManager(persistence_enabled=False)
    optimizer = PerformanceOptimizer()
    key = cache.build_key(
        task_signature="task",
        concept_signature="concept",
        dependency_hash="dep",
        evidence_hash="evidence",
        runtime_version="test",
        artifact_type="process_semantic_models",
    )
    calls = {"count": 0}

    def compute():
        calls["count"] += 1
        return {"model": "stable"}

    first, first_report = optimizer.lookup_or_compute(cache, key, compute)
    second, second_report = optimizer.lookup_or_compute(cache, key, compute)

    assert first == second
    assert first_report["cache_state"] == "miss"
    assert second_report["cache_state"] == "hit"
    assert calls["count"] == 1


def test_pipeline_has_exact_success_fast_shutdown_contract():

    source = open("runtime/pipeline.py", encoding="utf-8").read()

    assert "def _exact_success_shutdown_allowed" in source
    assert "evaluation_result.get(\"exact_success\") is True" in source
    assert "evaluation_result.get(\"difference_count\") == 0" in source
    assert "integrity_report.get(\"integrity_preserved\") is True" in source
    assert "gate_report.get(\"execution_authorized\") is True" in source
    assert "self._identity_governance_stable(runtime_context)" in source
    assert "self.finalize_runtime_fast()" in source


def test_fast_finalization_report_names_post_success_skips():

    source = open(
        "runtime/planning/runtime_finalization_optimizer.py",
        encoding="utf-8",
    ).read()

    assert "\"strategy_evolution\"" in source
    assert "\"failure_memory_update\"" in source
    assert "\"deep_validation\"" in source
    assert "\"temporal_promotion_checks\"" in source
    assert "\"full_memory_report\"" in source


def test_meta_controller_reuses_stable_cached_memory():

    decision = MetaControllerEngine().decide({
        "memory_lookup_report": {
            "exact_cache_hit": True,
            "concept_version_hash_unchanged": True,
            "stable_truth_exists": True,
        },
    })

    assert decision.action == "REUSE_MEMORY"
    assert decision.max_reasoning_depth == 0
    assert decision.max_active_routes == 0
    assert decision.enable_memory_reuse is True
    assert decision.enable_governance is False
    assert decision.enable_self_improvement is False
    assert decision.shutdown_mode == "fast"


def test_meta_controller_stops_after_exact_success():

    decision = MetaControllerEngine().decide({
        "evaluation_result": {
            "exact_success": True,
            "difference_count": 0,
        },
    })

    assert decision.action == "STOP_AFTER_SUCCESS"
    assert decision.enable_self_improvement is False
    assert decision.enable_strategy_evolution is False
    assert decision.shutdown_mode == "fast"


def test_meta_controller_prefers_localization_for_prediction_mismatch():

    decision = MetaControllerEngine().decide({
        "failure_analysis": {
            "failure_cause": "localized_prediction_mismatch",
        },
        "transformation_report": {
            "execution_aborted": False,
        },
    })

    assert decision.action == "RUN_LOCALIZATION"
    assert decision.enable_localization is True
    assert decision.enable_self_improvement is False
    assert decision.enable_strategy_evolution is False


def test_meta_controller_escalates_identity_instability():

    decision = MetaControllerEngine().decide({
        "identity_governance_state": "TEMPORARY_RECOVERY_HOLD",
    })

    assert decision.action == "ESCALATE_TO_GOVERNANCE"
    assert decision.enable_governance is True
    assert decision.shutdown_mode == "normal"


def test_meta_controller_caps_low_complexity_fast_reasoning():

    class TaskProfile:
        complexity = "low"
        process_complexity = 0.0

    class ReasoningBudget:
        mode = "fast"
        max_reasoning_depth = 8
        max_active_routes = 8

    decision = MetaControllerEngine().decide(
        {
            "current_task_profile": TaskProfile(),
            "current_reasoning_budget": ReasoningBudget(),
        }
    )

    assert decision.action == "RUN_FAST_REASONING"
    assert decision.max_reasoning_depth <= 2
    assert decision.max_active_routes <= 2
    assert decision.enable_strategy_evolution is False


def test_meta_decision_report_includes_memory_reuse_and_meta_reason():

    runtime = RuntimeState()
    report = runtime.apply_meta_decision(
        MetaDecision(
            action="RUN_FAST_REASONING",
            reason="low_complexity",
            confidence=0.9,
            max_reasoning_depth=2,
            max_active_routes=2,
            enable_memory_reuse=True,
        )
    )

    assert report["enable_memory_reuse"] is True
    assert runtime.meta_reason == "low_complexity"
    assert runtime.context["meta_reason"] == "low_complexity"
    assert runtime.context["meta_executive_report"][
        "enable_memory_reuse"
    ] is True
    assert runtime.is_action_enabled("RUN_FAST_REASONING") is True
