from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any

from runtime.reporting.canonical_report_binding_engine import (
    BindingState,
    ReportFieldBinding,
    canonical_report_binding_engine,
)
from runtime.reporting.final_report_renderer import (
    RAW_STRUCTURE_PATTERN,
    REPORT_BEGIN_MARKER,
    REPORT_END_MARKER,
    SECTION_ORDER,
)


class RepresentationValidationState(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"
    COMPRESSED = "COMPRESSED"
    EXTERNALIZED = "EXTERNALIZED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    INVALID_SOURCE = "INVALID_SOURCE"
    UNBOUND = "UNBOUND"


VALID_REPRESENTATION_STATES = {
    state.value for state in RepresentationValidationState
}


DIAGNOSTIC_ONLY_KEYS = {
    "execution_registry",
    "execution_timeline",
    "execution_telemetry",
    "runtime_telemetry",
    "metric_ownership",
    "metric_ownership_map",
    "runtime_metric_confidence_by_id",
    "snapshot_payload",
    "snapshot_payloads",
    "latest_snapshot_payload",
    "validation_history",
}


HEAVY_STRUCTURE_KEYS = {
    "execution_registry",
    "execution_timeline",
    "execution_telemetry",
    "runtime_telemetry",
    "runtime_metric_confidence_by_id",
    "metric_ownership",
    "snapshot_payloads",
    "snapshot_reports",
    "latest_snapshot_payload",
    "semantic_memory",
    "knowledge_fabric",
}


@dataclass(frozen=True)
class RepresentationValidationReport:
    representation_validation_success: bool
    representation_health_score: float
    representation_coverage: float
    visible_field_count: int
    compressed_field_count: int
    externalized_field_count: int
    hidden_field_count: int
    duplicate_field_count: int
    invalid_binding_count: int
    report_level_compliance: bool
    validation_errors: list[str]
    validation_warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "representation_validation_success": (
                self.representation_validation_success
            ),
            "representation_health_score": self.representation_health_score,
            "representation_coverage": self.representation_coverage,
            "visible_field_count": self.visible_field_count,
            "compressed_field_count": self.compressed_field_count,
            "externalized_field_count": self.externalized_field_count,
            "hidden_field_count": self.hidden_field_count,
            "duplicate_field_count": self.duplicate_field_count,
            "invalid_binding_count": self.invalid_binding_count,
            "report_level_compliance": self.report_level_compliance,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
        }


