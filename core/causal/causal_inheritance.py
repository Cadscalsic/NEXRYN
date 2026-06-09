from core.epistemic_models import clamp


class CausalInheritance:
    """Learns reusable causal templates from validated paths."""

    def __init__(self, inheritance_threshold=0.70):
        self.inheritance_threshold = clamp(inheritance_threshold)
        self.templates = {}

    def learn_template(self, source, target, relation_type, confidence=0.0):
        key = f"{source}:{relation_type}:{target}"
        record = self.templates.setdefault(
            key,
            {
                "source": source,
                "target": target,
                "relation_type": relation_type,
                "confidence": 0.0,
                "observations": 0,
            },
        )
        record["observations"] += 1
        record["confidence"] = clamp(
            max(record["confidence"], confidence)
            + min(record["observations"], 5) * 0.03
        )
        return dict(record)

    def learn_from_path(self, causal_path):
        chain = list(causal_path.get("causal_chain", []))
        confidence = causal_path.get("path_confidence", 0.0)
        learned = []
        for source, target in zip(chain, chain[1:]):
            learned.append(
                self.learn_template(
                    source,
                    target,
                    "causes",
                    confidence=confidence,
                )
            )
        return learned

    def expectations_for(self, source):
        return [
            item
            for item in self.templates.values()
            if item["source"] == source
            and item["confidence"] >= self.inheritance_threshold
        ]

    def apply_expectations(self, graph, source, context=None):
        applied = []
        for template in self.expectations_for(source):
            graph.add_node(
                node_id=template["source"],
                node_type="event",
                name=template["source"],
                confidence=template["confidence"],
                metadata={"inherited": True, "context": context or {}},
            )
            graph.add_node(
                node_id=template["target"],
                node_type="event",
                name=template["target"],
                confidence=template["confidence"],
                metadata={"inherited": True, "context": context or {}},
            )
            edge = graph.add_edge(
                source=template["source"],
                target=template["target"],
                relation_type=template["relation_type"],
                confidence=template["confidence"],
                weight=template["confidence"],
                evidence=[{"source": "causal_inheritance", **template}],
            )
            applied.append(edge.as_dict())
        return applied

    def report(self):
        return {
            "system": "causal_inheritance",
            "templates": list(self.templates.values()),
        }


__all__ = [
    "CausalInheritance",
]
