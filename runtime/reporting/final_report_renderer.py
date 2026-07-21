from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from runtime.reporting.canonical_report_binding_engine import (
    canonical_report_binding_engine,
)
from runtime.reporting.compact_report_compression_engine import (
    compact_report_compression_engine,
)
from runtime.reporting.pre_final_report_diagnostics import (
    pre_final_report_diagnostics,
)


REPORT_BEGIN_MARKER = "<<< NEXRYN_REPORT_BEGIN >>>"
REPORT_END_MARKER = "<<< NEXRYN_REPORT_END >>>"

SECTION_ORDER = [
    "REPORT HEADER",
    "EXECUTION SUMMARY",
    "COGNITIVE OUTPUTS",
    "PROGRAM QUALITY",
    "UNIFIED CONCEPT LIFECYCLE REPORT",
    "PROGRAM GENERATION REPORT",
    "PROGRAM BLUEPRINT INTELLIGENCE REPORT",
    "COGNITIVE PROGRAM LIFECYCLE REPORT",
    "COGNITIVE KNOWLEDGE DOMAINS REPORT",
    "COGNITIVE DOMAIN INTELLIGENCE REPORT",
    "COGNITIVE DOMAIN LIFECYCLE REPORT",
    "COGNITIVE DOMAIN INTERACTION REPORT",
    "COGNITIVE DOMAIN GOVERNANCE REPORT",
    "COGNITIVE DOMAIN ECOSYSTEM REPORT",
    "COGNITIVE DOMAIN CONSTITUTION REPORT",
    "SEMANTIC COMPILATION",
    "EXECUTABLE SEMANTIC COVERAGE",
    "COGNITIVE CAPABILITY COVERAGE",
    "TRANSFORMATION DECISION",
    "MULTI HYPOTHESIS REPORT",
    "CANDIDATE PROPOSAL PHASE",
    "COGNITIVE CANDIDATE ARENA",
    "COUNTERFACTUAL REASONING REPORT",
    "EXECUTABLE INTELLIGENCE REPORT",
    "SEARCH QUALITY",
    "KNOWLEDGE PIPELINE",
    "SYSTEM HEALTH",
    "TIMING SUMMARY",
    "COGNITIVE STAGE TIMING",
    "COGNITIVE RESOURCE SUMMARY",
    "WARNINGS AND GAPS",
    "RUNTIME METADATA",
    "OPTIONAL TECHNICAL APPENDIX",
    "FINAL STATUS",
]

RAW_STRUCTURE_PATTERN = re.compile(
    r"(^|\s)(\{'.*':|\['.*'\]|\{'[^'\n]+':|\[[{]\s*')",
    re.DOTALL,
)


