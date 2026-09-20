"""Lifecycle and readiness registry for cognitive program blueprints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


CANONICAL_PROGRAM_STAGES = [
    "DISCOVERED",
    "GENERATED",
    "CLASSIFIED",
    "CAPABILITY_PROFILE_ASSIGNED",
    "MENTAL_MODEL_ASSIGNED",
    "PACKAGE_REQUIREMENTS_IDENTIFIED",
    "EXECUTION_REQUIREMENTS_VALIDATED",
    "CANDIDATE_REQUIREMENTS_VALIDATED",
    "VALIDATION_REQUIREMENTS_VALIDATED",
    "CANDIDATE_READY",
    "EXECUTION_READY",
    "OPERATIONAL",
]


@dataclass
class CognitiveProgramLifecycle:
    program_id: str
    program_type: str
    semantic_family: str
    lifecycle_status: str
    maturity_level: str
    execution_readiness: str
    candidate_readiness: str
    operational_readiness: str
    required_packages: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    supported_concepts: list[str] = field(default_factory=list)
    capability_profile: dict[str, Any] = field(default_factory=dict)
    lifecycle_stages_completed: list[str] = field(default_factory=list)
    lifecycle_failures: list[dict[str, Any]] = field(default_factory=list)
    operational_maturity_score: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveProgramLifecycleRegistry:
    """Track maturation and candidate readiness for program blueprints."""

    system_name = "cognitive_program_lifecycle_registry"

    def build(
        self,
        blueprint_intelligence_report: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        report = blueprint_intelligence_report if isinstance(blueprint_intelligence_report, Mapping) else {}
        rows = report.get("program_blueprint_intelligence", [])
        rows = rows if isinstance(rows, list) else []
        lifecycles = [
            self._lifecycle(row).as_dict()
            for row in rows
            if isinstance(row, Mapping)
        ]
        return {
            "system": self.system_name,
            "COGNITIVE_PROGRAM_LIFECYCLE_REPORT": True,
            "program_registry": lifecycles,
            "total_program_blueprints": len(lifecycles),
            "readiness_distribution": self._distribution(lifecycles, "operational_readiness"),
            "execution_readiness_distribution": self._distribution(lifecycles, "execution_readiness"),
            "candidate_readiness_distribution": self._distribution(lifecycles, "candidate_readiness"),
            "maturity_distribution": self._distribution(lifecycles, "maturity_level"),
            "semantic_family_coverage": self._distribution(lifecycles, "semantic_family"),
            "operational_program_count": sum(
                1 for item in lifecycles
                if item.get("operational_readiness") == "READY"
            ),
            "blocked_program_count": sum(
                1 for item in lifecycles
                if item.get("lifecycle_failures")
            ),
            "partially_operational_program_count": sum(
                1 for item in lifecycles
                if item.get("operational_readiness") == "PARTIAL"
            ),
            "silent_lifecycle_failures": False,
        }

    def _lifecycle(self, intelligence: Mapping[str, Any]) -> CognitiveProgramLifecycle:
        required = _list(intelligence.get("required_packages"))
        missing = _list(intelligence.get("missing_requirements"))
        supported = _list(intelligence.get("supported_concepts"))
        execution = self._execution_readiness(intelligence)
        candidate = self._candidate_readiness(intelligence)
        operational = self._operational_readiness(execution, candidate, intelligence)
        completed = self._completed_stages(intelligence, execution, candidate, operational)
        failures = self._failures(intelligence, execution, candidate, operational, missing)
        maturity = self._maturity_level(execution, candidate, operational, completed)
        status = self._lifecycle_status(completed, failures, operational)
        score = round(len(completed) / len(CANONICAL_PROGRAM_STAGES), 4)
        return CognitiveProgramLifecycle(
            program_id=str(intelligence.get("blueprint_id") or f"program:{intelligence.get('program_type', 'unknown')}"),
            program_type=str(intelligence.get("program_type") or "unknown_program"),
            semantic_family=str(intelligence.get("semantic_family") or "Not Available"),
            lifecycle_status=status,
            maturity_level=maturity,
            execution_readiness=execution,
            candidate_readiness=candidate,
            operational_readiness=operational,
            required_packages=required,
            missing_requirements=missing,
            supported_concepts=supported,
            capability_profile=dict(intelligence.get("capability_profile") or {}),
            lifecycle_stages_completed=completed,
            lifecycle_failures=failures,
            operational_maturity_score=score,
        )

    def _execution_readiness(self, intelligence: Mapping[str, Any]) -> str:
        state = str(intelligence.get("execution_ready") or "NOT_SUPPORTED")
        if state == "EXECUTION_READY":
            return "READY"
        if state in {"PARTIALLY_OPERATIONAL", "BLUEPRINT_ONLY"}:
            return "PARTIAL"
        return "NOT_READY"

    def _candidate_readiness(self, intelligence: Mapping[str, Any]) -> str:
        state = str(intelligence.get("candidate_ready") or "NOT_READY")
        if state == "READY_FOR_PROPOSAL":
            return "READY"
        if state == "WAITING_FOR_VALIDATION":
            return "PARTIAL"
        return "NOT_READY"

    def _operational_readiness(
        self,
        execution: str,
        candidate: str,
        intelligence: Mapping[str, Any],
    ) -> str:
        validation_ready = _truth(intelligence.get("validation_ready"))
        if execution == "READY" and candidate == "READY" and validation_ready == "TRUE":
            return "READY"
        if "PARTIAL" in {execution, candidate} or validation_ready == "TRUE":
            return "PARTIAL"
        return "NOT_READY"

    def _completed_stages(
        self,
        intelligence: Mapping[str, Any],
        execution: str,
        candidate: str,
        operational: str,
    ) -> list[str]:
        stages = ["DISCOVERED"]
        if intelligence.get("program_type"):
            stages.append("GENERATED")
            stages.append("CLASSIFIED")
        if intelligence.get("capability_profile"):
            stages.append("CAPABILITY_PROFILE_ASSIGNED")
        if intelligence.get("mental_model") and str(intelligence.get("mental_model")) != "Not Available":
            stages.append("MENTAL_MODEL_ASSIGNED")
        if intelligence.get("required_packages"):
            stages.append("PACKAGE_REQUIREMENTS_IDENTIFIED")
        if execution in {"PARTIAL", "READY"}:
            stages.append("EXECUTION_REQUIREMENTS_VALIDATED")
        if candidate in {"PARTIAL", "READY"}:
            stages.append("CANDIDATE_REQUIREMENTS_VALIDATED")
        if _truth(intelligence.get("validation_ready")) == "TRUE":
            stages.append("VALIDATION_REQUIREMENTS_VALIDATED")
        if candidate == "READY":
            stages.append("CANDIDATE_READY")
        if execution == "READY":
            stages.append("EXECUTION_READY")
        if operational == "READY":
            stages.append("OPERATIONAL")
        return [stage for stage in CANONICAL_PROGRAM_STAGES if stage in stages]

    def _failures(
        self,
        intelligence: Mapping[str, Any],
        execution: str,
        candidate: str,
        operational: str,
        missing: list[str],
    ) -> list[dict[str, Any]]:
        failures = []
        if execution == "NOT_READY":
            failures.append(self._failure(
                "EXECUTION_REQUIREMENTS_VALIDATED",
                "NO_EXECUTION_PACKAGE",
                missing,
                "execution_readiness_blocked",
            ))
        if candidate != "READY":
            reason = (
                "MISSING_CANDIDATE_SUPPORT"
                if any("candidate" in item for item in missing)
                else str(intelligence.get("candidate_ready") or "NOT_READY")
            )
            failures.append(self._failure(
                "CANDIDATE_REQUIREMENTS_VALIDATED",
                reason,
                missing,
                "candidate_readiness_blocked",
            ))
        if operational != "READY":
            reason = (
                "VALIDATION_SUPPORT_MISSING"
                if any("validation" in item for item in missing)
                else "OPERATIONAL_REQUIREMENTS_INCOMPLETE"
            )
            failures.append(self._failure(
                "VALIDATION_REQUIREMENTS_VALIDATED",
                reason,
                missing,
                "operational_readiness_blocked",
            ))
        return failures

    def _failure(
        self,
        stage: str,
        reason: str,
        missing: list[str],
        impact: str,
    ) -> dict[str, Any]:
        return {
            "failed_stage": stage,
            "reason": reason,
            "missing_requirements": list(missing),
            "capability_impact": impact,
        }

    def _maturity_level(
        self,
        execution: str,
        candidate: str,
        operational: str,
        completed: list[str],
    ) -> str:
        if operational == "READY" and execution == "READY" and candidate == "READY":
            return "FULLY_OPERATIONAL"
        if operational == "READY":
            return "OPERATIONAL"
        if execution == "READY" or candidate == "READY":
            return "ADVANCED"
        if execution == "PARTIAL" or candidate == "PARTIAL":
            return "PARTIALLY_OPERATIONAL"
        if "CAPABILITY_PROFILE_ASSIGNED" in completed:
            return "FOUNDATIONAL"
        return "EXPERIMENTAL"

    def _lifecycle_status(
        self,
        completed: list[str],
        failures: list[dict[str, Any]],
        operational: str,
    ) -> str:
        if operational == "READY":
            return "OPERATIONAL"
        if failures:
            failure_stages = {item.get("failed_stage") for item in failures}
            for stage in reversed(CANONICAL_PROGRAM_STAGES):
                if stage in completed and stage not in failure_stages:
                    return stage
        return completed[-1] if completed else "DISCOVERED"

    def _distribution(self, rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        distribution: dict[str, int] = {}
        for row in rows:
            value = str(row.get(key) or "Not Available")
            distribution[value] = distribution.get(value, 0) + 1
        return distribution


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, (tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _truth(value: Any) -> str:
    text = str(value or "").upper()
    if text in {"TRUE", "FALSE"}:
        return text
    if value is True:
        return "TRUE"
    if value is False:
        return "FALSE"
    return "FALSE"


cognitive_program_lifecycle_registry = CognitiveProgramLifecycleRegistry()

__all__ = [
    "CognitiveProgramLifecycle",
    "CognitiveProgramLifecycleRegistry",
    "cognitive_program_lifecycle_registry",
]
