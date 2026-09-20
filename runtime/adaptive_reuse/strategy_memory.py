"""Access existing persisted strategy memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class StrategyMemory:
    def __init__(self, root: str | Path = "runtime/memory/storage/strategies") -> None:
        self.root = Path(root)

    def load(self, limit: int = 500) -> list[dict[str, Any]]:
        strategies = []
        if not self.root.exists():
            return strategies
        for path in sorted(self.root.glob("*.json"))[-limit:]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(payload, Mapping):
                continue
            strategy = payload.get("strategy", payload)
            if not isinstance(strategy, Mapping):
                continue
            record = dict(strategy)
            record["strategy_id"] = payload.get("strategy_id") or path.stem
            record["confidence"] = record.get("confidence", payload.get("confidence", 0.0))
            record["concept"] = record.get("concept") or record.get("type") or path.stem
            strategies.append(record)
        return strategies
