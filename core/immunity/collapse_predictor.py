# ============================================
# NEXRYN COLLAPSE PREDICTOR
# ============================================

from datetime import datetime


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


class CollapsePredictor:

    def predict(self, context):

        world = context.get(
            "causal_world_simulation_report",
            {},
        )

        world_collapse = world.get(
            "collapse_estimate",
            {},
        ).get(
            "collapse_probability",
            0.0,
        )

        thermodynamics = context.get(
            "cognitive_thermodynamics_report",
            {},
        )

        heat = thermodynamics.get(
            "semantic_heat_dissipation",
            {},
        ).get(
            "semantic_heat_after",
            context.get(
                "runtime_entropy",
                0.0,
            ),
        )

        recursion = context.get(
            "recursive_pressure_governor_report",
            {},
        )

        raw_depth = recursion.get(
            "raw_reasoning_depth",
            context.get(
                "raw_reasoning_depth",
                0,
            ),
        )

        recursion_risk = _clamp(
            raw_depth / 16,
        )

        collapse_risk = _clamp(
            world_collapse * 0.45
            +
            heat * 0.35
            +
            recursion_risk * 0.20
        )

        return {
            "system":
            "collapse_predictor",

            "collapse_risk":
            collapse_risk,

            "runaway_recursion_risk":
            recursion_risk,

            "collapse_state":
            (
                "imminent"
                if collapse_risk >= 0.82
                else "critical"
                if collapse_risk >= 0.68
                else "contained"
            ),

            "preventive_actions":
            (
                [
                    "halt_runaway_recursion",
                    "force_semantic_cooling",
                    "disable_unstable_fusion",
                ]
                if collapse_risk >= 0.68
                else [
                    "monitor_collapse_risk",
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
