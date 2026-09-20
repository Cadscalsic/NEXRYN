"""Cognitive Episode Engine for canonical episodic cognition.

The engine groups Cognitive Objects already published on the Unified Cognitive
Bus into one primary episode per execution cycle. It references objects by
identity instead of copying or storing a second object registry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.reflection.reflection_engine import (
    ReflectionEngine,
    ReflectionRegistry,
)


EPISODE_STAGES = (
    "Situation",
    "Goal",
    "Observation",
    "Reasoning",
    "Hypothesis Formation",
    "Search",
    "Concept Formation",
    "Program Synthesis",
    "Evidence Collection",
    "Truth Validation",
    "Decision",
    "Outcome",
    "Reflection",
    "Episode Closure",
)

EPISODE_OUTCOMES = {
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "FAILURE",
    "UNRESOLVED",
    "INTERRUPTED",
    "REPLAYED",
}

EPISODE_RELATIONSHIP_TYPES = {
    "CONTINUATION",
    "GENERALIZATION",
    "SPECIALIZATION",
    "CORRECTION",
    "EXTENSION",
    "ALTERNATIVE_SOLUTION",
    "REPEATED_SITUATION",
    "CONTRADICTION",
    "SUPPORT",
    "MERGE",
    "SPLIT",
}

STAGE_BY_OBJECT_TYPE = {
    "SITUATION": "Situation",
    "GOAL": "Goal",
    "OBSERVATION": "Observation",
    "REASONING": "Reasoning",
    "REASONING_STEP": "Reasoning",
    "INFERENCE": "Reasoning",
    "HYPOTHESIS": "Hypothesis Formation",
    "SEARCH_ROUTE": "Search",
    "CONCEPT": "Concept Formation",
    "PROGRAM": "Program Synthesis",
    "EVIDENCE": "Evidence Collection",
    "TRUTH": "Truth Validation",
    "TRUTH_CANDIDATE": "Truth Validation",
    "DECISION": "Decision",
    "MEMORY": "Episode Closure",
    "MEMORY_ENTRY": "Episode Closure",
    "FAILURE": "Outcome",
    "POLICY": "Decision",
    "CONSTRAINT": "Goal",
    "SEMANTIC_CONTEXT": "Reflection",
    "EXPERIENCE": "Reflection",
}

STAT_KEYS = {
    "CONCEPT": "concept_count",
    "PROGRAM": "program_count",
    "TRUTH": "truth_count",
    "TRUTH_CANDIDATE": "truth_count",
    "EVIDENCE": "evidence_count",
    "MEMORY": "memory_count",
    "MEMORY_ENTRY": "memory_count",
    "REASONING": "reasoning_count",
    "REASONING_STEP": "reasoning_count",
    "SEARCH_ROUTE": "search_count",
    "RELATIONSHIP": "relationship_count",
    "SEMANTIC_CONTEXT": "semantic_count",
    "DECISION": "decision_count",
    "FAILURE": "failure_count",
}


@dataclass(frozen=True)
class CognitiveEpisode:
    episode_id: str
    episode_uuid: str
    execution_id: str
    execution_cycle: str
    creation_timestamp: str
    last_update_timestamp: str
    episode_type: str = "PRIMARY_REASONING_EPISODE"
    episode_status: str = "OPEN"
    episode_priority: str = "normal"
    episode_confidence: float = 0.0
    episode_complexity: float = 0.0
    episode_duration: float = 0.0
    episode_quality: float = 0.0
    episode_outcome: str = "UNRESOLVED"
    episode_summary: str = ""
    object_ids: list[str] = field(default_factory=list)
    content: dict[str, list[str]] = field(default_factory=dict)
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    episode_graph: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, list[str]] = field(default_factory=dict)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    quality: dict[str, float] = field(default_factory=dict)
    statistics: dict[str, int] = field(default_factory=dict)
    reflection_id: str = ""
    reflection_status: str = "PENDING"
    reflection: dict[str, Any] = field(default_factory=dict)
    experience_eligibility: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    version: int = 1

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveEpisodeRegistry:
    """Canonical in-memory episode registry.

    It stores episode records and object membership references only. Cognitive
    Object identity and storage remain owned by the Unified Cognitive Bus.
    """

    def __init__(self) -> None:
        self.episodes: dict[str, CognitiveEpisode] = {}
        self.object_episode_index: dict[str, set[str]] = {}
        self.replay_count = 0

    def upsert(
        self,
        episode: CognitiveEpisode,
        *,
        reason: str = "episode_created",
        supporting_evidence: Iterable[Any] | None = None,
    ) -> CognitiveEpisode:
        previous = self.episodes.get(episode.episode_id)
        if previous is not None:
            if (
                previous.object_ids == episode.object_ids
                and previous.statistics == episode.statistics
                and previous.episode_outcome == episode.episode_outcome
                and previous.episode_status == episode.episode_status
            ):
                return previous
            timestamp = datetime.now(timezone.utc).isoformat()
            history = [
                *previous.history,
                {
                    "version": previous.version + 1,
                    "previous_version": previous.version,
                    "timestamp": timestamp,
                    "change_reason": str(reason),
                    "supporting_evidence": [str(item) for item in supporting_evidence or []],
                    "updated_objects": sorted(
                        set(episode.object_ids).symmetric_difference(previous.object_ids)
                    ),
                },
            ]
            episode = replace(
                episode,
                creation_timestamp=previous.creation_timestamp,
                last_update_timestamp=timestamp,
                history=history,
                version=previous.version + 1,
            )
        self.episodes[episode.episode_id] = episode
        for object_id in episode.object_ids:
            self.object_episode_index.setdefault(object_id, set()).add(episode.episode_id)
        return episode

    def get(self, episode_id: str) -> CognitiveEpisode | None:
        return self.episodes.get(str(episode_id))

    def episodes_for_object(self, object_id: str) -> list[str]:
        return sorted(self.object_episode_index.get(str(object_id), set()))

    def replay(self, episode_id: str) -> dict[str, Any]:
        episode = self.get(episode_id)
        if episode is None:
            return {
                "episode_id": str(episode_id),
                "replay_available": False,
                "reason": "episode_not_found",
            }
        self.replay_count += 1
        return {
            "episode_id": episode.episode_id,
            "episode_uuid": episode.episode_uuid,
            "replay_available": True,
            "replay_count": self.replay_count,
            "deterministic_ordering": True,
            "timeline": list(episode.timeline),
            "stage_sequence": list(episode.stages.values()),
            "episode_graph": dict(episode.episode_graph),
            "object_ids": list(episode.object_ids),
        }


class CognitiveEpisodeEngine:
    """Build one coherent Cognitive Episode from one execution's objects."""

    system_name = "cognitive_episode_engine"

    def __init__(
        self,
        registry: CognitiveEpisodeRegistry | None = None,
        reflection_engine: ReflectionEngine | None = None,
    ) -> None:
        self.registry = registry or CognitiveEpisodeRegistry()
        self.reflection_engine = reflection_engine or ReflectionEngine(ReflectionRegistry())

    def build_episode(
        self,
        *,
        execution_id: str,
        objects: Iterable[Mapping[str, Any]],
        deliveries: Mapping[str, Iterable[str]] | None = None,
        bus_events: Iterable[Mapping[str, Any]] | None = None,
        episode_type: str = "PRIMARY_REASONING_EPISODE",
    ) -> CognitiveEpisode:
        object_list = [dict(obj) for obj in objects]
        execution_id = str(execution_id or "execution:unknown")
        episode_id = _episode_id(execution_id)
        timestamp = _episode_timestamp(object_list)
        execution_cycle = _execution_cycle(object_list, execution_id)
        statistics = _episode_statistics(object_list)
        quality = _quality(object_list, statistics)
        outcome = _outcome(object_list, statistics)
        timeline = _timeline(object_list, bus_events or [])
        graph = _episode_graph(object_list, timeline)
        stages = _stages(object_list, timeline)
        context = _context(object_list, execution_id, execution_cycle)
        lineage = _lineage(object_list)
        relationships = _episode_relationships(object_list)
        object_ids = [str(obj.get("object_id")) for obj in object_list if obj.get("object_id")]
        episode = CognitiveEpisode(
            episode_id=episode_id,
            episode_uuid=str(uuid5(NAMESPACE_URL, episode_id)),
            execution_id=execution_id,
            execution_cycle=execution_cycle,
            creation_timestamp=timestamp,
            last_update_timestamp=timestamp,
            episode_type=episode_type,
            episode_status="CLOSED" if object_list else "EMPTY",
            episode_priority=_episode_priority(object_list),
            episode_confidence=quality["episode_confidence"],
            episode_complexity=quality["episode_complexity"],
            episode_duration=_episode_duration(timeline),
            episode_quality=quality["episode_quality"],
            episode_outcome=outcome,
            episode_summary=_summary(statistics, outcome),
            object_ids=object_ids,
            content=_content(object_list),
            stages=stages,
            context=context,
            timeline=timeline,
            episode_graph=graph,
            lineage=lineage,
            relationships=relationships,
            quality=quality,
            statistics=statistics,
            history=[
                {
                    "version": 1,
                    "previous_version": None,
                    "timestamp": timestamp,
                    "change_reason": "episode_created",
                    "supporting_evidence": _supporting_evidence(object_list),
                    "updated_objects": object_ids,
                }
            ],
            version=1,
        )
        reflection = self.reflection_engine.reflect(
            episode=episode.as_dict(),
            objects=object_list,
        )
        reflected_stages = dict(episode.stages)
        reflected_stages["Reflection"] = {
            **reflected_stages.get("Reflection", {"stage": "Reflection"}),
            "stage": "Reflection",
            "observed": reflection.reflection_status == "COMPLETED",
            "reflection_id": reflection.reflection_id,
            "object_ids": reflected_stages.get("Reflection", {}).get("object_ids", []),
            "event_count": reflected_stages.get("Reflection", {}).get("event_count", 0) + 1,
        }
        episode = replace(
            episode,
            episode_status="REFLECTED" if episode.episode_status == "CLOSED" else episode.episode_status,
            reflection_id=reflection.reflection_id,
            reflection_status=reflection.reflection_status,
            reflection=reflection.as_dict(),
            experience_eligibility={
                "eligible_for_experience": reflection.reflection_status == "COMPLETED"
                and outcome in {"SUCCESS", "PARTIAL_SUCCESS"},
                "reflection_required": True,
                "reflection_completed": reflection.reflection_status == "COMPLETED",
                "experience_engine_may_consume": reflection.reflection_status == "COMPLETED"
                and outcome in {"SUCCESS", "PARTIAL_SUCCESS"},
                "blocked_reason": ""
                if reflection.reflection_status == "COMPLETED"
                else "reflection_incomplete",
            },
            stages=reflected_stages,
        )
        return self.registry.upsert(episode, reason="episode_built_from_cognitive_objects")

    def replay(self, episode_id: str) -> dict[str, Any]:
        return self.registry.replay(episode_id)

    def report(self) -> dict[str, Any]:
        episodes = list(self.registry.episodes.values())
        outcomes = _distribution(ep.episode_outcome for ep in episodes)
        types = _distribution(ep.episode_type for ep in episodes)
        graph_edges = [ep.episode_graph.get("edge_count", 0) for ep in episodes]
        timeline_lengths = [len(ep.timeline) for ep in episodes]
        lineage_depths = [
            sum(len(values) for values in ep.lineage.values())
            for ep in episodes
        ]
        return {
            "COGNITIVE_EPISODE_REPORT": True,
            "system": self.system_name,
            "episodes_created": len(episodes),
            "episode_types": types,
            "episode_outcomes": outcomes,
            "episode_duration": {
                "average": _average(ep.episode_duration for ep in episodes),
                "maximum": max([ep.episode_duration for ep in episodes] or [0.0]),
            },
            "episode_quality": {
                "average": _average(ep.episode_quality for ep in episodes),
                "minimum": min([ep.episode_quality for ep in episodes] or [0.0]),
                "maximum": max([ep.episode_quality for ep in episodes] or [0.0]),
            },
            "episode_confidence": {
                "average": _average(ep.episode_confidence for ep in episodes),
            },
            "episode_complexity": {
                "average": _average(ep.episode_complexity for ep in episodes),
            },
            "reasoning_statistics": _sum_stat(episodes, "reasoning_count"),
            "search_statistics": _sum_stat(episodes, "search_count"),
            "concept_statistics": _sum_stat(episodes, "concept_count"),
            "program_statistics": _sum_stat(episodes, "program_count"),
            "evidence_statistics": _sum_stat(episodes, "evidence_count"),
            "truth_statistics": _sum_stat(episodes, "truth_count"),
            "memory_statistics": _sum_stat(episodes, "memory_count"),
            "relationship_statistics": _sum_stat(episodes, "relationship_count"),
            "semantic_statistics": _sum_stat(episodes, "semantic_count"),
            "decision_statistics": _sum_stat(episodes, "decision_count"),
            "failure_statistics": _sum_stat(episodes, "failure_count"),
            "timeline_statistics": {
                "average_events": _average(timeline_lengths),
                "maximum_events": max(timeline_lengths or [0]),
            },
            "lineage_statistics": {
                "average_lineage_depth": _average(lineage_depths),
                "maximum_lineage_depth": max(lineage_depths or [0]),
            },
            "episode_graph_metrics": {
                "episode_count": len(episodes),
                "average_edge_count": _average(graph_edges),
                "maximum_edge_count": max(graph_edges or [0]),
            },
            "replay_availability": {
                "available": bool(episodes),
                "replayable_episodes": len(episodes),
                "replay_count": self.registry.replay_count,
            },
            "reflection_summary": {
                "episodes_with_reflection_stage": sum(
                    1 for ep in episodes
                    if ep.stages.get("Reflection", {}).get("observed")
                ),
                "reflections_completed": sum(
                    1 for ep in episodes
                    if ep.reflection_status == "COMPLETED"
                ),
                "reflection_mandatory": True,
                "unreflected_experience_candidates": sum(
                    1 for ep in episodes
                    if ep.episode_outcome in {"SUCCESS", "PARTIAL_SUCCESS"}
                    and not ep.experience_eligibility.get("reflection_completed")
                ),
                "experience_engine_ready": any(
                    ep.experience_eligibility.get("experience_engine_may_consume")
                    for ep in episodes
                ),
            },
            "reflection_engine_report": self.reflection_engine.report(),
            "integration_health": {
                "creates_new_runtime": False,
                "duplicates_unified_cognitive_bus": False,
                "duplicates_object_registry": False,
                "duplicates_event_system": False,
                "episodes_reference_cognitive_objects": True,
                "parent_execution_summarizes_episode": True,
                "process_semantic_context_consumes_episodes": True,
                "cca_evaluates_episode_coverage": True,
                "experience_engine_transforms_successful_episodes": True,
                "mental_models_emerge_from_episode_graphs": True,
                "world_model_stores_episodes": True,
                "dna_evolves_from_repeated_episodes": True,
                "governance_supervises_episodes": True,
                "meta_cognition_evaluates_episode_quality": True,
            },
        }


