"""Canonical lifecycle representation for semantic concepts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from runtime.semantic.executable_semantics import EXECUTABLE_SEMANTICS
except Exception:  # pragma: no cover - keeps lifecycle importable during partial boot.
    EXECUTABLE_SEMANTICS = {}


SEMANTIC_CLUSTER_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Physics", ("gravity", "falling", "support", "collision", "rest_state")),
    ("Topology", ("topology", "topological", "hole")),
    ("Connectivity", ("connectivity", "connection", "component", "bridge")),
    ("Spatial", ("spatial", "relative_position", "position")),
    ("Motion", ("motion", "directional", "translation", "falling")),
    ("Color", ("color", "recolor")),
    ("Geometry", ("rotation", "reflection", "orientation", "scaling", "symmetry")),
    ("Growth", ("growth", "density", "propagation")),
    ("Transformation", ("transformation", "remapping", "mapping")),
    ("Temporal", ("temporal", "sequence", "time")),
    ("Object Identity", ("identity", "object")),
    ("Pattern Completion", ("path", "completion", "repair")),
    ("Reasoning", ("reasoning", "inference", "hypothesis")),
    ("Dependency", ("dependency", "causal")),
    ("Context", ("context", "semantic_context")),
)

MENTAL_MODEL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Gravity Simulation", ("gravity", "falling", "support", "collision", "rest_state")),
    ("Topology Mental Model", ("topology", "topological", "component", "connectivity", "bridge", "hole")),
    ("Object Transformation Mental Model", ("transformation", "rotation", "reflection", "scaling", "remapping")),
    ("Spatial Reasoning Mental Model", ("spatial", "relative_position", "position", "directional", "motion")),
    ("Color Mapping Mental Model", ("color", "symbolic", "mapping", "remapping")),
)

EXECUTION_PACKAGE_SUPPORT = {
    "rotation": "TRUE",
    "orientation_change": "TRUE",
    "reflection": "TRUE",
    "rotation_reflection": "TRUE",
    "path_finding": "TRUE",
    "path_construction": "TRUE",
    "route_completion": "TRUE",
    "gravity": "FALSE",
    "falling": "FALSE",
    "support": "FALSE",
    "collision": "FALSE",
    "rest_state": "FALSE",
    "component_splitting": "FALSE",
    "bridge_creation": "FALSE",
}

PROGRAM_REJECTION_NO_EXECUTION_PACKAGE = "NO_EXECUTION_PACKAGE"
PROGRAM_REJECTION_NO_COMPILER_SUPPORT = "NO_COMPILER_SUPPORT"
PROGRAM_REJECTION_NO_EXECUTABLE_MAPPING = "NO_EXECUTABLE_MAPPING"


@dataclass
class ConceptLifecycle:
    concept_id: str
    concept_name: str
    discovery_source: str = "Not Available"
    semantic_cluster: str = "Context"
    mental_model: str = "Not Available"
    truth_candidate_state: str = "FALSE"
    truth_state: str = "UNVERIFIED"
    executable_supported: str = "FALSE"
    execution_package_available: str = "UNKNOWN"
    compiler_supported: str = "FALSE"
    compiler_attempted: str = "FALSE"
    compiler_result: str = "NOT_ATTEMPTED"
    program_generation_attempted: str = "FALSE"
    program_generated: str = "FALSE"
    program_rejected: str = "FALSE"
    program_rejection_reason: str = "Not Available"
    candidate_generated: str = "FALSE"
    candidate_entered_arena: str = "FALSE"
    candidate_selected: str = "FALSE"
    candidate_rejected: str = "FALSE"
    candidate_rejection_reason: str = "Not Available"
    execution_attempted: str = "FALSE"
    execution_success: str = "FALSE"
    prediction_contribution: str = "NONE"
    semantic_memory_integrated: str = "FALSE"
    memory_entry_id: str | None = None
    memory_version: str | None = None
    memory_source: str | None = None
    accepted_by: list[str] = field(default_factory=list)
    rejected_by: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    lifecycle_status: str = "DISCOVERED"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class UnifiedConceptLifecycleBuilder:
    """Build lifecycle rows by reconciling existing cognitive reports."""

    system_name = "unified_concept_lifecycle"

    def build(
        self,
        report_state: Mapping[str, Any] | None,
        performance: Mapping[str, Any] | None = None,
        *,
        max_concepts: int | None = 128,
        include_rows: bool = True,
        max_nodes: int = 20_000,
        max_depth: int = 8,
        max_list_items: int = 200,
    ) -> dict[str, Any]:
        report_state = report_state if isinstance(report_state, Mapping) else {}
        performance = performance if isinstance(performance, Mapping) else {}
        context = _merge_dicts(dict(performance), dict(report_state))
        self._concept_collect_cache: dict[int, list[str]] = {}
        self._concept_collect_budget = {
            "max_nodes": max(1, int(max_nodes)),
            "max_depth": max(1, int(max_depth)),
            "max_list_items": max(1, int(max_list_items)),
        }
        try:
            concepts = self._collect_concepts(context)
            selected_concepts = concepts
            if max_concepts is not None:
                selected_concepts = concepts[:max(0, int(max_concepts))]
            rows = (
                [
                    self._build_concept(concept, context).as_dict()
                    for concept in selected_concepts
                ]
                if include_rows
                else []
            )
        finally:
            self._concept_collect_cache = {}
            self._concept_collect_budget = {}
        status_counts: dict[str, int] = {}
        for row in rows:
            status = str(row.get("lifecycle_status") or "DISCOVERED")
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "system": self.system_name,
            "UNIFIED_CONCEPT_LIFECYCLE_REPORT": True,
            "concept_count": len(concepts),
            "concept_lifecycles": rows,
            "lifecycle_status_counts": status_counts,
            "concept_lifecycle_rows_rendered": len(rows),
            "concept_lifecycle_rows_limited": len(rows) < len(concepts),
            "concept_lifecycle_max_rows": max_concepts,
            "canonical_concept_lifecycle_source": True,
            "concepts_traceable_from_discovery": True,
        }

    def _build_concept(
        self,
        concept: str,
        context: Mapping[str, Any],
    ) -> ConceptLifecycle:
        discovery_source = self._discovery_source(concept, context)
        compiler = _first_dict(context, "SEMANTIC_COMPILATION_REPORT", "semantic_compilation_report")
        synthesis = _first_dict(context, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report")
        compiler = _merge_dicts(
            compiler,
            _first_dict(synthesis, "semantic_to_transformation_compilation_report"),
        )
        proposal = _first_dict(context, "candidate_proposal_report", "CANDIDATE_PROPOSAL_REPORT")
        arena = _first_dict(context, "candidate_arena_summary", "COGNITIVE_CANDIDATE_ARENA_REPORT")
        coverage = _first_dict(context, "executable_semantic_coverage_report")
        program_generation = _first_dict(context, "program_generation_report", "PROGRAM_GENERATION_REPORT")
        truth = self._truth_state(concept, context)
        compiler_supported = self._compiler_supported(concept, compiler)
        compiler_attempted = "TRUE" if compiler else "FALSE"
        compiler_success = bool(compiler.get("semantic_to_transformation_compilation_success"))
        program_state = self._program_generation_state(
            concept,
            program_generation,
            compiler,
            synthesis,
        )
        program_generated = program_state["program_generated"]
        candidate_state = self._candidate_state(concept, proposal, arena, synthesis)
        execution_package = EXECUTION_PACKAGE_SUPPORT.get(concept, "UNKNOWN")
        executable_supported = "TRUE" if concept in EXECUTABLE_SEMANTICS else "FALSE"
        semantic_memory = self._semantic_memory_state(concept, context)
        prediction = self._prediction_contribution(concept, synthesis, arena)
        missing = self._missing_requirements(
            concept,
            execution_package,
            compiler_supported,
            program_generated,
            candidate_state,
            program_state,
        )
        rejected_by = self._rejected_by(
            compiler_supported,
            program_generated,
            candidate_state,
            coverage,
        )
        accepted_by = self._accepted_by(
            truth["truth_candidate_state"],
            compiler_supported,
            program_generated,
            candidate_state,
            semantic_memory,
        )
        lifecycle = ConceptLifecycle(
            concept_id=f"concept:{concept}",
            concept_name=concept,
            discovery_source=discovery_source,
            semantic_cluster=self.semantic_cluster(concept),
            mental_model=self.mental_model(concept),
            truth_candidate_state=truth["truth_candidate_state"],
            truth_state=truth["truth_state"],
            executable_supported=executable_supported,
            execution_package_available=execution_package,
            compiler_supported=compiler_supported,
            compiler_attempted=compiler_attempted,
            compiler_result="SUCCESS" if compiler_success else ("FAILED" if compiler else "NOT_ATTEMPTED"),
            program_generation_attempted=program_state["program_generation_attempted"],
            program_generated=program_generated,
            program_rejected="FALSE" if program_generated == "TRUE" else "TRUE",
            program_rejection_reason=program_state["program_rejection_reason"],
            candidate_generated=candidate_state["candidate_generated"],
            candidate_entered_arena=candidate_state["candidate_entered_arena"],
            candidate_selected=candidate_state["candidate_selected"],
            candidate_rejected=candidate_state["candidate_rejected"],
            candidate_rejection_reason=candidate_state["candidate_rejection_reason"],
            execution_attempted="TRUE" if prediction != "NONE" else "FALSE",
            execution_success="TRUE" if prediction in {"PRIMARY", "SUPPLEMENTARY"} else "FALSE",
            prediction_contribution=prediction,
            semantic_memory_integrated=semantic_memory["semantic_memory_integrated"],
            memory_entry_id=semantic_memory["memory_entry_id"],
            memory_version=semantic_memory["memory_version"],
            memory_source=semantic_memory["memory_source"],
            accepted_by=accepted_by,
            rejected_by=rejected_by,
            missing_requirements=missing,
        )
        lifecycle.lifecycle_status = self._lifecycle_status(lifecycle)
        return lifecycle

    def semantic_cluster(self, concept: str) -> str:
        return _classify(concept, SEMANTIC_CLUSTER_RULES, "Context")

    def mental_model(self, concept: str) -> str:
        return _classify(concept, MENTAL_MODEL_RULES, "Not Available")

    def _collect_concepts(self, context: Any) -> list[str]:
        if isinstance(context, (Mapping, list, tuple, set)):
            cache = getattr(self, "_concept_collect_cache", None)
            cache_key = id(context)
            if isinstance(cache, dict) and cache_key in cache:
                return list(cache[cache_key])
        concepts: list[str] = []
        visited: set[int] = set()
        nodes_seen = 0
        budget = getattr(self, "_concept_collect_budget", {}) or {}
        max_nodes = int(budget.get("max_nodes") or 20_000)
        max_depth = int(budget.get("max_depth") or 8)
        max_list_items = int(budget.get("max_list_items") or 200)

        def visit(value: Any, key_hint: str = "", depth: int = 0) -> None:
            nonlocal nodes_seen
            if nodes_seen >= max_nodes or depth > max_depth:
                return
            nodes_seen += 1
            if isinstance(value, str):
                if key_hint in CONCEPT_KEYS:
                    concepts.append(_normalize(value))
                return
            if isinstance(value, Mapping):
                object_id = id(value)
                if object_id in visited:
                    return
                visited.add(object_id)
                for key, item in value.items():
                    key_text = str(key)
                    if key_text in CONCEPT_KEYS:
                        visit(item, key_text, depth + 1)
                    elif key_text in REPORT_KEYS or isinstance(item, (Mapping, list, tuple, set)):
                        visit(item, key_text, depth + 1)
                return
            if isinstance(value, (list, tuple, set)):
                object_id = id(value)
                if object_id in visited:
                    return
                visited.add(object_id)
                for item in list(value)[:max_list_items]:
                    visit(item, key_hint, depth + 1)

        visit(context)
        result = [item for item in dict.fromkeys(concepts) if item]
        if isinstance(context, (Mapping, list, tuple, set)):
            cache = getattr(self, "_concept_collect_cache", None)
            if isinstance(cache, dict):
                cache[id(context)] = result
        return result

    def _discovery_source(self, concept: str, context: Mapping[str, Any]) -> str:
        source_names = []
        for key in (
            "semantic_attribution_report",
            "SEMANTIC_ATTRIBUTION_REPORT",
            "concept_lifecycle_report",
            "CONCEPT_LIFECYCLE_REPORT",
            "TRANSFORMATION_SYNTHESIS_REPORT",
            "SEMANTIC_COMPILATION_REPORT",
        ):
            value = context.get(key)
            if isinstance(value, Mapping) and concept in self._collect_concepts(value):
                source_names.append(key)
        return source_names[0] if source_names else "Semantic Attribution"

    def _truth_state(self, concept: str, context: Mapping[str, Any]) -> dict[str, str]:
        truth_candidate = "FALSE"
        truth_state = "UNVERIFIED"
        visited: set[int] = set()
        nodes_seen = 0
        budget = getattr(self, "_concept_collect_budget", {}) or {}
        max_nodes = min(5_000, int(budget.get("max_nodes") or 20_000))
        max_depth = int(budget.get("max_depth") or 8)
        max_list_items = int(budget.get("max_list_items") or 200)

        def visit(value: Any, depth: int = 0) -> None:
            nonlocal truth_candidate, truth_state
            nonlocal nodes_seen
            if nodes_seen >= max_nodes or depth > max_depth:
                return
            nodes_seen += 1
            if isinstance(value, Mapping):
                object_id = id(value)
                if object_id in visited:
                    return
                visited.add(object_id)
                if _normalize(value.get("concept")) == concept:
                    if value.get("eligible_for_truth_candidate") is True or value.get("candidate_ready") is True:
                        truth_candidate = "TRUE"
                    state = value.get("state") or value.get("status") or value.get("truth_state")
                    if state:
                        truth_state = str(state).upper()
                for item in value.values():
                    if isinstance(item, (Mapping, list, tuple, set)):
                        visit(item, depth + 1)
            elif isinstance(value, (list, tuple, set)):
                object_id = id(value)
                if object_id in visited:
                    return
                visited.add(object_id)
                for item in list(value)[:max_list_items]:
                    visit(item, depth + 1)

        for key in ("truth_candidate_report", "truth_candidate_engine_report", "concept_lifecycle_report", "CONCEPT_LIFECYCLE_REPORT"):
            visit(context.get(key))
        return {"truth_candidate_state": truth_candidate, "truth_state": truth_state}

    def _compiler_supported(self, concept: str, compiler: Mapping[str, Any]) -> str:
        concepts = set(self._collect_concepts(compiler))
        intents = {_normalize(item) for item in _as_list(compiler.get("detected_intents"))}
        execution_intents = self._collect_concepts(compiler.get("execution_intents"))
        if concept in concepts or concept in intents or concept in execution_intents:
            failure = str(compiler.get("failure_reason") or "")
            if failure in {"no_executable_semantic_intents", "no_supported_compiler_for_execution_intents"}:
                return "FALSE"
            return "TRUE"
        return "TRUE" if concept in EXECUTABLE_SEMANTICS else "FALSE"

    def _program_generated(
        self,
        concept: str,
        compiler: Mapping[str, Any],
        synthesis: Mapping[str, Any],
    ) -> bool:
        if compiler.get("semantic_to_transformation_compilation_success") and concept in self._collect_concepts(compiler):
            return True
        selected = _first_dict(synthesis, "selected_program")
        return bool(selected and concept in self._collect_concepts(synthesis))

    def _program_generation_state(
        self,
        concept: str,
        program_generation: Mapping[str, Any],
        compiler: Mapping[str, Any],
        synthesis: Mapping[str, Any],
    ) -> dict[str, str]:
        for item in _as_list(program_generation.get("program_blueprints")):
            if not isinstance(item, Mapping):
                continue
            if _normalize(item.get("concept_name")) != concept:
                continue
            success = "TRUE" if item.get("generation_success") == "TRUE" else "FALSE"
            attempted = "TRUE" if item.get("generation_attempted") == "TRUE" else "FALSE"
            reason = str(item.get("blocking_reason") or "Not Available")
            return {
                "program_generation_attempted": attempted,
                "program_generated": success,
                "program_rejection_reason": reason,
                "missing_requirements": [
                    str(requirement)
                    for requirement in item.get("missing_requirements", []) or []
                ],
            }
        generated = "TRUE" if self._program_generated(concept, compiler, synthesis) else "FALSE"
        return {
            "program_generation_attempted": "TRUE" if compiler else "FALSE",
            "program_generated": generated,
            "program_rejection_reason": self._program_rejection_reason(
                EXECUTION_PACKAGE_SUPPORT.get(concept, "UNKNOWN"),
                "TRUE" if concept in EXECUTABLE_SEMANTICS else "FALSE",
                "TRUE" if concept in EXECUTABLE_SEMANTICS else "FALSE",
                generated,
            ),
            "missing_requirements": [],
        }

    def _candidate_state(
        self,
        concept: str,
        proposal: Mapping[str, Any],
        arena: Mapping[str, Any],
        synthesis: Mapping[str, Any],
    ) -> dict[str, str]:
        generated = "FALSE"
        entered = "FALSE"
        selected = "FALSE"
        rejected = "FALSE"
        reason = "Not Available"
        proposal_items = []
        for key in ("candidate_proposals", "proposals", "candidate_summary", "rejected_proposals", "rejected_candidates"):
            proposal_items.extend(_as_list(proposal.get(key)))
            proposal_items.extend(_as_list(arena.get(key)))
            proposal_items.extend(_as_list(synthesis.get(key)))
        for item in proposal_items:
            if not isinstance(item, Mapping):
                continue
            item_concepts = set(self._collect_concepts(item))
            item_text = " ".join(str(item.get(key, "")) for key in ("intent", "operation", "source"))
            if concept not in item_concepts and concept not in _normalize(item_text):
                continue
            generated = "TRUE"
            if item.get("entered_arena") is True or item.get("proposal_status") == "PROPOSED":
                entered = "TRUE"
            if item.get("selected") is True or item.get("status") == "WINNER":
                selected = "TRUE"
            if item.get("proposal_status") == "REJECTED" or str(item.get("status", "")).startswith("REJECTED"):
                rejected = "TRUE"
                reasons = item.get("rejection_reasons") or item.get("blocked_reason")
                reason = ", ".join(str(part) for part in _as_list(reasons)) or "REJECTED"
        winner_operation = _normalize(arena.get("winner_operation"))
        if winner_operation and concept in _normalize(winner_operation):
            generated = entered = selected = "TRUE"
        return {
            "candidate_generated": generated,
            "candidate_entered_arena": entered,
            "candidate_selected": selected,
            "candidate_rejected": rejected,
            "candidate_rejection_reason": reason,
        }

    def _semantic_memory_state(self, concept: str, context: Mapping[str, Any]) -> dict[str, str | None]:
        for key in ("semantic_memory_report", "SEMANTIC_MEMORY_REPORT", "semantic_virtual_memory_report"):
            report = context.get(key)
            for entity in _as_list(_read_any(report, "Semantic Entities", "semantic_entities", "entities", "memory_entries")):
                if not isinstance(entity, Mapping):
                    continue
                if concept not in set(self._collect_concepts(entity)) and _normalize(entity.get("concept")) != concept:
                    continue
                return {
                    "semantic_memory_integrated": "TRUE",
                    "memory_entry_id": entity.get("semantic_memory_id") or entity.get("memory_entry_id") or entity.get("id"),
                    "memory_version": str(entity.get("memory_version") or entity.get("version")) if (entity.get("memory_version") or entity.get("version")) else None,
                    "memory_source": entity.get("memory_source") or key,
                }
        return {"semantic_memory_integrated": "FALSE", "memory_entry_id": None, "memory_version": None, "memory_source": None}

    def _prediction_contribution(
        self,
        concept: str,
        synthesis: Mapping[str, Any],
        arena: Mapping[str, Any],
    ) -> str:
        selected = _first_dict(synthesis, "selected_program")
        if selected and concept in set(self._collect_concepts(synthesis)):
            return "PRIMARY"
        if arena.get("winner_operation") and concept in _normalize(arena.get("winner_operation")):
            return "PRIMARY"
        if concept in set(self._collect_concepts(synthesis)):
            return "PARTIAL"
        return "NONE"

    def _missing_requirements(
        self,
        concept: str,
        execution_package: str,
        compiler_supported: str,
        program_generated: str,
        candidate_state: Mapping[str, str],
        program_state: Mapping[str, Any] | None = None,
    ) -> list[str]:
        missing = []
        program_state = program_state if isinstance(program_state, Mapping) else {}
        for item in program_state.get("missing_requirements", []) or []:
            missing.append(str(item))
        if execution_package == "FALSE":
            missing.append(f"{concept.replace('_', ' ').title()} Execution Package")
        if compiler_supported == "FALSE":
            missing.append("Semantic Compiler Support")
        if program_generated == "FALSE":
            missing.append("Program Generation")
        if candidate_state.get("candidate_generated") == "FALSE":
            missing.append("Candidate Proposal")
        return list(dict.fromkeys(missing))

    def _program_rejection_reason(
        self,
        execution_package: str,
        compiler_supported: str,
        executable_supported: str,
        program_generated: str,
    ) -> str:
        if program_generated == "TRUE":
            return "Not Available"
        if execution_package == "FALSE":
            return PROGRAM_REJECTION_NO_EXECUTION_PACKAGE
        if compiler_supported == "FALSE":
            return PROGRAM_REJECTION_NO_COMPILER_SUPPORT
        if executable_supported == "FALSE":
            return PROGRAM_REJECTION_NO_EXECUTABLE_MAPPING
        return "NO_PROGRAM_GENERATED"

    def _accepted_by(self, truth_candidate, compiler_supported, program_generated, candidate_state, semantic_memory):
        accepted = []
        if truth_candidate == "TRUE":
            accepted.append("Truth Governance")
        if compiler_supported == "TRUE":
            accepted.append("Semantic Compilation")
        if program_generated == "TRUE":
            accepted.append("Program Generation")
        if candidate_state.get("candidate_generated") == "TRUE":
            accepted.append("Candidate Proposal Phase")
        if semantic_memory.get("semantic_memory_integrated") == "TRUE":
            accepted.append("Semantic Memory")
        return accepted

    def _rejected_by(self, compiler_supported, program_generated, candidate_state, coverage):
        rejected = []
        if compiler_supported == "FALSE":
            rejected.append("Semantic Compilation")
        if program_generated == "FALSE":
            rejected.append("Program Generation")
        if candidate_state.get("candidate_rejected") == "TRUE":
            rejected.append("Cognitive Candidate Arena")
        if coverage.get("coverage_state") == "NOT_MEASURABLE":
            rejected.append("Executable Semantic Coverage")
        return rejected

    def _lifecycle_status(self, lifecycle: ConceptLifecycle) -> str:
        if lifecycle.prediction_contribution in {"PRIMARY", "SUPPLEMENTARY"}:
            return "OPERATIONAL"
        if lifecycle.execution_package_available == "FALSE":
            return "DISCOVERED_BUT_NOT_EXECUTABLE"
        if lifecycle.compiler_supported == "FALSE":
            return "DISCOVERED_BUT_NOT_COMPILABLE"
        if lifecycle.candidate_generated == "TRUE":
            return "CANDIDATE_AVAILABLE"
        return "DISCOVERED"


CONCEPT_KEYS = {
    "concept",
    "concept_name",
    "concepts",
    "detected_concepts",
    "attributed_concepts",
    "semantic_concepts",
    "generated_concepts",
    "target_concepts",
    "matched_concepts",
    "routed_concepts",
    "detected_intents",
}

REPORT_KEYS = {
    "concept_lifecycle_report",
    "CONCEPT_LIFECYCLE_REPORT",
    "semantic_attribution_report",
    "SEMANTIC_ATTRIBUTION_REPORT",
    "truth_candidate_report",
    "truth_candidate_engine_report",
    "SEMANTIC_COMPILATION_REPORT",
    "semantic_compilation_report",
    "TRANSFORMATION_SYNTHESIS_REPORT",
    "transformation_synthesis_report",
    "candidate_proposal_report",
    "candidate_arena_summary",
    "COGNITIVE_CANDIDATE_ARENA_REPORT",
    "semantic_memory_report",
    "SEMANTIC_MEMORY_REPORT",
    "program_generation_report",
    "PROGRAM_GENERATION_REPORT",
}


def _classify(concept: str, rules: tuple[tuple[str, tuple[str, ...]], ...], default: str) -> str:
    for name, tokens in rules:
        if any(token in concept for token in tokens):
            return name
    return default


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _first_dict(base: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = base.get(key) if isinstance(base, Mapping) else None
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _merge_dicts(*items: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in items:
        if isinstance(item, Mapping):
            merged.update(dict(item))
    return merged


def _read_any(source: Any, *keys: str) -> Any:
    if not isinstance(source, Mapping):
        return None
    for key in keys:
        if key in source:
            return source[key]
    return None


unified_concept_lifecycle_builder = UnifiedConceptLifecycleBuilder()

__all__ = [
    "ConceptLifecycle",
    "UnifiedConceptLifecycleBuilder",
    "unified_concept_lifecycle_builder",
]
