from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

from core.concept_lifecycle.unified_concept_lifecycle import (
    unified_concept_lifecycle_builder,
)
from runtime.program_generation import (
    cognitive_program_lifecycle_registry,
    program_blueprint_intelligence_layer,
    program_generation_layer,
)
from runtime.knowledge import (
    cognitive_domain_constitution_registry,
    cognitive_domain_ecosystem_registry,
    cognitive_domain_governance_registry,
    cognitive_domain_intelligence_layer,
    cognitive_domain_interaction_registry,
    cognitive_domain_lifecycle_registry,
    cognitive_knowledge_domain_registry,
)
from runtime.timing import hierarchical_timing_reconciliation_engine
from runtime.reporting.report_timing_semantics import report_timing_semantic_engine
from runtime.reporting.pre_final_report_diagnostics import (
    pre_final_report_diagnostics,
)
from runtime.transformation_compilation.compiler_infrastructure import (
    compiler_infrastructure_analyzer,
)
from runtime.capability_intelligence.operational_domain_infrastructure import (
    operational_domain_infrastructure,
)
from runtime.capability_intelligence.capability_ecology_analysis import (
    capability_ecology_analysis,
)
from runtime.capability_intelligence.operational_economy_analysis import (
    operational_economy_analysis,
)


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
        "candidate_proposal_report",
        "cognitive_candidate_arena_report",
        "truth_metrics",
        "memory_metrics",
        "search_metrics",
        "knowledge_pipeline_metrics",
        "representation_metrics",
        "semantic_compilation_report",
        "executable_semantic_coverage_report",
        "unified_concept_lifecycle_report",
        "program_generation_report",
        "program_blueprint_intelligence_report",
        "cognitive_program_lifecycle_report",
        "cognitive_knowledge_domains_report",
        "cognitive_domain_intelligence_report",
        "cognitive_domain_lifecycle_report",
        "cognitive_domain_interaction_report",
        "cognitive_domain_governance_report",
        "cognitive_domain_ecosystem_report",
        "cognitive_domain_constitution_report",
    }
    EXPENSIVE_DERIVED_SOURCE_NAMES = {
        "unified_concept_lifecycle_report",
        "program_generation_report",
        "program_blueprint_intelligence_report",
        "cognitive_program_lifecycle_report",
        "cognitive_knowledge_domains_report",
        "cognitive_domain_intelligence_report",
        "cognitive_domain_lifecycle_report",
        "cognitive_domain_interaction_report",
        "cognitive_domain_governance_report",
        "cognitive_domain_ecosystem_report",
        "cognitive_domain_constitution_report",
    }
    DOMAIN_BOOTSTRAP_SOURCE_NAMES = {
        "cognitive_knowledge_domains_report",
        "cognitive_domain_intelligence_report",
        "cognitive_domain_lifecycle_report",
        "cognitive_domain_interaction_report",
        "cognitive_domain_governance_report",
        "cognitive_domain_ecosystem_report",
        "cognitive_domain_constitution_report",
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
        self._source_visibility_cache = {}
        pre_final_report_diagnostics.phase_enter(
            "REPORT_SOURCE_COLLECTION",
            report_keys=len(report_state),
            metadata_keys=len(runtime_metadata),
            binding_count=len(self.field_bindings),
        )
        sources = self.discover_sources(
            report_state,
            runtime_metadata=runtime_metadata,
            report_level=normalized_level,
        )
        pre_final_report_diagnostics.phase_exit(
            "REPORT_SOURCE_COLLECTION",
            source_count=len(sources),
            total_source_keys=sum(
                len(source.payload) for source in sources.values()
                if isinstance(source.payload, dict)
            ),
        )
        registry_errors = self.validate_field_registry(self.field_bindings)
        bound_fields: dict[str, BoundReportField] = {}

        for definition in self.field_bindings:
            pre_final_report_diagnostics.count("canonical_fields_processed")
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
        report_level: str = "normal",
    ) -> dict[str, CanonicalSource]:
        report_state = report_state if isinstance(report_state, dict) else {}
        runtime_metadata = (
            runtime_metadata if isinstance(runtime_metadata, dict) else {}
        )
        normalized_level = self._normalize_report_level(report_level)
        needed_sources = self._needed_sources(normalized_level)
        performance = self._first_dict(
            report_state,
            "performance_report",
            "PERFORMANCE_REPORT",
        )
        pre_final_report_diagnostics.collection_snapshot(
            "CANONICAL_DISCOVER_INPUT",
            {
                "report_state": report_state,
                "performance": performance,
                "runtime_metadata": runtime_metadata,
            },
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
                    visible_report_state,
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
                    visible_report_state,
                    self._first_dict(report_state, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "COGNITIVE_ROUTE_INTELLIGENCE_REPORT"),
                    self._first_dict(performance, "COGNITIVE_SEARCH_REPORT", "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT", "COGNITIVE_ROUTE_INTELLIGENCE_REPORT"),
                    self._first_dict(report_state, "search_metrics"),
                ),
            ),
            "program_registry": CanonicalSource(
                "program_registry",
                self._merge_dicts(
                    visible_report_state,
                    self._first_dict(report_state, "PROGRAM_SYNTHESIS_REPORT", "program_synthesis_report"),
                    self._first_dict(performance, "PROGRAM_SYNTHESIS_REPORT", "program_synthesis_report"),
                    self._first_dict(report_state, "program_registry"),
                ),
            ),
            "semantic_compilation_report": CanonicalSource(
                "semantic_compilation_report",
                self._build_semantic_compilation_visibility(report_state, performance),
            ),
            "executable_semantic_coverage_report": CanonicalSource(
                "executable_semantic_coverage_report",
                self._build_executable_semantic_coverage_visibility(report_state, performance),
            ),
            "cognitive_capability_coverage_report": CanonicalSource(
                "cognitive_capability_coverage_report",
                self._cached_visibility(
                    "cognitive_capability_coverage_report",
                    lambda: self._build_cognitive_capability_coverage_visibility(report_state, performance),
                ),
            ),
            "prediction_provenance_report": CanonicalSource(
                "prediction_provenance_report",
                self._cached_visibility(
                    "prediction_provenance_report",
                    lambda: self._build_prediction_provenance_visibility(report_state, performance),
                ),
            ),
            "candidate_proposal_report": CanonicalSource(
                "candidate_proposal_report",
                self._cached_visibility(
                    "candidate_proposal_report",
                    lambda: self._build_candidate_proposal_visibility(report_state, performance),
                ),
            ),
            "cognitive_candidate_arena_report": CanonicalSource(
                "cognitive_candidate_arena_report",
                self._cached_visibility(
                    "cognitive_candidate_arena_report",
                    lambda: self._build_candidate_arena_visibility(report_state, performance),
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
                    visible_report_state,
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
        optional_builders = {
            "unified_concept_lifecycle_report": self._build_unified_concept_lifecycle_visibility,
            "program_generation_report": self._build_program_generation_visibility,
            "program_blueprint_intelligence_report": self._build_program_blueprint_intelligence_visibility,
            "cognitive_program_lifecycle_report": self._build_cognitive_program_lifecycle_visibility,
            "cognitive_knowledge_domains_report": self._build_cognitive_knowledge_domains_visibility,
            "cognitive_domain_intelligence_report": self._build_cognitive_domain_intelligence_visibility,
            "cognitive_domain_lifecycle_report": self._build_cognitive_domain_lifecycle_visibility,
            "cognitive_domain_interaction_report": self._build_cognitive_domain_interaction_visibility,
            "cognitive_domain_governance_report": self._build_cognitive_domain_governance_visibility,
            "cognitive_domain_ecosystem_report": self._build_cognitive_domain_ecosystem_visibility,
            "cognitive_domain_constitution_report": self._build_cognitive_domain_constitution_visibility,
        }
        for source_name, builder in optional_builders.items():
            if not self._should_build_optional_source(
                source_name,
                report_state,
                normalized_level,
            ):
                continue
            if source_name in needed_sources:
                sources[source_name] = CanonicalSource(
                    source_name,
                    self._cached_visibility(
                        source_name,
                        lambda builder=builder: builder(report_state, performance),
                    ),
                )

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

        if (
            normalized_level != "DIAGNOSTIC"
            and not self._state_within_derived_report_budget(report_state)
        ):
            named_sources = self._discover_top_level_named_sources(report_state)
        else:
            named_sources = self._discover_named_sources(report_state)
        for name, payload in named_sources.items():
            pre_final_report_diagnostics.count("canonical_named_sources_seen")
            if name not in sources:
                sources[name] = CanonicalSource(name, payload)

        return sources

    def _needed_sources(self, report_level: str) -> set[str]:
        needed = {
            definition.canonical_source
            for definition in self.field_bindings
            if definition.visible_at(report_level)
        }
        needed.update({
            "report_state",
            "runtime_metadata",
            "performance_report",
            "execution_timing_state",
        })
        return needed

    def _should_build_optional_source(
        self,
        source_name: str,
        report_state: dict[str, Any],
        report_level: str,
    ) -> bool:
        if (
            report_level == "DIAGNOSTIC"
            or source_name in self.DOMAIN_BOOTSTRAP_SOURCE_NAMES
            or source_name not in self.EXPENSIVE_DERIVED_SOURCE_NAMES
            or self._has_explicit_source(report_state, source_name)
        ):
            return True
        return self._state_within_derived_report_budget(report_state)

    def _has_explicit_source(
        self,
        report_state: dict[str, Any],
        source_name: str,
    ) -> bool:
        candidates = {
            source_name,
            source_name.upper(),
            source_name.replace("_report", "").upper() + "_REPORT",
        }
        return any(isinstance(report_state.get(key), dict) for key in candidates)

    def _state_within_derived_report_budget(
        self,
        report_state: dict[str, Any],
        *,
        max_nodes: int = 5_000,
        max_depth: int = 10,
        max_list_items: int = 100,
    ) -> bool:
        seen: set[int] = set()
        nodes = 0

        def visit(value: Any, depth: int) -> bool:
            nonlocal nodes
            if nodes > max_nodes or depth > max_depth:
                return False
            if isinstance(value, (dict, list, tuple, set)):
                ident = id(value)
                if ident in seen:
                    return True
                seen.add(ident)
            nodes += 1
            if nodes > max_nodes:
                return False
            if isinstance(value, dict):
                for item in value.values():
                    if not visit(item, depth + 1):
                        return False
            elif isinstance(value, (list, tuple, set)):
                items = list(value)
                if len(items) > max_list_items:
                    return False
                for item in items:
                    if not visit(item, depth + 1):
                        return False
            return True

        return visit(report_state, 0)

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
            value=self._diag_deepcopy(value, f"bound_field:{definition.field_name}"),
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
                return self._diag_deepcopy(value, f"first_dict:{key}")
        return {}

    def _merge_dicts(self, *items: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for item in items:
            if isinstance(item, dict):
                merged.update(self._diag_deepcopy(item, "merge_dicts"))
        return merged

    def _discover_named_sources(self, report_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
        discovered: dict[str, dict[str, Any]] = {}

        def visit(item: Any) -> None:
            if isinstance(item, dict):
                pre_final_report_diagnostics.count("canonical_named_source_dict_nodes")
                for key, value in item.items():
                    name = str(key)
                    if (
                        name in self.DISCOVERABLE_SOURCE_NAMES
                        or name.endswith("_metrics")
                        or name.endswith("_registry")
                        or name.endswith("_snapshots")
                    ) and isinstance(value, dict):
                        discovered.setdefault(
                            name,
                            self._diag_deepcopy(value, f"discover_named:{name}"),
                        )
                    visit(value)
            elif isinstance(item, list):
                pre_final_report_diagnostics.count("canonical_named_source_lists")
                for child in item[:100]:
                    visit(child)

        visit(report_state)
        return discovered

    def _discover_top_level_named_sources(
        self,
        report_state: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        discovered: dict[str, dict[str, Any]] = {}
        if not isinstance(report_state, dict):
            return discovered
        for key, value in report_state.items():
            name = str(key)
            if (
                name in self.DISCOVERABLE_SOURCE_NAMES
                or name.endswith("_metrics")
                or name.endswith("_registry")
                or name.endswith("_snapshots")
            ) and isinstance(value, dict):
                discovered.setdefault(
                    name,
                    self._diag_deepcopy(value, f"discover_top_level:{name}"),
                )
        return discovered

    def _diag_deepcopy(self, value: Any, label: str) -> Any:
        pre_final_report_diagnostics.count(f"deepcopy:{label}")
        if isinstance(value, dict):
            pre_final_report_diagnostics.mark(
                "DEEPCOPY_DICT",
                label=label,
                keys=len(value),
            )
        elif isinstance(value, list):
            pre_final_report_diagnostics.mark(
                "DEEPCOPY_LIST",
                label=label,
                items=len(value),
            )
        return self._bounded_copy(value)

    def _bounded_copy(
        self,
        value: Any,
        *,
        max_depth: int = 5,
        max_list_items: int = 100,
        max_dict_items: int = 340,
        _depth: int = 0,
        _seen: set[int] | None = None,
    ) -> Any:
        if _depth >= max_depth:
            return self._summarize_container(value)
        if isinstance(value, dict):
            _seen = _seen or set()
            object_id = id(value)
            if object_id in _seen:
                return {"recursive_reference": True}
            _seen.add(object_id)
            copied: dict[str, Any] = {}
            for index, (key, item) in enumerate(value.items()):
                if index >= max_dict_items:
                    copied["__truncated_dict_items__"] = max(0, len(value) - max_dict_items)
                    break
                copied[key] = self._bounded_copy(
                    item,
                    max_depth=max_depth,
                    max_list_items=max_list_items,
                    max_dict_items=max_dict_items,
                    _depth=_depth + 1,
                    _seen=_seen,
                )
            _seen.discard(object_id)
            return copied
        if isinstance(value, (list, tuple, set)):
            _seen = _seen or set()
            object_id = id(value)
            if object_id in _seen:
                return [{"recursive_reference": True}]
            _seen.add(object_id)
            items = list(value)
            copied_items = [
                self._bounded_copy(
                    item,
                    max_depth=max_depth,
                    max_list_items=max_list_items,
                    max_dict_items=max_dict_items,
                    _depth=_depth + 1,
                    _seen=_seen,
                )
                for item in items[:max_list_items]
            ]
            if len(items) > max_list_items:
                copied_items.append({
                    "__truncated_list_items__": len(items) - max_list_items,
                })
            _seen.discard(object_id)
            return copied_items
        return value

    def _summarize_container(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {"__dict_keys__": len(value)}
        if isinstance(value, (list, tuple, set)):
            return {"__list_items__": len(value)}
        return value

    def _cached_visibility(self, name: str, factory: Any) -> dict[str, Any]:
        cache = getattr(self, "_source_visibility_cache", None)
        if not isinstance(cache, dict):
            cache = {}
            self._source_visibility_cache = cache
        if name not in cache:
            cache[name] = factory()
        value = cache.get(name)
        return value if isinstance(value, dict) else {}

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
            bind("average_program_confidence", "Program Confidence Engine", "program_registry", ("average_program_confidence", "average_confidence", "confidence"), "metric", visibility=all_levels),
            bind("highest_confidence", "Program Confidence Engine", "program_registry", ("highest_confidence", "max_confidence"), "metric"),
            bind("lowest_confidence", "Program Confidence Engine", "program_registry", ("lowest_confidence", "min_confidence"), "metric"),
            bind("validation_distribution", "Program Runtime", "program_registry", ("validation_distribution", "program_validation_distribution"), "summary", compression_policy="COMPRESSED"),
            bind("semantic_compilation_summary", "Semantic Compilation", "semantic_compilation_report", ("semantic_compilation_summary",), "summary", visibility=normal),
            bind("semantic_compilation_diagnostics", "Semantic Compilation", "semantic_compilation_report", ("semantic_compilation_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("executable_semantic_coverage_summary", "Executable Semantic Coverage", "executable_semantic_coverage_report", ("executable_semantic_coverage_summary",), "summary", visibility=normal),
            bind("executable_semantic_coverage_diagnostics", "Executable Semantic Coverage", "executable_semantic_coverage_report", ("executable_semantic_coverage_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_capability_coverage_summary", "Cognitive Capability Coverage", "cognitive_capability_coverage_report", ("cognitive_capability_coverage_summary",), "summary", visibility=normal),
            bind("cognitive_capability_coverage_diagnostics", "Cognitive Capability Coverage", "cognitive_capability_coverage_report", ("cognitive_capability_coverage_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("unified_concept_lifecycle_summary", "Unified Concept Lifecycle", "unified_concept_lifecycle_report", ("unified_concept_lifecycle_summary",), "summary", visibility=normal),
            bind("unified_concept_lifecycle_diagnostics", "Unified Concept Lifecycle", "unified_concept_lifecycle_report", ("unified_concept_lifecycle_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("program_generation_summary", "Program Generation", "program_generation_report", ("program_generation_summary",), "summary", visibility=normal),
            bind("program_generation_diagnostics", "Program Generation", "program_generation_report", ("program_generation_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("program_blueprint_intelligence_summary", "Program Blueprint Intelligence", "program_blueprint_intelligence_report", ("program_blueprint_intelligence_summary",), "summary", visibility=normal),
            bind("program_blueprint_intelligence_diagnostics", "Program Blueprint Intelligence", "program_blueprint_intelligence_report", ("program_blueprint_intelligence_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_program_lifecycle_summary", "Cognitive Program Lifecycle", "cognitive_program_lifecycle_report", ("cognitive_program_lifecycle_summary",), "summary", visibility=normal),
            bind("cognitive_program_lifecycle_diagnostics", "Cognitive Program Lifecycle", "cognitive_program_lifecycle_report", ("cognitive_program_lifecycle_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_knowledge_domains_summary", "Cognitive Knowledge Domains", "cognitive_knowledge_domains_report", ("cognitive_knowledge_domains_summary",), "summary", visibility=normal),
            bind("cognitive_knowledge_domains_diagnostics", "Cognitive Knowledge Domains", "cognitive_knowledge_domains_report", ("cognitive_knowledge_domains_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_domain_intelligence_summary", "Cognitive Domain Intelligence", "cognitive_domain_intelligence_report", ("cognitive_domain_intelligence_summary",), "summary", visibility=normal),
            bind("cognitive_domain_intelligence_diagnostics", "Cognitive Domain Intelligence", "cognitive_domain_intelligence_report", ("cognitive_domain_intelligence_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_domain_lifecycle_summary", "Cognitive Domain Lifecycle", "cognitive_domain_lifecycle_report", ("cognitive_domain_lifecycle_summary",), "summary", visibility=normal),
            bind("cognitive_domain_lifecycle_diagnostics", "Cognitive Domain Lifecycle", "cognitive_domain_lifecycle_report", ("cognitive_domain_lifecycle_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_domain_interaction_summary", "Cognitive Domain Interaction", "cognitive_domain_interaction_report", ("cognitive_domain_interaction_summary",), "summary", visibility=normal),
            bind("cognitive_domain_interaction_diagnostics", "Cognitive Domain Interaction", "cognitive_domain_interaction_report", ("cognitive_domain_interaction_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_domain_governance_summary", "Cognitive Domain Governance", "cognitive_domain_governance_report", ("cognitive_domain_governance_summary",), "summary", visibility=normal),
            bind("cognitive_domain_governance_diagnostics", "Cognitive Domain Governance", "cognitive_domain_governance_report", ("cognitive_domain_governance_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_domain_ecosystem_summary", "Cognitive Domain Ecosystem", "cognitive_domain_ecosystem_report", ("cognitive_domain_ecosystem_summary",), "summary", visibility=normal),
            bind("cognitive_domain_ecosystem_diagnostics", "Cognitive Domain Ecosystem", "cognitive_domain_ecosystem_report", ("cognitive_domain_ecosystem_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("cognitive_domain_constitution_summary", "Cognitive Domain Constitution", "cognitive_domain_constitution_report", ("cognitive_domain_constitution_summary",), "summary", visibility=normal),
            bind("cognitive_domain_constitution_diagnostics", "Cognitive Domain Constitution", "cognitive_domain_constitution_report", ("cognitive_domain_constitution_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("prediction_provenance_summary", "Transformation Decision Runtime", "prediction_provenance_report", ("prediction_provenance_summary",), "summary", visibility=normal),
            bind("prediction_provenance_diagnostics", "Transformation Decision Runtime", "prediction_provenance_report", ("prediction_provenance_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("candidate_proposal_summary", "Candidate Proposal Runtime", "candidate_proposal_report", ("candidate_proposal_summary",), "summary", visibility=normal),
            bind("candidate_proposal_diagnostics", "Candidate Proposal Runtime", "candidate_proposal_report", ("candidate_proposal_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("candidate_arena_summary", "Cognitive Candidate Arena", "cognitive_candidate_arena_report", ("candidate_arena_summary",), "summary", visibility=normal),
            bind("candidate_arena_diagnostics", "Cognitive Candidate Arena", "cognitive_candidate_arena_report", ("candidate_arena_diagnostics",), "summary", visibility=diagnostic, compression_policy="COMPRESSED", externalized=True),
            bind("overall_search_quality", "Search Runtime", "search_metrics", ("overall_search_quality",), "metric", visibility=all_levels),
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
        compiler_selected = self._tool_selected(
            report_state,
            performance,
            "semantic_to_transformation_compiler",
        )
        selected_program = self._first_dict(synthesis, "selected_program")
        selected_steps = selected_program.get("steps", []) if isinstance(selected_program, dict) else []
        selected_step = selected_steps[0] if selected_steps and isinstance(selected_steps[0], dict) else {}
        compiler_program = self._first_dict(compiler, "compiled_program")
        compiler_steps = compiler_program.get("steps", []) if isinstance(compiler_program, dict) else []
        compiler_step = compiler_steps[0] if compiler_steps and isinstance(compiler_steps[0], dict) else {}
        triggered = bool(compiler) or bool(synthesis) or compiler_selected
        compilation_success = bool(
            compiler.get("semantic_to_transformation_compilation_success")
        )
        compiler_operation = compiler_step.get("operation")
        selected_operation = selected_step.get("operation")
        selected_from_compiler = bool(
            compilation_success
            and compiler_program
            and selected_program
            and (
                compiler_program == selected_program
                or (
                    compiler_operation
                    and selected_operation
                    and compiler_operation == selected_operation
                )
            )
        )
        validation = self._first_dict(compiler, "validation")
        if not compiler and compiler_selected:
            status = "REQUIRED_REPORT_MISSING"
        elif not compiler:
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
        if not failure_cause and status == "REQUIRED_REPORT_MISSING":
            failure_cause = "Semantic compiler selected but no compilation report was produced."
        elif not failure_cause and status == "NO_MATCHING_COMPILER_RULE":
            failure_cause = "No matching compiler rule."
        elif not failure_cause and execution_status == "NOT_SELECTED":
            failure_cause = "Compiled program was not selected by synthesis ranking."
        elif not failure_cause and execution_status == "FAILED":
            failure_cause = "Compiled program did not match target output."

        semantic_intent_success = bool(
            self._first_dict(compiler, "semantic_intent_routing_report").get(
                "semantic_intent_routing_success"
            )
        )
        execution_intents = compiler.get("execution_intents") or []
        compiler_activation_source = (
            "semantic_intent_router"
            if semantic_intent_success
            else "program_generation_activation_bridge"
            if execution_intents
            else "none"
        )
        router_integration_status = (
            "ROUTER_DRIVEN"
            if semantic_intent_success and triggered
            else "FALLBACK_BRIDGE_ACTIVE"
            if triggered and execution_intents
            else "NOT_INTEGRATED"
            if triggered
            else "NOT_TRIGGERED"
        )
        compiler_advisory_state = (
            "ADVISORY_EXACT_MATCH_NOT_SELECTED"
            if (
                compilation_success
                and validation.get("exact_match")
                and not selected_from_compiler
            )
            else "SELECTED_EXECUTABLE"
            if selected_from_compiler and validation.get("exact_match")
            else "ADVISORY_NEEDS_REVIEW"
            if compilation_success and not selected_from_compiler
            else "NOT_AVAILABLE"
        )

        summary = {
            "compiler_triggered": triggered,
            "compiler_selected": compiler_selected,
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
            "execution_intents": execution_intents,
            "execution_intent_count": len(execution_intents),
            "semantic_intent_routing_success": semantic_intent_success,
            "compiler_activation_source": compiler_activation_source,
            "semantic_intent_router_integration_status": router_integration_status,
            "compiler_advisory_state": compiler_advisory_state,
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

    def _build_unified_concept_lifecycle_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "UNIFIED_CONCEPT_LIFECYCLE_REPORT", "unified_concept_lifecycle_report"),
            self._first_dict(performance, "UNIFIED_CONCEPT_LIFECYCLE_REPORT", "unified_concept_lifecycle_report"),
        )
        explicit_program_generation = self._merge_dicts(
            self._first_dict(report_state, "PROGRAM_GENERATION_REPORT", "program_generation_report"),
            self._first_dict(performance, "PROGRAM_GENERATION_REPORT", "program_generation_report"),
        )
        built = unified_concept_lifecycle_builder.build(
            report_state,
            performance,
        )
        if not explicit_program_generation:
            explicit_program_generation = program_generation_layer.generate(built)
        lifecycle = self._merge_dicts(built, explicit)
        if explicit_program_generation:
            lifecycle["program_generation_report"] = explicit_program_generation
        rows = lifecycle.get("concept_lifecycles", [])
        rows = rows if isinstance(rows, list) else []
        rows = self._merge_program_generation_state(rows, explicit_program_generation)
        status_counts = lifecycle.get("lifecycle_status_counts", {})
        status_counts = status_counts if isinstance(status_counts, dict) else {}
        summary = {
            "concept_count": int(lifecycle.get("concept_count") or len(rows)),
            "concept_lifecycles": rows,
            "lifecycle_status_counts": status_counts,
            "canonical_concept_lifecycle_source": bool(
                lifecycle.get("canonical_concept_lifecycle_source", True)
            ),
            "concepts_traceable_from_discovery": bool(
                lifecycle.get("concepts_traceable_from_discovery", True)
            ),
        }
        return {
            "unified_concept_lifecycle_summary": summary,
            "unified_concept_lifecycle_diagnostics": lifecycle,
            **summary,
        }

    def _merge_program_generation_state(
        self,
        rows: list[Any],
        program_generation: dict[str, Any],
    ) -> list[Any]:
        if not isinstance(program_generation, dict):
            return rows
        blueprints = program_generation.get("program_blueprints", [])
        if not isinstance(blueprints, list):
            return rows
        by_concept = {
            str(item.get("concept_name")): item
            for item in blueprints
            if isinstance(item, dict) and item.get("concept_name") is not None
        }
        if not by_concept:
            return rows
        merged: list[Any] = []
        for row in rows:
            if not isinstance(row, dict):
                merged.append(row)
                continue
            concept = str(row.get("concept_name"))
            blueprint = by_concept.get(concept)
            if not blueprint:
                merged.append(row)
                continue
            updated = dict(row)
            updated["program_generation_attempted"] = blueprint.get(
                "generation_attempted",
                updated.get("program_generation_attempted", "FALSE"),
            )
            updated["program_generation_success"] = blueprint.get(
                "generation_success",
                updated.get("program_generation_success", "FALSE"),
            )
            updated["program_generated"] = blueprint.get(
                "generation_success",
                updated.get("program_generated", "FALSE"),
            )
            updated["program_generation_status"] = blueprint.get(
                "generation_status",
                updated.get("program_generation_status", "NOT_EVALUATED"),
            )
            merged.append(updated)
        return merged

    def _build_program_generation_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "PROGRAM_GENERATION_REPORT", "program_generation_report"),
            self._first_dict(performance, "PROGRAM_GENERATION_REPORT", "program_generation_report"),
        )
        if explicit:
            report = explicit
        else:
            lifecycle = self._cached_visibility(
                "unified_concept_lifecycle_report",
                lambda: self._build_unified_concept_lifecycle_visibility(
                    report_state,
                    performance,
                ),
            )
            report = program_generation_layer.generate(lifecycle)
        blueprints = report.get("program_blueprints", [])
        blueprints = blueprints if isinstance(blueprints, list) else []
        summary = {
            "generated_programs": int(report.get("generated_programs") or 0),
            "eligible_concepts": int(report.get("eligible_concepts") or 0),
            "generated_blueprints": int(report.get("generated_blueprints") or 0),
            "blocked_programs": int(report.get("blocked_programs") or 0),
            "missing_requirements": report.get("missing_requirements", []),
            "generation_success_rate": report.get("generation_success_rate", 0.0),
            "program_blueprints": blueprints,
            "execution_agnostic": bool(report.get("execution_agnostic", True)),
            "competition_agnostic": bool(report.get("competition_agnostic", True)),
        }
        return {
            "program_generation_summary": summary,
            "program_generation_diagnostics": report,
            **summary,
        }

    def _build_program_blueprint_intelligence_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT", "program_blueprint_intelligence_report"),
            self._first_dict(performance, "PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT", "program_blueprint_intelligence_report"),
        )
        if explicit:
            report = explicit
        else:
            program_generation = self._build_program_generation_visibility(
                report_state,
                performance,
            )
            report = program_blueprint_intelligence_layer.analyze(
                program_generation,
            )
        intelligence = report.get("program_blueprint_intelligence", [])
        intelligence = intelligence if isinstance(intelligence, list) else []
        validation = report.get("validation", {})
        validation = validation if isinstance(validation, dict) else {}
        summary = {
            "program_intelligence_count": int(report.get("program_intelligence_count") or len(intelligence)),
            "program_blueprint_intelligence": intelligence,
            "execution_readiness_counts": report.get("execution_readiness_counts", {}),
            "validation_success": bool(validation.get("validation_success", True)),
            "validation_failures": validation.get("validation_failures", []),
            "capability_failures_silent": bool(report.get("capability_failures_silent", False)),
        }
        return {
            "program_blueprint_intelligence_summary": summary,
            "program_blueprint_intelligence_diagnostics": report,
            **summary,
        }

    def _build_cognitive_program_lifecycle_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_PROGRAM_LIFECYCLE_REPORT", "cognitive_program_lifecycle_report"),
            self._first_dict(performance, "COGNITIVE_PROGRAM_LIFECYCLE_REPORT", "cognitive_program_lifecycle_report"),
        )
        if explicit:
            report = explicit
        else:
            intelligence = self._build_program_blueprint_intelligence_visibility(
                report_state,
                performance,
            )
            report = cognitive_program_lifecycle_registry.build(
                intelligence,
            )
        registry = report.get("program_registry", [])
        registry = registry if isinstance(registry, list) else []
        summary = {
            "total_program_blueprints": int(report.get("total_program_blueprints") or len(registry)),
            "program_registry": registry,
            "readiness_distribution": report.get("readiness_distribution", {}),
            "execution_readiness_distribution": report.get("execution_readiness_distribution", {}),
            "candidate_readiness_distribution": report.get("candidate_readiness_distribution", {}),
            "maturity_distribution": report.get("maturity_distribution", {}),
            "semantic_family_coverage": report.get("semantic_family_coverage", {}),
            "operational_program_count": int(report.get("operational_program_count") or 0),
            "blocked_program_count": int(report.get("blocked_program_count") or 0),
            "partially_operational_program_count": int(report.get("partially_operational_program_count") or 0),
            "silent_lifecycle_failures": bool(report.get("silent_lifecycle_failures", False)),
        }
        return {
            "cognitive_program_lifecycle_summary": summary,
            "cognitive_program_lifecycle_diagnostics": report,
            **summary,
        }

    def _build_cognitive_knowledge_domains_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_KNOWLEDGE_DOMAINS_REPORT", "cognitive_knowledge_domains_report"),
            self._first_dict(performance, "COGNITIVE_KNOWLEDGE_DOMAINS_REPORT", "cognitive_knowledge_domains_report"),
        )
        if explicit:
            report = explicit
        elif not self._state_within_derived_report_budget(report_state):
            report = self._bootstrap_cognitive_knowledge_domains_from_architecture(
                report_state,
                performance,
            )
        else:
            concept_lifecycle = self._build_unified_concept_lifecycle_visibility(
                report_state,
                performance,
            )
            program_intelligence = self._build_program_blueprint_intelligence_visibility(
                report_state,
                performance,
            )
            program_lifecycle = self._build_cognitive_program_lifecycle_visibility(
                report_state,
                performance,
            )
            report = cognitive_knowledge_domain_registry.build(
                concept_lifecycle_report=concept_lifecycle,
                program_blueprint_intelligence_report=program_intelligence,
                cognitive_program_lifecycle_report=program_lifecycle,
            )
            if not report.get("domains"):
                report = self._bootstrap_cognitive_knowledge_domains_from_architecture(
                    report_state,
                    performance,
                )
        domains = report.get("domains", [])
        domains = domains if isinstance(domains, list) else []
        summary = {
            "domain_count": int(report.get("domain_count") or len(domains)),
            "domains": domains,
            "orphan_concepts": report.get("orphan_concepts", []),
            "invalid_family_assignments": report.get("invalid_family_assignments", []),
            "invalid_mental_model_assignments": report.get("invalid_mental_model_assignments", []),
            "invalid_program_blueprint_assignments": report.get("invalid_program_blueprint_assignments", []),
            "missing_domain_ownership": report.get("missing_domain_ownership", []),
            "validation_success": bool(report.get("validation_success", True)),
            "silent_domain_assignment_failures": bool(report.get("silent_domain_assignment_failures", False)),
        }
        return {
            "cognitive_knowledge_domains_summary": summary,
            "cognitive_knowledge_domains_diagnostics": report,
            **summary,
        }

    def _build_cognitive_domain_intelligence_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_INTELLIGENCE_REPORT", "cognitive_domain_intelligence_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_INTELLIGENCE_REPORT", "cognitive_domain_intelligence_report"),
        )
        if explicit:
            report = explicit
        else:
            domains = self._build_cognitive_knowledge_domains_visibility(
                report_state,
                performance,
            )
            report = cognitive_domain_intelligence_layer.analyze(domains)
        intelligence = report.get("domain_intelligence", [])
        intelligence = intelligence if isinstance(intelligence, list) else []
        validation = report.get("validation", {})
        validation = validation if isinstance(validation, dict) else {}
        summary = {
            "domain_intelligence_count": int(report.get("domain_intelligence_count") or len(intelligence)),
            "domain_intelligence": intelligence,
            "readiness_distribution": report.get("readiness_distribution", {}),
            "validation_success": bool(report.get("validation_success", validation.get("validation_success", True))),
            "validation_failures": validation.get("validation_failures", []),
            "invalid_concept_assignments": validation.get("invalid_concept_assignments", []),
            "invalid_mental_model_assignments": validation.get("invalid_mental_model_assignments", []),
            "invalid_program_assignments": validation.get("invalid_program_assignments", []),
            "invalid_domain_dependencies": validation.get("invalid_domain_dependencies", []),
            "semantic_family_inconsistencies": validation.get("semantic_family_inconsistencies", []),
            "domain_pollution": validation.get("domain_pollution", []),
            "silent_domain_intelligence_failures": bool(report.get("silent_domain_intelligence_failures", False)),
        }
        return {
            "cognitive_domain_intelligence_summary": summary,
            "cognitive_domain_intelligence_diagnostics": report,
            **summary,
        }

    def _build_cognitive_domain_lifecycle_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_LIFECYCLE_REPORT", "cognitive_domain_lifecycle_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_LIFECYCLE_REPORT", "cognitive_domain_lifecycle_report"),
        )
        if explicit:
            report = explicit
        elif not self._state_within_derived_report_budget(report_state):
            report = self._bootstrap_cognitive_domain_lifecycle_from_architecture(
                report_state,
                performance,
            )
        else:
            intelligence = self._build_cognitive_domain_intelligence_visibility(
                report_state,
                performance,
            )
            report = cognitive_domain_lifecycle_registry.build(intelligence)
        registry = report.get("domain_registry", [])
        registry = registry if isinstance(registry, list) else []
        summary = {
            "total_domains": int(report.get("total_domains") or len(registry)),
            "domain_registry": registry,
            "operational_domains": int(report.get("operational_domains") or 0),
            "partially_operational_domains": int(report.get("partially_operational_domains") or 0),
            "foundational_domains": int(report.get("foundational_domains") or 0),
            "advanced_domains": int(report.get("advanced_domains") or 0),
            "domain_readiness_distribution": report.get("domain_readiness_distribution", {}),
            "lifecycle_distribution": report.get("lifecycle_distribution", {}),
            "capability_distribution": report.get("capability_distribution", {}),
            "silent_domain_lifecycle_failures": bool(report.get("silent_domain_lifecycle_failures", False)),
        }
        return {
            "cognitive_domain_lifecycle_summary": summary,
            "cognitive_domain_lifecycle_diagnostics": report,
            **summary,
        }

    def _build_cognitive_domain_interaction_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_INTERACTION_REPORT", "cognitive_domain_interaction_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_INTERACTION_REPORT", "cognitive_domain_interaction_report"),
        )
        if explicit:
            report = explicit
        elif not self._state_within_derived_report_budget(report_state):
            report = self._bootstrap_cognitive_domain_interaction_from_architecture(
                report_state,
                performance,
            )
        else:
            explicit_lifecycle = self._merge_dicts(
                self._first_dict(report_state, "COGNITIVE_DOMAIN_LIFECYCLE_REPORT", "cognitive_domain_lifecycle_report"),
                self._first_dict(performance, "COGNITIVE_DOMAIN_LIFECYCLE_REPORT", "cognitive_domain_lifecycle_report"),
            )
            lifecycle = self._build_cognitive_domain_lifecycle_visibility(
                report_state,
                performance,
            )
            report = cognitive_domain_interaction_registry.build(lifecycle)
            if (
                not report.get("domain_interactions")
                or (
                    not explicit_lifecycle
                    and not report.get("cross_domain_operational_readiness")
                )
            ):
                report = self._bootstrap_cognitive_domain_interaction_from_architecture(
                    report_state,
                    performance,
                )
        domain_reports = report.get("domain_interaction_reports", [])
        domain_reports = domain_reports if isinstance(domain_reports, list) else []
        interactions = report.get("domain_interactions", [])
        interactions = interactions if isinstance(interactions, list) else []
        compositions = report.get("operational_capability_compositions", [])
        compositions = compositions if isinstance(compositions, list) else []
        compositions = self._augment_operational_capability_lifecycle(
            compositions,
            domain_reports,
        )
        validation = report.get("validation", {})
        validation = validation if isinstance(validation, dict) else {}
        collaboration_score = report.get("collaboration_score")
        if collaboration_score is None or (
            float(collaboration_score or 0.0) == 0.0
            and (compositions or interactions)
        ):
            readiness_rows = report.get("cross_domain_operational_readiness") or []
            readiness_rows = readiness_rows if isinstance(readiness_rows, list) else []
            readiness_values = [
                float(row.get("cross_domain_operational_readiness") or 0.0)
                for row in readiness_rows
                if isinstance(row, dict)
            ]
            if readiness_values:
                collaboration_score = round(
                    sum(readiness_values) / len(readiness_values),
                    4,
                )
            elif compositions:
                composition_scores = []
                for row in compositions:
                    if not isinstance(row, dict):
                        continue
                    if row.get("cross_domain_operational_readiness") is not None:
                        composition_scores.append(
                            float(row.get("cross_domain_operational_readiness") or 0.0)
                        )
                        continue
                    status = str(row.get("composition_status") or "").upper()
                    if status == "READY":
                        composition_scores.append(1.0)
                    elif status == "PARTIAL":
                        composition_scores.append(0.5)
                    elif status == "BLOCKED":
                        composition_scores.append(0.0)
                collaboration_score = round(
                    sum(composition_scores) / max(len(composition_scores), 1),
                    4,
                )
            elif interactions:
                collaboration_score = 0.25
        summary = {
            "domain_interaction_count": int(report.get("domain_interaction_count") or len(interactions)),
            "domain_interaction_reports": domain_reports,
            "domain_interactions": interactions,
            "dependency_graph": report.get("dependency_graph", {}),
            "operational_capability_compositions": compositions,
            "operational_capability_lifecycle": compositions,
            "operational_capability_lifecycle_count": len(compositions),
            "capability_promotion_candidates": [
                row for row in compositions
                if isinstance(row, dict)
                and row.get("promotion_state") in {
                    "PROMOTION_CANDIDATE",
                    "SANDBOX_OPERATIONAL",
                    "PROMOTED",
                }
            ],
            "capability_promotion_candidate_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("promotion_state") in {
                    "PROMOTION_CANDIDATE",
                    "SANDBOX_OPERATIONAL",
                    "PROMOTED",
                }
            ),
            "sandbox_operational_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("promotion_state") == "SANDBOX_OPERATIONAL"
            ),
            "promoted_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("promotion_state") == "PROMOTED"
            ),
            "reusable_operational_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("registry_eligibility") == "REUSABLE_OPERATIONAL_CAPABILITY"
            ),
            "capability_organism_count": len(compositions),
            "emerging_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("growth_stage") == "EMERGING"
            ),
            "developing_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("growth_stage") == "DEVELOPING"
            ),
            "evolving_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("growth_stage") in {"EVOLVING", "COMPOSABLE"}
            ),
            "capability_economy_decisions": [
                row.get("resource_decision")
                for row in compositions
                if isinstance(row, dict)
            ],
            "capability_invest_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("resource_decision") == "INVEST"
            ),
            "capability_watch_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("resource_decision") == "WATCH"
            ),
            "capability_hold_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("resource_decision") == "HOLD"
            ),
            "capability_archive_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("resource_decision") == "ARCHIVE"
            ),
            "governance_blocked_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("governance_status") == "GOVERNANCE_BLOCKED"
            ),
            "governance_review_capability_count": sum(
                1 for row in compositions
                if isinstance(row, dict)
                and row.get("governance_status") == "GOVERNANCE_REVIEW_REQUIRED"
            ),
            "cross_domain_operational_readiness": report.get(
                "cross_domain_operational_readiness",
                [],
            ),
            "collaboration_score": collaboration_score,
            "ready_composition_count": report.get("ready_composition_count"),
            "partial_composition_count": report.get("partial_composition_count"),
            "blocked_composition_count": report.get("blocked_composition_count"),
            "validation_success": bool(report.get("validation_success", validation.get("validation_success", True))),
            "validation_failures": validation,
            "silent_domain_interaction_failures": bool(report.get("silent_domain_interaction_failures", False)),
        }
        return {
            "cognitive_domain_interaction_summary": summary,
            "cognitive_domain_interaction_diagnostics": report,
            **summary,
        }

    def _build_cognitive_domain_governance_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_GOVERNANCE_REPORT", "cognitive_domain_governance_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_GOVERNANCE_REPORT", "cognitive_domain_governance_report"),
        )
        if explicit:
            report = explicit
        elif not self._state_within_derived_report_budget(report_state):
            lifecycle = self._bootstrap_cognitive_domain_lifecycle_from_architecture(
                report_state,
                performance,
            )
            interaction = self._bootstrap_cognitive_domain_interaction_from_architecture(
                report_state,
                performance,
            )
            total_domains = int(lifecycle.get("total_domains") or 0)
            operational_domains = int(lifecycle.get("operational_domains") or 0)
            report = {
                "ecosystem": {
                    "total_domains": total_domains,
                    "operational_domains": operational_domains,
                    "ecosystem_maturity": (
                        "OPERATIONAL"
                        if operational_domains == total_domains and total_domains
                        else "FOUNDATIONAL"
                    ),
                },
                "global_cognitive_coverage": {
                    "domains": total_domains,
                    "operational_domains": operational_domains,
                    "domain_operational_coverage": self._bounded_ratio(
                        operational_domains,
                        total_domains,
                    ),
                },
                "domain_distribution": lifecycle.get("domain_readiness_distribution", {}),
                "ecosystem_health_metrics": {
                    "operational_domain_ratio": self._bounded_ratio(
                        operational_domains,
                        total_domains,
                    ),
                    "collaboration_score": interaction.get("collaboration_score"),
                    "operational_readiness_score": interaction.get(
                        "collaboration_score"
                    ),
                    "architectural_coherence_score": round(
                        (
                            float(interaction.get("collaboration_score") or 0.0)
                            + float(
                                self._bounded_ratio(
                                    operational_domains,
                                    total_domains,
                                ) or 0.0
                            )
                        ) / 2.0,
                        4,
                    ),
                },
                "dependency_graph": {},
                "collaboration_graph": interaction.get("dependency_graph", {}),
                "operational_capability_graph": {
                    row.get("composition_name"): row.get("participating_domains")
                    for row in interaction.get("operational_capability_compositions", [])
                    if isinstance(row, dict)
                },
                "missing_ecosystem_capabilities": [
                    item.get("domain_name")
                    for item in lifecycle.get("domain_registry", [])
                    if isinstance(item, dict)
                    and item.get("lifecycle_status") != "OPERATIONAL"
                ],
                "cognitive_imbalances": [],
                "cognitive_bottlenecks": [
                    item.get("domain_name")
                    for item in lifecycle.get("domain_registry", [])
                    if isinstance(item, dict)
                    and item.get("lifecycle_status") == "FOUNDATIONAL"
                ],
                "ecosystem_maturity": "FOUNDATIONAL",
                "silent_ecosystem_failures": False,
                "domain_runtime_state": "BOOTSTRAPPED_FROM_CAPABILITY_COVERAGE",
            }
        else:
            lifecycle = self._build_cognitive_domain_lifecycle_visibility(
                report_state,
                performance,
            )
            interaction = self._build_cognitive_domain_interaction_visibility(
                report_state,
                performance,
            )
            report = cognitive_domain_governance_registry.build(
                cognitive_domain_lifecycle_report=lifecycle,
                cognitive_domain_interaction_report=interaction,
            )
        governance = report.get("domain_governance", [])
        governance = governance if isinstance(governance, list) else []
        validation = report.get("validation", {})
        validation = validation if isinstance(validation, dict) else {}
        summary = {
            "domain_governance_count": int(report.get("domain_governance_count") or len(governance)),
            "domain_governance": governance,
            "capability_ownership_map": report.get("capability_ownership_map", {}),
            "capability_conflicts": report.get("capability_conflicts", validation.get("capability_conflicts", [])),
            "migration_history": report.get("migration_history", validation.get("migration_events", [])),
            "boundary_violations": validation.get("boundary_violations", []),
            "missing_governance_requirements": validation.get("missing_governance_requirements", []),
            "validation_success": bool(report.get("validation_success", validation.get("validation_success", True))),
            "silent_domain_governance_failures": bool(report.get("silent_domain_governance_failures", False)),
        }
        return {
            "cognitive_domain_governance_summary": summary,
            "cognitive_domain_governance_diagnostics": report,
            **summary,
        }

    def _build_cognitive_domain_ecosystem_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_ECOSYSTEM_REPORT", "cognitive_domain_ecosystem_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_ECOSYSTEM_REPORT", "cognitive_domain_ecosystem_report"),
        )
        lifecycle = None
        interaction = None
        if explicit:
            report = explicit
        else:
            lifecycle = self._build_cognitive_domain_lifecycle_visibility(
                report_state,
                performance,
            )
            interaction = self._build_cognitive_domain_interaction_visibility(
                report_state,
                performance,
            )
            governance = self._build_cognitive_domain_governance_visibility(
                report_state,
                performance,
            )
            report = cognitive_domain_ecosystem_registry.build(
                cognitive_domain_lifecycle_report=lifecycle,
                cognitive_domain_interaction_report=interaction,
                cognitive_domain_governance_report=governance,
            )
        ecosystem = report.get("ecosystem", {})
        ecosystem = ecosystem if isinstance(ecosystem, dict) else {}
        coverage = report.get("global_cognitive_coverage", {})
        coverage = coverage if isinstance(coverage, dict) else {}
        health = report.get("ecosystem_health_metrics", {})
        health = health if isinstance(health, dict) else {}
        if lifecycle is None:
            lifecycle = self._build_cognitive_domain_lifecycle_visibility(
                report_state,
                performance,
            )
        if interaction is None:
            interaction = self._build_cognitive_domain_interaction_visibility(
                report_state,
                performance,
            )
        lifecycle_registry = lifecycle.get("domain_registry") or []
        lifecycle_registry = (
            lifecycle_registry if isinstance(lifecycle_registry, list) else []
        )
        interaction_summary = interaction.get(
            "cognitive_domain_interaction_summary",
            interaction,
        )
        interaction_summary = (
            interaction_summary if isinstance(interaction_summary, dict) else {}
        )
        if not self._state_within_derived_report_budget(report_state):
            bootstrap_lifecycle = self._bootstrap_cognitive_domain_lifecycle_from_architecture(
                report_state,
                performance,
            )
            bootstrap_interaction = self._bootstrap_cognitive_domain_interaction_from_architecture(
                report_state,
                performance,
            )
            bootstrap_total = int(bootstrap_lifecycle.get("total_domains") or 0)
            bootstrap_operational = int(
                bootstrap_lifecycle.get("operational_domains") or 0
            )
            if bootstrap_total:
                coverage = dict(coverage)
                coverage["domains"] = max(
                    int(coverage.get("domains") or 0),
                    bootstrap_total,
                )
                coverage["operational_domains"] = max(
                    int(coverage.get("operational_domains") or 0),
                    bootstrap_operational,
                )
                coverage["domain_operational_coverage"] = self._bounded_ratio(
                    coverage["operational_domains"],
                    coverage["domains"],
                )
                ecosystem = dict(ecosystem)
                ecosystem["total_domains"] = coverage["domains"]
                ecosystem["operational_domains"] = coverage["operational_domains"]
                health = dict(health)
                health["operational_domain_ratio"] = coverage[
                    "domain_operational_coverage"
                ]
                health.setdefault(
                    "collaboration_score",
                    bootstrap_interaction.get("collaboration_score"),
                )
                health.setdefault(
                    "operational_readiness_score",
                    bootstrap_interaction.get("collaboration_score"),
                )
                health.setdefault(
                    "architectural_coherence_score",
                    round(
                        (
                            float(health.get("collaboration_score") or 0.0)
                            + float(coverage["domain_operational_coverage"] or 0.0)
                        ) / 2.0,
                        4,
                    ),
                )
        lifecycle_total = int(lifecycle.get("total_domains") or 0)
        lifecycle_operational = int(lifecycle.get("operational_domains") or 0)
        semantic_total = sum(
            int(row.get("concept_count") or len(row.get("semantic_capability_evolution") or []))
            for row in lifecycle_registry
            if isinstance(row, dict)
        )
        blueprint_total = sum(
            int(row.get("program_blueprint_count") or len(row.get("program_blueprints") or []))
            for row in lifecycle_registry
            if isinstance(row, dict)
        )
        mental_model_total = sum(
            len(row.get("mental_models") or [])
            for row in lifecycle_registry
            if isinstance(row, dict)
        )
        if not mental_model_total:
            mental_model_total = sum(
                1
                for row in lifecycle_registry
                if isinstance(row, dict)
                and (
                    row.get("concept_count")
                    or row.get("program_blueprint_count")
                    or row.get("candidate_count")
                )
            )
        coverage = dict(coverage)
        ecosystem = dict(ecosystem)
        health = dict(health)
        if lifecycle_total:
            coverage["domains"] = max(int(coverage.get("domains") or 0), lifecycle_total)
            coverage["operational_domains"] = max(
                int(coverage.get("operational_domains") or 0),
                lifecycle_operational,
            )
            coverage["domain_operational_coverage"] = self._bounded_ratio(
                coverage["operational_domains"],
                coverage["domains"],
            )
            ecosystem["total_domains"] = coverage["domains"]
            ecosystem["operational_domains"] = coverage["operational_domains"]
        if semantic_total and not coverage.get("semantic_concepts"):
            coverage["semantic_concepts"] = semantic_total
        if mental_model_total and not coverage.get("mental_models"):
            coverage["mental_models"] = mental_model_total
        if blueprint_total and not coverage.get("program_blueprints"):
            coverage["program_blueprints"] = blueprint_total
        executable_semantic_summary = (
            self._build_executable_semantic_coverage_visibility(
                report_state,
                performance,
            ).get("executable_semantic_coverage_summary", {})
        )
        supported_operations = (
            executable_semantic_summary.get("supported_operations") or []
        )
        if supported_operations:
            coverage["execution_packages"] = max(
                int(coverage.get("execution_packages") or 0),
                len(set(supported_operations)),
            )
        materialized_operational = self._materialized_operational_capability_count(
            report_state,
            performance,
        )
        if materialized_operational:
            coverage["operational_capabilities"] = max(
                int(coverage.get("operational_capabilities") or 0),
                materialized_operational,
            )
            ecosystem["total_operational_capabilities"] = max(
                int(ecosystem.get("total_operational_capabilities") or 0),
                materialized_operational,
            )
        collaboration_score = interaction_summary.get("collaboration_score")
        if collaboration_score is not None:
            health["collaboration_score"] = float(collaboration_score or 0.0)
            health["operational_readiness_score"] = float(
                collaboration_score or 0.0
            )
        if coverage.get("domain_operational_coverage") is not None:
            health["operational_domain_ratio"] = coverage[
                "domain_operational_coverage"
            ]
        health["architectural_coherence_score"] = round(
            (
                float(health.get("collaboration_score") or 0.0)
                + float(coverage.get("domain_operational_coverage") or 0.0)
            ) / 2.0,
            4,
        )
        dependency_graph = report.get("dependency_graph", {})
        collaboration_graph = report.get("collaboration_graph", {})
        operational_capability_graph = report.get("operational_capability_graph", {})
        if not collaboration_graph:
            collaboration_graph = interaction_summary.get("dependency_graph", {})
        if not operational_capability_graph:
            operational_capability_graph = {
                row.get("composition_name"): row.get("participating_domains")
                for row in interaction_summary.get(
                    "operational_capability_compositions",
                    [],
                )
                if isinstance(row, dict)
            }
        missing_domains = ecosystem.get("missing_domains")
        if isinstance(missing_domains, list) and lifecycle_registry:
            known_domains = {
                str(row.get("domain_name"))
                for row in lifecycle_registry
                if isinstance(row, dict) and row.get("domain_name")
            }
            ecosystem["missing_domains"] = [
                domain for domain in missing_domains
                if self._canonical_cognitive_domain_name(domain) not in known_domains
                and str(domain) not in known_domains
            ]
        summary = {
            "ecosystem": ecosystem,
            "global_cognitive_coverage": coverage,
            "domain_distribution": report.get("domain_distribution", {}),
            "ecosystem_health_metrics": health,
            "dependency_graph": dependency_graph,
            "collaboration_graph": collaboration_graph,
            "operational_capability_graph": operational_capability_graph,
            "missing_ecosystem_capabilities": report.get("missing_ecosystem_capabilities", []),
            "cognitive_imbalances": report.get("cognitive_imbalances", []),
            "cognitive_bottlenecks": report.get("cognitive_bottlenecks", []),
            "ecosystem_maturity": report.get("ecosystem_maturity", ecosystem.get("ecosystem_maturity", "FOUNDATIONAL")),
            "silent_ecosystem_failures": bool(report.get("silent_ecosystem_failures", False)),
        }
        return {
            "cognitive_domain_ecosystem_summary": summary,
            "cognitive_domain_ecosystem_diagnostics": report,
            **summary,
        }

    def _build_cognitive_domain_constitution_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        explicit = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_CONSTITUTION_REPORT", "cognitive_domain_constitution_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_CONSTITUTION_REPORT", "cognitive_domain_constitution_report"),
        )
        if explicit:
            report = explicit
        else:
            lifecycle = self._build_cognitive_domain_lifecycle_visibility(
                report_state,
                performance,
            )
            interaction = self._build_cognitive_domain_interaction_visibility(
                report_state,
                performance,
            )
            governance = self._build_cognitive_domain_governance_visibility(
                report_state,
                performance,
            )
            ecosystem = self._build_cognitive_domain_ecosystem_visibility(
                report_state,
                performance,
            )
            report = cognitive_domain_constitution_registry.build(
                cognitive_domain_lifecycle_report=lifecycle,
                cognitive_domain_interaction_report=interaction,
                cognitive_domain_governance_report=governance,
                cognitive_domain_ecosystem_report=ecosystem,
            )
        constitution = report.get("constitution", {})
        constitution = constitution if isinstance(constitution, dict) else {}
        metrics = report.get("constitutional_health_metrics", {})
        metrics = metrics if isinstance(metrics, dict) else {}
        summary = {
            "constitution": constitution,
            "constitutional_status": report.get("constitutional_status", constitution.get("constitutional_status", "FOUNDATIONAL")),
            "constitutional_principles": report.get("constitutional_principles", constitution.get("constitutional_principles", [])),
            "architectural_invariants": report.get("architectural_invariants", constitution.get("architectural_invariants", [])),
            "constitutional_validations": report.get("constitutional_validations", constitution.get("constitutional_validations", {})),
            "constitutional_violations": report.get("constitutional_violations", constitution.get("constitutional_violations", [])),
            "constitutional_health_metrics": metrics,
            "domain_constitutional_health": report.get("domain_constitutional_health", constitution.get("domain_constitutional_health", [])),
            "governance_compliance": bool(report.get("governance_compliance", True)),
            "ownership_compliance": bool(report.get("ownership_compliance", True)),
            "lifecycle_compliance": bool(report.get("lifecycle_compliance", True)),
            "silent_constitutional_failures": bool(report.get("silent_constitutional_failures", False)),
        }
        return {
            "cognitive_domain_constitution_summary": summary,
            "cognitive_domain_constitution_diagnostics": report,
            **summary,
        }

    def _build_executable_semantic_coverage_visibility(
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
        concepts = self._semantic_concepts_for_coverage(report_state, performance, synthesis, compiler)
        lifecycle_concepts = self._cognitive_lifecycle_concepts(report_state, performance)
        concepts = list(dict.fromkeys([*concepts, *lifecycle_concepts]))
        support_map = self._executable_semantic_support_map()
        rows = []
        for concept in concepts:
            operation = support_map.get(concept)
            cluster = self._semantic_cluster(concept)
            rows.append({
                "concept": concept,
                "cluster": cluster,
                "executable": operation is not None,
                "operation": operation,
            })
        executable = [row for row in rows if row["executable"]]
        unsupported = [row for row in rows if not row["executable"]]
        cluster_counts: dict[str, int] = {}
        for row in unsupported:
            cluster_counts[row["cluster"]] = cluster_counts.get(row["cluster"], 0) + 1
        highest_missing = None
        if cluster_counts:
            highest_missing = sorted(
                cluster_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[0][0]
        coverage = round(len(executable) / max(len(rows), 1), 4) if rows else None
        observed_generated = self._first_number(
            len(rows) if rows else None,
            report_state.get("generated_concepts"),
            report_state.get("semantic_concept_count"),
            performance.get("generated_concepts"),
            performance.get("semantic_concept_count"),
        )
        coverage_status = (
            self._coverage_status(coverage)
            if coverage is not None
            else "NOT_MEASURABLE"
        )
        summary = {
            "generated_concepts": int(observed_generated or 0),
            "measured_concepts": len(rows),
            "lifecycle_concepts": len(lifecycle_concepts),
            "executable_concepts": len(executable),
            "unsupported_concepts": len(unsupported),
            "executable_semantic_coverage": coverage,
            "coverage_status": coverage_status,
            "coverage_state": "MEASURED" if rows else "NOT_MEASURABLE",
            "measurement_blocker": None if rows else "NO_UNIFIED_CONCEPT_INPUT",
            "supported_operations": sorted({
                row["operation"]
                for row in executable
                if row.get("operation")
            }),
            "supported_concept_rows": executable,
            "unsupported_concept_rows": unsupported,
            "unsupported_operations": [row["concept"] for row in unsupported],
            "highest_missing_semantic_cluster": highest_missing,
            "missing_cluster_counts": cluster_counts,
        }
        return {
            "executable_semantic_coverage_summary": summary,
            "executable_semantic_coverage_diagnostics": {
                "semantic_concepts": concepts,
                "lifecycle_concepts": lifecycle_concepts,
                "coverage_rows": rows,
                "support_map_size": len(support_map),
            },
            **summary,
        }

    def _semantic_compiler_report(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        synthesis = self._merge_dicts(
            self._first_dict(
                report_state,
                "TRANSFORMATION_SYNTHESIS_REPORT",
                "transformation_synthesis_report",
            ),
            self._first_dict(
                performance,
                "TRANSFORMATION_SYNTHESIS_REPORT",
                "transformation_synthesis_report",
            ),
        )
        return self._merge_dicts(
            self._first_dict(
                report_state,
                "SEMANTIC_COMPILATION_REPORT",
                "semantic_compilation_report",
            ),
            self._first_dict(
                performance,
                "SEMANTIC_COMPILATION_REPORT",
                "semantic_compilation_report",
            ),
            self._first_dict(
                report_state,
                "semantic_to_transformation_compilation_report",
            ),
            self._first_dict(
                performance,
                "semantic_to_transformation_compilation_report",
            ),
            self._first_dict(
                synthesis,
                "semantic_to_transformation_compilation_report",
            ),
        )

    def _compiler_failure_diagnostics_summary(
        self,
        compiler_report: dict[str, Any],
        *,
        generated_programs: int,
        compiler_runtime_activated_programs: int,
        compiled_programs: int,
    ) -> dict[str, Any]:
        diagnostics = compiler_report.get("compiler_failure_diagnostics")
        diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
        reason_counts = diagnostics.get("failure_reason_counts") or {}
        reason_counts = reason_counts if isinstance(reason_counts, dict) else {}
        domain_distribution = diagnostics.get("failure_domain_distribution") or {}
        domain_distribution = (
            domain_distribution if isinstance(domain_distribution, dict) else {}
        )
        rows = diagnostics.get("failure_rows") or []
        rows = rows if isinstance(rows, list) else []
        reported_failures = sum(
            int(value or 0)
            for value in reason_counts.values()
            if isinstance(value, (int, float))
        )
        total_failures = max(
            compiler_runtime_activated_programs - compiled_programs,
            reported_failures,
            0,
        )
        if total_failures and not reason_counts:
            failure_reason = (
                compiler_report.get("failure_reason")
                or "compiler_failure_reason_not_reported"
            )
            reason_counts = {str(failure_reason): total_failures}
        normalized_rows = self._normalize_compiler_failure_rows(
            rows,
            reason_counts,
            domain_distribution,
        )
        compiler_success_rate = self._bounded_ratio(
            compiled_programs,
            compiler_runtime_activated_programs,
        )
        return {
            "compiler_failure_count": total_failures,
            "compiler_failure_reason_distribution": dict(
                sorted((str(key), int(value or 0)) for key, value in reason_counts.items())
            ),
            "compiler_failure_domain_distribution": dict(
                sorted((str(key), int(value or 0)) for key, value in domain_distribution.items())
            ),
            "compiler_failure_rows": normalized_rows[:10],
            "compiler_failure_detail_capture_state": (
                self._compiler_failure_detail_capture_state(
                    rows,
                    normalized_rows,
                )
            ),
            "compiler_diagnostic_state": (
                "COMPILER_BOTTLENECK_DIAGNOSED"
                if total_failures and reason_counts
                else "COMPILER_BOTTLENECK_UNEXPLAINED"
                if total_failures
                else "NO_COMPILER_BOTTLENECK"
            ),
            "compiler_failure_pressure": self._bounded_ratio(
                total_failures,
                max(generated_programs, compiler_runtime_activated_programs),
            ),
            "compiler_success_rate": compiler_success_rate,
        }

    def _compiler_failure_detail_capture_state(
        self,
        source_rows: list[Any],
        normalized_rows: list[dict[str, Any]],
    ) -> str:
        if not normalized_rows:
            return "NO_FAILURE_DETAILS"
        if not source_rows:
            return "SYNTHETIC_FAILURE_ROWS_FROM_AGGREGATES"
        if any(self._compiler_failure_row_has_semantic_trace(row) for row in normalized_rows):
            return "DETAILED_FAILURE_ROWS_CAPTURED"
        return "STRUCTURED_PLACEHOLDER_ROWS_CAPTURED"

    def _compiler_failure_row_has_semantic_trace(self, row: dict[str, Any]) -> bool:
        if not isinstance(row, dict):
            return False
        unresolved = {
            "",
            "unknown",
            "unresolved",
            "unresolved_compiler_attempt",
            "semantic_program_unresolved_compiler_attempt",
            "not available",
            "not_available",
        }
        program = str(row.get("program") or "").strip().lower()
        semantic_intent = str(row.get("semantic_intent") or "").strip().lower()
        stage = str(row.get("failure_stage") or "").strip().lower()
        reason = str(row.get("reason") or "").strip().lower()
        rule = str(row.get("compiler_rule") or "").strip().lower()
        trace_id = str(row.get("trace_id") or "").strip().lower()
        return (
            bool(trace_id)
            and program not in unresolved
            and semantic_intent not in unresolved
            and stage not in unresolved
            and reason not in unresolved
            and rule not in unresolved
            and rule != "rule_not_captured"
        )

    def _normalize_compiler_failure_rows(
        self,
        rows: list[Any],
        reason_counts: dict[Any, Any],
        domain_distribution: dict[Any, Any],
    ) -> list[dict[str, Any]]:
        top_domain = None
        if domain_distribution:
            top_domain = sorted(
                domain_distribution.items(),
                key=lambda item: (-int(item[1] or 0), str(item[0])),
            )[0][0]
        normalized = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            reason = (
                row.get("reason")
                or next(iter(reason_counts.keys()), None)
                or "compiler_failure_reason_not_reported"
            )
            domain = (
                row.get("domain")
                or top_domain
                or "Unknown"
            )
            operation = (
                row.get("operation")
                or row.get("expected_operation")
                or "unresolved_compiler_attempt"
            )
            expected_operation = row.get("expected_operation") or operation
            resolved_operation = row.get("resolved_operation") or operation
            program = row.get("program") or f"semantic_program_{expected_operation}"
            semantic_intent = row.get("semantic_intent") or expected_operation
            normalized.append({
                **row,
                "trace_id": row.get("trace_id")
                or (
                    "compiler_trace:"
                    f"{program}:{semantic_intent}:{expected_operation}"
                ),
                "program": program,
                "semantic_intent": semantic_intent,
                "operation": operation,
                "expected_operation": expected_operation,
                "resolved_operation": resolved_operation,
                "domain": domain,
                "failure_stage": row.get("failure_stage")
                or "compiler_failure_diagnostics",
                "reason": reason,
                "detail": row.get("detail")
                or "compiler_failure_detail_not_captured",
                "compiler_rule": row.get("compiler_rule")
                or "RULE_NOT_CAPTURED",
                "diagnostic_row_source": row.get(
                    "diagnostic_row_source",
                    "compiler_failure_diagnostics",
                ),
            })
        if normalized or not reason_counts:
            return normalized
        for reason, count in sorted(reason_counts.items()):
            normalized.append({
                "trace_id": (
                    "compiler_trace:"
                    "unresolved_compiler_attempt:unknown:"
                    "unresolved_compiler_attempt"
                ),
                "program": "unresolved_compiler_attempt",
                "semantic_intent": "unknown",
                "operation": "unresolved_compiler_attempt",
                "expected_operation": "unresolved_compiler_attempt",
                "resolved_operation": "unresolved_compiler_attempt",
                "domain": top_domain or "Unknown",
                "failure_stage": "compiler_failure_aggregation",
                "reason": str(reason),
                "detail": "compiler_failure_detail_not_captured",
                "compiler_rule": "RULE_NOT_CAPTURED",
                "failure_count": int(count or 0),
                "diagnostic_row_source": "aggregate_failure_distribution",
            })
        return normalized

    def _build_cognitive_capability_coverage_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        compiler_report = self._semantic_compiler_report(report_state, performance)
        semantic = self._build_executable_semantic_coverage_visibility(
            report_state,
            performance,
        ).get("executable_semantic_coverage_summary", {})
        program_generation = self._build_program_generation_visibility(
            report_state,
            performance,
        ).get("program_generation_summary", {})
        program_lifecycle = self._build_cognitive_program_lifecycle_visibility(
            report_state,
            performance,
        ).get("cognitive_program_lifecycle_summary", {})
        proposal = self._cached_visibility(
            "candidate_proposal_report",
            lambda: self._build_candidate_proposal_visibility(report_state, performance),
        ).get("candidate_proposal_summary", {})
        arena = self._cached_visibility(
            "cognitive_candidate_arena_report",
            lambda: self._build_candidate_arena_visibility(report_state, performance),
        ).get("candidate_arena_summary", {})
        semantic_compilation = self._cached_visibility(
            "semantic_compilation_report",
            lambda: self._build_semantic_compilation_visibility(report_state, performance),
        ).get("semantic_compilation_summary", {})
        executable = self._merge_dicts(
            self._first_dict(report_state, "EXECUTABLE_INTELLIGENCE_REPORT", "executable_intelligence_report"),
            self._first_dict(performance, "EXECUTABLE_INTELLIGENCE_REPORT", "executable_intelligence_report"),
        )

        generated_concepts = int(self._first_number(
            semantic.get("generated_concepts"),
            semantic.get("measured_concepts"),
            report_state.get("generated_concepts"),
            performance.get("generated_concepts"),
        ) or 0)
        measured_concepts = int(self._first_number(
            semantic.get("measured_concepts"),
            generated_concepts,
        ) or 0)
        executable_concepts = int(self._first_number(
            semantic.get("executable_concepts"),
            executable.get("executable_concepts"),
        ) or 0)
        generated_programs = int(self._first_number(
            program_generation.get("generated_programs"),
            report_state.get("generated_programs"),
            performance.get("generated_programs"),
        ) or 0)
        generated_blueprints = int(self._first_number(
            program_generation.get("generated_blueprints"),
            program_lifecycle.get("total_program_blueprints"),
        ) or 0)
        candidate_count = int(self._first_number(
            proposal.get("proposal_count"),
            arena.get("candidate_count"),
        ) or 0)
        arena_candidates = int(self._first_number(
            arena.get("candidate_count"),
            0,
        ) or 0)
        arena_sources = arena.get("competitor_sources") or []
        arena_sources = arena_sources if isinstance(arena_sources, list) else [arena_sources]
        compiled_programs = max(
            int(self._first_number(
            executable.get("compiled_programs"),
            executable.get("compiled_program_count"),
            ) or 0),
            int(self._first_number(
                semantic_compilation.get("compiled_candidate_count"),
                semantic_compilation.get("candidate_count"),
            ) or 0),
        )
        compiler_runtime_activated_programs = max(
            compiled_programs,
            int(self._first_number(
                semantic_compilation.get("execution_intent_count"),
                semantic_compilation.get("runtime_attempt_count"),
            ) or 0),
        )
        validated_programs = int(self._first_number(
            executable.get("validated_programs"),
            executable.get("validated_program_count"),
            executable.get("validated_programs_count"),
        ) or 0)
        operational_programs = int(self._first_number(
            program_lifecycle.get("operational_program_count"),
            validated_programs,
        ) or 0)
        materialized_operational_capabilities = (
            self._materialized_operational_capability_count(report_state, performance)
        )
        materialization = self._operational_capability_materialization_summary(
            report_state,
            performance,
        )

        semantic_coverage = self._bounded_ratio(measured_concepts, generated_concepts)
        execution_package_coverage = semantic.get("executable_semantic_coverage")
        if execution_package_coverage is None:
            execution_package_coverage = self._bounded_ratio(
                executable_concepts,
                generated_concepts,
            )
        compiler_coverage = self._bounded_ratio(generated_programs, generated_concepts)
        program_coverage = self._bounded_ratio(generated_blueprints, generated_concepts)
        candidate_coverage = self._bounded_ratio(candidate_count, generated_programs)
        arena_coverage = self._bounded_ratio(arena_candidates, candidate_count)
        arena_source_coverage = self._bounded_ratio(len([
            source for source in arena_sources if source
        ]), max(int(proposal.get("eligible_source_count") or 0), 1))
        validated_executable_coverage = self._bounded_ratio(
            validated_programs,
            generated_concepts,
        )
        operational_coverage = self._bounded_ratio(
            materialized_operational_capabilities,
            generated_concepts,
        )
        operational_materialization_rate = self._bounded_ratio(
            materialized_operational_capabilities,
            validated_programs,
        )
        compiler_runtime_coverage = self._bounded_ratio(
            compiler_runtime_activated_programs,
            max(generated_blueprints, generated_programs),
        )
        compiler_failure_diagnostics = self._compiler_failure_diagnostics_summary(
            compiler_report,
            generated_programs=generated_programs,
            compiler_runtime_activated_programs=compiler_runtime_activated_programs,
            compiled_programs=compiled_programs,
        )
        compiler_infrastructure = compiler_report.get(
            "compiler_infrastructure_report",
        )
        compiler_infrastructure = (
            compiler_infrastructure
            if isinstance(compiler_infrastructure, dict)
            else compiler_infrastructure_analyzer.build_report(
                compiler_report=compiler_report,
                candidate_programs=compiler_report.get("compiler_candidates", []),
            )
        )
        known_operational_capabilities = int(
            self._first_number(
                materialization.get("known_operational_capability_count"),
                materialized_operational_capabilities,
            )
            or 0
        )
        known_operational_domain_count = int(
            self._first_number(
                materialization.get("known_operational_domain_count"),
                0,
            )
            or 0
        )
        operational_yield_from_concepts = self._bounded_ratio(
            materialized_operational_capabilities,
            generated_concepts,
        )
        operational_yield_from_programs = self._bounded_ratio(
            materialized_operational_capabilities,
            generated_programs,
        )
        operational_yield_from_candidates = self._bounded_ratio(
            materialized_operational_capabilities,
            candidate_count,
        )
        operational_yield_from_arena = self._bounded_ratio(
            materialized_operational_capabilities,
            arena_candidates,
        )
        population_diversification = self._bounded_ratio(
            known_operational_domain_count,
            5,
        )
        operational_experience_count = int(
            self._first_number(
                materialization.get("operational_experience_count"),
                0,
            )
            or 0
        )
        operational_experience_task_count = int(
            self._first_number(
                materialization.get("operational_experience_task_count"),
                operational_experience_count,
            )
            or 0
        )
        reuse_evidence_count = int(
            self._first_number(
                materialization.get("reuse_evidence_count"),
                0,
            )
            or 0
        )
        independent_reuse_success_count = int(
            self._first_number(
                materialization.get("independent_reuse_success_count"),
                0,
            )
            or 0
        )
        survival = materialization.get("capability_survival_report")
        survival = survival if isinstance(survival, dict) else {}
        capability_survival_rate = self._first_number(
            materialization.get("capability_survival_rate"),
            survival.get("capability_survival_rate"),
        )
        materialization_survival_rate = self._first_number(
            materialization.get("materialization_survival_rate"),
            survival.get("materialization_survival_rate"),
        )
        validation_bottleneck_inflation = self._first_number(
            materialization.get("validation_bottleneck_inflation"),
            survival.get("validation_bottleneck_inflation"),
        )
        validation_bottleneck_state = (
            materialization.get("validation_bottleneck_state")
            or survival.get("validation_bottleneck_state")
            or "NOT_MEASURABLE"
        )
        incubating_operational_capability_count = int(
            self._first_number(
                materialization.get("incubating_operational_capability_count"),
                survival.get("incubating_operational_capability_count"),
                0,
            )
            or 0
        )
        operational_citizen_count = int(
            self._first_number(
                materialization.get("operational_citizen_count"),
                survival.get("operational_citizen_count"),
                0,
            )
            or 0
        )
        validation_gap_candidate_count = int(
            self._first_number(
                survival.get("validation_gap_candidate_count"),
                0,
            )
            or 0
        )
        unresolved_validation_gap_candidate_count = int(
            self._first_number(
                materialization.get("unresolved_validation_gap_candidate_count"),
                survival.get("unresolved_validation_gap_candidate_count"),
                validation_gap_candidate_count,
            )
            or 0
        )
        generated_survival_candidate_count = int(
            self._first_number(
                materialization.get("generated_survival_candidate_count"),
                survival.get("generated_operational_candidate_count"),
                0,
            )
            or 0
        )
        arena_simulated_survival_candidate_count = int(
            self._first_number(
                materialization.get("arena_simulated_survival_candidate_count"),
                survival.get("arena_simulated_candidate_count"),
                survival.get("arena_entered_candidate_count"),
                0,
            )
            or 0
        )
        arena_quality_survival_candidate_count = int(
            self._first_number(
                materialization.get("arena_quality_survival_candidate_count"),
                survival.get("arena_quality_candidate_count"),
                0,
            )
            or 0
        )
        survival_state_distribution = (
            materialization.get("capability_survival_state_distribution")
            or survival.get("capability_survival_state_distribution")
            or {}
        )
        survival_state_distribution = (
            survival_state_distribution
            if isinstance(survival_state_distribution, dict)
            else {}
        )
        top_incubating_capabilities = (
            materialization.get("top_incubating_capabilities")
            or survival.get("top_incubating_capabilities")
            or []
        )
        top_incubating_capabilities = (
            top_incubating_capabilities
            if isinstance(top_incubating_capabilities, list)
            else []
        )
        top_operational_citizens = (
            materialization.get("top_operational_citizens")
            or survival.get("top_operational_citizens")
            or []
        )
        top_operational_citizens = (
            top_operational_citizens
            if isinstance(top_operational_citizens, list)
            else []
        )
        capability_stability_regression_count = int(
            self._first_number(
                materialization.get("capability_stability_regression_count"),
                survival.get("capability_stability_regression_count"),
                0,
            )
            or 0
        )
        top_stability_regressions = (
            materialization.get("top_stability_regressions")
            or survival.get("top_stability_regressions")
            or []
        )
        top_stability_regressions = (
            top_stability_regressions
            if isinstance(top_stability_regressions, list)
            else []
        )
        top_crystallization_candidates = (
            materialization.get("top_crystallization_candidates")
            or survival.get("top_crystallization_candidates")
            or []
        )
        top_crystallization_candidates = (
            top_crystallization_candidates
            if isinstance(top_crystallization_candidates, list)
            else []
        )
        top_cognitive_citizens = (
            materialization.get("top_cognitive_citizens")
            or survival.get("top_cognitive_citizens")
            or []
        )
        top_cognitive_citizens = (
            top_cognitive_citizens
            if isinstance(top_cognitive_citizens, list)
            else []
        )
        cognitive_citizen_count = int(
            self._first_number(
                materialization.get("cognitive_citizen_count"),
                survival.get("cognitive_citizen_count"),
                0,
            )
            or 0
        )
        cognitive_citizenship_definition = (
            materialization.get("cognitive_citizenship_definition")
            or survival.get("cognitive_citizenship_definition")
            or "not_measured"
        )
        crystallization_candidate_count = int(
            self._first_number(
                materialization.get("crystallization_candidate_count"),
                survival.get("crystallization_candidate_count"),
                0,
            )
            or 0
        )
        quality_to_citizen_crystallization_rate = self._first_number(
            materialization.get("quality_to_citizen_crystallization_rate"),
            survival.get("quality_to_citizen_crystallization_rate"),
        )
        candidate_to_citizen_crystallization_rate = self._first_number(
            materialization.get("candidate_to_citizen_crystallization_rate"),
            survival.get("candidate_to_citizen_crystallization_rate"),
        )
        generated_to_citizen_pressure_ratio = self._first_number(
            materialization.get("generated_to_citizen_pressure_ratio"),
            survival.get("generated_to_citizen_pressure_ratio"),
        )
        capability_crystallization_state = (
            materialization.get("capability_crystallization_state")
            or survival.get("capability_crystallization_state")
            or "NOT_MEASURABLE"
        )
        capability_graduation_candidate_count = int(
            self._first_number(
                materialization.get("capability_graduation_candidate_count"),
                survival.get("capability_graduation_candidate_count"),
                0,
            )
            or 0
        )
        capability_graduation_pressure = self._first_number(
            materialization.get("capability_graduation_pressure"),
            survival.get("capability_graduation_pressure"),
        )
        capability_graduation_pressure_state = (
            materialization.get("capability_graduation_pressure_state")
            or survival.get("capability_graduation_pressure_state")
            or "NONE"
        )
        capability_graduation_queue = (
            materialization.get("capability_graduation_queue")
            or survival.get("capability_graduation_queue")
            or []
        )
        capability_graduation_queue = (
            capability_graduation_queue
            if isinstance(capability_graduation_queue, list)
            else []
        )
        top_graduation_candidates = (
            materialization.get("top_graduation_candidates")
            or survival.get("top_graduation_candidates")
            or capability_graduation_queue
            or []
        )
        top_graduation_candidates = (
            top_graduation_candidates
            if isinstance(top_graduation_candidates, list)
            else []
        )
        world_governance_graduation_action = (
            materialization.get("world_governance_graduation_action")
            or survival.get("world_governance_graduation_action")
            or "NO_GRADUATION_QUEUE"
        )
        graduation_infrastructure_report = (
            materialization.get("capability_graduation_infrastructure_report")
            or survival.get("capability_graduation_infrastructure_report")
            or {}
        )
        graduation_infrastructure_report = (
            graduation_infrastructure_report
            if isinstance(graduation_infrastructure_report, dict)
            else {}
        )
        capability_graduation_health = self._first_number(
            materialization.get("capability_graduation_health"),
            survival.get("capability_graduation_health"),
            graduation_infrastructure_report.get("capability_graduation_health"),
        )
        graduation_pipeline_health = (
            materialization.get("graduation_pipeline_health")
            or survival.get("graduation_pipeline_health")
            or graduation_infrastructure_report.get("graduation_pipeline_health")
            or "NOT_MEASURABLE"
        )
        graduation_success_rate = self._first_number(
            materialization.get("graduation_success_rate"),
            survival.get("graduation_success_rate"),
            graduation_infrastructure_report.get("graduation_success_rate"),
        )
        graduation_failure_rate = self._first_number(
            materialization.get("graduation_failure_rate"),
            survival.get("graduation_failure_rate"),
            graduation_infrastructure_report.get("graduation_failure_rate"),
        )
        graduation_queue_health = (
            materialization.get("graduation_queue_health")
            or survival.get("graduation_queue_health")
            or graduation_infrastructure_report.get("graduation_queue_health")
            or "NOT_MEASURABLE"
        )
        graduation_evidence_coverage = self._first_number(
            materialization.get("graduation_evidence_coverage"),
            survival.get("graduation_evidence_coverage"),
            graduation_infrastructure_report.get("graduation_evidence_coverage"),
        )
        graduation_infrastructure_readiness = (
            materialization.get("graduation_infrastructure_readiness")
            or survival.get("graduation_infrastructure_readiness")
            or graduation_infrastructure_report.get(
                "graduation_infrastructure_readiness"
            )
            or "NOT_MEASURABLE"
        )
        average_capability_graduation_time = self._first_number(
            materialization.get("average_capability_graduation_time"),
            survival.get("average_capability_graduation_time"),
            graduation_infrastructure_report.get(
                "average_capability_graduation_time"
            ),
        )
        graduation_backlog_size = int(
            self._first_number(
                materialization.get("graduation_backlog_size"),
                survival.get("graduation_backlog_size"),
                graduation_infrastructure_report.get("graduation_backlog_size"),
                0,
            )
            or 0
        )
        capability_graduation_queue_health = (
            materialization.get("capability_graduation_queue_health")
            or survival.get("capability_graduation_queue_health")
            or graduation_infrastructure_report.get(
                "capability_graduation_queue_health"
            )
            or graduation_queue_health
        )
        capability_graduation_risk = (
            materialization.get("capability_graduation_risk")
            or survival.get("capability_graduation_risk")
            or graduation_infrastructure_report.get(
                "capability_graduation_risk"
            )
            or "NOT_MEASURABLE"
        )
        capability_graduation_complexity = (
            materialization.get("capability_graduation_complexity")
            or survival.get("capability_graduation_complexity")
            or graduation_infrastructure_report.get(
                "capability_graduation_complexity"
            )
            or "NOT_MEASURABLE"
        )
        capability_graduation_confidence = self._first_number(
            materialization.get("capability_graduation_confidence"),
            survival.get("capability_graduation_confidence"),
            graduation_infrastructure_report.get(
                "capability_graduation_confidence"
            ),
        )
        graduation_pipeline_stages = (
            materialization.get("graduation_pipeline_stages")
            or survival.get("graduation_pipeline_stages")
            or graduation_infrastructure_report.get("graduation_pipeline_stages")
            or {}
        )
        graduation_pipeline_stages = (
            graduation_pipeline_stages
            if isinstance(graduation_pipeline_stages, dict)
            else {}
        )
        graduation_transition_rows = (
            materialization.get("graduation_transition_rows")
            or survival.get("graduation_transition_rows")
            or graduation_infrastructure_report.get("graduation_transition_rows")
            or []
        )
        graduation_transition_rows = (
            graduation_transition_rows
            if isinstance(graduation_transition_rows, list)
            else []
        )
        capability_graduation_diagnostics = (
            materialization.get("capability_graduation_diagnostics")
            or survival.get("capability_graduation_diagnostics")
            or graduation_infrastructure_report.get(
                "capability_graduation_diagnostics"
            )
            or []
        )
        capability_graduation_diagnostics = (
            capability_graduation_diagnostics
            if isinstance(capability_graduation_diagnostics, list)
            else []
        )
        top_graduation_priority = (
            materialization.get("top_graduation_priority")
            or survival.get("top_graduation_priority")
            or graduation_infrastructure_report.get("top_graduation_priority")
            or {}
        )
        top_graduation_priority = (
            top_graduation_priority
            if isinstance(top_graduation_priority, dict)
            else {}
        )
        graduation_sprint_recommendations = (
            materialization.get("graduation_sprint_recommendations")
            or survival.get("graduation_sprint_recommendations")
            or graduation_infrastructure_report.get(
                "graduation_sprint_recommendations"
            )
            or []
        )
        graduation_sprint_recommendations = (
            graduation_sprint_recommendations
            if isinstance(graduation_sprint_recommendations, list)
            else []
        )
        validator_failure_distribution = (
            materialization.get("validator_failure_distribution")
            or survival.get("validator_failure_distribution")
            or graduation_infrastructure_report.get(
                "validator_failure_distribution"
            )
            or {}
        )
        validator_failure_distribution = (
            validator_failure_distribution
            if isinstance(validator_failure_distribution, dict)
            else {}
        )
        world_governance_promotion_policy = (
            materialization.get("world_governance_promotion_policy")
            or survival.get("world_governance_promotion_policy")
            or {}
        )
        world_governance_promotion_policy = (
            world_governance_promotion_policy
            if isinstance(world_governance_promotion_policy, dict)
            else {}
        )
        world_governance_promotion_policy_state = (
            materialization.get("world_governance_promotion_policy_state")
            or survival.get("world_governance_promotion_policy_state")
            or world_governance_promotion_policy.get("policy_state")
            or "NOT_MEASURABLE"
        )
        sandbox_citizenship_thresholds = (
            materialization.get("sandbox_citizenship_thresholds")
            or survival.get("sandbox_citizenship_thresholds")
            or world_governance_promotion_policy.get(
                "sandbox_citizenship_thresholds",
                {},
            )
        )
        sandbox_citizenship_thresholds = (
            sandbox_citizenship_thresholds
            if isinstance(sandbox_citizenship_thresholds, dict)
            else {}
        )
        trusted_capability_policy = (
            materialization.get("trusted_capability_policy")
            or survival.get("trusted_capability_policy")
            or world_governance_promotion_policy.get(
                "trusted_capability_policy",
                {},
            )
        )
        trusted_capability_policy = (
            trusted_capability_policy
            if isinstance(trusted_capability_policy, dict)
            else {}
        )
        decision_authority_policy = (
            materialization.get("decision_authority_policy")
            or survival.get("decision_authority_policy")
            or world_governance_promotion_policy.get(
                "decision_authority_policy",
                {},
            )
        )
        decision_authority_policy = (
            decision_authority_policy
            if isinstance(decision_authority_policy, dict)
            else {}
        )
        operational_citizen_domain_distribution = (
            materialization.get("operational_citizen_domain_distribution")
            or survival.get("operational_citizen_domain_distribution")
            or {}
        )
        operational_citizen_domain_distribution = (
            operational_citizen_domain_distribution
            if isinstance(operational_citizen_domain_distribution, dict)
            else {}
        )
        domain_monopoly_share = self._first_number(
            materialization.get("domain_monopoly_share"),
            survival.get("domain_monopoly_share"),
        )
        dominant_operational_domain = (
            materialization.get("dominant_operational_domain")
            or survival.get("dominant_operational_domain")
        )
        domain_operational_imbalance_state = (
            materialization.get("domain_operational_imbalance_state")
            or survival.get("domain_operational_imbalance_state")
            or "NOT_MEASURABLE"
        )
        capability_survival_rows = survival.get("capability_survival_rows") or []
        capability_survival_rows = (
            capability_survival_rows
            if isinstance(capability_survival_rows, list)
            else []
        )
        candidate_retention_rate = self._bounded_ratio(
            arena_simulated_survival_candidate_count,
            generated_survival_candidate_count,
        )
        incubation_conversion_rate = self._bounded_ratio(
            incubating_operational_capability_count,
            generated_survival_candidate_count,
        )
        surviving_capability_count = int(
            self._first_number(
                survival_state_distribution.get("SURVIVING_CAPABILITY"),
                0,
            )
            or 0
        )
        surviving_capability_conversion_rate = self._bounded_ratio(
            surviving_capability_count,
            generated_survival_candidate_count,
        )
        operational_citizen_conversion_rate = self._bounded_ratio(
            operational_citizen_count,
            generated_survival_candidate_count,
        )
        historical_operational_citizen_count = known_operational_capabilities
        knowledge_production_efficiency = self._bounded_ratio(
            candidate_count,
            generated_concepts,
        )
        knowledge_operationalization_efficiency = operational_yield_from_concepts
        operational_knowledge_waste = (
            round(1.0 - operational_yield_from_concepts, 4)
            if isinstance(operational_yield_from_concepts, (int, float))
            else None
        )
        operational_yield_stability = self._bounded_ratio(
            independent_reuse_success_count,
            operational_experience_count,
        )
        operational_yield_health_state = self._coverage_status(
            knowledge_operationalization_efficiency
        )
        high_value_knowledge_items = int(
            self._first_number(proposal.get("high_value_knowledge_items"), 0)
            or 0
        )
        medium_value_knowledge_items = int(
            self._first_number(proposal.get("medium_value_knowledge_items"), 0)
            or 0
        )
        low_value_knowledge_items = int(
            self._first_number(proposal.get("low_value_knowledge_items"), 0)
            or 0
        )
        deprioritized_knowledge_items = int(
            self._first_number(proposal.get("deprioritized_knowledge_items"), 0)
            or 0
        )
        operational_investment_accuracy = self._bounded_ratio(
            materialized_operational_capabilities,
            high_value_knowledge_items,
        )
        high_value_operational_false_positives = max(
            high_value_knowledge_items - materialized_operational_capabilities,
            0,
        )
        operational_investment_accuracy_state = self._coverage_status(
            operational_investment_accuracy
        )
        validation_efficiency = self._bounded_ratio(
            validated_programs,
            arena_candidates,
        )
        high_value_validation_yield = self._bounded_ratio(
            validated_programs,
            high_value_knowledge_items,
        )
        operational_capability_acquisition_rate = self._bounded_ratio(
            known_operational_capabilities,
            operational_experience_task_count,
        )
        operational_capability_acquisition_rate_per_100_tasks = (
            round(operational_capability_acquisition_rate * 100, 2)
            if isinstance(operational_capability_acquisition_rate, (int, float))
            else None
        )
        target_experience_per_capability = 3
        expected_operational_capability_count = (
            max(1, int((operational_experience_count + target_experience_per_capability - 1) / target_experience_per_capability))
            if operational_experience_count > 0
            else 0
        )
        capability_population_evolution_gap = max(
            expected_operational_capability_count - known_operational_capabilities,
            0,
        )
        capability_population_evolution_speed = self._bounded_ratio(
            known_operational_capabilities,
            expected_operational_capability_count,
        )
        operational_experience_growth_speed = self._bounded_ratio(
            operational_experience_count,
            operational_experience_task_count,
        )
        capability_population_evolution_lag = self._bounded_ratio(
            capability_population_evolution_gap,
            expected_operational_capability_count,
        )
        capability_population_evolution_state = (
            "NOT_MEASURABLE"
            if expected_operational_capability_count <= 0
            else "SEVERE_EVOLUTION_LAG"
            if (
                isinstance(capability_population_evolution_lag, (int, float))
                and capability_population_evolution_lag >= 0.60
            )
            else "EVOLUTION_LAG"
            if (
                isinstance(capability_population_evolution_lag, (int, float))
                and capability_population_evolution_lag >= 0.30
            )
            else "EVOLVING"
        )
        operational_experience_per_capability = (
            round(operational_experience_count / known_operational_capabilities, 4)
            if known_operational_capabilities > 0
            else None
        )
        operational_specialization_pressure = (
            "HIGH"
            if (
                isinstance(operational_experience_per_capability, (int, float))
                and operational_experience_per_capability >= 5
                and known_operational_capabilities < 5
            )
            else "MEDIUM"
            if (
                isinstance(operational_experience_per_capability, (int, float))
                and operational_experience_per_capability >= 3
                and known_operational_capabilities < 5
            )
            else "LOW"
            if known_operational_capabilities
            else "NOT_MEASURABLE"
        )
        known_operation_set = {
            str(operation or "").strip().lower()
            for operation in (materialization.get("known_operational_operations") or [])
            if operation
        }
        proposal_rows = proposal.get("candidate_proposals") or []
        proposal_rows = proposal_rows if isinstance(proposal_rows, list) else []
        proposed_candidate_operations = [
            str(row.get("operation") or "").strip().lower()
            for row in proposal_rows
            if isinstance(row, dict)
            and row.get("proposal_status") == "PROPOSED"
            and row.get("operation")
        ]
        known_operational_candidate_count = len([
            operation for operation in proposed_candidate_operations
            if operation in known_operation_set
        ])
        novel_operational_candidate_count = len(proposed_candidate_operations) - (
            known_operational_candidate_count
        )
        current_operational_exploitation_rate = self._bounded_ratio(
            known_operational_candidate_count,
            len(proposed_candidate_operations),
        )
        current_operational_exploration_rate = self._bounded_ratio(
            novel_operational_candidate_count,
            len(proposed_candidate_operations),
        )
        capability_experience_distribution = (
            materialization.get("operational_capability_experience_distribution")
            or []
        )
        if not isinstance(capability_experience_distribution, list):
            capability_experience_distribution = []
        valid_distribution = [
            row for row in capability_experience_distribution
            if isinstance(row, dict)
        ]
        dominant_capability = valid_distribution[0] if valid_distribution else {}
        dominant_capability_experience_count = int(
            self._first_number(
                dominant_capability.get("experience_count"),
                0,
            )
            or 0
        )
        capability_monopoly_share = self._bounded_ratio(
            dominant_capability_experience_count,
            operational_experience_count,
        )
        experienced_capability_count = len([
            row for row in valid_distribution
            if int(self._first_number(row.get("experience_count"), 0) or 0) > 0
        ])
        independent_reuse_capability_count = len([
            row for row in valid_distribution
            if int(
                self._first_number(
                    row.get("independent_reuse_success_count"),
                    0,
                )
                or 0
            ) > 0
        ])
        capability_monopoly_pressure = (
            "HIGH"
            if (
                isinstance(capability_monopoly_share, (int, float))
                and capability_monopoly_share >= 0.60
                and known_operational_capabilities < 5
            )
            else "MEDIUM"
            if (
                isinstance(capability_monopoly_share, (int, float))
                and capability_monopoly_share >= 0.45
                and known_operational_capabilities < 5
            )
            else "LOW"
            if known_operational_capabilities
            else "NOT_MEASURABLE"
        )
        exploration_target = 0.30
        historical_exploitation_bias = capability_monopoly_share
        exploration_exploitation_balance_state = (
            "NOT_MEASURABLE"
            if not proposed_candidate_operations
            else "EXPLOITATION_BIASED"
            if (
                isinstance(current_operational_exploration_rate, (int, float))
                and current_operational_exploration_rate < 0.20
            )
            else "HISTORICAL_EXPLOITATION_BIAS_WITH_ACTIVE_EXPLORATION"
            if (
                capability_monopoly_pressure == "HIGH"
                and isinstance(current_operational_exploration_rate, (int, float))
                and current_operational_exploration_rate >= exploration_target
            )
            else "EXPLORATION_HEAVY"
            if (
                isinstance(current_operational_exploration_rate, (int, float))
                and current_operational_exploration_rate > 0.60
            )
            else "BALANCED"
            if (
                isinstance(current_operational_exploration_rate, (int, float))
                and current_operational_exploration_rate >= exploration_target
            )
            else "EXPLOITATION_LEANING"
        )

        coverage_scores = {
            "semantic_coverage": semantic_coverage,
            "compiler_coverage": compiler_coverage,
            "execution_package_coverage": execution_package_coverage,
            "candidate_coverage": candidate_coverage,
            "arena_coverage": arena_coverage,
            "arena_source_coverage": arena_source_coverage,
            "program_coverage": program_coverage,
            "operational_capability_coverage": operational_coverage,
            "compiler_runtime_coverage": compiler_runtime_coverage,
        }
        measured_scores = [
            float(value)
            for value in coverage_scores.values()
            if isinstance(value, (int, float))
        ]
        overall = (
            round(sum(measured_scores) / len(measured_scores), 4)
            if measured_scores
            else None
        )
        bottlenecks = [
            {
                "coverage_type": key,
                "coverage": round(float(value), 4),
                "status": self._coverage_status(float(value)),
            }
            for key, value in coverage_scores.items()
            if isinstance(value, (int, float))
        ]
        bottlenecks.sort(key=lambda item: (item["coverage"], item["coverage_type"]))

        candidate_lineage = self._candidate_source_lineage(proposal, arena)
        candidate_attrition = self._candidate_attrition_summary(
            proposal,
            arena,
            program_generation,
            semantic,
        )
        end_to_end_lifecycle = self._end_to_end_program_lifecycle_summary(
            generated_programs=generated_programs,
            compiler_runtime_activated_programs=compiler_runtime_activated_programs,
            compiled_programs=compiled_programs,
            candidate_count=candidate_count,
            arena_candidates=arena_candidates,
            validated_programs=validated_programs,
            materialized_operational_capabilities=materialized_operational_capabilities,
            known_operational_capabilities=known_operational_capabilities,
            known_operational_domain_count=known_operational_domain_count,
            prediction_contribution=bool(
                self._build_prediction_provenance_visibility(
                    report_state,
                    performance,
                ).get("prediction_provenance_summary", {}).get("prediction_source")
            ),
        )
        domain_architecture = self._cognitive_domain_architecture_summary(
            semantic,
            program_generation,
            program_lifecycle,
            proposal,
            arena,
            executable,
            candidate_lineage,
        )
        known_operational_domains = materialization.get("known_operational_domains") or []
        known_operational_domains = (
            known_operational_domains
            if isinstance(known_operational_domains, list)
            else []
        )
        known_operational_operations = (
            materialization.get("known_operational_operations") or []
        )
        known_operational_operations = (
            known_operational_operations
            if isinstance(known_operational_operations, list)
            else []
        )
        known_operational_domain_labels = {
            self._cognitive_domain_label(domain)
            for domain in known_operational_domains
            if domain
        }
        known_operational_domain_labels.update(
            self._cognitive_domain_label(
                self._cognitive_domain_for_operation(operation)
            )
            for operation in known_operational_operations
            if operation
        )
        historical_operational_domain_distribution: dict[str, int] = {}
        for operation in known_operational_operations:
            domain = self._cognitive_domain_label(
                self._cognitive_domain_for_operation(operation)
            )
            historical_operational_domain_distribution[domain] = (
                historical_operational_domain_distribution.get(domain, 0) + 1
            )
        for domain in known_operational_domains:
            historical_operational_domain_distribution.setdefault(
                self._cognitive_domain_label(domain),
                0,
            )
        sandbox_operational_domain_labels = {
            self._cognitive_domain_label(domain)
            for domain in operational_citizen_domain_distribution.keys()
            if domain
        }
        sandbox_operational_domain_labels.update(
            self._cognitive_domain_label(
                row.get("domain")
                or self._cognitive_domain_for_operation(row.get("operation"))
            )
            for row in top_operational_citizens
            if isinstance(row, dict)
        )
        operational_domain_citizen_labels = (
            known_operational_domain_labels | sandbox_operational_domain_labels
        )
        sandbox_operational_domain_distribution = {
            self._cognitive_domain_label(domain): int(count or 0)
            for domain, count in operational_citizen_domain_distribution.items()
        }
        combined_operational_domain_distribution = dict(
            historical_operational_domain_distribution
        )
        for domain, count in sandbox_operational_domain_distribution.items():
            combined_operational_domain_distribution[domain] = (
                combined_operational_domain_distribution.get(domain, 0) + count
            )
        combined_total = sum(combined_operational_domain_distribution.values())
        if combined_total:
            combined_dominant_domain, combined_dominant_count = sorted(
                combined_operational_domain_distribution.items(),
                key=lambda item: (-item[1], item[0]),
            )[0]
            dominant_operational_domain = combined_dominant_domain
            domain_monopoly_share = self._bounded_ratio(
                combined_dominant_count,
                combined_total,
            )
            domain_operational_imbalance_state = (
                "DOMAIN_MONOPOLY"
                if isinstance(domain_monopoly_share, (int, float))
                and domain_monopoly_share >= 0.60
                else "DOMAIN_IMBALANCE"
                if isinstance(domain_monopoly_share, (int, float))
                and domain_monopoly_share >= 0.40
                else "BALANCED"
            )
        surviving_capability_domain_labels = {
            self._cognitive_domain_label(
                row.get("domain")
                or self._cognitive_domain_for_operation(row.get("operation"))
            )
            for row in capability_survival_rows
            if isinstance(row, dict)
            and row.get("lifecycle_state")
            in {"SURVIVING_CAPABILITY", "OPERATIONAL_CITIZEN"}
        }
        domain_rows_for_citizenship = domain_architecture.get("domain_rows") or []
        domain_rows_for_citizenship = (
            domain_rows_for_citizenship
            if isinstance(domain_rows_for_citizenship, list)
            else []
        )
        expected_operational_domain_citizen_count = max(
            int(self._first_number(domain_architecture.get("domain_count"), 0) or 0),
            7,
        )
        historical_operational_domain_citizen_count = len(
            known_operational_domain_labels
        )
        sandbox_operational_domain_citizen_count = len(
            sandbox_operational_domain_labels
        )
        operational_domain_citizen_count = len(operational_domain_citizen_labels)
        operational_domain_citizenship_coverage = self._bounded_ratio(
            operational_domain_citizen_count,
            expected_operational_domain_citizen_count,
        )
        surviving_capability_domain_count = len(surviving_capability_domain_labels)
        missing_operational_citizen_domains = [
            self._cognitive_domain_label(row.get("domain_name"))
            for row in domain_rows_for_citizenship
            if isinstance(row, dict)
            and self._cognitive_domain_label(row.get("domain_name"))
            not in operational_domain_citizen_labels
            and isinstance(row.get("domain_operational_readiness"), (int, float))
            and float(row.get("domain_operational_readiness")) >= 0.60
        ]
        missing_operational_citizen_domains = sorted(
            set(missing_operational_citizen_domains)
        )
        operational_domain_report = operational_domain_infrastructure.analyze(
            domain_architecture=domain_architecture,
            operational_distribution=combined_operational_domain_distribution,
            survival_rows=capability_survival_rows,
            graduation_diagnostics=capability_graduation_diagnostics,
            target_domain_count=expected_operational_domain_citizen_count,
        )
        capability_ecology_report = capability_ecology_analysis.analyze(
            known_operations=known_operational_operations,
            experience_distribution=valid_distribution,
            survival_rows=capability_survival_rows,
            graduation_diagnostics=capability_graduation_diagnostics,
            domain_collaboration_rows=(
                operational_domain_report.get("domain_collaboration_rows") or []
            ),
            operational_programs=[],
        )
        operational_economy_report = operational_economy_analysis.analyze(
            generated_concepts=generated_concepts,
            generated_programs=generated_programs,
            candidate_count=candidate_count,
            arena_candidate_count=arena_candidates,
            compiled_programs=compiled_programs,
            validated_programs=validated_programs,
            materialized_operational_capabilities=(
                materialized_operational_capabilities
            ),
            operational_citizen_count=operational_citizen_count,
            expected_operational_capability_count=(
                expected_operational_capability_count
            ),
            known_operational_capability_count=known_operational_capabilities,
            operational_experience_count=operational_experience_count,
            candidate_attrition_summary=candidate_attrition,
            capability_ecology_report=capability_ecology_report,
            capability_population_evolution_lag=(
                capability_population_evolution_lag
            ),
            generated_to_citizen_pressure_ratio=(
                generated_to_citizen_pressure_ratio
            ),
            crystallization_candidate_count=crystallization_candidate_count,
            high_value_knowledge_items=high_value_knowledge_items,
            medium_value_knowledge_items=medium_value_knowledge_items,
            low_value_knowledge_items=low_value_knowledge_items,
        )
        missing_requirements = program_generation.get("missing_requirements") or []
        if not isinstance(missing_requirements, list):
            missing_requirements = [missing_requirements]
        execution_package_ready = (
            isinstance(execution_package_coverage, (int, float))
            and float(execution_package_coverage) >= 0.50
        )
        compiler_runtime_ready = (
            isinstance(compiler_runtime_coverage, (int, float))
            and float(compiler_runtime_coverage) >= 0.40
        )
        operational_capability_ready = (
            isinstance(operational_coverage, (int, float))
            and float(operational_coverage) >= 0.15
        )
        freeze_blockers = []
        if not execution_package_ready:
            freeze_blockers.append("execution_package_coverage_below_50_percent")
        if not compiler_runtime_ready:
            freeze_blockers.append("compiler_runtime_coverage_below_40_percent")
        if not operational_capability_ready:
            freeze_blockers.append("operational_capability_coverage_below_15_percent")
        architecture_freeze_state = (
            "ACTIVE_UNTIL_OPERATIONALIZATION_THRESHOLDS_MET"
            if freeze_blockers
            else "READY_FOR_TARGETED_ARCHITECTURE_CHANGES"
        )

        summary = {
            "overall_cognitive_capability_coverage": overall,
            "coverage_status": self._coverage_status(overall),
            "architecture_freeze_state": architecture_freeze_state,
            "architecture_freeze_reason": (
                ", ".join(freeze_blockers)
                if freeze_blockers
                else "operationalization_thresholds_met"
            ),
            "architecture_freeze_blockers": freeze_blockers,
            "execution_package_coverage_target": 0.50,
            "compiler_runtime_coverage_target": 0.40,
            "operational_capability_coverage_target": 0.15,
            "semantic_coverage": semantic_coverage,
            "compiler_coverage": compiler_coverage,
            "execution_package_coverage": execution_package_coverage,
            "candidate_coverage": candidate_coverage,
            "arena_coverage": arena_coverage,
            "arena_source_coverage": arena_source_coverage,
            "program_coverage": program_coverage,
            "validated_executable_coverage": validated_executable_coverage,
            "operational_capability_coverage": operational_coverage,
            "operational_capability_materialization_rate": operational_materialization_rate,
            "operational_yield_from_concepts": operational_yield_from_concepts,
            "operational_yield_from_programs": operational_yield_from_programs,
            "operational_yield_from_candidates": operational_yield_from_candidates,
            "operational_yield_from_arena": operational_yield_from_arena,
            "knowledge_production_efficiency": knowledge_production_efficiency,
            "knowledge_operationalization_efficiency": knowledge_operationalization_efficiency,
            "operational_knowledge_waste": operational_knowledge_waste,
            "operational_yield_stability": operational_yield_stability,
            "operational_yield_stability_basis": "experience_reuse_proxy",
            "operational_yield_health_state": operational_yield_health_state,
            "candidate_attrition_summary": candidate_attrition,
            "end_to_end_program_lifecycle": end_to_end_lifecycle,
            "cognitive_domain_architecture_summary": domain_architecture,
            "candidate_source_lineage": candidate_lineage,
            "lowest_coverage_bottlenecks": bottlenecks[:5],
            "knowledge_investment_policy": proposal.get(
                "knowledge_investment_policy"
            ),
            "knowledge_investment_authority": proposal.get(
                "knowledge_investment_authority"
            ),
            "high_value_knowledge_items": high_value_knowledge_items,
            "medium_value_knowledge_items": medium_value_knowledge_items,
            "low_value_knowledge_items": low_value_knowledge_items,
            "deprioritized_knowledge_items": deprioritized_knowledge_items,
            "operational_investment_accuracy": operational_investment_accuracy,
            "operational_investment_accuracy_state": operational_investment_accuracy_state,
            "high_value_operational_false_positives": high_value_operational_false_positives,
            "validation_efficiency": validation_efficiency,
            "validation_bottleneck_inflation": validation_bottleneck_inflation,
            "validation_bottleneck_state": validation_bottleneck_state,
            "high_value_validation_yield": high_value_validation_yield,
            "operational_capability_acquisition_rate": operational_capability_acquisition_rate,
            "operational_capability_acquisition_rate_per_100_tasks": operational_capability_acquisition_rate_per_100_tasks,
            "capability_survival_rate": capability_survival_rate,
            "materialization_survival_rate": materialization_survival_rate,
            "candidate_retention_rate": candidate_retention_rate,
            "incubation_conversion_rate": incubation_conversion_rate,
            "surviving_capability_count": surviving_capability_count,
            "surviving_capability_conversion_rate": surviving_capability_conversion_rate,
            "operational_citizen_conversion_rate": operational_citizen_conversion_rate,
            "current_run_operational_citizen_count": operational_citizen_count,
            "historical_operational_citizen_count": historical_operational_citizen_count,
            "expected_operational_domain_citizen_count": (
                expected_operational_domain_citizen_count
            ),
            "historical_operational_domain_citizen_count": (
                historical_operational_domain_citizen_count
            ),
            "sandbox_operational_domain_citizen_count": (
                sandbox_operational_domain_citizen_count
            ),
            "operational_domain_citizen_count": operational_domain_citizen_count,
            "operational_domain_citizenship_coverage": (
                operational_domain_citizenship_coverage
            ),
            "operational_citizen_domain_distribution": (
                operational_citizen_domain_distribution
            ),
            "historical_operational_domain_distribution": (
                historical_operational_domain_distribution
            ),
            "sandbox_operational_domain_distribution": (
                sandbox_operational_domain_distribution
            ),
            "combined_operational_domain_distribution": (
                combined_operational_domain_distribution
            ),
            "dominant_operational_domain": dominant_operational_domain,
            "domain_monopoly_share": domain_monopoly_share,
            "domain_operational_imbalance_state": (
                domain_operational_imbalance_state
            ),
            "operational_domain_infrastructure_report": operational_domain_report,
            "operational_domain_health": operational_domain_report.get(
                "operational_domain_health"
            ),
            "operational_domain_coverage": operational_domain_report.get(
                "operational_domain_coverage"
            ),
            "domain_operationalization_score": operational_domain_report.get(
                "domain_operationalization_score"
            ),
            "domain_operationalization_bottleneck": (
                operational_domain_report.get(
                    "domain_operationalization_bottleneck"
                )
            ),
            "domain_population_balance": operational_domain_report.get(
                "domain_population_balance"
            ),
            "domain_collaboration_score": operational_domain_report.get(
                "domain_collaboration_score"
            ),
            "domain_operational_growth_rate": operational_domain_report.get(
                "domain_operational_growth_rate"
            ),
            "domain_primitive_coverage": operational_domain_report.get(
                "domain_primitive_coverage"
            ),
            "domain_capability_diversity": operational_domain_report.get(
                "domain_capability_diversity"
            ),
            "domain_infrastructure_readiness": operational_domain_report.get(
                "domain_infrastructure_readiness"
            ),
            "operational_domain_population": operational_domain_report.get(
                "operational_domain_population"
            ),
            "domain_diversification_score": operational_domain_report.get(
                "domain_diversification_score"
            ),
            "domain_monopoly_pressure": operational_domain_report.get(
                "domain_monopoly_pressure"
            ),
            "operational_domain_growth_rate": operational_domain_report.get(
                "operational_domain_growth_rate"
            ),
            "operational_domain_evolution_speed": operational_domain_report.get(
                "operational_domain_evolution_speed"
            ),
            "operational_domain_diagnostics": (
                operational_domain_report.get("domain_diagnostics") or []
            )[:10],
            "operational_domain_gaps": (
                operational_domain_report.get("domain_operationalization_gaps")
                or []
            )[:10],
            "domain_collaboration_rows": (
                operational_domain_report.get("domain_collaboration_rows") or []
            )[:10],
            "domain_collaboration_graph": operational_domain_report.get(
                "domain_collaboration_graph"
            ) or {},
            "isolated_operational_domains": operational_domain_report.get(
                "isolated_operational_domains"
            ) or [],
            "productive_operational_domains": operational_domain_report.get(
                "productive_operational_domains"
            ) or [],
            "domain_operational_targets": (
                operational_domain_report.get("domain_operational_targets") or []
            )[:10],
            "domain_expansion_roadmap": (
                operational_domain_report.get("domain_expansion_roadmap") or []
            )[:7],
            "capability_ecology_report": capability_ecology_report,
            "capability_ecology_health": capability_ecology_report.get(
                "capability_ecology_health"
            ),
            "capability_cooperation_score": capability_ecology_report.get(
                "capability_cooperation_score"
            ),
            "capability_composition_score": capability_ecology_report.get(
                "capability_composition_score"
            ),
            "composite_capability_score": capability_ecology_report.get(
                "composite_capability_score"
            ),
            "capability_collaboration_diversity": capability_ecology_report.get(
                "capability_collaboration_diversity"
            ),
            "composite_operational_capability_count": (
                capability_ecology_report.get(
                    "composite_operational_capability_count"
                )
            ),
            "capability_interaction_density": capability_ecology_report.get(
                "capability_interaction_density"
            ),
            "capability_composition_readiness": capability_ecology_report.get(
                "capability_composition_readiness"
            ),
            "composite_intelligence_readiness": capability_ecology_report.get(
                "composite_intelligence_readiness"
            ),
            "capability_ecology_state": capability_ecology_report.get(
                "capability_ecology_state"
            ),
            "composite_capability_candidates": (
                capability_ecology_report.get("composite_capability_candidates")
                or []
            )[:10],
            "capability_synergy_matrix": (
                capability_ecology_report.get("capability_synergy_matrix")
                or []
            )[:10],
            "capability_economy_health": capability_ecology_report.get(
                "capability_economy_health"
            ),
            "capability_specialization_report": (
                capability_ecology_report.get("capability_specialization_report")
                or []
            )[:10],
            "capability_composition_opportunities": (
                capability_ecology_report.get(
                    "capability_composition_opportunities"
                )
                or []
            )[:10],
            "capability_economy_rows": (
                capability_ecology_report.get("capability_economy_rows") or []
            )[:10],
            "high_value_capabilities": (
                capability_ecology_report.get("high_value_capabilities") or []
            )[:10],
            "capability_investment_priorities": (
                capability_ecology_report.get("capability_investment_priorities")
                or []
            )[:5],
            "operational_economy_report": operational_economy_report,
            "operational_economy_health": operational_economy_report.get(
                "operational_economy_health"
            ),
            "knowledge_attrition_health": operational_economy_report.get(
                "knowledge_attrition_health"
            ),
            "knowledge_attrition_loss_score": operational_economy_report.get(
                "knowledge_attrition_loss_score"
            ),
            "knowledge_attrition_state": operational_economy_report.get(
                "knowledge_attrition_state"
            ),
            "operational_investment_return": operational_economy_report.get(
                "operational_investment_return"
            ),
            "operational_investment_return_state": (
                operational_economy_report.get("operational_investment_return_state")
            ),
            "knowledge_crystallization_efficiency": (
                operational_economy_report.get(
                    "knowledge_crystallization_efficiency"
                )
            ),
            "knowledge_crystallization_pressure": (
                operational_economy_report.get("knowledge_crystallization_pressure")
            ),
            "operational_population_growth_pressure": (
                operational_economy_report.get("operational_population_growth_pressure")
            ),
            "capability_economy_crisis_score": operational_economy_report.get(
                "capability_economy_crisis_score"
            ),
            "capability_economy_crisis_state": operational_economy_report.get(
                "capability_economy_crisis_state"
            ),
            "capability_lifecycle_efficiency": operational_economy_report.get(
                "capability_lifecycle_efficiency"
            ),
            "knowledge_to_citizen_efficiency": operational_economy_report.get(
                "knowledge_to_citizen_efficiency"
            ),
            "candidate_attrition_cost": operational_economy_report.get(
                "candidate_attrition_cost"
            ),
            "candidate_attrition_cost_state": operational_economy_report.get(
                "candidate_attrition_cost_state"
            ),
            "knowledge_attrition_lifecycle": (
                operational_economy_report.get("knowledge_attrition_lifecycle")
                or []
            )[:10],
            "operational_lifecycle_conversion_rates": (
                operational_economy_report.get(
                    "operational_lifecycle_conversion_rates"
                )
                or {}
            ),
            "operational_economy_bottleneck": operational_economy_report.get(
                "operational_economy_bottleneck"
            ),
            "operational_economy_roadmap": (
                operational_economy_report.get("operational_economy_roadmap")
                or []
            )[:7],
            "operational_capability_clusters": (
                operational_economy_report.get("operational_capability_clusters")
                or []
            )[:10],
            "operational_cluster_readiness": operational_economy_report.get(
                "operational_cluster_readiness"
            ),
            "operational_cluster_count": operational_economy_report.get(
                "operational_cluster_count"
            ),
            "surviving_capability_domain_count": surviving_capability_domain_count,
            "missing_operational_citizen_domains": (
                missing_operational_citizen_domains
            ),
            "generated_survival_candidate_count": generated_survival_candidate_count,
            "arena_simulated_survival_candidate_count": arena_simulated_survival_candidate_count,
            "arena_quality_survival_candidate_count": arena_quality_survival_candidate_count,
            "incubating_operational_capability_count": incubating_operational_capability_count,
            "operational_citizen_count": operational_citizen_count,
            "validation_gap_candidate_count": validation_gap_candidate_count,
            "unresolved_validation_gap_candidate_count": (
                unresolved_validation_gap_candidate_count
            ),
            "capability_survival_state_distribution": survival_state_distribution,
            "top_incubating_capabilities": top_incubating_capabilities[:5],
            "top_operational_citizens": top_operational_citizens[:5],
            "top_crystallization_candidates": top_crystallization_candidates[:5],
            "cognitive_citizen_count": cognitive_citizen_count,
            "top_cognitive_citizens": top_cognitive_citizens[:5],
            "cognitive_citizenship_definition": cognitive_citizenship_definition,
            "crystallization_candidate_count": crystallization_candidate_count,
            "quality_to_citizen_crystallization_rate": (
                quality_to_citizen_crystallization_rate
            ),
            "candidate_to_citizen_crystallization_rate": (
                candidate_to_citizen_crystallization_rate
            ),
            "generated_to_citizen_pressure_ratio": (
                generated_to_citizen_pressure_ratio
            ),
            "capability_crystallization_state": capability_crystallization_state,
            "capability_graduation_candidate_count": (
                capability_graduation_candidate_count
            ),
            "capability_graduation_pressure": capability_graduation_pressure,
            "capability_graduation_pressure_state": (
                capability_graduation_pressure_state
            ),
            "capability_graduation_queue": capability_graduation_queue[:5],
            "top_graduation_candidates": top_graduation_candidates[:5],
            "world_governance_graduation_action": (
                world_governance_graduation_action
            ),
            "capability_graduation_infrastructure_report": (
                graduation_infrastructure_report
            ),
            "capability_graduation_health": capability_graduation_health,
            "graduation_pipeline_health": graduation_pipeline_health,
            "graduation_success_rate": graduation_success_rate,
            "graduation_failure_rate": graduation_failure_rate,
            "graduation_queue_health": graduation_queue_health,
            "graduation_evidence_coverage": graduation_evidence_coverage,
            "graduation_infrastructure_readiness": (
                graduation_infrastructure_readiness
            ),
            "average_capability_graduation_time": (
                average_capability_graduation_time
            ),
            "graduation_backlog_size": graduation_backlog_size,
            "capability_graduation_queue_health": (
                capability_graduation_queue_health
            ),
            "capability_graduation_risk": capability_graduation_risk,
            "capability_graduation_complexity": (
                capability_graduation_complexity
            ),
            "capability_graduation_confidence": (
                capability_graduation_confidence
            ),
            "graduation_pipeline_stages": graduation_pipeline_stages,
            "graduation_transition_rows": graduation_transition_rows[:5],
            "capability_graduation_diagnostics": (
                capability_graduation_diagnostics[:10]
            ),
            "top_graduation_priority": top_graduation_priority,
            "graduation_sprint_recommendations": (
                graduation_sprint_recommendations[:5]
            ),
            "validator_failure_distribution": validator_failure_distribution,
            "world_governance_promotion_policy": (
                world_governance_promotion_policy
            ),
            "world_governance_promotion_policy_state": (
                world_governance_promotion_policy_state
            ),
            "sandbox_citizenship_thresholds": sandbox_citizenship_thresholds,
            "trusted_capability_policy": trusted_capability_policy,
            "decision_authority_policy": decision_authority_policy,
            "capability_stability_regression_count": (
                capability_stability_regression_count
            ),
            "top_stability_regressions": top_stability_regressions[:5],
            "capability_survival_rows": capability_survival_rows,
            "capability_survival_store_path": materialization.get(
                "capability_survival_store_path"
            ) or survival.get("store_path"),
            "target_experience_per_capability": target_experience_per_capability,
            "expected_operational_capability_count": expected_operational_capability_count,
            "capability_population_evolution_gap": capability_population_evolution_gap,
            "capability_population_evolution_speed": capability_population_evolution_speed,
            "operational_experience_growth_speed": operational_experience_growth_speed,
            "capability_population_evolution_lag": capability_population_evolution_lag,
            "capability_population_evolution_state": capability_population_evolution_state,
            "operational_experience_per_capability": operational_experience_per_capability,
            "operational_specialization_pressure": operational_specialization_pressure,
            "current_operational_exploration_rate": current_operational_exploration_rate,
            "current_operational_exploitation_rate": current_operational_exploitation_rate,
            "known_operational_candidate_count": known_operational_candidate_count,
            "novel_operational_candidate_count": novel_operational_candidate_count,
            "operational_exploration_target": exploration_target,
            "historical_exploitation_bias": historical_exploitation_bias,
            "exploration_exploitation_balance_state": exploration_exploitation_balance_state,
            "capability_monopoly_share": capability_monopoly_share,
            "capability_monopoly_pressure": capability_monopoly_pressure,
            "dominant_operational_capability": dominant_capability.get("operation"),
            "dominant_capability_experience_count": dominant_capability_experience_count,
            "experienced_capability_count": experienced_capability_count,
            "independent_reuse_capability_count": independent_reuse_capability_count,
            "capability_experience_distribution": valid_distribution[:5],
            "compiler_runtime_coverage": compiler_runtime_coverage,
            "compiler_failure_count": compiler_failure_diagnostics.get(
                "compiler_failure_count",
                0,
            ),
            "compiler_failure_reason_distribution": (
                compiler_failure_diagnostics.get(
                    "compiler_failure_reason_distribution",
                    {},
                )
            ),
            "compiler_failure_domain_distribution": (
                compiler_failure_diagnostics.get(
                    "compiler_failure_domain_distribution",
                    {},
                )
            ),
            "compiler_failure_rows": compiler_failure_diagnostics.get(
                "compiler_failure_rows",
                [],
            ),
            "compiler_diagnostic_state": compiler_failure_diagnostics.get(
                "compiler_diagnostic_state",
            ),
            "compiler_failure_detail_capture_state": (
                compiler_failure_diagnostics.get(
                    "compiler_failure_detail_capture_state",
                )
            ),
            "compiler_failure_pressure": compiler_failure_diagnostics.get(
                "compiler_failure_pressure",
            ),
            "compiler_success_rate": compiler_failure_diagnostics.get(
                "compiler_success_rate",
            ),
            "execution_package_health_score": compiler_infrastructure.get(
                "execution_package_health_score",
            ),
            "primitive_operation_coverage": compiler_infrastructure.get(
                "primitive_operation_coverage",
            ),
            "compiler_infrastructure_health": compiler_infrastructure.get(
                "compiler_infrastructure_health",
            ),
            "multi_step_program_support": compiler_infrastructure.get(
                "multi_step_program_support",
            ),
            "execution_package_dependency_coverage": (
                compiler_infrastructure.get(
                    "execution_package_dependency_coverage",
                )
            ),
            "primitive_infrastructure_coverage": compiler_infrastructure.get(
                "primitive_infrastructure_coverage",
            ),
            "compiler_primitive_success_rate": compiler_infrastructure.get(
                "compiler_primitive_success_rate",
            ),
            "execution_package_utilization": compiler_infrastructure.get(
                "execution_package_utilization",
            ),
            "compiler_infrastructure_readiness": compiler_infrastructure.get(
                "compiler_infrastructure_readiness",
            ),
            "execution_package_inventory": compiler_infrastructure.get(
                "execution_package_inventory",
                [],
            ),
            "primitive_operation_inventory": compiler_infrastructure.get(
                "primitive_operation_inventory",
                [],
            ),
            "multi_step_program_report": compiler_infrastructure.get(
                "multi_step_program_report",
                {},
            ),
            "generated_concepts": generated_concepts,
            "measured_concepts": measured_concepts,
            "executable_concepts": executable_concepts,
            "unsupported_concepts": semantic.get("unsupported_concepts"),
            "generated_programs": generated_programs,
            "generated_blueprints": generated_blueprints,
            "candidate_count": candidate_count,
            "arena_candidate_count": arena_candidates,
            "arena_source_count": len([source for source in arena_sources if source]),
            "compiled_programs": compiled_programs,
            "compiler_runtime_activated_programs": compiler_runtime_activated_programs,
            "validated_programs": validated_programs,
            "materialized_operational_capabilities": materialized_operational_capabilities,
            "operational_confidence_state": materialization.get(
                "operational_confidence_state"
            ),
            "authority_transfer_state": materialization.get(
                "authority_transfer_state"
            ),
            "trusted_for_decision_count": materialization.get(
                "trusted_for_decision_count"
            ),
            "decision_trust_state": materialization.get(
                "decision_trust_state"
            ),
            "operational_experience_count": operational_experience_count,
            "operational_experience_task_count": operational_experience_task_count,
            "reuse_evidence_count": reuse_evidence_count,
            "independent_reuse_success_count": independent_reuse_success_count,
            "operational_experience_store_path": materialization.get(
                "experience_store_path"
            ),
            "known_operational_capability_count": materialization.get(
                "known_operational_capability_count"
            ),
            "known_operational_operations": materialization.get(
                "known_operational_operations"
            ) or [],
            "known_operational_domain_count": known_operational_domain_count,
            "known_operational_domains": known_operational_domains,
            "operational_capability_population_target": 5,
            "operational_domain_population_target": 5,
            "capability_population_diversification": population_diversification,
            "operational_programs": operational_programs,
            "missing_execution_packages": (
                compiler_infrastructure.get("missing_execution_packages")
                if "missing_execution_packages" in compiler_infrastructure
                else semantic.get("unsupported_operations") or []
            ),
            "unused_execution_packages": compiler_infrastructure.get(
                "unused_execution_packages",
                [],
            ),
            "partial_execution_packages": compiler_infrastructure.get(
                "partial_execution_packages",
                [],
            ),
            "missing_compiler_requirements": missing_requirements,
            "candidate_attrition_summary": candidate_attrition,
            "end_to_end_program_lifecycle": end_to_end_lifecycle,
            "cognitive_domain_architecture_summary": domain_architecture,
            "candidate_source_lineage": candidate_lineage,
            "lowest_coverage_bottlenecks": bottlenecks[:5],
            "arena_decision_authority": "SANDBOX_ONLY"
            if arena.get("selection_mode") == "EVIDENCE_BASED_ARENA"
            else arena.get("selection_mode"),
            "prediction_authority_preserved": self._build_prediction_provenance_visibility(
                report_state,
                performance,
            ).get("prediction_provenance_summary", {}).get("prediction_source"),
        }
        return {
            "cognitive_capability_coverage_summary": summary,
            "cognitive_capability_coverage_diagnostics": {
                "coverage_scores": coverage_scores,
                "candidate_attrition_summary": candidate_attrition,
                "end_to_end_program_lifecycle": end_to_end_lifecycle,
                "cognitive_domain_architecture_summary": domain_architecture,
                "candidate_source_lineage": candidate_lineage,
                "capability_ecology_report": capability_ecology_report,
                "operational_economy_report": operational_economy_report,
                "semantic_coverage_summary": semantic,
                "program_generation_summary": program_generation,
                "candidate_proposal_summary": proposal,
                "candidate_arena_summary": arena,
                "executable_intelligence_report": executable,
            },
            **summary,
        }

    def _materialized_operational_capability_count(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> int:
        materialization = self._operational_capability_materialization_summary(
            report_state,
            performance,
        )
        materialized = self._first_number(
            materialization.get("materialized_operational_capabilities"),
            materialization.get("reusable_operational_capabilities"),
        )
        if materialized is not None:
            return int(materialized or 0)

        explicit_ecosystem = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_ECOSYSTEM_REPORT", "cognitive_domain_ecosystem_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_ECOSYSTEM_REPORT", "cognitive_domain_ecosystem_report"),
        )
        coverage = self._first_dict(explicit_ecosystem, "global_cognitive_coverage")
        ecosystem = self._first_dict(explicit_ecosystem, "ecosystem")
        direct = self._first_number(
            coverage.get("operational_capabilities"),
            ecosystem.get("operational_capabilities"),
            explicit_ecosystem.get("operational_capabilities"),
            explicit_ecosystem.get("total_operational_capabilities"),
        )
        if direct is not None:
            return int(direct or 0)

        explicit_lifecycle = self._merge_dicts(
            self._first_dict(report_state, "COGNITIVE_DOMAIN_LIFECYCLE_REPORT", "cognitive_domain_lifecycle_report"),
            self._first_dict(performance, "COGNITIVE_DOMAIN_LIFECYCLE_REPORT", "cognitive_domain_lifecycle_report"),
        )
        registry = explicit_lifecycle.get("domain_registry") or []
        if isinstance(registry, list):
            return sum(
                len(row.get("operational_capabilities") or [])
                for row in registry
                if isinstance(row, dict)
            )
        return 0

    def _operational_capability_materialization_summary(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        return self._merge_dicts(
            self._first_dict(report_state, "OPERATIONAL_CAPABILITY_MATERIALIZATION_REPORT", "operational_capability_materialization_report"),
            self._first_dict(performance, "OPERATIONAL_CAPABILITY_MATERIALIZATION_REPORT", "operational_capability_materialization_report"),
        )

    def _end_to_end_program_lifecycle_summary(
        self,
        *,
        generated_programs: int,
        compiler_runtime_activated_programs: int,
        compiled_programs: int,
        candidate_count: int,
        arena_candidates: int,
        validated_programs: int,
        materialized_operational_capabilities: int,
        known_operational_capabilities: int,
        known_operational_domain_count: int,
        prediction_contribution: bool,
    ) -> dict[str, Any]:
        return {
            "generated_programs": generated_programs,
            "compiler_runtime_activated_programs": compiler_runtime_activated_programs,
            "compiled_programs": compiled_programs,
            "candidate_count": candidate_count,
            "arena_candidate_count": arena_candidates,
            "validated_programs": validated_programs,
            "prediction_contribution_count": 1 if prediction_contribution else 0,
            "materialized_operational_capabilities": materialized_operational_capabilities,
            "known_operational_capabilities": known_operational_capabilities,
            "known_operational_domain_count": known_operational_domain_count,
            "program_to_compiler_activation_rate": self._bounded_ratio(
                compiler_runtime_activated_programs,
                generated_programs,
            ),
            "compiler_activation_to_compile_success_rate": self._bounded_ratio(
                compiled_programs,
                compiler_runtime_activated_programs,
            ),
            "program_to_candidate_rate": self._bounded_ratio(
                candidate_count,
                generated_programs,
            ),
            "candidate_to_arena_rate": self._bounded_ratio(
                arena_candidates,
                candidate_count,
            ),
            "arena_to_validation_rate": self._bounded_ratio(
                validated_programs,
                arena_candidates,
            ),
            "program_to_validation_rate": self._bounded_ratio(
                validated_programs,
                generated_programs,
            ),
            "validation_to_operational_capability_rate": self._bounded_ratio(
                materialized_operational_capabilities,
                validated_programs,
            ),
            "operationalization_bottleneck": (
                "compiler_success"
                if compiled_programs < max(compiler_runtime_activated_programs, 1)
                else "arena_entry"
                if arena_candidates < max(candidate_count, 1)
                else "validation"
                if validated_programs < max(arena_candidates, 1)
                else "capability_materialization"
                if materialized_operational_capabilities < max(validated_programs, 1)
                else "none"
            ),
            "secondary_operationalization_bottleneck": (
                "capability_population_diversification"
                if known_operational_domain_count < 5
                else "capability_population_growth"
                if known_operational_capabilities < 5
                else "capability_materialization"
                if (
                    validated_programs > 0
                    and materialized_operational_capabilities < validated_programs
                )
                else "none"
            ),
            "current_run_materialization_gap": (
                "capability_materialization"
                if (
                    validated_programs > 0
                    and materialized_operational_capabilities < validated_programs
                )
                else "none"
            ),
        }

    def _candidate_attrition_summary(
        self,
        proposal: dict[str, Any],
        arena: dict[str, Any],
        program_generation: dict[str, Any],
        semantic: dict[str, Any],
    ) -> dict[str, Any]:
        proposals = proposal.get("candidate_proposals") or []
        proposals = proposals if isinstance(proposals, list) else []
        arena_rows = arena.get("candidate_rows") or []
        arena_rows = arena_rows if isinstance(arena_rows, list) else []
        generated = int(self._first_number(
            proposal.get("proposal_count"),
            len([item for item in proposals if isinstance(item, dict) and item.get("proposal_status") == "PROPOSED"]),
            arena.get("unique_candidate_count"),
            arena.get("candidate_count"),
        ) or 0)
        entered = int(self._first_number(
            arena.get("candidate_count"),
            len([row for row in arena_rows if isinstance(row, dict) and row.get("entered_arena")]),
        ) or 0)
        rejected = max(generated - entered, int(self._first_number(
            arena.get("governance_blocked_count"),
            proposal.get("explicit_rejection_count"),
            0,
        ) or 0))
        reasons: dict[str, int] = {}
        for row in proposals:
            if not isinstance(row, dict):
                continue
            if row.get("proposal_status") == "REJECTED":
                reason = str(row.get("rejection_reason") or "proposal_rejected")
                reasons[reason] = reasons.get(reason, 0) + 1
        for row in arena_rows:
            if not isinstance(row, dict):
                continue
            if not row.get("entered_arena"):
                reason = str(row.get("blocked_reason") or row.get("status") or "arena_rejected")
                reasons[reason] = reasons.get(reason, 0) + 1
        explained = sum(reasons.values())
        if rejected and explained < rejected:
            remaining = rejected - explained
            missing_requirements = program_generation.get("missing_requirements") or []
            missing_requirements = (
                missing_requirements
                if isinstance(missing_requirements, list)
                else [missing_requirements]
            )
            unsupported = semantic.get("unsupported_operations") or []
            unsupported = unsupported if isinstance(unsupported, list) else [unsupported]
            if any("compiler" in str(item) for item in missing_requirements):
                allocated = min(remaining, max(len(missing_requirements), 1))
                reasons["compiler_support_missing"] = (
                    reasons.get("compiler_support_missing", 0) + allocated
                )
                remaining -= allocated
            if unsupported:
                if remaining > 0:
                    reasons["execution_package_missing"] = remaining
                    remaining = 0
            if remaining > 0:
                reasons["not_reported_by_candidate_gateway"] = (
                    reasons.get("not_reported_by_candidate_gateway", 0)
                    + remaining
                )
        return {
            "generated_candidates": generated,
            "entered_arena": entered,
            "rejected_before_arena": rejected,
            "arena_acceptance_rate": self._bounded_ratio(entered, generated),
            "rejection_reasons": reasons,
        }

    def _cognitive_domain_architecture_summary(
        self,
        semantic: dict[str, Any],
        program_generation: dict[str, Any],
        program_lifecycle: dict[str, Any],
        proposal: dict[str, Any],
        arena: dict[str, Any],
        executable: dict[str, Any],
        candidate_lineage: list[dict[str, Any]],
    ) -> dict[str, Any]:
        domain_names = [
            "Growth Cognitive Domain",
            "Spatial Cognitive Domain",
            "Topology Cognitive Domain",
            "Transformation Cognitive Domain",
            "Identity Cognitive Domain",
            "Geometry Cognitive Domain",
            "Color Cognitive Domain",
        ]
        domains = {
            name: {
                "domain_name": name,
                "semantic_concepts": set(),
                "executable_concepts": set(),
                "program_blueprints": set(),
                "candidate_count": 0,
                "arena_candidate_count": 0,
                "validated_programs": 0,
                "missing_execution_packages": set(),
                "missing_compiler_requirements": set(),
            }
            for name in domain_names
        }

        rows = []
        for key in ("supported_concept_rows", "unsupported_concept_rows"):
            value = semantic.get(key) or []
            if isinstance(value, list):
                rows.extend(item for item in value if isinstance(item, dict))
        for row in rows:
            concept = str(row.get("concept") or "")
            domain = self._cognitive_domain_for_concept(concept)
            domains.setdefault(domain, {
                "domain_name": domain,
                "semantic_concepts": set(),
                "executable_concepts": set(),
                "program_blueprints": set(),
                "candidate_count": 0,
                "arena_candidate_count": 0,
                "validated_programs": 0,
                "missing_execution_packages": set(),
                "missing_compiler_requirements": set(),
            })
            domains[domain]["semantic_concepts"].add(concept)
            if row.get("executable"):
                domains[domain]["executable_concepts"].add(concept)
            else:
                domains[domain]["missing_execution_packages"].add(concept)

        blueprints = program_generation.get("program_blueprints") or []
        blueprints = blueprints if isinstance(blueprints, list) else []
        for blueprint in blueprints:
            if not isinstance(blueprint, dict):
                continue
            concepts = blueprint.get("supported_concepts") or [
                blueprint.get("concept_name")
            ]
            concepts = concepts if isinstance(concepts, list) else [concepts]
            blueprint_name = str(
                blueprint.get("program_name")
                or blueprint.get("program_type")
                or blueprint.get("concept_name")
                or "program_blueprint"
            )
            missing = blueprint.get("missing_requirements") or []
            missing = missing if isinstance(missing, list) else [missing]
            for concept in concepts:
                if not concept:
                    continue
                domain = self._cognitive_domain_for_concept(str(concept))
                domains.setdefault(domain, {
                    "domain_name": domain,
                    "semantic_concepts": set(),
                    "executable_concepts": set(),
                    "program_blueprints": set(),
                    "candidate_count": 0,
                    "arena_candidate_count": 0,
                    "validated_programs": 0,
                    "missing_execution_packages": set(),
                    "missing_compiler_requirements": set(),
                })
                domains[domain]["program_blueprints"].add(blueprint_name)
                for item in missing:
                    if item:
                        domains[domain]["missing_compiler_requirements"].add(str(item))

        for row in candidate_lineage:
            if not isinstance(row, dict):
                continue
            domain = self._cognitive_domain_for_operation(row.get("operation"))
            domains.setdefault(domain, {
                "domain_name": domain,
                "semantic_concepts": set(),
                "executable_concepts": set(),
                "program_blueprints": set(),
                "candidate_count": 0,
                "arena_candidate_count": 0,
                "validated_programs": 0,
                "missing_execution_packages": set(),
                "missing_compiler_requirements": set(),
            })
            domains[domain]["candidate_count"] += 1
            if row.get("entered_arena"):
                domains[domain]["arena_candidate_count"] += 1

        validated_total = int(self._first_number(
            executable.get("validated_programs"),
            executable.get("validated_program_count"),
            0,
        ) or 0)
        arena_rows = arena.get("candidate_rows") or []
        arena_rows = arena_rows if isinstance(arena_rows, list) else []
        validated_assigned = 0
        for row in arena_rows:
            if not isinstance(row, dict) or not row.get("selected"):
                continue
            domain = self._cognitive_domain_for_operation(row.get("operation"))
            domains[domain]["validated_programs"] += 1
            validated_assigned += 1
        if validated_total and not validated_assigned:
            domains["Transformation Cognitive Domain"]["validated_programs"] = validated_total

        domain_rows = []
        for item in domains.values():
            semantic_count = len(item["semantic_concepts"])
            program_count = len(item["program_blueprints"])
            candidate_count = int(item["candidate_count"])
            arena_count = int(item["arena_candidate_count"])
            validated_count = int(item["validated_programs"])
            if program_count and not candidate_count:
                operationalization_gap = "candidate_generation_gap"
            elif candidate_count and not arena_count:
                operationalization_gap = "arena_entry_gap"
            elif arena_count and not validated_count:
                operationalization_gap = "validation_gap"
            elif len(item["executable_concepts"]) and not validated_count:
                operationalization_gap = "operational_validation_gap"
            else:
                operationalization_gap = "none"
            maturity_scores = [
                self._bounded_ratio(semantic_count, semantic_count),
                self._bounded_ratio(program_count, semantic_count),
                self._bounded_ratio(len(item["executable_concepts"]), semantic_count),
                self._bounded_ratio(candidate_count, max(program_count, 1)),
                self._bounded_ratio(arena_count, max(candidate_count, 1)),
                self._bounded_ratio(validated_count, max(semantic_count, 1)),
            ]
            measured = [score for score in maturity_scores if score is not None]
            readiness = round(sum(measured) / len(measured), 4) if measured else None
            domain_rows.append({
                "domain_name": item["domain_name"],
                "semantic_concept_count": semantic_count,
                "execution_package_count": len(item["executable_concepts"]),
                "program_blueprint_count": program_count,
                "candidate_count": candidate_count,
                "arena_candidate_count": arena_count,
                "validated_program_count": validated_count,
                "domain_operational_readiness": readiness,
                "domain_status": self._coverage_status(readiness),
                "operationalization_gap": operationalization_gap,
                "missing_execution_packages": sorted(item["missing_execution_packages"]),
                "missing_compiler_requirements": sorted(item["missing_compiler_requirements"]),
            })
        domain_rows.sort(
            key=lambda row: (
                -(row["semantic_concept_count"] or 0),
                row["domain_name"],
            )
        )
        active = [
            row for row in domain_rows
            if row["semantic_concept_count"]
            or row["program_blueprint_count"]
            or row["candidate_count"]
        ]
        operational = [
            row for row in active
            if row.get("domain_operational_readiness") is not None
            and row["domain_operational_readiness"] >= 0.70
        ]
        domain_operationalization_gaps = [
            row for row in active
            if row.get("operationalization_gap") not in {None, "none"}
        ]
        return {
            "domain_architecture_state": (
                "FOUNDATIONAL" if active else "NOT_MEASURABLE"
            ),
            "domain_count": len(active),
            "operational_domain_count": len(operational),
            "domain_rows": active,
            "domain_operationalization_gaps": sorted(
                domain_operationalization_gaps,
                key=lambda row: (
                    row.get("candidate_count") or 0,
                    row.get("arena_candidate_count") or 0,
                    row["domain_name"],
                ),
            )[:5],
            "lowest_readiness_domains": sorted(
                active,
                key=lambda row: (
                    row.get("domain_operational_readiness")
                    if row.get("domain_operational_readiness") is not None
                    else 999,
                    row["domain_name"],
                ),
            )[:5],
        }

    def _bootstrap_cognitive_knowledge_domains_from_architecture(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        coverage = self._cached_visibility(
            "cognitive_capability_coverage_report",
            lambda: self._build_cognitive_capability_coverage_visibility(
                report_state,
                performance,
            ),
        ).get("cognitive_capability_coverage_summary", {})
        architecture = coverage.get("cognitive_domain_architecture_summary") or {}
        architecture = architecture if isinstance(architecture, dict) else {}
        rows = architecture.get("domain_rows") or []
        rows = rows if isinstance(rows, list) else []
        domains = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            missing_packages = row.get("missing_execution_packages") or []
            missing_requirements = row.get("missing_compiler_requirements") or []
            missing = list(dict.fromkeys([
                *(missing_packages if isinstance(missing_packages, list) else [missing_packages]),
                *(missing_requirements if isinstance(missing_requirements, list) else [missing_requirements]),
            ]))
            domains.append({
                "domain_name": row.get("domain_name"),
                "semantic_families": [row.get("domain_name")],
                "mental_models": ["domain_runtime_bootstrap"],
                "program_blueprints": [
                    f"{row.get('domain_name')} blueprint"
                ] if row.get("program_blueprint_count") else [],
                "concept_count": row.get("semantic_concept_count"),
                "execution_package_count": row.get("execution_package_count"),
                "maturity_level": row.get("domain_status"),
                "lifecycle_status": (
                    "OPERATIONAL"
                    if row.get("domain_operational_readiness", 0) >= 0.70
                    else "FOUNDATIONAL"
                    if row.get("domain_operational_readiness") is not None
                    else "NOT_MEASURABLE"
                ),
                "operational_capabilities": (
                    ["candidate_generation", "arena_participation"]
                    if row.get("arena_candidate_count")
                    else []
                ),
                "missing_capabilities": [
                    item for item in missing
                    if item
                ],
                "domain_operational_readiness": row.get("domain_operational_readiness"),
                "candidate_count": row.get("candidate_count"),
                "arena_candidate_count": row.get("arena_candidate_count"),
                "validated_program_count": row.get("validated_program_count"),
                "bootstrap_source": "cognitive_capability_coverage",
            })
        return {
            "domain_count": len(domains),
            "domains": domains,
            "orphan_concepts": [],
            "invalid_family_assignments": [],
            "invalid_mental_model_assignments": [],
            "invalid_program_blueprint_assignments": [],
            "missing_domain_ownership": [
                domain.get("domain_name")
                for domain in domains
                if domain.get("lifecycle_status") != "OPERATIONAL"
            ],
            "validation_success": True,
            "silent_domain_assignment_failures": False,
            "domain_runtime_state": "BOOTSTRAPPED_FROM_CAPABILITY_COVERAGE",
        }

    def _bootstrap_cognitive_domain_lifecycle_from_architecture(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        domains_report = self._bootstrap_cognitive_knowledge_domains_from_architecture(
            report_state,
            performance,
        )
        domains = domains_report.get("domains") or []
        domains = domains if isinstance(domains, list) else []
        registry = []
        for domain in domains:
            if not isinstance(domain, dict):
                continue
            readiness = domain.get("domain_operational_readiness")
            readiness = readiness if isinstance(readiness, (int, float)) else None
            if readiness is not None and readiness >= 0.70:
                lifecycle_status = "OPERATIONAL"
            elif readiness is not None and readiness >= 0.40:
                lifecycle_status = "PARTIALLY_OPERATIONAL"
            else:
                lifecycle_status = "FOUNDATIONAL"
            registry.append({
                "domain_name": domain.get("domain_name"),
                "lifecycle_status": lifecycle_status,
                "maturity_level": domain.get("maturity_level"),
                "domain_operational_readiness": readiness,
                "operational_capabilities": domain.get("operational_capabilities", []),
                "missing_capabilities": domain.get("missing_capabilities", []),
                "concept_count": domain.get("concept_count"),
                "program_blueprint_count": len(domain.get("program_blueprints") or []),
                "candidate_count": domain.get("candidate_count"),
                "arena_candidate_count": domain.get("arena_candidate_count"),
                "validated_program_count": domain.get("validated_program_count"),
                "bootstrap_source": "cognitive_capability_coverage",
            })
        operational = [
            item for item in registry
            if item.get("lifecycle_status") == "OPERATIONAL"
        ]
        partial = [
            item for item in registry
            if item.get("lifecycle_status") == "PARTIALLY_OPERATIONAL"
        ]
        foundational = [
            item for item in registry
            if item.get("lifecycle_status") == "FOUNDATIONAL"
        ]
        return {
            "total_domains": len(registry),
            "domain_registry": registry,
            "operational_domains": len(operational),
            "partially_operational_domains": len(partial),
            "foundational_domains": len(foundational),
            "advanced_domains": len(operational),
            "domain_readiness_distribution": {
                "OPERATIONAL": len(operational),
                "PARTIALLY_OPERATIONAL": len(partial),
                "FOUNDATIONAL": len(foundational),
            },
            "lifecycle_distribution": {
                "OPERATIONAL": len(operational),
                "PARTIALLY_OPERATIONAL": len(partial),
                "FOUNDATIONAL": len(foundational),
            },
            "capability_distribution": {
                "domains_with_arena_participation": sum(
                    1 for item in registry if item.get("arena_candidate_count")
                ),
                "domains_with_validated_programs": sum(
                    1 for item in registry if item.get("validated_program_count")
                ),
            },
            "silent_domain_lifecycle_failures": False,
            "domain_runtime_state": "BOOTSTRAPPED_FROM_CAPABILITY_COVERAGE",
        }

    def _bootstrap_cognitive_domain_interaction_from_architecture(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        lifecycle = self._bootstrap_cognitive_domain_lifecycle_from_architecture(
            report_state,
            performance,
        )
        registry = lifecycle.get("domain_registry") or []
        registry = registry if isinstance(registry, list) else []
        by_domain = {
            str(row.get("domain_name")): row
            for row in registry
            if isinstance(row, dict) and row.get("domain_name")
        }
        specs = [
            {
                "composition_name": "Object Falling Simulation",
                "participating_domains": [
                    "Growth Cognitive Domain",
                    "Topology Cognitive Domain",
                    "Spatial Cognitive Domain",
                    "Transformation Cognitive Domain",
                ],
                "required_capabilities": [
                    "growth",
                    "topology",
                    "spatial_position",
                    "transformation",
                ],
            },
            {
                "composition_name": "Bridge Creation Capability",
                "participating_domains": [
                    "Topology Cognitive Domain",
                    "Spatial Cognitive Domain",
                    "Identity Cognitive Domain",
                ],
                "required_capabilities": [
                    "topology",
                    "spatial_position",
                    "identity_preservation",
                ],
            },
            {
                "composition_name": "Pattern Completion Capability",
                "participating_domains": [
                    "Transformation Cognitive Domain",
                    "Color Cognitive Domain",
                    "Spatial Cognitive Domain",
                    "Pattern Cognitive Domain",
                ],
                "required_capabilities": [
                    "transformation",
                    "color_mapping",
                    "spatial_position",
                    "pattern_completion",
                ],
            },
        ]
        interactions: list[dict[str, Any]] = []
        compositions: list[dict[str, Any]] = []
        reports: dict[str, dict[str, Any]] = {
            name: {
                "domain_name": name,
                "collaborating_domains": [],
                "shared_capabilities": [],
                "private_capabilities": [],
                "dependency_relationships": [],
                "optional_relationships": [],
                "capability_composition_status": "FOUNDATIONAL",
                "operational_capability_composition": [],
                "missing_collaborative_capabilities": [],
                "collaboration_maturity": "FOUNDATIONAL",
                "capability_sharing_maturity": "FOUNDATIONAL",
                "dependency_maturity": "FOUNDATIONAL",
                "operational_composition_maturity": "FOUNDATIONAL",
            }
            for name in by_domain
        }

        for spec in specs:
            domains = list(spec["participating_domains"])
            present = [domain for domain in domains if domain in by_domain]
            missing = [domain for domain in domains if domain not in by_domain]
            readiness_values = [
                max(
                    float(by_domain[domain].get("domain_operational_readiness") or 0.0),
                    0.25,
                )
                for domain in present
            ]
            readiness = round(
                sum(readiness_values) / max(len(domains), 1),
                4,
            )
            if not present:
                status = "BLOCKED"
            elif missing:
                status = "PARTIAL"
            elif readiness >= 0.70:
                status = "READY"
            elif readiness >= 0.40:
                status = "PARTIAL"
            else:
                status = "BLOCKED"
            blockers = []
            if missing:
                blockers.append("missing_required_domains")
            if readiness < 0.70:
                blockers.append("cross_domain_readiness_below_operational_threshold")
            composition = {
                "composition_name": spec["composition_name"],
                "participating_domains": domains,
                "present_domains": present,
                "missing_domains": missing,
                "required_capabilities": list(spec["required_capabilities"]),
                "missing_capabilities": missing,
                "composition_status": status,
                "cross_domain_operational_readiness": readiness,
                "composition_blockers": blockers,
                "composition_source": "cognitive_capability_composer_bootstrap",
            }
            compositions.append(composition)
            for source in present:
                report = reports.setdefault(source, {
                    "domain_name": source,
                    "collaborating_domains": [],
                    "shared_capabilities": [],
                    "private_capabilities": [],
                    "dependency_relationships": [],
                    "optional_relationships": [],
                    "capability_composition_status": "FOUNDATIONAL",
                    "operational_capability_composition": [],
                    "missing_collaborative_capabilities": [],
                    "collaboration_maturity": "FOUNDATIONAL",
                    "capability_sharing_maturity": "FOUNDATIONAL",
                    "dependency_maturity": "FOUNDATIONAL",
                    "operational_composition_maturity": "FOUNDATIONAL",
                })
                report["operational_capability_composition"].append(
                    spec["composition_name"]
                )
                report["missing_collaborative_capabilities"].extend(missing)
                for target in present:
                    if target == source:
                        continue
                    if target not in report["collaborating_domains"]:
                        report["collaborating_domains"].append(target)
                    if target not in report["dependency_relationships"]:
                        report["dependency_relationships"].append(target)
                    interactions.append({
                        "source_domain": source,
                        "target_domain": target,
                        "interaction_type": "COMPOSITION",
                        "shared_capabilities": list(spec["required_capabilities"]),
                        "required_capabilities": list(spec["required_capabilities"]),
                        "optional_capabilities": [],
                        "operational_constraints": blockers,
                        "interaction_status": (
                            "READY" if status == "READY" else "PARTIAL"
                            if status == "PARTIAL" else "BLOCKED"
                        ),
                        "composition_name": spec["composition_name"],
                    })

        for report in reports.values():
            compositions_for_domain = report["operational_capability_composition"]
            collaborators = report["collaborating_domains"]
            missing = report["missing_collaborative_capabilities"]
            report["collaboration_maturity"] = (
                "OPERATIONAL" if len(collaborators) >= 3 else
                "DEVELOPING" if len(collaborators) >= 2 else
                "PARTIAL" if collaborators else "FOUNDATIONAL"
            )
            report["capability_composition_status"] = (
                "COMPOSED" if compositions_for_domain else "FOUNDATIONAL"
            )
            report["operational_composition_maturity"] = (
                "ADVANCED" if len(compositions_for_domain) >= 2 else
                "DEVELOPING" if compositions_for_domain else "FOUNDATIONAL"
            )
            report["capability_sharing_maturity"] = (
                "DEVELOPING" if report["shared_capabilities"] else "FOUNDATIONAL"
            )
            report["dependency_maturity"] = (
                "DEVELOPING" if report["dependency_relationships"] else "FOUNDATIONAL"
            )
            report["missing_collaborative_capabilities"] = sorted(set(missing))

        readiness_rows = [
            {
                "composition_name": row["composition_name"],
                "participating_domains": row["participating_domains"],
                "cross_domain_operational_readiness": row[
                    "cross_domain_operational_readiness"
                ],
                "composition_status": row["composition_status"],
            }
            for row in compositions
        ]
        ready_count = sum(
            1 for row in compositions
            if row.get("composition_status") == "READY"
        )
        partial_count = sum(
            1 for row in compositions
            if row.get("composition_status") == "PARTIAL"
        )
        collaboration_score = round(
            sum(
                float(row.get("cross_domain_operational_readiness") or 0.0)
                for row in compositions
            ) / max(len(compositions), 1),
            4,
        )
        invalid_compositions = [
            row for row in compositions
            if row.get("composition_status") != "READY"
        ]
        return {
            "domain_interaction_count": len(interactions),
            "domain_interaction_reports": list(reports.values()),
            "domain_interactions": interactions,
            "dependency_graph": {
                name: row.get("dependency_relationships", [])
                for name, row in reports.items()
            },
            "operational_capability_compositions": compositions,
            "cross_domain_operational_readiness": readiness_rows,
            "collaboration_score": collaboration_score,
            "ready_composition_count": ready_count,
            "partial_composition_count": partial_count,
            "blocked_composition_count": len(invalid_compositions) - partial_count,
            "validation": {
                "invalid_domain_interactions": [
                    row for row in interactions
                    if row.get("interaction_status") == "BLOCKED"
                ],
                "circular_dependencies": [],
                "invalid_capability_composition": invalid_compositions,
                "prohibited_capability_sharing": [],
                "missing_shared_capabilities": invalid_compositions,
                "invalid_operational_constraints": [
                    row for row in interactions
                    if row.get("operational_constraints")
                ],
                "validation_success": not invalid_compositions,
            },
            "validation_success": not invalid_compositions,
            "silent_domain_interaction_failures": False,
            "composition_runtime_state": "BOOTSTRAPPED_COGNITIVE_CAPABILITY_COMPOSER",
        }

    def _augment_operational_capability_lifecycle(
        self,
        compositions: list[Any],
        domain_reports: list[Any],
    ) -> list[dict[str, Any]]:
        known_domains = {
            str(row.get("domain_name"))
            for row in domain_reports
            if isinstance(row, dict) and row.get("domain_name")
        }
        augmented: list[dict[str, Any]] = []
        for item in compositions:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            participating = row.get("participating_domains") or []
            participating = participating if isinstance(participating, list) else [participating]
            missing_domains = row.get("missing_domains") or []
            missing_domains = missing_domains if isinstance(missing_domains, list) else [missing_domains]
            normalized_missing = [
                domain for domain in missing_domains
                if str(domain) not in known_domains
                and self._canonical_cognitive_domain_name(domain) not in known_domains
            ]
            row["missing_domains"] = normalized_missing

            readiness = float(row.get("cross_domain_operational_readiness") or 0.0)
            status = str(row.get("composition_status") or "").upper()
            missing_capabilities = row.get("missing_capabilities") or []
            missing_capabilities = (
                missing_capabilities
                if isinstance(missing_capabilities, list)
                else [missing_capabilities]
            )
            blockers = row.get("composition_blockers") or []
            blockers = blockers if isinstance(blockers, list) else [blockers]

            stage_checks = [
                ("CAPABILITY_IDENTIFIED", bool(row.get("composition_name"))),
                ("REQUIRED_DOMAINS_IDENTIFIED", bool(participating)),
                ("REQUIRED_PROGRAMS_IDENTIFIED", bool(row.get("required_capabilities"))),
                (
                    "REQUIRED_EXECUTION_PACKAGES_IDENTIFIED",
                    not normalized_missing and not missing_capabilities,
                ),
                (
                    "CROSS_DOMAIN_COMPOSITION_READY",
                    status == "READY" or readiness >= 0.70,
                ),
                (
                    "CANDIDATE_COMPOSITION_READY",
                    status == "READY" or readiness >= 0.60,
                ),
                (
                    "ARENA_PARTICIPATION_READY",
                    status == "READY" and not blockers,
                ),
                ("VALIDATION_READY", status == "READY"),
                ("OPERATIONAL_READY", status == "READY"),
                ("REUSABLE_CAPABILITY", False),
                ("CAPABILITY_EVOLUTION_READY", False),
            ]
            completed = [name for name, passed in stage_checks if passed]
            blocking_stage = next(
                (name for name, passed in stage_checks if not passed),
                "NONE",
            )
            if status == "READY":
                lifecycle_state = "OPERATIONAL_READY"
                governance_status = "GOVERNANCE_READY"
                validation_status = "VALIDATION_READY"
                evolution_state = "REUSE_CANDIDATE"
            elif status == "BLOCKED":
                lifecycle_state = "COMPOSITION_BLOCKED"
                governance_status = "GOVERNANCE_BLOCKED"
                validation_status = "VALIDATION_BLOCKED"
                evolution_state = "EVOLUTION_BLOCKED"
            else:
                lifecycle_state = "COMPOSITION_PARTIAL"
                governance_status = "GOVERNANCE_REVIEW_REQUIRED"
                validation_status = "VALIDATION_PENDING"
                evolution_state = "REUSABILITY_NOT_ESTABLISHED"
            row.update({
                "lifecycle_state": lifecycle_state,
                "operational_readiness": readiness,
                "governance_status": governance_status,
                "validation_status": validation_status,
                "blocking_stage": blocking_stage,
                "completed_lifecycle_stages": completed,
                "required_domains": participating,
                "required_programs": row.get("required_capabilities", []),
                "required_execution_packages": row.get("required_capabilities", []),
                "arena_participation": (
                    "READY" if "ARENA_PARTICIPATION_READY" in completed else "NOT_READY"
                ),
                "confidence": readiness,
                "maturity": self._coverage_status(readiness),
                "evolution_state": evolution_state,
            })
            self._apply_capability_promotion_state(row)
            self._apply_capability_growth_state(row)
            self._apply_capability_economy_state(row)
            augmented.append(row)
        return augmented

    def _apply_capability_promotion_state(self, row: dict[str, Any]) -> None:
        readiness = float(row.get("operational_readiness") or 0.0)
        lifecycle_state = str(row.get("lifecycle_state") or "")
        governance_status = str(row.get("governance_status") or "")
        validation_status = str(row.get("validation_status") or "")
        arena_ready = row.get("arena_participation") == "READY"
        blockers = [
            item for item in row.get("composition_blockers", [])
            if item
        ]
        promotion_score = round(
            (
                readiness
                + (1.0 if lifecycle_state == "OPERATIONAL_READY" else 0.5 if lifecycle_state == "COMPOSITION_PARTIAL" else 0.0)
                + (1.0 if governance_status == "GOVERNANCE_READY" else 0.5 if governance_status == "GOVERNANCE_REVIEW_REQUIRED" else 0.0)
                + (1.0 if validation_status == "VALIDATION_READY" else 0.5 if validation_status == "VALIDATION_PENDING" else 0.0)
                + (1.0 if arena_ready else 0.0)
            ) / 5.0,
            4,
        )
        if (
            lifecycle_state == "OPERATIONAL_READY"
            and governance_status == "GOVERNANCE_READY"
            and validation_status == "VALIDATION_READY"
            and arena_ready
            and promotion_score >= 0.85
        ):
            promotion_state = "SANDBOX_OPERATIONAL"
            registry_eligibility = "PROMOTION_CANDIDATE"
            promotion_blockers: list[str] = []
        elif promotion_score >= 0.70 and governance_status != "GOVERNANCE_BLOCKED":
            promotion_state = "PROMOTION_CANDIDATE"
            registry_eligibility = "REVIEW_REQUIRED"
            promotion_blockers = [
                "sandbox_validation_required",
                "registry_contract_missing",
            ]
        else:
            promotion_state = "NOT_PROMOTABLE"
            registry_eligibility = "NOT_ELIGIBLE"
            promotion_blockers = list(blockers)
            if readiness < 0.70:
                promotion_blockers.append("operational_readiness_below_promotion_threshold")
            if governance_status != "GOVERNANCE_READY":
                promotion_blockers.append("governance_review_required")
            if validation_status != "VALIDATION_READY":
                promotion_blockers.append("validation_not_ready")
            if not arena_ready:
                promotion_blockers.append("arena_participation_not_ready")
        row.update({
            "promotion_state": promotion_state,
            "promotion_score": promotion_score,
            "registry_eligibility": registry_eligibility,
            "promotion_blockers": list(dict.fromkeys(promotion_blockers)),
            "operational_registry_entry": {
                "capability_name": row.get("composition_name"),
                "required_domains": row.get("required_domains", []),
                "required_programs": row.get("required_programs", []),
                "required_packages": row.get("required_execution_packages", []),
                "required_validators": ["cross_domain_validation", "governance_review"],
                "reusable_by": [
                    "domain_runtime",
                    "candidate_arena",
                    "adaptive_capability_evolution",
                ],
                "registry_state": registry_eligibility,
            },
        })

    def _apply_capability_growth_state(self, row: dict[str, Any]) -> None:
        readiness = float(row.get("operational_readiness") or 0.0)
        promotion_score = float(row.get("promotion_score") or 0.0)
        lifecycle_stages = row.get("completed_lifecycle_stages") or []
        lifecycle_stages = (
            lifecycle_stages if isinstance(lifecycle_stages, list) else [lifecycle_stages]
        )
        stage_coverage = self._bounded_ratio(len(lifecycle_stages), 11) or 0.0
        growth_score = round(
            (
                readiness
                + promotion_score
                + stage_coverage
            ) / 3.0,
            4,
        )
        if row.get("registry_eligibility") == "REUSABLE_OPERATIONAL_CAPABILITY":
            growth_stage = "REUSABLE"
        elif row.get("promotion_state") == "PROMOTED":
            growth_stage = "PROMOTED"
        elif row.get("promotion_state") == "SANDBOX_OPERATIONAL":
            growth_stage = "SANDBOX_OPERATIONAL"
        elif growth_score >= 0.70:
            growth_stage = "DEVELOPING"
        elif growth_score >= 0.35:
            growth_stage = "EMERGING"
        else:
            growth_stage = "INFANT"
        if growth_stage in {"REUSABLE", "PROMOTED", "SANDBOX_OPERATIONAL"}:
            organism_state = "OPERATIONAL_ORGANISM"
        elif growth_stage in {"DEVELOPING", "EMERGING"}:
            organism_state = "ACTIVE_GROWTH"
        else:
            organism_state = "SEED_CAPABILITY"
        name = str(row.get("composition_name") or "capability")
        capability_id = self._capability_identity_slug(name)
        row.update({
            "growth_stage": growth_stage,
            "growth_score": growth_score,
            "organism_state": organism_state,
            "evolution_readiness": round(
                (growth_score + promotion_score) / 2.0,
                4,
            ),
            "growth_blockers": row.get("promotion_blockers", []),
            "capability_identity": {
                "capability_id": capability_id,
                "capability_name": name,
                "version": "0.1",
                "identity_state": "EMERGENT_COGNITIVE_CAPABILITY",
                "lineage_source": row.get("composition_source"),
            },
            "capability_relationships": {
                "domains": row.get("required_domains", []),
                "dependencies": row.get("required_programs", []),
                "derived_capabilities": [],
                "composable_with": [],
            },
            "capability_history": {
                "validated_tasks": 0,
                "success_rate": None,
                "evolution_events": 0,
                "promotion_history": [],
                "reuse_count": 0,
            },
        })

    def _apply_capability_economy_state(self, row: dict[str, Any]) -> None:
        readiness = float(row.get("operational_readiness") or 0.0)
        growth_score = float(row.get("growth_score") or 0.0)
        promotion_score = float(row.get("promotion_score") or 0.0)
        domains = row.get("required_domains") or []
        domains = domains if isinstance(domains, list) else [domains]
        blockers = row.get("promotion_blockers") or []
        blockers = blockers if isinstance(blockers, list) else [blockers]
        task_coverage = self._bounded_ratio(len(domains), 8) or 0.0
        reuse_score = 0.0
        name = str(row.get("composition_name") or "").lower()
        if "pattern" in name:
            reuse_score = 0.75
        elif "bridge" in name:
            reuse_score = 0.55
        elif "falling" in name:
            reuse_score = 0.35
        learning_gain = round((growth_score + readiness) / 2.0, 4)
        future_potential = round(
            (task_coverage + reuse_score + learning_gain) / 3.0,
            4,
        )
        evolution_cost = round(
            min(1.0, 0.25 + 0.12 * len(domains) + 0.06 * len(blockers)),
            4,
        )
        maintenance_cost = round(
            min(1.0, 0.20 + 0.08 * len(domains) + 0.04 * len(blockers)),
            4,
        )
        operational_benefit = round(
            (
                readiness
                + task_coverage
                + reuse_score
                + future_potential
            ) / 4.0,
            4,
        )
        value_score = round(
            (
                operational_benefit
                + learning_gain
                + future_potential
            ) / 3.0,
            4,
        )
        total_cost = round((evolution_cost + maintenance_cost) / 2.0, 4)
        net_value = round(value_score - total_cost, 4)
        if promotion_score >= 0.70 and net_value >= 0.10:
            resource_decision = "INVEST"
        elif growth_score >= 0.35 and future_potential >= 0.35:
            resource_decision = "WATCH"
        elif growth_score < 0.20 and net_value < -0.20:
            resource_decision = "ARCHIVE"
        else:
            resource_decision = "HOLD"
        resource_budget = {
            "growth_budget": (
                "MEDIUM" if resource_decision == "INVEST" else
                "LOW" if resource_decision == "WATCH" else
                "MINIMAL"
            ),
            "evolution_budget": (
                "MEDIUM" if resource_decision == "INVEST" else
                "LOW" if resource_decision == "WATCH" else
                "NONE"
            ),
            "promotion_budget": (
                "LOW" if resource_decision == "INVEST" else "NONE"
            ),
            "maintenance_budget": (
                "LOW" if resource_decision in {"INVEST", "WATCH", "HOLD"} else "NONE"
            ),
            "retirement_budget": (
                "LOW" if resource_decision == "ARCHIVE" else "NONE"
            ),
        }
        if resource_decision == "INVEST":
            economy_rationale = "high_promotion_potential_and_positive_net_value"
        elif resource_decision == "WATCH":
            economy_rationale = "emerging_growth_with_future_potential"
        elif resource_decision == "ARCHIVE":
            economy_rationale = "low_growth_and_negative_economic_value"
        else:
            economy_rationale = "insufficient_value_for_active_investment"
        row.update({
            "value_score": value_score,
            "usage_score": reuse_score,
            "task_coverage": task_coverage,
            "learning_gain": learning_gain,
            "future_potential": future_potential,
            "evolution_cost": evolution_cost,
            "maintenance_cost": maintenance_cost,
            "operational_benefit": operational_benefit,
            "net_economic_value": net_value,
            "resource_decision": resource_decision,
            "resource_budget": resource_budget,
            "economy_rationale": economy_rationale,
        })

    def _capability_identity_slug(self, name: str) -> str:
        token = str(name or "capability").lower()
        pieces: list[str] = []
        current: list[str] = []
        for char in token:
            if char.isalnum():
                current.append(char)
            elif current:
                pieces.append("".join(current))
                current = []
        if current:
            pieces.append("".join(current))
        return "_".join(pieces) or "capability"

    def _canonical_cognitive_domain_name(self, name: Any) -> str:
        value = str(name or "").strip()
        if value.endswith(" Cognitive Domain"):
            return value
        aliases = {
            "Growth Domain": "Growth Cognitive Domain",
            "Spatial Domain": "Spatial Cognitive Domain",
            "Topology Domain": "Topology Cognitive Domain",
            "Transformation Domain": "Transformation Cognitive Domain",
            "Identity Domain": "Identity Cognitive Domain",
            "Geometry Domain": "Geometry Cognitive Domain",
            "Color Domain": "Color Cognitive Domain",
            "Pattern Completion Domain": "Pattern Cognitive Domain",
            "Pattern Domain": "Pattern Cognitive Domain",
        }
        return aliases.get(value, value)

    def _cognitive_domain_for_operation(self, operation: Any) -> str:
        token = str(operation or "").lower().replace("-", "_").replace(" ", "_")
        if token in {"duplicate_object", "scale"}:
            return "Growth Cognitive Domain"
        if token in {"translate", "construct_path"}:
            return "Spatial Cognitive Domain"
        if token in {"connect_components"}:
            return "Topology Cognitive Domain"
        if token in {"preserve_grid"}:
            return "Identity Cognitive Domain"
        if token in {"rotate", "reflect", "mirror_horizontal"}:
            return "Geometry Cognitive Domain"
        if token in {"replace_color", "recolor"}:
            return "Color Cognitive Domain"
        return "Transformation Cognitive Domain"

    def _cognitive_domain_label(self, domain: Any) -> str:
        label = str(domain or "").strip()
        if not label:
            return "Unknown"
        for suffix in (" Cognitive Domain", " Domain"):
            if label.endswith(suffix):
                label = label[: -len(suffix)]
        return label.strip().title()

    def _cognitive_domain_for_concept(self, concept: str) -> str:
        token = str(concept or "").lower().replace("-", "_").replace(" ", "_")
        if any(part in token for part in ("growth", "density", "propagation", "replication")):
            return "Growth Cognitive Domain"
        if any(part in token for part in ("spatial", "position", "motion", "direction", "path", "route")):
            return "Spatial Cognitive Domain"
        if any(part in token for part in ("topology", "connectivity", "component", "bridge", "hole")):
            return "Topology Cognitive Domain"
        if any(part in token for part in ("identity", "preservation", "shape", "size")):
            return "Identity Cognitive Domain"
        if any(part in token for part in ("symmetry", "rotation", "reflection", "geometry", "orientation")):
            return "Geometry Cognitive Domain"
        if any(part in token for part in ("color", "symbolic")):
            return "Color Cognitive Domain"
        return "Transformation Cognitive Domain"

    def _bounded_ratio(self, numerator: Any, denominator: Any) -> float | None:
        try:
            denominator_value = float(denominator)
            if denominator_value <= 0:
                return None
            ratio = float(numerator or 0) / denominator_value
            return round(max(0.0, min(1.0, ratio)), 4)
        except (TypeError, ValueError):
            return None

    def _candidate_source_lineage(
        self,
        proposal: dict[str, Any],
        arena: dict[str, Any],
    ) -> list[dict[str, Any]]:
        proposals = proposal.get("candidate_proposals") or []
        proposals = proposals if isinstance(proposals, list) else []
        arena_rows = arena.get("candidate_rows") or []
        arena_rows = arena_rows if isinstance(arena_rows, list) else []
        rows: list[dict[str, Any]] = []
        for item in proposals[:12]:
            if not isinstance(item, dict):
                continue
            raw_source = item.get("source")
            operation = item.get("operation")
            match = next(
                (
                    row for row in arena_rows
                    if isinstance(row, dict)
                    and (
                        row.get("operation") == operation
                        or row.get("candidate_id") == item.get("proposal_id")
                    )
                ),
                {},
            )
            rows.append({
                "raw_source": raw_source,
                "candidate_adapter": "candidate_proposal_runtime",
                "normalized_source": match.get("source") or raw_source,
                "arena_source": (
                    match.get("source")
                    or (
                        raw_source
                        if raw_source in (arena.get("competitor_sources") or [])
                        else None
                    )
                ),
                "proposal_status": item.get("proposal_status"),
                "operation": operation or match.get("operation"),
                "entered_arena": bool(match.get("entered_arena")),
            })
        if not rows and arena_rows:
            for row in arena_rows[:12]:
                if not isinstance(row, dict):
                    continue
                rows.append({
                    "raw_source": row.get("source"),
                    "candidate_adapter": "arena_observation",
                    "normalized_source": row.get("source"),
                    "arena_source": row.get("source"),
                    "proposal_status": "OBSERVED",
                    "operation": row.get("operation"),
                    "entered_arena": bool(row.get("entered_arena")),
                })
        return rows

    def _semantic_concepts_for_coverage(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
        synthesis: dict[str, Any],
        compiler: dict[str, Any],
    ) -> list[str]:
        concepts: list[str] = []

        def add(value: Any) -> None:
            if not isinstance(value, str):
                return
            token = value.strip().lower().replace("-", "_").replace(" ", "_")
            if token:
                concepts.append(token)

        def visit(value: Any) -> None:
            if isinstance(value, str):
                add(value)
            elif isinstance(value, dict):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "attributed_concepts",
                        "semantic_concepts",
                        "target_concepts",
                        "detected_intents",
                        "routed_concepts",
                    }:
                        visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for source in (
            synthesis.get("detected_concepts"),
            compiler.get("detected_intents"),
            report_state.get("detected_concepts"),
            report_state.get("attributed_concepts"),
            report_state.get("semantic_concepts"),
            report_state.get("target_concepts"),
            performance.get("detected_concepts"),
            performance.get("attributed_concepts"),
        ):
            visit(source)
        return list(dict.fromkeys(concepts))

    def _cognitive_lifecycle_concepts(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> list[str]:
        concepts: list[str] = []

        def add(value: Any) -> None:
            if not isinstance(value, str):
                return
            token = value.strip().lower().replace("-", "_").replace(" ", "_")
            if token:
                concepts.append(token)

        def visit(value: Any) -> None:
            if isinstance(value, str):
                add(value)
                return
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "attributed_concepts",
                        "semantic_concepts",
                        "generated_concepts",
                        "target_concepts",
                        "matched_concepts",
                        "routed_concepts",
                    }:
                        visit(item)
                    elif key in {
                        "concept_birth",
                        "concept_validation",
                        "concept_revival",
                        "concept_reputation_engine",
                        "registry",
                        "promotion_report",
                        "truth_candidate_promotion",
                    }:
                        visit(item)
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for container in (
            self._first_dict(report_state, "concept_lifecycle_report", "CONCEPT_LIFECYCLE_REPORT"),
            self._first_dict(performance, "concept_lifecycle_report", "CONCEPT_LIFECYCLE_REPORT"),
            self._first_dict(report_state, "semantic_attribution_report", "SEMANTIC_ATTRIBUTION_REPORT"),
            self._first_dict(performance, "semantic_attribution_report", "SEMANTIC_ATTRIBUTION_REPORT"),
            self._first_dict(report_state, "truth_candidate_report", "truth_candidate_engine_report"),
            self._first_dict(performance, "truth_candidate_report", "truth_candidate_engine_report"),
        ):
            visit(container)

        return list(dict.fromkeys(concepts))

    def _executable_semantic_support_map(self) -> dict[str, str]:
        support = {}
        for concept in (
            "rotation",
            "rotation_reflection",
            "orientation_change",
        ):
            support[concept] = "rotate"
        for concept in (
            "reflection",
            "symmetry_creation",
        ):
            support[concept] = "reflect"
        for concept in (
            "path_finding",
            "route_completion",
            "reachability",
            "path_construction",
        ):
            support[concept] = "construct_path"
        for concept in (
            "bridge_creation",
            "component_connection",
            "connectivity_change",
        ):
            support[concept] = "connect_components"
        for concept in (
            "hole_removal",
            "topology_repair",
            "connectivity_restoration",
            "topology_change",
        ):
            support[concept] = "construct_path"
        for concept in (
            "scaling",
            "scale_transformation",
            "size_transformation",
            "density_increase",
        ):
            support[concept] = "scale"
        for concept in (
            "noise_removal",
            "artifact_filtering",
            "object_removal",
            "color_elimination",
        ):
            support[concept] = "remove_object"
        for concept in (
            "color_mapping",
            "symbolic_remapping",
        ):
            support[concept] = "recolor"
        preservation_support = {
            "color_preservation": "preserve_colors",
            "topology_preservation": "preserve_topology",
            "shape_preservation": "preserve_shape",
            "size_preservation": "preserve_size",
            "density_preservation": "preserve_density",
            "symmetry_preservation": "preserve_symmetry",
            "symmetry_reasoning": "preserve_symmetry",
        }
        support.update(preservation_support)
        for concept in (
            "growth",
            "topological_growth",
            "propagation",
            "replication",
            "duplication",
            "object_creation",
        ):
            support[concept] = "duplicate_object"
        for concept in (
            "directional_motion",
            "object_translation",
        ):
            support[concept] = "translate"
        for concept in (
            "object_identity_preservation",
            "position_preservation",
        ):
            support[concept] = "preserve_grid"
        return support

    def _semantic_cluster(self, concept: str) -> str:
        if any(token in concept for token in ("topology", "connectivity", "bridge", "component", "hole")):
            return "Topology Transformations"
        if any(token in concept for token in ("position", "spatial", "relative", "direction", "motion")):
            return "Spatial And Motion"
        if any(token in concept for token in ("density", "growth", "propagation")):
            return "Density And Growth"
        if any(token in concept for token in ("symmetry", "reflection", "rotation", "orientation")):
            return "Symmetry And Geometry"
        if any(token in concept for token in ("color", "symbolic")):
            return "Symbolic And Color"
        if "preservation" in concept or "identity" in concept:
            return "Preservation And Identity"
        return "Other"

    def _coverage_status(self, coverage: float | None) -> str:
        if coverage is None:
            return "NOT_MEASURABLE"
        if coverage >= 0.70:
            return "HIGH"
        if coverage >= 0.40:
            return "MEDIUM"
        return "LOW"

    def _tool_selected(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
        tool_name: str,
    ) -> bool:
        selected: set[str] = set()

        def visit(value: Any) -> None:
            if isinstance(value, str):
                selected.add(value)
                return
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {"enabled_tools", "selected_tools", "tools"}:
                        visit(item)
                    elif key == "tool_selection_report" and isinstance(item, dict):
                        visit(item)
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        visit(report_state.get("enabled_tools"))
        visit(report_state.get("selected_tools"))
        visit(report_state.get("tool_selection_report"))
        visit(performance.get("enabled_tools"))
        visit(performance.get("selected_tools"))
        visit(performance.get("tool_selection_report"))
        return tool_name in selected

    def _build_report_state_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        visible = {
            key: self._bounded_copy(value, max_depth=2, max_list_items=20)
            for key, value in report_state.items()
            if not isinstance(value, (dict, list, tuple, set))
            or key in {
                "multi_task_results",
                "evaluation_metrics",
                "training_summary",
            }
        }
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
        task_results = visible.get("multi_task_results")
        if not isinstance(task_results, list):
            task_results = []
        total_executions = self._first_number(
            visible.get("total_executions"),
            visible.get("executions_total"),
            visible.get("tasks_executed"),
            performance.get("total_executions"),
            performance.get("tasks_executed"),
            len(task_results) if task_results else None,
        )
        completed_executions = self._first_number(
            visible.get("completed_executions"),
            visible.get("successful_tasks"),
            performance.get("completed_executions"),
            performance.get("successful_tasks"),
            self._count_completed_tasks(task_results) if task_results else None,
        )
        execution_coverage = self._first_number(
            visible.get("execution_coverage"),
            performance.get("execution_coverage"),
        )
        if generated_concepts is not None:
            visible.setdefault("generated_concepts", generated_concepts)
            visible.setdefault("concept_count", generated_concepts)
        if generated_programs is None:
            generated_programs = 0
        visible.setdefault("generated_programs", generated_programs)
        visible.setdefault("program_candidates", generated_programs)
        visible.setdefault("candidate_count", generated_programs)
        if total_executions is not None:
            visible.setdefault("total_executions", total_executions)
            visible.setdefault("executions_total", total_executions)
            visible.setdefault("tasks_executed", total_executions)
        if completed_executions is not None:
            visible.setdefault("completed_executions", completed_executions)
            visible.setdefault("successful_tasks", completed_executions)
        if execution_coverage is None and total_executions:
            execution_coverage = (completed_executions or 0) / total_executions
        if execution_coverage is not None:
            visible.setdefault("execution_coverage", execution_coverage)
        if not visible.get("runtime_status") and not visible.get("status"):
            visible["runtime_status"] = (
                "COMPLETED"
                if total_executions is not None
                and completed_executions == total_executions
                else "UNKNOWN"
            )
        return visible

    def _count_completed_tasks(self, task_results: list[Any]) -> int:
        completed = 0
        for item in task_results:
            if not isinstance(item, dict):
                continue
            status = str(
                item.get("status")
                or item.get("evaluation_result")
                or item.get("result")
                or ""
            ).upper()
            if item.get("success") is True or status in {
                "COMPLETED",
                "CORRECT",
                "PASS",
                "PASSED",
                "SUCCESS",
            }:
                completed += 1
        return completed

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
        compiler_attempted = bool(
            semantic.get("compiler_triggered")
            or semantic.get("compiler_selected")
            or semantic.get("execution_intent_count")
            or semantic.get("compiled_candidate_count")
            or semantic.get("compilation_status") in {
                "SUCCESS",
                "NO_MATCHING_COMPILER_RULE",
                "REQUIRED_REPORT_MISSING",
            }
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
            compiler_attempted,
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
            "compiler_attempted": compiler_attempted,
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
        compiler_attempted: bool,
        compiler_participation: bool,
        transfer_participation: bool,
        repair_participation: bool,
        counterfactual_participation: bool,
        has_selected_program: bool,
    ) -> list[str]:
        pipeline = ["Semantic Attribution", "Pattern Analysis", "Rule Analysis"]
        if compiler_attempted:
            pipeline.append("Semantic Compilation")
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
        provenance = self._cached_visibility(
            "prediction_provenance_report",
            lambda: self._build_prediction_provenance_visibility(report_state, performance),
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
        explicit_summary = self._first_dict(explicit, "candidate_arena_summary")
        if not explicit_summary and explicit.get("arena_state"):
            explicit_summary = explicit
        if explicit_summary and explicit_summary.get("selection_mode") == "EVIDENCE_BASED_ARENA":
            rows = self._first_list(explicit_summary, "candidate_summary", "candidate_rows")
            selection_state = explicit_summary.get("selection_state")
            selection_margin = self._first_number(
                explicit_summary.get("selection_margin"),
                0.0,
            )
            summary = {
                "arena_state": explicit_summary.get("arena_state"),
                "candidate_count": explicit_summary.get("candidate_count"),
                "attempted_candidate_count": explicit_summary.get("unique_candidate_count", explicit_summary.get("candidate_count")),
                "explicit_rejection_count": explicit_summary.get("governance_blocked_count", 0),
                "competitor_sources": explicit_summary.get("sources_entered") or [],
                "winner_source": explicit_summary.get("winner_source"),
                "arena_winner": explicit_summary.get("winner_candidate_id"),
                "winner_takes_all_detected": bool(
                    explicit_summary.get("source_dominance_detected")
                    and selection_state in {
                        "WINNER_SELECTED",
                        "CONDITIONAL_WINNER",
                        "SANDBOX_ONLY_WINNER",
                    }
                    and float(selection_margin or 0.0) > 0.0
                ),
                "dominance_source": explicit_summary.get("dominance_source"),
                "selection_mode": explicit_summary.get("selection_mode"),
                "validation_coverage": explicit_summary.get("validation_coverage"),
                "candidate_rows": rows,
                "rejected_candidate_rows": [
                    row for row in rows
                    if isinstance(row, dict) and str(row.get("status", "")).startswith(("BLOCKED", "REJECTED"))
                ],
                "source_outcomes": [
                    {
                        "source": row.get("source"),
                        "candidate_id": row.get("candidate_id"),
                        "operation": row.get("operation"),
                        "entered_arena": row.get("entered_arena"),
                        "status": row.get("status"),
                        "reason": row.get("blocked_reason"),
                    }
                    for row in rows
                    if isinstance(row, dict)
                ],
                "source_status": {
                    source: "ENTERED"
                    for source in explicit_summary.get("sources_entered", []) or []
                },
                "missing_competition_reason": explicit_summary.get("no_competition_reason"),
                "unique_candidate_count": explicit_summary.get("unique_candidate_count"),
                "source_count": explicit_summary.get("source_count"),
                "cross_source_consensus_count": explicit_summary.get(
                    "cross_source_consensus_count",
                    0,
                ),
                "cross_source_consensus_state": explicit_summary.get(
                    "cross_source_consensus_state"
                ),
                "cross_source_consensus_groups": explicit_summary.get(
                    "cross_source_consensus_groups"
                ) or [],
                "competition_diversity": explicit_summary.get("competition_diversity"),
                "operational_diversity": explicit_summary.get("operational_diversity"),
                "source_diversity": explicit_summary.get("source_diversity"),
                "arena_source_diversity_state": explicit_summary.get(
                    "arena_source_diversity_state"
                ),
                "arena_source_diversity_action": explicit_summary.get(
                    "arena_source_diversity_action"
                ),
                "target_candidate_sources": explicit_summary.get(
                    "target_candidate_sources"
                ) or [],
                "missing_candidate_sources": explicit_summary.get(
                    "missing_candidate_sources"
                ) or [],
                "simulation_count": explicit_summary.get("simulation_count"),
                "simulation_success_count": explicit_summary.get("simulation_success_count"),
                "governance_blocked_count": explicit_summary.get("governance_blocked_count"),
                "winner_operation": explicit_summary.get("winner_operation"),
                "winner_score": explicit_summary.get("winner_score"),
                "second_best_score": explicit_summary.get("second_best_score"),
                "selection_margin": selection_margin,
                "selection_state": selection_state,
                "source_dominance_detected": explicit_summary.get("source_dominance_detected"),
                "selection_explanation": explicit_summary.get("selection_explanation"),
            }
            return {
                "candidate_arena_summary": summary,
                "candidate_arena_diagnostics": {
                    "explicit_arena_report": explicit,
                    "all_candidates": rows,
                    "source_status": summary["source_status"],
                },
                **summary,
            }
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
        rejected = [candidate for candidate in candidates if not candidate.get("entered_arena")]
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
        if any(
            candidate.get("source") == "semantic_to_transformation_compiler"
            for candidate in rejected
        ):
            source_status["semantic_to_transformation_compiler"] = "BLOCKED"
        arena_state = (
            "COMPETITIVE"
            if len(sources) > 1
            else "SINGLE_SOURCE_DOMINANCE"
            if participants
            else "EMPTY"
        )
        source_outcomes = [
            {
                "source": candidate.get("source"),
                "candidate_id": candidate.get("candidate_id"),
                "operation": candidate.get("operation"),
                "entered_arena": bool(candidate.get("entered_arena")),
                "status": (
                    "ENTERED"
                    if candidate.get("entered_arena")
                    else "REJECTED"
                ),
                "reason": candidate.get("blocked_reason"),
            }
            for candidate in candidates
        ]
        summary = {
            "arena_state": explicit.get("arena_state") or arena_state,
            "candidate_count": len(participants),
            "attempted_candidate_count": len(candidates),
            "explicit_rejection_count": len(rejected),
            "competitor_sources": sources,
            "source_count": len(sources),
            "operational_diversity": round(
                len({candidate.get("operation") for candidate in participants if candidate.get("operation")})
                / max(len(participants), 1),
                4,
            ) if participants else 0.0,
            "source_diversity": round(len(sources) / max(len(participants), 1), 4)
            if participants else 0.0,
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
            "rejected_candidate_rows": rejected,
            "source_outcomes": source_outcomes,
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

    def _build_candidate_proposal_visibility(
        self,
        report_state: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        synthesis = self._merge_dicts(
            self._first_dict(report_state, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
            self._first_dict(performance, "TRANSFORMATION_SYNTHESIS_REPORT", "transformation_synthesis_report"),
        )
        explicit = self._merge_dicts(
            self._first_dict(report_state, "CANDIDATE_PROPOSAL_REPORT", "candidate_proposal_report"),
            self._first_dict(performance, "CANDIDATE_PROPOSAL_REPORT", "candidate_proposal_report"),
            self._first_dict(synthesis, "candidate_proposal_report"),
        )
        if explicit:
            proposals = self._first_list(explicit, "candidate_proposals")
            proposal_count = self._first_number(
                explicit.get("proposal_count"),
                len([row for row in proposals if isinstance(row, dict) and row.get("proposal_status") == "PROPOSED"]),
            )
            rejection_count = self._first_number(
                explicit.get("explicit_rejection_count"),
                len([row for row in proposals if isinstance(row, dict) and row.get("proposal_status") == "REJECTED"]),
            )
            summary = {
                "proposal_phase_entered": bool(explicit.get("proposal_phase_entered", True)),
                "proposal_phase_status": explicit.get("proposal_phase_status"),
                "eligible_source_count": explicit.get("eligible_source_count"),
                "proposal_count": proposal_count,
                "explicit_rejection_count": rejection_count,
                "sources_with_proposals": explicit.get("sources_with_proposals") or [],
                "sources_rejected": explicit.get("sources_rejected") or [],
                "knowledge_investment_policy": explicit.get("knowledge_investment_policy"),
                "knowledge_investment_authority": explicit.get(
                    "knowledge_investment_authority"
                ),
                "high_value_knowledge_items": explicit.get(
                    "high_value_knowledge_items"
                ),
                "medium_value_knowledge_items": explicit.get(
                    "medium_value_knowledge_items"
                ),
                "low_value_knowledge_items": explicit.get(
                    "low_value_knowledge_items"
                ),
                "deprioritized_knowledge_items": explicit.get(
                    "deprioritized_knowledge_items"
                ),
                "candidate_proposals": proposals,
                "source_diagnostics": explicit.get("source_diagnostics") or {},
                "adaptive_reuse_admission_trace": explicit.get(
                    "adaptive_reuse_admission_trace"
                ) or [],
            }
        else:
            arena = self._build_candidate_arena_visibility(report_state, performance).get(
                "candidate_arena_summary",
                {},
            )
            outcomes = arena.get("source_outcomes") or []
            proposals = [
                {
                    "source": row.get("source"),
                    "proposal_id": row.get("candidate_id"),
                    "proposal_status": "PROPOSED" if row.get("entered_arena") else "REJECTED",
                    "operation": None,
                    "candidate_available": bool(row.get("entered_arena")),
                    "rejection_reason": row.get("reason"),
                }
                for row in outcomes
                if isinstance(row, dict)
            ]
            summary = {
                "proposal_phase_entered": bool(proposals),
                "proposal_phase_status": (
                    "COMPETITIVE"
                    if len(arena.get("competitor_sources") or []) > 1
                    else "SINGLE_SOURCE"
                    if arena.get("competitor_sources")
                    else "EMPTY"
                ),
                "eligible_source_count": len(proposals),
                "proposal_count": arena.get("candidate_count", 0),
                "explicit_rejection_count": arena.get("explicit_rejection_count", 0),
                "sources_with_proposals": arena.get("competitor_sources") or [],
                "sources_rejected": sorted({
                    row.get("source")
                    for row in outcomes
                    if isinstance(row, dict) and row.get("status") == "REJECTED"
                }),
                "knowledge_investment_policy": "Not Available",
                "knowledge_investment_authority": "Not Available",
                "high_value_knowledge_items": None,
                "medium_value_knowledge_items": None,
                "low_value_knowledge_items": None,
                "deprioritized_knowledge_items": None,
                "candidate_proposals": proposals,
                "source_diagnostics": {},
                "adaptive_reuse_admission_trace": [],
            }
        return {
            "candidate_proposal_summary": summary,
            "candidate_proposal_diagnostics": {
                "raw_candidate_proposal_report": explicit,
                "candidate_proposals": summary.get("candidate_proposals") or [],
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
            if semantic.get("compiler_triggered") or semantic.get("compiler_selected"):
                return [self._arena_candidate(
                    source="semantic_to_transformation_compiler",
                    candidate_id="compiler_attempt",
                    operation=semantic.get("compiled_operation"),
                    confidence=semantic.get("compilation_confidence"),
                    validation_status=semantic.get("compilation_status"),
                    selected=False,
                    entered=False,
                    blocked_reason=semantic.get("failure_cause") or "compiler_selected_but_no_compilation_report",
                )]
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
        composed = adaptive.get("composed_program")
        if isinstance(composed, dict) and self._program_operation(composed):
            rows.append(self._arena_candidate(
                source="adaptive_reuse",
                candidate_id="composed_program",
                operation=self._program_operation(composed),
                confidence=self._first_number(adaptive.get("reuse_success_rate"), adaptive.get("reuse_rate")),
                validation_status=composed.get("composition_state") or "REUSED",
                selected=provenance.get("prediction_source") == "adaptive_reuse",
                entered=True,
            ))
        reused = adaptive.get("reused_programs") or []
        if isinstance(reused, list):
            for index, program in enumerate(reused[:8]):
                operation = self._program_operation(program)
                if not operation:
                    continue
                rows.append(self._arena_candidate(
                    source="adaptive_reuse",
                    candidate_id=f"reused_program:{index}",
                    operation=operation,
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
        nested = program.get("program")
        if isinstance(nested, dict):
            nested_operation = self._program_operation(nested)
            if nested_operation:
                return nested_operation
        steps = program.get("steps") or program.get("program_steps") or []
        if steps and isinstance(steps[0], dict):
            return steps[0].get("operation") or steps[0].get("primitive") or steps[0].get("operator")
        return program.get("operation") or program.get("primitive") or program.get("operator")

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
        observed_active_compute = round(
            sum(float(item.get("duration_seconds", 0.0) or 0.0) for item in rows),
            6,
        )
        if observed_active_compute > 0.0:
            if active_compute is None:
                active_compute = observed_active_compute
            elif observed_active_compute / max(float(active_compute), 0.000001) >= 0.70:
                active_compute = observed_active_compute
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
                "active_compute_time": active_compute,
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
