class MatchedBoundaryRunner:
    def __init__(self):
        self._sequence = 0

    def _pair(self, concept, target):
        self._sequence += 1
        metric = target["metric"]
        pair_id = f"boundary_pair:{concept}:{metric}:{self._sequence}"
        return [
            {
                "pair_id": pair_id,
                "probe_side": "below_boundary",
                "target_metric": metric,
                "target_value": target["probe_lower_bound"],
            },
            {
                "pair_id": pair_id,
                "probe_side": "above_boundary",
                "target_metric": metric,
                "target_value": target["probe_upper_bound"],
            },
        ]

    def plan(self, concept, concept_scope):
        targets = concept_scope.get(
            "provisional_scope",
            {},
        ).get("boundary_targets", [])
        probes = [
            probe
            for target in targets
            for probe in self._pair(concept, target)
        ]
        return {
            "system": "matched_boundary_runner",
            "phase": "6.96",
            "concept": concept,
            "runner_state": (
                "MATCHED_BOUNDARY_PROBES_PLANNED"
                if probes
                else "AWAITING_REFINED_CONCEPT_SCOPE"
            ),
            "matched_boundary_probes": probes,
            "matched_pair_count": len(probes) // 2,
            "probe_results_must_be_measured": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "MatchedBoundaryRunner",
]
