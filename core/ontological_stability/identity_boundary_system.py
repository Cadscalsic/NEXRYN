def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(value, maximum),
        ),
        4,
    )


class IdentityBoundarySystem:

    def inspect_analysis(self, analysis):

        failure = analysis.get(
            "failure_explanation",
            {},
        )

        stability = analysis.get(
            "merge_stability",
            {},
        )

        coherence = failure.get(
            "coherence",
            {},
        )

        hidden = failure.get(
            "hidden_conflicts",
            {},
        )

        conflict_layers = set(
            hidden.get(
                "conflict_layers",
                [],
            )
            +
            failure.get(
                "failure_reasons",
                [],
            )
        )

        semantic_similarity = _clamp(
            stability.get(
                "semantic_similarity",
                coherence.get(
                    "identity_coherence",
                    0.0,
                ),
            )
        )

        existential_compatible = not bool(
            conflict_layers
            &
            {
                "unsafe_merge_memory",
                "causal_role_conflict",
                "structural_signature_conflict",
                "hidden_causal_conflict",
                "hidden_structural_conflict",
            }
        )

        return {
            "geometric_similarity":
            semantic_similarity,

            "structural_compatible":
            "structural_signature_conflict"
            not in conflict_layers,

            "causal_compatible":
            "causal_role_conflict"
            not in conflict_layers,

            "symbolic_compatible":
            "archetype_misalignment"
            not in conflict_layers,

            "existential_compatible":
            existential_compatible,

            "identity_fusion_allowed":
            existential_compatible
            and stability.get(
                "merge_state",
            )
            != "unstable_merge",
        }

    def run_cycle(self, context):

        analyses = context.get(
            "identity_reasoner_report",
            {},
        ).get(
            "identity_analyses",
            [],
        )

        inspections = [
            self.inspect_analysis(
                analysis,
            )
            for analysis in analyses
        ]

        blocked = [
            item
            for item in inspections
            if not item.get(
                "identity_fusion_allowed",
            )
        ]

        return {
            "system":
            "identity_boundary_system",

            "multi_layer_identity_checks":
            inspections,

            "blocked_identity_fusions":
            len(
                blocked,
            ),

            "identity_boundary_state":
            (
                "identity_fusion_firewall_active"
                if blocked
                else "identity_fusion_within_bounds"
            ),
        }
