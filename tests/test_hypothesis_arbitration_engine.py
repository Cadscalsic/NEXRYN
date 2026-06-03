from runtime.engines.program_synthesis import ProgramSynthesisEngine
from runtime.reasoning.hypothesis_arbitration_engine import (
    HypothesisArbitrationEngine,
)


class FakeWorldModel:
    def anticipate_program(
        self,
        input_grid,
        target_grid,
        synthesized_program,
        minimum_accuracy,
    ):
        operation = synthesized_program["steps"][0]["operation"]
        accuracy = {
            "duplicate_object": 0.84,
            "expand_object": 0.96,
        }[operation]
        return {
            "prediction_report": {
                "prediction_accuracy": accuracy,
            },
        }


def test_execution_arbitration_prefers_world_model_fit_for_close_candidates():
    report = HypothesisArbitrationEngine().arbitrate_execution_candidates(
        hypotheses=[
            {
                "type": "object_count",
                "primitive": "duplicate_object",
                "search_final_score": 0.8707,
                "operator_reward_score": 0.84,
                "geometric_grounding": {"confidence": 0.96},
            },
            {
                "type": "object_size",
                "primitive": "expand_object",
                "search_final_score": 0.8291,
                "operator_reward_score": 0.88,
                "geometric_grounding": {"confidence": 0.94},
            },
        ],
        input_grid=[],
        target_grid=[],
        world_model_engine=FakeWorldModel(),
        program_synthesis_engine=ProgramSynthesisEngine(),
    )

    assert report["winner"]["hypothesis"]["primitive"] == "expand_object"
    assert report["winner"]["hypothesis"]["world_model_fit"] == 0.96
    assert report["selection_factors"] == [
        "search_final_score",
        "causal_support",
        "semantic_support",
        "world_model_fit",
        "historical_success",
    ]
