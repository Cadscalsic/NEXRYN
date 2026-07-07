"""Episode memory extraction and storage using existing experience files."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import uuid
from typing import Any, Mapping

from runtime.adaptive_reuse.experience_index import ExperienceIndex


class EpisodeMemory:
    def __init__(self, root: str | Path = "runtime/memory/storage/experiences") -> None:
        self.root = Path(root)
        self.index = ExperienceIndex(self.root.parent)

    def extract(self, runtime_context: Mapping[str, Any] | None) -> dict[str, Any]:
        context = dict(runtime_context or {})
        query = self.index.query_signature(context)
        payload = {
            **query.as_dict(),
            "experience_id": str(uuid.uuid4()),
            "winner_hypothesis": context.get("winner_hypothesis", {}),
            "semantic_graph": context.get("semantic_graph", {}),
            "execution_plan": context.get("execution_plan", {}),
            "dependency_graph": context.get("dependency_graph", {}),
            "program": context.get("program", context.get("synthesized_program", {})),
            "truth_commitments": context.get("truth_commitments", []),
            "context": context.get("context", {}),
            "transformations": context.get("transformations", []),
            "evaluation_result": context.get("evaluation_result", {}),
            "timestamp": str(datetime.utcnow()),
        }
        return payload

    def store_success(self, runtime_context: Mapping[str, Any] | None) -> dict[str, Any]:
        context = dict(runtime_context or {})
        evaluation = context.get("evaluation_result", {})
        if isinstance(evaluation, Mapping) and evaluation.get("success") is False:
            return {"stored": False, "reason": "task_not_successful"}
        payload = self.extract(context)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"experience_{payload['experience_id']}.json"
        try:
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        except OSError as error:
            return {"stored": False, "reason": str(error)}
        return {"stored": True, "experience_id": payload["experience_id"], "path": str(path)}
