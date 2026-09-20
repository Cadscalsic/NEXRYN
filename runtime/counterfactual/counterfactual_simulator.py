"""Sandbox counterfactual simulation."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Mapping

from runtime.arena.candidate_simulator import CandidateSimulator


class CounterfactualSimulator:
    system_name = "counterfactual_simulator"

    def __init__(self, candidate_simulator: CandidateSimulator | None = None):
        self.candidate_simulator = candidate_simulator or CandidateSimulator()

    def simulate(
        self,
        counterfactual: Mapping[str, Any],
        input_grid: Any,
        target_grid: Any,
        original_simulation: Mapping[str, Any] | None = None,
        budget: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        budget = budget if isinstance(budget, Mapping) else {}
        start = perf_counter()
        candidate = {
            "candidate_id": counterfactual.get("counterfactual_id"),
            "program": counterfactual.get("counterfactual_program", {"step_count": 0, "steps": []}),
        }
        sim = self.candidate_simulator.simulate(candidate, input_grid=input_grid, target_grid=target_grid)
        duration = perf_counter() - start
        original_diff = int((original_simulation or {}).get("difference_count", sim.get("difference_count", 0)) or 0)
        residual_reduction = max(0, original_diff - int(sim.get("difference_count", 0) or 0))
        return {
            "system": self.system_name,
            "counterfactual_id": counterfactual.get("counterfactual_id"),
            "simulation_success": sim.get("simulation_success"),
            "predicted_output": sim.get("predicted_output"),
            "execution_trace": sim.get("execution_trace"),
            "prediction_accuracy": sim.get("prediction_accuracy"),
            "difference_count": sim.get("difference_count"),
            "residual_reduction": residual_reduction,
            "structural_score": sim.get("structural_score"),
            "color_score": sim.get("color_score"),
            "object_score": sim.get("object_score"),
            "topology_score": sim.get("topology_score"),
            "identity_score": 0.0 if counterfactual.get("metadata", {}).get("identity_violation") else 1.0,
            "unsupported_steps": sim.get("unsupported_steps", []),
            "simulation_errors": sim.get("simulation_errors", []),
            "simulation_duration": round(duration, 6),
            "budget_exceeded": duration > float(budget.get("max_simulation_time_seconds", 1.0) or 1.0),
        }


counterfactual_simulator = CounterfactualSimulator()

__all__ = ["CounterfactualSimulator", "counterfactual_simulator"]
