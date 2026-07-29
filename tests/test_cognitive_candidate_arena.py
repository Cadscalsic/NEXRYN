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
from runtime.reasoning.candidate_proposal_runtime import CandidateProposalRuntime
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


def test_candidate_simulator_applies_localized_replace_color_positions():
    report = CandidateSimulator().simulate(
        {
            "candidate_id": "candidate:localized-remap",
            "program": {
                "steps": [
                    {
                        "operation": "replace_color",
                        "parameters": {
                            "color_mapping": {0: 6, 1: 3},
                            "application_scope": "localized_changed_cells",
                            "affected_positions": [[0, 1], [1, 0]],
                        },
                    }
                ]
            },
        },
        input_grid=[
            [0, 0, 0],
            [1, 2, 2],
        ],
        target_grid=[
            [0, 6, 0],
            [3, 2, 2],
        ],
    )

    assert report["simulation_success"] is True
    assert report["prediction_accuracy"] == 1.0
    assert report["difference_count"] == 0


def test_same_source_duplicate_candidates_are_collapsed():
    gateway = CandidateProposalGateway().submit([
        _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        _proposal("semantic_compiler", "global_recolor", [{"operation": "global_recolor", "parameters": {"color_mapping": {1: 2}}}]),
    ])

    normalized = CandidateNormalizer().normalize(gateway["proposals"])
    candidate = normalized["normalized_candidates"][0]

    assert normalized["duplicate_candidates_collapsed"] == 1
    assert normalized["equivalent_candidate_groups"]
    assert sorted(candidate["sources"]) == ["semantic_compiler"]
    assert sorted(candidate["origin_sources"]) == ["semantic_compiler"]
    assert sorted(candidate["normalized_sources"]) == ["semantic_compiler"]
    assert len(candidate["provenance_history"]) == 2


def test_cross_source_equivalent_candidates_remain_independent_for_evaluation():
    gateway = CandidateProposalGateway().submit([
        _proposal("program_generation", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        _proposal("semantic_to_transformation_compiler", "global_recolor", [{"operation": "global_recolor", "parameters": {"color_mapping": {1: 2}}}]),
        _proposal("adaptive_reuse", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
    ])

    normalized = CandidateNormalizer().normalize(gateway["proposals"])
    candidates = normalized["normalized_candidates"]
    sources = sorted(candidate["source"] for candidate in candidates)

    assert normalized["duplicate_candidates_collapsed"] == 0
    assert len(candidates) == 3
    assert sources == [
        "adaptive_reuse",
        "normalized_program_candidates",
        "semantic_compiler",
    ]
    assert normalized["cross_source_consensus_count"] == 1
    consensus = normalized["cross_source_consensus_groups"][0]
    assert consensus["consensus_state"] == "CROSS_SOURCE_CONSENSUS"
    assert consensus["sources"] == sources
    assert all(candidate["cross_source_consensus"] is True for candidate in candidates)


def test_candidate_proposal_runtime_preserves_operational_investment_signal():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "program_generation": [
                _proposal(
                    "program_generation",
                    "replace_color",
                    [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
                    operational_value_score=0.86,
                    investment_tier="HIGH_VALUE",
                    investment_reason="compiler_supported, high_reuse_arc_operation",
                ),
                _proposal(
                    "program_generation",
                    "construct_path",
                    [{"operation": "construct_path", "parameters": {}}],
                    operational_value_score=0.41,
                    investment_tier="LOW_VALUE",
                    investment_reason="missing_requirements_penalty",
                ),
            ]
        }
    )

    assert report["high_value_knowledge_items"] == 1
    assert report["low_value_knowledge_items"] == 1
    assert report["deprioritized_knowledge_items"] == 1
    assert report["candidate_proposals"][0]["operational_value_score"] == 0.86
    assert report["candidate_proposals"][0]["investment_tier"] == "HIGH_VALUE"


def test_candidate_proposal_runtime_accepts_adaptive_reuse_composed_program():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reuse_success_rate": 1.0,
                "composed_program": {
                    "program_steps": [
                        {"operation": "preserve_grid", "parameters": {}}
                    ],
                    "step_count": 1,
                    "composition_state": "COMPOSED_FROM_EXPERIENCE",
                },
            }
        }
    )

    assert report["proposal_phase_status"] == "SINGLE_SOURCE"
    assert report["proposal_count"] == 1
    assert report["explicit_rejection_count"] == 0
    assert report["sources_with_proposals"] == ["adaptive_reuse"]
    assert report["candidate_proposals"][0]["operation"] == "preserve_grid"
    assert report["candidate_proposals"][0]["program"] == {
        "step_count": 1,
        "steps": [{"operation": "preserve_grid", "parameters": {}}],
    }


