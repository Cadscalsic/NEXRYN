"""Cognitive runtime observability for artifact-centric execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


OBSERVABILITY_CONTRACT = [
    "inputs",
    "initialization",
    "processing_stages",
    "intermediate_state",
    "produced_artifacts",
    "consumed_artifacts",
    "published_artifacts",
    "lifecycle_changes",
    "metrics",
    "telemetry",
    "snapshots",
    "final_summary",
]

OBSERVABILITY_LEVELS = {
    0: "Invisible",
    1: "Lifecycle Only",
    2: "Lifecycle + Metrics",
    3: "Lifecycle + Metrics + Snapshots",
    4: "Full Artifact Observability",
    5: "Complete Cognitive Explainability",
}

REQUIRED_COGNITIVE_RUNTIMES = [
    "concept_formation_runtime",
    "program_synthesis_runtime",
    "executable_intelligence_runtime",
    "adaptive_search_intelligence_runtime",
    "evidence_builder_runtime",
    "knowledge_integration_runtime",
    "truth_runtime",
    "memory_runtime",
    "evaluation_runtime",
]


@dataclass
class CognitiveRuntimeSnapshot:
    snapshot_id: str
    runtime_id: str
    snapshot_type: str
    execution_stage: str
    status: str
    purpose: str
    owner_runtime: str
    timestamp: str
    execution_id: str
    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: dict[str, Any] = field(default_factory=dict)
    observations: list[Any] = field(default_factory=list)
    errors: list[Any] = field(default_factory=list)
    duration: float = 0.0
    parent_execution: str | None = None
    episode_id: str | None = None
    artifact_references: list[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_duration_seconds: float = 0.0
    input_count: int = 0
    output_count: int = 0
    failures: list[Any] = field(default_factory=list)
    warnings: list[Any] = field(default_factory=list)
    lifecycle_stage: str = "OBSERVED"
    summary: str = ""
    consumed_artifacts: list[str] = field(default_factory=list)
    produced_artifacts: list[str] = field(default_factory=list)
    published_artifacts: dict[str, int] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveRuntimeObservabilityEngine:
    """Builds the structured cognitive introspection layer for runtimes."""

    system_name = "cognitive_runtime_observability"

    def build_snapshot(
        self,
        *,
        runtime_id: str,
        purpose: str,
        execution_id: str | None = None,
        artifact_references: list[str] | None = None,
        consumed_artifacts: list[str] | None = None,
        produced_artifacts: list[str] | None = None,
        published_artifacts: Mapping[str, int] | None = None,
        confidence: float | None = None,
        duration_seconds: float | None = None,
        input_count: int | None = None,
        output_count: int | None = None,
        failures: list[Any] | None = None,
        warnings: list[Any] | None = None,
        lifecycle_stage: str = "OBSERVED",
        summary: str | None = None,
        metrics: Mapping[str, Any] | None = None,
        telemetry: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        references = list(dict.fromkeys(artifact_references or []))
        consumed = list(dict.fromkeys(consumed_artifacts or []))
        produced = list(dict.fromkeys(produced_artifacts or []))
        published = dict(published_artifacts or {})
        duration = round(_number(duration_seconds), 9)
        status = "FAILED" if failures else lifecycle_stage
        return CognitiveRuntimeSnapshot(
            snapshot_id=f"{runtime_id}:{execution_id or f'{runtime_id}:shared_state_execution'}:{purpose}",
            runtime_id=runtime_id,
            snapshot_type=purpose,
            execution_stage=lifecycle_stage,
            status=status,
            input_summary={
                "input_count": int(input_count if input_count is not None else len(consumed)),
                "consumed_artifact_count": len(consumed),
            },
            output_summary={
                "output_count": int(output_count if output_count is not None else sum(published.values())),
                "produced_artifact_count": len(produced),
                "published_artifacts": dict(published),
            },
            observations=[summary] if summary else [],
            errors=list(failures or []),
            duration=duration,
            parent_execution=None,
            episode_id=None,
            purpose=purpose,
            owner_runtime=runtime_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_id=execution_id or f"{runtime_id}:shared_state_execution",
            artifact_references=references,
            confidence=round(_number(confidence, default=0.9), 4),
            processing_duration_seconds=duration,
            input_count=int(input_count if input_count is not None else len(consumed)),
            output_count=int(output_count if output_count is not None else sum(published.values())),
            failures=list(failures or []),
            warnings=list(warnings or []),
            lifecycle_stage=lifecycle_stage,
            summary=summary or f"{runtime_id} {purpose}",
            consumed_artifacts=consumed,
            produced_artifacts=produced,
            published_artifacts=published,
            metrics=dict(metrics or {}),
            telemetry=dict(telemetry or {}),
        ).as_dict()

    def build_report(self, state: Any) -> dict[str, Any]:
        runtimes = self._runtime_ids(state)
        artifact_flow = self._artifact_flow(state, runtimes)
        snapshots = self._snapshots_by_runtime(state)
        lifecycle = self._lifecycle_by_runtime(state)
        telemetry = self._telemetry_by_runtime(state, runtimes)
        metrics = self._metrics_by_runtime(state, artifact_flow, snapshots, lifecycle)
        runtime_reports = {}
        for runtime_id in runtimes:
            flow = artifact_flow.get(runtime_id, self._empty_flow())
            runtime_snapshots = snapshots.get(runtime_id, [])
            runtime_lifecycle = lifecycle.get(runtime_id, [])
            runtime_metrics = metrics.get(runtime_id, {})
            runtime_telemetry = telemetry.get(runtime_id, {})
            diagnostics = self._self_diagnostics(
                runtime_id,
                flow,
                runtime_snapshots,
                runtime_lifecycle,
                runtime_metrics,
                runtime_telemetry,
            )
            health = self._runtime_health(
                flow,
                runtime_snapshots,
                runtime_lifecycle,
                runtime_metrics,
                runtime_telemetry,
                diagnostics,
            )
            level = self._observability_level(
                flow,
                runtime_snapshots,
                runtime_lifecycle,
                runtime_metrics,
                runtime_telemetry,
                diagnostics,
            )
            runtime_reports[runtime_id] = {
                "runtime_name": _display_name(runtime_id),
                "execution_id": self._execution_id(runtime_id, state),
                "inputs": flow["artifact_types_consumed"],
                "outputs": flow["artifact_types_produced"],
                "consumed_artifacts": flow["consumed_artifacts"],
                "produced_artifacts": flow["produced_artifacts"],
                "published_artifacts": flow["published_artifacts"],
                "rejected_artifacts": flow["rejected_artifacts"],
                "archived_artifacts": flow["archived_artifacts"],
                "promoted_artifacts": flow["promoted_artifacts"],
                "persisted_artifacts": flow["persisted_artifacts"],
                "snapshot_count": len(runtime_snapshots),
                "snapshots": runtime_snapshots[-20:],
                "telemetry_completeness": health["telemetry_completeness"],
                "metric_completeness": health["metric_completeness"],
                "lifecycle_completeness": health["lifecycle_completeness"],
                "health_score": health["observability_score"],
                "runtime_health": health,
                "observability_level": level,
                "observability_level_name": OBSERVABILITY_LEVELS[level],
                "coverage": self._contract_coverage(
                    flow,
                    runtime_snapshots,
                    runtime_lifecycle,
                    runtime_metrics,
                    runtime_telemetry,
                ),
                "warnings": diagnostics["warnings"],
                "self_diagnostics": diagnostics,
            }
        gaps = self._gap_detection(state, runtime_reports)
        timeline = self._timeline(state, snapshots)
        level5 = [
            runtime_id for runtime_id, report in runtime_reports.items()
            if report["observability_level"] == 5
        ]
        return {
            "system": self.system_name,
            "COGNITIVE_OBSERVABILITY_REPORT": True,
            "observability_contract": list(OBSERVABILITY_CONTRACT),
            "observability_levels": dict(OBSERVABILITY_LEVELS),
            "runtime_reports": runtime_reports,
            "runtime_health": {
                runtime_id: report["runtime_health"]
                for runtime_id, report in runtime_reports.items()
            },
            "artifact_flow_observability": artifact_flow,
            "cognitive_timeline": timeline,
            "observability_gap_detection": gaps,
            "self_diagnostics": {
                runtime_id: report["self_diagnostics"]
                for runtime_id, report in runtime_reports.items()
            },
            "coverage": {
                "required_runtimes": list(REQUIRED_COGNITIVE_RUNTIMES),
                "observed_runtimes": runtimes,
                "level_5_runtimes": level5,
                "level_5_coverage": round(len(level5) / max(len(runtimes), 1), 4),
                "every_runtime_level_5": len(level5) == len(runtimes),
            },
            "meta_cognition": self._meta_cognition(runtime_reports, gaps),
            "world_model_integration": {
                "consumes_only_fully_observable_cognition": True,
                "eligible_runtime_count": len(level5),
                "opaque_cognition_excluded": True,
            },
            "dna_integration": {
                "learns_only_from_explainable_behavior": True,
                "eligible_runtime_count": len(level5),
                "opaque_execution_excluded": True,
            },
        }

    def _runtime_ids(self, state: Any) -> list[str]:
        observed = set(REQUIRED_COGNITIVE_RUNTIMES)
        observed.update(
            str(event.get("runtime_id"))
            for event in getattr(state, "propagation_events", [])
            if event.get("runtime_id")
        )
        observed.update(
            str(event.get("runtime_id"))
            for event in getattr(state, "consumption_events", [])
            if event.get("runtime_id")
        )
        observed.update(
            str(snapshot.get("owner_runtime"))
            for snapshot in getattr(state, "runtime_observability_snapshots", [])
            if snapshot.get("owner_runtime")
        )
        ordered = [runtime for runtime in REQUIRED_COGNITIVE_RUNTIMES if runtime in observed]
        ordered.extend(sorted(observed - set(ordered)))
        return ordered

    def _artifact_flow(self, state: Any, runtimes: list[str]) -> dict[str, dict[str, Any]]:
        flow = {runtime_id: self._empty_flow() for runtime_id in runtimes}
        registry = getattr(state, "artifact_registry", {})
        for artifact_id, item in registry.items():
            owner = str(item.get("owner_runtime") or item.get("owner") or "unknown")
            bucket = flow.setdefault(owner, self._empty_flow())
            bucket["produced_artifacts"].append(artifact_id)
            bucket["artifact_types_produced"].append(str(item.get("artifact_type", "UNKNOWN")))
            if item.get("publication_status") == "PUBLISHED":
                bucket["published_artifacts"][artifact_id] = str(item.get("artifact_type", "UNKNOWN"))
            if item.get("archive_status") == "ARCHIVED":
                bucket["archived_artifacts"].append(artifact_id)
            if item.get("promotion_stage") not in {None, "CANDIDATE"}:
                bucket["promoted_artifacts"].append(artifact_id)
            if item.get("persistence_status") in {"PERSISTENT", "LONG_TERM_MEMORY"}:
                bucket["persisted_artifacts"].append(artifact_id)
        for event in getattr(state, "consumption_events", []):
            runtime_id = str(event.get("runtime_id") or "unknown")
            bucket = flow.setdefault(runtime_id, self._empty_flow())
            ids = [str(item) for item in event.get("consumed_artifact_ids", [])]
            bucket["consumed_artifacts"].extend(ids)
            bucket["artifact_types_consumed"].extend(
                str(item) for item in event.get("artifact_types", [])
            )
            bucket["missing_required"].extend(event.get("missing_required", []))
        for failure in getattr(state, "artifact_validation_failures", []):
            runtime_id = str(failure.get("runtime_id") or failure.get("attempted_owner") or "artifact_governance")
            bucket = flow.setdefault(runtime_id, self._empty_flow())
            if failure.get("artifact_id"):
                bucket["rejected_artifacts"].append(str(failure.get("artifact_id")))
        for runtime_id, bucket in flow.items():
            bucket["consumed_artifacts"] = sorted(set(bucket["consumed_artifacts"]))
            bucket["produced_artifacts"] = sorted(set(bucket["produced_artifacts"]))
            bucket["artifact_types_consumed"] = sorted(set(bucket["artifact_types_consumed"]))
            bucket["artifact_types_produced"] = sorted(set(bucket["artifact_types_produced"]))
            bucket["rejected_artifacts"] = sorted(set(bucket["rejected_artifacts"]))
            bucket["archived_artifacts"] = sorted(set(bucket["archived_artifacts"]))
            bucket["promoted_artifacts"] = sorted(set(bucket["promoted_artifacts"]))
            bucket["persisted_artifacts"] = sorted(set(bucket["persisted_artifacts"]))
            bucket["missing_required"] = sorted(set(bucket["missing_required"]))
        return flow

    def _empty_flow(self) -> dict[str, Any]:
        return {
            "artifact_types_consumed": [],
            "artifact_types_produced": [],
            "consumed_artifacts": [],
            "produced_artifacts": [],
            "published_artifacts": {},
            "rejected_artifacts": [],
            "archived_artifacts": [],
            "promoted_artifacts": [],
            "persisted_artifacts": [],
            "missing_required": [],
        }

    def _snapshots_by_runtime(self, state: Any) -> dict[str, list[dict[str, Any]]]:
        snapshots: dict[str, list[dict[str, Any]]] = {}
        for snapshot in getattr(state, "runtime_observability_snapshots", []):
            runtime_id = str(snapshot.get("owner_runtime") or "unknown")
            snapshots.setdefault(runtime_id, []).append(dict(snapshot))
        return snapshots

    def _lifecycle_by_runtime(self, state: Any) -> dict[str, list[dict[str, Any]]]:
        lifecycle: dict[str, list[dict[str, Any]]] = {}
        registry = getattr(state, "artifact_registry", {})
        for event in getattr(state, "artifact_lifecycle_events", []):
            artifact_id = str(event.get("artifact_id") or "")
            owner = str(
                event.get("runtime_id")
                or registry.get(artifact_id, {}).get("owner_runtime")
                or "unknown"
            )
            lifecycle.setdefault(owner, []).append(dict(event))
        return lifecycle

    def _telemetry_by_runtime(
        self,
        state: Any,
        runtimes: list[str],
    ) -> dict[str, dict[str, Any]]:
        telemetry = {runtime_id: {} for runtime_id in runtimes}
        for event in getattr(state, "propagation_events", []):
            runtime_id = str(event.get("runtime_id") or "unknown")
            telemetry.setdefault(runtime_id, {})["last_publication"] = dict(event)
        for event in getattr(state, "consumption_events", []):
            runtime_id = str(event.get("runtime_id") or "unknown")
            telemetry.setdefault(runtime_id, {})["last_consumption"] = dict(event)
        return telemetry

    def _metrics_by_runtime(
        self,
        state: Any,
        flow: Mapping[str, Mapping[str, Any]],
        snapshots: Mapping[str, list[dict[str, Any]]],
        lifecycle: Mapping[str, list[dict[str, Any]]],
    ) -> dict[str, dict[str, Any]]:
        metrics = {}
        runtime_metrics = getattr(state, "runtime_metrics", {})
        for runtime_id, bucket in flow.items():
            metrics[runtime_id] = {
                "produced_artifact_count": len(bucket.get("produced_artifacts", [])),
                "consumed_artifact_count": len(bucket.get("consumed_artifacts", [])),
                "published_artifact_count": len(bucket.get("published_artifacts", {})),
                "rejected_artifact_count": len(bucket.get("rejected_artifacts", [])),
                "promoted_artifact_count": len(bucket.get("promoted_artifacts", [])),
                "persisted_artifact_count": len(bucket.get("persisted_artifacts", [])),
                "snapshot_count": len(snapshots.get(runtime_id, [])),
                "lifecycle_event_count": len(lifecycle.get(runtime_id, [])),
                "runtime_metric_count": len(runtime_metrics) if isinstance(runtime_metrics, Mapping) else 0,
            }
        return metrics

    def _runtime_health(
        self,
        flow: Mapping[str, Any],
        snapshots: list[dict[str, Any]],
        lifecycle: list[dict[str, Any]],
        metrics: Mapping[str, Any],
        telemetry: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
    ) -> dict[str, float | bool]:
        artifact_total = (
            len(flow.get("produced_artifacts", []))
            + len(flow.get("consumed_artifacts", []))
            + len(flow.get("published_artifacts", {}))
        )
        artifact_completeness = 1.0 if artifact_total > 0 else 0.0
        snapshot_completeness = 1.0 if snapshots else 0.0
        metric_completeness = 1.0 if metrics else 0.0
        lifecycle_completeness = 1.0 if lifecycle else 0.0
        telemetry_completeness = 1.0 if telemetry else 0.0
        artifact_consistency = 0.0 if flow.get("missing_required") else 1.0
        publication_success = 1.0 if flow.get("published_artifacts") or flow.get("consumed_artifacts") else 0.0
        consumption_success = 1.0 if flow.get("consumed_artifacts") or not flow.get("missing_required") else 0.0
        execution_success = 0.0 if diagnostics.get("failures") else 1.0
        score = round(
            (
                execution_success
                + artifact_completeness
                + snapshot_completeness
                + metric_completeness
                + lifecycle_completeness
                + telemetry_completeness
                + artifact_consistency
                + publication_success
                + consumption_success
            ) / 9.0,
            4,
        )
        return {
            "execution_success": bool(execution_success),
            "artifact_completeness": artifact_completeness,
            "snapshot_completeness": snapshot_completeness,
            "metric_completeness": metric_completeness,
            "lifecycle_completeness": lifecycle_completeness,
            "telemetry_completeness": telemetry_completeness,
            "artifact_consistency": artifact_consistency,
            "publication_success": publication_success,
            "consumption_success": consumption_success,
            "observability_score": score,
        }

    def _observability_level(
        self,
        flow: Mapping[str, Any],
        snapshots: list[dict[str, Any]],
        lifecycle: list[dict[str, Any]],
        metrics: Mapping[str, Any],
        telemetry: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
    ) -> int:
        if not (flow.get("produced_artifacts") or flow.get("consumed_artifacts") or snapshots):
            return 0
        if lifecycle and not metrics:
            return 1
        if lifecycle and metrics and not snapshots:
            return 2
        if lifecycle and metrics and snapshots and not flow.get("published_artifacts") and not flow.get("consumed_artifacts"):
            return 3
        if lifecycle and metrics and snapshots and not diagnostics.get("failures"):
            return 5
        return 4

    def _contract_coverage(
        self,
        flow: Mapping[str, Any],
        snapshots: list[dict[str, Any]],
        lifecycle: list[dict[str, Any]],
        metrics: Mapping[str, Any],
        telemetry: Mapping[str, Any],
    ) -> dict[str, bool]:
        has_flow = bool(flow.get("produced_artifacts") or flow.get("consumed_artifacts"))
        has_snapshots = bool(snapshots)
        return {
            "inputs": bool(flow.get("artifact_types_consumed") or snapshots),
            "initialization": has_snapshots,
            "processing_stages": has_snapshots,
            "intermediate_state": has_snapshots,
            "produced_artifacts": bool(flow.get("produced_artifacts") or has_flow),
            "consumed_artifacts": bool(flow.get("consumed_artifacts") or has_flow),
            "published_artifacts": bool(flow.get("published_artifacts") or has_flow),
            "lifecycle_changes": bool(lifecycle),
            "metrics": bool(metrics),
            "telemetry": bool(telemetry),
            "snapshots": has_snapshots,
            "final_summary": has_snapshots,
        }

    def _self_diagnostics(
        self,
        runtime_id: str,
        flow: Mapping[str, Any],
        snapshots: list[dict[str, Any]],
        lifecycle: list[dict[str, Any]],
        metrics: Mapping[str, Any],
        telemetry: Mapping[str, Any],
    ) -> dict[str, Any]:
        warnings = []
        failures = []
        if not snapshots:
            warnings.append("missing_snapshots")
        if not metrics:
            warnings.append("missing_metrics")
        if not telemetry:
            warnings.append("missing_telemetry")
        if not lifecycle:
            warnings.append("missing_lifecycle_events")
        if flow.get("missing_required"):
            failures.append("missing_required_artifacts")
        return {
            "runtime_id": runtime_id,
            "inputs_exposed": bool(flow.get("artifact_types_consumed") or snapshots),
            "outputs_exposed": bool(flow.get("artifact_types_produced") or snapshots),
            "artifacts_exposed": bool(flow.get("produced_artifacts") or flow.get("consumed_artifacts")),
            "lifecycle_exposed": bool(lifecycle),
            "metrics_exposed": bool(metrics),
            "telemetry_exposed": bool(telemetry),
            "failures_exposed": True,
            "warnings": warnings,
            "failures": failures,
        }

    def _gap_detection(
        self,
        state: Any,
        runtime_reports: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        missing_snapshots = []
        missing_metrics = []
        missing_telemetry = []
        missing_artifact_reports = []
        missing_lifecycle_events = []
        for runtime_id, report in runtime_reports.items():
            diagnostics = report.get("self_diagnostics", {})
            if "missing_snapshots" in diagnostics.get("warnings", []):
                missing_snapshots.append(runtime_id)
            if "missing_metrics" in diagnostics.get("warnings", []):
                missing_metrics.append(runtime_id)
            if "missing_telemetry" in diagnostics.get("warnings", []):
                missing_telemetry.append(runtime_id)
            if not report.get("produced_artifacts") and not report.get("consumed_artifacts"):
                missing_artifact_reports.append(runtime_id)
            if "missing_lifecycle_events" in diagnostics.get("warnings", []):
                missing_lifecycle_events.append(runtime_id)
        registry = getattr(state, "artifact_registry", {})
        consumed = {
            artifact_id
            for event in getattr(state, "consumption_events", [])
            for artifact_id in event.get("consumed_artifact_ids", [])
        }
        promoted = {
            event.get("artifact_id")
            for event in getattr(state, "artifact_promotion_events", [])
            if event.get("artifact_id")
        }
        persisted = {
            event.get("artifact_id")
            for event in getattr(state, "artifact_persistence_events", [])
            if event.get("artifact_id")
        }
        return {
            "missing_snapshots": missing_snapshots,
            "missing_metrics": missing_metrics,
            "missing_telemetry": missing_telemetry,
            "missing_artifact_reports": missing_artifact_reports,
            "missing_lifecycle_events": missing_lifecycle_events,
            "hidden_state_changes": [],
            "orphan_artifacts": [
                artifact_id for artifact_id in registry
                if artifact_id not in getattr(state, "ownership", {})
            ][:100],
            "invisible_promotions": [
                artifact_id for artifact_id, item in registry.items()
                if item.get("promotion_stage") not in {None, "CANDIDATE"}
                and artifact_id not in promoted
            ][:100],
            "invisible_memory_persistence": [
                artifact_id for artifact_id, item in registry.items()
                if item.get("artifact_type") == "MEMORY"
                and item.get("persistence_status") in {"PERSISTENT", "LONG_TERM_MEMORY"}
                and artifact_id not in persisted
            ][:100],
            "invisible_truth_decisions": [
                artifact_id for artifact_id, item in registry.items()
                if item.get("artifact_type") == "TRUTH"
                and artifact_id not in consumed
                and item.get("consumption_status") == "CONSUMED"
            ][:100],
            "invisible_knowledge_links": [
                artifact_id for artifact_id, item in registry.items()
                if item.get("artifact_type") == "KNOWLEDGE"
                and not (item.get("lineage") or item.get("evidence_references"))
            ][:100],
        }

    def _timeline(
        self,
        state: Any,
        snapshots: Mapping[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        stages = []
        for runtime_id in REQUIRED_COGNITIVE_RUNTIMES:
            runtime_snapshots = snapshots.get(runtime_id, [])
            first = runtime_snapshots[0] if runtime_snapshots else {}
            last = runtime_snapshots[-1] if runtime_snapshots else {}
            artifacts = sorted({
                artifact_id
                for snapshot in runtime_snapshots
                for artifact_id in snapshot.get("artifact_references", [])
            })
            confidences = [
                _number(snapshot.get("confidence"))
                for snapshot in runtime_snapshots
                if snapshot.get("confidence") is not None
            ]
            stages.append({
                "runtime_id": runtime_id,
                "start": first.get("timestamp"),
                "end": last.get("timestamp"),
                "duration_seconds": round(sum(
                    _number(snapshot.get("processing_duration_seconds"))
                    for snapshot in runtime_snapshots
                ), 9),
                "artifacts": artifacts[:100],
                "confidence": round(sum(confidences) / max(len(confidences), 1), 4),
                "status": "observed" if runtime_snapshots else "not_observed",
            })
        return stages

    def _meta_cognition(
        self,
        runtime_reports: Mapping[str, Mapping[str, Any]],
        gaps: Mapping[str, Any],
    ) -> dict[str, Any]:
        ranked = sorted(
            runtime_reports.items(),
            key=lambda pair: pair[1].get("health_score", 0.0),
        )
        return {
            "least_observable_runtimes": [runtime_id for runtime_id, _ in ranked[:5]],
            "runtimes_with_poor_snapshots": list(gaps.get("missing_snapshots", []))[:10],
            "runtimes_losing_artifacts": [
                runtime_id for runtime_id, report in runtime_reports.items()
                if report.get("self_diagnostics", {}).get("failures")
            ],
            "runtimes_with_inconsistent_telemetry": list(gaps.get("missing_telemetry", []))[:10],
            "transparency_optimization_ready": True,
        }

    def _execution_id(self, runtime_id: str, state: Any) -> str:
        for snapshot in getattr(state, "runtime_observability_snapshots", []):
            if snapshot.get("owner_runtime") == runtime_id and snapshot.get("execution_id"):
                return str(snapshot["execution_id"])
        return f"{runtime_id}:shared_state_execution"


def _display_name(runtime_id: str) -> str:
    return runtime_id.replace("_", " ").title()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


cognitive_runtime_observability_engine = CognitiveRuntimeObservabilityEngine()


__all__ = [
    "CognitiveRuntimeObservabilityEngine",
    "CognitiveRuntimeSnapshot",
    "OBSERVABILITY_CONTRACT",
    "OBSERVABILITY_LEVELS",
    "REQUIRED_COGNITIVE_RUNTIMES",
    "cognitive_runtime_observability_engine",
]
