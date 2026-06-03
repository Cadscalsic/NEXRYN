from core.epistemic_models import clamp


class CausalBoundaryMapper:
    METRICS = (
        "causal_alignment",
        "contradiction_score",
        "confidence",
    )

    def _average(self, records, metric):
        if not records:
            return 0.0
        return clamp(
            sum(item[metric] for item in records) / len(records)
        )

    def _condition_patterns(self, records):
        patterns = {}
        for record in records:
            for key, value in record.get("conditions", {}).items():
                value_key = str(value)
                patterns.setdefault(key, {})
                patterns[key][value_key] = (
                    patterns[key].get(value_key, 0) + 1
                )
        return [
            {
                "condition": key,
                "observed_values": values,
            }
            for key, values in sorted(patterns.items())
        ]

    def map(self, concept, supported_observations, counterexamples):
        metric_boundaries = []
        if supported_observations and counterexamples:
            for metric in self.METRICS:
                holds_average = self._average(
                    supported_observations,
                    metric,
                )
                fails_average = self._average(counterexamples, metric)
                metric_boundaries.append({
                    "metric": metric,
                    "holds_average": holds_average,
                    "fails_average": fails_average,
                    "separation": clamp(abs(holds_average - fails_average)),
                    "direction": (
                        "higher_when_holds"
                        if holds_average > fails_average
                        else "lower_when_holds"
                        if holds_average < fails_average
                        else "no_observed_separation"
                    ),
                })

        return {
            "system": "causal_boundary_mapper",
            "phase": "6.93",
            "concept": concept,
            "holds_when": self._condition_patterns(supported_observations),
            "fails_when": self._condition_patterns(counterexamples),
            "boundary_conditions": metric_boundaries,
            "boundary_state": (
                "MIXED_OUTCOMES_REQUIRE_BOUNDARY_REFINEMENT"
                if supported_observations and counterexamples
                else "SUPPORTED_REGION_ONLY"
                if supported_observations
                else "COUNTEREXAMPLE_REGION_ONLY"
                if counterexamples
                else "AWAITING_CAUSAL_OBSERVATIONS"
            ),
            "boundary_inference_requires_more_execution_evidence": (
                len(supported_observations) + len(counterexamples) < 5
            ),
        }


__all__ = [
    "CausalBoundaryMapper",
]