def test_candidate_proposal_runtime_preserves_adaptive_reuse_reused_program_body():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reuse_success_rate": 1.0,
                "reused_programs": [
                    {
                        "program": {
                            "program_steps": [
                                {"operation": "translate", "parameters": {"delta_row": 1}},
                            ],
                        },
                        "step_count": 1,
                    }
                ],
            }
        }
    )

    proposal = report["candidate_proposals"][0]

    assert report["proposal_count"] == 1
    assert report["sources_rejected"] == []
    assert proposal["source"] == "adaptive_reuse"
    assert proposal["operation"] == "translate"
    assert proposal["program"]["steps"] == [
        {"operation": "translate", "parameters": {"delta_row": 1}},
    ]


def test_candidate_proposal_runtime_accepts_adaptive_reuse_operation_sequence():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reuse_success_rate": 1.0,
                "reused_programs": [
                    {
                        "operation_sequence": [
                            {"operator": "duplicate_object", "parameters": {}},
                        ],
                        "step_count": 1,
                    }
                ],
            }
        }
    )

    proposal = report["candidate_proposals"][0]

    assert proposal["operation"] == "duplicate_object"
    assert proposal["program"]["steps"] == [
        {"operator": "duplicate_object", "parameters": {}},
    ]


def test_candidate_proposal_runtime_rejects_empty_semantic_compiler_program():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "semantic_to_transformation_compiler": {
                "system": "semantic_to_transformation_compiler",
                "semantic_to_transformation_compilation_success": False,
                "failure_reason": "missing_grid_pair",
                "compiled_program": {
                    "program_type": "transformation_program",
                    "step_count": 0,
                    "steps": [],
                },
            }
        }
    )

    assert report["proposal_count"] == 0
    assert report["sources_with_proposals"] == []
    assert report["sources_rejected"] == ["semantic_to_transformation_compiler"]
    assert report["candidate_proposals"][0]["proposal_status"] == "REJECTED"
    assert report["candidate_proposals"][0]["rejection_reason"] == "missing_grid_pair"


def test_candidate_proposal_runtime_reports_empty_steps_with_cognitive_reuse_mode():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reuse_success_rate": 1.0,
                "reused_strategies": [{"type": "directional_motion"}],
                "composed_program": {
                    "program_steps": [],
                    "step_count": 0,
                    "composition_state": "NO_PROGRAM_REUSE",
                },
            }
        }
    )

    diagnostic = report["source_diagnostics"]["adaptive_reuse"]

    assert report["sources_rejected"] == ["adaptive_reuse"]
    assert report["candidate_proposals"][0]["rejection_reason"] == "COGNITIVE_REUSE_ONLY"
    assert diagnostic["source_seen"] is True
    assert diagnostic["candidate_detected"] is False
    assert diagnostic["program_steps_present"] is False
    assert diagnostic["rejection_reason"] == "COGNITIVE_REUSE_ONLY"
    assert diagnostic["reuse_output_mode"] == "COGNITIVE_REUSE_ONLY"
    assert diagnostic["arena_admission_eligible"] is False


def test_candidate_proposal_runtime_reports_cognitive_reuse_only():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reuse_success_rate": 1.0,
                "reused_strategies": [{"type": "directional_motion"}],
            }
        }
    )

    diagnostic = report["source_diagnostics"]["adaptive_reuse"]

    assert report["sources_rejected"] == ["adaptive_reuse"]
    assert report["candidate_proposals"][0]["rejection_reason"] == (
        "COGNITIVE_REUSE_ONLY"
    )
    assert diagnostic["reused_strategy_count"] == 1
    assert diagnostic["reused_program_count"] == 0
    assert diagnostic["candidate_detected"] is False
    assert diagnostic["reuse_output_mode"] == "COGNITIVE_REUSE_ONLY"
    assert diagnostic["arena_admission_eligible"] is False


