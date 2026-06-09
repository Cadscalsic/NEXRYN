"""Placement reasoning for localized prediction mismatches."""

from __future__ import annotations

from typing import Any, Mapping

from core.scene_graph import GraphReasoner
from core.world_model.counterfactual_simulator import CounterfactualSimulator
from core.world_model.position_predictor import PositionPredictor


class PlacementReasoner:
    """Coordinate graph evidence, position prediction, and counterfactual repair."""

    def __init__(
        self,
        position_predictor: PositionPredictor | None = None,
        counterfactual_simulator: CounterfactualSimulator | None = None,
        graph_reasoner: GraphReasoner | None = None,
    ) -> None:
        self.position_predictor = position_predictor or PositionPredictor()
        self.counterfactual_simulator = (
            counterfactual_simulator
            or CounterfactualSimulator(self.position_predictor)
        )
        self.graph_reasoner = graph_reasoner or GraphReasoner()

    def reason(
        self,
        input_grid: Any,
        expected_grid: Any | None = None,
        predicted_grid: Any | None = None,
        operation: str = "duplicate_object",
        position_rule: Mapping[str, Any] | None = None,
        search_radius: int = 1,
    ) -> dict[str, Any]:
        graph_report = (
            self.graph_reasoner.reason_about_placement(
                input_grid,
                expected_grid,
                operation=operation,
            )
            if expected_grid is not None
            else {"dependency_evidence": [], "placement_rules": []}
        )
        rule = dict(position_rule or {})
        if not rule and expected_grid is not None:
            learned = self.position_predictor.learn_position_rule(
                input_grid,
                expected_grid,
            )
            rule = self._rule_from_graph_or_predictor(graph_report, learned)

        prediction = (
            {
                "system": "position_predictor",
                "prediction_state": "EXTERNAL_PREDICTION_PROVIDED",
                "predicted_grid": predicted_grid,
            }
            if predicted_grid is not None
            else self.position_predictor.predict_positioned_operation(
                input_grid,
                operation,
                rule,
            )
        )
        if expected_grid is None:
            return {
                "system": "placement_reasoner",
                "placement_state": "PLACEMENT_EXPECTATION_MISSING",
                "position_rule": rule,
                "position_prediction": prediction,
                "graph_reasoning": graph_report,
                "dependency_evidence": graph_report.get("dependency_evidence", []),
            }

        mismatch = self.position_predictor.diagnose_position_mismatch(
            prediction.get("predicted_grid", []),
            expected_grid,
        )
        counterfactuals = (
            self.counterfactual_simulator.simulate_position_counterfactuals(
                input_grid,
                expected_grid,
                operation=operation,
                position_rule=rule,
                search_radius=search_radius,
            )
            if mismatch.get("failure_type") == "localized_prediction_mismatch"
            else {
                "system": "counterfactual_simulator",
                "localized_prediction_mismatch_resolved": True,
                "recommended_position_rule": rule,
            }
        )
        placement_state = self._placement_state(mismatch, counterfactuals)
        recommended_rule = (
            counterfactuals.get("recommended_position_rule")
            if placement_state == "PLACEMENT_REPAIRED_BY_COUNTERFACTUAL"
            else rule
        )
        return {
            "system": "placement_reasoner",
            "placement_state": placement_state,
            "operation": operation,
            "position_rule": rule,
            "recommended_position_rule": recommended_rule or {},
            "position_prediction": prediction,
            "position_mismatch": mismatch,
            "position_counterfactuals": counterfactuals,
            "graph_reasoning": graph_report,
            "dependency_evidence": graph_report.get("dependency_evidence", []),
        }

    def repair_localized_mismatch(
        self,
        input_grid: Any,
        expected_grid: Any,
        operation: str = "duplicate_object",
        position_rule: Mapping[str, Any] | None = None,
        search_radius: int = 1,
    ) -> dict[str, Any]:
        return self.reason(
            input_grid,
            expected_grid,
            operation=operation,
            position_rule=position_rule,
            search_radius=search_radius,
        )

    def _rule_from_graph_or_predictor(
        self,
        graph_report: Mapping[str, Any],
        learned: Mapping[str, Any],
    ) -> dict[str, Any]:
        graph_rules = graph_report.get("placement_rules", [])
        if graph_rules:
            rule = dict(graph_rules[0])
            rule["rule_state"] = "POSITION_RULE_LEARNED_FROM_SCENE_GRAPH"
            return rule
        return dict(learned)

    def _placement_state(
        self,
        mismatch: Mapping[str, Any],
        counterfactuals: Mapping[str, Any],
    ) -> str:
        if mismatch.get("failure_type") != "localized_prediction_mismatch":
            return "PLACEMENT_ALIGNED"
        if counterfactuals.get("localized_prediction_mismatch_resolved"):
            return "PLACEMENT_REPAIRED_BY_COUNTERFACTUAL"
        return "PLACEMENT_RULE_UNCERTAIN"


__all__ = [
    "PlacementReasoner",
]