class RepresentationLayerValidationEngine:
    """Authoritative validator for NEXRYN representation-layer artifacts."""

    def __init__(
        self,
        field_contracts: list[ReportFieldBinding] | None = None,
    ):
        self.field_contracts = list(
            field_contracts or canonical_report_binding_engine.field_bindings
        )
        self.metrics = self._empty_metrics()

    def validate(
        self,
        canonical_report_state: dict[str, Any] | None,
        *,
        binding_report: dict[str, Any] | None = None,
        compressed_report: dict[str, Any] | None = None,
        rendered_report: str | None = None,
        report_level: str = "normal",
    ) -> dict[str, Any]:
        canonical_report_state = (
            canonical_report_state
            if isinstance(canonical_report_state, dict)
            else {}
        )
        binding_report = binding_report if isinstance(binding_report, dict) else {}
        compressed_report = (
            compressed_report if isinstance(compressed_report, dict) else {}
        )
        report_level = self._normalize_report_level(report_level)

        field_bindings = self._field_bindings(binding_report)
        field_registry = self._field_registry(binding_report)
        canonical_sources = self._canonical_sources(binding_report)

        field_validation = self._validate_fields(field_bindings)
        source_validation = self._validate_canonical_sources(
            field_bindings,
            canonical_sources,
        )
        visibility_validation = self._validate_visibility(
            field_bindings,
            compressed_report,
            report_level,
        )
        compression_validation = self._validate_compression(
            canonical_report_state,
            compressed_report,
            field_bindings,
        )
        duplication_validation = self._detect_duplicates(
            field_bindings,
            field_registry,
            rendered_report,
        )
        completeness = self._representation_completeness(
            field_bindings,
            report_level,
        )
        structure_validation = self._validate_report_structure(rendered_report)
        readability_validation = self._validate_human_readability(
            rendered_report,
            canonical_report_state,
        )
        architecture_validation = self._validate_architectural_integrity(
            field_bindings,
            field_registry,
            canonical_sources,
        )

        validations = [
            field_validation,
            source_validation,
            visibility_validation,
            compression_validation,
            duplication_validation,
            structure_validation,
            readability_validation,
            architecture_validation,
        ]
        errors = self._unique(
            error
            for validation in validations
            for error in validation["errors"]
        )
        warnings = self._unique(
            warning
            for validation in validations
            for warning in validation["warnings"]
        )

        scores = self._score_report(
            field_bindings=field_bindings,
            completeness=completeness,
            visibility_validation=visibility_validation,
            compression_validation=compression_validation,
            readability_validation=readability_validation,
            architecture_validation=architecture_validation,
            errors=errors,
        )
        counts = self._state_counts(field_bindings)
        duplicate_count = duplication_validation["duplicate_count"]
        invalid_binding_count = counts["INVALID_SOURCE"] + counts["UNBOUND"]

        report = RepresentationValidationReport(
            representation_validation_success=not errors,
            representation_health_score=scores["representation_health_score"],
            representation_coverage=scores["representation_coverage"],
            visible_field_count=counts["VISIBLE"],
            compressed_field_count=counts["COMPRESSED"],
            externalized_field_count=counts["EXTERNALIZED"],
            hidden_field_count=counts["HIDDEN"],
            duplicate_field_count=duplicate_count,
            invalid_binding_count=invalid_binding_count,
            report_level_compliance=visibility_validation["success"],
            validation_errors=errors,
            validation_warnings=warnings,
        ).as_dict()

        report.update({
            "system": "representation_layer_validation_engine",
            "FIELD_VALIDATION": field_validation,
            "CANONICAL_SOURCE_VALIDATION": source_validation,
            "VISIBILITY_VALIDATION": visibility_validation,
            "COMPRESSION_VALIDATION": compression_validation,
            "DUPLICATION_DETECTION": duplication_validation,
            "REPRESENTATION_COMPLETENESS": completeness,
            "REPORT_STRUCTURE_VALIDATION": structure_validation,
            "HUMAN_REPRESENTATION_VALIDATION": readability_validation,
            "ARCHITECTURAL_INTEGRITY_VALIDATION": architecture_validation,
            "representation_states": counts,
            **scores,
        })
        self.metrics = deepcopy(report)
        return report

    def report(self) -> dict[str, Any]:
        return deepcopy(self.metrics)

    def _validate_fields(
        self,
        field_bindings: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        required_keys = {
            "field_name",
            "canonical_source",
            "field_owner",
            "representation_type",
            "visibility_policy",
            "binding_status",
            "compression_policy",
            "externalization_policy",
        }
        valid_statuses = {state.value for state in BindingState}

        for name, field in sorted(field_bindings.items()):
            missing = sorted(required_keys - set(field))
            errors.extend(f"field_missing_{key}:{name}" for key in missing)
            if field.get("field_name") not in {name, None}:
                errors.append(f"field_name_mismatch:{name}")
            if field.get("binding_status") not in valid_statuses:
                errors.append(f"invalid_binding_status:{name}")
            state = self._representation_state(field)
            if state not in VALID_REPRESENTATION_STATES:
                errors.append(f"invalid_representation_state:{name}")
            if str(field.get("display_value", "")).upper() == "UNKNOWN":
                errors.append(f"unknown_value_prohibited:{name}")
            if not field.get("field_owner"):
                errors.append(f"missing_owner:{name}")
            if not field.get("canonical_source"):
                errors.append(f"missing_canonical_source:{name}")
            if not field.get("visibility_policy"):
                errors.append(f"missing_visibility_policy:{name}")
            if field.get("binding_confidence") == 0 and (
                field.get("binding_status") == BindingState.BOUND.value
            ):
                warnings.append(f"zero_confidence_bound_field:{name}")

        return {
            "validation_success": not errors,
            "validated_field_count": len(field_bindings),
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_canonical_sources(
        self,
        field_bindings: dict[str, dict[str, Any]],
        canonical_sources: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        seen_source_fields: dict[tuple[str, str], str] = {}

        for name, field in sorted(field_bindings.items()):
            source_name = field.get("canonical_source")
            source = canonical_sources.get(str(source_name))
            if not source:
                errors.append(f"canonical_source_missing:{name}")
                continue
            if source.get("accessible") is False:
                errors.append(f"canonical_source_inaccessible:{name}")
            if source.get("field_count") is None:
                warnings.append(f"canonical_source_field_count_unknown:{name}")
            source_field = str(field.get("source_field") or name)
            key = (str(source_name), source_field)
            previous = seen_source_fields.get(key)
            if previous and previous != name:
                warnings.append(
                    f"shared_canonical_source_field:{previous}:{name}"
                )
            seen_source_fields[key] = name

        source_names = [
            str(field.get("canonical_source"))
            for field in field_bindings.values()
            if field.get("canonical_source")
        ]
        duplicate_source_names = self._duplicates(source_names)
        return {
            "validation_success": not errors,
            "canonical_source_count": len(canonical_sources),
            "duplicate_source_reference_count": len(duplicate_source_names),
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_visibility(
        self,
        field_bindings: dict[str, dict[str, Any]],
        compressed_report: dict[str, Any],
        report_level: str,
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        visible_count = 0

        for name, field in sorted(field_bindings.items()):
            visibility = {str(item).upper() for item in field.get("visibility_policy", [])}
            status = field.get("binding_status")
            allowed = report_level in visibility
            if allowed and status in {
                BindingState.BOUND.value,
                BindingState.COMPRESSED.value,
            }:
                visible_count += 1
            if (
                not allowed
                and status in {BindingState.BOUND.value, BindingState.COMPRESSED.value}
            ):
                errors.append(f"forbidden_field_visible:{name}")
            if (
                report_level in {"MINIMAL", "NORMAL"}
                and visibility == {"DIAGNOSTIC"}
                and name in compressed_report
            ):
                errors.append(f"diagnostic_field_exposed:{name}")
            if status == BindingState.HIDDEN.value and allowed:
                warnings.append(f"visible_field_hidden_by_policy:{name}")

        return {
            "validation_success": not errors,
            "visible_field_count": visible_count,
            "report_level": report_level,
            "report_level_compliance": not errors,
            "errors": errors,
            "warnings": warnings,
            "success": not errors,
        }

    def _validate_compression(
        self,
        canonical_report_state: dict[str, Any],
        compressed_report: dict[str, Any],
        field_bindings: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        compact = (
            compressed_report.get("compact_report", {})
            if isinstance(compressed_report, dict)
            else {}
        )
        if compact and not isinstance(compact, dict):
            errors.append("compact_report_invalid")
            compact = {}

        for key in HEAVY_STRUCTURE_KEYS:
            if key in compressed_report and not key.endswith("_summary"):
                errors.append(f"heavy_structure_not_compressed:{key}")

        for name, field in sorted(field_bindings.items()):
            if field.get("compression_policy") == "COMPRESSED":
                if field.get("binding_status") not in {
                    BindingState.COMPRESSED.value,
                    BindingState.HIDDEN.value,
                    BindingState.EXTERNALIZED.value,
                    BindingState.NOT_AVAILABLE.value,
                }:
                    errors.append(f"compression_policy_not_respected:{name}")
                if (
                    field.get("binding_status") == BindingState.COMPRESSED.value
                    and "Compressed Summary" not in str(field.get("display_value"))
                ):
                    errors.append(f"compressed_field_missing_summary:{name}")

        before = self._number(compact.get("actual_size_before"))
        after = self._number(compact.get("actual_size_after"))
        ratio = self._number(compact.get("report_compression_ratio"))
        if before is not None and after is not None and ratio is not None:
            expected = 0.0 if before <= 0 else round(max(0.0, 1.0 - after / before), 4)
            if abs(expected - ratio) > 0.0001:
                errors.append("compression_ratio_mismatch")
        elif compact:
            warnings.append("compression_size_metadata_incomplete")

        if compact.get("critical_information_preserved") is False:
            errors.append("critical_information_not_preserved")
        if canonical_report_state and not compressed_report:
            warnings.append("compressed_report_not_provided")

        return {
            "validation_success": not errors,
            "compression_quality": 1.0 if not errors else 0.0,
            "critical_information_preserved": compact.get(
                "critical_information_preserved",
                None,
            ),
            "errors": errors,
            "warnings": warnings,
        }

    def _detect_duplicates(
        self,
        field_bindings: dict[str, dict[str, Any]],
        field_registry: dict[str, dict[str, Any]],
        rendered_report: str | None,
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        duplicates: list[str] = []

        binding_names = [str(field.get("field_name")) for field in field_bindings.values()]
        duplicates.extend(f"duplicate_report_field:{name}" for name in self._duplicates(binding_names))

        registry_names = [str(field.get("field_name")) for field in field_registry.values()]
        duplicates.extend(f"duplicate_registry_field:{name}" for name in self._duplicates(registry_names))

        binding_pairs = [
            f"{field.get('field_name')}::{field.get('canonical_source')}"
            for field in field_bindings.values()
        ]
        duplicates.extend(
            f"duplicate_canonical_binding:{name}"
            for name in self._duplicates(binding_pairs)
        )

        if rendered_report:
            for section in SECTION_ORDER:
                marker = (
                    "NEXRYN :: FINAL STATUS"
                    if section == "FINAL STATUS"
                    else f"\n{section}\n"
                )
                if rendered_report.count(marker) > 1:
                    duplicates.append(f"duplicate_section:{section}")

        errors.extend(duplicates)
        return {
            "validation_success": not errors,
            "duplicate_field_count": len(duplicates),
            "duplicate_count": len(duplicates),
            "errors": errors,
            "warnings": warnings,
        }

    def _representation_completeness(
        self,
        field_bindings: dict[str, dict[str, Any]],
        report_level: str,
    ) -> dict[str, Any]:
        contract_by_name = {
            contract.field_name: contract for contract in self.field_contracts
        }
        required_names = {
            name
            for name, contract in contract_by_name.items()
            if contract.required and report_level in contract.visibility_policy
        }
        present_names = set(field_bindings)
        missing_fields = sorted(required_names - present_names)
        required_present = sorted(required_names & present_names)
        optional_present = sorted(present_names - required_names)
        states = {
            name: self._representation_state(field)
            for name, field in field_bindings.items()
        }
        unbound_fields = sorted(
            name for name, state in states.items() if state == "UNBOUND"
        )
        invalid_fields = sorted(
            name for name, state in states.items() if state == "INVALID_SOURCE"
        )
        represented = [
            name for name, state in states.items()
            if state in VALID_REPRESENTATION_STATES
        ]
        coverage = (
            round(len(represented) / len(field_bindings), 4)
            if field_bindings
            else 1.0
        )
        return {
            "required_fields_present": required_present,
            "optional_fields_present": optional_present,
            "hidden_fields": sorted(
                name for name, state in states.items() if state == "HIDDEN"
            ),
            "compressed_fields": sorted(
                name for name, state in states.items() if state == "COMPRESSED"
            ),
            "externalized_fields": sorted(
                name for name, state in states.items() if state == "EXTERNALIZED"
            ),
            "missing_fields": missing_fields,
            "unbound_fields": unbound_fields,
            "invalid_source_fields": invalid_fields,
            "representation_coverage": coverage,
            "validation_success": not missing_fields and not unbound_fields,
        }

    def _validate_report_structure(
        self,
        rendered_report: str | None,
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not rendered_report:
            warnings.append("rendered_report_not_provided")
            return {
                "validation_success": True,
                "errors": errors,
                "warnings": warnings,
            }

        if not rendered_report.startswith(REPORT_BEGIN_MARKER):
            errors.append("missing_report_begin_marker")
        if not rendered_report.rstrip().endswith(REPORT_END_MARKER):
            errors.append("missing_report_end_marker")
        if rendered_report.count("NEXRYN :: FINAL STATUS") != 1:
            errors.append("final_status_occurs_not_once")
        positions = []
        for section in SECTION_ORDER:
            marker = (
                "NEXRYN :: FINAL STATUS"
                if section == "FINAL STATUS"
                else f"\n{section}\n"
            )
            count = rendered_report.count(marker)
            if count == 0:
                errors.append(f"missing_section:{section}")
            if count > 1:
                errors.append(f"duplicate_section:{section}")
            index = rendered_report.find(marker)
            if index >= 0:
                positions.append(index)
        if positions != sorted(positions):
            errors.append("section_order_invalid")
        if "Technical Appendix" not in rendered_report:
            warnings.append("technical_appendix_reference_missing")
        return {
            "validation_success": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_human_readability(
        self,
        rendered_report: str | None,
        canonical_report_state: dict[str, Any],
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not rendered_report:
            warnings.append("rendered_report_not_provided")
            return {
                "validation_success": True,
                "human_readability_score": 1.0,
                "errors": errors,
                "warnings": warnings,
            }

        if RAW_STRUCTURE_PATTERN.search(rendered_report):
            errors.append("raw_python_structure_detected")
        if self._raw_telemetry_visible(rendered_report):
            errors.append("raw_telemetry_structure_visible")
        if rendered_report.rstrip().endswith(("{", "[", ":", ",")):
            errors.append("partial_rendering_detected")
        if "UNKNOWN" in rendered_report and canonical_report_state:
            errors.append("unknown_value_with_canonical_data")
        if re.search(r"\n[A-Za-z][A-Za-z ]+:\s*$", rendered_report):
            errors.append("empty_human_field_detected")

        score = max(0.0, round(1.0 - (len(errors) * 0.2), 4))
        return {
            "validation_success": not errors,
            "human_readability_score": score,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_architectural_integrity(
        self,
        field_bindings: dict[str, dict[str, Any]],
        field_registry: dict[str, dict[str, Any]],
        canonical_sources: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []

        for name, field in sorted(field_bindings.items()):
            registry = field_registry.get(name)
            if not registry:
                errors.append(f"field_missing_from_registry:{name}")
                continue
            if registry.get("owner") != field.get("field_owner"):
                errors.append(f"owner_registry_mismatch:{name}")
            if registry.get("canonical_source") != field.get("canonical_source"):
                errors.append(f"source_registry_mismatch:{name}")
            if registry.get("binding_state") != field.get("binding_status"):
                errors.append(f"binding_state_registry_mismatch:{name}")
            if field.get("canonical_source") not in canonical_sources:
                errors.append(f"field_source_not_registered:{name}")
            if not registry.get("report_levels"):
                errors.append(f"missing_report_level_contract:{name}")

        if not field_bindings:
            warnings.append("no_field_bindings_provided")
        return {
            "validation_success": not errors,
            "architectural_integrity_score": 1.0 if not errors else 0.0,
            "errors": errors,
            "warnings": warnings,
        }

    def _score_report(
        self,
        *,
        field_bindings: dict[str, dict[str, Any]],
        completeness: dict[str, Any],
        visibility_validation: dict[str, Any],
        compression_validation: dict[str, Any],
        readability_validation: dict[str, Any],
        architecture_validation: dict[str, Any],
        errors: list[str],
    ) -> dict[str, float]:
        total = max(len(field_bindings), 1)
        valid_bindings = sum(
            1
            for field in field_bindings.values()
            if field.get("binding_status")
            not in {BindingState.INVALID_SOURCE.value, BindingState.UNBOUND.value}
        )
        binding_success_rate = round(valid_bindings / total, 4)
        representation_coverage = completeness["representation_coverage"]
        visibility_compliance = 1.0 if visibility_validation["validation_success"] else 0.0
        compression_quality = 1.0 if compression_validation["validation_success"] else 0.0
        externalized = [
            field for field in field_bindings.values()
            if field.get("binding_status") == BindingState.EXTERNALIZED.value
        ]
        externalization_quality = 1.0 if all(
            "Technical Appendix" in str(field.get("display_value"))
            for field in externalized
        ) else 0.0
        human_readability_score = readability_validation["human_readability_score"]
        architectural_integrity_score = architecture_validation[
            "architectural_integrity_score"
        ]
        components = [
            representation_coverage,
            binding_success_rate,
            visibility_compliance,
            compression_quality,
            externalization_quality,
            human_readability_score,
            architectural_integrity_score,
        ]
        penalty = min(0.5, len(errors) * 0.03)
        health = max(0.0, round((sum(components) / len(components)) - penalty, 4))
        return {
            "representation_health_score": health,
            "representation_coverage": representation_coverage,
            "binding_success_rate": binding_success_rate,
            "visibility_compliance": visibility_compliance,
            "compression_quality": compression_quality,
            "externalization_quality": externalization_quality,
            "human_readability_score": human_readability_score,
            "architectural_integrity_score": architectural_integrity_score,
        }

    def _field_bindings(
        self,
        binding_report: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        fields = binding_report.get("field_bindings", {})
        return fields if isinstance(fields, dict) else {}

    def _field_registry(
        self,
        binding_report: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        registry = binding_report.get("report_field_registry", {})
        return registry if isinstance(registry, dict) else {}

    def _canonical_sources(
        self,
        binding_report: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        sources = binding_report.get("canonical_source_registry", {})
        return sources if isinstance(sources, dict) else {}

    def _representation_state(self, field: dict[str, Any]) -> str:
        status = field.get("binding_status")
        if status == BindingState.BOUND.value:
            return RepresentationValidationState.VISIBLE.value
        if status in VALID_REPRESENTATION_STATES:
            return str(status)
        return RepresentationValidationState.UNBOUND.value

    def _state_counts(
        self,
        field_bindings: dict[str, dict[str, Any]],
    ) -> dict[str, int]:
        counts = {state: 0 for state in sorted(VALID_REPRESENTATION_STATES)}
        for field in field_bindings.values():
            counts[self._representation_state(field)] += 1
        return counts

    def _raw_telemetry_visible(self, rendered_report: str) -> bool:
        telemetry_patterns = [
            "execution_trace':",
            "runtime_telemetry':",
            "array([[",
            "dtype=",
            "telemetry_payload",
        ]
        lowered = rendered_report.lower()
        return any(pattern.lower() in lowered for pattern in telemetry_patterns)

    def _normalize_report_level(self, level: str) -> str:
        aliases = {
            "DEBUG": "DIAGNOSTIC",
            "AUDIT": "DIAGNOSTIC",
            "FULL": "DIAGNOSTIC",
            "FULL_DIAGNOSTIC": "DIAGNOSTIC",
            "DIAGNOSTIC_SUMMARY": "DIAGNOSTIC",
        }
        normalized = aliases.get(
            str(level or "normal").upper(),
            str(level or "normal").upper(),
        )
        return normalized if normalized in {"MINIMAL", "NORMAL", "DIAGNOSTIC"} else "NORMAL"

    def _duplicates(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        duplicates: list[str] = []
        for value in values:
            if value in seen and value not in duplicates:
                duplicates.append(value)
            seen.add(value)
        return duplicates

    def _unique(self, values: Any) -> list[str]:
        return list(dict.fromkeys(str(value) for value in values if value))

    def _number(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _empty_metrics(self) -> dict[str, Any]:
        return {
            "representation_validation_success": False,
            "representation_health_score": 0.0,
            "representation_coverage": 0.0,
            "visible_field_count": 0,
            "compressed_field_count": 0,
            "externalized_field_count": 0,
            "hidden_field_count": 0,
            "duplicate_field_count": 0,
            "invalid_binding_count": 0,
            "report_level_compliance": False,
        }


representation_layer_validation_engine = RepresentationLayerValidationEngine()


__all__ = [
    "RepresentationLayerValidationEngine",
    "RepresentationValidationReport",
    "RepresentationValidationState",
    "representation_layer_validation_engine",
]