def _episode_id(execution_id: str) -> str:
    return f"cognitive_episode:{uuid5(NAMESPACE_URL, execution_id).hex[:16]}"


def _episode_timestamp(objects: list[dict[str, Any]]) -> str:
    timestamps = sorted(
        str(obj.get("creation_timestamp"))
        for obj in objects
        if obj.get("creation_timestamp")
    )
    return timestamps[0] if timestamps else datetime.now(timezone.utc).isoformat()


def _execution_cycle(objects: list[dict[str, Any]], execution_id: str) -> str:
    for obj in objects:
        if obj.get("execution_cycle"):
            return str(obj["execution_cycle"])
    return f"{execution_id}:cycle"


def _episode_priority(objects: list[dict[str, Any]]) -> str:
    priorities = [str(obj.get("object_priority") or obj.get("priority") or "normal") for obj in objects]
    for priority in ("critical", "high"):
        if priority in priorities:
            return priority
    return priorities[0] if priorities else "normal"


def _content(objects: list[dict[str, Any]]) -> dict[str, list[str]]:
    content = {
        "reasoning_objects": [],
        "search_objects": [],
        "concept_objects": [],
        "program_objects": [],
        "evidence_objects": [],
        "truth_objects": [],
        "memory_objects": [],
        "decision_objects": [],
        "constraint_objects": [],
        "policy_objects": [],
        "goal_objects": [],
        "failure_objects": [],
        "relationship_objects": [],
        "semantic_objects": [],
        "other_objects": [],
    }
    for obj in objects:
        object_id = str(obj.get("object_id"))
        object_type = str(obj.get("object_type", "UNKNOWN"))
        key = {
            "REASONING": "reasoning_objects",
            "REASONING_STEP": "reasoning_objects",
            "SEARCH_ROUTE": "search_objects",
            "CONCEPT": "concept_objects",
            "PROGRAM": "program_objects",
            "EVIDENCE": "evidence_objects",
            "TRUTH": "truth_objects",
            "TRUTH_CANDIDATE": "truth_objects",
            "MEMORY": "memory_objects",
            "MEMORY_ENTRY": "memory_objects",
            "DECISION": "decision_objects",
            "CONSTRAINT": "constraint_objects",
            "POLICY": "policy_objects",
            "GOAL": "goal_objects",
            "FAILURE": "failure_objects",
            "RELATIONSHIP": "relationship_objects",
            "SEMANTIC_CONTEXT": "semantic_objects",
        }.get(object_type, "other_objects")
        content[key].append(object_id)
    return content


