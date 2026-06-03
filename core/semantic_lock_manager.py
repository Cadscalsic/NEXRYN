# ============================================
# NEXRYN SEMANTIC LOCK MANAGER
# ============================================

from core.constitutional_core import ConstitutionalCore
from core.contradiction_engine import ContradictionEngine
from core.epistemic_certainty_engine import EpistemicCertaintyEngine
from runtime.meta_cognition.meta_cognitive_diversity_engine import (
    MetaCognitiveDiversityEngine,
)


class SemanticLockManager:

    CONSTITUTIONAL_SEMANTIC_LOCKS = [
        "identity_spine",
        "causal_framework",
        "semantic_registry",
        "epistemic_core",
    ]

    def __init__(self):

        self.constitutional_core = ConstitutionalCore()
        self.epistemic_certainty_engine = EpistemicCertaintyEngine()
        self.contradiction_engine = ContradictionEngine()
        self.diversity_engine = MetaCognitiveDiversityEngine()

    def manage(self, context):

        constitutional_report = self.constitutional_core.evaluate(
            context,
        )

        certainty_report = self.epistemic_certainty_engine.assess(
            context,
        )

        contradiction_report = self.contradiction_engine.analyze(
            context,
        )

        diversity_report = self.diversity_engine.assess(
            context,
        )

        lock_reasons = []
        if constitutional_report.get(
            "constitutional_state",
        ) == "core_locked":
            lock_reasons.append(
                "constitutional_core_violation",
            )

        if contradiction_report.get(
            "contradiction_severity",
            0.0,
        ) >= 0.36:
            lock_reasons.append(
                "contradiction_escalation",
            )

        if certainty_report.get(
            "epistemic_state",
        ) == "epistemic_understanding_gap":
            lock_reasons.append(
                "epistemic_certainty_insufficient",
            )

        # If diversity indicates high lock-in risk, escalate to policy blocking
        lock_in_risk = diversity_report.get("lock_in_risk", 0.0)
        if lock_in_risk >= 0.55:
            lock_reasons.append("contradiction_escalation")
            lock_reasons.append("policy_block_required")

        policy_blocked = lock_in_risk >= 0.55

        system_notifications = []
        if policy_blocked:
            system_notifications.append(
                {
                    "level": "warning",
                    "message": "High adaptive lock-in detected: blocking policy changes until diversity restored.",
                }
            )

        semantic_lock_state = (
            "semantic_lock_engaged"
            if lock_reasons
            else "semantic_lock_standby"
        )

        return {
            "system":
            "semantic_lock_manager",

            "constitutional_semantic_locks":
            list(
                self.CONSTITUTIONAL_SEMANTIC_LOCKS,
            ),

            "constitutional_report":
            constitutional_report,

            "epistemic_certainty_report":
            certainty_report,

            "contradiction_engine_report":
            contradiction_report,

            "diversity_report":
            diversity_report,

            "policy_blocked":
            policy_blocked,

            "system_notifications":
            system_notifications,

            "lock_reasons":
            lock_reasons,

            "semantic_lock_state":
            semantic_lock_state,
        }
