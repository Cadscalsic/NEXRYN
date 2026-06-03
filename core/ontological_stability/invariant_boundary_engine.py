from enum import Enum


class InvariantLevel(Enum):

    ABSOLUTE = 1
    CONSTITUTIONAL = 2
    STABILIZING = 3
    CONTEXTUAL = 4
    TEMPORARY = 5


class InvariantBoundaryEngine:

    ABSOLUTE_INVARIANTS = {
        "causal_continuity",
        "identity_continuity",
        "constitutional_truth",
    }

    CONSTITUTIONAL_INVARIANTS = {
        "preserve_ontology_identity",
        "protect_core_invariants",
        "architectural_invariant_preservation",
    }

    STABILIZING_INVARIANTS = {
        "semantic_anchor",
        "semantic_spine",
        "topology_preservation",
        "symmetry_preservation",
        "size_preservation",
    }

    CONTEXTUAL_INVARIANTS = {
        "symbolic_representation",
        "contextual_mapping",
        "heuristic_strategy",
    }

    def classify(self, invariant):

        if not isinstance(
            invariant,
            dict,
        ):

            invariant = {
                "id":
                invariant,
            }

        invariant_id = str(
            invariant.get(
                "id",
                invariant.get(
                    "name",
                    invariant,
                ),
            )
        )

        if invariant_id in self.ABSOLUTE_INVARIANTS:

            level = InvariantLevel.ABSOLUTE

        elif invariant_id in self.CONSTITUTIONAL_INVARIANTS:

            level = InvariantLevel.CONSTITUTIONAL

        elif invariant_id in self.STABILIZING_INVARIANTS:

            level = InvariantLevel.STABILIZING

        elif invariant_id in self.CONTEXTUAL_INVARIANTS:

            level = InvariantLevel.CONTEXTUAL

        else:

            level = InvariantLevel.TEMPORARY

        return {
            "invariant_id":
            invariant_id,

            "level":
            level.name,

            "negotiable":
            level in [
                InvariantLevel.CONTEXTUAL,
                InvariantLevel.TEMPORARY,
            ],

            "negotiation_policy":
            (
                "non_negotiable"
                if level in [
                    InvariantLevel.ABSOLUTE,
                    InvariantLevel.CONSTITUTIONAL,
                ]
                else "strictly_limited"
                if level == InvariantLevel.STABILIZING
                else "contextual_negotiation_allowed"
            ),
        }

    def run_cycle(self, context):

        invariants = [
            "causal_continuity",
            "identity_continuity",
            "constitutional_truth",
            "semantic_anchor",
            "semantic_spine",
            "topology_preservation",
            "symmetry_preservation",
            "size_preservation",
            "symbolic_representation",
            "contextual_mapping",
        ]

        for invariant in context.get(
            "architectural_invariants",
            [],
        ):

            if invariant not in invariants:

                invariants.append(
                    invariant,
                )

        hierarchy = [
            self.classify(
                invariant,
            )
            for invariant in invariants
        ]

        protected = [
            item
            for item in hierarchy
            if not item.get(
                "negotiable",
            )
        ]

        return {
            "system":
            "invariant_boundary_engine",

            "invariant_hierarchy":
            hierarchy,

            "protected_invariants":
            protected,

            "boundary_state":
            "invariant_hierarchy_enforced",
        }
