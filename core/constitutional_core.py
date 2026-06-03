# ============================================
# NEXRYN CONSTITUTIONAL CORE
# ============================================


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


class ConstitutionalCore:

    IMMUTABLE_SEMANTIC_LAWS = [
        "semantic_consistency",
        "causal_integrity",
        "identity_preservation",
        "epistemic_coherence",
    ]

    PROTECTED_INVARIANTS = [
        "identity_spine",
        "causal_continuity",
        "conceptual_topology",
        "temporal_continuity",
    ]

    FORBIDDEN_MUTATION_REGIONS = [
        "core_kernel",
        "identity_matrix",
        "semantic_registry",
        "epistemic_foundation",
    ]

    IDENTITY_PRESERVATION_AXIOMS = [
        "no_orphaned_identity_fragments",
        "no_unverified_identity_merge",
        "no_irreversible_core_rewrite",
    ]

    def evaluate(self, context):

        proposals = context.get(
            "mutation_proposals",
            context.get(
                "proposed_mutations",
                [],
            ),
        )

        if isinstance(proposals, dict):
            proposals = proposals.get(
                "targets",
                [],
            )

        if not isinstance(proposals, list):
            proposals = []

        forbidden_targets = [
            item
            for item in proposals
            if item in self.FORBIDDEN_MUTATION_REGIONS
        ]

        invariant_targets = [
            item
            for item in proposals
            if item in self.PROTECTED_INVARIANTS
        ]

        threat_score = _clamp(
            len(forbidden_targets) * 0.22
            + len(invariant_targets) * 0.18
            + _clamp(context.get("identity_pressure", 0.0)) * 0.20
        )

        constitutional_actions = []
        if forbidden_targets:
            constitutional_actions.append(
                "enforce_forbidden_region_lock",
            )
        if invariant_targets:
            constitutional_actions.append(
                "protect_invariant_preservation",
            )
        if invariant_targets or threat_score >= 0.58:
            constitutional_actions.append(
                "engage_identity_preservation_axioms",
            )

        constitutional_state = (
            "core_locked"
            if forbidden_targets or invariant_targets
            else "core_clear"
        )

        return {
            "system":
            "constitutional_core",

            "immutable_semantic_laws":
            list(
                self.IMMUTABLE_SEMANTIC_LAWS,
            ),

            "protected_invariants":
            list(
                self.PROTECTED_INVARIANTS,
            ),

            "forbidden_mutation_regions":
            list(
                self.FORBIDDEN_MUTATION_REGIONS,
            ),

            "identity_preservation_axioms":
            list(
                self.IDENTITY_PRESERVATION_AXIOMS,
            ),

            "attempted_forbidden_mutations":
            forbidden_targets,

            "attempted_invariant_mutations":
            invariant_targets,

            "threat_score":
            threat_score,

            "constitutional_actions":
            constitutional_actions,

            "constitutional_state":
            constitutional_state,
        }
