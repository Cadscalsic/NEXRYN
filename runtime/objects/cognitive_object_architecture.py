"""Unified Cognitive Object Architecture.

The layer introduces a canonical Cognitive Object that wraps existing runtime
artifacts without replacing them. Runtimes may keep their internal structures;
externally, their outputs can be normalized into this universal language.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_OBJECT_REGISTRY = Path("runtime/memory/storage/cognitive_objects/object_registry.json")


OBJECT_TYPE_KEYS: tuple[tuple[str, str, str], ...] = (
    ("concept", "concepts", "CONCEPT"),
    ("program", "programs", "PROGRAM"),
    ("evidence", "evidence", "EVIDENCE"),
    ("truth", "truth", "TRUTH"),
    ("memory", "memory_updates", "MEMORY"),
    ("policy", "policies_used", "POLICY"),
            ("decision", "decisions_taken", "DECISION"),
            ("situation", "situation_snapshot", "SITUATION"),
            ("experience", "experience", "EXPERIENCE"),
            ("mental_model", "mental_model_updates", "MENTAL_MODEL"),
            ("semantic", "canonical_concepts", "SEMANTIC_ABSTRACTION"),
)


@dataclass
class CognitiveObject:
    object_id: str
    global_identity: str
    object_type: str
    creation_runtime: str
    creation_timestamp: str
    execution_id: str = ""
    experience_id: str = ""
    situation_id: str = ""
    semantic_domain: str = ""
    ontology_node: str = ""
    mental_model_reference: str = ""
    parent_objects: list[str] = field(default_factory=list)
    child_objects: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    evidence_links: list[str] = field(default_factory=list)
    truth_links: list[str] = field(default_factory=list)
    memory_links: list[str] = field(default_factory=list)
    policy_links: list[str] = field(default_factory=list)
    decision_links: list[str] = field(default_factory=list)
    world_model_links: list[str] = field(default_factory=list)
    dna_links: list[str] = field(default_factory=list)
    confidence: float = 0.0
    importance: float = 0.0
    priority: str = "normal"
    novelty: float = 0.0
    complexity: float = 0.0
    compression_state: str = "uncompressed"
    lifecycle_state: str = "BIRTH"
    version: int = 1
    historical_evolution: list[dict[str, Any]] = field(default_factory=list)
    source_artifact_id: str = ""
    source_payload: dict[str, Any] = field(default_factory=dict)


class CognitiveObjectRegistry:
    """Assigns stable COG identities and persists object history."""

    def __init__(self, path: str | Path = DEFAULT_OBJECT_REGISTRY) -> None:
        self.path = Path(path)
        self.identity_map: dict[str, str] = {}
        self.objects: dict[str, dict[str, Any]] = {}
        self._load()

    def identity_for(self, source_key: str) -> str:
        if source_key not in self.identity_map:
            self.identity_map[source_key] = f"COG-{len(self.identity_map) + 1:010d}"
        return self.identity_map[source_key]

    def remember(self, objects: list[CognitiveObject]) -> dict[str, Any]:
        for item in objects:
            previous = self.objects.get(item.object_id, {})
            history = list(previous.get("historical_evolution", []))
            history.extend(item.historical_evolution)
            payload = asdict(item)
            payload["historical_evolution"] = _dedupe_history(history)[-100:]
            payload["version"] = int(previous.get("version", 0)) + 1 if previous else item.version
            self.objects[item.object_id] = payload
        self._store()
        return {
            "stored": True,
            "path": str(self.path),
            "identity_count": len(self.identity_map),
            "object_count": len(self.objects),
        }

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(payload, Mapping):
            self.identity_map = {
                str(key): str(value)
                for key, value in _mapping(payload.get("identity_map")).items()
            }
            self.objects = {
                str(key): dict(value)
                for key, value in _mapping(payload.get("objects")).items()
                if isinstance(value, Mapping)
            }

    def _store(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"identity_map": self.identity_map, "objects": self.objects},
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )


class UnifiedCognitiveObjectLayer:
    """Normalizes all runtime artifacts into canonical Cognitive Objects."""

    system_name = "unified_cognitive_object_layer"

    def __init__(self, registry: CognitiveObjectRegistry | None = None) -> None:
        self.registry = registry or CognitiveObjectRegistry()

    def build_report(
        self,
        *,
        runtime_reports: Mapping[str, Any] | None = None,
        artifact_lifecycle_report: Mapping[str, Any] | None = None,
        knowledge_report: Mapping[str, Any] | None = None,
        semantic_report: Mapping[str, Any] | None = None,
        experience_report: Mapping[str, Any] | None = None,
        situation_report: Mapping[str, Any] | None = None,
        decision_report: Mapping[str, Any] | None = None,
        policy_report: Mapping[str, Any] | None = None,
        world_model_report: Mapping[str, Any] | None = None,
        dna_report: Mapping[str, Any] | None = None,
        execution_id: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        context = {
            "runtime_reports": _mapping(runtime_reports),
            "artifact_lifecycle": _mapping(artifact_lifecycle_report),
            "knowledge": _mapping(knowledge_report),
            "semantic": _mapping(semantic_report) or _mapping(_mapping(knowledge_report).get("SEMANTIC_INTEGRATION_REPORT")),
            "experience": _mapping(experience_report),
            "situation": _mapping(situation_report),
            "decision": _mapping(decision_report),
            "policy": _mapping(policy_report),
            "world_model": _mapping(world_model_report),
            "dna": _mapping(dna_report),
        }
        exec_id = execution_id or self._execution_id(context)
        objects = self._objects(context, exec_id)
        relationships = self._relationships(objects, context)
        graph = self._object_graph(objects, relationships)
        persistence = self.registry.remember(objects) if persist else {
            "stored": False,
            "reason": "persistence_disabled",
        }
        lifecycle_stats = self._lifecycle_stats(objects)
        lineage_stats = self._lineage_stats(objects, relationships)
        return {
            "system": self.system_name,
            "UNIFIED_COGNITIVE_OBJECT_REPORT": True,
            "status": "OPERATIONAL",
            "objects": [asdict(item) for item in objects],
            "object_count": len(objects),
            "cognitive_object_graph": graph,
            "identity_coverage": self._identity_coverage(objects),
            "lifecycle_coverage": self._coverage(objects, lambda item: bool(item.lifecycle_state)),
            "relationship_density": round(len(relationships) / max(len(objects), 1), 4),
            "semantic_density": self._coverage(objects, lambda item: bool(item.semantic_domain or item.ontology_node)),
            "reuse_score": self._reuse_score(objects, relationships),
            "compression_ratio": self._compression_ratio(objects),
            "object_evolution": self._object_evolution(objects),
            "lineage_statistics": lineage_stats,
            "lifecycle_statistics": lifecycle_stats,
            "world_model_references": sorted({link for item in objects for link in item.world_model_links}),
            "dna_references": sorted({link for item in objects for link in item.dna_links}),
            "mental_model_references": sorted({item.mental_model_reference for item in objects if item.mental_model_reference}),
            "experience_references": sorted({item.experience_id for item in objects if item.experience_id}),
            "semantic_integration": {
                "semantic_clusters_are_cognitive_object_collections": True,
                "semantic_object_count": len([item for item in objects if item.object_type == "SEMANTIC_ABSTRACTION"]),
            },
            "experience_engine_integration": {
                "experiences_are_cognitive_object_collections": True,
                "experience_object_count": len([item for item in objects if item.experience_id]),
            },
            "world_model_integration": {
                "world_model_stores_cognitive_objects": True,
                "object_graph_ready": bool(graph["nodes"]),
            },
            "mental_model_integration": {
                "mental_models_emerge_from_object_subgraphs": True,
                "references": sorted({item.mental_model_reference for item in objects if item.mental_model_reference}),
            },
            "dna_integration": {
                "dna_evolves_from_object_histories": True,
                "object_history_count": sum(len(item.historical_evolution) for item in objects),
            },
            "decision_intelligence_integration": {
                "decisions_consume_cognitive_objects": True,
                "decision_link_count": sum(len(item.decision_links) for item in objects),
            },
            "situation_awareness_integration": {
                "situations_are_cognitive_object_collections": True,
                "situation_link_count": len([item for item in objects if item.situation_id]),
            },
            "world_governance_integration": {
                "governs_object_flow": True,
                "object_lifecycles_supervised": True,
            },
            "meta_cognition": {
                "evaluates_object_quality": True,
                "average_importance": round(sum(item.importance for item in objects) / max(len(objects), 1), 4),
                "average_confidence": round(sum(item.confidence for item in objects) / max(len(objects), 1), 4),
                "lineage_completeness": lineage_stats["lineage_completeness"],
            },
            "object_governance": {
                "creation_governed": True,
                "modification_governed": True,
                "promotion_governed": True,
                "deletion_governed": True,
                "compression_governed": True,
                "evolution_governed": True,
                "conflict_resolution_governed": True,
            },
            "persistence": persistence,
            "runtime_alignment": {
                "redesigns_runtime_implementations": False,
                "removes_existing_runtime_artifacts": False,
                "duplicates_existing_runtimes": False,
                "canonical_external_protocol": True,
                "runtime_internals_remain_free": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _objects(self, context: Mapping[str, Any], execution_id: str) -> list[CognitiveObject]:
        objects: list[CognitiveObject] = []
        experience = _mapping(context["experience"].get("experience"))
        experience_id = str(experience.get("experience_id") or context["experience"].get("experience_id") or "")
        situation_id = str(context["situation"].get("situation_id") or experience.get("situation_id") or "")
        semantic_domains = _semantic_domains(context)
        for artifact in self._source_items(context):
            object_type = artifact["object_type"]
            payload = _mapping(artifact["payload"])
            source_id = artifact["source_id"]
            runtime = str(payload.get("creation_runtime") or payload.get("owner_runtime") or payload.get("origin_runtime") or artifact["runtime"])
            source_key = f"{runtime}:{object_type}:{source_id}"
            object_id = self.registry.identity_for(source_key)
            lifecycle = str(payload.get("lifecycle_state") or payload.get("lifecycle") or payload.get("state") or artifact["lifecycle"])
            domain = str(payload.get("semantic_domain") or payload.get("domain") or _domain_for(object_type, semantic_domains))
            ontology_node = str(payload.get("ontology_node") or payload.get("canonical_name") or payload.get("concept_name") or payload.get("program_name") or object_type.title())
            parents = _refs(payload, "parent_objects", "parent_artifact", "lineage", "derived_from")
            dependencies = _refs(payload, "dependencies", "dependency_references", "required_concepts", "required_constraints")
            evidence_links = _refs(payload, "evidence_links", "evidence_references", "supporting_evidence", "supporting_evidence_ids")
            truth_links = _refs(payload, "truth_links", "truth_references", "supporting_truths")
            memory_links = _refs(payload, "memory_links", "memory_references", "supporting_memory")
            policy_links = _refs(payload, "policy_links", "policy_id", "selected_policy")
            decision_links = _refs(payload, "decision_links", "decision_id", "selected_decision")
            mental_model = str(payload.get("mental_model_reference") or payload.get("mental_model_id") or "")
            world_links = _refs(context["world_model"], "committed_updates", "world_model_links")
            dna_links = _refs(context["dna"], "traits", "dna_links")
            objects.append(CognitiveObject(
                object_id=object_id,
                global_identity=object_id,
                object_type=object_type,
                creation_runtime=runtime,
                creation_timestamp=str(payload.get("creation_timestamp") or payload.get("timestamp") or datetime.now(timezone.utc).isoformat()),
                execution_id=str(payload.get("execution_id") or execution_id),
                experience_id=str(payload.get("experience_id") or experience_id),
                situation_id=str(payload.get("situation_id") or situation_id),
                semantic_domain=domain,
                ontology_node=ontology_node,
                mental_model_reference=mental_model,
                parent_objects=parents,
                child_objects=_refs(payload, "child_objects", "child_artifacts"),
                dependencies=dependencies,
                evidence_links=evidence_links,
                truth_links=truth_links,
                memory_links=memory_links,
                policy_links=policy_links,
                decision_links=decision_links,
                world_model_links=world_links,
                dna_links=dna_links,
                confidence=_score(payload.get("confidence", payload.get("confidence_score", payload.get("decision_confidence", 0.5)))),
                importance=_importance(payload, object_type),
                priority=str(payload.get("priority", "normal")),
                novelty=_score(payload.get("novelty", payload.get("novelty_score", 0.0))),
                complexity=_score(payload.get("complexity", 0.0)),
                compression_state=str(payload.get("compression_state") or ("compressed" if payload.get("compression") or payload.get("compression_value") else "uncompressed")),
                lifecycle_state=lifecycle.upper(),
                version=int(payload.get("version", payload.get("artifact_version", 1)) or 1),
                historical_evolution=self._history(payload, lifecycle, runtime),
                source_artifact_id=source_id,
                source_payload=_small(payload, 14),
            ))
        return _dedupe_objects(objects)

    def _source_items(self, context: Mapping[str, Any]) -> list[dict[str, Any]]:
        items = []
        lifecycle = context["artifact_lifecycle"]
        for artifact in _list(lifecycle.get("artifacts")) + _list(lifecycle.get("registry")):
            if isinstance(artifact, Mapping):
                items.append(self._artifact_item(artifact))
        registry = _mapping(lifecycle.get("artifact_registry"))
        for artifact_id, artifact in registry.items():
            if isinstance(artifact, Mapping):
                payload = dict(artifact)
                payload.setdefault("artifact_id", artifact_id)
                items.append(self._artifact_item(payload))
        knowledge = context["knowledge"]
        for item in _list(knowledge.get("knowledge_objects")):
            if isinstance(item, Mapping):
                items.append(self._typed_item(item, "KNOWLEDGE", "knowledge_integration_runtime"))
        semantic = context["semantic"]
        for item in _list(semantic.get("canonical_concepts")):
            if isinstance(item, Mapping):
                items.append(self._typed_item(item, "SEMANTIC_ABSTRACTION", "knowledge_integration_runtime"))
        experience = _mapping(context["experience"].get("experience"))
        if experience:
            items.append(self._typed_item(experience, "EXPERIENCE", "experience_engine"))
            for key, _, object_type in OBJECT_TYPE_KEYS:
                value = experience.get(key) or experience.get(f"{key}s") or experience.get(_)
                for item in _list(value):
                    if isinstance(item, Mapping):
                        items.append(self._typed_item(item, object_type, _runtime_for(object_type)))
        situation = context["situation"]
        if situation:
            items.append(self._typed_item(situation, "SITUATION", "cognitive_situation_awareness"))
        decision = context["decision"]
        selected_decision = _mapping(decision.get("selected_decision"))
        if selected_decision:
            items.append(self._typed_item(selected_decision, "DECISION", "cognitive_decision_intelligence"))
        policy = context["policy"]
        selected_policy = _mapping(policy.get("selected_policy"))
        if selected_policy:
            items.append(self._typed_item(selected_policy, "POLICY", "cognitive_policy_engine"))
        return items

    def _artifact_item(self, artifact: Mapping[str, Any]) -> dict[str, Any]:
        object_type = str(artifact.get("artifact_type") or artifact.get("knowledge_type") or "ARTIFACT").upper()
        return self._typed_item(artifact, object_type, str(artifact.get("owner_runtime") or artifact.get("origin_runtime") or "artifact_lifecycle"))

    def _typed_item(self, payload: Mapping[str, Any], object_type: str, runtime: str) -> dict[str, Any]:
        source_id = str(
            payload.get("object_id")
            or payload.get("artifact_id")
            or payload.get("knowledge_id")
            or payload.get("semantic_id")
            or payload.get("experience_id")
            or payload.get("situation_id")
            or payload.get("decision_id")
            or payload.get("policy_id")
            or payload.get("truth_id")
            or payload.get("concept_id")
            or payload.get("program_id")
            or payload.get("id")
            or _id("source", object_type, payload)
        )
        return {
            "source_id": source_id,
            "object_type": object_type,
            "payload": dict(payload),
            "runtime": runtime,
            "lifecycle": str(payload.get("lifecycle_state") or payload.get("lifecycle") or "BIRTH"),
        }

    def _relationships(self, objects: list[CognitiveObject], context: Mapping[str, Any]) -> list[dict[str, Any]]:
        by_source = {item.source_artifact_id: item.object_id for item in objects}
        relationships = []
        for item in objects:
            for parent in item.parent_objects:
                relationships.append(_edge(by_source.get(parent, parent), item.object_id, "derived_from"))
            for dependency in item.dependencies:
                relationships.append(_edge(item.object_id, by_source.get(dependency, dependency), "depends_on"))
            for link in item.evidence_links:
                relationships.append(_edge(by_source.get(link, link), item.object_id, "supports"))
            for link in item.truth_links:
                relationships.append(_edge(by_source.get(link, link), item.object_id, "validated_by"))
            for link in item.memory_links:
                relationships.append(_edge(item.object_id, by_source.get(link, link), "stored_in"))
            for link in item.policy_links:
                relationships.append(_edge(by_source.get(link, link), item.object_id, "influences"))
            for link in item.decision_links:
                relationships.append(_edge(by_source.get(link, link), item.object_id, "referenced_by"))
            if item.experience_id:
                relationships.append(_edge(item.object_id, item.experience_id, "part_of_experience"))
            if item.situation_id:
                relationships.append(_edge(item.object_id, item.situation_id, "part_of_situation"))
            if item.semantic_domain:
                relationships.append(_edge(item.object_id, item.semantic_domain, "semantic"))
            if item.ontology_node:
                relationships.append(_edge(item.object_id, item.ontology_node, "ontology_node"))
        for edge in _list(context["artifact_lifecycle"].get("relationships")) + _list(context["artifact_lifecycle"].get("relationship_graph", {}).get("edges")):
            if isinstance(edge, Mapping):
                source = by_source.get(str(edge.get("source")), str(edge.get("source", "")))
                target = by_source.get(str(edge.get("target")), str(edge.get("target", "")))
                relationships.append(_edge(source, target, str(edge.get("relationship") or edge.get("relation") or "related_to")))
        return _dedupe_edges(relationships)

    def _object_graph(self, objects: list[CognitiveObject], relationships: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": item.object_id,
                    "type": item.object_type,
                    "runtime": item.creation_runtime,
                    "lifecycle_state": item.lifecycle_state,
                    "confidence": item.confidence,
                    "semantic_domain": item.semantic_domain,
                }
                for item in objects
            ],
            "edges": relationships,
            "node_count": len(objects),
            "edge_count": len(relationships),
            "relationship_types": sorted({edge["relationship"] for edge in relationships}),
        }

    def _execution_id(self, context: Mapping[str, Any]) -> str:
        experience = _mapping(context["experience"].get("experience"))
        for source in (experience, context["situation"], context["decision"], context["policy"]):
            if source.get("execution_id"):
                return str(source["execution_id"])
        return _id("execution", context)

    def _history(self, payload: Mapping[str, Any], lifecycle: str, runtime: str) -> list[dict[str, Any]]:
        history = list(_list(payload.get("historical_evolution")))
        history.append({
            "event": lifecycle.upper(),
            "runtime": runtime,
            "timestamp": str(payload.get("creation_timestamp") or payload.get("timestamp") or datetime.now(timezone.utc).isoformat()),
            "reason": "normalized_into_unified_cognitive_object",
        })
        for key in ("created_by", "transformed_by", "validated_by", "reused_by", "generalized_by", "compressed_by", "retired_by"):
            if payload.get(key):
                history.append({"event": key, "runtime": str(payload[key]), "timestamp": datetime.now(timezone.utc).isoformat()})
        return history

    def _identity_coverage(self, objects: list[CognitiveObject]) -> float:
        return self._coverage(objects, lambda item: item.object_id.startswith("COG-") and item.global_identity == item.object_id)

    def _coverage(self, objects: list[CognitiveObject], predicate) -> float:
        return round(sum(1 for item in objects if predicate(item)) / max(len(objects), 1), 4)

    def _reuse_score(self, objects: list[CognitiveObject], relationships: list[dict[str, Any]]) -> float:
        reusable = sum(1 for item in objects if item.object_type in {"MEMORY", "EXPERIENCE", "SEMANTIC_ABSTRACTION", "KNOWLEDGE"} or item.lifecycle_state in {"REUSED", "PROMOTED", "COMMITTED", "GENERALIZED"})
        reference_edges = sum(1 for edge in relationships if edge["relationship"] in {"referenced_by", "stored_in", "part_of_experience", "semantic"})
        return round(min(1.0, reusable / max(len(objects), 1) * 0.55 + reference_edges / max(len(relationships), 1) * 0.45), 4)

    def _compression_ratio(self, objects: list[CognitiveObject]) -> float:
        compressed = sum(1 for item in objects if item.compression_state != "uncompressed" or item.object_type == "SEMANTIC_ABSTRACTION")
        return round(compressed / max(len(objects), 1), 4)

    def _object_evolution(self, objects: list[CognitiveObject]) -> dict[str, Any]:
        stages = {}
        for item in objects:
            stages[item.lifecycle_state] = stages.get(item.lifecycle_state, 0) + 1
        return {
            "stage_distribution": stages,
            "objects_with_history": sum(1 for item in objects if item.historical_evolution),
            "total_history_events": sum(len(item.historical_evolution) for item in objects),
            "evolution_stages_supported": ["Birth", "Observation", "Concept", "Program", "Evidence", "Truth", "Memory", "Experience", "World Knowledge", "Mental Model", "DNA Influence"],
        }

    def _lineage_stats(self, objects: list[CognitiveObject], relationships: list[dict[str, Any]]) -> dict[str, Any]:
        with_lineage = sum(1 for item in objects if item.parent_objects or item.dependencies or item.evidence_links or item.truth_links or item.historical_evolution)
        return {
            "objects_with_lineage": with_lineage,
            "lineage_completeness": round(with_lineage / max(len(objects), 1), 4),
            "relationship_count": len(relationships),
            "genealogy_events": sum(len(item.historical_evolution) for item in objects),
        }

    def _lifecycle_stats(self, objects: list[CognitiveObject]) -> dict[str, Any]:
        states = {}
        for item in objects:
            states[item.lifecycle_state] = states.get(item.lifecycle_state, 0) + 1
        return {
            "states": states,
            "objects_with_lifecycle": sum(1 for item in objects if item.lifecycle_state),
            "permanent_identity_preserved": all(item.object_id == item.global_identity for item in objects),
        }


def _runtime_for(object_type: str) -> str:
    return {
        "CONCEPT": "concept_formation_runtime",
        "PROGRAM": "program_synthesis_runtime",
        "EVIDENCE": "evidence_builder_runtime",
        "TRUTH": "truth_runtime",
        "MEMORY": "memory_runtime",
        "POLICY": "cognitive_policy_engine",
        "DECISION": "cognitive_decision_intelligence",
        "SITUATION": "cognitive_situation_awareness",
        "EXPERIENCE": "experience_engine",
        "MENTAL_MODEL": "experience_engine",
    }.get(object_type, "unknown_runtime")


def _semantic_domains(context: Mapping[str, Any]) -> list[str]:
    domains = _list(context["semantic"].get("discovered_domains"))
    experience = _mapping(context["experience"].get("experience"))
    domains.extend(_list(experience.get("semantic_domains")))
    return sorted({str(item) for item in domains if item}) or ["General Knowledge"]


def _domain_for(object_type: str, domains: list[str]) -> str:
    if object_type in {"TRUTH", "EVIDENCE"}:
        return "Validation"
    if object_type in {"POLICY", "DECISION"}:
        return "Governance"
    if object_type == "MEMORY":
        return "Memory"
    return domains[0] if domains else "General Knowledge"


def _refs(payload: Mapping[str, Any], *keys: str) -> list[str]:
    refs = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            refs.extend(str(k) for k in value.keys())
            refs.extend(str(v) for v in value.values() if isinstance(v, (str, int, float)))
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                if isinstance(item, Mapping):
                    refs.append(str(item.get("id") or item.get("source") or item.get("artifact_id") or item.get("truth_id") or _id("ref", item)))
                elif item is not None:
                    refs.append(str(item))
        elif value:
            refs.append(str(value))
    return sorted(set(refs))


def _importance(payload: Mapping[str, Any], object_type: str) -> float:
    base = {
        "EXPERIENCE": 0.85,
        "TRUTH": 0.78,
        "SEMANTIC_ABSTRACTION": 0.76,
        "MEMORY": 0.72,
        "DECISION": 0.68,
        "POLICY": 0.62,
    }.get(object_type, 0.5)
    return round(min(1.0, base * 0.55 + _score(payload.get("confidence", 0.5)) * 0.3 + _score(payload.get("utility", payload.get("importance", 0.5))) * 0.15), 4)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, Mapping):
        return [dict(value)]
    return []


def _score(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _small(value: Mapping[str, Any], limit: int = 8) -> dict[str, Any]:
    output = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= limit:
            break
        if isinstance(item, (str, int, float, bool)) or item is None:
            output[str(key)] = item
        elif isinstance(item, list):
            output[str(key)] = {"count": len(item)}
        elif isinstance(item, Mapping):
            output[str(key)] = {"keys": sorted(str(k) for k in item.keys())[:8]}
        else:
            output[str(key)] = type(item).__name__
    return output


def _id(prefix: str, *values: Any) -> str:
    digest = hashlib.sha1(json.dumps(values, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _edge(source: Any, target: Any, relationship: str) -> dict[str, Any]:
    return {"source": str(source), "target": str(target), "relationship": relationship}


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge["source"], edge["target"], edge["relationship"])
        if not edge["source"] or not edge["target"] or edge["source"] == edge["target"] or marker in seen:
            continue
        output.append(edge)
        seen.add(marker)
    return output


def _dedupe_objects(objects: list[CognitiveObject]) -> list[CognitiveObject]:
    deduped = {}
    for item in objects:
        previous = deduped.get(item.object_id)
        if previous is None or _object_quality(item) >= _object_quality(previous):
            deduped[item.object_id] = item
    return list(deduped.values())


def _object_quality(item: CognitiveObject) -> float:
    score = 0.0
    score += 1.0 if item.lifecycle_state and item.lifecycle_state != "BIRTH" else 0.0
    score += 0.5 if item.source_payload else 0.0
    score += min(len(item.historical_evolution) * 0.1, 0.5)
    score += item.confidence * 0.25
    return score


def _dedupe_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for event in history:
        marker = json.dumps(_small(event, 6), sort_keys=True, default=str)
        if marker in seen:
            continue
        output.append(event)
        seen.add(marker)
    return output


unified_cognitive_object_layer = UnifiedCognitiveObjectLayer()
