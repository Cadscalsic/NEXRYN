def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ParadigmConflictResolver:

    CONFLICT_THRESHOLD = 0.34
    CRITICAL_THRESHOLD = 0.68
    MAX_MODE_CONTRIBUTION = 0.16
    MAX_REJECTION_CONTRIBUTION = 0.24

    def resolve(self, context=None):
        context = context or {}

        selection = context.get("meta_selection_report", {})
        dominant = selection.get(
            "dominant_reasoning",
            context.get("dominant_reasoning", "unknown"),
        )

        alternatives = selection.get(
            "candidate_modes",
            context.get("reasoning_modes", []),
        )

        if not isinstance(alternatives, list):
            alternatives = []

        alternatives = sorted(set(str(item) for item in alternatives if item))

        identity_blocks = (
            context.get("ontological_boundary_report", {})
            .get("identity_boundary", {})
            .get("blocked_identity_fusions", 0)
        )

        rejected = context.get(
            "concept_fusion_report",
            {},
        ).get(
            "rejected_count",
            0,
        )

        try:
            identity_blocks = max(0, int(identity_blocks or 0))
        except Exception:
            identity_blocks = 0

        try:
            rejected = max(0, int(rejected or 0))
        except Exception:
            rejected = 0

        pressure = _clamp(
            context.get("existential_pressure_report", {})
            .get("managed_pressure", 0.0)
        )

        mode_contribution = min(
            len(alternatives) * 0.08,
            self.MAX_MODE_CONTRIBUTION,
        )

        rejection_contribution = min(
            rejected * 0.08,
            self.MAX_REJECTION_CONTRIBUTION,
        )

        identity_contribution = min(
            identity_blocks * 0.12,
            0.24,
        )

        conflict_score = _clamp(
            mode_contribution
            + identity_contribution
            + rejection_contribution
            + pressure * 0.24
        )

        fast_mode = (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
        )

        conflict_active = conflict_score >= self.CONFLICT_THRESHOLD
        critical = conflict_score >= self.CRITICAL_THRESHOLD

        if fast_mode and conflict_active and not critical:
            return {
                "system": "paradigm_conflict_resolver",
                "dominant_paradigm": dominant,
                "candidate_paradigms": alternatives,
                "paradigm_conflict_score": conflict_score,
                "conflict_state": "conflict_deferred_in_fast_mode",
                "resolution_actions": [],
                "deferred_actions": [
                    "isolate_conflicting_paradigm_claims",
                    "route_hybrid_reasoning_through_attestation",
                ],
                "critical": False,
                "reason": "noncritical_paradigm_conflict_deferred_after_success",
                "score_breakdown": {
                    "mode_contribution": round(mode_contribution, 4),
                    "identity_contribution": round(identity_contribution, 4),
                    "rejection_contribution": round(rejection_contribution, 4),
                    "pressure_contribution": round(pressure * 0.24, 4),
                },
            }

        if critical:
            actions = [
                "isolate_conflicting_paradigm_claims",
                "route_hybrid_reasoning_through_attestation",
                "block_conflicting_paradigm_commit",
            ]
            state = "paradigm_conflict_critical"

        elif conflict_active:
            actions = [
                "isolate_conflicting_paradigm_claims",
                "route_hybrid_reasoning_through_attestation",
            ]
            state = "paradigm_conflict_resolution_active"

        else:
            actions = []
            state = "paradigm_conflict_low"

        return {
            "system": "paradigm_conflict_resolver",
            "dominant_paradigm": dominant,
            "candidate_paradigms": alternatives,
            "paradigm_conflict_score": conflict_score,
            "resolution_actions": actions,
            "conflict_state": state,
            "critical": critical,
            "conflict_active": conflict_active,
            "score_breakdown": {
                "mode_contribution": round(mode_contribution, 4),
                "identity_contribution": round(identity_contribution, 4),
                "rejection_contribution": round(rejection_contribution, 4),
                "pressure_contribution": round(pressure * 0.24, 4),
            },
        }