from copy import deepcopy

from runtime.counterfactual import (
    AlternativeWorldBuilder,
    AssumptionExtractor,
    CounterfactualBudgetManager,
    CounterfactualEligibilityGate,
    CounterfactualGenerator,
    CounterfactualMemory,
    CounterfactualReasoningEngine,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _candidate(operation="preserve_grid", program=None):
    return {
        "candidate_id": "winner-1",
        "hypothesis_id": "hypothesis:winner",
        "operation": operation,
        "program": program or {
            "step_count": 1,
            "steps": [{"operation": operation, "parameters": {}}],
        },
        "source_confidence": 0.7,
        "truth_support": 0.8,
        "context_support": 0.8,
        "dependency_support": 0.8,
    }


def _arena(candidate=None, **overrides):
    candidate = candidate or _candidate()
    report = {
        "winner_candidate_id": candidate["candidate_id"],
        "winner_operation": candidate["operation"],
        "winner_score": 0.82,
        "selection_margin": 0.01,
        "selection_state": "CONDITIONAL_WINNER",
        "execution_recommendation": {"selected_candidate": candidate},
        "normalized_candidates": [candidate],
        "candidate_count": 2,
    }
    report.update(overrides)
    return report


def test_counterfactual_search_skips_after_exact_success():
    arena = _arena(
        _candidate("replace_color", {
            "step_count": 1,
            "steps": [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
        }),
        winner_score=0.97,
        selection_margin=0.2,
        selection_state="WINNER_SELECTED",
    )

    report = CounterfactualReasoningEngine().reason(
        arena,
        input_grid=[[1]],
        target_grid=[[2]],
    )

    compact = report["COUNTERFACTUAL_REASONING_REPORT"]
    assert compact["counterfactual_required"] is False
    assert compact["eligibility_state"] == "SKIPPED"
    assert compact["stop_reason"] == "WINNER_STABLE"


def test_counterfactual_search_triggers_for_close_arena_score():
    gate = CounterfactualEligibilityGate().evaluate(
        _arena(selection_margin=0.01, winner_score=0.82),
        {},
    )

    assert gate["counterfactual_required"] is True
    assert "selection_margin_below_threshold" in gate["trigger_reasons"]


def test_generator_changes_only_one_assumption_per_basic_counterfactual():
    candidate = _candidate()
    assumptions = AssumptionExtractor().extract(candidate)["assumptions"]
    generated = CounterfactualGenerator().generate(
        candidate,
        assumptions,
        budget={"max_counterfactuals": 3},
    )

    assert generated["generated_counterfactual_count"] >= 1
    assert all(len(item["changed_assumption_ids"]) == 1 for item in generated["generated_counterfactuals"])


def test_original_runtime_state_and_sandbox_world_remain_unchanged():
    world = {"world_id": "current", "grid": [[1]], "preserved_invariants": ["identity"]}
    original = deepcopy(world)
    cf = {
        "counterfactual_id": "cf-1",
        "changed_assumption_id": "a1",
        "changed_assumption_ids": ["a1"],
        "change_type": "operation_substitution",
    }

    built = AlternativeWorldBuilder().build(cf, world)

    assert built["persistent_effects_forbidden"] is True
    assert world == original


def test_better_alternative_weakens_original_and_revision_reenters_arena():
    winner = _candidate("preserve_grid")
    alternative = {
        "candidate_id": "alt-1",
        "hypothesis_id": "hypothesis:alt",
        "operation": "replace_color",
        "program": {
            "step_count": 1,
            "steps": [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
        },
        "source_confidence": 0.8,
    }
    arena = _arena(winner)
    arena["normalized_candidates"] = [winner, alternative]

    report = CounterfactualReasoningEngine().reason(
        arena,
        input_grid=[[1, 1]],
        target_grid=[[2, 2]],
    )
    compact = report["COUNTERFACTUAL_REASONING_REPORT"]

    assert compact["simulated_counterfactual_count"] >= 1
    assert compact["falsifying_evidence"]
    assert compact["minimal_revision_generated"] is True
    assert report["minimal_revision_report"]["requires_arena_reentry"] is True


def test_identity_or_protected_invariant_counterfactual_is_blocked():
    world = AlternativeWorldBuilder().build({
        "counterfactual_id": "cf-protected",
        "changed_assumption_id": "identity",
        "changed_assumption_ids": ["identity"],
        "change_type": "invariance_challenge",
        "protected_invariant": True,
    })

    assert world["world_valid"] is False
    assert "protected_invariant_cannot_be_negated" in world["validation_issues"]


def test_residual_guided_mutation_reduces_residual_count():
    winner = _candidate("preserve_grid")
    arena = _arena(winner)

    report = CounterfactualReasoningEngine().reason(
        arena,
        input_grid=[[1, 0, 0, 1]],
        target_grid=[[1, 1, 1, 1]],
        runtime_context={"residual_cells": [[0, 1], [0, 2]]},
    )

    assert any(
        row["residual"] == 0
        for row in report["COUNTERFACTUAL_REASONING_REPORT"]["counterfactual_summary"]
    )


def test_budget_exhaustion_stops_safely():
    manager = CounterfactualBudgetManager()

    assert manager.allow("cf-1", 0, {"max_counterfactuals": 1})["allowed"] is True
    blocked = manager.allow("cf-2", 1, {"max_counterfactuals": 1})

    assert blocked["allowed"] is False
    assert blocked["stop_reason"] == "BUDGET_EXHAUSTED"


def test_counterfactual_memory_preserves_provenance_and_revalidates_reuse():
    memory = CounterfactualMemory()
    episode = {
        "task_signature": "task:1",
        "generated_counterfactual_count": 2,
        "failed_assumptions": ["a1"],
        "surviving_assumptions": ["a2"],
        "revision_operations": ["cf-1"],
    }

    memory.record_counterfactual_episode(episode)

    assert memory.retrieve_similar_counterfactuals("task:1")[0]["task_signature"] == "task:1"
    assert memory.get_falsified_assumptions() == ["a1"]
    assert memory.get_stable_assumptions() == ["a2"]
    assert memory.get_residual_revision_patterns()["cf-1"] == 1
    assert memory.get_counterfactual_statistics()["tested_counterfactuals"] == 2


def test_falsification_does_not_revoke_committed_truth():
    winner = _candidate("preserve_grid")
    alt = {
        "candidate_id": "alt",
        "hypothesis_id": "hypothesis:alt",
        "operation": "replace_color",
        "program": {"step_count": 1, "steps": [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]},
    }
    arena = _arena(winner)
    arena["normalized_candidates"] = [winner, alt]

    report = CounterfactualReasoningEngine().reason(
        arena,
        input_grid=[[1]],
        target_grid=[[2]],
        runtime_context={"committed_truth": True},
    )

    assert report["falsification_report"]["truth_revocation_performed"] is False


def test_counterfactual_report_is_compact_and_deterministic():
    engine_report = CounterfactualReasoningEngine().reason(
        _arena(_candidate("preserve_grid")),
        input_grid=[[1]],
        target_grid=[[2]],
    )
    state = {
        "runtime_status": "completed",
        "tasks_executed": 1,
        "successful_tasks": 1,
        "generated_programs": 1,
        "average_program_confidence": 0.8,
        "overall_search_quality": 0.7,
        "execution_coverage": 1.0,
        "COUNTERFACTUAL_REASONING_ENGINE_REPORT": engine_report,
    }
    renderer = DeterministicFinalReportRenderer()
    first = renderer.render(state, runtime_metadata={"execution_id": "cf-test"})
    second = renderer.render(state, runtime_metadata={"execution_id": "cf-test"})

    assert first == second
    assert "COUNTERFACTUAL REASONING REPORT" in first
    assert "Generated Counterfactuals:" in first
    assert "alternative_world" not in first
