"""Explainable adaptive authority for world-governance decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


GOVERNANCE_ACTIONS = (
    "ALLOW",
    "ALLOW_SANDBOX",
    "ALLOW_PROBATION",
    "DEFER",
    "DENY",
)

REJECTION_CATEGORIES = (
    "Truth Protection",
    "Identity Protection",
    "Ontology Protection",
    "Dependency Protection",
    "Context Protection",
    "Localization Failure",
    "Confidence Deficit",
    "Evidence Deficit",
    "Unknown Reason",
)


@dataclass
class GovernanceDecisionMemory:
    accepted_decisions: list[dict[str, Any]] = field(default_factory=list)
    rejected_decisions: list[dict[str, Any]] = field(default_factory=list)
    successful_probations: list[dict[str, Any]] = field(default_factory=list)
    false_rejections: list[dict[str, Any]] = field(default_factory=list)
    false_acceptances: list[dict[str, Any]] = field(default_factory=list)

    def record(self, report: Mapping[str, Any]) -> None:
        payload = dict(report)
        decision = str(payload.get("decision", "DENY"))
        if decision in {"ALLOW", "ALLOW_SANDBOX", "ALLOW_PROBATION"}:
            self.accepted_decisions.append(payload)
        elif decision == "DENY":
            self.rejected_decisions.append(payload)
        if (
            decision == "ALLOW_PROBATION"
            and payload.get("evaluation_success") is True
        ):
            self.successful_probations.append(payload)
        if payload.get("potential_governance_overreach") is True:
            self.false_rejections.append(payload)
        if (
            decision in {"ALLOW", "ALLOW_SANDBOX", "ALLOW_PROBATION"}
            and payload.get("critical_governance_risk") is True
        ):
            self.false_acceptances.append(payload)

    def report(self) -> dict[str, Any]:
        return {
            "system": "governance_decision_memory",
            "accepted_decision_count": len(self.accepted_decisions),
            "rejected_decision_count": len(self.rejected_decisions),
            "successful_probation_count": len(self.successful_probations),
            "false_rejection_count": len(self.false_rejections),
            "false_acceptance_count": len(self.false_acceptances),
            "accepted_decisions": self.accepted_decisions[-50:],
            "rejected_decisions": self.rejected_decisions[-50:],
            "successful_probations": self.successful_probations[-50:],
            "false_rejections": self.false_rejections[-50:],
            "false_acceptances": self.false_acceptances[-50:],
        }


class WorldGovernanceIntrospection:
    """Turns silent rejection into explainable adaptive governance."""

    system_name = "world_governance_introspection"

    def __init__(self, memory: GovernanceDecisionMemory | None = None):
        self.memory = memory or GovernanceDecisionMemory()

    def evaluate(
        self,
        context: Mapping[str, Any] | None = None,
        *,
        current_decision: str | None = None,
        rejection_reason: str | None = None,
        triggered_rules: list[str] | None = None,
    ) -> dict[str, Any]:
        context = context if isinstance(context, Mapping) else {}
        metrics = self._metrics(context)
        risks = self._risks(context)
        risk_score = max(
            risks["ontology_risk"],
            risks["identity_risk"],
            risks["truth_risk"],
        )
        category = self.classify_rejection(
            rejection_reason,
            triggered_rules or [],
            risks,
            metrics,
        )
        critical = self._critical_risk(risks, context)
        sandbox_eligible = (
            metrics["prediction_accuracy"] >= 0.90
            and not critical
        )
        probation_eligible = (
            metrics["prediction_accuracy"] >= 0.84
            and metrics["evidence_observed"] >= 0.50
            and not critical
        )
        false_rejection_probability = self._false_rejection_probability(
            metrics,
            current_decision,
            critical,
        )
        truth = self.adaptive_truth_thresholds(context)
        truth_commit_eligible = (
            metrics["confidence_observed"] >= truth["required_truth_threshold"]
            and metrics["evidence_observed"] >= truth["evidence_required"]
            and risks["truth_risk"] < 0.60
        )
        decision = self._decision(
            current_decision,
            critical,
            sandbox_eligible,
            probation_eligible,
            truth_commit_eligible,
            metrics,
        )
        recommended_action = self._recommended_action(
            decision,
            category,
            sandbox_eligible,
            probation_eligible,
            truth_commit_eligible,
        )
        report = {
            "system": self.system_name,
            "WORLD GOVERNANCE INTROSPECTION REPORT": True,
            "decision": decision,
            "reason": rejection_reason or self._reason(decision, category),
            "rejection_reason": rejection_reason,
            "risk_category": category,
            "triggered_rules": triggered_rules or [],
            "confidence_required": metrics["confidence_required"],
            "confidence_observed": metrics["confidence_observed"],
            "evidence_required": metrics["evidence_required"],
            "evidence_observed": metrics["evidence_observed"],
            "risk_score": round(risk_score, 4),
            "ontology_risk": risks["ontology_risk"],
            "identity_risk": risks["identity_risk"],
            "truth_risk": risks["truth_risk"],
            "trust_score": round(max(0.0, 1.0 - risk_score), 4),
            "probation_eligible": probation_eligible,
            "sandbox_eligible": sandbox_eligible,
            "truth_commit_eligible": truth_commit_eligible,
            "false_rejection_probability": false_rejection_probability,
            "potential_governance_overreach":
            false_rejection_probability >= 0.65,
            "critical_governance_risk": critical,
            "recommended_action": recommended_action,
            "learning_credit_authorized": decision in {
                "ALLOW_SANDBOX",
                "ALLOW_PROBATION",
                "ALLOW",
            },
            "evidence_accumulation_authorized": decision in {
                "ALLOW_SANDBOX",
                "ALLOW_PROBATION",
                "ALLOW",
                "DEFER",
            },
            "adaptive_truth_thresholds": truth,
            "governance_decision_report": {
                "decision": decision,
                "why_rejected": rejection_reason or self._reason(decision, category),
                "risk_category": category,
                "recommended_action": recommended_action,
            },
        }
        self.memory.record(report)
        return report

    def audit_false_rejection(
        self,
        gate_report: Mapping[str, Any],
        evaluation_result: Mapping[str, Any],
    ) -> dict[str, Any]:
        context = {
            **dict(gate_report or {}),
            "evaluation_success": evaluation_result.get("success"),
            "episode_completed": evaluation_result.get("episode_completed"),
            "prediction_accuracy": evaluation_result.get(
                "accuracy",
                evaluation_result.get("prediction_accuracy", 0.0),
            ),
        }
        report = self.evaluate(
            context,
            current_decision=(
                "DENY"
                if gate_report.get("execution_authorized") is not True
                and gate_report.get("sandbox_execution_authorized") is not True
                else "ALLOW"
            ),
            rejection_reason=gate_report.get("gate_state"),
            triggered_rules=["world_model_gate"],
        )
        return {
            "system": "governance_false_rejection_audit",
            "potential_governance_overreach":
            report["potential_governance_overreach"],
            "false_rejection_probability":
            report["false_rejection_probability"],
            "decision": report["decision"],
            "recommended_action": report["recommended_action"],
        }

    def adaptive_truth_thresholds(
        self,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context if isinstance(context, Mapping) else {}
        observation_count = self._number(
            context.get("observation_count", context.get("observed_count", 0)),
        )
        dependency_support = self._number(
            context.get(
                "dependency_support",
                context.get("dependency_confidence", 0.0),
            )
        )
        cross_task_stability = self._number(
            context.get("cross_task_stability", 0.0)
        )
        contradiction_score = self._number(
            context.get("contradiction_score", 0.0)
        )
        base_threshold = 0.95
        evidence_bonus = min(observation_count / 200.0, 0.05)
        dependency_bonus = 0.04 if dependency_support >= 0.88 else 0.0
        stability_bonus = 0.04 if cross_task_stability >= 0.88 else 0.0
        contradiction_bonus = 0.03 if contradiction_score <= 0.05 else 0.0
        required = max(
            0.84,
            base_threshold
            - evidence_bonus
            - dependency_bonus
            - stability_bonus
            - contradiction_bonus,
        )
        return {
            "adaptive_truth_thresholds_enabled": True,
            "base_truth_threshold": base_threshold,
            "required_truth_threshold": round(required, 4),
            "evidence_required": 0.70 if required <= 0.88 else 0.80,
            "observation_count": int(observation_count),
            "dependency_support": round(dependency_support, 4),
            "cross_task_stability": round(cross_task_stability, 4),
            "contradiction_score": round(contradiction_score, 4),
            "threshold_lowered": required < base_threshold,
        }

    def build_report(self) -> dict[str, Any]:
        return {
            "WORLD GOVERNANCE INTROSPECTION REPORT":
            self.memory.report()["accepted_decisions"][-1]
            if self.memory.accepted_decisions
            else (
                self.memory.rejected_decisions[-1]
                if self.memory.rejected_decisions
                else {}
            ),
            "GOVERNANCE DECISION MEMORY": self.memory.report(),
        }

    def classify_rejection(
        self,
        reason: str | None,
        triggered_rules: list[str],
        risks: Mapping[str, float],
        metrics: Mapping[str, float],
    ) -> str:
        text = " ".join([str(reason or ""), *map(str, triggered_rules)]).lower()
        if risks.get("truth_risk", 0.0) >= 0.70 or "truth" in text or "contradiction" in text:
            return "Truth Protection"
        if risks.get("identity_risk", 0.0) >= 0.70 or "identity" in text:
            return "Identity Protection"
        if risks.get("ontology_risk", 0.0) >= 0.70 or "ontology" in text or "topology" in text:
            return "Ontology Protection"
        if "dependency" in text:
            return "Dependency Protection"
        if "context" in text:
            return "Context Protection"
        if "localization" in text:
            return "Localization Failure"
        if metrics.get("confidence_observed", 0.0) < metrics.get("confidence_required", 0.0):
            return "Confidence Deficit"
        if metrics.get("evidence_observed", 0.0) < metrics.get("evidence_required", 0.0):
            return "Evidence Deficit"
        return "Unknown Reason"

    def _decision(
        self,
        current_decision: str | None,
        critical: bool,
        sandbox_eligible: bool,
        probation_eligible: bool,
        truth_commit_eligible: bool,
        metrics: Mapping[str, float],
    ) -> str:
        if critical:
            return "DENY"
        if str(current_decision or "").upper() in {"ALLOW", "ADMIT"}:
            return "ALLOW"
        if truth_commit_eligible and metrics["prediction_accuracy"] >= 0.95:
            return "ALLOW"
        if sandbox_eligible:
            return "ALLOW_SANDBOX"
        if probation_eligible:
            return "ALLOW_PROBATION"
        if metrics["evidence_observed"] >= 0.40:
            return "DEFER"
        return "DENY"

    def _recommended_action(
        self,
        decision: str,
        category: str,
        sandbox_eligible: bool,
        probation_eligible: bool,
        truth_commit_eligible: bool,
    ) -> str:
        if decision == "ALLOW":
            return "execute_and_monitor" if not truth_commit_eligible else "execute_and_truth_review"
        if decision == "ALLOW_SANDBOX" or sandbox_eligible:
            return "sandbox_execution_learning_credit_evidence_accumulation"
        if decision == "ALLOW_PROBATION" or probation_eligible:
            return "probationary_learning_credit_collect_more_evidence"
        if decision == "DEFER":
            return "defer_until_evidence_or_context_improves"
        return f"deny_due_to_{category.lower().replace(' ', '_')}"

    def _reason(self, decision: str, category: str) -> str:
        if decision in {"ALLOW_SANDBOX", "ALLOW_PROBATION"}:
            return "noncritical_learning_signal_preserved_under_controlled_exploration"
        if decision == "DEFER":
            return "evidence_insufficient_for_execution_but_not_critical"
        if decision == "ALLOW":
            return "governance_requirements_satisfied"
        return f"governance_rejection_classified_as_{category}"

    def _false_rejection_probability(
        self,
        metrics: Mapping[str, float],
        current_decision: str | None,
        critical: bool,
    ) -> float:
        rejected = str(current_decision or "").upper() in {
            "DENY",
            "REJECT",
            "QUARANTINE",
            "EXECUTION_ABORTED_WORLD_MODEL_REJECTION",
        }
        if not rejected or critical:
            return 0.0
        score = 0.0
        if metrics["evaluation_success"]:
            score += 0.35
        if metrics["episode_completed"]:
            score += 0.25
        if metrics["prediction_accuracy"] >= 0.90:
            score += 0.30
        if metrics["evidence_observed"] >= 0.60:
            score += 0.10
        return round(min(score, 1.0), 4)

    def _metrics(self, context: Mapping[str, Any]) -> dict[str, Any]:
        prediction_report = self._mapping(context.get("prediction_report"))
        evaluation = self._mapping(context.get("evaluation_result"))
        accuracy = self._number(
            context.get(
                "prediction_accuracy",
                evaluation.get(
                    "accuracy",
                    prediction_report.get("prediction_accuracy", 0.0),
                ),
            )
        )
        confidence = max(
            accuracy,
            self._number(context.get("confidence")),
            self._number(prediction_report.get("confidence")),
            self._number(context.get("execution_readiness")),
        )
        evidence = max(
            confidence,
            self._number(context.get("evidence_score")),
            self._number(context.get("support_score")),
            self._number(context.get("dependency_confidence")),
        )
        return {
            "prediction_accuracy": accuracy,
            "confidence_required": self._number(
                context.get("confidence_required", 0.95)
            ),
            "confidence_observed": round(confidence, 4),
            "evidence_required": self._number(
                context.get("evidence_required", 0.80)
            ),
            "evidence_observed": round(evidence, 4),
            "evaluation_success": (
                context.get("evaluation_success") is True
                or evaluation.get("success") is True
            ),
            "episode_completed": (
                context.get("episode_completed") is True
                or evaluation.get("episode_completed") is True
            ),
        }

    def _risks(self, context: Mapping[str, Any]) -> dict[str, float]:
        ontology_risk = max(
            self._number(context.get("ontology_risk")),
            1.0 if context.get("ontology_integrity_violation") is True else 0.0,
            1.0 if context.get("topology_preserved") is False else 0.0,
        )
        identity_risk = max(
            self._number(context.get("identity_risk")),
            1.0 if self._identity_unstable(context) else 0.0,
        )
        truth_risk = max(
            self._number(context.get("truth_risk")),
            1.0 if context.get("contradiction_detected") is True else 0.0,
            1.0 if context.get("semantic_contradictions") else 0.0,
        )
        return {
            "ontology_risk": round(min(ontology_risk, 1.0), 4),
            "identity_risk": round(min(identity_risk, 1.0), 4),
            "truth_risk": round(min(truth_risk, 1.0), 4),
        }

    def _critical_risk(
        self,
        risks: Mapping[str, float],
        context: Mapping[str, Any],
    ) -> bool:
        return (
            max(risks.values()) >= 0.75
            or context.get("protected_core_touched") is True
            or context.get("modify_locked_core") is True
        )

    def _identity_unstable(self, context: Mapping[str, Any]) -> bool:
        state = str(
            context.get(
                "identity_runtime_state",
                context.get("identity_governance_state", ""),
            )
        ).upper()
        return state in {
            "UNSTABLE",
            "IDENTITY_GOVERNANCE_UNSTABLE",
            "TEMPORARY_RECOVERY_HOLD",
        }

    def _mapping(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _number(self, value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return default


governance_decision_memory = GovernanceDecisionMemory()
world_governance_introspection = WorldGovernanceIntrospection(
    governance_decision_memory
)


__all__ = [
    "GOVERNANCE_ACTIONS",
    "REJECTION_CATEGORIES",
    "GovernanceDecisionMemory",
    "WorldGovernanceIntrospection",
    "governance_decision_memory",
    "world_governance_introspection",
]
