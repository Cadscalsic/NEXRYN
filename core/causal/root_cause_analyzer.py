from core.causal.multi_hop_reasoner import MultiHopReasoner


class RootCauseAnalyzer:
    """Traces causal explanations backward from an effect or review state."""

    def __init__(self, reasoner=None):
        self.reasoner = reasoner or MultiHopReasoner()

    def analyze(self, graph, target, max_depth=6):
        roots = graph.find_root_causes(target)
        analyses = []
        for root in roots:
            report = self.reasoner.discover(
                graph,
                root["node_id"],
                target=target,
                max_depth=max_depth,
            )
            analyses.append(report)
        analyses = sorted(
            analyses,
            key=lambda item: item["path_confidence"],
            reverse=True,
        )
        best = analyses[0] if analyses else {}
        return {
            "system": "root_cause_analyzer",
            "target": target,
            "root_causes": [
                item["node_id"]
                for item in roots
            ],
            "supporting_causes": [
                item["root_cause"]
                for item in analyses
                if item.get("path_confidence", 0.0) >= 0.5
            ],
            "causal_depth": best.get("depth", 0),
            "confidence": best.get("path_confidence", 0.0),
            "best_causal_chain": best.get("causal_chain", []),
            "paths": analyses,
        }


__all__ = [
    "RootCauseAnalyzer",
]
