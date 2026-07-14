"""Canonical cognitive concept formation engine.

The engine creates reusable cognitive concepts from runtime evidence.  It does
not solve tasks directly and it does not trust pre-existing concept labels as
truth; labels are treated as evidence that must compete with other candidates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


CONCEPT_LIFECYCLE = (
    "DISCOVERED",
    "CANDIDATE",
    "SUPPORTED",
    "VALIDATED",
    "GENERALIZED",
    "REUSED",
    "STABLE",
    "DOMINANT",
    "DEPRECATED",
    "ARCHIVED",
)

RELATION_TYPES = {
    "extends",
    "generalizes",
    "specializes",
    "supports",
    "contradicts",
    "depends_on",
    "causes",
    "derived_from",
    "equivalent_to",
}


@dataclass
class ConceptEvidence:
    evidence_id: str
    source_runtime: str
    signal: str
    payload: dict[str, Any]
    confidence: float = 0.5
    utility: float = 0.5
    truth_support: float = 0.0
    search_support: float = 0.0
    memory_support: float = 0.0


@dataclass
class ConceptRelationship:
    source: str
    target: str
    relation: str
    strength: float
    explanation: str


@dataclass
class CognitiveConcept:
    concept_id: str
    concept_name: str
    concept_type: str
    concept_category: str
    concept_description: str
    concept_signature: str
    origin_runtime: str
    origin_evidence: dict[str, Any]
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    rejected_evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    novelty: float = 0.0
    utility: float = 0.0
    generalization_score: float = 0.0
    complexity: float = 0.0
    search_support: float = 0.0
    truth_support: float = 0.0
    memory_support: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    parent_concepts: list[str] = field(default_factory=list)
    child_concepts: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    creation_timestamp: str = ""
    last_validation: str = ""
    lifecycle: str = "DISCOVERED"
    scoring: dict[str, float] = field(default_factory=dict)
    explanation: dict[str, Any] = field(default_factory=dict)


class CognitiveConceptFormationEngine:
    """Single authority for runtime concept creation."""

    def __init__(self, memory_path: str | Path | None = None):
        self.memory_path = Path(memory_path or "runtime/artifacts/runtime_data/concepts/concept_memory.json")
        self._memory = self._load_memory()

    def build_report(
        self,
        *,
        all_results: list[dict[str, Any]] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        cognitive_pipeline_report: Mapping[str, Any] | None = None,
        cognitive_search_report: Mapping[str, Any] | None = None,
        solver_reasoning_report: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        dependency_report: Mapping[str, Any] | None = None,
        causal_report: Mapping[str, Any] | None = None,
        lifecycle_report: Mapping[str, Any] | None = None,
        report_level: str = "normal",
        persist: bool = True,
    ) -> dict[str, Any]:
        del performance_report
        evidence = self._extract_evidence(
            all_results=all_results or [],
            cognitive_pipeline_report=dict(cognitive_pipeline_report or {}),
            cognitive_search_report=dict(cognitive_search_report or {}),
            solver_reasoning_report=dict(solver_reasoning_report or {}),
            truth_report=dict(truth_report or {}),
            memory_report=dict(memory_report or {}),
            dependency_report=dict(dependency_report or {}),
            causal_report=dict(causal_report or {}),
            lifecycle_report=dict(lifecycle_report or {}),
        )
        candidates = self._candidate_concepts(evidence)
        competition = self._compete(candidates)
        concepts = self._promote(competition["ranked_candidates"])
        generalized = self._generalize(concepts)
        concepts.extend(generalized)
        relationships = self._relationships(concepts)
        graph = self._graph(concepts, relationships)
        memory_report_payload = self._memory_report(concepts, relationships)
        if persist:
            self._persist(concepts, relationships)

        concepts_payload = [asdict(concept) for concept in concepts]
        validated = [
            item for item in concepts_payload
            if item.get("lifecycle") in {"SUPPORTED", "VALIDATED", "GENERALIZED", "STABLE", "DOMINANT"}
        ]
        rejected = competition["rejected_candidates"]
        stats = self._statistics(concepts, evidence, relationships)
        report = {
            "system": "cognitive_concept_formation_engine",
            "CONCEPT_FORMATION_REPORT": True,
            "status": "OPERATIONAL",
            "report_level": report_level,
            "generated_concepts": len(concepts),
            "concept_count": len(concepts),
            "concept_cost": stats["concept_cost"],
            "confidence": stats["average_confidence"],
            "discovered_concepts": concepts_payload,
            "validated_concepts": validated,
            "rejected_concepts": rejected,
            "generalized_concepts": [asdict(item) for item in generalized],
            "concept_graph": graph,
            "concept_competition": competition,
            "concept_evolution": memory_report_payload["concept_evolution"],
            "concept_statistics": stats,
            "top_concepts": sorted(
                concepts_payload,
                key=lambda item: item.get("utility", 0.0) + item.get("confidence", 0.0),
                reverse=True,
            )[:10],
            "emerging_concepts": [
                item for item in concepts_payload
                if item.get("lifecycle") in {"DISCOVERED", "CANDIDATE", "SUPPORTED"}
            ],
            "concept_coverage": stats["coverage"],
            "concept_diversity": stats["diversity"],
            "concept_compression": stats["compression"],
            "concept_memory": memory_report_payload,
            "single_authority": True,
            "authority_scope": [
                "reasoning_runtime",
                "search_runtime",
                "truth_runtime",
                "memory_runtime",
                "dependency_runtime",
                "causal_runtime",
                "execution_runtime",
            ],
        }
        return report

    def _extract_evidence(self, **sources) -> list[ConceptEvidence]:
        evidence: list[ConceptEvidence] = []
        for index, item in enumerate(sources["all_results"]):
            result = item.get("result", item) if isinstance(item, dict) else {}
            if not isinstance(result, dict):
                continue
            task_id = str(item.get("task") or result.get("task_id") or f"task_{index}")
            for hypothesis in self._hypotheses_from_result(result):
                evidence.extend(self._evidence_from_hypothesis(task_id, hypothesis))
            evaluation = self._mapping(result.get("evaluation_result"))
            if evaluation:
                evidence.append(self._evidence(
                    "truth_runtime",
                    "validation_feedback",
                    {"task": task_id, **self._small_mapping(evaluation)},
                    confidence=self._number(evaluation.get("prediction_accuracy"), 0.55),
                    utility=0.7 if evaluation.get("success") else 0.35,
                    truth_support=0.8 if evaluation.get("success") else 0.2,
                ))
            program = self._mapping(result.get("synthesized_program"))
            if program:
                evidence.append(self._evidence(
                    "program_synthesis",
                    "program_structure",
                    {"task": task_id, **self._small_mapping(program)},
                    confidence=0.62,
                    utility=min(1.0, 0.35 + self._number(program.get("step_count"), 1) * 0.1),
                ))

        search_report = sources["cognitive_search_report"]
        for route in self._list(search_report.get("route_ranking")):
            if isinstance(route, dict):
                evidence.append(self._evidence(
                    "search_runtime",
                    "search_route",
                    self._small_mapping(route),
                    confidence=self._number(route.get("current_confidence") or route.get("priority"), 0.5),
                    utility=self._number(route.get("expected_future_value"), 0.55),
                    search_support=0.85,
                ))
        for node in self._list(self._mapping(search_report.get("search_space_graph")).get("nodes")):
            if isinstance(node, dict) and node.get("type") in {"Hypothesis", "Transformation", "Constraint"}:
                evidence.append(self._evidence(
                    "search_runtime",
                    str(node.get("label") or node.get("type")),
                    self._small_mapping(node),
                    confidence=0.55,
                    utility=0.5,
                    search_support=0.7,
                ))

        pipeline = sources["cognitive_pipeline_report"]
        for event in self._list(pipeline.get("stage_timeline")):
            if isinstance(event, dict) and event.get("execution_status") == "completed":
                evidence.append(self._evidence(
                    "reasoning_runtime",
                    str(event.get("stage_id") or "pipeline_stage"),
                    self._small_mapping(event),
                    confidence=0.6,
                    utility=0.55,
                ))

        for runtime, key in [
            ("truth_runtime", "truth_report"),
            ("memory_runtime", "memory_report"),
            ("dependency_runtime", "dependency_report"),
            ("causal_runtime", "causal_report"),
            ("reasoning_runtime", "solver_reasoning_report"),
            ("memory_runtime", "lifecycle_report"),
        ]:
            evidence.extend(self._evidence_from_report(runtime, sources[key]))
        return self._dedupe_evidence(evidence)

    def _candidate_concepts(self, evidence: list[ConceptEvidence]) -> dict[str, dict[str, Any]]:
        candidates: dict[str, dict[str, Any]] = {}
        for item in evidence:
            name = self._concept_name(item)
            candidate = candidates.setdefault(name, {
                "name": name,
                "type": self._concept_type(item.signal, item.payload),
                "category": self._category(item),
                "evidence": [],
                "runtimes": set(),
                "signals": set(),
                "assumptions": 1,
            })
            candidate["evidence"].append(item)
            candidate["runtimes"].add(item.source_runtime)
            candidate["signals"].add(item.signal)
        return candidates

    def _compete(self, candidates: dict[str, dict[str, Any]]) -> dict[str, Any]:
        ranked = []
        rejected = []
        signature_winners: dict[str, dict[str, Any]] = {}
        for candidate in candidates.values():
            score = self._candidate_score(candidate)
            candidate["score"] = score
            signature = self._signature(candidate["name"].split("_")[:2])
            winner = signature_winners.get(signature)
            if winner is None or score["promotion_score"] > winner["score"]["promotion_score"]:
                if winner is not None:
                    rejected.append(self._rejection(winner, "lower_competitive_score"))
                signature_winners[signature] = candidate
            else:
                rejected.append(self._rejection(candidate, "lower_competitive_score"))
        ranked = sorted(
            signature_winners.values(),
            key=lambda item: item["score"]["promotion_score"],
            reverse=True,
        )
        return {
            "candidate_count": len(candidates),
            "ranked_candidates": [
                self._candidate_summary(item) for item in ranked
            ],
            "rejected_candidates": rejected,
            "competition_policy": {
                "prefer_more_evidence": True,
                "prefer_fewer_assumptions": True,
                "prefer_generalization": True,
                "prefer_compression": True,
                "prefer_cross_task_consistency": True,
            },
        }

    def _promote(self, ranked: list[dict[str, Any]]) -> list[CognitiveConcept]:
        concepts = []
        now = self._now()
        for candidate in ranked:
            if candidate["score"]["promotion_score"] < 0.35:
                continue
            evidence = candidate["supporting_evidence"]
            origin = evidence[0] if evidence else {}
            score = candidate["score"]
            lifecycle = self._lifecycle(score, len(evidence))
            concept_id = f"concept:{self._signature(candidate['concept_name'])}"
            concepts.append(CognitiveConcept(
                concept_id=concept_id,
                concept_name=candidate["concept_name"],
                concept_type=candidate["concept_type"],
                concept_category=candidate["concept_category"],
                concept_description=self._description(candidate),
                concept_signature=self._signature({
                    "name": candidate["concept_name"],
                    "signals": candidate["signals"],
                    "runtimes": candidate["origin_runtimes"],
                }),
                origin_runtime=str(origin.get("source_runtime", "unknown")),
                origin_evidence=origin,
                supporting_evidence=evidence,
                rejected_evidence=[],
                confidence=score["confidence_score"],
                novelty=score["novelty_score"],
                utility=score["utility_score"],
                generalization_score=score["generalization_potential"],
                complexity=score["complexity"],
                search_support=score["search_contribution"],
                truth_support=score["truth_contribution"],
                memory_support=score["memory_contribution"],
                dependencies=sorted(candidate["origin_runtimes"]),
                creation_timestamp=now,
                last_validation=now,
                lifecycle=lifecycle,
                scoring=score,
                explanation=self._explanation(candidate, lifecycle),
            ))
        return concepts

    def _generalize(self, concepts: list[CognitiveConcept]) -> list[CognitiveConcept]:
        groups: dict[str, list[CognitiveConcept]] = {}
        for concept in concepts:
            family = self._general_family(concept.concept_name, concept.concept_category)
            groups.setdefault(family, []).append(concept)
        generalized = []
        now = self._now()
        for family, children in sorted(groups.items()):
            if len(children) < 2:
                continue
            concept_id = f"concept:{self._signature('generalized:' + family)}"
            confidence = round(sum(child.confidence for child in children) / len(children), 4)
            utility = round(sum(child.utility for child in children) / len(children), 4)
            generalized.append(CognitiveConcept(
                concept_id=concept_id,
                concept_name=family,
                concept_type="abstract_pattern",
                concept_category=children[0].concept_category,
                concept_description=f"Generalized abstraction formed from {len(children)} related concepts.",
                concept_signature=self._signature([child.concept_signature for child in children]),
                origin_runtime="cognitive_concept_formation_engine",
                origin_evidence={"derived_from": [child.concept_id for child in children]},
                supporting_evidence=[child.origin_evidence for child in children],
                confidence=confidence,
                novelty=0.65,
                utility=utility,
                generalization_score=0.9,
                complexity=0.35,
                search_support=round(sum(child.search_support for child in children) / len(children), 4),
                truth_support=round(sum(child.truth_support for child in children) / len(children), 4),
                memory_support=round(sum(child.memory_support for child in children) / len(children), 4),
                child_concepts=[child.concept_id for child in children],
                related_concepts=[child.concept_id for child in children],
                creation_timestamp=now,
                last_validation=now,
                lifecycle="GENERALIZED",
                scoring={
                    "confidence_score": confidence,
                    "utility_score": utility,
                    "generalization_potential": 0.9,
                    "compression_value": 0.85,
                    "promotion_score": round((confidence + utility + 0.9) / 3, 4),
                },
                explanation={
                    "why_discovered": "Multiple promoted concepts shared evidence family and category.",
                    "why_survived": "Generalization compresses related concepts without contradicting evidence.",
                    "why_became_stable": "Pending reuse across additional tasks.",
                },
            ))
        return generalized

    def _relationships(self, concepts: list[CognitiveConcept]) -> list[ConceptRelationship]:
        by_id = {concept.concept_id: concept for concept in concepts}
        relationships = []
        for concept in concepts:
            for child_id in concept.child_concepts:
                if child_id in by_id:
                    relationships.append(ConceptRelationship(
                        source=concept.concept_id,
                        target=child_id,
                        relation="generalizes",
                        strength=0.9,
                        explanation="Generalized concept was derived from child evidence.",
                    ))
                    by_id[child_id].parent_concepts.append(concept.concept_id)
            for other in concepts:
                if concept.concept_id == other.concept_id:
                    continue
                if concept.concept_category == other.concept_category:
                    concept.related_concepts.append(other.concept_id)
                    relationships.append(ConceptRelationship(
                        source=concept.concept_id,
                        target=other.concept_id,
                        relation="supports",
                        strength=round(min(concept.confidence, other.confidence), 4),
                        explanation="Concepts share category and compatible evidence.",
                    ))
                elif set(concept.dependencies) & set(other.dependencies):
                    relationships.append(ConceptRelationship(
                        source=concept.concept_id,
                        target=other.concept_id,
                        relation="depends_on",
                        strength=0.5,
                        explanation="Concepts depend on overlapping origin runtimes.",
                    ))
        return self._dedupe_relationships(relationships)

    def _graph(
        self,
        concepts: list[CognitiveConcept],
        relationships: list[ConceptRelationship],
    ) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": concept.concept_id,
                    "label": concept.concept_name,
                    "type": concept.concept_type,
                    "category": concept.concept_category,
                    "lifecycle": concept.lifecycle,
                    "confidence": concept.confidence,
                }
                for concept in concepts
            ],
            "edges": [
                asdict(relation)
                for relation in relationships
                if relation.relation in RELATION_TYPES
            ],
            "relationship_types": sorted(RELATION_TYPES),
        }

    def _statistics(
        self,
        concepts: list[CognitiveConcept],
        evidence: list[ConceptEvidence],
        relationships: list[ConceptRelationship],
    ) -> dict[str, Any]:
        categories = {concept.concept_category for concept in concepts}
        runtimes = {
            evidence_item.source_runtime
            for evidence_item in evidence
        }
        average_confidence = self._average(concept.confidence for concept in concepts)
        compression = round(len(evidence) / max(len(concepts), 1), 4)
        return {
            "evidence_count": len(evidence),
            "relationship_count": len(relationships),
            "average_confidence": average_confidence,
            "average_utility": self._average(concept.utility for concept in concepts),
            "average_generalization_score": self._average(
                concept.generalization_score for concept in concepts
            ),
            "coverage": round(len(concepts) / max(len(evidence), 1), 4),
            "diversity": round(len(categories) / max(len(concepts), 1), 4),
            "compression": compression,
            "concept_cost": round(len(evidence) * 0.0002 + len(concepts) * 0.0005, 4),
            "origin_runtime_count": len(runtimes),
            "lifecycle_distribution": self._counts(concept.lifecycle for concept in concepts),
            "category_distribution": self._counts(concept.concept_category for concept in concepts),
        }

    def _memory_report(
        self,
        concepts: list[CognitiveConcept],
        relationships: list[ConceptRelationship],
    ) -> dict[str, Any]:
        previous = self._memory.get("concepts", {})
        reused = [
            concept for concept in concepts
            if concept.concept_id in previous
        ]
        weak = [
            asdict(concept) for concept in concepts
            if concept.confidence < 0.5 or concept.utility < 0.4
        ]
        strongest = sorted(
            [asdict(concept) for concept in concepts],
            key=lambda item: item.get("confidence", 0.0) + item.get("utility", 0.0),
            reverse=True,
        )[:10]
        return {
            "memory_path": str(self.memory_path),
            "most_reused_concepts": sorted(
                previous.values(),
                key=lambda item: item.get("reuse_count", 0),
                reverse=True,
            )[:10],
            "strongest_concepts": strongest,
            "weak_concepts": weak,
            "emerging_concepts": [
                asdict(concept) for concept in concepts
                if concept.lifecycle in {"DISCOVERED", "CANDIDATE", "SUPPORTED"}
            ],
            "failed_concepts": [],
            "concept_evolution": [
                {
                    "concept_id": concept.concept_id,
                    "previous_lifecycle": previous.get(concept.concept_id, {}).get("lifecycle"),
                    "current_lifecycle": concept.lifecycle,
                    "transition_explanation": self._transition_explanation(
                        previous.get(concept.concept_id, {}).get("lifecycle"),
                        concept.lifecycle,
                    ),
                }
                for concept in concepts
            ],
            "concept_history": self._memory.get("history", [])[-20:],
            "concept_reuse": {
                "reused_count": len(reused),
                "new_count": len(concepts) - len(reused),
            },
            "concept_families": self._counts(concept.concept_category for concept in concepts),
            "relationship_count": len(relationships),
        }

    def _persist(
        self,
        concepts: list[CognitiveConcept],
        relationships: list[ConceptRelationship],
    ) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        previous = self._memory.get("concepts", {})
        concepts_payload = {}
        for concept in concepts:
            prior = previous.get(concept.concept_id, {})
            payload = asdict(concept)
            payload["reuse_count"] = int(prior.get("reuse_count", 0)) + 1
            concepts_payload[concept.concept_id] = payload
        history = list(self._memory.get("history", []))[-50:]
        history.append({
            "timestamp": self._now(),
            "generated_concepts": len(concepts),
            "relationship_count": len(relationships),
        })
        self.memory_path.write_text(
            json.dumps({
                "system": "cognitive_concept_memory",
                "concepts": concepts_payload,
                "relationships": [asdict(item) for item in relationships],
                "history": history,
            }, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._memory = self._load_memory()

    def _load_memory(self) -> dict[str, Any]:
        if not self.memory_path.exists():
            return {"concepts": {}, "relationships": [], "history": []}
        try:
            return json.loads(self.memory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"concepts": {}, "relationships": [], "history": []}

    def _evidence_from_hypothesis(
        self,
        task_id: str,
        hypothesis: Mapping[str, Any],
    ) -> list[ConceptEvidence]:
        signal = str(
            hypothesis.get("semantic_class")
            or hypothesis.get("object_centric_transformation")
            or hypothesis.get("type")
            or hypothesis.get("primitive")
            or "hypothesis"
        )
        payload = {"task": task_id, **self._small_mapping(hypothesis)}
        confidence = self._number(hypothesis.get("confidence"), 0.55)
        utility = max(
            self._number(hypothesis.get("explanatory_power"), 0.0),
            self._number(hypothesis.get("residual_reduction"), 0.0),
            self._number(hypothesis.get("execution_score"), 0.0),
            0.45,
        )
        return [
            self._evidence(
                "reasoning_runtime",
                signal,
                payload,
                confidence=confidence,
                utility=utility,
                truth_support=self._number(hypothesis.get("world_model_fit"), 0.0),
                search_support=self._number(hypothesis.get("search_final_score"), 0.0),
            )
        ]

    def _evidence_from_report(
        self,
        runtime: str,
        report: Mapping[str, Any],
    ) -> list[ConceptEvidence]:
        evidence = []
        for key, value in sorted(report.items()):
            if key in {
                "concepts",
                "concept_nodes",
                "validated_concepts",
                "truths",
                "reused_truths",
                "dependencies",
                "dependency_chains",
                "causal_relations",
                "causal_graph",
            }:
                items = value if isinstance(value, list) else []
                for item in items[:20]:
                    if isinstance(item, dict):
                        signal = str(
                            item.get("concept")
                            or item.get("concept_name")
                            or item.get("relation")
                            or item.get("type")
                            or key
                        )
                        evidence.append(self._evidence(
                            runtime,
                            signal,
                            self._small_mapping(item),
                            confidence=self._number(
                                item.get("confidence") or item.get("score"),
                                0.55,
                            ),
                            utility=self._number(item.get("utility"), 0.5),
                            truth_support=0.7 if runtime == "truth_runtime" else 0.0,
                            memory_support=0.7 if runtime == "memory_runtime" else 0.0,
                        ))
            elif key.endswith("_count") and self._number(value, 0.0) > 0:
                evidence.append(self._evidence(
                    runtime,
                    key.replace("_count", ""),
                    {"metric": key, "value": value},
                    confidence=0.52,
                    utility=0.45,
                    memory_support=0.4 if runtime == "memory_runtime" else 0.0,
                ))
        return evidence

    def _hypotheses_from_result(self, result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        hypotheses = []
        for key in ("ranked_hypotheses", "hypotheses"):
            hypotheses.extend(
                item for item in self._list(result.get(key))
                if isinstance(item, dict)
            )
        search_result = self._mapping(result.get("search_result"))
        for path in self._list(search_result.get("paths")):
            if isinstance(path, dict):
                hypotheses.extend(
                    item for item in self._list(path.get("hypotheses"))
                    if isinstance(item, dict)
                )
        winner = result.get("winner_hypothesis")
        if isinstance(winner, dict):
            hypotheses.append(winner)
        return hypotheses

    def _concept_name(self, evidence: ConceptEvidence) -> str:
        signal = evidence.signal.lower().replace(" ", "_").replace("-", "_")
        payload = evidence.payload
        primitive = str(payload.get("primitive") or payload.get("operation") or "")
        if "color" in signal or "color" in primitive:
            return "color_correspondence_pattern"
        if "mirror" in signal or "reflect" in signal:
            return "reflection_symmetry_pattern"
        if "rotate" in signal:
            return "rotation_consistency_pattern"
        if "translate" in signal or "motion" in signal:
            return "spatial_translation_pattern"
        if "object" in signal and ("preserve" in signal or "identity" in signal):
            return "object_identity_preservation_pattern"
        if "shape" in signal or "structural" in signal:
            return "shape_equivalence_pattern"
        if "dependency" in signal:
            return "dependency_structure_pattern"
        if "causal" in signal or "cause" in signal:
            return "causal_support_pattern"
        if "validation" in signal or "truth" in signal:
            return "truth_validated_pattern"
        if "route" in signal or "search" in signal:
            return "search_route_reuse_pattern"
        if "program" in signal:
            return "program_composition_pattern"
        return f"{self._normalize_token(signal)}_pattern"

    def _concept_type(self, signal: str, payload: Mapping[str, Any]) -> str:
        joined = f"{signal} {' '.join(map(str, payload.keys()))}".lower()
        if "color" in joined:
            return "symbolic_correspondence"
        if any(token in joined for token in ("spatial", "translate", "mirror", "rotate", "position")):
            return "spatial_pattern"
        if any(token in joined for token in ("object", "shape", "topology", "structure")):
            return "structural_pattern"
        if "causal" in joined:
            return "causal_pattern"
        if "dependency" in joined:
            return "dependency_pattern"
        if "truth" in joined or "validation" in joined:
            return "validation_pattern"
        if "search" in joined or "route" in joined:
            return "search_pattern"
        return "abstract_pattern"

    def _category(self, evidence: ConceptEvidence) -> str:
        runtime = evidence.source_runtime
        name = self._concept_name(evidence)
        if "color" in name:
            return "attribute_cognition"
        if any(token in name for token in ("spatial", "reflection", "rotation")):
            return "spatial_cognition"
        if any(token in name for token in ("object", "shape")):
            return "structural_cognition"
        if "causal" in name:
            return "causal_cognition"
        if "dependency" in name:
            return "dependency_cognition"
        if runtime == "search_runtime":
            return "search_cognition"
        if runtime == "truth_runtime":
            return "truth_cognition"
        return "general_cognition"

    def _candidate_score(self, candidate: Mapping[str, Any]) -> dict[str, float]:
        evidence = candidate["evidence"]
        confidence = self._average(item.confidence for item in evidence)
        evidence_strength = min(1.0, len(evidence) / 4)
        runtime_diversity = len(candidate["runtimes"]) / 7
        utility = self._average(item.utility for item in evidence)
        search = self._average(item.search_support for item in evidence)
        truth = self._average(item.truth_support for item in evidence)
        memory = self._average(item.memory_support for item in evidence)
        novelty = 0.35 if f"concept:{self._signature(candidate['name'])}" in self._memory.get("concepts", {}) else 0.85
        generalization = min(1.0, 0.35 + runtime_diversity + min(len(candidate["signals"]), 5) * 0.08)
        complexity = round(min(1.0, 0.15 + len(candidate["signals"]) * 0.08), 4)
        compression = round(min(1.0, len(evidence) / max(len(candidate["signals"]), 1) / 3), 4)
        reasoning = round((confidence + utility) / 2, 4)
        stability = round((confidence + evidence_strength + truth + memory) / 4, 4)
        future = round((utility + generalization + novelty) / 3, 4)
        promotion = round(
            (confidence * 0.24)
            + (evidence_strength * 0.18)
            + (utility * 0.16)
            + (generalization * 0.15)
            + (compression * 0.12)
            + (truth * 0.08)
            + (search * 0.04)
            + (memory * 0.03)
            - (complexity * 0.05),
            4,
        )
        return {
            "confidence_score": round(confidence, 4),
            "evidence_strength": round(evidence_strength, 4),
            "novelty_score": round(novelty, 4),
            "utility_score": round(utility, 4),
            "generalization_potential": round(generalization, 4),
            "compression_value": compression,
            "search_contribution": round(search, 4),
            "reasoning_contribution": reasoning,
            "truth_contribution": round(truth, 4),
            "memory_contribution": round(memory, 4),
            "future_reuse_probability": future,
            "concept_stability": stability,
            "complexity": complexity,
            "promotion_score": promotion,
        }

    def _candidate_summary(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        evidence = list(candidate["evidence"])
        return {
            "concept_name": candidate["name"],
            "concept_type": candidate["type"],
            "concept_category": candidate["category"],
            "origin_runtimes": sorted(candidate["runtimes"]),
            "signals": sorted(candidate["signals"]),
            "supporting_evidence": [asdict(item) for item in evidence[:12]],
            "evidence_count": len(evidence),
            "assumption_count": candidate.get("assumptions", 1),
            "score": dict(candidate["score"]),
            "competition_result": "winner",
        }

    def _rejection(self, candidate: Mapping[str, Any], reason: str) -> dict[str, Any]:
        return {
            "concept_name": candidate["name"],
            "reason": reason,
            "score": dict(candidate.get("score", {})),
            "why_rejected": "A competing candidate explained comparable evidence with better promotion score.",
        }

    def _lifecycle(self, score: Mapping[str, float], evidence_count: int) -> str:
        promotion = score.get("promotion_score", 0.0)
        if promotion >= 0.78 and evidence_count >= 4:
            return "STABLE"
        if promotion >= 0.68:
            return "VALIDATED"
        if promotion >= 0.55:
            return "SUPPORTED"
        if promotion >= 0.4:
            return "CANDIDATE"
        return "DISCOVERED"

    def _description(self, candidate: Mapping[str, Any]) -> str:
        return (
            f"Abstract reusable pattern discovered from {candidate['evidence_count']} "
            f"evidence items across {len(candidate['origin_runtimes'])} runtime(s)."
        )

    def _explanation(self, candidate: Mapping[str, Any], lifecycle: str) -> dict[str, Any]:
        score = candidate["score"]
        return {
            "why_discovered": "Runtime evidence produced repeated compatible signals during reasoning.",
            "which_evidence_supports_it": [
                item["evidence_id"] for item in candidate["supporting_evidence"]
            ],
            "why_survived": (
                "Competitive promotion score remained above discovery threshold "
                f"({score['promotion_score']})."
            ),
            "why_replaced_another_concept": None,
            "why_became_stable": (
                "Lifecycle reached stability gates."
                if lifecycle in {"STABLE", "DOMINANT"}
                else "More cross-task validation required before stability."
            ),
            "why_rejected": None,
            "transition": f"DISCOVERED -> {lifecycle}",
        }

    def _transition_explanation(self, previous: str | None, current: str) -> str:
        if not previous:
            return f"New concept entered lifecycle as {current}."
        if previous == current:
            return f"Concept remained {current} after fresh evidence validation."
        return f"Lifecycle transitioned from {previous} to {current} due to updated evidence scoring."

    def _general_family(self, name: str, category: str) -> str:
        if category == "spatial_cognition":
            return "spatial_transformation_abstraction"
        if category == "attribute_cognition":
            return "attribute_correspondence_abstraction"
        if category == "structural_cognition":
            return "structural_equivalence_abstraction"
        if category == "dependency_cognition":
            return "dependency_abstraction"
        if category == "causal_cognition":
            return "causal_abstraction"
        if "truth" in name:
            return "validation_abstraction"
        return f"{category}_abstraction"

    def _evidence(
        self,
        runtime: str,
        signal: str,
        payload: Mapping[str, Any],
        confidence: float = 0.5,
        utility: float = 0.5,
        truth_support: float = 0.0,
        search_support: float = 0.0,
        memory_support: float = 0.0,
    ) -> ConceptEvidence:
        payload = dict(payload)
        signature = self._signature({"runtime": runtime, "signal": signal, "payload": payload})
        return ConceptEvidence(
            evidence_id=f"evidence:{signature}",
            source_runtime=runtime,
            signal=str(signal),
            payload=payload,
            confidence=self._clamp(confidence),
            utility=self._clamp(utility),
            truth_support=self._clamp(truth_support),
            search_support=self._clamp(search_support),
            memory_support=self._clamp(memory_support),
        )

    def _dedupe_evidence(self, evidence: Iterable[ConceptEvidence]) -> list[ConceptEvidence]:
        by_id = {}
        for item in evidence:
            by_id[item.evidence_id] = item
        return [by_id[key] for key in sorted(by_id)]

    def _dedupe_relationships(
        self,
        relationships: Iterable[ConceptRelationship],
    ) -> list[ConceptRelationship]:
        by_key = {}
        for relation in relationships:
            key = (relation.source, relation.target, relation.relation)
            if key not in by_key or relation.strength > by_key[key].strength:
                by_key[key] = relation
        return [by_key[key] for key in sorted(by_key)]

    def _small_mapping(self, value: Mapping[str, Any]) -> dict[str, Any]:
        result = {}
        for key, item in value.items():
            if len(result) >= 12:
                break
            if isinstance(item, (str, int, float, bool)) or item is None:
                result[str(key)] = item
            elif isinstance(item, list):
                result[str(key)] = item[:5]
            elif isinstance(item, dict):
                result[str(key)] = {
                    str(child_key): child_value
                    for child_key, child_value in list(item.items())[:5]
                    if isinstance(child_value, (str, int, float, bool)) or child_value is None
                }
        return result

    def _mapping(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _list(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def _number(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _average(self, values: Iterable[float]) -> float:
        items = [self._number(value, 0.0) for value in values]
        return round(sum(items) / max(len(items), 1), 4)

    def _counts(self, values: Iterable[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for value in values:
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def _signature(self, value: Any) -> str:
        payload = json.dumps(value, sort_keys=True, default=str)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def _normalize_token(self, value: str) -> str:
        cleaned = [
            char if char.isalnum() else "_"
            for char in value.lower()
        ]
        token = "".join(cleaned).strip("_")
        while "__" in token:
            token = token.replace("__", "_")
        return token or "abstract"

    def _clamp(self, value: float) -> float:
        return round(max(0.0, min(1.0, self._number(value, 0.0))), 4)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


concept_formation_engine = CognitiveConceptFormationEngine()


__all__ = [
    "CONCEPT_LIFECYCLE",
    "RELATION_TYPES",
    "ConceptEvidence",
    "ConceptRelationship",
    "CognitiveConcept",
    "CognitiveConceptFormationEngine",
    "concept_formation_engine",
]
