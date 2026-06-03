class ReflectiveRecursionLimits:

    def enforce(self, reflection, growth, pruning):

        limit_required = (
            reflection.get("reflection_load", 0.0) >= 0.34
            or growth.get("recursive_growth_pressure", 0.0) >= 0.38
            or pruning.get("semantic_pruning_need", 0.0) >= 0.50
        )

        return {
            "system": "reflective_recursion_limits",
            "limit_required": limit_required,
            "limit_actions": [
                "set_reflective_recursion_budget",
                "block_unbounded_recursive_self_reference",
            ]
            if limit_required
            else [],
            "limits_state": (
                "reflective_recursion_limits_active"
                if limit_required
                else "reflective_recursion_limits_standby"
            ),
        }
