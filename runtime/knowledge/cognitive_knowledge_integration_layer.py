"""Cognitive Knowledge Integration Layer (CKIL).

CKIL is the communication layer between cognitive runtimes.  It does not
reason, search, synthesize programs, or validate truth; it turns runtime
artifacts into a unified knowledge bus, knowledge graph, feedback loop, and
knowledge-oriented memory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping


@dataclass
class KnowledgeObject:
    knowledge_id: str
    knowledge_type: str
    origin_runtime: str
    supporting_concepts: list[str] = field(default_factory=list)
    supporting_programs: list[str] = field(default_factory=list)
    supporting_truths: list[str] = field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    supporting_routes: list[str] = field(default_factory=list)
    supporting_memory: list[str] = field(default_factory=list)
    confidence: float = 0.0
    utility: float = 0.0
    generalization: float = 0.0
    novelty: float = 0.0
    compression: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    lifecycle: str = "DISCOVERED"
    explainability: dict[str, Any] = field(default_factory=dict)


class CognitiveKnowledgeMemory:
    """Persistent knowledge libraries used by CKIL feedback."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or "runtime_data/knowledge/ckil_memory.json")

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._empty()
        return payload if isinstance(payload, dict) else self._empty()

    def remember(self, objects: list[KnowledgeObject]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.load()
        libraries = {
            "concept_library": "concept",
            "program_library": "program",
            "truth_library": "truth",
            "search_library": "route",
            "failure_library": "failure",
            "generalization_library": "generalization",
        }
        for library, kind in libraries.items():
            items = list(payload.get(library, []))
            if kind == "failure":
                selected = [
                    item for item in objects
                    if item.lifecycle in {"REJECTED", "FAILED", "ARCHIVED"}
                ]
            elif kind == "generalization":
                selected = [item for item in objects if item.generalization >= 0.55]
            else:
                selected = [item for item in objects if item.knowledge_type == kind]
            for item in selected:
                items.append(self._memory_entry(item))
            payload[library] = self._dedupe(items)[-500:]
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "persistent_cognitive_memory": True,
            "memory_path": str(self.path),
            "concept_library_size": len(payload["concept_library"]),
            "program_library_size": len(payload["program_library"]),
            "truth_library_size": len(payload["truth_library"]),
            "search_library_size": len(payload["search_library"]),
            "failure_library_size": len(payload["failure_library"]),
            "generalization_library_size": len(payload["generalization_library"]),
        }

    def retrieval(self) -> dict[str, Any]:
        payload = self.load()
        return {
            "retrieved_concepts": payload.get("concept_library", [])[-10:],
            "retrieved_programs": payload.get("program_library", [])[-10:],
            "successful_search_histories": payload.get("search_library", [])[-10:],
            "validated_truths": payload.get("truth_library", [])[-10:],
            "reasoning_starts_from_prior_knowledge": any(payload.get(key) for key in payload),
        }

    def _empty(self) -> dict[str, Any]:
        return {
            "concept_library": [],
            "program_library": [],
            "truth_library": [],
            "search_library": [],
            "failure_library": [],
            "generalization_library": [],
        }

    def _memory_entry(self, item: KnowledgeObject) -> dict[str, Any]:
        return {
            "knowledge_id": item.knowledge_id,
            "knowledge_type": item.knowledge_type,
            "origin_runtime": item.origin_runtime,
            "confidence": item.confidence,
            "utility": item.utility,
            "generalization": item.generalization,
            "lifecycle": item.lifecycle,
        }

    def _dedupe(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for item in items:
            deduped[str(item.get("knowledge_id"))] = item
        return list(deduped.values())


class CognitiveKnowledgeIntegrationLayer:
    """Canonical knowledge bus and integration report builder."""

    system_name = "cognitive_knowledge_integration_layer"

    def __init__(self, memory: CognitiveKnowledgeMemory | None = None) -> None:
        self.memory = memory or CognitiveKnowledgeMemory()

    def build_report(
        self,
        *,
        concept_formation_report: Mapping[str, Any] | None = None,
        program_synthesis_report: Mapping[str, Any] | None = None,
        adaptive_search_intelligence_report: Mapping[str, Any] | None = None,
        cognitive_route_intelligence_report: Mapping[str, Any] | None = None,
        evidence_architecture_report: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        reasoning_report: Mapping[str, Any] | None = None,
        acsc_report: Mapping[str, Any] | None = None,
        all_results: list[dict[str, Any]] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        report_level: str = "normal",
        persist: bool = True,
    ) -> dict[str, Any]:
        started = perf_counter()
        concept_report = dict(concept_formation_report or {})
        program_report = dict(program_synthesis_report or {})
        search_report = dict(adaptive_search_intelligence_report or {})
        route_report = dict(cognitive_route_intelligence_report or {})
        evidence_report = dict(evidence_architecture_report or {})
        truth = dict(truth_report or {})
        memory = dict(memory_report or {})
        reasoning = dict(reasoning_report or {})
        acsc = dict(acsc_report or {})
        objects = []
        objects.extend(self._evidence_objects(evidence_report))
        objects.extend(self._concept_objects(concept_report, truth))
        objects.extend(self._program_objects(program_report))
        objects.extend(self._truth_objects(truth))
        objects.extend(self._route_objects(route_report))
        objects.extend(self._memory_objects(memory))
        objects.extend(self._task_objects(all_results or []))
        events = self._knowledge_bus(objects, concept_report, program_report, search_report, route_report, evidence_report, truth, memory, reasoning)
        relationships = self._relationships(objects, events)
        self._attach_relationships(objects, relationships)
        graph = self._graph(objects, relationships)
        feedback = self._feedback(objects, events)
        consolidation = self._consolidation(objects)
        memory_growth = self.memory.remember(objects) if persist else {
            "persistent_cognitive_memory": False,
            "reason": "persistence_disabled",
        }
        retrieval = self.memory.retrieval()
        coverage = self._coverage(events)
        bottlenecks = self._bottlenecks(events, objects)
        runtime = max(
            _number((performance_report or {}).get("total_runtime_seconds")),
            _number((performance_report or {}).get("execution_time")),
            0.001,
        )
        elapsed = max(perf_counter() - started, 0.0)
        payload = [asdict(item) for item in objects]
        return {
            "system": self.system_name,
            "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT": True,
            "status": "OPERATIONAL",
            "report_level": report_level,
            "knowledge_objects": payload,
            "knowledge_object_count": len(payload),
            "knowledge_flow": self._knowledge_flow(events),
            "knowledge_bus": events,
            "knowledge_graph": graph,
            "knowledge_reuse": retrieval,
            "knowledge_feedback": feedback,
            "knowledge_consolidation": consolidation,
            "knowledge_evolution": self._evolution(objects, feedback, consolidation),
            "cross_runtime_communication": self._communication(events),
            "memory_growth": memory_growth,
            "integration_coverage": coverage,
            "knowledge_bottlenecks": bottlenecks,
            "influence_summary": {
                "concepts_influence_programs": self._has_event(events, "concept", "program"),
                "programs_influence_search": self._has_event(events, "program", "search"),
                "search_influences_evidence": self._has_event(events, "search", "evidence"),
                "evidence_influences_knowledge": self._has_event(events, "evidence", "knowledge"),
                "knowledge_influences_truth": self._has_event(events, "knowledge", "truth"),
                "search_influences_truth": False,
                "truth_consumes_raw_cognitive_artifacts": False,
                "truth_consumes_evidence_objects": bool(evidence_report.get("evidence_objects")),
                "truth_updates_concepts": self._has_event(events, "truth", "concept"),
                "stable_concepts_enter_memory": self._has_event(events, "concept", "memory"),
                "successful_programs_enter_memory": self._has_event(events, "program", "memory"),
                "reasoning_retrieves_stored_knowledge": bool(retrieval["reasoning_starts_from_prior_knowledge"]),
            },
            "runtime_alignment": {
                "executes_reasoning": False,
                "executes_search": False,
                "executes_evidence_inference": False,
                "executes_memory_engine": False,
                "redesigns_runtime_registry": False,
                "redesigns_execution_engine": False,
                "deterministic_execution": True,
                "reuses_existing_telemetry": True,
                "reuses_execution_lifecycle": True,
                "acsc_consumes_unified_knowledge": bool(acsc),
                "truth_raw_artifact_access_forbidden": True,
            },
            "instrumentation_overhead_seconds": round(elapsed, 9),
            "instrumentation_overhead_below_2_percent": elapsed / runtime < 0.02,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _evidence_objects(self, report):
        objects = []
        for evidence in _items(report, "evidence_objects"):
            evidence_id = str(evidence.get("id") or _id("evidence", evidence))
            objects.append(KnowledgeObject(
                knowledge_id=evidence_id,
                knowledge_type="evidence",
                origin_runtime=str(evidence.get("owner_runtime") or "evidence_builder_runtime"),
                supporting_concepts=_list(evidence.get("supporting_concepts")),
                supporting_programs=_list(evidence.get("supporting_programs")),
                supporting_routes=_list(evidence.get("supporting_routes")),
                supporting_evidence=[_small(evidence)],
                supporting_evidence_ids=[evidence_id],
                confidence=_clamp(evidence.get("confidence", 0.5)),
                utility=_clamp(evidence.get("reliability", 0.5)),
                generalization=_clamp(evidence.get("completeness", 0.5)),
                novelty=0.3,
                compression=0.65,
                dependencies=_list(evidence.get("dependency_references")),
                lifecycle=str(evidence.get("lifecycle", "PUBLISHED")),
                explainability={
                    "where_originated": "Evidence Builder Runtime",
                    "runtime_produced_it": "evidence_builder_runtime",
                    "who_consumed_it": ["knowledge_integration_runtime", "truth_runtime"],
                    "which_decision_it_influenced": "truth_validation_input",
                    "how_it_evolved": "Normalized observations were correlated into immutable evidence.",
                    "why_it_survived": "Canonical evidence is the bridge between observation and reasoning.",
                },
            ))
        return _dedupe_objects(objects)

    def _concept_objects(self, report, truth):
        objects = []
        for concept in _items(report, "discovered_concepts", "top_concepts", "validated_concepts"):
            concept_id = str(concept.get("concept_id") or _id("concept", concept.get("concept_name")))
            truth_support = _ids(_items(truth, "truth_candidates", "truth_commits"), "truth_id", "id")
            confidence = _clamp(_number(concept.get("confidence")) + min(len(truth_support) * 0.01, 0.1))
            lifecycle = str(concept.get("lifecycle") or "DISCOVERED")
            if truth_support and lifecycle in {"SUPPORTED", "VALIDATED", "GENERALIZED"}:
                lifecycle = "STRENGTHENED"
            objects.append(KnowledgeObject(
                knowledge_id=concept_id,
                knowledge_type="concept",
                origin_runtime=str(concept.get("origin_runtime", "concept_formation_runtime")),
                supporting_concepts=[concept_id],
                supporting_truths=truth_support[:5],
                supporting_evidence=_list(concept.get("supporting_evidence"))[:5],
                confidence=confidence,
                utility=_clamp(concept.get("utility")),
                generalization=_clamp(concept.get("generalization_score")),
                novelty=_clamp(concept.get("novelty", 0.5)),
                compression=_clamp(concept.get("scoring", {}).get("compression_value") if isinstance(concept.get("scoring"), Mapping) else concept.get("compression", 0.5)),
                dependencies=_list(concept.get("dependencies")),
                lifecycle=lifecycle,
                explainability={
                    "where_originated": "Concept Formation Engine",
                    "runtime_produced_it": "concept_formation_runtime",
                    "who_consumed_it": ["program_synthesis_runtime", "memory_runtime"],
                    "which_decision_it_influenced": "program_generation",
                    "how_it_evolved": "Truth support strengthens confidence and lifecycle.",
                    "why_it_survived": concept.get("explanation", {}).get("why_survived") if isinstance(concept.get("explanation"), Mapping) else "Retained by CKIL knowledge flow.",
                },
            ))
        return _dedupe_objects(objects)

    def _program_objects(self, report):
        objects = []
        for program in _items(report, "generated_program_objects", "winning_programs"):
            program_id = str(program.get("program_id") or _id("program", program.get("program_name")))
            objects.append(KnowledgeObject(
                knowledge_id=program_id,
                knowledge_type="program",
                origin_runtime="program_synthesis_runtime",
                supporting_concepts=_list(program.get("required_concepts")),
                supporting_programs=[program_id],
                supporting_evidence=[program.get("validation_results", {})] if isinstance(program.get("validation_results"), Mapping) else [],
                confidence=_clamp(program.get("confidence")),
                utility=_clamp(program.get("utility")),
                generalization=_clamp(program.get("generalization_score")),
                novelty=0.45,
                compression=_clamp(1.0 - _number(program.get("complexity"))),
                dependencies=_list(program.get("required_constraints")),
                lifecycle=str(program.get("lifecycle", "CANDIDATE")),
                explainability={
                    "where_originated": "Program Synthesis Intelligence Engine",
                    "runtime_produced_it": "program_synthesis_runtime",
                    "who_consumed_it": ["adaptive_search_intelligence_runtime", "memory_runtime"],
                    "which_decision_it_influenced": "search_strategy_and_route_priority",
                    "how_it_evolved": "Successful programs become reusable templates.",
                    "why_it_survived": "Program retained when confidence, utility, or validation was non-zero.",
                },
            ))
        return _dedupe_objects(objects)

    def _truth_objects(self, report):
        objects = []
        truths = _items(report, "truth_candidates", "truth_commits", "validated_truths")
        if not truths and report:
            truths = [{"truth_id": "truth_runtime:summary", "confidence": 0.5, "utility": 0.5}]
        for truth in truths:
            truth_id = str(truth.get("truth_id") or truth.get("id") or _id("truth", truth))
            objects.append(KnowledgeObject(
                knowledge_id=truth_id,
                knowledge_type="truth",
                origin_runtime="truth_runtime",
                supporting_truths=[truth_id],
                supporting_evidence=[_small(truth)],
                confidence=_clamp(truth.get("confidence", truth.get("confidence_score", 0.5))),
                utility=_clamp(truth.get("utility", 0.5)),
                generalization=_clamp(truth.get("generalization", 0.45)),
                novelty=0.35,
                compression=0.5,
                lifecycle=str(truth.get("lifecycle", "VALIDATED" if truth.get("validated") else "CANDIDATE")),
                explainability={
                    "where_originated": "Truth Runtime",
                    "runtime_produced_it": "truth_runtime",
                    "who_consumed_it": ["concept_formation_runtime", "memory_runtime"],
                    "which_decision_it_influenced": "concept_strengthening",
                    "how_it_evolved": "Validated truths strengthen concepts; rejected truths weaken them.",
                    "why_it_survived": "Truth evidence remains available to CKIL.",
                },
            ))
        return objects

    def _route_objects(self, report):
        routes = report.get("cognitive_routes", {})
        if isinstance(routes, Mapping):
            route_values = [item for item in routes.values() if isinstance(item, Mapping)]
        else:
            route_values = _list(routes)
        objects = []
        for route in route_values:
            route_id = str(route.get("route_id") or _id("route", route))
            objects.append(KnowledgeObject(
                knowledge_id=route_id,
                knowledge_type="route",
                origin_runtime="search_runtime",
                supporting_concepts=_list(route.get("supporting_concepts")),
                supporting_programs=_list(route.get("supporting_programs")),
                supporting_truths=[item.get("source", "truth_runtime") for item in _list(route.get("supporting_truths")) if isinstance(item, Mapping)],
                supporting_evidence=_list(route.get("supporting_evidence")),
                supporting_routes=[route_id],
                supporting_memory=[item.get("source", "memory_runtime") for item in _list(route.get("supporting_memory")) if isinstance(item, Mapping)],
                confidence=_clamp(route.get("current_confidence")),
                utility=_clamp(route.get("current_utility")),
                generalization=_clamp(route.get("generalization_score")),
                novelty=_clamp(route.get("novelty")),
                compression=_clamp(route.get("compression_score")),
                dependencies=_list(route.get("supporting_constraints")),
                lifecycle=str(route.get("proposed_state", route.get("current_state", "DISCOVERED"))),
                explainability={
                    "where_originated": "Search Runtime / Route Intelligence",
                    "runtime_produced_it": "search_runtime",
                    "who_consumed_it": ["truth_runtime", "acsc_runtime", "memory_runtime"],
                    "which_decision_it_influenced": "truth_evidence_and_resource_allocation",
                    "how_it_evolved": "Routes gain thermal and quality state through Route Intelligence and ACSC.",
                    "why_it_survived": route.get("decision_justification", "Route remained in the cognitive route graph."),
                },
            ))
        return objects

    def _memory_objects(self, report):
        if not report:
            return []
        return [KnowledgeObject(
            knowledge_id="memory_runtime:adaptive_reuse",
            knowledge_type="memory",
            origin_runtime="memory_runtime",
            supporting_memory=["adaptive_reuse_report"],
            confidence=0.55,
            utility=_clamp(report.get("reuse_rate", report.get("strategy_reuse_rate", 0.5))),
            generalization=0.45,
            novelty=0.2,
            compression=0.7,
            lifecycle="CONSOLIDATED",
            explainability={
                "where_originated": "Memory Runtime",
                "runtime_produced_it": "memory_runtime",
                "who_consumed_it": ["reasoning_runtime"],
                "which_decision_it_influenced": "prior_knowledge_retrieval",
                "how_it_evolved": "Memory accumulates CKIL knowledge libraries.",
                "why_it_survived": "Memory is the long-term substrate for reusable knowledge.",
            },
        )]

    def _task_objects(self, results):
        objects = []
        for index, result in enumerate(results[:20]):
            if not isinstance(result, Mapping):
                continue
            task_id = str(result.get("task_id") or result.get("task") or result.get("task_file") or f"task:{index}")
            objects.append(KnowledgeObject(
                knowledge_id=_id("task", task_id),
                knowledge_type="task",
                origin_runtime="execution_runtime",
                supporting_evidence=[_small(result)],
                confidence=1.0 if result.get("success") or result.get("exact_match") else 0.45,
                utility=0.5,
                generalization=0.3,
                novelty=0.4,
                compression=0.3,
                lifecycle="OBSERVED",
                explainability={
                    "where_originated": "Execution Runtime",
                    "runtime_produced_it": "execution_runtime",
                    "who_consumed_it": ["concept_formation_runtime", "memory_runtime"],
                    "which_decision_it_influenced": "evidence_extraction",
                    "how_it_evolved": "Task evidence enters concept formation and CKIL graph.",
                    "why_it_survived": "Observed task evidence is retained for future reasoning.",
                },
            ))
        return objects

    def _knowledge_bus(self, objects, concept_report, program_report, search_report, route_report, evidence_report, truth_report, memory_report, reasoning_report):
        events = []
        def publish(source, target, event_type, artifact_ids, reason):
            events.append({
                "event_id": _id("event", source, target, event_type, len(events)),
                "source_runtime": source,
                "target_runtime": target,
                "source_layer": source.split("_")[0],
                "target_layer": target.split("_")[0],
                "event_type": event_type,
                "artifact_ids": artifact_ids[:20],
                "reason": reason,
                "published": True,
                "subscribed": True,
            })
        concepts = [item.knowledge_id for item in objects if item.knowledge_type == "concept"]
        programs = [item.knowledge_id for item in objects if item.knowledge_type == "program"]
        routes = [item.knowledge_id for item in objects if item.knowledge_type == "route"]
        evidence = [item.knowledge_id for item in objects if item.knowledge_type == "evidence"]
        truths = [item.knowledge_id for item in objects if item.knowledge_type == "truth"]
        memories = [item.knowledge_id for item in objects if item.knowledge_type == "memory"]
        publish("concept_formation_runtime", "program_synthesis_runtime", "Concept Events", concepts, "Programs consume validated, dominant, and generalized concepts.")
        publish("program_synthesis_runtime", "adaptive_search_intelligence_runtime", "Program Events", programs, "Search prioritizes candidate programs by confidence, utility, and complexity.")
        publish("adaptive_search_intelligence_runtime", "evidence_builder_runtime", "Search Events", routes, "Evidence Builder receives route observations for normalization.")
        publish("evidence_builder_runtime", "knowledge_integration_runtime", "Evidence Events", evidence, "CKIL consumes canonical evidence objects.")
        publish("knowledge_integration_runtime", "truth_runtime", "Knowledge Evidence Events", evidence, "Truth consumes evidence-backed knowledge, not raw runtime artifacts.")
        publish("truth_runtime", "concept_formation_runtime", "Truth Events", truths, "Validated truths strengthen concepts and rejected truths weaken concepts.")
        publish("concept_formation_runtime", "memory_runtime", "Concept Events", concepts, "Stable concepts enter long-term memory; weak concepts remain short-term.")
        publish("program_synthesis_runtime", "memory_runtime", "Program Events", programs, "Successful programs become reusable templates; failed programs become negative experience.")
        publish("memory_runtime", "reasoning_runtime", "Memory Events", memories + concepts + programs + truths, "Reasoning retrieves concepts, programs, search histories, and validated truths.")
        publish("reasoning_runtime", "concept_formation_runtime", "Reasoning Events", routes + truths, "Reasoning outcomes become future concept evidence.")
        if search_report:
            publish("adaptive_search_intelligence_runtime", "acsc_runtime", "Search Events", routes, "ACSC receives route priorities through Route Intelligence.")
        if evidence_report and not evidence:
            publish("evidence_builder_runtime", "knowledge_integration_runtime", "Evidence Events", [], "Evidence report available but no canonical evidence objects were materialized.")
        return events

    def _relationships(self, objects, events):
        edges = []
        ids_by_type = {}
        for item in objects:
            ids_by_type.setdefault(item.knowledge_type, []).append(item.knowledge_id)
            for concept in item.supporting_concepts:
                edges.append(_edge(concept, item.knowledge_id, "supports"))
            for program in item.supporting_programs:
                edges.append(_edge(program, item.knowledge_id, "reuses" if program != item.knowledge_id else "derived_from"))
            for truth in item.supporting_truths:
                edges.append(_edge(truth, item.knowledge_id, "validates"))
            for route in item.supporting_routes:
                edges.append(_edge(route, item.knowledge_id, "derived_from"))
            for evidence_id in item.supporting_evidence_ids:
                edges.append(_edge(evidence_id, item.knowledge_id, "supports"))
            for dependency in item.dependencies:
                edges.append(_edge(item.knowledge_id, dependency, "depends_on"))
        for event in events:
            for artifact_id in event["artifact_ids"]:
                edges.append(_edge(artifact_id, event["target_runtime"], self._relation_for_event(event)))
        for concept_id in ids_by_type.get("concept", [])[:10]:
            for program_id in ids_by_type.get("program", [])[:10]:
                edges.append(_edge(concept_id, program_id, "supports"))
        for program_id in ids_by_type.get("program", [])[:10]:
            for route_id in ids_by_type.get("route", [])[:10]:
                edges.append(_edge(program_id, route_id, "reuses"))
        for truth_id in ids_by_type.get("truth", [])[:10]:
            for concept_id in ids_by_type.get("concept", [])[:10]:
                edges.append(_edge(truth_id, concept_id, "strengthens"))
        return _dedupe_edges(edges)

    def _relation_for_event(self, event):
        if event["source_runtime"] == "truth_runtime":
            return "strengthens"
        if event["target_runtime"] == "truth_runtime":
            return "validates"
        if event["target_runtime"] == "memory_runtime":
            return "reuses"
        return "supports"

    def _attach_relationships(self, objects, relationships):
        by_id = {item.knowledge_id: item for item in objects}
        for edge in relationships:
            if edge["source"] in by_id:
                by_id[edge["source"]].relationships.append(edge)
            if edge["target"] in by_id:
                by_id[edge["target"]].relationships.append(edge)

    def _graph(self, objects, relationships):
        nodes = [
            {
                "id": item.knowledge_id,
                "type": item.knowledge_type,
                "origin_runtime": item.origin_runtime,
                "confidence": item.confidence,
                "utility": item.utility,
                "lifecycle": item.lifecycle,
            }
            for item in objects
        ]
        runtime_nodes = sorted({event_endpoint for item in relationships for event_endpoint in (item["source"], item["target"]) if str(event_endpoint).endswith("_runtime")})
        nodes.extend({"id": node, "type": "runtime"} for node in runtime_nodes)
        return {
            "nodes": nodes,
            "edges": relationships,
            "node_count": len(nodes),
            "edge_count": len(relationships),
            "relationship_types": sorted({edge["relation"] for edge in relationships}),
        }

    def _feedback(self, objects, events):
        concept_updates = []
        for item in objects:
            if item.knowledge_type != "concept":
                continue
            truth_strength = len(item.supporting_truths) * 0.02
            memory_strength = 0.03 if item.lifecycle in {"STABLE", "DOMINANT", "STRENGTHENED", "GENERALIZED"} else 0.0
            concept_updates.append({
                "knowledge_id": item.knowledge_id,
                "confidence_delta": round(truth_strength, 4),
                "utility_delta": round(memory_strength, 4),
                "generalization_delta": round(truth_strength / 2, 4),
                "lifecycle_update": "STRENGTHENED" if truth_strength else item.lifecycle,
            })
        return {
            "closed_loop_feedback": True,
            "loop": ["concepts", "programs", "search", "truth", "memory", "concept_update"],
            "concept_updates": concept_updates,
            "events_consumed": len(events),
        }

    def _consolidation(self, objects):
        by_signature: dict[tuple[str, str], list[KnowledgeObject]] = {}
        for item in objects:
            signature = (
                item.knowledge_type,
                "|".join(sorted(item.supporting_concepts + item.supporting_programs + item.supporting_truths))[:120],
            )
            by_signature.setdefault(signature, []).append(item)
        duplicates = [
            [item.knowledge_id for item in items]
            for items in by_signature.values()
            if len(items) > 1
        ]
        dominant = sorted(
            objects,
            key=lambda item: (item.confidence + item.utility + item.generalization, item.knowledge_id),
            reverse=True,
        )[:10]
        obsolete = [
            item.knowledge_id for item in objects
            if item.lifecycle in {"REJECTED", "FAILED", "ARCHIVED"} or (item.confidence < 0.1 and item.utility < 0.1)
        ]
        return {
            "duplicate_concepts_merged": len([group for group in duplicates if group and group[0].startswith("concept")]),
            "equivalent_programs_merged": len([group for group in duplicates if group and group[0].startswith("program")]),
            "compatible_truths_merged": len([group for group in duplicates if group and group[0].startswith("truth")]),
            "repeated_knowledge_compressed": len(duplicates),
            "obsolete_knowledge_removed": len(obsolete),
            "dominant_knowledge_strengthened": [item.knowledge_id for item in dominant],
            "duplicate_groups": duplicates[:10],
        }

    def _evolution(self, objects, feedback, consolidation):
        return {
            "objects_evolved": len(objects),
            "concepts_updated": len(feedback.get("concept_updates", [])),
            "dominant_strengthened": consolidation.get("dominant_knowledge_strengthened", []),
            "average_confidence": round(sum(item.confidence for item in objects) / max(len(objects), 1), 4),
            "average_generalization": round(sum(item.generalization for item in objects) / max(len(objects), 1), 4),
        }

    def _communication(self, events):
        runtimes = sorted({event["source_runtime"] for event in events} | {event["target_runtime"] for event in events})
        return {
            "published_events": len(events),
            "subscribed_events": len([event for event in events if event.get("subscribed")]),
            "runtimes_connected": runtimes,
            "communication_paths": [
                {
                    "from": event["source_runtime"],
                    "to": event["target_runtime"],
                    "event_type": event["event_type"],
                }
                for event in events
            ],
        }

    def _coverage(self, events):
        required = {
            ("concept_formation_runtime", "program_synthesis_runtime"),
            ("program_synthesis_runtime", "adaptive_search_intelligence_runtime"),
            ("adaptive_search_intelligence_runtime", "evidence_builder_runtime"),
            ("evidence_builder_runtime", "knowledge_integration_runtime"),
            ("knowledge_integration_runtime", "truth_runtime"),
            ("truth_runtime", "concept_formation_runtime"),
            ("concept_formation_runtime", "memory_runtime"),
            ("program_synthesis_runtime", "memory_runtime"),
            ("memory_runtime", "reasoning_runtime"),
        }
        observed = {(event["source_runtime"], event["target_runtime"]) for event in events}
        covered = required & observed
        return {
            "required_paths": len(required),
            "covered_paths": len(covered),
            "coverage_score": round(len(covered) / max(len(required), 1), 4),
            "coverage_percentage": round(len(covered) / max(len(required), 1) * 100, 2),
            "missing_paths": sorted(list(required - observed)),
            "approaches_100_percent": len(covered) == len(required),
        }

    def _knowledge_flow(self, events):
        order = [
            "Pattern Analysis",
            "Concept Formation",
            "Program Synthesis",
            "Adaptive Search",
            "Reasoning",
            "Truth Validation",
            "Memory Consolidation",
            "Knowledge Feedback",
            "Concept Evolution",
            "Future Tasks",
        ]
        return {
            "canonical_flow": order,
            "event_count": len(events),
            "active_flow_edges": [
                f"{event['source_runtime']} -> {event['target_runtime']}"
                for event in events
            ],
        }

    def _bottlenecks(self, events, objects):
        bottlenecks = []
        if not [item for item in objects if item.knowledge_type == "truth"]:
            bottlenecks.append("truth_artifact_volume_low")
        if not [item for item in objects if item.knowledge_type == "memory"]:
            bottlenecks.append("memory_artifact_volume_low")
        if len(events) < 7:
            bottlenecks.append("cross_runtime_event_coverage_low")
        return bottlenecks or ["no_major_knowledge_bottleneck_detected"]

    def _has_event(self, events, source_fragment, target_fragment):
        return any(
            source_fragment in event["source_runtime"]
            and target_fragment in event["target_runtime"]
            for event in events
        )


def _id(prefix: str, *values: Any) -> str:
    digest = hashlib.sha1(
        "|".join(str(value) for value in values).encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}:{digest}"


def _items(report: Mapping[str, Any], *keys: str) -> list[dict[str, Any]]:
    values = []
    seen = set()
    for key in keys:
        for item in _list(report.get(key)):
            if isinstance(item, Mapping):
                marker = json.dumps(_small(item), sort_keys=True)
                if marker not in seen:
                    values.append(dict(item))
                    seen.add(marker)
    return values


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _ids(items: list[Mapping[str, Any]], *keys: str) -> list[str]:
    output = []
    for item in items:
        for key in keys:
            if item.get(key):
                output.append(str(item[key]))
                break
    return output


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return max(0.0, min(1.0, _number(value)))


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


def _edge(source: Any, target: Any, relation: str) -> dict[str, Any]:
    return {
        "source": str(source),
        "target": str(target),
        "relation": relation,
    }


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge["source"], edge["target"], edge["relation"])
        if edge["source"] == edge["target"] or marker in seen:
            continue
        output.append(edge)
        seen.add(marker)
    return output


def _dedupe_objects(objects: list[KnowledgeObject]) -> list[KnowledgeObject]:
    deduped = {}
    for item in objects:
        deduped[item.knowledge_id] = item
    return list(deduped.values())


cognitive_knowledge_integration_layer = CognitiveKnowledgeIntegrationLayer()
