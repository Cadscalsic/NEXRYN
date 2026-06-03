def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticConstitutionalLaw:

    def rule(
        self,
        identity,
        semantic,
        merge,
        conflict,
        overlap,
        contradiction,
    ):

        constitutional_score = _clamp(
            identity.get("identity_compatibility", 0.0) * 0.22
            +
            semantic.get("semantic_admissibility", 0.0) * 0.20
            +
            merge.get("merge_legality", 0.0) * 0.20
            +
            (1.0 - conflict.get("conflict_intensity", 1.0)) * 0.14
            +
            overlap.get("layered_identity_overlap", 0.0) * 0.12
            +
            (1.0 - contradiction.get("contradiction_risk", 1.0)) * 0.12
        )

        actions = []
        if constitutional_score < 0.58:
            actions.extend([
                "enforce_semantic_constitutional_law",
                "require_constitutional_clearance",
            ])
        if merge.get("merge_legality", 1.0) < 0.50:
            actions.append("deny_merge_constitutional_status")
        if semantic.get("semantic_admissibility", 1.0) < 0.50:
            actions.append("deny_semantic_admissibility")

        return {
            "system": "semantic_constitutional_law",
            "constitutional_score": constitutional_score,
            "constitutional_actions": actions,
            "constitutional_state": (
                "constitutional_law_enforced"
                if actions
                else "constitutional_law_clear"
            ),
        }
