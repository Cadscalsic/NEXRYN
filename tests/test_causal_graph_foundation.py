from core.belief_engine import EpistemicCognitionLayer
from core.causal_graph import CausalGraph


def strong_evidence(concept, source, task_id):
    return {
        "concept": concept,
        "source": source,
        "support_score": 1.0,
        "contradiction_score": 0.0,
        "reliability": 1.0,
        "semantic_consistency": 1.0,
        "causal_alignment": 1.0,
        "metadata": {
            "task_id": task_id,
        },
    }


def test_causal_graph_builds_observation_concept_truth_spine():
    graph = CausalGraph()
    graph.build_causal_spine(
        "shape_preservation",
        observations=[
            strong_evidence("shape_preservation", "task_a", "task_a"),
            strong_evidence("shape_preservation", "task_b", "task_b"),
            strong_evidence("shape_preservation", "task_c", "task_c"),
        ],
        confidence=1.0,
    )

    alignment = graph.compute_causal_alignment("shape_preservation")
    validation = graph.validate_causal_graph()
    explanation = graph.explain_truth("shape_preservation")

    assert alignment["alignment_score"] == 1.0
    assert alignment["alignment_ready"] is True
    assert validation["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
    assert explanation["why"][0] == "observed in 3 tasks"
    assert "concept:shape_preservation" in explanation["explanation_path"]
    assert "truth:shape_preservation" in explanation["explanation_path"]


def test_causal_graph_alignment_uses_scene_graph_evidence():
    graph = CausalGraph()
    spine = graph.build_causal_spine(
        "color_preservation",
        observations=[
            strong_evidence("color_preservation", "task_a", "task_a"),
        ],
        confidence=0.72,
        context={
            "task_id": "scene_task",
            "input_grid": [[0, 1, 0]],
            "output_grid": [[0, 1, 0, 1]],
        },
    )

    alignment = graph.compute_causal_alignment("color_preservation")

    assert spine["scene_evidence"]
    assert alignment["components"]["dependency_coherence"] >= 0.80
    assert alignment["alignment_score"] > 0.80


def test_causal_graph_validation_reports_orphans_and_unsupported_truths():
    graph = CausalGraph()
    graph.add_node(
        node_id="concept:orphan",
        node_type="CONCEPT",
        concept_name="orphan",
        confidence=0.4,
    )
    graph.add_node(
        node_id="truth:unsupported",
        node_type="TRUTH",
        concept_name="unsupported is stable",
        confidence=0.4,
    )

    report = graph.validate_causal_graph()

    assert report["validation_state"] == "CAUSAL_GRAPH_VALIDATION_REQUIRED"
    assert "concept:orphan" in report["orphan_concepts"]
    assert "truth:unsupported" in report["unsupported_truths"]


def test_epistemic_runtime_exposes_causal_explanation_for_truth_candidate():
    layer = EpistemicCognitionLayer()
    context = {
        "epistemic_hypotheses": [{
            "concept": "shape_preservation",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("shape_preservation", "task_a", "task_a"),
            strong_evidence("shape_preservation", "task_b", "task_b"),
            strong_evidence("shape_preservation", "task_c", "task_c"),
        ],
    }

    report = layer.run_cycle(context)
    evaluation = report["evaluations"][0]
    candidate = evaluation["truth_candidate"]

    assert candidate["causal_graph_alignment"]["alignment_ready"] is True
    assert candidate["causal_explanation"]["why"]
    assert "causal_graph_alignment" in [
        metric["metric"]
        for metric in candidate["metrics"]
    ]
    assert report["causal_graph_validator"][
        "causal_graph_foundation_validation"
    ]["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
