from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

from runtime.execution.execution_adaptation_engine import ExecutionAdaptationEngine
from runtime.execution.execution_feedback_engine import ExecutionFeedbackEngine
from runtime.execution.execution_memory import ExecutionMemory
from runtime.execution.localized_execution_planner import LocalizedExecutionPlanner
from runtime.execution.object_grounding_engine import ObjectGroundingEngine
from runtime.execution.primitive_selector import PrimitiveSelector
from runtime.execution.program_compiler import ProgramCompiler
from runtime.execution.program_synthesis_engine import ProgramSynthesisEngine
from runtime.execution.program_validator import ProgramValidator
from runtime.execution.residual_localization_engine import ResidualLocalizationEngine
from runtime.execution.residual_repair_engine import ResidualRepairEngine
from runtime.security.learned_object_execution_authority import (
    LearnedObjectExecutionGrantAuthority,
)
from runtime.reporting.natural_production_handoff import (
    natural_production_handoff_observer,
)


class ExecutableIntelligenceEngine:
    """Governed bridge from validated semantic knowledge to executable candidates."""

    def __init__(
        self,
        *,
        object_grounder: ObjectGroundingEngine | None = None,
        planner: LocalizedExecutionPlanner | None = None,
        primitive_selector: PrimitiveSelector | None = None,
        synthesizer: ProgramSynthesisEngine | None = None,
        compiler: ProgramCompiler | None = None,
        validator: ProgramValidator | None = None,
        residual_localizer: ResidualLocalizationEngine | None = None,
        repair_engine: ResidualRepairEngine | None = None,
        adaptation_engine: ExecutionAdaptationEngine | None = None,
        memory: ExecutionMemory | None = None,
        feedback_engine: ExecutionFeedbackEngine | None = None,
        grant_authority: LearnedObjectExecutionGrantAuthority | None = None,
    ) -> None:
        self.object_grounder = object_grounder or ObjectGroundingEngine()
        self.planner = planner or LocalizedExecutionPlanner()
        self.primitive_selector = primitive_selector or PrimitiveSelector()
        self.synthesizer = synthesizer or ProgramSynthesisEngine()
        self.compiler = compiler or ProgramCompiler()
        self.validator = validator or ProgramValidator()
        self.residual_localizer = residual_localizer or ResidualLocalizationEngine()
        self.repair_engine = repair_engine or ResidualRepairEngine()
        self.adaptation_engine = adaptation_engine or ExecutionAdaptationEngine()
        self.memory = memory or ExecutionMemory()
        self.feedback_engine = feedback_engine or ExecutionFeedbackEngine()
        self.grant_authority = grant_authority or LearnedObjectExecutionGrantAuthority()
        self._consumed_production_grants: set[str] = set()
        self.underlying_executor_call_count = 0

    def run(
        self,
        *,
        semantic_intent: str,
        operation: str,
        input_grid: list[list[int]] | None = None,
        target_grid: list[list[int]] | None = None,
        predicted_output: list[list[int]] | None = None,
        hypotheses: list[dict[str, Any]] | None = None,
        validated_candidate: dict[str, Any] | None = None,
        arena_execution_recommendation: dict[str, Any] | None = None,
        candidate_qualification: dict[str, Any] | None = None,
        execution_grant: dict[str, Any] | None = None,
        budget_admission: dict[str, Any] | None = None,
        production_execution_request: dict[str, Any] | None = None,
        counterfactual_revision: dict[str, Any] | None = None,
        governance_context: dict[str, Any] | None = None,
        execution_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        arena_recommendation = (
            arena_execution_recommendation
            if isinstance(arena_execution_recommendation, dict)
            else {}
        )
        probe_candidate = (
            arena_recommendation.get("validation_probe_candidate")
            if isinstance(arena_recommendation.get("validation_probe_candidate"), dict)
            else {}
        )
        selected_candidate = (
            arena_recommendation.get("selected_candidate")
            if isinstance(arena_recommendation.get("selected_candidate"), dict)
            else {}
        )
        probe_grounding_context = (
            arena_recommendation.get("validation_probe_grounding_context")
            if isinstance(
                arena_recommendation.get("validation_probe_grounding_context"),
                dict,
            )
            else {}
        )
        grounding_context_received = bool(probe_grounding_context)
        grounding_payload = self._grounding_context_payload_diagnostic(
            probe_grounding_context,
        )
        effective_input_grid = (
            input_grid
            if self._grid_available(input_grid)
            else probe_grounding_context.get("input_grid")
        )
        effective_target_grid = (
            target_grid
            if self._grid_available(target_grid)
            else probe_grounding_context.get("target_grid")
        )
        effective_predicted_output = (
            predicted_output
            if self._grid_available(predicted_output)
            else probe_grounding_context.get("predicted_output")
        )
        candidate = (
            validated_candidate
            if isinstance(validated_candidate, dict)
            else selected_candidate
            if selected_candidate
            else probe_candidate
            if probe_candidate
            else {"operation": operation}
        )
        validation_probe_consumed = bool(
            probe_candidate and not selected_candidate and candidate is probe_candidate
        )
        consumed_candidate_identity = self._candidate_identity(candidate)
        operation_name = str(candidate.get("operation") or operation or semantic_intent)
        semantic_intent_name = str(
            semantic_intent
            or candidate.get("intent")
            or candidate.get("semantic_intent")
            or operation_name
        )
        grounding = self.object_grounder.ground(
            effective_input_grid,
            semantic_intent=semantic_intent_name,
            candidate=candidate,
        )
        plan = self.planner.plan(operation_name, grounding, semantic_intent=semantic_intent_name)
        primitives = self.primitive_selector.select(operation_name, plan, semantic_intent=semantic_intent_name)
        synthesis = self.synthesizer.synthesize(
            semantic_intent=semantic_intent_name,
            hypotheses=hypotheses or [],
            validated_candidate=candidate,
            counterfactual_revision=counterfactual_revision,
            execution_plan=plan,
            primitive_selection=primitives,
        )
        compiled = self.compiler.compile(
            semantic_intent=semantic_intent_name,
            primitive_sequence=synthesis.get("primitive_sequence"),
            execution_plan=plan,
            synthesized_program=synthesis,
        )
        validation = self.validator.validate(
            compiled,
            grounding_report=grounding,
            governance_context=governance_context,
        )
        residual = self.residual_localizer.localize(
            effective_predicted_output
            if effective_predicted_output is not None
            else effective_input_grid,
            effective_target_grid
            if effective_target_grid is not None
            else effective_input_grid,
            program=compiled.get("compiled_program"),
            grounding_report=grounding,
        )
        repairs = self.repair_engine.repair(
            residual,
            program=compiled.get("compiled_program"),
        )
        adaptation = self.adaptation_engine.adapt(
            compiled.get("compiled_program"),
            repairs,
        )
        memory_report = self.memory.record_execution(
            program=adaptation.get("adapted_program") or compiled.get("compiled_program"),
            validation=validation,
            residual=residual,
            repair=repairs,
            grounding=grounding,
        )
        feedback = self.feedback_engine.feedback(
            execution_result=validation,
            residual_report=residual,
            repair_report=repairs,
            adaptation_report=adaptation,
        )
        production_execution = self.execute_production(
            candidate=candidate,
            compiled_program=adaptation.get("adapted_program")
            or compiled.get("compiled_program"),
            validation=validation,
            qualification=candidate_qualification,
            arena_selection=arena_recommendation,
            execution_grant=execution_grant,
            budget_admission=budget_admission,
            production_execution_request=production_execution_request,
            governance_state=governance_context,
            execution_context=execution_context,
            input_grid=effective_input_grid,
            requested_operation=operation_name,
        )
        production_outcome_feedback = self.feedback_engine.process_production_outcome(
            production_execution,
            storage_root=(
                execution_context.get("outcome_feedback_storage_root")
                if isinstance(execution_context, dict)
                else None
            ),
            current_run_id=(
                execution_context.get("run_id")
                if isinstance(execution_context, dict)
                else None
            ),
            evaluation_result=(
                execution_context.get("production_outcome_evaluation")
                if isinstance(execution_context, dict)
                and isinstance(
                    execution_context.get("production_outcome_evaluation"),
                    dict,
                )
                else None
            ),
        )
        report = self._report(
            grounding=grounding,
            plan=plan,
            primitives=primitives,
            synthesis=synthesis,
            compiled=compiled,
            validation=validation,
            residual=residual,
            repairs=repairs,
            adaptation=adaptation,
            memory=memory_report,
            feedback=feedback,
            production_execution=production_execution,
            production_outcome_feedback=production_outcome_feedback,
            validation_probe_consumed=validation_probe_consumed,
            consumed_candidate_identity=consumed_candidate_identity,
            arena_recommendation=arena_recommendation,
            grounding_trace={
                "validation_probe_grounding_context_received": (
                    grounding_context_received
                ),
                **grounding_payload,
                "validation_probe_grounding_context_input_available": (
                    self._grid_available(probe_grounding_context.get("input_grid"))
                ),
                "validation_probe_grounding_context_target_available": (
                    self._grid_available(probe_grounding_context.get("target_grid"))
                ),
                "validation_probe_grounding_context_prediction_available": (
                    self._grid_available(
                        probe_grounding_context.get("predicted_output")
                    )
                ),
                "object_grounding_input_source": (
                    "runtime_input_grid"
                    if self._grid_available(input_grid)
                    else "validation_probe_grounding_context"
                    if self._grid_available(probe_grounding_context.get("input_grid"))
                    else "missing_input_grid"
                ),
                "object_grounding_input_available": (
                    self._grid_available(effective_input_grid)
                ),
            },
        )
        probe_validation = report.get("validation_probe_evidence_acceptance_state")
        final_execution_mode = (
            "production"
            if production_execution.get("real_execution_performed") is True
            else "production_denied"
            if production_execution.get("production_execution_requested") is True
            else
            "sandbox_validation_only"
            if validation_probe_consumed and validation.get("validation_success")
            else "sandbox"
            if validation.get("validation_success")
            else "blocked"
        )
        final_selection_state = (
            "PRODUCTION_EXECUTED"
            if production_execution.get("real_execution_performed") is True
            else "PRODUCTION_EXECUTION_DENIED"
            if production_execution.get("production_execution_requested") is True
            else
            "VALIDATION_PROBE_VALIDATED"
            if validation_probe_consumed and validation.get("validation_success")
            else "VALIDATED_WITH_REPAIR"
            if validation.get("validation_success")
            else "BLOCKED"
        )
        return {
            "OBJECT_GROUNDING_REPORT": grounding,
            "LOCALIZED_EXECUTION_PLAN": plan,
            "PRIMITIVE_SELECTION_REPORT": primitives,
            "PROGRAM_SYNTHESIS_REPORT": synthesis,
            "PROGRAM_COMPILATION_REPORT": compiled,
            "PROGRAM_VALIDATION_REPORT": validation,
            "RESIDUAL_LOCALIZATION_REPORT": residual,
            "RESIDUAL_REPAIR_REPORT": repairs,
            "EXECUTION_ADAPTATION_REPORT": adaptation,
            "EXECUTION_MEMORY_REPORT": memory_report,
            "EXECUTION_FEEDBACK_REPORT": feedback,
            "EXECUTABLE_INTELLIGENCE_REPORT": report,
            "final_execution_recommendation": {
                "selected_candidate": adaptation.get("adapted_program") or compiled.get("compiled_program"),
                "source_candidate_identity": consumed_candidate_identity,
                "selection_state": final_selection_state,
                "execution_mode": final_execution_mode,
                "validation_probe_consumed": validation_probe_consumed,
                "validation_probe_authority": (
                    "SANDBOX_VALIDATION_ONLY"
                    if validation_probe_consumed
                    else "NONE"
                ),
                "validation_probe_evidence_acceptance_state": (
                    probe_validation
                    if validation_probe_consumed
                    else "NO_VALIDATION_PROBE"
                ),
                "selection_evidence": {
                    "validation": validation,
                    "residual": residual,
                    "repairs": repairs,
                    "production_execution": production_execution,
                },
            },
            "PRODUCTION_EXECUTION_RESULT": production_execution,
            "NATURAL_PRODUCTION_HANDOFF_TRACE": (
                production_execution.get("NATURAL_PRODUCTION_HANDOFF_TRACE", {})
            ),
            "PRODUCTION_OUTCOME_FEEDBACK_REPORT": production_outcome_feedback,
        }

    def execute_production(
        self,
        *,
        candidate: Mapping[str, Any] | None,
        compiled_program: Mapping[str, Any] | None,
        validation: Mapping[str, Any] | None,
        qualification: Mapping[str, Any] | None,
        arena_selection: Mapping[str, Any] | None,
        execution_grant: Mapping[str, Any] | None,
        budget_admission: Mapping[str, Any] | None,
        production_execution_request: Mapping[str, Any] | None = None,
        governance_state: Mapping[str, Any] | None = None,
        execution_context: Mapping[str, Any] | None = None,
        input_grid: list[list[int]] | None = None,
        requested_operation: str | None = None,
    ) -> dict[str, Any]:
        candidate_map = dict(candidate or {})
        request = self._production_consumption_request(
            candidate=candidate_map,
            arena_selection=dict(arena_selection or {}),
            execution_grant=execution_grant,
            budget_admission=budget_admission,
            production_execution_request=production_execution_request,
            governance_state=governance_state,
            execution_context=execution_context,
            requested_operation=requested_operation,
        )
        if not request["production_execution_requested"]:
            denied = self._production_denied(
                "PRODUCTION_EXECUTION_NOT_REQUESTED",
                request=request,
            )
            return self._with_natural_handoff_trace(
                denied,
                candidate=candidate_map,
                validation=dict(validation or {}),
                qualification=dict(qualification or {}),
                arena_selection=dict(arena_selection or {}),
                execution_grant=execution_grant,
                budget_admission=budget_admission,
                execution_context=execution_context,
            )

        preconditions = self._production_preconditions(
            candidate=candidate_map,
            qualification=dict(qualification or {}),
            arena_selection=dict(arena_selection or {}),
            validation=dict(validation or {}),
            request=request,
        )
        if preconditions["precondition_state"] != "SATISFIED":
            denied = self._production_denied(
                preconditions["denial_reason"],
                request=request,
                preconditions=preconditions,
            )
            return self._with_natural_handoff_trace(
                denied,
                candidate=candidate_map,
                validation=dict(validation or {}),
                qualification=dict(qualification or {}),
                arena_selection=dict(arena_selection or {}),
                execution_grant=execution_grant,
                budget_admission=budget_admission,
                execution_context=execution_context,
            )

        grant_id = str(dict(execution_grant or {}).get("grant_id") or "")
        if grant_id in self._consumed_production_grants:
            denied = self._production_denied(
                "DENIED_GRANT_ALREADY_CONSUMED",
                request=request,
                preconditions=preconditions,
            )
            return self._with_natural_handoff_trace(
                denied,
                candidate=candidate_map,
                validation=dict(validation or {}),
                qualification=dict(qualification or {}),
                arena_selection=dict(arena_selection or {}),
                execution_grant=execution_grant,
                budget_admission=budget_admission,
                execution_context=execution_context,
            )

        consumption = self.grant_authority.validate_for_consumption(
            execution_grant,
            run_id=request["run_id"],
            candidate_id=request["candidate_id"],
            learned_object_id=request["learned_object_id"],
            requested_operation=request["requested_operation"],
            budget_admission=dict(budget_admission or {}),
        )
        if consumption.get("production_execution_authorized") is not True:
            denied = self._production_denied(
                str(consumption.get("denial_reason") or "GRANT_INVALID"),
                request=request,
                preconditions=preconditions,
                grant_consumption=consumption,
            )
            return self._with_natural_handoff_trace(
                denied,
                candidate=candidate_map,
                validation=dict(validation or {}),
                qualification=dict(qualification or {}),
                arena_selection=dict(arena_selection or {}),
                execution_grant=execution_grant,
                budget_admission=budget_admission,
                execution_context=execution_context,
            )

        integrity = self._execution_integrity(
            candidate=candidate_map,
            compiled_program=dict(compiled_program or {}),
            grant=dict(execution_grant or {}),
            budget_admission=dict(budget_admission or {}),
            request=request,
            qualification=dict(qualification or {}),
            arena_selection=dict(arena_selection or {}),
            validation=dict(validation or {}),
            governance_state=dict(governance_state or {}),
        )
        if integrity["execution_integrity_state"] != "VALID":
            denied = self._production_denied(
                integrity["denial_reason"],
                request=request,
                preconditions=preconditions,
                grant_consumption=consumption,
                integrity=integrity,
            )
            return self._with_natural_handoff_trace(
                denied,
                candidate=candidate_map,
                validation=dict(validation or {}),
                qualification=dict(qualification or {}),
                arena_selection=dict(arena_selection or {}),
                execution_grant=execution_grant,
                budget_admission=budget_admission,
                execution_context=execution_context,
            )

        self._consumed_production_grants.add(grant_id)
        consumed_grant = self.grant_authority.consume_grant(execution_grant)
        started_at = str(datetime.utcnow())
        operation_result = self._invoke_underlying_production_operation(
            compiled_program=dict(compiled_program or {}),
            input_grid=input_grid,
            request=request,
        )
        executable_payload = self._executable_payload(
            compiled_program=dict(compiled_program or {}),
            request=request,
            candidate=candidate_map,
        )
        completed_at = str(datetime.utcnow())
        execution_result_id = self._stable_id(
            "production_execution_result",
            {
                "grant_id": grant_id,
                "run_id": request["run_id"],
                "candidate_id": request["candidate_id"],
                "learned_object_id": request["learned_object_id"],
                "operation": request["requested_operation"],
                "started_at": started_at,
                "result": operation_result,
            },
        )
        provenance = self._outcome_provenance(
            request=request,
            candidate=candidate_map,
            grant=dict(execution_grant or {}),
            consumed_grant=consumed_grant,
            budget_admission=dict(budget_admission or {}),
            qualification=dict(qualification or {}),
            arena_selection=dict(arena_selection or {}),
            validation=dict(validation or {}),
            execution_result_id=execution_result_id,
            actual_operation=operation_result.get("actual_operation"),
        )
        receipt = self._execution_receipt(
            request=request,
            grant=dict(execution_grant or {}),
            budget_admission=dict(budget_admission or {}),
            execution_result_id=execution_result_id,
            authorization_result="AUTHORIZED",
            consumption_state="CONSUMED",
        )
        production = {
            "execution_result_id": execution_result_id,
            "execution_state": "PRODUCTION_EXECUTED",
            "real_execution_performed": True,
            "production_execution_requested": True,
            "production_admission_state": "AUTHORIZED",
            "run_id": request["run_id"],
            "candidate_id": request["candidate_id"],
            "learned_object_id": request["learned_object_id"],
            "grant_id": grant_id,
            "grant_state_after": consumed_grant.get("grant_state"),
            "grant_consumption_state": "CONSUMED",
            "operation": request["requested_operation"],
            "budget_context": dict(budget_admission or {}),
            "executor_identity": "runtime.execution.executable_intelligence_engine.ExecutableIntelligenceEngine.execute_production",
            "started_at": started_at,
            "completed_at": completed_at,
            "result": operation_result,
            "executable_payload": executable_payload,
            "underlying_executor_called": True,
            "underlying_executor_call_count": self.underlying_executor_call_count,
            "grant_identity": consumption,
            "execution_integrity": integrity,
            "outcome_provenance": provenance,
            "outcome_provenance_state": provenance["outcome_provenance_state"],
            "execution_receipt": receipt,
            "execution_receipt_state": "LEARNED_OBJECT_EXECUTION_RECEIPT_RECORDED",
            "reusable_execution_authority": False,
        }
        return self._with_natural_handoff_trace(
            production,
            candidate=candidate_map,
            validation=dict(validation or {}),
            qualification=dict(qualification or {}),
            arena_selection=dict(arena_selection or {}),
            execution_grant=consumed_grant,
            budget_admission=budget_admission,
            execution_context=execution_context,
        )

    def _production_consumption_request(
        self,
        *,
        candidate: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        execution_grant: Mapping[str, Any] | None,
        budget_admission: Mapping[str, Any] | None,
        production_execution_request: Mapping[str, Any] | None,
        governance_state: Mapping[str, Any] | None,
        execution_context: Mapping[str, Any] | None,
        requested_operation: str | None,
    ) -> dict[str, Any]:
        explicit = dict(production_execution_request or {})
        selected = arena_selection.get("selected_candidate")
        selected = selected if isinstance(selected, Mapping) else {}
        identity = self._candidate_identity(candidate or selected)
        context = dict(execution_context or {})
        grant = dict(execution_grant or {})
        operation_scope = (
            grant.get("execution_operation_scope")
            if isinstance(grant.get("execution_operation_scope"), Mapping)
            else {}
        )
        run_id = str(
            explicit.get("run_id")
            or context.get("run_id")
            or grant.get("run_id")
            or candidate.get("target_run_id")
            or "current_run"
        )
        operation = str(
            explicit.get("requested_operation")
            or requested_operation
            or candidate.get("operation")
            or operation_scope.get("operation")
            or ""
        )
        requested_scope = dict(
            explicit.get("requested_scope")
            if isinstance(explicit.get("requested_scope"), Mapping)
            else operation_scope
        )
        return {
            "run_id": run_id,
            "candidate_id": str(
                explicit.get("candidate_id")
                or candidate.get("candidate_id")
                or identity.get("candidate_id")
                or ""
            ),
            "learned_object_id": str(
                explicit.get("learned_object_id")
                or candidate.get("learned_object_id")
                or candidate.get("source_learned_object_id")
                or identity.get("learned_object_id")
                or ""
            ),
            "requested_operation": operation,
            "requested_scope": requested_scope,
            "execution_grant_present": isinstance(execution_grant, Mapping),
            "budget_admission_present": isinstance(budget_admission, Mapping),
            "budget_admission": dict(budget_admission or {}),
            "governance_state": dict(governance_state or {}),
            "execution_context": context,
            "production_execution_requested": bool(
                explicit.get("production_execution_requested") is True
                or context.get("production_execution_requested") is True
                or arena_selection.get("execution_mode") == "real"
            ),
        }

    def _production_preconditions(
        self,
        *,
        candidate: Mapping[str, Any],
        qualification: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        validation: Mapping[str, Any],
        request: Mapping[str, Any],
    ) -> dict[str, Any]:
        selected = arena_selection.get("selected_candidate")
        selected = selected if isinstance(selected, Mapping) else {}
        selected_candidate_id = (
            arena_selection.get("selected_candidate_id")
            or selected.get("candidate_id")
        )
        checks = {
            "candidate_identity_present": bool(
                request.get("candidate_id") and request.get("learned_object_id")
            ),
            "sandbox_validation_passed": bool(
                validation.get("validation_success") is True
                or validation.get("validation_state")
                in {"PASSED", "SANDBOX_VALIDATION_PASSED", "ACCEPTED"}
            ),
            "qualification_present": bool(qualification),
            "qualification_passed": qualification.get("qualification_state")
            in {"QUALIFIED", "EXECUTION_ELIGIBLE"},
            "arena_selection_present": bool(arena_selection),
            "arena_winner_selected": arena_selection.get("selection_state")
            in {"WINNER_SELECTED", "EXECUTION_ELIGIBLE"},
            "candidate_is_arena_winner": str(selected_candidate_id or "")
            == str(request.get("candidate_id") or ""),
            "sandbox_authority_not_used_for_production": arena_selection.get(
                "validation_probe_authority"
            )
            != "SANDBOX_VALIDATION_ONLY"
            or bool(selected_candidate_id),
            "execution_grant_present": request.get("execution_grant_present") is True,
            "budget_admission_present": request.get("budget_admission_present") is True,
        }
        denial_order = [
            ("candidate_identity_present", "CANDIDATE_IDENTITY_MISSING"),
            ("sandbox_validation_passed", "SANDBOX_VALIDATION_NOT_PASSED"),
            ("qualification_present", "QUALIFICATION_MISSING"),
            ("qualification_passed", "QUALIFICATION_FAILED"),
            ("arena_selection_present", "ARENA_SELECTION_MISSING"),
            ("arena_winner_selected", "ARENA_NO_EXECUTABLE_WINNER"),
            ("candidate_is_arena_winner", "CANDIDATE_NOT_ARENA_WINNER"),
            (
                "sandbox_authority_not_used_for_production",
                "SANDBOX_RESULT_PRESENTED_AS_PRODUCTION_AUTHORITY",
            ),
            ("execution_grant_present", "GRANT_MISSING"),
            ("budget_admission_present", "BUDGET_ADMISSION_MISSING"),
        ]
        for key, reason in denial_order:
            if checks.get(key) is not True:
                return {
                    "precondition_state": "BLOCKED",
                    "checks": checks,
                    "denial_reason": reason,
                }
        return {
            "precondition_state": "SATISFIED",
            "checks": checks,
            "denial_reason": "NONE",
        }

    def _execution_integrity(
        self,
        *,
        candidate: Mapping[str, Any],
        compiled_program: Mapping[str, Any],
        grant: Mapping[str, Any],
        budget_admission: Mapping[str, Any],
        request: Mapping[str, Any],
        qualification: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        validation: Mapping[str, Any],
        governance_state: Mapping[str, Any],
    ) -> dict[str, Any]:
        candidate_fingerprint = self._candidate_fingerprint(candidate)
        authorized_fingerprint = grant.get("candidate_fingerprint")
        program_fingerprint = self._program_fingerprint(compiled_program)
        grant_scope = (
            grant.get("execution_operation_scope")
            if isinstance(grant.get("execution_operation_scope"), Mapping)
            else {}
        )
        authorized_program_fingerprint = (
            grant.get("program_fingerprint")
            or grant_scope.get("program_fingerprint")
        )
        blocking_governance = [
            key
            for key, value in governance_state.items()
            if value in {False, "BLOCK", "BLOCKED", "FAIL", "FAILED", "REVOKED"}
        ]
        budget_state = str(
            budget_admission.get("runtime_budget_state")
            or budget_admission.get("budget_admission_state")
            or budget_admission.get("route_budget_enforcement_state")
            or ""
        )
        requested_scope = request.get("requested_scope")
        checks = {
            "source_provenance_present": bool(
                candidate.get("canonical_provenance")
                or grant.get("canonical_provenance")
            ),
            "arena_selection_identity_valid": bool(
                not grant.get("arena_selection_identity")
                or grant.get("arena_selection_identity")
                == self._identity_value(arena_selection, "arena_selection")
            ),
            "qualification_identity_valid": bool(
                not grant.get("qualification_identity")
                or grant.get("qualification_identity")
                == self._identity_value(qualification, "qualification")
            ),
            "sandbox_validation_identity_valid": bool(
                not grant.get("validation_identity")
                or not self._explicit_identity_value(validation, "validation")
                or grant.get("validation_identity")
                == self._identity_value(validation, "validation")
            ),
            "candidate_fingerprint_valid": (
                not authorized_fingerprint
                or authorized_fingerprint == candidate_fingerprint
            ),
            "program_fingerprint_valid": (
                not authorized_program_fingerprint
                or authorized_program_fingerprint == program_fingerprint
            ),
            "authority_still_valid": bool(
                grant.get("grant_state") == "ISSUED"
                and grant.get("revoked") is not True
                and grant.get("persistent") is False
                and grant.get("transferable") is False
                and grant.get("authority") == "EXECUTION"
                and grant.get("scope") == "CURRENT_RUN_ONLY"
            ),
            "budget_still_valid": bool(
                budget_state
                in {
                    "RUNTIME_BUDGET_FINALIZED",
                    "ROUTE_BUDGET_ADMITTED",
                    "BUDGET_ADMITTED",
                }
                and budget_admission.get("realized_overrun_state")
                != "REALIZED_OVERRUN"
                and budget_admission.get("violation_reason") in {None, "", "NONE"}
            ),
            "governance_still_valid": not blocking_governance,
            "operation_binding_valid": str(grant_scope.get("operation") or "")
            == str(request.get("requested_operation") or ""),
            "scope_binding_valid": self._scope_permits(grant_scope, requested_scope),
            "run_binding_valid": str(grant.get("run_id") or "")
            == str(request.get("run_id") or ""),
        }
        failed = [key for key, value in checks.items() if value is not True]
        denial_reason = "NONE"
        if "source_provenance_present" in failed:
            denial_reason = "SOURCE_PROVENANCE_MISSING"
        elif "arena_selection_identity_valid" in failed:
            denial_reason = "ARENA_SELECTION_IDENTITY_MISMATCH"
        elif "qualification_identity_valid" in failed:
            denial_reason = "QUALIFICATION_IDENTITY_MISMATCH"
        elif "sandbox_validation_identity_valid" in failed:
            denial_reason = "SANDBOX_VALIDATION_IDENTITY_MISMATCH"
        elif "candidate_fingerprint_valid" in failed:
            denial_reason = "CANDIDATE_MUTATED_AFTER_GRANT"
        elif "program_fingerprint_valid" in failed:
            denial_reason = "PROGRAM_FINGERPRINT_CHANGED"
        elif "governance_still_valid" in failed:
            denial_reason = "GOVERNANCE_BLOCKED_AFTER_GRANT"
        elif failed:
            denial_reason = failed[0].upper()
        return {
            "execution_integrity_state": "VALID" if not failed else "INVALID",
            **checks,
            "candidate_fingerprint": candidate_fingerprint,
            "program_fingerprint": program_fingerprint,
            "denial_reason": denial_reason,
        }

    def _invoke_underlying_production_operation(
        self,
        *,
        compiled_program: Mapping[str, Any],
        input_grid: list[list[int]] | None,
        request: Mapping[str, Any],
    ) -> dict[str, Any]:
        self.underlying_executor_call_count += 1
        result_grid = deepcopy(input_grid)
        steps = compiled_program.get("steps")
        steps = steps if isinstance(steps, list) else []
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            operation = step.get("operation") or request.get("requested_operation")
            if operation == "replace_color" and isinstance(result_grid, list):
                mapping = step.get("parameters", {}).get("color_mapping", {})
                mapping = mapping if isinstance(mapping, Mapping) else {}
                result_grid = [
                    [
                        mapping.get(cell, mapping.get(str(cell), cell))
                        for cell in row
                    ]
                    for row in result_grid
                ]
        return {
            "actual_operation": request.get("requested_operation"),
            "output_grid": result_grid,
            "operation_call_count": 1,
        }

    def _executable_payload(
        self,
        *,
        compiled_program: Mapping[str, Any],
        request: Mapping[str, Any],
        candidate: Mapping[str, Any],
    ) -> dict[str, Any]:
        steps = compiled_program.get("steps")
        steps = steps if isinstance(steps, list) else []
        normalized_steps = []
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            operation = step.get("operation") or step.get("primitive") or step.get("operator")
            if not operation:
                continue
            parameters = step.get("parameters") if isinstance(step.get("parameters"), Mapping) else {}
            normalized_steps.append({
                "operation": str(operation),
                "parameters": dict(parameters),
                "parameter_provenance": {
                    key: "ORIGINAL_EXECUTION"
                    for key in sorted(str(item) for item in parameters)
                },
            })
        payload = {
            "operation": request.get("requested_operation"),
            "steps": normalized_steps,
            "source_candidate_id": request.get("candidate_id"),
            "source_learned_object_id": request.get("learned_object_id"),
            "parameter_provenance_state": (
                "PARAMETERS_PRESERVED_FROM_EXECUTION_INPUT"
                if normalized_steps
                else "NO_EXECUTABLE_PARAMETERS_OBSERVED"
            ),
            "authority": "LEARNING_DATA",
            "execution_authority": "NONE",
            "reusable_execution_authority": False,
        }
        payload["executable_payload_fingerprint"] = self._stable_id(
            "executable_payload",
            {
                "operation": payload["operation"],
                "steps": normalized_steps,
                "candidate_id": candidate.get("candidate_id"),
            },
        )
        return payload

    def _production_denied(
        self,
        reason: str,
        *,
        request: Mapping[str, Any],
        preconditions: Mapping[str, Any] | None = None,
        grant_consumption: Mapping[str, Any] | None = None,
        integrity: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "execution_result_id": None,
            "execution_state": "PRODUCTION_EXECUTION_DENIED",
            "production_admission_state": "DENIED",
            "production_execution_requested": bool(
                request.get("production_execution_requested")
            ),
            "real_execution_performed": False,
            "run_id": request.get("run_id"),
            "candidate_id": request.get("candidate_id"),
            "learned_object_id": request.get("learned_object_id"),
            "grant_id": (
                grant_consumption.get("grant_id")
                if isinstance(grant_consumption, Mapping)
                else None
            ),
            "grant_consumption_state": (
                grant_consumption.get("consumption_state")
                if isinstance(grant_consumption, Mapping)
                else "NOT_CONSUMED"
            ),
            "denial_reason": reason,
            "budget_context": request.get("budget_admission", {}),
            "underlying_executor_called": False,
            "underlying_executor_call_count": self.underlying_executor_call_count,
            "preconditions": dict(preconditions or {}),
            "grant_identity": dict(grant_consumption or {}),
            "execution_integrity": dict(integrity or {}),
            "outcome_provenance_state": "OUTCOME_PROVENANCE_INCOMPLETE",
            "reusable_execution_authority": False,
        }

    def _with_natural_handoff_trace(
        self,
        production: dict[str, Any],
        *,
        candidate: Mapping[str, Any],
        validation: Mapping[str, Any],
        qualification: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        execution_grant: Mapping[str, Any] | None,
        budget_admission: Mapping[str, Any] | None,
        execution_context: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        context = dict(execution_context or {})
        trace = natural_production_handoff_observer.build_trace(
            run_id=context.get("run_id") or production.get("run_id"),
            task_id=context.get("task_id") or candidate.get("task_id"),
            candidate=candidate,
            materialization={
                "materialized": bool(candidate.get("candidate_id")),
                "materialization_id": candidate.get("materialization_id"),
            },
            sandbox_validation=validation,
            qualification=qualification,
            arena_selection=arena_selection,
            execution_grant=execution_grant,
            budget_admission=budget_admission,
            production_execution=production,
            production_outcome=production.get("outcome_provenance", {}),
            run_budget_state=context.get("run_budget_state"),
            synthetic_assistance_used=bool(
                context.get("synthetic_assistance_used")
            ),
            test_fixture_used=bool(context.get("test_fixture_used")),
            manual_grant_issuance=bool(context.get("manual_grant_issuance")),
            manual_executor_invocation=bool(
                context.get("manual_executor_invocation")
            ),
        )
        production["NATURAL_PRODUCTION_HANDOFF_TRACE"] = trace
        production["natural_production_handoff_trace"] = trace
        return production

    def _execution_receipt(
        self,
        *,
        request: Mapping[str, Any],
        grant: Mapping[str, Any],
        budget_admission: Mapping[str, Any],
        execution_result_id: str,
        authorization_result: str,
        consumption_state: str,
    ) -> dict[str, Any]:
        receipt = {
            "receipt_id": self._stable_id(
                "learned_object_execution_receipt",
                {
                    "run_id": request.get("run_id"),
                    "execution_grant_id": grant.get("grant_id"),
                    "candidate_id": request.get("candidate_id"),
                    "learned_object_id": request.get("learned_object_id"),
                    "operation": request.get("requested_operation"),
                    "outcome_ref": execution_result_id,
                    "consumption_state": consumption_state,
                },
            ),
            "run_id": request.get("run_id"),
            "execution_grant_id": grant.get("grant_id"),
            "candidate_id": request.get("candidate_id"),
            "learned_object_id": request.get("learned_object_id"),
            "operation": request.get("requested_operation"),
            "authorization_result": authorization_result,
            "budget_admission_result": budget_admission.get("runtime_budget_state")
            or budget_admission.get("budget_admission_state")
            or budget_admission.get("route_budget_enforcement_state"),
            "consumption_state": consumption_state,
            "outcome_ref": execution_result_id,
            "authority": "NONE",
            "reusable_execution_authority": False,
        }
        return receipt

    def _identity_value(self, value: Mapping[str, Any], prefix: str) -> str:
        for key in (
            f"{prefix}_id",
            "selection_id",
            "validation_id",
            "qualification_id",
            "arena_id",
            "id",
        ):
            if value.get(key):
                return str(value[key])
        return self._stable_id(prefix, dict(value or {}))

    def _explicit_identity_value(
        self,
        value: Mapping[str, Any],
        prefix: str,
    ) -> str | None:
        for key in (
            f"{prefix}_id",
            "selection_id",
            "validation_id",
            "qualification_id",
            "arena_id",
            "id",
        ):
            if value.get(key):
                return str(value[key])
        return None

    def _outcome_provenance(
        self,
        *,
        request: Mapping[str, Any],
        candidate: Mapping[str, Any],
        grant: Mapping[str, Any],
        consumed_grant: Mapping[str, Any],
        budget_admission: Mapping[str, Any],
        qualification: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        validation: Mapping[str, Any],
        execution_result_id: str,
        actual_operation: str | None,
    ) -> dict[str, Any]:
        candidate_fingerprint = self._candidate_fingerprint(candidate)
        provenance = {
            "learned_object_id": request.get("learned_object_id"),
            "retrieval_provenance": candidate.get("canonical_provenance")
            or grant.get("canonical_provenance")
            or {},
            "candidate_id": request.get("candidate_id"),
            "candidate_fingerprint": candidate_fingerprint,
            "sandbox_validation_identity": grant.get("validation_identity")
            or validation.get("validation_id"),
            "qualification_identity": grant.get("qualification_identity")
            or qualification.get("qualification_id"),
            "arena_decision_identity": grant.get("arena_selection_identity")
            or arena_selection.get("arena_selection_id")
            or arena_selection.get("selection_id"),
            "grant_id": grant.get("grant_id"),
            "grant_consumed": consumed_grant.get("grant_consumed") is True,
            "grant_audit_record": True,
            "run_id": request.get("run_id"),
            "budget_admission_identity": (
                budget_admission.get("runtime_budget_receipt_fingerprint")
                or budget_admission.get("runtime_budget_snapshot_id")
                or budget_admission.get("budget_admission_id")
                or self._stable_id("budget_admission", budget_admission)
            ),
            "budget_context": dict(budget_admission),
            "requested_operation": request.get("requested_operation"),
            "actual_operation": actual_operation,
            "executor_identity": "runtime.execution.executable_intelligence_engine.ExecutableIntelligenceEngine.execute_production",
            "execution_result_id": execution_result_id,
        }
        required = [
            "learned_object_id",
            "retrieval_provenance",
            "candidate_id",
            "candidate_fingerprint",
            "sandbox_validation_identity",
            "qualification_identity",
            "arena_decision_identity",
            "grant_id",
            "run_id",
            "budget_admission_identity",
            "requested_operation",
            "actual_operation",
            "executor_identity",
            "execution_result_id",
        ]
        missing = [key for key in required if not provenance.get(key)]
        provenance["outcome_provenance_state"] = (
            "OUTCOME_PROVENANCE_COMPLETE"
            if not missing
            else "OUTCOME_PROVENANCE_INCOMPLETE"
        )
        provenance["missing_outcome_provenance"] = missing
        provenance["reusable_execution_authority"] = False
        return provenance

    def _scope_permits(
        self,
        grant_scope: Mapping[str, Any],
        requested_scope: Any,
    ) -> bool:
        requested = requested_scope if isinstance(requested_scope, Mapping) else {}
        if not requested:
            return True
        for key, requested_value in requested.items():
            if key == "operation":
                continue
            if key not in grant_scope:
                return False
            allowed_value = grant_scope.get(key)
            if isinstance(allowed_value, (int, float)) and isinstance(
                requested_value,
                (int, float),
            ):
                if requested_value > allowed_value:
                    return False
            elif allowed_value != requested_value:
                return False
        return True

    def _candidate_fingerprint(self, candidate: Mapping[str, Any]) -> str:
        return self._stable_id("candidate_fingerprint", dict(candidate or {}))

    def _program_fingerprint(self, program: Mapping[str, Any]) -> str:
        return self._stable_id("program_fingerprint", dict(program or {}))

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            default=str,
            separators=(",", ":"),
        )
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"

    def _grid_available(self, grid: Any) -> bool:
        if hasattr(grid, "grid"):
            return self._grid_available(getattr(grid, "grid"))
        if hasattr(grid, "size"):
            try:
                return int(getattr(grid, "size") or 0) > 0
            except (TypeError, ValueError):
                return False
        return isinstance(grid, list) and any(
            isinstance(row, list) and row for row in grid
        )

    def _grounding_context_payload_diagnostic(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        expected = ["input_grid", "target_grid", "predicted_output"]
        received = sorted(str(key) for key in context)
        missing = [key for key in expected if key not in context]
        empty = [
            key for key in expected
            if key in context and not self._grid_available(context.get(key))
        ]
        aliases = {
            "input_grid": ["input", "source_grid", "source"],
            "target_grid": ["output", "target", "output_grid"],
            "predicted_output": ["prediction", "predicted_grid", "output_grid"],
        }
        alias_hits = {
            key: [
                alias for alias in alias_list
                if alias in context and alias not in expected
            ]
            for key, alias_list in aliases.items()
        }
        return {
            "validation_probe_grounding_expected_payload_keys": expected,
            "validation_probe_grounding_received_payload_keys": received,
            "validation_probe_grounding_missing_payload_keys": missing,
            "validation_probe_grounding_empty_payload_keys": empty,
            "validation_probe_grounding_payload_alias_hits": alias_hits,
        }

    def _report(self, **parts: dict[str, Any]) -> dict[str, Any]:
        grounding = parts["grounding"]
        plan = parts["plan"]
        synthesis = parts["synthesis"]
        compiled = parts["compiled"]
        validation = parts["validation"]
        residual = parts["residual"]
        repairs = parts["repairs"]
        adaptation = parts["adaptation"]
        feedback = parts["feedback"]
        grounding_trace = (
            parts.get("grounding_trace")
            if isinstance(parts.get("grounding_trace"), dict)
            else {}
        )
        validation_probe_consumed = bool(parts.get("validation_probe_consumed"))
        production_execution = (
            parts.get("production_execution")
            if isinstance(parts.get("production_execution"), dict)
            else {}
        )
        production_outcome_feedback = (
            parts.get("production_outcome_feedback")
            if isinstance(parts.get("production_outcome_feedback"), dict)
            else {}
        )
        consumed_candidate_identity = (
            parts.get("consumed_candidate_identity")
            if isinstance(parts.get("consumed_candidate_identity"), dict)
            else {}
        )
        arena_recommendation = (
            parts.get("arena_recommendation")
            if isinstance(parts.get("arena_recommendation"), dict)
            else {}
        )
        target_objects = plan.get("target_objects", [])
        localized_operations = plan.get("localized_operations", [])
        residual_regions = residual.get("residual_regions", [])
        validation_probe_compiled = (
            validation_probe_consumed
            and compiled.get("compiled_successfully") is True
        )
        validation_probe_flow = self._validation_probe_flow(
            validation_probe_consumed=validation_probe_consumed,
            validation_probe_compiled=validation_probe_compiled,
            grounding=grounding,
            validation=validation,
            residual=residual,
        )
        compiled_programs = int(compiled.get("compiled_programs", 0) or 0)
        compiled_execution_programs = 0 if validation_probe_consumed else compiled_programs
        validation_probe_compiled_programs = (
            compiled_programs if validation_probe_consumed else 0
        )
        return {
            "semantic_intent_operational": True,
            "object_grounding_operational": grounding.get("object_grounding_operational", False),
            "object_grounding_infrastructure_operational": grounding.get("object_grounding_operational", False),
            "object_grounding_produced": bool(target_objects),
            **self._object_grounding_trace(
                grounding=grounding,
                plan=plan,
                trace=grounding_trace,
            ),
            "grounded_target_object_count": len(target_objects),
            "localized_execution_planning_operational": plan.get("localized_execution_planning_operational", False),
            "primitive_selection_operational": parts["primitives"].get("primitive_selection_operational", False),
            "program_synthesis_operational": synthesis.get("program_synthesis_operational", False),
            "program_compilation_operational": compiled.get("program_compilation_operational", False),
            "program_validation_operational": validation.get("program_validation_operational", False),
            "residual_localization_operational": residual.get("residual_localization_operational", False),
            "residual_repair_operational": repairs.get("residual_repair_operational", False),
            "execution_adaptation_operational": adaptation.get("execution_adaptation_operational", False),
            "execution_memory_operational": parts["memory"].get("execution_memory_operational", False),
            "governed_execution_operational": validation.get("governed_execution_operational", False),
            "knowledge_feedback_operational": feedback.get("knowledge_feedback_operational", False),
            "executable_concepts": 1 if compiled.get("compiled_successfully") else 0,
            "localized_operations": len(localized_operations),
            "target_objects": len(target_objects),
            "synthesized_programs": synthesis.get("synthesized_programs", 0),
            "compiled_programs": compiled_programs,
            "compiled_execution_programs": compiled_execution_programs,
            "validation_probe_compiled_programs": validation_probe_compiled_programs,
            "validated_programs": validation.get("validated_programs", 0),
            "residual_regions": len(residual_regions),
            "generated_repairs": repairs.get("generated_repairs", 0),
            "execution_success_rate": residual.get("prediction_accuracy", 0.0),
            "execution_adaptations": adaptation.get("execution_adaptations", 0),
            "execution_feedback": feedback.get("execution_feedback"),
            "compiler_participation": compiled.get("compiler_participation", 0),
            "validation_probe_consumed": validation_probe_consumed,
            "consumed_candidate_identity": consumed_candidate_identity,
            "selected_candidate_identity": self._candidate_identity(
                arena_recommendation.get("selected_candidate")
            ),
            "validation_probe_candidate_identity": self._candidate_identity(
                arena_recommendation.get("validation_probe_candidate")
            ),
            "validation_probe_compiler_participation": (
                compiled.get("compiler_participation", 0)
                if validation_probe_consumed
                else 0
            ),
            "validation_probe_admission_state": (
                "VALIDATION_PROBE_COMPILED"
                if validation_probe_compiled
                else "VALIDATION_PROBE_COMPILATION_FAILED"
                if validation_probe_consumed
                else "NO_VALIDATION_PROBE"
            ),
            "validation_probe_authority": (
                "SANDBOX_VALIDATION_ONLY"
                if validation_probe_consumed
                else arena_recommendation.get("validation_probe_authority")
                or "NONE"
            ),
            **validation_probe_flow,
            "localized_execution_success": residual.get("localized_execution_success", 0),
            "residual_repair_success": repairs.get("residual_repair_success", 0),
            "production_admission_state": production_execution.get(
                "production_admission_state",
                "NOT_REQUESTED",
            ),
            "production_execution_result_id": production_execution.get(
                "execution_result_id"
            ),
            "production_execution_grant_id": production_execution.get("grant_id"),
            "production_execution_grant_consumption_state": (
                production_execution.get("grant_consumption_state")
            ),
            "production_execution_outcome_provenance_state": (
                production_execution.get("outcome_provenance_state")
            ),
            "production_outcome_feedback_state": production_outcome_feedback.get(
                "feedback_state"
            ),
            "production_outcome_feedback_level": production_outcome_feedback.get(
                "feedback_level"
            ),
            "NATURAL_PRODUCTION_HANDOFF_TRACE": production_execution.get(
                "NATURAL_PRODUCTION_HANDOFF_TRACE",
                {},
            ),
            "natural_production_handoff_trace": production_execution.get(
                "NATURAL_PRODUCTION_HANDOFF_TRACE",
                {},
            ),
            "underlying_executor_called": production_execution.get(
                "underlying_executor_called",
                False,
            ),
            "real_execution_performed": production_execution.get(
                "real_execution_performed",
                False,
            ),
        }

    def _candidate_identity(self, candidate: Any) -> dict[str, Any]:
        if not isinstance(candidate, dict):
            return {}
        metadata = (
            candidate.get("metadata")
            if isinstance(candidate.get("metadata"), dict)
            else {}
        )
        learned_object_id = (
            candidate.get("learned_object_id")
            or candidate.get("source_learned_object_id")
            or metadata.get("learned_object_id")
            or metadata.get("source_learned_object_id")
        )
        return {
            "candidate_id": candidate.get("candidate_id"),
            "source": candidate.get("source"),
            "operation": candidate.get("operation"),
            "learned_object_id": learned_object_id,
            "source_learned_object_id": (
                candidate.get("source_learned_object_id")
                or metadata.get("source_learned_object_id")
                or learned_object_id
            ),
            "learned_object_type": (
                candidate.get("learned_object_type")
                or metadata.get("learned_object_type")
            ),
            "reuse_proposal_id": (
                candidate.get("reuse_proposal_id")
                or metadata.get("reuse_proposal_id")
            ),
            "source_run_id": (
                candidate.get("source_run_id")
                or metadata.get("source_run_id")
            ),
            "target_run_id": (
                candidate.get("target_run_id")
                or metadata.get("target_run_id")
            ),
            "authority": candidate.get("authority") or metadata.get("authority"),
            "behavioral_authority": (
                candidate.get("behavioral_authority")
                or metadata.get("behavioral_authority")
            ),
        }

    def _object_grounding_trace(
        self,
        *,
        grounding: dict[str, Any],
        plan: dict[str, Any],
        trace: dict[str, Any],
    ) -> dict[str, Any]:
        candidate_objects = grounding.get("candidate_objects")
        candidate_objects = (
            candidate_objects if isinstance(candidate_objects, list) else []
        )
        target_objects = plan.get("target_objects")
        target_objects = target_objects if isinstance(target_objects, list) else []
        if target_objects:
            state = "OBJECT_GROUNDING_PRODUCED"
            blocked_stage = "none"
            action = "use_grounded_target_object_evidence"
        elif not trace.get("object_grounding_input_available"):
            state = "GROUNDING_INPUT_MISSING"
            blocked_stage = "validation_probe_grounding_context"
            action = "forward_validation_probe_grounding_context"
        elif not candidate_objects:
            state = "GROUNDING_INPUT_HAS_NO_OBJECTS"
            blocked_stage = "object_extraction"
            action = "select_object_rich_validation_task"
        else:
            state = "TARGET_OBJECT_SELECTION_FAILED"
            blocked_stage = "target_object_selection"
            action = "inspect_candidate_target_object_contract"
        return {
            "object_grounding_flow_state": state,
            "object_grounding_blocked_stage": blocked_stage,
            "object_grounding_flow_action": action,
            "object_grounding_candidate_object_count": len(candidate_objects),
            **trace,
        }

    def _validation_probe_flow(
        self,
        *,
        validation_probe_consumed: bool,
        validation_probe_compiled: bool,
        grounding: dict[str, Any],
        validation: dict[str, Any],
        residual: dict[str, Any],
    ) -> dict[str, Any]:
        if not validation_probe_consumed:
            return {
                "validation_probe_sandbox_validation_invoked": False,
                "validation_probe_validation_result_captured": False,
                "validation_probe_evidence_acceptance_evaluated": False,
                "validation_probe_evidence_acceptance_state": "NO_VALIDATION_PROBE",
                "validation_probe_evidence_insufficiency_cause": "NO_VALIDATION_PROBE",
                "validation_probe_required_evidence": "Not Available",
                "validation_probe_recommended_validation_action": "Not Available",
                "compiled_to_validated_probe_state": "NO_VALIDATION_PROBE",
            }
        validation_invoked = validation_probe_compiled and bool(
            validation.get("program_validation_operational")
        )
        result_captured = validation_invoked and isinstance(
            validation.get("validation_success"),
            bool,
        )
        evidence_evaluated = result_captured
        blockers = validation.get("validation_blockers") or []
        blockers = blockers if isinstance(blockers, list) else [blockers]
        if not validation_probe_compiled:
            acceptance_state = "INSUFFICIENT"
            probe_state = "VALIDATION_PROBE_COMPILATION_FAILED"
        elif validation.get("validation_success") is True:
            acceptance_state = "ACCEPTED"
            probe_state = "VALIDATION_PROBE_VALIDATED"
        elif any(
            blocker in {"missing_object_grounding", "missing_ground_truth"}
            for blocker in blockers
        ) or not validation.get("object_consistency"):
            acceptance_state = "INSUFFICIENT"
            probe_state = "SANDBOX_VALIDATION_EVIDENCE_INSUFFICIENT"
        elif blockers:
            acceptance_state = "REJECTED"
            probe_state = "SANDBOX_VALIDATION_REJECTED"
        else:
            acceptance_state = "REJECTED"
            probe_state = "SANDBOX_VALIDATION_REJECTED"
        comparable_output_captured = bool(
            residual.get("residual_localization_operational")
            and residual.get("prediction_accuracy") is not None
        )
        insufficiency = self._evidence_insufficiency(
            acceptance_state=acceptance_state,
            grounding=grounding,
            validation=validation,
            residual=residual,
            comparable_output_captured=comparable_output_captured,
        )
        return {
            "validation_probe_sandbox_validation_invoked": validation_invoked,
            "validation_probe_validation_result_captured": result_captured,
            "validation_probe_comparable_output_captured": comparable_output_captured,
            "validation_probe_evidence_acceptance_evaluated": evidence_evaluated,
            "validation_probe_evidence_acceptance_state": acceptance_state,
            **insufficiency,
            "compiled_to_validated_probe_state": probe_state,
        }

    def _evidence_insufficiency(
        self,
        *,
        acceptance_state: str,
        grounding: dict[str, Any],
        validation: dict[str, Any],
        residual: dict[str, Any],
        comparable_output_captured: bool,
    ) -> dict[str, str]:
        if acceptance_state == "ACCEPTED":
            return {
                "validation_probe_evidence_insufficiency_cause": "NONE",
                "validation_probe_required_evidence": "evidence_contract_satisfied",
                "validation_probe_recommended_validation_action": "retain_validation_evidence",
            }
        if acceptance_state == "REJECTED":
            blockers = validation.get("validation_blockers") or []
            blockers = blockers if isinstance(blockers, list) else [blockers]
            cause = "governance_blocked" if blockers else "evidence_contract_rejected"
            return {
                "validation_probe_evidence_insufficiency_cause": cause,
                "validation_probe_required_evidence": "contract_compliant_validation_evidence",
                "validation_probe_recommended_validation_action": "review_validation_contract_blockers",
            }
        target_objects = grounding.get("target_objects")
        target_objects = target_objects if isinstance(target_objects, list) else []
        candidate_objects = grounding.get("candidate_objects")
        candidate_objects = candidate_objects if isinstance(candidate_objects, list) else []
        blockers = validation.get("validation_blockers") or []
        blockers = blockers if isinstance(blockers, list) else [blockers]
        if "missing_object_grounding" in blockers or not target_objects:
            return {
                "validation_probe_evidence_insufficiency_cause": "missing_object_grounding",
                "validation_probe_required_evidence": "grounded_target_object_evidence",
                "validation_probe_recommended_validation_action": "select_object_grounded_validation_task",
            }
        if not comparable_output_captured:
            return {
                "validation_probe_evidence_insufficiency_cause": "missing_comparable_output",
                "validation_probe_required_evidence": "input_output_grid_pair",
                "validation_probe_recommended_validation_action": "select_ground_truth_aligned_validation_task",
            }
        if residual.get("residual_count"):
            return {
                "validation_probe_evidence_insufficiency_cause": "execution_residual_remaining",
                "validation_probe_required_evidence": "residual_free_sandbox_validation",
                "validation_probe_recommended_validation_action": "select_residual_repair_validation_task",
            }
        if not candidate_objects:
            return {
                "validation_probe_evidence_insufficiency_cause": "weak_grounding_context",
                "validation_probe_required_evidence": "strong_candidate_object_grounding",
                "validation_probe_recommended_validation_action": "select_object_context_rich_validation_task",
            }
        return {
            "validation_probe_evidence_insufficiency_cause": "evidence_strength_below_acceptance_threshold",
            "validation_probe_required_evidence": "additional_governed_validation_evidence",
            "validation_probe_recommended_validation_action": "select_governed_validation_evidence_task",
        }


executable_intelligence_engine = ExecutableIntelligenceEngine()


__all__ = ["ExecutableIntelligenceEngine", "executable_intelligence_engine"]
