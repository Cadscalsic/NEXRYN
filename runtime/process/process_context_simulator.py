"""Simulation for graph-derived process contexts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.process.process_simulator import ProcessSimulator


class ProcessContextSimulator:
    """Execute candidate process chains and score graph-flow reproduction."""

    system_name = "process_context_simulator"

    def __init__(self, simulator: ProcessSimulator | None = None):
        self.simulator = simulator or ProcessSimulator()

    def simulate(
        self,
        process_context: Mapping[str, Any],
        input_grid=None,
        output_grid=None,
    ) -> dict[str, Any]:
        base = self.simulator.simulate(
            process_context,
            input_grid=input_grid,
            output_grid=output_grid,
        )
        transition_count = len(process_context.get("transition_sequence", []) or [])
        state_count = process_context.get("state_count") or (
            2 + len(process_context.get("intermediate_states", []) or [])
        )
        graph_fit = round(
            min(1.0, transition_count / max(int(state_count) - 1, 1)),
            4,
        )
        process_reproduction_score = round(
            max(
                float(base.get("simulation_accuracy", 0.0) or 0.0),
                graph_fit * 0.55
                + float(base.get("dependency_consistency", 0.0) or 0.0) * 0.45,
            ),
            4,
        )
        return {
            **base,
            "system": self.system_name,
            "graph_flow_fit": graph_fit,
            "process_reproduction_score": process_reproduction_score,
            "candidate_process_executed": transition_count > 0,
            "timestamp": str(datetime.utcnow()),
        }


process_context_simulator = ProcessContextSimulator()


__all__ = ["ProcessContextSimulator", "process_context_simulator"]
