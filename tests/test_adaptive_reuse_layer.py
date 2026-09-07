import json

from runtime.adaptive_reuse import AdaptiveReuseLayer
from runtime.adaptive_reuse.episode_memory import EpisodeMemory
from runtime.adaptive_reuse.experience_index import ExperienceIndex
from runtime.adaptive_reuse.program_reuse_engine import ProgramReuseEngine
from runtime.adaptive_reuse.strategy_retriever import StrategyRetriever
from runtime.reasoning.candidate_proposal_runtime import CandidateProposalRuntime


class _EmptyProgramMemory:
    def load(self):
        return []


class _UnusableProgramMemory:
    def load(self):
        return [
            {
                "program_id": "program:concept_only",
                "program": {
                    "program_steps": [
                        {"operation": "unknown_concept_only", "parameters": {}},
                    ],
                },
                "confidence": 0.99,
            }
        ]


class _ProgramMemory:
    def load(self):
        return [{
            "program_id": "program:recolor",
            "program": {
                "program_steps": [
                    {"operation": "recolor", "parameters": {"target": 2}},
                ],
            },
            "operation_sequence": [{"operation": "recolor"}],
            "confidence": 0.95,
        }]


def _layer(tmp_path):
    storage = tmp_path / "storage"
    experiences = storage / "experiences"
    experiences.mkdir(parents=True)
    (experiences / "experience_color.json").write_text(
        json.dumps({
            "experience_id": "experience_color",
            "winner_hypothesis": {
                "type": "color_replacement",
                "confidence": 0.95,
                "description": "symbolic color replacement",
            },
            "evaluation_result": {
                "success": True,
                "final_score": 0.96,
            },
            "semantic_graph": {
                "concept_nodes": [
                    {"concept": "color_transformation", "confidence": 0.95},
                    {"concept": "symbolic_surface_remapping", "confidence": 0.9},
                ],
            },
            "execution_plan": {
                "node_count": 1,
                "nodes": [
                    {
                        "operation": "recolor",
                        "dependencies": ["color_mapping"],
                    },
                ],
            },
            "truth_commitments": [
                {"concept": "color_transformation", "truth_state": "LOCKED"},
            ],
        }),
        encoding="utf-8",
    )
    index = ExperienceIndex(storage)
    retriever = StrategyRetriever(experience_index=index)
    programs = ProgramReuseEngine(_ProgramMemory())
    return AdaptiveReuseLayer(
        experience_index=index,
        strategy_retriever=retriever,
        program_reuse_engine=programs,
        episode_memory=EpisodeMemory(experiences),
    )


def test_adaptive_reuse_layer_retrieves_adapts_and_reports_hits(tmp_path):
    report = _layer(tmp_path).evaluate({
        "concept": "color_transformation",
        "semantic_graph": {
            "concept_nodes": [
                {"concept": "color_transformation"},
                {"concept": "symbolic_surface_remapping"},
            ],
        },
        "execution_plan": {
            "nodes": [{"operation": "recolor"}],
        },
        "truth_commitments": [
            {"concept": "color_transformation", "truth_state": "LOCKED"},
        ],
    })

    assert report["ADAPTIVE_REUSE_REPORT"] is True
    assert report["experience_count"] == 1
    assert report["retrieval_successes"] == 1
    assert report["strategy_hits"] >= 1
    assert report["program_hits"] >= 1
    assert report["truth_hits"] >= 1
    assert report["cache_hits"] >= 3
    assert report["reuse_success_rate"] == 1.0
    assert report["estimated_compute_saved"] > 0
    assert report["composed_program"]["step_count"] >= 1
    assert report["reuse_output_mode"] == "EXECUTABLE_REUSE_AVAILABLE"
    assert report["arena_admission_eligible"] is True


def test_adaptive_reuse_layer_marks_cognitive_reuse_without_executable_payload(tmp_path):
    storage = tmp_path / "storage"
    experiences = storage / "experiences"
    experiences.mkdir(parents=True)
    (experiences / "experience_identity.json").write_text(
        json.dumps({
            "experience_id": "experience_identity",
            "winner_hypothesis": {
                "type": "identity_prior",
                "confidence": 0.91,
            },
            "evaluation_result": {
                "success": True,
                "final_score": 0.93,
            },
            "semantic_graph": {
                "concept_nodes": [
                    {"concept": "identity_prior", "confidence": 0.91},
                ],
            },
            "truth_commitments": [
                {"concept": "identity_prior", "truth_state": "LOCKED"},
            ],
        }),
        encoding="utf-8",
    )
    index = ExperienceIndex(storage)
    layer = AdaptiveReuseLayer(
        experience_index=index,
        strategy_retriever=StrategyRetriever(index),
        program_reuse_engine=ProgramReuseEngine(_EmptyProgramMemory()),
        episode_memory=EpisodeMemory(experiences),
    )

    report = layer.evaluate({
        "concept": "identity_prior",
        "semantic_graph": {
            "concept_nodes": [{"concept": "identity_prior"}],
        },
        "truth_commitments": [
            {"concept": "identity_prior", "truth_state": "LOCKED"},
        ],
    })

    assert report["retrieval_successes"] == 1
    assert report["cognitive_reuse_available"] is True
    assert report["executable_reuse_available"] is False
    assert report["arena_admission_eligible"] is False
    assert report["reuse_output_mode"] == "COGNITIVE_REUSE_ONLY"


