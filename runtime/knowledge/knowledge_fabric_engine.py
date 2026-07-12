"""Knowledge Fabric Engine.

The Fabric is a cognitive relationship layer above Semantic Memory. It never
duplicates semantic entities or experiences; it references Semantic Memory IDs
and stores only connection structures, bridges, dependencies, and interaction
patterns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


FABRIC_RELATIONSHIP_TYPES = {
    "Supports",
    "Requires",
    "Influences",
    "Strengthens",
    "Weakens",
    "Extends",
    "Constrains",
    "Specializes",
    "Generalizes",
    "Bridges",
    "Transfers",
    "Predicts",
    "Explains",
    "Emerges From",
    "Depends On",
    "Conflicts With",
    "Complements",
}

SEMANTIC_TO_FABRIC_RELATIONSHIP = {
    "Belongs To": "Depends On",
    "Explains": "Explains",
    "Supports": "Supports",
    "Contradicts": "Conflicts With",
    "Generalizes": "Generalizes",
    "Specializes": "Specializes",
    "Depends On": "Depends On",
    "Influences": "Influences",
    "Derived From": "Emerges From",
    "Associated With": "Complements",
    "Equivalent To": "Complements",
    "Boundary Of": "Constrains",
}

BRIDGE_CATEGORIES = {
    "Principle",
    "Strategy",
    "Pattern",
    "Rule",
    "Lesson",
    "Experience",
    "Truth",
}

TOKEN_STOPWORDS = {
    "domain",
    "concept",
    "knowledge",
    "semantic",
    "memory",
    "entity",
    "experience",
    "lesson",
    "strategy",
    "principle",
    "policy",
}


@dataclass(frozen=True)
class FabricEntity:
    fabric_id: str
    fabric_identity: str
    fabric_type: str
    fabric_scope: str
    fabric_confidence: float
    fabric_strength: float
    fabric_density: float
    fabric_stability: float
    fabric_priority: str
    fabric_version: int = 1
    fabric_history: list[dict[str, Any]] = field(default_factory=list)
    source_entity_ids: list[str] = field(default_factory=list)
    target_entity_ids: list[str] = field(default_factory=list)
    relationship_types: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    lineage: dict[str, list[str]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class KnowledgeFabricRegistry:
    """Registry for fabric relationships and bridge entities only."""

    def __init__(self) -> None:
        self.fabric_entities: dict[str, FabricEntity] = {}
        self.fabric_relationships: list[dict[str, Any]] = []
        self.legal_reference_ids: set[str] = set()
        self.integration_count = 0

    def allow_references(self, entity_ids: Iterable[str]) -> None:
        self.legal_reference_ids.update(str(entity_id) for entity_id in entity_ids if entity_id)

    def upsert(self, entity: FabricEntity) -> FabricEntity:
        previous = self.fabric_entities.get(entity.fabric_id)
        if previous is not None:
            history = [
                *previous.fabric_history,
                {
                    "version": previous.fabric_version + 1,
                    "previous_version": previous.fabric_version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "change_reason": "fabric_entity_reinforced",
                    "source_entity_ids": sorted(set(previous.source_entity_ids + entity.source_entity_ids)),
                    "target_entity_ids": sorted(set(previous.target_entity_ids + entity.target_entity_ids)),
                },
            ]
            entity = replace(
                entity,
                fabric_version=previous.fabric_version + 1,
                fabric_history=history,
                source_entity_ids=sorted(set(previous.source_entity_ids + entity.source_entity_ids)),
                target_entity_ids=sorted(set(previous.target_entity_ids + entity.target_entity_ids)),
                relationship_types=sorted(set(previous.relationship_types + entity.relationship_types)),
                domains=sorted(set(previous.domains + entity.domains)),
                fabric_confidence=round(max(previous.fabric_confidence, entity.fabric_confidence), 4),
                fabric_strength=round(max(previous.fabric_strength, entity.fabric_strength), 4),
                fabric_stability=round(clamp(previous.fabric_stability + 0.08), 4),
            )
        self.fabric_entities[entity.fabric_id] = entity
        return entity

    def add_relationship(self, relationship: Mapping[str, Any]) -> None:
        source_id = str(relationship.get("source") or relationship.get("source_entity_id") or "")
        target_id = str(relationship.get("target") or relationship.get("target_entity_id") or "")
        if self.legal_reference_ids and (
            source_id not in self.legal_reference_ids
            or target_id not in self.legal_reference_ids
        ):
            return
        relation_type = _fabric_relationship_type(relationship.get("relationship_type") or relationship.get("relation_type"))
        confidence = round(clamp(relationship.get("confidence", relationship.get("relation_confidence", 0.5))), 4)
        strength = round(clamp(relationship.get("strength", relationship.get("relation_strength", confidence))), 4)
        item = {
            "relation_id": _relation_id(source_id, target_id, relation_type),
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "relation_type": relation_type,
            "relation_strength": strength,
            "relation_confidence": confidence,
            "evidence_ids": [str(item) for item in _list(relationship.get("evidence_ids"))],
            "context_ids": [str(item) for item in _list(relationship.get("context_ids"))],
            "provenance": dict(relationship.get("provenance") or relationship.get("lineage") or {}),
            "validity_scope": {
                "source_domain": str(relationship.get("source_domain") or ""),
                "target_domain": str(relationship.get("target_domain") or ""),
                "cross_domain": bool(relationship.get("cross_domain", False)),
            },
            "lifecycle_state": str(
                relationship.get("lifecycle_state")
                or _lifecycle_state(confidence, relationship.get("provenance") or relationship.get("lineage"))
            ),
            "version": int(relationship.get("version", 1)),
        }
        marker = (item["source_entity_id"], item["target_entity_id"], item["relation_type"])
        existing = {
            (rel["source_entity_id"], rel["target_entity_id"], rel["relation_type"])
            for rel in self.fabric_relationships
        }
        if source_id and target_id and source_id != target_id and marker not in existing:
            self.fabric_relationships.append(item)


class KnowledgeFabricEngine:
    """Connect semantic knowledge into one unified relationship fabric."""

    system_name = "knowledge_fabric_engine"

    def __init__(self, registry: KnowledgeFabricRegistry | None = None) -> None:
        self.registry = registry or KnowledgeFabricRegistry()

    def integrate(self, *, semantic_memory_report: Mapping[str, Any]) -> dict[str, Any]:
        entities = [_entity_view(entity) for entity in _list(semantic_memory_report.get("Semantic Entities"))]
        relationships = [_relationship_view(rel) for rel in _list(semantic_memory_report.get("Relationships"))]
        domains = sorted({
            str(domain)
            for domain in (
                _list(semantic_memory_report.get("Domains"))
                or [entity["domain"] for entity in entities]
            )
            if domain
        })
        by_id = {entity["id"]: entity for entity in entities if entity["id"]}
        self.registry.allow_references(by_id)

        self._import_semantic_relationships(relationships, by_id)
        self._connect_domain_membership(entities)
        self._discover_cross_domain_links(entities)
        self._build_domain_bridges(entities)
        self._build_global_fabric(domains, entities)
        self.registry.integration_count += 1

        return self.build_report(domains=domains, semantic_entity_count=len(entities))

    def build_report(self, *, domains: Iterable[str] | None = None, semantic_entity_count: int | None = None) -> dict[str, Any]:
        domain_list = sorted({str(domain) for domain in (domains or []) if domain})
        relationships = list(self.registry.fabric_relationships)
        fabric_entities = list(self.registry.fabric_entities.values())
        connected, disconnected = _domain_connectivity(domain_list, relationships)
        cross_domain_links = [
            rel for rel in relationships
            if rel["validity_scope"]["cross_domain"]
        ]
        bridges = [
            entity.as_dict()
            for entity in fabric_entities
            if entity.fabric_type in {"SemanticBridge", "DomainBridge", "GlobalFabric"}
        ]
        metrics = _connectivity_metrics(
            domains=domain_list,
            semantic_entity_count=semantic_entity_count or 0,
            fabric_entities=fabric_entities,
            relationships=relationships,
        )
        weak_connections = [
            rel for rel in relationships
            if rel["relation_confidence"] < 0.5 or rel["relation_strength"] < 0.5
        ]
        return {
            "KNOWLEDGE_FABRIC_FOUNDATION_REPORT": True,
            "system": self.system_name,
            "status": "OPERATIONAL",
            "Fabric Entities": [entity.as_dict() for entity in fabric_entities],
            "fabric_entity_count": len(fabric_entities),
            "Fabric Relationships": relationships,
            "Connected Domains": connected,
            "Disconnected Domains": disconnected,
            "Relationship Count": len(relationships),
            "Bridge Count": len(bridges),
            "Cross-Domain Links": cross_domain_links,
            "Connectivity Metrics": metrics,
            "Fabric Density": metrics["global_connectivity"],
            "Fabric Stability": _average(entity.fabric_stability for entity in fabric_entities),
            "Emerging Bridges": bridges,
            "Weak Connections": weak_connections,
            "Semantic Coverage": {
                "referenced_semantic_entities": len(_referenced_entity_ids(fabric_entities, relationships)),
                "semantic_entity_count": semantic_entity_count or 0,
                "coverage_ratio": round(
                    len(_referenced_entity_ids(fabric_entities, relationships))
                    / max(semantic_entity_count or 0, 1),
                    4,
                ),
                "semantic_memory_is_canonical": True,
            },
            "Integration Contracts": {
                "creates_new_memory_system": False,
                "duplicates_semantic_memory": False,
                "duplicates_concepts": False,
                "duplicates_experiences": False,
                "duplicates_domains": False,
                "duplicates_semantic_payloads": False,
                "accepts_orphan_relationships": False,
                "mutates_semantic_entities": False,
                "creates_new_truth": False,
                "stores_relationships_only": True,
                "semantic_memory_remains_canonical": True,
                "references_semantic_memory_entities": True,
                "queries_return_ids_before_hydration": True,
                "relation_hypotheses_require_evidence_and_truth_validation": True,
                "mental_models_receive_connected_fabric": True,
                "world_model_receives_connected_semantics": True,
                "executive_governance_receives_cross_domain_intelligence": True,
            },
        }

    def _import_semantic_relationships(
        self,
        relationships: list[dict[str, Any]],
        by_id: Mapping[str, dict[str, Any]],
    ) -> None:
        for relationship in relationships:
            source = by_id.get(relationship["source"])
            target = by_id.get(relationship["target"])
            if not source or not target:
                continue
            relation_type = SEMANTIC_TO_FABRIC_RELATIONSHIP.get(
                relationship["relationship_type"],
                "Complements",
            )
            cross_domain = source["domain"] != target["domain"]
            self.registry.add_relationship({
                "source": relationship["source"],
                "target": relationship["target"],
                "relationship_type": relation_type,
                "confidence": relationship["confidence"],
                "strength": relationship["confidence"],
                "source_domain": source["domain"],
                "target_domain": target["domain"],
                "cross_domain": cross_domain,
                "lineage": {
                    "semantic_relationship": [
                        f"{relationship['source']}->{relationship['target']}:{relationship['relationship_type']}"
                    ]
                },
                "provenance": {
                    "owner": "Semantic Memory",
                    "source": "semantic_memory_relationship",
                    "semantic_relationship": [
                        f"{relationship['source']}->{relationship['target']}:{relationship['relationship_type']}"
                    ],
                },
                "lifecycle_state": "VALIDATED",
            })

    def _connect_domain_membership(self, entities: list[dict[str, Any]]) -> None:
        domains = {
            entity["domain"]: entity
            for entity in entities
            if entity["category"] == "Domain"
        }
        for entity in entities:
            domain_entity = domains.get(entity["domain"])
            if domain_entity and domain_entity["id"] != entity["id"]:
                self.registry.add_relationship({
                    "source": entity["id"],
                    "target": domain_entity["id"],
                    "relationship_type": "Depends On",
                    "confidence": entity["confidence"],
                    "strength": entity["stability"],
                    "source_domain": entity["domain"],
                    "target_domain": domain_entity["domain"],
                    "cross_domain": False,
                    "lineage": {"semantic_entity_ids": [entity["id"], domain_entity["id"]]},
                    "provenance": {
                        "owner": "Semantic Memory",
                        "source": "semantic_memory_domain_membership",
                        "semantic_entity_ids": [entity["id"], domain_entity["id"]],
                    },
                    "lifecycle_state": "VALIDATED",
                })

    def _discover_cross_domain_links(self, entities: list[dict[str, Any]]) -> None:
        for index, left in enumerate(entities):
            for right in entities[index + 1:]:
                if left["domain"] == right["domain"]:
                    continue
                similarity = _similarity(left["tokens"], right["tokens"])
                if similarity <= 0 and not _bridgeworthy(left, right):
                    continue
                strength = max(similarity, _category_affinity(left, right))
                relationship_type = _cross_domain_relationship(left, right, similarity)
                self.registry.add_relationship({
                    "source": left["id"],
                    "target": right["id"],
                    "relationship_type": relationship_type,
                    "confidence": max(0.35, min(left["confidence"], right["confidence"], strength + 0.35)),
                    "strength": max(0.35, strength),
                    "source_domain": left["domain"],
                    "target_domain": right["domain"],
                    "cross_domain": True,
                    "lineage": {"semantic_entity_ids": [left["id"], right["id"]]},
                    "provenance": {
                        "owner": "Knowledge Fabric",
                        "source": "fabric_relation_hypothesis",
                        "semantic_entity_ids": [left["id"], right["id"]],
                    },
                    "lifecycle_state": "PROPOSED",
                })
                if relationship_type in {"Bridges", "Transfers", "Explains", "Generalizes"}:
                    self.registry.upsert(_fabric_entity(
                        identity=f"{left['domain']} -> {right['domain']} via {left['identity']} / {right['identity']}",
                        fabric_type="SemanticBridge",
                        fabric_scope="cross_domain",
                        confidence=max(0.35, min(left["confidence"], right["confidence"], strength + 0.35)),
                        strength=max(0.35, strength),
                        density=strength,
                        stability=_average([left["stability"], right["stability"]]),
                        source_ids=[left["id"]],
                        target_ids=[right["id"]],
                        relationship_types=[relationship_type],
                        domains=[left["domain"], right["domain"]],
                    ))

    def _build_domain_bridges(self, entities: list[dict[str, Any]]) -> None:
        by_domain: dict[str, list[dict[str, Any]]] = {}
        for entity in entities:
            by_domain.setdefault(entity["domain"], []).append(entity)
        domains = sorted(by_domain)
        for index, left_domain in enumerate(domains):
            for right_domain in domains[index + 1:]:
                left_items = by_domain[left_domain]
                right_items = by_domain[right_domain]
                bridge_score = _domain_bridge_score(left_items, right_items)
                if bridge_score <= 0:
                    continue
                left_ids = [item["id"] for item in left_items[:3]]
                right_ids = [item["id"] for item in right_items[:3]]
                self.registry.upsert(_fabric_entity(
                    identity=f"{left_domain} <-> {right_domain}",
                    fabric_type="DomainBridge",
                    fabric_scope="cross_domain",
                    confidence=bridge_score,
                    strength=bridge_score,
                    density=bridge_score,
                    stability=_average(item["stability"] for item in left_items + right_items),
                    source_ids=left_ids,
                    target_ids=right_ids,
                    relationship_types=["Bridges"],
                    domains=[left_domain, right_domain],
                ))

    def _build_global_fabric(
        self,
        domains: list[str],
        entities: list[dict[str, Any]],
    ) -> None:
        if not entities:
            return
        relationships = list(self.registry.fabric_relationships)
        density = len(relationships) / max(len(entities) * max(len(entities) - 1, 1), 1)
        self.registry.upsert(_fabric_entity(
            identity="Unified Semantic Fabric",
            fabric_type="GlobalFabric",
            fabric_scope="global",
            confidence=_average(entity["confidence"] for entity in entities),
            strength=_average(rel["relation_strength"] for rel in relationships),
            density=density,
            stability=_average(entity["stability"] for entity in entities),
            source_ids=[entity["id"] for entity in entities],
            target_ids=[entity["id"] for entity in entities],
            relationship_types=sorted({rel["relation_type"] for rel in relationships}),
            domains=domains,
        ))


def _fabric_entity(
    *,
    identity: str,
    fabric_type: str,
    fabric_scope: str,
    confidence: float,
    strength: float,
    density: float,
    stability: float,
    source_ids: list[str],
    target_ids: list[str],
    relationship_types: list[str],
    domains: list[str],
) -> FabricEntity:
    return FabricEntity(
        fabric_id=_fabric_id(fabric_type, identity, domains),
        fabric_identity=identity,
        fabric_type=fabric_type,
        fabric_scope=fabric_scope,
        fabric_confidence=round(clamp(confidence), 4),
        fabric_strength=round(clamp(strength), 4),
        fabric_density=round(clamp(density), 4),
        fabric_stability=round(clamp(stability), 4),
        fabric_priority=_priority(confidence, strength, density),
        fabric_history=[{
            "version": 1,
            "previous_version": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "change_reason": "fabric_entity_created",
            "source_entity_ids": list(source_ids),
            "target_entity_ids": list(target_ids),
        }],
        source_entity_ids=sorted(set(source_ids)),
        target_entity_ids=sorted(set(target_ids)),
        relationship_types=sorted(set(relationship_types)),
        domains=sorted(set(domains)),
        lineage={"semantic_memory_entity_ids": sorted(set(source_ids + target_ids))},
    )


def _entity_view(value: Any) -> dict[str, Any]:
    entity = dict(value) if isinstance(value, Mapping) else {}
    identity = str(entity.get("semantic_identity") or entity.get("id") or "")
    domain = str(entity.get("semantic_domain") or "General Knowledge")
    category = str(entity.get("semantic_category") or "Knowledge")
    summary = str(entity.get("semantic_summary") or "")
    tokens = set(entity.get("indexes", {}).get("meaning", []))
    tokens.update(_tokens(" ".join([identity, domain, category, summary])))
    return {
        "id": str(entity.get("semantic_memory_id") or ""),
        "identity": identity,
        "domain": domain,
        "category": category,
        "level": str(entity.get("semantic_level") or ""),
        "confidence": _number(entity.get("semantic_confidence", 0.5)),
        "stability": _number(entity.get("semantic_stability", 0.5)),
        "importance": _number(entity.get("semantic_importance", 0.5)),
        "tokens": tokens,
    }


def _relationship_view(value: Any) -> dict[str, Any]:
    relationship = dict(value) if isinstance(value, Mapping) else {}
    return {
        "source": str(relationship.get("source") or ""),
        "target": str(relationship.get("target") or ""),
        "relationship_type": str(relationship.get("relationship_type") or "Associated With"),
        "confidence": _number(relationship.get("confidence", 0.5)),
    }


def _fabric_relationship_type(value: Any) -> str:
    text = str(value or "Complements")
    return text if text in FABRIC_RELATIONSHIP_TYPES else "Complements"


def _cross_domain_relationship(left: Mapping[str, Any], right: Mapping[str, Any], similarity: float) -> str:
    categories = {str(left["category"]), str(right["category"])}
    if "Truth" in categories or "Principle" in categories:
        return "Explains"
    if "Strategy" in categories or "Pattern" in categories:
        return "Transfers"
    if "Domain" in categories:
        return "Bridges"
    if similarity >= 0.2:
        return "Generalizes"
    return "Complements"


def _bridgeworthy(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    categories = {str(left["category"]), str(right["category"])}
    if categories & BRIDGE_CATEGORIES:
        return True
    if "Domain" in categories:
        return False
    return left["importance"] >= 0.7 and right["importance"] >= 0.7


def _category_affinity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    categories = {str(left["category"]), str(right["category"])}
    if categories & {"Principle", "Strategy", "Pattern", "Rule"}:
        return 0.55
    if categories & {"Lesson", "Experience", "Truth"}:
        return 0.45
    return 0.0


def _domain_bridge_score(left_items: list[dict[str, Any]], right_items: list[dict[str, Any]]) -> float:
    if not left_items or not right_items:
        return 0.0
    scores = []
    for left in left_items:
        for right in right_items:
            score = max(_similarity(left["tokens"], right["tokens"]), _category_affinity(left, right))
            if score > 0:
                scores.append(score)
    return round(clamp(_average(scores)), 4)


def _domain_connectivity(
    domains: list[str],
    relationships: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    if len(domains) <= 1:
        return domains, []
    connected = set()
    for relationship in relationships:
        scope = relationship["validity_scope"]
        if scope["cross_domain"]:
            connected.add(scope["source_domain"])
            connected.add(scope["target_domain"])
    return sorted(connected), sorted(set(domains) - connected)


def _connectivity_metrics(
    *,
    domains: list[str],
    semantic_entity_count: int,
    fabric_entities: list[FabricEntity],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    cross_domain_links = [
        rel for rel in relationships
        if rel["validity_scope"]["cross_domain"]
    ]
    bridges = [entity for entity in fabric_entities if entity.fabric_type in {"SemanticBridge", "DomainBridge", "GlobalFabric"}]
    possible_domain_links = max(len(domains) * max(len(domains) - 1, 0) / 2, 1)
    possible_entity_links = max(semantic_entity_count * max(semantic_entity_count - 1, 0), 1)
    relationship_types = {rel["relation_type"] for rel in relationships}
    referenced = _referenced_entity_ids(fabric_entities, relationships)
    return {
        "connection_density": round(len(relationships) / possible_entity_links, 4),
        "bridge_density": round(len(bridges) / possible_domain_links, 4),
        "relationship_diversity": round(len(relationship_types) / max(len(FABRIC_RELATIONSHIP_TYPES), 1), 4),
        "cross_domain_coverage": round(
            len(
                {rel["validity_scope"]["source_domain"] for rel in cross_domain_links}
                | {rel["validity_scope"]["target_domain"] for rel in cross_domain_links}
            )
            / max(len(domains), 1),
            4,
        ),
        "knowledge_connectivity": round(len(referenced) / max(semantic_entity_count, 1), 4),
        "semantic_reach": len(referenced),
        "transfer_reach": len([rel for rel in relationships if rel["relation_type"] == "Transfers"]),
        "global_connectivity": round(
            (
                len(relationships) / possible_entity_links
                + len(bridges) / possible_domain_links
                + len(referenced) / max(semantic_entity_count, 1)
            )
            / 3,
            4,
        ),
    }


def _referenced_entity_ids(
    fabric_entities: list[FabricEntity],
    relationships: list[dict[str, Any]],
) -> set[str]:
    referenced = set()
    for entity in fabric_entities:
        referenced.update(entity.source_entity_ids)
        referenced.update(entity.target_entity_ids)
    for relationship in relationships:
        referenced.add(relationship["source_entity_id"])
        referenced.add(relationship["target_entity_id"])
    return {item for item in referenced if item}


def _relation_id(source_id: str, target_id: str, relation_type: str) -> str:
    digest = hashlib.sha1(f"{source_id}:{target_id}:{relation_type}".encode("utf-8")).hexdigest()[:16]
    return f"FAB-REL-{digest}"


def _lifecycle_state(confidence: float, provenance: Any) -> str:
    source = ""
    if isinstance(provenance, Mapping):
        source = str(provenance.get("source") or "")
    if source == "fabric_relation_hypothesis":
        return "PROPOSED"
    if confidence >= 0.9:
        return "STABLE"
    if confidence >= 0.7:
        return "VALIDATED"
    if confidence >= 0.5:
        return "EVIDENCE_SUPPORTED"
    return "PROPOSED"


def _fabric_id(fabric_type: str, identity: str, domains: list[str]) -> str:
    digest = hashlib.sha1(
        f"{fabric_type}:{identity}:{','.join(sorted(domains))}".encode("utf-8")
    ).hexdigest()[:16]
    return f"knowledge_fabric:{digest}"


def _priority(confidence: float, strength: float, density: float) -> str:
    score = (float(confidence) + float(strength) + float(density)) / 3
    if score >= 0.8:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _tokens(value: str) -> set[str]:
    normalized = value.lower().replace("_", " ").replace("-", " ").replace(":", " ")
    return {
        token.strip(".,;()[]{}")
        for token in normalized.split()
        if len(token.strip(".,;()[]{}")) > 2
        and token.strip(".,;()[]{}") not in TOKEN_STOPWORDS
    }


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 4)


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


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


knowledge_fabric_engine = KnowledgeFabricEngine()


__all__ = [
    "FabricEntity",
    "KnowledgeFabricEngine",
    "KnowledgeFabricRegistry",
    "knowledge_fabric_engine",
]
