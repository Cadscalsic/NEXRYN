"""World-governed sandbox citizenship promotion policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


EXPECTED_OPERATIONAL_DOMAINS = (
    "Color",
    "Geometry",
    "Growth",
    "Identity",
    "Spatial",
    "Topology",
    "Transformation",
)


@dataclass(frozen=True)
class SandboxCitizenshipThresholds:
    min_distinct_tasks: int
    min_arena_quality_count: int
    min_average_accuracy: float
    min_best_accuracy: float
    allowed_trends: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "min_distinct_tasks": self.min_distinct_tasks,
            "min_arena_quality_count": self.min_arena_quality_count,
            "min_average_accuracy": self.min_average_accuracy,
            "min_best_accuracy": self.min_best_accuracy,
            "allowed_trends": list(self.allowed_trends),
        }


@dataclass(frozen=True)
class CapabilityPromotionPolicyDecision:
    policy_state: str
    rationale: list[str]
    sandbox_citizenship_thresholds: SandboxCitizenshipThresholds
    validation_sponsorship_contract: dict[str, Any]
    trusted_capability_policy: dict[str, Any]
    decision_authority_policy: dict[str, Any]
    authority_boundary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_state": self.policy_state,
            "rationale": list(self.rationale),
            "sandbox_citizenship_thresholds": (
                self.sandbox_citizenship_thresholds.as_dict()
            ),
            "validation_sponsorship_contract": dict(
                self.validation_sponsorship_contract
            ),
            "trusted_capability_policy": dict(self.trusted_capability_policy),
            "decision_authority_policy": dict(self.decision_authority_policy),
            "authority_boundary": dict(self.authority_boundary),
        }


class CapabilityPromotionPolicyEngine:
    """Set dynamic sandbox citizenship policy from world population health."""

    def decide(
        self,
        metrics: Mapping[str, Any] | None = None,
    ) -> CapabilityPromotionPolicyDecision:
        data = dict(metrics or {})
        citizen_count = _int(data.get("operational_citizen_count"))
        generated = _int(data.get("generated_survival_candidate_count"))
        domain_coverage = _ratio(data.get("operational_domain_citizenship_coverage"))
        monopoly_share = _ratio(data.get("domain_monopoly_share"))
        pressure = _float(data.get("generated_to_citizen_pressure_ratio"))
        crystallization_state = str(
            data.get("capability_crystallization_state") or ""
        )

        rationale: list[str] = []
        if citizen_count < 10:
            rationale.append("operational_citizen_population_low")
        if domain_coverage < 0.70:
            rationale.append("operational_domain_citizenship_coverage_low")
        if pressure > 5.0 or (
            generated > 0 and citizen_count == 0
        ):
            rationale.append("generated_to_citizen_pressure_high")
        if crystallization_state == "SEVERE_CRYSTALLIZATION_FAILURE":
            rationale.append("severe_capability_crystallization_failure")
        if monopoly_share >= 0.60:
            rationale.append("domain_monopoly_pressure")

        if (
            citizen_count >= 50
            and domain_coverage >= 0.70
            and pressure <= 5.0
            and monopoly_share < 0.40
        ):
            policy_state = "TIGHTEN_SANDBOX_CITIZENSHIP"
            thresholds = SandboxCitizenshipThresholds(
                min_distinct_tasks=5,
                min_arena_quality_count=5,
                min_average_accuracy=0.88,
                min_best_accuracy=0.90,
                allowed_trends=("STABLE", "IMPROVING", "STABLE_HIGH_PERFORMANCE"),
            )
            rationale.append("operational_population_mature")
        elif rationale:
            policy_state = "RELAX_SANDBOX_CITIZENSHIP"
            thresholds = SandboxCitizenshipThresholds(
                min_distinct_tasks=3,
                min_arena_quality_count=3,
                min_average_accuracy=0.80,
                min_best_accuracy=0.0,
                allowed_trends=(
                    "STABLE",
                    "IMPROVING",
                    "STABLE_HIGH_PERFORMANCE",
                    "DECLINING_MINOR",
                ),
            )
        else:
            policy_state = "STANDARD_SANDBOX_CITIZENSHIP"
            thresholds = SandboxCitizenshipThresholds(
                min_distinct_tasks=4,
                min_arena_quality_count=4,
                min_average_accuracy=0.84,
                min_best_accuracy=0.80,
                allowed_trends=("STABLE", "IMPROVING", "STABLE_HIGH_PERFORMANCE"),
            )
            rationale.append("operational_population_balanced")

        return CapabilityPromotionPolicyDecision(
            policy_state=policy_state,
            rationale=rationale,
            sandbox_citizenship_thresholds=thresholds,
            validation_sponsorship_contract={
                "contract_state": "WORLD_GOVERNANCE_VALIDATION_SPONSOR",
                "truth_preparation_gate": "OPPORTUNITY_PERMISSION_ONLY",
                "capability_merit_system": "VALIDATION_PRIORITY_ONLY",
                "philosophical_principle": (
                    "governance_may_open_the_road_to_truth_but_never_grant_truth"
                ),
                "allowed_outputs": [
                    "validation_opportunity_priority",
                    "validation_opportunity_count",
                    "elite_validation_priority",
                    "capability_merit_score",
                    "ground_truth_priority",
                    "validation_sprint_allocation",
                    "cluster_validation_priority",
                    "cross_domain_validation_priority",
                ],
                "forbidden_outputs": [
                    "trust_score",
                    "truth_score",
                    "graduation_score",
                    "promotion_decision",
                    "truth_decision",
                    "governed_validation_decision",
                ],
                "allowed_opportunity_types": [
                    "elite_validation_opportunities",
                    "cross_domain_validation_opportunities",
                    "cluster_validation_opportunities",
                    "independent_validation_opportunities",
                    "ground_truth_opportunities",
                    "validation_sprint_opportunities",
                ],
                "truth_boundary_contract": [
                    "INVESTMENT_NEVER_INFLUENCES_TRUTH_FORMATION",
                    "MERIT_NEVER_INFLUENCES_TRUTH_FORMATION",
                    "VALIDATION_PRIORITY_NEVER_INFLUENCES_TRUTH_FORMATION",
                    "VALIDATION_SPONSORSHIP_NEVER_INFLUENCES_TRUST_FORMATION",
                ],
                "promotion_philosophy": (
                    "importance_allocates_opportunities_evidence_decides_promotion"
                ),
                "validation_requirements_changed": False,
            },
            trusted_capability_policy={
                "policy_state": "STRICT_REVIEW_REQUIRED",
                "min_distinct_tasks": 10,
                "min_average_accuracy": 0.95,
                "requires_reuse_evidence": True,
                "requires_cross_task_validation": True,
                "regression_allowed": False,
            },
            decision_authority_policy={
                "policy_state": "SEPARATE_AUTHORITY_REVIEW_REQUIRED",
                "automatic_authority_transfer": False,
                "prediction_authority_preserved": "adaptive_search",
            },
            authority_boundary={
                "sandbox_citizenship_is_not_trust": True,
                "trusted_for_decision": False,
                "citizenship_authority": "SANDBOX_ONLY",
                "world_governance_role": "VALIDATION_SPONSOR",
                "truth_authority": False,
                "trust_authority": False,
                "graduation_authority": False,
            },
        )


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ratio(value: Any) -> float:
    return max(0.0, min(1.0, _float(value)))


capability_promotion_policy_engine = CapabilityPromotionPolicyEngine()


__all__ = [
    "CapabilityPromotionPolicyDecision",
    "CapabilityPromotionPolicyEngine",
    "EXPECTED_OPERATIONAL_DOMAINS",
    "SandboxCitizenshipThresholds",
    "capability_promotion_policy_engine",
]
