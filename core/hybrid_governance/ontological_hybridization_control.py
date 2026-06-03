def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class OntologicalHybridizationControl:

    def control(self, context, identity):

        ontology_fatigue = _clamp(
            context.get("ontological_boundary_report", {})
            .get("existential_fatigue", {})
            .get("ontological_fatigue", 0.0)
        )
        hybrid_balance = _clamp(identity.get("hybrid_identity_balance", 0.5))

        hybridization_risk = _clamp(
            ontology_fatigue * 0.44
            +
            (1.0 - hybrid_balance) * 0.56
        )

        return {
            "system": "ontological_hybridization_control",
            "hybridization_risk": hybridization_risk,
            "hybridization_actions": [
                "sandbox_ontological_hybrids",
                "require_invariant_boundary_attestation",
            ]
            if hybridization_risk >= 0.36
            else [],
            "hybridization_state": (
                "ontological_hybridization_guarded"
                if hybridization_risk >= 0.36
                else "ontological_hybridization_allowed"
            ),
        }
