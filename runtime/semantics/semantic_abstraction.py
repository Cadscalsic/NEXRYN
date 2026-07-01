# ============================================
# NEXRYN SEMANTIC ABSTRACTION ENGINE
# ============================================

from runtime.semantics.semantic_ontology import (
    lookup_hypothesis_concept,
    lookup_operator_semantics,
    validate_semantic_consistency,
    compress_semantic_concept,
    compression_level_for_concept,
    semantic_compression_allowed
)


# ============================================
# SEMANTIC ABSTRACTION ENGINE
# ============================================

class SemanticAbstractionEngine:

    def __init__(self):

        self.generic_fallback_count = 0

        self.ontology_hits = 0

    # ============================================
    # EVIDENCE-AWARE PRIMITIVE CLASSIFICATION
    # ============================================

    def _numeric_signal(
        self,
        hypothesis,
        *keys
    ):

        grounding = hypothesis.get(
            "geometric_grounding",
            {}
        )

        if not isinstance(
            grounding,
            dict
        ):

            grounding = {}

        for source in (
            hypothesis,
            grounding
        ):

            for key in keys:

                try:

                    value = source.get(
                        key
                    )

                    if value is not None:

                        return float(
                            value
                        )

                except (AttributeError, TypeError, ValueError):

                    continue

        return None

    def _count_delta_from_evidence(
        self,
        hypothesis,
        evidence_context=None
    ):

        shared_evidence = self._shared_task_evidence(
            evidence_context
        )

        if (
            shared_evidence
            and
            shared_evidence.get(
                "object_count_delta"
            ) is not None
        ):

            return shared_evidence.get(
                "object_count_delta"
            )

        context_delta = self._count_delta_from_context(
            evidence_context
        )

        if context_delta is not None:

            return context_delta

        input_count = self._numeric_signal(
            hypothesis,
            "input_count",
            "input_object_count"
        )

        output_count = self._numeric_signal(
            hypothesis,
            "output_count",
            "output_object_count"
        )

        if (
            input_count is not None
            and
            output_count is not None
        ):

            return output_count - input_count

        delta = self._numeric_signal(
            hypothesis,
            "object_count_delta"
        )

        if delta is not None:

            return delta

        return None

    def _shared_task_evidence(
        self,
        evidence_context
    ):

        if not isinstance(
            evidence_context,
            dict
        ):

            return {}

        evidence = evidence_context.get(
            "__task_evidence__",
            {}
        )

        if isinstance(
            evidence,
            dict
        ):

            return evidence

        return {}

    def _count_delta_from_context(
        self,
        evidence_context
    ):

        if not isinstance(
            evidence_context,
            dict
        ):

            return None

        input_summary = evidence_context.get(
            "input_summary",
            {}
        )

        output_summary = evidence_context.get(
            "output_summary",
            {}
        )

        if not isinstance(
            input_summary,
            dict
        ):

            input_summary = {}

        if not isinstance(
            output_summary,
            dict
        ):

            output_summary = {}

        input_count = input_summary.get(
            "object_count"
        )

        output_count = output_summary.get(
            "object_count"
        )

        if (
            input_count is None
            or
            output_count is None
        ):

            input_count = self._pattern_value(
                evidence_context,
                "input_object_count"
            )

            output_count = self._pattern_value(
                evidence_context,
                "output_object_count"
            )

        if (
            input_count is None
            or
            output_count is None
        ):

            object_rule = self._rule_record(
                evidence_context,
                "object_change"
            )

            input_count = object_rule.get(
                "input_count",
                input_count
            )

            output_count = object_rule.get(
                "output_count",
                output_count
            )

        if (
            input_count is None
            or
            output_count is None
        ):

            input_objects = evidence_context.get(
                "input_object_summaries",
                evidence_context.get(
                    "input_objects"
                )
            )

            output_objects = evidence_context.get(
                "output_object_summaries",
                evidence_context.get(
                    "output_objects"
                )
            )

            if isinstance(
                input_objects,
                list
            ) and isinstance(
                output_objects,
                list
            ):

                input_count = len(
                    input_objects
                )

                output_count = len(
                    output_objects
                )

        try:

            if (
                input_count is not None
                and
                output_count is not None
            ):

                return float(output_count) - float(input_count)

        except (TypeError, ValueError):

            return None

        return None

    def _pattern_value(
        self,
        evidence_context,
        pattern_name
    ):

        if not isinstance(
            evidence_context,
            dict
        ):

            return None

        for pattern in evidence_context.get(
            "patterns",
            []
        ) or []:

            if not isinstance(
                pattern,
                dict
            ):

                continue

            if pattern.get(
                "pattern"
            ) == pattern_name:

                return pattern.get(
                    "value"
                )

        return None

    def _rule_record(
        self,
        evidence_context,
        rule_name
    ):

        if not isinstance(
            evidence_context,
            dict
        ):

            return {}

        for rule in evidence_context.get(
            "rules",
            []
        ) or []:

            if not isinstance(
                rule,
                dict
            ):

                continue

            if rule.get(
                "rule"
            ) == rule_name:

                return rule

        return {}

    def _density_delta_from_context(
        self,
        evidence_context
    ):

        shared_evidence = self._shared_task_evidence(
            evidence_context
        )

        if (
            shared_evidence
            and
            shared_evidence.get(
                "density_delta"
            ) is not None
        ):

            return shared_evidence.get(
                "density_delta"
            )

        if not isinstance(
            evidence_context,
            dict
        ):

            return None

        input_summary = evidence_context.get(
            "input_summary",
            {}
        )

        output_summary = evidence_context.get(
            "output_summary",
            {}
        )

        if not isinstance(
            input_summary,
            dict
        ):

            input_summary = {}

        if not isinstance(
            output_summary,
            dict
        ):

            output_summary = {}

        input_density = input_summary.get(
            "density"
        )

        output_density = output_summary.get(
            "density"
        )

        if (
            input_density is None
            or
            output_density is None
        ):

            density_pattern = self._pattern_value(
                evidence_context,
                "density_change"
            )

            if isinstance(
                density_pattern,
                dict
            ):

                input_density = density_pattern.get(
                    "input_density",
                    input_density
                )

                output_density = density_pattern.get(
                    "output_density",
                    output_density
                )

                difference = density_pattern.get(
                    "difference"
                )

                if difference is not None:

                    try:

                        return float(
                            difference
                        )

                    except (TypeError, ValueError):

                        pass

        if (
            input_density is None
            or
            output_density is None
        ):

            density_rule = self._rule_record(
                evidence_context,
                "density_change"
            )

            input_density = density_rule.get(
                "input_density",
                input_density
            )

            output_density = density_rule.get(
                "output_density",
                output_density
            )

            difference = density_rule.get(
                "difference"
            )

            if difference is not None:

                try:

                    return float(
                        difference
                    )

                except (TypeError, ValueError):

                    pass

        try:

            if (
                input_density is not None
                and
                output_density is not None
            ):

                return float(output_density) - float(input_density)

        except (TypeError, ValueError):

            return None

        return None

    def _symmetry_changed_from_context(
        self,
        evidence_context
    ):

        shared_evidence = self._shared_task_evidence(
            evidence_context
        )

        if (
            shared_evidence
            and
            shared_evidence.get(
                "symmetry_changed"
            ) is not None
        ):

            return shared_evidence.get(
                "symmetry_changed"
            )

        if not isinstance(
            evidence_context,
            dict
        ):

            return None

        symmetry_pattern = self._pattern_value(
            evidence_context,
            "symmetry_changes"
        )

        if isinstance(
            symmetry_pattern,
            dict
        ):

            input_horizontal = symmetry_pattern.get(
                "input_horizontal"
            )

            output_horizontal = symmetry_pattern.get(
                "output_horizontal"
            )

            input_vertical = symmetry_pattern.get(
                "input_vertical"
            )

            output_vertical = symmetry_pattern.get(
                "output_vertical"
            )

            if (
                input_horizontal is not None
                and
                output_horizontal is not None
                and
                input_horizontal != output_horizontal
            ):

                return True

            if (
                input_vertical is not None
                and
                output_vertical is not None
                and
                input_vertical != output_vertical
            ):

                return True

        symmetry_rule = self._rule_record(
            evidence_context,
            "symmetry_change"
        )

        if symmetry_rule:

            input_horizontal = symmetry_rule.get(
                "input_horizontal"
            )

            output_horizontal = symmetry_rule.get(
                "output_horizontal"
            )

            input_vertical = symmetry_rule.get(
                "input_vertical"
            )

            output_vertical = symmetry_rule.get(
                "output_vertical"
            )

            return bool(
                input_horizontal != output_horizontal
                or
                input_vertical != output_vertical
            )

        return None

    def classify_transformation_primitive(
        self,
        hypothesis,
        primitive,
        evidence_context=None
    ):

        hypothesis_type = str(
            hypothesis.get(
                "type",
                ""
            )
        )

        count_delta = self._count_delta_from_evidence(
            hypothesis,
            evidence_context=evidence_context
        )

        if (
            count_delta is not None
            and
            (
                "object_count" in hypothesis_type
                or
                primitive == "preserve_objects"
            )
        ):

            if count_delta > 0:

                return (
                    "duplicate_object",
                    "object_count_increase"
                )

            if count_delta < 0:

                return (
                    "remove_object",
                    "object_count_decrease"
                )

        density_delta = self._numeric_signal(
            hypothesis,
            "density_delta"
        )

        if density_delta is None:

            density_delta = self._density_delta_from_context(
                evidence_context
            )

        if (
            density_delta is not None
            and
            (
                "density" in hypothesis_type
                or
                primitive == "preserve_density"
            )
        ):

            if density_delta > 0:

                if count_delta == 0:

                    return (
                        "expand_object",
                        "stable_count_density_growth"
                    )

                return (
                    "expand_pattern",
                    "density_increase"
                )

            if density_delta < 0:

                return (
                    "reduce_pattern",
                    "density_decrease"
                )

        size_delta = self._numeric_signal(
            hypothesis,
            "size_delta",
            "object_size_delta"
        )

        if size_delta is None:

            input_size = self._numeric_signal(
                hypothesis,
                "input_total_size"
            )

            output_size = self._numeric_signal(
                hypothesis,
                "output_total_size"
            )

            if (
                input_size is not None
                and
                output_size is not None
            ):

                size_delta = output_size - input_size

        if (
            size_delta is not None
            and
            (
                "size" in hypothesis_type
                or
                primitive == "preserve_size"
            )
        ):

            if size_delta > 0:

                return (
                    "expand_object",
                    "object_size_increase"
                )

            if size_delta < 0:

                return (
                    "shrink_object",
                    "object_size_decrease"
                )

        return (
            primitive,
            None
        )

    def validate_transformation_semantics(
        self,
        hypothesis,
        causal_effect,
        evidence_context=None
    ):

        contradictions = []

        count_delta = self._count_delta_from_evidence(
            hypothesis,
            evidence_context=evidence_context
        )

        if (
            count_delta is not None
            and
            count_delta != 0
            and
            causal_effect == "preserve_object_count"
        ):

            contradictions.append(
                "object_count_changed_but_preserve_object_count"
            )

        density_delta = self._numeric_signal(
            hypothesis,
            "density_delta"
        )

        if density_delta is None:

            density_delta = self._density_delta_from_context(
                evidence_context
            )

        if (
            density_delta is not None
            and
            density_delta != 0
            and
            causal_effect == "preserve_density"
        ):

            contradictions.append(
                "density_changed_but_preserve_density"
            )

        size_delta = self._numeric_signal(
            hypothesis,
            "size_delta",
            "object_size_delta"
        )

        if size_delta is None:

            input_size = self._numeric_signal(
                hypothesis,
                "input_total_size"
            )

            output_size = self._numeric_signal(
                hypothesis,
                "output_total_size"
            )

            if (
                input_size is not None
                and
                output_size is not None
            ):

                size_delta = output_size - input_size

        if (
            size_delta is not None
            and
            size_delta != 0
            and
            causal_effect == "preserve_area"
        ):

            contradictions.append(
                "object_size_changed_but_preserve_area"
            )

        symmetry_changed = self._symmetry_changed_from_context(
            evidence_context
        )

        if (
            symmetry_changed is True
            and
            causal_effect == "preserve_symmetry"
        ):

            contradictions.append(
                "symmetry_changed_but_preserve_symmetry"
            )

        return {
            "system": "transformation_semantic_validator",
            "semantic_valid": not contradictions,
            "contradictions": contradictions,
        }

    def extract_transformation_evidence(
        self,
        hypothesis,
        evidence_context=None
    ):

        shared_evidence = self._shared_task_evidence(
            evidence_context
        )

        if shared_evidence:

            return dict(
                shared_evidence
            )

        count_delta = self._count_delta_from_evidence(
            hypothesis,
            evidence_context=evidence_context
        )

        density_delta = self._numeric_signal(
            hypothesis,
            "density_delta"
        )

        if density_delta is None:

            density_delta = self._density_delta_from_context(
                evidence_context
            )

        size_delta = self._numeric_signal(
            hypothesis,
            "size_delta",
            "object_size_delta"
        )

        if size_delta is None:

            input_size = self._numeric_signal(
                hypothesis,
                "input_total_size"
            )

            output_size = self._numeric_signal(
                hypothesis,
                "output_total_size"
            )

            if (
                input_size is not None
                and
                output_size is not None
            ):

                size_delta = output_size - input_size

        symmetry_changed = self._symmetry_changed_from_context(
            evidence_context
        )

        return {
            "object_count_delta": count_delta,
            "object_count_changed": (
                None
                if count_delta is None
                else count_delta != 0
            ),
            "object_count_direction": (
                "increase"
                if count_delta is not None and count_delta > 0
                else "decrease"
                if count_delta is not None and count_delta < 0
                else "stable"
                if count_delta == 0
                else "unknown"
            ),
            "density_delta": density_delta,
            "density_changed": (
                None
                if density_delta is None
                else density_delta != 0
            ),
            "object_size_delta": size_delta,
            "object_size_changed": (
                None
                if size_delta is None
                else size_delta != 0
            ),
            "symmetry_changed": symmetry_changed,
        }

    def enforce_evidence_semantic_consistency(
        self,
        abstraction,
        evidence
    ):

        contradictions = list(
            abstraction.get(
                "semantic_contradictions",
                []
            )
        )

        causal_effect = abstraction.get(
            "causal_effect"
        )

        semantic_concept = abstraction.get(
            "semantic_concept"
        )

        primitive = abstraction.get(
            "primitive"
        )

        count_delta = evidence.get(
            "object_count_delta"
        )

        if (
            count_delta is not None
            and
            count_delta != 0
            and
            (
                causal_effect == "preserve_object_count"
                or
                semantic_concept == "object_identity_preservation"
                or
                primitive == "preserve_objects"
            )
        ):

            contradictions.append(
                "object_count_changed_but_object_identity_preservation"
            )

        density_delta = evidence.get(
            "density_delta"
        )

        if (
            density_delta is not None
            and
            density_delta != 0
            and
            causal_effect == "preserve_density"
        ):

            contradictions.append(
                "density_changed_but_preserve_density"
            )

        size_delta = evidence.get(
            "object_size_delta"
        )

        if (
            size_delta is not None
            and
            size_delta != 0
            and
            causal_effect == "preserve_area"
        ):

            contradictions.append(
                "object_size_changed_but_preserve_area"
            )

        if (
            evidence.get(
                "symmetry_changed"
            ) is True
            and
            causal_effect == "preserve_symmetry"
        ):

            contradictions.append(
                "symmetry_changed_but_preserve_symmetry"
            )

        contradictions = list(
            dict.fromkeys(
                contradictions
            )
        )

        if contradictions:

            abstraction[
                "semantic_valid"
            ] = False

            abstraction[
                "semantic_consistency"
            ] = False

            abstraction[
                "semantic_penalty"
            ] = max(
                abstraction.get(
                    "semantic_penalty",
                    0
                ),
                1
            )

            abstraction[
                "semantic_consistency_reason"
            ] = "semantic_evidence_contradiction"

        abstraction[
            "semantic_contradictions"
        ] = contradictions

        abstraction[
            "semantic_evidence"
        ] = evidence

        return abstraction

    # ============================================
    # ABSTRACT HYPOTHESIS
    # ============================================

    def abstract_hypothesis(

        self,

        hypothesis,

        evidence_context=None
    ):

        if not isinstance(
            hypothesis,
            dict
        ):

            hypothesis = {}

        hypothesis_type = hypothesis.get(
            "type",
            "unknown"
        )

        primitive = hypothesis.get(
            "primitive"
        )

        original_primitive = primitive

        primitive, reclassification_reason = (
            self.classify_transformation_primitive(
                hypothesis,
                primitive,
                evidence_context=evidence_context
            )
        )

        operator_semantics = lookup_operator_semantics(
            primitive
        )

        if operator_semantics:

            semantic_concept = operator_semantics.get(
                "semantic_concept",
                "generic_transformation"
            )

            category = operator_semantics.get(
                "category",
                "unknown"
            )

            causal_effect = operator_semantics.get(
                "causal_effect",
                "unknown"
            )

            spatial_effect = operator_semantics.get(
                "spatial_effect",
                "unknown"
            )

            semantic_class = operator_semantics.get(
                "semantic_class",
                "unknown"
            )

            self.ontology_hits += 1

        else:

            semantic_concept = lookup_hypothesis_concept(
                hypothesis_type
            )

            category = hypothesis.get(
                "category",
                "unknown"
            )

            causal_effect = hypothesis.get(
                "causal_effect",
                "unknown"
            )

            spatial_effect = hypothesis.get(
                "spatial_effect",
                "unknown"
            )

            semantic_class = hypothesis.get(
                "semantic_class",
                "unknown"
            )

            if semantic_concept == "generic_transformation":

                self.generic_fallback_count += 1

        consistency = validate_semantic_consistency(
            primitive,
            semantic_concept,
            category,
            semantic_class
        )

        semantic_validation = self.validate_transformation_semantics(
            hypothesis,
            causal_effect,
            evidence_context=evidence_context
        )

        if not semantic_validation.get(
            "semantic_valid",
            True
        ):

            consistency = {
                **consistency,
                "consistent": False,
                "penalty": max(
                    consistency.get(
                        "penalty",
                        0
                    ),
                    1
                ),
                "reason": "semantic_evidence_contradiction",
            }

        compression_level = compression_level_for_concept(
            semantic_concept
        )

        evidence = self.extract_transformation_evidence(
            hypothesis,
            evidence_context=evidence_context
        )

        abstraction = {

            "original_type":
            hypothesis_type,

            "primitive":
            primitive,

            "original_primitive":
            original_primitive,

            "semantic_reclassification_reason":
            reclassification_reason,

            "semantic_concept":
            semantic_concept,

            "compressed_concept":
            compression_level.local_identity,

            "local_identity":
            compression_level.local_identity,

            "structural_identity":
            compression_level.structural_identity,

            "causal_identity":
            compression_level.causal_identity,

            "archetypal_identity":
            compression_level.archetypal_identity,

            "topology_signature":
            compression_level.topology_signature,

            "confidence":
            hypothesis.get(
                "confidence",
                0.0
            ),

            "category":
            category,

            "causal_effect":
            causal_effect,

            "spatial_effect":
            spatial_effect,

            "semantic_class":
            semantic_class,

            "semantic_consistency":
            consistency.get(
                "consistent",
                True
            ),

            "semantic_penalty":
            consistency.get(
                "penalty",
                0
            ),

            "semantic_consistency_reason":
            consistency.get(
                "reason",
                "unknown"
            ),

            "semantic_evidence_scope":
            (
                "task_context"
                if isinstance(evidence_context, dict)
                else "hypothesis"
            ),

            "semantic_validator":
            semantic_validation.get(
                "system"
            ),

            "semantic_valid":
            semantic_validation.get(
                "semantic_valid",
                True
            ),

            "semantic_contradictions":
            semantic_validation.get(
                "contradictions",
                []
            )
        }

        return self.enforce_evidence_semantic_consistency(
            abstraction,
            evidence
        )

    # ============================================
    # INFER RELATION
    # ============================================

    def infer_relation(
        self,
        previous,
        current
    ):

        if not previous.get(
            "semantic_consistency",
            True
        ) or not current.get(
            "semantic_consistency",
            True
        ):

            return "contradicts"

        previous_effect = previous.get(
            "causal_effect"
        )

        current_effect = current.get(
            "causal_effect"
        )

        previous_category = previous.get(
            "category"
        )

        current_category = current.get(
            "category"
        )

        previous_class = previous.get(
            "semantic_class"
        )

        current_class = current.get(
            "semantic_class"
        )

        if previous_category == "stability" and current_category != "stability":

            return "inhibits"

        if previous_category != "stability" and current_category == "stability":

            return "depends_on"

        if previous_effect == current_effect and previous_effect != "unknown":

            return "causes"

        if previous_category == current_category and previous_category != "unknown":

            return "enables"

        if previous_class == current_class and previous_class != "unknown":

            return "specializes"

        return "semantic_sequence"

    # ============================================
    # EDGE METRICS
    # ============================================

    def build_edge_metrics(
        self,
        previous,
        current,
        relation
    ):

        shared = 0

        for key in [
            "category",
            "causal_effect",
            "semantic_class",
            "compressed_concept"
        ]:

            if previous.get(key) == current.get(key):

                shared += 1

        semantic_distance = round(
            1.0 - (shared / 4),
            4
        )

        relation_weights = {
            "causes": 0.95,
            "enables": 0.80,
            "depends_on": 0.70,
            "specializes": 0.65,
            "inhibits": 0.45,
            "contradicts": 0.10,
            "semantic_sequence": 0.50
        }

        edge_weight = relation_weights.get(
            relation,
            0.50
        )

        causal_strength = round(
            edge_weight
            *
            (1.0 - semantic_distance * 0.5),
            4
        )

        activation_energy = round(
            semantic_distance
            +
            (
                1.0 - edge_weight
            ),
            4
        )

        return {
            "edge_weight": round(edge_weight, 4),
            "causal_strength": causal_strength,
            "semantic_distance": semantic_distance,
            "activation_energy": activation_energy
        }

    # ============================================
    # ADAPTIVE COMPRESSION
    # ============================================

    def apply_adaptive_compression(
        self,
        concept_nodes
    ):

        previous_node = None

        for node in concept_nodes:

            semantic_distance = 1.0

            if previous_node is not None:

                relation = self.infer_relation(
                    previous_node,
                    node
                )

                metrics = self.build_edge_metrics(
                    previous_node,
                    node,
                    relation
                )

                semantic_distance = metrics.get(
                    "semantic_distance",
                    1.0
                )

            node[
                "compressed_concept"
            ] = node.get(
                "local_identity",
                node.get(
                    "concept"
                )
            )

            compression_decision = {
                "allowed": False,
                "causal_overlap": 0.0,
                "structural_overlap": 0.0,
                "topology_divergence": 1.0
            }

            if previous_node is not None:

                previous_level = compression_level_for_concept(
                    previous_node.get(
                        "concept"
                    )
                )

                current_level = compression_level_for_concept(
                    node.get(
                        "concept"
                    )
                )

                compression_decision = semantic_compression_allowed(
                    previous_level,
                    current_level
                )

                if compression_decision.get(
                    "allowed",
                    False
                ):

                    node[
                        "compressed_concept"
                    ] = compress_semantic_concept(
                        node.get(
                            "concept"
                        ),
                        semantic_distance=semantic_distance
                    )

            node[
                "compression_distance"
            ] = semantic_distance

            node[
                "compression_applied"
            ] = (
                node.get(
                    "compressed_concept"
                )
                !=
                node.get(
                    "concept"
                )
            )

            node[
                "compression_decision"
            ] = compression_decision

            previous_node = node

        return concept_nodes

    # ============================================
    # ABSTRACT MULTIPLE HYPOTHESES
    # ============================================

    def abstract_hypotheses(

        self,

        hypotheses,

        evidence_context=None
    ):

        abstractions = []

        shared_context = evidence_context

        if isinstance(
            evidence_context,
            dict
        ):

            shared_context = {
                **evidence_context,
                "__task_evidence__":
                self.extract_transformation_evidence(
                    {},
                    evidence_context=evidence_context
                )
            }

        for hypothesis in hypotheses:

            abstractions.append(

                self.abstract_hypothesis(
                    hypothesis,
                    evidence_context=shared_context
                )
            )

        return abstractions

    # ============================================
    # BUILD SEMANTIC GRAPH
    # ============================================

    def build_semantic_graph(

        self,

        abstractions
    ):

        concept_nodes = []

        concept_edges = []

        concept_counts = {}

        for abstraction in abstractions:

            concept = abstraction.get(
                "semantic_concept",
                "generic_transformation"
            )

            concept_counts[concept] = (
                concept_counts.get(
                    concept,
                    0
                )
                + 1
            )

            concept_nodes.append({

                "concept":
                concept,

                "compressed_concept":
                abstraction.get(
                    "compressed_concept",
                    concept
                ),

                "local_identity":
                abstraction.get(
                    "local_identity",
                    concept
                ),

                "structural_identity":
                abstraction.get(
                    "structural_identity",
                    concept
                ),

                "causal_identity":
                abstraction.get(
                    "causal_identity",
                    concept
                ),

                "archetypal_identity":
                abstraction.get(
                    "archetypal_identity",
                    concept
                ),

                "topology_signature":
                abstraction.get(
                    "topology_signature",
                    "none"
                ),

                "primitive":
                abstraction.get(
                    "primitive"
                ),

                "confidence":
                abstraction.get(
                    "confidence",
                    0.0
                ),

                "category":
                abstraction.get(
                    "category",
                    "unknown"
                ),

                "causal_effect":
                abstraction.get(
                    "causal_effect",
                    "unknown"
                ),

                "spatial_effect":
                abstraction.get(
                    "spatial_effect",
                    "unknown"
                ),

                "semantic_class":
                abstraction.get(
                    "semantic_class",
                    "unknown"
                ),

                "semantic_evidence":
                abstraction.get(
                    "semantic_evidence",
                    {}
                )
            })

        concept_nodes = self.apply_adaptive_compression(
            concept_nodes
        )

        for index in range(
            1,
            len(concept_nodes)
        ):

            previous = concept_nodes[index - 1]

            current = concept_nodes[index]

            relation = self.infer_relation(
                previous,
                current
            )

            edge_metrics = self.build_edge_metrics(
                previous,
                current,
                relation
            )

            concept_edges.append({

                "source":
                index - 1,

                "target":
                index,

                "relation":
                relation,

                "edge_weight":
                edge_metrics.get(
                    "edge_weight"
                ),

                "causal_strength":
                edge_metrics.get(
                    "causal_strength"
                ),

                "semantic_distance":
                edge_metrics.get(
                    "semantic_distance"
                ),

                "activation_energy":
                edge_metrics.get(
                    "activation_energy"
                )
            })

        transformation_causal_graph = (
            self.build_transformation_causal_graph(
                concept_nodes
            )
        )

        generic_count = concept_counts.get(
            "generic_transformation",
            0
        )

        concept_count = len(
            abstractions
        )

        semantic_specificity = 0.0

        if concept_count:

            semantic_specificity = round(
                1.0
                -
                (
                    generic_count
                    /
                    concept_count
                ),
                4
            )

        return {

            "concept_nodes":
            concept_nodes,

            "concept_edges":
            concept_edges,

            "transformation_causal_graph":
            transformation_causal_graph,

            "causal_order":
            transformation_causal_graph.get(
                "causal_order",
                []
            ),

            "causal_chains":
            transformation_causal_graph.get(
                "causal_chains",
                []
            ),

            "primary_causal_chain":
            transformation_causal_graph.get(
                "primary_causal_chain",
                []
            ),

            "causal_edge_count":
            transformation_causal_graph.get(
                "edge_count",
                0
            ),

            "causal_chain_count":
            transformation_causal_graph.get(
                "causal_chain_count",
                0
            ),

            "concept_count":
            concept_count,

            "unique_concepts":
            len(concept_counts),

            "concept_distribution":
            concept_counts,

            "compressed_concept_distribution":
            self.build_compressed_distribution(
                concept_nodes
            ),

            "semantic_specificity":
            semantic_specificity,

            "ontology_hits":
            self.ontology_hits,

            "generic_fallback_count":
            self.generic_fallback_count
        }

    # ============================================
    # TRANSFORMATION CAUSAL GRAPH
    # ============================================

    def build_transformation_causal_graph(
        self,
        concept_nodes
    ):

        transformation_nodes = []
        seen = set()

        for index, node in enumerate(
            concept_nodes
        ):

            concept = node.get(
                "concept"
            )

            if concept in seen:

                continue

            if not self._is_transformation_concept(
                node
            ):

                continue

            seen.add(
                concept
            )

            transformation_nodes.append({
                "node_id": len(
                    transformation_nodes
                ),
                "source_index": index,
                "concept": concept,
                "primitive": node.get(
                    "primitive"
                ),
                "causal_effect": node.get(
                    "causal_effect"
                ),
                "semantic_class": node.get(
                    "semantic_class"
                ),
                "confidence": node.get(
                    "confidence",
                    0.0
                ),
                "evidence": node.get(
                    "semantic_evidence",
                    {}
                ),
                "causal_priority": self._causal_priority(
                    node
                ),
            })

        transformation_nodes = sorted(
            transformation_nodes,
            key=lambda node: (
                node.get(
                    "causal_priority",
                    50
                ),
                -float(
                    node.get(
                        "confidence",
                        0.0
                    )
                    or
                    0.0
                ),
                node.get(
                    "source_index",
                    0
                ),
            )
        )

        for order_index, node in enumerate(
            transformation_nodes
        ):

            node[
                "causal_order_index"
            ] = order_index

        causal_edges = []

        for index, source in enumerate(
            transformation_nodes
        ):

            for target in transformation_nodes[
                index + 1:
            ]:

                relation = self._causal_relation(
                    source,
                    target
                )

                if relation is None:

                    continue

                causal_edges.append({
                    "source": source.get(
                        "concept"
                    ),
                    "target": target.get(
                        "concept"
                    ),
                    "relation": relation.get(
                        "relation"
                    ),
                    "evidence": relation.get(
                        "evidence"
                    ),
                    "confidence": relation.get(
                        "confidence"
                    ),
                })

        causal_order = [
            node.get(
                "concept"
            )
            for node in transformation_nodes
        ]

        causal_chains = self._causal_chains(
            transformation_nodes,
            causal_edges
        )

        return {
            "system": "multi_transformation_causal_graph",
            "nodes": transformation_nodes,
            "edges": causal_edges,
            "causal_order": causal_order,
            "causal_chains": causal_chains,
            "primary_causal_chain": (
                causal_chains[0]
                if causal_chains
                else []
            ),
            "causal_chain_count": len(
                causal_chains
            ),
            "node_count": len(
                transformation_nodes
            ),
            "edge_count": len(
                causal_edges
            ),
            "causal_ordering_ready": (
                len(
                    transformation_nodes
                )
                >= 2
            ),
        }

    def _causal_chains(
        self,
        transformation_nodes,
        causal_edges
    ):

        order = [
            node.get(
                "concept"
            )
            for node in transformation_nodes
        ]

        order_index = {
            concept: index
            for index, concept in enumerate(
                order
            )
        }

        adjacency = {}

        for edge in causal_edges:

            source = edge.get(
                "source"
            )

            target = edge.get(
                "target"
            )

            if (
                source not in order_index
                or
                target not in order_index
                or
                order_index[source] >= order_index[target]
            ):

                continue

            adjacency.setdefault(
                source,
                []
            ).append(
                target
            )

        for source in adjacency:

            adjacency[source] = sorted(
                set(
                    adjacency[source]
                ),
                key=lambda concept: order_index.get(
                    concept,
                    999
                )
            )

        chains = []

        def walk(path):

            current = path[-1]
            targets = adjacency.get(
                current,
                []
            )

            extended = False

            for target in targets:

                if target in path:

                    continue

                extended = True
                walk(
                    [
                        *path,
                        target,
                    ]
                )

            if not extended and len(path) >= 2:

                chains.append(
                    path
                )

        for concept in order:

            walk(
                [
                    concept
                ]
            )

        unique_chains = []
        seen = set()

        for chain in chains:

            key = tuple(
                chain
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            unique_chains.append(
                chain
            )

        return sorted(
            unique_chains,
            key=lambda chain: (
                -len(
                    chain
                ),
                [
                    order_index.get(
                        concept,
                        999
                    )
                    for concept in chain
                ],
            )
        )

    def _is_transformation_concept(
        self,
        node
    ):

        concept = node.get(
            "concept"
        )

        if concept in {
            "replication",
            "duplication",
            "growth",
            "propagation",
            "symmetry_reasoning",
            "fragmentation",
            "fusion",
            "contraction",
            "object_elimination",
            "topology_change",
            "containment",
        }:

            return True

        if node.get(
            "semantic_class"
        ) in {
            "multiplicative",
            "diffusive",
            "expansive",
            "transformative",
            "transformation",
        }:

            return True

        return False

    def _causal_priority(
        self,
        node
    ):

        concept = node.get(
            "concept"
        )

        priority = {
            "replication": 10,
            "duplication": 10,
            "growth": 15,
            "fragmentation": 18,
            "fusion": 18,
            "propagation": 20,
            "contraction": 20,
            "containment": 25,
            "symmetry_reasoning": 30,
            "topology_change": 35,
            "object_elimination": 40,
        }

        return priority.get(
            concept,
            50
        )

    def _causal_relation(
        self,
        source,
        target
    ):

        source_concept = source.get(
            "concept"
        )

        target_concept = target.get(
            "concept"
        )

        evidence = target.get(
            "evidence",
            {}
        )

        count_delta = evidence.get(
            "object_count_delta"
        )

        density_delta = evidence.get(
            "density_delta"
        )

        symmetry_changed = evidence.get(
            "symmetry_changed"
        )

        if (
            source_concept in {
                "replication",
                "duplication",
            }
            and
            target_concept == "propagation"
            and
            count_delta is not None
            and
            count_delta > 0
            and
            density_delta is not None
            and
            density_delta > 0
        ):

            return {
                "relation": "enables_density_increase",
                "evidence": "object_count_increase_and_density_increase",
                "confidence": self._edge_confidence(
                    source,
                    target,
                    0.92
                ),
            }

        if (
            source_concept == "growth"
            and
            target_concept == "propagation"
            and
            count_delta == 0
            and
            density_delta is not None
            and
            density_delta > 0
        ):

            return {
                "relation": "expands_into_density_increase",
                "evidence": "stable_object_count_with_density_increase",
                "confidence": self._edge_confidence(
                    source,
                    target,
                    0.88
                ),
            }

        if (
            source_concept == "growth"
            and
            target_concept == "containment"
            and
            density_delta is not None
            and
            density_delta > 0
        ):

            return {
                "relation": "creates_containment_pressure",
                "evidence": "area_growth_with_region_pressure",
                "confidence": self._edge_confidence(
                    source,
                    target,
                    0.72
                ),
            }

        if (
            source_concept == "propagation"
            and
            target_concept == "symmetry_reasoning"
            and
            symmetry_changed is True
        ):

            return {
                "relation": "reshapes_symmetry",
                "evidence": "density_change_with_symmetry_change",
                "confidence": self._edge_confidence(
                    source,
                    target,
                    0.84
                ),
            }

        if (
            source_concept in {
                "replication",
                "duplication",
            }
            and
            target_concept == "symmetry_reasoning"
            and
            symmetry_changed is True
        ):

            return {
                "relation": "changes_spatial_arrangement",
                "evidence": "object_count_change_with_symmetry_change",
                "confidence": self._edge_confidence(
                    source,
                    target,
                    0.78
                ),
            }

        if (
            source_concept == "growth"
            and
            target_concept == "symmetry_reasoning"
            and
            symmetry_changed is True
        ):

            return {
                "relation": "reshapes_symmetry_through_growth",
                "evidence": "stable_count_growth_with_symmetry_change",
                "confidence": self._edge_confidence(
                    source,
                    target,
                    0.80
                ),
            }

        return {
            "relation": "precedes",
            "evidence": "causal_priority_order",
            "confidence": self._edge_confidence(
                source,
                target,
                0.55
            ),
        }

    def _edge_confidence(
        self,
        source,
        target,
        base
    ):

        source_confidence = float(
            source.get(
                "confidence",
                0.0
            )
            or
            0.0
        )

        target_confidence = float(
            target.get(
                "confidence",
                0.0
            )
            or
            0.0
        )

        return round(
            min(
                1.0,
                base
                *
                max(
                    source_confidence,
                    0.1
                )
                *
                max(
                    target_confidence,
                    0.1
                )
            ),
            4
        )

    # ============================================
    # BUILD COMPRESSED DISTRIBUTION
    # ============================================

    def build_compressed_distribution(
        self,
        concept_nodes
    ):

        distribution = {}

        for node in concept_nodes:

            concept = node.get(
                "compressed_concept",
                node.get(
                    "concept",
                    "unknown"
                )
            )

            distribution[concept] = (
                distribution.get(
                    concept,
                    0
                )
                + 1
            )

        return distribution