def test_candidate_proposal_runtime_treats_operational_reuse_evidence_as_cognitive_only():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reuse_success_rate": 0.0,
                "operational_independent_reuse_success_count": 32,
                "operational_reuse_evidence_count": 34,
                "reused_strategies": [],
                "reused_programs": [],
                "composed_program": {},
                "adaptive_reuse_candidate_materialization_state": (
                    "COGNITIVE_REUSE_ONLY"
                ),
            }
        }
    )

    diagnostic = report["source_diagnostics"]["adaptive_reuse"]

    assert report["sources_rejected"] == ["adaptive_reuse"]
    assert report["candidate_proposals"][0]["rejection_reason"] == (
        "COGNITIVE_REUSE_ONLY"
    )
    assert diagnostic["candidate_detected"] is False
    assert diagnostic["reuse_output_mode"] == "COGNITIVE_REUSE_ONLY"
    assert diagnostic["arena_admission_eligible"] is False


def test_adaptive_reuse_does_not_win_automatically_when_simulation_is_worse():
    report = _arena().run(
        [
            _proposal(
                "adaptive_reuse",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
                confidence=1.0,
                metadata={
                    "program_representation": "program_steps",
                    "reuse_evidence": "historical_reuse_candidate",
                },
            ),
            _proposal("rule_engine", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}], confidence=0.8),
        ],
        input_grid=[[1, 1]],
        target_grid=[[2, 2]],
    )

    assert report["winner_source"] == "rule_engine"
    assert report["winner_score"] > report["second_best_score"]
    adaptive_row = next(
        row for row in report["candidate_summary"]
        if row["source"] == "adaptive_reuse"
    )
    assert adaptive_row["program_representation"] == "program_steps"
    assert adaptive_row["reuse_evidence"] == "historical_reuse_candidate"


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
    assert report["winner_takes_all_detected"] is False


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


def test_no_safe_winner_can_emit_validation_probe_without_prediction_authority():
    report = _arena().run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
            _proposal(
                "rule_engine",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
                confidence=0.6,
            ),
        ],
        input_grid=[[1, 1], [0, 0]],
        target_grid=[[2, 2], [2, 2]],
    )

    recommendation = report["execution_recommendation"]

    assert report["selection_state"] == "NO_SAFE_WINNER"
    assert report["winner_selected_from_evidence"] is False
    assert report["winner_candidate_id"] is None
    assert recommendation["selected_candidate"] is None
    assert recommendation["execution_mode"] == "blocked"
    assert recommendation["validation_probe_candidate"] is not None
    assert recommendation["validation_probe_mode"] == "sandbox_validation_only"
    assert report["validation_probe_candidate_id"] == recommendation[
        "validation_probe_candidate"
    ]["candidate_id"]
    assert report["validation_probe_operation"] == "replace_color"
    assert report["validation_probe_authority"] == "SANDBOX_VALIDATION_ONLY"
    assert report["arena_to_compiled_bridge_state"] == "VALIDATION_PROBE_AVAILABLE"
    assert report["arena_to_compiled_bridge_action"] == (
        "route_validation_probe_to_compiler_without_prediction_authority"
    )
    probe_row = next(
        row for row in report["candidate_summary"]
        if row["candidate_id"] == report["validation_probe_candidate_id"]
    )
    assert probe_row["validation_probe"] is True
    assert probe_row["selected"] is False


