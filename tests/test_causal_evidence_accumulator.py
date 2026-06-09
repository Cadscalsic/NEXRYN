from core.causal import CausalEvidenceAccumulator, CausalGraph


def test_causal_evidence_accumulator_updates_confidence_history():
    accumulator = CausalEvidenceAccumulator()

    first = accumulator.observe(
        "duplication",
        "object_count_increase",
        confidence=0.8,
        task_id="task_a",
        context="duplication",
    )
    second = accumulator.observe(
        "duplication",
        "object_count_increase",
        confidence=0.9,
        task_id="task_b",
        context="duplication",
    )

    assert second["support_count"] == 2
    assert second["confidence"] >= first["confidence"]
    assert len(second["confidence_history"]) == 2


def test_causal_evidence_accumulator_applies_records_to_graph():
    accumulator = CausalEvidenceAccumulator()
    accumulator.observe(
        "duplication",
        "object_count_increase",
        confidence=0.9,
        task_id="task_a",
    )
    graph = accumulator.apply_to_graph(CausalGraph())

    assert "duplication" in graph.nodes
    assert graph.outgoing("duplication")[0].target == "object_count_increase"
