"""Generate and prepare multiple cognitive hypotheses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from runtime.hypothesis.hypothesis_memory import HypothesisMemory
from runtime.hypothesis.hypothesis_ranker import HypothesisRanker
from runtime.hypothesis.hypothesis_registry import HypothesisRegistry
from runtime.hypothesis.hypothesis_validator import HypothesisValidator


HYPOTHESIS_TEMPLATES = {
    "replication": [
        ("duplicate_object", "execution", 0.92, True),
        ("mirror_duplicate_object", "transformation", 0.84, True),
        ("symbolic_duplicate_object", "semantic", 0.80, False),
        ("topology_preserving_duplicate", "transformation", 0.86, True),
        ("localized_duplicate", "execution", 0.88, True),
    ],
    "duplication": [
        ("duplicate_object", "execution", 0.92, True),
        ("mirror_duplicate_object", "transformation", 0.84, True),
        ("symbolic_duplicate_object", "semantic", 0.80, False),
        ("topology_preserving_duplicate", "transformation", 0.86, True),
        ("localized_duplicate", "execution", 0.88, True),
    ],
    "object_creation": [
        ("duplicate_object", "execution", 0.88, True),
        ("localized_object_creation", "transformation", 0.82, True),
        ("symbolic_object_creation", "semantic", 0.78, False),
    ],
    "color_preservation": [
        ("preserve_color", "execution", 0.92, True),
        ("preserve_palette", "semantic", 0.88, False),
        ("preserve_object_colors", "transformation", 0.90, True),
        ("preserve_contextual_colors", "semantic", 0.84, False),
    ],
    "symbolic_remapping": [
        ("remap_symbols", "execution", 0.90, True),
        ("contextual_symbol_remap", "semantic", 0.82, False),
        ("object_bound_symbol_remap", "transformation", 0.86, True),
    ],
    "topological_growth": [
        ("expand_topology", "execution", 0.88, True),
        ("localized_topological_growth", "transformation", 0.84, True),
        ("topology_preserving_growth", "semantic", 0.80, False),
    ],
    "growth": [
        ("grow_topology", "execution", 0.86, True),
        ("expand_pattern", "transformation", 0.84, True),
        ("contextual_growth", "semantic", 0.78, False),
    ],
    "directional_motion": [
        ("translate_object", "execution", 0.90, True),
        ("localized_translate", "transformation", 0.86, True),
        ("contextual_motion", "semantic", 0.78, False),
    ],
    "symmetry_preservation": [
        ("preserve_symmetry", "execution", 0.88, True),
        ("mirror_preserving_symmetry", "transformation", 0.84, True),
        ("relational_symmetry_preservation", "semantic", 0.82, False),
    ],
}

DEFAULT_TEMPLATES = [
    ("semantic_interpretation", "semantic", 0.62, False),
    ("transformation_interpretation", "transformation", 0.58, True),
    ("execution_probe", "execution", 0.54, True),
]


class MultiHypothesisEngine:
    """Generate, validate, rank, and remember multiple hypotheses."""

    system_name = "multi_hypothesis_engine"

    def __init__(
        self,
        registry: HypothesisRegistry | None = None,
        validator: HypothesisValidator | None = None,
        ranker: HypothesisRanker | None = None,
        memory: HypothesisMemory | None = None,
    ):
        self.registry = registry or HypothesisRegistry()
        self.validator = validator or HypothesisValidator()
        self.ranker = ranker or HypothesisRanker()
        self.memory = memory or HypothesisMemory()

    def generate(
        self,
        concepts: Iterable[Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        semantic_intent_report: Mapping[str, Any] | None = None,
        reusable_hypotheses: Iterable[Mapping[str, Any]] | None = None,
        max_hypotheses: int = 24,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = self._collect_concepts(concepts, runtime_context, semantic_intent_report)
        generated = []
        for concept in concepts:
            templates = HYPOTHESIS_TEMPLATES.get(concept, DEFAULT_TEMPLATES)
            for name, hypothesis_type, confidence, execution_ready in templates:
                generated.append(self._hypothesis(
                    concept,
                    name,
                    hypothesis_type,
                    confidence,
                    execution_ready,
                    source="multi_hypothesis_engine",
                    runtime_context=runtime_context,
                ))
                if len(generated) >= max_hypotheses:
                    break
            if len(generated) >= max_hypotheses:
                break

        reused = list(reusable_hypotheses or [])
        if not reused:
            reused = self.memory.retrieve(concepts, limit=max(0, max_hypotheses - len(generated)))
        for reused_hypothesis in reused:
            if len(generated) >= max_hypotheses:
                break
            generated.append(self._reusable_hypothesis(reused_hypothesis, runtime_context))

        generated = self._dedupe(generated)[:max_hypotheses]
        for hypothesis in generated:
            self.registry.register(hypothesis)

        validation = self.validator.validate_many(generated, runtime_context)
        accepted_ids = set(validation.get("accepted_hypothesis_ids", []))
        rejected_ids = set(validation.get("rejected_hypothesis_ids", []))
        for hypothesis_id in accepted_ids:
            self.registry.accept(hypothesis_id)
        for hypothesis_id in rejected_ids:
            self.registry.reject(hypothesis_id, "validation_failed")
        ranking = self.ranker.rank(generated, validation)
        for hypothesis in generated:
            self.memory.remember(
                hypothesis,
                success=hypothesis.get("hypothesis_id") in accepted_ids,
                reusable=hypothesis.get("hypothesis_id") in accepted_ids and hypothesis.get("execution_ready"),
            )

        semantic_generated = any(item.get("hypothesis_type") == "semantic" for item in generated)
        transformation_generated = any(item.get("hypothesis_type") == "transformation" for item in generated)
        execution_ready = [
            item for item in ranking.get("best_candidates", [])
            if item.get("execution_ready")
        ]
        report = {
            "system": self.system_name,
            "generated_hypotheses": generated,
            "hypothesis_count": len(generated),
            "generation_success": bool(generated),
            "semantic_hypotheses_generated": semantic_generated,
            "transformation_hypotheses_generated": transformation_generated,
            "execution_hypotheses_generated": any(item.get("hypothesis_type") == "execution" for item in generated),
            "reusable_hypotheses_generated": any(item.get("hypothesis_type") == "reusable" for item in generated),
            "validation_report": validation,
            "ranking_report": ranking,
            "registry_report": self.registry.report(),
            "memory_report": self.memory.report(),
            "accepted_hypotheses": [
                item for item in generated if item.get("hypothesis_id") in accepted_ids
            ],
            "rejected_hypotheses": [
                item for item in generated if item.get("hypothesis_id") in rejected_ids
            ],
            "reusable_hypotheses": self.registry.reusable(),
            "best_ranked": ranking.get("best_candidates", [])[:3],
            "execution_ready": execution_ready,
            "hypothesis_ranking_operational": bool(ranking.get("hypothesis_ranking_operational")),
            "hypothesis_validation_operational": bool(validation.get("validation_operational")),
            "hypothesis_memory_operational": bool(self.memory.report().get("hypothesis_memory_operational")),
            "max_hypotheses": max_hypotheses,
            "timestamp": str(datetime.utcnow()),
        }
        report["MULTI_HYPOTHESIS_REPORT"] = self._compact_report(report)
        return report

    def _hypothesis(
        self,
        concept: str,
        name: str,
        hypothesis_type: str,
        confidence: float,
        execution_ready: bool,
        *,
        source: str,
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        context_support = _score(runtime_context.get("context_support", runtime_context.get("semantic_context_confidence", confidence)))
        truth_support = _score(runtime_context.get("truth_support", runtime_context.get("truth_alignment", confidence)))
        dependency_support = _score(runtime_context.get("dependency_support", runtime_context.get("dependency_chain_coverage", confidence)))
        identity_confidence = _score(runtime_context.get("identity_confidence", confidence))
        hypothesis_id = f"hypothesis:{concept}:{name}"
        return {
            "hypothesis_id": hypothesis_id,
            "hypothesis_name": name,
            "hypothesis_type": hypothesis_type,
            "source_concept": concept,
            "matched_concepts": [concept],
            "confidence": round(float(confidence), 4),
            "semantic_support": round(float(confidence), 4),
            "context_support": context_support,
            "truth_support": truth_support,
            "dependency_support": dependency_support,
            "identity_confidence": identity_confidence,
            "execution_confidence": round(float(confidence if execution_ready else 0.0), 4),
            "execution_ready": bool(execution_ready),
            "reusable": bool(execution_ready and confidence >= 0.84),
            "generated_from": source,
        }

    def _reusable_hypothesis(
        self,
        hypothesis: Mapping[str, Any],
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        record = dict(hypothesis)
        concept = _normalize(record.get("source_concept") or "reusable")
        name = _normalize(record.get("hypothesis_name") or "reused_hypothesis")
        confidence = _score(record.get("evolved_confidence", record.get("confidence", 0.72)))
        reused = self._hypothesis(
            concept,
            name,
            "reusable",
            confidence,
            bool(record.get("execution_ready", True)),
            source="hypothesis_memory",
            runtime_context=runtime_context,
        )
        reused["source_hypothesis_id"] = record.get("hypothesis_id")
        return reused

    def _collect_concepts(
        self,
        concepts: Iterable[Any] | None,
        runtime_context: Mapping[str, Any],
        semantic_intent_report: Mapping[str, Any] | None,
    ) -> list[str]:
        found = []

        def add(value: Any) -> None:
            token = _normalize(value)
            if token and token not in found:
                found.append(token)

        def visit(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                add(value)
                return
            if isinstance(value, Mapping):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "generated_concepts",
                        "semantic_concepts",
                        "matched_concepts",
                        "source_concept",
                    }:
                        visit(item)
                    elif isinstance(item, (Mapping, list, tuple, set)):
                        visit(item)
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        visit(concepts)
        for key in ("detected_concepts", "generated_concepts", "semantic_concepts", "concepts"):
            visit(runtime_context.get(key))
        report = semantic_intent_report if isinstance(semantic_intent_report, Mapping) else {}
        visit(report.get("detected_concepts"))
        visit(report.get("execution_intents"))
        return found

    def _dedupe(self, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_id = {}
        for hypothesis in hypotheses:
            by_id.setdefault(hypothesis["hypothesis_id"], hypothesis)
        return list(by_id.values())

    def _compact_report(self, report: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "Generated Hypotheses": report.get("hypothesis_count", 0),
            "Accepted": len(report.get("accepted_hypotheses", []) or []),
            "Rejected": len(report.get("rejected_hypotheses", []) or []),
            "Reusable": len(report.get("reusable_hypotheses", []) or []),
            "Best Ranked": [
                item.get("hypothesis_name")
                for item in report.get("best_ranked", []) or []
                if isinstance(item, Mapping)
            ],
            "Execution Ready": [
                item.get("hypothesis_name")
                for item in report.get("execution_ready", []) or []
                if isinstance(item, Mapping)
            ],
        }


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


multi_hypothesis_engine = MultiHypothesisEngine()

__all__ = ["MultiHypothesisEngine", "multi_hypothesis_engine"]
