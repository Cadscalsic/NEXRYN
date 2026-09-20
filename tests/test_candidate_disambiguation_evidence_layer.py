from runtime.arena import (
    ArenaMemory,
    CandidateDisambiguationEvidenceLayer,
    CognitiveCandidateArena,
)


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


def test_tie_emits_observation_only_disambiguation_need():
    report = _arena().run(
        [
            _proposal(
                "semantic_compiler",
                "construct_path",
                [
                    {
                        "operation": "construct_path",
                        "parameters": {"path_color": 1, "path_cells": [[0, 1], [0, 2]]},
                    }
                ],
            ),
            _proposal(
                "rule_engine",
                "duplicate_object",
                [
                    {
                        "operation": "duplicate_object",
                        "parameters": {
                            "cells_to_write": [
                                {"row": 0, "col": 1, "value": 1},
                                {"row": 0, "col": 2, "value": 1},
                            ]
                        },
                    }
                ],
            ),
        ],
        input_grid=[[1, 0, 0, 1]],
        target_grid=[[1, 1, 1, 1]],
        runtime_context={"run_id": "run_tie", "task_id": "task_tie"},
        task_signature="task:tied-path",
    )

    disambiguation = report["candidate_arena_diagnostics"][
        "candidate_disambiguation_report"
    ]

    assert report["selection_state"] == "TIE_REQUIRES_REVIEW"
    assert report["candidate_disambiguation_need_count"] == 1
    assert report["candidate_disambiguation_authority"] == "OBSERVATION_REQUEST_ONLY"
    assert report["candidate_disambiguation_behavioral_authority"] == "NONE"
    assert report["execution_recommendation"]["execution_mode"] == "blocked"
    need = disambiguation["candidate_disambiguation_evidence_needs"][0]
    assert need["authority_state"] == "OBSERVATION_REQUEST_ONLY"
    assert need["behavioral_authority"] == "NONE"
    assert need["disagreement_type"] in {
        "PREDICTION_DISAGREEMENT",
        "SEMANTIC_DISAGREEMENT",
        "STRUCTURAL_DISAGREEMENT",
    }
    assert need["proposed_evidence_method"] in {
        "DISCRIMINATIVE_VALIDATION",
        "COUNTERFACTUAL_DISAMBIGUATION",
    }
    assert set(need["candidate_ids"]) == set(disambiguation["top_tied_candidate_ids"])


def test_non_discriminating_tie_preserves_tie_without_winner_authority():
    report = _arena().run(
        [
            _proposal(
                "semantic_compiler",
                "construct_path",
                [
                    {
                        "operation": "construct_path",
                        "parameters": {"path_color": 1, "path_cells": [[0, 1], [0, 2]]},
                    }
                ],
                candidate_id="same-a",
            ),
            _proposal(
                "rule_engine",
                "connect_components",
                [
                    {
                        "operation": "connect_components",
                        "parameters": {"path_color": 1, "path_cells": [[0, 1], [0, 2]]},
                    }
                ],
                candidate_id="same-b",
            ),
        ],
        input_grid=[[1, 0, 0, 1]],
        target_grid=[[1, 1, 1, 1]],
    )

    disambiguation = report["candidate_arena_diagnostics"][
        "candidate_disambiguation_report"
    ]
    need = disambiguation["candidate_disambiguation_evidence_needs"][0]

    assert report["selection_state"] == "TIE_REQUIRES_REVIEW"
    assert need["disagreement_type"] != "PREDICTION_DISAGREEMENT"
    assert report["winner_selected_from_evidence"] is False
    assert report["candidate_disambiguation_resolution_state"] == (
        "TIE_REMAINS_INSUFFICIENT_EVIDENCE"
    )
    assert report["candidate_disambiguation_authority"] == "OBSERVATION_REQUEST_ONLY"


def test_disambiguation_identity_distinguishes_equivalent_cross_source_candidates():
    layer = CandidateDisambiguationEvidenceLayer()
    report = layer.analyze(
        [
            {
                "candidate_id": "a",
                "source": "semantic_compiler",
                "sources": ["semantic_compiler"],
                "operation": "replace_color",
                "program_signature": "same-program",
                "program": {"steps": [{"operation": "replace_color"}]},
            },
            {
                "candidate_id": "b",
                "source": "rule_engine",
                "sources": ["rule_engine"],
                "operation": "replace_color",
                "program_signature": "same-program",
                "program": {"steps": [{"operation": "replace_color"}]},
            },
        ],
        [
            {"candidate_id": "a", "final_score": 0.9, "eligible_for_selection": True},
            {"candidate_id": "b", "final_score": 0.9, "eligible_for_selection": True},
        ],
        {
            "a": {"simulation_success": True, "predicted_output": [[2]], "prediction_accuracy": 1.0},
            "b": {"simulation_success": True, "predicted_output": [[2]], "prediction_accuracy": 1.0},
        },
        {
            "selection_state": "TIE_REQUIRES_REVIEW",
            "winner_candidate": {"candidate_id": "a"},
            "second_best_candidate": {"candidate_id": "b"},
        },
    )

    identities = report["candidate_identities"]
    assert len({item["candidate_fingerprint"] for item in identities}) == 2
    need = report["candidate_disambiguation_evidence_needs"][0]
    assert need["disagreement_type"] == "SOURCE_SUPPORT_DISAGREEMENT"
    assert need["proposed_evidence_method"] == "CROSS_SOURCE_CORROBORATION"


def test_disambiguation_layer_is_not_applicable_when_arena_selects_winner():
    report = _arena().run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
            _proposal(
                "adaptive_reuse",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
                confidence=0.6,
            ),
        ],
        input_grid=[[1, 1]],
        target_grid=[[2, 2]],
    )

    disambiguation = report["candidate_arena_diagnostics"][
        "candidate_disambiguation_report"
    ]
    assert report["selection_state"] == "WINNER_SELECTED"
    assert disambiguation["tie_disambiguation_applicable"] is False
    assert disambiguation["candidate_disambiguation_evidence_needs"] == []
    assert disambiguation["score_authority"] == "NONE"
