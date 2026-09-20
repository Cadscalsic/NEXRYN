from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any


VISIBILITY_POLICY_VERSION = "report_level_visibility.v1"


class ReportLevel(str, Enum):
    MINIMAL = "MINIMAL"
    NORMAL = "NORMAL"
    DIAGNOSTIC = "DIAGNOSTIC"


class FieldPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True)
class FieldPolicy:
    field_name: str
    report_level_visibility: tuple[ReportLevel, ...]
    field_priority: FieldPriority
    field_owner: str
    field_type: str
    diagnostic_only: bool = False
    compressible: bool = False
    externalizable: bool = False

    def visible_at(self, level: ReportLevel) -> bool:
        return level in self.report_level_visibility

    def as_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "report_level_visibility": [
                level.value for level in self.report_level_visibility
            ],
            "field_priority": self.field_priority.value,
            "field_owner": self.field_owner,
            "field_type": self.field_type,
            "diagnostic_only": self.diagnostic_only,
            "compressible": self.compressible,
            "externalizable": self.externalizable,
        }


@dataclass(frozen=True)
class SectionPolicy:
    section_name: str
    report_level_visibility: tuple[ReportLevel, ...]
    externalizable: bool = False

    def visible_at(self, level: ReportLevel) -> bool:
        return level in self.report_level_visibility


