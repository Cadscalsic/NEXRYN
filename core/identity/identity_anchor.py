# ============================================
# NEXRYN IDENTITY ANCHOR
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


class IdentityAnchor:

    def __init__(self):

        self.protected_cognition_laws = [
            "preserve_identity_continuity",
            "preserve_causal_traceability",
            "preserve_semantic_separation",
            "preserve_architectural_invariants",
        ]

        self.architectural_invariants = [
            "sandbox_before_core_commit",
            "verify_before_mutation",
            "rehearse_before_graduation",
            "rollback_on_identity_drift",
        ]

        self.core_principles = [
            "identity_over_novelty",
            "causality_over_shortcut",
            "bounded_entropy_over_unchecked_expansion",
            "constructive_evolution_over_random_mutation",
        ]

    def _continuity_signal(self, context):

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        return _clamp(
            rehearsal.get(
                "identity_forecaster",
                {},
            ).get(
                "identity_continuity",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            ),
        )

    def anchor(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        identity_core = context.get(
            "identity_core_report",
            {},
        )

        drift = _clamp(
            identity_core.get(
                "identity_drift",
                context.get(
                    "identity_drift",
                    0.0,
                ),
            ),
        )

        continuity = self._continuity_signal(
            context,
        )

        anchor_strength = _clamp(
            1.0
            -
            drift * 0.52
            +
            continuity * 0.28
        )

        active_anchors = [
            "core_principles",
            "causal_history",
            "architectural_invariants",
            "protected_cognition_laws",
        ]

        if continuity < 0.62:

            active_anchors.extend([
                "identity_spine_reinforcement",
                "mutation_identity_gate",
            ])

        return {
            "system":
            "identity_anchor",

            "anchor_strength":
            anchor_strength,

            "identity_drift":
            drift,

            "identity_continuity":
            continuity,

            "anchor_state":
            (
                "reinforced"
                if continuity < 0.62
                or drift >= 0.40
                else "watched"
                if continuity < 0.76
                or drift >= 0.24
                else "stable"
            ),

            "active_anchors":
            active_anchors,

            "core_principles":
            self.core_principles,

            "architectural_invariants":
            self.architectural_invariants,

            "protected_cognition_laws":
            self.protected_cognition_laws,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
