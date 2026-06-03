# ============================================
# NEXRYN GRADUATED COMMITMENT
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class GraduatedCommitment:

    def build_plan(self, trust_report, reputation_report):

        trust_score = _clamp(
            trust_report.get(
                "trust_score",
                0.0,
            ),
        )

        reputation = _clamp(
            reputation_report.get(
                "average_reputation",
                0.0,
            ),
        )

        risk_pressure = _clamp(
            trust_report.get(
                "risk_pressure",
                1.0,
            ),
        )

        commit_probability = _clamp(
            trust_score * 0.50
            +
            reputation * 0.30
            +
            (1.0 - risk_pressure) * 0.20
        )

        commitment_tier = (
            "core_commit"
            if commit_probability >= 0.78
            else "canary_commit"
            if commit_probability >= 0.58
            else "probationary_commit"
            if commit_probability >= 0.40
            else "sandbox_observation"
            if commit_probability >= 0.18
            else "shadow_reject"
        )

        permission_ceiling = {
            "core_commit":
            "write_core_memory",

            "canary_commit":
            "limited_core_write",

            "probationary_commit":
            "temporary_semantic_write",

            "sandbox_observation":
            "read_only_with_shadow_execution",

            "shadow_reject":
            "observe_only",
        }.get(
            commitment_tier,
            "observe_only",
        )

        return {
            "system":
            "graduated_commitment",

            "commit_probability":
            commit_probability,

            "commitment_tier":
            commitment_tier,

            "permission_ceiling":
            permission_ceiling,

            "graduation_path":
            [
                "shadow_observation",
                "sandbox_observation",
                "probationary_commit",
                "canary_commit",
                "core_commit",
            ],

            "promotion_conditions":
            [
                "stable_identity_continuity",
                "bounded_entropy_delta",
                "repeated_semantic_consistency",
                "positive_causal_rehearsal",
            ],

            "rollback_conditions":
            [
                "identity_drift_spike",
                "semantic_collapse_signal",
                "unbounded_entropy_delta",
                "reputation_decay",
            ],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
