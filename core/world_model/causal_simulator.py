# ============================================
# NEXRYN CAUSAL WORLD SIMULATOR
# ============================================

from datetime import datetime

from core.world_model.counterfactual_engine import (
    CausalCounterfactualEngine,
)

from core.world_model.future_projection import (
    FutureProjectionEngine,
)

from core.world_model.position_predictor import (
    PositionPredictor,
)

from core.world_model.counterfactual_simulator import (
    CounterfactualSimulator,
)

from core.world_model.placement_reasoner import (
    PlacementReasoner,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class CausalWorldSimulator:

    def __init__(self):

        self.future_projection = FutureProjectionEngine()
        self.counterfactual_engine = CausalCounterfactualEngine()
        self.position_predictor = PositionPredictor()
        self.position_counterfactual_simulator = CounterfactualSimulator(
            self.position_predictor,
        )
        self.placement_reasoner = PlacementReasoner(
            self.position_predictor,
            self.position_counterfactual_simulator,
        )
        self.simulation_history = []

    def estimate_collapse(self, future_report, counterfactual_report):

        terminal_entropy = future_report.get(
            "terminal_entropy",
            0.0,
        )

        best_entropy = counterfactual_report.get(
            "best_outcome",
            {},
        ).get(
            "projected_entropy",
            terminal_entropy,
        )

        return {
            "collapse_probability":
            _clamp(
                terminal_entropy * 0.65
                +
                best_entropy * 0.35
            ),

            "collapse_state":
            (
                "imminent"
                if terminal_entropy >= 0.86
                else "critical"
                if terminal_entropy >= 0.74
                else "contained"
            ),
        }

    def predict_identity_risk(self, context, counterfactual_report):

        current_identity = context.get(
            "identity_anchor_core_report",
            {},
        ).get(
            "identity_drift_before",
            context.get(
                "identity_drift",
                0.0,
            ),
        )

        best_identity = counterfactual_report.get(
            "best_outcome",
            {},
        ).get(
            "projected_identity_risk",
            current_identity,
        )

        return {
            "current_identity_risk":
            _clamp(
                current_identity,
            ),

            "predicted_identity_risk":
            _clamp(
                best_identity,
            ),

            "identity_risk_state":
            (
                "rising"
                if best_identity > current_identity + 0.04
                else "stabilized"
                if best_identity <= current_identity
                else "watched"
            ),
        }

    def simulate_future(self, context, horizon=3):

        return self.future_projection.simulate_future(
            context,
            horizon=horizon,
        )

    def compare_outcomes(self, context):

        return self.counterfactual_engine.compare_outcomes(
            context,
        )

    def simulate_positioning(self, context):

        input_grid = context.get("input_grid")
        expected_grid = context.get(
            "expected_grid",
            context.get("output_grid"),
        )
        operation = context.get(
            "operation",
            context.get("primitive", "duplicate_object"),
        )

        if input_grid is None or expected_grid is None:
            return {
                "system": "position_predictor",
                "position_model_active": False,
                "reason": "input_or_expected_grid_missing",
            }

        position_rule = context.get("position_rule")
        placement_reasoning = self.placement_reasoner.reason(
            input_grid,
            expected_grid,
            operation=operation,
            position_rule=position_rule
            if isinstance(position_rule, dict)
            else None,
            search_radius=context.get("position_search_radius", 1),
        )
        return {
            "system": "position_predictor",
            "position_model_active": True,
            "position_rule": placement_reasoning.get("position_rule", {}),
            "recommended_position_rule": placement_reasoning.get(
                "recommended_position_rule",
                {},
            ),
            "position_prediction": placement_reasoning.get(
                "position_prediction",
                {},
            ),
            "position_mismatch": placement_reasoning.get(
                "position_mismatch",
                {},
            ),
            "position_counterfactuals": placement_reasoning.get(
                "position_counterfactuals",
                {},
            ),
            "placement_reasoning": placement_reasoning,
            "dependency_evidence": placement_reasoning.get(
                "dependency_evidence",
                [],
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        future_report = self.simulate_future(
            context,
            horizon=3,
        )

        counterfactual_report = self.compare_outcomes(
            context,
        )

        collapse_report = self.estimate_collapse(
            future_report,
            counterfactual_report,
        )

        identity_report = self.predict_identity_risk(
            context,
            counterfactual_report,
        )

        position_report = self.simulate_positioning(
            context,
        )

        report = {
            "system":
            "causal_world_simulator",

            "causal_physics":
            "cognitive_cause_effect_model",

            "future_projection":
            future_report,

            "counterfactuals":
            counterfactual_report,

            "collapse_estimate":
            collapse_report,

            "identity_risk_prediction":
            identity_report,

            "position_prediction":
            position_report,

            "recommended_intervention":
            (
                "adjust_position_rule"
                if position_report.get(
                    "position_mismatch",
                    {},
                ).get("failure_type")
                == "localized_prediction_mismatch"
                else counterfactual_report.get(
                    "best_outcome",
                    {},
                ).get(
                    "scenario",
                    "observe",
                )
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.simulation_history.append(
            report,
        )

        self.simulation_history = (
            self.simulation_history[-64:]
        )

        return report


causal_world_simulator = (
    CausalWorldSimulator()
)
