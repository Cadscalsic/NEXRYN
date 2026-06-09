from core.causal.multi_hop_reasoner import MultiHopReasoner


class CausalChainBuilder:
    """Builds direct, indirect, branching, and converging causal chains."""

    def __init__(self, reasoner=None):
        self.reasoner = reasoner or MultiHopReasoner()

    def build(self, graph, sources=None, targets=None, max_depth=6):
        sources = list(sources or graph.nodes.keys())
        targets = list(targets or graph.nodes.keys())
        direct = []
        indirect = []
        branching = []
        converging = []

        for source in sources:
            outgoing = graph.outgoing(source)
            if len(outgoing) > 1:
                branching.append({
                    "source": source,
                    "targets": [edge.target for edge in outgoing],
                })
            for edge in outgoing:
                direct.append({
                    "causal_chain": [edge.source, edge.target],
                    "relation_type": edge.relation_type,
                    "path_strength": edge.weight,
                    "path_confidence": edge.confidence,
                    "depth": 1,
                })

        for target in targets:
            incoming = graph.incoming(target)
            if len(incoming) > 1:
                converging.append({
                    "target": target,
                    "sources": [edge.source for edge in incoming],
                })
            for source in sources:
                if source == target:
                    continue
                report = self.reasoner.discover(
                    graph,
                    source,
                    target,
                    max_depth=max_depth,
                )
                if report["depth"] > 1:
                    indirect.append(report)

        return {
            "system": "causal_chain_builder",
            "direct_chains": direct,
            "indirect_chains": indirect,
            "branching_chains": branching,
            "converging_chains": converging,
        }


__all__ = [
    "CausalChainBuilder",
]
