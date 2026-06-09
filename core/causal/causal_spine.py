from core.epistemic_models import clamp


class CausalSpine:
    """Persistent causal backbone for promoted and protected paths."""

    def __init__(
        self,
        promotion_threshold=0.75,
        protection_threshold=0.85,
        decay_rate=0.05,
    ):
        self.promotion_threshold = clamp(promotion_threshold)
        self.protection_threshold = clamp(protection_threshold)
        self.decay_rate = clamp(decay_rate)
        self.paths = {}

    def _path_id(self, causal_chain):
        return " -> ".join(str(item) for item in causal_chain)

    def insert(self, causal_path, identity_governance=None):
        identity_governance = identity_governance or {}
        chain = list(causal_path.get("causal_chain", []))
        path_id = causal_path.get("path_id") or self._path_id(chain)
        record = {
            "path_id": path_id,
            "causal_chain": chain,
            "path_strength": clamp(causal_path.get("path_strength", 0.0)),
            "path_confidence": clamp(
                causal_path.get("path_confidence", 0.0)
            ),
            "reinforcement_count": 1,
            "support_count": int(causal_path.get("support_count", 1)),
            "contradiction_count": int(
                causal_path.get("contradiction_count", 0)
            ),
            "spine_state": "INSERTED",
            "protected": False,
            "identity_governance": dict(identity_governance),
        }
        self.paths[path_id] = record
        return record

    def reinforce(self, path_id, amount=0.05):
        record = self.paths[path_id]
        record["path_strength"] = clamp(record["path_strength"] + amount)
        record["path_confidence"] = clamp(record["path_confidence"] + amount)
        record["reinforcement_count"] += 1
        record["support_count"] += 1
        if record["path_confidence"] >= self.protection_threshold:
            record["protected"] = True
            record["spine_state"] = "PROTECTED"
        return record

    def weaken(self, path_id, amount=0.05):
        record = self.paths[path_id]
        record["path_strength"] = clamp(record["path_strength"] - amount)
        record["path_confidence"] = clamp(record["path_confidence"] - amount)
        record["contradiction_count"] += 1
        if not record.get("protected"):
            record["spine_state"] = "WEAKENED"
        return record

    def rank_paths(self):
        return sorted(
            self.paths.values(),
            key=lambda item: (
                item["path_confidence"],
                item["path_strength"],
                item["support_count"],
            ),
            reverse=True,
        )

    def decay(self):
        for record in self.paths.values():
            if record.get("protected"):
                continue
            record["path_strength"] = clamp(
                record["path_strength"] - self.decay_rate
            )
            record["path_confidence"] = clamp(
                record["path_confidence"] - self.decay_rate
            )
            if record["spine_state"] == "PROMOTED":
                record["spine_state"] = "DECAYING"
        return self.report()

    def promote(self, path_id, identity_governance=None):
        record = self.paths[path_id]
        identity_governance = identity_governance or record.get(
            "identity_governance",
            {},
        )
        gates = [
            identity_governance.get("identity_governance", True),
            identity_governance.get("identity_continuity", True),
            identity_governance.get("semantic_integrity", True),
            identity_governance.get("ontology_integrity", True),
        ]
        allowed = all(gates)
        if (
            allowed
            and record["path_confidence"] >= self.promotion_threshold
            and record["path_strength"] >= self.promotion_threshold
        ):
            record["spine_state"] = "PROMOTED"
            record["protected"] = (
                record["path_confidence"] >= self.protection_threshold
            )
        else:
            record["spine_state"] = "PROMOTION_BLOCKED"
        record["identity_governance"] = dict(identity_governance)
        return record

    def protect(self, path_id):
        record = self.paths[path_id]
        record["protected"] = True
        record["spine_state"] = "PROTECTED"
        return record

    def report(self):
        return {
            "system": "causal_spine",
            "path_count": len(self.paths),
            "paths": list(self.paths.values()),
            "ranked_paths": self.rank_paths(),
            "protected_paths": [
                item
                for item in self.paths.values()
                if item.get("protected")
            ],
        }


__all__ = [
    "CausalSpine",
]
