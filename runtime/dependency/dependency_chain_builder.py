"""Build executable dependency chains from typed memory."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.dependency.dependency_graph_engine import DependencyGraphEngine
from runtime.dependency.dependency_trace_engine import DependencyTraceEngine
from runtime.dependency.explanation_engine import ExplanationEngine
from runtime.dependency.reasoned_dependency_chain import ReasonedDependencyChain


EXECUTABLE_DEPENDENCY_TYPES = {
    "requires",
    "preserves",
    "modifies",
    "enables",
    "causes",
    "constrains",
    "derives_from",
}


class DependencyChainBuilder:
    system_name = "dependency_chain_builder"

    def __init__(
        self,
        trace_engine: DependencyTraceEngine | None = None,
        explanation_engine: ExplanationEngine | None = None,
    ):
        self.trace_engine = trace_engine or DependencyTraceEngine()
        self.explanation_engine = explanation_engine or ExplanationEngine()

    def build(
        self,
        concept: str,
        links: Iterable[Mapping[str, Any]],
        observed_contradictions: Iterable[str] | None = None,
        max_depth: int = 8,
    ) -> dict[str, Any]:
        links = [dict(link) for link in links or []]
        graph = DependencyGraphEngine(links)
        chain, chain_edges = graph.longest_chain(
            concept,
            allowed_types=EXECUTABLE_DEPENDENCY_TYPES,
            max_depth=max_depth,
        )
        executable_edges = [
            link
            for link in links
            if link.get("dependency_type") in EXECUTABLE_DEPENDENCY_TYPES
        ]
        observed = {str(item) for item in observed_contradictions or [] if item}
        contradictions = [
            str(link.get("target"))
            for link in links
            if link.get("dependency_type") == "forbids"
            and str(link.get("target")) in observed
        ]
        confidences = [
            clamp(link.get("confidence", 0.0)) for link in executable_edges
        ]
        coherence = (
            sum(confidences) / len(confidences)
            if confidences
            else 0.0
        )
        causal_edges = [
            link
            for link in executable_edges
            if link.get("dependency_type") in {"requires", "causes", "enables", "derives_from"}
        ]
        causal_alignment = (
            sum(clamp(link.get("confidence", 0.0)) for link in causal_edges)
            / len(causal_edges)
            if causal_edges
            else coherence
        )
        trace = self.trace_engine.trace(concept, chain_edges)
        dependency_graph = graph.as_dict()
        explanation = self.explanation_engine.explain(
            str(concept),
            chain_edges,
            dependency_graph,
        )
        chain_model = ReasonedDependencyChain(
            concept=str(concept),
            dependency_graph=dependency_graph,
            dependencies=chain,
            dependency_types=[
                str(edge.get("dependency_type")) for edge in chain_edges
            ],
            chain_depth=max(len(chain) - 1, 0),
            coverage=round(
                len(executable_edges) / max(len(links), 1),
                4,
            ),
            coherence=round(clamp(coherence), 4),
            causal_alignment=round(clamp(causal_alignment), 4),
            contradictions=contradictions,
            explanation_path=explanation["explanation_path"],
        )
        explanation_quality = clamp(
            explanation["explanation_quality"] * 0.55
            + (1.0 if chain_model.chain_depth >= 4 else chain_model.chain_depth / 4.0)
            * 0.20
            + chain_model.coverage * 0.15
            + chain_model.coherence * 0.10
        )
        dependency_reasoning_report = (
            "DEPENDENCY REASONING REPORT\n"
            f"process_dependency_links_loaded = {len(links)}\n"
            f"process_dependency_links_used = {len(executable_edges)}\n"
            f"dependency_chain_depth = {chain_model.chain_depth}\n"
            f"dependency_chain_coverage = {chain_model.coverage}\n"
            f"explanation_quality = {round(explanation_quality, 4)}\n"
            f"dependency_coherence = {chain_model.coherence}\n"
        )
        return {
            **chain_model.as_dict(),
            "system": self.system_name,
            "dependency_trace": trace,
            "dependency_explanation": explanation,
            "explanation_quality": round(explanation_quality, 4),
            "dependency_explanation_quality": round(explanation_quality, 4),
            "dependency_reasoning_report": dependency_reasoning_report,
            "process_dependency_links_used": len(executable_edges),
            "executable_dependency_links_used": len(executable_edges),
            "architecture_bottleneck": False,
            "recommended_next_step": "consume_executable_dependency_chains",
        }


__all__ = ["DependencyChainBuilder", "EXECUTABLE_DEPENDENCY_TYPES"]
