def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class MergeLegalityEngine:

    def assess(self, context, identity, semantic):

        fusion_report = context.get("concept_fusion_report", {})
        rejected_count = fusion_report.get("rejected_count", 0)
        accepted_count = fusion_report.get("accepted_count", 0)
        total = max(1, rejected_count + accepted_count)
        rejection_pressure = _clamp(rejected_count / total)

        judicial_legality = (
            context.get("judicial_cognition_report", {})
            .get("semantic_legality", {})
            .get("semantic_legality", 0.56)
        )

        fusion_stability = (
            context.get("hybrid_governance_report", {})
            .get("cognitive_fusion_stability", {})
            .get("fusion_stability", 0.58)
        )

        merge_legality = _clamp(
            judicial_legality * 0.30
            +
            fusion_stability * 0.25
            +
            identity.get("identity_compatibility", 0.5) * 0.25
            +
            semantic.get("semantic_admissibility", 0.5) * 0.20
            -
            rejection_pressure * 0.16
        )

        actions = []
        if merge_legality < 0.56:
            actions.extend([
                "block_illegal_identity_merge",
                "require_merge_constitutional_hearing",
            ])
        if rejection_pressure > 0.42:
            actions.append("reduce_merge_submission_pressure")

        return {
            "system": "merge_legality_engine",
            "merge_legality": merge_legality,
            "rejection_pressure": rejection_pressure,
            "merge_legality_actions": actions,
            "merge_legality_state": (
                "merge_legality_restricted"
                if actions
                else "merge_legality_clear"
            ),
        }
