import json

from runtime.adaptive_reuse import AdaptiveReuseLayer
from runtime.adaptive_reuse.episode_memory import EpisodeMemory
from runtime.adaptive_reuse.experience_index import ExperienceIndex
from runtime.adaptive_reuse.program_reuse_engine import ProgramReuseEngine
from runtime.adaptive_reuse.strategy_retriever import StrategyRetriever


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
