from runtime.pipeline import AdaptiveCognitivePipeline


def test_adaptive_reasoning_budget_caps_dependency_explosion_by_default():
    pipeline = AdaptiveCognitivePipeline()

    pipeline.configure_reasoning_budget(mode="adaptive")

    assert pipeline.reasoning_budget["max_chain_depth"] == 4
    assert pipeline.reasoning_budget["max_dependency_depth"] == 4
    assert pipeline.reasoning_budget["max_concepts"] == 8


def test_cli_reasoning_budget_overrides_adaptive_caps():
    pipeline = AdaptiveCognitivePipeline()

    pipeline.configure_reasoning_budget(
        mode="adaptive",
        max_chain_depth=6,
        max_concepts=3,
    )

    assert pipeline.reasoning_budget["max_chain_depth"] == 6
    assert pipeline.reasoning_budget["max_dependency_depth"] == 6
    assert pipeline.reasoning_budget["max_concepts"] == 3