def test_experience_index_treats_none_scores_as_missing(tmp_path):
    storage = tmp_path / "storage"
    experiences = storage / "experiences"
    experiences.mkdir(parents=True)
    (experiences / "experience_null_scores.json").write_text(
        json.dumps({
            "experience_id": "experience_null_scores",
            "execution_cost": None,
            "reasoning_depth": None,
            "winner_hypothesis": {
                "type": "color_replacement",
                "confidence": None,
            },
            "evaluation_result": {
                "success": False,
                "final_score": None,
                "accuracy": None,
            },
        }),
        encoding="utf-8",
    )

    loaded = ExperienceIndex(storage).load()

    assert len(loaded) == 1
    assert loaded[0].execution_cost == 0.0
    assert loaded[0].reasoning_depth == 0
    assert loaded[0].confidence == 0.0


def test_program_reuse_converts_cognitive_strategy_to_executable_operation():
    report = ProgramReuseEngine(_EmptyProgramMemory()).retrieve(
        {"concept": "directional_motion"},
        strategies=[
            {
                "type": "directional_motion",
                "confidence": 0.91,
            }
        ],
    )

    assert report["program_reuse_success"] is True
    assert report["program_hits"] == 1
    assert report["composed_program"]["program_steps"] == [
        {"operation": "translate", "parameters": {}},
    ]


def test_program_reuse_keeps_preservation_capabilities_arena_executable():
    report = ProgramReuseEngine(_EmptyProgramMemory()).retrieve(
        {"concept": "color_preservation"},
        strategies=[
            {
                "type": "color_preservation",
                "confidence": 0.93,
            },
            {
                "type": "object_identity_preservation",
                "confidence": 0.9,
            },
        ],
    )

    operations = [
        step["operation"]
        for step in report["composed_program"]["program_steps"]
    ]

    assert report["program_reuse_success"] is True
    assert operations == ["preserve_colors", "preserve_grid"]


def test_adaptive_reuse_strategy_program_enters_candidate_proposal_runtime():
    adaptive_report = ProgramReuseEngine(_EmptyProgramMemory()).retrieve(
        {"concept": "directional_motion"},
        strategies=[
            {
                "type": "directional_motion",
                "confidence": 0.91,
            }
        ],
    )
    adaptive_report["reuse_success_rate"] = 1.0

    proposal_report = CandidateProposalRuntime().collect(
        candidate_sources={"adaptive_reuse": adaptive_report},
    )

    assert proposal_report["sources_with_proposals"] == ["adaptive_reuse"]
    assert proposal_report["sources_rejected"] == []
    assert proposal_report["candidate_proposals"][0]["operation"] == "translate"


def test_program_reuse_fails_closed_for_parameter_required_strategy_without_parameters():
    report = ProgramReuseEngine(_UnusableProgramMemory()).retrieve(
        {"concept": "color_replacement"},
        strategies=[
            {
                "type": "partial_color_replacement",
                "confidence": 0.9,
            }
        ],
    )

    assert report["program_reuse_success"] is False
    assert report["program_hits"] == 0
    assert report["reused_programs"] == []
    assert report["composed_program"]["program_steps"] == []


def test_program_reuse_accepts_primitive_field_in_memory_fragment_steps():
    class _PrimitiveProgramMemory:
        def load(self):
            return [
                {
                    "program_id": "program:primitive",
                    "program": {
                        "program_steps": [
                            {"primitive": "object_connection", "parameters": {}},
                        ],
                    },
                    "confidence": 0.95,
                }
            ]

    report = ProgramReuseEngine(_PrimitiveProgramMemory()).retrieve(
        {"concept": "bridge_creation"},
    )

    assert report["program_reuse_success"] is True
    assert report["composed_program"]["program_steps"] == [
        {"operation": "connect_components", "parameters": {}},
    ]
