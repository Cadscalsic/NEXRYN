from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationCurriculum:
    identifier: str
    display_name: str
    version: str
    priority: int
    enabled: bool
    path: Path
    group_filter: str | None = None


class ValidationCurriculumRegistry:
    """Registry-driven search over governed validation curricula."""

    system_name = "validation_curriculum_registry"

    def __init__(self):
        self._curricula: dict[str, ValidationCurriculum] = {}

    def register_curriculum(
        self,
        *,
        identifier: str,
        display_name: str,
        version: str = "1.0",
        priority: int = 100,
        enabled: bool = True,
        path: str | Path,
        group_filter: str | None = None,
    ) -> None:
        self._curricula[str(identifier)] = ValidationCurriculum(
            identifier=str(identifier),
            display_name=str(display_name),
            version=str(version),
            priority=int(priority),
            enabled=bool(enabled),
            path=Path(path),
            group_filter=group_filter,
        )

    def register_default_academy(self, path: str | Path) -> None:
        path = Path(path)
        self.register_curriculum(
            identifier="elite_validation_academy",
            display_name="Elite Validation Academy",
            version="1.1",
            priority=100,
            enabled=True,
            path=path,
            group_filter=None,
        )

    def curricula(self) -> list[ValidationCurriculum]:
        return sorted(
            self._curricula.values(),
            key=lambda item: (-item.priority, item.identifier),
        )

    def search(self, plan: dict[str, Any]) -> dict[str, Any]:
        lifecycle = ["PLAN_PARSED", "CURRICULUM_SEARCH_STARTED"]
        reports = []
        matches = []
        loaded = 0
        enabled = [item for item in self.curricula() if item.enabled]
        disabled = [item for item in self.curricula() if not item.enabled]
        total_tasks = 0
        for curriculum in enabled:
            tasks, load_report = self._load_curriculum(curriculum)
            loaded += 1 if load_report.get("loaded") else 0
            total_tasks += len(tasks)
            reports.append(load_report)
            for task in tasks:
                match = self._match(plan, task, curriculum)
                if match["matching_score"] > 0:
                    matches.append(match)
        lifecycle.extend(["CURRICULUM_SEARCH_COMPLETED", "MATCHING_COMPLETED"])
        matches.sort(
            key=lambda item: (
                -float(item.get("matching_score", 0.0)),
                -int(item.get("curriculum_priority", 0)),
                str(item.get("task_id")),
            )
        )
        selected = matches[0] if matches else {}
        if selected:
            lifecycle.extend(["TASK_SELECTED", "WAITING_EXECUTION"])
        return {
            "system": self.system_name,
            "consumption_lifecycle": lifecycle,
            "registry_state": "READY",
            "registered_curricula": len(self._curricula),
            "registered_curriculum_ids": [
                curriculum.identifier for curriculum in self.curricula()
            ],
            "loaded_curricula": loaded,
            "enabled_curricula": len(enabled),
            "disabled_curricula": len(disabled),
            "disabled_curriculum_ids": [
                curriculum.identifier for curriculum in disabled
            ],
            "curricula_searched": len(enabled),
            "curriculum_reports": reports,
            "total_validation_tasks": total_tasks,
            "matching_tasks": len(matches),
            "matching_task_rows": matches[:10],
            "best_matching_task": selected.get("task_id", "Not Available"),
            "best_matching_task_name": selected.get("task_name", "Not Available"),
            "best_matching_curriculum": selected.get(
                "curriculum_display_name",
                "Not Available",
            ),
            "matching_score": selected.get("matching_score", 0.0),
            "matching_explanation": selected.get(
                "matching_explanation",
                "no_matching_validation_task",
            ),
            "selection_authority": "TRAINING_ASSISTANT",
            "selection_state": "WAITING_EXECUTION" if selected else "NO_MATCH",
            "waiting_execution": bool(selected),
            "generation_eligible": not bool(selected),
            "generation_invoked": False,
            "waiting_generator": not bool(selected),
            "selected_validation_task": selected.get("task_id", "Not Available"),
            "selected_validation_task_metadata": selected,
            "constitutional_boundary": (
                "TRAINING_ASSISTANT_SELECTION_PREPARES_VALIDATION_ONLY"
            ),
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "execution_authority": "NONE",
        }

    def _load_curriculum(
        self,
        curriculum: ValidationCurriculum,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        try:
            payload = json.loads(curriculum.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [], {
                "identifier": curriculum.identifier,
                "display_name": curriculum.display_name,
                "version": curriculum.version,
                "priority": curriculum.priority,
                "enabled": curriculum.enabled,
                "loaded": False,
                "load_failure": str(error),
                "task_count": 0,
                "supported_domains": [],
                "supported_operations": [],
                "supported_evidence": [],
            }
        raw_tasks = payload.get("tasks") if isinstance(payload, dict) else []
        tasks = []
        for raw_task in raw_tasks if isinstance(raw_tasks, list) else []:
            if not isinstance(raw_task, dict):
                continue
            if (
                curriculum.group_filter
                and raw_task.get("elite_group") != curriculum.group_filter
            ):
                continue
            tasks.append(self._normalize_task(raw_task, curriculum))
        return tasks, {
            "identifier": curriculum.identifier,
            "display_name": curriculum.display_name,
            "version": curriculum.version,
            "priority": curriculum.priority,
            "enabled": curriculum.enabled,
            "loaded": True,
            "task_count": len(tasks),
            "supported_domains": sorted({
                domain for task in tasks for domain in task["supported_domains"]
            }),
            "supported_operations": sorted({
                op for task in tasks for op in task["supported_operations"]
            }),
            "supported_evidence": sorted({
                evidence for task in tasks for evidence in task["supported_evidence"]
            }),
        }

    def _normalize_task(
        self,
        task: dict[str, Any],
        curriculum: ValidationCurriculum,
    ) -> dict[str, Any]:
        domains = self._terms(
            task.get("target_cognitive_domains")
            or task.get("cross_domain_participation")
            or task.get("cross_domain_requirement")
            or [task.get("target_domain")]
        )
        capability_targets = self._terms(
            task.get("capability_targets")
            or [
                task.get("target_capability"),
                task.get("target_cluster"),
            ]
        )
        evidence = self._terms([
            task.get("required_validation_evidence"),
            task.get("primary_evidence_category"),
            *(task.get("secondary_evidence_categories") or []),
        ])
        return {
            "task_id": self._term(task.get("task_id")),
            "task_name": self._term(task.get("task_name")),
            "curriculum_id": curriculum.identifier,
            "curriculum_display_name": curriculum.display_name,
            "curriculum_priority": curriculum.priority,
            "primary_evidence_category": self._term(
                task.get("primary_evidence_category")
                or task.get("required_validation_evidence")
            ),
            "secondary_evidence_categories": self._terms(
                task.get("secondary_evidence_categories")
            ),
            "supported_operations": sorted(set(capability_targets)),
            "supported_domains": sorted(set(domains)),
            "supported_evidence": sorted(set(evidence)),
            "required_grounding": self._terms(
                task.get("required_grounding")
                or [task.get("required_task_property")]
            ),
            "reasoning_patterns": self._terms([
                task.get("reasoning_complexity"),
                task.get("elite_group"),
                task.get("target_cluster"),
            ]),
            "capability_targets": capability_targets,
            "difficulty": self._term(
                task.get("validation_difficulty") or task.get("difficulty_level")
            ),
            "cross_domain": bool(domains and len(domains) > 1),
            "validation_contract": self._term(
                task.get("expected_validation_contract")
                or task.get("required_task_property")
            ),
            "operational_reuse_potential": self._term(
                task.get("operational_reuse_potential")
            ),
            "raw_task": task,
        }

    def _match(
        self,
        plan: dict[str, Any],
        task: dict[str, Any],
        curriculum: ValidationCurriculum,
    ) -> dict[str, Any]:
        required_evidence = self._term(plan.get("required_evidence"))
        required_category = self._term(plan.get("required_evidence_category"))
        validation_task = self._term(plan.get("required_validation_task"))
        operation = self._term(plan.get("target_operation"))
        strategy = self._term(plan.get("tie_break_strategy"))
        score = 0.0
        reasons = []
        task_evidence = {
            self._norm(item) for item in task.get("supported_evidence", [])
        }
        task_ops = {
            self._norm(item) for item in task.get("supported_operations", [])
        }
        task_grounding = {
            self._norm(item) for item in task.get("required_grounding", [])
        }
        task_patterns = {
            self._norm(item) for item in task.get("reasoning_patterns", [])
        }
        contract = self._norm(task.get("validation_contract"))
        if self._norm(required_evidence) in task_evidence:
            score += 40
            reasons.append("primary_required_evidence_match")
        if self._norm(required_category) in task_evidence:
            score += 25
            reasons.append("required_evidence_category_match")
        if self._norm(operation) in task_ops:
            score += 20
            reasons.append("target_operation_match")
        if self._norm(strategy) in task_patterns or self._norm(strategy) in task_grounding:
            score += 10
            reasons.append("tie_break_strategy_match")
        if self._norm(validation_task) in contract or self._norm(validation_task) in task_grounding:
            score += 10
            reasons.append("required_validation_task_contract_match")
        if "cross_source" in self._norm(strategy) and (
            "cross_source" in contract
            or any("cross_source" in item for item in task_evidence | task_grounding)
        ):
            score += 15
            reasons.append("cross_source_compatibility")
        if task.get("cross_domain"):
            score += 5
            reasons.append("cross_domain_usefulness")
        if task.get("operational_reuse_potential") in {"high", "medium"}:
            score += 3
            reasons.append("operational_reuse_signal")
        return {
            **{key: value for key, value in task.items() if key != "raw_task"},
            "matching_score": round(score, 4),
            "matching_reasons": reasons,
            "matching_explanation": (
                ", ".join(reasons) if reasons else "metadata_not_compatible"
            ),
            "plan_id": plan.get("plan_id"),
            "plan_required_evidence": required_evidence,
            "plan_required_evidence_category": required_category,
            "plan_target_operation": operation,
            "plan_tie_break_strategy": strategy,
            "selection_authority": "TRAINING_ASSISTANT",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "execution_authority": "NONE",
            "curriculum_priority": curriculum.priority,
        }

    def _term(self, value: Any) -> str:
        text = str(value or "").strip()
        return text if text else "Not Available"

    def _terms(self, values: Any) -> list[str]:
        if values is None:
            return []
        if isinstance(values, (str, int, float)):
            values = [values]
        return [
            str(item).strip()
            for item in values
            if str(item or "").strip()
        ]

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower()
