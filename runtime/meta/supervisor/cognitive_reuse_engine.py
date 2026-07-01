"""Coordinates memory-layer lookup for the supervisor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from runtime.meta.supervisor.execution_memory import ExecutionMemory
from runtime.meta.supervisor.program_memory import ProgramMemory
from runtime.meta.supervisor.strategy_memory import StrategyMemory
from runtime.meta.supervisor.task_signature_engine import TaskSignature


@dataclass
class ReuseLookupResult:
    program_match: Any = None
    strategy_match: Any = None
    validated_context: Mapping[str, Any] | None = None
    locked_truth: Mapping[str, Any] | None = None
    completed_execution: Any = None


class CognitiveReuseEngine:
    def __init__(
        self,
        program_memory: ProgramMemory,
        strategy_memory: StrategyMemory,
        execution_memory: ExecutionMemory,
    ):
        self.program_memory = program_memory
        self.strategy_memory = strategy_memory
        self.execution_memory = execution_memory

    def lookup(
        self,
        task_signature: TaskSignature,
        runtime_context: Mapping[str, Any],
    ) -> ReuseLookupResult:
        signature_id = task_signature.stable_id()
        program_match = (
            self.program_memory.best_match_for_signature(task_signature)
            if hasattr(self.program_memory, "best_match_for_signature")
            else self.program_memory.best_match(signature_id)
        )
        return ReuseLookupResult(
            program_match=program_match,
            strategy_match=self.strategy_memory.best_match(
                signature_id,
                runtime_context,
            ),
            validated_context=self._validated_context(runtime_context),
            locked_truth=self._locked_truth(runtime_context),
            completed_execution=self.execution_memory.completed_episode(signature_id),
        )

    def _validated_context(
        self,
        runtime_context: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        candidates = [
            runtime_context.get("process_context_discovery_report"),
            runtime_context.get("process_context_report"),
            runtime_context.get("context_report"),
            runtime_context.get("validated_context"),
        ]
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            if candidate.get("stale") is True:
                continue
            if (
                candidate.get("process_context_ready") is True
                or candidate.get("validated") is True
                or candidate.get("status") == "PROCESS_CONTEXT_VALIDATED"
            ):
                return candidate
        return None

    def _locked_truth(
        self,
        runtime_context: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        candidates = [
            runtime_context.get("truth_commit_result"),
            runtime_context.get("truth_lifecycle_report"),
            runtime_context.get("governance_cache_report"),
            runtime_context.get("truth_registry_report"),
        ]
        for candidate in candidates:
            if isinstance(candidate, Mapping) and (
                candidate.get("final_commit_state") == "LOCKED_TRUTH_PRESERVED"
                or candidate.get("locked_truth_preserved") is True
            ):
                return {
                    **candidate,
                    "final_commit_state": "LOCKED_TRUTH_PRESERVED",
                }
        return None


__all__ = [
    "CognitiveReuseEngine",
    "ReuseLookupResult",
]
