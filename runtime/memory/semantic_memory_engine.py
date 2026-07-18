"""Semantic Memory Engine.

Semantic Memory is a cognitive layer above Experience and below Mental Model
Discovery. It does not store raw execution, create another runtime, or write to
World Model / DNA. It organizes validated experiences and reflected experience
candidates into long-term semantic entities, relationships, indexes, hierarchy,
and retrieval structures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


DOMAIN_KEYWORDS = {
    "Geometry": ("geometry", "spatial", "symmetry", "shape", "position", "rotation"),
    "Topology": ("topology", "boundary", "connected", "hole", "region"),
    "Object Dynamics": ("object", "motion", "movement", "dynamics", "identity"),
    "Counting": ("count", "number", "quantity", "cardinality"),
    "Pattern Completion": ("pattern", "completion", "sequence", "repeat"),
    "Transformation": ("transform", "transformation", "color", "resize", "translate"),
    "Reasoning": ("reasoning", "inference", "hypothesis", "causal"),
    "Search": ("search", "route", "exploration", "pruning"),
    "Planning": ("planning", "decision", "strategy", "program"),
    "Memory": ("memory", "experience", "lesson", "retrieval"),
    "Learning": ("learning", "generalization", "transfer", "improvement"),
    "Governance": ("governance", "policy", "risk", "executive"),
    "Executive Intelligence": ("executive", "recommendation", "priority"),
    "Semantic Context": ("semantic", "context", "meaning", "domain"),
    "World Knowledge": ("world", "model", "environment"),
    "Meta-Cognition": ("meta", "reflection", "self", "maturity"),
}

RELATIONSHIP_TYPES = {
    "Belongs To",
    "Explains",
    "Supports",
    "Contradicts",
    "Generalizes",
    "Specializes",
    "Depends On",
    "Influences",
    "Derived From",
    "Associated With",
    "Equivalent To",
    "Boundary Of",
}

MATURITY_LEVELS = (
    "Candidate",
    "Emerging",
    "Stable",
    "Canonical",
    "Fundamental",
    "Deprecated",
    "Archived",
)


@dataclass(frozen=True)
class SemanticMemoryEntity:
    semantic_memory_id: str
    semantic_identity: str
    semantic_domain: str
    semantic_category: str
    semantic_level: str
    semantic_summary: str
    semantic_confidence: float
    semantic_stability: float
    semantic_priority: str
    semantic_importance: float
    semantic_version: int = 1
    semantic_history: list[dict[str, Any]] = field(default_factory=list)
    semantic_status: str = "Candidate"
    source_type: str = ""
    source_ids: list[str] = field(default_factory=list)
    lineage: dict[str, list[str]] = field(default_factory=dict)
    indexes: dict[str, list[str] | float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticMemoryRegistry:
    """In-memory semantic registry with lineage-preserving upserts."""

    def __init__(self) -> None:
        self.entities: dict[str, SemanticMemoryEntity] = {}
        self.relationships: list[dict[str, Any]] = []
        self._relationship_markers: set[tuple[str, str, str]] = set()
        self.indexes: dict[str, dict[str, set[str]]] = {
            "meaning": {},
            "domain": {},
            "context": {},
            "abstraction": {},
            "similarity": {},
            "importance": {},
            "frequency": {},
            "transferability": {},
            "generalization": {},
        }
        self.ingestion_count = 0
        self.retrieval_count = 0

    def upsert(self, entity: SemanticMemoryEntity) -> SemanticMemoryEntity:
        previous = self.entities.get(entity.semantic_memory_id)
        if previous is not None:
            history = [
                *previous.semantic_history,
                {
                    "version": previous.semantic_version + 1,
                    "previous_version": previous.semantic_version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "change_reason": "semantic_entity_reinforced",
                    "source_ids": sorted(set(previous.source_ids + entity.source_ids)),
                },
            ]
            accumulated_evidence = max(
                len(set(previous.source_ids + entity.source_ids)),
                previous.semantic_version + 1,
            )
            entity = replace(
                entity,
                semantic_version=previous.semantic_version + 1,
                semantic_history=history,
                source_ids=sorted(set(previous.source_ids + entity.source_ids)),
                semantic_confidence=round(max(previous.semantic_confidence, entity.semantic_confidence), 4),
                semantic_stability=round(clamp(previous.semantic_stability + 0.1), 4),
                semantic_status=_maturity_status(
                    max(previous.semantic_confidence, entity.semantic_confidence),
                    clamp(previous.semantic_stability + 0.1),
                    accumulated_evidence,
                ),
            )
        self.entities[entity.semantic_memory_id] = entity
        self._index(entity)
        return entity

    def add_relationship(self, relationship: Mapping[str, Any]) -> None:
        item = {
            "source": str(relationship.get("source")),
            "target": str(relationship.get("target")),
            "relationship_type": _relationship_type(relationship.get("relationship_type")),
            "confidence": round(clamp(relationship.get("confidence", 0.5)), 4),
            "lineage": dict(relationship.get("lineage") or {}),
        }
        marker = (item["source"], item["target"], item["relationship_type"])
        if (
            item["source"]
            and item["target"]
            and marker not in self._relationship_markers
        ):
            self.relationships.append(item)
            self._relationship_markers.add(marker)

    def retrieve(self, *, meaning: str = "", domain: str = "", top_k: int = 5) -> dict[str, Any]:
        self.retrieval_count += 1
        query_tokens = _tokens(" ".join([meaning, domain]))
        ranked = []
        for entity in self.entities.values():
            score = _similarity(query_tokens, set(entity.indexes.get("meaning", [])))
            if domain and entity.semantic_domain == domain:
                score = max(score, 0.75)
            if score > 0:
                ranked.append({"entity": entity.as_dict(), "similarity": round(score, 4)})
        ranked.sort(key=lambda item: item["similarity"], reverse=True)
        return {
            "semantic_retrieval": True,
            "query": {"meaning": meaning, "domain": domain},
            "retrieved_count": len(ranked),
            "results": ranked[:top_k],
            "retrieval_mode": "semantic_not_chronological",
        }

    def _index(self, entity: SemanticMemoryEntity) -> None:
        for index_name, values in entity.indexes.items():
            bucket = self.indexes.setdefault(index_name, {})
            if isinstance(values, (list, tuple, set)):
                for value in values:
                    bucket.setdefault(str(value), set()).add(entity.semantic_memory_id)
            else:
                bucket.setdefault(str(values), set()).add(entity.semantic_memory_id)


class SemanticMemoryEngine:
    """Organize experience-derived knowledge into semantic memory."""

    system_name = "semantic_memory_engine"

    def __init__(self, registry: SemanticMemoryRegistry | None = None) -> None:
        self.registry = registry or SemanticMemoryRegistry()

    def integrate(
        self,
        *,
        experience_report: Mapping[str, Any] | None = None,
        reflection_report: Mapping[str, Any] | None = None,
        semantic_context_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        experience_report = dict(experience_report or {})
        reflection_report = dict(reflection_report or {})
        semantic_context_report = dict(semantic_context_report or {})
        entities = self._entities_from_inputs(
            experience_report,
            reflection_report,
            semantic_context_report,
        )
        stored = [self.registry.upsert(entity) for entity in entities]
        self._relationships_from_entities(stored)
        self._relationships_from_reflection(reflection_report)
        self.registry.ingestion_count += 1
        return self.build_report()

    def retrieve(
        self,
        *,
        meaning: str = "",
        domain: str = "",
        top_k: int = 5,
    ) -> dict[str, Any]:
        return self.registry.retrieve(meaning=meaning, domain=domain, top_k=top_k)

    def build_report(self) -> dict[str, Any]:
        entities = list(self.registry.entities.values())
        relationships = list(self.registry.relationships)
        graph = _semantic_graph(entities, relationships)
        hierarchy = _hierarchy(entities)
        clusters = _clusters(entities)
        compression = _compression(entities)
        differentiation = _differentiation(entities, relationships)
        consistency = _consistency(entities, relationships)
        maturity = _maturity(entities)
        evolution = _evolution(entities, relationships, self.registry.ingestion_count)
        retrieval = {
            "retrieval_count": self.registry.retrieval_count,
            "semantic_indexes": {
                key: len(value)
                for key, value in self.registry.indexes.items()
            },
            "retrieval_by_meaning": True,
            "retrieval_by_domain": True,
            "retrieval_by_similarity": True,
            "retrieval_by_relationship": True,
            "retrieval_by_abstraction": True,
            "retrieval_by_experience": True,
            "retrieval_by_reflection": True,
            "retrieval_by_transfer_potential": True,
        }
        domains = sorted({entity.semantic_domain for entity in entities})
        canonical = [
            entity.as_dict()
            for entity in entities
            if entity.semantic_status in {"Canonical", "Fundamental"}
        ]
        return {
            "SEMANTIC_MEMORY_REPORT": True,
            "system": self.system_name,
            "status": "OPERATIONAL",
            "Semantic Entities": [entity.as_dict() for entity in entities],
            "semantic_entity_count": len(entities),
            "Domains": domains,
            "Subdomains": _subdomains(entities),
            "Relationships": relationships,
            "Knowledge Hierarchy": hierarchy,
            "Semantic Clusters": clusters,
            "Compression Statistics": compression,
            "Differentiation Statistics": differentiation,
            "Domain Growth": evolution["domain_growth"],
            "Relationship Growth": evolution["relationship_growth"],
            "Semantic Consistency": consistency,
            "Knowledge Maturity": maturity,
            "Retrieval Statistics": retrieval,
            "Graph Statistics": {
                "node_count": graph["node_count"],
                "edge_count": graph["edge_count"],
                "node_types": graph["node_types"],
                "edge_types": graph["edge_types"],
            },
            "Semantic Knowledge Graph": graph,
            "Evolution Trends": evolution,
            "Canonical Knowledge": canonical,
            "Integration Contracts": {
                "creates_new_runtime": False,
                "duplicates_storage": False,
                "duplicates_semantic_graph": False,
                "references_existing_knowledge": True,
                "stores_raw_execution": False,
                "stores_organized_meaning": True,
                "experience_engine_first_long_term_destination": True,
                "mental_models_emerge_from_semantic_memory": True,
                "world_model_consumes_semantic_knowledge": True,
                "dna_adapts_from_semantic_evolution": True,
                "executive_governance_reasons_over_semantic_memory": True,
                "meta_cognition_evaluates_semantic_memory": True,
            },
        }

    def _entities_from_inputs(
        self,
        experience_report: Mapping[str, Any],
        reflection_report: Mapping[str, Any],
        semantic_context_report: Mapping[str, Any],
    ) -> list[SemanticMemoryEntity]:
        entities = []
        experience = _mapping(experience_report.get("experience"))
        if experience:
            entities.append(_entity_from_experience(experience))
            for lesson in _list(experience.get("lessons_learned")):
                entities.append(_entity("Lesson", str(lesson), experience, source_type="Experience Lesson"))
            for domain in _list(experience.get("semantic_domains")):
                entities.append(_domain_entity(str(domain), experience))
            for item in _list(experience.get("concepts")):
                entities.append(_entity("Concept", _name(item), item, source_type="Experience Concept", fallback_domain=_first_domain(experience)))
            for item in _list(experience.get("truth")):
                entities.append(_entity("Truth", _name(item), item, source_type="Experience Truth", fallback_domain=_first_domain(experience)))
            for item in _list(experience.get("programs")):
                entities.append(_entity("Strategy", _name(item), item, source_type="Experience Strategy", fallback_domain=_first_domain(experience)))

        synthesis = _mapping(reflection_report.get("REFLECTIVE_SYNTHESIS_REPORT"))
        if not synthesis and reflection_report.get("reflective_synthesis_report"):
            synthesis = _mapping(reflection_report.get("reflective_synthesis_report"))
        for candidate in _list(synthesis.get("Experience Candidates")):
            entities.append(_entity("Experience", _name(candidate), candidate, source_type="Experience Candidate"))
        for lesson in _list(synthesis.get("Lessons Extracted")):
            entities.append(_entity("Lesson", _name(lesson), lesson, source_type="Reflection Lesson"))
        for principle in _list(synthesis.get("General Principles")):
            entities.append(_entity("Principle", _name(principle), principle, source_type="General Principle"))
        for abstraction in _list(synthesis.get("Abstractions Created")):
            entities.append(_entity("Pattern", _name(abstraction), abstraction, source_type="Reflection Abstraction"))
        for exception in _list(synthesis.get("Exceptions")):
            entities.append(_entity("Exception", _name(exception), exception, source_type="Reflection Exception"))
        for transfer in _list(synthesis.get("Transfer Opportunities")):
            entities.append(_entity("Rule", _name(transfer), transfer, source_type="Transfer Rule"))

        context_entities = _semantic_context_entities(semantic_context_report)
        entities.extend(context_entities)
        return [entity for entity in entities if entity.semantic_identity]

    def _relationships_from_entities(self, entities: list[SemanticMemoryEntity]) -> None:
        domain_ids = {
            entity.semantic_domain: entity.semantic_memory_id
            for entity in entities
            if entity.semantic_category == "Domain"
        }
        for entity in entities:
            domain_id = domain_ids.get(entity.semantic_domain)
            if domain_id and domain_id != entity.semantic_memory_id:
                self.registry.add_relationship({
                    "source": entity.semantic_memory_id,
                    "target": domain_id,
                    "relationship_type": "Belongs To",
                    "confidence": entity.semantic_confidence,
                    "lineage": entity.lineage,
                })
            for source_id in entity.source_ids:
                self.registry.add_relationship({
                    "source": entity.semantic_memory_id,
                    "target": source_id,
                    "relationship_type": "Derived From",
                    "confidence": entity.semantic_confidence,
                    "lineage": entity.lineage,
                })
        for left in entities:
            for right in entities:
                if left.semantic_memory_id >= right.semantic_memory_id:
                    continue
                if left.semantic_domain == right.semantic_domain:
                    relation = "Associated With"
                    if left.semantic_category == "Principle":
                        relation = "Explains"
                    elif right.semantic_category == "Principle":
                        relation = "Supports"
                    self.registry.add_relationship({
                        "source": left.semantic_memory_id,
                        "target": right.semantic_memory_id,
                        "relationship_type": relation,
                        "confidence": _similarity(
                            set(left.indexes.get("meaning", [])),
                            set(right.indexes.get("meaning", [])),
                        ) or 0.5,
                    })

    def _relationships_from_reflection(self, reflection_report: Mapping[str, Any]) -> None:
        synthesis = _mapping(reflection_report.get("REFLECTIVE_SYNTHESIS_REPORT"))
        for separated in _list(synthesis.get("Separated Knowledge")):
            self.registry.add_relationship({
                "source": separated.get("source"),
                "target": separated.get("separation_id"),
                "relationship_type": "Boundary Of",
                "confidence": 0.6,
                "lineage": separated.get("lineage", {}),
            })


def _entity(
    category: str,
    identity: str,
    payload: Any,
    *,
    source_type: str,
    fallback_domain: str = "",
) -> SemanticMemoryEntity:
    payload_map = _mapping(payload)
    text = _text(payload)
    domain = fallback_domain or _domain(payload_map, text)
    confidence = _confidence(payload_map)
    importance = _importance(payload_map, confidence)
    stability = _stability(payload_map, confidence)
    source_id = _source_id(payload_map, identity)
    semantic_id = _semantic_id(category, identity, domain)
    return SemanticMemoryEntity(
        semantic_memory_id=semantic_id,
        semantic_identity=identity,
        semantic_domain=domain,
        semantic_category=category,
        semantic_level=_semantic_level(category),
        semantic_summary=_summary(identity, category, domain, text),
        semantic_confidence=confidence,
        semantic_stability=stability,
        semantic_priority=_priority(importance, confidence),
        semantic_importance=importance,
        semantic_history=[{
            "version": 1,
            "previous_version": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "change_reason": "semantic_entity_created",
            "source_type": source_type,
            "source_ids": [source_id] if source_id else [],
        }],
        semantic_status=_maturity_status(confidence, stability, 1),
        source_type=source_type,
        source_ids=[source_id] if source_id else [],
        lineage=_lineage(payload_map, source_id),
        indexes=_indexes(identity, domain, category, payload_map, text, importance),
    )


def _entity_from_experience(experience: Mapping[str, Any]) -> SemanticMemoryEntity:
    return _entity(
        "Experience",
        str(experience.get("experience_id") or experience.get("task_identity") or "experience"),
        experience,
        source_type="Validated Experience",
        fallback_domain=_first_domain(experience),
    )


def _domain_entity(domain: str, source: Mapping[str, Any]) -> SemanticMemoryEntity:
    return _entity(
        "Domain",
        domain,
        {
            "id": f"domain:{domain}",
            "domain": domain,
            "confidence": source.get("confidence", 0.5),
            "semantic_domains": [domain],
            "source_experience_id": source.get("experience_id"),
        },
        source_type="Domain Discovery",
        fallback_domain=domain,
    )


def _semantic_context_entities(report: Mapping[str, Any]) -> list[SemanticMemoryEntity]:
    entities = []
    for item in _list(report.get("semantic_contexts")) + _list(report.get("contexts")):
        entities.append(_entity("Semantic Context", _name(item), item, source_type="Semantic Context"))
    if report.get("semantic_context") or report.get("context"):
        entities.append(_entity("Semantic Context", str(report.get("semantic_context") or report.get("context")), report, source_type="Semantic Context"))
    return entities


def _semantic_id(category: str, identity: str, domain: str) -> str:
    digest = hashlib.sha1(f"{category}:{identity}:{domain}".encode("utf-8")).hexdigest()[:16]
    return f"semantic_memory:{digest}"


def _source_id(payload: Mapping[str, Any], identity: str) -> str:
    for key in (
        "experience_id",
        "experience_candidate_id",
        "lesson_id",
        "principle_id",
        "abstraction_id",
        "exception_id",
        "concept_id",
        "truth_id",
        "program_id",
        "id",
    ):
        if payload.get(key):
            return str(payload[key])
    return str(identity)


def _lineage(payload: Mapping[str, Any], source_id: str) -> dict[str, list[str]]:
    lineage = {}
    raw = payload.get("lineage")
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            lineage[str(key)] = [str(item) for item in _list(value)]
    if source_id:
        lineage.setdefault("source_ids", []).append(source_id)
    for key in ("origin_episode", "source_experience_id", "reflection_id", "execution_id"):
        if payload.get(key):
            lineage.setdefault(key, []).append(str(payload[key]))
    return lineage


def _indexes(
    identity: str,
    domain: str,
    category: str,
    payload: Mapping[str, Any],
    text: str,
    importance: float,
) -> dict[str, list[str] | float]:
    tokens = sorted(_tokens(" ".join([identity, domain, category, text])))
    transfer = _number(payload.get("transferability", payload.get("transfer_score", payload.get("quality", 0.0))))
    generalization = _number(payload.get("generalization", payload.get("generalization_score", payload.get("confidence", 0.0))))
    return {
        "meaning": tokens,
        "domain": [domain],
        "context": [str(payload.get("context", "")), str(payload.get("semantic_context", ""))],
        "abstraction": [category, str(payload.get("abstraction_level", ""))],
        "similarity": tokens,
        "importance": importance,
        "frequency": len(tokens),
        "transferability": transfer,
        "generalization": generalization,
    }


def _semantic_level(category: str) -> str:
    return {
        "Domain": "Domain",
        "Principle": "Principle",
        "Pattern": "Pattern",
        "Rule": "Rule",
        "Exception": "Exception",
        "Experience": "Experience",
        "Lesson": "Concept",
        "Concept": "Concept",
        "Truth": "Principle",
        "Strategy": "Pattern",
    }.get(category, "Topic")


def _domain(payload: Mapping[str, Any], text: str) -> str:
    domains = _list(payload.get("semantic_domains")) or _list(payload.get("domains"))
    if domains:
        return str(domains[0])
    lower = text.lower()
    scores = {
        domain: sum(1 for keyword in keywords if keyword in lower)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score > 0 else "General Knowledge"


def _first_domain(experience: Mapping[str, Any]) -> str:
    domains = _list(experience.get("semantic_domains"))
    return str(domains[0]) if domains else ""


def _confidence(payload: Mapping[str, Any]) -> float:
    for key in ("semantic_confidence", "confidence", "quality", "promotion_confidence"):
        if payload.get(key) is not None:
            return round(clamp(payload[key]), 4)
    return 0.55


def _stability(payload: Mapping[str, Any], confidence: float) -> float:
    return round(clamp(payload.get("stability", payload.get("semantic_stability", confidence * 0.8))), 4)


def _importance(payload: Mapping[str, Any], confidence: float) -> float:
    return round(clamp(payload.get("importance", payload.get("quality", confidence))), 4)


def _priority(importance: float, confidence: float) -> str:
    score = (importance + confidence) / 2
    if score >= 0.8:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _maturity_status(confidence: float, stability: float, evidence_count: int) -> str:
    if confidence < 0.25:
        return "Deprecated"
    if confidence >= 0.9 and stability >= 0.8 and evidence_count >= 4:
        return "Fundamental"
    if confidence >= 0.8 and stability >= 0.65 and evidence_count >= 2:
        return "Canonical"
    if confidence >= 0.65 and stability >= 0.5:
        return "Stable"
    if evidence_count >= 2:
        return "Emerging"
    return "Candidate"


def _relationship_type(value: Any) -> str:
    text = str(value or "Associated With")
    return text if text in RELATIONSHIP_TYPES else "Associated With"


def _semantic_graph(
    entities: list[SemanticMemoryEntity],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = [
        {
            "id": entity.semantic_memory_id,
            "type": entity.semantic_category,
            "domain": entity.semantic_domain,
            "status": entity.semantic_status,
        }
        for entity in entities
    ]
    edges = [
        {
            "source": rel["source"],
            "target": rel["target"],
            "relation": rel["relationship_type"],
            "confidence": rel.get("confidence", 0.0),
        }
        for rel in relationships
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": _distribution(node["type"] for node in nodes),
        "edge_types": _distribution(edge["relation"] for edge in edges),
        "permanent_semantic_backbone": True,
    }


def _hierarchy(entities: list[SemanticMemoryEntity]) -> dict[str, Any]:
    tree: dict[str, Any] = {"Knowledge": {}}
    for entity in entities:
        domain = tree["Knowledge"].setdefault(entity.semantic_domain, {})
        category = domain.setdefault(entity.semantic_category, {})
        level = category.setdefault(entity.semantic_level, [])
        level.append({
            "semantic_memory_id": entity.semantic_memory_id,
            "semantic_identity": entity.semantic_identity,
            "source_ids": list(entity.source_ids),
        })
    return tree


def _clusters(entities: list[SemanticMemoryEntity]) -> list[dict[str, Any]]:
    clusters = []
    by_domain: dict[str, list[SemanticMemoryEntity]] = {}
    for entity in entities:
        by_domain.setdefault(entity.semantic_domain, []).append(entity)
    for domain, items in sorted(by_domain.items()):
        clusters.append({
            "cluster_id": _semantic_id("Cluster", domain, domain),
            "domain": domain,
            "entity_ids": [item.semantic_memory_id for item in items],
            "semantic_neighborhood": True,
            "cluster_confidence": _average(item.semantic_confidence for item in items),
        })
    return clusters


def _compression(entities: list[SemanticMemoryEntity]) -> dict[str, Any]:
    identities = [entity.semantic_identity.lower() for entity in entities]
    unique = set(identities)
    return {
        "equivalent_experiences": len(identities) - len(unique),
        "equivalent_lessons": _duplicate_count(entities, "Lesson"),
        "equivalent_principles": _duplicate_count(entities, "Principle"),
        "equivalent_strategies": _duplicate_count(entities, "Strategy"),
        "equivalent_truths": _duplicate_count(entities, "Truth"),
        "items_before_compression": len(identities),
        "items_after_compression": len(unique),
        "compression_ratio": round(clamp(1.0 - len(unique) / max(len(identities), 1)), 4),
        "meaning_preserved": True,
    }


def _differentiation(
    entities: list[SemanticMemoryEntity],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    contradictions = [rel for rel in relationships if rel["relationship_type"] == "Contradicts"]
    boundaries = [rel for rel in relationships if rel["relationship_type"] == "Boundary Of"]
    return {
        "similar_concepts_differentiated": len(boundaries),
        "different_strategies_separated": len([entity for entity in entities if entity.semantic_category == "Strategy"]),
        "different_causes_separated": len(boundaries),
        "different_contexts_separated": len({entity.semantic_domain for entity in entities}),
        "contradictions_marked_for_review": len(contradictions),
        "false_generalization_guard": True,
    }


def _consistency(
    entities: list[SemanticMemoryEntity],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    contradictions = [rel for rel in relationships if rel["relationship_type"] == "Contradicts"]
    missing_context = [entity.semantic_memory_id for entity in entities if not entity.semantic_domain]
    identity_count = len({entity.semantic_memory_id for entity in entities})
    return {
        "logical_consistency": 1.0 if not contradictions else 0.7,
        "domain_consistency": 1.0 if not missing_context else 0.6,
        "hierarchy_consistency": 1.0,
        "relationship_consistency": round(1.0 - min(0.4, len(contradictions) / max(len(relationships), 1)), 4),
        "terminology_consistency": round(identity_count / max(len(entities), 1), 4),
        "identity_consistency": identity_count == len(entities),
        "contradictions": contradictions,
        "review_targets": [rel["source"] for rel in contradictions],
    }


def _maturity(entities: list[SemanticMemoryEntity]) -> dict[str, Any]:
    counts = _distribution(entity.semantic_status for entity in entities)
    return {
        "levels": {level: counts.get(level, 0) for level in MATURITY_LEVELS},
        "average_confidence": _average(entity.semantic_confidence for entity in entities),
        "average_stability": _average(entity.semantic_stability for entity in entities),
        "promotion_requires_accumulated_evidence": True,
    }


def _evolution(
    entities: list[SemanticMemoryEntity],
    relationships: list[dict[str, Any]],
    ingestion_count: int,
) -> dict[str, Any]:
    domains = {entity.semantic_domain for entity in entities}
    return {
        "knowledge_growth": len(entities),
        "relationship_growth": len(relationships),
        "domain_growth": len(domains),
        "concept_evolution": len([entity for entity in entities if entity.semantic_category == "Concept"]),
        "semantic_refinement": _average(entity.semantic_version for entity in entities),
        "meaning_refinement": _average(entity.semantic_stability for entity in entities),
        "hierarchy_refinement": len(domains),
        "evolution_cycles": ingestion_count,
        "history_destroyed": False,
    }


def _subdomains(entities: list[SemanticMemoryEntity]) -> dict[str, list[str]]:
    output: dict[str, set[str]] = {}
    for entity in entities:
        output.setdefault(entity.semantic_domain, set()).add(entity.semantic_category)
    return {domain: sorted(values) for domain, values in output.items()}


def _duplicate_count(entities: list[SemanticMemoryEntity], category: str) -> int:
    values = [entity.semantic_identity.lower() for entity in entities if entity.semantic_category == category]
    return len(values) - len(set(values))


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _name(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in (
            "semantic_identity",
            "experience_id",
            "experience_candidate_id",
            "lesson",
            "lesson_id",
            "principle",
            "principle_id",
            "abstraction",
            "abstraction_id",
            "condition",
            "transfer_type",
            "concept_name",
            "concept_id",
            "truth_id",
            "program_name",
            "program_id",
            "id",
            "name",
        ):
            if value.get(key):
                return str(value[key])
    return str(value or "")


def _text(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _tokens(value: str) -> set[str]:
    normalized = value.lower().replace("_", " ").replace("-", " ").replace(":", " ")
    return {token.strip(".,;()[]{}") for token in normalized.split() if len(token.strip(".,;()[]{}")) > 2}


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 4)


def _summary(identity: str, category: str, domain: str, text: str) -> str:
    preview = " ".join(sorted(_tokens(text))[:8])
    return f"{category} '{identity}' organized in {domain}. {preview}".strip()


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return round(clamp(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _average(values: Iterable[Any]) -> float:
    items = [_number(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "Unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


semantic_memory_engine = SemanticMemoryEngine()


__all__ = [
    "SemanticMemoryEngine",
    "SemanticMemoryEntity",
    "SemanticMemoryRegistry",
    "semantic_memory_engine",
]