def test_validation_probe_grounding_context_uses_shared_payload_when_direct_grids_empty():
    report = _arena().run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
                confidence=0.55,
            )
        ],
        input_grid=[],
        target_grid=[],
        runtime_context={
            "shared_state_inputs": {
                "input_grid": [[1, 0], [0, 0]],
                "target_grid": [[2, 0], [0, 0]],
                "predicted_output": [[2, 0], [0, 0]],
            }
        },
        analysis_only=True,
    )

    context = report["execution_recommendation"]["validation_probe_grounding_context"]
    shared_trace = report["validation_probe_shared_input_trace"]

    assert report["validation_probe_candidate_id"]
    assert context["input_grid"] == [[1, 0], [0, 0]]
    assert context["target_grid"] == [[2, 0], [0, 0]]
    assert context["predicted_output"] == [[2, 0], [0, 0]]
    assert shared_trace["input_population_state"] == "SHARED_TASK_IO_AVAILABLE"
    assert shared_trace["empty_keys"] == []
    assert shared_trace["non_empty_keys"] == [
        "input_grid",
        "target_grid",
        "predicted_output",
    ]


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


def test_arena_reports_source_diversity_sprint_when_single_source_enters():
    report = _arena().run(
        [
            _proposal(
                "program_generation",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
            ),
        ],
        input_grid=[[1]],
        target_grid=[[1]],
        runtime_context={
            "expected_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
                "adaptive_reuse",
            ],
        },
    )

    assert report["source_count"] == 1
    assert report["arena_source_diversity_state"] == "LOW_SOURCE_DIVERSITY"
    assert report["arena_source_diversity_action"] == (
        "SOURCE_DIVERSITY_SPRINT_REQUIRED"
    )
    assert "semantic_compiler" in report["missing_candidate_sources"]
    assert "adaptive_reuse" in report["missing_candidate_sources"]


def test_arena_reports_multi_source_state_when_competitive_sources_enter():
    report = _arena().run(
        [
            _proposal(
                "program_generation",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
            ),
            _proposal(
                "semantic_to_transformation_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
        runtime_context={
            "expected_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
            ],
        },
    )

    assert report["source_count"] == 2
    assert report["arena_source_diversity_state"] == "MULTI_SOURCE_ARENA"
    assert report["arena_source_diversity_action"] == "MONITOR_SOURCE_DIVERSITY"


def test_arena_traces_source_flow_from_proposal_runtime_to_competition():
    report = _arena().run(
        [
            _proposal(
                "program_generation",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
            ),
            _proposal(
                "semantic_to_transformation_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
        runtime_context={
            "candidate_proposal_report": {
                "sources_with_proposals": [
                    "program_generation",
                    "semantic_to_transformation_compiler",
                ],
            },
            "expected_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
            ],
        },
    )

    flow = {
        row["normalized_source"]: row
        for row in report["candidate_source_flow_trace"]
    }

    assert report["proposal_sources_with_proposals"] == [
        "program_generation",
        "semantic_to_transformation_compiler",
    ]
    assert flow["normalized_program_candidates"]["proposal_runtime_proposed"] is True
    assert flow["normalized_program_candidates"]["entered_arena"] is True
    assert flow["semantic_compiler"]["proposal_runtime_proposed"] is True
    assert flow["semantic_compiler"]["arena_proposal_built"] is True
    assert flow["semantic_compiler"]["gateway_accepted"] is True
    assert flow["semantic_compiler"]["entered_arena"] is True
    assert flow["semantic_compiler"]["build_failure_reason"] == "none"


def test_arena_source_flow_reports_direct_build_failure_reason():
    report = _arena().run(
        [
            _proposal(
                "program_generation",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
            ),
        ],
        input_grid=[[1]],
        target_grid=[[1]],
        runtime_context={
            "candidate_proposal_report": {
                "sources_with_proposals": [
                    "program_generation",
                    "semantic_to_transformation_compiler",
                ],
                "candidate_proposals": [
                    {
                        "source": "program_generation",
                        "proposal_status": "PROPOSED",
                        "operation": "preserve_grid",
                        "program": {
                            "step_count": 1,
                            "steps": [
                                {"operation": "preserve_grid", "parameters": {}}
                            ],
                        },
                    }
                ],
            },
            "expected_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
            ],
        },
    )

    flow = {
        row["normalized_source"]: row
        for row in report["candidate_source_flow_trace"]
    }

    assert flow["semantic_compiler"]["flow_state"] == (
        "PROPOSAL_NOT_BUILT_FOR_ARENA"
    )
    assert flow["semantic_compiler"]["build_failure_reason"] == (
        "proposal_row_missing"
    )
    assert flow["semantic_compiler"]["build_failure_detail"] == (
        "source_listed_in_sources_with_proposals_but_no_row_found"
    )


def test_arena_source_flow_keeps_proposal_runtime_rejections_visible():
    report = _arena().run(
        [
            _proposal(
                "program_generation",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
            ),
        ],
        input_grid=[[1]],
        target_grid=[[1]],
        runtime_context={
            "candidate_proposal_report": {
                "sources_with_proposals": ["program_generation"],
                "sources_rejected": ["semantic_to_transformation_compiler"],
                "candidate_proposals": [
                    {
                        "source": "program_generation",
                        "proposal_status": "PROPOSED",
                        "operation": "preserve_grid",
                        "program": {
                            "step_count": 1,
                            "steps": [
                                {"operation": "preserve_grid", "parameters": {}}
                            ],
                        },
                    },
                    {
                        "source": "semantic_to_transformation_compiler",
                        "proposal_status": "REJECTED",
                        "rejection_reason": "missing_grid_pair",
                        "program": {"step_count": 0, "steps": []},
                    },
                ],
                "source_diagnostics": {
                    "semantic_to_transformation_compiler": {
                        "candidate_detected": False,
                        "program_steps_present": False,
                    }
                },
            },
            "expected_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
            ],
        },
    )

    flow = {
        row["normalized_source"]: row
        for row in report["candidate_source_flow_trace"]
    }

    assert flow["semantic_compiler"]["flow_state"] == (
        "REJECTED_BY_PROPOSAL_RUNTIME"
    )
    assert flow["semantic_compiler"]["proposal_runtime_rejected"] is True
    assert flow["semantic_compiler"]["proposal_runtime_rejection_reason"] == (
        "missing_grid_pair"
    )
    assert flow["semantic_compiler"]["blocked_stage"] == (
        "candidate_proposal_runtime"
    )
    assert flow["semantic_compiler"]["source_diagnostic"] == {
        "candidate_detected": False,
        "program_steps_present": False,
    }


