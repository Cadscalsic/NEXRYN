from copy import deepcopy

from runtime.arena import (
    ArenaMemory,
    CandidateDiversityAnalyzer,
    CandidateNormalizer,
    CandidateProposalGateway,
    CandidateScorer,
    CandidateSimulator,
    CognitiveCandidateArena,
    SourceDominanceGuard,
    WinnerSelectionPolicy,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _proposal(source, operation, steps, confidence=0.9, **extra):
    return {
        "source": source,
        "hypothesis_id": f"hypothesis:{source}:{operation}",
        "intent": operation,
        "operation": operation,
        "program": {"step_count": len(steps), "steps": steps},
        "source_confidence": confidence,
        "semantic_support": extra.pop("semantic_support", 0.9),
        "truth_support": extra.pop("truth_support", 0.9),
        "context_support": extra.pop("context_support", 0.9),
        "dependency_support": extra.pop("dependency_support", 0.9),
        "identity_support": extra.pop("identity_support", 0.9),
        "localization_support": extra.pop("localization_support", 0.9),
        **extra,
    }


def _arena():
    return CognitiveCandidateArena(memory=ArenaMemory())


def test_multiple_independent_candidates_enter_arena_and_best_wins():
    proposals = [
        _proposal(
            "semantic_compiler",
            "replace_color",
            [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            confidence=0.90,
        ),
        _proposal(
            "adaptive_reuse",
            "preserve_grid",
            [{"operation": "preserve_grid", "parameters": {}}],
            confidence=1.0,
        ),
    ]

    report = _arena().run(
        proposals,
        input_grid=[[1, 1], [0, 0]],
        target_grid=[[2, 2], [0, 0]],
    )

    assert report["arena_state"] == "WINNER_SELECTED"
    assert report["candidate_count"] == 2
    assert report["source_count"] == 2
    assert report["simulation_count"] == 2
    assert report["winner_source"] == "semantic_compiler"
    assert report["winner_operation"] == "replace_color"
    assert report["winner_selected_from_evidence"] is True
    assert report["direct_source_to_executor_access"] is False


def test_duplicate_candidates_are_collapsed_and_provenance_preserved():
    gateway = CandidateProposalGateway().submit([
        _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        _proposal("rule_engine", "global_recolor", [{"operation": "global_recolor", "parameters": {"color_mapping": {1: 2}}}]),
    ])

    normalized = CandidateNormalizer().normalize(gateway["proposals"])
    candidate = normalized["normalized_candidates"][0]

    assert normalized["duplicate_candidates_collapsed"] == 1
    assert normalized["equivalent_candidate_groups"]
    assert sorted(candidate["sources"]) == ["rule_engine", "semantic_compiler"]
    assert len(candidate["provenance_history"]) == 2


def test_adaptive_reuse_does_not_win_automatically_when_simulation_is_worse():
    report = _arena().run(
        [
            _proposal("adaptive_reuse", "preserve_grid", [{"operation": "preserve_grid", "parameters": {}}], confidence=1.0),
            _proposal("rule_engine", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}], confidence=0.8),
        ],
        input_grid=[[1, 1]],
        target_grid=[[2, 2]],
    )

    assert report["winner_source"] == "rule_engine"
    assert report["winner_score"] > report["second_best_score"]


def test_highest_confidence_candidate_loses_when_simulation_is_worse():
    report = _arena().run(
        [
            _proposal("adaptive_reuse", "preserve_grid", [{"operation": "preserve_grid", "parameters": {}}], confidence=1.0),
            _proposal("semantic_compiler", "construct_path", [{"operation": "construct_path", "parameters": {"path_color": 1, "path_cells": [[0, 1], [0, 2]]}}], confidence=0.82),
        ],
        input_grid=[[1, 0, 0, 1]],
        target_grid=[[1, 1, 1, 1]],
    )

    assert report["winner_source"] == "semantic_compiler"
    assert report["candidate_summary"][0]["score"] != report["candidate_summary"][1]["score"]


def test_topology_damaging_candidate_is_penalized():
    gateway = CandidateProposalGateway().submit([
        _proposal("repair_engine", "remove_object", [{"operation": "remove_object", "parameters": {"cells_to_clear": [[0, 1]], "background_color": 0}}]),
    ])
    candidate = CandidateNormalizer().normalize(gateway["proposals"])["normalized_candidates"][0]
    simulation = CandidateSimulator().simulate(
        candidate,
        input_grid=[[1, 1, 1]],
        target_grid=[[1, 1, 1]],
    )
    score = CandidateScorer().score(candidate, simulation)

    assert score["penalties"]["topology_destruction"] > 0.0
    assert score["penalties"]["unexplained_residuals"] > 0.0


def test_identity_violating_candidate_is_blocked_but_visible():
    report = _arena().run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
                metadata={"identity_violation": True},
            ),
            _proposal("rule_engine", "preserve_grid", [{"operation": "preserve_grid", "parameters": {}}]),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
    )

    blocked = [row for row in report["candidate_summary"] if row["status"] == "BLOCKED_BY_GOVERNANCE"]
    assert blocked
    assert report["governance_blocked_count"] == 1
    assert "identity_violation" in blocked[0]["blocked_reason"]


