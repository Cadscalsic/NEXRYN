from runtime.planning.execution_profile import (
    SHARED_LIFECYCLE,
    SHARED_METRIC_KEYS,
    build_execution_profile,
)
from runtime.pipeline.legacy_pipeline import AdaptiveCognitivePipeline


def test_adaptive_and_deep_profiles_share_one_pipeline_contract():
    adaptive = build_execution_profile("adaptive")
    deep = build_execution_profile("deep")

    assert adaptive.pipeline_name == "adaptive"
    assert deep.pipeline_name == "adaptive"
    assert adaptive.lifecycle_contract == deep.lifecycle_contract
    assert adaptive.metric_contract == deep.metric_contract
    assert adaptive.lifecycle_contract == SHARED_LIFECYCLE
    assert adaptive.metric_contract == SHARED_METRIC_KEYS
    assert deep.reasoning_depth > adaptive.reasoning_depth
    assert deep.search_budget > adaptive.search_budget


def test_pipeline_configuration_exposes_profile_without_swapping_pipeline():
    pipeline = AdaptiveCognitivePipeline()

    adaptive_budget = pipeline.configure_reasoning_budget(mode="adaptive")
    deep_budget = pipeline.configure_reasoning_budget(mode="deep")

    assert adaptive_budget["cognitive_pipeline"] == "adaptive"
    assert deep_budget["cognitive_pipeline"] == "adaptive"
    assert adaptive_budget["shared_metric_contract"] == deep_budget[
        "shared_metric_contract"
    ]
    assert adaptive_budget["shared_lifecycle_contract"] == deep_budget[
        "shared_lifecycle_contract"
    ]
    assert deep_budget["max_reasoning_depth"] > adaptive_budget[
        "max_reasoning_depth"
    ]