def test_arena_detects_cross_source_consensus_without_pre_evaluation_merge():
    report = _arena().run(
        [
            _proposal(
                "program_generation",
                "duplicate_object",
                [{"operation": "duplicate_object", "parameters": {"cells_to_write": [[0, 1, 2]]}}],
            ),
            _proposal(
                "semantic_to_transformation_compiler",
                "duplicate_object",
                [{"operation": "duplicate_object", "parameters": {"cells_to_write": [[0, 1, 2]]}}],
            ),
            _proposal(
                "adaptive_reuse",
                "duplicate_object",
                [{"operation": "duplicate_object", "parameters": {"cells_to_write": [[0, 1, 2]]}}],
            ),
        ],
        input_grid=[[1, 0]],
        target_grid=[[1, 2]],
        runtime_context={
            "expected_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
                "adaptive_reuse",
            ],
        },
    )

    assert report["candidate_count"] == 3
    assert report["cross_source_consensus_state"] == "CROSS_SOURCE_CONSENSUS"
    assert report["cross_source_consensus_count"] == 1
    assert sorted(report["cross_source_consensus_groups"][0]["sources"]) == [
        "adaptive_reuse",
        "normalized_program_candidates",
        "semantic_compiler",
    ]
    assert all(
        row["cross_source_consensus"] is True
        for row in report["candidate_summary"]
    )


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


def test_diversity_analyzer_preserves_cross_source_program_variants():
    gateway = CandidateProposalGateway().submit([
        _proposal("semantic_compiler", "replace_color", [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]),
        _proposal("rule_engine", "remap_colors", [{"operation": "remap_colors", "parameters": {"color_mapping": {1: 2}}}]),
    ])
    normalized = CandidateNormalizer().normalize(gateway["proposals"])["normalized_candidates"]
    diversity = CandidateDiversityAnalyzer().analyze(normalized)

    assert diversity["candidate_count"] == 2
    assert diversity["unique_program_count"] == 1
    assert diversity["source_count"] == 2
    assert diversity["diversity_sufficient"] is False