def test_tie_produces_review_state():
    report = _arena().run(
        [
            _proposal("semantic_compiler", "construct_path", [{"operation": "construct_path", "parameters": {"path_color": 1, "path_cells": [[0, 1], [0, 2]]}}]),
            _proposal("rule_engine", "duplicate_object", [{"operation": "duplicate_object", "parameters": {"cells_to_write": [{"row": 0, "col": 1, "value": 1}, {"row": 0, "col": 2, "value": 1}]}}]),
        ],
        input_grid=[[1, 0, 0, 1]],
        target_grid=[[1, 1, 1, 1]],
    )

    assert report["selection_state"] == "TIE_REQUIRES_REVIEW"
    assert report["arena_state"] == "TIE_REQUIRES_REVIEW"


def test_weak_candidates_produce_no_safe_winner():
    report = _arena().run(
        [
            _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 3}}}], confidence=0.2, semantic_support=0.2, truth_support=0.2, context_support=0.2, dependency_support=0.2, identity_support=0.2, localization_support=0.0),
            _proposal("rule_engine", "preserve_grid", [{"operation": "preserve_grid", "parameters": {}}], confidence=0.2, semantic_support=0.2, truth_support=0.2, context_support=0.2, dependency_support=0.2, identity_support=0.2, localization_support=0.0),
        ],
        input_grid=[[1, 1]],
        target_grid=[[2, 2]],
    )

    assert report["selection_state"] == "NO_SAFE_WINNER"
    assert report["arena_state"] == "NO_SAFE_WINNER"


def test_single_valid_source_reports_single_source_only():
    report = _arena().run(
        [
            _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
    )

    assert report["arena_state"] == "SINGLE_SOURCE_ONLY"
    assert report["no_competition_reason"] == "Only one legitimate candidate entered the arena."


def test_rejected_gateway_candidate_remains_visible_in_report():
    report = _arena().run(
        [
            {"source": "adaptive_reuse", "winner": True, "operation": "preserve_grid", "program": {"steps": [{"operation": "preserve_grid", "parameters": {}}]}},
            _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
    )

    rejected = report["rejected_candidates"]
    assert any("source_attempted_direct_winner_declaration" in item["rejection_reasons"] for item in rejected)


def test_sandbox_simulation_has_no_persistent_effects():
    candidate = CandidateNormalizer().normalize(CandidateProposalGateway().submit([
        _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}])
    ])["proposals"])["normalized_candidates"][0]
    input_grid = [[1, 1]]
    original = deepcopy(input_grid)

    simulation = CandidateSimulator().simulate(candidate, input_grid=input_grid, target_grid=[[2, 2]])

    assert simulation["predicted_output"] == [[2, 2]]
    assert input_grid == original


def test_source_dominance_guard_detects_single_adaptive_source():
    review = SourceDominanceGuard().review(
        [{"source": "adaptive_reuse", "sources": ["adaptive_reuse"], "candidate_id": "a"}],
        winner={"source": "adaptive_reuse"},
    )

    assert review["dominance_detected"] is True
    assert "adaptive_reuse_without_meaningful_competition" in review["dominance_reasons"]


def test_arena_memory_statistics_are_operational():
    memory = ArenaMemory()
    arena = CognitiveCandidateArena(memory=memory)
    arena.run(
        [
            _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
            _proposal("adaptive_reuse", "preserve_grid", [{"operation": "preserve_grid", "parameters": {}}]),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
        task_signature="task:color",
    )

    assert memory.retrieve_similar_competitions("task:color")
    assert memory.get_source_statistics()["entries"]
    assert memory.get_operation_statistics()["winning_operations"]
    assert memory.get_program_statistics()["winning_program_signatures"]


def test_arena_report_is_compact_and_deterministic():
    report_state = {
        "runtime_status": "completed",
        "tasks_executed": 1,
        "successful_tasks": 1,
        "generated_programs": 2,
        "average_program_confidence": 0.8,
        "overall_search_quality": 0.7,
        "execution_coverage": 1.0,
        "COGNITIVE_CANDIDATE_ARENA_REPORT": _arena().run(
            [
                _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
                _proposal("adaptive_reuse", "preserve_grid", [{"operation": "preserve_grid", "parameters": {}}]),
            ],
            input_grid=[[1]],
            target_grid=[[2]],
        )["COGNITIVE_CANDIDATE_ARENA_REPORT"],
    }
    renderer = DeterministicFinalReportRenderer()
    first = renderer.render(report_state, runtime_metadata={"execution_id": "arena-test"})
    second = renderer.render(report_state, runtime_metadata={"execution_id": "arena-test"})

    assert first == second
    assert "COGNITIVE CANDIDATE ARENA" in first
    assert "Winner Score:" in first
    assert "candidate_arena_diagnostics" not in first


def test_diversity_analyzer_ignores_identical_program_name_variants():
    gateway = CandidateProposalGateway().submit([
        _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        _proposal("rule_engine", "remap_colors", [{"operation": "remap_colors", "parameters": {"color_mapping": {1: 2}}}]),
    ])
    normalized = CandidateNormalizer().normalize(gateway["proposals"])["normalized_candidates"]
    diversity = CandidateDiversityAnalyzer().analyze(normalized)

    assert diversity["candidate_count"] == 1
    assert diversity["unique_program_count"] == 1
    assert diversity["diversity_sufficient"] is False
