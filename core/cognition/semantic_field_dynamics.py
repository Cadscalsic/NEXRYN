# ============================================
# NEXRYN SEMANTIC FIELD DYNAMICS
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


class SemanticFieldDynamics:

    def _semantic_drift(self, context):

        return _clamp(
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

    def _semantic_physics(self, context):

        return context.get(
            "semantic_physics_report",
            {},
        )

    def semantic_gravity_fields(self, context):

        physics = self._semantic_physics(
            context,
        )

        gravity = physics.get(
            "semantic_gravity",
            {},
        )

        drift = self._semantic_drift(
            context,
        )

        gravity_strength = _clamp(
            gravity.get(
                "gravity_strength",
                0.0,
            )
        )

        field_pull = _clamp(
            gravity_strength
            *
            (
                1.0
                -
                drift
                * 0.45
            )
        )

        return {
            "gravity_strength":
            gravity_strength,

            "field_pull":
            field_pull,

            "anchor_targets":
            gravity.get(
                "gravity_wells",
                [],
            )[:16],

            "gravity_field_state":
            (
                "anchor_field_holding"
                if field_pull >= 0.48
                else "anchor_field_weak"
            ),
        }

    def drift_diffusion_equations(self, context, gravity_report):

        drift = self._semantic_drift(
            context,
        )

        field_pull = gravity_report.get(
            "field_pull",
            0.0,
        )

        diffusion_rate = _clamp(
            drift
            *
            (
                1.0
                -
                field_pull
                * 0.55
            )
        )

        corrected_drift = _clamp(
            drift
            -
            field_pull
            * 0.28
        )

        return {
            "input_semantic_drift":
            drift,

            "diffusion_rate":
            diffusion_rate,

            "projected_corrected_drift":
            corrected_drift,

            "drift_diffusion_state":
            (
                "drift_diffusion_high"
                if diffusion_rate >= 0.58
                else "drift_diffusion_contained"
            ),
        }

    def entropy_cooling_mechanics(self, context, diffusion_report):

        physics = self._semantic_physics(
            context,
        )

        entropy = _clamp(
            physics.get(
                "entropy_diffusion",
                {},
            ).get(
                "runtime_entropy",
                context.get(
                    "runtime_entropy",
                    0.0,
                ),
            )
        )

        diffusion_rate = diffusion_report.get(
            "diffusion_rate",
            0.0,
        )

        cooling_intensity = _clamp(
            entropy
            * 0.55
            +
            diffusion_rate
            * 0.45
        )

        cooled_entropy = _clamp(
            entropy
            -
            cooling_intensity
            * 0.22
        )

        return {
            "cooling_intensity":
            cooling_intensity,

            "projected_entropy":
            cooled_entropy,

            "cooling_policy":
            (
                "progressive_cognitive_cooling"
                if cooling_intensity >= 0.42
                else "passive_entropy_decay"
            ),
        }

    def semantic_inertia_tensors(self, context, gravity_report):

        physics = self._semantic_physics(
            context,
        )

        inertia = _clamp(
            physics.get(
                "identity_inertia",
                {},
            ).get(
                "identity_inertia",
                0.0,
            )
        )

        mass = _clamp(
            physics.get(
                "cognitive_mass",
                {},
            ).get(
                "average_cognitive_mass",
                0.0,
            )
        )

        tensor_strength = _clamp(
            inertia
            * 0.55
            +
            mass
            * 0.3
            +
            gravity_report.get(
                "field_pull",
                0.0,
            )
            * 0.15
        )

        return {
            "inertia_tensor_strength":
            tensor_strength,

            "mutation_spike_resistance":
            _clamp(
                tensor_strength
                * 0.84,
            ),

            "inertia_tensor_state":
            (
                "semantic_inertia_tensor_stable"
                if tensor_strength >= 0.56
                else "semantic_inertia_tensor_fragile"
            ),
        }

    def topological_semantic_elasticity(
        self,
        context,
        diffusion_report,
        inertia_report,
    ):

        physics = self._semantic_physics(
            context,
        )

        orbital_score = _clamp(
            physics.get(
                "semantic_orbital_stability",
                {},
            ).get(
                "orbital_score",
                0.0,
            )
        )

        diffusion_rate = diffusion_report.get(
            "diffusion_rate",
            0.0,
        )

        inertia = inertia_report.get(
            "inertia_tensor_strength",
            0.0,
        )

        elasticity = _clamp(
            orbital_score
            * 0.42
            +
            inertia
            * 0.42
            +
            (
                1.0
                -
                diffusion_rate
            )
            * 0.16
        )

        return {
            "elasticity":
            elasticity,

            "adaptation_without_collapse":
            elasticity >= 0.52,

            "elasticity_state":
            (
                "topological_elasticity_safe"
                if elasticity >= 0.52
                else "topological_elasticity_brittle"
            ),
        }

    def identity_tensor_continuity(
        self,
        context,
        inertia_report,
        elasticity_report,
    ):

        continuity = _clamp(
            context.get(
                "identity_continuity",
                context.get(
                    "identity_continuity_guardian_report",
                    {},
                ).get(
                    "continuity_score",
                    0.62,
                ),
            )
        )

        tensor_continuity = _clamp(
            continuity
            * 0.46
            +
            inertia_report.get(
                "inertia_tensor_strength",
                0.0,
            )
            * 0.34
            +
            elasticity_report.get(
                "elasticity",
                0.0,
            )
            * 0.2
        )

        return {
            "identity_continuity":
            continuity,

            "tensor_continuity":
            tensor_continuity,

            "tensor_continuity_state":
            (
                "identity_tensor_continuous"
                if tensor_continuity >= 0.56
                else "identity_tensor_tearing"
            ),
        }

    def attractor_basin_stabilization(
        self,
        gravity_report,
        diffusion_report,
        cooling_report,
        tensor_report,
    ):

        basin_strength = _clamp(
            gravity_report.get(
                "field_pull",
                0.0,
            )
            * 0.34
            +
            (
                1.0
                -
                diffusion_report.get(
                    "diffusion_rate",
                    0.0,
                )
            )
            * 0.24
            +
            (
                1.0
                -
                cooling_report.get(
                    "projected_entropy",
                    1.0,
                )
            )
            * 0.18
            +
            tensor_report.get(
                "tensor_continuity",
                0.0,
            )
            * 0.24
        )

        return {
            "basin_strength":
            basin_strength,

            "attractor_targets":
            gravity_report.get(
                "anchor_targets",
                [],
            )[:12],

            "basin_state":
            (
                "stable_semantic_basin"
                if basin_strength >= 0.54
                else "basin_stabilization_required"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        gravity = self.semantic_gravity_fields(
            context,
        )
        diffusion = self.drift_diffusion_equations(
            context,
            gravity,
        )
        cooling = self.entropy_cooling_mechanics(
            context,
            diffusion,
        )
        inertia = self.semantic_inertia_tensors(
            context,
            gravity,
        )
        elasticity = self.topological_semantic_elasticity(
            context,
            diffusion,
            inertia,
        )
        tensor = self.identity_tensor_continuity(
            context,
            inertia,
            elasticity,
        )
        basin = self.attractor_basin_stabilization(
            gravity,
            diffusion,
            cooling,
            tensor,
        )

        unstable = (
            gravity.get(
                "gravity_field_state",
            )
            == "anchor_field_weak"
            or diffusion.get(
                "drift_diffusion_state",
            )
            == "drift_diffusion_high"
            or inertia.get(
                "inertia_tensor_state",
            )
            == "semantic_inertia_tensor_fragile"
            or elasticity.get(
                "elasticity_state",
            )
            == "topological_elasticity_brittle"
            or tensor.get(
                "tensor_continuity_state",
            )
            == "identity_tensor_tearing"
            or basin.get(
                "basin_state",
            )
            == "basin_stabilization_required"
        )

        return {
            "system":
            "semantic_field_dynamics",

            "semantic_gravity_fields":
            gravity,

            "drift_diffusion_equations":
            diffusion,

            "entropy_cooling_mechanics":
            cooling,

            "semantic_inertia_tensors":
            inertia,

            "topological_semantic_elasticity":
            elasticity,

            "identity_tensor_continuity":
            tensor,

            "attractor_basin_stabilization":
            basin,

            "field_policy":
            (
                "stabilize_semantic_field_before_evolution"
                if unstable
                else "semantic_field_allows_controlled_adaptation"
            ),

            "semantic_field_state":
            (
                "semantic_field_unstable"
                if unstable
                else "semantic_field_stable"
            ),
        }


semantic_field_dynamics = SemanticFieldDynamics()
