"""Single-source metric ownership for runtime observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class MetricAuthority:
    metric_name: str
    producer: str
    storage_location: str
    update_frequency: str
    last_update_stage: str

    def as_dict(self) -> dict[str, str]:
        return {
            "metric_name": self.metric_name,
            "producer": self.producer,
            "storage_location": self.storage_location,
            "update_frequency": self.update_frequency,
            "last_update_stage": self.last_update_stage,
        }


class MetricAuthorityRegistry:
    """Resolve public metrics from their canonical producer."""

    def __init__(self) -> None:
        self._authorities: dict[str, MetricAuthority] = {}
        self._register_defaults()

    def register(
        self,
        metric_name: str,
        producer: str,
        storage_location: str,
        update_frequency: str = "per_runtime_cycle",
        last_update_stage: str = "finalization",
    ) -> None:
        if metric_name in self._authorities:
            existing = self._authorities[metric_name]
            if existing.producer != producer:
                raise ValueError(
                    f"duplicate metric authority for {metric_name}: "
                    f"{existing.producer} and {producer}"
                )
        self._authorities[metric_name] = MetricAuthority(
            metric_name=metric_name,
            producer=producer,
            storage_location=storage_location,
            update_frequency=update_frequency,
            last_update_stage=last_update_stage,
        )

    def authority_for(self, metric_name: str) -> dict[str, str] | None:
        authority = self._authorities.get(metric_name)
        return authority.as_dict() if authority else None

    def source_map(self) -> dict[str, dict[str, str]]:
        return {
            name: authority.as_dict()
            for name, authority in sorted(self._authorities.items())
        }

    def reconcile(
        self,
        metrics: Mapping[str, Any],
        sources: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        reconciled = dict(metrics)
        conflicts = []
        for metric_name, authority in self._authorities.items():
            authoritative = sources.get(authority.producer, {})
            if metric_name not in authoritative:
                continue
            canonical = authoritative.get(metric_name)
            observed = {
                source_name: source.get(metric_name)
                for source_name, source in sources.items()
                if metric_name in source
            }
            conflicting = {
                source_name: value
                for source_name, value in observed.items()
                if value != canonical
            }
            if conflicting:
                conflicts.append({
                    "metric_name": metric_name,
                    "authority": authority.producer,
                    "canonical_value": canonical,
                    "conflicting_sources": conflicting,
                })
            reconciled[metric_name] = canonical
        reconciled["METRIC_SOURCE_MAP"] = self.source_map()
        reconciled["metric_authority_conflicts"] = conflicts
        return reconciled

    def _register_defaults(self) -> None:
        for name in (
            "dependency_chains_executed",
            "dependency_chain_depth",
            "dependency_chain_coverage",
            "dependency_reasoning_skipped",
            "dependency_activation_state",
            "dependency_time",
            "dependency_executor_cache_hits",
            "dependency_executor_cache_misses",
        ):
            self.register(
                name,
                "dependency_runtime",
                "performance_report/dependency_reasoning_report",
                last_update_stage="dependency_reasoning",
            )
        for name in (
            "context_count",
            "registered_context_count",
            "semantic_context_count",
            "process_context_count",
            "context_created",
            "context_registered",
            "context_consumed",
            "context_lost",
        ):
            self.register(
                name,
                "context_registry",
                "performance_counters/context_registry_report",
                last_update_stage="context_truth_advancement",
            )
        for name in ("candidate_count", "candidate_generated", "candidate_rejected"):
            self.register(
                name,
                "truth_candidate_engine",
                "truth_candidate_report/performance_counters",
                last_update_stage="context_truth_advancement",
            )
        for name in (
            "committed_count",
            "truth_commit_count",
            "truth_committed",
            "truth_rejected",
        ):
            self.register(
                name,
                "truth_commit_engine",
                "truth_commit_report/performance_counters",
                last_update_stage="context_truth_advancement",
            )
        for name in (
            "strategy_hits",
            "strategy_misses",
            "truth_hits",
            "truth_misses",
            "context_hits",
            "context_misses",
            "program_hits",
            "program_misses",
            "reuse_rate",
            "estimated_compute_saved",
            "estimated_runtime_saved",
        ):
            self.register(
                name,
                "adaptive_reuse_engine",
                "adaptive_reuse_engine.report",
                last_update_stage="performance_report",
            )
        for name in ("cache_hits", "cache_misses", "cache_hit_rate"):
            self.register(
                name,
                "local_runtime_cache",
                "performance_counters",
                last_update_stage="performance_report",
            )


metric_authority_registry = MetricAuthorityRegistry()


__all__ = ["MetricAuthorityRegistry", "metric_authority_registry"]
