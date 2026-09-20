def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class OntologicalHybridizationControl:

    RISK_THRESHOLD = 0.36
    CRITICAL_THRESHOLD = 0.65

    def control(
        self,
        context=None,
        identity=None,
    ):

        context = context or {}
        identity = identity or {}

        ontology_fatigue = _clamp(
            context.get(
                "ontological_boundary_report",
                {},
            )
            .get(
                "existential_fatigue",
                {},
            )
            .get(
                "ontological_fatigue",
                0.0,
            )
        )

        hybrid_balance = _clamp(
            identity.get(
                "hybrid_identity_balance",
                0.5,
            )
        )

        hybridization_risk = _clamp(
            ontology_fatigue * 0.44
            +
            (1.0 - hybrid_balance) * 0.56
        )

        fast_mode = (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
        )

        critical = (
            hybridization_risk >= self.CRITICAL_THRESHOLD
        )

        guarded = (
            hybridization_risk >= self.RISK_THRESHOLD
        )

        if fast_mode and guarded and not critical:

            return {
                "system":
                "ontological_hybridization_control",

                "hybridization_risk":
                hybridization_risk,

                "hybridization_state":
                "deferred_fast_mode",

                "hybridization_actions":
                [],

                "deferred_actions": [
                    "sandbox_ontological_hybrids",
                    "require_invariant_boundary_attestation",
                ],

                "critical":
                False,

                "reason":
                "noncritical_ontological_review_deferred",
            }

        if critical:

            actions = [
                "sandbox_ontological_hybrids",
                "require_invariant_boundary_attestation",
                "block_hybrid_commit",
            ]

            state = (
                "ontological_hybridization_critical"
            )

        elif guarded:

            actions = [
                "sandbox_ontological_hybrids",
                "require_invariant_boundary_attestation",
            ]

            state = (
                "ontological_hybridization_guarded"
            )

        else:

            actions = []

            state = (
                "ontological_hybridization_allowed"
            )

        return {
            "system":
            "ontological_hybridization_control",

            "hybridization_risk":
            hybridization_risk,

            "hybridization_actions":
            actions,

            "hybridization_state":
            state,

            "critical":
            critical,

            "guarded":
            guarded,

            "ontology_fatigue":
            ontology_fatigue,

            "hybrid_identity_balance":
            hybrid_balance,
        }