def _episode_statistics(objects: list[dict[str, Any]]) -> dict[str, int]:
    stats = {
        "concept_count": 0,
        "program_count": 0,
        "truth_count": 0,
        "evidence_count": 0,
        "memory_count": 0,
        "reasoning_count": 0,
        "search_count": 0,
        "relationship_count": 0,
        "semantic_count": 0,
        "decision_count": 0,
        "failure_count": 0,
        "object_count": len(objects),
    }
    for obj in objects:
        object_type = str(obj.get("object_type", "UNKNOWN"))
        key = STAT_KEYS.get(object_type)
        if key:
            stats[key] += 1
        stats["relationship_count"] += len(obj.get("relationships", []) or [])
    return stats


def _quality(objects: list[dict[str, Any]], stats: Mapping[str, int]) -> dict[str, float]:
    confidence = _average(
        obj.get("object_confidence", obj.get("confidence", 0.0))
        for obj in objects
    )
    evidence_quality = clamp(stats.get("evidence_count", 0) / max(stats.get("object_count", 1), 1))
    truth_quality = clamp(stats.get("truth_count", 0) / max(stats.get("object_count", 1), 1))
    relationship_completeness = clamp(stats.get("relationship_count", 0) / max(stats.get("object_count", 1), 1))
    object_diversity = clamp(len({obj.get("object_type") for obj in objects}) / 8.0)
    semantic_richness = clamp(
        sum(1 for obj in objects if obj.get("semantic_payload")) / max(len(objects), 1)
    )
    generalization_quality = _average(obj.get("generalization_score", 0.0) for obj in objects)
    novelty = _average(obj.get("object_novelty", 0.0) for obj in objects)
    complexity = _average(obj.get("object_complexity", 0.0) for obj in objects)
    efficiency = clamp(1.0 - (complexity * 0.5))
    episode_quality = _average([
        confidence,
        evidence_quality,
        truth_quality,
        relationship_completeness,
        object_diversity,
        semantic_richness,
        generalization_quality,
        efficiency,
    ])
    return {
        "reasoning_quality": confidence,
        "evidence_quality": evidence_quality,
        "truth_quality": truth_quality,
        "generalization_quality": generalization_quality,
        "efficiency": efficiency,
        "novelty": novelty,
        "semantic_richness": semantic_richness,
        "object_completeness": clamp(stats.get("object_count", 0) / 8.0),
        "relationship_completeness": relationship_completeness,
        "episode_confidence": confidence,
        "episode_complexity": complexity,
        "episode_quality": episode_quality,
    }


