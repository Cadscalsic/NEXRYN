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
    # ABSTRACT HYPOTHESIS
    # ============================================

    def abstract_hypothesis(

        self,

        hypothesis
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

        compression_level = compression_level_for_concept(
            semantic_concept
        )

        return {

            "original_type":
            hypothesis_type,

            "primitive":
            primitive,

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
            )
        }

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

        hypotheses
    ):

        abstractions = []

        for hypothesis in hypotheses:

            abstractions.append(

                self.abstract_hypothesis(
                    hypothesis
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
