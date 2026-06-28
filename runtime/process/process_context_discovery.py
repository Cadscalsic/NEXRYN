"""Discovery entry point for Alpha 1.1 process contexts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from runtime.process.process_transition_extractor import (
    ProcessTransitionExtractor,
)


class ProcessContextDiscovery:
    """Discover process context families from concepts and dependency chains."""

    system_name = "process_context_discovery"

    CONTEXT_FAMILIES = {
        "learning": [
            "learn",
            "learning",
            "discover",
            "discovery",
            "explore",
            "observe",
            "evidence",
        ],
        "validation": [
            "verify",
            "validate",
            "validation",
            "confirm",
            "test",
            "trial",
            "attestation",
        ],
        "adaptation": [
            "adapt",
            "adaptive",
            "adjust",
            "optimize",
            "improve",
            "repair",
            "stabilize",
        ],
        "execution": [
            "execute",
            "execution",
            "apply",
            "perform",
            "transform",
            "commit",
        ],
        "planning": [
            "plan",
            "planning",
            "predict",
            "forecast",
            "simulate",
            "anticipate",
        ],
        "governance": [
            "governance",
            "constitution",
            "policy",
            "permission",
            "identity",
            "truth",
        ],
    }

    def __init__(self, extractor: ProcessTransitionExtractor | None = None):
        self.extractor = extractor or ProcessTransitionExtractor()
        self._cache: dict[str, dict[str, Any]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _stable_hash(self, payload: Any) -> str:
        try:
            encoded = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            encoded = str(payload)

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _dependency_items(
        self,
        dependency_chain: list[str] | Mapping[str, Any] | None,
    ) -> list[str]:
        if dependency_chain is None:
            return []

        if isinstance(dependency_chain, Mapping):
            candidates = (
                dependency_chain.get("resolved_dependency_chain")
                or dependency_chain.get("chain")
                or dependency_chain.get("dependencies")
                or dependency_chain.get("explanation_path")
                or []
            )
        else:
            candidates = dependency_chain

        if not isinstance(candidates, list):
            return []

        return [
            str(item)
            for item in candidates
            if item is not None
        ]

    def _cache_key(
        self,
        concept: str,
        dependency_chain: list[str] | Mapping[str, Any] | None,
    ) -> str:
        return self._stable_hash({
            "concept": str(concept),
            "dependency_chain": self._dependency_items(dependency_chain),
        })

    def _discover_process_family(
        self,
        concept: str,
        dependency_items: list[str],
    ) -> dict[str, Any]:
        text = " ".join([str(concept), *dependency_items]).lower()

        scores = {}

        for family, keywords in self.CONTEXT_FAMILIES.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[family] = score

        best_family = max(scores, key=scores.get) if scores else "unknown"
        best_score = scores.get(best_family, 0)

        if best_score <= 0:
            best_family = "unknown"

        return {
            "process_family": best_family,
            "family_score": best_score,
            "family_scores": scores,
        }

    def _discover_causal_context(
        self,
        dependency_items: list[str],
    ) -> dict[str, Any]:
        depth = len(dependency_items)

        if depth == 0:
            causal_context = "isolated_process"
            causal_score = 0.2
        elif depth <= 2:
            causal_context = "shallow_dependency_process"
            causal_score = 0.45
        elif depth <= 5:
            causal_context = "moderate_causal_process"
            causal_score = 0.68
        else:
            causal_context = "deep_causal_process"
            causal_score = 0.84

        return {
            "causal_context": causal_context,
            "dependency_depth": depth,
            "causal_score": causal_score,
        }

    def _discover_goal_context(
        self,
        family: str,
    ) -> str:
        mapping = {
            "learning": "knowledge_acquisition",
            "validation": "truth_validation",
            "adaptation": "runtime_improvement",
            "execution": "task_execution",
            "planning": "future_state_control",
            "governance": "safety_and_identity_control",
            "unknown": "undetermined_goal_context",
        }

        return mapping.get(family, "undetermined_goal_context")

    def _adaptive_score(
        self,
        family_score: int,
        causal_score: float,
        extracted: Mapping[str, Any],
    ) -> float:
        discovery_score = 1.0 if extracted.get("process_context_discovered") else 0.0

        normalized_family_score = min(family_score / 3.0, 1.0)

        return round(
            normalized_family_score * 0.35
            + causal_score * 0.35
            + discovery_score * 0.30,
            4,
        )

    def cache_report(self) -> dict[str, Any]:
        total = self.cache_hits + self.cache_misses

        return {
            "system": "process_context_discovery_cache",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hits / total, 4) if total else 0.0,
            "cache_size": len(self._cache),
        }

    def discover(
        self,
        concept: str,
        dependency_chain: list[str] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        dependency_items = self._dependency_items(dependency_chain)
        cache_key = self._cache_key(concept, dependency_chain)

        if cache_key in self._cache:
            self.cache_hits += 1
            report = dict(self._cache[cache_key])
            report["cache_hit"] = True
            report["cache_report"] = self.cache_report()
            return report

        self.cache_misses += 1

        extracted = self.extractor.extract(concept, dependency_chain)

        if not isinstance(extracted, dict):
            extracted = {}

        family = self._discover_process_family(concept, dependency_items)
        causal = self._discover_causal_context(dependency_items)

        goal_context = self._discover_goal_context(
            family.get("process_family", "unknown"),
        )

        adaptive_score = self._adaptive_score(
            family_score=family.get("family_score", 0),
            causal_score=causal.get("causal_score", 0.0),
            extracted=extracted,
        )

        process_context_generated = bool(
            extracted.get("process_context_discovered")
            or family.get("process_family") != "unknown"
            or causal.get("dependency_depth", 0) > 0
        )

        report = {
            **extracted,
            "system": self.system_name,
            "process_context_generated": process_context_generated,
            "process_family": family.get("process_family"),
            "family_score": family.get("family_score"),
            "family_scores": family.get("family_scores"),
            "causal_context": causal.get("causal_context"),
            "dependency_depth": causal.get("dependency_depth"),
            "causal_score": causal.get("causal_score"),
            "goal_context": goal_context,
            "adaptive_context_score": adaptive_score,
            "cache_hit": False,
            "cache_report": self.cache_report(),
        }

        self._cache[cache_key] = dict(report)

        if len(self._cache) > 2048:
            self._cache = dict(list(self._cache.items())[-1024:])

        return report


__all__ = ["ProcessContextDiscovery"]