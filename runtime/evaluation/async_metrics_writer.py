"""Non-blocking metrics persistence."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any


ALLOWED_WRITE_KEYS = {
    "evaluation_summary",
    "success_statistics",
    "resource_usage",
}


class AsyncMetricsWriter:
    def __init__(
        self,
        output_path: str | Path = "runtime_data/evaluation_summary.jsonl",
        logger: logging.Logger | None = None,
    ) -> None:
        self.output_path = Path(output_path)
        self.logger = logger or logging.getLogger(__name__)

    def write_async(self, payload: dict[str, Any] | None) -> threading.Thread:
        safe_payload = {
            key: value
            for key, value in dict(payload or {}).items()
            if key in ALLOWED_WRITE_KEYS
        }
        thread = threading.Thread(
            target=self._write,
            args=(safe_payload,),
            name="evaluation-metrics-writer",
            daemon=True,
        )
        thread.start()
        return thread

    def _write(self, payload: dict[str, Any]) -> None:
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with self.output_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        except Exception as error:
            self.logger.warning("[EVAL] async metrics write failed: %s", error)
