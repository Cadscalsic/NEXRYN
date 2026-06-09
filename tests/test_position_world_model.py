from core.causal.dependency_graph import DependencyGraphEngine
from core.world_model import (
    CausalWorldSimulator,
    CounterfactualSimulator,
    PositionPredictor,
)


def test_dependency_graph_facade_uses_existing_engine(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    for _ in range(5):
        engine.ingest_dependencies([
            {
                "source": "duplication",
                "target": "relation:right_of",
                "confidence": 0.95,
                "supported": True,
                "transfer_success": True,
            },
        ])
    report = engine.validate_dependency_coherence(
        "duplication",
        required_dependencies=["relation:right_of"],
    )

    assert report["dependency_coherence"] >= 0.80
    assert report["missing_dependencies"] == []


def test_position_predictor_learns_duplicate_placement():
    predictor = PositionPredictor()
    rule = predictor.learn_position_rule(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )
    prediction = predictor.predict_positioned_operation(
        [[1, 0, 0]],
        "duplicate_object",
        rule,
    )

    assert rule["rule_state"] == "POSITION_RULE_LEARNED"
    assert rule["placement_vector"]["delta_col"] == 2.0
    assert prediction["predicted_grid"] == [[1, 0, 1]]


def test_position_predictor_diagnoses_localized_mismatch():
    predictor = PositionPredictor()
    mismatch = predictor.diagnose_position_mismatch(
        [[1, 1, 0]],
        [[1, 0, 1]],
    )

    assert mismatch["failure_type"] == "localized_prediction_mismatch"
    assert mismatch["difference_count"] == 2


def test_counterfactual_simulator_finds_better_position():
    simulator = CounterfactualSimulator()
    report = simulator.simulate_position_counterfactuals(
        [[1, 0, 0]],
        [[1, 0, 1]],
        position_rule={
            "operation": "duplicate_object",
            "source_object": "obj_1",
            "placement_vector": {"delta_row": 0, "delta_col": 1},
        },
        search_radius=1,
    )

    assert report["localized_prediction_mismatch_resolved"] is True
    assert report["best_counterfactual"]["placement_vector"]["delta_col"] == 2
    assert report["best_counterfactual"]["difference_count"] == 0


def test_world_model_reports_position_prediction_mismatch():
    report = CausalWorldSimulator().run_cycle({
        "input_grid": [[1, 0, 0]],
        "expected_grid": [[1, 0, 1]],
        "operation": "duplicate_object",
        "position_rule": {
            "operation": "duplicate_object",
            "source_object": "obj_1",
            "placement_vector": {"delta_row": 0, "delta_col": 1},
            "confidence": 0.72,
        },
    })

    position = report["position_prediction"]

    assert position["position_model_active"] is True
    assert position["position_prediction"]["predicted_grid"] == [[1, 1, 0]]
    assert position["position_mismatch"]["failure_type"] == (
        "localized_prediction_mismatch"
    )
    assert report["recommended_intervention"] == "adjust_position_rule"
