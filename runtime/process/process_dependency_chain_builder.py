"""Build executable reasoning chains from typed process dependencies."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.process.process_dependency_graph import ProcessDependencyGraph
from runtime.process.process_dependency_trace import ProcessDependencyTrace


CHAIN_DEPENDENCY_TYPES = {
    "requires",
    "preserves",
    "enables",
    "causes",
    "constrains",
    "derives_from",
}


@dataclass(frozen=True)
class ReasonedDependencyChain:
    concept: str
    chain: list[str]
    dependency_types: list[str]
    depth: int
    coverage: float
    coherence: float
    causal_alignment: float
    contradictions: list[str] = field(default_factory=list)
    links_used: int = 0
    trace: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "reasoned_dependency_chain": True,
            "resolved_dependency_chain": list(self.chain),
            "dependency_chain_depth": self.depth,
            "dependency_chain_coverage": self.coverage,
            "dependency_coherence": self.coherence,
            "dependency_coherence_average": self.coherence,
            "dependency_causal_alignment": self.causal_alignment,
            "process_dependency_links_used": self.links_used,
            "architecture_bottleneck": False,
            "recommended_next_step": "consume_reasoned_dependency_chains",
        }


class ProcessDependencyChainBuilder:
    """Construct ReasonedDependencyChain from typed dependency links."""

    system_name = "process_dependency_chain_builder"

    def build(
        self,
        concept: str,
        links: Iterable[Mapping[str, Any]],
        observed_contradictions: Iterable[str] | None = None,
    ) -> ReasonedDependencyChain:
        links = [dict(link) for link in links or []]
        graph = ProcessDependencyGraph(links)
        chain, chain_edges = graph.longest_chain(
            concept,
            allowed_types=CHAIN_DEPENDENCY_TYPES,
        )
        reachable = graph.reachable_links(
            concept,
            allowed_types=CHAIN_DEPENDENCY_TYPES,
        )
        support_links = [
            link
            for link in links
            if link.get("dependency_type") in CHAIN_DEPENDENCY_TYPES
        ]
        forbidden = [
            link
            for link in links
            if link.get("dependency_type") == "forbids"
        ]
        observed = {str(item) for item in observed_contradictions or [] if item}
        contradictions = [
            str(link.get("target"))
            for link in forbidden
            if str(link.get("target")) in observed
        ]
        coverage = (
            len(reachable) / len(support_links)
            if support_links
            else 0.0
        )
        confidences = [
            clamp(link.get("confidence", 0.0))
            for link in reachable or chain_edges
        ]
        coherence = (
            sum(confidences) / len(confidences)
            if confidences
            else 0.0
        )
        causal_types = {"requires", "enables", "causes", "derives_from"}
        causal_edges = [
            link
            for link in reachable or chain_edges
            if link.get("dependency_type") in causal_types
        ]
        causal_alignment = (
            sum(clamp(link.get("confidence", 0.0)) for link in causal_edges)
            / len(causal_edges)
            if causal_edges
            else coherence
        )
        trace = ProcessDependencyTrace(
            concept=str(concept),
            steps=[
                {
                    "source": link.get("source"),
                    "dependency_type": link.get("dependency_type"),
                    "target": link.get("target"),
                    "confidence": link.get("confidence", 0.0),
                }
                for link in chain_edges
            ],
            contradictions=contradictions,
        )
        return ReasonedDependencyChain(
            concept=str(concept),
            chain=chain,
            dependency_types=[
                str(link.get("dependency_type")) for link in chain_edges
            ],
            depth=max(len(chain) - 1, 0),
            coverage=round(clamp(coverage), 4),
            coherence=round(clamp(coherence), 4),
            causal_alignment=round(clamp(causal_alignment), 4),
            contradictions=contradictions,
            links_used=len(reachable),
            trace=trace.as_dict(),
        )


__all__ = [
    "CHAIN_DEPENDENCY_TYPES",
    "ProcessDependencyChainBuilder",
    "ReasonedDependencyChain",
]