class ReportLevelSeparationContract:
    """Authoritative visibility policy for NEXRYN report fields."""

    REQUIRED_FIELDS = {
        ReportLevel.MINIMAL: {
            "runtime_status",
            "total_runtime_seconds",
            "execution_coverage",
            "snapshot_coverage",
            "generated_concepts",
            "generated_programs",
            "validated_programs",
            "truth_candidate_count",
            "overall_search_quality",
            "average_program_confidence",
            "system_health",
            "final_status",
        },
        ReportLevel.NORMAL: {
            "runtime_status",
            "execution_summary",
            "cognitive_outputs",
            "program_quality",
            "search_quality",
            "knowledge_pipeline_summary",
            "timing_summary",
            "system_health",
            "coverage_metrics",
            "warnings",
            "final_status",
        },
        ReportLevel.DIAGNOSTIC: {
            "runtime_status",
            "execution_tree",
            "runtime_telemetry",
            "snapshot_summaries",
            "validation_diagnostics",
            "metric_attribution_diagnostics",
            "execution_registry_diagnostics",
            "final_status",
        },
    }

    def __init__(self):
        self.field_policies = self._build_field_policies()
        self.section_policies = self._build_section_policies()

    def normalize_level(self, level: str | ReportLevel) -> ReportLevel:
        if isinstance(level, ReportLevel):
            return level
        normalized = str(level or "NORMAL").upper()
        aliases = {
            "DEBUG": "DIAGNOSTIC",
            "AUDIT": "DIAGNOSTIC",
            "FULL": "DIAGNOSTIC",
            "FULL_DIAGNOSTIC": "DIAGNOSTIC",
            "DIAGNOSTIC_SUMMARY": "DIAGNOSTIC",
        }
        normalized = aliases.get(normalized, normalized)
        try:
            return ReportLevel(normalized)
        except ValueError:
            return ReportLevel.NORMAL

    def policy_for(self, field_name: str) -> FieldPolicy:
        if field_name in self.field_policies:
            return self.field_policies[field_name]
        return FieldPolicy(
            field_name=field_name,
            report_level_visibility=(ReportLevel.DIAGNOSTIC,),
            field_priority=FieldPriority.DIAGNOSTIC_ONLY,
            field_owner="unclassified_diagnostics",
            field_type="unknown",
            diagnostic_only=True,
            compressible=True,
            externalizable=True,
        )

    def visibility_for(self, field_name: str) -> dict[str, Any]:
        return self.policy_for(field_name).as_dict()

    def allowed_fields_for(self, level: str | ReportLevel) -> set[str]:
        report_level = self.normalize_level(level)
        return {
            name
            for name, policy in self.field_policies.items()
            if policy.visible_at(report_level)
        }

    def hidden_fields_for(self, level: str | ReportLevel) -> set[str]:
        report_level = self.normalize_level(level)
        return {
            name
            for name, policy in self.field_policies.items()
            if not policy.visible_at(report_level)
        }

    def externalized_fields_for(self, level: str | ReportLevel) -> set[str]:
        report_level = self.normalize_level(level)
        return {
            name
            for name, policy in self.field_policies.items()
            if policy.externalizable and not policy.visible_at(report_level)
        }

    def apply_visibility(
        self,
        canonical_report: dict[str, Any] | None,
        *,
        level: str | ReportLevel = ReportLevel.NORMAL,
    ) -> dict[str, Any]:
        canonical_report = (
            canonical_report if isinstance(canonical_report, dict) else {}
        )
        report_level = self.normalize_level(level)
        visible_report: dict[str, Any] = {}
        hidden_fields: dict[str, Any] = {}
        externalized_fields: dict[str, Any] = {}

        for field_name in sorted(canonical_report.keys(), key=str):
            value = canonical_report[field_name]
            policy = self.policy_for(field_name)
            if policy.visible_at(report_level):
                visible_report[field_name] = deepcopy(value)
            else:
                hidden_fields[field_name] = deepcopy(value)
                if policy.externalizable:
                    externalized_fields[field_name] = deepcopy(value)

        metadata = self.metadata_for(
            report_level,
            visible_fields=set(visible_report),
            hidden_fields=set(hidden_fields),
            externalized_fields=set(externalized_fields),
            validation_errors=self.validate(
                visible_report,
                level=report_level,
                canonical_report=canonical_report,
            )["validation_errors"],
        )
        visible_report["report_level_metadata"] = metadata
        return {
            "canonical_report": canonical_report,
            "visible_report": visible_report,
            "hidden_fields": hidden_fields,
            "externalized_fields": externalized_fields,
            "report_level_metadata": metadata,
        }

    def validate(
        self,
        report: dict[str, Any] | None,
        *,
        level: str | ReportLevel = ReportLevel.NORMAL,
        canonical_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = report if isinstance(report, dict) else {}
        canonical_report = (
            canonical_report if isinstance(canonical_report, dict) else report
        )
        report_level = self.normalize_level(level)
        validation_errors: list[str] = []
        forbidden_fields: list[str] = []
        diagnostic_fields_removed = 0

        for field_name in sorted(report.keys(), key=str):
            if field_name == "report_level_metadata":
                continue
            policy = self.policy_for(field_name)
            if not policy.visible_at(report_level):
                forbidden_fields.append(field_name)
                validation_errors.append(f"forbidden_field:{field_name}")

        for field_name in sorted(canonical_report.keys(), key=str):
            policy = self.policy_for(field_name)
            if (
                policy.diagnostic_only
                and not policy.visible_at(report_level)
                and field_name not in report
            ):
                diagnostic_fields_removed += 1

        missing_required = [
            field_name
            for field_name in sorted(self.REQUIRED_FIELDS[report_level])
            if field_name not in report
        ]
        validation_errors.extend(
            f"missing_required_field:{field_name}"
            for field_name in missing_required
        )
        validation_errors.extend(self.validate_policy_registry())

        metadata = self.metadata_for(
            report_level,
            visible_fields=set(report) - {"report_level_metadata"},
            hidden_fields=set(canonical_report) - set(report),
            externalized_fields={
                name
                for name in set(canonical_report) - set(report)
                if self.policy_for(name).externalizable
            },
            validation_errors=validation_errors,
            diagnostic_fields_removed=diagnostic_fields_removed,
        )
        return {
            "report_level": report_level.value,
            "report_validation_success": not validation_errors,
            "validation_errors": validation_errors,
            "forbidden_fields": forbidden_fields,
            "missing_required_fields": missing_required,
            "report_level_metadata": metadata,
        }

    def validate_policy_registry(self) -> list[str]:
        errors: list[str] = []
        for field_name, policy in sorted(self.field_policies.items()):
            levels = list(policy.report_level_visibility)
            if len(levels) != len(set(levels)):
                errors.append(f"duplicate_field_visibility:{field_name}")
            if policy.diagnostic_only and any(
                level != ReportLevel.DIAGNOSTIC for level in levels
            ):
                errors.append(f"visibility_conflict:{field_name}")
            if policy.externalizable and not policy.diagnostic_only:
                errors.append(f"externalization_conflict:{field_name}")
            if not policy.field_priority:
                errors.append(f"missing_priority:{field_name}")
        return errors

    def metadata_for(
        self,
        level: str | ReportLevel,
        *,
        visible_fields: set[str],
        hidden_fields: set[str],
        externalized_fields: set[str],
        validation_errors: list[str],
        diagnostic_fields_removed: int | None = None,
    ) -> dict[str, Any]:
        report_level = self.normalize_level(level)
        if diagnostic_fields_removed is None:
            diagnostic_fields_removed = len([
                field_name
                for field_name in hidden_fields
                if self.policy_for(field_name).diagnostic_only
            ])
        return {
            "report_level": report_level.value,
            "visible_section_count": len(visible_fields),
            "hidden_section_count": len(hidden_fields),
            "externalized_section_count": len(externalized_fields),
            "report_validation_success": not validation_errors,
            "diagnostic_fields_removed": diagnostic_fields_removed,
            "technical_appendix_available": bool(externalized_fields),
            "visibility_policy_version": VISIBILITY_POLICY_VERSION,
        }

    def section_visibility_for(self, section_name: str) -> dict[str, Any]:
        policy = self.section_policies.get(section_name)
        if policy is None:
            policy = SectionPolicy(
                section_name=section_name,
                report_level_visibility=(ReportLevel.DIAGNOSTIC,),
                externalizable=True,
            )
        return {
            "section_name": policy.section_name,
            "report_level_visibility": [
                level.value for level in policy.report_level_visibility
            ],
            "externalizable": policy.externalizable,
        }

    def _build_field_policies(self) -> dict[str, FieldPolicy]:
        minimal_normal_diagnostic = (
            ReportLevel.MINIMAL,
            ReportLevel.NORMAL,
            ReportLevel.DIAGNOSTIC,
        )
        normal_diagnostic = (ReportLevel.NORMAL, ReportLevel.DIAGNOSTIC)
        diagnostic_only = (ReportLevel.DIAGNOSTIC,)

        policies = [
            self._policy("runtime_status", minimal_normal_diagnostic, FieldPriority.CRITICAL, "execution_runtime", "status"),
            self._policy("final_status", minimal_normal_diagnostic, FieldPriority.CRITICAL, "final_report", "status"),
            self._policy("total_runtime_seconds", minimal_normal_diagnostic, FieldPriority.CRITICAL, "timing", "number"),
            self._policy("execution_time", minimal_normal_diagnostic, FieldPriority.CRITICAL, "timing", "number"),
            self._policy("execution_coverage", minimal_normal_diagnostic, FieldPriority.CRITICAL, "execution_lifecycle", "number"),
            self._policy("snapshot_coverage", minimal_normal_diagnostic, FieldPriority.CRITICAL, "snapshot_runtime", "number"),
            self._policy("lifecycle_coverage", minimal_normal_diagnostic, FieldPriority.HIGH, "execution_lifecycle", "number"),
            self._policy("generated_concepts", minimal_normal_diagnostic, FieldPriority.HIGH, "cognitive_outputs", "count"),
            self._policy("generated_programs", minimal_normal_diagnostic, FieldPriority.HIGH, "program_synthesis", "count"),
            self._policy("validated_programs", minimal_normal_diagnostic, FieldPriority.HIGH, "program_validation", "count"),
            self._policy("truth_candidate_count", minimal_normal_diagnostic, FieldPriority.HIGH, "truth_runtime", "count"),
            self._policy("overall_search_quality", minimal_normal_diagnostic, FieldPriority.HIGH, "search_runtime", "metric"),
            self._policy("average_program_confidence", minimal_normal_diagnostic, FieldPriority.HIGH, "program_synthesis", "metric"),
            self._policy("system_health", minimal_normal_diagnostic, FieldPriority.CRITICAL, "observability", "summary"),
            self._policy("critical_warnings", minimal_normal_diagnostic, FieldPriority.CRITICAL, "validation", "list"),
            self._policy("critical_errors", minimal_normal_diagnostic, FieldPriority.CRITICAL, "validation", "list"),
            self._policy("warnings", normal_diagnostic, FieldPriority.HIGH, "validation", "list"),
            self._policy("errors", normal_diagnostic, FieldPriority.CRITICAL, "validation", "list"),
            self._policy("execution_summary", normal_diagnostic, FieldPriority.CRITICAL, "execution_runtime", "summary"),
            self._policy("cognitive_outputs", normal_diagnostic, FieldPriority.HIGH, "cognitive_outputs", "summary"),
            self._policy("program_quality", normal_diagnostic, FieldPriority.HIGH, "program_synthesis", "summary"),
            self._policy("search_quality", normal_diagnostic, FieldPriority.HIGH, "search_runtime", "summary"),
            self._policy("knowledge_pipeline_summary", normal_diagnostic, FieldPriority.HIGH, "knowledge_pipeline", "summary"),
            self._policy("timing_summary", normal_diagnostic, FieldPriority.MEDIUM, "timing", "summary"),
            self._policy("coverage_metrics", normal_diagnostic, FieldPriority.HIGH, "execution_lifecycle", "summary"),
            self._policy("lifecycle_summaries", normal_diagnostic, FieldPriority.MEDIUM, "execution_lifecycle", "summary"),
            self._policy("validation_summaries", normal_diagnostic, FieldPriority.MEDIUM, "validation", "summary"),
            self._policy("runtime_metadata_summaries", normal_diagnostic, FieldPriority.MEDIUM, "runtime_metadata", "summary"),
            self._policy("knowledge_pipeline_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "knowledge_pipeline", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("compression_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "representation", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("representation_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "representation", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("execution_tree", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "execution_runtime", "tree", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("runtime_telemetry", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "telemetry", "object", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("execution_telemetry", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "telemetry", "object", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("metric_ownership", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "metric_attribution", "map", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("metric_ownership_map", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "metric_attribution", "map", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("runtime_metric_confidence_by_id", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "metric_attribution", "map", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("snapshot_payloads", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "snapshot_runtime", "payload", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("snapshot_summaries", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "snapshot_runtime", "diagnostic", diagnostic_only=True, compressible=True, externalizable=False),
            self._policy("execution_registry", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "execution_registry", "registry", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("execution_registry_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "execution_registry", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("validation_history", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "validation", "history", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("validation_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "validation", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("metric_attribution_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "metric_attribution", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("timing_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "timing", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("lifecycle_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "execution_lifecycle", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("quality_diagnostics", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "quality", "diagnostic", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("large_arrays", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "diagnostics", "array", diagnostic_only=True, compressible=True, externalizable=True),
            self._policy("runtime_registry", diagnostic_only, FieldPriority.DIAGNOSTIC_ONLY, "runtime_registry", "registry", diagnostic_only=True, compressible=True, externalizable=True),
        ]
        return {policy.field_name: policy for policy in policies}

    def _build_section_policies(self) -> dict[str, SectionPolicy]:
        minimal_normal_diagnostic = (
            ReportLevel.MINIMAL,
            ReportLevel.NORMAL,
            ReportLevel.DIAGNOSTIC,
        )
        normal_diagnostic = (ReportLevel.NORMAL, ReportLevel.DIAGNOSTIC)
        diagnostic_only = (ReportLevel.DIAGNOSTIC,)
        sections = [
            SectionPolicy("Execution Summary", minimal_normal_diagnostic),
            SectionPolicy("Final Status", minimal_normal_diagnostic),
            SectionPolicy("Execution Tree", diagnostic_only, externalizable=True),
            SectionPolicy("Timing Summary", normal_diagnostic),
            SectionPolicy("Program Quality", normal_diagnostic),
            SectionPolicy("Knowledge Pipeline Summary", normal_diagnostic),
            SectionPolicy("Snapshot Payloads", diagnostic_only, externalizable=True),
        ]
        return {section.section_name: section for section in sections}

    def _policy(
        self,
        field_name: str,
        visibility: tuple[ReportLevel, ...],
        priority: FieldPriority,
        owner: str,
        field_type: str,
        *,
        diagnostic_only: bool = False,
        compressible: bool = False,
        externalizable: bool = False,
    ) -> FieldPolicy:
        return FieldPolicy(
            field_name=field_name,
            report_level_visibility=visibility,
            field_priority=priority,
            field_owner=owner,
            field_type=field_type,
            diagnostic_only=diagnostic_only,
            compressible=compressible,
            externalizable=externalizable,
        )


report_level_separation_contract = ReportLevelSeparationContract()
