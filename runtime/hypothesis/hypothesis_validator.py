"""Governed validation for hypotheses.

The validator intentionally never executes programs. It only checks whether a
hypothesis is semantically and governably admissible for later execution stages.
"""

from __future__ import annotations

from typing import Any, Mapping


class HypothesisValidator:
    """Validate semantic, context, dependency, identity, and truth consistency."""

    system_name = "hypothesis_validator"

    def validate(
        self,
        hypothesis: Mapping[str, Any],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        record = dict(hypothesis)
        checks = {
            "semantic_consistency": self._support_check(record, "semantic_support", 0.25),
            "contextual_consistency": self._support_check(record, "context_support", 0.20),
            "dependency_consistency": self._governance_check(
                runtime_context,
                ("dependency_governance_report", "dependency_graph_validation", "typed_dependency_validation_report"),
            ),
            "identity_consistency": self._governance_check(
                runtime_context,
                ("identity_governance_report", "identity_continuity_engine_report", "identity_continuity_guardian_report"),
            ),
            "truth_consistency": self._governance_check(
                runtime_context,
                ("truth_governance_report", "truth_validation_report", "truth_commit_result"),
            ),
            "context_governance": self._governance_check(
                runtime_context,
                ("context_governance_report", "contextual_truth_report", "semantic_context_report"),
            ),
        }
        passed = all(item["passed"] for item in checks.values())
        validation_score = sum(item["score"] for item in checks.values()) / max(len(checks), 1)
        return {
            "system": self.system_name,
            "hypothesis_id": record.get("hypothesis_id"),
            "validation_passed": passed,
            "validation_operational": True,
            "validation_score": round(validation_score, 4),
            "execution_ready": bool(passed and record.get("execution_ready")),
            "validation_checks": checks,
            "rejection_reasons": [
                name for name, result in checks.items()
                if not result["passed"]
            ],
        }

    def validate_many(
        self,
        hypotheses: list[Mapping[str, Any]],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        results = [self.validate(item, runtime_context) for item in hypotheses]
        accepted_ids = [
            item["hypothesis_id"] for item in results
            if item.get("validation_passed")
        ]
        rejected_ids = [
            item["hypothesis_id"] for item in results
            if not item.get("validation_passed")
        ]
        return {
            "system": self.system_name,
            "validation_operational": True,
            "validated_hypotheses": results,
            "accepted_hypothesis_ids": accepted_ids,
            "rejected_hypothesis_ids": rejected_ids,
            "accepted_count": len(accepted_ids),
            "rejected_count": len(rejected_ids),
        }

    def _support_check(self, record: Mapping[str, Any], field: str, minimum: float) -> dict[str, Any]:
        score = _score(record.get(field, record.get("confidence", 0.0)))
        return {
            "passed": score >= minimum,
            "score": score,
            "reason": "support_threshold_met" if score >= minimum else f"{field}_below_threshold",
        }

    def _governance_check(self, runtime_context: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
        observed = []
        for key in keys:
            value = runtime_context.get(key)
            if not isinstance(value, Mapping):
                continue
            observed.append(key)
            if self._explicit_failure(value):
                return {
                    "passed": False,
                    "score": 0.0,
                    "observed": observed,
                    "reason": f"{key}_failed",
                }
        return {
            "passed": True,
            "score": 1.0,
            "observed": observed,
            "reason": "no_blocking_governance_failure",
        }

    def _explicit_failure(self, value: Mapping[str, Any]) -> bool:
        for key, item in value.items():
            normalized_key = _normalize(key)
            normalized_value = _normalize(item)
            if normalized_key.endswith(("passed", "success", "ready", "validated")) and item is False:
                return True
            if normalized_key in {"status", "state", "validation_state", "governance_state"}:
                if normalized_value in {"failed", "rejected", "blocked", "invalid", "unsafe"}:
                    return True
        return False


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


hypothesis_validator = HypothesisValidator()

__all__ = ["HypothesisValidator", "hypothesis_validator"]
