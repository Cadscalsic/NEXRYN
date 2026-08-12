from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


class RepairNoveltyGuard:
    def review(
        self,
        repair_candidate: Mapping[str, Any] | None,
        *,
        previous_signatures: set[str] | None = None,
        lineage: list[str] | None = None,
    ) -> dict[str, Any]:
        candidate = repair_candidate if isinstance(repair_candidate, Mapping) else {}
        signature = self.signature(candidate)
        seen = previous_signatures or set()
        candidate_id = str(candidate.get("candidate_id") or "")
        lineage_ids = lineage or []
        if candidate_id and candidate_id in lineage_ids[:-1]:
            state = "REPAIR_CYCLE_DETECTED"
        elif signature in seen:
            state = "DUPLICATE_REPAIR"
        else:
            state = "NOVEL_REPAIR"
        return {
            "repair_novelty_state": state,
            "repair_signature": signature,
            "duplicate_repair": state != "NOVEL_REPAIR",
        }

    def signature(self, repair_candidate: Mapping[str, Any]) -> str:
        metadata = repair_candidate.get("metadata", {})
        program = repair_candidate.get("program", {})
        payload = {
            "parent_candidate_id": metadata.get("parent_candidate_id"),
            "residual_fingerprint": metadata.get("target_residual_fingerprint"),
            "repair_operation": metadata.get("repair_operation") or repair_candidate.get("operation"),
            "target_locations": metadata.get("target_locations"),
            "program": program,
        }
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


repair_novelty_guard = RepairNoveltyGuard()


__all__ = ["RepairNoveltyGuard", "repair_novelty_guard"]
