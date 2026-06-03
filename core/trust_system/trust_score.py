# ============================================
# NEXRYN TRUST SCORE
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


class TrustScore:

    def compute(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        firewall = context.get(
            "semantic_firewall_report",
            {},
        )

        sandbox = firewall.get(
            "concept_sandboxing",
            context.get(
                "concept_sandboxing_report",
                {},
            ),
        )

        ontology = firewall.get(
            "ontology_intrusion_detection",
            {},
        )

        identity = firewall.get(
            "identity_attack_detection",
            {},
        )

        firewall_pressure = _clamp(
            firewall.get(
                "firewall_pressure",
                context.get(
                    "firewall_pressure",
                    0.0,
                ),
            ),
        )

        sandbox_pressure = _clamp(
            max([
                item.get(
                    "sandbox_pressure",
                    0.0,
                )
                for item in sandbox.get(
                    "sandboxed_events",
                    [],
                )
            ] or [
                context.get(
                    "sandbox_pressure",
                    0.0,
                ),
            ])
        )

        merge_risk = _clamp(
            ontology.get(
                "average_merge_risk",
                context.get(
                    "average_merge_risk",
                    0.0,
                ),
            ),
        )

        identity_risk = _clamp(
            identity.get(
                "attack_score",
                context.get(
                    "identity_attack_score",
                    0.0,
                ),
            ),
        )

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                ontology.get(
                    "runtime_entropy",
                    0.0,
                ),
            ),
        )

        rehearsal_evidence = context.get(
            "causal_rehearsal_report",
            {},
        ).get(
            "evidence_exports",
            {},
        )

        legitimacy_evidence = context.get(
            "semantic_legitimacy_report",
            {},
        ).get(
            "evidence_exports",
            {},
        )

        positive_evidence = _clamp(
            context.get(
                "semantic_attestation_score",
                legitimacy_evidence.get(
                    "semantic_attestation_score",
                    0.0,
                ),
            )
            +
            context.get(
                "identity_attestation_score",
                rehearsal_evidence.get(
                    "identity_attestation_score",
                    0.0,
                ),
            )
            +
            context.get(
                "causal_attestation_score",
                max(
                    rehearsal_evidence.get(
                        "causal_attestation_score",
                        0.0,
                    ),
                    legitimacy_evidence.get(
                        "causal_attestation_score",
                        0.0,
                    ),
                ),
            )
        )

        legitimacy_score = _clamp(
            context.get(
                "semantic_legitimacy_report",
                {},
            ).get(
                "semantic_legitimacy_score",
                0.0,
            ),
        )

        risk_pressure = _clamp(
            firewall_pressure * 0.30
            +
            sandbox_pressure * 0.25
            +
            merge_risk * 0.20
            +
            identity_risk * 0.15
            +
            entropy * 0.10
        )

        trust_score = _clamp(
            0.62
            -
            risk_pressure * 0.55
            +
            positive_evidence * 0.18
            +
            legitimacy_score * 0.12
        )

        return {
            "system":
            "trust_score",

            "trust_score":
            trust_score,

            "risk_pressure":
            risk_pressure,

            "firewall_pressure":
            firewall_pressure,

            "sandbox_pressure":
            sandbox_pressure,

            "average_merge_risk":
            merge_risk,

            "identity_risk":
            identity_risk,

            "runtime_entropy":
            entropy,

            "positive_evidence":
            positive_evidence,

            "semantic_legitimacy_score":
            legitimacy_score,

            "trust_band":
            (
                "trusted"
                if trust_score >= 0.72
                else "probationary"
                if trust_score >= 0.46
                else "sandboxed"
                if trust_score >= 0.24
                else "untrusted"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
