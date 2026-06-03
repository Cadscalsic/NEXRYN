class ContextualTruthEngine:
    """Models preservation truths as conditional rules when transform context exists."""

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
            },
        },
    }

    def __init__(self):
        self.preservation_boundaries = self.PRESERVATION_BOUNDARIES

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

    def contextual_truth_model(self, concept, context=None):
        context = context if isinstance(context, dict) else {}
        boundary = self.preservation_boundaries.get(concept)
        if not boundary:
            return {
                "system": "contextual_truth_engine",
                "concept": concept,
                "truth_type": "absolute",
                "concept_family": None,
                "preservation_concept": concept,
                "conditional_form": None,
                "truth_condition": None,
                "contextual_explanation": (
                    "No preservation boundary is available for this concept."
                ),
                "context_mode": None,
                "transform_concepts": [],
                "active_transform_context": False,
            }

        family = boundary["family"]
        transform_concepts = sorted(boundary["transform_concepts"])
        observed_mode = self._context_mode(concept, boundary, context)
        active_transform_context = observed_mode == "transform_context"
        conditional_form = (
            f"IF no_{family}_transform: {concept}"
        )
        explanation = (
            "Preservation concepts are modeled as conditional truths. "
            f"{concept} is valid unless an explicit {family} transform occurs."
        )
        if active_transform_context:
            explanation = (
                "A transform context is detected, so this preservation rule "
                "is interpreted as a conditional boundary rather than an absolute truth."
            )
        return {
            "system": "contextual_truth_engine",
            "concept": concept,
            "truth_type": "conditional",
            "concept_family": family,
            "preservation_concept": concept,
            "conditional_form": conditional_form,
            "truth_condition": f"no_{family}_transform",
            "contextual_explanation": explanation,
            "context_mode": observed_mode,
            "transform_concepts": transform_concepts,
            "active_transform_context": active_transform_context,
        }


__all__ = [
    "ContextualTruthEngine",
]
