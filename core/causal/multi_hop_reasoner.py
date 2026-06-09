from core.causal.causal_path_ranker import CausalPathRanker


class MultiHopReasoner:
    """Discovers direct, indirect, and root causal chains."""

    CAUSAL_RELATIONS = {
        "causes",
        "supports",
        "enables",
        "explains",
        "depends_on",
        "invalidates",
        "context_requires",
        "implies",
    }

    def __init__(self, ranker=None):
        self.ranker = ranker or CausalPathRanker()

    def discover(self, graph, source, target=None, max_depth=6):
        paths = graph.find_all_paths(
            source,
            target=target,
            max_depth=max_depth,
            relation_types=self.CAUSAL_RELATIONS,
        )
        ranked = self.ranker.rank(paths)
        best = ranked[0] if ranked else {
            "causal_chain": [],
            "depth": 0,
            "path_strength": 0.0,
            "path_confidence": 0.0,
            "score": 0.0,
        }
        root_cause = (
            best["causal_chain"][0]
            if best["causal_chain"]
            else source
        )
        return {
            "system": "multi_hop_reasoner",
            "root_cause": root_cause,
            "causal_chain": best["causal_chain"],
            "depth": best["depth"],
            "path_strength": best["path_strength"],
            "path_confidence": best["path_confidence"],
            "direct_causes": [
                item["node"]["node_id"]
                for item in graph.find_dependencies(target or source)
            ]
            if target or source
            else [],
            "indirect_causes": [
                node_id
                for node_id in best["causal_chain"][:-2]
            ],
            "ranked_paths": ranked,
        }


__all__ = [
    "MultiHopReasoner",
]
