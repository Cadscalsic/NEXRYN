# ============================================
# NEXRYN COGNITIVE SPINE STABILIZER
# ============================================


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(
            value,
        )
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


class CognitiveSpineStabilizer:

    def anchor_reinforcement(self, context):

        anchor_graph = context.get(
            "semantic_anchor_graph_report",
            context.get(
                "semantic_anchor_graph",
                {},
            ),
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        raw_strength = _clamp(
            anchor_graph.get(
                "identity_stability",
                anchor_graph.get(
                    "anchor_strength",
                    0.5,
                ),
            )
        )

        block_rewrite = guardian.get(
            "catastrophic_rewrite_guard",
            {},
        ).get(
            "block_rewrite",
            False,
        )

        reinforced_strength = _clamp(
            raw_strength
            +
            (
                0.08
                if not block_rewrite
                else -0.14
            )
        )

        return {
            "raw_anchor_strength":
            raw_strength,

            "reinforced_anchor_strength":
            reinforced_strength,

            "block_rewrite":
            block_rewrite,

            "anchor_reinforcement_state":
            (
                "anchors_reinforced"
                if reinforced_strength >= 0.58
                and not block_rewrite
                else "anchors_require_repair"
            ),
        }

    def semantic_field_bracing(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        gravity = field.get(
            "semantic_gravity_fields",
            {},
        )

        elasticity = field.get(
            "topological_semantic_elasticity",
            {},
        )

        inertia = field.get(
            "semantic_inertia_tensors",
            {},
        )

        spine = context.get(
            "semantic_spine_report",
            {},
        )

        brace_score = _clamp(
            gravity.get(
                "field_pull",
                0.0,
            )
            * 0.28
            +
            elasticity.get(
                "elasticity",
                0.0,
            )
            * 0.26
            +
            inertia.get(
                "inertia_tensor_strength",
                0.0,
            )
            * 0.22
            +
            spine.get(
                "spine_integrity",
                0.0,
            )
            * 0.24
        )

        return {
            "field_brace_score":
            brace_score,

            "field_policy":
            field.get(
                "field_policy",
                "unknown",
            ),

            "semantic_spine_state":
            spine.get(
                "semantic_spine_state",
                "unknown",
            ),

            "field_bracing_state":
            (
                "semantic_field_braced"
                if brace_score >= 0.52
                else "semantic_field_brace_weak"
            ),
        }

    def continuity_ligaments(self, context):

        stability = context.get(
            "identity_stability_report",
            {},
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        continuity = _clamp(
            context.get(
                "identity_continuity",
                stability.get(
                    "identity_continuity",
                    guardian.get(
                        "continuity_score",
                        0.62,
                    ),
                ),
            )
        )

        drift = _clamp(
            context.get(
                "semantic_drift",
                context.get(
                    "stability_field_report",
                    {},
                ).get(
                    "semantic_drift",
                    {},
                ).get(
                    "semantic_drift",
                    0.0,
                ),
            )
        )

        ligament_strength = _clamp(
            continuity
            *
            (
                1.0
                -
                drift
                * 0.42
            )
        )

        return {
            "identity_continuity":
            continuity,

            "semantic_drift":
            drift,

            "ligament_strength":
            ligament_strength,

            "continuity_ligament_state":
            (
                "continuity_ligaments_intact"
                if ligament_strength >= 0.48
                else "continuity_ligaments_fragile"
            ),
        }

    def spine_repair_protocol(
        self,
        anchor_report,
        field_report,
        ligament_report,
    ):

        actions = []

        if anchor_report.get(
            "anchor_reinforcement_state",
        ) == "anchors_require_repair":

            actions.append(
                "rebuild_semantic_anchor_graph",
            )

        if field_report.get(
            "field_bracing_state",
        ) == "semantic_field_brace_weak":

            actions.append(
                "increase_semantic_gravity_field",
            )

        if ligament_report.get(
            "continuity_ligament_state",
        ) == "continuity_ligaments_fragile":

            actions.append(
                "restore_causal_identity_ligaments",
            )

        if not actions:

            actions.append(
                "maintain_cognitive_spine",
            )

        return {
            "repair_actions":
            sorted(
                set(
                    actions,
                )
            ),

            "spine_repair_state":
            (
                "spine_repair_active"
                if actions != [
                    "maintain_cognitive_spine",
                ]
                else "spine_repair_standby"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        anchors = self.anchor_reinforcement(
            context,
        )
        field = self.semantic_field_bracing(
            context,
        )
        ligaments = self.continuity_ligaments(
            context,
        )
        repair = self.spine_repair_protocol(
            anchors,
            field,
            ligaments,
        )

        spine_stability = _clamp(
            anchors.get(
                "reinforced_anchor_strength",
                0.0,
            )
            * 0.38
            +
            field.get(
                "field_brace_score",
                0.0,
            )
            * 0.34
            +
            ligaments.get(
                "ligament_strength",
                0.0,
            )
            * 0.28
        )

        return {
            "system":
            "cognitive_spine_stabilizer",

            "anchor_reinforcement":
            anchors,

            "semantic_field_bracing":
            field,

            "continuity_ligaments":
            ligaments,

            "spine_repair_protocol":
            repair,

            "spine_stability":
            spine_stability,

            "cognitive_spine_state":
            (
                "cognitive_spine_stabilized"
                if spine_stability >= 0.56
                and repair.get(
                    "spine_repair_state",
                )
                == "spine_repair_standby"
                else "cognitive_spine_repairing"
                if spine_stability >= 0.42
                else "cognitive_spine_fragile"
            ),
        }


cognitive_spine_stabilizer = CognitiveSpineStabilizer()
