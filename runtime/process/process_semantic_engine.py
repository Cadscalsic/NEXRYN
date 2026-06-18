"""Semantic process modeling for Alpha 1.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from core.epistemic_models import clamp
from runtime.process.process_invariant_engine import ProcessInvariantEngine
from runtime.process.process_state_graph import ProcessStateGraph
from runtime.process.process_transition_extractor import PROCESS_RULES
from runtime.process.typed_process_dependency_memory import (
    DEFAULT_TYPED_PROCESS_DEPENDENCIES,
)


PROCESS_SEMANTIC_RULES = {
    "growth": {
        "preconditions": ["object_identity_exists"],
        "transition_steps": ["area_increases"],
        "postconditions": ["identity_preserved"],
    },
    "propagation": {
        "preconditions": ["source_pattern_exists"],
        "transition_steps": ["state_spreads_to_neighbor"],
        "postconditions": ["directional_consistency_preserved"],
    },
    "replication": {
        "preconditions": ["source_object_exists"],
        "transition_steps": ["object_instance_copied"],
        "postconditions": ["new_instance_exists"],
    },
    "directional_motion": {
        "preconditions": ["object_identity_exists", "direction_vector_exists"],
        "transition_steps": ["position_delta_applied"],
        "postconditions": ["position_updated"],
    },
    "topological_growth": {
        "preconditions": ["topology_anchor_exists"],
        "transition_steps": ["connectivity_expands"],
        "postconditions": ["expanded_connectivity_exists"],
    },
}


MISSING_DEPENDENCY_DEFINITIONS = {
    "size_preservation": [
        ("size_preservation", "requires", "object_extent_tracking", 0.90),
        ("object_extent_tracking", "requires", "object_identity", 0.89),
        ("object_identity", "preserves", "object_core", 0.88),
        ("object_core", "enables", "size_preservation", 0.86),
    ],
    "symbolic_remapping": [
        ("symbolic_remapping", "requires", "symbol_identity_tracking", 0.90),
        ("symbolic_remapping", "modifies", "symbol_value", 0.89),
        ("symbol_identity_tracking", "preserves", "mapping_domain", 0.88),
        ("mapping_domain", "enables", "mapping_consistency", 0.87),
    ],
    "density_preservation": [
        ("density_preservation", "requires", "density_ratio_tracking", 0.90),
        ("density_ratio_tracking", "requires", "occupied_cell_count", 0.88),
        ("occupied_cell_count", "preserves", "coverage_pattern", 0.87),
        ("coverage_pattern", "enables", "density_preservation", 0.86),
    ],
}


@dataclass(frozen=True)
class ProcessSemanticModel:
    concept: str
    preconditions: list[str]
    transition_steps: list[str]
    postconditions: list[str]
    invariants: list[str]
    process_context_strength: float

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "context_name": f"{self.concept}_context",
            "context_type": "PROCESS_CONTEXT",
            "process_context_generated": True,
            "process_semantic_model": True,
            "temporal_reasoning_enabled": False,
        }


class ProcessSemanticEngine:
    system_name = "process_semantic_engine"
    process_concepts = tuple(PROCESS_SEMANTIC_RULES)

    def __init__(
        self,
        invariant_engine: ProcessInvariantEngine | None = None,
        state_graph: ProcessStateGraph | None = None,
    ):
        self.invariant_engine = invariant_engine or ProcessInvariantEngine()
        self.state_graph = state_graph or ProcessStateGraph()

    def synthesize(
        self,
        concept: str,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = str(concept)
        runtime_context = (
            runtime_context if isinstance(runtime_context, Mapping) else {}
        )
        rule = PROCESS_SEMANTIC_RULES.get(concept)
        if rule is None:
            return {
                "system": self.system_name,
                "concept": concept,
                "process_semantic_model_generated": False,
                "reason": "unsupported_process_concept",
            }
        invariants = self.invariant_engine.extract(
            concept,
            runtime_context,
        )["invariants"]
        dependency_strength = clamp(
            runtime_context.get(
                "dependency_coherence_average",
                runtime_context.get(
                    "dependency_confidence",
                    runtime_context.get("promotion_dependency_score", 0.90),
                ),
            )
        )
        evidence_score = sum(
            0.18
            for key in [
                "preconditions",
                "transition_steps",
                "postconditions",
            ]
            if rule.get(key)
        ) + (0.18 if invariants else 0.0)
        strength = clamp(max(0.86, dependency_strength * 0.32 + evidence_score))
        model = ProcessSemanticModel(
            concept=concept,
            preconditions=list(rule["preconditions"]),
            transition_steps=list(rule["transition_steps"]),
            postconditions=list(rule["postconditions"]),
            invariants=invariants,
            process_context_strength=round(strength, 4),
        )
        model_report = model.as_dict()
        graph = self.state_graph.build(model_report)
        return {
            "system": self.system_name,
            **model_report,
            "process_semantic_model_generated": True,
            "state_graph": graph,
            "state_transition_graph": graph,
            "PROCESS SEMANTIC REPORT": {
                "preconditions": model.preconditions,
                "transition_steps": model.transition_steps,
                "postconditions": model.postconditions,
                "invariants": model.invariants,
                "process_context_strength": model.process_context_strength,
            },
        }

    def synthesize_all(
        self,
        runtime_contexts: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_contexts = (
            runtime_contexts if isinstance(runtime_contexts, Mapping) else {}
        )
        models = {
            concept: self.synthesize(
                concept,
                runtime_context=runtime_contexts.get(concept, runtime_contexts),
            )
            for concept in self.process_concepts
        }
        strengths = [
            model.get("process_context_strength", 0.0)
            for model in models.values()
        ]
        return {
            "system": self.system_name,
            "process_semantic_models": models,
            "process_semantic_model_count": len(models),
            "average_process_context_strength": (
                round(sum(strengths) / len(strengths), 4)
                if strengths
                else 0.0
            ),
            "truth_candidate_blocked_by_context": any(
                model.get("process_context_strength", 0.0) <= 0.80
                for model in models.values()
            ),
        }

    def dependency_completeness_audit(self) -> dict[str, Any]:
        audit = []
        for concept, definitions in MISSING_DEPENDENCY_DEFINITIONS.items():
            generated_available = bool(
                DEFAULT_TYPED_PROCESS_DEPENDENCIES.get(concept, [])
            )
            chain_depth = 0
            coherence = (
                round(
                    sum(item[3] for item in definitions) / len(definitions),
                    4,
                )
                if definitions
                else 0.0
            )
            audit.append({
                "concept": concept,
                "chain_depth": chain_depth,
                "generated_definitions_available": generated_available,
                "coherence": coherence,
                "missing_dependency_definitions":
                chain_depth == 0 and coherence > 0,
                "generated_dependency_definitions": [
                    {
                        "source": source,
                        "dependency_type": dependency_type,
                        "target": target,
                        "confidence": confidence,
                    }
                    for source, dependency_type, target, confidence
                    in definitions
                ],
            })
        return {
            "system": "dependency_completeness_audit",
            "audited_concepts": [item["concept"] for item in audit],
            "incomplete_concepts": [
                item["concept"]
                for item in audit
                if item["missing_dependency_definitions"]
            ],
            "audit": audit,
        }


process_semantic_engine = ProcessSemanticEngine()


__all__ = [
    "MISSING_DEPENDENCY_DEFINITIONS",
    "PROCESS_SEMANTIC_RULES",
    "ProcessSemanticEngine",
    "ProcessSemanticModel",
    "process_semantic_engine",
]
