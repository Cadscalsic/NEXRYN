from core.knowledge.contradiction_review_policy import (
    MEDIUM_RISK_REVIEW_LIMIT as POLICY_MEDIUM_RISK_REVIEW_LIMIT,
    SOFT_REVIEW_ZONE,
    classify_contradiction_review,
)


class FinalCommitDecisionEngine:
    """Resolves promotion and review without auto-revoking locked truths."""

    LOW_RISK_REVIEW_LIMIT = 0.10 + SOFT_REVIEW_ZONE
    MEDIUM_RISK_REVIEW_LIMIT = POLICY_MEDIUM_RISK_REVIEW_LIMIT
    DEFAULT_REVOCATION_GRACE_PERIOD = 2

    REVOCATION_REVIEW_GATES = {
        "contradiction_below_limit",
    }

    def __init__(self, revocation_grace_period=None):
        self.revocation_grace_period = max(
            int(
                self.DEFAULT_REVOCATION_GRACE_PERIOD
                if revocation_grace_period is None
                else revocation_grace_period
            ),
            0,
        )
        self._low_risk_review_streaks = {}

    def _revocation_severity(self, contradiction_score):
        return classify_contradiction_review(
            contradiction_score,
        )["contradiction_review_severity"]

    def evaluate(
        self,
        gates,
        stable_truth_authority_locked=False,
        contradiction_score=None,
        truth_key=None,
    ):
        failed_gates = [
            name
            for name, passed in gates.items()
            if not passed
        ]
        effective_failed_gates = [
            name
            for name in failed_gates
            if not (
                stable_truth_authority_locked
                and name == "belief_is_truth_candidate"
            )
        ]
        revocation_review_reasons = [
            name
            for name in effective_failed_gates
            if name in self.REVOCATION_REVIEW_GATES
        ]
        revocation_severity = (
            self._revocation_severity(contradiction_score)
            if revocation_review_reasons
            else None
        )
        grace_period_key = str(truth_key) if truth_key is not None else None
        revocation_grace_period_active = False
        low_risk_review_streak = 0
        only_low_risk_contradiction_failed = (
            stable_truth_authority_locked
            and revocation_severity == "LOW_RISK_REVIEW"
            and effective_failed_gates == ["contradiction_below_limit"]
        )
        if grace_period_key is not None:
            if only_low_risk_contradiction_failed:
                low_risk_review_streak = (
                    self._low_risk_review_streaks.get(grace_period_key, 0)
                    + 1
                )
                self._low_risk_review_streaks[grace_period_key] = (
                    low_risk_review_streak
                )
                revocation_grace_period_active = (
                    low_risk_review_streak <= self.revocation_grace_period
                )
            else:
                self._low_risk_review_streaks.pop(grace_period_key, None)

        if stable_truth_authority_locked:
            if revocation_grace_period_active:
                decision = "TRUTH_COMMITTED"
                final_commit_state = "LOCKED_TRUTH_PRESERVED"
            elif revocation_review_reasons:
                decision = "TRUTH_REVOCATION_REVIEW_REQUIRED"
                final_commit_state = "LOCKED_TRUTH_REVIEW_REQUIRED"
            elif effective_failed_gates:
                decision = "TRUTH_COMMIT_HELD"
                final_commit_state = "LOCKED_TRUTH_TEMPORARY_HOLD"
            else:
                decision = "TRUTH_COMMITTED"
                final_commit_state = "LOCKED_TRUTH_PRESERVED"
        elif effective_failed_gates:
            decision = "REMAIN_BELIEF"
            final_commit_state = "FINAL_COMMIT_BLOCKED"
        else:
            decision = "TRUTH_COMMITTED"
            final_commit_state = "FINAL_COMMIT_APPROVED"

        return {
            "system": "final_commit_decision_engine",
            "decision": decision,
            "final_commit_state": final_commit_state,
            "stable_truth_authority_locked": stable_truth_authority_locked,
            "failed_gates": failed_gates,
            "effective_failed_gates": effective_failed_gates,
            "revocation_review_reasons": revocation_review_reasons,
            "revocation_severity": revocation_severity,
            "revocation_grace_period": self.revocation_grace_period,
            "revocation_grace_period_active":
            revocation_grace_period_active,
            "low_risk_review_streak": low_risk_review_streak,
            "preventive_review_observation":
            revocation_grace_period_active,
            "revocation_severity_thresholds": {
                "low_risk_review_maximum":
                self.LOW_RISK_REVIEW_LIMIT,
                "medium_risk_review_maximum":
                self.MEDIUM_RISK_REVIEW_LIMIT,
            },
            "forbid_automatic_truth_revocation":
            stable_truth_authority_locked,
            "manual_review_required":
            decision == "TRUTH_REVOCATION_REVIEW_REQUIRED",
        }


__all__ = [
    "FinalCommitDecisionEngine",
]