class DeterministicFinalReportRenderer:
    """Single owner for final human-readable NEXRYN reports."""

    def __init__(self, console_budget_chars: int = 34000):
        self.console_budget_chars = int(console_budget_chars or 34000)
        self.metrics = self._empty_metrics()

    def render(
        self,
        report_state: dict[str, Any] | None,
        *,
        runtime_metadata: dict[str, Any] | None = None,
        report_level: str = "normal",
        artifact_directory: str | os.PathLike[str] | None = None,
        write_artifact: bool = False,
        write_diagnostic_artifact: bool = False,
        console_budget_chars: int | None = None,
    ) -> str:
        report_state = report_state if isinstance(report_state, dict) else {}
        runtime_metadata = (
            runtime_metadata if isinstance(runtime_metadata, dict) else {}
        )
        report_level = self._normalize_report_level(report_level)
        budget = (
            self.console_budget_chars
            if console_budget_chars is None
            else int(console_budget_chars)
        )
        if report_level == "minimal":
            pre_final_report_diagnostics.phase_enter(
                "REPORT_PROJECTION",
                input_keys=len(report_state),
                multi_task_results=len(report_state.get("multi_task_results", []) or []),
            )
            report_state = self._minimal_report_projection(report_state)
            pre_final_report_diagnostics.phase_exit(
                "REPORT_PROJECTION",
                output_keys=len(report_state),
                projected_tasks=len(report_state.get("multi_task_results", []) or []),
            )
        pre_final_report_diagnostics.phase_enter(
            "CANONICAL_BIND",
            report_keys=len(report_state),
            report_level=report_level,
        )
        binding_result = canonical_report_binding_engine.bind(
            report_state,
            runtime_metadata=runtime_metadata,
            report_level=report_level,
        )
        pre_final_report_diagnostics.phase_exit(
            "CANONICAL_BIND",
            source_count=len(binding_result.get("canonical_source_registry", {}) or {}),
            field_count=len(binding_result.get("report_field_registry", {}) or {}),
        )
        bound_report_state = dict(report_state)
        bound_report_state["CANONICAL_REPORT_BINDING"] = binding_result
        bound_report_state["report_field_registry"] = (
            binding_result["report_field_registry"]
        )
        bound_report_state["canonical_source_registry"] = (
            binding_result["canonical_source_registry"]
        )
        bound_report_state["binding_diagnostics"] = (
            binding_result["binding_diagnostics"]
        )

        pre_final_report_diagnostics.phase_enter(
            "REPORT_RENDER_PREP",
            bound_keys=len(bound_report_state),
        )
        if report_level in {"minimal", "normal"}:
            compression_result = {
                "compressed_report": bound_report_state,
                "compression_report": {
                    "compression_status": "NOT_REQUIRED",
                    "report_level": report_level,
                    "reason": "interactive_final_report_projection",
                },
                "compression_statistics": {
                    "original_size": 0,
                    "compressed_size": 0,
                    "compression_ratio": 1.0,
                    "heavy_keys_removed": 0,
                    "arrays_summarized": 0,
                    "repeated_reports_collapsed": 0,
                },
            }
            bound_report_state["compression_report"] = compression_result[
                "compression_report"
            ]
            compressed_report_state = bound_report_state
        else:
            compression_result = compact_report_compression_engine.compress(
                bound_report_state,
                profile=report_level,
                artifact_directory=artifact_directory,
                write_appendix=write_diagnostic_artifact,
            )
            compressed_report_state = compression_result["compressed_report"]
        pre_final_report_diagnostics.collection_snapshot(
            "COMPRESSED_REPORT_STATE",
            compressed_report_state,
        )

        canonical = self._canonical_state(
            compressed_report_state,
            runtime_metadata=runtime_metadata,
            report_level=report_level,
            binding_result=binding_result,
        )
        pre_final_report_diagnostics.collection_snapshot(
            "CANONICAL_RENDER_STATE",
            canonical,
        )
        full_report = self._render_full_report(canonical)
        pre_final_report_diagnostics.mark(
            "REPORT_FULL_STRING_CONSTRUCTED",
            full_report_chars=len(full_report),
            full_report_bytes=len(full_report.encode("utf-8")),
        )
        validation_errors = self.validate(full_report)
        rendered_report = full_report

        if budget > 0 and len(full_report) > budget:
            rendered_report = self._render_budget_summary(canonical, full_report)
            validation_errors = self.validate(rendered_report)
        pre_final_report_diagnostics.phase_exit(
            "REPORT_RENDER_PREP",
            rendered_chars=len(rendered_report),
            validation_errors=len(validation_errors),
            budget=budget,
        )

        artifact_written = False
        diagnostic_artifact_written = False
        if write_artifact and artifact_directory:
            artifact_text = full_report if rendered_report != full_report else rendered_report
            self.write_text_artifact(
                artifact_text,
                Path(artifact_directory) / "runtime_report.txt",
            )
            artifact_written = True
        if write_diagnostic_artifact and artifact_directory:
            self.write_diagnostic_artifact(
                {
                    "canonical_report": bound_report_state,
                    "compressed_report": compressed_report_state,
                    "compression_statistics": (
                        compression_result["compression_statistics"]
                    ),
                },
                Path(artifact_directory) / "runtime_diagnostic_report.json",
            )
            diagnostic_artifact_written = True

        self.metrics = self._build_metrics(
            rendered_report,
            validation_errors,
            artifact_written=artifact_written,
            diagnostic_artifact_written=diagnostic_artifact_written,
        )
        return rendered_report

    def emit(self, rendered_report: str, stream: Any | None = None) -> None:
        stream = stream or os.sys.stdout
        pre_final_report_diagnostics.mark(
            "FINAL_REPORT_FIRST_BYTE_WRITTEN",
            rendered_chars=len(rendered_report),
            rendered_bytes=len(rendered_report.encode("utf-8")),
        )
        stream.write(rendered_report)
        if not rendered_report.endswith("\n"):
            stream.write("\n")
        stream.flush()
        pre_final_report_diagnostics.mark(
            "FINAL_REPORT_LAST_BYTE_WRITTEN",
            rendered_chars=len(rendered_report),
        )

    def validate(self, rendered_report: str) -> list[str]:
        errors: list[str] = []
        if not rendered_report.startswith(REPORT_BEGIN_MARKER):
            errors.append("missing_report_begin_marker")
        if not rendered_report.rstrip().endswith(REPORT_END_MARKER):
            errors.append("missing_report_end_marker")
        if rendered_report.count("NEXRYN :: FINAL STATUS") != 1:
            errors.append("final_status_occurs_not_once")
        if "\nFINAL STATUS\n" in rendered_report:
            errors.append("duplicate_section:FINAL STATUS")

        section_positions = []
        for section in SECTION_ORDER:
            marker = self._section_title(section)
            count = rendered_report.count(marker)
            if count == 0:
                errors.append(f"missing_section:{section}")
            if count > 1:
                errors.append(f"duplicate_section:{section}")
            position = rendered_report.find(marker)
            if position >= 0:
                section_positions.append(position)
        if section_positions != sorted(section_positions):
            errors.append("section_order_invalid")

        first_content = rendered_report[len(REPORT_BEGIN_MARKER):].lstrip()
        if first_content.startswith((",", "}", "]", ":", "'")):
            errors.append("partial_beginning_detected")
        if self._ends_inside_structure(rendered_report):
            errors.append("incomplete_ending_detected")
        if RAW_STRUCTURE_PATTERN.search(rendered_report):
            errors.append("raw_python_structure_detected")
        if "UNKNOWN" in rendered_report:
            errors.append("unknown_value_detected")
        return errors

    def write_text_artifact(self, text: str, path: Path) -> None:
        self._atomic_write_text(text, path)

    def write_diagnostic_artifact(self, payload: Any, path: Path) -> None:
        diagnostic_text = json.dumps(
            self._json_safe(payload),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._atomic_write_text(diagnostic_text, path)

    def report(self) -> dict[str, Any]:
        return dict(self.metrics)

    def _minimal_report_projection(
        self,
        report_state: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(report_state, dict):
            return {}
        training = report_state.get("training_report", {})
        training = training if isinstance(training, dict) else {}
        performance = report_state.get("performance_report", {})
        performance = performance if isinstance(performance, dict) else {}
        task_results = [
            {
                "task": item.get("task"),
                "status": item.get("status"),
                **({"error": item.get("error")} if item.get("error") else {}),
            }
            for item in list(report_state.get("multi_task_results", []) or [])[:20]
            if isinstance(item, dict)
        ]
        training_task_results = [
            {
                "task": item.get("task"),
                "status": item.get("status"),
                **({"error": item.get("error")} if item.get("error") else {}),
            }
            for item in list(training.get("multi_task_results", []) or [])[:20]
            if isinstance(item, dict)
        ]
        return {
            "system": report_state.get("system", "nexryn_runtime"),
            "runtime_status": report_state.get("runtime_status"),
            "tasks_executed": report_state.get("tasks_executed"),
            "successful_tasks": report_state.get("successful_tasks"),
            "failed_tasks": report_state.get("failed_tasks"),
            "incomplete_tasks": report_state.get("incomplete_tasks"),
            "multi_task_results": task_results,
            "training_report": {
                "system": training.get("system", "training_report"),
                "tasks_selected": training.get("tasks_selected"),
                "tasks_executed": training.get("tasks_executed"),
                "successful_tasks": training.get("successful_tasks"),
                "failed_tasks": training.get("failed_tasks"),
                "incomplete_tasks": training.get("incomplete_tasks"),
                "multi_task_results": training_task_results,
                "concepts_discovered": dict(
                    list((training.get("concepts_discovered", {}) or {}).items())[:24]
                ) if isinstance(training.get("concepts_discovered"), dict) else {},
                "training_report_projection_guard": {
                    **dict(training.get("training_report_projection_guard", {}) or {}),
                    "final_renderer_minimal_projection": True,
                },
                "performance_report": self._compact_metric_map(
                    training.get("performance_report", {})
                ),
            },
            "performance_report": self._compact_metric_map(performance),
            "execution_timing": self._compact_metric_map(
                report_state.get("execution_timing", {})
            ),
            "report_projection_guard": {
                "report_level": "minimal",
                "raw_runtime_state_omitted": True,
                "final_renderer_minimal_projection": True,
                "projected_task_result_count": len(task_results),
                "projected_training_task_result_count": len(training_task_results),
            },
        }

    def _compact_metric_map(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        allowed = {}
        for key in (
            "system",
            "total_runtime_seconds",
            "active_compute_time_seconds",
            "untracked_runtime_seconds",
            "execution_time",
            "runtime_summary",
            "cognitive_efficiency",
            "memory_efficiency",
            "shutdown_efficiency",
            "top_expensive_modules",
            "stage_metrics",
            "execution_timing_state",
            "timing_records",
            "runtime_attribution_report",
        ):
            item = value.get(key)
            if isinstance(item, list):
                allowed[key] = item[:8]
            elif isinstance(item, dict):
                allowed[key] = {
                    sub_key: sub_value
                    for sub_key, sub_value in item.items()
                    if isinstance(sub_value, (str, int, float, bool, type(None)))
                }
            elif item is not None:
                allowed[key] = item
        return allowed

    def _canonical_state(
        self,
        report_state: dict[str, Any],
        *,
        runtime_metadata: dict[str, Any],
        report_level: str,
        binding_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        performance = self._first_dict(
            report_state,
            "performance_report",
            "PERFORMANCE_REPORT",
        )
        cognitive_runtime = self._first_dict(
            report_state,
            "COGNITIVE_RUNTIME_REPORT",
            "cognitive_runtime_report",
        )
        lifecycle = self._first_dict(
            report_state,
            "RUNTIME_LIFECYCLE_REPORT",
            "runtime_lifecycle_report",
            source=performance,
        )
        observability = self._first_dict(
            report_state,
            "RUNTIME_OBSERVABILITY_REPORT",
            "runtime_observability_report",
            source=performance,
        )
        binding = self._first_dict(
            report_state,
            "EXECUTION_BINDING_REPORT",
            "execution_binding_report",
            source=performance,
        )
        search = self._first_dict(
            report_state,
            "COGNITIVE_SEARCH_REPORT",
            "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT",
            "COGNITIVE_ROUTE_INTELLIGENCE_REPORT",
            source=performance,
        )
        program = self._first_dict(
            report_state,
            "PROGRAM_SYNTHESIS_REPORT",
            "program_synthesis_report",
            source=performance,
        )
        knowledge = self._first_dict(
            report_state,
            "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT",
            "KNOWLEDGE_PROPAGATION_REPORT",
            "knowledge_propagation_report",
            source=performance,
        )
        metric_sync = self._first_dict(
            report_state,
            "RUNTIME_METRIC_SYNCHRONIZATION_REPORT",
            "runtime_metric_synchronization_report",
            source=performance,
        )

        return {
            "report_state": report_state,
            "runtime_metadata": runtime_metadata,
            "report_level": report_level,
            "performance": performance,
            "cognitive_runtime": cognitive_runtime,
            "lifecycle": lifecycle,
            "observability": observability,
            "binding": binding,
            "search": search,
            "program": program,
            "knowledge": knowledge,
            "metric_sync": metric_sync,
            "report_binding": binding_result or {},
        }

    def _render_full_report(self, canonical: dict[str, Any]) -> str:
        sections = [
            self._render_header(canonical),
            self._render_execution_summary(canonical),
            self._render_cognitive_outputs(canonical),
            self._render_program_quality(canonical),
            self._render_unified_concept_lifecycle(canonical),
            self._render_program_generation(canonical),
            self._render_program_blueprint_intelligence(canonical),
            self._render_cognitive_program_lifecycle(canonical),
            self._render_cognitive_knowledge_domains(canonical),
            self._render_cognitive_domain_intelligence(canonical),
            self._render_cognitive_domain_lifecycle(canonical),
            self._render_cognitive_domain_interaction(canonical),
            self._render_cognitive_domain_governance(canonical),
            self._render_cognitive_domain_ecosystem(canonical),
            self._render_cognitive_domain_constitution(canonical),
            self._render_semantic_compilation(canonical),
            self._render_executable_semantic_coverage(canonical),
            self._render_cognitive_capability_coverage(canonical),
            self._render_transformation_decision(canonical),
            self._render_multi_hypothesis_report(canonical),
            self._render_candidate_proposal(canonical),
            self._render_candidate_arena(canonical),
            self._render_counterfactual_reasoning(canonical),
            self._render_executable_intelligence(canonical),
            self._render_search_quality(canonical),
            self._render_knowledge_pipeline(canonical),
            self._render_system_health(canonical),
            self._render_timing_summary(canonical),
            self._render_stage_timing(canonical),
            self._render_resource_summary(canonical),
            self._render_diagnostic_timing_detail(canonical),
            self._render_warnings(canonical),
            self._render_runtime_metadata(canonical),
            self._render_technical_appendix(canonical),
            self._render_final_status(canonical),
        ]
        text = "\n".join([REPORT_BEGIN_MARKER, *sections, REPORT_END_MARKER])
        return self._normalize_text(text)

    def _render_budget_summary(
        self,
        canonical: dict[str, Any],
        full_report: str,
    ) -> str:
        canonical = dict(canonical)
        canonical["technical_appendix_note"] = (
            "Console budget exceeded; full diagnostic payload is available "
            "through runtime_diagnostic_report.json when enabled."
        )
        text = "\n".join([
            REPORT_BEGIN_MARKER,
            self._render_header(canonical),
            self._render_execution_summary(canonical),
            self._render_cognitive_outputs(canonical),
            self._render_program_quality(canonical),
            self._render_unified_concept_lifecycle(canonical),
            self._render_program_generation(canonical),
            self._render_program_blueprint_intelligence(canonical),
            self._render_cognitive_program_lifecycle(canonical),
            self._render_cognitive_knowledge_domains(canonical),
            self._render_cognitive_domain_intelligence(canonical),
            self._render_cognitive_domain_lifecycle(canonical),
            self._render_cognitive_domain_interaction(canonical),
            self._render_cognitive_domain_governance(canonical),
            self._render_cognitive_domain_ecosystem(canonical),
            self._render_cognitive_domain_constitution(canonical),
            self._render_semantic_compilation(canonical),
            self._render_executable_semantic_coverage(canonical),
            self._render_cognitive_capability_coverage(canonical),
            self._render_transformation_decision(canonical),
            self._render_multi_hypothesis_report(canonical),
            self._render_candidate_proposal(canonical),
            self._render_candidate_arena(canonical),
            self._render_counterfactual_reasoning(canonical),
            self._render_executable_intelligence(canonical),
            self._render_search_quality(canonical),
            self._render_knowledge_pipeline(canonical),
            self._render_system_health(canonical),
            self._render_timing_summary(canonical),
            self._render_stage_timing(canonical),
            self._render_resource_summary(canonical),
            self._render_diagnostic_timing_detail(canonical),
            self._render_warnings(canonical),
            self._render_runtime_metadata(canonical),
            self._section("OPTIONAL TECHNICAL APPENDIX", [
                "Console Appendix: omitted",
                f"Full Report Characters: {len(full_report)}",
                canonical["technical_appendix_note"],
            ]),
            self._render_final_status(canonical),
            REPORT_END_MARKER,
        ])
        return self._normalize_text(text)

    def _render_header(self, canonical: dict[str, Any]) -> str:
        metadata = canonical["runtime_metadata"]
        return self._section("REPORT HEADER", [
            f"System Name: {self._value(metadata.get('system'), 'NEXRYN')}",
            f"Execution Mode: {self._field(canonical, 'execution_mode')}",
            f"Execution Profile: {self._field(canonical, 'execution_profile')}",
            f"Report Level: {canonical['report_level']}",
            "Execution Identifier: "
            f"{self._field(canonical, 'execution_identifier')}",
            f"Timestamp: {self._field(canonical, 'timestamp')}",
            "Runtime Status: "
            f"{self._field(canonical, 'runtime_status')}",
        ])

    def _render_execution_summary(self, canonical: dict[str, Any]) -> str:
        state = canonical["report_state"]
        performance = canonical["performance"]
        lifecycle = canonical["lifecycle"]
        return self._section("EXECUTION SUMMARY", [
            f"Total Executions: {self._field(canonical, 'total_executions')}",
            f"Completed Executions: {self._field(canonical, 'completed_executions')}",
            f"Archived Executions: {self._field(canonical, 'archived_executions')}",
            f"Execution Coverage: {self._field(canonical, 'execution_coverage')}",
            f"Snapshot Coverage: {self._field(canonical, 'snapshot_coverage')}",
            f"Lifecycle Coverage: {self._field(canonical, 'lifecycle_coverage')}",
            f"Parent Execution Duration: {self._field(canonical, 'parent_execution_duration')}",
            f"Total Wall Time: {self._field(canonical, 'total_wall_time')}",
            f"Overall Status: {self._field(canonical, 'runtime_status')}",
        ])

    def _render_cognitive_outputs(self, canonical: dict[str, Any]) -> str:
        state = canonical["report_state"]
        performance = canonical["performance"]
        knowledge = canonical["knowledge"]
        return self._section("COGNITIVE OUTPUTS", [
            f"Generated Concepts: {self._field(canonical, 'generated_concepts')}",
            f"Generated Programs: {self._field(canonical, 'generated_programs')}",
            f"Validated Programs: {self._field(canonical, 'validated_programs')}",
            f"Truth Candidates: {self._field(canonical, 'truth_candidates')}",
            f"Generated Memory Entries: {self._field(canonical, 'generated_memory_entries')}",
            f"Semantic Memory Entries: {self._field(canonical, 'semantic_memory_entries')}",
            f"Search Routes: {self._field(canonical, 'search_routes')}",
            f"Experience Count: {self._field(canonical, 'experience_count')}",
            f"Fabric Links: {self._field(canonical, 'fabric_links')}",
        ])

    def _render_program_quality(self, canonical: dict[str, Any]) -> str:
        program = canonical["program"]
        performance = canonical["performance"]
        return self._section("PROGRAM QUALITY", [
            f"Average Program Confidence: {self._field(canonical, 'average_program_confidence')}",
            f"Highest Confidence: {self._field(canonical, 'highest_confidence')}",
            f"Lowest Confidence: {self._field(canonical, 'lowest_confidence')}",
            f"Validation Distribution: {self._field(canonical, 'validation_distribution')}",
        ])

    def _render_unified_concept_lifecycle(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "unified_concept_lifecycle_summary")
        summary = summary if isinstance(summary, dict) else {}
        rows = summary.get("concept_lifecycles") or []
        rows = rows if isinstance(rows, list) else []
        lines = [
            f"Concept Count: {self._value(summary.get('concept_count'))}",
            "Canonical Source: "
            f"{self._value(summary.get('canonical_concept_lifecycle_source'))}",
            "Traceable From Discovery: "
            f"{self._value(summary.get('concepts_traceable_from_discovery'))}",
        ]
        status_counts = summary.get("lifecycle_status_counts") or {}
        if isinstance(status_counts, dict) and status_counts:
            lines.append(
                "Lifecycle Status Counts: "
                + "; ".join(
                    f"{self._value(key)}={self._value(value)}"
                    for key, value in sorted(status_counts.items())
                )
            )
        for row in rows[:12]:
            if not isinstance(row, dict):
                continue
            missing = row.get("missing_requirements") or []
            if not isinstance(missing, list):
                missing = [missing]
            lines.extend([
                "--------------------------------------------------",
                f"Concept: {self._value(row.get('concept_name'))}",
                f"Semantic Cluster: {self._value(row.get('semantic_cluster'))}",
                f"Mental Model: {self._value(row.get('mental_model'))}",
                f"Truth Candidate: {self._value(row.get('truth_candidate_state'))}",
                f"Compiler Support: {self._value(row.get('compiler_supported'))}",
                f"Execution Package: {self._value(row.get('execution_package_available'))}",
                f"Candidate Generation State: {self._value(row.get('candidate_generated'))}",
                "Execution State: "
                f"attempted={self._value(row.get('execution_attempted'))}, "
                f"success={self._value(row.get('execution_success'))}",
                f"Prediction Contribution: {self._value(row.get('prediction_contribution'))}",
                f"Semantic Memory Integration: {self._value(row.get('semantic_memory_integrated'))}",
                f"Missing Requirements: {', '.join(str(item) for item in missing) if missing else 'Not Available'}",
                f"Lifecycle Status: {self._value(row.get('lifecycle_status'))}",
            ])
        if len(rows) > 12:
            lines.append(f"Additional Concepts Omitted: {len(rows) - 12}")
        return self._section("UNIFIED CONCEPT LIFECYCLE REPORT", lines)

    def _render_program_generation(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "program_generation_summary")
        summary = summary if isinstance(summary, dict) else {}
        blueprints = summary.get("program_blueprints") or []
        blueprints = blueprints if isinstance(blueprints, list) else []
        missing = summary.get("missing_requirements") or []
        missing = missing if isinstance(missing, list) else [missing]
        lines = [
            f"Generated Programs: {self._value(summary.get('generated_programs'))}",
            f"Eligible Concepts: {self._value(summary.get('eligible_concepts'))}",
            f"Generated Blueprints: {self._value(summary.get('generated_blueprints'))}",
            f"Blocked Programs: {self._value(summary.get('blocked_programs'))}",
            f"Missing Requirements: {', '.join(str(item) for item in missing) if missing else 'Not Available'}",
            f"Generation Success Rate: {self._percent(summary.get('generation_success_rate'))}",
            f"Execution Agnostic: {self._value(summary.get('execution_agnostic'))}",
            f"Competition Agnostic: {self._value(summary.get('competition_agnostic'))}",
        ]
        for blueprint in blueprints[:12]:
            if not isinstance(blueprint, dict):
                continue
            blueprint_missing = blueprint.get("missing_requirements") or []
            if not isinstance(blueprint_missing, list):
                blueprint_missing = [blueprint_missing]
            lines.extend([
                "--------------------------------------------------",
                f"Program: {self._label(str(blueprint.get('program_type') or 'program'))}",
                f"Concept: {self._value(blueprint.get('concept_name'))}",
                f"Semantic Cluster: {self._value(blueprint.get('semantic_cluster'))}",
                f"Generation Status: {self._value(blueprint.get('generation_status'))}",
                f"Compiler Support: {self._value(blueprint.get('compiler_supported'))}",
                f"Execution Package: {self._value(blueprint.get('execution_package_available'))}",
                f"Executable: {self._value(blueprint.get('executable'))}",
                f"Candidate Ready: {self._value(blueprint.get('candidate_ready'))}",
                f"Blocking Reason: {self._value(blueprint.get('blocking_reason'))}",
                "Missing Requirements: "
                f"{', '.join(str(item) for item in blueprint_missing) if blueprint_missing else 'Not Available'}",
            ])
        if len(blueprints) > 12:
            lines.append(f"Additional Blueprints Omitted: {len(blueprints) - 12}")
        return self._section("PROGRAM GENERATION REPORT", lines)

    def _render_program_blueprint_intelligence(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "program_blueprint_intelligence_summary")
        summary = summary if isinstance(summary, dict) else {}
        programs = summary.get("program_blueprint_intelligence") or []
        programs = programs if isinstance(programs, list) else []
        readiness_counts = summary.get("execution_readiness_counts") or {}
        readiness_counts = readiness_counts if isinstance(readiness_counts, dict) else {}
        failures = summary.get("validation_failures") or []
        failures = failures if isinstance(failures, list) else [failures]
        lines = [
            f"Program Intelligence Count: {self._value(summary.get('program_intelligence_count'))}",
            f"Validation Success: {self._value(summary.get('validation_success'))}",
            f"Silent Capability Failures: {self._value(summary.get('capability_failures_silent'))}",
            "Validation Failures: "
            f"{', '.join(str(item) for item in failures) if failures else 'Not Available'}",
        ]
        if readiness_counts:
            lines.append(
                "Execution Readiness Counts: "
                + "; ".join(
                    f"{self._value(key)}={self._value(value)}"
                    for key, value in sorted(readiness_counts.items())
                )
            )
        for program in programs[:12]:
            if not isinstance(program, dict):
                continue
            supported = program.get("supported_concepts") or []
            supported = supported if isinstance(supported, list) else [supported]
            required = program.get("required_packages") or []
            required = required if isinstance(required, list) else [required]
            missing = program.get("missing_requirements") or []
            missing = missing if isinstance(missing, list) else [missing]
            limitations = program.get("capability_limitations") or []
            limitations = limitations if isinstance(limitations, list) else [limitations]
            lines.extend([
                "--------------------------------------------------",
                f"Program: {self._label(str(program.get('program_type') or 'program'))}",
                f"Semantic Family: {self._value(program.get('semantic_family'))}",
                f"Mental Model: {self._value(program.get('mental_model'))}",
                "Supported Concepts: "
                f"{', '.join(str(item) for item in supported) if supported else 'Not Available'}",
                f"Execution Readiness: {self._value(program.get('execution_ready'))}",
                f"Candidate Readiness: {self._value(program.get('candidate_ready'))}",
                f"Compiler Support: {self._value(program.get('compiler_supported'))}",
                f"Validation Ready: {self._value(program.get('validation_ready'))}",
                f"Execution Package: {self._value(program.get('execution_package_available'))}",
                "Required Packages: "
                f"{', '.join(str(item) for item in required) if required else 'Not Available'}",
                "Missing Requirements: "
                f"{', '.join(str(item) for item in missing) if missing else 'Not Available'}",
                "Capability Limitations: "
                f"{', '.join(str(item) for item in limitations) if limitations else 'Not Available'}",
                f"Capability Status: {self._value(program.get('lifecycle_status'))}",
            ])
        if len(programs) > 12:
            lines.append(f"Additional Program Intelligence Rows Omitted: {len(programs) - 12}")
        return self._section("PROGRAM BLUEPRINT INTELLIGENCE REPORT", lines)

    def _render_cognitive_program_lifecycle(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_program_lifecycle_summary")
        summary = summary if isinstance(summary, dict) else {}
        registry = summary.get("program_registry") or []
        registry = registry if isinstance(registry, list) else []
        lines = [
            f"Total Program Blueprints: {self._value(summary.get('total_program_blueprints'))}",
            f"Operational Program Count: {self._value(summary.get('operational_program_count'))}",
            f"Blocked Program Count: {self._value(summary.get('blocked_program_count'))}",
            "Partially Operational Program Count: "
            f"{self._value(summary.get('partially_operational_program_count'))}",
            f"Silent Lifecycle Failures: {self._value(summary.get('silent_lifecycle_failures'))}",
            "Readiness Distribution: "
            f"{self._inline_map(summary.get('readiness_distribution'))}",
            "Maturity Distribution: "
            f"{self._inline_map(summary.get('maturity_distribution'))}",
            "Semantic Family Coverage: "
            f"{self._inline_map(summary.get('semantic_family_coverage'))}",
        ]
        for row in registry[:12]:
            if not isinstance(row, dict):
                continue
            required = row.get("required_packages") or []
            required = required if isinstance(required, list) else [required]
            missing = row.get("missing_requirements") or []
            missing = missing if isinstance(missing, list) else [missing]
            supported = row.get("supported_concepts") or []
            supported = supported if isinstance(supported, list) else [supported]
            failures = row.get("lifecycle_failures") or []
            failure_bits = []
            if isinstance(failures, list):
                for failure in failures[:4]:
                    if isinstance(failure, dict):
                        failure_bits.append(
                            f"{failure.get('failed_stage')}:{failure.get('reason')}"
                        )
            lines.extend([
                "--------------------------------------------------",
                f"Program: {self._label(str(row.get('program_type') or 'program'))}",
                f"Semantic Family: {self._value(row.get('semantic_family'))}",
                f"Lifecycle Status: {self._value(row.get('lifecycle_status'))}",
                f"Maturity Level: {self._value(row.get('maturity_level'))}",
                f"Execution Readiness: {self._value(row.get('execution_readiness'))}",
                f"Candidate Readiness: {self._value(row.get('candidate_readiness'))}",
                f"Operational Readiness: {self._value(row.get('operational_readiness'))}",
                "Required Packages: "
                f"{', '.join(str(item) for item in required) if required else 'Not Available'}",
                "Missing Requirements: "
                f"{', '.join(str(item) for item in missing) if missing else 'Not Available'}",
                "Supported Concepts: "
                f"{', '.join(str(item) for item in supported) if supported else 'Not Available'}",
                f"Capability Profile: {self._compact_value(row.get('capability_profile'))}",
                "Lifecycle Failures: "
                f"{', '.join(failure_bits) if failure_bits else 'Not Available'}",
            ])
        if len(registry) > 12:
            lines.append(f"Additional Program Lifecycle Rows Omitted: {len(registry) - 12}")
        return self._section("COGNITIVE PROGRAM LIFECYCLE REPORT", lines)

    def _render_cognitive_knowledge_domains(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_knowledge_domains_summary")
        summary = summary if isinstance(summary, dict) else {}
        domains = summary.get("domains") or []
        domains = domains if isinstance(domains, list) else []
        lines = [
            f"Domain Count: {self._value(summary.get('domain_count'))}",
            f"Validation Success: {self._value(summary.get('validation_success'))}",
            "Silent Domain Assignment Failures: "
            f"{self._value(summary.get('silent_domain_assignment_failures'))}",
            "Orphan Concepts: "
            f"{self._value(summary.get('orphan_concepts'))}",
            "Missing Domain Ownership: "
            f"{self._value(summary.get('missing_domain_ownership'))}",
        ]
        invalid_family = summary.get("invalid_family_assignments") or []
        invalid_model = summary.get("invalid_mental_model_assignments") or []
        invalid_program = summary.get("invalid_program_blueprint_assignments") or []
        if invalid_family:
            lines.append(f"Invalid Family Assignments: {self._value(invalid_family)}")
        if invalid_model:
            lines.append(f"Invalid Mental Model Assignments: {self._value(invalid_model)}")
        if invalid_program:
            lines.append(f"Invalid Program Blueprint Assignments: {self._value(invalid_program)}")
        for domain in domains[:15]:
            if not isinstance(domain, dict):
                continue
            families = domain.get("semantic_families") or []
            families = families if isinstance(families, list) else [families]
            mental_models = domain.get("mental_models") or []
            mental_models = mental_models if isinstance(mental_models, list) else [mental_models]
            programs = domain.get("program_blueprints") or []
            programs = programs if isinstance(programs, list) else [programs]
            missing = domain.get("missing_capabilities") or []
            missing = missing if isinstance(missing, list) else [missing]
            operational = domain.get("operational_capabilities") or []
            operational = operational if isinstance(operational, list) else [operational]
            lines.extend([
                "--------------------------------------------------",
                f"Domain: {self._value(domain.get('domain_name'))}",
                "Semantic Families: "
                f"{', '.join(str(item) for item in families) if families else 'Not Available'}",
                "Mental Models: "
                f"{', '.join(str(item) for item in mental_models) if mental_models else 'Not Available'}",
                "Program Blueprints: "
                f"{', '.join(str(item) for item in programs) if programs else 'Not Available'}",
                f"Concept Count: {self._value(domain.get('concept_count'))}",
                "Execution Package Count: "
                f"{self._value(domain.get('execution_package_count'))}",
                f"Domain Maturity: {self._value(domain.get('maturity_level'))}",
                f"Operational Status: {self._value(domain.get('lifecycle_status'))}",
                "Operational Capabilities: "
                f"{', '.join(str(item) for item in operational) if operational else 'Not Available'}",
                "Missing Capabilities: "
                f"{', '.join(str(item) for item in missing) if missing else 'Not Available'}",
            ])
        if len(domains) > 15:
            lines.append(f"Additional Cognitive Domains Omitted: {len(domains) - 15}")
        return self._section("COGNITIVE KNOWLEDGE DOMAINS REPORT", lines)

    def _render_cognitive_domain_intelligence(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_domain_intelligence_summary")
        summary = summary if isinstance(summary, dict) else {}
        domains = summary.get("domain_intelligence") or []
        domains = domains if isinstance(domains, list) else []
        active_domains = [
            domain
            for domain in domains
            if isinstance(domain, dict)
            and (
                domain.get("semantic_concept_count")
                or domain.get("mental_model_count")
                or domain.get("program_blueprint_count")
                or domain.get("execution_package_count")
                or domain.get("operational_capability_count")
                or domain.get("missing_capabilities")
            )
        ]
        failures = summary.get("validation_failures") or []
        failures = failures if isinstance(failures, list) else [failures]
        lines = [
            f"Domain Intelligence Count: {self._value(summary.get('domain_intelligence_count'))}",
            f"Validation Success: {self._value(summary.get('validation_success'))}",
            "Silent Domain Intelligence Failures: "
            f"{self._value(summary.get('silent_domain_intelligence_failures'))}",
            "Readiness Distribution: "
            f"{self._inline_map(summary.get('readiness_distribution'))}",
            f"Validation Failures: {self._value(failures)}",
        ]
        for domain in active_domains[:12]:
            if not isinstance(domain, dict):
                continue
            semantic_capabilities = domain.get("semantic_capabilities") or []
            semantic_capabilities = semantic_capabilities if isinstance(semantic_capabilities, list) else [semantic_capabilities]
            operational = domain.get("operational_capabilities") or []
            operational = operational if isinstance(operational, list) else [operational]
            required_domains = domain.get("required_domains") or []
            required_domains = required_domains if isinstance(required_domains, list) else [required_domains]
            optional_domains = domain.get("optional_domains") or []
            optional_domains = optional_domains if isinstance(optional_domains, list) else [optional_domains]
            families = domain.get("semantic_families") or []
            families = families if isinstance(families, list) else [families]
            mental_models = domain.get("mental_models") or []
            mental_models = mental_models if isinstance(mental_models, list) else [mental_models]
            programs = domain.get("program_blueprints") or []
            programs = programs if isinstance(programs, list) else [programs]
            packages = domain.get("execution_packages") or []
            packages = packages if isinstance(packages, list) else [packages]
            missing = domain.get("missing_capabilities") or []
            missing = missing if isinstance(missing, list) else [missing]
            supported_operations = domain.get("supported_operations") or []
            supported_operations = supported_operations if isinstance(supported_operations, list) else [supported_operations]
            lines.extend([
                "--------------------------------------------------",
                f"Domain Name: {self._value(domain.get('domain_name'))}",
                "Semantic Capabilities: "
                f"{', '.join(str(item) for item in semantic_capabilities) if semantic_capabilities else 'Not Available'}",
                "Operational Capabilities: "
                f"{', '.join(str(item) for item in operational) if operational else 'Not Available'}",
                "Domain Dependencies: "
                f"{', '.join(str(item) for item in required_domains) if required_domains else 'Independent'}",
                "Optional Domains: "
                f"{', '.join(str(item) for item in optional_domains) if optional_domains else 'Not Available'}",
                "Semantic Families: "
                f"{', '.join(str(item) for item in families) if families else 'Not Available'}",
                "Mental Models: "
                f"{', '.join(str(item) for item in mental_models) if mental_models else 'Not Available'}",
                "Program Blueprints: "
                f"{', '.join(str(item) for item in programs) if programs else 'Not Available'}",
                "Execution Packages: "
                f"{', '.join(str(item) for item in packages) if packages else 'Not Available'}",
                "Supported Operations: "
                f"{', '.join(str(item) for item in supported_operations) if supported_operations else 'Not Available'}",
                "Missing Capabilities: "
                f"{', '.join(str(item) for item in missing) if missing else 'Not Available'}",
                f"Domain Readiness: {self._value(domain.get('readiness_state'))}",
                f"Maturity Level: {self._value(domain.get('maturity_level'))}",
                "Coverage Counts: "
                f"concepts={self._value(domain.get('semantic_concept_count'))}, "
                f"families={self._value(domain.get('semantic_family_count'))}, "
                f"mental_models={self._value(domain.get('mental_model_count'))}, "
                f"programs={self._value(domain.get('program_blueprint_count'))}, "
                f"packages={self._value(domain.get('execution_package_count'))}, "
                f"operational={self._value(domain.get('operational_capability_count'))}",
            ])
        if len(active_domains) > 12:
            lines.append(f"Additional Active Domain Intelligence Rows Omitted: {len(active_domains) - 12}")
        inactive_count = len(domains) - len(active_domains)
        if inactive_count > 0:
            lines.append(f"Inactive Domain Intelligence Rows Omitted: {inactive_count}")
        return self._section("COGNITIVE DOMAIN INTELLIGENCE REPORT", lines)

    def _render_cognitive_domain_lifecycle(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_domain_lifecycle_summary")
        summary = summary if isinstance(summary, dict) else {}
        registry = summary.get("domain_registry") or []
        registry = registry if isinstance(registry, list) else []
        active_rows = [
            row for row in registry
            if isinstance(row, dict)
            and (
                row.get("semantic_capability_evolution")
                or row.get("mental_model_evolution")
                or row.get("program_blueprint_evolution")
                or row.get("execution_capability_evolution")
                or row.get("operational_capability_evolution")
                or row.get("missing_capabilities")
            )
        ]
        lines = [
            f"Total Domains: {self._value(summary.get('total_domains'))}",
            f"Operational Domains: {self._value(summary.get('operational_domains'))}",
            "Partially Operational Domains: "
            f"{self._value(summary.get('partially_operational_domains'))}",
            f"Foundational Domains: {self._value(summary.get('foundational_domains'))}",
            f"Advanced Domains: {self._value(summary.get('advanced_domains'))}",
            "Domain Readiness Distribution: "
            f"{self._inline_map(summary.get('domain_readiness_distribution'))}",
            "Lifecycle Distribution: "
            f"{self._inline_map(summary.get('lifecycle_distribution'))}",
            "Capability Distribution: "
            f"{self._inline_map(summary.get('capability_distribution'))}",
            "Silent Domain Lifecycle Failures: "
            f"{self._value(summary.get('silent_domain_lifecycle_failures'))}",
        ]
        for row in active_rows[:12]:
            required = row.get("required_domains") or []
            required = required if isinstance(required, list) else [required]
            optional = row.get("optional_domains") or []
            optional = optional if isinstance(optional, list) else [optional]
            missing = row.get("missing_capabilities") or []
            missing = missing if isinstance(missing, list) else [missing]
            failures = row.get("lifecycle_failures") or []
            failure_bits = []
            if isinstance(failures, list):
                for failure in failures[:4]:
                    if isinstance(failure, dict):
                        failure_bits.append(
                            f"{failure.get('failed_lifecycle_stage')}:{failure.get('reason')}"
                        )
            inherited = row.get("inherited_capabilities") or {}
            lines.extend([
                "--------------------------------------------------",
                f"Domain Name: {self._value(row.get('domain_name'))}",
                f"Lifecycle Stage: {self._value(row.get('lifecycle_stage'))}",
                f"Maturity Level: {self._value(row.get('maturity_level'))}",
                "Readiness States: "
                f"Semantic={self._value(row.get('semantic_readiness'))}; "
                f"Mental Models={self._value(row.get('mental_model_readiness'))}; "
                f"Programs={self._value(row.get('program_readiness'))}; "
                f"Execution={self._value(row.get('execution_readiness'))}; "
                f"Candidate={self._value(row.get('candidate_readiness'))}; "
                f"Operational={self._value(row.get('operational_readiness'))}",
                "Dependencies: "
                f"{', '.join(str(item) for item in required) if required else 'Independent'}",
                "Optional Dependencies: "
                f"{', '.join(str(item) for item in optional) if optional else 'Not Available'}",
                "Inherited Capabilities: "
                f"{self._inline_map(inherited)}",
                "Missing Capabilities: "
                f"{', '.join(str(item) for item in missing) if missing else 'Not Available'}",
                "Lifecycle Failures: "
                f"{', '.join(failure_bits) if failure_bits else 'Not Available'}",
                f"Operational Status: {self._value(row.get('operational_status'))}",
            ])
        if len(active_rows) > 12:
            lines.append(f"Additional Active Domain Lifecycle Rows Omitted: {len(active_rows) - 12}")
        inactive_count = len(registry) - len(active_rows)
        if inactive_count > 0:
            lines.append(f"Inactive Domain Lifecycle Rows Omitted: {inactive_count}")
        return self._section("COGNITIVE DOMAIN LIFECYCLE REPORT", lines)

    def _render_cognitive_domain_interaction(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_domain_interaction_summary")
        summary = summary if isinstance(summary, dict) else {}
        reports = summary.get("domain_interaction_reports") or []
        reports = reports if isinstance(reports, list) else []
        active_reports = [
            row for row in reports
            if isinstance(row, dict)
            and (
                row.get("collaborating_domains")
                or row.get("shared_capabilities")
                or row.get("private_capabilities")
                or row.get("operational_capability_composition")
                or row.get("missing_collaborative_capabilities")
            )
        ]
        compositions = summary.get("operational_capability_compositions") or []
        compositions = compositions if isinstance(compositions, list) else []
        readiness_rows = summary.get("cross_domain_operational_readiness") or []
        readiness_rows = readiness_rows if isinstance(readiness_rows, list) else []
        lines = [
            f"Domain Interactions: {self._value(summary.get('domain_interaction_count'))}",
            "Operational Capability Lifecycle Count: "
            f"{self._value(summary.get('operational_capability_lifecycle_count'))}",
            "Capability Promotion Candidates: "
            f"{self._value(summary.get('capability_promotion_candidate_count'))}",
            "Sandbox Operational Capabilities: "
            f"{self._value(summary.get('sandbox_operational_capability_count'))}",
            "Promoted Capabilities: "
            f"{self._value(summary.get('promoted_capability_count'))}",
            "Reusable Operational Capabilities: "
            f"{self._value(summary.get('reusable_operational_capability_count'))}",
            "Capability Organisms: "
            f"{self._value(summary.get('capability_organism_count'))}",
            "Emerging Capabilities: "
            f"{self._value(summary.get('emerging_capability_count'))}",
            "Developing Capabilities: "
            f"{self._value(summary.get('developing_capability_count'))}",
            "Evolving Capabilities: "
            f"{self._value(summary.get('evolving_capability_count'))}",
            "Capability Economy Invest: "
            f"{self._value(summary.get('capability_invest_count'))}",
            "Capability Economy Watch: "
            f"{self._value(summary.get('capability_watch_count'))}",
            "Capability Economy Hold: "
            f"{self._value(summary.get('capability_hold_count'))}",
            "Capability Economy Archive: "
            f"{self._value(summary.get('capability_archive_count'))}",
            "Governance Review Capabilities: "
            f"{self._value(summary.get('governance_review_capability_count'))}",
            "Governance Blocked Capabilities: "
            f"{self._value(summary.get('governance_blocked_capability_count'))}",
            f"Validation Success: {self._value(summary.get('validation_success'))}",
            "Dependency Graph: "
            f"{self._inline_map(summary.get('dependency_graph'))}",
        ]
        if canonical["report_level"] == "diagnostic":
            lines.insert(
                1,
                f"Collaboration Score: {self._percent(summary.get('collaboration_score'))}",
            )
            lines.insert(
                3,
                "Silent Interaction Failures: "
                f"{self._value(summary.get('silent_domain_interaction_failures'))}",
            )
        for index, composition in enumerate(compositions[:3]):
            if isinstance(composition, dict):
                lines.append(
                    "Operational Capability Composition: "
                    f"{self._value(composition.get('composition_name'))} "
                    f"[{self._value(composition.get('composition_status'))}]"
                )
                if canonical["report_level"] == "diagnostic" or index == 0:
                    lines.append(
                    "  Cross-Domain Readiness: "
                    f"{self._percent(composition.get('cross_domain_operational_readiness'))}"
                    )
                lines.append(
                    "  Capability Lifecycle: "
                    f"{self._value(composition.get('lifecycle_state'))}; "
                    f"Blocking Stage: {self._value(composition.get('blocking_stage'))}; "
                    f"Governance: {self._value(composition.get('governance_status'))}; "
                    f"Validation: {self._value(composition.get('validation_status'))}"
                )
                lines.append(
                    "  Capability Promotion: "
                    f"{self._value(composition.get('promotion_state'))}; "
                    f"Score: {self._percent(composition.get('promotion_score'))}; "
                    f"Registry: {self._value(composition.get('registry_eligibility'))}"
                )
                identity = composition.get("capability_identity") or {}
                identity = identity if isinstance(identity, dict) else {}
                lines.append(
                    "  Capability Growth: "
                    f"{self._value(composition.get('growth_stage'))}; "
                    f"Organism: {self._value(composition.get('organism_state'))}; "
                    f"Growth Score: {self._percent(composition.get('growth_score'))}; "
                    f"Evolution: {self._percent(composition.get('evolution_readiness'))}"
                )
                if canonical["report_level"] == "diagnostic" or index == 0:
                    lines.append(
                        "  Capability Identity: "
                        f"{self._value(identity.get('capability_id'))} "
                        f"v{self._value(identity.get('version'))}"
                    )
                lines.append(
                    "  Capability Economy: "
                    f"{self._value(composition.get('resource_decision'))}; "
                    f"Value: {self._percent(composition.get('value_score'))}; "
                    f"Benefit: {self._percent(composition.get('operational_benefit'))}; "
                    f"Net: {self._percent(composition.get('net_economic_value'))}"
                )
                if canonical["report_level"] == "diagnostic" or index == 0:
                    budget = composition.get("resource_budget") or {}
                    budget = budget if isinstance(budget, dict) else {}
                    lines.append(
                        "  Capability Resource Budget: "
                        f"growth={self._value(budget.get('growth_budget'))}, "
                        f"evolution={self._value(budget.get('evolution_budget'))}, "
                        f"promotion={self._value(budget.get('promotion_budget'))}, "
                        f"maintenance={self._value(budget.get('maintenance_budget'))}, "
                        f"retirement={self._value(budget.get('retirement_budget'))}"
                    )
                    lines.append(
                        "  Economy Rationale: "
                        f"{self._value(composition.get('economy_rationale'))}"
                    )
                blockers = composition.get("promotion_blockers") or []
                blockers = blockers if isinstance(blockers, list) else [blockers]
                if blockers and (canonical["report_level"] == "diagnostic" or index == 0):
                    lines.append(
                        "  Promotion Blockers: "
                        + ", ".join(str(item) for item in blockers[:5])
                    )
        readiness_limit = 3 if canonical["report_level"] == "diagnostic" else 0
        for row in readiness_rows[:readiness_limit]:
            if isinstance(row, dict):
                domains = row.get("participating_domains") or []
                domains = domains if isinstance(domains, list) else [domains]
                short_domains = [
                    str(item).replace(" Cognitive Domain", "")
                    for item in domains
                ]
                lines.append(
                    "Cross-Domain Operational Readiness: "
                    f"{' + '.join(short_domains)} = "
                    f"{self._percent(row.get('cross_domain_operational_readiness'))} "
                    f"[{self._value(row.get('composition_status'))}]"
                )
        for row in active_reports[:6]:
            collaborators = row.get("collaborating_domains") or []
            collaborators = collaborators if isinstance(collaborators, list) else [collaborators]
            shared = row.get("shared_capabilities") or []
            shared = shared if isinstance(shared, list) else [shared]
            private = row.get("private_capabilities") or []
            private = private if isinstance(private, list) else [private]
            dependencies = row.get("dependency_relationships") or []
            dependencies = dependencies if isinstance(dependencies, list) else [dependencies]
            compositions_for_domain = row.get("operational_capability_composition") or []
            compositions_for_domain = compositions_for_domain if isinstance(compositions_for_domain, list) else [compositions_for_domain]
            missing = row.get("missing_collaborative_capabilities") or []
            missing = missing if isinstance(missing, list) else [missing]
            lines.extend([
                "--------------------------------------------------",
                f"Domain Name: {self._value(row.get('domain_name'))}",
                "Collaborating Domains: "
                f"{', '.join(str(item) for item in collaborators) if collaborators else 'Not Available'}",
                "Shared Capabilities: "
                f"{', '.join(str(item) for item in shared) if shared else 'Not Available'}",
                "Private Capabilities: "
                f"{', '.join(str(item) for item in private) if private else 'Not Available'}",
                "Dependency Relationships: "
                f"{', '.join(str(item) for item in dependencies) if dependencies else 'Independent'}",
                f"Capability Composition Status: {self._value(row.get('capability_composition_status'))}",
                "Operational Capability Composition: "
                f"{', '.join(str(item) for item in compositions_for_domain) if compositions_for_domain else 'Not Available'}",
                "Missing Collaborative Capabilities: "
                f"{', '.join(str(item) for item in missing) if missing else 'Not Available'}",
                f"Collaboration Maturity: {self._value(row.get('collaboration_maturity'))}",
                f"Capability Sharing Maturity: {self._value(row.get('capability_sharing_maturity'))}",
                f"Dependency Maturity: {self._value(row.get('dependency_maturity'))}",
                f"Operational Composition Maturity: {self._value(row.get('operational_composition_maturity'))}",
            ])
        if len(active_reports) > 6:
            lines.append(f"Additional Active Domain Interaction Rows Omitted: {len(active_reports) - 6}")
        inactive = len(reports) - len(active_reports)
        if inactive > 0:
            lines.append(f"Inactive Domain Interaction Rows Omitted: {inactive}")
        return self._section("COGNITIVE DOMAIN INTERACTION REPORT", lines)

    def _render_cognitive_domain_governance(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_domain_governance_summary")
        summary = summary if isinstance(summary, dict) else {}
        rows = summary.get("domain_governance") or []
        rows = rows if isinstance(rows, list) else []
        active_rows = [
            row for row in rows
            if isinstance(row, dict)
            and (
                row.get("capability_conflicts")
                or row.get("boundary_violations")
            )
        ]
        if not active_rows:
            active_rows = [row for row in rows if isinstance(row, dict)][:3]
        lines = [
            f"Domain Governance Count: {self._value(summary.get('domain_governance_count'))}",
            f"Validation Success: {self._value(summary.get('validation_success'))}",
            "Silent Governance Failures: "
            f"{self._value(summary.get('silent_domain_governance_failures'))}",
            f"Capability Conflicts: {self._value(summary.get('capability_conflicts'))}",
            f"Boundary Violations: {self._value(summary.get('boundary_violations'))}",
            f"Migration Events: {self._compact_value(summary.get('migration_history'))}",
        ]
        for row in active_rows[:4]:
            conflicts = row.get("capability_conflicts") or []
            conflicts = conflicts if isinstance(conflicts, list) else [conflicts]
            migrations = row.get("migration_history") or []
            migrations = migrations if isinstance(migrations, list) else [migrations]
            violations = row.get("boundary_violations") or []
            violations = violations if isinstance(violations, list) else [violations]
            missing = row.get("missing_governance_requirements") or []
            missing = missing if isinstance(missing, list) else [missing]
            migration_bits = []
            for event in migrations[:3]:
                if isinstance(event, dict):
                    migration_bits.append(
                        f"{event.get('capability')}:{event.get('previous_owner')}->{event.get('new_owner')}"
                    )
            lines.extend([
                "--------------------------------------------------",
                f"Domain Name: {self._value(row.get('domain_name'))}",
                f"Governance Status: {self._value(row.get('governance_status'))}",
                f"Semantic Integrity: {self._percent(row.get('semantic_coherence_score'))}",
                f"Ownership Integrity: {self._percent(row.get('ownership_consistency_score'))}",
                f"Dependency Integrity: {self._percent(row.get('dependency_consistency_score'))}",
                f"Domain Health Score: {self._percent(row.get('governance_integrity_score'))}",
                f"Capability Conflicts: {self._compact_value(conflicts) if conflicts else 'NONE'}",
                f"Migration Events: {', '.join(migration_bits) if migration_bits else 'NONE'}",
                f"Boundary Violations: {self._compact_value(violations) if violations else 'NONE'}",
                "Missing Governance Requirements: "
                f"{', '.join(str(item) for item in missing) if missing else 'NONE'}",
            ])
        if len(active_rows) > 4:
            lines.append(f"Additional Active Domain Governance Rows Omitted: {len(active_rows) - 4}")
        inactive = len(rows) - len(active_rows)
        if inactive > 0:
            lines.append(f"Inactive Domain Governance Rows Omitted: {inactive}")
        return self._section("COGNITIVE DOMAIN GOVERNANCE REPORT", lines)

    def _render_cognitive_domain_ecosystem(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""

        summary = self._binding_value(canonical, "cognitive_domain_ecosystem_summary")
        summary = summary if isinstance(summary, dict) else {}
        ecosystem = summary.get("ecosystem") or {}
        ecosystem = ecosystem if isinstance(ecosystem, dict) else {}
        coverage = summary.get("global_cognitive_coverage") or {}
        coverage = coverage if isinstance(coverage, dict) else {}
        health = summary.get("ecosystem_health_metrics") or {}
        health = health if isinstance(health, dict) else {}
        lines = [
            f"Total Domains: {self._value(coverage.get('domains'))}",
            f"Operational Domains: {self._value(coverage.get('operational_domains'))}",
            f"Total Semantic Concepts: {self._value(coverage.get('semantic_concepts'))}",
            f"Total Mental Models: {self._value(coverage.get('mental_models'))}",
            f"Total Program Blueprints: {self._value(coverage.get('program_blueprints'))}",
            f"Total Execution Packages: {self._value(coverage.get('execution_packages'))}",
            f"Total Operational Capabilities: {self._value(coverage.get('operational_capabilities'))}",
            f"Candidate Ready Programs: {self._value(coverage.get('candidate_ready_programs'))}",
            f"Capability Coverage: {self._percent(health.get('capability_coverage_score'))}",
            f"Ecosystem Health: {self._percent(health.get('architectural_coherence_score'))}",
            f"Collaboration Score: {self._percent(health.get('collaboration_score'))}",
            f"Operational Readiness: {self._percent(health.get('operational_readiness_score'))}",
            f"Architectural Coherence: {self._percent(health.get('architectural_coherence_score'))}",
            f"Ecosystem Maturity: {self._value(summary.get('ecosystem_maturity'))}",
            f"Domain Distribution: {self._inline_map(summary.get('domain_distribution'))}",
            f"Covered Domains: {self._value(ecosystem.get('covered_domains'))}",
            f"Partially Covered Domains: {self._value(ecosystem.get('partially_covered_domains'))}",
            f"Missing Domains: {self._value(ecosystem.get('missing_domains'))}",
            f"Missing Capabilities: {self._value(summary.get('missing_ecosystem_capabilities'))}",
            f"Cognitive Bottlenecks: {self._compact_value(summary.get('cognitive_bottlenecks'))}",
            f"Cognitive Imbalances: {self._compact_value(summary.get('cognitive_imbalances'))}",
            f"Dependency Graph Summary: {self._compact_value(summary.get('dependency_graph'))}",
            f"Collaboration Summary: {self._compact_value(summary.get('collaboration_graph'))}",
            f"Operational Capability Graph: {self._compact_value(summary.get('operational_capability_graph'))}",
            f"Silent Ecosystem Failures: {self._value(summary.get('silent_ecosystem_failures'))}",
        ]
        return self._section("COGNITIVE DOMAIN ECOSYSTEM REPORT", lines)

    def _render_cognitive_domain_constitution(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""

        summary = self._binding_value(canonical, "cognitive_domain_constitution_summary")
        summary = summary if isinstance(summary, dict) else {}
        metrics = summary.get("constitutional_health_metrics") or {}
        metrics = metrics if isinstance(metrics, dict) else {}
        violations = summary.get("constitutional_violations") or []
        health = summary.get("domain_constitutional_health") or []
        validations = summary.get("constitutional_validations") or {}
        lines = [
            f"Constitutional Status: {self._value(summary.get('constitutional_status'))}",
            f"Constitutional Integrity: {self._percent(metrics.get('constitutional_integrity_score'))}",
            f"Architectural Integrity: {self._percent(metrics.get('architectural_integrity_score'))}",
            f"Semantic Integrity: {self._percent(metrics.get('semantic_integrity_score'))}",
            f"Governance Integrity: {self._percent(metrics.get('governance_integrity_score'))}",
            f"Collaboration Integrity: {self._percent(metrics.get('collaboration_integrity_score'))}",
            f"Ecosystem Coherence: {self._percent(metrics.get('ecosystem_coherence_score'))}",
            f"Constitutional Compliance: {self._percent(metrics.get('constitutional_compliance_score'))}",
            f"Governance Compliance: {self._value(summary.get('governance_compliance'))}",
            f"Ownership Compliance: {self._value(summary.get('ownership_compliance'))}",
            f"Lifecycle Compliance: {self._value(summary.get('lifecycle_compliance'))}",
            f"Constitutional Invariants: {self._value(summary.get('architectural_invariants'))}",
            f"Constitutional Validations: {self._inline_map(validations)}",
            f"Constitutional Violations: {self._compact_value(violations)}",
            f"Domain Constitutional Health: {self._compact_value(health)}",
            f"Silent Constitutional Failures: {self._value(summary.get('silent_constitutional_failures'))}",
        ]
        return self._section("COGNITIVE DOMAIN CONSTITUTION REPORT", lines)

    def _render_semantic_compilation(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "semantic_compilation_summary")
        summary = summary if isinstance(summary, dict) else {}
        diagnostics = self._binding_value(canonical, "semantic_compilation_diagnostics")
        diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
        concepts = summary.get("detected_concepts") or []
        if not isinstance(concepts, list):
            concepts = [concepts]
        parameters = summary.get("parameter_inference") or {}
        parameter_bits = []
        if isinstance(parameters, dict):
            for key in sorted(parameters.keys(), key=str):
                value = parameters.get(key)
                if isinstance(value, (dict, list)):
                    value = self._compact_value(value)
                parameter_bits.append(f"{key}={self._value(value)}")
        lines = [
            f"Detected Concepts: {', '.join(str(item) for item in concepts[:12]) if concepts else 'Not Available'}",
            f"Semantic Intent Router Success: {self._value(summary.get('semantic_intent_routing_success'))}",
            "Semantic Intent Router Integration: "
            f"{self._value(summary.get('semantic_intent_router_integration_status'))}",
            "Compiler Activation Source: "
            f"{self._value(summary.get('compiler_activation_source'))}",
            f"Execution Intents: {self._value(summary.get('execution_intent_count'))}",
            f"Compiler Triggered: {self._value(summary.get('compiler_triggered'))}",
            f"Compiled Candidates: {self._value(summary.get('compiled_candidate_count'))}",
            f"Selected Intent: {self._value(summary.get('selected_intent'))}",
            f"Compiled Operation: {self._value(summary.get('compiled_operation'))}",
            f"Selected Operation: {self._value(summary.get('selected_operation'))}",
            f"Selected From Compiler: {self._value(summary.get('selected_from_compiler'))}",
            f"Compiler Advisory State: {self._value(summary.get('compiler_advisory_state'))}",
            f"Compilation Confidence: {self._value(summary.get('compilation_confidence'))}",
            f"Prediction Accuracy: {self._value(summary.get('prediction_accuracy'))}",
            f"Compilation Status: {self._value(summary.get('compilation_status'))}",
            f"Primitive Executor Called: {self._value(summary.get('primitive_executor_called'))}",
            f"Execution Status: {self._value(summary.get('execution_status'))}",
            f"Failure Cause: {self._value(summary.get('failure_cause'))}",
        ]
        if parameter_bits:
            lines.append(f"Parameter Inference: {'; '.join(parameter_bits[:8])}")
        if canonical["report_level"] == "diagnostic":
            compiler = diagnostics.get("compiler_report", {})
            graph = compiler.get("transformation_graph", {}) if isinstance(compiler, dict) else {}
            plan = compiler.get("transformation_plan", {}) if isinstance(compiler, dict) else {}
            if isinstance(graph, dict):
                lines.append(
                    "Transformation Graph: "
                    f"nodes={self._value(graph.get('node_count'))}, "
                    f"edges={self._value(graph.get('edge_count'))}"
                )
            if isinstance(plan, dict):
                lines.append(f"Transformation Plan Type: {self._value(plan.get('plan_type'))}")
                lines.append(f"Transformation Plan Rationale: {self._value(plan.get('rationale'))}")
        return self._section("SEMANTIC COMPILATION", lines)

    def _render_transformation_decision(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "prediction_provenance_summary")
        summary = summary if isinstance(summary, dict) else {}
        pipeline = summary.get("decision_pipeline") or []
        if not isinstance(pipeline, list):
            pipeline = [pipeline]
        lines = [
            f"Prediction Source: {self._value(summary.get('prediction_source'))}",
            f"Decision Owner: {self._value(summary.get('decision_owner'))}",
            f"Decision Confidence: {self._value(summary.get('decision_confidence'))}",
            f"Winning Candidate: {self._value(summary.get('winning_candidate'))}",
            f"Selected Operation: {self._value(summary.get('selected_operation'))}",
            f"Compiler Attempted: {self._value(summary.get('compiler_attempted'))}",
            f"Compiler Participation: {self._value(summary.get('compiler_participation'))}",
            f"Repair Participation: {self._value(summary.get('repair_participation'))}",
            "Transfer Learning Participation: "
            f"{self._value(summary.get('transfer_learning_participation'))}",
            f"Counterfactual Search: {self._value(summary.get('counterfactual_search'))}",
            f"Program Validation: {self._value(summary.get('program_validation'))}",
            f"Prediction Accuracy: {self._value(summary.get('prediction_accuracy'))}",
            f"Generated Concepts Observed: {self._value(summary.get('generated_concept_count'))}",
            f"Generated Programs Observed: {self._value(summary.get('generated_program_count'))}",
            f"Program Candidates: {self._value(summary.get('candidate_count'))}",
            f"Programs Rejected: {self._value(summary.get('programs_rejected'))}",
            f"Programs Executed: {self._value(summary.get('programs_executed'))}",
            "Decision Pipeline: "
            f"{' -> '.join(str(item) for item in pipeline) if pipeline else 'Not Available'}",
        ]
        if canonical["report_level"] == "diagnostic":
            diagnostics = self._binding_value(canonical, "prediction_provenance_diagnostics")
            diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
            for key in (
                "transformation_synthesis_report",
                "color_mapping_report",
                "adaptive_reuse_report",
                "search_report",
                "repair_report",
            ):
                value = diagnostics.get(key)
                if isinstance(value, dict):
                    lines.append(f"{self._label(key)} Fields: {len(value)}")
        return self._section("TRANSFORMATION DECISION", lines)

    def _render_executable_semantic_coverage(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "executable_semantic_coverage_summary")
        summary = summary if isinstance(summary, dict) else {}
        supported = summary.get("supported_operations") or []
        supported = supported if isinstance(supported, list) else [supported]
        unsupported = summary.get("unsupported_operations") or []
        unsupported = unsupported if isinstance(unsupported, list) else [unsupported]
        missing_clusters = summary.get("missing_cluster_counts") or {}
        lines = [
            f"Generated Concepts: {self._value(summary.get('generated_concepts'))}",
            f"Measured Concepts: {self._value(summary.get('measured_concepts'))}",
            f"Coverage State: {self._value(summary.get('coverage_state'))}",
            f"Executable Concepts: {self._value(summary.get('executable_concepts'))}",
            f"Unsupported Concepts: {self._value(summary.get('unsupported_concepts'))}",
            f"Coverage: {self._percent(summary.get('executable_semantic_coverage'))}",
            f"Coverage Status: {self._value(summary.get('coverage_status'))}",
            f"Measurement Blocker: {self._value(summary.get('measurement_blocker'))}",
            f"Highest Missing Semantic Cluster: {self._value(summary.get('highest_missing_semantic_cluster'))}",
            f"Supported Operations: {', '.join(str(item) for item in supported) if supported else 'Not Available'}",
            f"Unsupported Operations: {', '.join(str(item) for item in unsupported[:12]) if unsupported else 'Not Available'}",
        ]
        if isinstance(missing_clusters, dict) and missing_clusters:
            cluster_bits = [
                f"{cluster}={count}"
                for cluster, count in sorted(missing_clusters.items())
            ]
            lines.append(f"Missing Cluster Counts: {'; '.join(cluster_bits[:8])}")
        return self._section("EXECUTABLE SEMANTIC COVERAGE", lines)

    def _render_cognitive_capability_coverage(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "cognitive_capability_coverage_summary")
        summary = summary if isinstance(summary, dict) else {}
        bottlenecks = summary.get("lowest_coverage_bottlenecks") or []
        bottlenecks = bottlenecks if isinstance(bottlenecks, list) else []
        attrition = summary.get("candidate_attrition_summary") or {}
        attrition = attrition if isinstance(attrition, dict) else {}
        lifecycle = summary.get("end_to_end_program_lifecycle") or {}
        lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
        domain_architecture = summary.get("cognitive_domain_architecture_summary") or {}
        domain_architecture = (
            domain_architecture if isinstance(domain_architecture, dict) else {}
        )
        lineage = summary.get("candidate_source_lineage") or []
        lineage = lineage if isinstance(lineage, list) else []
        survival_distribution = (
            summary.get("capability_survival_state_distribution") or {}
        )
        survival_distribution = (
            survival_distribution
            if isinstance(survival_distribution, dict)
            else {}
        )
        top_incubating = summary.get("top_incubating_capabilities") or []
        top_incubating = top_incubating if isinstance(top_incubating, list) else []
        missing_packages = summary.get("missing_execution_packages") or []
        missing_packages = (
            missing_packages if isinstance(missing_packages, list) else [missing_packages]
        )
        missing_requirements = summary.get("missing_compiler_requirements") or []
        missing_requirements = (
            missing_requirements
            if isinstance(missing_requirements, list)
            else [missing_requirements]
        )
        lines = [
            "Overall Cognitive Capability Coverage: "
            f"{self._percent(summary.get('overall_cognitive_capability_coverage'))}",
            f"Coverage Status: {self._value(summary.get('coverage_status'))}",
            "Architecture Freeze State: "
            f"{self._value(summary.get('architecture_freeze_state'))}",
            "Architecture Freeze Reason: "
            f"{self._value(summary.get('architecture_freeze_reason'))}",
            "Execution Package Coverage Target: "
            f"{self._percent(summary.get('execution_package_coverage_target'))}",
            "Compiler Runtime Coverage Target: "
            f"{self._percent(summary.get('compiler_runtime_coverage_target'))}",
            "Operational Capability Coverage Target: "
            f"{self._percent(summary.get('operational_capability_coverage_target'))}",
            f"Semantic Coverage: {self._percent(summary.get('semantic_coverage'))}",
            f"Compiler Coverage: {self._percent(summary.get('compiler_coverage'))}",
            "Execution Package Coverage: "
            f"{self._percent(summary.get('execution_package_coverage'))}",
            f"Candidate Coverage: {self._percent(summary.get('candidate_coverage'))}",
            f"Arena Coverage: {self._percent(summary.get('arena_coverage'))}",
            "Arena Source Coverage: "
            f"{self._percent(summary.get('arena_source_coverage'))}",
            f"Program Coverage: {self._percent(summary.get('program_coverage'))}",
            "Compiler Runtime Coverage: "
            f"{self._percent(summary.get('compiler_runtime_coverage'))}",
            "Validated Executable Coverage: "
            f"{self._percent(summary.get('validated_executable_coverage'))}",
            "Operational Capability Coverage: "
            f"{self._percent(summary.get('operational_capability_coverage'))}",
            "Operational Capability Materialization Rate: "
            f"{self._percent(summary.get('operational_capability_materialization_rate'))}",
            "Operational Yield From Concepts: "
            f"{self._percent(summary.get('operational_yield_from_concepts'))}",
            "Operational Yield From Programs: "
            f"{self._percent(summary.get('operational_yield_from_programs'))}",
            "Operational Yield From Candidates: "
            f"{self._percent(summary.get('operational_yield_from_candidates'))}",
            "Operational Yield From Arena: "
            f"{self._percent(summary.get('operational_yield_from_arena'))}",
            "Knowledge Production Efficiency: "
            f"{self._percent(summary.get('knowledge_production_efficiency'))}",
            "Knowledge Operationalization Efficiency: "
            f"{self._percent(summary.get('knowledge_operationalization_efficiency'))}",
            "Operational Knowledge Waste: "
            f"{self._percent(summary.get('operational_knowledge_waste'))}",
            "Operational Yield Stability: "
            f"{self._percent(summary.get('operational_yield_stability'))}",
            "Operational Yield Stability Basis: "
            f"{self._value(summary.get('operational_yield_stability_basis'))}",
            "Operational Yield Health State: "
            f"{self._value(summary.get('operational_yield_health_state'))}",
            "Knowledge Investment Policy: "
            f"{self._value(summary.get('knowledge_investment_policy'))}",
            "Knowledge Investment Authority: "
            f"{self._value(summary.get('knowledge_investment_authority'))}",
            "High Value Knowledge Items: "
            f"{self._value(summary.get('high_value_knowledge_items'))}",
            "Medium Value Knowledge Items: "
            f"{self._value(summary.get('medium_value_knowledge_items'))}",
            "Low Value Knowledge Items: "
            f"{self._value(summary.get('low_value_knowledge_items'))}",
            "Deprioritized Knowledge Items: "
            f"{self._value(summary.get('deprioritized_knowledge_items'))}",
            "Operational Investment Accuracy: "
            f"{self._percent(summary.get('operational_investment_accuracy'))}",
            "Operational Investment Accuracy State: "
            f"{self._value(summary.get('operational_investment_accuracy_state'))}",
            "High Value Operational False Positives: "
            f"{self._value(summary.get('high_value_operational_false_positives'))}",
            "Validation Efficiency: "
            f"{self._percent(summary.get('validation_efficiency'))}",
            "Validation Bottleneck Inflation: "
            f"{self._percent(summary.get('validation_bottleneck_inflation'))}",
            "Validation Bottleneck State: "
            f"{self._value(summary.get('validation_bottleneck_state'))}",
            "High Value Validation Yield: "
            f"{self._percent(summary.get('high_value_validation_yield'))}",
            "Operational Capability Acquisition Rate: "
            f"{self._percent(summary.get('operational_capability_acquisition_rate'))}",
            "Capability Acquisition Rate Per 100 Tasks: "
            f"{self._value(summary.get('operational_capability_acquisition_rate_per_100_tasks'))}",
            "Capability Survival Rate: "
            f"{self._percent(summary.get('capability_survival_rate'))}",
            "Materialization Survival Rate: "
            f"{self._percent(summary.get('materialization_survival_rate'))}",
            "Candidate Retention Rate: "
            f"{self._percent(summary.get('candidate_retention_rate'))}",
            "Incubation Conversion Rate: "
            f"{self._percent(summary.get('incubation_conversion_rate'))}",
            "Surviving Capability Conversion Rate: "
            f"{self._percent(summary.get('surviving_capability_conversion_rate'))}",
            "Operational Citizen Conversion Rate: "
            f"{self._percent(summary.get('operational_citizen_conversion_rate'))}",
            "Generated Survival Candidates: "
            f"{self._value(summary.get('generated_survival_candidate_count'))}",
            "Arena-Simulated Survival Candidates: "
            f"{self._value(summary.get('arena_simulated_survival_candidate_count'))}",
            "Arena-Quality Survival Candidates: "
            f"{self._value(summary.get('arena_quality_survival_candidate_count'))}",
            "Incubating Operational Capabilities: "
            f"{self._value(summary.get('incubating_operational_capability_count'))}",
            "Operational Citizens: "
            f"{self._value(summary.get('operational_citizen_count'))}",
            "Current Run Operational Citizens: "
            f"{self._value(summary.get('current_run_operational_citizen_count'))}",
            "Historical Operational Citizens: "
            f"{self._value(summary.get('historical_operational_citizen_count'))}",
            "Operational Domain Citizenship Coverage: "
            f"{self._percent(summary.get('operational_domain_citizenship_coverage'))}",
            "Historical Operational Domain Citizens: "
            f"{self._value(summary.get('historical_operational_domain_citizen_count'))}",
            "Expected Operational Domain Citizens: "
            f"{self._value(summary.get('expected_operational_domain_citizen_count'))}",
            "Surviving Capability Domain Count: "
            f"{self._value(summary.get('surviving_capability_domain_count'))}",
            "Missing Operational Citizen Domains: "
            f"{self._value(summary.get('missing_operational_citizen_domains'))}",
            "Surviving Capabilities: "
            f"{self._value(summary.get('surviving_capability_count'))}",
            "Validation Gap Candidate Count: "
            f"{self._value(summary.get('validation_gap_candidate_count'))}",
            "Capability Population Evolution Speed: "
            f"{self._percent(summary.get('capability_population_evolution_speed'))}",
            "Operational Experience Growth Speed: "
            f"{self._percent(summary.get('operational_experience_growth_speed'))}",
            "Capability Population Evolution Lag: "
            f"{self._percent(summary.get('capability_population_evolution_lag'))}",
            "Capability Population Evolution State: "
            f"{self._value(summary.get('capability_population_evolution_state'))}",
            "Expected Operational Capability Count: "
            f"{self._value(summary.get('expected_operational_capability_count'))}",
            "Capability Population Evolution Gap: "
            f"{self._value(summary.get('capability_population_evolution_gap'))}",
            "Target Experience Per Capability: "
            f"{self._value(summary.get('target_experience_per_capability'))}",
            f"Generated Concepts: {self._value(summary.get('generated_concepts'))}",
            f"Generated Programs: {self._value(summary.get('generated_programs'))}",
            f"Generated Blueprints: {self._value(summary.get('generated_blueprints'))}",
            f"Candidate Count: {self._value(summary.get('candidate_count'))}",
            f"Arena Candidate Count: {self._value(summary.get('arena_candidate_count'))}",
            f"Arena Source Count: {self._value(summary.get('arena_source_count'))}",
            "Candidate Attrition Coverage: "
            f"{self._percent(attrition.get('arena_acceptance_rate'))}",
            "Rejected Before Arena: "
            f"{self._value(attrition.get('rejected_before_arena'))}",
            f"Compiled Programs: {self._value(summary.get('compiled_programs'))}",
            "Compiler Runtime Activated Programs: "
            f"{self._value(summary.get('compiler_runtime_activated_programs'))}",
            f"Validated Programs: {self._value(summary.get('validated_programs'))}",
            "Materialized Operational Capabilities: "
            f"{self._value(summary.get('materialized_operational_capabilities'))}",
            "Operational Confidence State: "
            f"{self._value(summary.get('operational_confidence_state'))}",
            "Authority Transfer State: "
            f"{self._value(summary.get('authority_transfer_state'))}",
            "Decision Trust State: "
            f"{self._value(summary.get('decision_trust_state'))}",
            "Trusted For Decision: "
            f"{self._value(summary.get('trusted_for_decision_count'))}",
            "Operational Experience Count: "
            f"{self._value(summary.get('operational_experience_count'))}",
            "Operational Experience Task Count: "
            f"{self._value(summary.get('operational_experience_task_count'))}",
            "Operational Experience Per Capability: "
            f"{self._value(summary.get('operational_experience_per_capability'))}",
            "Operational Specialization Pressure: "
            f"{self._value(summary.get('operational_specialization_pressure'))}",
            "Current Operational Exploration Rate: "
            f"{self._percent(summary.get('current_operational_exploration_rate'))}",
            "Current Operational Exploitation Rate: "
            f"{self._percent(summary.get('current_operational_exploitation_rate'))}",
            "Known Operational Candidate Count: "
            f"{self._value(summary.get('known_operational_candidate_count'))}",
            "Novel Operational Candidate Count: "
            f"{self._value(summary.get('novel_operational_candidate_count'))}",
            "Operational Exploration Target: "
            f"{self._percent(summary.get('operational_exploration_target'))}",
            "Historical Exploitation Bias: "
            f"{self._percent(summary.get('historical_exploitation_bias'))}",
            "Exploration Exploitation Balance State: "
            f"{self._value(summary.get('exploration_exploitation_balance_state'))}",
            "Capability Monopoly Share: "
            f"{self._percent(summary.get('capability_monopoly_share'))}",
            "Capability Monopoly Pressure: "
            f"{self._value(summary.get('capability_monopoly_pressure'))}",
            "Dominant Operational Capability: "
            f"{self._value(summary.get('dominant_operational_capability'))}",
            "Dominant Capability Experience Count: "
            f"{self._value(summary.get('dominant_capability_experience_count'))}",
            "Experienced Capability Count: "
            f"{self._value(summary.get('experienced_capability_count'))}",
            "Independent Reuse Capability Count: "
            f"{self._value(summary.get('independent_reuse_capability_count'))}",
            "Known Operational Capabilities: "
            f"{self._value(summary.get('known_operational_capability_count'))}",
            "Operational Capability Population Target: "
            f"{self._value(summary.get('operational_capability_population_target'))}",
            "Known Operational Operations: "
            f"{self._value(summary.get('known_operational_operations'))}",
            "Known Operational Domains: "
            f"{self._value(summary.get('known_operational_domains'))}",
            "Operational Domain Population Target: "
            f"{self._value(summary.get('operational_domain_population_target'))}",
            "Capability Population Diversification: "
            f"{self._percent(summary.get('capability_population_diversification'))}",
            "Reuse Evidence Count: "
            f"{self._value(summary.get('reuse_evidence_count'))}",
            "Independent Reuse Successes: "
            f"{self._value(summary.get('independent_reuse_success_count'))}",
            "Operational Experience Store: "
            f"{self._value(summary.get('operational_experience_store_path'))}",
            "Capability Survival Store: "
            f"{self._value(summary.get('capability_survival_store_path'))}",
            "Domain Architecture State: "
            f"{self._value(domain_architecture.get('domain_architecture_state'))}",
            f"Cognitive Domain Count: {self._value(domain_architecture.get('domain_count'))}",
            "Operational Domain Count: "
            f"{self._value(domain_architecture.get('operational_domain_count'))}",
            f"Decision Authority: {self._value(summary.get('arena_decision_authority'))}",
            "Prediction Authority Preserved: "
            f"{self._value(summary.get('prediction_authority_preserved'))}",
            "End-To-End Program Lifecycle: "
            f"programs={self._value(lifecycle.get('generated_programs'))} "
            f"compiler={self._value(lifecycle.get('compiler_runtime_activated_programs'))} "
            f"compiled={self._value(lifecycle.get('compiled_programs'))} "
            f"candidates={self._value(lifecycle.get('candidate_count'))} "
            f"arena={self._value(lifecycle.get('arena_candidate_count'))} "
            f"validated={self._value(lifecycle.get('validated_programs'))} "
            f"prediction={self._value(lifecycle.get('prediction_contribution_count'))} "
            f"operational={self._value(lifecycle.get('materialized_operational_capabilities'))} "
            f"known={self._value(lifecycle.get('known_operational_capabilities'))}",
            "Operationalization Bottleneck: "
            f"{self._value(lifecycle.get('operationalization_bottleneck'))}",
            "Secondary Operationalization Bottleneck: "
            f"{self._value(lifecycle.get('secondary_operationalization_bottleneck'))}",
            "Current Run Materialization Gap: "
            f"{self._value(lifecycle.get('current_run_materialization_gap'))}",
            "Compiler Success Rate: "
            f"{self._percent(lifecycle.get('compiler_activation_to_compile_success_rate'))}",
            "Validation Success Rate: "
            f"{self._percent(lifecycle.get('arena_to_validation_rate'))}",
            "Capability Materialization Rate: "
            f"{self._percent(lifecycle.get('validation_to_operational_capability_rate'))}",
        ]
        rejection_reasons = attrition.get("rejection_reasons") or {}
        if isinstance(rejection_reasons, dict) and rejection_reasons:
            lines.append(
                "Candidate Attrition Reasons: "
                + "; ".join(
                    f"{self._value(reason)}={self._value(count)}"
                    for reason, count in sorted(rejection_reasons.items())
                )
            )
        capability_distribution = summary.get("capability_experience_distribution") or []
        capability_distribution = (
            capability_distribution
            if isinstance(capability_distribution, list)
            else []
        )
        if capability_distribution:
            lines.append("Capability Experience Distribution:")
            for row in capability_distribution[:5]:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._value(row.get('operation'))}: "
                    f"domain={self._value(row.get('domain'))} "
                    f"experience={self._value(row.get('experience_count'))} "
                    f"reuse={self._value(row.get('independent_reuse_success_count'))}"
                )
        if survival_distribution:
            lines.append(
                "Capability Survival State Distribution: "
                + "; ".join(
                    f"{self._value(state)}={self._value(count)}"
                    for state, count in sorted(survival_distribution.items())
                )
            )
        if top_incubating:
            lines.append("Top Incubating Capabilities:")
            for row in top_incubating[:5]:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._value(row.get('capability_id'))}: "
                    f"operation={self._value(row.get('operation'))} "
                    f"domain={self._value(row.get('domain'))} "
                    f"state={self._value(row.get('lifecycle_state'))} "
                    f"tasks={self._value(row.get('distinct_task_count'))} "
                    f"arena={self._value(row.get('arena_simulated_count'))} "
                    f"best_accuracy={self._percent(row.get('best_accuracy'))} "
                    f"avg_accuracy={self._percent(row.get('average_accuracy'))} "
                    f"validation_attempts={self._value(row.get('validation_attempts'))} "
                    f"trend={self._value(row.get('improvement_trend'))} "
                    f"next={self._value(row.get('next_required_evidence'))}"
                )
        domain_rows = domain_architecture.get("domain_rows") or []
        domain_rows = domain_rows if isinstance(domain_rows, list) else []
        if domain_rows:
            lines.append("Cognitive Domain Architecture:")
            for row in domain_rows[:5]:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._value(row.get('domain_name'))}: "
                    f"semantic={self._value(row.get('semantic_concept_count'))} "
                    f"packages={self._value(row.get('execution_package_count'))} "
                    f"programs={self._value(row.get('program_blueprint_count'))} "
                    f"candidates={self._value(row.get('candidate_count'))} "
                    f"arena={self._value(row.get('arena_candidate_count'))} "
                    f"validated={self._value(row.get('validated_program_count'))} "
                    f"readiness={self._percent(row.get('domain_operational_readiness'))} "
                    f"status={self._value(row.get('domain_status'))} "
                    f"gap={self._value(row.get('operationalization_gap'))}"
                )
        domain_gaps = domain_architecture.get("domain_operationalization_gaps") or []
        domain_gaps = domain_gaps if isinstance(domain_gaps, list) else []
        if domain_gaps:
            lines.append("Domain Operationalization Gaps:")
            for row in domain_gaps[:5]:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._value(row.get('domain_name'))}: "
                    f"{self._value(row.get('operationalization_gap'))} "
                    f"programs={self._value(row.get('program_blueprint_count'))} "
                    f"packages={self._value(row.get('execution_package_count'))} "
                    f"candidates={self._value(row.get('candidate_count'))} "
                    f"arena={self._value(row.get('arena_candidate_count'))}"
                )
        if bottlenecks:
            lines.append("Lowest Coverage Bottlenecks:")
            for item in bottlenecks[:3]:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._label(item.get('coverage_type'))}: "
                    f"{self._percent(item.get('coverage'))} "
                    f"status={self._value(item.get('status'))}"
                )
        if missing_packages:
            lines.append(
                "Missing Execution Packages: "
                + ", ".join(str(item) for item in missing_packages[:8])
            )
        if missing_requirements:
            lines.append(
                "Missing Compiler Requirements: "
                + ", ".join(str(item) for item in missing_requirements[:8])
            )
        if lineage:
            lines.append("Candidate Source Lineage:")
            lineage_limit = 3 if canonical["report_level"] == "diagnostic" else 1
            for row in lineage[:lineage_limit]:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "  "
                    f"raw={self._value(row.get('raw_source'))} -> "
                    f"adapter={self._value(row.get('candidate_adapter'))} -> "
                    f"normalized={self._value(row.get('normalized_source'))} -> "
                    f"arena={self._value(row.get('arena_source'))} "
                    f"op={self._value(row.get('operation'))} "
                    f"entered={self._value(row.get('entered_arena'))}"
                )
        return self._section("COGNITIVE CAPABILITY COVERAGE", lines)

    def _render_candidate_arena(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "candidate_arena_summary")
        summary = summary if isinstance(summary, dict) else {}
        sources = summary.get("competitor_sources") or []
        if not isinstance(sources, list):
            sources = [sources]
        rows = summary.get("candidate_rows") or []
        rows = rows if isinstance(rows, list) else []
        source_status = summary.get("source_status") or {}
        source_status = source_status if isinstance(source_status, dict) else {}
        source_outcomes = summary.get("source_outcomes") or []
        source_outcomes = source_outcomes if isinstance(source_outcomes, list) else []
        source_diversity = summary.get("source_diversity")
        operational_diversity = summary.get("operational_diversity")
        source_diversity_bottleneck = (
            "LOW_SOURCE_DIVERSITY"
            if (
                isinstance(source_diversity, (int, float))
                and source_diversity < 0.25
                and isinstance(operational_diversity, (int, float))
                and operational_diversity >= 0.75
            )
            else "none"
        )
        lines = [
            f"Arena State: {self._value(summary.get('arena_state'))}",
            f"Candidate Count: {self._value(summary.get('candidate_count'))}",
            f"Unique Candidate Count: {self._value(summary.get('unique_candidate_count'))}",
            f"Source Count: {self._value(summary.get('source_count'))}",
            f"Attempted Candidates: {self._value(summary.get('attempted_candidate_count'))}",
            f"Explicit Rejections: {self._value(summary.get('explicit_rejection_count'))}",
            f"Competitor Sources: {', '.join(str(item) for item in sources) if sources else 'Not Available'}",
            f"Competition Diversity: {self._value(summary.get('competition_diversity'))}",
            f"Operational Diversity: {self._value(summary.get('operational_diversity'))}",
            f"Source Diversity: {self._value(summary.get('source_diversity'))}",
            f"Source Diversity Bottleneck: {source_diversity_bottleneck}",
            f"Simulation Count: {self._value(summary.get('simulation_count'))}",
            f"Simulation Success Count: {self._value(summary.get('simulation_success_count'))}",
            f"Governance Blocked Count: {self._value(summary.get('governance_blocked_count'))}",
            f"Winner Source: {self._value(summary.get('winner_source'))}",
            f"Arena Winner: {self._value(summary.get('arena_winner'))}",
            f"Winner Operation: {self._value(summary.get('winner_operation'))}",
            f"Winner Score: {self._value(summary.get('winner_score'))}",
            f"Second Best Score: {self._value(summary.get('second_best_score'))}",
            f"Selection Margin: {self._value(summary.get('selection_margin'))}",
            f"Selection State: {self._value(summary.get('selection_state'))}",
            f"Winner Takes All Detected: {self._value(summary.get('winner_takes_all_detected'))}",
            f"Source Dominance Detected: {self._value(summary.get('source_dominance_detected'))}",
            f"Dominance Source: {self._value(summary.get('dominance_source'))}",
            f"Selection Mode: {self._value(summary.get('selection_mode'))}",
            f"Validation Coverage: {self._percent(summary.get('validation_coverage'))}",
            f"Missing Competition Reason: {self._value(summary.get('missing_competition_reason'))}",
            f"Selection Explanation: {self._value(summary.get('selection_explanation'))}",
        ]
        if rows:
            lines.append("Top Arena Candidates:")
            for index, row in enumerate(rows[:6], start=1):
                if not isinstance(row, dict):
                    continue
                marker = "selected" if row.get("selected") else "candidate"
                origin_sources = self._source_names(row, "origin_source", "origin_sources")
                normalized_sources = self._source_names(row, "normalized_source", "normalized_sources")
                lines.append(
                    "  "
                    f"{index}. {self._value(row.get('source'))}: "
                    f"{self._value(row.get('candidate_id'))} "
                    f"op={self._value(row.get('operation'))} "
                    f"confidence={self._value(row.get('confidence', row.get('score')))} "
                    f"accuracy={self._value(row.get('accuracy'))} "
                    f"status={self._value(row.get('validation_status'))} "
                    f"{marker}"
                )
                lines.append(f"     Origin Sources: {origin_sources}")
                lines.append(f"     Normalized Sources: {normalized_sources}")
        if source_outcomes:
            lines.append("Cognitive Source Outcomes:")
            for outcome in source_outcomes[:6]:
                if not isinstance(outcome, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._value(outcome.get('source'))}: "
                    f"{self._value(outcome.get('status'))} "
                    f"reason={self._value(outcome.get('reason'))}"
                )
        if canonical["report_level"] == "diagnostic" and source_status:
            lines.append("Arena Source Status:")
            for source, status in sorted(source_status.items()):
                lines.append(f"  {source}: {status}")
        return self._section("COGNITIVE CANDIDATE ARENA", lines)

    def _render_multi_hypothesis_report(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        state = canonical["report_state"]
        performance = canonical["performance"]
        report = self._first_dict(
            state,
            "MULTI_HYPOTHESIS_REPORT",
            "multi_hypothesis_report",
        )
        if not report:
            engine_report = self._first_dict(
                state,
                "MULTI_HYPOTHESIS_ENGINE_REPORT",
                "multi_hypothesis_engine_report",
            )
            if not engine_report:
                engine_report = self._first_dict(
                    performance,
                    "MULTI_HYPOTHESIS_ENGINE_REPORT",
                    "multi_hypothesis_engine_report",
                )
            compact = self._first_dict(engine_report, "MULTI_HYPOTHESIS_REPORT")
            report = compact or engine_report
        best = report.get("Best Ranked") or report.get("best_ranked") or []
        ready = report.get("Execution Ready") or report.get("execution_ready") or []
        if isinstance(best, list):
            best_text = ", ".join(
                self._value(item.get("hypothesis_name") if isinstance(item, dict) else item)
                for item in best[:6]
            )
        else:
            best_text = self._value(best)
        if isinstance(ready, list):
            ready_text = ", ".join(
                self._value(item.get("hypothesis_name") if isinstance(item, dict) else item)
                for item in ready[:6]
            )
        else:
            ready_text = self._value(ready)
        lines = [
            f"Generated Hypotheses: {self._value(report.get('Generated Hypotheses', report.get('hypothesis_count')))}",
            f"Accepted: {self._value(report.get('Accepted', report.get('accepted_count')))}",
            f"Rejected: {self._value(report.get('Rejected', report.get('rejected_count')))}",
            f"Reusable: {self._value(report.get('Reusable', report.get('reusable_count')))}",
            f"Best Ranked: {best_text or 'Not Available'}",
            f"Execution Ready: {ready_text or 'Not Available'}",
        ]
        if canonical["report_level"] == "diagnostic":
            lines.extend([
                "Hypothesis Ranking Operational: "
                f"{self._value(report.get('hypothesis_ranking_operational'))}",
                "Hypothesis Validation Operational: "
                f"{self._value(report.get('hypothesis_validation_operational'))}",
                "Hypothesis Memory Operational: "
                f"{self._value(report.get('hypothesis_memory_operational'))}",
            ])
        return self._section("MULTI HYPOTHESIS REPORT", lines)

    def _render_candidate_proposal(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        summary = self._binding_value(canonical, "candidate_proposal_summary")
        summary = summary if isinstance(summary, dict) else {}
        proposals = summary.get("candidate_proposals") or []
        proposals = proposals if isinstance(proposals, list) else []
        sources = summary.get("sources_with_proposals") or []
        sources = sources if isinstance(sources, list) else [sources]
        rejected = summary.get("sources_rejected") or []
        rejected = rejected if isinstance(rejected, list) else [rejected]
        lines = [
            f"Proposal Phase Entered: {self._value(summary.get('proposal_phase_entered'))}",
            f"Proposal Phase Status: {self._value(summary.get('proposal_phase_status'))}",
            f"Eligible Sources: {self._value(summary.get('eligible_source_count'))}",
            f"Candidate Proposals: {self._value(summary.get('proposal_count'))}",
            f"Explicit Rejections: {self._value(summary.get('explicit_rejection_count'))}",
            f"Sources With Proposals: {', '.join(str(item) for item in sources) if sources else 'Not Available'}",
            f"Sources Rejected: {', '.join(str(item) for item in rejected) if rejected else 'Not Available'}",
            "Knowledge Investment Policy: "
            f"{self._value(summary.get('knowledge_investment_policy'))}",
            "Knowledge Investment Authority: "
            f"{self._value(summary.get('knowledge_investment_authority'))}",
            "High Value Knowledge Items: "
            f"{self._value(summary.get('high_value_knowledge_items'))}",
            "Medium Value Knowledge Items: "
            f"{self._value(summary.get('medium_value_knowledge_items'))}",
            "Low Value Knowledge Items: "
            f"{self._value(summary.get('low_value_knowledge_items'))}",
            "Deprioritized Knowledge Items: "
            f"{self._value(summary.get('deprioritized_knowledge_items'))}",
        ]
        if proposals:
            lines.append("Proposal Ledger:")
            for proposal in proposals[:6]:
                if not isinstance(proposal, dict):
                    continue
                lines.append(
                    "  "
                    f"{self._value(proposal.get('source'))}: "
                    f"{self._value(proposal.get('proposal_status'))} "
                    f"op={self._value(proposal.get('operation'))} "
                    f"value={self._value(proposal.get('operational_value_score'))} "
                    f"tier={self._value(proposal.get('investment_tier'))} "
                    f"reason={self._value(proposal.get('investment_reason') or proposal.get('rejection_reason'))}"
                )
        return self._section("CANDIDATE PROPOSAL PHASE", lines)

    def _render_search_quality(self, canonical: dict[str, Any]) -> str:
        search = canonical["search"]
        return self._section("SEARCH QUALITY", [
            f"Overall Search Quality: {self._field(canonical, 'overall_search_quality')}",
            f"Search Efficiency: {self._field(canonical, 'search_efficiency')}",
            f"Search Coverage: {self._field(canonical, 'search_coverage')}",
            f"Search Entropy: {self._field(canonical, 'search_entropy')}",
            f"Average Route Quality: {self._field(canonical, 'average_route_quality')}",
        ])

    def _render_counterfactual_reasoning(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        state = canonical["report_state"]
        performance = canonical["performance"]
        report = self._first_dict(
            state,
            "COUNTERFACTUAL_REASONING_REPORT",
            "counterfactual_reasoning_report",
        )
        if not report:
            engine = self._first_dict(
                state,
                "COUNTERFACTUAL_REASONING_ENGINE_REPORT",
                "counterfactual_reasoning_engine_report",
            )
            if not engine:
                engine = self._first_dict(
                    performance,
                    "COUNTERFACTUAL_REASONING_ENGINE_REPORT",
                    "counterfactual_reasoning_engine_report",
                )
            report = self._first_dict(engine, "COUNTERFACTUAL_REASONING_REPORT") or engine
        summary = report.get("counterfactual_summary") or []
        summary = summary if isinstance(summary, list) else []
        lines = [
            f"Counterfactual Required: {self._value(report.get('counterfactual_required'))}",
            f"Eligibility State: {self._value(report.get('eligibility_state'))}",
            f"Trigger Reasons: {', '.join(str(item) for item in report.get('trigger_reasons', [])[:6]) if isinstance(report.get('trigger_reasons'), list) and report.get('trigger_reasons') else 'Not Available'}",
            f"Assumptions: {self._value(report.get('assumption_count'))}",
            f"Challengeable Assumptions: {self._value(report.get('challengeable_assumption_count'))}",
            f"Generated Counterfactuals: {self._value(report.get('generated_counterfactual_count'))}",
            f"Simulated Counterfactuals: {self._value(report.get('simulated_counterfactual_count'))}",
            f"Rejected Counterfactuals: {self._value(report.get('rejected_counterfactual_count'))}",
            f"Best Counterfactual: {self._value(report.get('best_counterfactual_id'))}",
            f"Original Still Best: {self._value(report.get('original_candidate_still_best'))}",
            f"Falsification State: {self._value(report.get('falsification_state'))}",
            f"Winner Stability State: {self._value(report.get('winner_stability_state'))}",
            f"Winner Stability Score: {self._value(report.get('winner_stability_score'))}",
            f"Minimal Revision Generated: {self._value(report.get('minimal_revision_generated'))}",
            f"Execution Recommendation: {self._value(report.get('execution_recommendation'))}",
            f"Budget Used: {self._value(report.get('budget_used'))}",
            f"Stop Reason: {self._value(report.get('stop_reason'))}",
        ]
        if summary:
            lines.append("Counterfactual Summary:")
            for index, row in enumerate(summary[:6], start=1):
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "  "
                    f"{index}. {self._value(row.get('counterfactual_id'))} "
                    f"accuracy={self._value(row.get('accuracy'))} "
                    f"residual={self._value(row.get('residual'))} "
                    f"evidence={self._value(row.get('evidence'))}"
                )
        return self._section("COUNTERFACTUAL REASONING REPORT", lines)

    def _render_executable_intelligence(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        state = canonical["report_state"]
        performance = canonical["performance"]
        report = self._first_dict(
            state,
            "EXECUTABLE_INTELLIGENCE_REPORT",
            "executable_intelligence_report",
        )
        if not report:
            engine = self._first_dict(
                state,
                "EXECUTABLE_INTELLIGENCE_ENGINE_REPORT",
                "executable_intelligence_engine_report",
            )
            if not engine:
                engine = self._first_dict(
                    performance,
                    "EXECUTABLE_INTELLIGENCE_ENGINE_REPORT",
                    "executable_intelligence_engine_report",
                )
            report = self._first_dict(engine, "EXECUTABLE_INTELLIGENCE_REPORT") or engine
        lines = [
            f"Semantic Intent Operational: {self._value(report.get('semantic_intent_operational'))}",
            f"Object Grounding Operational: {self._value(report.get('object_grounding_operational'))}",
            f"Localized Execution Planning Operational: {self._value(report.get('localized_execution_planning_operational'))}",
            f"Primitive Selection Operational: {self._value(report.get('primitive_selection_operational'))}",
            f"Program Synthesis Operational: {self._value(report.get('program_synthesis_operational'))}",
            f"Program Compilation Operational: {self._value(report.get('program_compilation_operational'))}",
            f"Program Validation Operational: {self._value(report.get('program_validation_operational'))}",
            f"Residual Localization Operational: {self._value(report.get('residual_localization_operational'))}",
            f"Residual Repair Operational: {self._value(report.get('residual_repair_operational'))}",
            f"Execution Adaptation Operational: {self._value(report.get('execution_adaptation_operational'))}",
            f"Execution Memory Operational: {self._value(report.get('execution_memory_operational'))}",
            f"Governed Execution Operational: {self._value(report.get('governed_execution_operational'))}",
            f"Knowledge Feedback Operational: {self._value(report.get('knowledge_feedback_operational'))}",
            f"Executable Concepts: {self._value(report.get('executable_concepts'))}",
            f"Localized Operations: {self._value(report.get('localized_operations'))}",
            f"Target Objects: {self._value(report.get('target_objects'))}",
            f"Synthesized Programs: {self._value(report.get('synthesized_programs'))}",
            f"Compiled Programs: {self._value(report.get('compiled_programs'))}",
            f"Validated Programs: {self._value(report.get('validated_programs'))}",
            f"Residual Regions: {self._value(report.get('residual_regions'))}",
            f"Generated Repairs: {self._value(report.get('generated_repairs'))}",
            f"Execution Success Rate: {self._value(report.get('execution_success_rate'))}",
            f"Execution Adaptations: {self._value(report.get('execution_adaptations'))}",
            f"Execution Feedback: {self._value(report.get('execution_feedback'))}",
        ]
        return self._section("EXECUTABLE INTELLIGENCE REPORT", lines)

    def _render_knowledge_pipeline(self, canonical: dict[str, Any]) -> str:
        knowledge = canonical["knowledge"]
        return self._section("KNOWLEDGE PIPELINE", [
            f"Knowledge Propagation Status: {self._field(canonical, 'knowledge_propagation_status')}",
            f"Integrated Concepts: {self._field(canonical, 'integrated_concepts')}",
            f"Knowledge Links: {self._field(canonical, 'knowledge_links')}",
            f"Replication State: {self._field(canonical, 'replication_state')}",
        ])

    def _render_system_health(self, canonical: dict[str, Any]) -> str:
        state = canonical["report_state"]
        binding = canonical["binding"]
        metric_sync = canonical["metric_sync"]
        observability = canonical["observability"]
        return self._section("SYSTEM HEALTH", [
            f"Binding Status: {self._field(canonical, 'binding_status')}",
            f"Metric Validation Status: {self._field(canonical, 'metric_validation_status')}",
            f"Observability Status: {self._field(canonical, 'observability_status')}",
            f"Missing Execution Instances: {self._field(canonical, 'missing_execution_instances')}",
            f"Missing Snapshot Runtimes: {self._field(canonical, 'missing_snapshot_runtimes')}",
            f"Governance Budget State: {self._field(canonical, 'governance_budget_state')}",
            f"Instrumentation Overhead State: {self._field(canonical, 'instrumentation_overhead_state')}",
        ])

    def _render_timing_summary(self, canonical: dict[str, Any]) -> str:
        runtime_summary = self._binding_value(canonical, "runtime_timing_summary")
        if not isinstance(runtime_summary, dict):
            runtime_summary = {}
        top_consumers = self._binding_value(canonical, "top_time_consumers")
        top_consumers = top_consumers if isinstance(top_consumers, list) else []
        reporting_timing = self._binding_value(canonical, "reporting_timing_summary")
        reporting_timing = reporting_timing if isinstance(reporting_timing, dict) else {}
        lines = [
            f"Total Wall Time: {self._seconds(runtime_summary.get('total_wall_time') or self._field(canonical, 'total_wall_time'))}",
            f"Active Compute Time: {self._seconds(runtime_summary.get('active_compute_time') or self._field(canonical, 'active_compute_time'))}",
            f"Cognitive Runtime Time: {self._seconds(runtime_summary.get('cognitive_runtime_time'))}",
            f"Untracked Time: {self._seconds(runtime_summary.get('untracked_time') or self._field(canonical, 'untracked_time'))}",
            f"Timing Coverage: {self._percent(runtime_summary.get('timing_coverage') or self._field(canonical, 'timing_coverage'))}",
            f"Report Lifecycle Total Time: {self._seconds(reporting_timing.get('report_lifecycle_total_time') or self._field(canonical, 'report_lifecycle_total_time'))}",
            f"Final Report Rendering Time: {self._seconds(reporting_timing.get('final_report_rendering_time') or self._field(canonical, 'final_report_rendering_time'))}",
            f"Report Timing Status: {self._value(reporting_timing.get('report_timing_status'))}",
            f"Finalization Time: {self._seconds(runtime_summary.get('finalization_time') or self._field(canonical, 'finalization_time'))}",
        ]
        if canonical["report_level"] != "minimal":
            lines.extend([
                "REPORTING TIMING SUMMARY",
                f"Canonical Report Assembly Time: {self._seconds(reporting_timing.get('canonical_report_assembly_time'))}",
                f"Cognitive Summary Aggregation Time: {self._seconds(reporting_timing.get('cognitive_summary_aggregation_time'))}",
                f"Report Binding Time: {self._seconds(reporting_timing.get('report_binding_time'))}",
                f"Report Visibility Filtering Time: {self._seconds(reporting_timing.get('report_visibility_filtering_time'))}",
                f"Report Compression Time: {self._seconds(reporting_timing.get('report_compression_time'))}",
                f"Representation Validation Time: {self._seconds(reporting_timing.get('representation_validation_time'))}",
                f"Technical Appendix Serialization Time: {self._seconds(reporting_timing.get('technical_appendix_serialization_time'))}",
                f"Report Artifact Writing Time: {self._seconds(reporting_timing.get('report_artifact_writing_time'))}",
                f"Console Emission Time: {self._seconds(reporting_timing.get('console_emission_time'))}",
                f"Report Overlap Duration: {self._seconds(reporting_timing.get('report_overlap_duration'))}",
                f"Report Timing Semantics Valid: {self._value(reporting_timing.get('report_timing_semantics_valid'))}",
            ])
        if top_consumers:
            lines.append("Top Three Exclusive-Time Consumers:")
            lines.extend(
                "  "
                f"{item.get('rank', index + 1)}. "
                f"{item.get('stage_name', 'Not Available')}: "
                f"{self._seconds(item.get('exclusive_duration') or item.get('duration_seconds'))} "
                f"({self._percent(item.get('percentage_of_active_compute'), already_percent=True)} "
                "of ACTIVE_COMPUTE_TIME)"
                for index, item in enumerate(top_consumers[:3])
                if isinstance(item, dict)
            )
        reconciliation = self._binding_value(canonical, "timing_reconciliation_summary")
        reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
        if canonical["report_level"] == "minimal":
            lines.extend([
                f"Overlap Detected: {self._value(reconciliation.get('overlap_detected'))}",
                f"Timing Coverage: {self._percent(runtime_summary.get('timing_coverage') or self._field(canonical, 'timing_coverage'))} of TOTAL_WALL_TIME",
                f"Resource Percentage Sum: {self._percent(reconciliation.get('resource_percentage_sum'), already_percent=True)} of ACTIVE_COMPUTE_TIME",
            ])
        return self._section("TIMING SUMMARY", lines)

    def _render_stage_timing(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        rows = self._binding_value(canonical, "timing_hierarchy_summary")
        rows = rows if isinstance(rows, list) else []
        if not rows:
            return self._section("COGNITIVE STAGE TIMING", [
                "TIMING HIERARCHY SUMMARY",
                "Stage Timing: Not Available",
            ])
        lines = [
            "TIMING HIERARCHY SUMMARY",
            "stage_name                       inclusive_duration  exclusive_duration  relationship_type  timing_scope",
        ]
        for row in rows:
            if not isinstance(row, dict):
                continue
            indent = "  " * int(row.get("depth", 0) or 0)
            label = indent + self._stage_display_label(row, max_width=max(30 - len(indent), 12))
            lines.append(
                f"{label[:30]:30} "
                f"{self._seconds(row.get('inclusive_duration')):>18} "
                f"{self._seconds(row.get('exclusive_duration')):>18} "
                f"{str(row.get('relationship_type', 'Not Available'))[:17]:17} "
                f"{str(row.get('timing_scope', 'Not Available'))[:24]:24}"
            )
        return self._section("COGNITIVE STAGE TIMING", lines)

    def _render_resource_summary(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] == "minimal":
            return ""
        hierarchy_rows = self._binding_value(canonical, "timing_hierarchy_summary")
        hierarchy_rows = hierarchy_rows if isinstance(hierarchy_rows, list) else []
        rows = self._binding_value(canonical, "resource_consumption_ranking")
        rows = rows if isinstance(rows, list) else []
        top = rows[0] if rows else {}
        reconciliation = self._binding_value(canonical, "timing_reconciliation_summary")
        reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
        lines = [
            "RESOURCE CONSUMPTION RANKING",
            "stage_name                       exclusive_duration  percentage_of_active_compute  rank",
        ]
        for row in rows[:10]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"{str(row.get('stage_name', 'Not Available'))[:30]:30} "
                f"{self._seconds(row.get('exclusive_duration')):>18} "
                f"{self._percent(row.get('percentage_of_active_compute'), already_percent=True):>28} "
                f"{self._value(row.get('rank')):>4}"
            )
        lines.extend([
            f"Highest Time Consumer: {self._value(top.get('stage_name'))}",
            "Highest Time Consumer Percentage: "
            f"{self._percent(top.get('percentage_of_active_compute'), already_percent=True)} of ACTIVE_COMPUTE_TIME",
            "Resource Percentage Sum: "
            f"{self._percent(reconciliation.get('resource_percentage_sum'), already_percent=True)} of ACTIVE_COMPUTE_TIME",
            f"Overlap Accounted For: {self._value(reconciliation.get('overlap_accounted_for'))}",
            f"Timing Hierarchy Valid: {self._value(reconciliation.get('timing_hierarchy_valid'))}",
            f"Timing Coverage: {self._field(canonical, 'timing_coverage')} of TOTAL_WALL_TIME",
            f"Untracked Time: {self._seconds(self._field(canonical, 'untracked_time'))}",
            f"Resource Distribution Status: {'AVAILABLE' if rows or hierarchy_rows else 'Not Available'}",
        ])
        return self._section("COGNITIVE RESOURCE SUMMARY", lines)

    def _render_diagnostic_timing_detail(self, canonical: dict[str, Any]) -> str:
        if canonical["report_level"] != "diagnostic":
            return ""
        rows = self._binding_value(canonical, "diagnostic_timing_nodes")
        rows = rows if isinstance(rows, list) else []
        report_nodes = self._binding_value(canonical, "reporting_timing_nodes")
        report_nodes = report_nodes if isinstance(report_nodes, list) else []
        legacy_mappings = self._binding_value(canonical, "legacy_report_timing_mappings")
        legacy_mappings = legacy_mappings if isinstance(legacy_mappings, list) else []
        lines = []
        for row in report_nodes:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"Reporting {row.get('stage_name')}: "
                f"scope={self._value(row.get('timing_scope'))}, "
                f"inclusive={self._seconds(row.get('inclusive_duration_seconds'))}, "
                f"exclusive={self._seconds(row.get('exclusive_duration_seconds'))}, "
                f"parent={self._value(row.get('parent_timing_id'))}, "
                f"source={self._value(row.get('measurement_source'))}, "
                f"consistency={self._value(row.get('source_consistency'))}"
            )
        for mapping in legacy_mappings:
            if not isinstance(mapping, dict):
                continue
            lines.append(
                f"Legacy Reporting Field {self._value(mapping.get('legacy_field'))}: "
                f"semantics={self._value(mapping.get('legacy_timing_semantics'))}, "
                f"canonical_scope={self._value(mapping.get('canonical_timing_scope'))}, "
                f"normal_allowed={self._value(mapping.get('normal_reporting_allowed'))}"
            )
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"{row.get('stage_name')}: "
                f"timing_id={self._value(row.get('timing_id'))}, "
                f"inclusive={self._seconds(row.get('inclusive_duration_seconds'))}, "
                f"exclusive={self._seconds(row.get('exclusive_duration_seconds'))}, "
                f"child_union={self._seconds(row.get('child_interval_union_duration'))}, "
                f"parallel_overlap={self._seconds(row.get('parallel_overlap_duration'))}, "
                f"duplicate_overlap={self._seconds(row.get('duplicate_overlap_duration'))}, "
                f"parent={self._value(row.get('parent_timing_id'))}, "
                f"source={self._value(row.get('measurement_source'))}, "
                f"relationship={self._value(row.get('relationship_type'))}"
            )
        return self._section("DIAGNOSTIC TIMING DETAIL", lines or [
            "Raw Timing Records: Not Available",
        ])

    def _render_warnings(self, canonical: dict[str, Any]) -> str:
        warnings = self._derive_warnings(canonical)
        if not warnings:
            warnings = ["No validated report warnings."]
        return self._section("WARNINGS AND GAPS", [
            f"Warning Count: {len(warnings)}",
            *[f"- {warning}" for warning in warnings],
        ])

    def _render_runtime_metadata(self, canonical: dict[str, Any]) -> str:
        metadata = canonical["runtime_metadata"]
        keys = [
            "mode",
            "report_level",
            "runtime_status",
            "execution_time",
            "training_batch_size",
            "tasks_directory",
            "governance_budget_seconds",
            "governance_budget_exceeded",
            "cache_boot_loaded",
            "cache_boot_skipped",
            "timestamp",
        ]
        return self._section("RUNTIME METADATA", [
            f"{self._label(key)}: {self._value(metadata.get(key))}"
            for key in keys
        ])

    def _render_technical_appendix(self, canonical: dict[str, Any]) -> str:
        state = canonical["report_state"]
        included = [
            key
            for key in sorted(state.keys(), key=str)
            if key.isupper()
        ][:25]
        note = canonical.get(
            "technical_appendix_note",
            "Diagnostic structures are intentionally excluded from console "
            "rendering and can be serialized as JSON.",
        )
        return self._section("OPTIONAL TECHNICAL APPENDIX", [
            f"Appendix State: {note}",
            f"Available Diagnostic Key Count: {len(included)}",
            "Report Binding Registry: Externalized to Technical Appendix",
            "Binding Validation Status: "
            f"{self._binding_status(canonical)}",
        ])

    def _render_final_status(self, canonical: dict[str, Any]) -> str:
        state = canonical["report_state"]
        status = self._value(
            self._read_any(state, canonical["performance"], "runtime_status", "status"),
            "COMPLETED",
        )
        warning_count = len(self._derive_warnings(canonical))
        return self._section("FINAL STATUS", [
            f"Status: {str(status).upper()}",
            "Report Complete: TRUE",
            f"Warnings: {warning_count}",
            "Errors: 0",
        ], title="NEXRYN :: FINAL STATUS")

    def _derive_warnings(self, canonical: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        search = canonical["search"]
        program = canonical["program"]
        state = canonical["report_state"]
        compact = self._first_dict(state, "compact_report")
        compression_report = self._first_dict(state, "compression_report")
        program_lifecycle = self._first_dict(
            state,
            "COGNITIVE_PROGRAM_LIFECYCLE_REPORT",
            "cognitive_program_lifecycle_report",
        )
        entropy = self._read_any(search, "search_entropy")
        routes = self._read_any(search, "route_count", "unique_route_count")
        if self._number(entropy) == 0 and (self._number(routes) or 0) > 1:
            warnings.append("Search entropy remains zero despite multiple routes.")
        if (
            self._read_any(program, "validation_distribution") is None
            and self._read_any(program, "generated_programs") is not None
            and not program_lifecycle.get("program_registry")
        ):
            warnings.append("Generated programs lack final lifecycle states.")
        compression_status = str(
            compression_report.get("compression_status", "")
        ).upper()
        if (
            compression_status not in {"NOT_REQUIRED", "SKIPPED"}
            and isinstance(compact, dict)
            and all(
            int(compact.get(key, 0) or 0) == 0
            for key in (
                "heavy_keys_removed",
                "arrays_summarized",
                "repeated_reports_collapsed",
            )
            )
        ):
            warnings.append("Compact reporting performed no compression.")
        if state.get("legacy_cache_detected"):
            warnings.append("Legacy cache remains detected.")
        if self._read_any(canonical["performance"], "untracked_runtime_seconds"):
            warnings.append("Timing scope remains ambiguous.")
        return list(dict.fromkeys(warnings))

    def _section(
        self,
        section_name: str,
        lines: list[str],
        *,
        title: str | None = None,
    ) -> str:
        heading = title or section_name
        body = "\n".join(str(line) for line in lines)
        return f"\n{'=' * 50}\n{heading}\n{'=' * 50}\n\n{body}"

    def _section_title(self, section_name: str) -> str:
        if section_name == "FINAL STATUS":
            return "NEXRYN :: FINAL STATUS"
        return f"\n{section_name}\n"

    def _normalize_report_level(self, level: str) -> str:
        aliases = {
            "full": "diagnostic",
            "debug": "diagnostic",
            "audit": "diagnostic",
            "diagnostic_summary": "diagnostic",
            "full_diagnostic": "diagnostic",
        }
        normalized = str(level or "normal").lower()
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in {"minimal", "normal", "diagnostic"} else "normal"

    def _first_dict(
        self,
        base: dict[str, Any],
        *keys: str,
        source_override: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        active_source = kwargs.get("source", source_override)
        if active_source is None:
            active_source = base
        for key in keys:
            value = active_source.get(key) if isinstance(active_source, dict) else None
            if isinstance(value, dict):
                return value
        return {}

    def _read_any(self, *sources_and_keys: Any) -> Any:
        sources = [item for item in sources_and_keys if isinstance(item, dict)]
        keys = [item for item in sources_and_keys if isinstance(item, str)]
        for source in sources:
            for key in keys:
                if key in source:
                    return source[key]
        return None

    def _field(self, canonical: dict[str, Any], field_name: str) -> str:
        binding = canonical.get("report_binding", {})
        values = binding.get("field_values", {}) if isinstance(binding, dict) else {}
        if field_name in values:
            return self._value(values[field_name], "Not Available")
        fields = binding.get("field_bindings", {}) if isinstance(binding, dict) else {}
        field = fields.get(field_name) if isinstance(fields, dict) else None
        if isinstance(field, dict):
            return self._value(field.get("display_value"), "Not Available")
        return "Not Available"

    def _binding_value(self, canonical: dict[str, Any], field_name: str) -> Any:
        binding = canonical.get("report_binding", {})
        fields = binding.get("field_bindings", {}) if isinstance(binding, dict) else {}
        field = fields.get(field_name) if isinstance(fields, dict) else None
        if isinstance(field, dict) and "value" in field:
            return field.get("value")
        values = binding.get("field_values", {}) if isinstance(binding, dict) else {}
        if isinstance(values, dict):
            return values.get(field_name)
        return None

    def _seconds(self, value: Any) -> str:
        if isinstance(value, str) and value == "Not Available":
            return value
        number = self._number(value)
        if number is None:
            return "Not Available"
        return f"{round(number, 4):g} s"

    def _percent(self, value: Any, *, already_percent: bool = False) -> str:
        if isinstance(value, str):
            if value.endswith("%"):
                return value
            number = self._number(value)
        else:
            number = self._number(value)
        if number is None:
            return "Not Available"
        percent = number if already_percent or number > 1.0 else number * 100.0
        return f"{round(percent, 4):g}%"

    def _binding_status(self, canonical: dict[str, Any]) -> str:
        binding = canonical.get("report_binding", {})
        diagnostics = (
            binding.get("binding_diagnostics", {})
            if isinstance(binding, dict)
            else {}
        )
        return self._value(
            diagnostics.get("binding_validation_status"),
            "Not Available",
        )

    def _value(self, value: Any, default: Any = "Not Available") -> str:
        if value is None:
            value = default
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            return str(round(value, 4) if isinstance(value, float) else value)
        if isinstance(value, str):
            return "Not Available" if value.upper() == "UNKNOWN" else value
        if isinstance(value, list):
            if not value:
                return "0"
            if all(not isinstance(item, (dict, list, tuple, set)) for item in value):
                preview = ", ".join(str(item) for item in value[:8])
                suffix = f" (+{len(value) - 8} more)" if len(value) > 8 else ""
                return preview + suffix
            return f"{len(value)} entries"
        if isinstance(value, dict):
            if not value:
                return "0"
            return ", ".join(
                f"{self._label(str(key))}={self._value(item)}"
                for key, item in list(value.items())[:8]
            )
        return str(value)

    def _source_names(self, row: dict[str, Any], singular_key: str, plural_key: str) -> str:
        plural = row.get(plural_key)
        if isinstance(plural, list) and all(not isinstance(item, (dict, list, tuple, set)) for item in plural):
            return ", ".join(str(item) for item in plural) if plural else "Not Available"
        singular = row.get(singular_key)
        if isinstance(singular, str) and singular:
            return singular
        if singular is not None:
            return self._value(singular)
        return self._value(plural)

    def _compact_value(self, value: Any) -> str:
        if isinstance(value, list):
            if not value:
                return "0"
            return f"{len(value)} items"
        if isinstance(value, dict):
            if not value:
                return "0"
            return f"{len(value)} fields"
        return self._value(value)

    def _inline_map(self, value: Any) -> str:
        if not isinstance(value, dict) or not value:
            return "Not Available"
        return "; ".join(
            f"{self._value(key)}={self._value(item)}"
            for key, item in sorted(value.items())
        )

    def _label(self, key: str) -> str:
        return key.replace("_", " ").title()

    def _stage_display_label(self, row: dict[str, Any], *, max_width: int) -> str:
        label = str(row.get("stage_name") or "Not Available")
        if len(label) <= max_width:
            return label
        suffix_source = str(
            row.get("timing_id")
            or row.get("execution_id")
            or label,
        )
        suffix = re.sub(r"[^A-Za-z0-9]", "", suffix_source)[-6:] or "stage"
        keep = max(max_width - len(suffix) - 2, 6)
        return f"{label[:keep]}~{suffix}"

    def _number(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_text(self, text: str) -> str:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        normalized = "\n".join(line.rstrip() for line in lines).strip() + "\n"
        return normalized

    def _ends_inside_structure(self, rendered_report: str) -> bool:
        tail = rendered_report.rstrip()
        return tail.endswith(("{", "[", ":", ","))

    def _build_metrics(
        self,
        rendered_report: str,
        validation_errors: list[str],
        *,
        artifact_written: bool,
        diagnostic_artifact_written: bool,
    ) -> dict[str, Any]:
        duplicate_count = sum(
            1
            for section in SECTION_ORDER
            if rendered_report.count(self._section_title(section)) > 1
        )
        raw_count = len(RAW_STRUCTURE_PATTERN.findall(rendered_report))
        return {
            "report_render_success": not validation_errors,
            "report_complete": (
                rendered_report.startswith(REPORT_BEGIN_MARKER)
                and rendered_report.rstrip().endswith(REPORT_END_MARKER)
                and not validation_errors
            ),
            "report_truncated": "Console Appendix: omitted" in rendered_report,
            "report_section_count": sum(
                1
                for section in SECTION_ORDER
                if self._section_title(section) in rendered_report
            ),
            "report_duplicate_section_count": duplicate_count,
            "report_raw_structure_count": raw_count,
            "report_begin_marker_present": rendered_report.startswith(
                REPORT_BEGIN_MARKER,
            ),
            "report_end_marker_present": rendered_report.rstrip().endswith(
                REPORT_END_MARKER,
            ),
            "report_character_count": len(rendered_report),
            "report_line_count": len(rendered_report.splitlines()),
            "report_artifact_written": artifact_written,
            "diagnostic_artifact_written": diagnostic_artifact_written,
            "report_validation_errors": validation_errors,
        }

    def _empty_metrics(self) -> dict[str, Any]:
        return {
            "report_render_success": False,
            "report_complete": False,
            "report_truncated": False,
            "report_section_count": 0,
            "report_duplicate_section_count": 0,
            "report_raw_structure_count": 0,
            "report_begin_marker_present": False,
            "report_end_marker_present": False,
            "report_character_count": 0,
            "report_line_count": 0,
            "report_artifact_written": False,
            "diagnostic_artifact_written": False,
            "report_validation_errors": [],
        }

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if hasattr(value, "tolist"):
            try:
                return value.tolist()
            except Exception:
                return str(value)
        return str(value)

    def _atomic_write_text(self, text: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)


final_report_renderer = DeterministicFinalReportRenderer()
