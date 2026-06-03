# ============================================
# NEXRYN IDENTITY REASONER
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


class IdentityReasoner:

    def __init__(self):

        self.reasoning_history = []

    def _tokens(self, value):

        if value is None:

            return set()

        if isinstance(
            value,
            (list, tuple, set),
        ):

            tokens = set()

            for item in value:

                tokens.update(
                    self._tokens(
                        item,
                    )
                )

            return tokens

        return set(
            str(
                value,
            )
            .lower()
            .replace(
                "-",
                "_",
            )
            .split(
                "_",
            )
        )

    def _jaccard(self, left, right):

        left_tokens = self._tokens(
            left,
        )
        right_tokens = self._tokens(
            right,
        )

        if not left_tokens and not right_tokens:

            return 0.0

        return _clamp(
            len(
                left_tokens & right_tokens,
            )
            /
            max(
                len(
                    left_tokens | right_tokens,
                ),
                1,
            )
        )

    def _concept_id(self, concept):

        return concept.get(
            "concept_id",
            concept.get(
                "concept",
                concept.get(
                    "id",
                    concept.get(
                        "canonical_concept",
                        "unknown_concept",
                    ),
                ),
            ),
        )

    def _identity(self, concept):

        identity = concept.get(
            "identity",
            {},
        )

        concept_id = self._concept_id(
            concept,
        )

        return {
            "local_identity":
            identity.get(
                "local_identity",
                concept_id,
            ),

            "structural_identity":
            identity.get(
                "structural_identity",
                concept.get(
                    "structural_signature",
                    concept_id,
                ),
            ),

            "causal_identity":
            identity.get(
                "causal_identity",
                concept.get(
                    "causal_role",
                    concept_id,
                ),
            ),

            "archetypal_identity":
            identity.get(
                "archetypal_identity",
                concept.get(
                    "archetype",
                    "general_concept",
                ),
            ),

            "symbolic_identity":
            identity.get(
                "symbolic_identity",
                concept.get(
                    "symbolic_signature",
                    concept_id,
                ),
            ),

            "unsafe_merge_context":
            concept.get(
                "unsafe_merge_context",
                False,
            ),

            "ontology_damage":
            concept.get(
                "ontology_damage",
                0.0,
            ),
        }

    def archetype_alignment(self, concept_a, concept_b):

        return self._jaccard(
            self._identity(
                concept_a,
            ).get(
                "archetypal_identity",
            ),
            self._identity(
                concept_b,
            ).get(
                "archetypal_identity",
            ),
        )

    def analyze_structural_compatibility(self, concept_a, concept_b):

        score = self._jaccard(
            self._identity(
                concept_a,
            ).get(
                "structural_identity",
            ),
            self._identity(
                concept_b,
            ).get(
                "structural_identity",
            ),
        )

        return {
            "structural_compatibility":
            score,

            "structural_state":
            (
                "structurally_compatible"
                if score >= 0.58
                else "structural_partial_overlap"
                if score >= 0.28
                else "structural_conflict"
            ),
        }

    def analyze_causal_compatibility(self, concept_a, concept_b):

        score = self._jaccard(
            self._identity(
                concept_a,
            ).get(
                "causal_identity",
            ),
            self._identity(
                concept_b,
            ).get(
                "causal_identity",
            ),
        )

        return {
            "causal_compatibility":
            score,

            "causal_state":
            (
                "causally_compatible"
                if score >= 0.58
                else "causal_partial_overlap"
                if score >= 0.28
                else "causal_conflict"
            ),
        }

    def compute_identity_distance(self, concept_a, concept_b):

        identity_a = self._identity(
            concept_a,
        )
        identity_b = self._identity(
            concept_b,
        )

        weights = {
            "local_identity":
            0.12,

            "structural_identity":
            0.26,

            "causal_identity":
            0.24,

            "archetypal_identity":
            0.24,

            "symbolic_identity":
            0.14,
        }

        layer_distances = {}

        for layer, weight in weights.items():

            similarity = self._jaccard(
                identity_a.get(
                    layer,
                ),
                identity_b.get(
                    layer,
                ),
            )

            layer_distances[
                layer
            ] = _clamp(
                1.0
                -
                similarity
            )

        identity_distance = _clamp(
            sum(
                layer_distances[layer]
                * weight
                for layer, weight in weights.items()
            )
        )

        return {
            "identity_distance":
            identity_distance,

            "layer_distances":
            layer_distances,

            "distance_state":
            (
                "identity_far"
                if identity_distance >= 0.62
                else "identity_near_with_conflict"
                if identity_distance >= 0.34
                else "identity_near"
            ),
        }

    def compute_identity_coherence(self, concept_a, concept_b):

        structural = self.analyze_structural_compatibility(
            concept_a,
            concept_b,
        )
        causal = self.analyze_causal_compatibility(
            concept_a,
            concept_b,
        )
        archetype = self.archetype_alignment(
            concept_a,
            concept_b,
        )
        distance = self.compute_identity_distance(
            concept_a,
            concept_b,
        )

        coherence = _clamp(
            structural.get(
                "structural_compatibility",
                0.0,
            )
            * 0.30
            +
            causal.get(
                "causal_compatibility",
                0.0,
            )
            * 0.28
            +
            archetype
            * 0.24
            +
            (
                1.0
                -
                distance.get(
                    "identity_distance",
                    0.0,
                )
            )
            * 0.18
        )

        return {
            "identity_coherence":
            coherence,

            "structural_analysis":
            structural,

            "causal_analysis":
            causal,

            "archetype_alignment":
            archetype,

            "identity_distance":
            distance,

            "coherence_state":
            (
                "coherent_identity_overlap"
                if coherence >= 0.62
                else "repairable_identity_overlap"
                if coherence >= 0.38
                else "incoherent_identity_overlap"
            ),
        }

    def analyze_identity_overlap(self, concept_a, concept_b):

        return {
            "source":
            self._concept_id(
                concept_a,
            ),

            "target":
            self._concept_id(
                concept_b,
            ),

            "coherence":
            self.compute_identity_coherence(
                concept_a,
                concept_b,
            ),
        }

    def detect_hidden_identity_conflicts(self, concept_a, concept_b):

        coherence = self.compute_identity_coherence(
            concept_a,
            concept_b,
        )

        layer_distances = (
            coherence.get(
                "identity_distance",
                {},
            ).get(
                "layer_distances",
                {},
            )
        )

        conflicts = [
            layer
            for layer, distance in layer_distances.items()
            if distance >= 0.72
        ]

        hidden = (
            coherence.get(
                "identity_coherence",
                0.0,
            )
            >= 0.38
            and bool(
                conflicts,
            )
        )

        return {
            "hidden_conflict_detected":
            hidden,

            "conflict_layers":
            conflicts,

            "hidden_conflict_state":
            (
                "hidden_identity_conflict"
                if hidden
                else "no_hidden_identity_conflict"
            ),
        }

    def explain_identity_failure(self, concept_a, concept_b):

        coherence = self.compute_identity_coherence(
            concept_a,
            concept_b,
        )
        hidden = self.detect_hidden_identity_conflicts(
            concept_a,
            concept_b,
        )

        reasons = []

        if coherence.get(
            "structural_analysis",
            {},
        ).get(
            "structural_state",
        ) == "structural_conflict":

            reasons.append(
                "structural_signature_conflict",
            )

        if coherence.get(
            "causal_analysis",
            {},
        ).get(
            "causal_state",
        ) == "causal_conflict":

            reasons.append(
                "causal_role_conflict",
            )

        if coherence.get(
            "archetype_alignment",
            0.0,
        ) < 0.28:

            reasons.append(
                "archetype_misalignment",
            )

        if (
            concept_a.get(
                "unsafe_merge_context",
                False,
            )
            or concept_b.get(
                "unsafe_merge_context",
                False,
            )
        ):

            reasons.append(
                "unsafe_merge_memory",
            )

        left_tokens = self._tokens(
            self._concept_id(
                concept_a,
            )
        )
        right_tokens = self._tokens(
            self._concept_id(
                concept_b,
            )
        )

        specialization_tokens = {
            "structural",
            "adaptive",
            "hybrid",
            "merged",
            "evolved",
        }

        if (
            left_tokens ^ right_tokens
        ) & specialization_tokens:

            reasons.append(
                "specialization_boundary_conflict",
            )

        reasons.extend(
            [
                f"hidden_{layer}_conflict"
                for layer in hidden.get(
                    "conflict_layers",
                    [],
                )
            ]
        )

        if not reasons:

            reasons.append(
                "identity_failure_not_detected",
            )

        return {
            "failure_reasons":
            reasons,

            "coherence":
            coherence,

            "hidden_conflicts":
            hidden,

            "failure_state":
            (
                "identity_failure_explained"
                if reasons
                != [
                    "identity_failure_not_detected",
                ]
                else "identity_compatible"
            ),
        }

    def generate_identity_repair_plan(self, failure_report):

        reasons = failure_report.get(
            "failure_reasons",
            [],
        )

        plan = []

        if "structural_signature_conflict" in reasons:

            plan.append(
                "split_structural_signature_from_meta_concept",
            )

        if "causal_role_conflict" in reasons:

            plan.append(
                "require_causal_rehearsal_before_merge",
            )

        if "archetype_misalignment" in reasons:

            plan.append(
                "block_archetype_fusion",
            )

        if any(
            reason.startswith(
                "hidden_",
            )
            for reason in reasons
        ):

            plan.append(
                "preserve_multi_layer_identity_boundaries",
            )

        if "unsafe_merge_memory" in reasons:

            plan.append(
                "block_merge_until_failure_memory_clears",
            )

        if "specialization_boundary_conflict" in reasons:

            plan.append(
                "track_parent_strategy_as_lineage_not_identity_merge",
            )

        if not plan:

            plan.append(
                "allow_guarded_identity_overlap",
            )

        return {
            "repair_actions":
            plan,

            "repair_state":
            (
                "repair_required"
                if plan
                != [
                    "allow_guarded_identity_overlap",
                ]
                else "repair_not_required"
            ),
        }

    def predict_merge_stability(self, concept_a, concept_b):

        coherence = self.compute_identity_coherence(
            concept_a,
            concept_b,
        )
        hidden = self.detect_hidden_identity_conflicts(
            concept_a,
            concept_b,
        )

        stability = _clamp(
            coherence.get(
                "identity_coherence",
                0.0,
            )
            -
            (
                0.22
                if hidden.get(
                    "hidden_conflict_detected",
                    False,
                )
                else 0.0
            )
            -
            (
                0.32
                if concept_a.get(
                    "unsafe_merge_context",
                    False,
                )
                or concept_b.get(
                    "unsafe_merge_context",
                    False,
                )
                else 0.0
            )
        )

        return {
            "merge_stability":
            stability,

            "merge_state":
            (
                "stable_merge"
                if stability >= 0.62
                else "repair_before_merge"
                if stability >= 0.38
                else "unstable_merge"
            ),
        }

    def _normalize_concept(self, concept):

        if not isinstance(
            concept,
            dict,
        ):

            return {
                "concept":
                concept,
            }

        if "type" in concept and "concept" not in concept:

            normalized = dict(
                concept,
            )
            normalized[
                "concept"
            ] = concept.get(
                "type",
            )
            normalized[
                "causal_role"
            ] = concept.get(
                "causal_effect",
                concept.get(
                    "primitive",
                    concept.get(
                        "type",
                    ),
                ),
            )
            normalized[
                "structural_signature"
            ] = concept.get(
                "geometric_grounding",
                {},
            ).get(
                "delta_type",
                concept.get(
                    "type",
                ),
            )
            return normalized

        return concept

    def _concepts_from_context(self, context):

        concepts = []

        for key in [
            "candidate_concepts",
            "concept_candidates",
            "active_concepts",
        ]:

            value = context.get(
                key,
                [],
            )

            if isinstance(
                value,
                list,
            ):

                concepts.extend(
                    value,
                )

        concepts.extend(
            context.get(
                "semantic_graph",
                {},
            ).get(
                "concept_nodes",
                [],
            )
        )

        for path in context.get(
            "search_result",
            {},
        ).get(
            "paths",
            [],
        ):

            concepts.extend(
                path.get(
                    "hypotheses",
                    [],
                )
            )

        evolved = context.get(
            "evolved_hypotheses",
            [],
        )

        if isinstance(
            evolved,
            dict,
        ):

            concepts.append(
                evolved,
            )

        elif isinstance(
            evolved,
            list,
        ):

            concepts.extend(
                evolved,
            )

        latest_failure = context.get(
            "cognitive_failure_memory",
            {},
        ).get(
            "latest_failure",
            {},
        )

        collapse_source = latest_failure.get(
            "collapse_source",
            "",
        )

        if "::" in collapse_source:

            left, right = collapse_source.split(
                "::",
                1,
            )

            concepts.extend([
                {
                    "concept":
                    left,

                    "unsafe_merge_context":
                    True,

                    "ontology_damage":
                    latest_failure.get(
                        "ontology_damage",
                        0.0,
                    ),
                },
                {
                    "concept":
                    right,

                    "unsafe_merge_context":
                    True,

                    "ontology_damage":
                    latest_failure.get(
                        "ontology_damage",
                        0.0,
                    ),
                },
            ])

        concepts.extend(
            context.get(
                "concept_fusion_report",
                {},
            ).get(
                "fused_concepts",
                [],
            )
        )

        normalized = []

        for concept in concepts:

            if isinstance(
                concept,
                dict,
            ):

                normalized.append(
                    self._normalize_concept(
                        concept.get(
                            "meta_concept",
                            concept,
                        )
                    )
                )

        return normalized

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        concepts = self._concepts_from_context(
            context,
        )

        analyses = []

        for index, concept_a in enumerate(
            concepts,
        ):

            for concept_b in concepts[
                index + 1:
            ]:

                failure = self.explain_identity_failure(
                    concept_a,
                    concept_b,
                )

                analyses.append({
                    "overlap":
                    self.analyze_identity_overlap(
                        concept_a,
                        concept_b,
                    ),

                    "failure_explanation":
                    failure,

                    "repair_plan":
                    self.generate_identity_repair_plan(
                        failure,
                    ),

                    "merge_stability":
                    self.predict_merge_stability(
                        concept_a,
                        concept_b,
                    ),
                })

        report = {
            "system":
            "identity_reasoner",

            "reasoning_mode":
            "identity_conflict_explanation_and_repair",

            "observed_concept_count":
            len(
                concepts,
            ),

            "identity_analyses":
            analyses,

            "repair_required_count":
            len([
                analysis
                for analysis in analyses
                if analysis.get(
                    "repair_plan",
                    {},
                ).get(
                    "repair_state",
                )
                == "repair_required"
            ]),

            "identity_reasoning_state":
            (
                "identity_repair_required"
                if any(
                    analysis.get(
                        "merge_stability",
                        {},
                    ).get(
                        "merge_state",
                    )
                    == "unstable_merge"
                    for analysis in analyses
                )
                else "identity_reasoning_active"
                if analyses
                else "no_identity_overlap_to_reason",
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.reasoning_history.append(
            report,
        )

        self.reasoning_history = (
            self.reasoning_history[-128:]
        )

        return report


identity_reasoner = IdentityReasoner()
