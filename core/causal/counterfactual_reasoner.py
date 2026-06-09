from core.epistemic_models import clamp


class CounterfactualReasoner:
    """Lightweight context perturbation checks for concept robustness."""

    COUNTERFACTUALS = [
        ("color_behavior", "color_reassigned"),
        ("object_count", "doubled"),
        ("topology_behavior", "split"),
        ("identity_behavior", "identity_split"),
        ("symmetry_behavior", "disappears"),
    ]

    def _invalidated_by(self, concept, key, value):
        if concept == "color_preservation":
            return key == "color_behavior" and value == "color_reassigned"
        if concept == "object_identity_preservation":
            return (
                key == "identity_behavior" and value == "identity_split"
            ) or (key == "object_count" and value in {"changed", "doubled"})
        if concept == "identity_preservation":
            return key == "identity_behavior" and value == "identity_split"
        if concept == "topology_preservation":
            return key == "topology_behavior" and value == "split"
        return False

    def test(self, concept, context=None):
        context = dict(context or {})
        tests = []
        invalidations = 0

        for key, value in self.COUNTERFACTUALS:
            alternative = dict(context)
            alternative[key] = value
            invalidates = self._invalidated_by(concept, key, value)
            invalidations += 1 if invalidates else 0
            tests.append({
                "question": f"what happens if {key} becomes {value}?",
                "changed_factor": key,
                "counterfactual_value": value,
                "concept_remains_valid": not invalidates,
                "effect": "invalidates" if invalidates else "preserves",
            })

        robustness = clamp(1.0 - (invalidations / max(len(tests), 1)))
        if robustness >= 0.80:
            status = "SURVIVES"
        elif robustness >= 0.50:
            status = "PARTIAL"
        else:
            status = "FAILS"
        return {
            "system": "counterfactual_reasoner",
            "concept": concept,
            "tests": tests,
            "counterfactual_robustness": robustness,
            "counterfactual_status": status,
            "truth_survival": status,
            "truth_degradation": clamp(1.0 - robustness),
            "dependency_collapse": invalidations > 1,
            "causal_resilience": robustness,
            "requires_counterfactual_testing": robustness < 0.75,
            "invalidating_factors": [
                item["changed_factor"]
                for item in tests
                if not item["concept_remains_valid"]
            ],
        }


__all__ = [
    "CounterfactualReasoner",
]
