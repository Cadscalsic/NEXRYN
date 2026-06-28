"""Build semantic contexts from dependency and process evidence."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping


class SemanticContextBuilder:
    """Convert dependency/process evidence into registerable contexts."""

    system_name = "semantic_context_builder"

    def build(
        self,
        concept: str,
        dependency_chain: Mapping[str, Any] | Iterable[Any] | None = None,
        process_context: Mapping[str, Any] | None = None,
        observations: Iterable[Any] | None = None,
        concept_history: Iterable[Any] | None = None,
        world_signals: Mapping[str, Any] | None = None,
        identity_constraints: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        dependency_chain = dependency_chain if dependency_chain is not None else {}
        process_context = process_context if isinstance(process_context, Mapping) else {}
        world_signals = world_signals if isinstance(world_signals, Mapping) else {}
        identity_constraints = (
            identity_constraints
            if isinstance(identity_constraints, Mapping)
            else {}
        )
        observations = list(observations or [])
        concept_history = list(concept_history or [])

        dependency_score = _dependency_score(dependency_chain)
        causal_score = _causal_score(dependency_chain, process_context)
        identity_score = _score(
            identity_constraints,
            "identity_continuity",
            "identity_score",
            "identity_confidence",
            default=0.72,
        )
        stability_score = _stability_score(
            dependency_chain,
            process_context,
            observations,
            concept_history,
            world_signals,
        )
        support_score = round(
            min(1.0, dependency_score * 0.45 + causal_score * 0.25
                + stability_score * 0.20 + identity_score * 0.10),
            4,
        )
        confidence = round(
            min(1.0, support_score * 0.65 + dependency_score * 0.25
                + identity_score * 0.10),
            4,
        )

        return {
            "system": self.system_name,
            "context_id": _context_id(concept, dependency_chain, process_context),
            "context_type": "SEMANTIC_CONTEXT",
            "concept": concept,
            "support_score": support_score,
            "dependency_score": dependency_score,
            "causal_score": causal_score,
            "identity_score": identity_score,
            "stability_score": stability_score,
            "confidence": confidence,
            "dependency_chain": _compact_dependency_chain(dependency_chain),
            "process_context": dict(process_context),
            "world_context": dict(world_signals),
            "identity_constraints": dict(identity_constraints),
            "report_state": "final",
        }

    def build_batch(
        self,
        dependency_chains: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        dependency_chains = (
            dependency_chains
            if isinstance(dependency_chains, Mapping)
            else {}
        )
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        process_models = runtime_context.get("process_semantic_models", {})
        if not isinstance(process_models, Mapping):
            process_models = {}

        contexts = []
        rejected = []
        for concept, dependency_chain in dependency_chains.items():
            if not _has_dependency_support(dependency_chain):
                rejected.append({
                    "concept": concept,
                    "reason": "insufficient_dependency_support",
                })
                continue
            contexts.append(
                self.build(
                    concept,
                    dependency_chain=dependency_chain,
                    process_context=_process_context_for(concept, process_models),
                    observations=runtime_context.get("observation_history", []),
                    concept_history=runtime_context.get("concept_history", []),
                    world_signals=runtime_context.get("world_model_report", {}),
                    identity_constraints=runtime_context.get(
                        "identity_runtime_report",
                        runtime_context.get("transformational_identity", {}),
                    ),
                )
            )

        reason = None if contexts else "insufficient_dependency_support"
        return {
            "system": self.system_name,
            "report_state": "final",
            "contexts_discovered": len(contexts),
            "semantic_contexts": contexts,
            "contexts_rejected": len(rejected),
            "rejection_reasons": [
                item["reason"]
                for item in rejected
            ],
            "result_count": len(contexts),
            "reason": reason,
        }


def _process_context_for(concept: str, process_models: Mapping[str, Any]) -> dict[str, Any]:
    value = process_models.get(concept)
    if isinstance(value, Mapping):
        return dict(value)
    for item in process_models.values():
        if isinstance(item, Mapping) and item.get("concept") == concept:
            return dict(item)
    return {}


def _has_dependency_support(dependency_chain: Any) -> bool:
    if isinstance(dependency_chain, Mapping):
        return bool(
            dependency_chain.get("chain")
            or dependency_chain.get("resolved_dependency_chain")
            or dependency_chain.get("dependency_chain_depth", 0) > 0
            or dependency_chain.get("dependency_chain_coverage", 0.0) > 0.0
        )
    return bool(list(dependency_chain or []))


def _dependency_score(dependency_chain: Any) -> float:
    if isinstance(dependency_chain, Mapping):
        return max(
            _score(
                dependency_chain,
                "dependency_confidence",
                "dependency_coherence",
                "dependency_coherence_average",
                default=0.0,
            ),
            _score(
                dependency_chain,
                "dependency_chain_coverage",
                "coverage",
                default=0.0,
            ),
            min(1.0, float(dependency_chain.get("dependency_chain_depth", 0)) / 4),
        )
    return min(1.0, len(list(dependency_chain or [])) / 4)


def _causal_score(dependency_chain: Any, process_context: Mapping[str, Any]) -> float:
    causal_terms = ("causes", "enables", "creates", "transitions_to", "supports")
    text = f"{dependency_chain} {process_context}".lower()
    matches = sum(1 for term in causal_terms if term in text)
    process_ready = bool(process_context)
    return round(min(1.0, matches / 3 + (0.2 if process_ready else 0.0)), 4)


def _stability_score(
    dependency_chain: Any,
    process_context: Mapping[str, Any],
    observations: list[Any],
    concept_history: list[Any],
    world_signals: Mapping[str, Any],
) -> float:
    base = 0.35
    if _has_dependency_support(dependency_chain):
        base += 0.25
    if process_context:
        base += 0.15
    if observations:
        base += 0.10
    if concept_history:
        base += 0.10
    if world_signals:
        base += 0.05
    return round(min(1.0, base), 4)


def _compact_dependency_chain(dependency_chain: Any) -> Any:
    if isinstance(dependency_chain, Mapping):
        return (
            dependency_chain.get("resolved_dependency_chain")
            or dependency_chain.get("chain")
            or dict(dependency_chain)
        )
    return list(dependency_chain or [])


def _score(mapping: Mapping[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            try:
                return round(max(0.0, min(1.0, float(value))), 4)
            except (TypeError, ValueError):
                return 0.0
    return round(max(0.0, min(1.0, float(default))), 4)


def _normalize(value: Any) -> str:
    return str(value or "runtime_concept").strip().lower().replace(" ", "_")


def _context_id(concept: str, dependency_chain: Any, process_context: Any) -> str:
    payload = f"{concept}:{dependency_chain}:{process_context}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"semantic_context:{concept}:{digest}"


semantic_context_builder = SemanticContextBuilder()


__all__ = ["SemanticContextBuilder", "semantic_context_builder"]
