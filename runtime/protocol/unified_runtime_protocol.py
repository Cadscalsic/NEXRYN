"""Unified Cognitive Runtime Protocol for NEXRYN runtimes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


PROTOCOL_VERSION = "1.0.0"

MANDATORY_INTERFACE_FIELDS = (
    "runtime_name",
    "runtime_id",
    "runtime_version",
    "execution_id",
    "execution_mode",
    "execution_profile",
    "runtime_category",
    "owner_layer",
    "dependencies",
    "required_inputs",
    "optional_inputs",
    "expected_outputs",
    "generated_artifacts",
    "consumed_artifacts",
    "published_artifacts",
    "health",
    "confidence",
    "lifecycle",
    "observability_level",
    "governance_status",
    "resource_usage",
    "runtime_state",
    "failure_status",
    "recovery_status",
    "completion_status",
)

STANDARD_INPUT_FIELDS = (
    "required_artifacts",
    "required_context",
    "required_dependencies",
    "required_evidence",
    "required_knowledge",
    "required_memory",
    "required_runtime_services",
)

STANDARD_OUTPUT_FIELDS = (
    "produced_artifacts",
    "published_artifacts",
    "generated_metrics",
    "generated_evidence",
    "generated_context",
    "generated_knowledge",
    "generated_truth",
    "generated_memory",
)

STANDARD_CONFIDENCE_FIELDS = (
    "execution_confidence",
    "artifact_confidence",
    "evidence_confidence",
    "prediction_confidence",
    "reliability",
    "completeness",
    "consistency",
    "stability",
)

STANDARD_HEALTH_FIELDS = (
    "execution_health",
    "artifact_health",
    "lifecycle_health",
    "observability_health",
    "resource_health",
    "evidence_health",
    "protocol_compliance",
)

STANDARD_RESOURCE_FIELDS = (
    "cpu_time",
    "execution_time",
    "memory_usage",
    "artifact_count",
    "context_count",
    "evidence_count",
    "search_cost",
    "concept_cost",
    "energy_score",
    "efficiency_score",
)

STANDARD_DIAGNOSTIC_FIELDS = (
    "warnings",
    "errors",
    "recommendations",
    "recoverable_failures",
    "blocking_failures",
    "missing_inputs",
    "missing_outputs",
    "missing_artifacts",
    "protocol_violations",
)

STANDARD_SNAPSHOT_FIELDS = (
    "snapshot_id",
    "runtime",
    "runtime_id",
    "execution_id",
    "snapshot_type",
    "lifecycle_stage",
    "execution_stage",
    "status",
    "input_summary",
    "processing_summary",
    "output_summary",
    "artifacts",
    "confidence",
    "timestamp",
    "metrics",
    "observations",
    "warnings",
    "errors",
    "duration",
    "parent_execution",
    "episode_id",
    "summary",
)

STANDARD_CAPABILITIES = (
    "Concept Extraction",
    "Program Synthesis",
    "Adaptive Search",
    "Evidence Construction",
    "Truth Validation",
    "Memory Encoding",
    "Dependency Resolution",
    "Process Construction",
    "Reuse Discovery",
    "Causal Analysis",
)

RUNTIME_STATES = (
    "CREATED",
    "INITIALIZED",
    "READY",
    "RUNNING",
    "WAITING",
    "PUBLISHING",
    "FINALIZING",
    "COMPLETED",
    "ARCHIVED",
)

LEGAL_TRANSITIONS = {
    "CREATED": {"INITIALIZED"},
    "INITIALIZED": {"READY"},
    "READY": {"RUNNING"},
    "RUNNING": {"WAITING", "PUBLISHING", "FINALIZING"},
    "WAITING": {"RUNNING", "PUBLISHING", "FINALIZING"},
    "PUBLISHING": {"FINALIZING"},
    "FINALIZING": {"COMPLETED"},
    "COMPLETED": {"ARCHIVED"},
    "ARCHIVED": set(),
}

CAPABILITY_HINTS = {
    "concept": ("Concept Extraction",),
    "program": ("Program Synthesis",),
    "search": ("Adaptive Search",),
    "evidence": ("Evidence Construction",),
    "truth": ("Truth Validation",),
    "memory": ("Memory Encoding",),
    "dependency": ("Dependency Resolution",),
    "process": ("Process Construction",),
    "reuse": ("Reuse Discovery",),
    "causal": ("Causal Analysis",),
}


@dataclass(frozen=True)
class ProtocolVersion:
    major: int = 1
    minor: int = 0
    patch: int = 0
    backward_compatibility: str = "minor_and_patch"
    deprecation_policy: str = "major_versions_require_negotiation"

    @property
    def version(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["version"] = self.version
        return data


@dataclass
class RuntimeDiagnostics:
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    recoverable_failures: list[str] = field(default_factory=list)
    blocking_failures: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)
    missing_artifacts: list[str] = field(default_factory=list)
    protocol_violations: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedRuntimeDescriptor:
    runtime_name: str
    runtime_id: str
    runtime_version: str
    execution_id: str
    execution_mode: str
    execution_profile: dict[str, Any]
    runtime_category: str
    owner_layer: str
    dependencies: list[str]
    required_inputs: dict[str, list[str]]
    optional_inputs: dict[str, list[str]]
    expected_outputs: dict[str, list[str]]
    generated_artifacts: list[str]
    consumed_artifacts: list[str]
    published_artifacts: list[str]
    health: dict[str, float]
    confidence: dict[str, float]
    lifecycle: list[str]
    observability_level: int
    governance_status: dict[str, bool]
    resource_usage: dict[str, float]
    runtime_state: str
    failure_status: str
    recovery_status: str
    completion_status: str
    protocol_version: str = PROTOCOL_VERSION
    capabilities: list[str] = field(default_factory=list)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    supported_snapshot_types: list[str] = field(default_factory=list)
    snapshot_schema_version: str = "1.0.0"
    snapshot_producer: str = ""
    snapshot_consumer: str = ""
    telemetry: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    reasoning_state: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeLifecycleValidator:
    """Validates canonical runtime state transitions."""

    def validate(self, states: list[str]) -> dict[str, Any]:
        violations = []
        normalized = [str(state).upper() for state in states if state]
        for source, target in zip(normalized, normalized[1:]):
            if target not in LEGAL_TRANSITIONS.get(source, set()):
                violations.append({
                    "from": source,
                    "to": target,
                    "violation": "illegal_runtime_state_transition",
                })
        return {
            "valid": not violations,
            "states": normalized,
            "violations": violations,
        }


class UnifiedRuntimeProtocol:
    """Normalizes runtimes into one deterministic semantic contract."""

    system_name = "unified_runtime_protocol"

    def __init__(self, version: ProtocolVersion | None = None) -> None:
        self.version = version or ProtocolVersion()
        self.lifecycle_validator = RuntimeLifecycleValidator()

    def descriptor_from_record(
        self,
        runtime_id: str,
        record: Mapping[str, Any],
        observability: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        observability = observability if isinstance(observability, Mapping) else {}
        diagnostics = self._diagnostics(record, observability)
        lifecycle = self._canonical_lifecycle(record.get("lifecycle"))
        lifecycle_result = self.lifecycle_validator.validate(lifecycle)
        if not lifecycle_result["valid"]:
            diagnostics.protocol_violations.append("illegal_lifecycle_transition")
        confidence = self._confidence(record, observability, diagnostics)
        health = self._health(record, observability, diagnostics)
        generated = self._artifact_ids(record, "generated_artifacts", "produced_artifacts")
        consumed = self._artifact_ids(record, "consumed_artifacts")
        published = self._artifact_ids(record, "published_artifacts")
        descriptor = UnifiedRuntimeDescriptor(
            runtime_name=str(record.get("runtime_name") or _display_name(runtime_id)),
            runtime_id=runtime_id,
            runtime_version=str(record.get("runtime_version") or "1.0.0"),
            execution_id=str(record.get("execution_id") or f"{runtime_id}:protocol_execution"),
            execution_mode=str(record.get("execution_mode") or "standard"),
            execution_profile=dict(record.get("execution_profile") or {}),
            runtime_category=str(record.get("runtime_category") or "cognitive_runtime"),
            owner_layer=str(record.get("owner_layer") or record.get("owner") or runtime_id),
            dependencies=list(record.get("dependencies") or record.get("children") or []),
            required_inputs=self._input_contract(record, required=True),
            optional_inputs=self._input_contract(record, required=False),
            expected_outputs=self._output_contract(record),
            generated_artifacts=generated,
            consumed_artifacts=consumed,
            published_artifacts=published,
            health=health,
            confidence=confidence,
            lifecycle=lifecycle,
            observability_level=int(record.get("observability_level") or observability.get("observability_level") or 5),
            governance_status=self._governance_status(diagnostics),
            resource_usage=self._resource_usage(record),
            runtime_state=lifecycle[-1] if lifecycle else "COMPLETED",
            failure_status="BLOCKED" if diagnostics.blocking_failures else "NONE",
            recovery_status="RECOVERABLE" if diagnostics.recoverable_failures else "STABLE",
            completion_status="COMPLETE" if not diagnostics.blocking_failures else "INCOMPLETE",
            protocol_version=self.version.version,
            capabilities=self._capabilities(runtime_id, record),
            snapshots=self._snapshots(runtime_id, record),
            supported_snapshot_types=list(record.get("supported_snapshot_types") or []),
            snapshot_schema_version=str(record.get("snapshot_schema_version") or "1.0.0"),
            snapshot_producer=str(record.get("snapshot_producer") or ""),
            snapshot_consumer=str(record.get("snapshot_consumer") or ""),
            telemetry=dict(record.get("telemetry") or {}),
            diagnostics=diagnostics.as_dict(),
            evidence=list(record.get("evidence") or []),
            reasoning_state=dict(record.get("reasoning_state") or record.get("graph") or {}),
        )
        return descriptor.as_dict()

    def normalize_registry(
        self,
        runtime_registry: Mapping[str, Mapping[str, Any]],
        observability_report: Mapping[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        observability_report = (
            observability_report if isinstance(observability_report, Mapping) else {}
        )
        runtime_reports = observability_report.get("runtime_reports", {})
        normalized = {}
        for runtime_id, record in sorted(runtime_registry.items()):
            runtime_observability = (
                runtime_reports.get(runtime_id, {})
                if isinstance(runtime_reports, Mapping)
                else {}
            )
            normalized[runtime_id] = self.descriptor_from_record(
                runtime_id,
                record if isinstance(record, Mapping) else {},
                runtime_observability,
            )
        return normalized

    def build_snapshot(
        self,
        runtime: Mapping[str, Any],
        lifecycle_stage: str | None = None,
    ) -> dict[str, Any]:
        runtime_id = str(runtime.get("runtime_id") or "unknown_runtime")
        snapshots = runtime.get("snapshots") if isinstance(runtime.get("snapshots"), list) else []
        input_summary = runtime.get("required_inputs", {})
        output_summary = runtime.get("expected_outputs", {})
        artifacts = sorted(set(
            list(runtime.get("generated_artifacts") or [])
            + list(runtime.get("consumed_artifacts") or [])
            + list(runtime.get("published_artifacts") or [])
        ))
        return {
            "snapshot_id": f"ucrp:{runtime_id}:{len(snapshots)}",
            "runtime": runtime_id,
            "execution_id": runtime.get("execution_id"),
            "lifecycle_stage": lifecycle_stage or runtime.get("runtime_state") or "COMPLETED",
            "input_summary": input_summary,
            "processing_summary": {
                "capabilities": list(runtime.get("capabilities") or []),
                "resource_usage": dict(runtime.get("resource_usage") or {}),
            },
            "output_summary": output_summary,
            "artifacts": artifacts,
            "confidence": dict(runtime.get("confidence") or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": f"{runtime_id} protocol snapshot",
        }

    def validate_descriptor(self, runtime: Mapping[str, Any]) -> dict[str, Any]:
        missing_interfaces = [
            field_name for field_name in MANDATORY_INTERFACE_FIELDS
            if field_name not in runtime
        ]
        missing_inputs = [
            field_name for field_name in STANDARD_INPUT_FIELDS
            if field_name not in runtime.get("required_inputs", {})
        ]
        missing_outputs = [
            field_name for field_name in STANDARD_OUTPUT_FIELDS
            if field_name not in runtime.get("expected_outputs", {})
        ]
        missing_confidence = [
            field_name for field_name in STANDARD_CONFIDENCE_FIELDS
            if field_name not in runtime.get("confidence", {})
        ]
        missing_health = [
            field_name for field_name in STANDARD_HEALTH_FIELDS
            if field_name not in runtime.get("health", {})
        ]
        missing_resources = [
            field_name for field_name in STANDARD_RESOURCE_FIELDS
            if field_name not in runtime.get("resource_usage", {})
        ]
        lifecycle = self.lifecycle_validator.validate(list(runtime.get("lifecycle") or []))
        diagnostics = runtime.get("diagnostics", {})
        protocol_violations = list(diagnostics.get("protocol_violations", [])) if isinstance(diagnostics, Mapping) else []
        if not lifecycle["valid"]:
            protocol_violations.append("illegal_lifecycle_transition")
        missing_total = (
            len(missing_interfaces)
            + len(missing_inputs)
            + len(missing_outputs)
            + len(missing_confidence)
            + len(missing_health)
            + len(missing_resources)
            + len(protocol_violations)
        )
        denominator = (
            len(MANDATORY_INTERFACE_FIELDS)
            + len(STANDARD_INPUT_FIELDS)
            + len(STANDARD_OUTPUT_FIELDS)
            + len(STANDARD_CONFIDENCE_FIELDS)
            + len(STANDARD_HEALTH_FIELDS)
            + len(STANDARD_RESOURCE_FIELDS)
        )
        compliance_score = round(max(0.0, 1.0 - missing_total / max(denominator, 1)), 4)
        return {
            "runtime_id": runtime.get("runtime_id"),
            "compliant": missing_total == 0,
            "compliance_score": compliance_score,
            "missing_interfaces": missing_interfaces,
            "missing_inputs": missing_inputs,
            "missing_outputs": missing_outputs,
            "missing_confidence": missing_confidence,
            "missing_health": missing_health,
            "missing_resources": missing_resources,
            "protocol_violations": protocol_violations,
            "lifecycle": lifecycle,
        }

    def _canonical_lifecycle(self, lifecycle: Any) -> list[str]:
        if isinstance(lifecycle, list) and all(str(item).upper() in RUNTIME_STATES for item in lifecycle):
            return [str(item).upper() for item in lifecycle]
        return [
            "CREATED",
            "INITIALIZED",
            "READY",
            "RUNNING",
            "PUBLISHING",
            "FINALIZING",
            "COMPLETED",
        ]

    def _input_contract(self, record: Mapping[str, Any], required: bool) -> dict[str, list[str]]:
        source = record.get("required_inputs" if required else "optional_inputs")
        if isinstance(source, Mapping):
            contract = {
                field_name: _string_list(source.get(field_name))
                for field_name in STANDARD_INPUT_FIELDS
            }
        else:
            contract = {field_name: [] for field_name in STANDARD_INPUT_FIELDS}
        if required:
            inputs = _string_list(record.get("inputs"))
            contract["required_artifacts"] = sorted(set(contract["required_artifacts"] + inputs))
        return contract

    def _output_contract(self, record: Mapping[str, Any]) -> dict[str, list[str]]:
        source = record.get("expected_outputs")
        if isinstance(source, Mapping):
            contract = {
                field_name: _string_list(source.get(field_name))
                for field_name in STANDARD_OUTPUT_FIELDS
            }
        else:
            contract = {field_name: [] for field_name in STANDARD_OUTPUT_FIELDS}
        produced = self._artifact_ids(record, "generated_artifacts", "produced_artifacts")
        published = self._artifact_ids(record, "published_artifacts")
        metrics = list((record.get("metrics") or {}).keys()) if isinstance(record.get("metrics"), Mapping) else []
        contract["produced_artifacts"] = sorted(set(contract["produced_artifacts"] + produced))
        contract["published_artifacts"] = sorted(set(contract["published_artifacts"] + published))
        contract["generated_metrics"] = sorted(set(contract["generated_metrics"] + [str(item) for item in metrics]))
        return contract

    def _capabilities(self, runtime_id: str, record: Mapping[str, Any]) -> list[str]:
        declared = _string_list(record.get("capabilities"))
        inferred = []
        text = f"{runtime_id} {record.get('runtime_name', '')}".lower()
        for token, capabilities in CAPABILITY_HINTS.items():
            if token in text:
                inferred.extend(capabilities)
        return sorted(set(declared + inferred)) or ["Cognitive Runtime Service"]

    def _resource_usage(self, record: Mapping[str, Any]) -> dict[str, float]:
        metrics = record.get("metrics") if isinstance(record.get("metrics"), Mapping) else {}
        return {
            "cpu_time": _number(record.get("cpu_time")),
            "execution_time": _number(record.get("duration_seconds")),
            "memory_usage": _number(record.get("memory_cost")),
            "artifact_count": _number(metrics.get("produced_artifact_count") or metrics.get("published_artifact_count")),
            "context_count": _number(metrics.get("context_count")),
            "evidence_count": _number(metrics.get("evidence_count") or metrics.get("truth_candidates")),
            "search_cost": _number(metrics.get("search_cost")),
            "concept_cost": _number(metrics.get("concept_cost")),
            "energy_score": round(max(0.0, 1.0 - _number(record.get("duration_seconds"))), 4),
            "efficiency_score": _number(metrics.get("search_efficiency"), default=1.0),
        }

    def _confidence(
        self,
        record: Mapping[str, Any],
        observability: Mapping[str, Any],
        diagnostics: RuntimeDiagnostics,
    ) -> dict[str, float]:
        coverage = _number(record.get("coverage"), default=1.0)
        health = _number(observability.get("health_score"), default=coverage)
        penalty = 0.1 if diagnostics.protocol_violations else 0.0
        base = round(max(0.0, min(1.0, max(coverage, health) - penalty)), 4)
        return {
            "execution_confidence": base,
            "artifact_confidence": _number(record.get("artifact_confidence"), default=base),
            "evidence_confidence": _number(record.get("evidence_confidence"), default=base),
            "prediction_confidence": _number(record.get("prediction_confidence"), default=base),
            "reliability": base,
            "completeness": base,
            "consistency": 0.0 if diagnostics.protocol_violations else 1.0,
            "stability": 0.0 if diagnostics.blocking_failures else 1.0,
        }

    def _health(
        self,
        record: Mapping[str, Any],
        observability: Mapping[str, Any],
        diagnostics: RuntimeDiagnostics,
    ) -> dict[str, float]:
        coverage = _number(record.get("coverage"), default=1.0)
        runtime_health = observability.get("runtime_health", {})
        obs_health = (
            _number(runtime_health.get("observability_score"), default=coverage)
            if isinstance(runtime_health, Mapping)
            else coverage
        )
        protocol = 0.0 if diagnostics.protocol_violations else 1.0
        return {
            "execution_health": 0.0 if diagnostics.blocking_failures else 1.0,
            "artifact_health": _number(runtime_health.get("artifact_completeness"), default=coverage) if isinstance(runtime_health, Mapping) else coverage,
            "lifecycle_health": _number(runtime_health.get("lifecycle_completeness"), default=1.0) if isinstance(runtime_health, Mapping) else 1.0,
            "observability_health": obs_health,
            "resource_health": 1.0,
            "evidence_health": coverage,
            "protocol_compliance": protocol,
        }

    def _governance_status(self, diagnostics: RuntimeDiagnostics) -> dict[str, bool]:
        compliant = not diagnostics.protocol_violations and not diagnostics.blocking_failures
        return {
            "protocol_compliance": compliant,
            "lifecycle_compliance": "illegal_lifecycle_transition" not in diagnostics.protocol_violations,
            "artifact_compliance": not diagnostics.missing_artifacts,
            "observability_compliance": "missing_snapshots" not in diagnostics.warnings,
            "security_compliance": True,
            "truth_compliance": True,
            "memory_compliance": True,
        }

    def _diagnostics(
        self,
        record: Mapping[str, Any],
        observability: Mapping[str, Any],
    ) -> RuntimeDiagnostics:
        warnings = []
        if not record.get("snapshots") and not observability.get("snapshots"):
            warnings.append("missing_snapshots")
        if not record.get("telemetry") and not observability.get("telemetry_completeness"):
            warnings.append("missing_telemetry")
        return RuntimeDiagnostics(warnings=warnings)

    def _snapshots(self, runtime_id: str, record: Mapping[str, Any]) -> list[dict[str, Any]]:
        source = record.get("snapshots")
        if not isinstance(source, list):
            return []
        snapshots = []
        for index, snapshot in enumerate(source[:20]):
            if isinstance(snapshot, Mapping) and _is_runtime_snapshot(snapshot):
                snapshots.append(dict(snapshot))
                continue
            snapshots.append({
                "snapshot_id": f"ucrp:{runtime_id}:{index}",
                "runtime": runtime_id,
                "execution_id": record.get("execution_id"),
                "lifecycle_stage": "RUNNING" if index < len(source) - 1 else "COMPLETED",
                "input_summary": {},
                "processing_summary": dict(snapshot) if isinstance(snapshot, Mapping) else {"value": str(snapshot)},
                "output_summary": {},
                "artifacts": self._artifact_ids(record, "generated_artifacts", "published_artifacts"),
                "confidence": {"execution_confidence": _number(record.get("coverage"), default=1.0)},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": f"{runtime_id} normalized snapshot",
            })
        return snapshots

    def _artifact_ids(self, record: Mapping[str, Any], *keys: str) -> list[str]:
        ids = []
        for key in keys:
            value = record.get(key)
            if isinstance(value, Mapping):
                ids.extend(str(item) for item in value.keys())
            else:
                ids.extend(_string_list(value))
        return sorted(set(ids))


class RuntimeDiscoveryRegistry:
    """Self-describing runtime discovery table."""

    system_name = "runtime_discovery_registry"

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, Any]] = {}

    def register(self, descriptor: Mapping[str, Any]) -> dict[str, Any]:
        runtime_id = str(descriptor.get("runtime_id") or "")
        if not runtime_id:
            raise ValueError("runtime_id is required for runtime discovery")
        record = {
            "identity": {
                "runtime_id": runtime_id,
                "runtime_name": descriptor.get("runtime_name"),
                "version": descriptor.get("runtime_version"),
                "protocol": descriptor.get("protocol_version"),
            },
            "capabilities": list(descriptor.get("capabilities") or []),
            "dependencies": list(descriptor.get("dependencies") or []),
            "inputs": dict(descriptor.get("required_inputs") or {}),
            "outputs": dict(descriptor.get("expected_outputs") or {}),
            "health": dict(descriptor.get("health") or {}),
            "observability": {
                "level": descriptor.get("observability_level"),
                "snapshots": len(descriptor.get("snapshots") or []),
                "supported_snapshot_types": list(
                    descriptor.get("supported_snapshot_types") or []
                ),
                "snapshot_schema_version": descriptor.get("snapshot_schema_version"),
                "snapshot_producer": descriptor.get("snapshot_producer"),
                "snapshot_consumer": descriptor.get("snapshot_consumer"),
            },
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self._registry[runtime_id] = record
        return dict(record)

    def discover(self) -> dict[str, dict[str, Any]]:
        return dict(self._registry)

    def get(self, runtime_id: str) -> dict[str, Any] | None:
        record = self._registry.get(runtime_id)
        return dict(record) if record else None


class ProtocolNegotiator:
    """Negotiates protocol compatibility before runtime communication."""

    def negotiate(
        self,
        runtime_a: Mapping[str, Any],
        runtime_b: Mapping[str, Any],
    ) -> dict[str, Any]:
        version_a = str(runtime_a.get("protocol_version") or "0.0.0")
        version_b = str(runtime_b.get("protocol_version") or "0.0.0")
        compatible = version_a.split(".")[0] == version_b.split(".")[0]
        outputs_a = _flatten_contract(runtime_a.get("expected_outputs"))
        inputs_b = _flatten_contract(runtime_b.get("required_inputs"))
        supported_artifacts = sorted(outputs_a & inputs_b)
        return {
            "runtime_a": runtime_a.get("runtime_id"),
            "runtime_b": runtime_b.get("runtime_id"),
            "protocol_version_a": version_a,
            "protocol_version_b": version_b,
            "compatible": compatible,
            "capabilities": {
                str(runtime_a.get("runtime_id")): list(runtime_a.get("capabilities") or []),
                str(runtime_b.get("runtime_id")): list(runtime_b.get("capabilities") or []),
            },
            "expected_inputs": dict(runtime_b.get("required_inputs") or {}),
            "expected_outputs": dict(runtime_a.get("expected_outputs") or {}),
            "supported_artifact_types": supported_artifacts,
            "communication_status": "READY" if compatible else "BLOCKED_PROTOCOL_VERSION",
        }


class ProtocolComplianceEngine:
    """Builds the UNIFIED_RUNTIME_PROTOCOL_REPORT."""

    system_name = "protocol_compliance_engine"

    def __init__(
        self,
        protocol: UnifiedRuntimeProtocol | None = None,
        discovery: RuntimeDiscoveryRegistry | None = None,
    ) -> None:
        self.protocol = protocol or UnifiedRuntimeProtocol()
        self.discovery = discovery or RuntimeDiscoveryRegistry()

    def build_report(
        self,
        runtime_registry: Mapping[str, Mapping[str, Any]],
        observability_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = self.protocol.normalize_registry(
            runtime_registry,
            observability_report=observability_report,
        )
        runtime_reports = {}
        for runtime_id, descriptor in normalized.items():
            self.discovery.register(descriptor)
            validation = self.protocol.validate_descriptor(descriptor)
            runtime_reports[runtime_id] = {
                "runtime_identity": {
                    "runtime_id": runtime_id,
                    "runtime_name": descriptor["runtime_name"],
                    "runtime_version": descriptor["runtime_version"],
                    "execution_id": descriptor["execution_id"],
                },
                "protocol_version": descriptor["protocol_version"],
                "compliance_score": validation["compliance_score"],
                "capabilities": descriptor["capabilities"],
                "inputs": descriptor["required_inputs"],
                "outputs": descriptor["expected_outputs"],
                "artifact_types": self._artifact_types(descriptor),
                "health": descriptor["health"],
                "observability": {
                    "level": descriptor["observability_level"],
                    "snapshot_count": len(descriptor["snapshots"]),
                    "latest_snapshot": (
                        descriptor["snapshots"][-1]
                        if descriptor["snapshots"] else None
                    ),
                    "snapshot_types": [
                        snapshot.get("snapshot_type")
                        for snapshot in descriptor["snapshots"]
                    ],
                    "snapshot_duration": round(
                        sum(_number(snapshot.get("duration")) for snapshot in descriptor["snapshots"]),
                        9,
                    ),
                    "snapshot_generation_success": bool(descriptor["snapshots"]),
                    "snapshot_generation_failures": [
                        snapshot for snapshot in descriptor["snapshots"]
                        if snapshot.get("errors")
                    ],
                    "telemetry_present": bool(descriptor["telemetry"]),
                },
                "lifecycle": validation["lifecycle"],
                "diagnostics": descriptor["diagnostics"],
                "compatibility": {
                    "semantic_version": ProtocolVersion().as_dict(),
                    "backward_compatible": True,
                },
                "missing_interfaces": validation["missing_interfaces"],
                "protocol_violations": validation["protocol_violations"],
                "descriptor": descriptor,
            }
        scores = [item["compliance_score"] for item in runtime_reports.values()]
        overall_score = round(sum(scores) / max(len(scores), 1), 4)
        return {
            "system": self.system_name,
            "UNIFIED_RUNTIME_PROTOCOL_REPORT": True,
            "protocol_version": self.protocol.version.as_dict(),
            "runtime_protocol_contract": {
                "mandatory_interfaces": list(MANDATORY_INTERFACE_FIELDS),
                "standard_inputs": list(STANDARD_INPUT_FIELDS),
                "standard_outputs": list(STANDARD_OUTPUT_FIELDS),
                "standard_confidence": list(STANDARD_CONFIDENCE_FIELDS),
                "standard_health": list(STANDARD_HEALTH_FIELDS),
                "standard_resources": list(STANDARD_RESOURCE_FIELDS),
                "standard_diagnostics": list(STANDARD_DIAGNOSTIC_FIELDS),
                "standard_snapshots": list(STANDARD_SNAPSHOT_FIELDS),
                "standard_states": list(RUNTIME_STATES),
                "artifact_operations": [
                    "create_artifact",
                    "consume_artifact",
                    "publish_artifact",
                    "validate_artifact",
                    "promote_artifact",
                    "archive_artifact",
                ],
                "delete_operations_allowed": False,
            },
            "runtime_reports": runtime_reports,
            "runtime_discovery": self.discovery.discover(),
            "protocol_compliance": {
                "runtime_count": len(runtime_reports),
                "compliance_score": overall_score,
                "compliance_percentage": round(overall_score * 100.0, 2),
                "fully_compliant": overall_score == 1.0,
                "non_compliant_runtimes": [
                    runtime_id for runtime_id, report in runtime_reports.items()
                    if report["compliance_score"] < 1.0
                ],
            },
            "world_model_integration": {
                "communicates_only_through_protocol": True,
                "runtime_internals_access_allowed": False,
                "runtimes_replaceable": True,
            },
            "dna_integration": {
                "observes_protocol_compliant_cognition_only": True,
                "evolves_from_behavior_not_implementation": True,
            },
            "meta_cognition": {
                "protocol_quality_evaluable": True,
                "violating_runtimes": [
                    runtime_id for runtime_id, report in runtime_reports.items()
                    if report["protocol_violations"]
                ],
                "hidden_interface_runtimes": [
                    runtime_id for runtime_id, report in runtime_reports.items()
                    if report["missing_interfaces"]
                ],
                "protocol_update_required": False,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _artifact_types(self, descriptor: Mapping[str, Any]) -> list[str]:
        values = []
        for contract_name in ("required_inputs", "expected_outputs"):
            contract = descriptor.get(contract_name)
            if isinstance(contract, Mapping):
                for items in contract.values():
                    values.extend(_string_list(items))
        return sorted(set(values))


def build_unified_runtime_protocol_report(
    runtime_registry: Mapping[str, Mapping[str, Any]],
    observability_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return ProtocolComplianceEngine().build_report(
        runtime_registry,
        observability_report=observability_report,
    )


def _flatten_contract(contract: Any) -> set[str]:
    if not isinstance(contract, Mapping):
        return set()
    values: set[str] = set()
    for items in contract.values():
        values.update(_string_list(items))
    return values


def _is_runtime_snapshot(snapshot: Mapping[str, Any]) -> bool:
    required = {
        "snapshot_id",
        "runtime_id",
        "execution_id",
        "snapshot_type",
        "timestamp",
        "execution_stage",
        "status",
        "input_summary",
        "output_summary",
        "metrics",
        "observations",
        "warnings",
        "errors",
        "duration",
        "parent_execution",
        "episode_id",
    }
    legacy = {
        "snapshot_id",
        "runtime",
        "execution_id",
        "lifecycle_stage",
        "input_summary",
        "processing_summary",
        "output_summary",
        "artifacts",
        "confidence",
        "timestamp",
        "summary",
    }
    keys = set(snapshot.keys())
    return required.issubset(keys) or legacy.issubset(keys)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [str(item) for item in value.keys()]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _display_name(runtime_id: str) -> str:
    return runtime_id.replace("_", " ").title()


__all__ = [
    "CAPABILITY_HINTS",
    "LEGAL_TRANSITIONS",
    "MANDATORY_INTERFACE_FIELDS",
    "PROTOCOL_VERSION",
    "ProtocolComplianceEngine",
    "ProtocolNegotiator",
    "ProtocolVersion",
    "RuntimeDiagnostics",
    "RuntimeDiscoveryRegistry",
    "RuntimeLifecycleValidator",
    "RUNTIME_STATES",
    "STANDARD_CAPABILITIES",
    "STANDARD_CONFIDENCE_FIELDS",
    "STANDARD_DIAGNOSTIC_FIELDS",
    "STANDARD_HEALTH_FIELDS",
    "STANDARD_INPUT_FIELDS",
    "STANDARD_OUTPUT_FIELDS",
    "STANDARD_RESOURCE_FIELDS",
    "STANDARD_SNAPSHOT_FIELDS",
    "UnifiedRuntimeDescriptor",
    "UnifiedRuntimeProtocol",
    "build_unified_runtime_protocol_report",
]
