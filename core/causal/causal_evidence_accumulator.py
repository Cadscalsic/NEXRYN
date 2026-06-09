from core.epistemic_models import clamp


class CausalEvidenceAccumulator:
    """Accumulates repeated support and contradiction for causal relations."""

    def __init__(self):
        self.records = {}

    def _key(self, source, target, relation_type="causes"):
        return f"{source}->{relation_type}->{target}"

    def observe(
        self,
        source,
        target,
        relation_type="causes",
        supported=True,
        confidence=0.5,
        task_id=None,
        context=None,
    ):
        key = self._key(source, target, relation_type)
        record = self.records.setdefault(
            key,
            {
                "source": source,
                "target": target,
                "relation_type": relation_type,
                "support_count": 0,
                "contradiction_count": 0,
                "confidence": 0.0,
                "confidence_history": [],
                "tasks": [],
                "contexts": [],
            },
        )
        if supported:
            record["support_count"] += 1
        else:
            record["contradiction_count"] += 1
        if task_id is not None and task_id not in record["tasks"]:
            record["tasks"].append(task_id)
        if context is not None and context not in record["contexts"]:
            record["contexts"].append(context)

        total = record["support_count"] + record["contradiction_count"]
        support_ratio = record["support_count"] / max(total, 1)
        evidence_volume = clamp(total / 5.0)
        record["confidence"] = clamp(
            (
                support_ratio
                + evidence_volume
                + clamp(confidence)
            )
            / 3.0
        )
        record["confidence_history"].append(record["confidence"])
        return dict(record)

    def apply_to_graph(self, graph):
        for record in self.records.values():
            graph.add_node(
                node_id=record["source"],
                node_type="event",
                name=record["source"],
                confidence=record["confidence"],
                evidence_count=record["support_count"],
                contradiction_score=(
                    record["contradiction_count"]
                    / max(
                        record["support_count"]
                        + record["contradiction_count"],
                        1,
                    )
                ),
            )
            graph.add_node(
                node_id=record["target"],
                node_type="event",
                name=record["target"],
                confidence=record["confidence"],
                evidence_count=record["support_count"],
            )
            graph.add_edge(
                source=record["source"],
                target=record["target"],
                relation_type=record["relation_type"],
                confidence=record["confidence"],
                weight=record["confidence"],
                evidence=[record],
            )
        return graph

    def report(self):
        return {
            "system": "causal_evidence_accumulator",
            "relations": list(self.records.values()),
            "relation_count": len(self.records),
        }


__all__ = [
    "CausalEvidenceAccumulator",
]
