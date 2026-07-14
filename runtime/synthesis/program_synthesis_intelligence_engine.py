"""Program synthesis intelligence from cognitive concepts.

Programs here are abstract reasoning procedures, not executable code.  The
engine consumes concept formation output and runtime evidence, then creates
ranked reusable program objects for later execution layers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.synthesis.program_confidence_engine import program_confidence_engine


PROGRAM_LIFECYCLE = (
    "DISCOVERED",
    "CANDIDATE",
    "COMPOSED",
    "VALIDATED",
    "PROMOTED",
    "REUSED",
    "GENERALIZED",
    "STABLE",
    "DEPRECATED",
    "ARCHIVED",
)

PROGRAM_RELATIONSHIPS = {
    "extends",
    "composes",
    "generalizes",
    "specializes",
    "reuses",
    "depends_on",
    "validated_by",
    "derived_from",
}


@dataclass
class CognitiveProgram:
    program_id: str
    program_name: str
    program_type: str
    program_signature: str
    goal: str
    input_representation: dict[str, Any]
    output_representation: dict[str, Any]
    required_concepts: list[str]
    required_transformations: list[str]
    required_constraints: list[str]
    execution_strategy: dict[str, Any]
    complexity: float
    confidence: float
    generalization_score: float
    utility: float
    expected_cost: float
    historical_success: float
    failure_history: list[dict[str, Any]]
    creation_runtime: str
    lifecycle: str
    validation_results: dict[str, Any] = field(default_factory=dict)
    explanation: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgramRelationship:
    source: str
    target: str
    relation: str
    strength: float
    explanation: str


class ProgramSynthesisIntelligenceEngine:
    """Create reusable abstract programs from discovered concepts."""

    def __init__(self, memory_path: str | Path | None = None):
        self.memory_path = Path(
            memory_path or "runtime_data/programs/program_memory.json"
        )
        self._memory = self._load_memory()

    def build_report(
        self,
        *,
        concept_formation_report: Mapping[str, Any] | None = None,
        cognitive_search_report: Mapping[str, Any] | None = None,
        solver_reasoning_report: Mapping[str, Any] | None = None,
        dependency_report: Mapping[str, Any] | None = None,
        causal_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        all_results: list[dict[str, Any]] | None = None,
        report_level: str = "normal",
        persist: bool = True,
    ) -> dict[str, Any]:
        concepts = self._concepts(concept_formation_report or {})
        candidates = self._generate_candidates(
            concepts=concepts,
            cognitive_search_report=dict(cognitive_search_report or {}),
            solver_reasoning_report=dict(solver_reasoning_report or {}),
            dependency_report=dict(dependency_report or {}),
            causal_report=dict(causal_report or {}),
            memory_report=dict(memory_report or {}),
            all_results=all_results or [],
        )
        candidates = self._dedupe_candidates(candidates)
        competition = self._compete(candidates)
        programs = self._promote(competition["ranked_candidates"])
        generalized = self._generalize(programs)
        programs.extend(generalized)
        relationships = self._relationships(programs)
        graph = self._graph(programs, relationships)
        memory = self._memory_report(programs, relationships)
        if persist:
            self._persist(programs, relationships)
        payload = [asdict(program) for program in programs]
        confidence_report = program_confidence_engine.build_report(
            payload,
            reuse_history={
                program_id: record.get("reuse_count", 0)
                for program_id, record in self._memory.get("programs", {}).items()
                if isinstance(record, Mapping)
            },
            episode_history=self._memory.get("history", []),
        )
        payload = confidence_report["program_confidence_assessments"]
        confidence_by_id = {
            item["program_id"]: item
            for item in payload
        }
        winners = [
            item for item in payload
            if item.get("lifecycle") in {"VALIDATED", "PROMOTED", "REUSED", "GENERALIZED", "STABLE"}
        ][:10]
        graph = self._apply_confidence_to_graph(graph, confidence_by_id)
        stats = self._statistics(programs, candidates, relationships, concepts)
        stats.update(self._confidence_statistics(confidence_report))
        return {
            "system": "program_synthesis_intelligence_engine",
            "PROGRAM_SYNTHESIS_REPORT": True,
            "status": "OPERATIONAL",
            "report_level": report_level,
            "generated_programs": len(programs),
            "program_candidates": len(candidates),
            "programs_validated": stats["programs_validated"],
            "programs_rejected": len(competition["rejected_programs"]),
            "winning_programs": winners,
            "generated_program_objects": payload,
            "rejected_programs": competition["rejected_programs"],
            "program_graph": graph,
            "program_evolution": memory["program_evolution"],
            "program_statistics": stats,
            "program_confidence": confidence_report,
            "average_program_confidence": confidence_report["average_program_confidence"],
            "highest_program_confidence": confidence_report["highest_program_confidence"],
            "lowest_program_confidence": confidence_report["lowest_program_confidence"],
            "confidence_distribution": confidence_report["confidence_distribution"],
            "validated_program_count": confidence_report["validated_program_count"],
            "low_confidence_program_count": confidence_report["low_confidence_program_count"],
            "high_confidence_program_count": confidence_report["high_confidence_program_count"],
            "program_reuse": memory["program_reuse"],
            "program_generalization": [asdict(program) for program in generalized],
            "program_competition": competition,
            "program_families": memory["program_families"],
            "program_memory": memory,
            "program_ranking": [
                self._candidate_summary(item)
                for item in competition["ranked_candidates"]
            ],
            "program_validation": [
                program.validation_results for program in programs
            ],
            "single_program_authority": True,
            "program_confidence_authority": "program_confidence_engine",
        }

    def _generate_candidates(
        self,
        *,
        concepts: list[dict[str, Any]],
        cognitive_search_report: Mapping[str, Any],
        solver_reasoning_report: Mapping[str, Any],
        dependency_report: Mapping[str, Any],
        causal_report: Mapping[str, Any],
        memory_report: Mapping[str, Any],
        all_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        candidates = []
        by_category: dict[str, list[dict[str, Any]]] = {}
        for concept in concepts:
            by_category.setdefault(
                str(concept.get("concept_category", "general_cognition")),
                [],
            ).append(concept)
        for category, items in sorted(by_category.items()):
            candidates.append(
                self._candidate_from_concepts(
                    name=f"{category}_reasoning_program",
                    program_type="concept_composition",
                    concepts=items[:6],
                    source="concept_graph",
                    goal=f"Apply {category} concepts as a reusable reasoning procedure.",
                )
            )
        top = sorted(
            concepts,
            key=lambda item: (
                self._number(item.get("utility"), 0.0)
                + self._number(item.get("confidence"), 0.0)
            ),
            reverse=True,
        )[:8]
        for concept in top:
            candidates.append(
                self._candidate_from_concepts(
                    name=f"{concept.get('concept_name', 'concept')}_application_program",
                    program_type="single_concept_application",
                    concepts=[concept],
                    source="concept_memory",
                    goal="Operationalize a high-utility concept.",
                )
            )
        routes = self._list(cognitive_search_report.get("route_ranking"))
        for index, route in enumerate(routes[:8]):
            if not isinstance(route, dict):
                continue
            candidates.append(
                self._candidate_from_runtime(
                    name=f"search_route_program_{index}",
                    program_type="search_route_procedure",
                    source="search_runtime",
                    evidence=route,
                    concepts=top[:3],
                )
            )
        for index, program in enumerate(self._historical_programs(all_results, memory_report)[:8]):
            candidates.append(
                self._candidate_from_runtime(
                    name=f"historical_program_reuse_{index}",
                    program_type="memory_reuse_procedure",
                    source="memory_runtime",
                    evidence=program,
                    concepts=top[:4],
                )
            )
        if dependency_report:
            candidates.append(
                self._candidate_from_runtime(
                    name="dependency_constrained_program",
                    program_type="constraint_satisfaction",
                    source="dependency_runtime",
                    evidence=self._small_mapping(dependency_report),
                    concepts=top[:5],
                )
            )
        if causal_report:
            candidates.append(
                self._candidate_from_runtime(
                    name="causal_validation_program",
                    program_type="causal_procedure",
                    source="causal_runtime",
                    evidence=self._small_mapping(causal_report),
                    concepts=top[:5],
                )
            )
        if solver_reasoning_report:
            candidates.append(
                self._candidate_from_runtime(
                    name="reasoning_graph_program",
                    program_type="hierarchical_reasoning",
                    source="reasoning_runtime",
                    evidence=self._small_mapping(solver_reasoning_report),
                    concepts=top[:6],
                )
            )
        return candidates

    def _candidate_from_concepts(
        self,
        *,
        name: str,
        program_type: str,
        concepts: list[dict[str, Any]],
        source: str,
        goal: str,
    ) -> dict[str, Any]:
        return {
            "program_name": self._normalize(name),
            "program_type": program_type,
            "goal": goal,
            "source": source,
            "required_concepts": [self._concept_ref(concept) for concept in concepts],
            "concepts": concepts,
            "required_transformations": self._transformations(concepts),
            "required_constraints": self._constraints(concepts),
            "strategy": self._strategy(program_type, concepts),
            "evidence": {"source": source, "concept_count": len(concepts)},
        }

    def _candidate_from_runtime(
        self,
        *,
        name: str,
        program_type: str,
        source: str,
        evidence: Mapping[str, Any],
        concepts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        candidate = self._candidate_from_concepts(
            name=name,
            program_type=program_type,
            concepts=concepts,
            source=source,
            goal=f"Reuse {source} evidence as an abstract program.",
        )
        candidate["evidence"] = dict(evidence)
        return candidate

    def _compete(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = []
        rejected = []
        for candidate in candidates:
            score = self._score(candidate)
            candidate["score"] = score
            if score["ranking_score"] >= 0.34:
                ranked.append(candidate)
            else:
                rejected.append(self._rejection(candidate, "ranking_score_below_threshold"))
        ranked.sort(
            key=lambda item: (
                item["score"]["ranking_score"],
                item["program_name"],
            ),
            reverse=True,
        )
        winners = []
        seen_goals = set()
        for candidate in ranked:
            goal_key = candidate["program_type"]
            if goal_key in seen_goals and candidate["score"]["ranking_score"] < 0.72:
                rejected.append(self._rejection(candidate, "lower_rank_same_program_type"))
                continue
            seen_goals.add(goal_key)
            winners.append(candidate)
        return {
            "candidate_count": len(candidates),
            "ranked_candidates": winners,
            "ranked_candidate_summaries": [
                self._candidate_summary(item) for item in winners
            ],
            "rejected_programs": rejected,
            "ranking_policy": {
                "evidence_coverage": True,
                "concept_coverage": True,
                "expected_success": True,
                "generalization": True,
                "complexity_penalty": True,
                "execution_cost_penalty": True,
                "reuse_potential": True,
                "compression": True,
            },
        }

    def _promote(self, ranked: list[dict[str, Any]]) -> list[CognitiveProgram]:
        now = self._now()
        programs = []
        for candidate in ranked:
            score = candidate["score"]
            validation = self._validation(candidate, score)
            program_id = f"program:{self._signature(candidate['program_name'])}"
            lifecycle = self._lifecycle(score, program_id)
            programs.append(CognitiveProgram(
                program_id=program_id,
                program_name=candidate["program_name"],
                program_type=candidate["program_type"],
                program_signature=self._signature({
                    "name": candidate["program_name"],
                    "concepts": candidate["required_concepts"],
                    "strategy": candidate["strategy"],
                }),
                goal=candidate["goal"],
                input_representation={
                    "kind": "conceptual_runtime_state",
                    "required_evidence": candidate["required_concepts"],
                },
                output_representation={
                    "kind": "abstract_reasoning_plan",
                    "strategy": candidate["strategy"]["strategy_type"],
                },
                required_concepts=list(candidate["required_concepts"]),
                required_transformations=list(candidate["required_transformations"]),
                required_constraints=list(candidate["required_constraints"]),
                execution_strategy=dict(candidate["strategy"]),
                complexity=score["complexity"],
                confidence=score["expected_success"],
                generalization_score=score["generalization"],
                utility=score["utility"],
                expected_cost=score["expected_cost"],
                historical_success=score["historical_success"],
                failure_history=[] if validation["correctness"] >= 0.35 else [{
                    "reason": "low_correctness_validation",
                    "score": validation["correctness"],
                }],
                creation_runtime="program_synthesis_runtime",
                lifecycle=lifecycle,
                validation_results=validation,
                explanation=self._explanation(candidate, lifecycle, validation),
            ))
        return programs

    def _generalize(self, programs: list[CognitiveProgram]) -> list[CognitiveProgram]:
        groups: dict[str, list[CognitiveProgram]] = {}
        for program in programs:
            family = program.program_type.split("_")[0] + "_program_family"
            groups.setdefault(family, []).append(program)
        generalized = []
        for family, members in sorted(groups.items()):
            if len(members) < 2:
                continue
            confidence = self._average(item.confidence for item in members)
            utility = self._average(item.utility for item in members)
            generalized.append(CognitiveProgram(
                program_id=f"program:{self._signature('generalized:' + family)}",
                program_name=family,
                program_type="generalized_program_family",
                program_signature=self._signature([item.program_signature for item in members]),
                goal=f"General reusable procedure for {family}.",
                input_representation={"kind": "concept_family"},
                output_representation={"kind": "generalized_reasoning_plan"},
                required_concepts=sorted({
                    concept
                    for item in members
                    for concept in item.required_concepts
                }),
                required_transformations=sorted({
                    transformation
                    for item in members
                    for transformation in item.required_transformations
                }),
                required_constraints=sorted({
                    constraint
                    for item in members
                    for constraint in item.required_constraints
                }),
                execution_strategy={
                    "strategy_type": "hierarchical_procedure",
                    "steps": ["select_family_member", "adapt_constraints", "validate_alignment"],
                    "composition": [item.program_id for item in members],
                },
                complexity=self._average(item.complexity for item in members),
                confidence=confidence,
                generalization_score=0.92,
                utility=utility,
                expected_cost=self._average(item.expected_cost for item in members),
                historical_success=self._average(item.historical_success for item in members),
                failure_history=[],
                creation_runtime="program_synthesis_runtime",
                lifecycle="GENERALIZED",
                validation_results={
                    "correctness": confidence,
                    "completeness": 0.82,
                    "constraint_satisfaction": 0.78,
                    "consistency": 0.84,
                    "concept_alignment": 0.9,
                    "truth_alignment": 0.72,
                    "generalization": 0.92,
                    "accepted": True,
                },
                explanation={
                    "why_generated": "Multiple related programs shared type and concept coverage.",
                    "why_selected": "Generalization compresses reusable procedure families.",
                    "which_concepts_compose_it": sorted({
                        concept for item in members for concept in item.required_concepts
                    }),
                    "why_rejected": None,
                    "why_generalized": "Family-level abstraction improves reuse potential.",
                    "why_reused": None,
                },
            ))
        return generalized

    def _relationships(self, programs: list[CognitiveProgram]) -> list[ProgramRelationship]:
        relationships = []
        for program in programs:
            for concept in program.required_concepts:
                relationships.append(ProgramRelationship(
                    source=program.program_id,
                    target=concept,
                    relation="depends_on",
                    strength=0.8,
                    explanation="Program requires concept evidence.",
                ))
            for child in program.execution_strategy.get("composition", []):
                relationships.append(ProgramRelationship(
                    source=program.program_id,
                    target=child,
                    relation="generalizes",
                    strength=0.9,
                    explanation="Program generalizes composed member program.",
                ))
        for left in programs:
            for right in programs:
                if left.program_id == right.program_id:
                    continue
                if set(left.required_concepts) & set(right.required_concepts):
                    relationships.append(ProgramRelationship(
                        source=left.program_id,
                        target=right.program_id,
                        relation="reuses",
                        strength=0.55,
                        explanation="Programs share required concepts.",
                    ))
        return self._dedupe_relationships(relationships)

    def _graph(
        self,
        programs: list[CognitiveProgram],
        relationships: list[ProgramRelationship],
    ) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": program.program_id,
                    "label": program.program_name,
                    "type": "Program",
                    "program_type": program.program_type,
                    "lifecycle": program.lifecycle,
                    "confidence": program.confidence,
                }
                for program in programs
            ],
            "edges": [
                asdict(relation)
                for relation in relationships
                if relation.relation in PROGRAM_RELATIONSHIPS
            ],
            "relationship_types": sorted(PROGRAM_RELATIONSHIPS),
        }

    def _apply_confidence_to_graph(
        self,
        graph: Mapping[str, Any],
        confidence_by_id: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        updated = dict(graph)
        nodes = []
        for node in (graph.get("nodes", []) if isinstance(graph, Mapping) else []):
            if not isinstance(node, Mapping):
                continue
            confidence = confidence_by_id.get(str(node.get("id")), {})
            nodes.append({
                **dict(node),
                "confidence": confidence.get("confidence", node.get("confidence")),
                "confidence_level": confidence.get("confidence_level"),
                "validation_status": confidence.get("validation_status"),
            })
        updated["nodes"] = nodes
        return updated

    def _score(self, candidate: Mapping[str, Any]) -> dict[str, float]:
        concepts = candidate.get("concepts", [])
        concept_count = len(concepts)
        concept_confidence = self._average(
            self._number(item.get("confidence"), 0.5)
            for item in concepts
            if isinstance(item, Mapping)
        )
        concept_utility = self._average(
            self._number(item.get("utility"), 0.5)
            for item in concepts
            if isinstance(item, Mapping)
        )
        generalization = self._average(
            self._number(item.get("generalization_score"), 0.5)
            for item in concepts
            if isinstance(item, Mapping)
        )
        evidence_coverage = min(1.0, concept_count / 4)
        concept_coverage = min(1.0, len(candidate.get("required_concepts", [])) / 5)
        complexity = round(min(1.0, 0.18 + concept_count * 0.08), 4)
        expected_cost = round(0.05 + complexity * 0.25, 4)
        historical = self._historical_success(candidate)
        reuse = 0.75 if historical > 0 else 0.45
        compression = round(evidence_coverage / max(complexity, 0.1), 4)
        expected_success = round(
            (concept_confidence * 0.45)
            + (concept_utility * 0.25)
            + (historical * 0.15)
            + (evidence_coverage * 0.15),
            4,
        )
        ranking = round(
            (evidence_coverage * 0.18)
            + (concept_coverage * 0.18)
            + (expected_success * 0.22)
            + (generalization * 0.16)
            + (reuse * 0.10)
            + (min(compression, 1.0) * 0.10)
            - (complexity * 0.04)
            - (expected_cost * 0.02),
            4,
        )
        return {
            "evidence_coverage": round(evidence_coverage, 4),
            "concept_coverage": round(concept_coverage, 4),
            "expected_success": expected_success,
            "generalization": round(generalization, 4),
            "complexity": complexity,
            "expected_cost": expected_cost,
            "reuse_potential": reuse,
            "compression": min(round(compression, 4), 1.0),
            "utility": round(concept_utility, 4),
            "historical_success": round(historical, 4),
            "ranking_score": ranking,
        }

    def _validation(
        self,
        candidate: Mapping[str, Any],
        score: Mapping[str, float],
    ) -> dict[str, Any]:
        correctness = score["expected_success"]
        completeness = min(1.0, 0.35 + score["concept_coverage"] * 0.5)
        constraints = 0.7 if candidate.get("required_constraints") else 0.5
        consistency = min(1.0, 0.45 + score["evidence_coverage"] * 0.45)
        concept_alignment = score["concept_coverage"]
        truth_alignment = min(1.0, 0.35 + score["historical_success"] * 0.4 + correctness * 0.25)
        generalization = score["generalization"]
        accepted = (
            correctness >= 0.35
            and completeness >= 0.45
            and concept_alignment > 0
        )
        return {
            "program_name": candidate["program_name"],
            "correctness": round(correctness, 4),
            "completeness": round(completeness, 4),
            "constraint_satisfaction": round(constraints, 4),
            "consistency": round(consistency, 4),
            "concept_alignment": round(concept_alignment, 4),
            "truth_alignment": round(truth_alignment, 4),
            "generalization": round(generalization, 4),
            "accepted": accepted,
            "validation_reason": (
                "candidate_program_supported"
                if accepted else "candidate_program_rejected"
            ),
        }

    def _statistics(
        self,
        programs: list[CognitiveProgram],
        candidates: list[dict[str, Any]],
        relationships: list[ProgramRelationship],
        concepts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        validated = [
            program for program in programs
            if program.validation_results.get("accepted")
        ]
        executed = 0
        generalized = [
            program for program in programs
            if program.lifecycle == "GENERALIZED"
        ]
        average_complexity = self._average(program.complexity for program in programs)
        return {
            "programs_generated": len(programs),
            "program_candidates": len(candidates),
            "programs_validated": len(validated),
            "programs_rejected": max(0, len(candidates) - len(validated)),
            "programs_executed": executed,
            "winning_programs": len([
                program for program in programs
                if program.lifecycle in {"VALIDATED", "PROMOTED", "REUSED", "GENERALIZED", "STABLE"}
            ]),
            "reuse_rate": round(len([
                program for program in programs if program.lifecycle == "REUSED"
            ]) / max(len(programs), 1), 4),
            "generalization_rate": round(len(generalized) / max(len(programs), 1), 4),
            "average_complexity": average_complexity,
            "compression_ratio": round(len(concepts) / max(len(programs), 1), 4),
            "concept_coverage": round(
                len({concept for program in programs for concept in program.required_concepts})
                / max(len(concepts), 1),
                4,
            ),
            "relationship_count": len(relationships),
            "lifecycle_distribution": self._counts(program.lifecycle for program in programs),
            "family_distribution": self._counts(program.program_type for program in programs),
        }

    def _confidence_statistics(
        self,
        confidence_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "average_program_confidence": confidence_report.get("average_program_confidence", 0.0),
            "highest_program_confidence": confidence_report.get("highest_program_confidence", 0.0),
            "lowest_program_confidence": confidence_report.get("lowest_program_confidence", 0.0),
            "confidence_distribution": dict(confidence_report.get("confidence_distribution", {})),
            "validated_program_count": confidence_report.get("validated_program_count", 0),
            "low_confidence_program_count": confidence_report.get("low_confidence_program_count", 0),
            "high_confidence_program_count": confidence_report.get("high_confidence_program_count", 0),
        }

    def _memory_report(
        self,
        programs: list[CognitiveProgram],
        relationships: list[ProgramRelationship],
    ) -> dict[str, Any]:
        previous = self._memory.get("programs", {})
        reused = [program for program in programs if program.program_id in previous]
        return {
            "memory_path": str(self.memory_path),
            "winning_programs": [
                asdict(program) for program in programs
                if program.lifecycle in {"VALIDATED", "PROMOTED", "REUSED", "GENERALIZED", "STABLE"}
            ][:10],
            "reusable_programs": [
                asdict(program) for program in programs
                if program.validation_results.get("accepted")
            ],
            "general_programs": [
                asdict(program) for program in programs
                if program.lifecycle == "GENERALIZED"
            ],
            "task_specific_programs": [
                asdict(program) for program in programs
                if program.program_type in {"single_concept_application", "search_route_procedure"}
            ],
            "failed_programs": [
                asdict(program) for program in programs
                if not program.validation_results.get("accepted")
            ],
            "program_families": self._counts(program.program_type for program in programs),
            "program_evolution": [
                {
                    "program_id": program.program_id,
                    "previous_lifecycle": previous.get(program.program_id, {}).get("lifecycle"),
                    "current_lifecycle": program.lifecycle,
                    "transition_explanation": self._transition(
                        previous.get(program.program_id, {}).get("lifecycle"),
                        program.lifecycle,
                    ),
                }
                for program in programs
            ],
            "program_history": self._memory.get("history", [])[-20:],
            "program_reuse": {
                "reused_count": len(reused),
                "new_count": len(programs) - len(reused),
            },
            "relationship_count": len(relationships),
        }

    def _persist(
        self,
        programs: list[CognitiveProgram],
        relationships: list[ProgramRelationship],
    ) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        previous = self._memory.get("programs", {})
        payload = {}
        for program in programs:
            item = asdict(program)
            item["reuse_count"] = int(
                previous.get(program.program_id, {}).get("reuse_count", 0)
            ) + 1
            payload[program.program_id] = item
        history = list(self._memory.get("history", []))[-50:]
        history.append({
            "timestamp": self._now(),
            "generated_programs": len(programs),
            "program_candidates": len(programs),
            "relationship_count": len(relationships),
        })
        self.memory_path.write_text(
            json.dumps({
                "system": "program_synthesis_memory",
                "programs": payload,
                "relationships": [asdict(item) for item in relationships],
                "history": history,
            }, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._memory = self._load_memory()

    def _load_memory(self) -> dict[str, Any]:
        if not self.memory_path.exists():
            return {"programs": {}, "relationships": [], "history": []}
        try:
            return json.loads(self.memory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"programs": {}, "relationships": [], "history": []}

    def _concepts(self, report: Mapping[str, Any]) -> list[dict[str, Any]]:
        items = (
            report.get("discovered_concepts")
            or report.get("generated_program_objects")
            or report.get("top_concepts")
            or []
        )
        return [item for item in items if isinstance(item, dict)]

    def _historical_programs(
        self,
        all_results: list[dict[str, Any]],
        memory_report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        programs = []
        for item in all_results:
            result = item.get("result", item) if isinstance(item, dict) else {}
            if isinstance(result, dict) and isinstance(result.get("synthesized_program"), dict):
                programs.append(result["synthesized_program"])
        for key in ("reused_programs", "programs", "top_reused_assets"):
            for item in self._list(memory_report.get(key)):
                if isinstance(item, dict):
                    programs.append(item)
        return programs

    def _candidate_summary(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "program_name": candidate["program_name"],
            "program_type": candidate["program_type"],
            "goal": candidate["goal"],
            "required_concepts": list(candidate["required_concepts"]),
            "required_transformations": list(candidate["required_transformations"]),
            "required_constraints": list(candidate["required_constraints"]),
            "execution_strategy": dict(candidate["strategy"]),
            "score": dict(candidate["score"]),
        }

    def _rejection(self, candidate: Mapping[str, Any], reason: str) -> dict[str, Any]:
        return {
            "program_name": candidate.get("program_name"),
            "program_type": candidate.get("program_type"),
            "reason": reason,
            "score": dict(candidate.get("score", {})),
            "why_rejected": "Program lost competition or failed validation gates.",
        }

    def _lifecycle(self, score: Mapping[str, float], program_id: str | None = None) -> str:
        if program_id and program_id in self._memory.get("programs", {}):
            return "REUSED"
        if score["ranking_score"] >= 0.78:
            return "PROMOTED"
        if score["ranking_score"] >= 0.64:
            return "VALIDATED"
        if score["ranking_score"] >= 0.5:
            return "COMPOSED"
        return "CANDIDATE"

    def _explanation(
        self,
        candidate: Mapping[str, Any],
        lifecycle: str,
        validation: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "why_generated": "Concept formation produced reusable knowledge that can be operationalized.",
            "why_selected": (
                "Program survived competition with accepted validation."
                if validation.get("accepted") else None
            ),
            "which_concepts_compose_it": list(candidate["required_concepts"]),
            "why_rejected": None if validation.get("accepted") else "Validation gates were not satisfied.",
            "why_generalized": (
                "Program participates in a generalized family."
                if lifecycle == "GENERALIZED" else None
            ),
            "why_reused": (
                "Program signature was found in memory."
                if lifecycle == "REUSED" else None
            ),
        }

    def _strategy(self, program_type: str, concepts: list[dict[str, Any]]) -> dict[str, Any]:
        categories = sorted({
            str(concept.get("concept_category", "general_cognition"))
            for concept in concepts
        })
        steps = []
        if any("spatial" in category for category in categories):
            steps.extend(["match_spatial_pattern", "apply_spatial_constraints"])
        if any("attribute" in category for category in categories):
            steps.extend(["match_attribute_correspondence", "apply_symbolic_mapping"])
        if any("structural" in category for category in categories):
            steps.extend(["detect_objects", "preserve_structural_relations"])
        if not steps:
            steps.extend(["retrieve_concepts", "compose_reasoning_plan"])
        steps.append("validate_against_truth_and_constraints")
        return {
            "strategy_type": program_type,
            "composition_mode": "modular_concept_chain",
            "steps": self._unique(steps),
            "supports": [
                "pattern_matching",
                "constraint_satisfaction",
                "hierarchical_procedures",
                "conditional_logic",
            ],
        }

    def _transformations(self, concepts: list[dict[str, Any]]) -> list[str]:
        transformations = []
        for concept in concepts:
            name = str(concept.get("concept_name", "")).lower()
            category = str(concept.get("concept_category", "")).lower()
            if "color" in name or "attribute" in category:
                transformations.append("symbolic_attribute_mapping")
            if "spatial" in name or "spatial" in category:
                transformations.append("spatial_relation_transform")
            if "object" in name or "shape" in name or "structural" in category:
                transformations.append("object_structure_operation")
            if "causal" in name or "causal" in category:
                transformations.append("causal_validation_step")
            if "dependency" in name or "dependency" in category:
                transformations.append("dependency_constraint_step")
        return self._unique(transformations or ["conceptual_reasoning_step"])

    def _constraints(self, concepts: list[dict[str, Any]]) -> list[str]:
        constraints = []
        for concept in concepts:
            lifecycle = concept.get("lifecycle")
            if lifecycle:
                constraints.append(f"concept_lifecycle:{lifecycle}")
            if concept.get("truth_support", 0):
                constraints.append("truth_alignment_required")
            if concept.get("search_support", 0):
                constraints.append("search_support_required")
        return self._unique(constraints or ["concept_alignment_required"])

    def _historical_success(self, candidate: Mapping[str, Any]) -> float:
        program_id = f"program:{self._signature(candidate['program_name'])}"
        prior = self._memory.get("programs", {}).get(program_id, {})
        if not prior:
            return 0.0
        return self._number(prior.get("historical_success"), 0.0)

    def _transition(self, previous: str | None, current: str) -> str:
        if not previous:
            return f"New program entered lifecycle as {current}."
        if previous == current:
            return f"Program remained {current} after validation."
        return f"Program transitioned from {previous} to {current}."

    def _dedupe_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_signature = {}
        for candidate in candidates:
            signature = self._signature({
                "name": candidate["program_name"],
                "concepts": candidate["required_concepts"],
                "type": candidate["program_type"],
            })
            by_signature[signature] = candidate
        return [by_signature[key] for key in sorted(by_signature)]

    def _dedupe_relationships(
        self,
        relationships: Iterable[ProgramRelationship],
    ) -> list[ProgramRelationship]:
        by_key = {}
        for relation in relationships:
            key = (relation.source, relation.target, relation.relation)
            if key not in by_key or relation.strength > by_key[key].strength:
                by_key[key] = relation
        return [by_key[key] for key in sorted(by_key)]

    def _concept_ref(self, concept: Mapping[str, Any]) -> str:
        return str(
            concept.get("concept_id")
            or concept.get("concept_name")
            or concept.get("concept")
            or "unknown_concept"
        )

    def _small_mapping(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return {
            str(key): item
            for key, item in list(value.items())[:12]
            if isinstance(item, (str, int, float, bool, list, dict)) or item is None
        }

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

    def _unique(self, values: Iterable[str]) -> list[str]:
        return sorted({str(value) for value in values if value})

    def _normalize(self, value: str) -> str:
        token = "".join(
            char if char.isalnum() else "_"
            for char in value.lower()
        ).strip("_")
        while "__" in token:
            token = token.replace("__", "_")
        return token or "program"

    def _signature(self, value: Any) -> str:
        payload = json.dumps(value, sort_keys=True, default=str)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


program_synthesis_intelligence_engine = ProgramSynthesisIntelligenceEngine()


__all__ = [
    "PROGRAM_LIFECYCLE",
    "PROGRAM_RELATIONSHIPS",
    "CognitiveProgram",
    "ProgramRelationship",
    "ProgramSynthesisIntelligenceEngine",
    "program_synthesis_intelligence_engine",
]
