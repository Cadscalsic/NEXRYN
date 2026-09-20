"""Deterministic orchestration for cognitive solver stages."""

from __future__ import annotations

import os
import time
import tracemalloc
from typing import Callable

from .context import CognitiveContext
from .stage import CognitiveStage
from .stages import build_default_stages


class CognitivePipelineOrchestrator:
    def __init__(self, stages: list[CognitiveStage] | None = None) -> None:
        self.stages = stages or build_default_stages()

    def execute(
        self,
        context: CognitiveContext,
        should_skip: Callable[[CognitiveStage, CognitiveContext], bool] | None = None,
        should_stop: Callable[[CognitiveContext], bool] | None = None,
        max_iterations: int = 1,
    ) -> CognitiveContext:
        context.metadata.setdefault("supports_iterative_loops", True)
        context.metadata.setdefault("supports_recursive_refinement", True)
        context.metadata.setdefault("supports_early_termination", True)
        context.metadata.setdefault("supports_future_parallel_execution", True)
        context.metadata.setdefault("supports_future_dynamic_scheduling", True)
        for iteration in range(max(1, max_iterations)):
            context.metadata["pipeline_iteration"] = iteration
            for stage in self.stages:
                if should_skip and should_skip(stage, context):
                    self._record_skipped(context, stage)
                    continue
                if should_stop and should_stop(context):
                    context.metadata["early_termination"] = True
                    return context
                self._run_stage(context, stage)
        return context

    def _run_stage(self, context: CognitiveContext, stage: CognitiveStage) -> None:
        start_wall = time.perf_counter()
        start_cpu = time.process_time()
        start_clock = time.time()
        tracemalloc_started = False
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            tracemalloc_started = True
        start_memory = tracemalloc.get_traced_memory()[0]
        before = context.snapshot()
        status = "completed"
        error = None
        outputs = {}
        try:
            outputs = stage.execute(context)
        except Exception as exc:  # pragma: no cover - defensive pipeline guard
            status = "failed"
            error = str(exc)
        end_memory = tracemalloc.get_traced_memory()[0]
        if tracemalloc_started:
            tracemalloc.stop()
        end_clock = time.time()
        duration = time.perf_counter() - start_wall
        cpu_cost = time.process_time() - start_cpu
        after = context.snapshot()
        event = {
            "stage_id": stage.spec.stage_id,
            "stage_name": stage.spec.stage_name,
            "inputs": list(stage.spec.required_inputs),
            "outputs": list(stage.spec.generated_outputs),
            "execution_start": start_clock,
            "execution_end": end_clock,
            "duration": duration,
            "cpu_cost": cpu_cost,
            "memory_cost": max(0, end_memory - start_memory),
            "confidence": context.confidence_scores.get(stage.spec.stage_id, stage.confidence),
            "generated_concepts": self._growth_keys(before, after, "concepts"),
            "consumed_concepts": list(stage.spec.consumed_outputs),
            "dependencies": list(stage.dependencies),
            "produced_knowledge": outputs,
            "execution_status": status,
            "error": error,
            "process_id": os.getpid(),
        }
        snapshot = {
            "stage_id": stage.spec.stage_id,
            "stage_name": stage.spec.stage_name,
            "context_snapshot": after,
            "context_growth": self._growth(before, after),
            "confidence_distribution": dict(context.confidence_scores),
            "generated_hypotheses": after["hypotheses"] - before["hypotheses"],
            "generated_programs": after["candidate_programs"] - before["candidate_programs"],
            "validation_summary": list(context.validation_results[-3:]),
        }
        context.stage_events.append(event)
        context.stage_snapshots.append(snapshot)
        context.execution_history.append(event)
        context.trace.append(stage.spec.stage_name)

    def _record_skipped(self, context: CognitiveContext, stage: CognitiveStage) -> None:
        event = {
            "stage_id": stage.spec.stage_id,
            "stage_name": stage.spec.stage_name,
            "inputs": list(stage.spec.required_inputs),
            "outputs": list(stage.spec.generated_outputs),
            "execution_start": time.time(),
            "execution_end": time.time(),
            "duration": 0.0,
            "cpu_cost": 0.0,
            "memory_cost": 0,
            "confidence": 0.0,
            "generated_concepts": [],
            "consumed_concepts": list(stage.spec.consumed_outputs),
            "dependencies": list(stage.dependencies),
            "produced_knowledge": {},
            "execution_status": "skipped",
        }
        context.stage_events.append(event)
        context.stage_snapshots.append({
            "stage_id": stage.spec.stage_id,
            "stage_name": stage.spec.stage_name,
            "context_snapshot": context.snapshot(),
            "context_growth": {},
            "confidence_distribution": dict(context.confidence_scores),
            "generated_hypotheses": 0,
            "generated_programs": 0,
            "validation_summary": list(context.validation_results[-3:]),
        })

    def _growth(self, before: dict, after: dict) -> dict:
        keys = (
            "perceived_objects",
            "relationships",
            "concepts",
            "hypotheses",
            "transformations",
            "candidate_programs",
            "evidence",
            "validation_results",
            "knowledge_candidates",
        )
        return {key: after[key] - before[key] for key in keys}

    def _growth_keys(self, before: dict, after: dict, key: str) -> list[str]:
        if after.get(key, 0) <= before.get(key, 0):
            return []
        return [key]


__all__ = ["CognitivePipelineOrchestrator"]
