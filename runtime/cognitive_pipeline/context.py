"""Shared cognitive context enriched by solver pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CognitiveContext:
    task: Any = None
    input_grid: Any = None
    output_grid: Any = None
    rules: list[dict[str, Any]] = field(default_factory=list)
    perceived_objects: list[Any] = field(default_factory=list)
    relationships: list[Any] = field(default_factory=list)
    concept_graph: dict[str, Any] = field(default_factory=dict)
    hypotheses: list[Any] = field(default_factory=list)
    transformations: list[Any] = field(default_factory=list)
    candidate_programs: list[Any] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    evidence: list[Any] = field(default_factory=list)
    constraints: list[Any] = field(default_factory=list)
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    reasoning_history: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[Any] = field(default_factory=list)
    knowledge_candidates: list[Any] = field(default_factory=list)
    stage_events: list[dict[str, Any]] = field(default_factory=list)
    stage_snapshots: list[dict[str, Any]] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    solution: Any = None
    final_output: Any = None

    def add_concept(self, concept_id: str, payload: Any = True) -> None:
        self.concept_graph.setdefault("concepts", {})[concept_id] = payload

    def snapshot(self) -> dict[str, Any]:
        return {
            "perceived_objects": len(self.perceived_objects),
            "relationships": len(self.relationships),
            "concepts": len(self.concept_graph.get("concepts", {})),
            "hypotheses": len(self.hypotheses),
            "transformations": len(self.transformations),
            "candidate_programs": len(self.candidate_programs),
            "confidence_scores": dict(self.confidence_scores),
            "evidence": len(self.evidence),
            "constraints": len(self.constraints),
            "validation_results": len(self.validation_results),
            "knowledge_candidates": len(self.knowledge_candidates),
            "trace": list(self.trace),
        }


__all__ = ["CognitiveContext"]
