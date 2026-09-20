"""Explain why execution is ready, probationary, or blocked."""

from __future__ import annotations

from typing import Any, Mapping


READINESS_COMPONENTS = (
    "object_readiness",
    "localization_readiness",
    "transformation_readiness",
    "causal_readiness",
    "dependency_readiness",
    "context_readiness",
    "governance_readiness",
)


class ExecutionReadinessExplainer:
    system_name = "execution_readiness_explainer"

    def explain(
        self,
        readiness: Mapping[str, Any] | None = None,
        localization: Mapping[str, Any] | None = None,
        grounding: Mapping[str, Any] | None = None,
        governance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        readiness = readiness if isinstance(readiness, Mapping) else {}
        localization = localization if isinstance(localization, Mapping) else {}
        grounding = grounding if isinstance(grounding, Mapping) else {}
        governance = governance if isinstance(governance, Mapping) else {}

        scores = self._scores(readiness, localization, grounding, governance)
        execution_ready = readiness.get("execution_ready") is True
        probation_ready = self._probation_ready(readiness, governance)
        score = max(
            self._number(readiness.get("execution_readiness")),
            sum(scores.values()) / max(len(scores), 1),
        )
        blocking = [
            name
            for name, value in scores.items()
            if value < self._threshold_for(name)
        ]
        if readiness.get("safety_blocked") is True:
            blocking.append("safety_blocked")
        missing = self._missing_requirements(blocking, localization, grounding)
        readiness_class = (
            "EXECUTION_READY"
            if execution_ready
            else "EXECUTION_PROBATION"
            if probation_ready
            else "EXECUTION_BLOCKED"
            if blocking
            else "EXECUTION_DEFERRED"
        )
        return {
            "system": self.system_name,
            "EXECUTION READINESS REPORT": True,
            "execution_ready": execution_ready,
            "execution_probation": probation_ready,
            "execution_readiness_score": round(score, 4),
            "readiness_class": readiness_class,
            "blocking_factors": list(dict.fromkeys(blocking)),
            "missing_requirements": missing,
            "recommended_next_action": self._recommended_next_action(
                execution_ready,
                probation_ready,
                blocking,
            ),
            "object_readiness": round(scores["object_readiness"], 4),
            "localization_readiness": round(scores["localization_readiness"], 4),
            "transformation_readiness": round(scores["transformation_readiness"], 4),
            "causal_readiness": round(scores["causal_readiness"], 4),
            "dependency_readiness": round(scores["dependency_readiness"], 4),
            "context_readiness": round(scores["context_readiness"], 4),
            "governance_readiness": round(scores["governance_readiness"], 4),
        }

    def _scores(
        self,
        readiness: Mapping[str, Any],
        localization: Mapping[str, Any],
        grounding: Mapping[str, Any],
        governance: Mapping[str, Any],
    ) -> dict[str, float]:
        confidence_components = localization.get("confidence_components", {})
        if not isinstance(confidence_components, Mapping):
            confidence_components = {}
        target_objects = (
            grounding.get("target_objects")
            or localization.get("target_objects")
            or []
        )
        affected_objects = grounding.get("affected_objects") or []
        candidate_regions = grounding.get("candidate_object_regions") or []
        object_score = max(
            self._number(confidence_components.get("object_detection")),
            0.85 if target_objects else 0.0,
            0.65 if affected_objects or candidate_regions else 0.0,
        )
        localization_score = max(
            self._number(localization.get("localization_confidence")),
            self._number(readiness.get("localization_confidence")),
        )
        transformation_score = max(
            self._number(confidence_components.get("transformation")),
            0.75 if grounding.get("transformation_targets") else 0.0,
            self._number(readiness.get("hypothesis_confidence")),
        )
        causal_score = max(
            self._number(confidence_components.get("causal_support")),
            self._number(localization.get("causal_support")),
            self._number(readiness.get("causal_support")),
        )
        dependency_score = max(
            self._number(readiness.get("dependency_support")),
            self._number(localization.get("dependency_support")),
            0.70 if target_objects else 0.0,
        )
        context_score = max(
            self._number(localization.get("context_confidence")),
            self._number(localization.get("context_readiness")),
            0.70 if localization.get("localized_program") else 0.0,
        )
        governance_score = (
            self._number(governance.get("trust_score"), 1.0)
            if governance
            else 1.0
        )
        if governance.get("decision") == "DENY":
            governance_score = 0.0
        return {
            "object_readiness": object_score,
            "localization_readiness": localization_score,
            "transformation_readiness": transformation_score,
            "causal_readiness": causal_score,
            "dependency_readiness": dependency_score,
            "context_readiness": context_score,
            "governance_readiness": governance_score,
        }

    def _probation_ready(
        self,
        readiness: Mapping[str, Any],
        governance: Mapping[str, Any],
    ) -> bool:
        return (
            self._number(readiness.get("prediction_accuracy")) >= 0.90
            and self._number(governance.get("trust_score"), 1.0) >= 0.90
            and self._number(governance.get("risk_score")) <= 0.10
            and governance.get("learning_credit_authorized") is not False
            and readiness.get("safety_blocked") is not True
        )

    def _missing_requirements(
        self,
        blocking: list[str],
        localization: Mapping[str, Any],
        grounding: Mapping[str, Any],
    ) -> list[str]:
        missing = []
        if "object_readiness" in blocking:
            missing.append("target_objects_or_candidate_object_regions")
        if "localization_readiness" in blocking:
            missing.append("localization_confidence_or_recovery_evidence")
        if "transformation_readiness" in blocking:
            missing.append("transformation_targets")
        if "causal_readiness" in blocking:
            missing.append("causal_support")
        if "dependency_readiness" in blocking:
            missing.append("dependency_support")
        if "context_readiness" in blocking:
            missing.append("localized_program_or_context_support")
        if not localization.get("localized_program"):
            missing.append("localized_program")
        if not (grounding.get("localization_hints") or localization.get("localization_hints")):
            missing.append("localization_hints")
        return list(dict.fromkeys(missing))

    def _recommended_next_action(
        self,
        execution_ready: bool,
        probation_ready: bool,
        blocking: list[str],
    ) -> str:
        if execution_ready:
            return "execute"
        if probation_ready:
            return "execute_under_probation_and_record_grounding_evidence"
        if "object_readiness" in blocking:
            return "run_object_centric_grounding_recovery"
        if "localization_readiness" in blocking:
            return "run_residual_guided_localization_recovery"
        return "collect_missing_grounding_evidence"

    def _threshold_for(self, name: str) -> float:
        if name == "governance_readiness":
            return 0.90
        if name in {"object_readiness", "localization_readiness"}:
            return 0.60
        return 0.50

    def _number(self, value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return default


execution_readiness_explainer = ExecutionReadinessExplainer()


__all__ = [
    "ExecutionReadinessExplainer",
    "execution_readiness_explainer",
]
