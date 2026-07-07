"""Deterministic experience indexing over existing runtime memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_STORAGE_ROOT = Path("runtime/memory/storage")


@dataclass
class Experience:
    experience_id: str
    task_signature: str = ""
    visual_signature: str = ""
    semantic_signature: str = ""
    concept_signature: str = ""
    execution_signature: str = ""
    dependency_signature: str = ""
    program_signature: str = ""
    context_signature: str = ""
    truth_signature: str = ""
    performance_score: float = 0.0
    success_rate: float = 0.0
    execution_cost: float = 0.0
    reasoning_depth: int = 0
    reuse_count: int = 0
    last_used: str = ""
    confidence: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)

    def signature_tokens(self, name: str) -> set[str]:
        value = getattr(self, name, "")
        return _tokens(value)

    def as_dict(self) -> dict[str, Any]:
        data = {
            "experience_id": self.experience_id,
            "task_signature": self.task_signature,
            "visual_signature": self.visual_signature,
            "semantic_signature": self.semantic_signature,
            "concept_signature": self.concept_signature,
            "execution_signature": self.execution_signature,
            "dependency_signature": self.dependency_signature,
            "program_signature": self.program_signature,
            "context_signature": self.context_signature,
            "truth_signature": self.truth_signature,
            "performance_score": self.performance_score,
            "success_rate": self.success_rate,
            "execution_cost": self.execution_cost,
            "reasoning_depth": self.reasoning_depth,
            "reuse_count": self.reuse_count,
            "last_used": self.last_used,
            "confidence": self.confidence,
        }
        return data


class ExperienceIndex:
    def __init__(self, storage_root: str | Path = DEFAULT_STORAGE_ROOT) -> None:
        self.storage_root = Path(storage_root)
        self.experience_root = self.storage_root / "experiences"

    def load(self, limit: int = 500) -> list[Experience]:
        experiences = []
        if not self.experience_root.exists():
            return experiences
        paths = sorted(self.experience_root.glob("*.json"))[-limit:]
        for path in paths:
            payload = self._read_json(path)
            if isinstance(payload, Mapping):
                experiences.append(self.normalize(payload, fallback_id=path.stem))
        return experiences

    def normalize(
        self,
        payload: Mapping[str, Any],
        fallback_id: str = "",
    ) -> Experience:
        winner = _mapping(payload.get("winner_hypothesis"))
        evaluation = _mapping(payload.get("evaluation_result"))
        graph = _mapping(payload.get("semantic_graph"))
        plan = _mapping(payload.get("execution_plan"))
        concepts = [
            str(node.get("concept"))
            for node in graph.get("concept_nodes", [])
            if isinstance(node, Mapping) and node.get("concept")
        ]
        nodes = [
            str(node.get("operation"))
            for node in plan.get("nodes", [])
            if isinstance(node, Mapping) and node.get("operation")
        ]
        dependency_edges = []
        for node in plan.get("nodes", []):
            if not isinstance(node, Mapping):
                continue
            dependency_edges.extend(str(item) for item in node.get("dependencies", []) or [])
        performance = _score(
            evaluation.get("final_score"),
            evaluation.get("accuracy"),
            winner.get("execution_score"),
            winner.get("confidence"),
        )
        success = 1.0 if evaluation.get("success") is True else performance
        confidence = _score(winner.get("confidence"), evaluation.get("accuracy"), performance)
        program_signature = _join(nodes or _program_ops(payload))
        task_signature = _hashable_signature(
            payload.get("task_signature")
            or payload.get("task_path")
            or payload.get("experience_id")
            or fallback_id
        )
        return Experience(
            experience_id=str(payload.get("experience_id") or fallback_id),
            task_signature=task_signature,
            visual_signature=_hashable_signature(payload.get("visual_signature") or ""),
            semantic_signature=_join(
                concepts
                or _tokens(payload.get("semantic_summary"))
                or _tokens(winner.get("description"))
            ),
            concept_signature=_join(concepts),
            execution_signature=_join(nodes),
            dependency_signature=_join(dependency_edges),
            program_signature=program_signature,
            context_signature=_join(_context_tokens(payload)),
            truth_signature=_join(_truth_tokens(payload)),
            performance_score=performance,
            success_rate=success,
            execution_cost=_score(payload.get("execution_cost")),
            reasoning_depth=int(_score(payload.get("reasoning_depth"))),
            reuse_count=int(payload.get("reuse_count", 0) or 0),
            last_used=str(payload.get("last_used") or payload.get("timestamp") or ""),
            confidence=confidence,
            payload=dict(payload),
        )

    def query_signature(self, runtime_context: Mapping[str, Any] | None) -> Experience:
        context = _mapping(runtime_context)
        graph = _mapping(context.get("semantic_graph"))
        winner = _mapping(context.get("winner_hypothesis"))
        plan = _mapping(context.get("execution_plan"))
        concepts = [
            str(node.get("concept"))
            for node in graph.get("concept_nodes", [])
            if isinstance(node, Mapping) and node.get("concept")
        ]
        concept = context.get("concept") or winner.get("type") or context.get("task_concept")
        if concept:
            concepts.append(str(concept))
        nodes = [
            str(node.get("operation"))
            for node in plan.get("nodes", [])
            if isinstance(node, Mapping) and node.get("operation")
        ]
        task_signature = _hashable_signature(
            context.get("task_signature")
            or context.get("task_path")
            or context.get("task_id")
            or concept
            or ""
        )
        return Experience(
            experience_id="current_query",
            task_signature=task_signature,
            visual_signature=_hashable_signature(context.get("visual_signature") or ""),
            semantic_signature=_join(
                concepts
                or _tokens(context.get("semantic_summary"))
                or _tokens(winner.get("description"))
            ),
            concept_signature=_join(concepts),
            execution_signature=_join(nodes),
            dependency_signature=_join(_dependency_tokens(context)),
            program_signature=_join(nodes or _program_ops(context)),
            context_signature=_join(_context_tokens(context)),
            truth_signature=_join(_truth_tokens(context)),
            performance_score=0.0,
            success_rate=0.0,
            execution_cost=0.0,
            reasoning_depth=0,
            reuse_count=0,
            last_used=str(datetime.utcnow()),
            confidence=_score(winner.get("confidence")),
            payload=dict(context),
        )

    def _read_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _score(*values: Any) -> float:
    for value in values:
        try:
            return round(max(0.0, min(1.0, float(value))), 4)
        except (TypeError, ValueError):
            continue
    return 0.0


def _tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, Mapping):
        text = json.dumps(value, sort_keys=True, default=str)
    elif isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value)
    else:
        text = str(value)
    normalized = text.lower().replace("_", " ").replace("-", " ")
    return {token for token in normalized.split() if len(token) > 2}


def _join(values: Any) -> str:
    if isinstance(values, str):
        tokens = _tokens(values)
    else:
        tokens = {str(value).lower() for value in values or [] if value}
    return "|".join(sorted(tokens))


def _hashable_signature(value: Any) -> str:
    if not value:
        return ""
    text = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _program_ops(value: Mapping[str, Any]) -> list[str]:
    program = _mapping(value.get("program"))
    steps = program.get("program_steps") or program.get("steps") or value.get("program_steps") or []
    operations = []
    for step in steps:
        if isinstance(step, Mapping):
            operation = step.get("operation") or step.get("operator")
            if operation:
                operations.append(str(operation))
    return operations


def _context_tokens(value: Mapping[str, Any]) -> list[str]:
    tokens = []
    for key in (
        "context",
        "context_id",
        "semantic_context",
        "process_context",
        "causal_context",
        "world_context",
    ):
        item = value.get(key)
        if item:
            tokens.extend(_tokens(item))
    return sorted(tokens)


def _truth_tokens(value: Mapping[str, Any]) -> list[str]:
    tokens = []
    for key in ("truth_commitments", "reusable_truth_commitments", "truth_registry_report"):
        item = value.get(key)
        if item:
            tokens.extend(_tokens(item))
    return sorted(tokens)


def _dependency_tokens(value: Mapping[str, Any]) -> list[str]:
    tokens = []
    for key in ("dependency_graph", "dependency_snapshot", "dependency_chain", "resolved_dependency_chain"):
        item = value.get(key)
        if item:
            tokens.extend(_tokens(item))
    return sorted(tokens)
