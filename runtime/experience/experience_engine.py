"""Cognitive Experience Engine.

The engine consumes existing runtime reports and emits one complete cognitive
experience for an execution cycle. It does not replace memory, truth, world
model, or DNA; it packages their outputs into an episode that those systems can
reuse.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from runtime.adaptive_reuse.experience_index import ExperienceIndex


DEFAULT_EXPERIENCE_ROOT = Path("runtime/memory/storage/experiences")


@dataclass
class CognitiveExperience:
    experience_id: str
    execution_id: str
    timestamp: str
    task_identity: str
    execution_profile: dict[str, Any] = field(default_factory=dict)
    situation_snapshot: dict[str, Any] = field(default_factory=dict)
    objectives: list[Any] = field(default_factory=list)
    constraints: list[Any] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    semantic_domains: list[str] = field(default_factory=list)
    concepts: list[Any] = field(default_factory=list)
    programs: list[Any] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    truth: list[Any] = field(default_factory=list)
    memory_updates: dict[str, Any] = field(default_factory=dict)
    policies_used: list[Any] = field(default_factory=list)
    decisions_taken: list[Any] = field(default_factory=list)
    search_routes: list[Any] = field(default_factory=list)
    reasoning_graph: dict[str, Any] = field(default_factory=dict)
    knowledge_changes: dict[str, Any] = field(default_factory=dict)
    resources_used: dict[str, Any] = field(default_factory=dict)
    costs: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    success_state: str = "unknown"
    failures: list[dict[str, Any]] = field(default_factory=list)
    recovery_actions: list[Any] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    mental_model_updates: list[dict[str, Any]] = field(default_factory=list)
    dna_updates: dict[str, Any] = field(default_factory=dict)
    world_model_updates: dict[str, Any] = field(default_factory=dict)


class ExperienceEngine:
    """Builds one reusable cognitive experience from existing runtime outputs."""

    system_name = "cognitive_experience_engine"

    def __init__(self, experience_root: str | Path = DEFAULT_EXPERIENCE_ROOT) -> None:
        self.experience_root = Path(experience_root)
        self.index = ExperienceIndex(self.experience_root.parent)

    def build_report(
        self,
        *,
        execution_report: Mapping[str, Any] | None = None,
        reasoning_report: Mapping[str, Any] | None = None,
        search_report: Mapping[str, Any] | None = None,
        concept_report: Mapping[str, Any] | None = None,
        program_report: Mapping[str, Any] | None = None,
        acsc_report: Mapping[str, Any] | None = None,
        evidence_report: Mapping[str, Any] | None = None,
        knowledge_report: Mapping[str, Any] | None = None,
        semantic_report: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        situation_report: Mapping[str, Any] | None = None,
        policy_report: Mapping[str, Any] | None = None,
        decision_report: Mapping[str, Any] | None = None,
        analytics_report: Mapping[str, Any] | None = None,
        governance_report: Mapping[str, Any] | None = None,
        world_model_report: Mapping[str, Any] | None = None,
        dna_report: Mapping[str, Any] | None = None,
        meta_cognition_report: Mapping[str, Any] | None = None,
        task_identity: str | None = None,
        execution_id: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        reports = {
            "execution": _mapping(execution_report),
            "reasoning": _mapping(reasoning_report),
            "search": _mapping(search_report),
            "concept": _mapping(concept_report),
            "program": _mapping(program_report),
            "acsc": _mapping(acsc_report),
            "evidence": _mapping(evidence_report),
            "knowledge": _mapping(knowledge_report),
            "semantic": _mapping(semantic_report) or _mapping(_mapping(knowledge_report).get("SEMANTIC_INTEGRATION_REPORT")),
            "truth": _mapping(truth_report),
            "memory": _mapping(memory_report),
            "situation": _mapping(situation_report),
            "policy": _mapping(policy_report),
            "decision": _mapping(decision_report),
            "analytics": _mapping(analytics_report),
            "governance": _mapping(governance_report),
            "world_model": _mapping(world_model_report),
            "dna": _mapping(dna_report),
            "meta": _mapping(meta_cognition_report),
        }
        identity = task_identity or self._task_identity(reports)
        exec_id = execution_id or self._execution_id(reports, identity)
        experience = self._build_experience(reports, identity, exec_id)
        prior = self._retrieve_similar_experiences(experience)
        graph = self._experience_graph(experience, prior)
        compression = self._experience_compression(experience, prior)
        transfer = self._transfer_learning(experience, prior)
        persistence = self._persist(experience) if persist else {
            "stored": False,
            "reason": "persistence_disabled",
        }
        payload = asdict(experience)
        payload.update(self._indexable_signatures(experience))
        return {
            "system": self.system_name,
            "COGNITIVE_EXPERIENCE_REPORT": True,
            "status": "OPERATIONAL",
            "experience": payload,
            "experience_count": 1,
            "exactly_one_experience_per_execution": True,
            "experience_summary": self._experience_summary(experience),
            "situation_evolution": self._situation_evolution(reports),
            "semantic_abstractions": self._semantic_abstractions(reports),
            "concept_evolution": self._concept_evolution(reports),
            "program_evolution": self._program_evolution(reports),
            "search_experience": self._search_experience(reports),
            "evidence_evolution": self._evidence_evolution(reports),
            "truth_evolution": self._truth_evolution(reports),
            "memory_evolution": self._memory_evolution(reports),
            "policy_usage": self._policy_usage(reports),
            "decision_analysis": self._decision_analysis(reports),
            "failure_analysis": self._failure_analysis(experience),
            "success_analysis": self._success_analysis(experience),
            "lessons_learned": experience.lessons_learned,
            "mental_model_updates": experience.mental_model_updates,
            "dna_updates": experience.dna_updates,
            "world_model_updates": experience.world_model_updates,
            "meta_cognitive_reflection": self._meta_reflection(experience, reports),
            "experience_retrieval": prior,
            "experience_similarity": prior.get("best_similarity", 0.0),
            "experience_compression": compression,
            "experience_graph": graph,
            "transfer_learning_opportunities": transfer,
            "experience_importance": self._importance(experience),
            "experience_reusability_score": self._reusability(experience, prior),
            "storage": persistence,
            "runtime_alignment": {
                "duplicates_memory_runtime": False,
                "duplicates_world_model": False,
                "replaces_truth_runtime": False,
                "executes_cognition": False,
                "integrates_existing_outputs": True,
                "experience_is_universal_container": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def retrieve_similar_experiences(self, runtime_context: Mapping[str, Any], top_k: int = 5) -> dict[str, Any]:
        query = self.index.query_signature(runtime_context)
        ranked = []
        for experience in self.index.load():
            score = _similarity(_experience_tokens(query.as_dict()), _experience_tokens(experience.as_dict()))
            if score > 0:
                ranked.append({"experience": experience.as_dict(), "similarity": score})
        ranked.sort(key=lambda item: item["similarity"], reverse=True)
        return {
            "retrieved": bool(ranked),
            "ranked_experiences": ranked[:top_k],
            "best_similarity": ranked[0]["similarity"] if ranked else 0.0,
        }

    def _build_experience(self, reports: Mapping[str, dict[str, Any]], task_identity: str, execution_id: str) -> CognitiveExperience:
        semantic_domains = self._semantic_domains(reports)
        concepts = _items(reports["concept"], "discovered_concepts", "validated_concepts", "top_concepts")
        programs = _items(reports["program"], "generated_program_objects", "winning_programs", "selected_programs")
        evidence = _items(reports["evidence"], "evidence_objects", "validated_evidence")
        truth = _items(reports["truth"], "truth_candidates", "validated_truths", "truth_commits")
        decisions = _items(reports["decision"], "candidate_decisions", "rejected_alternatives")
        selected_decision = _mapping(reports["decision"].get("selected_decision"))
        if selected_decision:
            decisions.insert(0, selected_decision)
        policies = _items(reports["policy"], "candidate_policies", "rejected_policies")
        selected_policy = _mapping(reports["policy"].get("selected_policy"))
        if selected_policy:
            policies.insert(0, selected_policy)
        failures = self._failure_objects(reports)
        confidence = self._confidence(reports)
        success_state = self._success_state(reports, failures)
        experience = CognitiveExperience(
            experience_id=_id("experience", execution_id, task_identity, semantic_domains, success_state),
            execution_id=execution_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_identity=task_identity,
            execution_profile=self._execution_profile(reports),
            situation_snapshot=self._situation_snapshot(reports),
            objectives=self._objectives(reports),
            constraints=self._constraints(reports),
            context=self._context(reports),
            semantic_domains=semantic_domains,
            concepts=concepts,
            programs=programs,
            evidence=evidence,
            truth=truth,
            memory_updates=self._memory_evolution(reports),
            policies_used=policies,
            decisions_taken=decisions,
            search_routes=self._routes(reports),
            reasoning_graph=self._reasoning_graph(reports),
            knowledge_changes=self._knowledge_changes(reports),
            resources_used=self._resources(reports),
            costs=self._costs(reports),
            confidence=confidence,
            success_state=success_state,
            failures=failures,
            recovery_actions=self._recovery_actions(reports, failures),
            lessons_learned=[],
            recommendations=[],
            mental_model_updates=[],
            dna_updates={},
            world_model_updates={},
        )
        experience.lessons_learned = self._lessons(experience, reports)
        experience.recommendations = self._recommendations(experience, reports)
        experience.mental_model_updates = self._mental_models(experience, reports)
        experience.dna_updates = self._dna_updates(experience, reports)
        experience.world_model_updates = self._world_model_updates(experience, reports)
        return experience

    def _persist(self, experience: CognitiveExperience) -> dict[str, Any]:
        self.experience_root.mkdir(parents=True, exist_ok=True)
        payload = asdict(experience)
        payload.update(self._indexable_signatures(experience))
        path = self.experience_root / f"{_safe_filename(experience.experience_id)}.json"
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        except OSError as error:
            return {"stored": False, "reason": str(error)}
        return {"stored": True, "experience_id": experience.experience_id, "path": str(path)}

    def _retrieve_similar_experiences(self, experience: CognitiveExperience) -> dict[str, Any]:
        query_context = {
            "task_id": experience.task_identity,
            "semantic_summary": " ".join(experience.semantic_domains),
            "context": experience.context,
            "truth_commitments": experience.truth,
            "execution_plan": {"nodes": [{"operation": item} for item in _names(experience.programs)]},
        }
        return self.retrieve_similar_experiences(query_context)

    def _experience_graph(self, experience: CognitiveExperience, retrieval: Mapping[str, Any]) -> dict[str, Any]:
        nodes = [{"id": experience.experience_id, "type": "experience", "success_state": experience.success_state}]
        edges = []
        for item in retrieval.get("ranked_experiences", []):
            prior = _mapping(item.get("experience"))
            prior_id = str(prior.get("experience_id", "unknown_experience"))
            nodes.append({"id": prior_id, "type": "experience", "similarity": item.get("similarity", 0.0)})
            relation = "similar_to"
            if experience.success_state == "success" and _number(prior.get("success_rate")) < 0.5:
                relation = "succeeded_after"
            elif experience.success_state != "success" and _number(prior.get("success_rate")) >= 0.5:
                relation = "failed_after"
            edges.append({"source": experience.experience_id, "target": prior_id, "relation": relation})
        for model in experience.mental_model_updates:
            model_id = str(model.get("mental_model_id"))
            nodes.append({"id": model_id, "type": "mental_model", "domain": model.get("domain")})
            edges.append({"source": experience.experience_id, "target": model_id, "relation": "generalizes"})
        return {
            "nodes": _dedupe_nodes(nodes),
            "edges": _dedupe_edges(edges),
            "node_count": len(_dedupe_nodes(nodes)),
            "edge_count": len(_dedupe_edges(edges)),
        }

    def _experience_compression(self, experience: CognitiveExperience, retrieval: Mapping[str, Any]) -> dict[str, Any]:
        similar = [item for item in retrieval.get("ranked_experiences", []) if _number(item.get("similarity")) >= 0.5]
        return {
            "similar_experiences_found": len(similar),
            "canonical_experience_candidate": bool(similar) and experience.success_state == "success",
            "common_patterns": sorted(set(experience.semantic_domains + _names(experience.mental_model_updates))),
            "redundant_episode_risk": round(min(1.0, len(similar) / 5), 4),
        }

    def _transfer_learning(self, experience: CognitiveExperience, retrieval: Mapping[str, Any]) -> list[dict[str, Any]]:
        opportunities = []
        for domain in experience.semantic_domains:
            opportunities.append({
                "domain": domain,
                "source_experience_id": experience.experience_id,
                "transfer_target": f"{domain} task family",
                "confidence": experience.confidence,
            })
        for item in retrieval.get("ranked_experiences", [])[:3]:
            prior = _mapping(item.get("experience"))
            opportunities.append({
                "domain": prior.get("semantic_signature", "prior_experience"),
                "source_experience_id": prior.get("experience_id"),
                "transfer_target": "similar future execution",
                "confidence": item.get("similarity", 0.0),
            })
        return opportunities

    def _indexable_signatures(self, experience: CognitiveExperience) -> dict[str, Any]:
        concepts = _names(experience.concepts)
        programs = _names(experience.programs)
        truths = _names(experience.truth)
        return {
            "task_signature": _signature(experience.task_identity),
            "semantic_signature": "|".join(sorted(token.lower().replace(" ", "_") for token in experience.semantic_domains)),
            "semantic_summary": " ".join(experience.semantic_domains + _names(experience.mental_model_updates)),
            "semantic_graph": {
                "concept_nodes": [
                    {"concept": name}
                    for name in sorted(set(experience.semantic_domains + _names(experience.concepts)))
                ],
            },
            "concept_signature": "|".join(sorted(concepts)),
            "program_signature": "|".join(sorted(programs)),
            "execution_plan": {
                "nodes": [
                    {"operation": name, "dependencies": experience.semantic_domains}
                    for name in sorted(set(programs + _names(experience.search_routes)))
                ],
            },
            "truth_signature": "|".join(sorted(truths)),
            "truth_commitments": experience.truth,
            "evaluation_result": {"success": experience.success_state == "success", "accuracy": experience.confidence},
            "context_signature": _signature(experience.context),
            "execution_signature": "|".join(sorted(_names(experience.search_routes) + programs)),
            "performance_score": self._reusability(experience, {"best_similarity": 0.0}),
            "success_rate": 1.0 if experience.success_state == "success" else 0.0,
            "execution_cost": _number(experience.costs.get("total_cost", experience.costs.get("execution_time", 0.0))),
            "reasoning_depth": int(_number(experience.execution_profile.get("reasoning_depth", 0))),
        }

    def _task_identity(self, reports: Mapping[str, dict[str, Any]]) -> str:
        for report in reports.values():
            for key in ("task_identity", "task_id", "task", "task_file", "goal", "current_goal"):
                if report.get(key):
                    return str(report[key])
        situation = reports["situation"]
        if situation.get("current_goal"):
            return str(situation["current_goal"])
        return "unknown_task"

    def _execution_id(self, reports: Mapping[str, dict[str, Any]], task_identity: str) -> str:
        for report in reports.values():
            for key in ("execution_id", "run_id", "trace_id"):
                if report.get(key):
                    return str(report[key])
        return _id("execution", task_identity, self._semantic_domains(reports))

    def _semantic_domains(self, reports: Mapping[str, dict[str, Any]]) -> list[str]:
        semantic = reports["semantic"]
        domains = list(semantic.get("discovered_domains", []))
        if not domains:
            domains = list(_mapping(semantic.get("world_governance_integration")).get("resource_priority_by_domain", {}).keys())
        if not domains:
            situation = reports["situation"]
            domains = _list(situation.get("semantic_domains")) or _list(situation.get("domains"))
        if not domains:
            domains = ["General Knowledge"]
        return sorted({str(domain) for domain in domains if domain})

    def _execution_profile(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        execution = reports["execution"]
        governance = reports["governance"]
        profile = _mapping(governance.get("execution_intent")).get("Execution Profile") or _mapping(governance.get("execution_profile"))
        return {
            "profile": profile or execution.get("execution_profile", "standard"),
            "reasoning_depth": reports["reasoning"].get("reasoning_depth", execution.get("reasoning_depth", 0)),
            "confidence_target": _mapping(governance.get("execution_intent")).get("Confidence Target"),
        }

    def _situation_snapshot(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        situation = reports["situation"]
        return {
            "initial_situation": situation.get("initial_situation", situation.get("previous_situation", {})),
            "intermediate_situations": _list(situation.get("intermediate_situations")),
            "final_situation": situation.get("final_situation", situation.get("situation_summary", situation)),
            "situation_stability": situation.get("situation_stability", situation.get("stability", 0.0)),
            "situation_confidence": situation.get("confidence", situation.get("situation_confidence", 0.0)),
            "situation_complexity": situation.get("situation_complexity", situation.get("complexity", 0.0)),
            "situation_outcome": situation.get("situation_outcome", situation.get("outcome", "unknown")),
        }

    def _objectives(self, reports: Mapping[str, dict[str, Any]]) -> list[Any]:
        situation = reports["situation"]
        governance = reports["governance"]
        intent = _mapping(governance.get("execution_intent"))
        return _list(situation.get("objectives")) or _list(intent.get("Expected Outputs")) or [situation.get("current_goal") or intent.get("Goal") or self._task_identity(reports)]

    def _constraints(self, reports: Mapping[str, dict[str, Any]]) -> list[Any]:
        constraints = []
        for report in reports.values():
            constraints.extend(_list(report.get("constraints")))
            constraints.extend(_list(report.get("stopping_conditions")))
        return constraints[:30]

    def _context(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        return {
            "situation": _small(reports["situation"]),
            "governance": _small(reports["governance"]),
            "analytics": _small(reports["analytics"]),
        }

    def _routes(self, reports: Mapping[str, dict[str, Any]]) -> list[Any]:
        search = reports["search"]
        routes = search.get("cognitive_routes", search.get("search_routes", []))
        if isinstance(routes, Mapping):
            return list(routes.values())[:50]
        return _list(routes)[:50]

    def _reasoning_graph(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        return _mapping(reports["reasoning"].get("reasoning_graph")) or _mapping(reports["knowledge"].get("knowledge_graph"))

    def _knowledge_changes(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        knowledge = reports["knowledge"]
        return {
            "knowledge_objects": knowledge.get("knowledge_object_count", len(_list(knowledge.get("knowledge_objects")))),
            "semantic_abstractions": len(_list(_mapping(knowledge.get("SEMANTIC_INTEGRATION_REPORT")).get("canonical_concepts"))),
            "consolidation": knowledge.get("knowledge_consolidation", {}),
            "evolution": knowledge.get("knowledge_evolution", {}),
        }

    def _resources(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        governance = reports["governance"]
        decision = reports["decision"]
        return {
            "runtime_budgets": governance.get("runtime_budgets", governance.get("Runtime Budgets", {})),
            "budget_allocation": reports["policy"].get("budget_allocation", decision.get("budget_allocation", {})),
            "resources": governance.get("resources", {}),
        }

    def _costs(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        analytics = reports["analytics"]
        decision = reports["decision"]
        execution = reports["execution"]
        return {
            "total_cost": _number(analytics.get("execution_cost", execution.get("execution_cost", 0.0))),
            "decision_cost": decision.get("decision_cost", {}),
            "execution_time": execution.get("execution_time", analytics.get("execution_time", 0.0)),
        }

    def _confidence(self, reports: Mapping[str, dict[str, Any]]) -> float:
        values = [
            reports["situation"].get("confidence"),
            reports["situation"].get("situation_confidence"),
            reports["decision"].get("decision_confidence"),
            reports["truth"].get("confidence"),
            reports["analytics"].get("overall_cognitive_intelligence_score"),
            reports["semantic"].get("semantic_confidence"),
        ]
        scores = [_number(value) for value in values if value is not None]
        return round(sum(scores) / max(len(scores), 1), 4)

    def _success_state(self, reports: Mapping[str, dict[str, Any]], failures: list[dict[str, Any]]) -> str:
        for report in reports.values():
            if report.get("success") is True or report.get("exact_match") is True:
                return "success"
            if report.get("success") is False:
                return "failure"
        if failures:
            return "partial_success"
        truth = reports["truth"]
        if _items(truth, "truth_commits", "validated_truths"):
            return "success"
        return "unknown"

    def _failure_objects(self, reports: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
        failures = []
        for name, report in reports.items():
            for key in ("failures", "rejected_decisions", "rejected_policies", "anomalies", "detected_anomalies"):
                for item in _list(report.get(key)):
                    failures.append({"source": name, "failure": item})
            if report.get("success") is False:
                failures.append({"source": name, "failure": "reported_unsuccessful_execution"})
        return failures[:50]

    def _recovery_actions(self, reports: Mapping[str, dict[str, Any]], failures: list[dict[str, Any]]) -> list[Any]:
        actions = []
        for report in reports.values():
            actions.extend(_list(report.get("recovery_actions")))
            actions.extend(_list(report.get("recommended_actions")))
        if failures and not actions:
            actions.append("Preserve failure as reusable experience and prefer alternative policy next time.")
        return actions[:30]

    def _lessons(self, experience: CognitiveExperience, reports: Mapping[str, dict[str, Any]]) -> list[str]:
        lessons = []
        if experience.success_state == "success":
            lessons.append("Successful execution pattern should be reusable for similar future situations.")
        if experience.failures:
            lessons.append("Failure signals should be retained with root context for future prevention.")
        if experience.semantic_domains:
            lessons.append(f"Semantic domains observed: {', '.join(experience.semantic_domains)}.")
        if reports["knowledge"].get("SEMANTIC_INTEGRATION_REPORT"):
            lessons.append("Low-level artifacts were compressed into semantic abstractions before experience storage.")
        if not lessons:
            lessons.append("Experience preserved for future comparison and transfer learning.")
        return lessons

    def _recommendations(self, experience: CognitiveExperience, reports: Mapping[str, dict[str, Any]]) -> list[str]:
        recommendations = []
        recommendations.extend(_list(reports["analytics"].get("recommended_actions")))
        recommendations.extend(_list(reports["semantic"].get("recommendations")))
        if experience.success_state == "success":
            recommendations.append("Promote this episode as a reusable experience candidate.")
        if experience.confidence < 0.55:
            recommendations.append("Collect stronger evidence before using this experience as a canonical mental model.")
        return [str(item) for item in recommendations[:20]]

    def _mental_models(self, experience: CognitiveExperience, reports: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
        models = []
        semantic_names = _names(_list(reports["semantic"].get("canonical_concepts")))
        for domain in experience.semantic_domains:
            model_name = self._mental_model_name(domain, semantic_names)
            models.append({
                "mental_model_id": _id("mental_model", domain, model_name),
                "name": model_name,
                "domain": domain,
                "source_experience_id": experience.experience_id,
                "confidence": experience.confidence,
                "update_type": "strengthen" if experience.success_state == "success" else "calibrate",
                "legacy_experience_signal": True,
                "operational_model_requires_semantic_memory_and_fabric": True,
                "not_a_canonical_mental_model": True,
            })
        return models

    def _mental_model_name(self, domain: str, semantic_names: list[str]) -> str:
        for name in semantic_names:
            if domain.lower().split()[0] in name.lower():
                return name
        mapping = {
            "Geometry": "Spatial Rearrangement",
            "Color Theory": "Color Transformation",
            "Counting": "Counting",
            "Pattern Completion": "Pattern Completion",
            "Graph Reasoning": "Graph Reasoning",
        }
        return mapping.get(domain, f"{domain} Mental Model")

    def _dna_updates(self, experience: CognitiveExperience, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        semantic_traits = _mapping(reports["semantic"].get("dna_integration")).get("semantic_domain_traits", {})
        return {
            "experience_driven_dna": True,
            "source_experience_id": experience.experience_id,
            "traits": semantic_traits or {domain: "reinforce_successful_experience" for domain in experience.semantic_domains},
            "mutation_allowed": experience.success_state == "success" and experience.confidence >= 0.7,
            "temporary_reasoning_excluded": True,
        }

    def _world_model_updates(self, experience: CognitiveExperience, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        return {
            "world_model_stores_experiences": True,
            "source_experience_id": experience.experience_id,
            "experience_domains": experience.semantic_domains,
            "knowledge_reconstructed_from_experience": True,
            "committed_updates": reports["world_model"].get("committed_updates", reports["world_model"]),
        }

    def _experience_summary(self, experience: CognitiveExperience) -> dict[str, Any]:
        return {
            "experience_id": experience.experience_id,
            "task_identity": experience.task_identity,
            "success_state": experience.success_state,
            "semantic_domains": experience.semantic_domains,
            "confidence": experience.confidence,
            "lesson_count": len(experience.lessons_learned),
            "mental_model_count": len(experience.mental_model_updates),
        }

    def _situation_evolution(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        snapshot = self._situation_snapshot(reports)
        return {
            **snapshot,
            "situation_evolution": reports["situation"].get("situation_evolution", {}),
            "situation_history": reports["situation"].get("situation_history", []),
        }

    def _semantic_abstractions(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        semantic = reports["semantic"]
        return {
            "semantic_clusters": semantic.get("semantic_clusters", []),
            "ontology_updates": semantic.get("ontology_growth", {}),
            "canonical_concepts": semantic.get("canonical_concepts", []),
            "semantic_domains": self._semantic_domains(reports),
        }

    def _concept_evolution(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        semantic = reports["semantic"]
        return {
            "generated_concepts": _items(reports["concept"], "discovered_concepts", "validated_concepts", "top_concepts"),
            "abstract_concepts": semantic.get("canonical_concepts", []),
            "semantic_clusters": semantic.get("semantic_clusters", []),
            "ontology_updates": semantic.get("ontology_growth", {}),
            "generalization_score": semantic.get("generalization_quality", 0.0),
        }

    def _program_evolution(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        programs = _items(reports["program"], "generated_program_objects", "winning_programs", "selected_programs")
        return {
            "generated_programs": programs,
            "selected_programs": _items(reports["program"], "winning_programs", "selected_programs"),
            "reusable_programs": [item for item in programs if _number(item.get("generalization_score")) >= 0.5],
            "program_quality": _average(item.get("confidence") for item in programs),
            "program_cost": _average(item.get("complexity") for item in programs),
        }

    def _search_experience(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        return {
            "search_routes": self._routes(reports),
            "search_decisions": reports["search"].get("route_decisions", []),
            "cooling_decisions": reports["acsc"].get("thermal_decisions", reports["acsc"].get("cooling_decisions", [])),
            "search_strategy": reports["search"].get("search_strategy", reports["policy"].get("search_policy", {})),
        }

    def _evidence_evolution(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        evidence = _items(reports["evidence"], "evidence_objects", "validated_evidence")
        return {
            "evidence_generated": evidence,
            "evidence_strength": _average(item.get("confidence") for item in evidence),
            "evidence_reliability": _average(item.get("reliability") for item in evidence),
            "evidence_relationships": reports["evidence"].get("evidence_relationships", []),
        }

    def _truth_evolution(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        candidates = _items(reports["truth"], "truth_candidates")
        committed = _items(reports["truth"], "truth_commits", "validated_truths")
        return {
            "truth_candidates": candidates,
            "truth_promotions": committed,
            "truth_commitments": committed,
            "rejected_truth": _items(reports["truth"], "rejected_truths"),
            "truth_confidence": _average(item.get("confidence") for item in candidates + committed),
        }

    def _memory_evolution(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        memory = reports["memory"]
        knowledge = reports["knowledge"]
        return {
            "memory_promotions": memory.get("memory_promotions", []),
            "memory_retrieval": memory.get("retrieval", knowledge.get("knowledge_reuse", {})),
            "memory_reuse": memory.get("reuse_rate", memory.get("strategy_reuse_rate", 0.0)),
            "memory_compression": memory.get("compression", knowledge.get("knowledge_consolidation", {})),
            "memory_importance": memory.get("importance", 0.0),
        }

    def _policy_usage(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        policy = reports["policy"]
        return {
            "activated_policies": policy.get("activated_policies", policy.get("selected_policy", [])),
            "rejected_policies": policy.get("rejected_policies", []),
            "policy_effectiveness": policy.get("policy_statistics", {}),
            "policy_cost": policy.get("actual_cost", policy.get("expected_cost", 0.0)),
        }

    def _decision_analysis(self, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        decision = reports["decision"]
        return {
            "decision": decision.get("selected_decision", {}),
            "decision_context": decision.get("task_profile", {}),
            "decision_confidence": decision.get("decision_confidence", 0.0),
            "alternative_decisions": decision.get("candidate_decisions", []),
            "rejected_decisions": decision.get("rejected_alternatives", []),
            "decision_outcome": decision.get("actual_outcomes", {}),
            "decision_utility": decision.get("decision_utility", decision.get("selection_score", 0.0)),
        }

    def _failure_analysis(self, experience: CognitiveExperience) -> dict[str, Any]:
        return {
            "failures": experience.failures,
            "failure_count": len(experience.failures),
            "failure_importance": round(min(1.0, len(experience.failures) / 5), 4),
            "future_prevention": experience.recovery_actions,
        }

    def _success_analysis(self, experience: CognitiveExperience) -> dict[str, Any]:
        return {
            "success_pattern": experience.success_state,
            "confidence": experience.confidence,
            "resources_saved": experience.resources_used.get("resources_saved", 0.0),
            "transfer_potential": len(experience.semantic_domains),
            "generalization_potential": self._reusability(experience, {"best_similarity": 0.0}),
        }

    def _meta_reflection(self, experience: CognitiveExperience, reports: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        return {
            "experience_useful": self._importance(experience) >= 0.35,
            "should_be_remembered": True,
            "should_become_mental_model": experience.success_state == "success" and experience.confidence >= 0.6,
            "should_modify_dna": experience.dna_updates.get("mutation_allowed", False),
            "should_update_world_model": True,
            "meta_cognition_source": reports["meta"],
        }

    def _importance(self, experience: CognitiveExperience) -> float:
        score = (
            experience.confidence * 0.35
            + min(1.0, len(experience.semantic_domains) / 4) * 0.2
            + (0.2 if experience.success_state == "success" else 0.05)
            + min(1.0, len(experience.lessons_learned) / 5) * 0.15
            + min(1.0, len(experience.failures) / 3) * 0.1
        )
        return round(min(1.0, score), 4)

    def _reusability(self, experience: CognitiveExperience, retrieval: Mapping[str, Any]) -> float:
        score = (
            experience.confidence * 0.35
            + min(1.0, len(experience.mental_model_updates) / 4) * 0.25
            + (0.2 if experience.success_state == "success" else 0.05)
            + _number(retrieval.get("best_similarity")) * 0.2
        )
        return round(min(1.0, score), 4)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _items(report: Mapping[str, Any], *keys: str) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for key in keys:
        for item in _list(report.get(key)):
            if not isinstance(item, Mapping):
                continue
            marker = json.dumps(_small(item, 12), sort_keys=True, default=str)
            if marker not in seen:
                output.append(dict(item))
                seen.add(marker)
    return output


def _names(items: Any) -> list[str]:
    names = []
    for item in _list(items):
        if isinstance(item, Mapping):
            for key in ("canonical_name", "concept_name", "program_name", "truth_id", "concept_id", "program_id", "id", "name", "mental_model_id"):
                if item.get(key):
                    names.append(str(item[key]))
                    break
        elif item:
            names.append(str(item))
    return names


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _average(values: Any) -> float:
    numbers = [_number(value) for value in values if value is not None]
    return round(sum(numbers) / max(len(numbers), 1), 4)


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


def _signature(value: Any) -> str:
    if not value:
        return ""
    return hashlib.sha1(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _id(prefix: str, *values: Any) -> str:
    digest = hashlib.sha1(json.dumps(values, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _experience_tokens(value: Mapping[str, Any]) -> set[str]:
    text = json.dumps(value, sort_keys=True, default=str).lower().replace("_", " ").replace("-", " ")
    return {token for token in text.split() if len(token) > 2}


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 4)


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {}
    for node in nodes:
        deduped[str(node.get("id"))] = node
    return list(deduped.values())


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge.get("source"), edge.get("target"), edge.get("relation"))
        if marker in seen:
            continue
        output.append(edge)
        seen.add(marker)
    return output


def _safe_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return safe[:120] or "experience"


cognitive_experience_engine = ExperienceEngine()
