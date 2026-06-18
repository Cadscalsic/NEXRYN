"""Executable dependency-chain data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReasonedDependencyChain:
    concept: str
    dependency_graph: dict[str, Any]
    dependencies: list[str]
    dependency_types: list[str]
    chain_depth: int
    coverage: float
    coherence: float
    causal_alignment: float
    contradictions: list[str] = field(default_factory=list)
    explanation_path: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "reasoned_dependency_chain": True,
            "chain": list(self.dependencies),
            "resolved_dependency_chain": list(self.dependencies),
            "dependency_chain_depth": self.chain_depth,
            "dependency_chain_coverage": self.coverage,
            "dependency_coherence": self.coherence,
            "dependency_coherence_average": self.coherence,
            "dependency_causal_alignment": self.causal_alignment,
        }


__all__ = ["ReasonedDependencyChain"]
