from core.epistemic_models import clamp


class ConceptScopeOptimizer:
    def optimize(self, concept, boundary_conditions=None):
        boundaries = []
        for item in boundary_conditions or []:
            holds = clamp(item.get("holds_average", 0.0))
            fails = clamp(item.get("fails_average", 0.0))
            midpoint = clamp((holds + fails) / 2.0)
            margin = clamp(abs(holds - fails) / 4.0, 0.02, 0.20)
            boundaries.append({
                "metric": item["metric"],
                "direction": item.get("direction"),
                "holds_average": holds,
                "fails_average": fails,
                "decision_midpoint": midpoint,
                "probe_lower_bound": clamp(midpoint - margin),
                "probe_upper_bound": clamp(midpoint + margin),
                "separation": clamp(abs(holds - fails)),
            })

        return {
            "system": "concept_scope_optimizer",
            "phase": "6.96",
            "concept": concept,
            "scope_state": (
                "PROVISIONAL_CONCEPT_SCOPE_REFINED"
                if boundaries
                else "AWAITING_BOUNDARY_CONDITIONS"
            ),
            "provisional_scope": {
                "boundary_targets": boundaries,
                "law_state": "PROVISIONAL_BOUNDARY_HYPOTHESIS",
            },
            "boundary_target_count": len(boundaries),
            "scope_is_provisional_until_matched_replication": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "ConceptScopeOptimizer",
]
