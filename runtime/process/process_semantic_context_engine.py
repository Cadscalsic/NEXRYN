"""Alpha 1.1 Process Semantic Cognition layer."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from runtime.process.process_context_discovery import ProcessContextDiscovery
from runtime.process.process_context_registry import (
    ProcessContext,
    ProcessContextRegistry,
)
from runtime.process.process_context_validator import ProcessContextValidator
from runtime.process.process_dependency_ingestion import (
    ProcessDependencyIngestion,
)
from runtime.process.process_dependency_reasoner import (
    ProcessDependencyReasoner,
)
from runtime.process.process_dependency_validator import (
    ProcessDependencyValidator,
)
from runtime.process.process_strength_estimator import ProcessStrengthEstimator
from runtime.process.process_state_model import ProcessSemanticContext
from runtime.process.process_transition_graph import ProcessTransitionGraph


class ProcessSemanticContextEngine:
    """Discover, validate, register, and expose semantic process contexts."""

    system_name = "alpha_1_1_process_semantic_context_engine"

    def __init__(
        self,
        discovery: ProcessContextDiscovery | None = None,
        validator: ProcessContextValidator | None = None,
        strength_estimator: ProcessStrengthEstimator | None = None,
        registry: ProcessContextRegistry | None = None,
        dependency_ingestion: ProcessDependencyIngestion | None = None,
        dependency_validator: ProcessDependencyValidator | None = None,
        dependency_reasoner: ProcessDependencyReasoner | None = None,
        transition_graph: ProcessTransitionGraph | None = None,
    ):
        self.discovery = discovery or ProcessContextDiscovery()
        self.validator = validator or ProcessContextValidator()
        self.strength_estimator = strength_estimator or ProcessStrengthEstimator()
        self.registry = registry or ProcessContextRegistry()
        self.dependency_ingestion = (
            dependency_ingestion or ProcessDependencyIngestion()
        )
        self.dependency_validator = (
            dependency_validator or ProcessDependencyValidator()
        )
        self.dependency_reasoner = dependency_reasoner or ProcessDependencyReasoner()
        self.transition_graph = transition_graph or ProcessTransitionGraph()

    def synthesize(
        self,
        concept: str,
        dependency_chain: list[str] | Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        dependency_chain = dependency_chain or runtime_context.get(
            "process_dependency_memory",
            runtime_context.get("resolved_dependency_chain", []),
        )
        discovery = self.discovery.discover(concept, dependency_chain)
        if not discovery.get("process_context_discovered"):
            return {
                **discovery,
                "process_context_ready": False,
                "governance_visible": False,
            }
        typed_dependency_report = self._typed_dependency_report(
            concept,
            discovery,
            runtime_context,
        )
        typed_dependency_validation = self.dependency_validator.validate(
            typed_dependency_report
        )
        typed_dependency_reasoning = self.dependency_reasoner.reason(
            str(concept),
            typed_dependency_report,
            observed_contradictions=runtime_context.get(
                "observed_contradictions",
                runtime_context.get("contradictions", []),
            ),
        )

        dependency_confidence = max(
            clamp(runtime_context.get("dependency_confidence", 0.0)),
            clamp(runtime_context.get("promotion_dependency_score", 0.0)),
            clamp(typed_dependency_report.get("dependency_confidence", 0.0)),
            clamp(
                typed_dependency_report.get(
                    "dependency_coherence_average",
                    typed_dependency_report.get("dependency_coherence", 0.0),
                )
            ),
        )
        dependency_semantics_score = clamp(
            typed_dependency_reasoning.get(
                "dependency_semantics_score",
                dependency_confidence,
            )
        )
        identity_continuity = clamp(
            runtime_context.get(
                "identity_runtime_continuity",
                runtime_context.get(
                    "identity_continuity",
                    runtime_context.get(
                        "identity_strength",
                        runtime_context.get("identity_safe_truth_integration", {}).get(
                            "identity_continuity",
                            0.0,
                        )
                        if isinstance(
                            runtime_context.get("identity_safe_truth_integration"),
                            Mapping,
                        )
                        else 0.0,
                    ),
                ),
            )
        )
        if identity_continuity == 0.0 and dependency_confidence >= 0.80:
            identity_continuity = 0.90
        causal_alignment = max(
            clamp(runtime_context.get("causal_alignment", 0.0)),
            clamp(runtime_context.get("causal_stability", 0.0)),
            clamp(runtime_context.get("promotion_dependency_score", 0.0)),
            dependency_semantics_score,
        )
        contradiction_score = clamp(runtime_context.get("contradiction_score", 0.0))

        strength = self.strength_estimator.estimate(
            discovery,
            dependency_confidence=dependency_confidence,
            causal_alignment=causal_alignment,
            identity_continuity=identity_continuity,
        )
        validation = self.validator.validate(
            discovery,
            identity_continuity=identity_continuity,
            causal_alignment=causal_alignment,
            contradiction_score=contradiction_score,
        )
        context = ProcessContext(
            name=str(discovery["context_name"]),
            process_family=str(discovery["process_family"]),
            concept=str(concept),
            preconditions=list(discovery["preconditions"]),
            transition_signature=list(discovery["transition_signature"]),
            postconditions=list(discovery["postconditions"]),
            invariants=list(discovery["invariants"]),
            dependency_links=[
                item.get("target", "")
                for item in typed_dependency_report.get(
                    "typed_dependency_relations",
                    [],
                )
                if item.get("target")
            ] or list(discovery["dependency_links"]),
            temporal_signature=dict(discovery["temporal_signature"]),
            context_strength=strength["process_context_strength"],
            identity_continuity=identity_continuity,
            causal_alignment=causal_alignment,
            constraints=list(discovery.get("constraints", [])),
        )
        registered = self.registry.register(context)
        semantic_context = ProcessSemanticContext(
            concept=str(concept),
            preconditions=list(discovery["preconditions"]),
            transition_steps=list(discovery["transition_signature"]),
            postconditions=list(discovery["postconditions"]),
            invariants=list(discovery["invariants"]),
            temporal_constraints=[
                "temporal_reasoning_disabled",
                *list(discovery.get("constraints", [])),
            ],
            context_strength=strength["process_context_strength"],
        )
        semantic_context_report = semantic_context.as_dict()
        transition_graph_report = self.transition_graph.build(
            semantic_context,
        )
        report = {
            **registered,
            "system": self.system_name,
            "process_semantic_context":
            semantic_context_report,
            "state_transition_graph":
            transition_graph_report,
            "initial_state":
            transition_graph_report["initial_state"],
            "transition_steps":
            semantic_context_report["transition_steps"],
            "final_state":
            transition_graph_report["final_state"],
            "temporal_constraints":
            semantic_context_report["temporal_constraints"],
            "process_semantic_context_synthesized": True,
            "process_context_discovery_report": discovery,
            "process_context_validation_report": validation,
            "process_context_strength_report": strength,
            "typed_dependency_report": typed_dependency_report,
            "typed_dependency_validation_report":
            typed_dependency_validation,
            "typed_dependency_reasoning_report": typed_dependency_reasoning,
            "typed_process_dependencies": "enabled",
            "process_dependency_links_used":
            typed_dependency_report.get("process_dependency_links_used", 0),
            "process_dependency_links_loaded":
            typed_dependency_report.get("process_dependency_links_loaded", 0),
            "process_dependency_relevance_rate":
            typed_dependency_reasoning.get(
                "process_dependency_relevance_rate",
                0.0,
            ),
            "process_dependency_links_used_above_threshold":
            typed_dependency_reasoning.get(
                "process_dependency_links_used_above_threshold",
                False,
            ),
            "exact_blocker":
            typed_dependency_reasoning.get("exact_blocker", []),
            "process_context_ready": bool(
                registered.get("process_context_ready")
                and validation.get("process_context_ready")
                and typed_dependency_validation.get(
                    "typed_dependency_validation_passed"
                )
                and not typed_dependency_reasoning.get("exact_blocker")
            ),
            "truth_candidate_blocked_by_context": not bool(
                registered.get("process_context_strength", 0.0) > 0.80
                and registered.get("process_context_ready")
            ),
            "governance_visible": bool(
                registered.get("governance_visible")
                and validation.get("governance_visible")
            ),
            "process_context_report": self._log_report(registered, validation),
        }
        return report

    def discover_all(
        self,
        runtime_contexts: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_contexts = runtime_contexts if isinstance(runtime_contexts, Mapping) else {}
        concepts = (
            "growth",
            "propagation",
            "replication",
            "directional_motion",
            "topological_growth",
        )
        reports = [
            self.synthesize(
                concept,
                runtime_context=runtime_contexts.get(concept, runtime_contexts),
            )
            for concept in concepts
        ]
        ready = [
            report for report in reports if report.get("process_context_ready")
        ]
        strengths = [
            report.get("process_context_strength", 0.0)
            for report in reports
        ]
        return {
            "system": self.system_name,
            "process_contexts": reports,
            "process_context_count": len(reports),
            "process_context_coverage": (
                round(len(ready) / len(concepts), 4)
                if concepts
                else 1.0
            ),
            "process_context_registration_rate": (
                round(len(ready) / len(reports), 4) if reports else 1.0
            ),
            "average_process_context_strength": (
                round(sum(strengths) / len(strengths), 4)
                if strengths
                else 0.0
            ),
            "ready_contexts": [
                report.get("context_name") for report in ready
            ],
            "discovered_contexts": [
                report.get("context_name")
                for report in reports
                if report.get("process_context_generated")
            ],
            "truth_candidate_blocked_by_context": any(
                report.get("truth_candidate_blocked_by_context", True)
                for report in reports
            ),
            **{
                f"{concept}_context_discovered": any(
                    report.get("context_name") == f"{concept}_context"
                    and report.get("process_context_generated")
                    for report in reports
                )
                for concept in concepts
            },
        }

    def get_process_context(self, name: str) -> dict[str, Any]:
        return self.registry.get(name)

    def registry_report(self) -> dict[str, Any]:
        return self.registry.report()

    def _typed_dependency_report(self, concept, discovery, runtime_context):
        existing = runtime_context.get("typed_dependency_report", {})
        if isinstance(existing, Mapping) and existing.get(
            "typed_process_dependencies_enabled"
        ):
            return dict(existing)
        existing_memory = runtime_context.get("process_dependency_memory", {})
        if isinstance(existing_memory, Mapping) and existing_memory.get(
            "typed_dependency_relations"
        ):
            links = existing_memory.get("typed_dependency_relations", [])
            return {
                **dict(existing_memory),
                "typed_process_dependencies": "enabled",
                "typed_process_dependencies_enabled": True,
                "typed_dependency_relations": links,
                "process_dependency_links_used": len(links),
                "relevant_process_dependency_links": len(links),
            }
        relevant_targets = [
            *discovery.get("preconditions", []),
            *discovery.get("transition_signature", []),
            *discovery.get("postconditions", []),
            *discovery.get("invariants", []),
            *discovery.get("constraints", []),
        ]
        return self.dependency_ingestion.resolve_for_process(
            str(concept),
            relevant_targets=relevant_targets,
            observed_contradictions=runtime_context.get(
                "observed_contradictions",
                runtime_context.get("contradictions", []),
            ),
        )

    def _log_report(self, context, validation):
        return (
            "PROCESS CONTEXT REPORT\n"
            f"concept = {context.get('concept')}\n"
            f"context_name = {context.get('context_name')}\n"
            f"process_family = {context.get('process_family')}\n"
            f"preconditions = {context.get('preconditions')}\n"
            "transition_signature = "
            f"{context.get('transition_signature')}\n"
            f"postconditions = {context.get('postconditions')}\n"
            f"invariants = {context.get('invariants')}\n"
            f"state_transition_graph = {context.get('state_transition_graph', {})}\n"
            f"context_strength = {context.get('process_context_strength')}\n"
            f"governance_visible = {validation.get('governance_visible')}\n"
        )


__all__ = [
    "ProcessContext",
    "ProcessSemanticContext",
    "ProcessSemanticContextEngine",
]
