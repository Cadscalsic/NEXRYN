"""Measure cross-context reliability of process dependencies."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


CONTEXT_KEYS = (
    "directions",
    "object_types",
    "colors",
    "topologies",
    "sizes",
    "spatial_patterns",
)

RELATION_WEIGHTS = {
    "causes": 1.0,
    "creates": 0.99,
    "requires": 0.98,
    "preserves": 0.96,
    "modifies": 0.94,
    "depends_on": 0.93,
    "derived_from": 0.91,
    "enables": 0.90,
    "supports": 0.84,
    "context_requires": 0.84,
    "context_strengthens": 0.80,
    "context_weakens": 0.58,
    "inhibits": 0.35,
}

CONTRADICTION_KEYS = (
    "contradiction",
    "contradiction_detected",
    "conflict",
    "conflict_detected",
    "inconsistent",
    "hidden_contradiction",
)


class DependencyCoherenceEngine:
    """Estimate whether discovered dependencies remain stable across contexts."""

    system_name = "dependency_coherence_engine"

    def evaluate(
        self,
        concept: str,
        dependency_chains: Any | None = None,
        dependency_chain: Any | None = None,
        semantic_contexts: Any | None = None,
        contextual_truth_reports: Any | None = None,
        transformation_traces: Any | None = None,
        task_metadata: Any | None = None,
        process_signatures: Any | None = None,
        process_signature: Any | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        chains = dependency_chains if dependency_chains is not None else dependency_chain
        signatures = (
            process_signatures
            if process_signatures is not None
            else process_signature
        )

        dependencies = self._dependencies_from(chains, runtime_context)
        signature_report = self._first_mapping(signatures)
        dependencies.update(self._signature_dependencies(signature_report))
        if concept:
            dependencies.add(concept)

        context_items = self._as_items(semantic_contexts)
        context_items.extend(self._as_items(task_metadata))
        context_items.extend(self._as_items(transformation_traces))
        context_items.extend(self._as_items(contextual_truth_reports))
        context_items.extend(self._as_items(runtime_context.get("context_surface_evidence")))
        context_items.extend(self._as_items(runtime_context.get("task_metadata")))
        context_items.extend(self._as_items(runtime_context.get("semantic_context")))

        diversity = self._context_diversity(context_items, runtime_context)
        truth_score = self._truth_score(contextual_truth_reports, runtime_context)
        trace_reliability = self._trace_reliability(transformation_traces, runtime_context)
        signature_confidence = clamp(
            signature_report.get(
                "signature_confidence",
                signature_report.get("signature_strength", 0.0),
            )
            if signature_report
            else runtime_context.get("signature_confidence", 0.0)
        )
        chain_confidence = self._chain_confidence(chains, runtime_context)
        observations = self._dependency_observations(
            dependencies,
            chains,
            context_items,
            signature_report,
            runtime_context,
        )
        hidden_contradictions = self._hidden_contradictions(
            dependencies,
            chains,
            context_items,
            runtime_context,
        )
        stable_dependencies = []
        fragile_dependencies = []
        scores = []
        for dependency in sorted(dependencies):
            support = observations.get(dependency, [])
            support_score = (
                sum(support) / len(support)
                if support
                else chain_confidence * 0.75
            )
            contradiction_penalty = self._contradiction_penalty(
                dependency,
                hidden_contradictions,
            )
            stability = clamp(
                support_score * 0.52
                + diversity["score"] * 0.24
                + signature_confidence * 0.14
                + truth_score * 0.10
                - contradiction_penalty
            )
            scores.append(stability)
            if stability >= 0.78 and contradiction_penalty == 0.0:
                stable_dependencies.append(dependency)
            elif stability < 0.78 or contradiction_penalty > 0.0:
                fragile_dependencies.append(dependency)

        dependency_stability = (
            sum(scores) / len(scores)
            if scores
            else 0.0
        )
        contextual_variance = clamp(
            (1.0 - dependency_stability) * 0.68
            + (1.0 - diversity["score"]) * 0.32
        )
        causal_reliability = clamp(
            chain_confidence * 0.38
            + truth_score * 0.22
            + trace_reliability * 0.20
            + signature_confidence * 0.20
        )
        contradiction_penalty = min(len(hidden_contradictions) * 0.10, 0.35)
        dependency_coherence = clamp(
            dependency_stability * 0.48
            + causal_reliability * 0.30
            + diversity["score"] * 0.17
            + (1.0 - contextual_variance) * 0.05
            - contradiction_penalty
        )
        return {
            "system": self.system_name,
            "concept": concept,
            "dependency_coherence": round(dependency_coherence, 4),
            "stable_dependencies": stable_dependencies,
            "fragile_dependencies": fragile_dependencies,
            "contextual_variance": round(contextual_variance, 4),
            "causal_reliability": round(causal_reliability, 4),
            "hidden_contradictions": hidden_contradictions,
            "dependency_stability": round(dependency_stability, 4),
            "context_diversity": diversity["counts"],
            "context_diversity_score": round(diversity["score"], 4),
            "dependency_count": len(dependencies),
            "dependency_coherence_ready": (
                dependency_coherence >= 0.90
                and not hidden_contradictions
                and bool(stable_dependencies)
            ),
            "evidence_additive": True,
        }

    def _dependencies_from(self, chains, runtime_context, include_runtime=True):
        dependencies = set()
        for item in self._as_items(chains):
            if isinstance(item, Mapping):
                chain = item.get("resolved_dependency_chain")
                if chain is not None:
                    dependencies.update(
                        self._dependencies_from(
                            chain,
                            runtime_context,
                            include_runtime=False,
                        )
                    )
                for relation in item.get("typed_dependency_relations", []) or []:
                    if isinstance(relation, Mapping):
                        dependencies.add(_normalize(relation.get("source")))
                        dependencies.add(_normalize(relation.get("target")))
                for key in ("source", "target", "dependency", "concept"):
                    if item.get(key):
                        dependencies.add(_normalize(item.get(key)))
            elif isinstance(item, (list, tuple, set)):
                dependencies.update(
                    _normalize(value)
                    for value in item
                    if not isinstance(value, Mapping)
                )
            else:
                dependencies.add(_normalize(item))
        if include_runtime:
            process_memory = runtime_context.get("process_dependency_memory", {})
            if isinstance(process_memory, Mapping):
                dependencies.update(
                    self._dependencies_from(
                        process_memory,
                        {},
                        include_runtime=False,
                    )
                )
        return {dependency for dependency in dependencies if dependency}

    def _signature_dependencies(self, signature_report):
        dependencies = set()
        if not isinstance(signature_report, Mapping):
            return dependencies
        for key in (
            "signature_invariants",
            "signature_constraints",
            "signature_capabilities",
            "matched_features",
            "required_features",
            "dependency_nodes",
            "signature_tokens",
        ):
            for value in signature_report.get(key, []) or []:
                dependencies.add(_normalize(value))
        return {dependency for dependency in dependencies if dependency}

    def _dependency_observations(
        self,
        dependencies,
        chains,
        context_items,
        signature_report,
        runtime_context,
    ):
        observations = defaultdict(list)
        for item in self._as_items(chains):
            if isinstance(item, Mapping):
                relation_score = RELATION_WEIGHTS.get(
                    _normalize(item.get("relation", item.get("relation_type"))),
                    0.86,
                )
                score = clamp(
                    item.get("confidence", item.get("support_score", 0.86))
                ) * relation_score
                for key in ("source", "target", "dependency", "concept"):
                    value = _normalize(item.get(key))
                    if value in dependencies:
                        observations[value].append(score)
        for item in context_items:
            text = _text_tokens(item)
            confidence = self._item_confidence(item)
            for dependency in dependencies:
                if dependency in text:
                    observations[dependency].append(confidence)
        if isinstance(signature_report, Mapping):
            sig_confidence = clamp(
                signature_report.get(
                    "signature_confidence",
                    signature_report.get("signature_strength", 0.0),
                )
            )
            for dependency in self._signature_dependencies(signature_report):
                observations[dependency].append(sig_confidence)
        chain_confidence = self._chain_confidence(chains, runtime_context)
        for dependency in dependencies:
            if not observations[dependency]:
                observations[dependency].append(chain_confidence)
        return observations

    def _hidden_contradictions(
        self,
        dependencies,
        chains,
        context_items,
        runtime_context,
    ):
        contradictions = []
        evidence = []
        evidence.extend(self._as_items(chains))
        evidence.extend(context_items)
        evidence.extend(self._as_items(runtime_context.get("contradictions")))
        evidence.extend(self._as_items(runtime_context.get("contradiction_report")))
        for item in evidence:
            item_contradicts = self._item_contradicts(item)
            text = _text_tokens(item)
            if not item_contradicts and not any(
                token.startswith(("not_", "anti_", "without_"))
                for token in text
            ):
                continue
            matched = [
                dependency
                for dependency in dependencies
                if dependency in text
                or f"not_{dependency}" in text
                or f"anti_{dependency}" in text
                or f"without_{dependency}" in text
            ]
            if not matched and item_contradicts:
                matched = [_normalize(_read(item, "dependency", "concept", "target"))]
            for dependency in matched:
                if dependency:
                    contradictions.append({
                        "dependency": dependency,
                        "evidence": _compact_evidence(item),
                    })
        unique = []
        seen = set()
        for item in contradictions:
            key = (item["dependency"], str(item["evidence"]))
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    def _context_diversity(self, context_items, runtime_context):
        categories = {key: set() for key in CONTEXT_KEYS}
        for item in context_items:
            self._collect_context_values(item, categories)
        surface = runtime_context.get("context_surface_report", {})
        if isinstance(surface, Mapping):
            evidence = surface.get("context_surface_evidence", {})
            if isinstance(evidence, Mapping):
                self._collect_context_values(evidence, categories)
            diversity = surface.get("context_diversity", {})
            if isinstance(diversity, Mapping):
                for key, count in diversity.items():
                    if key in categories:
                        for index in range(int(count or 0)):
                            categories[key].add(f"{key}:{index}")
        counts = {key: len(values) for key, values in categories.items()}
        target = {
            "directions": 3,
            "object_types": 2,
            "colors": 2,
            "topologies": 2,
            "sizes": 2,
            "spatial_patterns": 3,
        }
        ratios = [
            clamp(counts[key] / target[key])
            for key in CONTEXT_KEYS
        ]
        return {
            "counts": counts,
            "score": clamp(sum(ratios) / len(ratios)),
        }

    def _collect_context_values(self, item, categories):
        if isinstance(item, Mapping):
            for key, value in item.items():
                norm_key = _normalize(key)
                if norm_key in categories:
                    for entry in _iter_values(value):
                        categories[norm_key].add(_normalize(entry))
                else:
                    self._collect_context_values(value, categories)
        elif isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            for value in item:
                self._collect_context_values(value, categories)

    def _truth_score(self, contextual_truth_reports, runtime_context):
        values = []
        for item in self._as_items(contextual_truth_reports):
            if isinstance(item, Mapping):
                values.extend(
                    clamp(item.get(key))
                    for key in (
                        "effective_contextual_truth",
                        "contextual_truth_score",
                        "truth_score",
                        "confidence",
                    )
                    if item.get(key) is not None
                )
        for key in ("contextual_truth_authority", "contextual_truth"):
            report = runtime_context.get(key, {})
            if isinstance(report, Mapping):
                values.extend(
                    clamp(report.get(metric))
                    for metric in (
                        "effective_contextual_truth",
                        "contextual_truth_score",
                    )
                    if report.get(metric) is not None
                )
        return sum(values) / len(values) if values else 0.92

    def _trace_reliability(self, transformation_traces, runtime_context):
        traces = self._as_items(transformation_traces)
        traces.extend(self._as_items(runtime_context.get("execution_trace")))
        traces.extend(self._as_items(runtime_context.get("execution_history")))
        if not traces:
            return clamp(runtime_context.get("prediction_accuracy", 0.92))
        successes = 0
        scored = 0
        scores = []
        for trace in traces:
            if isinstance(trace, Mapping):
                if trace.get("success") is not None:
                    successes += int(trace.get("success") is True)
                    scored += 1
                for key in ("accuracy", "prediction_accuracy", "score", "confidence"):
                    if trace.get(key) is not None:
                        scores.append(clamp(trace.get(key)))
        success_rate = successes / scored if scored else 0.92
        score = sum(scores) / len(scores) if scores else success_rate
        return clamp(max(success_rate, score))

    def _chain_confidence(self, chains, runtime_context):
        values = []
        for item in self._as_items(chains):
            if isinstance(item, Mapping):
                values.extend(
                    clamp(item.get(key))
                    for key in (
                        "dependency_confidence",
                        "dependency_chain_coverage",
                        "confidence",
                    )
                    if item.get(key) is not None
                )
        process_memory = runtime_context.get("process_dependency_memory", {})
        if isinstance(process_memory, Mapping):
            values.extend(
                clamp(process_memory.get(key))
                for key in (
                    "dependency_confidence",
                    "dependency_chain_coverage",
                )
                if process_memory.get(key) is not None
            )
        return sum(values) / len(values) if values else 0.90

    def _contradiction_penalty(self, dependency, hidden_contradictions):
        return min(
            0.42,
            0.16
            * sum(
                item.get("dependency") == dependency
                for item in hidden_contradictions
            ),
        )

    def _item_confidence(self, item):
        if isinstance(item, Mapping):
            for key in (
                "confidence",
                "support",
                "support_score",
                "context_strength",
                "contextual_truth_score",
            ):
                if item.get(key) is not None:
                    return clamp(item.get(key))
        return 0.88

    def _item_contradicts(self, item):
        if isinstance(item, Mapping):
            if item.get("success") is False:
                return True
            return any(bool(item.get(key)) for key in CONTRADICTION_KEYS)
        text = _text_tokens(item)
        return bool({"contradiction", "conflict", "inconsistent"} & text)

    def _first_mapping(self, value):
        if isinstance(value, Mapping):
            if isinstance(value.get("process_signature_report"), Mapping):
                return value["process_signature_report"]
            return value
        for item in self._as_items(value):
            if isinstance(item, Mapping):
                return item
        return {}

    def _as_items(self, value):
        if value is None:
            return []
        if isinstance(value, Mapping):
            return [value]
        if isinstance(value, (str, bytes)):
            return [value]
        try:
            return list(value)
        except TypeError:
            return [value]


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _iter_values(value):
    if value is None:
        return []
    if isinstance(value, Mapping):
        return value.values()
    if isinstance(value, (str, bytes)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _text_tokens(item) -> set[str]:
    tokens = set()
    if isinstance(item, Mapping):
        for key, value in item.items():
            tokens.add(_normalize(key))
            tokens.update(_text_tokens(value))
    elif isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
        for value in item:
            tokens.update(_text_tokens(value))
    else:
        value = _normalize(item)
        if value:
            tokens.add(value)
    return tokens


def _read(item, *keys):
    if not isinstance(item, Mapping):
        return ""
    for key in keys:
        if item.get(key):
            return item[key]
    return ""


def _compact_evidence(item):
    if isinstance(item, Mapping):
        return {
            key: item[key]
            for key in (
                "dependency",
                "concept",
                "target",
                "reason",
                "contradiction",
                "conflict",
                "success",
            )
            if key in item
        }
    return str(item)


dependency_coherence_engine = DependencyCoherenceEngine()


__all__ = [
    "DependencyCoherenceEngine",
    "dependency_coherence_engine",
]
