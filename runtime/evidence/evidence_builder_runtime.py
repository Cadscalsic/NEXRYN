"""Evidence Builder Runtime.

This layer normalizes raw cognitive observations into immutable evidence
objects.  It does not infer truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping


EVIDENCE_CATEGORIES = (
    "structural",
    "spatial",
    "transformation",
    "dependency",
    "temporal",
    "behavioral",
    "semantic",
    "search",
    "pattern",
    "conflict",
    "consistency",
    "memory",
    "context",
)


@dataclass(frozen=True)
class NormalizedObservation:
    observation_id: str
    observation_type: str
    source_runtime: str
    source_artifact: str
    artifact_type: str
    execution_id: str | None = None
    task_id: str | None = None
    category: str = "semantic"
    concepts: tuple[str, ...] = ()
    programs: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    confidence: float = 0.5
    reliability: float = 0.5
    completeness: float = 0.5
    timestamp: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceObject:
    id: str
    evidence_type: str
    source_runtime: str
    source_artifact: str
    execution_id: str | None
    task_id: str | None
    observation_type: str
    supporting_concepts: tuple[str, ...] = ()
    supporting_programs: tuple[str, ...] = ()
    supporting_routes: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    confidence: float = 0.5
    reliability: float = 0.5
    completeness: float = 0.5
    timestamp: str = ""
    lifecycle: str = "PUBLISHED"
    lineage: tuple[str, ...] = ()
    owner_runtime: str = "evidence_builder_runtime"
    validation_status: str = "MATERIALIZED"
    immutable: bool = True
    cross_runtime_support: tuple[str, ...] = ()
    normalized_observations: tuple[str, ...] = ()


class EvidenceBuilderRuntime:
    """Materialize canonical evidence objects from runtime observations."""

    system_name = "evidence_builder_runtime"

    def build_report(
        self,
        *,
        concept_formation_report: Mapping[str, Any] | None = None,
        program_synthesis_report: Mapping[str, Any] | None = None,
        adaptive_search_intelligence_report: Mapping[str, Any] | None = None,
        cognitive_route_intelligence_report: Mapping[str, Any] | None = None,
        dependency_report: Mapping[str, Any] | None = None,
        context_report: Mapping[str, Any] | None = None,
        knowledge_report: Mapping[str, Any] | None = None,
        shared_state: Mapping[str, Any] | None = None,
        execution_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        raw_inputs = {
            "concept_formation_runtime": dict(concept_formation_report or {}),
            "program_synthesis_runtime": dict(program_synthesis_report or {}),
            "adaptive_search_intelligence_runtime": dict(adaptive_search_intelligence_report or {}),
            "route_store_runtime": dict(cognitive_route_intelligence_report or {}),
            "dependency_runtime": dict(dependency_report or {}),
            "context_runtime": dict(context_report or {}),
            "knowledge_integration_runtime": dict(knowledge_report or {}),
        }
        observations: list[NormalizedObservation] = []
        for runtime_id, payload in raw_inputs.items():
            observations.extend(
                self._normalize_runtime(
                    runtime_id,
                    payload,
                    execution_id=execution_id,
                    task_id=task_id,
                )
            )
        if isinstance(shared_state, Mapping):
            observations.extend(self._normalize_shared_state(shared_state, execution_id, task_id))

        deduped, duplicate_groups = self._dedupe_observations(observations)
        evidence = self._build_evidence(deduped)
        conflicts = self._conflicts(evidence)
        report = self._report(observations, deduped, evidence, duplicate_groups, conflicts)
        return report

    def _normalize_runtime(
        self,
        runtime_id: str,
        payload: Mapping[str, Any],
        *,
        execution_id: str | None,
        task_id: str | None,
    ) -> list[NormalizedObservation]:
        if not payload:
            return []
        if runtime_id == "concept_formation_runtime":
            return [
                self._observation(
                    "concept",
                    runtime_id,
                    item,
                    category=self._category_for(item, "semantic"),
                    execution_id=execution_id,
                    task_id=task_id,
                )
                for item in _items(payload, "discovered_concepts", "top_concepts", "validated_concepts", "concepts")
            ]
        if runtime_id == "program_synthesis_runtime":
            return [
                self._observation(
                    "program",
                    runtime_id,
                    item,
                    category=self._category_for(item, "transformation"),
                    execution_id=execution_id,
                    task_id=task_id,
                )
                for item in _items(payload, "generated_program_objects", "winning_programs", "programs")
            ]
        if runtime_id in {"adaptive_search_intelligence_runtime", "route_store_runtime"}:
            route_items = _items(payload, "route_ranking", "routes", "search_routes")
            routes = payload.get("cognitive_routes")
            if isinstance(routes, Mapping):
                route_items.extend(dict(item) for item in routes.values() if isinstance(item, Mapping))
            return [
                self._observation(
                    "route",
                    runtime_id,
                    item,
                    category="search",
                    execution_id=execution_id,
                    task_id=task_id,
                )
                for item in route_items
            ]
        if runtime_id == "dependency_runtime":
            dependencies = _items(payload, "dependencies", "dependency_objects", "dependency_edges", "dependency_references")
            graph = payload.get("dependency_graph")
            if isinstance(graph, Mapping):
                dependencies.extend(dict(edge) for edge in _list(graph.get("edges")) if isinstance(edge, Mapping))
            return [
                self._observation(
                    "dependency",
                    runtime_id,
                    item,
                    category="dependency",
                    execution_id=execution_id,
                    task_id=task_id,
                )
                for item in dependencies
            ]
        if runtime_id == "context_runtime":
            contexts = []
            for key, value in payload.items():
                if "context" not in str(key).lower():
                    continue
                if isinstance(value, Mapping):
                    contexts.append({"id": f"context:{key}", "context_type": key, **dict(value)})
                elif isinstance(value, list):
                    contexts.extend(dict(item) for item in value if isinstance(item, Mapping))
            return [
                self._observation(
                    "context",
                    runtime_id,
                    item,
                    category="context",
                    execution_id=execution_id,
                    task_id=task_id,
                )
                for item in contexts
            ]
        if runtime_id == "knowledge_integration_runtime":
            return [
                self._observation(
                    "knowledge",
                    runtime_id,
                    item,
                    category=self._category_for(item, "consistency"),
                    execution_id=execution_id,
                    task_id=task_id,
                )
                for item in _items(payload, "knowledge_objects")
            ]
        return []

    def _normalize_shared_state(
        self,
        shared_state: Mapping[str, Any],
        execution_id: str | None,
        task_id: str | None,
    ) -> list[NormalizedObservation]:
        observations = []
        for store_name, observation_type, category in (
            ("concept_store", "concept", "semantic"),
            ("program_store", "program", "transformation"),
            ("search_routes", "route", "search"),
            ("dependency_graph", "dependency", "dependency"),
            ("context_store", "context", "context"),
            ("knowledge_objects", "knowledge", "consistency"),
        ):
            store = shared_state.get(store_name)
            if not isinstance(store, Mapping):
                continue
            for item in store.values():
                if isinstance(item, Mapping):
                    observations.append(
                        self._observation(
                            observation_type,
                            str(item.get("origin_runtime") or item.get("owner") or store_name),
                            item,
                            category=category,
                            execution_id=execution_id,
                            task_id=task_id,
                        )
                    )
        return observations

    def _observation(
        self,
        observation_type: str,
        runtime_id: str,
        item: Mapping[str, Any],
        *,
        category: str,
        execution_id: str | None,
        task_id: str | None,
    ) -> NormalizedObservation:
        artifact_id = _artifact_id(observation_type, item)
        concepts = tuple(sorted(set(_strings(
            item.get("supporting_concepts"),
            item.get("required_concepts"),
            item.get("concepts"),
            item.get("concept_id"),
            item.get("id") if observation_type == "concept" else None,
        ))))
        programs = tuple(sorted(set(_strings(
            item.get("supporting_programs"),
            item.get("programs"),
            item.get("program_id"),
            item.get("id") if observation_type == "program" else None,
        ))))
        routes = tuple(sorted(set(_strings(
            item.get("supporting_routes"),
            item.get("route_id"),
            item.get("id") if observation_type == "route" else None,
        ))))
        dependencies = tuple(sorted(set(_strings(
            item.get("dependencies"),
            item.get("dependency_references"),
            item.get("required_constraints"),
            item.get("source"),
            item.get("target"),
        ))))
        confidence = _confidence(item)
        timestamp = str(item.get("timestamp") or item.get("observed_at") or datetime.now(timezone.utc).isoformat())
        return NormalizedObservation(
            observation_id=_id("observation", runtime_id, observation_type, artifact_id),
            observation_type=observation_type,
            source_runtime=runtime_id,
            source_artifact=artifact_id,
            artifact_type=observation_type,
            execution_id=str(item.get("execution_id") or execution_id) if item.get("execution_id") or execution_id else None,
            task_id=str(item.get("task_id") or item.get("task") or task_id) if item.get("task_id") or item.get("task") or task_id else None,
            category=category if category in EVIDENCE_CATEGORIES else "semantic",
            concepts=concepts,
            programs=programs,
            routes=routes,
            dependencies=dependencies,
            confidence=confidence,
            reliability=_clamp(item.get("reliability", confidence)),
            completeness=_completeness(item),
            timestamp=timestamp,
            payload=_small(item),
        )

    def _dedupe_observations(
        self,
        observations: list[NormalizedObservation],
    ) -> tuple[list[NormalizedObservation], list[list[str]]]:
        grouped: dict[tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], list[NormalizedObservation]] = {}
        for observation in observations:
            signature = (
                observation.observation_type,
                observation.source_artifact,
                observation.concepts,
                observation.programs,
                observation.routes,
            )
            grouped.setdefault(signature, []).append(observation)
        deduped = []
        duplicate_groups = []
        for items in grouped.values():
            strongest = sorted(
                items,
                key=lambda item: (item.confidence, item.reliability, item.completeness),
                reverse=True,
            )[0]
            deduped.append(strongest)
            if len(items) > 1:
                duplicate_groups.append([item.observation_id for item in items])
        return deduped, duplicate_groups

    def _build_evidence(self, observations: list[NormalizedObservation]) -> list[EvidenceObject]:
        by_subject: dict[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], list[NormalizedObservation]] = {}
        for observation in observations:
            subject = (
                observation.category,
                observation.concepts,
                observation.programs,
                observation.routes,
            )
            by_subject.setdefault(subject, []).append(observation)

        evidence = []
        for (category, concepts, programs, routes), items in by_subject.items():
            runtimes = sorted({item.source_runtime for item in items})
            dependencies = tuple(sorted({dep for item in items for dep in item.dependencies}))
            confidence = _clamp(
                sum(item.confidence for item in items) / max(len(items), 1)
                + min((len(runtimes) - 1) * 0.05, 0.2)
                + min((len(items) - 1) * 0.02, 0.1)
            )
            reliability = _clamp(sum(item.reliability for item in items) / max(len(items), 1))
            completeness = _clamp(sum(item.completeness for item in items) / max(len(items), 1))
            evidence_type = f"{category}_evidence"
            source_artifact = "+".join(item.source_artifact for item in items[:5])
            evidence.append(EvidenceObject(
                id=_id("evidence", evidence_type, concepts, programs, routes, dependencies),
                evidence_type=evidence_type,
                source_runtime="evidence_builder_runtime",
                source_artifact=source_artifact,
                execution_id=items[0].execution_id,
                task_id=items[0].task_id,
                observation_type="+".join(sorted({item.observation_type for item in items})),
                supporting_concepts=concepts,
                supporting_programs=programs,
                supporting_routes=routes,
                dependency_references=dependencies,
                confidence=round(confidence, 4),
                reliability=round(reliability, 4),
                completeness=round(completeness, 4),
                timestamp=datetime.now(timezone.utc).isoformat(),
                lineage=tuple(item.observation_id for item in items),
                cross_runtime_support=tuple(runtimes),
                normalized_observations=tuple(item.observation_id for item in items),
            ))
        return sorted(evidence, key=lambda item: item.id)

    def _report(
        self,
        raw_observations: list[NormalizedObservation],
        normalized_observations: list[NormalizedObservation],
        evidence: list[EvidenceObject],
        duplicate_groups: list[list[str]],
        conflicts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        categories = sorted({item.evidence_type for item in evidence})
        dropped = [
            asdict(item)
            for item in raw_observations
            if item.observation_id not in {obs.observation_id for obs in normalized_observations}
        ]
        evidence_payload = [asdict(item) for item in evidence]
        average_confidence = round(
            sum(item.confidence for item in evidence) / max(len(evidence), 1),
            4,
        )
        return {
            "system": self.system_name,
            "EVIDENCE_ARCHITECTURE_REPORT": True,
            "status": "OPERATIONAL",
            "raw_observations": [asdict(item) for item in raw_observations],
            "raw_observation_count": len(raw_observations),
            "normalized_observations": [asdict(item) for item in normalized_observations],
            "normalized_observation_count": len(normalized_observations),
            "evidence_objects": evidence_payload,
            "evidence_count": len(evidence_payload),
            "evidence_categories": categories,
            "evidence_coverage": {
                "concepts": any(item.supporting_concepts for item in evidence),
                "programs": any(item.supporting_programs for item in evidence),
                "routes": any(item.supporting_routes for item in evidence),
                "dependencies": any(item.dependency_references for item in evidence),
                "coverage_score": round(len(categories) / len(EVIDENCE_CATEGORIES), 4),
            },
            "evidence_confidence": {
                "average_confidence": average_confidence,
                "minimum_confidence": min((item.confidence for item in evidence), default=0.0),
                "maximum_confidence": max((item.confidence for item in evidence), default=0.0),
            },
            "cross_runtime_support": {
                item.id: list(item.cross_runtime_support)
                for item in evidence
                if len(item.cross_runtime_support) > 1
            },
            "evidence_conflicts": conflicts,
            "evidence_completeness": round(
                sum(item.completeness for item in evidence) / max(len(evidence), 1),
                4,
            ),
            "dropped_evidence": dropped,
            "duplicate_evidence": duplicate_groups,
            "evidence_lineage": {
                item.id: list(item.lineage)
                for item in evidence
            },
            "runtime_alignment": {
                "performs_inference": False,
                "materializes_evidence_only": True,
                "truth_consumes_raw_concepts": False,
                "truth_consumes_evidence_objects": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _category_for(self, item: Mapping[str, Any], default: str) -> str:
        text = " ".join(str(value).lower() for value in _small(item).values())
        if "conflict" in text or "contradiction" in text:
            return "conflict"
        if "spatial" in text or "position" in text:
            return "spatial"
        if "pattern" in text:
            return "pattern"
        if "consistent" in text or "validated" in text:
            return "consistency"
        return default

    def _conflicts(self, evidence: list[EvidenceObject]) -> list[dict[str, Any]]:
        conflicts = []
        for item in evidence:
            if item.evidence_type == "conflict_evidence" or item.confidence < 0.35:
                conflicts.append({
                    "evidence_id": item.id,
                    "confidence": item.confidence,
                    "evidence_type": item.evidence_type,
                    "state": "CONFLICT_OBSERVED",
                })
        return conflicts


def _items(report: Mapping[str, Any], *keys: str) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for key in keys:
        value = report.get(key)
        if isinstance(value, Mapping):
            candidates = value.values()
        elif isinstance(value, list):
            candidates = value
        else:
            continue
        for item in candidates:
            if not isinstance(item, Mapping):
                continue
            marker = json.dumps(_small(item), sort_keys=True, default=str)
            if marker not in seen:
                output.append(dict(item))
                seen.add(marker)
    return output


def _artifact_id(prefix: str, item: Mapping[str, Any]) -> str:
    for key in ("id", "knowledge_id", "concept_id", "program_id", "route_id", "truth_id"):
        if item.get(key):
            return str(item[key])
    return _id(prefix, _small(item))


def _confidence(item: Mapping[str, Any]) -> float:
    for key in (
        "confidence",
        "current_confidence",
        "support_score",
        "evidence_score",
        "utility",
        "current_utility",
    ):
        if item.get(key) is not None:
            return _clamp(item.get(key))
    return 0.5


def _completeness(item: Mapping[str, Any]) -> float:
    signals = 0
    for key in (
        "id",
        "concept_id",
        "program_id",
        "route_id",
        "supporting_concepts",
        "supporting_programs",
        "supporting_routes",
        "dependencies",
        "confidence",
        "utility",
    ):
        signals += int(bool(item.get(key)))
    return _clamp(0.2 + signals / 10)


def _strings(*values: Any) -> list[str]:
    output = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, Mapping):
            output.extend(str(item) for item in value.values() if isinstance(item, (str, int, float)))
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                if isinstance(item, Mapping):
                    output.extend(_strings(item.get("id"), item.get("source"), item.get("target")))
                elif item is not None:
                    output.append(str(item))
        else:
            output.append(str(value))
    return [item for item in output if item]


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _small(value: Mapping[str, Any], limit: int = 12) -> dict[str, Any]:
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


def _clamp(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _id(prefix: str, *values: Any) -> str:
    digest = hashlib.sha1(
        json.dumps(values, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}:{digest}"


evidence_builder_runtime = EvidenceBuilderRuntime()
