"""Top-level orchestration for experience-based adaptive reuse."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from runtime.instrumentation import runtime_lifecycle
from runtime.adaptive_reuse.episode_memory import EpisodeMemory
from runtime.adaptive_reuse.experience_index import ExperienceIndex
from runtime.adaptive_reuse.memory_consolidation import AdaptiveMemoryConsolidation
from runtime.adaptive_reuse.program_reuse_engine import ProgramReuseEngine
from runtime.adaptive_reuse.reuse_statistics import ReuseStatistics
from runtime.adaptive_reuse.strategy_retriever import StrategyRetriever


class AdaptiveReuseLayer:
    def __init__(
        self,
        experience_index: ExperienceIndex | None = None,
        strategy_retriever: StrategyRetriever | None = None,
        program_reuse_engine: ProgramReuseEngine | None = None,
        episode_memory: EpisodeMemory | None = None,
        consolidation: AdaptiveMemoryConsolidation | None = None,
    ) -> None:
        self.experience_index = experience_index or ExperienceIndex()
        self.strategy_retriever = strategy_retriever or StrategyRetriever(self.experience_index)
        self.program_reuse_engine = program_reuse_engine or ProgramReuseEngine()
        self.episode_memory = episode_memory or EpisodeMemory()
        self.consolidation = consolidation or AdaptiveMemoryConsolidation()
        self.last_report: dict[str, Any] = {}

    def evaluate(
        self,
        runtime_context: Mapping[str, Any] | None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        lifecycle_execution = runtime_lifecycle.create(
            module_name="adaptive_reuse_layer",
            runtime_name="Reuse Runtime",
            caller="main",
            trigger="adaptive_reuse_evaluate",
        )
        runtime_lifecycle.requested(lifecycle_execution)
        runtime_lifecycle.queued(lifecycle_execution)
        runtime_lifecycle.started(lifecycle_execution)
        runtime_lifecycle.running(lifecycle_execution)
        context = dict(runtime_context or {})
        experiences = self.experience_index.load()
        stats = ReuseStatistics(
            experience_count=len(experiences),
            retrieval_attempts=1,
        )
        retrieval = self.strategy_retriever.retrieve(context, top_k=top_k)
        if retrieval.get("retrieval_success"):
            stats.retrieval_successes = 1
        strategies = retrieval.get("reused_strategies", [])
        stats.strategy_hits = len(strategies)
        stats.experience_similarity = retrieval.get("experience_similarity", 0.0)
        stats.adaptation_operations = retrieval.get("adaptation_operations", [])

        program_report = self.program_reuse_engine.retrieve(context, strategies)
        stats.program_hits = int(program_report.get("program_hits", 0) or 0)

        context_hits, contexts = self._reuse_contexts(context, retrieval)
        truth_hits, truths = self._reuse_truths(context, retrieval)
        dependency_hits, dependencies = self._reuse_dependencies(context, retrieval)
        stats.context_hits = context_hits
        stats.truth_hits = truth_hits
        stats.dependency_hits = dependency_hits
        stats.estimated_runtime_saved = (
            stats.strategy_hits * 0.18
            + stats.program_hits * 0.30
            + stats.context_hits * 0.15
            + stats.truth_hits * 0.20
            + stats.dependency_hits * 0.25
        )
        stats.estimated_compute_saved = (
            stats.strategy_hits * 1.0
            + stats.program_hits * 1.5
            + stats.context_hits * 0.75
            + stats.truth_hits * 1.25
            + stats.dependency_hits * 1.0
        )
        if not any(
            (
                stats.strategy_hits,
                stats.program_hits,
                stats.context_hits,
                stats.truth_hits,
                stats.dependency_hits,
            )
        ):
            stats.reuse_failures.append({"reason": "no_similar_experience_or_validated_asset"})

        consolidation_report = self.consolidation.consolidate(experiences)
        stats.knowledge_growth = {
            "experience_count": len(experiences),
            "strategy_memory_count": self._count_files("runtime/memory/storage/strategies"),
            "truth_memory_count": self._truth_count(),
            "consolidation": consolidation_report,
        }
        report = stats.report()
        report.update({
            "retrieved_experiences": retrieval.get("ranked_experiences", []),
            "reused_strategies": strategies,
            "reused_programs": program_report.get("reused_programs", []),
            "composed_program": program_report.get("composed_program", {}),
            "reused_contexts": contexts,
            "reused_truths": truths,
            "reused_dependencies": dependencies,
            "memory_consolidation_report": consolidation_report,
            "reused_assets": {
                "strategy": strategies[0] if strategies else None,
                "program": program_report.get("composed_program", {}),
                "context": contexts[0] if contexts else None,
                "truth": truths[0] if truths else None,
                "dependency_snapshot": dependencies[0] if dependencies else None,
            },
        })
        report["reused_assets"] = {
            key: value
            for key, value in report["reused_assets"].items()
            if value
        }
        reuse_success = bool(
            stats.strategy_hits
            or stats.program_hits
            or stats.context_hits
            or stats.truth_hits
            or stats.dependency_hits
        )
        runtime_lifecycle.completed(
            lifecycle_execution,
            completion_reason=(
                "adaptive_reuse_assets_found"
                if reuse_success
                else "adaptive_reuse_no_assets_found"
            ),
            output_count=len(report.get("reused_assets", {})),
            memory_cost=len(report.get("reused_assets", {})),
        )
        runtime_lifecycle.reported(lifecycle_execution)
        lifecycle_data = lifecycle_execution.as_dict()
        reuse_time = max(
            lifecycle_data["elapsed_seconds"],
            round(max(perf_counter() - started_at, 0.0), 6),
        )
        report.update({
            "execution_id": lifecycle_data["execution_id"],
            "execution_start": lifecycle_data["execution_start"],
            "execution_end": lifecycle_data["execution_end"],
            "start_timestamp": lifecycle_data["start_timestamp"],
            "end_timestamp": lifecycle_data["end_timestamp"],
            "elapsed_seconds": reuse_time,
            "elapsed_time": reuse_time,
            "duration_seconds": reuse_time,
            "wall_clock_time": lifecycle_data["wall_clock_time"],
            "cpu_time": lifecycle_data["cpu_time"],
            "exclusive_time": lifecycle_data["exclusive_time"],
            "inclusive_time": lifecycle_data["inclusive_time"],
            "cpu_cost": lifecycle_data["cpu_cost"],
            "memory_cost": lifecycle_data["memory_cost"],
            "input_count": len(context),
            "output_count": lifecycle_data["output_count"],
            "success": True,
            "failure": None,
            "reuse_time": reuse_time,
            "reuse_time_seconds": reuse_time,
            "runtime_lifecycle": lifecycle_data,
        })
        self.last_report = report
        return report

    def store_success(self, runtime_context: Mapping[str, Any] | None) -> dict[str, Any]:
        return self.episode_memory.store_success(runtime_context)

    def _reuse_contexts(
        self,
        context: Mapping[str, Any],
        retrieval: Mapping[str, Any],
    ) -> tuple[int, list[dict[str, Any]]]:
        contexts = []
        for item in retrieval.get("ranked_experiences", []):
            payload = item.get("payload", {}) if isinstance(item, Mapping) else {}
            if isinstance(payload, Mapping) and payload.get("context"):
                contexts.append(dict(payload["context"]))
        if not contexts:
            path = Path("runtime/memory/context_memory.json")
            payload = self._read_json(path)
            stored = payload.get("contexts", {}) if isinstance(payload, Mapping) else {}
            iterable = stored.values() if isinstance(stored, Mapping) else stored if isinstance(stored, list) else []
            query_text = str(context).lower()
            for item in iterable:
                if isinstance(item, Mapping) and _overlap(query_text, str(item).lower()) > 0:
                    contexts.append(dict(item))
                    break
        return len(contexts), contexts[:5]

    def _reuse_truths(
        self,
        context: Mapping[str, Any],
        retrieval: Mapping[str, Any],
    ) -> tuple[int, list[dict[str, Any]]]:
        truths = []
        for item in context.get("truth_commitments", []) or context.get("reusable_truth_commitments", []) or []:
            if isinstance(item, Mapping):
                truths.append(dict(item))
        if not truths:
            payload = self._read_json(Path("runtime/memory/storage/truth_registry.json"))
            stored = payload.get("truths", []) if isinstance(payload, Mapping) else []
            query_text = str(context).lower()
            for truth in stored:
                if not isinstance(truth, Mapping):
                    continue
                status = str(truth.get("status") or truth.get("truth_state") or "").upper()
                confidence = _float(
                    truth.get("calibrated_confidence"),
                    truth.get("truth_confidence"),
                    truth.get("evidence_strength"),
                )
                if confidence >= 0.86 and (
                    "ACTIVE" in status
                    or "LOCKED" in status
                    or _overlap(query_text, str(truth).lower()) > 0
                ):
                    truths.append(dict(truth))
                    if len(truths) >= 5:
                        break
        return len(truths), truths[:5]

    def _reuse_dependencies(
        self,
        context: Mapping[str, Any],
        retrieval: Mapping[str, Any],
    ) -> tuple[int, list[dict[str, Any]]]:
        payload = self._read_json(Path("runtime/memory/storage/process_dependency_memory.json"))
        chains = payload.get("process_chains", {}) if isinstance(payload, Mapping) else {}
        query_text = str(context).lower()
        dependencies = []
        if isinstance(chains, Mapping):
            for concept, edges in chains.items():
                if str(concept).lower() not in query_text and _overlap(query_text, str(edges).lower()) <= 0:
                    continue
                dependencies.append({
                    "concept": concept,
                    "dependency_graph": edges,
                    "reuse_state": "DEPENDENCY_GRAPH_REUSED",
                })
                if len(dependencies) >= 5:
                    break
        if not dependencies:
            for item in retrieval.get("ranked_experiences", []):
                signature = item.get("dependency_signature")
                if signature:
                    dependencies.append({
                        "source_experience_id": item.get("experience_id"),
                        "dependency_signature": signature,
                        "reuse_state": "DEPENDENCY_SIGNATURE_REUSED",
                    })
                    break
        return len(dependencies), dependencies

    def _read_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _count_files(self, root: str) -> int:
        path = Path(root)
        return len(list(path.glob("*.json"))) if path.exists() else 0

    def _truth_count(self) -> int:
        payload = self._read_json(Path("runtime/memory/storage/truth_registry.json"))
        truths = payload.get("truths", []) if isinstance(payload, Mapping) else []
        return len(truths) if isinstance(truths, list) else 0


def _float(*values: Any) -> float:
    for value in values:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            continue
    return 0.0


def _overlap(left: str, right: str) -> float:
    left_tokens = {token for token in left.replace("_", " ").split() if len(token) > 2}
    right_tokens = {token for token in right.replace("_", " ").split() if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


adaptive_reuse_layer = AdaptiveReuseLayer()
