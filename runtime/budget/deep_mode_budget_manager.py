"""Budget policy for bounded deep-mode execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class DeepModeBudget:
    max_total_runtime_seconds: float = 120.0
    max_task_runtime_seconds: float = 30.0
    max_report_time_seconds: float = 5.0
    max_concept_lifecycle_seconds: float = 2.0
    max_diagnostic_sections: int = 5
    max_deep_concepts: int = 12
    max_deep_chain_depth: int = 6

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_total_runtime_seconds": self.max_total_runtime_seconds,
            "max_task_runtime_seconds": self.max_task_runtime_seconds,
            "max_report_time_seconds": self.max_report_time_seconds,
            "max_concept_lifecycle_seconds":
            self.max_concept_lifecycle_seconds,
            "max_diagnostic_sections": self.max_diagnostic_sections,
            "max_deep_concepts": self.max_deep_concepts,
            "max_deep_chain_depth": self.max_deep_chain_depth,
        }


class DeepModeBudgetManager:
    """Keep deep mode selective, lazy, and budget-aware."""

    system_name = "deep_mode_budget_manager"

    AUDIT_FLAG_TO_SECTION = {
        "audit_concepts": "concepts",
        "audit_dependencies": "dependencies",
        "audit_truth": "truth",
        "audit_cache": "cache",
        "audit_lineage": "lineage",
    }

    def __init__(self, defaults: DeepModeBudget | None = None):
        self.defaults = defaults or DeepModeBudget()

    def build_budget(self, **overrides) -> DeepModeBudget:
        values = self.defaults.as_dict()
        for key, value in overrides.items():
            if value is None or key not in values:
                continue
            values[key] = max(float(value), 0.0)
        values["max_diagnostic_sections"] = int(values["max_diagnostic_sections"])
        values["max_deep_concepts"] = max(int(values["max_deep_concepts"]), 1)
        values["max_deep_chain_depth"] = max(int(values["max_deep_chain_depth"]), 1)
        return DeepModeBudget(**values)

    def audit_flags_from_args(self, args) -> dict[str, bool]:
        return {
            flag: bool(getattr(args, flag, False))
            for flag in self.AUDIT_FLAG_TO_SECTION
        }

    def requested_sections(self, audit_flags: Mapping[str, Any] | None) -> list[str]:
        audit_flags = audit_flags if isinstance(audit_flags, Mapping) else {}
        return [
            section
            for flag, section in self.AUDIT_FLAG_TO_SECTION.items()
            if audit_flags.get(flag)
        ]

    def should_expand(
        self,
        section: str,
        audit_flags: Mapping[str, Any] | None = None,
    ) -> bool:
        return section in self.requested_sections(audit_flags)

    def bounded_report_level(
        self,
        mode: str,
        report_level: str,
        audit_flags: Mapping[str, Any] | None = None,
    ) -> str:
        mode = str(mode or "adaptive").lower()
        report_level = str(report_level or "normal").lower()
        if mode not in {"deep", "full"}:
            return report_level
        if report_level not in {"full", "debug", "audit"}:
            return report_level
        if self.requested_sections(audit_flags):
            return report_level
        return "normal"

    def constrain_reasoning_budget(
        self,
        budget: Mapping[str, Any],
        deep_budget: DeepModeBudget | None = None,
    ) -> dict[str, Any]:
        deep_budget = deep_budget or self.defaults
        constrained = dict(budget or {})
        constrained["cache_dependencies"] = True
        constrained["full_governance"] = False
        constrained["max_concepts"] = (
            min(
                int(constrained["max_concepts"]),
                deep_budget.max_deep_concepts,
            )
            if constrained.get("max_concepts")
            else deep_budget.max_deep_concepts
        )
        constrained["max_chain_depth"] = (
            min(
                int(constrained["max_chain_depth"]),
                deep_budget.max_deep_chain_depth,
            )
            if constrained.get("max_chain_depth")
            else deep_budget.max_deep_chain_depth
        )
        constrained["max_dependency_depth"] = constrained["max_chain_depth"]
        constrained["deep_budget"] = deep_budget.as_dict()
        constrained["deep_selective_execution_enabled"] = True
        return constrained

    def task_budget_exceeded(
        self,
        elapsed_seconds: float,
        deep_budget: DeepModeBudget | Mapping[str, Any] | None = None,
    ) -> bool:
        budget = self._budget_dict(deep_budget)
        return float(elapsed_seconds or 0.0) > float(
            budget.get("max_task_runtime_seconds", self.defaults.max_task_runtime_seconds)
        )

    def concept_lifecycle_budget_exceeded(
        self,
        elapsed_seconds: float,
        deep_budget: DeepModeBudget | Mapping[str, Any] | None = None,
    ) -> bool:
        budget = self._budget_dict(deep_budget)
        return float(elapsed_seconds or 0.0) > float(
            budget.get(
                "max_concept_lifecycle_seconds",
                self.defaults.max_concept_lifecycle_seconds,
            )
        )

    def report_budget_exceeded(
        self,
        elapsed_seconds: float,
        deep_budget: DeepModeBudget | Mapping[str, Any] | None = None,
    ) -> bool:
        budget = self._budget_dict(deep_budget)
        return float(elapsed_seconds or 0.0) > float(
            budget.get("max_report_time_seconds", self.defaults.max_report_time_seconds)
        )

    def build_report(
        self,
        mode: str = "adaptive",
        deep_budget: DeepModeBudget | Mapping[str, Any] | None = None,
        audit_flags: Mapping[str, Any] | None = None,
        layers_requested: list[str] | None = None,
        layers_executed: list[str] | None = None,
        layers_deferred: list[str] | None = None,
        reports_generated: list[str] | None = None,
        reports_skipped: list[str] | None = None,
        concepts_recomputed: int = 0,
        concepts_reused: int = 0,
        elapsed: Mapping[str, Any] | None = None,
        task_budget_exceeded: bool = False,
    ) -> dict[str, Any]:
        budget = self._budget_dict(deep_budget)
        elapsed = elapsed if isinstance(elapsed, Mapping) else {}
        used = {
            "total_runtime_seconds": float(elapsed.get("total_runtime_seconds", 0.0) or 0.0),
            "report_generation_seconds": float(elapsed.get("report_generation_seconds", 0.0) or 0.0),
            "concept_lifecycle_seconds": float(elapsed.get("concept_lifecycle_seconds", 0.0) or 0.0),
            "task_runtime_seconds": float(elapsed.get("task_runtime_seconds", 0.0) or 0.0),
        }
        remaining = {
            "total_runtime_seconds": round(
                max(budget["max_total_runtime_seconds"] - used["total_runtime_seconds"], 0.0),
                4,
            ),
            "report_generation_seconds": round(
                max(budget["max_report_time_seconds"] - used["report_generation_seconds"], 0.0),
                4,
            ),
            "concept_lifecycle_seconds": round(
                max(
                    budget["max_concept_lifecycle_seconds"]
                    - used["concept_lifecycle_seconds"],
                    0.0,
                ),
                4,
            ),
            "task_runtime_seconds": round(
                max(budget["max_task_runtime_seconds"] - used["task_runtime_seconds"], 0.0),
                4,
            ),
        }
        return {
            "system": self.system_name,
            "DEEP_MODE_OPTIMIZATION_REPORT": True,
            "mode": mode,
            "bounded_deep_mode": str(mode).lower() in {"deep", "full"},
            "selective_execution_enabled": True,
            "deep_budget": budget,
            "deep_budget_used": used,
            "deep_budget_remaining": remaining,
            "audit_sections_requested": self.requested_sections(audit_flags),
            "layers_requested": list(layers_requested or []),
            "layers_executed": list(layers_executed or []),
            "layers_deferred": list(layers_deferred or []),
            "reports_generated": list(reports_generated or []),
            "reports_skipped": list(reports_skipped or []),
            "concepts_recomputed": int(concepts_recomputed or 0),
            "concepts_reused": int(concepts_reused or 0),
            "task_budget_exceeded": bool(task_budget_exceeded),
            "report_budget_exceeded": self.report_budget_exceeded(
                used["report_generation_seconds"],
                budget,
            ),
            "concept_lifecycle_budget_exceeded":
            self.concept_lifecycle_budget_exceeded(
                used["concept_lifecycle_seconds"],
                budget,
            ),
        }

    def _budget_dict(
        self,
        budget: DeepModeBudget | Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if isinstance(budget, DeepModeBudget):
            return budget.as_dict()
        if isinstance(budget, Mapping):
            return {**self.defaults.as_dict(), **dict(budget)}
        return self.defaults.as_dict()


deep_mode_budget_manager = DeepModeBudgetManager()


__all__ = [
    "DeepModeBudget",
    "DeepModeBudgetManager",
    "deep_mode_budget_manager",
]
