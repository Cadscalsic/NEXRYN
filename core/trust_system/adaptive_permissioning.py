# ============================================
# NEXRYN ADAPTIVE PERMISSIONING
# ============================================

from datetime import datetime

from core.trust_system.cognitive_reputation import (
    CognitiveReputation,
)

from core.trust_system.graduated_commitment import (
    GraduatedCommitment,
)

from core.trust_system.trust_score import (
    TrustScore,
)


class AdaptivePermissioning:

    def __init__(self):

        self.trust_score = TrustScore()
        self.cognitive_reputation = CognitiveReputation()
        self.graduated_commitment = GraduatedCommitment()
        self.permission_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        trust_report = self.trust_score.compute(
            context,
        )

        reputation_report = self.cognitive_reputation.evaluate(
            context,
            trust_report,
        )

        commitment_report = self.graduated_commitment.build_plan(
            trust_report,
            reputation_report,
        )

        commit_probability = commitment_report.get(
            "commit_probability",
            0.0,
        )

        report = {
            "system":
            "adaptive_permissioning",

            "trust_model":
            "continuous_trust_spectrum",

            "binary_trust_replaced":
            True,

            "trust_score":
            trust_report,

            "cognitive_reputation":
            reputation_report,

            "graduated_commitment":
            commitment_report,

            "commit_probability":
            commit_probability,

            "permission_state":
            (
                "evolve_safely"
                if commit_probability >= 0.40
                else "observe_and_rehearse"
                if commit_probability >= 0.18
                else "hold_in_shadow"
            ),

            "anti_paralysis_controls":
            [
                "preserve_nonzero_shadow_learning",
                "prefer_rehearsal_over_hard_denial",
                "graduate_permissions_with_evidence",
                "decay_defensive_pressure_after_stability",
            ],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.permission_history.append(
            report,
        )

        self.permission_history = (
            self.permission_history[-128:]
        )

        return report


adaptive_permissioning = (
    AdaptivePermissioning()
)
