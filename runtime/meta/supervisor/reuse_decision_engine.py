"""Reuse-first decision rules for the meta-cognitive supervisor."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


ALLOWED_DIRECTIVE_ACTIONS = {
    "REUSE_EXECUTABLE_PROGRAM",
    "REUSE_KNOWN_STRATEGY",
    "REUSE_VALIDATED_CONTEXT",
    "REUSE_LOCKED_TRUTH",
    "RUN_LIGHT_REASONING",
    "RUN_DEEP_REASONING",
    "STOP_COGNITION",
}


@dataclass
class CognitiveDirective:
    action: str
    reason: str
    confidence: float
    allow_reasoning: bool
    allow_program_synthesis: bool
    allow_strategy_search: bool
    allow_context_discovery: bool
    allow_governance: bool
    shutdown_mode: str

    def as_report(self) -> dict[str, Any]:
        return asdict(self)


class ReuseDecisionEngine:
    PROGRAM_REUSE_THRESHOLD = 0.95
    STRATEGY_SUCCESS_THRESHOLD = 0.90
    CONTEXT_MATCH_THRESHOLD = 0.90

    def decide(
        self,
        runtime_context: Mapping[str, Any],
        program_match: Any = None,
        strategy_match: Any = None,
        validated_context: Mapping[str, Any] | None = None,
        locked_truth: Mapping[str, Any] | None = None,
        episode_completed: bool = False,
    ) -> CognitiveDirective:
        if episode_completed:
            return CognitiveDirective(
                action="STOP_COGNITION",
                reason="episode_completed",
                confidence=1.0,
                allow_reasoning=False,
                allow_program_synthesis=False,
                allow_strategy_search=False,
                allow_context_discovery=False,
                allow_governance=False,
                shutdown_mode="fast",
            )

        if (
            program_match is not None
            and getattr(program_match, "match_confidence", 0.0)
            >= self.PROGRAM_REUSE_THRESHOLD
        ):
            return CognitiveDirective(
                action="REUSE_EXECUTABLE_PROGRAM",
                reason="validated_program_match_confidence_met",
                confidence=float(getattr(program_match, "match_confidence", 0.0)),
                allow_reasoning=False,
                allow_program_synthesis=False,
                allow_strategy_search=False,
                allow_context_discovery=False,
                allow_governance=True,
                shutdown_mode="fast",
            )

        if (
            strategy_match is not None
            and getattr(strategy_match, "success_rate", 0.0)
            >= self.STRATEGY_SUCCESS_THRESHOLD
            and getattr(strategy_match, "context_match", 0.0)
            >= self.CONTEXT_MATCH_THRESHOLD
        ):
            confidence = min(
                float(getattr(strategy_match, "success_rate", 0.0)),
                float(getattr(strategy_match, "context_match", 0.0)),
            )
            return CognitiveDirective(
                action="REUSE_KNOWN_STRATEGY",
                reason="validated_strategy_success_and_context_match_met",
                confidence=confidence,
                allow_reasoning=True,
                allow_program_synthesis=False,
                allow_strategy_search=False,
                allow_context_discovery=False,
                allow_governance=True,
                shutdown_mode="fast",
            )

        if self._validated_context_exists(validated_context):
            return CognitiveDirective(
                action="REUSE_VALIDATED_CONTEXT",
                reason="validated_context_exists",
                confidence=float(validated_context.get("context_confidence", 0.90)),
                allow_reasoning=True,
                allow_program_synthesis=True,
                allow_strategy_search=True,
                allow_context_discovery=False,
                allow_governance=True,
                shutdown_mode="fast",
            )

        if self._locked_truth_preserved(locked_truth):
            return CognitiveDirective(
                action="REUSE_LOCKED_TRUTH",
                reason="locked_truth_preserved",
                confidence=1.0,
                allow_reasoning=True,
                allow_program_synthesis=True,
                allow_strategy_search=True,
                allow_context_discovery=True,
                allow_governance=False,
                shutdown_mode="fast",
            )

        if self._deep_reasoning_required(runtime_context):
            return CognitiveDirective(
                action="RUN_DEEP_REASONING",
                reason="no_validated_reuse_match_and_uncertainty_high",
                confidence=0.50,
                allow_reasoning=True,
                allow_program_synthesis=True,
                allow_strategy_search=True,
                allow_context_discovery=True,
                allow_governance=True,
                shutdown_mode="normal",
            )

        return CognitiveDirective(
            action="RUN_LIGHT_REASONING",
            reason="no_validated_reuse_match",
            confidence=0.60,
            allow_reasoning=True,
            allow_program_synthesis=True,
            allow_strategy_search=True,
            allow_context_discovery=True,
            allow_governance=True,
            shutdown_mode="fast",
        )

    def _validated_context_exists(
        self,
        validated_context: Mapping[str, Any] | None,
    ) -> bool:
        if not isinstance(validated_context, Mapping):
            return False
        return (
            validated_context.get("process_context_ready") is True
            or validated_context.get("status") == "PROCESS_CONTEXT_VALIDATED"
            or validated_context.get("validated") is True
        ) and validated_context.get("stale") is not True

    def _locked_truth_preserved(
        self,
        locked_truth: Mapping[str, Any] | None,
    ) -> bool:
        if not isinstance(locked_truth, Mapping):
            return False
        return locked_truth.get("final_commit_state") == "LOCKED_TRUTH_PRESERVED"

    def _deep_reasoning_required(self, runtime_context: Mapping[str, Any]) -> bool:
        uncertainty = runtime_context.get("uncertainty_level", 0.0)
        conflict = runtime_context.get("conflict_level")
        try:
            uncertainty = float(uncertainty)
        except (TypeError, ValueError):
            uncertainty = 0.0
        return uncertainty >= 0.75 or conflict in {"high", "critical"}


reuse_decision_engine = ReuseDecisionEngine()


__all__ = [
    "ALLOWED_DIRECTIVE_ACTIONS",
    "CognitiveDirective",
    "ReuseDecisionEngine",
    "reuse_decision_engine",
]
