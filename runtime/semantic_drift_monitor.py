from core.epistemic_models import clamp


class SemanticDriftMonitor:
    def __init__(self):
        self.history = []
        self.historical_pressure = 0.0

    def measure(self, context):
        context = context if isinstance(context, dict) else {}
        homeostasis = (
            context.get("cognitive_homeostasis_report", {})
            .get("semantic_drift_detection", {})
        )
        explicit = context.get("semantic_drift")
        instantaneous = clamp(
            explicit
            if explicit is not None
            else homeostasis.get("semantic_drift", 0.0)
        )
        previous_pressure = self.historical_pressure
        self.historical_pressure = clamp(
            instantaneous * 0.72
            + previous_pressure * 0.28
        )
        saturation_count = sum(
            item.get("instantaneous_drift", 0.0) >= 0.94
            for item in self.history[-3:]
        ) + int(instantaneous >= 0.94)
        report = {
            "system": "semantic_drift_monitor",
            "instantaneous_drift": instantaneous,
            "historical_pressure": self.historical_pressure,
            "previous_historical_pressure": previous_pressure,
            "effective_drift": max(
                instantaneous,
                self.historical_pressure,
            ),
            "source": (
                "explicit_runtime_signal"
                if explicit is not None
                else homeostasis.get(
                    "measurement_source",
                    "cognitive_homeostasis",
                )
            ),
            "saturation_state": (
                "possible_metric_saturation"
                if saturation_count >= 3
                else "high_drift_signal"
                if instantaneous >= 0.78
                else "unsaturated"
            ),
            "saturated_cycles": saturation_count,
        }
        self.history.append(report)
        self.history = self.history[-128:]
        return report


semantic_drift_monitor = SemanticDriftMonitor()
