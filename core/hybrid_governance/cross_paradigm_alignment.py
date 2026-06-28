def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class CrossParadigmAlignment:

    ALIGNMENT_THRESHOLD = 0.58
    CRITICAL_THRESHOLD = 0.42

    def align(self, conflict=None, coexistence=None, translation=None, runtime_context=None):
        conflict = conflict or {}
        coexistence = coexistence or {}
        translation = translation or {}
        runtime_context = runtime_context or {}

        conflict_score = _clamp(conflict.get("paradigm_conflict_score", 0.0))
        semantic_coexistence = _clamp(coexistence.get("semantic_coexistence", 0.0))
        translation_load = _clamp(translation.get("translation_load", 0.0))

        alignment = _clamp(
            (1.0 - conflict_score) * 0.38
            + semantic_coexistence * 0.38
            + (1.0 - translation_load) * 0.24
        )

        fast_mode = (
            runtime_context.get("episode_completed") is True
            or runtime_context.get("shutdown_mode") == "fast"
            or runtime_context.get("post_success_mode") == "fast"
        )

        critical = alignment < self.CRITICAL_THRESHOLD
        needs_alignment = alignment < self.ALIGNMENT_THRESHOLD

        if fast_mode and needs_alignment and not critical:
            return {
                "system": "cross_paradigm_alignment",
                "alignment_score": alignment,
                "alignment_state": "alignment_deferred_in_fast_mode",
                "alignment_actions": [],
                "deferred_actions": [
                    "align_paradigms_through_shared_invariants",
                    "keep_unaligned_outputs_sandboxed",
                ],
                "critical": False,
                "reason": "noncritical_alignment_deferred_after_success",
            }

        if critical:
            actions = [
                "align_paradigms_through_shared_invariants",
                "keep_unaligned_outputs_sandboxed",
                "block_paradigm_commit_until_alignment",
            ]
            state = "cross_paradigm_alignment_critical"

        elif needs_alignment:
            actions = [
                "align_paradigms_through_shared_invariants",
                "keep_unaligned_outputs_sandboxed",
            ]
            state = "cross_paradigm_alignment_required"

        else:
            actions = []
            state = "cross_paradigm_alignment_stable"

        return {
            "system": "cross_paradigm_alignment",
            "alignment_score": alignment,
            "alignment_state": state,
            "alignment_actions": actions,
            "critical": critical,
            "needs_alignment": needs_alignment,
            "scores": {
                "paradigm_conflict_score": conflict_score,
                "semantic_coexistence": semantic_coexistence,
                "translation_load": translation_load,
            },
        }