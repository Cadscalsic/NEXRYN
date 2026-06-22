from runtime.knowledge_optimization import (
    MAX_EVIDENCE_COLLECTION_TIME,
    adaptive_validation_thresholds,
    concept_commit_engine,
    confidence_plateau_detector,
    contradiction_ledger,
    evidence_saturation_controller,
    knowledge_optimization_reporter,
    knowledge_reuse_gate,
    memory_confidence_tracker,
    strategy_reuse_engine,
)


def test_contradictions_are_proportional_not_binary():
    evidence = [
        {"evidence_type": "exact_success", "confidence": 1.0}
        for _ in range(99)
    ] + [{"evidence_type": "contradiction", "confidence": 1.0}]

    report = contradiction_ledger.evaluate("stable_shape", evidence)

    assert report["contradiction_score"] == 0.01
    assert report["binary_contradiction"] is False


def test_evidence_saturation_has_hard_limits_and_decision():
    report = evidence_saturation_controller.evaluate({
        "support_confidence": 0.60,
        "contradiction_score": 0.05,
        "evidence_collection_time": 12.0,
        "validation_cycles": 99,
    })

    assert report["decision"] in {"PROMOTE", "QUARANTINE", "REJECT"}
    assert report["evidence_saturated"] is True
    assert report["continue_collecting"] is False
    assert report["collection_time"] == MAX_EVIDENCE_COLLECTION_TIME


def test_stable_saturated_concepts_are_promoted():
    report = concept_commit_engine.evaluate(
        "color_transfer",
        {
            "support_score": 0.91,
            "support_threshold": 0.85,
            "contradiction_score": 0.02,
            "contradiction_limit": 0.10,
            "evidence_saturated": True,
        },
        governance_approved=True,
    )

    assert report["promoted"] is True
    assert report["concept_state"] == "LOCKED_CONCEPT"
    assert report["shutdown_runtime"] is True


def test_strategy_reuse_precedes_reasoning():
    report = strategy_reuse_engine.find_reusable_strategy(
        {},
        {
            "strategy_memory": [
                {
                    "shape_similarity": 0.97,
                    "context_similarity": 0.93,
                    "strategy_confidence": 0.90,
                }
            ]
        },
    )
    gate = knowledge_reuse_gate.evaluate({}, report)

    assert report["reuse_existing_strategy"] is True
    assert report["selected_source"] == "strategy_memory"
    assert gate["skip_deep_reasoning"] is True
    assert gate["preferred_order"][0] == "knowledge_reuse_gate"


def test_confidence_plateau_terminates_cognition():
    report = confidence_plateau_detector.evaluate(
        [0.90, 0.905, 0.907, 0.908, 0.909, 0.9095]
    )

    assert report["plateau_detected"] is True
    assert report["terminate_reason"] == "COGNITIVE_PLATEAU"
    assert "shutdown_runtime" in report["actions"]


def test_adaptive_thresholds_and_memory_confidence():
    thresholds = adaptive_validation_thresholds.evaluate({
        "concept_stability": 0.99,
        "contradiction_score": 0.01,
    })
    confidence = memory_confidence_tracker.update(
        "strategy:shape-copy",
        reuse_succeeded=True,
    )
    report = knowledge_optimization_reporter.build_report({
        "strategy_hits": 1,
        "strategy_misses": 0,
        "contradiction_score": 0.01,
        "thinking_avoidance_rate": 1.0,
    })

    assert thresholds["required_evidence"] < 10
    assert confidence["strategy_confidence"] > 0.5
    assert report["KNOWLEDGE_OPTIMIZATION_REPORT"]["reuse_rate"] == 1.0
