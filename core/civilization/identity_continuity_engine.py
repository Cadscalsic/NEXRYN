# ============================================
# NEXRYN IDENTITY CONTINUITY ENGINE
# ============================================


def _clamp(value):

    try:
        value = float(
            value,
        )
    except Exception:
        value = 0.0

    return round(
        max(
            0.0,
            min(
                value,
                1.0,
            ),
        ),
        4,
    )


class IdentityContinuityEngine:

    def protect_cognitive_spine(self, context):

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        anchor_graph = context.get(
            "semantic_anchor_graph_report",
            {},
        )

        stabilizer = context.get(
            "cognitive_spine_stabilizer_report",
            {},
        )

        anchor_strength = _clamp(
            stabilizer.get(
                "anchor_reinforcement",
                {},
            ).get(
                "reinforced_anchor_strength",
                anchor_graph.get(
                    "identity_stability",
                    anchor_graph.get(
                        "anchor_strength",
                        0.5,
                    ),
                ),
            )
        )

        spine_stability = _clamp(
            stabilizer.get(
                "spine_stability",
                anchor_strength,
            )
        )

        block_rewrite = guardian.get(
            "catastrophic_rewrite_guard",
            {},
        ).get(
            "block_rewrite",
            False,
        )

        return {
            "anchor_strength":
            anchor_strength,

            "spine_stability":
            spine_stability,

            "block_rewrite":
            block_rewrite,

            "spine_state":
            (
                "cognitive_spine_protected"
                if spine_stability >= 0.56
                and not block_rewrite
                else "cognitive_spine_repairing"
                if spine_stability >= 0.42
                else "cognitive_spine_fragile"
            ),
        }

    def prevent_fragmentation(self, context):

        stability = context.get(
            "stability_field_report",
            {},
        )

        fragmentation = stability.get(
            "identity_fragmentation",
            {},
        ).get(
            "fragmentation_detected",
            False,
        )

        drift = _clamp(
            stability.get(
                "semantic_drift",
                {},
            ).get(
                "semantic_drift",
                context.get(
                    "identity_drift",
                    0.0,
                ),
            )
        )

        return {
            "fragmentation_detected":
            fragmentation,

            "semantic_drift":
            drift,

            "fragmentation_state":
            (
                "fragmentation_intervention_required"
                if fragmentation
                else "semantic_drift_intervention_required"
                if drift > 0.62
                else "fragmentation_contained"
            ),
        }

    def repair_identity(self, spine_report, fragmentation_report):

        repair_actions = []

        if spine_report.get(
            "spine_state",
        ) in [
            "cognitive_spine_fragile",
            "cognitive_spine_repairing",
        ]:

            repair_actions.append(
                "reinforce_identity_anchors",
            )

        if fragmentation_report.get(
            "fragmentation_state",
        ) in [
            "fragmentation_intervention_required",
            "semantic_drift_intervention_required",
        ]:

            repair_actions.extend([
                "rollback_unstable_identity_edges",
                "reconstruct_semantic_spine",
            ])

        if not repair_actions:

            repair_actions.append(
                "maintain_identity_continuity",
            )

        return {
            "repair_actions":
            sorted(
                set(
                    repair_actions,
                )
            ),

            "repair_state":
            (
                "identity_repair_active"
                if len(
                    repair_actions,
                ) > 1
                or repair_actions[0] != "maintain_identity_continuity"
                else "identity_repair_standby"
            ),
        }

    def preserve_semantic_spine(self, repair_report):

        return {
            "semantic_spine_policy":
            (
                "preserve_and_reconstruct"
                if repair_report.get(
                    "repair_state",
                ) == "identity_repair_active"
                else "preserve_current_spine"
            ),

            "protected_invariants":
            [
                "causal_history",
                "semantic_anchors",
                "identity_lineage",
                "constitutional_constraints",
                "constitutional_truth_commitments",
            ],
        }

    def run_cycle(self, context):

        spine = self.protect_cognitive_spine(
            context,
        )
        fragmentation = self.prevent_fragmentation(
            context,
        )
        repair = self.repair_identity(
            spine,
            fragmentation,
        )
        preservation = self.preserve_semantic_spine(
            repair,
        )

        return {
            "system":
            "identity_continuity_engine",

            "cognitive_spine":
            spine,

            "fragmentation_guard":
            fragmentation,

            "identity_repair":
            repair,

            "semantic_spine_preservation":
            preservation,

            "identity_continuity_state":
            (
                "identity_continuity_repairing"
                if repair.get(
                    "repair_state",
                ) == "identity_repair_active"
                else "identity_continuity_stable"
            ),
        }


identity_continuity_engine = IdentityContinuityEngine()
