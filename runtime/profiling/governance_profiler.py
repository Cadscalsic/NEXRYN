"""Governance overhead attribution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class GovernanceMetrics:
    total_governance_time: float
    contradiction_review_time: float
    context_discovery_time: float
    truth_commit_time: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


class GovernanceProfiler:
    def profile(
        self,
        module_timings: list[dict[str, Any]] | None,
        runtime_context: dict[str, Any] | None = None,
    ) -> GovernanceMetrics:
        module_timings = module_timings or []
        total = self._sum_matching(module_timings, ("governance",))
        context = self._sum_matching(module_timings, ("context_discovery", "process_semantic"))
        truth = self._sum_matching(module_timings, ("truth_commit", "truth"))
        contradiction = self._sum_matching(module_timings, ("contradiction",))
        return GovernanceMetrics(
            total_governance_time=round(total, 4),
            contradiction_review_time=round(contradiction, 4),
            context_discovery_time=round(context, 4),
            truth_commit_time=round(truth, 4),
        )

    def _sum_matching(self, module_timings, needles):
        return sum(
            self._float(item.get("seconds"))
            for item in module_timings
            if any(needle in str(item.get("module", "")) for needle in needles)
        )

    def _float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


governance_profiler = GovernanceProfiler()


__all__ = [
    "GovernanceMetrics",
    "GovernanceProfiler",
    "governance_profiler",
]
