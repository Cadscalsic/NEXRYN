def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticPruningController:

    def control(self, context, growth):

        memory_pressure = _clamp(context.get("memory_pressure_score", 0.0))
        compression = _clamp(
            context.get("memory_compression_report", {}).get("compression_ratio", 1.0)
        )
        growth_pressure = _clamp(growth.get("recursive_growth_pressure", 0.0))

        pruning_need = _clamp(
            memory_pressure * 0.42
            +
            (1.0 - compression) * 0.22
            +
            growth_pressure * 0.36
        )

        return {
            "system": "semantic_pruning_controller",
            "memory_pressure": memory_pressure,
            "compression_ratio": compression,
            "semantic_pruning_need": pruning_need,
            "pruning_actions": [
                "prune_low_value_recursive_context",
                "preserve_identity_and_topology_anchors",
            ]
            if pruning_need >= 0.34
            else [],
            "pruning_state": (
                "semantic_pruning_control_active"
                if pruning_need >= 0.34
                else "semantic_pruning_standby"
            ),
        }
