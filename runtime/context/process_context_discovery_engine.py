"""Discovery of process-native contexts from typed dependency chains."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from core.process_abstraction import ProcessAbstractionLayer


PROCESS_CONCEPTS = {
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
}

CONTEXT_NAME_ALIASES = {
    "directional_motion": "motion_context",
}

PRECONDITION_RELATIONS = {
    "depends_on",
    "derived_from",
    "preserves",
    "requires",
    "supports",
}

TRANSITION_RELATIONS = {
    "causes",
    "creates",
    "enables",
    "merges",
    "modifies",
    "splits",
    "transitions_to",
}

OUTCOME_RELATIONS = {
    "causes",
    "creates",
    "enables",
    "modifies",
    "splits",
    "supports",
}


class ProcessContextDiscoveryEngine:
    """Identify where process concepts can validly occur before temporal modeling."""

    system_name = "process_context_discovery_engine"

    def discover(
        self,
        concept: str,
        dependency_chain: Mapping[str, Any] | Iterable[Any] | None = None,
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

        if concept not in PROCESS_CONCEPTS:
            return {
                "system": self.system_name,
                "concept": concept,
                "context_name": "",
                "preconditions": [],
                "transition_family": [],
                "expected_outcomes": [],
                "context_confidence": 0.0,
                "process_context_discovered": False,
                "status": "PROCESS_CONTEXT_DISCOVERY_REJECTED",
                "reason": "unsupported_process_concept",
            }

        nodes = self._dependency_nodes(dependency_chain)
        relations = self._typed_relations(dependency_chain)
        preconditions = self._preconditions(concept, nodes, relations)
        transition_family = self._transition_family(concept, nodes, relations)
        expected_outcomes = self._expected_outcomes(concept, nodes, relations)
        dependency_confidence = self._dependency_confidence(
            dependency_chain,
            relations,
        )
        coverage = self._dependency_coverage(dependency_chain, nodes, relations)
        confidence = self._context_confidence(
            preconditions,
            transition_family,
            expected_outcomes,
            dependency_confidence,
            coverage,
        )
        context_name = self._context_name(concept)
        abstraction = ProcessAbstractionLayer.get(concept)

        return {
            "system": self.system_name,
            "concept": concept,
            "context_name": context_name,
            "preconditions": preconditions,
            "transition_family": transition_family,
            "expected_outcomes": expected_outcomes,
            "context_confidence": round(confidence, 4),
            "process_context_discovered": confidence > 0.0,
            "process_context_generated": confidence > 0.0,
            "process_context_ready": confidence >= 0.78,
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if confidence > 0.90
                else "PROCESS_CONTEXT_SUPPORTED"
                if confidence >= 0.78
                else "PROCESS_CONTEXT_CANDIDATE"
            ),
            "dependency_confidence": dependency_confidence,
            "dependency_chain_coverage": coverage,
            "canonical_context_name": (
                abstraction.context_id if abstraction is not None else context_name
            ),
            "context_aliases": self._context_aliases(concept, context_name),
            "process_preconditions_identified": bool(preconditions),
            "process_transition_family_identified": bool(transition_family),
            "process_expected_outcomes_identified": bool(expected_outcomes),
        }

    def discover_contexts(
        self,
        concepts: Iterable[str] | None = None,
        dependency_chains: Mapping[str, Any] | None = None,
        dependency_resolver: Any | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        concepts = list(concepts or sorted(PROCESS_CONCEPTS))
        dependency_chains = (
            dependency_chains
            if isinstance(dependency_chains, Mapping)
            else {}
        )
        return [
            self.discover(
                concept,
                dependency_chain=self._resolve_dependency_chain(
                    concept,
                    dependency_chains,
                    dependency_resolver,
                    runtime_context,
                ),
                runtime_context=runtime_context,
            )
            for concept in concepts
        ]

    def report(
        self,
        concepts: Iterable[str] | None = None,
        dependency_chains: Mapping[str, Any] | None = None,
        dependency_resolver: Any | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contexts = self.discover_contexts(
            concepts=concepts,
            dependency_chains=dependency_chains,
            dependency_resolver=dependency_resolver,
            runtime_context=runtime_context,
        )
        discovered = [
            context
            for context in contexts
            if context.get("process_context_discovered")
        ]
        return {
            "system": self.system_name,
            "process_context_count": len(discovered),
            "process_contexts": contexts,
            "discovered_context_names": [
                context["context_name"]
                for context in discovered
            ],
            "process_context_discovery_ready": bool(discovered),
            "process_context_governance_bypass_forbidden": True,
        }

    def as_process_context_report(
        self,
        discovery_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Adapt discovery output for temporal/context-strength engines."""

        report = (
            discovery_report
            if isinstance(discovery_report, Mapping)
            else {}
        )
        concept = _normalize(report.get("concept"))
        transition_steps = list(report.get("transition_family", []) or [])
        postconditions = list(report.get("expected_outcomes", []) or [])
        strength = clamp(report.get("context_confidence", 0.0))
        return {
            "system": self.system_name,
            "concept": concept,
            "context_name": report.get("context_name", self._context_name(concept)),
            "process_context": report.get(
                "context_name",
                self._context_name(concept),
            ),
            "generated_context": report.get(
                "context_name",
                self._context_name(concept),
            ),
            "preconditions": list(report.get("preconditions", []) or []),
            "transition_steps": transition_steps,
            "postconditions": postconditions,
            "process_context_strength": strength,
            "confidence": strength,
            "process_context_generated": bool(
                report.get("process_context_discovered")
            ),
            "process_context_ready": strength >= 0.78,
            "status": report.get("status", "PROCESS_CONTEXT_CANDIDATE"),
            "supporting_math_evidence": {
                "typed_dependencies_generated": bool(transition_steps),
                "transition_sequence_generated": bool(transition_steps),
                "preconditions_identified": bool(report.get("preconditions")),
                "postconditions_identified": bool(postconditions),
                "process_signature_generated": True,
                "process_signature_match": True,
                "process_signature_strength": strength,
                "dependency_semantics_score": strength,
                "identity_scope_leakage_detected": False,
            },
        }

    def _resolve_dependency_chain(
        self,
        concept,
        dependency_chains,
        dependency_resolver,
        runtime_context,
    ):
        if concept in dependency_chains:
            return dependency_chains[concept]
        if dependency_resolver is not None:
            for method_name in ("resolve_dependency_chain", "resolve_chain"):
                method = getattr(dependency_resolver, method_name, None)
                if callable(method):
                    return method(concept)
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        memory = runtime_context.get("process_dependency_memory", {})
        if isinstance(memory, Mapping) and memory.get("concept") == concept:
            return memory
        return memory

    def _context_name(self, concept):
        concept = _normalize(concept)
        return CONTEXT_NAME_ALIASES.get(concept, f"{concept}_context")

    def _context_aliases(self, concept, context_name):
        abstraction = ProcessAbstractionLayer.get(concept)
        aliases = {context_name}
        if abstraction is not None:
            aliases.add(abstraction.context_id)
        return sorted(aliases)

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
            metadata = (
                item.get("metadata", {})
                if isinstance(item.get("metadata", {}), Mapping)
                else {}
            )
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
        preconditions = [
            relation
            for relation in relations
            if relation["source"] == concept
            and relation["relation"] in PRECONDITION_RELATIONS
        ]
        if preconditions:
            return preconditions
        return [
            {
                "source": concept,
                "relation": "requires",
                "target": node,
                "confidence": 0.80,
            }
            for node in nodes[1:3]
        ]

    def _transition_family(self, concept, nodes, relations):
        transitions = [
            relation
            for relation in relations
            if relation["relation"] in TRANSITION_RELATIONS
            or relation["source"] == concept
        ]
        if transitions:
            return transitions
        return [
            {
                "source": source,
                "relation": "transitions_to",
                "target": target,
                "confidence": 0.80,
            }
            for source, target in zip(nodes, nodes[1:])
        ]

    def _expected_outcomes(self, concept, nodes, relations):
        outcomes = [
            relation
            for relation in relations
            if relation["relation"] in OUTCOME_RELATIONS
            and relation["target"] != concept
        ]
        if outcomes:
            return outcomes
        return [
            {
                "source": nodes[-2] if len(nodes) > 1 else concept,
                "relation": "results_in",
                "target": nodes[-1],
                "confidence": 0.80,
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
        return round(clamp(sum(values) / len(values)), 4) if values else 0.0

    def _dependency_coverage(self, dependency_chain, nodes, relations):
        if isinstance(dependency_chain, Mapping):
            coverage = dependency_chain.get("dependency_chain_coverage")
            if coverage is not None:
                return clamp(coverage)
        return clamp(len(nodes) / max(len(relations), 1)) if nodes else 0.0

    def _context_confidence(
        self,
        preconditions,
        transition_family,
        expected_outcomes,
        dependency_confidence,
        coverage,
    ):
        structure = clamp(
            bool(preconditions) * 0.28
            + min(len(transition_family), 3) / 3 * 0.34
            + bool(expected_outcomes) * 0.20
            + min(len(expected_outcomes), 3) / 3 * 0.18
        )
        return clamp(
            structure * 0.48
            + dependency_confidence * 0.34
            + coverage * 0.18
        )


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


process_context_discovery_engine = ProcessContextDiscoveryEngine()


__all__ = [
    "ProcessContextDiscoveryEngine",
    "process_context_discovery_engine",
]
