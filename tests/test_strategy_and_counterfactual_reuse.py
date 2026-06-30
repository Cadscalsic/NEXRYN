from runtime.reasoning.counterfactual_reuse_engine import (
    CounterfactualReuseEngine,
)
from runtime.strategy.strategy_reuse_engine import StrategyReuseEngine


def test_strategy_reuse_promotes_committed_truths_to_solution_methods():
    report = StrategyReuseEngine().evaluate(
        truths=[{
            "concept": "growth",
            "truth_id": "truth:growth",
            "truth_confidence": 0.94,
        }],
        hypotheses=[{
            "concept": "growth",
            "hypothesis_id": "hypothesis:growth:truth_reuse",
            "confidence": 0.93,
            "status": "ACCEPTED_HYPOTHESIS",
        }],
    )

    assert report["strategy_hits"] == 1
    assert report["strategy_misses"] == 0
    assert report["strategy_reuse_rate"] == 1.0
    assert report["reused_strategies"][0]["concept"] == "growth"
    assert (
        report["reused_strategies"][0]["reuse_state"]
        == "STRATEGY_REUSED"
    )


def test_counterfactual_reuse_tracks_hits_and_success():
    report = CounterfactualReuseEngine().evaluate(
        counterfactuals=[{
            "counterfactual_id": "counterfactual:growth:truth_removed",
            "concept": "growth",
            "counterfactual_robustness": 0.94,
            "status": "COUNTERFACTUAL_READY",
        }],
        truths=[{
            "concept": "growth",
            "truth_confidence": 0.94,
        }],
        hypotheses=[{
            "concept": "growth",
            "status": "ACCEPTED_HYPOTHESIS",
        }],
    )

    assert report["counterfactual_hits"] == 1
    assert report["counterfactual_misses"] == 0
    assert report["counterfactual_reuse_rate"] == 1.0
    assert report["counterfactual_success"] == 1
    assert report["counterfactual_success_rate"] == 1.0
