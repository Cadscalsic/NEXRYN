from core.epistemic_models import clamp
from core.truth.contextual_truth_engine import ContextualTruthEngine


class RuntimeCausalAlignmentEngine:
    """Explains when a preservation truth is bounded by a transform context."""

    PRESERVATION_BOUNDARIES = {
        "shape_preservation": {
            "family": "shape",
            "transform_concepts": {
                "shape_transform",
                "shape_transformation",
                "shape_change",
                "expand_object",
                "duplicate_object",
            },
        },
        "color_preservation": {
            "family": "color",
            "transform_concepts": {
                "color_transform",
                "color_change",
                "recolor",
                "recolor_object",
                "replace_color",
                "symbolic_remapping",
                "attribute_remapping",
            },
        },
        "symmetry_preservation": {
            "family": "symmetry",
            "transform_concepts": {
                "symmetry_break",
                "symmetry_transform",
                "asymmetry",
                "symmetry_reasoning",
                "symmetry_analysis",
            },
        },
        "topology_preservation": {
            "family": "topology",
            "transform_concepts": {
                "topology_transform",
                "topological_change",
                "topological_growth",
                "grow_topology",
                "expand_pattern",
                "fill_region",
                "topological_reasoning",
                "topology_analysis",
            },
        },
        "object_identity_preservation": {
            "family": "identity",
            "transform_concepts": {
                "object_identity_transform",
                "object_split",
                "object_merge",
                "identity_continuity",
                "identity_tracking",
                "identity_preservation",
                "object_persistence",
                "object_core",
            },
        },
        "identity_persistence": {
            "family": "identity",
            "transform_concepts": {
                "object_identity_transform",
                "object_persistence",
            },
        },
        "identity_forking": {
            "family": "identity",
            "transform_concepts": {
                "object_split",
                "object_merge",
                "identity_continuity",
                "identity_tracking",
                "identity_preservation",
                "object_persistence",
                "object_core",
            },
        },
    }

    CAUSAL_PATH_TEMPLATES = {
        "color_preservation": [
            "color_observation",
            "color_behavior",
            "color_mapping_rule",
            "no_color_reassignment",
            "color_preservation",
        ],
        "object_identity_preservation": [
            "object_observation",
            "identity_behavior",
            "lineage_continuity",
            "object_persistence",
            "object_identity_preservation",
        ],
        "identity_persistence": [
            "object_observation",
            "identity_behavior",
            "lineage_continuity",
            "object_persistence",
            "identity_persistence",
        ],
        "growth": [
            "source_object",
            "identity_persistence",
            "topology_expansion",
            "shape_preservation",
            "growth",
        ],
        "replication": [
            "source_pattern_preserved",
            "identity_forking",
            "identity_split",
            "object_count_increase",
            "replication",
        ],
        "topological_growth": [
            "growth",
            "topology_expansion",
            "local_shape",
            "topology_preservation",
            "topological_growth",
        ],
        "symmetry_reasoning": [
            "object_observation",
            "symmetry_relation",
            "symmetry_axis",
            "object_pair_mapping",
            "relation_consistency",
            "symmetry_reasoning",
        ],
    }

    def __init__(
        self,
        minimum_explanation_confidence=0.70,
        max_explained_contradiction=0.06,
    ):
        self.minimum_explanation_confidence = clamp(
            minimum_explanation_confidence,
        )
        self.max_explained_contradiction = clamp(
            max_explained_contradiction,
        )

    def _explicit_explanation(self, concept, context):
        explanations = context.get("causal_boundary_explanations", {})
        if not isinstance(explanations, dict):
            return {}
        explanation = explanations.get(concept, {})
        return explanation if isinstance(explanation, dict) else {}

    def _active_concepts(self, context):
        concepts = set()
        for key in (
            "semantic_concepts",
            "active_concepts",
            "concepts",
            "detected_concepts",
        ):
            value = context.get(key, [])
            if isinstance(value, dict):
                value = value.keys()
            if isinstance(value, (list, tuple, set)):
                concepts.update(str(item) for item in value)
        semantic_graph = context.get("semantic_graph", {})
        if isinstance(semantic_graph, dict):
            graph_concepts = semantic_graph.get("concepts", [])
            if isinstance(graph_concepts, dict):
                graph_concepts = graph_concepts.keys()
            if isinstance(graph_concepts, (list, tuple, set)):
                concepts.update(str(item) for item in graph_concepts)
        return concepts

    def _is_transform_reasoning_context(self, family, active_concepts):
        reasoning_keywords = (
            "reasoning",
            "analysis",
            "evaluation",
            "inspection",
            "validation",
        )
        for item in active_concepts:
            normalized = str(item).lower()
            if family in normalized and any(
                keyword in normalized
                for keyword in reasoning_keywords
            ):
                return True
        return False

    def _context_mode(self, concept, boundary, context):
        conditions = context.get("causal_conditions", {})
        if not isinstance(conditions, dict):
            conditions = {}
        family = boundary["family"]
        mode = conditions.get(
            f"{family}_mode",
            conditions.get(
                f"{family}_relation",
                conditions.get("transformation_mode"),
            ),
        )
        if isinstance(mode, str):
            normalized = mode.lower()
            if (
                "transform" in normalized
                or "change" in normalized
                or "recolor" in normalized
                or "replace" in normalized
                or "symbolic" in normalized
                or "remap" in normalized
                or "grow" in normalized
                or "expand" in normalized
                or "fill" in normalized
                or "duplicate" in normalized
            ):
                return "transform_context"
            if "preserve" in normalized or "same" in normalized:
                return "preservation_context"

        active_concepts = self._active_concepts(context)
        if boundary["transform_concepts"] & active_concepts:
            return "transform_context"
        if self._is_transform_reasoning_context(family, active_concepts):
            return "transform_context"
        if concept in active_concepts:
            return "preservation_context"
        return "unknown_context"

    def _boundary_observations(self, concept, context):
        observations = context.get("causal_boundary_observations", {})
        if isinstance(observations, dict):
            observations = observations.get(concept, [])
        if isinstance(observations, dict):
            observations = [observations]
        if not isinstance(observations, list):
            return []
        return [
            item
            for item in observations
            if isinstance(item, dict)
        ]

    def _mixed_boundary_support(self, concept, context):
        observations = self._boundary_observations(concept, context)
        supported = [
            item
            for item in observations
            if item.get("outcome", item.get("state")) in {
                "holds",
                "preserved",
                "support",
            }
        ]
        counterexamples = [
            item
            for item in observations
            if item.get("outcome", item.get("state")) in {
                "breaks",
                "transformed",
                "counterexample",
            }
        ]
        total = len(supported) + len(counterexamples)
        confidence = clamp(total / 5) if total else 0.0
        return {
            "supported_region_count": len(supported),
            "counterexample_region_count": len(counterexamples),
            "mixed_boundary_observed": bool(supported and counterexamples),
            "boundary_observation_confidence": confidence,
        }

    def _as_items(self, value):
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        if isinstance(value, (str, bytes)):
            return [value]
        try:
            return list(value)
        except TypeError:
            return [value]

    def _tokens(self, value):
        tokens = set()
        if value is None:
            return tokens
        if isinstance(value, dict):
            for key, item in value.items():
                key_token = self._normalize(key)
                if key_token:
                    tokens.add(key_token)
                tokens.update(self._tokens(item))
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                tokens.update(self._tokens(item))
        else:
            token = self._normalize(value)
            if token:
                tokens.add(token)
        return tokens

    def _normalize(self, value):
        return str(value or "").strip().lower().replace(" ", "_")

    def _dependency_nodes(self, process_dependency_memory):
        nodes = set()
        if not isinstance(process_dependency_memory, dict):
            return nodes
        for item in self._as_items(
            process_dependency_memory.get("resolved_dependency_chain", [])
        ):
            if isinstance(item, dict):
                nodes.update(self._tokens(item))
            else:
                nodes.add(self._normalize(item))
        for relation in self._as_items(
            process_dependency_memory.get("typed_dependency_relations", [])
        ):
            if isinstance(relation, dict):
                nodes.add(self._normalize(relation.get("source")))
                nodes.add(self._normalize(relation.get("target")))
                nodes.add(self._normalize(relation.get("relation")))
        return {node for node in nodes if node}

    def _context_nodes(self, context):
        nodes = set()
        for key in (
            "semantic_context",
            "context_hierarchy",
            "contextual_truth",
            "causal_validation",
            "causal_graph_alignment",
            "causal_explanation",
            "context_discovery",
            "dependency_chain_alignment",
            "semantic_boundary_report",
            "relational_reasoning_report",
        ):
            nodes.update(self._tokens(context.get(key)))
        return nodes

    def _template_for(self, concept, process_dependency_memory):
        concept = self._normalize(concept)
        if concept in self.CAUSAL_PATH_TEMPLATES:
            return list(self.CAUSAL_PATH_TEMPLATES[concept])
        chain = [
            self._normalize(item)
            for item in process_dependency_memory.get(
                "resolved_dependency_chain",
                [],
            )
            if not isinstance(item, dict)
        ] if isinstance(process_dependency_memory, dict) else []
        if chain:
            return chain
        return [concept]

    def build_explicit_causal_alignment(
        self,
        concept,
        dependency_chain=None,
        context=None,
    ):
        context = context if isinstance(context, dict) else {}
        process_dependency_memory = (
            dependency_chain
            if isinstance(dependency_chain, dict)
            else context.get("process_dependency_memory", {})
        )
        process_dependency_memory = (
            process_dependency_memory
            if isinstance(process_dependency_memory, dict)
            else {}
        )
        concept = self._normalize(concept)
        causal_path = self._template_for(concept, process_dependency_memory)
        available_nodes = set()
        available_nodes.update(self._dependency_nodes(process_dependency_memory))
        available_nodes.update(self._context_nodes(context))
        explanation_path = context.get("causal_graph_alignment", {}).get(
            "explanation_path",
            context.get("causal_explanation", {}).get("explanation_path", []),
        )
        available_nodes.update(self._tokens(explanation_path))
        causal_gaps = [
            node
            for node in causal_path
            if node not in available_nodes
        ]
        weak_links = []
        graph_alignment = context.get("causal_graph_alignment", {})
        graph_alignment = graph_alignment if isinstance(graph_alignment, dict) else {}
        components = graph_alignment.get("components", {})
        components = components if isinstance(components, dict) else {}
        chain_confidence = clamp(
            process_dependency_memory.get(
                "dependency_confidence",
                process_dependency_memory.get("dependency_chain_coverage", 0.0),
            )
        )
        chain_coverage = clamp(
            process_dependency_memory.get("dependency_chain_coverage", 0.0)
        )
        dependency_coherence_report = context.get(
            "dependency_coherence_report",
            {},
        )
        dependency_coherence = clamp(
            dependency_coherence_report.get(
                "dependency_coherence",
                components.get("dependency_coherence", chain_confidence),
            )
        ) if isinstance(dependency_coherence_report, dict) else clamp(
            components.get("dependency_coherence", chain_confidence)
        )
        effective_components = {
            **components,
            "dependency_coherence": max(
                clamp(components.get("dependency_coherence", 0.0)),
                dependency_coherence,
            ),
        }
        component_scores = [
            clamp(effective_components.get("evidence_consistency", 0.0)),
            clamp(effective_components.get("cross_task_stability", 0.0)),
            clamp(effective_components.get("contradiction_resistance", 0.0)),
            clamp(effective_components.get("dependency_coherence", 0.0)),
        ]
        component_scores = [score for score in component_scores if score > 0.0]
        for name, score in effective_components.items():
            if isinstance(score, (int, float)) and clamp(score) < 0.80:
                weak_links.append(str(name))
        validation = context.get("causal_validation", {})
        validation = validation if isinstance(validation, dict) else {}
        validation_score = clamp(
            validation.get(
                "validation_score",
                validation.get("causal_validation_score", 0.0),
            )
        )
        path_coverage = clamp(
            (len(causal_path) - len(causal_gaps)) / max(len(causal_path), 1)
        )
        component_average = (
            sum(component_scores) / len(component_scores)
            if component_scores
            else 0.0
        )
        causal_reliability = clamp(
            path_coverage * 0.30
            + dependency_coherence * 0.25
            + chain_confidence * 0.18
            + max(validation_score, component_average) * 0.17
            + chain_coverage * 0.10
        )
        causal_alignment = clamp(
            causal_reliability * 0.62
            + path_coverage * 0.23
            + dependency_coherence * 0.15
            - min(len(weak_links) * 0.025, 0.10)
        )
        unexplained_nodes = sorted(set(causal_gaps + weak_links))
        return {
            "system": "runtime_causal_alignment_engine",
            "concept": concept,
            "causal_alignment": round(causal_alignment, 4),
            "causal_path": causal_path,
            "causal_gaps": causal_gaps,
            "unexplained_nodes": unexplained_nodes,
            "weak_causal_links": weak_links,
            "causal_reliability": round(causal_reliability, 4),
            "dependency_coherence": round(dependency_coherence, 4),
            "path_coverage": round(path_coverage, 4),
            "alignment_ready": (
                causal_alignment > 0.82
                and causal_reliability > 0.82
                and not causal_gaps
            ),
            "causal_explainability_required": True,
        }

    def evaluate(self, concept, aggregate=None, context=None):
        context = context if isinstance(context, dict) else {}
        aggregate = aggregate or {}
        explicit_alignment = self.build_explicit_causal_alignment(
            concept,
            context.get("process_dependency_memory", {}),
            context,
        )
        raw_contradiction = clamp(
            getattr(
                aggregate,
                "contradiction_score",
                aggregate.get("contradiction_score", 0.0)
                if isinstance(aggregate, dict)
                else 0.0,
            )
        )
        boundary = self.PRESERVATION_BOUNDARIES.get(concept)
        if not boundary:
            return {
                "system": "runtime_causal_alignment_engine",
                "concept": concept,
                "causal_alignment":
                explicit_alignment["causal_alignment"],
                "causal_path": explicit_alignment["causal_path"],
                "causal_gaps": explicit_alignment["causal_gaps"],
                "unexplained_nodes":
                explicit_alignment["unexplained_nodes"],
                "causal_reliability":
                explicit_alignment["causal_reliability"],
                "explicit_causal_alignment": explicit_alignment,
                "alignment_state": "NO_RUNTIME_BOUNDARY_MODEL",
                "contradiction_interpretable": False,
                "raw_contradiction_score": raw_contradiction,
                "adjusted_contradiction_score": raw_contradiction,
                "contradiction_adjustment": 0.0,
                "causal_alignment_supported": False,
                "automatic_truth_commit_forbidden": True,
            }

        explicit = self._explicit_explanation(concept, context)
        observed_mode = explicit.get(
            "mode",
            self._context_mode(concept, boundary, context),
        )
        observation_support = self._mixed_boundary_support(
            concept,
            context,
        )
        explicit_confidence = clamp(
            explicit.get("explanation_confidence", 0.0),
        )
        mode_supported = observed_mode in {
            "transform_context",
            "preservation_context",
        }
        explanation_confidence = max(
            explicit_confidence,
            observation_support["boundary_observation_confidence"],
            0.80 if mode_supported else 0.0,
        )

        contradiction_interpretable = (
            explanation_confidence
            >= self.minimum_explanation_confidence
            and (
                mode_supported
                or observation_support[
                    "mixed_boundary_observed"
                ]
            )
        )
        process_dependency_memory = context.get(
            "process_dependency_memory",
            {},
        )
        process_dependency_memory = (
            process_dependency_memory
            if isinstance(process_dependency_memory, dict)
            else {}
        )

        dependency_confidence = context.get(
            "dependency_confidence",
            process_dependency_memory.get(
                "dependency_confidence",
                0.0,
            ),
        )

        promotion_dependency_score = context.get(
            "promotion_dependency_score",
            process_dependency_memory.get(
                "promotion_dependency_score",
                0.0,
            ),
        )

        causal_alignment_audit = {
            "explanation_confidence":
                explanation_confidence,
            "minimum_explanation_confidence":
                self.minimum_explanation_confidence,
            "mode_supported":
                mode_supported,
            "mixed_boundary_observed":
                observation_support[
                    "mixed_boundary_observed"
                ],
            "dependency_confidence":
                dependency_confidence,
            "promotion_dependency_score":
                promotion_dependency_score,
            "contradiction_interpretable":
                contradiction_interpretable,
        }
        adjusted_contradiction = (
            min(raw_contradiction, self.max_explained_contradiction)
            if contradiction_interpretable
            else raw_contradiction
        )
        adjustment = round(
            max(raw_contradiction - adjusted_contradiction, 0.0),
            4,
        )
        return {
            "system": "runtime_causal_alignment_engine",
            "concept": concept,
            "causal_alignment":
            explicit_alignment["causal_alignment"],
            "causal_path": explicit_alignment["causal_path"],
            "causal_gaps": explicit_alignment["causal_gaps"],
            "unexplained_nodes":
            explicit_alignment["unexplained_nodes"],
            "causal_reliability":
            explicit_alignment["causal_reliability"],
            "explicit_causal_alignment": explicit_alignment,
            "property_family": boundary["family"],
            "preservation_concept": concept,
            "transform_concepts": sorted(boundary["transform_concepts"]),
            "observed_mode": observed_mode,
            "alignment_state": (
                "CONTEXTUAL_BOUNDARY_EXPLAINED"
                if contradiction_interpretable
                else "CONTEXTUAL_BOUNDARY_REQUIRED"
            ),
            "contradiction_interpretable": contradiction_interpretable,
            "explanation_confidence": explanation_confidence,
            "minimum_explanation_confidence":
            self.minimum_explanation_confidence,
            "raw_contradiction_score": raw_contradiction,
            "adjusted_contradiction_score": adjusted_contradiction,
            "contradiction_adjustment": adjustment,
            "causal_alignment_supported":
            contradiction_interpretable,
            "causal_alignment_audit":
            causal_alignment_audit,
            "boundary_evidence": observation_support,
            "required_action": (
                None
                if contradiction_interpretable
                else "collect_contextual_causal_boundary_evidence"
            ),
            "preservation_and_transform_are_contextual_not_absolute": True,
            "contextual_truth_model": ContextualTruthEngine().contextual_truth_model(
                concept,
                context,
            ),
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "CausalAlignmentEngine",
    "RuntimeCausalAlignmentEngine",
]


CausalAlignmentEngine = RuntimeCausalAlignmentEngine
