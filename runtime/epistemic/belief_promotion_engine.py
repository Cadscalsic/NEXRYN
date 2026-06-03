from core.epistemic_models import BeliefState
from runtime.promotion_diagnostics_engine import PromotionDiagnosticsEngine


class BeliefPromotionEngine:
    def __init__(self):
        self.diagnostics_engine = PromotionDiagnosticsEngine()

    def evaluate(self, aggregate, trials, calibrated_confidence):
        diagnostics = self.diagnostics_engine.evaluate(
            aggregate,
            trials,
            calibrated_confidence,
        )
        trial_counts = diagnostics["trial_counts"]
        passed_trials = trial_counts["passed"]
        failed_trials = trial_counts["failed"]
        gates = {
            item["gate_name"]: item["passed"]
            for item in diagnostics["gates"]
        }

        if failed_trials or not gates["contradiction_below_rejection"]:
            state = BeliefState.REJECTED
        elif (
            gates["validated_trials"]
            and gates["validated_confidence"]
            and gates["validated_consistency"]
            and gates["truth_candidate_strength"]
            and gates["truth_candidate_confidence"]
            and gates["truth_candidate_contradiction"]
            and gates["truth_candidate_causality"]
        ):
            state = BeliefState.TRUTH_CANDIDATE
        elif (
            gates["validated_trials"]
            and gates["validated_confidence"]
            and gates["validated_consistency"]
        ):
            state = BeliefState.VALIDATED
        elif (
            gates["supported_trial"]
            and gates["supported_confidence"]
        ):
            state = BeliefState.SUPPORTED
        elif gates["has_evidence"]:
            state = BeliefState.PROBATION
        else:
            state = BeliefState.CANDIDATE

        for item in diagnostics["gates"]:
            item["current_state"] = state.value
        diagnostics["current_state"] = state.value

        return {
            "system": "belief_promotion_engine",
            "state": state,
            "promotion_state": state.value,
            "passed_trials": passed_trials,
            "failed_trials": failed_trials,
            "inconclusive_trials": trial_counts["inconclusive"],
            "total_trials": trial_counts["total"],
            "gates": gates,
            "gate_diagnostics": diagnostics["gates"],
            "promotion_diagnostics": diagnostics,
            "blocked_gates": [
                name
                for name, passed in gates.items()
                if not passed
            ],
            "promotion_path": [
                "CANDIDATE",
                "PROBATION",
                "SUPPORTED",
                "VALIDATED",
                "TRUTH_CANDIDATE",
                "TRUTH_COMMITTED",
            ],
            "confidence_is_not_truth": True,
        }


__all__ = [
    "BeliefPromotionEngine",
]
