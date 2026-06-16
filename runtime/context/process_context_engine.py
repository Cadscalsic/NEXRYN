"""Runtime process contexts for transition-aware concepts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.context.process_context_discovery_engine import (
    ProcessContextDiscoveryEngine,
)


PROCESS_CONCEPTS = {
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
}

PRECONDITION_RELATIONS = {
    "requires",
    "depends_on",
    "derived_from",
    "preserves",
    "supports",
}

TRANSITION_RELATIONS = {
    "causes",
    "creates",
    "enables",
    "modifies",
    "splits",
    "merges",
}


class ProcessContextEngine:
    """Build temporal process contexts from dependency and identity reports."""

    system_name = "process_context_engine"

    def __init__(self):
        self.discovery_engine = ProcessContextDiscoveryEngine()

    def evaluate(
        self,
        concept: str,
        dependency_chain: Mapping[str, Any] | Iterable[Any] | None = None,
        transformational_identity: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
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
                "preconditions": [],
                "transition_steps": [],
                "postconditions": [],
                "process_context_strength": 0.0,
                "process_context_generated": False,
                "process_context_ready": False,
                "status": "PROCESS_CONTEXT_REJECTED",
                "reason": "unsupported_process_concept",
            }

        nodes = self._dependency_nodes(dependency_chain)
        relations = self._typed_relations(dependency_chain)
        discovery_report = self._discovery_report(
            concept,
            dependency_chain,
            runtime_context,
        )
        preconditions = self._preconditions(concept, nodes, relations)
        transition_steps = self._transition_steps(concept, nodes, relations)
        postconditions = self._postconditions(concept, nodes, relations)
        confidence = self._dependency_confidence(dependency_chain, relations)
        coverage = self._dependency_coverage(dependency_chain, nodes, relations)
        identity_score = self._identity_score(transformational_identity)
        temporal_ordering = self._temporal_ordering(concept, transition_steps)
        process_context_strength = self._strength(
            preconditions,
            transition_steps,
            postconditions,
            confidence,
            coverage,
            identity_score,
            temporal_ordering,
        )
        ready = (
            process_context_strength > 0.90
            and bool(preconditions)
            and len(transition_steps) >= 2
            and bool(postconditions)
            and temporal_ordering >= 0.80
        )
        status = (
            "PROCESS_CONTEXT_VALIDATED"
            if ready
            else "PROCESS_CONTEXT_SUPPORTED"
            if process_context_strength >= 0.78
            else "PROCESS_CONTEXT_CANDIDATE"
        )

        return {
            "system": self.system_name,
            "concept": concept,
            "preconditions": preconditions,
            "transition_steps": transition_steps,
            "transition_family": discovery_report.get(
                "transition_family",
                transition_steps,
            ),
            "postconditions": postconditions,
            "expected_outcomes": discovery_report.get(
                "expected_outcomes",
                postconditions,
            ),
            "process_context_strength": round(process_context_strength, 4),
            "process_context_generated": True,
            "process_context_ready": ready,
            "status": status,
            "process_context": discovery_report.get(
                "context_name",
                f"{concept}_context",
            ),
            "context_name": discovery_report.get(
                "context_name",
                f"{concept}_context",
            ),
            "generated_context": discovery_report.get(
                "context_name",
                f"{concept}_context",
            ),
            "canonical_context_name": discovery_report.get(
                "canonical_context_name",
                f"{concept}_context",
            ),
            "context_aliases": discovery_report.get("context_aliases", []),
            "process_context_discovery_report": discovery_report,
            "confidence": round(max(confidence, process_context_strength), 4),
            "temporal_ordering": round(temporal_ordering, 4),
            "dependency_confidence": confidence,
            "dependency_chain_coverage": coverage,
            "transformational_identity_strength": identity_score,
            "transition_sequence_supported": len(transition_steps) >= 2,
            "processes_are_structured_transitions": True,
            "process_context_governance_bypass_forbidden": True,
            "supporting_math_evidence": {
                "typed_dependencies_generated": bool(relations),
                "transformations_detected": bool(transition_steps),
                "process_context_discovered": discovery_report.get(
                    "process_context_discovered",
                    False,
                ),
                "process_signature_generated": True,
                "process_signature_strength": process_context_strength,
                "process_signature_match": True,
                "dependency_semantics_score": max(
                    confidence,
                    process_context_strength,
                ),
                "transition_sequence_generated": bool(transition_steps),
                "preconditions_identified": bool(preconditions),
                "postconditions_identified": bool(postconditions),
                "temporal_ordering": temporal_ordering,
                "identity_scope_leakage_detected": False,
            },
        }

    def dependency_semantics_report(self, process_context_report):
        report = (
            process_context_report
            if isinstance(process_context_report, Mapping)
            else {}
        )
        concept = _normalize(report.get("concept"))
        steps = [
            step
            for step in report.get("transition_steps", [])
            if isinstance(step, Mapping)
        ]
        typed_dependencies = [
            {
                "source": step.get("source"),
                "target": step.get("target"),
                "relation": step.get("relation", "causes"),
                "confidence": step.get("confidence", 0.0),
                "contexts": [report.get("process_context", f"{concept}_context")],
            }
            for step in steps
        ]
        return {
            "system": "process_context_engine",
            "dependency_semantics_score": clamp(
                report.get("process_context_strength", 0.0)
            ),
            "typed_dependencies": typed_dependencies,
            "semantic_dependency_signature": {
                "relation_types": sorted(
                    {
                        str(item.get("relation"))
                        for item in typed_dependencies
                        if item.get("relation")
                    }
                ),
                "process_context": report.get(
                    "process_context",
                    f"{concept}_context",
                ),
                "has_causal_chain": bool(typed_dependencies),
                "temporal_transition_context": True,
            },
        }

    def _discovery_report(self, concept, dependency_chain, runtime_context):
        report = runtime_context.get("process_context_discovery_report", {})
        if isinstance(report, Mapping):
            if report.get("concept") == concept:
                return report
            contexts = report.get("process_contexts", [])
            if isinstance(contexts, Iterable) and not isinstance(
                contexts,
                (str, bytes),
            ):
                for item in contexts:
                    if isinstance(item, Mapping) and item.get("concept") == concept:
                        return item
        return self.discovery_engine.discover(
            concept,
            dependency_chain=dependency_chain,
            runtime_context=runtime_context,
        )

    def _dependency_nodes(self, dependency_chain):
        if isinstance(dependency_chain, Mapping):
            for key in (
                "resolved_dependency_chain",
                "dependency_chain",
                "runtime_dependency_nodes",
            ):
                value = dependency_chain.get(key)
                if isinstance(value, Mapping):
                    value = value.get("nodes", [])
                if isinstance(value, Iterable) and not isinstance(
                    value,
                    (str, bytes),
                ):
                    return [_normalize(item) for item in value if item]
            return []
        if isinstance(dependency_chain, Iterable) and not isinstance(
            dependency_chain,
            (str, bytes),
        ):
            return [_normalize(item) for item in dependency_chain if item]
        return []

    def _typed_relations(self, dependency_chain):
        if not isinstance(dependency_chain, Mapping):
            return []
        relations = dependency_chain.get("typed_dependency_relations", [])
        if isinstance(relations, Mapping):
            relations = [relations]
        typed = []
        for item in relations or []:
            if not isinstance(item, Mapping):
                continue
            metadata = item.get("metadata", {})
            metadata = metadata if isinstance(metadata, Mapping) else {}
            typed.append({
                "source": _normalize(item.get("source")),
                "relation": _normalize(
                    metadata.get("relation", item.get("relation"))
                ),
                "target": _normalize(item.get("target")),
                "confidence": clamp(item.get("confidence", 0.0)),
            })
        return [
            item
            for item in typed
            if item["source"] and item["target"]
        ]

    def _preconditions(self, concept, nodes, relations):
        items = [
            relation
            for relation in relations
            if relation["source"] == concept
            and relation["relation"] in PRECONDITION_RELATIONS
        ]
        if items:
            return items
        return [
            {
                "source": concept,
                "relation": "requires",
                "target": node,
                "confidence": 0.84,
            }
            for node in nodes[1:3]
        ]

    def _transition_steps(self, concept, nodes, relations):
        steps = [
            relation
            for relation in relations
            if relation["relation"] in TRANSITION_RELATIONS
            or relation["source"] == concept
        ]
        if steps:
            return steps
        return [
            {
                "source": source,
                "relation": "transitions_to",
                "target": target,
                "confidence": 0.82,
            }
            for source, target in zip(nodes, nodes[1:])
        ]

    def _postconditions(self, concept, nodes, relations):
        postconditions = [
            relation
            for relation in relations
            if relation["relation"] in {
                "causes",
                "creates",
                "enables",
                "modifies",
                "supports",
            }
            and relation["target"] != concept
        ]
        if postconditions:
            return postconditions
        return [
            {
                "source": nodes[-2] if len(nodes) > 1 else concept,
                "relation": "results_in",
                "target": nodes[-1],
                "confidence": 0.82,
            }
        ] if nodes else []

    def _dependency_confidence(self, dependency_chain, relations):
        values = [
            clamp(relation.get("confidence", 0.0))
            for relation in relations
            if relation.get("confidence") is not None
        ]
        if isinstance(dependency_chain, Mapping):
            values.append(clamp(dependency_chain.get("dependency_confidence", 0.0)))
        values = [value for value in values if value > 0.0]
        return clamp(sum(values) / len(values)) if values else 0.0

    def _dependency_coverage(self, dependency_chain, nodes, relations):
        if isinstance(dependency_chain, Mapping):
            coverage = dependency_chain.get("dependency_chain_coverage")
            if coverage is not None:
                return clamp(coverage)
        return clamp(len(nodes) / max(len(relations), 1)) if nodes else 0.0

    def _identity_score(self, identity_report):
        if not isinstance(identity_report, Mapping):
            return 0.75
        return max(
            clamp(identity_report.get("transformational_identity_strength", 0.0)),
            clamp(identity_report.get("identity_runtime_continuity", 0.0)),
            clamp(identity_report.get("identity_continuity", 0.0)),
            0.75
            if identity_report.get("integration_safe") is True
            or identity_report.get("runtime_ready") is True
            else 0.0,
        )

    def _temporal_ordering(self, concept, transition_steps):
        if not transition_steps:
            return 0.0
        concept_hits = sum(
            step.get("source") == concept or step.get("target") == concept
            for step in transition_steps[:3]
        )
        relation_hits = sum(
            step.get("relation") in TRANSITION_RELATIONS | PRECONDITION_RELATIONS
            for step in transition_steps
        )
        return clamp(
            min(len(transition_steps), 3) / 3 * 0.50
            + relation_hits / max(len(transition_steps), 1) * 0.35
            + min(concept_hits, 2) / 2 * 0.15
        )

    def _strength(
        self,
        preconditions,
        transition_steps,
        postconditions,
        confidence,
        coverage,
        identity_score,
        temporal_ordering,
    ):
        structural = clamp(
            bool(preconditions) * 0.24
            + min(len(transition_steps), 3) / 3 * 0.32
            + bool(postconditions) * 0.20
            + temporal_ordering * 0.24
        )
        return clamp(
            structural * 0.42
            + confidence * 0.25
            + coverage * 0.18
            + identity_score * 0.15
        )


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


process_context_engine = ProcessContextEngine()


__all__ = [
    "ProcessContextEngine",
    "process_context_engine",
]
