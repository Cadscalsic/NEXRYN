def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class CrossParadigmAlignment:

    def align(self, conflict, coexistence, translation):

        alignment = _clamp(
            (1.0 - conflict.get("paradigm_conflict_score", 0.0)) * 0.38
            +
            coexistence.get("semantic_coexistence", 0.0) * 0.38
            +
            (1.0 - translation.get("translation_load", 0.0)) * 0.24
        )

        return {
            "system": "cross_paradigm_alignment",
            "alignment_score": alignment,
            "alignment_actions": [
                "align_paradigms_through_shared_invariants",
                "keep_unaligned_outputs_sandboxed",
            ]
            if alignment < 0.58
            else [],
            "alignment_state": (
                "cross_paradigm_alignment_required"
                if alignment < 0.58
                else "cross_paradigm_alignment_stable"
            ),
        }
