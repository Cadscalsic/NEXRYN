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
        counterfactual_revision: dict[str, Any] | None = None,
        governance_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidate = validated_candidate if isinstance(validated_candidate, dict) else {"operation": operation}
        grounding = self.object_grounder.ground(
            input_grid,
            semantic_intent=semantic_intent,
            candidate=candidate,
        )
        plan = self.planner.plan(operation, grounding, semantic_intent=semantic_intent)
        primitives = self.primitive_selector.select(operation, plan, semantic_intent=semantic_intent)
        synthesis = self.synthesizer.synthesize(
            semantic_intent=semantic_intent,
            hypotheses=hypotheses or [],
            validated_candidate=candidate,
            counterfactual_revision=counterfactual_revision,
            execution_plan=plan,
            primitive_selection=primitives,
        )
        compiled = self.compiler.compile(
            semantic_intent=semantic_intent,
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
            predicted_output if predicted_output is not None else input_grid,
            target_grid if target_grid is not None else input_grid,
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
                "selection_state": "VALIDATED_WITH_REPAIR" if validation.get("validation_success") else "BLOCKED",
                "execution_mode": "sandbox" if validation.get("validation_success") else "blocked",
                "selection_evidence": {
                    "validation": validation,
                    "residual": residual,
                    "repairs": repairs,
                },
            },
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
        target_objects = plan.get("target_objects", [])
        localized_operations = plan.get("localized_operations", [])
        residual_regions = residual.get("residual_regions", [])
        return {
            "semantic_intent_operational": True,
            "object_grounding_operational": grounding.get("object_grounding_operational", False),
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
            "compiled_programs": compiled.get("compiled_programs", 0),
            "validated_programs": validation.get("validated_programs", 0),
            "residual_regions": len(residual_regions),
            "generated_repairs": repairs.get("generated_repairs", 0),
            "execution_success_rate": residual.get("prediction_accuracy", 0.0),
            "execution_adaptations": adaptation.get("execution_adaptations", 0),
            "execution_feedback": feedback.get("execution_feedback"),
            "compiler_participation": compiled.get("compiler_participation", 0),
            "localized_execution_success": residual.get("localized_execution_success", 0),
            "residual_repair_success": repairs.get("residual_repair_success", 0),
            "real_execution_performed": False,
        }


executable_intelligence_engine = ExecutableIntelligenceEngine()


__all__ = ["ExecutableIntelligenceEngine", "executable_intelligence_engine"]
