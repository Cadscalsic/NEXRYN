"""Shared process-context data models and pure helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from core.epistemic_models import clamp


@dataclass
class ProcessContext:
    """Lightweight process-context model shared across runtime layers."""

    name: str = ""
    process_family: str = ""
    preconditions: list[str] = field(default_factory=list)
    transition_signature: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    dependency_links: list[str] = field(default_factory=list)
    temporal_signature: dict[str, Any] = field(default_factory=dict)
    context_strength: float = 0.0
    identity_continuity: float = 0.0
    causal_alignment: float = 0.0
    concept: str = ""
    constraints: list[str] = field(default_factory=list)
    process_id: str = ""
    source_graph: dict[str, Any] = field(default_factory=dict)
    initial_state: dict[str, Any] = field(default_factory=dict)
    intermediate_states: list[dict[str, Any]] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)
    transition_sequence: list[str] = field(default_factory=list)
    expected_outcomes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    transition_events: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    transition_confidence: float = 0.0
    state_confidence: float = 0.0
    process_confidence: float = 0.0
    support_score: float = 0.0
    contradiction_score: float = 0.0
    validation: dict[str, Any] = field(default_factory=dict)
    simulation: dict[str, Any] = field(default_factory=dict)
    reuse_hit: bool = False

    @property
    def governance_visible(self) -> bool:
        return bool(
            self.context_strength >= 0.85
            and self.identity_continuity >= 0.85
            and self.causal_alignment >= 0.85
        )

    @property
    def ready(self) -> bool:
        return bool(self.governance_visible and self.dependency_links)

    def compact_dict(self) -> dict[str, Any]:
        return {
            "context_name": self.name or self.process_id,
            "concept": self.concept,
            "process_family": self.process_family,
            "context_type": "PROCESS_CONTEXT",
            "process_context_strength": clamp(self.context_strength),
            "identity_continuity": clamp(self.identity_continuity),
            "causal_alignment": clamp(self.causal_alignment),
            "governance_visible": self.governance_visible,
            "process_context_ready": self.ready,
            "dependency_link_count": len(self.dependency_links),
            "transition_count": len(self.transition_signature),
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if self.ready
                else "PROCESS_CONTEXT_SUPPORTED"
            ),
        }

    def as_dict(self, compact: bool = False) -> dict[str, Any]:
        if compact:
            return self.compact_dict()

        data = asdict(self)
        data.update(
            {
                "context_name": self.name or self.process_id,
                "context_type": "PROCESS_CONTEXT",
                "process_context": self.name or self.process_id,
                "transition_steps": list(self.transition_signature or self.transition_sequence),
                "transitions": list(self.transition_signature or self.transition_sequence),
                "temporal_constraints": list(self.constraints),
                "process_context_strength": clamp(self.context_strength),
                "context_confidence": clamp(self.context_strength),
                "confidence": clamp(self.context_strength),
                "semantic_validation": True,
                "identity_compatible": self.identity_continuity >= 0.85,
                "governance_visible": self.governance_visible,
                "process_context_generated": True,
                "process_context_ready": self.ready,
                "status": (
                    "PROCESS_CONTEXT_VALIDATED"
                    if self.ready
                    else "PROCESS_CONTEXT_SUPPORTED"
                ),
                "supporting_math_evidence": {
                    "typed_dependencies_generated": bool(self.dependency_links),
                    "process_signature_generated": True,
                    "process_signature_match": True,
                    "process_signature_strength": clamp(self.context_strength),
                    "transition_sequence_generated": bool(self.transition_signature or self.transition_sequence),
                    "preconditions_identified": bool(self.preconditions),
                    "postconditions_identified": bool(self.postconditions),
                    "temporal_state_sequence_generated": bool(
                        self.preconditions
                        and (self.transition_signature or self.transition_sequence)
                        and self.postconditions
                    ),
                    "final_state_identified": bool(self.postconditions),
                    "dependency_semantics_score": clamp(self.context_strength),
                    "identity_scope_leakage_detected": False,
                },
            }
        )
        data.setdefault("process_depth", len(self.transition_sequence or self.transition_signature))
        data.setdefault("state_count", 2 + len(self.intermediate_states))
        data.setdefault("process_context_confidence", data.get("confidence", 0.0))
        return data


def process_context_from_mapping(data: Mapping[str, Any]) -> ProcessContext:
    """Create a ProcessContext from a mapping without importing runtime subsystems."""

    data = data if isinstance(data, Mapping) else {}
    transition_signature = list(
        data.get(
            "transition_signature",
            data.get("transition_steps", data.get("transitions", data.get("causal_sequence", []))),
        )
        or []
    )
    transition_sequence = list(data.get("transition_sequence", transition_signature) or [])
    preconditions = list(data.get("preconditions", []) or [])
    postconditions = list(data.get("postconditions", []) or [])
    invariants = list(data.get("invariants", []) or [])
    dependency_links = list(data.get("dependency_links", []) or [])
    context_strength = clamp(
        data.get("context_strength", data.get("process_context_strength", 0.0))
    )
    identity_continuity = clamp(data.get("identity_continuity", 0.0))
    causal_alignment = clamp(data.get("causal_alignment", 0.0))
    return ProcessContext(
        name=str(data.get("name") or data.get("context_name") or data.get("process_id") or ""),
        process_family=str(
            data.get("process_family")
            or data.get("concept")
            or data.get("context_name", "").replace("_context", "")
        ),
        preconditions=preconditions,
        transition_signature=transition_signature,
        postconditions=postconditions,
        invariants=invariants,
        dependency_links=dependency_links,
        temporal_signature=dict(data.get("temporal_signature", {}) or {}),
        context_strength=context_strength,
        identity_continuity=identity_continuity,
        causal_alignment=causal_alignment,
        concept=str(data.get("concept", "")),
        constraints=list(data.get("constraints", []) or []),
        process_id=str(data.get("process_id") or data.get("name") or data.get("context_name") or ""),
        source_graph=dict(data.get("source_graph", {}) or {}),
        initial_state=dict(data.get("initial_state", {}) or {}),
        intermediate_states=list(data.get("intermediate_states", []) or []),
        final_state=dict(data.get("final_state", {}) or {}),
        transition_sequence=transition_sequence,
        expected_outcomes=list(data.get("expected_outcomes", []) or []),
        confidence=clamp(data.get("confidence", context_strength)),
        transition_events=list(data.get("transition_events", []) or []),
        dependencies=list(data.get("dependencies", []) or []),
        transition_confidence=clamp(data.get("transition_confidence", 0.0)),
        state_confidence=clamp(data.get("state_confidence", 0.0)),
        process_confidence=clamp(data.get("process_confidence", context_strength)),
        support_score=clamp(data.get("support_score", 0.0)),
        contradiction_score=clamp(data.get("contradiction_score", 0.0)),
        validation=dict(data.get("validation", {}) or {}),
        simulation=dict(data.get("simulation", {}) or {}),
        reuse_hit=bool(data.get("reuse_hit", False)),
    )


def normalize_context_name(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


__all__ = [
    "ProcessContext",
    "process_context_from_mapping",
    "normalize_context_name",
]
