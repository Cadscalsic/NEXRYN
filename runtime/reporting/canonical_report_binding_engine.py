from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable


class BindingState(str, Enum):
    BOUND = "BOUND"
    HIDDEN = "HIDDEN"
    COMPRESSED = "COMPRESSED"
    EXTERNALIZED = "EXTERNALIZED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    INVALID_SOURCE = "INVALID_SOURCE"
    UNBOUND = "UNBOUND"


class RepresentationState(str, Enum):
    EXPOSED = "EXPOSED"
    HIDDEN = "HIDDEN"
    COMPRESSED = "COMPRESSED"
    EXTERNALIZED = "EXTERNALIZED"


VALID_VISIBILITY_LEVELS = {"MINIMAL", "NORMAL", "DIAGNOSTIC"}
VALID_REPRESENTATION_TYPES = {
    "boolean",
    "count",
    "duration",
    "list",
    "map",
    "metric",
    "number",
    "percentage",
    "status",
    "summary",
    "text",
}


@dataclass(frozen=True)
class CanonicalSource:
    source_name: str
    payload: dict[str, Any]
    accessible: bool = True

    def as_registry_entry(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "accessible": self.accessible,
            "field_count": len(self.payload),
        }


@dataclass(frozen=True)
class ReportFieldBinding:
    field_name: str
    field_owner: str
    canonical_source: str
    visibility_policy: tuple[str, ...]
    compression_policy: str = "EXPOSED"
    externalization_policy: bool = False
    representation_type: str = "text"
    source_fields: tuple[str, ...] = ()
    required: bool = False

    def visible_at(self, report_level: str) -> bool:
        return report_level.upper() in self.visibility_policy

    def as_contract(self) -> dict[str, Any]:
        data = asdict(self)
        data["visibility_policy"] = list(self.visibility_policy)
        data["source_fields"] = list(self.source_fields)
        return data


@dataclass(frozen=True)
class BoundReportField:
    field_name: str
    field_owner: str
    canonical_source: str
    visibility_policy: tuple[str, ...]
    compression_policy: str
    externalization_policy: bool
    binding_status: str
    binding_confidence: float
    representation_type: str
    representation_state: str
    value: Any = None
    display_value: str = "Not Available"
    source_field: str | None = None
    validation_errors: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["visibility_policy"] = list(self.visibility_policy)
        data["validation_errors"] = list(self.validation_errors)
        return data