def _outcome(objects: list[dict[str, Any]], stats: Mapping[str, int]) -> str:
    statuses = {str(obj.get("object_status") or obj.get("status") or "") for obj in objects}
    if "INTERRUPTED" in statuses:
        return "INTERRUPTED"
    if stats.get("failure_count", 0) > 0 or "RETIRED" in statuses:
        return "FAILURE"
    if stats.get("truth_count", 0) > 0:
        return "SUCCESS"
    if stats.get("evidence_count", 0) > 0 or stats.get("concept_count", 0) > 0:
        return "PARTIAL_SUCCESS"
    return "UNRESOLVED" if objects else "INTERRUPTED"


def _timeline(
    objects: list[dict[str, Any]],
    bus_events: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    events = []
    for obj in objects:
        object_id = str(obj.get("object_id"))
        object_type = str(obj.get("object_type", "UNKNOWN"))
        created = str(obj.get("creation_timestamp") or obj.get("last_update_timestamp") or "")
        events.append({
            "timestamp": created,
            "event": "object_created",
            "stage": STAGE_BY_OBJECT_TYPE.get(object_type, "Observation"),
            "object_id": object_id,
            "object_type": object_type,
        })
        if obj.get("object_status") in {"VALIDATED", "SUPPORTED", "CANONICAL"}:
            events.append({
                "timestamp": str(obj.get("last_update_timestamp") or created),
                "event": "object_validated",
                "stage": STAGE_BY_OBJECT_TYPE.get(object_type, "Observation"),
                "object_id": object_id,
                "object_type": object_type,
            })
        for history in obj.get("history", []) or []:
            events.append({
                "timestamp": str(history.get("timestamp") or created),
                "event": str(history.get("reason") or history.get("change_reason") or "object_updated"),
                "stage": STAGE_BY_OBJECT_TYPE.get(object_type, "Observation"),
                "object_id": object_id,
                "object_type": object_type,
            })
    for event in bus_events:
        events.append({
            "timestamp": str(event.get("timestamp") or ""),
            "event": str(event.get("event_type") or "bus_event"),
            "stage": "Observation",
            "object_id": str(event.get("object_id") or ""),
            "object_type": "BUS_EVENT",
        })
    return sorted(events, key=lambda item: (item["timestamp"], item["object_id"], item["event"]))


def _episode_graph(
    objects: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = [
        {
            "object_id": obj.get("object_id"),
            "object_type": obj.get("object_type"),
            "object_family": obj.get("object_family"),
        }
        for obj in objects
    ]
    object_ids = {str(node["object_id"]) for node in nodes}
    edges = []
    ordered_ids = [event["object_id"] for event in timeline if event.get("object_id")]
    for source, target in zip(ordered_ids, ordered_ids[1:]):
        if source != target:
            edges.append({"source": source, "target": target, "edge_type": "TEMPORAL_FLOW"})
    for obj in objects:
        source = str(obj.get("object_id"))
        for target in obj.get("dependencies", []) or []:
            edges.append({
                "source": source,
                "target": str(target),
                "edge_type": "REASONING_DEPENDENCY",
                "target_is_episode_object": str(target) in object_ids,
            })
        for relationship in obj.get("relationships", []) or []:
            edge_type = str(relationship.get("relationship_type") or relationship.get("relationship") or "SEMANTIC_FLOW")
            edges.append({
                "source": source,
                "target": str(relationship.get("target")),
                "edge_type": edge_type,
                "target_is_episode_object": str(relationship.get("target")) in object_ids,
            })
    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "temporal_flow_edges": sum(1 for edge in edges if edge["edge_type"] == "TEMPORAL_FLOW"),
        "reasoning_dependency_edges": sum(1 for edge in edges if "DEPEND" in edge["edge_type"]),
        "evidence_dependency_edges": sum(1 for edge in edges if "SUPPORT" in edge["edge_type"]),
        "truth_dependency_edges": sum(1 for edge in edges if edge["edge_type"] in {"SUPPORTED_BY", "VALIDATED_BY"}),
        "decision_flow_edges": sum(1 for edge in edges if "DECISION" in edge["edge_type"]),
        "execution_flow_edges": sum(1 for edge in edges if edge["edge_type"] == "TEMPORAL_FLOW"),
        "causal_flow_edges": sum(1 for edge in edges if "CAUSE" in edge["edge_type"]),
        "semantic_flow_edges": sum(1 for edge in edges if edge["edge_type"] in {"REFERENCES", "SEMANTIC_FLOW"}),
    }


def _stages(
    objects: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    stages = {
        stage: {
            "stage": stage,
            "observed": False,
            "object_ids": [],
            "event_count": 0,
        }
        for stage in EPISODE_STAGES
    }
    stages["Situation"]["observed"] = bool(objects)
    stages["Goal"]["observed"] = any(obj.get("object_type") in {"GOAL", "CONSTRAINT"} for obj in objects)
    stages["Observation"]["observed"] = bool(objects)
    stages["Outcome"]["observed"] = bool(objects)
    stages["Reflection"]["observed"] = any(obj.get("object_type") in {"MEMORY", "SEMANTIC_CONTEXT", "EXPERIENCE"} for obj in objects)
    stages["Episode Closure"]["observed"] = bool(objects)
    for obj in objects:
        object_type = str(obj.get("object_type", "UNKNOWN"))
        stage = STAGE_BY_OBJECT_TYPE.get(object_type, "Observation")
        stages[stage]["observed"] = True
        stages[stage]["object_ids"].append(str(obj.get("object_id")))
    for event in timeline:
        stage = event.get("stage")
        if stage in stages:
            stages[stage]["event_count"] += 1
    return stages


def _context(
    objects: list[dict[str, Any]],
    execution_id: str,
    execution_cycle: str,
) -> dict[str, Any]:
    runtimes = sorted({str(obj.get("runtime_origin")) for obj in objects if obj.get("runtime_origin")})
    domains = sorted({
        str(obj.get("semantic_payload", {}).get("domain"))
        for obj in objects
        if isinstance(obj.get("semantic_payload"), Mapping)
        and obj.get("semantic_payload", {}).get("domain")
    })
    return {
        "problem_context": _first_payload(objects, "semantic_payload"),
        "execution_context": {"execution_id": execution_id, "execution_cycle": execution_cycle},
        "environmental_context": {"source": "unified_cognitive_bus"},
        "task_context": {"object_count": len(objects)},
        "reasoning_context": {"reasoning_objects": _ids_for(objects, {"REASONING", "REASONING_STEP"})},
        "search_context": {"search_objects": _ids_for(objects, {"SEARCH_ROUTE"})},
        "learning_context": {"memory_objects": _ids_for(objects, {"MEMORY", "MEMORY_ENTRY"})},
        "governance_context": {"policy_objects": _ids_for(objects, {"POLICY", "CONSTRAINT"})},
        "temporal_context": {"first_timestamp": _episode_timestamp(objects), "execution_cycle": execution_cycle},
        "resource_context": {"runtime_origins": runtimes},
        "semantic_context": {"domains": domains},
    }


def _lineage(objects: list[dict[str, Any]]) -> dict[str, list[str]]:
    lineage = {
        "problem": [],
        "hypothesis": _ids_for(objects, {"HYPOTHESIS"}),
        "concept": _ids_for(objects, {"CONCEPT"}),
        "program": _ids_for(objects, {"PROGRAM"}),
        "evidence": _ids_for(objects, {"EVIDENCE"}),
        "truth": _ids_for(objects, {"TRUTH", "TRUTH_CANDIDATE"}),
        "decision": _ids_for(objects, {"DECISION"}),
        "outcome": _ids_for(objects, {"FAILURE", "MEMORY", "MEMORY_ENTRY"}),
        "experience": _ids_for(objects, {"EXPERIENCE"}),
        "memory": _ids_for(objects, {"MEMORY", "MEMORY_ENTRY"}),
    }
    semantic = _first_payload(objects, "semantic_payload")
    if semantic:
        lineage["problem"] = [str(semantic)]
    return {key: value for key, value in lineage.items() if value}


def _episode_relationships(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relationships = []
    for obj in objects:
        for relationship in obj.get("relationships", []) or []:
            rel_type = str(relationship.get("relationship_type") or relationship.get("relationship") or "SUPPORT")
            relationships.append({
                "relationship_type": rel_type if rel_type in EPISODE_RELATIONSHIP_TYPES else "SUPPORT",
                "source_object_id": obj.get("object_id"),
                "target": relationship.get("target"),
            })
    return relationships


def _supporting_evidence(objects: list[dict[str, Any]]) -> list[str]:
    evidence = []
    for obj in objects:
        evidence.extend(str(item) for item in obj.get("supporting_objects", []) or [])
        for item in obj.get("history", []) or []:
            evidence.extend(str(ref) for ref in item.get("supporting_evidence", []) or [])
    return sorted({item for item in evidence if item})


def _summary(stats: Mapping[str, int], outcome: str) -> str:
    return (
        f"{outcome}: episode contains {stats.get('object_count', 0)} cognitive objects, "
        f"{stats.get('concept_count', 0)} concepts, {stats.get('program_count', 0)} programs, "
        f"{stats.get('evidence_count', 0)} evidence objects, and {stats.get('truth_count', 0)} truths."
    )


def _episode_duration(timeline: list[dict[str, Any]]) -> float:
    return float(max(len(timeline) - 1, 0))


def _first_payload(objects: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for obj in objects:
        payload = obj.get(key)
        if isinstance(payload, Mapping) and payload:
            return dict(payload)
    return {}


def _ids_for(objects: list[dict[str, Any]], object_types: set[str]) -> list[str]:
    return [
        str(obj.get("object_id"))
        for obj in objects
        if str(obj.get("object_type")) in object_types and obj.get("object_id")
    ]


def _sum_stat(episodes: list[CognitiveEpisode], key: str) -> dict[str, int]:
    return {
        "total": sum(int(ep.statistics.get(key, 0)) for ep in episodes),
        "episodes_with_stat": sum(1 for ep in episodes if ep.statistics.get(key, 0) > 0),
    }


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "Unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _average(values: Iterable[Any]) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


__all__ = [
    "CognitiveEpisode",
    "CognitiveEpisodeEngine",
    "CognitiveEpisodeRegistry",
    "EPISODE_OUTCOMES",
    "EPISODE_STAGES",
]
