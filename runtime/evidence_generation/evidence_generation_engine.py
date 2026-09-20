from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class EvidenceGenerationEngine:
    """Generates validation opportunities without granting evidence or truth."""

    GENERATED_BY = "EvidenceGenerationEngine"
    GOVERNANCE_STATE = "POTENTIAL_VALIDATION_OPPORTUNITY_ONLY"
    BOUNDARY = "GENERATED_TASKS_ARE_VALIDATION_OPPORTUNITIES_NOT_EVIDENCE"

    def __init__(
        self,
        generated_curriculum_path=(
            "runtime/evidence_generation/generated_curriculum"
        ),
    ):
        self.generated_curriculum_path = Path(generated_curriculum_path)

    def _term(self, value):
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _slug(self, *values):
        base = "__".join(
            self._term(value) for value in values if self._term(value)
        )
        digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
        label = base[:72].strip("_") or "validation_opportunity"
        return f"{label}__{digest}.json"

    def _plan_ready(self, economy_context):
        return (
            isinstance(economy_context, dict)
            and economy_context.get("evidence_acquisition_state")
            == "EVIDENCE_ACQUISITION_PLAN_READY"
            and (
                economy_context.get("evidence_acquisition_required_evidence")
                or economy_context.get("evidence_acquisition_validation_task")
            )
        )

    def _generated_domains(self, category, strategy, operation):
        domains = set()
        for value in (category, strategy, operation):
            term = self._term(value)
            if "source" in term or "consensus" in term:
                domains.add("source_diversity")
            if "color" in term or "replace_color" in term:
                domains.add("color")
            if "independent" in term:
                domains.add("independent_validation")
            if "ground" in term or "object" in term:
                domains.add("object_grounding")
        return sorted(domains or {"governed_validation"})

    def _example_task(self, operation):
        operation = self._term(operation)
        if operation == "replace_color":
            return {
                "train": [
                    {
                        "input": [[0, 1, 1], [0, 2, 2], [3, 3, 0]],
                        "output": [[6, 1, 1], [6, 2, 2], [3, 3, 0]],
                    }
                ],
                "test": [
                    {
                        "input": [[0, 4, 4], [0, 5, 5], [7, 7, 0]],
                        "output": [[6, 4, 4], [6, 5, 5], [7, 7, 0]],
                    }
                ],
            }
        return {
            "train": [
                {
                    "input": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    "output": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                }
            ],
            "test": [
                {
                    "input": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
                    "output": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
                }
            ],
        }

    def _metadata(self, economy_context, timestamp):
        required_evidence = self._term(
            economy_context.get("evidence_acquisition_required_evidence")
        )
        validation_task = self._term(
            economy_context.get("evidence_acquisition_validation_task")
        )
        strategy = self._term(
            economy_context.get("evidence_acquisition_tie_break_strategy")
        )
        category = self._term(
            economy_context.get("evidence_acquisition_required_category")
        )
        operation = self._term(
            economy_context.get("evidence_acquisition_target_operation")
        )
        target_candidate = (
            economy_context.get("evidence_acquisition_target_candidate")
            or "Not Available"
        )
        target_concepts = [
            value
            for value in [
                operation,
                strategy,
                category,
                "validation_opportunity",
                "source_consensus" if "source" in strategy else None,
                "cross_source_consensus" if "cross_source" in strategy else None,
            ]
            if value
        ]
        task_properties = [
            value
            for value in [
                validation_task,
                strategy,
                category,
                "generated_validation_opportunity",
            ]
            if value
        ]
        return {
            "generated_by": self.GENERATED_BY,
            "generated_reason": (
                "evidence_acquisition_plan_has_no_existing_curriculum_task"
            ),
            "required_evidence": [required_evidence] if required_evidence else [],
            "generation_timestamp": timestamp,
            "target_candidate": target_candidate,
            "target_capability": operation or "Not Available",
            "governance_state": self.GOVERNANCE_STATE,
            "generation_version": "1.0",
            "execution_count": 0,
            "validation_count": 0,
            "evidence_produced": False,
            "consumed_by_training_assistant": False,
            "evidence_opportunity_type": "POTENTIAL_VALIDATION_OPPORTUNITY",
            "constitutional_boundary": self.BOUNDARY,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "validation_authority": "SANDBOX_VALIDATION_ONLY",
            "target_concepts": target_concepts,
            "task_properties": task_properties,
            "evidence_targets": [required_evidence] if required_evidence else [],
            "validation_objective": validation_task or required_evidence,
            "primary_operation": operation,
            "target_domain": (
                "source_diversity" if "source" in strategy else "validation"
            ),
        }

    def _report(
        self,
        *,
        economy_context,
        generation_required,
        existing_tasks_found,
        generated_files=None,
        status="GENERATION_NOT_REQUIRED",
    ):
        generated_files = generated_files or []
        required_evidence = economy_context.get(
            "evidence_acquisition_required_evidence"
        )
        validation_task = economy_context.get(
            "evidence_acquisition_validation_task"
        )
        strategy = economy_context.get(
            "evidence_acquisition_tie_break_strategy"
        )
        category = economy_context.get(
            "evidence_acquisition_required_category"
        )
        operation = economy_context.get(
            "evidence_acquisition_target_operation"
        )
        return {
            "system": "evidence_generation_engine",
            "generation_required": bool(generation_required),
            "generation_trigger": (
                "evidence_acquisition_plan_without_existing_task"
                if generation_required
                else "none"
            ),
            "required_evidence": required_evidence or "Not Available",
            "required_validation_task": validation_task or "Not Available",
            "existing_tasks_found": bool(existing_tasks_found),
            "generated_tasks": len(generated_files),
            "generated_task_files": [str(path) for path in generated_files],
            "generated_curriculum_path": str(self.generated_curriculum_path),
            "generated_curriculum_size": len(
                list(self.generated_curriculum_path.glob("*.json"))
            )
            if self.generated_curriculum_path.exists()
            else 0,
            "generated_domains": self._generated_domains(
                category,
                strategy,
                operation,
            ),
            "generation_strategy": strategy or "Not Available",
            "generation_governance": self.GOVERNANCE_STATE,
            "training_assistant_queue_updated": bool(generated_files),
            "future_execution_ready": bool(generated_files),
            "generation_status": status,
            "constitutional_boundary": self.BOUNDARY,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "evidence_produced": False,
        }

    def generate_for_plan(self, economy_context, *, existing_tasks_found=False):
        economy_context = economy_context if isinstance(economy_context, dict) else {}
        generation_required = (
            self._plan_ready(economy_context) and not existing_tasks_found
        )
        if not generation_required:
            return self._report(
                economy_context=economy_context,
                generation_required=False,
                existing_tasks_found=existing_tasks_found,
            )

        required_evidence = economy_context.get(
            "evidence_acquisition_required_evidence"
        )
        validation_task = economy_context.get(
            "evidence_acquisition_validation_task"
        )
        operation = economy_context.get(
            "evidence_acquisition_target_operation"
        )
        target_candidate = economy_context.get(
            "evidence_acquisition_target_candidate"
        )
        filename = self._slug(
            required_evidence,
            validation_task,
            operation,
            target_candidate,
        )
        path = self.generated_curriculum_path / filename
        self.generated_curriculum_path.mkdir(parents=True, exist_ok=True)
        status = "GENERATED_VALIDATION_OPPORTUNITY"
        if path.exists():
            status = "GENERATED_TASK_ALREADY_AVAILABLE"
        else:
            timestamp = datetime.now(timezone.utc).isoformat()
            payload = self._example_task(operation)
            payload["nexryn_metadata"] = self._metadata(
                economy_context,
                timestamp,
            )
            temporary_path = path.with_suffix(f"{path.suffix}.tmp")
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2, ensure_ascii=True)
            temporary_path.replace(path)
        return self._report(
            economy_context=economy_context,
            generation_required=True,
            existing_tasks_found=False,
            generated_files=[path],
            status=status,
        )
