"""Cross-mode semantic parity comparison for Adaptive and Deep/Full reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Mapping

from runtime.validation.mode_parity_contract import (
    ModeParityContract,
    mode_parity_contract,
)


@dataclass(frozen=True)
class ModeSnapshot:
    mode: str
    report_sections: set[str]
    runtimes: set[str]
    execution_tree_shape: list[str]
    lifecycle_coverage: float
    binding_coverage: float
    timing_coverage: float
    registry_synchronization: str
    synthetic_execution_count: int
    context_count: int
    context_coverage: float
    concept_count: int
    program_count: int
    search_route_count: int
    truth_candidate_count: int
    validated_truth_count: int
    rejected_truth_count: int
    memory_entry_count: int
    knowledge_object_count: int
    snapshot_count: int
    governance_budget_seconds: float | None
    governance_budget_exceeded: bool
    validation_depth: float
    truth_evidence_coverage: float
    memory_visibility: float
    report_size: int
    total_runtime_seconds: float
    finalization_time_seconds: float
    governance_time_seconds: float
    profile_metadata: dict[str, Any]


class CrossModeParityValidator:
    system_name = "cross_mode_parity_validator"

    def __init__(self, contract: ModeParityContract | None = None) -> None:
        self.contract = contract or mode_parity_contract

    def compare(
        self,
        adaptive_report: Mapping[str, Any],
        full_report: Mapping[str, Any],
        *,
        adaptive_label: str = "adaptive",
        full_label: str = "deep",
    ) -> dict[str, Any]:
        adaptive = self._snapshot(adaptive_report, adaptive_label)
        full = self._snapshot(full_report, full_label)
        differences = []
        expected = []

        differences.extend(self._architecture_diffs(adaptive, full))
        differences.extend(self._monotonicity_diffs(adaptive, full))
        differences.extend(self._continuity_diffs(adaptive, full))
        differences.extend(self._resource_diffs(full))
        differences.extend(self._reporting_diffs(adaptive, full))
        expected.extend(self._expected_profile_differences(adaptive, full))

        critical = [item for item in differences if item["severity"] == "CRITICAL"]
        unexpected = [
            item for item in differences
            if item["category"] != "EXPECTED_PROFILE_DIFFERENCE"
        ]
        first_divergence = self._first_divergence(differences)
        scores = self._scores(adaptive, full, differences)
        parity_score = round(sum(scores.values()) / max(len(scores), 1), 2)
        semantic_status = self._semantic_status(parity_score, critical)
        mode_comparison_report = {
            "system": self.system_name,
            "MODE_COMPARISON_REPORT": True,
            "contract": self.contract.as_dict(),
            "execution_profile_metadata": {
                "adaptive": adaptive.profile_metadata,
                "full": full.profile_metadata,
            },
            "activated_runtimes": {
                "adaptive": sorted(adaptive.runtimes),
                "full": sorted(full.runtimes),
                "missing_in_full": sorted(adaptive.runtimes - full.runtimes),
                "extra_in_full": sorted(full.runtimes - adaptive.runtimes),
            },
            "execution_tree_diff": self._tree_diff(adaptive, full),
            "lifecycle_diff": self._value_diff(
                "lifecycle_coverage",
                adaptive.lifecycle_coverage,
                full.lifecycle_coverage,
            ),
            "registry_diff": {
                "adaptive": adaptive.registry_synchronization,
                "full": full.registry_synchronization,
                "matches": (
                    adaptive.registry_synchronization
                    == full.registry_synchronization
                    == "SYNCHRONIZED"
                ),
            },
            "binding_diff": self._value_diff(
                "binding_coverage",
                adaptive.binding_coverage,
                full.binding_coverage,
            ),
            "context_diff": self._value_diff(
                "context_count",
                adaptive.context_count,
                full.context_count,
            ),
            "concept_diff": self._semantic_count_diff(
                "concept",
                adaptive.concept_count,
                full.concept_count,
            ),
            "program_diff": self._semantic_count_diff(
                "program",
                adaptive.program_count,
                full.program_count,
            ),
            "search_diff": self._value_diff(
                "search_route_count",
                adaptive.search_route_count,
                full.search_route_count,
            ),
            "truth_diff": {
                **self._value_diff(
                    "truth_candidate_count",
                    adaptive.truth_candidate_count,
                    full.truth_candidate_count,
                ),
                "validated_truth_count": full.validated_truth_count,
                "rejected_truth_count": full.rejected_truth_count,
            },
            "memory_diff": self._value_diff(
                "memory_entry_count",
                adaptive.memory_entry_count,
                full.memory_entry_count,
            ),
            "knowledge_diff": self._value_diff(
                "knowledge_object_count",
                adaptive.knowledge_object_count,
                full.knowledge_object_count,
            ),
            "governance_diff": {
                "adaptive_budget_seconds": adaptive.governance_budget_seconds,
                "full_budget_seconds": full.governance_budget_seconds,
                "full_budget_explicit": full.governance_budget_seconds is not None,
                "full_budget_exceeded": full.governance_budget_exceeded,
            },
            "performance_diff": {
                "adaptive_runtime_seconds": adaptive.total_runtime_seconds,
                "full_runtime_seconds": full.total_runtime_seconds,
                "runtime_delta_seconds": round(
                    full.total_runtime_seconds - adaptive.total_runtime_seconds,
                    4,
                ),
            },
            "report_diff": {
                "adaptive_sections": len(adaptive.report_sections),
                "full_sections": len(full.report_sections),
                "full_is_superset": adaptive.report_sections <= full.report_sections,
                "missing_full_sections": sorted(
                    adaptive.report_sections - full.report_sections
                ),
            },
            "semantic_parity_status": semantic_status,
            "expected_differences": expected,
            "unexpected_differences": unexpected,
            "critical_divergences": critical,
            "first_divergence": first_divergence,
            "parity_score_components": scores,
            "mode_parity_score": parity_score,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        stabilization_report = self._stabilization_report(
            mode_comparison_report,
            differences,
            expected,
        )
        return {
            "MODE_COMPARISON_REPORT": mode_comparison_report,
            "FULL_MODE_STABILIZATION_REPORT": stabilization_report,
        }

    def _snapshot(self, report: Mapping[str, Any], mode: str) -> ModeSnapshot:
        data = report if isinstance(report, Mapping) else {}
        performance = _mapping(data.get("performance_report"))
        runtime = _mapping(
            data.get("COGNITIVE_RUNTIME_REPORT")
            or performance.get("COGNITIVE_RUNTIME_REPORT")
            or performance.get("cognitive_runtime_report")
        )
        execution = _mapping(
            data.get("COGNITIVE_EXECUTION_ENGINE_REPORT")
            or performance.get("COGNITIVE_EXECUTION_ENGINE_REPORT")
            or performance.get("cognitive_execution_engine_report")
        )
        binding = _mapping(
            data.get("EXECUTION_BINDING_REPORT")
            or performance.get("EXECUTION_BINDING_REPORT")
            or performance.get("execution_binding_report")
        )
        shared = _mapping(
            data.get("SHARED_COGNITIVE_STATE_REPORT")
            or performance.get("SHARED_COGNITIVE_STATE_REPORT")
            or performance.get("shared_cognitive_state_report")
        )
        metadata = _mapping(data.get("runtime_metadata"))
        shared_counts = _mapping(_path(shared, "state_consistency.counts"))
        runtime_registry = _mapping(runtime.get("runtime_registry"))
        execution_tree = execution.get("execution_tree") or runtime.get("runtime_graph", {}).get("nodes", [])
        truth_report = _mapping(data.get("truth_candidate_report"))
        return ModeSnapshot(
            mode=mode,
            report_sections=set(str(key) for key in data.keys()),
            runtimes=set(str(key) for key in runtime_registry.keys()),
            execution_tree_shape=self._tree_shape(execution_tree),
            lifecycle_coverage=_number(execution.get("lifecycle_coverage")),
            binding_coverage=_number(binding.get("binding_coverage")),
            timing_coverage=_number(binding.get("timing_coverage")),
            registry_synchronization=str(
                binding.get("registry_synchronization") or "UNKNOWN"
            ),
            synthetic_execution_count=int(_number(execution.get("synthetic_execution_count"))),
            context_count=int(_first_number(
                shared_counts.get("context_count"),
                metadata.get("context_count"),
                len(_mapping(data.get("contexts"))),
            )),
            context_coverage=_number(shared.get("context_propagation_coverage")),
            concept_count=int(_first_number(
                shared_counts.get("concept_count"),
                data.get("generated_concepts"),
                performance.get("concept_count"),
            )),
            program_count=int(_first_number(
                shared_counts.get("program_count"),
                data.get("generated_programs"),
                performance.get("generated_programs"),
            )),
            search_route_count=int(_first_number(
                shared_counts.get("search_route_count"),
                _path(performance, "canonical_metrics.search_routes"),
                _path(data, "COGNITIVE_SEARCH_REPORT.route_statistics.routes_created"),
            )),
            truth_candidate_count=int(_first_number(
                shared_counts.get("truth_candidate_count"),
                len(_list(data.get("truth_candidates"))),
                len(_list(truth_report.get("evaluations"))),
            )),
            validated_truth_count=int(_first_number(
                len(_list(data.get("truth_commits"))),
                len(_list(truth_report.get("validated_truths"))),
            )),
            rejected_truth_count=len([
                item for item in _list(truth_report.get("evaluations"))
                if isinstance(item, Mapping)
                and item.get("eligible") is False
            ]),
            memory_entry_count=int(_first_number(
                shared_counts.get("memory_entry_count"),
                _path(performance, "canonical_metrics.memory_entries"),
            )),
            knowledge_object_count=int(_first_number(
                shared_counts.get("knowledge_object_count"),
                _path(data, "COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT.knowledge_object_count"),
            )),
            snapshot_count=int(_first_number(shared_counts.get("snapshot_count"))),
            governance_budget_seconds=_optional_number(
                metadata.get("governance_budget_seconds")
            ),
            governance_budget_exceeded=bool(
                metadata.get("governance_budget_exceeded")
                or performance.get("governance_budget_exceeded")
            ),
            validation_depth=_first_number(
                _path(data, "DEEP_MODE_OPTIMIZATION_REPORT.deep_budget.max_diagnostic_sections"),
                _path(performance, "DEEP_MODE_OPTIMIZATION_REPORT.deep_budget.max_diagnostic_sections"),
                len(_list(truth_report.get("evaluations"))),
            ),
            truth_evidence_coverage=_ratio(
                len(_list(truth_report.get("evaluations")))
                + len(_list(data.get("truth_candidates"))),
                max(int(_first_number(
                    shared_counts.get("truth_candidate_count"),
                    len(_list(data.get("truth_candidates"))),
                )), 1),
            ),
            memory_visibility=_ratio(
                int(_first_number(shared_counts.get("memory_entry_count"), 0)),
                1,
            ),
            report_size=len(json.dumps(data, default=str)),
            total_runtime_seconds=_first_number(
                metadata.get("execution_time"),
                performance.get("total_runtime_seconds"),
                performance.get("execution_time"),
            ),
            finalization_time_seconds=_first_number(
                metadata.get("finalization_duration"),
                _path(performance, "canonical_metrics.finalization_time_seconds"),
            ),
            governance_time_seconds=_first_number(
                metadata.get("governance_budget_seconds"),
                _path(performance, "runtime_breakdown.governance_time"),
            ),
            profile_metadata=_mapping(metadata.get("execution_profile")),
        )

    def _architecture_diffs(self, adaptive, full):
        diffs = []
        missing_runtimes = adaptive.runtimes - full.runtimes
        extra_runtimes = full.runtimes - adaptive.runtimes
        if missing_runtimes:
            diffs.append(self._failure(
                "REGISTRY_DIVERGENCE",
                "runtime_registry",
                "Registry",
                sorted(adaptive.runtimes),
                sorted(full.runtimes),
                "CRITICAL",
                f"Full mode missing runtimes: {sorted(missing_runtimes)}",
                "Ensure all runtimes register through the shared cognitive runtime framework.",
            ))
        if extra_runtimes:
            diffs.append(self._failure(
                "EXPECTED_PROFILE_DIFFERENCE",
                "runtime_registry",
                "Registry",
                sorted(adaptive.runtimes),
                sorted(full.runtimes),
                "INFO",
                "Full mode activated additional declared diagnostic runtimes.",
                "No fix required if declared by profile.",
            ))
        for metric, expected in self.contract.exact_metrics.items():
            observed = getattr(full, metric)
            adaptive_value = getattr(adaptive, metric)
            if observed != expected or adaptive_value != expected:
                category = {
                    "lifecycle_coverage": "LIFECYCLE_DIVERGENCE",
                    "binding_coverage": "BINDING_DIVERGENCE",
                    "timing_coverage": "BINDING_DIVERGENCE",
                    "registry_synchronization": "REGISTRY_DIVERGENCE",
                    "synthetic_execution_count": "REGISTRY_DIVERGENCE",
                }.get(metric, "UNEXPLAINED_OUTPUT_DIVERGENCE")
                diffs.append(self._failure(
                    category,
                    metric,
                    "Registry",
                    expected,
                    {"adaptive": adaptive_value, "full": observed},
                    "CRITICAL",
                    f"{metric} violates required parity value.",
                    "Repair lifecycle/binding instrumentation before accepting full-mode output.",
                ))
        return diffs

    def _monotonicity_diffs(self, adaptive, full):
        checks = [
            ("context_coverage", adaptive.context_coverage, full.context_coverage, "CONTEXT_LOSS"),
            ("validation_depth", adaptive.validation_depth, full.validation_depth, "EXPECTED_PROFILE_DIFFERENCE"),
            ("truth_evidence_coverage", adaptive.truth_evidence_coverage, full.truth_evidence_coverage, "TRUTH_LOSS"),
            ("memory_visibility", adaptive.memory_visibility, full.memory_visibility, "MEMORY_LOSS"),
        ]
        diffs = []
        for metric, left, right, category in checks:
            if right + 1e-9 < left:
                diffs.append(self._failure(
                    category,
                    metric,
                    self._stage_for_metric(metric),
                    left,
                    right,
                    "CRITICAL" if category != "EXPECTED_PROFILE_DIFFERENCE" else "WARNING",
                    f"Full mode {metric} fell below adaptive.",
                    "Inspect shared state propagation and mode profile constraints.",
                ))
        return diffs

    def _continuity_diffs(self, adaptive, full):
        diffs = []
        if adaptive.context_count > 0 and full.context_count == 0:
            diffs.append(self._failure(
                "CONTEXT_LOSS",
                "context_count",
                "Shared Context",
                adaptive.context_count,
                full.context_count,
                "CRITICAL",
                "Full mode context count dropped to zero.",
                "Load SharedCognitiveState before full-mode expansion and prevent silent context rebuild.",
            ))
        if adaptive.truth_candidate_count > 0 and full.truth_candidate_count == 0:
            diffs.append(self._failure(
                "TRUTH_LOSS",
                "truth_candidate_count",
                "Truth Runtime",
                adaptive.truth_candidate_count,
                full.truth_candidate_count,
                "CRITICAL",
                "Full mode silently lost all truth candidates.",
                "Require explicit truth rejection/validation evidence before candidate removal.",
            ))
        if adaptive.knowledge_object_count > 0 and full.knowledge_object_count == 0:
            diffs.append(self._failure(
                "KNOWLEDGE_LOSS",
                "knowledge_object_count",
                "Knowledge Integration",
                adaptive.knowledge_object_count,
                full.knowledge_object_count,
                "CRITICAL",
                "Full mode lost knowledge objects.",
                "Verify CKIL consumes SharedCognitiveState and persists objects.",
            ))
        if adaptive.memory_entry_count > 0 and full.memory_entry_count == 0:
            diffs.append(self._failure(
                "MEMORY_LOSS",
                "memory_entry_count",
                "Memory Runtime",
                adaptive.memory_entry_count,
                full.memory_entry_count,
                "CRITICAL",
                "Full mode lost memory visibility.",
                "Verify memory runtime publication into SharedCognitiveState.",
            ))
        if full.concept_count < adaptive.concept_count:
            diffs.append(self._failure(
                "SEMANTIC_REFINEMENT",
                "concept_count",
                "Concept Formation",
                adaptive.concept_count,
                full.concept_count,
                "INFO",
                "Full mode produced fewer concepts; accepted only when compression or validation explains it.",
                "Attach concept merge/rejection evidence when this occurs in real reports.",
            ))
        if full.program_count < adaptive.program_count:
            diffs.append(self._failure(
                "SEMANTIC_REFINEMENT",
                "program_count",
                "Program Synthesis",
                adaptive.program_count,
                full.program_count,
                "INFO",
                "Full mode produced fewer programs; accepted only when pruning/validation explains it.",
                "Attach program pruning/rejection evidence when this occurs in real reports.",
            ))
        return diffs

    def _resource_diffs(self, full):
        limits = self.contract.resource_limits
        checks = {
            "maximum_execution_time_seconds": full.total_runtime_seconds,
            "maximum_routes": full.search_route_count,
            "maximum_concepts": full.concept_count,
            "maximum_programs": full.program_count,
            "maximum_truth_candidates": full.truth_candidate_count,
            "maximum_memory_growth": full.memory_entry_count,
            "maximum_snapshots": full.snapshot_count,
            "maximum_report_size": full.report_size,
            "maximum_finalization_time_seconds": full.finalization_time_seconds,
            "maximum_governance_time_seconds": full.governance_time_seconds,
        }
        diffs = []
        if full.governance_budget_seconds is None:
            diffs.append(self._failure(
                "GOVERNANCE_DIVERGENCE",
                "governance_budget_seconds",
                "Registry",
                "explicit budget",
                None,
                "CRITICAL",
                "Full mode has no explicit governance budget.",
                "Set a bounded profile governance budget unless using a formal diagnostic profile.",
            ))
        for limit_name, observed in checks.items():
            limit = limits.get(limit_name)
            if limit is not None and observed > limit:
                diffs.append(self._failure(
                    "RESOURCE_EXHAUSTION",
                    limit_name,
                    "Execution Finalization",
                    limit,
                    observed,
                    "WARNING",
                    f"Full mode exceeded {limit_name}.",
                    "Degrade gracefully, emit partial results, and tighten resource guards.",
                ))
        if full.governance_budget_exceeded:
            diffs.append(self._failure(
                "GOVERNANCE_DIVERGENCE",
                "governance_budget_exceeded",
                "Governance",
                False,
                True,
                "WARNING",
                "Full mode exceeded governance budget.",
                "Tune profile governance budget or reduce diagnostic expansion.",
            ))
        return diffs

    def _reporting_diffs(self, adaptive, full):
        if adaptive.report_sections <= full.report_sections:
            return []
        return [self._failure(
            "REPORTING_DEFECT",
            "report_sections",
            "Reporting",
            sorted(adaptive.report_sections),
            sorted(full.report_sections),
            "WARNING",
            "Full report is not a superset of adaptive/normal report sections.",
            "Propagate report_level and verify full report builders execute.",
        )]

    def _expected_profile_differences(self, adaptive, full):
        entries = []
        for metric in (
            "search_route_count",
            "validation_depth",
            "snapshot_count",
            "report_size",
            "total_runtime_seconds",
        ):
            left = getattr(adaptive, metric)
            right = getattr(full, metric)
            if left != right:
                entries.append({
                    "category": "EXPECTED_PROFILE_DIFFERENCE",
                    "metric": metric,
                    "adaptive": left,
                    "full": right,
                    "reason": "Profiles may differ by depth, validation, telemetry, reporting, or budget.",
                })
        return entries

    def _scores(self, adaptive, full, differences):
        def score_for(categories):
            relevant = [item for item in differences if item["category"] in categories]
            if any(item["severity"] == "CRITICAL" for item in relevant):
                return 0.0
            if relevant:
                return 75.0
            return 100.0

        return {
            "Architecture Parity": score_for({"REGISTRY_DIVERGENCE", "STATE_REBUILD"}),
            "Lifecycle Parity": score_for({"LIFECYCLE_DIVERGENCE"}),
            "Registry Parity": score_for({"REGISTRY_DIVERGENCE"}),
            "Context Parity": score_for({"CONTEXT_LOSS"}),
            "Knowledge Parity": score_for({"KNOWLEDGE_LOSS"}),
            "Truth Parity": score_for({"TRUTH_LOSS"}),
            "Memory Parity": score_for({"MEMORY_LOSS"}),
            "Governance Parity": score_for({"GOVERNANCE_DIVERGENCE"}),
            "Reporting Parity": score_for({"REPORTING_DEFECT"}),
            "Recovery Parity": score_for({"RESOURCE_EXHAUSTION", "TIMEOUT"}),
        }

    def _stabilization_report(self, comparison, differences, expected):
        critical = comparison["critical_divergences"]
        unexpected = comparison["unexpected_differences"]
        return {
            "system": self.system_name,
            "FULL_MODE_STABILIZATION_REPORT": True,
            "mode_parity_score": comparison["mode_parity_score"],
            "semantic_parity_status": comparison["semantic_parity_status"],
            "critical_divergences": critical,
            "expected_differences": expected,
            "unexpected_differences": unexpected,
            "first_divergence_point": comparison["first_divergence"],
            "context_continuity": comparison["context_diff"],
            "truth_continuity": comparison["truth_diff"],
            "knowledge_continuity": comparison["knowledge_diff"],
            "governance_status": comparison["governance_diff"],
            "resource_status": [
                item for item in differences
                if item["category"] in {"RESOURCE_EXHAUSTION", "TIMEOUT"}
            ] or [{"status": "BOUNDED"}],
            "report_completeness": comparison["report_diff"],
            "regression_status": "FAILED" if critical else "PASSED",
            "blocking_defects": critical,
            "recommended_fix_order": [
                item["recommended_fix"] for item in critical + unexpected
            ][:10],
        }

    def _first_divergence(self, differences):
        if not differences:
            return {
                "first_divergence_runtime": None,
                "first_divergence_timestamp": None,
                "first_divergence_metric": None,
                "first_divergence_artifact": None,
                "parent_execution": None,
                "downstream_effects": [],
            }
        order = {stage: index for index, stage in enumerate(self.contract.stage_order)}
        selected = sorted(
            differences,
            key=lambda item: order.get(item["first_divergence_stage"], 999),
        )[0]
        return {
            "first_divergence_runtime": selected["affected_runtime"],
            "first_divergence_timestamp": selected["timestamp"],
            "first_divergence_metric": selected["metric"],
            "first_divergence_artifact": selected["observed_value"],
            "parent_execution": selected.get("source_execution_id"),
            "downstream_effects": selected.get("downstream_effects", []),
        }

    def _failure(
        self,
        category,
        runtime,
        stage,
        expected,
        observed,
        severity,
        root_cause,
        fix,
    ):
        return {
            "category": category,
            "affected_runtime": runtime,
            "first_divergence_stage": stage,
            "source_execution_id": None,
            "expected_value": expected,
            "observed_value": observed,
            "severity": severity,
            "probable_root_cause": root_cause,
            "recommended_fix": fix,
            "metric": runtime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "downstream_effects": self._downstream_for_stage(stage),
        }

    def _tree_shape(self, tree):
        if not isinstance(tree, list):
            return []
        shape = []
        for node in tree:
            if isinstance(node, Mapping):
                shape.append(str(node.get("runtime_id") or node.get("execution_type") or node.get("id")))
                shape.extend(self._tree_shape(node.get("children")))
        return shape

    def _tree_diff(self, adaptive, full):
        return {
            "adaptive_shape": adaptive.execution_tree_shape,
            "full_shape": full.execution_tree_shape,
            "same_structure": adaptive.execution_tree_shape == full.execution_tree_shape,
            "missing_in_full": [
                item for item in adaptive.execution_tree_shape
                if item not in full.execution_tree_shape
            ],
        }

    def _value_diff(self, metric, adaptive_value, full_value):
        return {
            "metric": metric,
            "adaptive": adaptive_value,
            "full": full_value,
            "delta": (
                round(full_value - adaptive_value, 4)
                if isinstance(adaptive_value, (int, float))
                and isinstance(full_value, (int, float))
                else None
            ),
        }

    def _semantic_count_diff(self, artifact, adaptive_value, full_value):
        status = (
            "expanded_or_equal"
            if full_value >= adaptive_value
            else "requires_refinement_evidence"
        )
        explanation = (
            "Full/deep may add artifacts through depth."
            if full_value >= adaptive_value
            else f"Fewer {artifact}s require merge, pruning, rejection, or compression evidence."
        )
        return {
            "artifact": artifact,
            "adaptive": adaptive_value,
            "full": full_value,
            "semantic_status": status,
            "explanation": explanation,
        }

    def _semantic_status(self, score, critical):
        if critical:
            return "BLOCKED_BY_CRITICAL_DIVERGENCE"
        if score >= 100:
            return "FULL_PARITY"
        if score >= 90:
            return "ACCEPTABLE_PROFILE_VARIATION"
        if score >= 75:
            return "PARTIAL_PARITY"
        if score >= 50:
            return "ARCHITECTURAL_DIVERGENCE"
        return "MODE_IMPLEMENTATION_SPLIT"

    def _stage_for_metric(self, metric):
        return {
            "context_coverage": "Shared Context",
            "validation_depth": "Truth Runtime",
            "truth_evidence_coverage": "Truth Runtime",
            "memory_visibility": "Memory Runtime",
        }.get(metric, "Reporting")

    def _downstream_for_stage(self, stage):
        order = list(self.contract.stage_order)
        if stage not in order:
            return []
        return order[order.index(stage) + 1:]


def _mapping(value):
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value):
    return value if isinstance(value, list) else []


def _number(value):
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _optional_number(value):
    if value is None:
        return None
    return _number(value)


def _first_number(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return 0.0


def _ratio(numerator, denominator):
    return round(_number(numerator) / max(_number(denominator), 0.0001), 4)


def _path(source, path):
    current = source if isinstance(source, Mapping) else {}
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


cross_mode_parity_validator = CrossModeParityValidator()


__all__ = ["CrossModeParityValidator", "cross_mode_parity_validator"]
