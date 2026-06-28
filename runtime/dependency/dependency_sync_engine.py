"""Canonical dependency snapshots shared across runtime layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from core.epistemic_models import clamp


MAX_DEPENDENCY_DEPTH = 8
MAX_DEPENDENCY_CHAINS = 100


PRESERVATION_CONCEPTS = {
    "shape_preservation",
    "color_preservation",
    "position_preservation",
    "topology_preservation",
    "symmetry_preservation",
    "object_identity_preservation",
}


@dataclass
class DependencySnapshot:
    concept: str
    dependency_discovered: bool = False
    dependency_registered: bool = False
    dependency_promoted: bool = False
    dependency_injected: bool = False
    dependency_confidence: float = 0.0
    dependency_chain_coverage: float = 0.0
    dependency_chain_depth: int = 0
    dependency_source: str = "unresolved"
    dependency_block_reason: str | None = None
    missing_dependencies: list[Any] = field(default_factory=list)
    typed_dependency_relations: list[dict[str, Any]] = field(default_factory=list)
    process_dependency_memory: dict[str, Any] = field(default_factory=dict)
    adaptive_dependency_budget: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dependency_confidence"] = round(clamp(data["dependency_confidence"]), 4)
        data["dependency_chain_coverage"] = round(
            clamp(data["dependency_chain_coverage"]),
            4,
        )
        data["dependency_chain_depth"] = max(0, int(data["dependency_chain_depth"]))
        data["dependency_injection_synchronized"] = True
        return data


class DependencyStateRegistry:
    """Stores the single dependency state each runtime should consume."""

    def __init__(self) -> None:
        self._snapshots: dict[str, DependencySnapshot] = {}

    def register(self, snapshot: DependencySnapshot) -> DependencySnapshot:
        self._snapshots[_normalize(snapshot.concept)] = snapshot
        return snapshot

    def get(self, concept: str) -> DependencySnapshot | None:
        return self._snapshots.get(_normalize(concept))

    def report(self) -> dict[str, Any]:
        return {
            "system": "dependency_state_registry",
            "snapshot_count": len(self._snapshots),
            "snapshots": {
                concept: snapshot.as_dict()
                for concept, snapshot in sorted(self._snapshots.items())
            },
        }


class DependencySyncEngine:
    """Build and inject one canonical dependency snapshot per concept."""

    def __init__(
        self,
        registry: DependencyStateRegistry | None = None,
        max_depth: int = MAX_DEPENDENCY_DEPTH,
        max_chains: int = MAX_DEPENDENCY_CHAINS,
    ) -> None:
        self.registry = registry or DependencyStateRegistry()
        self.max_depth = max(1, int(max_depth or MAX_DEPENDENCY_DEPTH))
        self.max_chains = max(1, int(max_chains or MAX_DEPENDENCY_CHAINS))

    def synchronize(
        self,
        concept: str,
        runtime: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime = runtime if isinstance(runtime, Mapping) else {}
        snapshot = self.snapshot(concept, runtime)
        self.registry.register(snapshot)
        return self.inject(runtime, snapshot)

    def snapshot(
        self,
        concept: str,
        runtime: Mapping[str, Any] | None = None,
    ) -> DependencySnapshot:
        concept = _normalize(concept)
        runtime = runtime if isinstance(runtime, Mapping) else {}
        sources = self._candidate_sources(runtime)

        confidence, confidence_source = self._best_number(
            sources,
            "dependency_confidence",
        )
        coverage, coverage_source = self._best_number(
            sources,
            "dependency_chain_coverage",
        )
        depth, depth_source = self._best_int(
            sources,
            "dependency_chain_depth",
        )
        missing_dependencies = self._best_list(sources, "missing_dependencies")
        typed_relations = self._best_list(sources, "typed_dependency_relations")
        process_memory = self._best_mapping(
            sources,
            preferred_names=("process_dependency_memory", "runtime"),
        )

        source = (
            confidence_source
            or coverage_source
            or depth_source
            or "unresolved"
        )
        depth = min(depth, self.max_depth)
        coverage = max(coverage, clamp(depth / self.max_depth if depth else 0.0))
        discovered = bool(confidence > 0.0 or depth > 0 or typed_relations)
        registered = bool(process_memory or runtime.get("process_dependency_memory"))
        promoted = bool(
            confidence > 0.85
            and coverage > 0.0
            and depth >= 3
            and not missing_dependencies
        )
        block_reason = self._block_reason(
            discovered,
            confidence,
            coverage,
            depth,
            missing_dependencies,
        )
        return DependencySnapshot(
            concept=concept,
            dependency_discovered=discovered,
            dependency_registered=registered,
            dependency_promoted=promoted,
            dependency_injected=discovered,
            dependency_confidence=confidence,
            dependency_chain_coverage=coverage,
            dependency_chain_depth=depth,
            dependency_source=source,
            dependency_block_reason=block_reason,
            missing_dependencies=missing_dependencies,
            typed_dependency_relations=typed_relations,
            process_dependency_memory=dict(process_memory),
            adaptive_dependency_budget={
                "MAX_DEPENDENCY_DEPTH": self.max_depth,
                "MAX_DEPENDENCY_CHAINS": self.max_chains,
                "dependency_early_exit_enabled": True,
                "dependency_reuse_enabled": True,
                "dependency_depth_guard_applied": depth >= self.max_depth,
                "dependency_chain_budget_remaining": max(
                    0,
                    self.max_chains - _int(runtime.get("dependency_chains_executed")),
                ),
            },
        )

    def inject(
        self,
        runtime: Mapping[str, Any] | None,
        snapshot: DependencySnapshot,
    ) -> dict[str, Any]:
        data = dict(runtime or {})
        snapshot_data = snapshot.as_dict()
        process_memory = {
            **snapshot.process_dependency_memory,
            **snapshot_data,
        }
        data.update({
            "dependency_snapshot": snapshot_data,
            "dependency_confidence": snapshot.dependency_confidence,
            "dependency_chain_coverage": snapshot.dependency_chain_coverage,
            "dependency_chain_depth": snapshot.dependency_chain_depth,
            "missing_dependencies": list(snapshot.missing_dependencies),
            "process_dependency_memory": process_memory,
            "dependency_promotion_evidence": snapshot_data,
            "adaptive_dependency_budget": snapshot.adaptive_dependency_budget,
        })
        causal_validation = data.get("causal_validation", {})
        if isinstance(causal_validation, Mapping):
            data["causal_validation"] = {
                **dict(causal_validation),
                "dependency_confidence": snapshot.dependency_confidence,
                "dependency_chain_coverage": snapshot.dependency_chain_coverage,
                "dependency_chain_depth": snapshot.dependency_chain_depth,
                "missing_dependencies": list(snapshot.missing_dependencies),
                "dependency_promotion_evidence": snapshot_data,
            }
        return data

    def _candidate_sources(
        self,
        runtime: Mapping[str, Any],
    ) -> list[tuple[str, Mapping[str, Any]]]:
        sources: list[tuple[str, Mapping[str, Any]]] = [("runtime", runtime)]
        for name in (
            "dependency_snapshot",
            "process_dependency_memory",
            "dependency_promotion_evidence",
            "dependency_chain_alignment",
            "typed_dependency_report",
        ):
            value = runtime.get(name)
            if isinstance(value, Mapping):
                sources.append((name, value))
        causal_validation = runtime.get("causal_validation")
        if isinstance(causal_validation, Mapping):
            sources.append(("causal_validation", causal_validation))
            evidence = causal_validation.get("dependency_promotion_evidence")
            if isinstance(evidence, Mapping):
                sources.append(("causal_validation.dependency_promotion_evidence", evidence))
        return sources

    def _best_number(
        self,
        sources: list[tuple[str, Mapping[str, Any]]],
        key: str,
    ) -> tuple[float, str | None]:
        best = 0.0
        best_source: str | None = None
        for source, mapping in sources:
            value = clamp(mapping.get(key, 0.0))
            if value > best:
                best = value
                best_source = source
        return best, best_source

    def _best_int(
        self,
        sources: list[tuple[str, Mapping[str, Any]]],
        key: str,
    ) -> tuple[int, str | None]:
        best = 0
        best_source: str | None = None
        for source, mapping in sources:
            value = _int(mapping.get(key))
            if value > best:
                best = value
                best_source = source
        return best, best_source

    def _best_list(
        self,
        sources: list[tuple[str, Mapping[str, Any]]],
        key: str,
    ) -> list[Any]:
        for _, mapping in sources:
            value = mapping.get(key)
            if isinstance(value, list) and value:
                return list(value)
        return []

    def _best_mapping(
        self,
        sources: list[tuple[str, Mapping[str, Any]]],
        preferred_names: tuple[str, ...],
    ) -> Mapping[str, Any]:
        for preferred in preferred_names:
            for source, mapping in sources:
                if source == preferred and mapping:
                    return mapping
        return {}

    def _block_reason(
        self,
        discovered: bool,
        confidence: float,
        coverage: float,
        depth: int,
        missing_dependencies: list[Any],
    ) -> str | None:
        if not discovered:
            return "dependency_not_discovered"
        if missing_dependencies:
            return "dependency_chain_missing_dependencies"
        if confidence <= 0.0:
            return "dependency_confidence_zero"
        if confidence <= 0.85:
            return "dependency_confidence_below_promotion_floor"
        if coverage <= 0.0:
            return "dependency_chain_coverage_zero"
        if depth <= 0:
            return "dependency_chain_depth_zero"
        return None


def _normalize(value: Any) -> str:
    return str(value or "").strip()


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


dependency_state_registry = DependencyStateRegistry()
dependency_sync_engine = DependencySyncEngine(dependency_state_registry)


__all__ = [
    "DependencySnapshot",
    "DependencyStateRegistry",
    "DependencySyncEngine",
    "MAX_DEPENDENCY_DEPTH",
    "MAX_DEPENDENCY_CHAINS",
    "PRESERVATION_CONCEPTS",
    "dependency_state_registry",
    "dependency_sync_engine",
]
