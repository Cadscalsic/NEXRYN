from core.epistemic_models import TrialResult


class TrialResolutionEngine:
    PASS_GATES = [
        ("evidence_count", ">=", 1, "collect_epistemic_evidence"),
        (
            "evidence_strength",
            ">=",
            0.68,
            "collect_execution_validation_evidence",
        ),
        (
            "contradiction_score",
            "<",
            0.18,
            "resolve_or_explain_contradictory_evidence",
        ),
        (
            "semantic_consistency",
            ">=",
            0.64,
            "validate_semantic_consistency",
        ),
        (
            "causal_alignment",
            ">=",
            0.60,
            "collect_causal_attestation_evidence",
        ),
    ]

    def _gate(self, aggregate, name, comparator, required, action):
        current = getattr(aggregate, name)
        passed = (
            current >= required
            if comparator == ">="
            else current < required
        )
        gap = (
            max(required - current, 0.0)
            if comparator == ">="
            else max(current - required, 0.0)
        )
        return {
            "gate_name": name,
            "current_value": current,
            "threshold": {
                "comparator": comparator,
                "required": required,
            },
            "gap": round(gap, 4),
            "passed": passed,
            "status": "PASSED" if passed else "FAILED",
            "required_action": None if passed else action,
        }

    def resolve(self, aggregate, previous_trials=None):
        previous_trials = list(previous_trials or [])
        pass_gates = [
            self._gate(aggregate, *specification)
            for specification in self.PASS_GATES
        ]
        unresolved_gates = [
            item
            for item in pass_gates
            if not item["passed"]
        ]
        rejection_gates = {
            "contradiction_reaches_rejection_threshold":
            aggregate.contradiction_score >= 0.55,
            "support_below_rejection_threshold": (
                aggregate.evidence_count >= 2
                and aggregate.support_score < 0.30
            ),
        }
        rejection_reasons = [
            name
            for name, triggered in rejection_gates.items()
            if triggered
        ]
        result = (
            TrialResult.FAILED
            if rejection_reasons
            else TrialResult.PASSED
            if not unresolved_gates
            else TrialResult.INCONCLUSIVE
        )
        prior_inconclusive_streak = 0
        for trial in reversed(previous_trials):
            if trial.trial_result != TrialResult.INCONCLUSIVE:
                break
            prior_inconclusive_streak += 1
        inconclusive_streak = (
            prior_inconclusive_streak + 1
            if result == TrialResult.INCONCLUSIVE
            else 0
        )
        ranked_unresolved_gates = sorted(
            unresolved_gates,
            key=lambda item: item["gap"],
        )

        return {
            "system": "trial_resolution_engine",
            "concept": aggregate.concept,
            "trial_result": result.value,
            "resolution_reason": (
                "rejection_gate_triggered"
                if result == TrialResult.FAILED
                else "all_pass_gates_satisfied"
                if result == TrialResult.PASSED
                else "pass_gates_unresolved"
            ),
            "pass_gates": pass_gates,
            "rejection_gates": rejection_gates,
            "rejection_reasons": rejection_reasons,
            "ranked_unresolved_gates": ranked_unresolved_gates,
            "dominant_unresolved_gate": (
                ranked_unresolved_gates[-1]
                if ranked_unresolved_gates
                else None
            ),
            "inconclusive_streak": inconclusive_streak,
            "stalled_inconclusive_pattern": inconclusive_streak >= 3,
            "near_resolution_threshold": (
                result == TrialResult.INCONCLUSIVE
                and bool(ranked_unresolved_gates)
                and ranked_unresolved_gates[-1]["gap"] <= 0.02
            ),
            "required_actions": [
                item["required_action"]
                for item in ranked_unresolved_gates
                if item["required_action"]
            ],
        }


__all__ = [
    "TrialResolutionEngine",
]
