from runtime.world.soft_execution_gate import soft_execution_gate


class WorldModelGate:
    """Requires explicit world-model authorization before transformation."""

    def evaluate(self, anticipation_report=None):
        anticipation_report = (
            anticipation_report
            if isinstance(anticipation_report, dict)
            else {}
        )
        execution_accepted = (
            anticipation_report.get("execution_accepted", False) is True
        )
        soft_execution_report = soft_execution_gate.evaluate(
            anticipation_report
        )
        sandbox_execution_accepted = (
            soft_execution_report["soft_execution_authorized"]
        )
        gate_state = (
            "EXECUTION_AUTHORIZED"
            if execution_accepted
            else "EXECUTION_ROUTED_TO_SANDBOX"
            if sandbox_execution_accepted
            else "EXECUTION_ABORTED_WORLD_MODEL_REJECTION"
        )
        return {
            "system": "world_model_gate",
            "execution_authorized": execution_accepted,
            "execution_aborted": not execution_accepted,
            "sandbox_execution_authorized": sandbox_execution_accepted,
            "soft_execution_report": soft_execution_report,
            "gate_state": gate_state,
            "acceptance_state":
            anticipation_report.get("acceptance_state"),
            "explicit_execution_acceptance_required": True,
            "sandbox_execution_isolated": sandbox_execution_accepted,
        }


world_model_gate = WorldModelGate()


__all__ = [
    "WorldModelGate",
    "world_model_gate",
]
