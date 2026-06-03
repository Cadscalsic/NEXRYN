# ============================================
# NEXRYN SEMANTIC SPINE
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


class SemanticSpine:

    def __init__(self):

        self.semantic_spine_state = None
        self.recovery_streak = 0

    def regulate_recovery(self, repair_required):

        previous_state = self.semantic_spine_state

        if repair_required:

            self.recovery_streak = 0
            state = "semantic_spine_repairing"

        elif previous_state in [
            "semantic_spine_repairing",
            "semantic_spine_recovering",
        ]:

            self.recovery_streak += 1
            state = (
                "semantic_spine_stable"
                if self.recovery_streak >= 3
                else "semantic_spine_recovering"
            )

        else:

            self.recovery_streak = 0
            state = "semantic_spine_stable"

        self.semantic_spine_state = state

        return {
            "semantic_spine_state":
            state,

            "previous_semantic_spine_state":
            previous_state,

            "recovery_streak":
            self.recovery_streak,

            "required_recovery_cycles":
            3,

            "recovery_confirmation_pending":
            state == "semantic_spine_recovering",
        }

    def semantic_gravity(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        gravity = field.get(
            "semantic_gravity_fields",
            {},
        )

        return {
            "gravity_strength":
            _clamp(
                gravity.get(
                    "field_pull",
                    gravity.get(
                        "gravity_strength",
                        0.0,
                    ),
                )
            ),

            "anchor_targets":
            gravity.get(
                "anchor_targets",
                [],
            ),

            "semantic_gravity_state":
            gravity.get(
                "gravity_field_state",
                "anchor_field_weak",
            ),
        }

    def identity_tensor_continuity(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        tensor = field.get(
            "identity_tensor_continuity",
            {},
        )

        return {
            "tensor_continuity":
            _clamp(
                tensor.get(
                    "tensor_continuity",
                    0.0,
                )
            ),

            "identity_tensor_state":
            tensor.get(
                "tensor_continuity_state",
                "identity_tensor_tearing",
            ),
        }

    def drift_diffusion_suppression(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        diffusion = field.get(
            "drift_diffusion_equations",
            {},
        )

        diffusion_rate = _clamp(
            diffusion.get(
                "diffusion_rate",
                1.0,
            )
        )

        return {
            "diffusion_rate":
            diffusion_rate,

            "suppression_strength":
            _clamp(
                1.0
                -
                diffusion_rate,
            ),

            "suppression_state":
            (
                "drift_suppressed"
                if diffusion_rate < 0.42
                else "drift_suppression_required"
            ),
        }

    def semantic_elastic_topology(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        elasticity = field.get(
            "topological_semantic_elasticity",
            {},
        )

        return {
            "elasticity":
            _clamp(
                elasticity.get(
                    "elasticity",
                    0.0,
                )
            ),

            "adaptation_without_collapse":
            elasticity.get(
                "adaptation_without_collapse",
                False,
            ),

            "elastic_topology_state":
            elasticity.get(
                "elasticity_state",
                "topological_elasticity_brittle",
            ),
        }

    def attractor_basin_stabilization(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        basin = field.get(
            "attractor_basin_stabilization",
            {},
        )

        return {
            "basin_strength":
            _clamp(
                basin.get(
                    "basin_strength",
                    0.0,
                )
            ),

            "attractor_targets":
            basin.get(
                "attractor_targets",
                [],
            ),

            "basin_state":
            basin.get(
                "basin_state",
                "basin_stabilization_required",
            ),
        }

    def thermodynamic_entropy_cooling(self, context):

        field = context.get(
            "semantic_field_dynamics_report",
            {},
        )

        cooling = field.get(
            "entropy_cooling_mechanics",
            {},
        )

        projected_entropy = _clamp(
            cooling.get(
                "projected_entropy",
                context.get(
                    "runtime_entropy",
                    1.0,
                ),
            )
        )

        return {
            "cooling_intensity":
            _clamp(
                cooling.get(
                    "cooling_intensity",
                    0.0,
                )
            ),

            "projected_entropy":
            projected_entropy,

            "entropy_cooling_state":
            (
                "entropy_cooling_active"
                if projected_entropy >= 0.52
                else "entropy_cooled"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        gravity = self.semantic_gravity(
            context,
        )
        tensor = self.identity_tensor_continuity(
            context,
        )
        suppression = self.drift_diffusion_suppression(
            context,
        )
        topology = self.semantic_elastic_topology(
            context,
        )
        basin = self.attractor_basin_stabilization(
            context,
        )
        cooling = self.thermodynamic_entropy_cooling(
            context,
        )

        spine_integrity = _clamp(
            gravity.get(
                "gravity_strength",
                0.0,
            )
            * 0.2
            +
            tensor.get(
                "tensor_continuity",
                0.0,
            )
            * 0.24
            +
            suppression.get(
                "suppression_strength",
                0.0,
            )
            * 0.16
            +
            topology.get(
                "elasticity",
                0.0,
            )
            * 0.16
            +
            basin.get(
                "basin_strength",
                0.0,
            )
            * 0.16
            +
            (
                1.0
                -
                cooling.get(
                    "projected_entropy",
                    1.0,
                )
            )
            * 0.08
        )

        repair_required = (
            spine_integrity < 0.56
            or tensor.get(
                "identity_tensor_state",
            )
            == "identity_tensor_tearing"
            or suppression.get(
                "suppression_state",
            )
            == "drift_suppression_required"
            or basin.get(
                "basin_state",
            )
            == "basin_stabilization_required"
        )
        recovery = self.regulate_recovery(
            repair_required,
        )

        return {
            "system":
            "semantic_spine",

            "semantic_gravity":
            gravity,

            "identity_tensor_continuity":
            tensor,

            "drift_diffusion_suppression":
            suppression,

            "semantic_elastic_topology":
            topology,

            "attractor_basin_stabilization":
            basin,

            "thermodynamic_entropy_cooling":
            cooling,

            "spine_integrity":
            spine_integrity,

            "spine_policy":
            (
                "repair_semantic_spine_before_governance_expansion"
                if repair_required
                else "confirm_semantic_spine_recovery_before_governance_expansion"
                if recovery["recovery_confirmation_pending"]
                else "semantic_spine_supports_controlled_evolution"
            ),

            **recovery,
        }


semantic_spine = SemanticSpine()
