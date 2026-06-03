class TruthLineageGraph:
    def __init__(self):
        self._parents = {}
        self._children = {}

    def add(self, truth_id, parent_truths=None):
        truth_id = str(truth_id)
        parents = set(parent_truths or [])
        for previous_parent in self._parents.get(truth_id, set()):
            self._children.get(previous_parent, set()).discard(truth_id)
        self._parents[truth_id] = parents
        for parent_truth_id in parents:
            self._children.setdefault(parent_truth_id, set()).add(truth_id)

    def parent_truths(self, truth_id):
        return sorted(self._parents.get(truth_id, set()))

    def child_truths(self, truth_id):
        return sorted(self._children.get(truth_id, set()))

    def ancestors(self, truth_id):
        return self._walk(truth_id, self._parents)

    def descendants(self, truth_id):
        return self._walk(truth_id, self._children)

    def _walk(self, truth_id, adjacency):
        visited = set()
        pending = list(adjacency.get(truth_id, set()))
        while pending:
            related_truth_id = pending.pop()
            if related_truth_id in visited:
                continue
            visited.add(related_truth_id)
            pending.extend(adjacency.get(related_truth_id, set()))
        return sorted(visited)

    def report(self):
        return {
            "system": "truth_lineage_graph",
            "phase": "7.2",
            "nodes": sorted(
                set(self._parents) | set(self._children)
            ),
            "edges": [
                {
                    "parent_truth_id": parent_truth_id,
                    "child_truth_id": child_truth_id,
                }
                for parent_truth_id in sorted(self._children)
                for child_truth_id in sorted(
                    self._children[parent_truth_id]
                )
            ],
            "lineage_enabled": True,
        }


__all__ = [
    "TruthLineageGraph",
]
