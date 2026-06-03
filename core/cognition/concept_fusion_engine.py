# ============================================
# NEXRYN CONCEPT FUSION ENGINE
# ============================================

from datetime import datetime


MAX_FUSIONS_PER_CYCLE = 24
MAX_LOG_ITEMS_PER_SECTION = 20


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


class ConceptFusionEngine:

    def __init__(self):

        self.fusion_history = []

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

    def _multi_layer_identity(self, concept):

        concept_id = self._concept_id(
            concept,
        )

        identity = concept.get(
            "identity",
            {},
        )

        local_identity = identity.get(
            "local_identity",
            concept_id,
        )

        structural_identity = identity.get(
            "structural_identity",
            concept.get(
                "structural_signature",
                concept.get(
                    "structure",
                    concept_id,
                ),
            ),
        )

        causal_identity = identity.get(
            "causal_identity",
            concept.get(
                "causal_role",
                concept.get(
                    "causal_signature",
                    concept_id,
                ),
            ),
        )

        archetypal_identity = identity.get(
            "archetypal_identity",
            concept.get(
                "archetype",
                self._infer_archetype(
                    concept_id,
                ),
            ),
        )

        symbolic_identity = identity.get(
            "symbolic_identity",
            concept.get(
                "symbolic_signature",
                concept_id,
            ),
        )

        return {
            "local_identity":
            local_identity,

            "structural_identity":
            structural_identity,

            "causal_identity":
            causal_identity,

            "archetypal_identity":
            archetypal_identity,

            "symbolic_identity":
            symbolic_identity,
        }

    def _infer_archetype(self, concept_id):

        tokens = self._tokens(
            concept_id,
        )

        if "object" in tokens and "size" in tokens:

            return "object_spatial_magnitude"

        if "motion" in tokens or "shift" in tokens:

            return "spatial_causality"

        if "identity" in tokens:

            return "identity_preservation"

        return "general_concept"

    def compute_semantic_similarity(self, concept_a, concept_b):

        identity_a = self._multi_layer_identity(
            concept_a,
        )

        identity_b = self._multi_layer_identity(
            concept_b,
        )

        layer_scores = {}

        weights = {
            "local_identity":
            0.14,

            "structural_identity":
            0.26,

            "causal_identity":
            0.22,

            "archetypal_identity":
            0.24,

            "symbolic_identity":
            0.14,
        }

        for layer, weight in weights.items():

            layer_scores[
                layer
            ] = self._jaccard(
                identity_a.get(
                    layer,
                ),
                identity_b.get(
                    layer,
                ),
            )

        hierarchical_similarity = _clamp(
            sum(
                layer_scores[layer]
                * weight
                for layer, weight in weights.items()
            )
        )

        surface_similarity = self._jaccard(
            self._concept_id(
                concept_a,
            ),
            self._concept_id(
                concept_b,
            ),
        )

        return {
            "surface_similarity":
            surface_similarity,

            "hierarchical_similarity":
            hierarchical_similarity,

            "layer_scores":
            layer_scores,

            "identity_a":
            identity_a,

            "identity_b":
            identity_b,
        }

    def compute_structural_compatibility(self, concept_a, concept_b):

        identity_a = self._multi_layer_identity(
            concept_a,
        )

        identity_b = self._multi_layer_identity(
            concept_b,
        )

        structural = self._jaccard(
            identity_a.get(
                "structural_identity",
            ),
            identity_b.get(
                "structural_identity",
            ),
        )

        archetypal = self._jaccard(
            identity_a.get(
                "archetypal_identity",
            ),
            identity_b.get(
                "archetypal_identity",
            ),
        )

        return _clamp(
            structural * 0.62
            +
            archetypal * 0.38
        )

    def compute_causal_compatibility(self, concept_a, concept_b):

        identity_a = self._multi_layer_identity(
            concept_a,
        )

        identity_b = self._multi_layer_identity(
            concept_b,
        )

        causal = self._jaccard(
            identity_a.get(
                "causal_identity",
            ),
            identity_b.get(
                "causal_identity",
            ),
        )

        symbolic = self._jaccard(
            identity_a.get(
                "symbolic_identity",
            ),
            identity_b.get(
                "symbolic_identity",
            ),
        )

        return _clamp(
            causal * 0.72
            +
            symbolic * 0.28
        )

    def detect_concept_overlap(self, concepts=None):

        if concepts is None:

            concepts = []

        overlaps = []
        seen_fusions = set()

        for index, concept_a in enumerate(
            concepts,
        ):

            if len(
                overlaps,
            ) >= MAX_FUSIONS_PER_CYCLE:

                break

            for concept_b in concepts[
                index + 1:
            ]:

                if len(
                    overlaps,
                ) >= MAX_FUSIONS_PER_CYCLE:

                    break

                fusion_key = tuple(
                    sorted([
                        str(
                            self._concept_id(
                                concept_a,
                            )
                        ),
                        str(
                            self._concept_id(
                                concept_b,
                            )
                        ),
                    ])
                )

                if fusion_key[0] == fusion_key[1]:

                    continue

                if fusion_key in seen_fusions:

                    continue

                seen_fusions.add(
                    fusion_key,
                )

                semantic = self.compute_semantic_similarity(
                    concept_a,
                    concept_b,
                )

                structural = self.compute_structural_compatibility(
                    concept_a,
                    concept_b,
                )

                causal = self.compute_causal_compatibility(
                    concept_a,
                    concept_b,
                )

                overlap_score = _clamp(
                    semantic.get(
                        "hierarchical_similarity",
                        0.0,
                    )
                    * 0.46
                    +
                    structural * 0.30
                    +
                    causal * 0.24
                )

                if overlap_score >= 0.34:

                    overlaps.append({
                        "source":
                        self._concept_id(
                            concept_a,
                        ),

                        "target":
                        self._concept_id(
                            concept_b,
                        ),

                        "source_concept":
                        concept_a,

                        "target_concept":
                        concept_b,

                        "semantic_similarity":
                        semantic,

                        "structural_compatibility":
                        structural,

                        "causal_compatibility":
                        causal,

                        "overlap_score":
                        overlap_score,
                    })

        return overlaps

    def resolve_identity_conflict(self, overlap):

        semantic = overlap.get(
            "semantic_similarity",
            {},
        )

        structural = overlap.get(
            "structural_compatibility",
            0.0,
        )

        causal = overlap.get(
            "causal_compatibility",
            0.0,
        )

        conflict_score = _clamp(
            (
                1.0
                -
                structural
            )
            * 0.38
            +
            (
                1.0
                -
                causal
            )
            * 0.32
            +
            (
                1.0
                -
                semantic.get(
                    "hierarchical_similarity",
                    0.0,
                )
            )
            * 0.30
        )

        return {
            "conflict_score":
            conflict_score,

            "conflict_state":
            (
                "identity_conflict"
                if conflict_score >= 0.58
                else "resolvable_difference"
                if conflict_score >= 0.32
                else "identity_compatible"
            ),
        }

    def generate_meta_concept(self, overlap):

        source = overlap.get(
            "source_concept",
            {},
        )

        target = overlap.get(
            "target_concept",
            {},
        )

        identity_a = self._multi_layer_identity(
            source,
        )

        identity_b = self._multi_layer_identity(
            target,
        )

        source_id = overlap.get(
            "source",
            self._concept_id(
                source,
            ),
        )

        target_id = overlap.get(
            "target",
            self._concept_id(
                target,
            ),
        )

        shared_tokens = sorted(
            self._tokens(
                source_id,
            )
            &
            self._tokens(
                target_id,
            )
        )

        if shared_tokens:

            meta_id = "_".join(
                shared_tokens,
            )

        else:

            meta_id = (
                f"meta_{source_id}_{target_id}"
            )

        if "object" in self._tokens(source_id) | self._tokens(target_id):

            if "size" in self._tokens(source_id) | self._tokens(target_id):

                meta_id = "object_size"

        return {
            "meta_concept_id":
            meta_id,

            "source_concepts":
            [
                source_id,
                target_id,
            ],

            "identity":
            {
                "local_identity":
                meta_id,

                "structural_identity":
                [
                    identity_a.get(
                        "structural_identity",
                    ),
                    identity_b.get(
                        "structural_identity",
                    ),
                ],

                "causal_identity":
                [
                    identity_a.get(
                        "causal_identity",
                    ),
                    identity_b.get(
                        "causal_identity",
                    ),
                ],

                "archetypal_identity":
                identity_a.get(
                    "archetypal_identity",
                )
                if self._jaccard(
                    identity_a.get(
                        "archetypal_identity",
                    ),
                    identity_b.get(
                        "archetypal_identity",
                    ),
                )
                >= 0.34
                else [
                    identity_a.get(
                        "archetypal_identity",
                    ),
                    identity_b.get(
                        "archetypal_identity",
                    ),
                ],

                "symbolic_identity":
                sorted(
                    self._tokens(
                        identity_a.get(
                            "symbolic_identity",
                        ),
                    )
                    |
                    self._tokens(
                        identity_b.get(
                            "symbolic_identity",
                        ),
                    )
                ),
            },

            "fusion_origin":
            "concept_fusion_engine",
        }

    def fusion_stability_score(self, overlap, conflict_report):

        return _clamp(
            overlap.get(
                "overlap_score",
                0.0,
            )
            * 0.48
            +
            overlap.get(
                "structural_compatibility",
                0.0,
            )
            * 0.20
            +
            overlap.get(
                "causal_compatibility",
                0.0,
            )
            * 0.20
            +
            (
                1.0
                -
                conflict_report.get(
                    "conflict_score",
                    0.0,
                )
            )
            * 0.12
        )

    def reject_unstable_fusion(self, fusion_report):

        return (
            fusion_report.get(
                "fusion_stability",
                0.0,
            )
            < 0.46
            or fusion_report.get(
                "identity_conflict",
                {},
            ).get(
                "conflict_state",
            )
            == "identity_conflict"
        )

    def stabilize_fused_identity(self, meta_concept, stability):

        stabilized = dict(
            meta_concept,
        )

        stabilized[
            "fusion_stability"
        ] = stability

        stabilized[
            "identity_state"
        ] = (
            "stable_fused_identity"
            if stability >= 0.62
            else "probationary_fused_identity"
        )

        stabilized[
            "commit_policy"
        ] = (
            "allow_meta_concept"
            if stability >= 0.62
            else "sandbox_meta_concept"
        )

        return stabilized

    def build_meta_representation(self, concepts=None):

        overlaps = self.detect_concept_overlap(
            concepts,
        )

        fused = []
        rejected = []
        seen_meta_concepts = set()

        for overlap in overlaps:

            if (
                len(
                    fused,
                )
                +
                len(
                    rejected,
                )
                >= MAX_FUSIONS_PER_CYCLE
            ):

                break

            conflict = self.resolve_identity_conflict(
                overlap,
            )

            meta_concept = self.generate_meta_concept(
                overlap,
            )

            meta_concept_id = meta_concept.get(
                "meta_concept_id",
            )

            if meta_concept_id in seen_meta_concepts:

                continue

            seen_meta_concepts.add(
                meta_concept_id,
            )

            stability = self.fusion_stability_score(
                overlap,
                conflict,
            )

            fusion_report = {
                "overlap":
                overlap,

                "identity_conflict":
                conflict,

                "meta_concept":
                meta_concept,

                "fusion_stability":
                stability,
            }

            if self.reject_unstable_fusion(
                fusion_report,
            ):

                rejected.append(
                    fusion_report,
                )

            else:

                fusion_report[
                    "meta_concept"
                ] = self.stabilize_fused_identity(
                    meta_concept,
                    stability,
                )

                fused.append(
                    fusion_report,
                )

        return {
            "detected_overlaps":
            overlaps[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "fused_concepts":
            fused[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "rejected_fusions":
            rejected[
                :MAX_LOG_ITEMS_PER_SECTION
            ],

            "fusion_count":
            len(
                fused,
            ),

            "rejected_count":
            len(
                rejected,
            ),
        }

    def _concepts_from_context(self, context):

        candidates = []

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

                candidates.extend(
                    value,
                )

        for concept in context.get(
            "conceptive_neurogenesis_report",
            {},
        ).get(
            "generated_concepts",
            [],
        ):

            candidates.append(
                concept,
            )

        for concept in context.get(
            "semantic_operating_system_report",
            {},
        ).get(
            "virtual_semantic_memory",
            {},
        ).get(
            "loaded_concepts",
            [],
        ):

            candidates.append(
                concept,
            )

        sandboxed_events = (
            context.get(
                "semantic_firewall_report",
                {},
            )
            .get(
                "concept_sandboxing",
                {},
            )
            .get(
                "sandboxed_events",
                [],
            )
        )

        for event in sandboxed_events:

            source = event.get(
                "source",
                {},
            )

            for key in [
                "first",
                "second",
                "concept",
            ]:

                if source.get(
                    key,
                ):

                    candidates.append({
                        "concept":
                        source.get(
                            key,
                        ),
                    })

        normalized = []

        for item in candidates:

            if isinstance(
                item,
                dict,
            ):

                normalized.append(
                    item,
                )

            else:

                normalized.append({
                    "concept":
                    item,
                })

        return normalized

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        if context.get(
            "freeze_new_fusions",
            False,
        ):

            return {
                "system":
                "concept_fusion_engine",

                "fusion_mode":
                "multi_layer_identity_meta_concept_resolution",

                "observed_concept_count":
                0,

                "meta_representation":
                {
                    "detected_overlaps":
                    [],

                    "fused_concepts":
                    [],

                    "rejected_fusions":
                    [],

                    "fusion_count":
                    0,

                    "rejected_count":
                    0,
                },

                "fused_concepts":
                [],

                "rejected_fusions":
                [],

                "fusion_state":
                "fusions_frozen_by_entropy_kill_switch",

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            }

        concepts = self._concepts_from_context(
            context,
        )

        representation = self.build_meta_representation(
            concepts,
        )

        report = {
            "system":
            "concept_fusion_engine",

            "fusion_mode":
            "multi_layer_identity_meta_concept_resolution",

            "observed_concept_count":
            len(
                concepts,
            ),

            "meta_representation":
            representation,

            "fused_concepts":
            representation.get(
                "fused_concepts",
                [],
            ),

            "rejected_fusions":
            representation.get(
                "rejected_fusions",
                [],
            ),

            "fusion_state":
            (
                "meta_concepts_available"
                if representation.get(
                    "fusion_count",
                    0,
                )
                else "fusion_rejected_unstable"
                if representation.get(
                    "rejected_count",
                    0,
                )
                else "no_concept_overlap"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.fusion_history.append(
            report,
        )

        self.fusion_history = (
            self.fusion_history[-128:]
        )

        return report


concept_fusion_engine = ConceptFusionEngine()
