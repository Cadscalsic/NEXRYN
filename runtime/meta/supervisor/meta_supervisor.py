"""Meta-cognitive supervisor authority for reuse-first runtime control."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from runtime.meta.supervisor.cognitive_reuse_engine import CognitiveReuseEngine
from runtime.meta.supervisor.execution_memory import execution_memory
from runtime.meta.supervisor.program_memory import program_memory
from runtime.meta.supervisor.reuse_decision_engine import (
    CognitiveDirective,
    reuse_decision_engine,
)
from runtime.meta.supervisor.strategy_memory import strategy_memory
from runtime.meta.supervisor.task_signature_engine import (
    TaskSignature,
    task_signature_engine,
)


class MetaSupervisor:
    can_block_reasoning = True
    can_block_strategy_search = True
    can_block_context_discovery = True
    can_block_program_synthesis = True
    can_block_governance_revalidation = True
    can_force_fast_shutdown = True

    ACTION_PERMISSIONS = {
        "reasoning": "allow_reasoning",
        "deep_reasoning": "allow_reasoning",
        "program_synthesis": "allow_program_synthesis",
        "strategy_search": "allow_strategy_search",
        "strategy_evolution": "allow_strategy_search",
        "hypothesis_expansion": "allow_strategy_search",
        "context_discovery": "allow_context_discovery",
        "context_hierarchy_reconstruction": "allow_context_discovery",
        "governance": "allow_governance",
        "governance_revalidation": "allow_governance",
        "truth_revalidation": "allow_governance",
        "contradiction_review": "allow_governance",
        "truth_recommitment": "allow_governance",
        "introspection": "allow_reasoning",
        "self_improvement": "allow_reasoning",
        "curiosity_expansion": "allow_strategy_search",
    }

    def __init__(self):
        self.signature_engine = task_signature_engine
        self.reuse_engine = CognitiveReuseEngine(
            program_memory=program_memory,
            strategy_memory=strategy_memory,
            execution_memory=execution_memory,
        )
        self.decision_engine = reuse_decision_engine
        self.current_directive: CognitiveDirective | None = None
        self.current_signature: TaskSignature | None = None
        self.current_lookup = None
        self.decision_history: list[dict[str, Any]] = []
        self.reuse_counters = {
            "cache_hits": 0,
            "strategy_hits": 0,
            "program_hits": 0,
            "context_hits": 0,
            "truth_hits": 0,
            "total_decisions": 0,
        }

    def reset_episode(self) -> None:
        self.current_directive = None
        self.current_signature = None
        self.current_lookup = None

    def supervise(
        self,
        runtime_context: Mapping[str, Any] | None,
    ) -> CognitiveDirective:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        task_signature = self.signature_engine.build_signature(runtime_context)
        lookup = self.reuse_engine.lookup(task_signature, runtime_context)
        episode_completed = (
            runtime_context.get("episode_completed") is True
            or lookup.completed_execution is not None
        )
        directive = self.decision_engine.decide(
            runtime_context=runtime_context,
            program_match=lookup.program_match,
            strategy_match=lookup.strategy_match,
            validated_context=lookup.validated_context,
            locked_truth=lookup.locked_truth,
            episode_completed=episode_completed,
        )
        self.current_signature = task_signature
        self.current_lookup = lookup
        self.current_directive = directive
        self._record_reuse(directive)
        self.decision_history.append(
            {
                "task_signature": task_signature.as_dict(),
                "task_signature_id": task_signature.stable_id(),
                "directive": directive.as_report(),
            }
        )
        return directive

    def is_action_allowed(self, action: str) -> bool:
        directive = self.current_directive
        if directive is None:
            return True
        if directive.action == "STOP_COGNITION":
            return False
        permission = self.ACTION_PERMISSIONS.get(str(action))
        if permission is None:
            return True
        return bool(getattr(directive, permission))

    def apply_to_context(
        self,
        runtime_context: dict[str, Any],
    ) -> dict[str, Any]:
        directive = self.current_directive or self.supervise(runtime_context)
        runtime_context["cognitive_directive"] = directive.as_report()
        runtime_context["META_SUPERVISOR_REPORT"] = self.build_meta_supervisor_report()
        runtime_context["meta_supervisor_report"] = runtime_context["META_SUPERVISOR_REPORT"]
        runtime_context["COGNITIVE_REUSE_REPORT"] = self.build_cognitive_reuse_report()
        runtime_context["cognitive_reuse_report"] = runtime_context["COGNITIVE_REUSE_REPORT"]
        return runtime_context

    def build_meta_supervisor_report(self) -> dict[str, Any]:
        directive = self.current_directive
        signature = self.current_signature
        lookup = self.current_lookup
        action = directive.action if directive is not None else "RUN_LIGHT_REASONING"
        return {
            "task_signature": signature.as_dict() if signature is not None else {},
            "task_signature_id": signature.stable_id() if signature is not None else "",
            "selected_action": action,
            "memory_layer_used": self._memory_layer_for_action(action),
            "reasoning_skipped": directive.allow_reasoning is False if directive else False,
            "governance_skipped": directive.allow_governance is False if directive else False,
            "context_reused": action == "REUSE_VALIDATED_CONTEXT",
            "strategy_reused": action == "REUSE_KNOWN_STRATEGY",
            "program_reused": action == "REUSE_EXECUTABLE_PROGRAM",
            "truth_reused": action == "REUSE_LOCKED_TRUTH",
            "estimated_time_saved": self._estimated_time_saved(action),
            "shutdown_mode": directive.shutdown_mode if directive else "fast",
            "directive": directive.as_report() if directive else {},
            "program_match": asdict(lookup.program_match) if getattr(lookup, "program_match", None) else None,
            "strategy_match": asdict(lookup.strategy_match) if getattr(lookup, "strategy_match", None) else None,
        }

    def build_cognitive_reuse_report(self) -> dict[str, Any]:
        total = max(self.reuse_counters["total_decisions"], 1)
        hits = (
            self.reuse_counters["program_hits"]
            + self.reuse_counters["strategy_hits"]
            + self.reuse_counters["context_hits"]
            + self.reuse_counters["truth_hits"]
        )
        return {
            "cache_hits": self.reuse_counters["cache_hits"],
            "strategy_hits": self.reuse_counters["strategy_hits"],
            "program_hits": self.reuse_counters["program_hits"],
            "context_hits": self.reuse_counters["context_hits"],
            "truth_hits": self.reuse_counters["truth_hits"],
            "reuse_rate": round(hits / total, 4),
        }

    def _record_reuse(self, directive: CognitiveDirective) -> None:
        self.reuse_counters["total_decisions"] += 1
        if directive.action == "REUSE_EXECUTABLE_PROGRAM":
            self.reuse_counters["program_hits"] += 1
            self.reuse_counters["cache_hits"] += 1
        elif directive.action == "REUSE_KNOWN_STRATEGY":
            self.reuse_counters["strategy_hits"] += 1
            self.reuse_counters["cache_hits"] += 1
        elif directive.action == "REUSE_VALIDATED_CONTEXT":
            self.reuse_counters["context_hits"] += 1
            self.reuse_counters["cache_hits"] += 1
        elif directive.action == "REUSE_LOCKED_TRUTH":
            self.reuse_counters["truth_hits"] += 1
            self.reuse_counters["cache_hits"] += 1

    def _memory_layer_for_action(self, action: str) -> str:
        return {
            "REUSE_EXECUTABLE_PROGRAM": "program_memory",
            "REUSE_KNOWN_STRATEGY": "strategy_memory",
            "REUSE_VALIDATED_CONTEXT": "validated_context_memory",
            "REUSE_LOCKED_TRUTH": "locked_truth_memory",
            "STOP_COGNITION": "execution_memory",
        }.get(action, "reasoning")

    def _estimated_time_saved(self, action: str) -> float:
        return {
            "REUSE_EXECUTABLE_PROGRAM": 0.85,
            "REUSE_KNOWN_STRATEGY": 0.65,
            "REUSE_VALIDATED_CONTEXT": 0.35,
            "REUSE_LOCKED_TRUTH": 0.25,
            "STOP_COGNITION": 0.95,
        }.get(action, 0.0)


meta_supervisor = MetaSupervisor()


__all__ = [
    "CognitiveDirective",
    "MetaSupervisor",
    "meta_supervisor",
]
