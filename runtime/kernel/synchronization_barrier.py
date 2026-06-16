"""Stage-completion barrier for cognitive blackboard synchronization."""

from __future__ import annotations

from contextlib import AbstractContextManager
from copy import deepcopy
from typing import Any, Mapping


class SynchronizationBarrier:
    """Tracks committed stage writes before synchronization assertions run."""

    REQUIRED_STAGES = (
        "graph_reasoner",
        "localization_engine",
        "program_synthesizer",
        "execution_plan_builder",
    )

    def __init__(self, required_stages: tuple[str, ...] | None = None) -> None:
        self.required_stages = tuple(required_stages or self.REQUIRED_STAGES)
        self.completed_stages: set[str] = set()
        self.transaction_depth = 0
        self._pending_state: dict[str, Any] | None = None
        self._pending_stages: set[str] = set()

    def transaction(self, blackboard: Any) -> "_BlackboardTransaction":
        return _BlackboardTransaction(self, blackboard)

    @property
    def in_transaction(self) -> bool:
        return self.transaction_depth > 0

    def begin(self, state: Mapping[str, Any]) -> dict[str, Any]:
        if self.transaction_depth == 0:
            self._pending_state = deepcopy(dict(state))
            self._pending_stages = set()
        self.transaction_depth += 1
        return self._pending_state or {}

    def stage_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        if self._pending_state is None:
            self._pending_state = deepcopy(dict(state))
        return self._pending_state

    def mark_stage_complete(self, stage: str) -> None:
        stage = str(stage or "").strip()
        if not stage:
            return
        if self.in_transaction:
            self._pending_stages.add(stage)
        else:
            self.completed_stages.add(stage)

    def commit(self) -> tuple[dict[str, Any] | None, set[str]]:
        if self.transaction_depth == 0:
            return None, set()
        self.transaction_depth -= 1
        if self.transaction_depth > 0:
            return None, set()
        pending_state = self._pending_state
        pending_stages = set(self._pending_stages)
        self.completed_stages.update(pending_stages)
        self._pending_state = None
        self._pending_stages = set()
        return pending_state, pending_stages

    def rollback(self) -> None:
        self.transaction_depth = 0
        self._pending_state = None
        self._pending_stages = set()

    def ready(self) -> bool:
        return all(stage in self.completed_stages for stage in self.required_stages)

    def missing_stages(self) -> list[str]:
        return [
            stage
            for stage in self.required_stages
            if stage not in self.completed_stages
        ]

    def report(self) -> dict[str, Any]:
        return {
            "system": "synchronization_barrier",
            "required_stages": list(self.required_stages),
            "completed_stages": sorted(self.completed_stages),
            "missing_stages": self.missing_stages(),
            "transaction_open": self.in_transaction,
            "ready_for_synchronization_assertions": self.ready()
            and not self.in_transaction,
        }


class _BlackboardTransaction(AbstractContextManager):
    def __init__(self, barrier: SynchronizationBarrier, blackboard: Any) -> None:
        self.barrier = barrier
        self.blackboard = blackboard

    def __enter__(self) -> Any:
        self.barrier.begin(self.blackboard.state)
        return self.blackboard

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is not None:
            self.barrier.rollback()
            return False
        self.blackboard.commit()
        return False


__all__ = [
    "SynchronizationBarrier",
]
