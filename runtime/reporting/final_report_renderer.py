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


REPORT_BEGIN_MARKER = "<<< NEXRYN_REPORT_BEGIN >>>"
REPORT_END_MARKER = "<<< NEXRYN_REPORT_END >>>"

SECTION_ORDER = [
    "REPORT HEADER",
    "EXECUTION SUMMARY",
    "COGNITIVE OUTPUTS",
    "PROGRAM QUALITY",
    "SEMANTIC COMPILATION",
    "TRANSFORMATION DECISION",
    "COGNITIVE CANDIDATE ARENA",
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

    def __init__(self, console_budget_chars: int = 30000):
        self.console_budget_chars = int(console_budget_chars or 30000)
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
        binding_result = canonical_report_binding_engine.bind(
            report_state,
            runtime_metadata=runtime_metadata,
            report_level=report_level,
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

        compression_result = compact_report_compression_engine.compress(
            bound_report_state,
            profile=report_level,
            artifact_directory=artifact_directory,
            write_appendix=write_diagnostic_artifact,
        )
        compressed_report_state = compression_result["compressed_report"]

        canonical = self._canonical_state(
            compressed_report_state,
            runtime_metadata=runtime_metadata,
            report_level=report_level,
            binding_result=binding_result,
        )
        full_report = self._render_full_report(canonical)
        validation_errors = self.validate(full_report)
        rendered_report = full_report

        if budget > 0 and len(full_report) > budget:
            rendered_report = self._render_budget_summary(canonical, full_report)
            validation_errors = self.validate(rendered_report)

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
        stream.write(rendered_report)
        if not rendered_report.endswith("\n"):
            stream.write("\n")
        stream.flush()

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
            self._render_semantic_compilation(canonical),
            self._render_transformation_decision(canonical),
            self._render_candidate_arena(canonical),
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
            self._render_semantic_compilation(canonical),
            self._render_transformation_decision(canonical),
            self._render_candidate_arena(canonical),
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
            f"Execution Intents: {self._value(summary.get('execution_intent_count'))}",
            f"Compiler Triggered: {self._value(summary.get('compiler_triggered'))}",
            f"Compiled Candidates: {self._value(summary.get('compiled_candidate_count'))}",
            f"Selected Intent: {self._value(summary.get('selected_intent'))}",
            f"Compiled Operation: {self._value(summary.get('compiled_operation'))}",
            f"Selected Operation: {self._value(summary.get('selected_operation'))}",
            f"Selected From Compiler: {self._value(summary.get('selected_from_compiler'))}",
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
        lines = [
            f"Arena State: {self._value(summary.get('arena_state'))}",
            f"Candidate Count: {self._value(summary.get('candidate_count'))}",
            f"Competitor Sources: {', '.join(str(item) for item in sources) if sources else 'Not Available'}",
            f"Winner Source: {self._value(summary.get('winner_source'))}",
            f"Arena Winner: {self._value(summary.get('arena_winner'))}",
            f"Winner Takes All Detected: {self._value(summary.get('winner_takes_all_detected'))}",
            f"Dominance Source: {self._value(summary.get('dominance_source'))}",
            f"Selection Mode: {self._value(summary.get('selection_mode'))}",
            f"Validation Coverage: {self._percent(summary.get('validation_coverage'))}",
            f"Missing Competition Reason: {self._value(summary.get('missing_competition_reason'))}",
        ]
        if rows:
            lines.append("Top Arena Candidates:")
            for index, row in enumerate(rows[:6], start=1):
                if not isinstance(row, dict):
                    continue
                marker = "selected" if row.get("selected") else "candidate"
                lines.append(
                    "  "
                    f"{index}. {self._value(row.get('source'))}: "
                    f"{self._value(row.get('candidate_id'))} "
                    f"op={self._value(row.get('operation'))} "
                    f"confidence={self._value(row.get('confidence'))} "
                    f"status={self._value(row.get('validation_status'))} "
                    f"{marker}"
                )
        if canonical["report_level"] == "diagnostic" and source_status:
            lines.append("Arena Source Status:")
            for source, status in sorted(source_status.items()):
                lines.append(f"  {source}: {status}")
        return self._section("COGNITIVE CANDIDATE ARENA", lines)

    def _render_search_quality(self, canonical: dict[str, Any]) -> str:
        search = canonical["search"]
        return self._section("SEARCH QUALITY", [
            f"Overall Search Quality: {self._field(canonical, 'overall_search_quality')}",
            f"Search Efficiency: {self._field(canonical, 'search_efficiency')}",
            f"Search Coverage: {self._field(canonical, 'search_coverage')}",
            f"Search Entropy: {self._field(canonical, 'search_entropy')}",
            f"Average Route Quality: {self._field(canonical, 'average_route_quality')}",
        ])

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
        entropy = self._read_any(search, "search_entropy")
        routes = self._read_any(search, "route_count", "unique_route_count")
        if self._number(entropy) == 0 and (self._number(routes) or 0) > 1:
            warnings.append("Search entropy remains zero despite multiple routes.")
        if (
            self._read_any(program, "validation_distribution") is None
            and self._read_any(program, "generated_programs") is not None
        ):
            warnings.append("Generated programs lack final lifecycle states.")
        if isinstance(compact, dict) and all(
            int(compact.get(key, 0) or 0) == 0
            for key in (
                "heavy_keys_removed",
                "arrays_summarized",
                "repeated_reports_collapsed",
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