class CanonicalReportBindingEngine:
    """Owns deterministic bindings from canonical report state to report fields."""

    DISCOVERABLE_SOURCE_NAMES = {
        "execution_timing",
        "execution_timing_state",
        "execution_registry",
        "metric_attribution_state",
        "runtime_metrics",
        "runtime_snapshots",
        "program_registry",
        "truth_metrics",
        "memory_metrics",
        "search_metrics",
        "knowledge_pipeline_metrics",
        "representation_metrics",
    }

    def __init__(
        self,
        field_bindings: Iterable[ReportFieldBinding] | None = None,
    ):
        self.field_bindings = list(field_bindings or self._default_bindings())
        self.metrics = self._empty_metrics()
        self.report_field_registry: dict[str, dict[str, Any]] = {}
        self.canonical_source_registry: dict[str, dict[str, Any]] = {}

    def bind(
        self,
        report_state: dict[str, Any] | None,
        *,
        runtime_metadata: dict[str, Any] | None = None,
        report_level: str = "normal",
    ) -> dict[str, Any]:
        report_state = report_state if isinstance(report_state, dict) else {}
        runtime_metadata = (
            runtime_metadata if isinstance(runtime_metadata, dict) else {}
        )
        normalized_level = self._normalize_report_level(report_level)
        sources = self.discover_sources(
            report_state,
            runtime_metadata=runtime_metadata,
        )
        registry_errors = self.validate_field_registry(self.field_bindings)
        bound_fields: dict[str, BoundReportField] = {}

        for definition in self.field_bindings:
            field_errors = [
                error
                for error in registry_errors
                if error.endswith(f":{definition.field_name}")
            ]
            source = sources.get(definition.canonical_source)
            source_exists = source is not None
            source_accessible = bool(source and source.accessible)

            if field_errors:
                bound = self._invalid_field(definition, field_errors)
            elif not definition.visible_at(normalized_level):
                bound = self._policy_field(definition, normalized_level)
            elif not source_exists or not source_accessible:
                bound = self._missing_source_field(
                    definition,
                    source_exists=source_exists,
                )
            else:
                value, source_field = self._resolve_value(definition, source)
                bound = self._bound_field(definition, value, source_field)
            bound_fields[definition.field_name] = bound

        validation_errors = list(registry_errors)
        validation_errors.extend(
            self._validate_required_fields(bound_fields, normalized_level)
        )
        validation_errors.extend(self._validate_no_unknown(bound_fields))

        self.canonical_source_registry = {
            name: source.as_registry_entry()
            for name, source in sorted(sources.items())
        }
        self.report_field_registry = self._build_report_field_registry(
            bound_fields,
        )
        diagnostics = self._build_diagnostics(bound_fields, validation_errors)
        self.metrics = diagnostics
        return {
            "report_level": normalized_level,
            "canonical_source_registry": deepcopy(self.canonical_source_registry),
            "report_field_registry": deepcopy(self.report_field_registry),
            "field_bindings": {
                name: field.as_dict()
                for name, field in sorted(bound_fields.items())
            },
            "field_values": {
                name: field.display_value
                for name, field in sorted(bound_fields.items())
            },
            "binding_diagnostics": diagnostics,
        }

    def discover_sources(
        self,
        report_state: dict[str, Any] | None,
        *,
        runtime_metadata: dict[str, Any] | None = None,
    ) -> dict[str, CanonicalSource]:
        report_state = report_state if isinstance(report_state, dict) else {}
        runtime_metadata = (
            runtime_metadata if isinstance(runtime_metadata, dict) else {}
        )
        performance = self._first_dict(
            report_state,
            "performance_report",
            "PERFORMANCE_REPORT",
        )
        timing_visibility = self._build_timing_visibility(
            report_state,
            performance,
            runtime_metadata,
        )
        sources = {
            "report_state": CanonicalSource("report_state", report_state),
            "runtime_metadata": CanonicalSource(
                "runtime_metadata",
                runtime_metadata,
            ),
            "runtime_metrics": CanonicalSource(
                "runtime_metrics",
                self._merge_dicts(
                    self._first_dict(report_state, "runtime_metrics"),
                    self._first_dict(performance, "runtime_metrics"),
                    runtime_metadata,
                ),
            ),
            "performance_report": CanonicalSource(
                "performance_report",
                performance,
            ),
            "execution_timing_state": CanonicalSource(
                "execution_timing_state",
                timing_visibility,
            ),
            "execution_registry": CanonicalSource(
                "execution_registry",
                self._merge_dicts(
                    report_state,
                    self._first_dict(report_state, "RUNTIME_LIFECYCLE_REPORT", "runtime_lifecycle_report"),
                    self._first_dict(performance, "RUNTIME_LIFECYCLE_REPORT", "runtime_lifecycle_report"),
                ),
            ),
            "execution_binding_registry": CanonicalSource(
                "execution_binding_registry",
                self._merge_dicts(
                    self._first_dict(report_state, "EXECUTION_BINDING_REPORT", "execution_binding_report"),
                    self._first_dict(performance, "EXECUTION_BINDING_REPORT", "execution_binding_report"),
                ),
            ),
            "search_metrics": CanonicalSource(
                "search_metrics",
                self._merge_dicts(
                    report_state,
                    self._first_dict(report_state, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "COGNITIVE_ROUTE_INTELLIGENCE_REPORT"),
                    self._first_dict(performance, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "COGNITIVE_ROUTE_INTELLIGENCE_REPORT"),
                    self._first_dict(report_state, "search_metrics"),
                ),
            ),
            "program_registry": CanonicalSource(
                "program_registry",
                self._merge_dicts(
                    report_state,
                    self._first_dict(report_state, "PROGRAM_SYNTHESIS_REPORT", "program_synthesis_report"),
                    self._first_dict(performance, "PROGRAM_SYNTHESIS_REPORT", "program_synthesis_report"),
                    self._first_dict(report_state, "program_registry"),
                ),
            ),
            "truth_metrics": CanonicalSource(
                "truth_metrics",
                self._merge_dicts(
                    self._first_dict(report_state, "truth_metrics"),
                    self._first_dict(performance, "truth_metrics"),
                ),
            ),
            "memory_metrics": CanonicalSource(
                "memory_metrics",
                self._merge_dicts(
                    self._first_dict(report_state, "memory_metrics"),
                    self._first_dict(performance, "memory_metrics"),
                ),
            ),
            "knowledge_pipeline_metrics": CanonicalSource(
                "knowledge_pipeline_metrics",
                self._merge_dicts(
                    report_state,
                    self._first_dict(report_state, "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT", "KNOWLEDGE_PROPAGATION_REPORT", "knowledge_propagation_report"),
                    self._first_dict(performance, "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT", "KNOWLEDGE_PROPAGATION_REPORT", "knowledge_propagation_report"),
                    self._first_dict(report_state, "knowledge_pipeline_metrics"),
                ),
            ),
            "metric_attribution_state": CanonicalSource(
                "metric_attribution_state",
                self._merge_dicts(
                    self._first_dict(report_state, "metric_attribution_state", "metric_ownership"),
                    self._first_dict(performance, "metric_attribution_state", "metric_ownership"),
                ),
            ),
            "representation_metrics": CanonicalSource(
                "representation_metrics",
                self._merge_dicts(
                    self._first_dict(report_state, "compact_report"),
                    self._first_dict(report_state, "representation_metrics"),
                ),
            ),
            "metric_sync_report": CanonicalSource(
                "metric_sync_report",
                self._merge_dicts(
                    self._first_dict(report_state, "RUNTIME_METRIC_SYNCHRONIZATION_REPORT", "runtime_metric_synchronization_report"),
                    self._first_dict(performance, "RUNTIME_METRIC_SYNCHRONIZATION_REPORT", "runtime_metric_synchronization_report"),
                ),
            ),
            "observability_report": CanonicalSource(
                "observability_report",
                self._merge_dicts(
                    self._first_dict(report_state, "RUNTIME_OBSERVABILITY_REPORT", "runtime_observability_report"),
                    self._first_dict(performance, "RUNTIME_OBSERVABILITY_REPORT", "runtime_observability_report"),
                ),
            ),
        }

        canonical_metrics = self._merge_dicts(
            self._first_dict(report_state, "canonical_metrics"),
            self._first_dict(performance, "canonical_metrics"),
        )
        if canonical_metrics:
            for source in list(sources.values()):
                if source.payload:
                    source.payload.update({
                        key: value
                        for key, value in canonical_metrics.items()
                        if key not in source.payload
                    })

        for name, payload in self._discover_named_sources(report_state).items():
            if name not in sources:
                sources[name] = CanonicalSource(name, payload)

        return sources

    def validate_field_registry(
        self,
        field_bindings: Iterable[ReportFieldBinding] | None = None,
    ) -> list[str]:
        bindings = list(field_bindings or self.field_bindings)
        errors: list[str] = []
        by_field: dict[str, ReportFieldBinding] = {}
        for binding in bindings:
            if not binding.field_name:
                errors.append("missing_field_name")
                continue
            existing = by_field.get(binding.field_name)
            if existing is not None:
                errors.append(f"conflicting_binding:{binding.field_name}")
                if existing.field_owner != binding.field_owner:
                    errors.append(f"duplicate_owner:{binding.field_name}")
                if existing.canonical_source != binding.canonical_source:
                    errors.append(f"conflicting_source:{binding.field_name}")
            by_field[binding.field_name] = binding
            if not binding.field_owner:
                errors.append(f"missing_owner:{binding.field_name}")
            if not binding.canonical_source:
                errors.append(f"missing_canonical_source:{binding.field_name}")
            if not set(binding.visibility_policy).issubset(VALID_VISIBILITY_LEVELS):
                errors.append(f"invalid_visibility_policy:{binding.field_name}")
            if binding.representation_type not in VALID_REPRESENTATION_TYPES:
                errors.append(f"invalid_representation_type:{binding.field_name}")
        return list(dict.fromkeys(errors))

    def report(self) -> dict[str, Any]:
        return dict(self.metrics)

    def _bound_field(
        self,
        definition: ReportFieldBinding,
        value: Any,
        source_field: str | None,
    ) -> BoundReportField:
        if value is None:
            return BoundReportField(
                **self._field_kwargs(definition),
                binding_status=BindingState.NOT_AVAILABLE.value,
                binding_confidence=0.0,
                representation_state=RepresentationState.EXPOSED.value,
                display_value="Not Available",
                source_field=source_field,
            )
        state = RepresentationState.EXPOSED
        status = BindingState.BOUND
        display = self._represent(value, definition.representation_type)
        if definition.compression_policy == "COMPRESSED":
            state = RepresentationState.COMPRESSED
            status = BindingState.COMPRESSED
            display = self._compressed_display(value)
        return BoundReportField(
            **self._field_kwargs(definition),
            binding_status=status.value,
            binding_confidence=1.0,
            representation_state=state.value,
            value=deepcopy(value),
            display_value=display,
            source_field=source_field,
        )

    def _policy_field(
        self,
        definition: ReportFieldBinding,
        report_level: str,
    ) -> BoundReportField:
        if definition.externalization_policy:
            status = BindingState.EXTERNALIZED
            state = RepresentationState.EXTERNALIZED
            display = "Externalized to Technical Appendix"
        else:
            status = BindingState.HIDDEN
            state = RepresentationState.HIDDEN
            display = "Hidden by Report Policy"
        return BoundReportField(
            **self._field_kwargs(definition),
            binding_status=status.value,
            binding_confidence=1.0,
            representation_state=state.value,
            display_value=display,
            validation_errors=(
                f"not_visible_at:{report_level}:{definition.field_name}",
            ),
        )

    def _invalid_field(
        self,
        definition: ReportFieldBinding,
        errors: list[str],
    ) -> BoundReportField:
        return BoundReportField(
            **self._field_kwargs(definition),
            binding_status=BindingState.INVALID_SOURCE.value,
            binding_confidence=0.0,
            representation_state=RepresentationState.EXPOSED.value,
            display_value="Not Available",
            validation_errors=tuple(errors),
        )

    def _missing_source_field(
        self,
        definition: ReportFieldBinding,
        *,
        source_exists: bool,
    ) -> BoundReportField:
        error = (
            "canonical_source_inaccessible"
            if source_exists
            else "canonical_source_missing"
        )
        return BoundReportField(
            **self._field_kwargs(definition),
            binding_status=BindingState.INVALID_SOURCE.value,
            binding_confidence=0.0,
            representation_state=RepresentationState.EXPOSED.value,
            display_value="Not Available",
            validation_errors=(f"{error}:{definition.field_name}",),
        )

    def _resolve_value(
        self,
        definition: ReportFieldBinding,
        source: CanonicalSource,
    ) -> tuple[Any, str | None]:
        for field_name in definition.source_fields or (definition.field_name,):
            if field_name in source.payload:
                return source.payload[field_name], field_name
        return None, None

    def _represent(self, value: Any, representation_type: str) -> str:
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if representation_type == "percentage" and isinstance(value, (int, float)):
            percent = value * 100 if 0 <= value <= 1 else value
            return f"{round(percent, 4):g}%"
        if isinstance(value, float):
            return str(round(value, 4))
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            return "Not Available" if value.upper() == "UNKNOWN" else value
        if isinstance(value, list):
            if not value:
                return "0"
            if representation_type == "list":
                return ", ".join(str(item) for item in value[:8])
            return f"{len(value)} entries"
        if isinstance(value, dict):
            if not value:
                return "0"
            if representation_type == "map":
                return "Externalized to Technical Appendix"
            if representation_type == "summary":
                return self._compressed_display(value)
            return ", ".join(
                f"{self._label(str(key))}={self._represent(item, 'text')}"
                for key, item in list(value.items())[:8]
            )
        return str(value)

    def _compressed_display(self, value: Any) -> str:
        if isinstance(value, dict):
            return f"Compressed Summary: {len(value)} fields"
        if isinstance(value, list):
            return f"Compressed Summary: {len(value)} entries"
        return self._represent(value, "text")

    def _build_report_field_registry(
        self,
        bound_fields: dict[str, BoundReportField],
    ) -> dict[str, dict[str, Any]]:
        timestamp = str(datetime.utcnow())
        return {
            name: {
                "field_name": name,
                "canonical_source": bound.canonical_source,
                "owner": bound.field_owner,
                "report_levels": list(bound.visibility_policy),
                "binding_state": bound.binding_status,
                "representation_state": bound.representation_state,
                "last_validation": timestamp,
            }
            for name, bound in sorted(bound_fields.items())
        }

    def _build_diagnostics(
        self,
        bound_fields: dict[str, BoundReportField],
        validation_errors: list[str],
    ) -> dict[str, Any]:
        total = len(bound_fields)
        counts = {
            "bound_field_count": self._count_status(bound_fields, BindingState.BOUND),
            "compressed_field_count": self._count_status(bound_fields, BindingState.COMPRESSED),
            "hidden_field_count": self._count_status(bound_fields, BindingState.HIDDEN),
            "externalized_field_count": self._count_status(bound_fields, BindingState.EXTERNALIZED),
            "unbound_field_count": self._count_status(bound_fields, BindingState.UNBOUND),
            "invalid_source_count": self._count_status(bound_fields, BindingState.INVALID_SOURCE),
            "not_available_field_count": self._count_status(bound_fields, BindingState.NOT_AVAILABLE),
        }
        successful = (
            counts["bound_field_count"]
            + counts["compressed_field_count"]
            + counts["hidden_field_count"]
            + counts["externalized_field_count"]
        )
        return {
            **counts,
            "binding_success_rate": round(successful / total, 4) if total else 1.0,
            "binding_validation_status": (
                "VALID" if not validation_errors else "INVALID"
            ),
            "validation_errors": validation_errors,
            "canonical_source_count": len(self.canonical_source_registry),
            "report_field_count": total,
            "unknown_value_count": 0,
        }

    def _validate_required_fields(
        self,
        bound_fields: dict[str, BoundReportField],
        report_level: str,
    ) -> list[str]:
        errors = []
        for name, bound in sorted(bound_fields.items()):
            if (
                bound.binding_status
                in {BindingState.NOT_AVAILABLE.value, BindingState.INVALID_SOURCE.value}
                and self._definition_for(name).required
                and report_level in bound.visibility_policy
            ):
                errors.append(f"required_field_not_bound:{name}")
        return errors

    def _validate_no_unknown(
        self,
        bound_fields: dict[str, BoundReportField],
    ) -> list[str]:
        errors = []
        for name, bound in sorted(bound_fields.items()):
            if str(bound.display_value).upper() == "UNKNOWN":
                errors.append(f"unknown_value_prohibited:{name}")
        return errors

    def _count_status(
        self,
        bound_fields: dict[str, BoundReportField],
        status: BindingState,
    ) -> int:
        return sum(
            1
            for field_value in bound_fields.values()
            if field_value.binding_status == status.value
        )

    def _definition_for(self, field_name: str) -> ReportFieldBinding:
        for definition in self.field_bindings:
            if definition.field_name == field_name:
                return definition
        raise KeyError(field_name)

    def _field_kwargs(self, definition: ReportFieldBinding) -> dict[str, Any]:
        return {
            "field_name": definition.field_name,
            "field_owner": definition.field_owner,
            "canonical_source": definition.canonical_source,
            "visibility_policy": definition.visibility_policy,
            "compression_policy": definition.compression_policy,
            "externalization_policy": definition.externalization_policy,
            "representation_type": definition.representation_type,
        }

    def _first_dict(
        self,
        base: dict[str, Any],
        *keys: str,
    ) -> dict[str, Any]:
        for key in keys:
            value = base.get(key) if isinstance(base, dict) else None
            if isinstance(value, dict):
                return deepcopy(value)
        return {}

    def _merge_dicts(self, *items: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for item in items:
            if isinstance(item, dict):
                merged.update(deepcopy(item))
        return merged

    def _discover_named_sources(self, report_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
        discovered: dict[str, dict[str, Any]] = {}

        def visit(item: Any) -> None:
            if isinstance(item, dict):
                for key, value in item.items():
                    name = str(key)
                    if (
                        name in self.DISCOVERABLE_SOURCE_NAMES
                        or name.endswith("_metrics")
                        or name.endswith("_registry")
                        or name.endswith("_snapshots")
                    ) and isinstance(value, dict):
                        discovered.setdefault(name, deepcopy(value))
                    visit(value)
            elif isinstance(item, list):
                for child in item[:100]:
                    visit(child)

        visit(report_state)
        return discovered

    def _normalize_report_level(self, level: str) -> str:
        aliases = {
            "DEBUG": "DIAGNOSTIC",
            "AUDIT": "DIAGNOSTIC",
            "FULL": "DIAGNOSTIC",
            "FULL_DIAGNOSTIC": "DIAGNOSTIC",
            "DIAGNOSTIC_SUMMARY": "DIAGNOSTIC",
        }
        normalized = aliases.get(str(level or "normal").upper(), str(level or "normal").upper())
        return normalized if normalized in VALID_VISIBILITY_LEVELS else "NORMAL"

    def _label(self, key: str) -> str:
        return key.replace("_", " ").title()

    def _empty_metrics(self) -> dict[str, Any]:
        return {
            "bound_field_count": 0,
            "compressed_field_count": 0,
            "hidden_field_count": 0,
            "externalized_field_count": 0,
            "unbound_field_count": 0,
            "invalid_source_count": 0,
            "binding_success_rate": 0.0,
            "binding_validation_status": "NOT_RUN",
        }

    def _default_bindings(self) -> list[ReportFieldBinding]:
        all_levels = ("MINIMAL", "NORMAL", "DIAGNOSTIC")
        normal = ("NORMAL", "DIAGNOSTIC")
        diagnostic = ("DIAGNOSTIC",)

        def bind(
            field_name: str,
            owner: str,
            source: str,
            source_fields: tuple[str, ...],
            representation_type: str,
            *,
            visibility: tuple[str, ...] = normal,
            required: bool = False,
            compression_policy: str = "EXPOSED",
            externalized: bool = False,
        ) -> ReportFieldBinding:
            return ReportFieldBinding(
                field_name=field_name,
                field_owner=owner,
                canonical_source=source,
                visibility_policy=visibility,
                compression_policy=compression_policy,
                externalization_policy=externalized,
                representation_type=representation_type,
                source_fields=source_fields,
                required=required,
            )

        return [
            bind("system_name", "Runtime Metadata", "runtime_metadata", ("system",), "text", visibility=all_levels),
            bind("execution_mode", "Runtime Metadata", "runtime_metadata", ("mode",), "text", visibility=all_levels),
            bind("execution_profile", "Runtime Metadata", "runtime_metadata", ("profile",), "text", visibility=all_levels),
            bind("execution_identifier", "Runtime Metadata", "runtime_metadata", ("execution_id",), "text", visibility=all_levels),
            bind("timestamp", "Runtime Metadata", "runtime_metadata", ("timestamp",), "text", visibility=all_levels),
            bind("runtime_status", "Execution Runtime", "report_state", ("runtime_status", "status"), "status", visibility=all_levels, required=True),
            bind("total_executions", "Execution Runtime", "execution_registry", ("total_executions", "executions_total", "tasks_executed"), "count", visibility=all_levels, required=True),
            bind("completed_executions", "Execution Runtime", "execution_registry", ("completed_executions", "successful_tasks"), "count", visibility=all_levels, required=True),
            bind("archived_executions", "Execution Runtime", "execution_registry", ("archived_executions", "archived_execution_count"), "count"),
            bind("execution_coverage", "Execution Runtime", "execution_registry", ("execution_coverage",), "percentage", visibility=all_levels, required=True),
            bind("snapshot_coverage", "Snapshot Runtime", "execution_registry", ("snapshot_coverage",), "percentage", visibility=all_levels),
            bind("lifecycle_coverage", "Execution Runtime", "execution_registry", ("lifecycle_coverage",), "percentage"),
            bind("parent_execution_duration", "Execution Runtime", "execution_registry", ("parent_execution_duration",), "duration"),
            bind("total_wall_time", "Runtime Metrics", "performance_report", ("total_runtime_seconds", "execution_time"), "duration", visibility=all_levels),
            bind("generated_concepts", "Concept Runtime", "report_state", ("generated_concepts", "concept_count"), "count", visibility=all_levels),
            bind("generated_programs", "Program Runtime", "report_state", ("generated_programs", "program_candidates", "canonical_programs"), "count", visibility=all_levels, required=True),
            bind("validated_programs", "Program Runtime", "report_state", ("validated_programs",), "count", visibility=all_levels),
            bind("truth_candidates", "Truth Runtime", "report_state", ("truth_candidates", "truth_candidate_count"), "count", visibility=all_levels),
            bind("generated_memory_entries", "Semantic Memory", "knowledge_pipeline_metrics", ("generated_memory_entries",), "count"),
            bind("semantic_memory_entries", "Semantic Memory", "knowledge_pipeline_metrics", ("semantic_memory_entries",), "count"),
            bind("search_routes", "Search Runtime", "search_metrics", ("search_routes", "route_count", "unique_route_count"), "count"),
            bind("experience_count", "Semantic Memory", "knowledge_pipeline_metrics", ("experience_count",), "count"),
            bind("fabric_links", "Knowledge Fabric", "knowledge_pipeline_metrics", ("fabric_links", "generated_fabric_links"), "count"),
            bind("average_program_confidence", "Program Confidence Engine", "program_registry", ("average_program_confidence", "average_confidence", "confidence"), "metric", visibility=all_levels, required=True),
            bind("highest_confidence", "Program Confidence Engine", "program_registry", ("highest_confidence", "max_confidence"), "metric"),
            bind("lowest_confidence", "Program Confidence Engine", "program_registry", ("lowest_confidence", "min_confidence"), "metric"),
            bind("validation_distribution", "Program Runtime", "program_registry", ("validation_distribution", "program_validation_distribution"), "summary", compression_policy="COMPRESSED"),
            bind("overall_search_quality", "Search Runtime", "search_metrics", ("overall_search_quality",), "metric", visibility=all_levels, required=True),
            bind("search_efficiency", "Search Runtime", "search_metrics", ("search_efficiency",), "metric"),
            bind("search_coverage", "Search Runtime", "search_metrics", ("search_coverage",), "metric"),
            bind("search_entropy", "Search Runtime", "search_metrics", ("search_entropy",), "metric"),
            bind("average_route_quality", "Search Runtime", "search_metrics", ("average_route_quality", "route_quality"), "metric"),
            bind("knowledge_propagation_status", "Knowledge Pipeline", "knowledge_pipeline_metrics", ("status", "propagation_status"), "status"),
            bind("integrated_concepts", "Knowledge Pipeline", "knowledge_pipeline_metrics", ("integrated_concepts", "concepts_integrated"), "count"),
            bind("knowledge_links", "Knowledge Pipeline", "knowledge_pipeline_metrics", ("knowledge_links", "link_count"), "count"),
            bind("replication_state", "Knowledge Pipeline", "knowledge_pipeline_metrics", ("replication_state",), "status"),
            bind("binding_status", "Execution Runtime", "execution_binding_registry", ("binding_status", "status"), "status"),
            bind("metric_validation_status", "Metric Attribution", "metric_sync_report", ("metric_validation_status", "status"), "status"),
            bind("observability_status", "Runtime Observability", "observability_report", ("observability_status", "status"), "status"),
            bind("missing_execution_instances", "Execution Runtime", "execution_binding_registry", ("missing_execution_instances",), "count"),
            bind("missing_snapshot_runtimes", "Snapshot Runtime", "execution_binding_registry", ("missing_snapshot_runtimes",), "count"),
            bind("governance_budget_state", "Governance Runtime", "report_state", ("governance_budget_state", "governance_budget_exceeded"), "status"),
            bind("instrumentation_overhead_state", "Runtime Observability", "report_state", ("instrumentation_overhead_state",), "status"),
            bind("execution_time", "Runtime Metrics", "runtime_metadata", ("execution_time",), "duration", visibility=all_levels),
            bind("total_runtime_seconds", "Runtime Metrics", "performance_report", ("total_runtime_seconds",), "duration", visibility=all_levels),
            bind("active_compute_time_seconds", "Runtime Metrics", "performance_report", ("active_compute_time_seconds",), "duration"),
            bind("untracked_runtime_seconds", "Runtime Metrics", "performance_report", ("untracked_runtime_seconds",), "duration"),
            bind("finalization_duration", "Runtime Metrics", "performance_report", ("finalization_duration",), "duration"),
            bind("stage_timing_summary", "Runtime Metrics", "execution_timing_state", ("stage_timing_summary",), "summary"),
            bind("runtime_timing_summary", "Runtime Metrics", "execution_timing_state", ("runtime_timing_summary",), "summary", visibility=all_levels),
            bind("top_time_consumers", "Runtime Metrics", "execution_timing_state", ("top_time_consumers",), "list", visibility=all_levels),
            bind("timing_coverage", "Runtime Metrics", "execution_timing_state", ("timing_coverage",), "percentage", visibility=all_levels),
            bind("untracked_time", "Runtime Metrics", "execution_timing_state", ("untracked_time",), "duration", visibility=all_levels),
            bind("active_compute_time", "Runtime Metrics", "execution_timing_state", ("active_compute_time",), "duration", visibility=all_levels),
            bind("report_generation_time", "Runtime Metrics", "execution_timing_state", ("report_generation_time",), "duration", visibility=all_levels),
            bind("finalization_time", "Runtime Metrics", "execution_timing_state", ("finalization_time",), "duration", visibility=all_levels),
            bind("raw_timing_records", "Runtime Metrics", "execution_timing_state", ("raw_timing_records",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("metric_ownership_map", "Metric Attribution", "metric_attribution_state", ("metric_ownership_map", "metric_ownership"), "map", visibility=diagnostic, externalized=True),
            bind("snapshot_payload", "Snapshot Runtime", "runtime_snapshots", ("latest_snapshot_payload", "snapshot_payload"), "map", visibility=diagnostic, externalized=True),
            bind("execution_timeline", "Execution Runtime", "execution_registry", ("execution_timeline",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
        ]

    def _build_timing_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
        runtime_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        timing_report = self._first_dict(
            report_state,
            "execution_timing",
            "EXECUTION_TIMING_UNIFICATION_REPORT",
            "execution_timing_report",
        )
        timing_state = self._merge_dicts(
            self._first_dict(timing_report, "execution_timing_state"),
            self._first_dict(report_state, "execution_timing_state"),
            self._first_dict(performance, "execution_timing_state"),
        )
        timing_summary = self._merge_dicts(
            self._first_dict(timing_report, "timing_summary"),
            self._first_dict(report_state, "timing_summary"),
            self._first_dict(performance, "timing_summary"),
        )
        runtime_summary = self._first_dict(performance, "runtime_summary")
        runtime_breakdown = self._first_dict(performance, "runtime_breakdown")
        records = self._first_list(
            timing_report,
            "timing_records",
            fallback=self._first_list(timing_state, "timing_records"),
        )
        current_execution_id = str(
            runtime_metadata.get("execution_id")
            or report_state.get("execution_id")
            or "",
        )
        total_runtime = self._first_number(
            timing_state.get("total_wall_time"),
            timing_summary.get("total_wall_time"),
            runtime_summary.get("total_runtime_seconds"),
            performance.get("total_runtime_seconds"),
            runtime_metadata.get("execution_time"),
        )
        active_compute = self._first_number(
            performance.get("active_compute_time_seconds"),
            runtime_summary.get("active_compute_time_seconds"),
            timing_state.get("cognitive_runtime_time"),
        )
        untracked = self._first_number(
            timing_state.get("unattributed_time"),
            performance.get("untracked_runtime_seconds"),
            performance.get("unattributed_runtime_seconds"),
            runtime_breakdown.get("untracked_runtime"),
        )
        coverage = self._first_number(
            timing_state.get("timing_coverage"),
            timing_summary.get("timing_coverage"),
        )
        if coverage is None and total_runtime is not None and untracked is not None:
            coverage = max(0.0, min(1.0, 1.0 - (untracked / max(total_runtime, 0.000001))))

        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        seen_stage_names: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            record_execution_id = str(record.get("execution_id") or "")
            if (
                current_execution_id
                and record_execution_id
                and record_execution_id != current_execution_id
            ):
                continue
            duration = self._first_number(
                record.get("wall_duration_seconds"),
                record.get("inclusive_duration_seconds"),
                record.get("duration_seconds"),
            )
            if duration is None or duration <= 0.0:
                continue
            if str(record.get("validation_status", "VALID")).upper() not in {"VALID", ""}:
                continue
            scope = str(record.get("timing_scope") or record.get("scope") or "")
            name = self._stage_name(scope or str(record.get("timing_name") or ""))
            key = (name, scope)
            if key in seen:
                continue
            seen.add(key)
            seen_stage_names.add(name)
            rows.append(self._stage_row(
                name,
                duration,
                total_runtime,
                timing_scope=scope or "TIMING_RECORD",
                timing_status=str(record.get("timing_status") or "OBSERVED"),
                source="ExecutionTimingState",
                raw=record,
            ))

        stage_metrics = self._first_list(performance, "stage_metrics")
        for stage in stage_metrics:
            if not isinstance(stage, dict):
                continue
            duration = self._first_number(
                stage.get("total_duration"),
                stage.get("duration_seconds"),
                stage.get("seconds"),
            )
            if duration is None or duration <= 0.0:
                continue
            name = self._stage_name(str(stage.get("stage_name") or stage.get("module") or ""))
            if name in seen_stage_names:
                continue
            key = (name, "RUNTIME_STAGE")
            if key in seen:
                continue
            seen.add(key)
            seen_stage_names.add(name)
            rows.append(self._stage_row(
                name,
                duration,
                total_runtime,
                timing_scope="RUNTIME_STAGE",
                timing_status="OBSERVED",
                source="Runtime Metric Attribution",
                raw=stage,
            ))

        for module in ([] if stage_metrics else self._first_list(performance, "module_timings")):
            if not isinstance(module, dict):
                continue
            duration = self._first_number(module.get("seconds"), module.get("duration"))
            if duration is None or duration <= 0.0:
                continue
            name = self._stage_name(str(module.get("module") or module.get("stage") or ""))
            if name in seen_stage_names:
                continue
            key = (name, "PER_RUNTIME_TIMING")
            if key in seen:
                continue
            seen.add(key)
            seen_stage_names.add(name)
            rows.append(self._stage_row(
                name,
                duration,
                total_runtime,
                timing_scope="PER_RUNTIME_TIMING",
                timing_status="OBSERVED",
                source="Per-Runtime Timing Records",
                raw=module,
            ))

        for key, value in sorted(runtime_breakdown.items()):
            duration = self._first_number(value)
            if duration is None or duration <= 0.0 or key == "untracked_runtime":
                continue
            name = self._stage_name(key)
            if name in seen_stage_names:
                continue
            unique = (name, "RUNTIME_BREAKDOWN")
            if unique in seen:
                continue
            seen.add(unique)
            seen_stage_names.add(name)
            rows.append(self._stage_row(
                name,
                duration,
                total_runtime,
                timing_scope="RUNTIME_BREAKDOWN",
                timing_status="OBSERVED",
                source="Runtime Metric Attribution",
            ))

        rows = sorted(
            rows,
            key=lambda item: (-float(item["duration_seconds"]), item["stage_name"]),
        )
        top = [
            {
                "rank": index + 1,
                "stage_name": row["stage_name"],
                "duration_seconds": row["duration_seconds"],
                "percentage_of_total_runtime": row["percentage_of_total_runtime"],
                "timing_scope": row["timing_scope"],
            }
            for index, row in enumerate(rows[:3])
        ]
        highest = top[0] if top else {}
        productive = [
            row for row in rows
            if row["stage_name"] not in {"Boot", "Finalization", "Report Generation"}
        ]
        lowest = min(
            productive,
            key=lambda item: float(item["duration_seconds"]),
            default={},
        )
        report_generation = self._first_number(
            timing_state.get("report_generation_time"),
            self._summary_duration(timing_summary, "report_generation_time"),
            runtime_breakdown.get("report_time"),
        )
        finalization = self._first_number(
            timing_state.get("finalization_time"),
            self._summary_duration(timing_summary, "finalization_time"),
            performance.get("finalization_duration"),
        )
        return {
            **timing_state,
            "stage_timing_summary": rows,
            "runtime_timing_summary": {
                "total_wall_time": total_runtime,
                "active_compute_time": active_compute,
                "cognitive_runtime_time": self._first_number(timing_state.get("cognitive_runtime_time")),
                "untracked_time": untracked,
                "timing_coverage": coverage,
                "report_generation_time": report_generation,
                "finalization_time": finalization,
                "stage_count": len(rows),
            },
            "top_time_consumers": top,
            "timing_coverage": coverage,
            "untracked_time": untracked,
            "active_compute_time": active_compute,
            "report_generation_time": report_generation,
            "finalization_time": finalization,
            "highest_time_consumer": highest.get("stage_name"),
            "highest_time_consumer_percentage": highest.get("percentage_of_total_runtime"),
            "lowest_productive_stage": lowest.get("stage_name"),
            "resource_distribution_status": "AVAILABLE" if rows else "NOT_AVAILABLE",
            "raw_timing_records": records,
        }

    def _stage_row(
        self,
        stage_name: str,
        duration: float,
        total_runtime: float | None,
        *,
        timing_scope: str,
        timing_status: str,
        source: str,
        raw: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        denominator = max(float(total_runtime or 0.0), 0.000001)
        return {
            "stage_name": stage_name,
            "duration_seconds": round(max(float(duration), 0.0), 4),
            "percentage_of_total_runtime": round((float(duration) / denominator) * 100.0, 4),
            "timing_scope": timing_scope,
            "timing_status": timing_status,
            "measurement_source": source,
            "measurement_method": (raw or {}).get("measurement_method"),
            "parent_timing_id": (raw or {}).get("parent_timing_id"),
            "inclusive_duration": (raw or {}).get("inclusive_duration_seconds"),
            "exclusive_duration": (raw or {}).get("exclusive_duration_seconds"),
            "cpu_duration": (raw or {}).get("cpu_duration_seconds"),
            "wall_duration": (raw or {}).get("wall_duration_seconds"),
        }

    def _stage_name(self, raw: str) -> str:
        key = str(raw or "").strip().lower()
        key = key.removesuffix("_time").removesuffix("_seconds")
        aliases = {
            "boot": "Boot",
            "task_selection": "Task Selection",
            "task_loading": "Task Loading",
            "grid_analysis": "Grid Analysis",
            "pattern_analysis": "Pattern Analysis",
            "rule_analysis": "Rule Analysis",
            "reasoning": "Reasoning",
            "reasoning_orchestrator": "Reasoning",
            "search": "Search",
            "concept_formation": "Concept Formation",
            "program_synthesis": "Program Synthesis",
            "adaptive_search": "Adaptive Search",
            "evidence_building": "Evidence Building",
            "knowledge_integration": "Knowledge Integration",
            "memory": "Memory",
            "truth": "Truth",
            "evaluation": "Evaluation",
            "post_execution_cognitive": "Post-Execution Cognition",
            "governance": "Governance",
            "finalization": "Finalization",
            "report_generation": "Report Generation",
            "report": "Report Generation",
            "cognitive_runtime": "Cognitive Runtime",
            "child_runtime": "Child Runtime",
            "total_wall": "Total Wall Time",
        }
        if key in aliases:
            return aliases[key]
        for needle, label in aliases.items():
            if needle and needle in key:
                return label
        return key.replace("_", " ").title() if key else "Timing Stage"

    def _summary_duration(self, timing_summary: dict[str, Any], key: str) -> float | None:
        value = timing_summary.get(key)
        if isinstance(value, dict):
            return self._first_number(value.get("duration_seconds"))
        return self._first_number(value)

    def _first_number(self, *values: Any) -> float | None:
        for value in values:
            if isinstance(value, dict) and "duration_seconds" in value:
                value = value.get("duration_seconds")
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number >= 0.0:
                return round(number, 6)
        return None

    def _first_list(
        self,
        base: dict[str, Any],
        *keys: str,
        fallback: list[Any] | None = None,
    ) -> list[Any]:
        for key in keys:
            value = base.get(key) if isinstance(base, dict) else None
            if isinstance(value, list):
                return deepcopy(value)
            if isinstance(value, tuple):
                return [deepcopy(item) for item in value]
        return list(fallback or [])


canonical_report_binding_engine = CanonicalReportBindingEngine()


__all__ = [
    "BindingState",
    "BoundReportField",
    "CanonicalReportBindingEngine",
    "CanonicalSource",
    "ReportFieldBinding",
    "RepresentationState",
    "canonical_report_binding_engine",
]
