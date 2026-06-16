"""Single source of truth for cross-stage cognitive runtime state."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from runtime.kernel.synchronization_barrier import SynchronizationBarrier


class StateSynchronizationFailure(AssertionError):
    """Raised when cognitive stages observe divergent runtime state."""


class CognitiveBlackboard:
    """Canonical writable runtime state shared by cognitive stages."""

    failure_code = "STATE_SYNCHRONIZATION_FAILURE"

    def __init__(self, initial_state: Mapping[str, Any] | None = None) -> None:
        self.state: dict[str, Any] = self._default_state()
        self.barrier = SynchronizationBarrier()
        if isinstance(initial_state, Mapping):
            self.merge(initial_state)

    def _default_state(self) -> dict[str, Any]:
        return {
            "graph_reasoning": {},
            "placement_rules": [],
            "position_rule": {},
            "localized_prediction": {},
            "synthesized_program": {},
            "execution_plan": {},
            "world_model": {},
            "evaluation": {},
        }

    def merge(self, values: Mapping[str, Any]) -> None:
        for section, value in values.items():
            if section not in self.state:
                continue
            self.write(section, value)

    def transaction(self):
        return self.barrier.transaction(self)

    def commit(self) -> dict[str, Any]:
        pending_state, _pending_stages = self.barrier.commit()
        if pending_state is not None:
            self.state = pending_state
        return self.state

    def mark_stage_complete(self, stage: str) -> None:
        self.barrier.mark_stage_complete(stage)

    def barrier_report(self) -> dict[str, Any]:
        return self.barrier.report()

    def _target_state(self) -> dict[str, Any]:
        if self.barrier.in_transaction:
            return self.barrier.stage_state(self.state)
        return self.state

    def write(self, section: str, value: Any) -> Any:
        if section not in self.state:
            raise KeyError(f"Unknown cognitive blackboard section: {section}")
        target = self._target_state()
        target[section] = deepcopy(value)
        return target[section]

    def update(self, section: str, values: Mapping[str, Any]) -> dict[str, Any]:
        if section not in self.state:
            raise KeyError(f"Unknown cognitive blackboard section: {section}")
        target = self._target_state()
        if not isinstance(target[section], dict):
            target[section] = {}
        target[section].update(deepcopy(dict(values)))
        return target[section]

    def read(self, section: str) -> Any:
        if section not in self.state:
            raise KeyError(f"Unknown cognitive blackboard section: {section}")
        return self._target_state()[section]

    @property
    def graph_reasoning(self) -> dict[str, Any]:
        return self._target_state()["graph_reasoning"]

    @property
    def placement_rules(self) -> list[Any]:
        return self._target_state()["placement_rules"]

    @property
    def position_rule(self) -> dict[str, Any]:
        return self._target_state()["position_rule"]

    @property
    def localized_prediction(self) -> dict[str, Any]:
        return self._target_state()["localized_prediction"]

    @property
    def synthesized_program(self) -> dict[str, Any]:
        return self._target_state()["synthesized_program"]

    @property
    def execution_plan(self) -> dict[str, Any]:
        return self._target_state()["execution_plan"]

    @property
    def world_model(self) -> dict[str, Any]:
        return self._target_state()["world_model"]

    @property
    def evaluation(self) -> dict[str, Any]:
        return self._target_state()["evaluation"]

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self._target_state())

    def synchronize_from_graph_reasoning(
        self,
        graph_reasoning: Mapping[str, Any] | None,
    ) -> None:
        graph_reasoning = (
            graph_reasoning
            if isinstance(graph_reasoning, Mapping)
            else {}
        )
        self.write("graph_reasoning", graph_reasoning)
        placement_rules = list(graph_reasoning.get("placement_rules", []) or [])
        self.write("placement_rules", placement_rules)
        if placement_rules:
            self.write("position_rule", placement_rules[0])
        self.mark_stage_complete("graph_reasoner")

    def synchronize_from_world_model(
        self,
        anticipation_report: Mapping[str, Any] | None,
    ) -> None:
        anticipation_report = (
            anticipation_report
            if isinstance(anticipation_report, Mapping)
            else {}
        )
        localization = anticipation_report.get("transformation_localization", {})
        localized_program = anticipation_report.get(
            "localized_synthesized_program",
            {},
        )
        prediction_report = anticipation_report.get("prediction_report", {})
        if isinstance(localized_program, Mapping):
            self.write("synthesized_program", localized_program)
            self.mark_stage_complete("program_synthesizer")
        if isinstance(localization, Mapping):
            self.write("localized_prediction", localization)
            self.mark_stage_complete("localization_engine")
            reports = localization.get("localization_reports", []) or []
            if reports:
                report = reports[0]
                if isinstance(report, Mapping):
                    causal_evidence = report.get("causal_evidence", {})
                    rule = (
                        causal_evidence.get("position_rule", {})
                        if isinstance(causal_evidence, Mapping)
                        else {}
                    )
                    if isinstance(rule, Mapping) and rule:
                        self.write("position_rule", rule)
        self.update(
            "world_model",
            {
                "anticipation": anticipation_report,
                "prediction_report": prediction_report,
                "prediction_accuracy": prediction_report.get(
                    "prediction_accuracy",
                    0.0,
                )
                if isinstance(prediction_report, Mapping)
                else 0.0,
                "execution_authorized": anticipation_report.get(
                    "execution_accepted",
                    False,
                ),
            },
        )

    def synchronize_execution_plan(
        self,
        execution_plan: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        execution_plan = (
            dict(execution_plan)
            if isinstance(execution_plan, Mapping)
            else {}
        )
        steps = self.synthesized_program.get("steps", [])
        localized_prediction_ready = bool(
            self.graph_reasoning.get(
                "localized_prediction_ready",
                self.localized_prediction.get("localization_ready", False),
            )
        )
        prerequisites_ready = bool(
            self.position_rule
            and self.synthesized_program.get("steps")
            and execution_plan.get("nodes") is not None
        )
        localization_ready = bool(localized_prediction_ready and prerequisites_ready)
        localized_step_count = len(steps)
        execution_plan.update({
            "localization_ready": localization_ready,
            "localized_step_count": localized_step_count,
            "position_rule": deepcopy(self.position_rule),
            "synthesized_program": deepcopy(self.synthesized_program),
        })
        self.write("execution_plan", execution_plan)
        self.mark_stage_complete("execution_plan_builder")
        if self.barrier.ready() and not self.barrier.in_transaction:
            self.assert_synchronized()
        return self.execution_plan

    def assert_synchronized(self) -> None:
        if self.barrier.in_transaction:
            return
        if not self.barrier.ready():
            return
        graph_ready = bool(
            self.graph_reasoning.get("localized_prediction_ready", False)
        )
        plan_ready = bool(
            self.execution_plan.get("localization_ready", False)
        )
        if graph_ready != plan_ready:
            self._fail(
                "localized_prediction_ready diverged from localization_ready"
            )

        steps = self.synthesized_program.get("steps", [])
        localized_step_count = self.execution_plan.get(
            "localized_step_count",
            0,
        )
        if len(steps) != localized_step_count:
            self._fail(
                "synthesized step count diverged from localized_step_count"
            )

        confidence = float(self.position_rule.get("confidence", 0.0) or 0.0)
        if confidence > 0.0 and not plan_ready:
            self._fail(
                "position_rule confidence requires localization_ready"
            )

    def _fail(self, reason: str) -> None:
        raise StateSynchronizationFailure(
            f"{self.failure_code}: {reason}"
        )


def cognitive_blackboard_from_context(context: dict[str, Any]) -> CognitiveBlackboard:
    blackboard = context.get("cognitive_blackboard")
    if isinstance(blackboard, CognitiveBlackboard):
        return blackboard
    blackboard = CognitiveBlackboard(
        blackboard
        if isinstance(blackboard, Mapping)
        else None
    )
    context["cognitive_blackboard"] = blackboard
    return blackboard


__all__ = [
    "CognitiveBlackboard",
    "StateSynchronizationFailure",
    "SynchronizationBarrier",
    "cognitive_blackboard_from_context",
]
