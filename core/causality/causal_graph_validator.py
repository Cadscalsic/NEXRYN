from core.epistemic_models import clamp
from core.causality.causal_evidence_accumulator import (
    CausalEvidenceAccumulator,
)


CORE_CAUSAL_RELATIONSHIPS = [
    {
        "source": "density_preservation",
        "target": "topology_preservation",
    },
    {
        "source": "topology_preservation",
        "target": "symmetry_preservation",
    },
    {
        "source": "symmetry_preservation",
        "target": "object_identity_preservation",
    },
]


class CausalGraphValidator:
    """Validates required causal relationships before a truth enters the core."""

    def __init__(
        self,
        minimum_causal_strength=0.30,
        relationships=None,
        evidence_accumulator=None,
    ):
        self.minimum_causal_strength = clamp(minimum_causal_strength)
        self.relationships = list(
            CORE_CAUSAL_RELATIONSHIPS
            if relationships is None
            else relationships
        )
        self.evidence_accumulator = (
            evidence_accumulator or CausalEvidenceAccumulator()
        )

    def _nodes(self, graph):
        return list(graph.get("concept_nodes", graph.get("nodes", [])))

    def _edges(self, graph):
        nodes = self._nodes(graph)
        edges = []
        for edge in graph.get("concept_edges", graph.get("edges", [])):
            source = edge.get("source")
            target = edge.get("target")
            if isinstance(source, int) and 0 <= source < len(nodes):
                source = nodes[source].get("concept")
            if isinstance(target, int) and 0 <= target < len(nodes):
                target = nodes[target].get("concept")
            edges.append({
                **edge,
                "source": source,
                "target": target,
                "causal_strength": clamp(
                    edge.get(
                        "causal_strength",
                        edge.get("edge_weight", 0.0),
                    )
                ),
            })
        return edges

    def _relationships(self, context):
        return context.get(
            "core_causal_relationships",
            self.relationships,
        )

    def _requirements(self, concept, context):
        return [
            dict(relationship)
            for relationship in self._relationships(context)
            if relationship.get("target") == concept
        ]

    def _downstream_relationships(self, concept, context):
        relationships = context.get(
            "core_causal_relationships",
            self.relationships,
        )
        return [
            dict(relationship)
            for relationship in relationships
            if relationship.get("source") == concept
        ]

    def evaluate(self, concept, semantic_graph=None, context=None):
        context = context if isinstance(context, dict) else {}
        semantic_graph = (
            semantic_graph
            if isinstance(semantic_graph, dict)
            else {}
        )
        graph_observed = bool(
            self._nodes(semantic_graph)
            or semantic_graph.get("concept_edges")
            or semantic_graph.get("edges")
        )
        requirements = self._requirements(concept, context)
        downstream_relationships = self._downstream_relationships(
            concept,
            context,
        )
        edges = self._edges(semantic_graph)
        checks = []
        for requirement in requirements:
            minimum_strength = clamp(
                requirement.get(
                    "minimum_causal_strength",
                    self.minimum_causal_strength,
                )
            )
            matched_edge = next(
                (
                    edge
                    for edge in edges
                    if (
                        edge.get("source") == requirement["source"]
                        and edge.get("target") == requirement["target"]
                    )
                ),
                None,
            )
            causal_strength = (
                matched_edge["causal_strength"]
                if matched_edge is not None
                else 0.0
            )
            causal_support = (
                self.evidence_accumulator.observe(
                    requirement["source"],
                    requirement["target"],
                    causal_strength,
                    minimum_strength,
                )
                if matched_edge is not None
                else self.evidence_accumulator.report_for(
                    requirement["source"],
                    requirement["target"],
                )
            )
            current_edge_supported = (
                matched_edge is not None
                and causal_strength >= minimum_strength
            )
            accumulated_support_ready = (
                causal_support["causal_support_ready"]
            )
            checks.append({
                **requirement,
                "minimum_causal_strength": minimum_strength,
                "causal_strength": causal_strength,
                "edge_observed": matched_edge is not None,
                "current_edge_supported": current_edge_supported,
                "accumulated_support_ready": accumulated_support_ready,
                "support_source": (
                    "CURRENT_GRAPH_OBSERVATION"
                    if current_edge_supported
                    else "ACCUMULATED_CAUSAL_EVIDENCE"
                    if accumulated_support_ready
                    else "INSUFFICIENT_CAUSAL_EVIDENCE"
                ),
                "passed":
                current_edge_supported or accumulated_support_ready,
                "causal_support": causal_support,
                "causal_support_score":
                causal_support["causal_support_score"],
                "causal_support_ready":
                causal_support["causal_support_ready"],
                "matched_edge": matched_edge,
            })

        causal_consistency_score = min(
            (
                check["causal_strength"]
                for check in checks
            ),
            default=1.0,
        )
        causal_support_score = min(
            (
                check["causal_support_score"]
                for check in checks
            ),
            default=1.0,
        )
        validation_ready = (
            all(
                check["passed"]
                and check["causal_support_ready"]
                for check in checks
            )
            if graph_observed
            else True
        )
        return {
            "system": "causal_graph_validator",
            "concept": concept,
            "graph_observed": graph_observed,
            "required_relationships": requirements,
            "downstream_relationships": downstream_relationships,
            "downstream_relationships_are_diagnostic_only": True,
            "relationship_checks": checks,
            "causal_consistency_score": causal_consistency_score,
            "causal_support_score": causal_support_score,
            "minimum_causal_strength": self.minimum_causal_strength,
            "validation_ready": validation_ready,
            "blocked_relationships": [
                {
                    "source": check["source"],
                    "target": check["target"],
                }
                for check in checks
                if not check["passed"]
            ],
            "accumulating_relationships": [
                {
                    "source": check["source"],
                    "target": check["target"],
                    "causal_support_score":
                    check["causal_support_score"],
                }
                for check in checks
                if check["passed"] and not check["causal_support_ready"]
            ],
            "causal_support_accumulator":
            self.evidence_accumulator.report(),
            "validation_state": (
                "CAUSAL_GRAPH_NOT_OBSERVED"
                if not graph_observed
                else "CAUSAL_GRAPH_VALIDATED"
                if validation_ready
                else "CAUSAL_SUPPORT_ACCUMULATING"
                if all(check["passed"] for check in checks)
                else "CAUSAL_GRAPH_VALIDATION_REQUIRED"
            ),
            "semantic_sequence_is_not_causal_proof": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "CORE_CAUSAL_RELATIONSHIPS",
    "CausalGraphValidator",
]
