class ExecutionIntegrityGuard:
    """Restricts transformation execution to the authorized plan."""

    def primitives_from_plan(self, execution_plan=None):
        execution_plan = (
            execution_plan
            if isinstance(execution_plan, dict)
            else {}
        )
        nodes = sorted(
            execution_plan.get("nodes", []),
            key=lambda node: node.get("execution_index", 0),
        )
        return [
            {
                "primitive": node.get("operation"),
                "parameters": node.get("parameters", {}),
            }
            for node in nodes
            if node.get("operation")
        ]

    def evaluate(
        self,
        execution_plan=None,
        execution_trace=None,
        execution_authorized=True,
    ):
        execution_trace = (
            execution_trace
            if isinstance(execution_trace, list)
            else []
        )
        planned_ops = [
            primitive["primitive"]
            for primitive in self.primitives_from_plan(execution_plan)
        ]
        executed_ops = [
            event.get("primitive", event.get("operation"))
            for event in execution_trace
            if event.get("status") in ["completed", "executed"]
        ]
        comparison_required = execution_authorized is True
        integrity_preserved = (
            not comparison_required
            or executed_ops == planned_ops
        )
        return {
            "system": "execution_integrity_guard",
            "planned_ops": planned_ops,
            "executed_ops": executed_ops,
            "integrity_preserved": integrity_preserved,
            "comparison_required": comparison_required,
            "integrity_state": (
                "EXECUTION_INTEGRITY_PRESERVED"
                if comparison_required and integrity_preserved
                else "EXECUTION_INTEGRITY_VIOLATION"
                if comparison_required
                else "EXECUTION_NOT_AUTHORIZED"
            ),
            "unauthorized_ops": [
                operation
                for index, operation in enumerate(executed_ops)
                if (
                    index >= len(planned_ops)
                    or operation != planned_ops[index]
                )
            ],
            "execution_drift_detected":
            comparison_required and not integrity_preserved,
            "executed_ops_must_equal_planned_ops": True,
        }


execution_integrity_guard = ExecutionIntegrityGuard()


__all__ = [
    "ExecutionIntegrityGuard",
    "execution_integrity_guard",
]
