"""Runtime-owned observability snapshots for cognitive executions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


SNAPSHOT_SCHEMA_VERSION = "1.0.0"

RUNTIME_SNAPSHOT_TYPES = {
    "execution_runtime": (
        "execution_boot",
        "execution_start",
        "execution_pipeline",
        "execution_finish",
        "execution_summary",
    ),
    "truth_runtime": (
        "truth_candidate_generation",
        "truth_validation",
        "truth_promotion",
        "truth_commit",
        "truth_statistics",
    ),
    "evaluation_runtime": (
        "evaluation_start",
        "metric_collection",
        "scoring",
        "reward_assignment",
        "penalty_assignment",
        "evaluation_summary",
    ),
    "dependency_runtime": (
        "dependency_discovery",
        "dependency_graph",
        "dependency_execution",
        "dependency_completion",
    ),
    "process_runtime": (
        "process_generation",
        "process_validation",
        "process_execution",
        "process_summary",
    ),
    "causal_runtime": (
        "causal_generation",
        "cause_effect_pairs",
        "root_cause_analysis",
        "causal_validation",
        "causal_summary",
    ),
    "reuse_runtime": (
        "reuse_lookup",
        "reuse_candidates",
        "reuse_selection",
        "reuse_application",
        "reuse_summary",
    ),
    "executable_intelligence_runtime": (
        "semantic_program_activation",
        "program_blueprint_generation",
        "candidate_proposal",
        "candidate_arena",
        "executable_intelligence_summary",
    ),
}

DEFAULT_RUNTIME_SNAPSHOT_TYPES = (
    "runtime_start",
    "runtime_checkpoint",
    "runtime_finish",
    "runtime_summary",
)


@dataclass(frozen=True)
class RuntimeSnapshot:
    snapshot_id: str
    runtime_id: str
    execution_id: str
    snapshot_type: str
    timestamp: str
    execution_stage: str
    status: str
    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    observations: list[Any] = field(default_factory=list)
    warnings: list[Any] = field(default_factory=list)
    errors: list[Any] = field(default_factory=list)
    duration: float = 0.0
    parent_execution: str | None = None
    episode_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeSnapshotProducer:
    """Deterministic, non-blocking snapshot producer owned by one runtime."""

    def __init__(
        self,
        runtime_id: str,
        supported_snapshot_types: tuple[str, ...] | None = None,
    ) -> None:
        self.runtime_id = runtime_id
        self.supported_snapshot_types = tuple(
            supported_snapshot_types
            or RUNTIME_SNAPSHOT_TYPES.get(runtime_id)
            or DEFAULT_RUNTIME_SNAPSHOT_TYPES
        )

    def build(
        self,
        *,
        execution_id: str,
        snapshot_type: str,
        execution_stage: str,
        status: str,
        sequence: int,
        input_summary: Mapping[str, Any] | None = None,
        output_summary: Mapping[str, Any] | None = None,
        metrics: Mapping[str, Any] | None = None,
        observations: list[Any] | None = None,
        warnings: list[Any] | None = None,
        errors: list[Any] | None = None,
        duration: float | None = None,
        parent_execution: str | None = None,
        episode_id: str | None = None,
    ) -> dict[str, Any]:
        snapshot_type = (
            snapshot_type
            if snapshot_type in self.supported_snapshot_types
            else self.supported_snapshot_types[min(sequence, len(self.supported_snapshot_types) - 1)]
        )
        snapshot = RuntimeSnapshot(
            snapshot_id=f"{self.runtime_id}:{execution_id}:{sequence}:{snapshot_type}",
            runtime_id=self.runtime_id,
            execution_id=execution_id,
            snapshot_type=snapshot_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_stage=execution_stage,
            status=status,
            input_summary=_summary(input_summary),
            output_summary=_summary(output_summary),
            metrics=dict(metrics or {}),
            observations=list(observations or []),
            warnings=list(warnings or []),
            errors=list(errors or []),
            duration=round(_number(duration), 9),
            parent_execution=parent_execution,
            episode_id=episode_id,
        )
        data = snapshot.as_dict()
        data["schema_version"] = SNAPSHOT_SCHEMA_VERSION
        data["immutable"] = True
        return data


class RuntimeSnapshotConsumer:
    """Read-only summary view over a runtime's published snapshots."""

    def summarize(self, snapshots: list[dict[str, Any]] | None) -> dict[str, Any]:
        items = [dict(item) for item in snapshots or [] if isinstance(item, Mapping)]
        failures = [
            item for item in items
            if item.get("errors") or str(item.get("status", "")).upper() == "FAILED"
        ]
        return {
            "snapshot_count": len(items),
            "latest_snapshot": items[-1] if items else None,
            "snapshot_types": [str(item.get("snapshot_type")) for item in items],
            "snapshot_duration": round(
                sum(_number(item.get("duration")) for item in items),
                9,
            ),
            "snapshot_generation_success": bool(items) and not failures,
            "snapshot_generation_failures": failures,
        }


def supported_snapshot_types(runtime_id: str) -> tuple[str, ...]:
    return tuple(
        RUNTIME_SNAPSHOT_TYPES.get(runtime_id)
        or DEFAULT_RUNTIME_SNAPSHOT_TYPES
    )


def snapshot_registry_metadata(runtime_id: str) -> dict[str, Any]:
    return {
        "supported_snapshot_types": list(supported_snapshot_types(runtime_id)),
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_producer": f"{runtime_id}.RuntimeSnapshotProducer",
        "snapshot_consumer": f"{runtime_id}.RuntimeSnapshotConsumer",
    }


def _summary(value: Mapping[str, Any] | None, limit: int = 20) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    output = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= limit:
            break
        if isinstance(item, (str, int, float, bool)) or item is None:
            output[str(key)] = item
        elif isinstance(item, Mapping):
            output[str(key)] = {
                "key_count": len(item),
                "keys": sorted(str(child) for child in item.keys())[:20],
            }
        elif isinstance(item, (list, tuple, set)):
            output[str(key)] = {"count": len(item)}
        else:
            output[str(key)] = type(item).__name__
    return output


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


runtime_snapshot_consumer = RuntimeSnapshotConsumer()


__all__ = [
    "DEFAULT_RUNTIME_SNAPSHOT_TYPES",
    "RUNTIME_SNAPSHOT_TYPES",
    "RuntimeSnapshot",
    "RuntimeSnapshotConsumer",
    "RuntimeSnapshotProducer",
    "SNAPSHOT_SCHEMA_VERSION",
    "runtime_snapshot_consumer",
    "snapshot_registry_metadata",
    "supported_snapshot_types",
]
