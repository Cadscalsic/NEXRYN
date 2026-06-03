# ============================================
# NEXRYN SEMANTIC PHYSICS
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


class SemanticPhysics:

    def _concept_nodes(self, context):

        semantic_graph = context.get(
            "semantic_graph",
            {},
        )

        if not isinstance(
            semantic_graph,
            dict,
        ):

            return []

        nodes = semantic_graph.get(
            "concept_nodes",
            [],
        )

        return [
            node
            for node in nodes
            if isinstance(
                node,
                dict,
            )
        ]

    def _concept_id(self, node):

        return (
            node.get(
                "compressed_concept",
            )
            or node.get(
                "semantic_concept",
            )
            or node.get(
                "concept",
            )
            or node.get(
                "primitive",
                "unknown_concept",
            )
        )

    def _anchor_nodes(self, nodes):

        anchors = []

        for node in nodes:

            semantic_class = node.get(
                "semantic_class",
                "",
            )
            category = node.get(
                "category",
                "",
            )

            if (
                semantic_class == "invariant"
                or category == "stability"
            ):

                anchors.append(
                    node,
                )

        return anchors

    def cognitive_mass(self, context):

        nodes = self._concept_nodes(
            context,
        )

        masses = []

        for node in nodes:

            confidence = _clamp(
                node.get(
                    "confidence",
                    0.5,
                )
            )
            invariant_bonus = (
                0.18
                if node.get(
                    "semantic_class",
                )
                == "invariant"
                else 0.0
            )
            topology_bonus = (
                0.12
                if node.get(
                    "topology_signature",
                    "none",
                )
                != "none"
                else 0.0
            )

            mass = _clamp(
                confidence
                * 0.7
                +
                invariant_bonus
                +
                topology_bonus
            )

            masses.append({
                "concept":
                self._concept_id(
                    node,
                ),

                "mass":
                mass,

                "density":
                _clamp(
                    mass
                    /
                    max(
                        len(
                            set(
                                str(
                                    value,
                                )
                                for value in node.values()
                            )
                        ),
                        1,
                    )
                    * 6.0
                ),
            })

        average_mass = _clamp(
            sum(
                item[
                    "mass"
                ]
                for item in masses
            )
            /
            max(
                len(
                    masses,
                ),
                1,
            )
        )

        return {
            "concept_masses":
            masses[:24],

            "average_cognitive_mass":
            average_mass,

            "mass_state":
            (
                "heavy_stable_field"
                if average_mass >= 0.62
                else "light_unstable_field"
            ),
        }

    def semantic_gravity(self, context, mass_report=None):

        nodes = self._concept_nodes(
            context,
        )
        anchors = self._anchor_nodes(
            nodes,
        )

        if mass_report is None:

            mass_report = self.cognitive_mass(
                context,
            )

        average_mass = mass_report.get(
            "average_cognitive_mass",
            0.0,
        )

        anchor_ratio = _clamp(
            len(
                anchors,
            )
            /
            max(
                len(
                    nodes,
                ),
                1,
            )
        )

        gravity_strength = _clamp(
            average_mass
            * 0.55
            +
            anchor_ratio
            * 0.45
        )

        return {
            "gravity_strength":
            gravity_strength,

            "anchor_count":
            len(
                anchors,
            ),

            "gravity_wells":
            [
                self._concept_id(
                    node,
                )
                for node in anchors[:12]
            ],

            "gravity_state":
            (
                "semantic_gravity_stable"
                if gravity_strength >= 0.58
                else "semantic_gravity_weak"
            ),
        }

    def entropy_diffusion(self, context):

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                context.get(
                    "entropy_regulator_report",
                    {},
                ).get(
                    "entropy_delta_report",
                    {},
                ).get(
                    "runtime_entropy",
                    0.0,
                ),
            )
        )

        node_count = len(
            self._concept_nodes(
                context,
            )
        )

        diffusion_pressure = _clamp(
            entropy
            *
            min(
                node_count / 24,
                1.0,
            )
        )

        return {
            "runtime_entropy":
            entropy,

            "diffusion_pressure":
            diffusion_pressure,

            "entropy_diffusion_state":
            (
                "semantic_overheating"
                if diffusion_pressure >= 0.68
                else "diffusion_controlled"
            ),
        }

    def identity_inertia(self, context, gravity_report=None):

        if gravity_report is None:

            gravity_report = self.semantic_gravity(
                context,
            )

        identity_continuity = _clamp(
            context.get(
                "identity_continuity",
                context.get(
                    "identity_continuity_guardian_report",
                    {},
                ).get(
                    "continuity_score",
                    0.65,
                ),
            )
        )

        gravity_strength = gravity_report.get(
            "gravity_strength",
            0.0,
        )

        inertia = _clamp(
            identity_continuity
            * 0.62
            +
            gravity_strength
            * 0.38
        )

        return {
            "identity_continuity":
            identity_continuity,

            "identity_inertia":
            inertia,

            "inertia_state":
            (
                "identity_inertia_stable"
                if inertia >= 0.62
                else "identity_inertia_fragile"
            ),
        }

    def semantic_orbital_stability(self, context, gravity_report=None):

        if gravity_report is None:

            gravity_report = self.semantic_gravity(
                context,
            )

        nodes = self._concept_nodes(
            context,
        )

        orbiting_concepts = []

        for node in nodes:

            if node in self._anchor_nodes(
                [node],
            ):

                continue

            concept = self._concept_id(
                node,
            )
            orbiting_concepts.append({
                "concept":
                concept,

                "orbit_policy":
                "orbit_anchor_do_not_direct_merge",
            })

        orbital_score = _clamp(
            gravity_report.get(
                "gravity_strength",
                0.0,
            )
            -
            min(
                len(
                    orbiting_concepts,
                )
                / 80,
                0.25,
            )
        )

        return {
            "orbital_score":
            orbital_score,

            "orbiting_concepts":
            orbiting_concepts[:24],

            "orbital_state":
            (
                "semantic_orbits_stable"
                if orbital_score >= 0.5
                else "semantic_orbits_unstable"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        mass = self.cognitive_mass(
            context,
        )
        gravity = self.semantic_gravity(
            context,
            mass,
        )
        diffusion = self.entropy_diffusion(
            context,
        )
        inertia = self.identity_inertia(
            context,
            gravity,
        )
        orbital = self.semantic_orbital_stability(
            context,
            gravity,
        )

        fragile = (
            gravity.get(
                "gravity_state",
            )
            == "semantic_gravity_weak"
            or diffusion.get(
                "entropy_diffusion_state",
            )
            == "semantic_overheating"
            or inertia.get(
                "inertia_state",
            )
            == "identity_inertia_fragile"
            or orbital.get(
                "orbital_state",
            )
            == "semantic_orbits_unstable"
        )

        return {
            "system":
            "semantic_physics",

            "cognitive_mass":
            mass,

            "semantic_gravity":
            gravity,

            "entropy_diffusion":
            diffusion,

            "identity_inertia":
            inertia,

            "semantic_orbital_stability":
            orbital,

            "physics_policy":
            (
                "stabilize_before_merge"
                if fragile
                else "semantic_physics_stable"
            ),

            "semantic_physics_state":
            (
                "semantic_physics_fragile"
                if fragile
                else "semantic_physics_stable"
            ),
        }


semantic_physics = SemanticPhysics()
