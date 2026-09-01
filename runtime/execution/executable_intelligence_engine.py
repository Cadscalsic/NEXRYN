from __future__ import annotations

from typing import Any

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
        counterfactual_revision: dict[str, Any] | None = None,
        governance_context: dict[str, Any] | None = None,
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
            "sandbox_validation_only"
            if validation_probe_consumed and validation.get("validation_success")
            else "sandbox"
            if validation.get("validation_success")
            else "blocked"
        )
        final_selection_state = (
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
                },
            },
        }

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
            "real_execution_performed": False,
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
