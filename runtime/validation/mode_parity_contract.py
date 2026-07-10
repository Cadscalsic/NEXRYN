"""Formal cross-mode parity contract for NEXRYN execution profiles."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModeParityContract:
    invariant_components: tuple[str, ...] = (
        "Runtime Registry",
        "Execution Registry",
        "Execution Tree structure",
        "Lifecycle stages",
        "Metric ownership",
        "Binding rules",
        "World Model access",
        "DNA access",
        "Knowledge Bus",
        "Shared Cognitive State",
        "Truth contract",
        "Memory contract",
        "Concept contract",
        "Program contract",
        "Search contract",
        "Governance contract",
    )
    allowed_differences: tuple[str, ...] = (
        "Search depth",
        "Route count",
        "Validation count",
        "Reasoning depth",
        "Execution budget",
        "Timeout thresholds",
        "Report verbosity",
        "Snapshot density",
        "Persistence detail",
        "Telemetry volume",
    )
    monotonic_metrics: tuple[str, ...] = (
        "context_coverage",
        "validation_depth",
        "truth_evidence_coverage",
        "memory_visibility",
    )
    exact_metrics: dict[str, object] = field(default_factory=lambda: {
        "lifecycle_coverage": 1.0,
        "binding_coverage": 1.0,
        "timing_coverage": 1.0,
        "registry_synchronization": "SYNCHRONIZED",
        "synthetic_execution_count": 0,
    })
    failure_categories: tuple[str, ...] = (
        "EXPECTED_PROFILE_DIFFERENCE",
        "SEMANTIC_REFINEMENT",
        "CONTEXT_LOSS",
        "KNOWLEDGE_LOSS",
        "TRUTH_LOSS",
        "MEMORY_LOSS",
        "LIFECYCLE_DIVERGENCE",
        "REGISTRY_DIVERGENCE",
        "BINDING_DIVERGENCE",
        "GOVERNANCE_DIVERGENCE",
        "RESOURCE_EXHAUSTION",
        "TIMEOUT",
        "REPORTING_DEFECT",
        "STATE_REBUILD",
        "STATE_LEAKAGE",
        "CROSS_TASK_CONTAMINATION",
        "UNEXPLAINED_OUTPUT_DIVERGENCE",
    )
    resource_limits: dict[str, float] = field(default_factory=lambda: {
        "maximum_execution_time_seconds": 120.0,
        "maximum_routes": 64.0,
        "maximum_branch_depth": 12.0,
        "maximum_branch_width": 16.0,
        "maximum_concepts": 512.0,
        "maximum_programs": 256.0,
        "maximum_truth_candidates": 512.0,
        "maximum_graph_nodes": 4096.0,
        "maximum_graph_edges": 8192.0,
        "maximum_memory_growth": 1024.0,
        "maximum_snapshots": 128.0,
        "maximum_report_size": 5_000_000.0,
        "maximum_finalization_time_seconds": 10.0,
        "maximum_governance_time_seconds": 20.0,
    })
    stage_order: tuple[str, ...] = (
        "Boot",
        "Registry",
        "Shared Context",
        "Reasoning",
        "Search",
        "Concept Formation",
        "Program Synthesis",
        "Adaptive Search",
        "Knowledge Integration",
        "Truth Runtime",
        "Memory Runtime",
        "Evaluation",
        "Execution Finalization",
        "Reporting",
    )

    def as_dict(self) -> dict[str, object]:
        return {
            "invariant_components": list(self.invariant_components),
            "allowed_differences": list(self.allowed_differences),
            "monotonic_metrics": list(self.monotonic_metrics),
            "exact_metrics": dict(self.exact_metrics),
            "failure_categories": list(self.failure_categories),
            "resource_limits": dict(self.resource_limits),
            "stage_order": list(self.stage_order),
        }


mode_parity_contract = ModeParityContract()


__all__ = ["ModeParityContract", "mode_parity_contract"]
