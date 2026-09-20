"""Report projection governance for post-execution finalization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from runtime.resource_governance.execution_policy import ExecutionPolicyName


class ReportProjection(str, Enum):
    MINIMAL_RESULT = "MINIMAL_RESULT"
    COMPACT_OPERATIONAL = "COMPACT_OPERATIONAL"
    STANDARD = "STANDARD"
    RESEARCH = "RESEARCH"
    DIAGNOSTIC = "DIAGNOSTIC"


@dataclass(frozen=True)
class ReportProjectionContract:
    projection_name: str
    required_sections: tuple[str, ...]
    lazy_sections: tuple[str, ...]
    deferred_sections: tuple[str, ...]
    max_construction_time: float
    max_report_size: int
    diagnostic_appendix_allowed: bool
    canonical_binding_mode: str
    final_rendering_sync: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "projection_name": self.projection_name,
            "required_sections": list(self.required_sections),
            "lazy_sections": list(self.lazy_sections),
            "deferred_sections": list(self.deferred_sections),
            "max_construction_time": self.max_construction_time,
            "max_report_size": self.max_report_size,
            "diagnostic_appendix_allowed": self.diagnostic_appendix_allowed,
            "canonical_binding_mode": self.canonical_binding_mode,
            "final_rendering_sync": self.final_rendering_sync,
        }


@dataclass
class ReportBindingMetrics:
    projection_name: str
    bound_section_count: int = 0
    skipped_section_count: int = 0
    source_nodes_visited: int = 0
    objects_copied: int = 0
    binding_duration: float = 0.0

    def as_dict(self):
        return dict(self.__dict__)


class ReportingGovernor:
    def select_projection(self, policy: ExecutionPolicyName, terminal_state: str | None = None) -> ReportProjectionContract:
        if policy == ExecutionPolicyName.LOW_LATENCY:
            return self._contract(ReportProjection.MINIMAL_RESULT, ("task_id", "terminal_state", "final_prediction", "governor_summary", "deferred_maintenance_status"), (), ("diagnostic_appendix", "knowledge_fabric", "full_registry_histories"), 0.05, 8_192, False, "projected", True)
        if policy == ExecutionPolicyName.MAX_ACCURACY:
            return self._contract(ReportProjection.STANDARD, ("task_id", "terminal_state", "final_prediction", "validated_result_provenance", "governor_summary"), ("semantic_delta", "program_delta"), ("full_fabric_report", "deep_appendix"), 0.25, 65_536, False, "projected", True)
        if policy == ExecutionPolicyName.RESEARCH:
            return self._contract(ReportProjection.RESEARCH, ("task_id", "terminal_state", "provenance", "telemetry_summary"), ("research_appendix",), ("complete_registry_snapshots",), 0.75, 262_144, False, "research_projected", True)
        if policy == ExecutionPolicyName.DIAGNOSTIC:
            return self._contract(ReportProjection.DIAGNOSTIC, ("task_id", "terminal_state", "signal_ledger", "transition_ledger", "diagnostic_summary"), ("full_dependency_graph", "raw_timing_nodes"), (), 1.0, 524_288, True, "diagnostic_full", True)
        if policy == ExecutionPolicyName.TRAINING:
            return self._contract(ReportProjection.STANDARD, ("task_id", "terminal_state", "training_metrics", "governor_summary"), ("curriculum_delta",), ("training_aggregation", "full_state_save"), 0.3, 65_536, False, "training_projected", True)
        return self._contract(ReportProjection.COMPACT_OPERATIONAL, ("task_id", "terminal_state", "final_prediction", "compact_summary", "governor_summary"), ("registry_delta",), ("knowledge_fabric", "diagnostic_appendix", "full_canonical_report"), 0.15, 32_768, False, "projected", True)

    def bind_projection(self, contract: ReportProjectionContract, available_sections: dict[str, Any] | None = None) -> ReportBindingMetrics:
        sections = dict(available_sections or {})
        bound = sum(1 for section in contract.required_sections if section in sections or section in {"task_id", "terminal_state", "governor_summary"})
        skipped = len(contract.deferred_sections) + max(0, len(contract.required_sections) - bound)
        return ReportBindingMetrics(
            projection_name=contract.projection_name,
            bound_section_count=bound,
            skipped_section_count=skipped,
            source_nodes_visited=bound,
            objects_copied=bound,
            binding_duration=min(contract.max_construction_time, 0.001 * max(bound, 1)),
        )

    def _contract(self, projection, required, lazy, deferred, max_time, max_size, diagnostic, binding, rendering):
        return ReportProjectionContract(projection.value, tuple(required), tuple(lazy), tuple(deferred), max_time, max_size, diagnostic, binding, rendering)


__all__ = ["ReportBindingMetrics", "ReportProjection", "ReportProjectionContract", "ReportingGovernor"]
