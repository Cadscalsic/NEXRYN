from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

from runtime.timing import hierarchical_timing_reconciliation_engine
from runtime.reporting.report_timing_semantics import report_timing_semantic_engine


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
        "prediction_provenance_report",
        "cognitive_candidate_arena_report",
        "truth_metrics",
        "memory_metrics",
        "search_metrics",
        "knowledge_pipeline_metrics",
        "representation_metrics",
        "semantic_compilation_report",
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
        visible_report_state = self._build_report_state_visibility(
            report_state,
            performance,
        )
        sources = {
            "report_state": CanonicalSource("report_state", visible_report_state),
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
            "semantic_compilation_report": CanonicalSource(
                "semantic_compilation_report",
                self._build_semantic_compilation_visibility(report_state, performance),
            ),
            "prediction_provenance_report": CanonicalSource(
                "prediction_provenance_report",
                self._build_prediction_provenance_visibility(report_state, performance),
            ),
            "cognitive_candidate_arena_report": CanonicalSource(
                "cognitive_candidate_arena_report",
                self._build_candidate_arena_visibility(report_state, performance),
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
        if representation_type == "count" and isinstance(value, float) and value.is_integer():
            return str(int(value))
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
            bind("generated_concepts", "Concept Runtime", "report_state", ("generated_concepts", "concept_count", "semantic_concept_count"), "count", visibility=all_levels),
            bind("generated_programs", "Program Runtime", "report_state", ("generated_programs", "program_candidates", "canonical_programs", "candidate_count"), "count", visibility=all_levels, required=True),
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
            bind("semantic_compilation_summary", "Semantic Compilation", "semantic_compilation_report", ("semantic_compilation_summary",), "summary", visibility=normal),
            bind("semantic_compilation_diagnostics", "Semantic Compilation", "semantic_compilation_report", ("semantic_compilation_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("prediction_provenance_summary", "Transformation Decision Runtime", "prediction_provenance_report", ("prediction_provenance_summary",), "summary", visibility=normal),
            bind("prediction_provenance_diagnostics", "Transformation Decision Runtime", "prediction_provenance_report", ("prediction_provenance_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("candidate_arena_summary", "Cognitive Candidate Arena", "cognitive_candidate_arena_report", ("candidate_arena_summary",), "summary", visibility=normal),
            bind("candidate_arena_diagnostics", "Cognitive Candidate Arena", "cognitive_candidate_arena_report", ("candidate_arena_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
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
            bind("timing_hierarchy_summary", "Runtime Metrics", "execution_timing_state", ("timing_hierarchy_summary",), "summary"),
            bind("resource_consumption_ranking", "Runtime Metrics", "execution_timing_state", ("resource_consumption_ranking",), "list", visibility=all_levels),
            bind("timing_reconciliation_summary", "Runtime Metrics", "execution_timing_state", ("timing_reconciliation_summary",), "summary", visibility=all_levels),
            bind("reporting_timing_summary", "Runtime Metrics", "execution_timing_state", ("reporting_timing_summary",), "summary", visibility=all_levels),
            bind("reporting_timing_nodes", "Runtime Metrics", "execution_timing_state", ("reporting_timing_nodes",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("legacy_report_timing_mappings", "Runtime Metrics", "execution_timing_state", ("legacy_report_timing_mappings",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("runtime_timing_summary", "Runtime Metrics", "execution_timing_state", ("runtime_timing_summary",), "summary", visibility=all_levels),
            bind("top_time_consumers", "Runtime Metrics", "execution_timing_state", ("top_time_consumers",), "list", visibility=all_levels),
            bind("timing_coverage", "Runtime Metrics", "execution_timing_state", ("timing_coverage",), "percentage", visibility=all_levels),
            bind("untracked_time", "Runtime Metrics", "execution_timing_state", ("untracked_time",), "duration", visibility=all_levels),
            bind("active_compute_time", "Runtime Metrics", "execution_timing_state", ("active_compute_time",), "duration", visibility=all_levels),
            bind("report_generation_time", "Runtime Metrics", "execution_timing_state", ("report_generation_time",), "duration", visibility=all_levels),
            bind("report_lifecycle_total_time", "Runtime Metrics", "execution_timing_state", ("report_lifecycle_total_time",), "duration", visibility=all_levels),
            bind("final_report_rendering_time", "Runtime Metrics", "execution_timing_state", ("final_report_rendering_time",), "duration", visibility=all_levels),
            bind("finalization_time", "Runtime Metrics", "execution_timing_state", ("finalization_time",), "duration", visibility=all_levels),
            bind("diagnostic_timing_nodes", "Runtime Metrics", "execution_timing_state", ("diagnostic_timing_nodes",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("raw_timing_records", "Runtime Metrics", "execution_timing_state", ("raw_timing_records",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("metric_ownership_map", "Metric Attribution", "metric_attribution_state", ("metric_ownership_map", "metric_ownership"), "map", visibility=diagnostic, externalized=True),
            bind("snapshot_payload", "Snapshot Runtime", "runtime_snapshots", ("latest_snapshot_payload", "snapshot_payload"), "map", visibility=diagnostic, externalized=True),
            bind("execution_timeline", "Execution Runtime", "execution_registry", ("execution_timeline",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
        ]

    def _build_semantic_compilation_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        synthesis = self._merge_dicts(
            self._first_dict(report_state, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
            self._first_dict(performance, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
        )
        compiler = self._merge_dicts(
            self._first_dict(report_state, "SEMANTIC_COMPILATION_REPORT", "semantic_compilation_report"),
            self._first_dict(performance, "SEMANTIC_COMPILATION_REPORT", "semantic_compilation_report"),
            self._first_dict(synthesis, "semantic_to_transformation_compilation_report"),
        )
        selected_program = self._first_dict(synthesis, "selected_program")
        selected_steps = selected_program.get("steps", []) if isinstance(selected_program, dict) else []
        selected_step = selected_steps[0] if selected_steps and isinstance(selected_steps[0], dict) else {}
        compiler_program = self._first_dict(compiler, "compiled_program")
        compiler_steps = compiler_program.get("steps", []) if isinstance(compiler_program, dict) else []
        compiler_step = compiler_steps[0] if compiler_steps and isinstance(compiler_steps[0], dict) else {}
        triggered = bool(compiler) or bool(synthesis)
        compilation_success = bool(
            compiler.get("semantic_to_transformation_compilation_success")
        )
        compiler_operation = compiler_step.get("operation")
        selected_operation = selected_step.get("operation")
        selected_from_compiler = bool(
            compilation_success
            and compiler_program
            and selected_program
            and compiler_program == selected_program
        )
        validation = self._first_dict(compiler, "validation")
        if not compiler:
            status = "NOT_TRIGGERED"
        elif compilation_success:
            status = "SUCCESS"
        else:
            status = "NO_MATCHING_COMPILER_RULE"
        if selected_from_compiler and validation.get("exact_match"):
            execution_status = "SUCCESS"
        elif selected_from_compiler:
            execution_status = "FAILED"
        elif compilation_success:
            execution_status = "NOT_SELECTED"
        elif triggered:
            execution_status = "NOT_EXECUTED"
        else:
            execution_status = "NOT_TRIGGERED"

        failure_cause = compiler.get("failure_reason")
        if not failure_cause and status == "NO_MATCHING_COMPILER_RULE":
            failure_cause = "No matching compiler rule."
        elif not failure_cause and execution_status == "NOT_SELECTED":
            failure_cause = "Compiled program was not selected by synthesis ranking."
        elif not failure_cause and execution_status == "FAILED":
            failure_cause = "Compiled program did not match target output."

        summary = {
            "compiler_triggered": triggered,
            "compilation_status": status,
            "execution_status": execution_status,
            "selected_from_compiler": selected_from_compiler,
            "detected_concepts": synthesis.get("detected_concepts") or compiler.get("detected_intents") or [],
            "generated_concepts": self._first_number(
                report_state.get("generated_concepts"),
                report_state.get("concept_count"),
                report_state.get("semantic_concept_count"),
                performance.get("semantic_concept_count"),
                len(synthesis.get("detected_concepts", []) or []) if synthesis.get("detected_concepts") else None,
                len(compiler.get("detected_intents", []) or []) if compiler.get("detected_intents") else None,
            ),
            "generated_programs": self._first_number(
                report_state.get("generated_programs"),
                report_state.get("program_candidates"),
                synthesis.get("candidate_count"),
                len(synthesis.get("generated_transformations", []) or []) if synthesis.get("generated_transformations") else None,
                compiler.get("candidate_count"),
            ),
            "execution_intents": compiler.get("execution_intents") or [],
            "execution_intent_count": len(compiler.get("execution_intents") or []),
            "semantic_intent_routing_success": bool(
                self._first_dict(compiler, "semantic_intent_routing_report").get(
                    "semantic_intent_routing_success"
                )
            ),
            "selected_intent": compiler.get("selected_intent"),
            "compiled_candidate_count": compiler.get("candidate_count", 0),
            "compiled_operation": compiler_operation,
            "selected_operation": selected_operation,
            "compilation_confidence": self._first_number(
                synthesis.get("transformation_confidence"),
                validation.get("accuracy"),
            ),
            "prediction_accuracy": self._first_number(
                synthesis.get("transformation_accuracy"),
                validation.get("accuracy"),
            ),
            "parameter_inference": compiler_step.get("parameters", {}),
            "failure_cause": failure_cause,
            "primitive_executor_called": selected_from_compiler,
        }
        return {
            "semantic_compilation_summary": summary,
            "semantic_compilation_diagnostics": {
                "transformation_synthesis_report": synthesis,
                "compiler_report": compiler,
                "selected_program": selected_program,
            },
            **summary,
        }

    def _build_report_state_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        visible = deepcopy(report_state)
        synthesis = self._merge_dicts(
            self._first_dict(report_state, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
            self._first_dict(performance, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
        )
        compiler = self._merge_dicts(
            self._first_dict(report_state, "SEMANTIC_COMPILATION_REPORT", "semantic_compilation_report"),
            self._first_dict(performance, "SEMANTIC_COMPILATION_REPORT", "semantic_compilation_report"),
            self._first_dict(synthesis, "semantic_to_transformation_compilation_report"),
        )
        generated_concepts = self._first_number(
            visible.get("generated_concepts"),
            visible.get("concept_count"),
            visible.get("semantic_concept_count"),
            performance.get("semantic_concept_count"),
            len(synthesis.get("detected_concepts", []) or []) if synthesis.get("detected_concepts") else None,
            len(compiler.get("detected_intents", []) or []) if compiler.get("detected_intents") else None,
        )
        generated_programs = self._first_number(
            visible.get("generated_programs"),
            visible.get("program_candidates"),
            visible.get("canonical_programs"),
            synthesis.get("candidate_count"),
            len(synthesis.get("generated_transformations", []) or []) if synthesis.get("generated_transformations") else None,
            compiler.get("candidate_count"),
        )
        if generated_concepts is not None:
            visible.setdefault("generated_concepts", generated_concepts)
            visible.setdefault("concept_count", generated_concepts)
        if generated_programs is not None:
            visible.setdefault("generated_programs", generated_programs)
            visible.setdefault("program_candidates", generated_programs)
            visible.setdefault("candidate_count", generated_programs)
        return visible

    def _build_prediction_provenance_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "PREDICTION_PROVENANCE_REPORT", "prediction_provenance_report"),
            self._first_dict(performance, "PREDICTION_PROVENANCE_REPORT", "prediction_provenance_report"),
        )
        synthesis = self._merge_dicts(
            self._first_dict(report_state, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
            self._first_dict(performance, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
        )
        semantic = self._build_semantic_compilation_visibility(report_state, performance).get(
            "semantic_compilation_summary",
            {},
        )
        color = self._merge_dicts(
            self._first_dict(report_state, "COLOR_MAPPING_REPORT", "color_mapping_report"),
            self._first_dict(performance, "COLOR_MAPPING_REPORT", "color_mapping_report"),
        )
        adaptive = self._merge_dicts(
            self._first_dict(report_state, "ADAPTIVE_REUSE_REPORT", "adaptive_reuse_report"),
            self._first_dict(performance, "ADAPTIVE_REUSE_REPORT", "adaptive_reuse_report"),
        )
        search = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "cognitive_search_report"),
            self._first_dict(performance, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "cognitive_search_report"),
        )
        repair = self._merge_dicts(
            self._first_dict(report_state, "REPAIR_REPORT", "repair_report", "execution_repair_report"),
            self._first_dict(performance, "REPAIR_REPORT", "repair_report", "execution_repair_report"),
        )
        evaluation = self._merge_dicts(
            self._first_dict(report_state, "EVALUATION_REPORT", "evaluation_report"),
            self._first_dict(performance, "EVALUATION_REPORT", "evaluation_report"),
        )

        selected_program = self._first_dict(synthesis, "selected_program")
        selected_steps = selected_program.get("steps", []) if selected_program else []
        selected_step = selected_steps[0] if selected_steps and isinstance(selected_steps[0], dict) else {}
        selected_operation = selected_step.get("operation")
        selected_candidate = (
            explicit.get("winning_candidate")
            or synthesis.get("selected_candidate")
            or selected_operation
            or color.get("selected_mapping")
            or "Not Available"
        )
        candidate_count = self._first_number(
            explicit.get("candidate_count"),
            synthesis.get("candidate_count"),
            semantic.get("compiled_candidate_count"),
            search.get("program_candidates"),
            report_state.get("program_candidates"),
        )
        generated_program_count = self._first_number(
            explicit.get("generated_program_count"),
            synthesis.get("candidate_count"),
            report_state.get("generated_programs"),
            search.get("program_candidates"),
        )
        generated_concept_count = self._first_number(
            explicit.get("generated_concept_count"),
            len(synthesis.get("detected_concepts", []) or []) if synthesis.get("detected_concepts") else None,
            report_state.get("generated_concepts"),
            report_state.get("concept_count"),
        )
        compiler_participation = bool(semantic.get("selected_from_compiler"))
        repair_participation = bool(
            repair.get("repair_success_rate")
            or repair.get("repair_applied")
            or report_state.get("repair_success_rate")
        )
        reuse_assets = adaptive.get("reused_assets", {})
        transfer_participation = bool(
            adaptive.get("reuse_success_rate")
            or adaptive.get("reuse_rate")
            or adaptive.get("reused_programs")
            or (isinstance(reuse_assets, dict) and any(reuse_assets.values()))
        )
        counterfactual_participation = bool(
            synthesis.get("counterfactual_candidates")
            or search.get("counterfactual_candidates")
            or search.get("counterfactual_search")
        )
        program_validation = (
            explicit.get("program_validation")
            or evaluation.get("success_state")
            or synthesis.get("validation_status")
            or ("SUCCESS" if self._first_number(synthesis.get("transformation_accuracy"), evaluation.get("accuracy")) == 1.0 else "UNKNOWN")
        )
        confidence = self._first_number(
            explicit.get("decision_confidence"),
            synthesis.get("transformation_confidence"),
            synthesis.get("transformation_accuracy"),
            color.get("mapping_confidence"),
            evaluation.get("accuracy"),
        )
        prediction_accuracy = self._first_number(
            explicit.get("prediction_accuracy"),
            synthesis.get("transformation_accuracy"),
            color.get("program_accuracy"),
            evaluation.get("accuracy"),
        )
        owner, source = self._prediction_owner(
            explicit,
            compiler_participation,
            selected_program,
            color,
            transfer_participation,
            search,
            repair_participation,
        )
        pipeline = self._decision_pipeline(
            owner,
            compiler_participation,
            transfer_participation,
            repair_participation,
            counterfactual_participation,
            bool(selected_program),
        )
        summary = {
            "prediction_source": source,
            "decision_owner": owner,
            "decision_confidence": confidence,
            "winning_candidate": selected_candidate,
            "selected_operation": selected_operation,
            "decision_pipeline": pipeline,
            "compiler_participation": compiler_participation,
            "repair_participation": repair_participation,
            "transfer_learning_participation": transfer_participation,
            "counterfactual_search": counterfactual_participation,
            "program_validation": program_validation,
            "prediction_accuracy": prediction_accuracy,
            "candidate_count": candidate_count,
            "generated_program_count": generated_program_count,
            "generated_concept_count": generated_concept_count,
            "programs_rejected": explicit.get("programs_rejected"),
            "programs_executed": explicit.get("programs_executed") or (1 if selected_program else None),
        }
        return {
            "prediction_provenance_summary": summary,
            "prediction_provenance_diagnostics": {
                "explicit_provenance_report": explicit,
                "transformation_synthesis_report": synthesis,
                "semantic_compilation_summary": semantic,
                "color_mapping_report": color,
                "adaptive_reuse_report": adaptive,
                "search_report": search,
                "repair_report": repair,
                "evaluation_report": evaluation,
            },
            **summary,
        }

    def _prediction_owner(
        self,
        explicit: dict[str, Any],
        compiler_participation: bool,
        selected_program: dict[str, Any],
        color: dict[str, Any],
        transfer_participation: bool,
        search: dict[str, Any],
        repair_participation: bool,
    ) -> tuple[str, str]:
        if explicit.get("decision_owner") or explicit.get("prediction_source"):
            owner = explicit.get("decision_owner") or explicit.get("prediction_source")
            return str(owner), str(explicit.get("prediction_source") or owner)
        if compiler_participation:
            return "Semantic-to-Transformation Compiler", "semantic_to_transformation_compiler"
        if selected_program:
            return "Transformation Synthesis Engine", "transformation_synthesis"
        if color.get("selected_program") or color.get("mapping_matrix"):
            return "Color Mapping Engine", "color_mapping"
        if transfer_participation:
            return "Adaptive Reuse Layer", "adaptive_reuse"
        if search.get("winning_programs") or search.get("best_route"):
            return "Adaptive Search", "adaptive_search"
        if repair_participation:
            return "Repair System", "repair"
        return "UNRESOLVED", "Not Available"

    def _decision_pipeline(
        self,
        owner: str,
        compiler_participation: bool,
        transfer_participation: bool,
        repair_participation: bool,
        counterfactual_participation: bool,
        has_selected_program: bool,
    ) -> list[str]:
        pipeline = ["Semantic Attribution", "Pattern Analysis", "Rule Analysis"]
        if compiler_participation:
            pipeline.append("Semantic-to-Transformation Compiler")
        if transfer_participation:
            pipeline.append("Adaptive Reuse")
        if counterfactual_participation:
            pipeline.append("Counterfactual Search")
        if has_selected_program:
            pipeline.extend(["Transformation Synthesis", "Primitive Executor"])
        elif owner != "UNRESOLVED":
            pipeline.append(owner)
        if repair_participation:
            pipeline.append("Repair System")
        pipeline.append("Prediction")
        return list(dict.fromkeys(pipeline))

    def _build_candidate_arena_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        provenance = self._build_prediction_provenance_visibility(
            report_state,
            performance,
        ).get("prediction_provenance_summary", {})
        semantic = self._build_semantic_compilation_visibility(
            report_state,
            performance,
        ).get("semantic_compilation_summary", {})
        synthesis = self._merge_dicts(
            self._first_dict(report_state, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
            self._first_dict(performance, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
        )
        compiler = self._first_dict(synthesis, "semantic_to_transformation_compilation_report")
        adaptive = self._merge_dicts(
            self._first_dict(report_state, "ADAPTIVE_REUSE_REPORT", "adaptive_reuse_report"),
            self._first_dict(performance, "ADAPTIVE_REUSE_REPORT", "adaptive_reuse_report"),
        )
        color = self._merge_dicts(
            self._first_dict(report_state, "COLOR_MAPPING_REPORT", "color_mapping_report"),
            self._first_dict(performance, "COLOR_MAPPING_REPORT", "color_mapping_report"),
        )
        search = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "cognitive_search_report"),
            self._first_dict(performance, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "cognitive_search_report"),
        )
        repair = self._merge_dicts(
            self._first_dict(report_state, "REPAIR_REPORT", "repair_report", "execution_repair_report"),
            self._first_dict(performance, "REPAIR_REPORT", "repair_report", "execution_repair_report"),
        )
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_CANDIDATE_ARENA_REPORT", "candidate_arena_report"),
            self._first_dict(performance, "COGNITIVE_CANDIDATE_ARENA_REPORT", "candidate_arena_report"),
        )
        candidates = []
        candidates.extend(self._arena_candidates_from_explicit(explicit))
        candidates.extend(self._arena_candidates_from_compiler(compiler, semantic, provenance))
        candidates.extend(self._arena_candidates_from_adaptive_reuse(adaptive, provenance))
        candidates.extend(self._arena_candidates_from_synthesis(synthesis, provenance))
        candidates.extend(self._arena_candidates_from_color_mapping(color, provenance))
        candidates.extend(self._arena_candidates_from_search(search, provenance))
        candidates.extend(self._arena_candidates_from_repair(repair, provenance))
        candidates = self._dedupe_arena_candidates(candidates)
        participants = [candidate for candidate in candidates if candidate.get("entered_arena")]
        winner = next((candidate for candidate in candidates if candidate.get("selected")), {})
        sources = sorted({candidate.get("source") for candidate in participants if candidate.get("source")})
        dominance_source = None
        if winner and len(participants) <= 1:
            dominance_source = winner.get("source")
        elif winner:
            winner_source_count = sum(
                1 for candidate in participants
                if candidate.get("source") == winner.get("source")
            )
            if winner_source_count == len(participants):
                dominance_source = winner.get("source")
        validation_observed = sum(
            1 for candidate in participants
            if candidate.get("validation_status") not in {None, "UNKNOWN", "NOT_AVAILABLE"}
        )
        source_status = self._arena_source_statuses(
            compiler,
            adaptive,
            synthesis,
            color,
            search,
            repair,
            participants,
        )
        arena_state = (
            "COMPETITIVE"
            if len(sources) > 1
            else "SINGLE_SOURCE_DOMINANCE"
            if participants
            else "EMPTY"
        )
        summary = {
            "arena_state": explicit.get("arena_state") or arena_state,
            "candidate_count": len(participants),
            "competitor_sources": sources,
            "winner_source": winner.get("source") or provenance.get("prediction_source"),
            "arena_winner": winner.get("candidate_id") or provenance.get("winning_candidate"),
            "winner_takes_all_detected": bool(participants and len(sources) <= 1),
            "dominance_source": dominance_source,
            "selection_mode": "OBSERVED_DECISION_ONLY",
            "validation_coverage": round(
                validation_observed / max(len(participants), 1),
                4,
            ) if participants else 0.0,
            "candidate_rows": participants,
            "source_status": source_status,
            "missing_competition_reason": (
                "Only one candidate source entered the arena."
                if participants and len(sources) <= 1
                else "No executable candidates were observed."
                if not participants
                else None
            ),
        }
        return {
            "candidate_arena_summary": summary,
            "candidate_arena_diagnostics": {
                "all_candidates": candidates,
                "source_status": source_status,
                "prediction_provenance_summary": provenance,
                "explicit_arena_report": explicit,
            },
            **summary,
        }

    def _arena_candidates_from_explicit(self, explicit: dict[str, Any]) -> list[dict[str, Any]]:
        rows = explicit.get("candidate_rows") or explicit.get("candidates") or []
        return [
            self._arena_candidate(
                source=row.get("source", "explicit_arena"),
                candidate_id=row.get("candidate_id") or row.get("name"),
                operation=row.get("operation"),
                confidence=row.get("confidence") or row.get("score"),
                validation_status=row.get("validation_status"),
                selected=bool(row.get("selected")),
                entered=True,
                blocked_reason=row.get("blocked_reason"),
            )
            for row in rows
            if isinstance(row, dict)
        ]

    def _arena_candidates_from_compiler(
        self,
        compiler: dict[str, Any],
        semantic: dict[str, Any],
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not compiler:
            return []
        success = bool(compiler.get("semantic_to_transformation_compilation_success"))
        return [self._arena_candidate(
            source="semantic_to_transformation_compiler",
            candidate_id=compiler.get("selected_intent") or semantic.get("selected_intent") or "compiler_candidate",
            operation=semantic.get("compiled_operation"),
            confidence=semantic.get("compilation_confidence") or compiler.get("validation", {}).get("accuracy"),
            validation_status=semantic.get("compilation_status"),
            selected=bool(semantic.get("selected_from_compiler")),
            entered=success,
            blocked_reason=None if success else compiler.get("failure_reason") or "no_matching_compiler_rule",
        )]

    def _arena_candidates_from_adaptive_reuse(
        self,
        adaptive: dict[str, Any],
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not adaptive:
            return []
        rows = []
        reused = adaptive.get("reused_programs") or []
        if isinstance(reused, list):
            for index, program in enumerate(reused[:8]):
                rows.append(self._arena_candidate(
                    source="adaptive_reuse",
                    candidate_id=f"reused_program:{index}",
                    operation=self._program_operation(program),
                    confidence=self._first_number(adaptive.get("reuse_success_rate"), adaptive.get("reuse_rate")),
                    validation_status="REUSED",
                    selected=provenance.get("prediction_source") == "adaptive_reuse",
                    entered=True,
                ))
        if not rows and (
            adaptive.get("reuse_success_rate")
            or adaptive.get("reuse_rate")
            or adaptive.get("reused_assets")
        ):
            rows.append(self._arena_candidate(
                source="adaptive_reuse",
                candidate_id="adaptive_reuse_decision",
                operation=provenance.get("winning_candidate"),
                confidence=self._first_number(adaptive.get("reuse_success_rate"), adaptive.get("reuse_rate")),
                validation_status="REUSED",
                selected=provenance.get("prediction_source") == "adaptive_reuse",
                entered=True,
            ))
        return rows

    def _arena_candidates_from_synthesis(
        self,
        synthesis: dict[str, Any],
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows = []
        ranked = synthesis.get("ranked_candidates") or []
        if isinstance(ranked, list):
            for index, candidate in enumerate(ranked[:12]):
                if not isinstance(candidate, dict):
                    continue
                program = candidate.get("program", {})
                rows.append(self._arena_candidate(
                    source="transformation_synthesis",
                    candidate_id=f"synthesis_candidate:{index}",
                    operation=self._program_operation(program),
                    confidence=self._first_number(candidate.get("score"), candidate.get("confidence")),
                    validation_status=self._validation_from_accuracy(candidate.get("prediction_accuracy")),
                    selected=program and program == synthesis.get("selected_program"),
                    entered=True,
                ))
        selected = self._first_dict(synthesis, "selected_program")
        if selected and not rows:
            rows.append(self._arena_candidate(
                source="transformation_synthesis",
                candidate_id="selected_program",
                operation=self._program_operation(selected),
                confidence=self._first_number(synthesis.get("transformation_confidence"), synthesis.get("transformation_accuracy")),
                validation_status=self._validation_from_accuracy(synthesis.get("transformation_accuracy")),
                selected=provenance.get("prediction_source") == "transformation_synthesis",
                entered=True,
            ))
        return rows

    def _arena_candidates_from_color_mapping(
        self,
        color: dict[str, Any],
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not color or not (color.get("selected_program") or color.get("mapping_matrix")):
            return []
        return [self._arena_candidate(
            source="color_mapping",
            candidate_id="color_mapping_candidate",
            operation=self._program_operation(color.get("selected_program", {})) or "recolor",
            confidence=self._first_number(color.get("mapping_confidence"), color.get("program_accuracy")),
            validation_status=self._validation_from_accuracy(color.get("program_accuracy")),
            selected=provenance.get("prediction_source") == "color_mapping",
            entered=True,
        )]

    def _arena_candidates_from_search(
        self,
        search: dict[str, Any],
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows = []
        for key, source in (
            ("winning_programs", "adaptive_search"),
            ("counterfactual_candidates", "counterfactual_search"),
        ):
            values = search.get(key) or []
            if isinstance(values, list):
                for index, item in enumerate(values[:8]):
                    if not isinstance(item, dict):
                        continue
                    rows.append(self._arena_candidate(
                        source=source,
                        candidate_id=f"{source}:{index}",
                        operation=self._program_operation(item.get("program", item)),
                        confidence=self._first_number(item.get("score"), item.get("prediction_accuracy")),
                        validation_status=self._validation_from_accuracy(item.get("prediction_accuracy")),
                        selected=provenance.get("prediction_source") == source,
                        entered=True,
                    ))
        return rows

    def _arena_candidates_from_repair(
        self,
        repair: dict[str, Any],
        provenance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not repair or not (repair.get("repair_applied") or repair.get("repair_success_rate")):
            return []
        return [self._arena_candidate(
            source="repair",
            candidate_id="repair_candidate",
            operation=repair.get("repair_operation") or repair.get("operation"),
            confidence=repair.get("repair_success_rate"),
            validation_status="REPAIR_APPLIED",
            selected=provenance.get("prediction_source") == "repair",
            entered=True,
        )]

    def _arena_source_statuses(
        self,
        compiler: dict[str, Any],
        adaptive: dict[str, Any],
        synthesis: dict[str, Any],
        color: dict[str, Any],
        search: dict[str, Any],
        repair: dict[str, Any],
        participants: list[dict[str, Any]],
    ) -> dict[str, str]:
        active = {candidate.get("source") for candidate in participants}
        return {
            "semantic_to_transformation_compiler": (
                "ENTERED" if "semantic_to_transformation_compiler" in active
                else "NOT_TRIGGERED" if not compiler
                else "BLOCKED"
            ),
            "adaptive_reuse": "ENTERED" if "adaptive_reuse" in active else "NOT_TRIGGERED" if not adaptive else "NO_EXECUTABLE_CANDIDATE",
            "transformation_synthesis": "ENTERED" if "transformation_synthesis" in active else "NOT_TRIGGERED" if not synthesis else "NO_EXECUTABLE_CANDIDATE",
            "color_mapping": "ENTERED" if "color_mapping" in active else "NOT_TRIGGERED" if not color else "NO_EXECUTABLE_CANDIDATE",
            "adaptive_search": "ENTERED" if "adaptive_search" in active else "NOT_TRIGGERED" if not search else "NO_EXECUTABLE_CANDIDATE",
            "repair": "ENTERED" if "repair" in active else "NOT_TRIGGERED" if not repair else "NO_EXECUTABLE_CANDIDATE",
        }

    def _arena_candidate(
        self,
        *,
        source: str,
        candidate_id: Any,
        operation: Any = None,
        confidence: Any = None,
        validation_status: Any = None,
        selected: bool = False,
        entered: bool = True,
        blocked_reason: Any = None,
    ) -> dict[str, Any]:
        return {
            "source": source,
            "candidate_id": str(candidate_id or source),
            "operation": operation,
            "confidence": self._first_number(confidence),
            "validation_status": validation_status or "UNKNOWN",
            "selected": bool(selected),
            "entered_arena": bool(entered),
            "blocked_reason": blocked_reason,
        }

    def _dedupe_arena_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        unique = []
        for candidate in candidates:
            key = (
                candidate.get("source"),
                candidate.get("candidate_id"),
                candidate.get("operation"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique

    def _program_operation(self, program: Any) -> Any:
        if not isinstance(program, dict):
            return None
        steps = program.get("steps") or []
        if steps and isinstance(steps[0], dict):
            return steps[0].get("operation")
        return program.get("operation") or program.get("primitive")

    def _validation_from_accuracy(self, accuracy: Any) -> str:
        value = self._first_number(accuracy)
        if value is None:
            return "UNKNOWN"
        if value >= 1.0:
            return "SUCCESS"
        if value > 0.0:
            return "PARTIAL"
        return "FAILED"

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
        reconciled_records: list[dict[str, Any]] = []
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
            reconciled_records.append(record)
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
        if rows or records or total_runtime:
            reconciliation = hierarchical_timing_reconciliation_engine.reconcile(
                reconciled_records,
                total_wall_time=total_runtime,
                active_compute_time=active_compute,
                stage_rows=rows,
            )
            hierarchy_rows = reconciliation["timing_hierarchy_summary"]
            resource_ranking = reconciliation["resource_consumption_ranking"]
        else:
            reconciliation = {
                "timing_hierarchy_valid": False,
                "timing_reconciliation_success": False,
                "root_timing_id": None,
                "timing_node_count": 0,
                "parent_node_count": 0,
                "child_node_count": 0,
                "exclusive_time_total": 0.0,
                "inclusive_time_total": 0.0,
                "overlap_duration": 0.0,
                "parallel_overlap_duration": 0.0,
                "duplicate_overlap_duration": 0.0,
                "resource_percentage_sum": 0.0,
                "resource_percentage_denominator": "ACTIVE_COMPUTE_TIME",
                "active_compute_time": active_compute,
                "overlap_detected": False,
                "overlap_accounted_for": True,
                "diagnostic_timing_nodes": [],
                "timing_source_conflicts": [],
                "timing_boundary_violations": [],
            }
            hierarchy_rows = []
            resource_ranking = []
        top = [
            {
                "rank": index + 1,
                "stage_name": row["stage_name"],
                "duration_seconds": row["exclusive_duration"],
                "exclusive_duration": row["exclusive_duration"],
                "percentage_of_active_compute": row["percentage_of_active_compute"],
                "percentage_denominator": row["percentage_denominator"],
                "timing_scope": "EXCLUSIVE_RESOURCE_RANKING",
            }
            for index, row in enumerate(resource_ranking[:3])
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
        reporting_timing = report_timing_semantic_engine.reconcile(
            timing_records=reconciled_records,
            performance=performance,
            timing_state=timing_state,
            timing_summary=timing_summary,
            runtime_metadata=runtime_metadata,
        )
        reporting_summary = reporting_timing["report_timing_summary"]
        finalization = self._first_number(
            timing_state.get("finalization_time"),
            self._summary_duration(timing_summary, "finalization_time"),
            performance.get("finalization_duration"),
        )
        return {
            **timing_state,
            "stage_timing_summary": hierarchy_rows,
            "timing_hierarchy_summary": hierarchy_rows,
            "resource_consumption_ranking": resource_ranking,
            "timing_reconciliation_summary": {
                key: reconciliation.get(key)
                for key in (
                    "timing_hierarchy_valid",
                    "timing_reconciliation_success",
                    "root_timing_id",
                    "timing_node_count",
                    "parent_node_count",
                    "child_node_count",
                    "exclusive_time_total",
                    "inclusive_time_total",
                    "overlap_duration",
                    "parallel_overlap_duration",
                    "duplicate_overlap_duration",
                    "resource_percentage_sum",
                    "resource_percentage_denominator",
                    "overlap_detected",
                    "overlap_accounted_for",
                )
            },
            "reporting_timing_summary": reporting_summary,
            "reporting_timing_nodes": reporting_timing["report_timing_nodes"],
            "legacy_report_timing_mappings": reporting_timing["legacy_report_timing_mappings"],
            "report_timing_taxonomy": reporting_timing["report_timing_taxonomy"],
            "runtime_timing_summary": {
                "total_wall_time": total_runtime,
                "active_compute_time": reconciliation.get("active_compute_time", active_compute),
                "cognitive_runtime_time": self._first_number(timing_state.get("cognitive_runtime_time")),
                "untracked_time": untracked,
                "timing_coverage": coverage,
                "report_lifecycle_total_time": reporting_summary.get("report_lifecycle_total_time"),
                "final_report_rendering_time": reporting_summary.get("final_report_rendering_time"),
                "report_generation_time": report_generation,
                "finalization_time": finalization,
                "stage_count": len(hierarchy_rows),
                "top_three_exclusive_time_consumers": top,
                "overlap_detected": reconciliation.get("overlap_detected"),
                "untracked_time_denominator": "TOTAL_WALL_TIME",
            },
            "top_time_consumers": top,
            "timing_coverage": coverage,
            "untracked_time": untracked,
            "active_compute_time": active_compute,
            "report_generation_time": report_generation,
            "report_lifecycle_total_time": reporting_summary.get("report_lifecycle_total_time"),
            "final_report_rendering_time": reporting_summary.get("final_report_rendering_time"),
            "finalization_time": finalization,
            "highest_time_consumer": highest.get("stage_name"),
            "highest_time_consumer_percentage": highest.get("percentage_of_active_compute"),
            "lowest_productive_stage": lowest.get("stage_name"),
            "resource_distribution_status": "AVAILABLE" if rows else "NOT_AVAILABLE",
            "diagnostic_timing_nodes": reconciliation["diagnostic_timing_nodes"],
            "timing_source_conflicts": reconciliation["timing_source_conflicts"],
            "timing_boundary_violations": reconciliation["timing_boundary_violations"],
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
            "raw": deepcopy(raw or {}),
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
