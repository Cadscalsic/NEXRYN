"""Semantic context foundation for runtime cognitive artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from hashlib import sha1
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


DOMAIN_EVIDENCE = {
    "Geometry & Shape": {
        "shape",
        "geometry",
        "symmetry",
        "mirror",
        "reflection",
        "rotation",
        "flip",
        "horizontal",
        "vertical",
        "size",
        "area",
    },
    "Topology & Structure": {
        "topology",
        "structure",
        "connectivity",
        "connected",
        "boundary",
        "component",
        "adjacent",
        "neighbor",
    },
    "Object Dynamics": {
        "object",
        "motion",
        "move",
        "velocity",
        "position",
        "transition",
        "state",
        "dynamic",
    },
    "Color & Attributes": {
        "color",
        "attribute",
        "palette",
        "red",
        "blue",
        "green",
        "value",
    },
    "Counting & Quantity": {
        "count",
        "quantity",
        "cardinality",
        "number",
        "set",
        "size",
        "measure",
    },
    "Pattern Completion": {
        "pattern",
        "completion",
        "repeat",
        "sequence",
        "replication",
        "propagation",
    },
    "Spatial Reasoning": {
        "spatial",
        "position",
        "direction",
        "left",
        "right",
        "above",
        "below",
        "grid",
    },
    "Temporal Reasoning": {
        "temporal",
        "time",
        "before",
        "after",
        "lifecycle",
        "history",
        "sequence",
    },
    "Symbolic Mapping": {
        "symbol",
        "mapping",
        "map",
        "remap",
        "label",
        "token",
        "ontology",
    },
    "Planning": {
        "plan",
        "goal",
        "strategy",
        "route",
        "policy",
        "decision",
    },
    "Causal Reasoning": {
        "cause",
        "causal",
        "dependency",
        "depends",
        "influence",
        "support",
        "contradict",
    },
    "Program Synthesis": {
        "program",
        "code",
        "synthesis",
        "execute",
        "runtime",
        "operation",
    },
    "Knowledge Integration": {
        "knowledge",
        "integration",
        "evidence",
        "abstraction",
        "reuse",
        "generalization",
    },
    "Truth Validation": {
        "truth",
        "validation",
        "candidate",
        "verified",
        "confidence",
        "contradiction",
    },
    "Memory Organization": {
        "memory",
        "experience",
        "retrieval",
        "storage",
        "recall",
        "history",
    },
}

ROLE_EVIDENCE = {
    "Concept": {"concept", "abstraction", "idea", "semantic"},
    "Operation": {"operation", "operator", "compute", "execute"},
    "Transformation": {"transform", "transformation", "transition", "change"},
    "Relation": {"relation", "relationship", "edge", "connects"},
    "Constraint": {"constraint", "limit", "required", "excluded"},
    "Invariant": {"invariant", "preserved", "constant", "stable"},
    "Object": {"object", "entity", "instance"},
    "Attribute": {"attribute", "property", "color", "size"},
    "Process": {"process", "state", "precondition", "postcondition"},
    "Goal": {"goal", "objective", "target"},
    "Strategy": {"strategy", "plan", "route"},
    "Evidence": {"evidence", "observation", "support"},
    "Truth": {"truth", "validated", "candidate"},
    "Policy": {"policy", "governance", "rule"},
    "Decision": {"decision", "choice", "selected"},
    "Situation": {"situation", "world", "awareness"},
    "Experience": {"experience", "memory", "episode"},
}

RELATION_EVIDENCE = {
    "Depends On": {"depends", "requires", "precondition", "prerequisite"},
    "Generalizes": {"generalizes", "abstraction", "parent", "family"},
    "Specializes": {"specializes", "child", "specific", "refinement"},
    "Supports": {"supports", "evidence", "validates", "reinforces"},
    "Contradicts": {"contradicts", "conflict", "counterexample", "invalid"},
    "Transforms Into": {"transforms", "transition", "into", "becomes"},
    "Uses": {"uses", "consumes", "input"},
    "Produces": {"produces", "output", "result"},
    "Influences": {"influences", "causal", "affects"},
}

SEMANTIC_LIFECYCLE_ORDER = (
    "UNKNOWN",
    "OBSERVED",
    "PROVISIONAL",
    "SUPPORTED",
    "STABLE",
    "VALIDATED",
    "LOCKED",
    "GENERALIZED",
    "CANONICAL",
)

RESIDUAL_STATUSES = {
    "NEW",
    "OBSERVED",
    "SUPPORTED",
    "DISCOVERING",
    "CANDIDATE_CONCEPT",
    "MERGED",
    "RESOLVED",
    "REJECTED",
}


@dataclass(frozen=True)
class SemanticBoundary:
    valid_conditions: list[str] = field(default_factory=list)
    invalid_conditions: list[str] = field(default_factory=list)
    required_prerequisites: list[str] = field(default_factory=list)
    excluded_conditions: list[str] = field(default_factory=list)
    environment_constraints: list[str] = field(default_factory=list)
    transformation_constraints: list[str] = field(default_factory=list)
    confidence_limits: list[str] = field(default_factory=list)
    generalization_limits: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticContext:
    context_id: str
    object_id: str
    execution_id: str
    runtime_origin: str
    creation_timestamp: str
    primary_domain: str
    secondary_domains: list[str]
    semantic_role: str
    operation_family: str
    reasoning_family: str
    concept_family: str
    task_family: str
    object_family: str
    causal_family: str
    transformation_family: str
    semantic_neighbors: list[str]
    semantic_distance: dict[str, float]
    parent_abstractions: list[str]
    child_specializations: list[str]
    related_objects: list[str]
    context_confidence: float
    context_stability: float
    context_version: int
    boundary: SemanticBoundary
    semantic_edges: list[dict[str, Any]] = field(default_factory=list)
    lifecycle_stage: str = "OBSERVED"
    assignment_confidence: float = 0.0
    boundary_confidence: float = 0.0
    relationship_confidence: float = 0.0
    domain_confidence: float = 0.0
    role_confidence: float = 0.0
    generalization_confidence: float = 0.0
    overall_context_confidence: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "boundary": self.boundary.as_dict(),
            "semantic_context_constructed": True,
            "semantic_context_registry_ready": True,
            "meaning_required_before_continuation": True,
        }


@dataclass(frozen=True)
class SemanticResidual:
    residual_id: str
    associated_object: str
    execution_id: str
    origin_runtime: str
    observed_behavior: list[str]
    failed_assignment_reason: str
    candidate_domains: list[str]
    candidate_roles: list[str]
    candidate_neighbors: list[str]
    supporting_evidence: list[str]
    missing_evidence: list[str]
    confidence: float
    novelty_score: float
    reoccurrence_count: int
    status: str = "NEW"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResidualCluster:
    cluster_id: str
    residual_ids: list[str]
    shared_transformations: list[str]
    shared_evidence: list[str]
    shared_execution_patterns: list[str]
    shared_semantic_neighbors: list[str]
    shared_runtime_behavior: list[str]
    shared_causal_structures: list[str]
    similarity_score: float
    candidate_concept: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnknownRegion:
    region_id: str
    candidate_domain: str
    associated_contexts: list[str]
    associated_residuals: list[str]
    density_score: float
    novelty_score: float
    prediction_error: float
    evidence_gap: float
    truth_gap: float
    recommended_actions: list[str]
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticContextRegistry:
    """Stable in-memory registry for semantic contexts."""

    system_name = "semantic_context_registry"

    def __init__(self):
        self._contexts: dict[str, SemanticContext] = {}
        self._object_index: dict[str, str] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._version_history: dict[str, list[dict[str, Any]]] = {}
        self._residuals: dict[str, SemanticResidual] = {}
        self._residual_signature_index: dict[str, str] = {}
        self._residual_clusters: dict[str, ResidualCluster] = {}
        self._unknown_regions: dict[str, UnknownRegion] = {}
        self._prediction_errors: list[dict[str, Any]] = []
        self._ontology_gaps: list[dict[str, Any]] = []

    def register(self, context: SemanticContext) -> dict[str, Any]:
        previous = self._contexts.get(context.context_id)
        version = (previous.context_version + 1) if previous else context.context_version
        if version != context.context_version:
            context = replace(context, context_version=version)
        self._contexts[context.context_id] = context
        self._object_index[context.object_id] = context.context_id
        self._history.setdefault(context.context_id, [])
        self._history[context.context_id].append(
            {
                "event": "registered",
                "version": context.context_version,
                "primary_domain": context.primary_domain,
                "semantic_role": context.semantic_role,
                "context_confidence": context.context_confidence,
                "lifecycle_stage": context.lifecycle_stage,
            }
        )
        self._version_history.setdefault(context.context_id, [])
        self._version_history[context.context_id].append(
            {
                "new_version": context.context_version,
                "previous_version": previous.context_version if previous else None,
                "change_reason": "semantic_context_registered",
                "supporting_evidence": list(context.semantic_neighbors),
                "author_runtime": context.runtime_origin,
                "historical_snapshot": previous.as_dict() if previous else {},
            }
        )
        return context.as_dict()

    def register_residual(self, residual: SemanticResidual) -> dict[str, Any]:
        previous = self._residuals.get(residual.residual_id)
        if previous:
            residual = replace(
                residual,
                reoccurrence_count=previous.reoccurrence_count + 1,
                status=_residual_status(previous.reoccurrence_count + 1),
            )
        self._residuals[residual.residual_id] = residual
        self._residual_signature_index[residual.residual_id] = (
            residual.residual_id
        )
        self._cluster_residuals()
        self._detect_unknown_regions()
        return residual.as_dict()

    def evolve_context(
        self,
        context_id: str,
        change_reason: str,
        supporting_evidence: Iterable[Any] | None = None,
        author_runtime: str = "process_semantic_context_engine",
        target_stage: str | None = None,
        confidence_updates: Mapping[str, float] | None = None,
    ) -> dict[str, Any]:
        context = self._contexts.get(str(context_id))
        if context is None:
            return {}
        evidence = [str(item) for item in supporting_evidence or []]
        confidence_updates = (
            confidence_updates if isinstance(confidence_updates, Mapping) else {}
        )
        next_stage = target_stage or _next_lifecycle_stage(
            context.lifecycle_stage,
            evidence_count=len(evidence),
            confidence=max(
                clamp(confidence_updates.get("overall_context_confidence", 0.0)),
                context.overall_context_confidence,
                context.context_confidence,
            ),
        )
        historical_snapshot = context.as_dict()
        evolved = replace(
            context,
            context_version=context.context_version + 1,
            lifecycle_stage=next_stage,
            assignment_confidence=clamp(
                confidence_updates.get(
                    "assignment_confidence",
                    context.assignment_confidence or context.context_confidence,
                )
            ),
            boundary_confidence=clamp(
                confidence_updates.get(
                    "boundary_confidence",
                    context.boundary_confidence,
                )
            ),
            relationship_confidence=clamp(
                confidence_updates.get(
                    "relationship_confidence",
                    context.relationship_confidence,
                )
            ),
            domain_confidence=clamp(
                confidence_updates.get(
                    "domain_confidence",
                    context.domain_confidence,
                )
            ),
            role_confidence=clamp(
                confidence_updates.get(
                    "role_confidence",
                    context.role_confidence,
                )
            ),
            generalization_confidence=clamp(
                confidence_updates.get(
                    "generalization_confidence",
                    context.generalization_confidence,
                )
            ),
            overall_context_confidence=clamp(
                confidence_updates.get(
                    "overall_context_confidence",
                    context.overall_context_confidence or context.context_confidence,
                )
            ),
        )
        self._contexts[evolved.context_id] = evolved
        self._history.setdefault(evolved.context_id, [])
        self._history[evolved.context_id].append(
            {
                "event": "evolved",
                "version": evolved.context_version,
                "lifecycle_stage": evolved.lifecycle_stage,
                "change_reason": change_reason,
            }
        )
        self._version_history.setdefault(evolved.context_id, [])
        self._version_history[evolved.context_id].append(
            {
                "new_version": evolved.context_version,
                "previous_version": context.context_version,
                "change_reason": str(change_reason),
                "supporting_evidence": evidence,
                "author_runtime": str(author_runtime),
                "historical_snapshot": historical_snapshot,
            }
        )
        return evolved.as_dict()

    def record_prediction_error(
        self,
        context_id: str,
        predicted: Any,
        observed: Any,
        error_score: float,
        runtime_origin: str = "unknown_runtime",
    ) -> dict[str, Any]:
        record = {
            "context_id": str(context_id),
            "predicted": predicted,
            "observed": observed,
            "prediction_error": clamp(error_score),
            "runtime_origin": str(runtime_origin),
            "investigation_priority": clamp(0.50 + clamp(error_score) * 0.50),
        }
        self._prediction_errors.append(record)
        self._detect_unknown_regions()
        return record

    def get(self, context_id: str) -> dict[str, Any]:
        context = self._contexts.get(str(context_id))
        return context.as_dict() if context else {}

    def get_by_object(self, object_id: str) -> dict[str, Any]:
        context_id = self._object_index.get(str(object_id))
        return self.get(context_id) if context_id else {}

    def all(self) -> list[dict[str, Any]]:
        return [context.as_dict() for context in self._contexts.values()]

    def residuals(self) -> list[dict[str, Any]]:
        return [residual.as_dict() for residual in self._residuals.values()]

    def residual_clusters(self) -> list[dict[str, Any]]:
        return [cluster.as_dict() for cluster in self._residual_clusters.values()]

    def unknown_regions(self) -> list[dict[str, Any]]:
        return [region.as_dict() for region in self._unknown_regions.values()]

    def semantic_graph(self) -> dict[str, Any]:
        context_nodes = [
            {
                "node_id": context.context_id,
                "node_type": "Semantic Context",
                "domain": context.primary_domain,
                "role": context.semantic_role,
            }
            for context in self._contexts.values()
        ]
        residual_nodes = [
            {
                "node_id": residual.residual_id,
                "node_type": "Semantic Residual",
                "domain": residual.candidate_domains[0]
                if residual.candidate_domains
                else "Unknown",
                "role": residual.candidate_roles[0]
                if residual.candidate_roles
                else "Unknown",
            }
            for residual in self._residuals.values()
        ]
        edges = []
        for context in self._contexts.values():
            for edge in context.semantic_edges:
                for target in edge.get("targets", []) or []:
                    edges.append(
                        {
                            "source": context.context_id,
                            "target": str(target),
                            "edge_type": edge.get("relationship", "Support"),
                            "confidence": edge.get("confidence", 0.0),
                        }
                    )
            for parent in context.parent_abstractions:
                edges.append(
                    {
                        "source": context.context_id,
                        "target": parent,
                        "edge_type": "Hierarchy",
                        "confidence": context.context_confidence,
                    }
                )
            for child in context.child_specializations:
                edges.append(
                    {
                        "source": context.context_id,
                        "target": child,
                        "edge_type": "Inheritance",
                        "confidence": context.context_confidence,
                    }
                )
        for cluster in self._residual_clusters.values():
            for residual_id in cluster.residual_ids:
                edges.append(
                    {
                        "source": cluster.cluster_id,
                        "target": residual_id,
                        "edge_type": "Similarity",
                        "confidence": cluster.similarity_score,
                    }
                )
        return {
            "nodes": [*context_nodes, *residual_nodes],
            "edges": edges,
            "node_count": len(context_nodes) + len(residual_nodes),
            "edge_count": len(edges),
            "edge_types": sorted({edge["edge_type"] for edge in edges}),
        }

    def report(self) -> dict[str, Any]:
        self._discover_ontology_gaps()
        contexts = self.all()
        graph = self.semantic_graph()
        residuals = self.residuals()
        clusters = self.residual_clusters()
        unknown_regions = self.unknown_regions()
        return {
            "system": self.system_name,
            "semantic_contexts": contexts,
            "semantic_context_count": len(contexts),
            "registered_object_ids": sorted(self._object_index),
            "associated_domains": sorted(
                {context["primary_domain"] for context in contexts}
            ),
            "history": dict(self._history),
            "version_history": dict(self._version_history),
            "semantic_backbone_ready": bool(contexts),
            "semantic_graph": graph,
            "semantic_graph_statistics": {
                "node_count": graph["node_count"],
                "edge_count": graph["edge_count"],
                "edge_types": graph["edge_types"],
            },
            "residual_count": len(residuals),
            "semantic_residuals": residuals,
            "residual_clusters": clusters,
            "unknown_regions": unknown_regions,
            "candidate_concepts": [
                cluster["candidate_concept"]
                for cluster in clusters
                if cluster["status"] == "CANDIDATE_CONCEPT"
            ],
            "ontology_gaps": list(self._ontology_gaps),
            "prediction_errors": list(self._prediction_errors),
            "lifecycle_distribution": _distribution(
                context["lifecycle_stage"] for context in contexts
            ),
            "domain_distribution": _distribution(
                context["primary_domain"] for context in contexts
            ),
            "role_distribution": _distribution(
                context["semantic_role"] for context in contexts
            ),
        }

    def _discover_ontology_gaps(self) -> None:
        transformations = {
            context.transformation_family
            for context in self._contexts.values()
            if context.transformation_family
            and context.transformation_family != "transformation_unspecified"
        }
        specializations = {
            item
            for context in self._contexts.values()
            for item in context.child_specializations
        }
        observed = transformations | specializations
        expected_siblings = {"reflection", "rotation", "scaling", "translation"}
        if not observed.intersection(expected_siblings):
            self._ontology_gaps = []
            return
        self._ontology_gaps = [
            {
                "gap_id": f"ontology_gap:transformation:{missing}",
                "parent_abstraction": "transformation",
                "missing_sibling_concept": missing,
                "observed_siblings": sorted(observed.intersection(expected_siblings)),
                "gap_type": "missing_sibling_concept_detected",
                "confidence": round(
                    clamp(len(observed.intersection(expected_siblings)) / 3.0),
                    4,
                ),
                "hypothesis": {
                    "observed": sorted(observed.intersection(expected_siblings)),
                    "hypothesis": "missing_transformation_family",
                    "candidate": missing,
                    "provisional_until_truth_validated": True,
                },
            }
            for missing in sorted(expected_siblings - observed)
        ]

    def _cluster_residuals(self) -> None:
        residuals = list(self._residuals.values())
        clusters: dict[str, list[SemanticResidual]] = {}
        for residual in residuals:
            signature = _cluster_signature(residual)
            clusters.setdefault(signature, [])
            clusters[signature].append(residual)
        self._residual_clusters = {}
        for signature, members in clusters.items():
            if len(members) < 2:
                continue
            residual_sets = [set(member.supporting_evidence) for member in members]
            shared_evidence = sorted(set.intersection(*residual_sets)) if residual_sets else []
            shared_neighbors = sorted(
                set.intersection(
                    *[set(member.candidate_neighbors) for member in members]
                )
            )
            similarity = _cluster_similarity(members)
            candidate = _candidate_concept_name(members, shared_evidence)
            status = "CANDIDATE_CONCEPT" if len(members) >= 3 else "DISCOVERING"
            cluster = ResidualCluster(
                cluster_id=f"residual_cluster:{signature}",
                residual_ids=[member.residual_id for member in members],
                shared_transformations=[
                    item for item in shared_evidence
                    if item in {"growth", "motion", "reflection", "rotation", "propagation"}
                ],
                shared_evidence=shared_evidence,
                shared_execution_patterns=sorted(
                    set.intersection(
                        *[set(member.observed_behavior) for member in members]
                    )
                ),
                shared_semantic_neighbors=shared_neighbors,
                shared_runtime_behavior=sorted(
                    {member.origin_runtime for member in members}
                ),
                shared_causal_structures=[
                    item for item in shared_evidence
                    if item in {"causal", "depends", "supports", "collision"}
                ],
                similarity_score=similarity,
                candidate_concept=candidate,
                status=status,
            )
            self._residual_clusters[cluster.cluster_id] = cluster
            if status == "CANDIDATE_CONCEPT":
                for member in members:
                    self._residuals[member.residual_id] = replace(
                        member,
                        status="CANDIDATE_CONCEPT",
                    )

    def _detect_unknown_regions(self) -> None:
        self._unknown_regions = {}
        for cluster in self._residual_clusters.values():
            residuals = [
                self._residuals[residual_id]
                for residual_id in cluster.residual_ids
                if residual_id in self._residuals
            ]
            if not residuals:
                continue
            density = clamp(len(residuals) / 4.0)
            novelty = clamp(
                sum(residual.novelty_score for residual in residuals)
                / len(residuals)
            )
            prediction_error = max(
                [
                    error["prediction_error"]
                    for error in self._prediction_errors
                    if error["context_id"] in {
                        residual.associated_object for residual in residuals
                    }
                ]
                or [0.0]
            )
            evidence_gap = clamp(
                sum(len(residual.missing_evidence) for residual in residuals)
                / max(len(residuals) * 4, 1)
            )
            truth_gap = 1.0 if cluster.status == "CANDIDATE_CONCEPT" else 0.75
            candidate_domain = (
                residuals[0].candidate_domains[0]
                if residuals[0].candidate_domains
                else "Unknown"
            )
            region = UnknownRegion(
                region_id=f"unknown_region:{cluster.cluster_id.split(':')[-1]}",
                candidate_domain=candidate_domain,
                associated_contexts=[
                    context.context_id
                    for context in self._contexts.values()
                    if context.primary_domain == candidate_domain
                ],
                associated_residuals=[residual.residual_id for residual in residuals],
                density_score=round(density, 4),
                novelty_score=round(novelty, 4),
                prediction_error=round(prediction_error, 4),
                evidence_gap=round(evidence_gap, 4),
                truth_gap=truth_gap,
                recommended_actions=[
                    "collect_boundary_evidence",
                    "route_candidate_concept_to_truth_runtime",
                    "compare_against_neighboring_contexts",
                ],
                confidence=round(
                    clamp((density * 0.35) + (novelty * 0.35) + (evidence_gap * 0.30)),
                    4,
                ),
            )
            if region.density_score >= 0.50 or region.prediction_error >= 0.40:
                self._unknown_regions[region.region_id] = region


class CognitiveArtifactSemanticContextEngine:
    """Assign semantic identity to cognitive artifacts without mutating them."""

    system_name = "process_semantic_context_engine"

    def __init__(
        self,
        registry: SemanticContextRegistry | None = None,
        assignment_threshold: float = 0.72,
    ):
        self.registry = registry or SemanticContextRegistry()
        self.assignment_threshold = clamp(assignment_threshold)

    def contextualize(
        self,
        artifact: Mapping[str, Any],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        artifact = artifact if isinstance(artifact, Mapping) else {}
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        evidence_tokens = _tokens_from(artifact, runtime_context)
        object_id = _object_id(artifact, evidence_tokens)
        execution_id = str(
            artifact.get("execution_id")
            or runtime_context.get("execution_id")
            or "semantic_execution_unknown"
        )
        runtime_origin = str(
            artifact.get("runtime_origin")
            or runtime_context.get("runtime_origin")
            or artifact.get("source_runtime")
            or runtime_context.get("source_runtime")
            or "unknown_runtime"
        )
        domain_scores = _score_evidence(evidence_tokens, DOMAIN_EVIDENCE)
        role_scores = _score_evidence(evidence_tokens, ROLE_EVIDENCE)
        primary_domain = _winner(domain_scores, "Knowledge Integration")
        secondary_domains = [
            domain
            for domain, score in sorted(
                domain_scores.items(),
                key=lambda item: (-item[1], item[0]),
            )
            if domain != primary_domain and score > 0.0
        ]
        semantic_role = _winner(role_scores, "Unknown")
        families = self._families(
            evidence_tokens,
            primary_domain,
            semantic_role,
        )
        related_objects = _related_objects(artifact, runtime_context)
        semantic_edges = self._semantic_edges(evidence_tokens, related_objects)
        neighbors = self._semantic_neighbors(
            evidence_tokens,
            primary_domain,
            semantic_role,
            secondary_domains,
        )
        distance = self._semantic_distance(
            evidence_tokens,
            primary_domain,
            secondary_domains,
            neighbors,
        )
        confidence = self._confidence(
            domain_scores,
            role_scores,
            artifact,
            runtime_context,
        )
        confidence_breakdown = self._confidence_breakdown(
            domain_scores,
            role_scores,
            confidence,
            artifact,
            runtime_context,
            semantic_edges,
        )
        context = SemanticContext(
            context_id=_context_id(object_id, runtime_origin),
            object_id=object_id,
            execution_id=execution_id,
            runtime_origin=runtime_origin,
            creation_timestamp=_timestamp(runtime_context),
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            semantic_role=semantic_role,
            operation_family=families["operation_family"],
            reasoning_family=families["reasoning_family"],
            concept_family=families["concept_family"],
            task_family=families["task_family"],
            object_family=families["object_family"],
            causal_family=families["causal_family"],
            transformation_family=families["transformation_family"],
            semantic_neighbors=neighbors,
            semantic_distance=distance,
            parent_abstractions=self._parent_abstractions(
                primary_domain,
                semantic_role,
                families,
            ),
            child_specializations=self._child_specializations(
                artifact,
                evidence_tokens,
            ),
            related_objects=related_objects,
            context_confidence=confidence,
            context_stability=self._stability(confidence, artifact, runtime_context),
            context_version=1,
            boundary=self._boundary(artifact, runtime_context, confidence),
            semantic_edges=semantic_edges,
            lifecycle_stage=_initial_lifecycle_stage(confidence),
            assignment_confidence=confidence_breakdown["assignment_confidence"],
            boundary_confidence=confidence_breakdown["boundary_confidence"],
            relationship_confidence=confidence_breakdown[
                "relationship_confidence"
            ],
            domain_confidence=confidence_breakdown["domain_confidence"],
            role_confidence=confidence_breakdown["role_confidence"],
            generalization_confidence=confidence_breakdown[
                "generalization_confidence"
            ],
            overall_context_confidence=confidence_breakdown[
                "overall_context_confidence"
            ],
        )
        registered = self.registry.register(context)
        residual = {}
        if confidence < self.assignment_threshold:
            residual = self._residual_from_assignment(
                artifact,
                runtime_context,
                registered,
                evidence_tokens,
                domain_scores,
                role_scores,
                confidence,
            )
            residual = self.registry.register_residual(residual)
        return {
            "system": self.system_name,
            "artifact_unchanged": dict(artifact),
            "semantic_context": registered,
            "semantic_context_id": registered["context_id"],
            "semantic_context_registered": True,
            "semantic_context_required": True,
            "semantic_residual": residual,
            "semantic_residual_created": bool(residual),
            "truth_candidate_blocked_by_semantic_context": bool(residual),
            "registry_report": self.registry.report(),
        }

    def contextualize_many(
        self,
        artifacts: Iterable[Mapping[str, Any]],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        reports = [
            self.contextualize(artifact, runtime_context=runtime_context)
            for artifact in artifacts
            if isinstance(artifact, Mapping)
        ]
        return {
            "system": self.system_name,
            "semantic_context_reports": reports,
            "semantic_context_count": len(reports),
            "semantic_context_coverage": 1.0 if reports else 0.0,
            "registry_report": self.registry.report(),
        }

    def registry_report(self) -> dict[str, Any]:
        return self.registry.report()

    def process_semantic_context_report(self) -> dict[str, Any]:
        registry_report = self.registry.report()
        contexts = registry_report["semantic_contexts"]
        graph_stats = registry_report["semantic_graph_statistics"]
        residuals = registry_report["semantic_residuals"]
        unknown_regions = registry_report["unknown_regions"]
        return {
            "PROCESS_SEMANTIC_CONTEXT_REPORT": True,
            "system": self.system_name,
            "semantic_contexts_created": len(contexts),
            "objects_assigned": registry_report["registered_object_ids"],
            "domain_distribution": registry_report["domain_distribution"],
            "role_distribution": registry_report["role_distribution"],
            "boundary_models": {
                context["context_id"]: context["boundary"]
                for context in contexts
            },
            "hierarchy_depth": max(
                [len(context["parent_abstractions"]) for context in contexts]
                or [0]
            ),
            "semantic_graph_statistics": graph_stats,
            "residual_count": len(residuals),
            "residual_clusters": registry_report["residual_clusters"],
            "unknown_regions": unknown_regions,
            "candidate_concepts": registry_report["candidate_concepts"],
            "ontology_gaps": registry_report["ontology_gaps"],
            "prediction_errors": registry_report["prediction_errors"],
            "context_confidence_distribution": _confidence_distribution(contexts),
            "lifecycle_distribution": registry_report["lifecycle_distribution"],
            "generalization_opportunities": [
                context["context_id"]
                for context in contexts
                if context["generalization_confidence"] >= 0.70
                and context["lifecycle_stage"] in {"SUPPORTED", "STABLE", "VALIDATED"}
            ],
            "training_recommendations": _training_recommendations(
                residuals,
                unknown_regions,
            ),
            "integration_health": self.integration_health(),
        }

    def integration_health(self) -> dict[str, Any]:
        report = self.registry.report()
        context_count = report["semantic_context_count"]
        residual_count = report["residual_count"]
        graph_ready = report["semantic_graph_statistics"]["node_count"] >= context_count
        return {
            "concept_formation_consumes_semantic_contexts": True,
            "program_synthesis_consumes_semantic_contexts": True,
            "evidence_builder_consumes_semantic_contexts": True,
            "knowledge_integration_canonical_semantic_context": True,
            "truth_runtime_receives_contextualized_candidates": True,
            "memory_runtime_receives_contextualized_experiences": True,
            "situation_awareness_receives_contextualized_situations": True,
            "decision_intelligence_receives_contextualized_decisions": True,
            "executive_world_governance_context_aware": True,
            "world_model_semantic_context_ready": context_count > 0,
            "dna_semantic_experience_ready": context_count > 0,
            "meta_cognition_semantic_quality_ready": True,
            "semantic_graph_ready": graph_ready,
            "residual_discovery_active": residual_count >= 0,
        }

    def runtime_integration_packet(self) -> dict[str, Any]:
        report = self.registry.report()
        contexts = report["semantic_contexts"]
        return {
            "semantic_contexts": contexts,
            "world_model_entities": [
                {
                    "entity_id": context["object_id"],
                    "meaning": context,
                    "boundaries": context["boundary"],
                    "relationships": context["semantic_edges"],
                    "domains": [
                        context["primary_domain"],
                        *context["secondary_domains"],
                    ],
                    "hierarchies": {
                        "parents": context["parent_abstractions"],
                        "children": context["child_specializations"],
                    },
                    "confidence": context["overall_context_confidence"],
                    "history": report["history"].get(context["context_id"], []),
                }
                for context in contexts
            ],
            "dna_semantic_experiences": [
                {
                    "trait_anchor": context["concept_family"],
                    "semantic_domain": context["primary_domain"],
                    "context_family": context["operation_family"],
                    "successful_abstractions": context["parent_abstractions"],
                    "recurring_situations": context["semantic_neighbors"],
                    "long_term_semantic_evolution": context["lifecycle_stage"],
                }
                for context in contexts
            ],
            "meta_cognition": {
                "context_quality": _average(
                    context["overall_context_confidence"] for context in contexts
                ),
                "boundary_quality": _average(
                    context["boundary_confidence"] for context in contexts
                ),
                "semantic_consistency": 1.0
                if not report["prediction_errors"]
                else round(
                    1.0 - _average(
                        item["prediction_error"]
                        for item in report["prediction_errors"]
                    ),
                    4,
                ),
                "residual_discovery": report["residual_count"],
                "ontology_evolution": len(report["ontology_gaps"]),
                "generalization_quality": _average(
                    context["generalization_confidence"] for context in contexts
                ),
                "context_stability": _average(
                    context["context_stability"] for context in contexts
                ),
                "unknown_region_reduction": 1.0
                if not report["unknown_regions"]
                else round(1.0 / (1 + len(report["unknown_regions"])), 4),
            },
            "executive_world_governance": {
                "attention_allocation": _attention_allocation(report),
                "goal_prioritization": [
                    "resolve_semantic_residuals",
                    "stabilize_context_boundaries",
                    "validate_candidate_concepts",
                ],
                "mental_model_selection": [
                    context["reasoning_family"] for context in contexts
                ],
                "experience_retrieval": [
                    context["object_id"] for context in contexts
                ],
                "runtime_steering": "semantic_context_aware",
                "policy_activation": "semantic_boundary_governed",
                "strategic_planning": "unknown_region_reduction",
            },
        }

    def evolve_context(
        self,
        context_id: str,
        change_reason: str,
        supporting_evidence: Iterable[Any] | None = None,
        author_runtime: str = "process_semantic_context_engine",
        target_stage: str | None = None,
        confidence_updates: Mapping[str, float] | None = None,
    ) -> dict[str, Any]:
        return self.registry.evolve_context(
            context_id,
            change_reason=change_reason,
            supporting_evidence=supporting_evidence,
            author_runtime=author_runtime,
            target_stage=target_stage,
            confidence_updates=confidence_updates,
        )

    def record_prediction_error(
        self,
        context_id: str,
        predicted: Any,
        observed: Any,
        error_score: float,
        runtime_origin: str = "unknown_runtime",
    ) -> dict[str, Any]:
        return self.registry.record_prediction_error(
            context_id,
            predicted,
            observed,
            error_score,
            runtime_origin=runtime_origin,
        )

    def _families(self, tokens, primary_domain, semantic_role):
        normalized_domain = _normalize(primary_domain)
        return {
            "operation_family": _family_from_tokens(
                tokens,
                ("transform", "validate", "synthesize", "integrate", "store"),
                semantic_role.lower(),
            ),
            "reasoning_family": _family_from_tokens(
                tokens,
                ("spatial", "temporal", "causal", "symbolic", "planning"),
                normalized_domain,
            ),
            "concept_family": _family_from_tokens(
                tokens,
                ("symmetry", "mapping", "quantity", "truth", "memory"),
                normalized_domain,
            ),
            "task_family": _family_from_tokens(
                tokens,
                ("completion", "validation", "retrieval", "planning"),
                normalized_domain,
            ),
            "object_family": _family_from_tokens(
                tokens,
                ("object", "program", "evidence", "truth", "memory"),
                semantic_role.lower(),
            ),
            "causal_family": _family_from_tokens(
                tokens,
                ("dependency", "support", "contradiction", "influence"),
                "causal_neutral",
            ),
            "transformation_family": _family_from_tokens(
                tokens,
                ("reflection", "rotation", "remapping", "growth", "motion"),
                "transformation_unspecified",
            ),
        }

    def _semantic_neighbors(self, tokens, primary_domain, semantic_role, secondary_domains):
        neighbors = {
            _normalize(primary_domain),
            _normalize(semantic_role),
            *[_normalize(domain) for domain in secondary_domains],
        }
        for token in tokens:
            for evidence in DOMAIN_EVIDENCE.values():
                if token in evidence:
                    neighbors.add(token)
            for evidence in ROLE_EVIDENCE.values():
                if token in evidence:
                    neighbors.add(token)
        return sorted(item for item in neighbors if item)

    def _semantic_distance(self, tokens, primary_domain, secondary_domains, neighbors):
        token_set = set(tokens)
        distances = {}
        for domain in [primary_domain, *secondary_domains]:
            evidence = DOMAIN_EVIDENCE.get(domain, set())
            overlap = len(token_set & evidence)
            union = max(len(token_set | evidence), 1)
            distances[_normalize(domain)] = round(1.0 - (overlap / union), 4)
        for neighbor in neighbors[:8]:
            if neighbor not in distances:
                distances[neighbor] = 0.0 if neighbor in token_set else 0.5
        return distances

    def _parent_abstractions(self, primary_domain, semantic_role, families):
        parents = [
            "cognitive_artifact",
            _normalize(primary_domain),
            _normalize(semantic_role),
        ]
        for key in ("reasoning_family", "operation_family", "concept_family"):
            value = families.get(key)
            if value and value not in parents:
                parents.append(value)
        return [item for item in parents if item]

    def _child_specializations(self, artifact, tokens):
        children = set()
        for key in ("concept", "name", "context_name", "program_name", "truth_id"):
            value = artifact.get(key)
            if value:
                children.add(_normalize(value))
        for token in tokens:
            if token in {
                "horizontal",
                "vertical",
                "reflection",
                "rotation",
                "growth",
                "replication",
                "cardinality",
                "truth",
            }:
                children.add(token)
        return sorted(children)

    def _semantic_edges(self, tokens, related_objects):
        token_set = set(tokens)
        edges = []
        for relation, evidence in RELATION_EVIDENCE.items():
            overlap = sorted(token_set & evidence)
            if not overlap:
                continue
            edges.append(
                {
                    "relationship": relation,
                    "evidence": overlap,
                    "confidence": round(min(0.60 + len(overlap) * 0.10, 0.95), 4),
                    "targets": list(related_objects),
                }
            )
        return edges

    def _confidence(self, domain_scores, role_scores, artifact, runtime_context):
        explicit = max(
            clamp(artifact.get("confidence", 0.0)),
            clamp(artifact.get("context_confidence", 0.0)),
            clamp(runtime_context.get("confidence", 0.0)),
            clamp(runtime_context.get("semantic_context_score", 0.0)),
        )
        domain_signal = max(domain_scores.values() or [0.0])
        role_signal = max(role_scores.values() or [0.0])
        evidence_signal = min((domain_signal + role_signal) / 6.0, 1.0)
        if explicit > 0.0:
            return round(clamp(max(explicit, 0.20 + evidence_signal * 0.50)), 4)
        return round(clamp(0.20 + evidence_signal * 0.55), 4)

    def _confidence_breakdown(
        self,
        domain_scores,
        role_scores,
        confidence,
        artifact,
        runtime_context,
        semantic_edges,
    ):
        domain_signal = min(max(domain_scores.values() or [0.0]) / 4.0, 1.0)
        role_signal = min(max(role_scores.values() or [0.0]) / 3.0, 1.0)
        boundary_signal = 1.0 if (
            artifact.get("preconditions")
            or artifact.get("valid_conditions")
            or runtime_context.get("valid_conditions")
        ) else 0.35
        relationship_signal = min(len(semantic_edges) / 4.0, 1.0)
        generalization_signal = 1.0 if (
            artifact.get("generalization_limits")
            or runtime_context.get("generalization_limits")
            or domain_signal >= 0.75
        ) else 0.40
        return {
            "assignment_confidence": confidence,
            "boundary_confidence": round(clamp(boundary_signal), 4),
            "relationship_confidence": round(clamp(relationship_signal), 4),
            "domain_confidence": round(clamp(domain_signal), 4),
            "role_confidence": round(clamp(role_signal), 4),
            "generalization_confidence": round(
                clamp(generalization_signal * confidence),
                4,
            ),
            "overall_context_confidence": round(
                clamp(
                    confidence * 0.35
                    + domain_signal * 0.20
                    + role_signal * 0.15
                    + boundary_signal * 0.15
                    + relationship_signal * 0.10
                    + generalization_signal * 0.05
                ),
                4,
            ),
        }

    def _stability(self, confidence, artifact, runtime_context):
        support = max(
            clamp(artifact.get("support_score", 0.0)),
            clamp(runtime_context.get("support_score", 0.0)),
            clamp(runtime_context.get("context_stability", 0.0)),
        )
        return round(clamp((confidence * 0.70) + (support * 0.30)), 4)

    def _boundary(self, artifact, runtime_context, confidence):
        return SemanticBoundary(
            valid_conditions=_list_from(
                artifact.get("valid_conditions")
                or runtime_context.get("valid_conditions")
                or artifact.get("preconditions")
            ),
            invalid_conditions=_list_from(
                artifact.get("invalid_conditions")
                or runtime_context.get("invalid_conditions")
                or artifact.get("counterexamples")
            ),
            required_prerequisites=_list_from(
                artifact.get("required_prerequisites")
                or artifact.get("preconditions")
                or runtime_context.get("required_prerequisites")
            ),
            excluded_conditions=_list_from(
                artifact.get("excluded_conditions")
                or runtime_context.get("excluded_conditions")
            ),
            environment_constraints=_list_from(
                artifact.get("environment_constraints")
                or runtime_context.get("environment_constraints")
                or artifact.get("constraints")
            ),
            transformation_constraints=_list_from(
                artifact.get("transformation_constraints")
                or artifact.get("invariants")
                or runtime_context.get("transformation_constraints")
            ),
            confidence_limits=[
                f"context_confidence>={round(confidence, 4)}",
                "confidence_is_not_truth",
            ],
            generalization_limits=_list_from(
                artifact.get("generalization_limits")
                or runtime_context.get("generalization_limits")
                or ["requires_supporting_evidence"]
            ),
        )

    def _residual_from_assignment(
        self,
        artifact,
        runtime_context,
        context,
        evidence_tokens,
        domain_scores,
        role_scores,
        confidence,
    ):
        candidate_domains = [
            domain for domain, score in sorted(
                domain_scores.items(),
                key=lambda item: (-item[1], item[0]),
            )
            if score > 0.0
        ][:5]
        candidate_roles = [
            role for role, score in sorted(
                role_scores.items(),
                key=lambda item: (-item[1], item[0]),
            )
            if score > 0.0
        ][:5]
        missing = []
        if not candidate_domains:
            missing.append("domain_evidence")
        if not candidate_roles:
            missing.append("role_evidence")
        if not artifact.get("preconditions") and not artifact.get("valid_conditions"):
            missing.append("boundary_evidence")
        if not context.get("semantic_edges"):
            missing.append("relationship_evidence")
        signature_parts = sorted(
            set(evidence_tokens)
            & {
                "downward",
                "collision",
                "propagation",
                "motion",
                "spatial",
                "causal",
                "unknown",
                "anomaly",
            }
        ) or [context["object_id"]]
        signature = "|".join(signature_parts)
        residual_identity = (
            f"{signature}:{context['object_id']}:{context['execution_id']}"
        )
        residual_id = (
            "semantic_residual:"
            f"{sha1(residual_identity.encode('utf-8')).hexdigest()[:16]}"
        )
        return SemanticResidual(
            residual_id=residual_id,
            associated_object=context["object_id"],
            execution_id=context["execution_id"],
            origin_runtime=context["runtime_origin"],
            observed_behavior=sorted(set(evidence_tokens)),
            failed_assignment_reason=(
                "assignment_confidence_below_required_threshold"
            ),
            candidate_domains=candidate_domains,
            candidate_roles=candidate_roles,
            candidate_neighbors=context.get("semantic_neighbors", []),
            supporting_evidence=sorted(set(evidence_tokens)),
            missing_evidence=missing,
            confidence=confidence,
            novelty_score=round(clamp(1.0 - confidence), 4),
            reoccurrence_count=1,
            status="NEW",
        )


def _tokens_from(*values) -> list[str]:
    tokens = set()
    for value in values:
        _collect_tokens(value, tokens)
    return sorted(tokens)


def _collect_tokens(value, tokens):
    if isinstance(value, Mapping):
        for key, item in value.items():
            _collect_tokens(key, tokens)
            _collect_tokens(item, tokens)
        return
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            _collect_tokens(item, tokens)
        return
    text = str(value or "").replace("-", "_").replace("/", "_")
    for raw in text.lower().split("_"):
        for token in raw.split():
            token = "".join(ch for ch in token if ch.isalnum())
            if token:
                tokens.add(token)


def _score_evidence(tokens, evidence_map):
    token_set = set(tokens)
    return {
        label: float(len(token_set & evidence))
        for label, evidence in evidence_map.items()
    }


def _winner(scores, fallback):
    if not scores:
        return fallback
    label, score = max(scores.items(), key=lambda item: (item[1], item[0]))
    return label if score > 0.0 else fallback


def _object_id(artifact, tokens):
    for key in ("object_id", "artifact_id", "concept", "program_id", "truth_id", "memory_id"):
        value = artifact.get(key)
        if value:
            return str(value)
    digest = sha1(" ".join(tokens).encode("utf-8")).hexdigest()[:12]
    return f"artifact:{digest}"


def _context_id(object_id, runtime_origin):
    digest = sha1(f"{runtime_origin}:{object_id}".encode("utf-8")).hexdigest()[:16]
    return f"semantic_context:{digest}"


def _timestamp(runtime_context):
    value = runtime_context.get("creation_timestamp") or runtime_context.get("timestamp")
    if value:
        return str(value)
    return datetime.now(timezone.utc).isoformat()


def _related_objects(artifact, runtime_context):
    related = []
    for key in ("related_objects", "dependencies", "supports", "uses", "produces"):
        related.extend(_list_from(artifact.get(key)))
        related.extend(_list_from(runtime_context.get(key)))
    return sorted({str(item) for item in related if item})


def _list_from(value):
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [str(key) for key in value.keys()]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("&", "and")


def _family_from_tokens(tokens, candidates, fallback):
    token_set = set(tokens)
    for candidate in candidates:
        if candidate in token_set:
            return candidate
    return _normalize(fallback)


def _initial_lifecycle_stage(confidence):
    confidence = clamp(confidence)
    if confidence >= 0.90:
        return "SUPPORTED"
    if confidence >= 0.72:
        return "PROVISIONAL"
    if confidence >= 0.40:
        return "OBSERVED"
    return "UNKNOWN"


def _next_lifecycle_stage(current, evidence_count, confidence):
    current = str(current or "UNKNOWN").upper()
    try:
        index = SEMANTIC_LIFECYCLE_ORDER.index(current)
    except ValueError:
        index = 0
    if evidence_count >= 5 and confidence >= 0.90:
        index += 2
    elif evidence_count > 0 and confidence >= 0.70:
        index += 1
    return SEMANTIC_LIFECYCLE_ORDER[
        min(index, len(SEMANTIC_LIFECYCLE_ORDER) - 1)
    ]


def _residual_status(reoccurrence_count):
    if reoccurrence_count >= 3:
        return "SUPPORTED"
    if reoccurrence_count >= 2:
        return "OBSERVED"
    return "NEW"


def _cluster_signature(residual):
    evidence = set(residual.supporting_evidence)
    anchors = sorted(
        evidence
        & {
            "downward",
            "collision",
            "propagation",
            "motion",
            "spatial",
            "causal",
            "state",
            "support",
            "unsupported",
        }
    )
    if not anchors:
        anchors = sorted(set(residual.candidate_neighbors[:4]))
    return sha1(" ".join(anchors).encode("utf-8")).hexdigest()[:16]


def _cluster_similarity(members):
    if len(members) < 2:
        return 1.0
    scores = []
    for index, left in enumerate(members):
        for right in members[index + 1:]:
            left_set = set(left.supporting_evidence) | set(left.candidate_neighbors)
            right_set = set(right.supporting_evidence) | set(right.candidate_neighbors)
            union = max(len(left_set | right_set), 1)
            scores.append(len(left_set & right_set) / union)
    return round(clamp(sum(scores) / len(scores)), 4) if scores else 1.0


def _candidate_concept_name(members, shared_evidence):
    evidence = set(shared_evidence)
    if {"downward", "propagation", "collision"} & evidence:
        return "candidate_concept:gravity_simulation"
    if evidence:
        return "candidate_concept:" + "_".join(sorted(evidence)[:3])
    return "candidate_concept:unexplained_semantic_cluster"


def _distribution(values):
    result: dict[str, int] = {}
    for value in values:
        key = str(value or "Unknown")
        result[key] = result.get(key, 0) + 1
    return result


def _average(values):
    values = [clamp(value) for value in values]
    return round(sum(values) / len(values), 4) if values else 0.0


def _confidence_distribution(contexts):
    buckets = {"low": 0, "medium": 0, "high": 0}
    for context in contexts:
        confidence = clamp(context.get("overall_context_confidence", 0.0))
        if confidence >= 0.85:
            buckets["high"] += 1
        elif confidence >= 0.60:
            buckets["medium"] += 1
        else:
            buckets["low"] += 1
    return buckets


def _training_recommendations(residuals, unknown_regions):
    recommendations = []
    if residuals:
        recommendations.append("increase_examples_for_low_confidence_assignments")
    if unknown_regions:
        recommendations.append("generate_tasks_for_unknown_semantic_regions")
    if not recommendations:
        recommendations.append("continue_semantic_context_generalization")
    return recommendations


def _attention_allocation(report):
    allocation = {}
    for residual in report["semantic_residuals"]:
        allocation[residual["associated_object"]] = round(
            0.50 + residual["novelty_score"] * 0.50,
            4,
        )
    for region in report["unknown_regions"]:
        allocation[region["region_id"]] = region["confidence"]
    return allocation


__all__ = [
    "CognitiveArtifactSemanticContextEngine",
    "SemanticBoundary",
    "SemanticContext",
    "SemanticContextRegistry",
    "SemanticResidual",
    "ResidualCluster",
    "UnknownRegion",
]
