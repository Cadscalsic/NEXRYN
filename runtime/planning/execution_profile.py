"""Execution profiles for the shared cognitive pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


SHARED_METRIC_KEYS = (
    "concept_count",
    "program_count",
    "truth_candidates",
    "memory_entries",
    "search_routes",
    "confidence",
    "costs",
    "durations",
    "coverage",
)

SHARED_LIFECYCLE = (
    "initialize",
    "execute",
    "finalize",
    "report",
    "cleanup",
)


@dataclass(frozen=True)
class ExecutionProfile:
    name: str
    pipeline_name: str = "adaptive"
    reasoning_depth: int = 4
    dependency_depth: int = 6
    search_budget: int = 4
    max_hypotheses: int = 4
    max_contexts: int = 8
    max_concepts: int | None = 8
    report_level: str = "normal"
    telemetry_enabled: bool = True
    cache_dependencies: bool = True
    explanation_enabled: bool = True
    process_semantics_enabled: bool = True
    temporal_reasoning_enabled: bool = False
    full_governance_enabled: bool = False
    validation_level: str = "standard"
    finalization_mode: str = "evidence_based"
    governance_budget_seconds: float | None = 10.0
    audit_sections_requested: tuple[str, ...] = ()
    lifecycle_contract: tuple[str, ...] = SHARED_LIFECYCLE
    metric_contract: tuple[str, ...] = SHARED_METRIC_KEYS
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_budget_defaults(self) -> dict[str, Any]:
        return {
            "mode": self.name,
            "execution_profile": self.name,
            "cognitive_pipeline": self.pipeline_name,
            "pipeline_name": self.pipeline_name,
            "max_chain_depth": self.dependency_depth,
            "max_dependency_depth": self.dependency_depth,
            "max_reasoning_depth": self.reasoning_depth,
            "max_hypotheses": self.max_hypotheses,
            "max_active_routes": self.search_budget,
            "max_contexts": self.max_contexts,
            "max_concepts": self.max_concepts,
            "telemetry_enabled": self.telemetry_enabled,
            "cache_dependencies": self.cache_dependencies,
            "explanation_enabled": self.explanation_enabled,
            "process_semantics_enabled": self.process_semantics_enabled,
            "temporal_reasoning_enabled": self.temporal_reasoning_enabled,
            "full_governance_enabled": self.full_governance_enabled,
            "full_governance": self.full_governance_enabled,
            "report_level": self.report_level,
            "validation_level": self.validation_level,
            "finalization_mode": self.finalization_mode,
            "governance_budget_seconds": self.governance_budget_seconds,
            "audit_sections_requested": list(self.audit_sections_requested),
            "shared_lifecycle_contract": list(self.lifecycle_contract),
            "shared_metric_contract": list(self.metric_contract),
            **dict(self.metadata or {}),
        }

    def as_runtime_metadata(self) -> dict[str, Any]:
        return {
            "execution_profile": self.name,
            "cognitive_pipeline": self.pipeline_name,
            "pipeline_contract": "unified_execution_architecture",
            "profile_extends": "adaptive" if self.name != "adaptive" else None,
            "reasoning_depth": self.reasoning_depth,
            "search_budget": self.search_budget,
            "report_level": self.report_level,
            "validation_level": self.validation_level,
            "finalization_mode": self.finalization_mode,
            "lifecycle_contract": list(self.lifecycle_contract),
            "metric_contract": list(self.metric_contract),
        }


class AdaptiveProfile(ExecutionProfile):
    def __init__(self, **overrides: Any):
        values = {
            "name": "adaptive",
            "reasoning_depth": 4,
            "dependency_depth": 6,
            "search_budget": 4,
            "max_hypotheses": 4,
            "max_contexts": 8,
            "max_concepts": 8,
            "report_level": "normal",
            "validation_level": "standard",
            "finalization_mode": "evidence_based",
            "governance_budget_seconds": 10.0,
        }
        values.update(overrides)
        super().__init__(**values)


class DeepProfile(ExecutionProfile):
    def __init__(self, **overrides: Any):
        values = {
            "name": "deep",
            "reasoning_depth": 8,
            "dependency_depth": 12,
            "search_budget": 10,
            "max_hypotheses": 10,
            "max_contexts": 12,
            "max_concepts": 12,
            "report_level": "full",
            "validation_level": "strict",
            "finalization_mode": "full",
            "governance_budget_seconds": 20.0,
            "full_governance_enabled": True,
        }
        values.update(overrides)
        super().__init__(**values)


class DiagnosticProfile(ExecutionProfile):
    def __init__(self, **overrides: Any):
        values = {
            "name": "diagnostic",
            "reasoning_depth": 6,
            "dependency_depth": 8,
            "search_budget": 6,
            "max_hypotheses": 6,
            "max_contexts": 10,
            "max_concepts": 10,
            "report_level": "debug",
            "validation_level": "diagnostic",
            "finalization_mode": "full",
            "governance_budget_seconds": 20.0,
        }
        values.update(overrides)
        super().__init__(**values)


def build_execution_profile(
    mode: str | None = None,
    report_level: str | None = None,
    audit_sections_requested: list[str] | tuple[str, ...] | None = None,
) -> ExecutionProfile:
    mode = str(mode or "adaptive").lower()
    audit_sections = tuple(audit_sections_requested or ())
    profile_by_mode = {
        "fast": AdaptiveProfile(
            name="fast",
            reasoning_depth=2,
            dependency_depth=4,
            search_budget=3,
            max_hypotheses=2,
            max_contexts=4,
            max_concepts=5,
            report_level="minimal",
            telemetry_enabled=False,
            explanation_enabled=False,
            process_semantics_enabled=False,
            finalization_mode="fast",
            governance_budget_seconds=5.0,
        ),
        "adaptive": AdaptiveProfile(),
        "deep": DeepProfile(audit_sections_requested=audit_sections),
        "full": DeepProfile(
            name="full",
            audit_sections_requested=audit_sections,
        ),
        "diagnostic": DiagnosticProfile(audit_sections_requested=audit_sections),
    }
    profile = profile_by_mode.get(mode, profile_by_mode["adaptive"])
    if report_level is None:
        return profile
    return ExecutionProfile(
        **{
            **profile.__dict__,
            "report_level": str(report_level).lower(),
        }
    )


__all__ = [
    "ExecutionProfile",
    "AdaptiveProfile",
    "DeepProfile",
    "DiagnosticProfile",
    "SHARED_LIFECYCLE",
    "SHARED_METRIC_KEYS",
    "build_execution_profile",
]
