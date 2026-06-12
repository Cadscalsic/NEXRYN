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

    def evaluate(self, concept, aggregate=None, context=None):
        context = context if isinstance(context, dict) else {}
        aggregate = aggregate or {}
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
    "RuntimeCausalAlignmentEngine",
]
