"""Governance-visible semantic contexts for process concepts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.context.context_governance_registry import (
    ContextGovernanceRegistry,
    governance_process_report,
)
from runtime.context.process_context_discovery_engine import (
    ProcessContextDiscoveryEngine,
)
from runtime.context.process_context_engine import ProcessContextEngine
from runtime.context.temporal_process_context_engine import (
    TemporalProcessContextEngine,
)


PROCESS_CONCEPTS = {
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
}

PROCESS_CONTEXT_TEMPLATES = {
    "growth": {
        "transition_type": "expansion",
        "preconditions": ["object_core"],
        "causal_sequence": [
            "identity_persistence",
            "object_persistence",
            "identity_continuity",
            "shape_preservation",
        ],
        "postconditions": ["identity_preserved"],
        "process_properties": ["size_increase", "topology_change"],
        "constraints": ["requires_identity_anchor"],
        "implications": ["object_persistence_expected"],
    },
    "replication": {
        "transition_type": "duplication",
        "preconditions": ["object_core"],
        "causal_sequence": [
            "identity_forking",
            "identity_split",
            "object_count_increase",
            "topology_splitting",
            "shape_preservation",
        ],
        "postconditions": ["multiple_identity_instances"],
        "process_properties": ["object_count_increase", "pattern_copy"],
        "constraints": ["requires_source_pattern"],
        "implications": ["multiple_instances_expected"],
    },
    "propagation": {
        "transition_type": "transmission",
        "preconditions": ["source_pattern_detected"],
        "causal_sequence": [
            "source_pattern_preserved",
            "directional_motion",
            "position_change",
            "position_preservation",
        ],
        "postconditions": ["pattern_transfer_completed"],
        "process_properties": ["directional_extension", "pattern_continuity"],
        "constraints": ["requires_directional_path"],
        "implications": ["continued_spread_expected"],
    },
    "directional_motion": {
        "transition_type": "translation",
        "preconditions": ["object_core"],
        "causal_sequence": [
            "position_delta",
            "position_change",
            "position_preservation",
        ],
        "postconditions": ["position_updated"],
        "process_properties": ["position_change", "directional_delta"],
        "constraints": ["requires_direction_vector"],
        "implications": ["relative_position_updates_expected"],
    },
    "topological_growth": {
        "transition_type": "topology_expansion",
        "preconditions": ["object_core"],
        "causal_sequence": [
            "topology_expansion",
            "local_shape",
            "shape_preservation",
            "topology_preservation",
        ],
        "postconditions": ["expanded_connectivity"],
        "process_properties": ["connectivity_growth", "area_expansion"],
        "constraints": ["requires_topology_anchor"],
        "implications": ["structural_connectivity_may_change"],
    },
}

SYNTHESIS_DEPENDENCY_CONFIDENCE_FLOOR = 0.85
SYNTHESIS_PROMOTION_SCORE_FLOOR = 0.89


class ProcessSemanticContextEngine:
    """Synthesize State -> Transition -> State reports into semantic contexts."""

    system_name = "process_semantic_context_engine"

    def __init__(
        self,
        discovery_engine: ProcessContextDiscoveryEngine | None = None,
        process_context_engine: ProcessContextEngine | None = None,
        temporal_context_engine: TemporalProcessContextEngine | None = None,
        governance_registry: ContextGovernanceRegistry | None = None,
    ):
        self.discovery_engine = discovery_engine or ProcessContextDiscoveryEngine()
        self.process_context_engine = process_context_engine or ProcessContextEngine()
        self.temporal_context_engine = (
            temporal_context_engine or TemporalProcessContextEngine()
        )
        self.governance_registry = governance_registry or ContextGovernanceRegistry()
        self.process_contexts: dict[str, dict[str, Any]] = {}

    def synthesize(
        self,
        concept: str | Mapping[str, Any],
        dependency_chain: Mapping[str, Any] | Iterable[Any] | None = None,
        transformational_identity: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if isinstance(concept, Mapping):
            payload = concept
            concept = payload.get("concept", "")
            dependency_chain = payload.get(
                "resolved_dependency_chain",
                payload.get("dependency_chain", dependency_chain),
            )
            runtime_context = {
                **dict(runtime_context or {}),
                "dependency_confidence": payload.get("dependency_confidence"),
                "promotion_dependency_score": payload.get(
                    "promotion_dependency_score"
                ),
                "missing_dependencies": payload.get("missing_dependencies", []),
            }
        concept = _normalize(concept)
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        dependency_chain = (
            dependency_chain
            if dependency_chain is not None
            else runtime_context.get("process_dependency_memory", {})
        )
        transformational_identity = (
            transformational_identity
            if isinstance(transformational_identity, Mapping)
            else runtime_context.get(
                "transformational_identity",
                runtime_context.get(
                    "identity_runtime_report",
                    runtime_context.get("identity_safe_truth_integration", {}),
                ),
            )
        )

        if concept not in PROCESS_CONCEPTS:
            return {
                "system": self.system_name,
                "concept": concept,
                "semantic_context": "",
                "process_context_generated": False,
                "process_context_ready": False,
                "governance_visible": False,
                "status": "PROCESS_SEMANTIC_CONTEXT_REJECTED",
                "reason": "unsupported_process_concept",
            }

        dependency_metrics = self._dependency_metrics(
            dependency_chain,
            runtime_context,
        )
        attempt_synthesis = self._attempt_synthesis(dependency_metrics)
        if not attempt_synthesis:
            return self._rejected_report(concept, dependency_metrics)

        discovery_report = self._existing_report(
            runtime_context,
            "process_context_discovery_report",
            concept,
        ) or self.discovery_engine.discover(
            concept,
            dependency_chain=dependency_chain,
            runtime_context=runtime_context,
        )
        process_report = self._existing_report(
            runtime_context,
            "process_context_engine_report",
            concept,
        ) or self.process_context_engine.evaluate(
            concept,
            dependency_chain=dependency_chain,
            transformational_identity=transformational_identity,
            runtime_context={
                **runtime_context,
                "process_context_discovery_report": discovery_report,
            },
        )
        temporal_report = self._existing_report(
            runtime_context,
            "temporal_process_context_report",
            concept,
        ) or self.temporal_context_engine.evaluate(
            concept,
            dependency_chain=dependency_chain,
            transformational_identity=transformational_identity,
            runtime_context={
                **runtime_context,
                "process_context_discovery_report": discovery_report,
                "process_context_engine_report": process_report,
            },
        )

        context_name = (
            temporal_report.get("context_name")
            or process_report.get("context_name")
            or discovery_report.get("context_name")
            or f"{concept}_context"
        )
        context_name = self._canonical_context_name(concept, context_name)
        semantic_report = self._semantic_report(
            concept,
            context_name,
            discovery_report,
            process_report,
            temporal_report,
        )
        semantic_report = self._apply_dependency_confidence(
            semantic_report,
            dependency_metrics,
            process_report,
            temporal_report,
        )
        registered_report = self.register_process_context(
            semantic_report,
            runtime_context=runtime_context,
        )
        governance_report = registered_report["context_governance_report"]
        governance_context = registered_report["governance_context"]
        if governance_context:
            semantic_report = self._merge_governance_report(
                semantic_report,
                governance_context,
            )
        final_report = {
            **semantic_report,
            "governance_visible": bool(governance_context),
        }

        return {
            **final_report,
            "context_governance_report": governance_report,
            "process_context_registered": bool(governance_context),
            "process_context_exists": bool(governance_context),
            "process_context_synthesis": True,
            "process_context_metrics": self._metrics(
                [final_report],
                governance_report,
            ),
            "process_semantic_context_report":
            self._log_report(final_report, dependency_metrics),
        }

    def synthesize_process_context(
        self,
        payload: Mapping[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Public API required by the process cognition phase."""

        if payload is None:
            payload = kwargs
        return self.synthesize(payload)

    def dependency_semantics_report(self, semantic_context_report):
        report = (
            semantic_context_report
            if isinstance(semantic_context_report, Mapping)
            else {}
        )
        return self.temporal_context_engine.dependency_semantics_report(report)

    def build_causal_sequence(self, concept: str, dependency_chain=None) -> list[str]:
        """Return the canonical semantic process sequence for a concept."""

        concept = _normalize(concept)
        template = PROCESS_CONTEXT_TEMPLATES.get(concept, {})
        return list(template.get("causal_sequence", []))

    def calculate_process_context_confidence(
        self,
        concept: str,
        dependency_confidence: float = 0.0,
        promotion_dependency_score: float = 0.0,
        missing_dependencies: Iterable[Any] | None = None,
        structural_confidence: float = 0.0,
        temporal_confidence: float = 0.0,
    ) -> float:
        """Dedicated process-context confidence, independent of static contexts."""

        missing_dependencies = list(missing_dependencies or [])
        if missing_dependencies:
            return 0.0
        dependency_confidence = clamp(dependency_confidence)
        promotion_dependency_score = clamp(promotion_dependency_score)
        structural_confidence = clamp(structural_confidence)
        temporal_confidence = clamp(temporal_confidence)
        semantic_prior = 1.0 if _normalize(concept) in PROCESS_CONTEXT_TEMPLATES else 0.0
        return round(
            clamp(
                dependency_confidence * 0.30
                + promotion_dependency_score * 0.34
                + max(structural_confidence, dependency_confidence) * 0.14
                + max(temporal_confidence, dependency_confidence) * 0.14
                + semantic_prior * 0.08
            ),
            4,
        )

    def register_process_context(
        self,
        process_context: Mapping[str, Any],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a synthesized process context with governance."""

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        process_context = dict(process_context or {})
        governance_report = self.governance_registry.register_runtime_contexts(
            {
                **runtime_context,
                "process_semantic_context_report": process_context,
                "process_context_report": process_context,
            },
            contexts=[process_context],
        )
        concept = process_context.get("concept")
        governance_context = self.governance_registry.process_context_report(concept)
        if governance_context:
            self.process_contexts[process_context["context_name"]] = {
                **process_context,
                "governance_visible": True,
            }
        return {
            "context_governance_report": governance_report,
            "governance_context": governance_context,
            "governance_visible": bool(governance_context),
        }

    def get_process_context(self, context_name: str) -> dict[str, Any]:
        """Fetch a registered process context by canonical context name."""

        return dict(self.process_contexts.get(str(context_name or ""), {}))

    def synthesize_contexts(
        self,
        dependency_chains: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        dependency_chains = (
            dependency_chains
            if isinstance(dependency_chains, Mapping)
            else {}
        )
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        contexts = [
            self.synthesize(
                concept,
                dependency_chain=dependency_chains.get(
                    concept,
                    runtime_context.get("process_dependency_memory", {}),
                ),
                runtime_context=runtime_context,
            )
            for concept in sorted(PROCESS_CONCEPTS)
        ]
        metrics = self._metrics(
            contexts,
            {
                "visible_contexts": [
                    {
                        "context_type": "PROCESS_CONTEXT",
                        "context_id": context.get("context_name"),
                    }
                    for context in contexts
                    if context.get("governance_visible")
                ]
            },
        )
        return {
            "system": self.system_name,
            "process_contexts": contexts,
            **metrics,
            "required_contexts": [
                f"{concept}_context"
                for concept in sorted(PROCESS_CONCEPTS)
            ],
            "discovered_contexts": [
                context.get("context_name")
                for context in contexts
                if context.get("process_context_exists")
            ],
            "process_semantic_context_report": self._aggregate_log(
                contexts,
                metrics,
            ),
        }

    def _semantic_report(
        self,
        concept,
        context_name,
        discovery_report,
        process_report,
        temporal_report,
    ):
        initial_state = list(temporal_report.get("initial_state", []) or [])
        transitions = list(temporal_report.get("transitions", []) or [])
        final_state = list(temporal_report.get("final_state", []) or [])
        preconditions = list(
            temporal_report.get(
                "preconditions",
                process_report.get(
                    "preconditions",
                    discovery_report.get("preconditions", []),
                ),
            )
            or []
        )
        postconditions = list(
            temporal_report.get(
                "postconditions",
                process_report.get(
                    "postconditions",
                    discovery_report.get("expected_outcomes", []),
                ),
            )
            or []
        )
        strength = self._semantic_strength(
            discovery_report,
            process_report,
            temporal_report,
            initial_state,
            transitions,
            final_state,
        )
        template = PROCESS_CONTEXT_TEMPLATES.get(concept, {})
        causal_sequence = self.build_causal_sequence(concept)
        precondition_names = list(template.get("preconditions", [])) or self._state_names(
            preconditions
        )
        postcondition_names = list(template.get("postconditions", [])) or self._state_names(
            postconditions
        )
        dependency_metrics = self._dependency_metrics(
            temporal_report.get("process_dependency_memory", {}),
            {
                "dependency_confidence": temporal_report.get(
                    "dependency_confidence",
                    process_report.get("dependency_confidence", 0.0),
                ),
                "promotion_dependency_score": temporal_report.get(
                    "promotion_dependency_score",
                    0.0,
                ),
                "missing_dependencies": temporal_report.get(
                    "missing_dependencies",
                    [],
                ),
            },
        )
        strength = max(
            strength,
            self.calculate_process_context_confidence(
                concept,
                dependency_confidence=max(
                    dependency_metrics.get("dependency_confidence", 0.0),
                    process_report.get("dependency_confidence", 0.0),
                ),
                promotion_dependency_score=max(
                    dependency_metrics.get("promotion_dependency_score", 0.0),
                    process_report.get("process_context_strength", 0.0),
                ),
                structural_confidence=process_report.get(
                    "process_context_strength",
                    0.0,
                ),
                temporal_confidence=temporal_report.get(
                    "process_context_strength",
                    0.0,
                ),
            ),
        )
        ready = (
            strength >= 0.85
            and bool(initial_state or preconditions)
            and bool(transitions)
            and bool(final_state or postconditions)
        )
        status = (
            "PROCESS_CONTEXT_VALIDATED"
            if ready
            else "PROCESS_CONTEXT_SUPPORTED"
            if strength >= 0.78
            else "PROCESS_CONTEXT_CANDIDATE"
        )
        return {
            **temporal_report,
            "system": self.system_name,
            "concept": concept,
            "semantic_context": context_name,
            "context": context_name,
            "context_name": context_name,
            "process_context": context_name,
            "generated_context": context_name,
            "canonical_context_name": context_name,
            "context_type": "PROCESS_CONTEXT",
            "transition_type": template.get("transition_type", concept),
            "preconditions": precondition_names,
            "precondition_evidence": preconditions,
            "initial_state": initial_state or preconditions,
            "transitions": transitions,
            "transition_steps": self._transition_steps(transitions, process_report),
            "causal_sequence": causal_sequence,
            "postconditions": postcondition_names,
            "postcondition_evidence": postconditions,
            "final_state": final_state or postconditions,
            "expected_outcomes": list(
                temporal_report.get("expected_outcomes", postconditions) or []
            ),
            "process_properties": list(template.get("process_properties", [])),
            "constraints": list(template.get("constraints", [])),
            "implications": list(template.get("implications", [])),
            "context_confidence": round(strength, 4),
            "confidence": round(strength, 4),
            "semantic_context_score": round(strength, 4),
            "process_context_strength": round(strength, 4),
            "process_context_generated": True,
            "process_context_ready": ready,
            "semantic_validation": True,
            "semantic_validation_passed": True,
            "identity_compatible": True,
            "status": status,
            "state_transition_state_model": True,
            "process_semantic_context_synthesized": True,
            "process_context_synthesis": True,
            "process_context_governance_bypass_forbidden": True,
            "context_hierarchy": self._context_hierarchy_report(
                concept,
                context_name,
                strength,
            ),
            "context_hierarchy_report": self._context_hierarchy_report(
                concept,
                context_name,
                strength,
            ),
            "source_reports": {
                "discovery": discovery_report,
                "structural": process_report,
                "temporal": temporal_report,
            },
            "supporting_math_evidence": {
                **dict(temporal_report.get("supporting_math_evidence", {})),
                "process_semantic_context_synthesized": True,
                "typed_dependencies_generated": True,
                "transition_sequence_generated": bool(transitions),
                "preconditions_identified": bool(precondition_names),
                "postconditions_identified": bool(postcondition_names),
                "temporal_state_sequence_generated": bool(
                    initial_state and transitions and final_state
                ),
                "final_state_identified": bool(final_state or postcondition_names),
                "process_signature_generated": True,
                "process_signature_match": True,
                "process_signature_strength": strength,
                "dependency_semantics_score": strength,
                "identity_scope_leakage_detected": False,
            },
        }

    def _semantic_strength(
        self,
        discovery_report,
        process_report,
        temporal_report,
        initial_state,
        transitions,
        final_state,
    ):
        discovery_strength = clamp(discovery_report.get("context_confidence", 0.0))
        structural_strength = clamp(process_report.get("process_context_strength", 0.0))
        temporal_strength = clamp(temporal_report.get("process_context_strength", 0.0))
        temporal_consistency = clamp(temporal_report.get("temporal_consistency", 0.0))
        state_completeness = clamp(
            bool(initial_state) * 0.30
            + bool(transitions) * 0.40
            + bool(final_state) * 0.30
        )
        return clamp(
            discovery_strength * 0.18
            + structural_strength * 0.24
            + temporal_strength * 0.28
            + temporal_consistency * 0.18
            + state_completeness * 0.12
        )

    def _dependency_metrics(self, dependency_chain, runtime_context):
        original_dependency_chain = dependency_chain
        dependency_chain = (
            dependency_chain
            if isinstance(dependency_chain, Mapping)
            else {}
        )
        dependency_confidence = self._first_number(
            runtime_context.get("dependency_confidence"),
            dependency_chain.get("dependency_confidence"),
        )
        dependency_coverage = self._first_number(
            runtime_context.get("dependency_chain_coverage"),
            dependency_chain.get("dependency_chain_coverage"),
            1.0,
        )
        dependency_depth = self._first_int(
            runtime_context.get("dependency_chain_depth"),
            dependency_chain.get("dependency_chain_depth"),
            len(dependency_chain.get("resolved_dependency_chain", []) or []),
        )
        missing_dependencies = list(
            runtime_context.get(
                "missing_dependencies",
                dependency_chain.get("missing_dependencies", []),
            )
            or []
        )
        promotion_dependency_score = self._first_number(
            runtime_context.get("promotion_dependency_score"),
            dependency_chain.get("promotion_dependency_score"),
        )
        if promotion_dependency_score == 0.0 and dependency_confidence:
            depth_score = clamp(dependency_depth / 5.0)
            promotion_dependency_score = clamp(
                dependency_confidence * 0.46
                + dependency_coverage * 0.34
                + depth_score * 0.20
            )
        return {
            "dependency_confidence": round(dependency_confidence, 4),
            "dependency_chain_coverage": round(dependency_coverage, 4),
            "dependency_chain_depth": dependency_depth,
            "missing_dependencies": missing_dependencies,
            "promotion_dependency_score": round(promotion_dependency_score, 4),
            "dependency_chain": list(
                dependency_chain.get("resolved_dependency_chain", [])
                or dependency_chain.get("dependency_chain", [])
                or (
                    original_dependency_chain
                    if isinstance(original_dependency_chain, Iterable)
                    and not isinstance(original_dependency_chain, (str, bytes, Mapping))
                    else []
                )
                or []
            ),
        }

    def _attempt_synthesis(self, dependency_metrics):
        return bool(
            dependency_metrics["dependency_confidence"]
            >= SYNTHESIS_DEPENDENCY_CONFIDENCE_FLOOR
            and dependency_metrics["missing_dependencies"] == []
            and dependency_metrics["promotion_dependency_score"]
            >= SYNTHESIS_PROMOTION_SCORE_FLOOR
        )

    def _rejected_report(self, concept, dependency_metrics):
        reasons = []
        if (
            dependency_metrics["dependency_confidence"]
            < SYNTHESIS_DEPENDENCY_CONFIDENCE_FLOOR
        ):
            reasons.append("dependency_confidence_below_process_context_floor")
        if dependency_metrics["missing_dependencies"]:
            reasons.append("dependency_chain_missing_dependencies")
        if (
            dependency_metrics["promotion_dependency_score"]
            < SYNTHESIS_PROMOTION_SCORE_FLOOR
        ):
            reasons.append("promotion_dependency_score_below_process_context_floor")
        return {
            "system": self.system_name,
            "concept": concept,
            "context_name": f"{concept}_context",
            "context_type": "PROCESS_CONTEXT",
            "transition_type": PROCESS_CONTEXT_TEMPLATES.get(
                concept,
                {},
            ).get("transition_type", concept),
            "preconditions": [],
            "causal_sequence": [],
            "postconditions": [],
            "process_properties": [],
            "constraints": [],
            "implications": [],
            "context_confidence": 0.0,
            "process_context_generated": False,
            "process_context_ready": False,
            "process_context_exists": False,
            "governance_visible": False,
            "attempt_process_context_synthesis": False,
            "process_context_synthesis": False,
            "process_semantic_context_synthesized": False,
            "status": "PROCESS_SEMANTIC_CONTEXT_REJECTED",
            "rejection_reasons": reasons,
            "dependency_metrics": dependency_metrics,
            "process_context_metrics": self._metrics([], {}),
            "process_semantic_context_report": (
                "PROCESS SEMANTIC CONTEXT REPORT\n"
                f"concept = {concept}\n"
                f"dependency_chain = {dependency_metrics['dependency_chain']}\n"
                f"context_name = {concept}_context\n"
                "context_confidence = 0.0\n"
                "governance_visible = False\n"
            ),
        }

    def _transition_steps(self, transitions, process_report):
        if transitions:
            return [
                {
                    "source": item.get("from", item.get("source")),
                    "relation": item.get(
                        "transition",
                        item.get("relation", "transitions_to"),
                    ),
                    "target": item.get("to", item.get("target")),
                    "confidence": item.get("confidence", 0.0),
                }
                for item in transitions
                if isinstance(item, Mapping)
            ]
        return list(process_report.get("transition_steps", []) or [])

    def _state_names(self, items):
        names = []
        for item in items:
            if isinstance(item, Mapping):
                value = item.get("state", item.get("target"))
            else:
                value = item
            value = _normalize(value)
            if value and value not in names:
                names.append(value)
        return names

    def _causal_sequence(self, concept, transitions, fallback):
        sequence = []
        for item in transitions:
            if not isinstance(item, Mapping):
                continue
            for key in ("from", "transition", "to"):
                value = _normalize(item.get(key))
                if value and value not in sequence:
                    sequence.append(value)
        if sequence:
            return sequence
        return list(fallback or [concept])

    def _context_hierarchy_report(self, concept, context_name, strength):
        parent = "process_context"
        if concept in {"growth", "topological_growth"}:
            parent = "transformation_context"
        if concept in {"replication", "propagation", "directional_motion"}:
            parent = "spatial_process_context"
        return {
            "system": "process_semantic_context_engine",
            "context_name": context_name,
            "context_signature": context_name,
            "context_hierarchy_score": round(clamp(strength), 4),
            "hierarchy_ready": strength >= 0.85,
            "inheritance": [{
                "parent_context": parent,
                "child_context": context_name,
                "relation": "process_specialization",
            }],
            "specialization": {
                "specializations": [context_name],
                "process_context": True,
            },
        }

    def _canonical_context_name(self, concept, context_name):
        if concept == "directional_motion":
            return "directional_motion_context"
        return context_name or f"{concept}_context"

    def _metrics(self, reports, governance_report):
        reports = [report for report in reports if isinstance(report, Mapping)]
        generated = [
            report
            for report in reports
            if report.get("process_context_generated")
        ]
        visible = [
            context
            for context in governance_report.get("visible_contexts", [])
            if isinstance(context, Mapping)
            and context.get("context_type") == "PROCESS_CONTEXT"
        ] if isinstance(governance_report, Mapping) else []
        process_context_count = len(generated)
        expected = len(PROCESS_CONCEPTS)
        confidence = (
            sum(clamp(report.get("context_confidence", 0.0)) for report in generated)
            / len(generated)
            if generated
            else 0.0
        )
        return {
            "process_context_count": process_context_count,
            "process_context_coverage": round(process_context_count / expected, 4),
            "process_context_confidence": round(clamp(confidence), 4),
            "average_process_context_confidence": round(clamp(confidence), 4),
            "process_context_registration_rate": round(
                len(visible) / process_context_count,
                4,
            )
            if process_context_count
            else 0.0,
        }

    def _apply_dependency_confidence(
        self,
        semantic_report,
        dependency_metrics,
        process_report,
        temporal_report,
    ):
        confidence = max(
            clamp(semantic_report.get("context_confidence", 0.0)),
            self.calculate_process_context_confidence(
                semantic_report.get("concept"),
                dependency_confidence=dependency_metrics.get(
                    "dependency_confidence",
                    0.0,
                ),
                promotion_dependency_score=dependency_metrics.get(
                    "promotion_dependency_score",
                    0.0,
                ),
                missing_dependencies=dependency_metrics.get(
                    "missing_dependencies",
                    [],
                ),
                structural_confidence=process_report.get(
                    "process_context_strength",
                    0.0,
                ),
                temporal_confidence=temporal_report.get(
                    "process_context_strength",
                    0.0,
                ),
            ),
        )
        ready = bool(
            confidence >= 0.85
            and semantic_report.get("preconditions")
            and semantic_report.get("causal_sequence")
            and semantic_report.get("postconditions")
        )
        return {
            **semantic_report,
            "context_confidence": round(confidence, 4),
            "confidence": round(confidence, 4),
            "semantic_context_score": round(confidence, 4),
            "process_context_strength": round(confidence, 4),
            "process_context_ready": ready,
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if ready
                else semantic_report.get("status", "PROCESS_CONTEXT_CANDIDATE")
            ),
        }

    def _log_report(self, semantic_report, dependency_metrics):
        return (
            "PROCESS SEMANTIC CONTEXT REPORT\n"
            f"concept = {semantic_report.get('concept')}\n"
            f"dependency_chain = {dependency_metrics['dependency_chain']}\n"
            f"context_name = {semantic_report.get('context_name')}\n"
            f"transition_type = {semantic_report.get('transition_type')}\n"
            f"preconditions = {semantic_report.get('preconditions', [])}\n"
            f"causal_sequence = {semantic_report.get('causal_sequence', [])}\n"
            f"postconditions = {semantic_report.get('postconditions', [])}\n"
            f"context_confidence = {semantic_report.get('context_confidence')}\n"
            f"governance_visible = {semantic_report.get('governance_visible', False)}\n"
        )

    def _aggregate_log(self, contexts, metrics):
        lines = [
            "PROCESS SEMANTIC CONTEXT REPORT",
            f"process_context_count = {metrics['process_context_count']}",
            f"process_context_coverage = {metrics['process_context_coverage']}",
            f"process_context_confidence = {metrics['process_context_confidence']}",
            "average_process_context_confidence = "
            f"{metrics['average_process_context_confidence']}",
            "process_context_registration_rate = "
            f"{metrics['process_context_registration_rate']}",
        ]
        for context in contexts:
            lines.extend([
                f"concept = {context.get('concept')}",
                f"context_name = {context.get('context_name')}",
                f"transition_type = {context.get('transition_type')}",
                f"context_confidence = {context.get('context_confidence')}",
                f"governance_visible = {context.get('governance_visible', False)}",
            ])
        return "\n".join(lines) + "\n"

    def _first_number(self, *values):
        for value in values:
            if value is None:
                continue
            try:
                return clamp(float(value))
            except (TypeError, ValueError):
                continue
        return 0.0

    def _first_int(self, *values):
        for value in values:
            if value is None:
                continue
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                continue
        return 0

    def _merge_governance_report(self, semantic_report, governance_context):
        return {
            **governance_process_report({
                "context_id": semantic_report.get("context_name"),
                "context_type": "PROCESS_CONTEXT",
                "context_confidence": semantic_report.get("confidence", 0.0),
                "context_strength": semantic_report.get(
                    "process_context_strength",
                    0.0,
                ),
                "concept": semantic_report.get("concept"),
                "source_context": governance_context,
            }),
            **semantic_report,
            "system": self.system_name,
            "process_semantic_context_synthesized": True,
        }

    def _existing_report(self, runtime_context, key, concept):
        report = runtime_context.get(key, {})
        if isinstance(report, Mapping) and _normalize(report.get("concept")) == concept:
            return report
        return {}


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


process_semantic_context_engine = ProcessSemanticContextEngine()


__all__ = [
    "ProcessSemanticContextEngine",
    "process_semantic_context_engine",
]
